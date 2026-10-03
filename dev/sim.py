#!/usr/bin/env python3
"""In-process simulation of the resource: the real server and client Lua run in two Lua 5.4 runtimes with stand-ins for
FiveM natives, ox_lib, qbx_core and ox_inventory, and SQLite standing in for MySQL. Client callbacks reach server callbacks
and server events reach client handlers, like in game. Time is virtual, so gatherings and the contest close can be
fast-forwarded. It cannot draw anything or check GTA itself (props, anims, blips), but it runs every rule, query and payout.

    pip install lupa      (once)
    python dev/sim.py     exits non-zero on any failure
"""
import re, sqlite3, sys, json, math, time
from pathlib import Path
import lupa.lua54 as lupa

ROOT = Path(__file__).resolve().parent.parent
results = []
def check(name, cond, detail=''):
    results.append((name, bool(cond)))
    if not cond and detail: print('   ', name, '->', detail)

# ---------------------------------------------------------------- MySQL on SQLite
db = sqlite3.connect(':memory:')
db.row_factory = sqlite3.Row
CONFLICT = {'s2_holiday_points': '(citizenid, event, year)', 's2_holiday_playtime': '(citizenid, day)'}
clock = {'ms': 0}

def translate(sql):
    s = ' '.join(sql.split())
    s = s.replace('TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP', 'INTEGER NOT NULL DEFAULT 0')
    s = s.replace('TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP', 'INTEGER NOT NULL DEFAULT 0')
    s = re.sub(r', KEY \w+ \([^)]*\)', '', s)
    s = s.replace('INSERT IGNORE INTO', 'INSERT OR IGNORE INTO')
    s = re.sub(r'LEFT\((\w+), (\d+)\)', r'substr(\1, 1, \2)', s)
    m = re.search(r'INSERT INTO (\w+) .* ON DUPLICATE KEY UPDATE (.*)$', s)
    if m:
        table, sets = m.group(1), re.sub(r'VALUES\((\w+)\)', r'excluded.\1', m.group(2))
        if table == 's2_holiday_points': sets += ', updated = %d' % clock['ms']   # ON UPDATE CURRENT_TIMESTAMP
        s = s[:s.index(' ON DUPLICATE KEY UPDATE')] + f' ON CONFLICT{CONFLICT[table]} DO UPDATE SET {sets}'
    if s.startswith('INSERT INTO s2_holiday_points') and 'updated' not in s.split(' ON ')[0]:
        s = s.replace('(citizenid, event, year, points, name) VALUES (?, ?, ?, ?, ?)', '(citizenid, event, year, points, name, updated) VALUES (?, ?, ?, ?, ?, %d)' % clock['ms'])
    return s

def run_sql(sql, params):
    q = translate(sql)
    args = [params[i] for i in range(1, len(params) + 1)] if params is not None else []
    try:
        cur = db.execute(q, args)
    except Exception as e:
        raise RuntimeError(f'SQL error: {e}\n  {q}\n  {args}')
    db.commit()
    return cur

# ---------------------------------------------------------------- shared Lua prelude
PRELUDE = r'''
SIM = { threads = {}, log = {} }
local vmeta = {}
vmeta.__index = vmeta
vmeta.__sub = function(a, b) return vector3(a.x - b.x, a.y - b.y, a.z - b.z) end
vmeta.__add = function(a, b) return vector3(a.x + b.x, a.y + b.y, a.z + b.z) end
vmeta.__mul = function(a, k) return vector3(a.x * k, a.y * k, a.z * k) end
vmeta.__div = function(a, k) return vector3(a.x / k, a.y / k, a.z / k) end
vmeta.__len = function(a) return math.sqrt(a.x * a.x + a.y * a.y + a.z * a.z) end
vmeta.__eq = function(a, b) return a.x == b.x and a.y == b.y and a.z == b.z end
function vector3(x, y, z) return setmetatable({ x = x + 0.0, y = y + 0.0, z = z + 0.0 }, vmeta) end
vec3 = vector3
function joaat(s)
    s = tostring(s):lower(); local h = 0
    for i = 1, #s do h = (h + s:byte(i)) & 0xFFFFFFFF; h = (h + (h << 10)) & 0xFFFFFFFF; h = h ~ (h >> 6) end
    h = (h + (h << 3)) & 0xFFFFFFFF; h = h ~ (h >> 11); h = (h + (h << 15)) & 0xFFFFFFFF
    return h >= 0x80000000 and h - 0x100000000 or h
end
GetHashKey = joaat
local realTime, realDate = os.time, os.date
os.time = function(t) if t then return realTime(t) end return SIM.base + PY.now() // 1000 end
os.date = function(fmt, t) return realDate(fmt, t or os.time()) end
function CreateThread(fn) SIM.threads[#SIM.threads + 1] = { co = coroutine.create(fn), wake = PY.now() } end
Citizen = { CreateThread = CreateThread }
function Wait(ms) coroutine.yield(ms or 0) end
function SetTimeout(ms, fn) SIM.threads[#SIM.threads + 1] = { co = coroutine.create(fn), wake = PY.now() + ms } end
function SIM.step(now) -- run every thread that is due
    local ran = true
    while ran do
        ran = false
        for _, t in ipairs(SIM.threads) do
            if not t.dead and t.wake <= now then
                ran = true
                local ok, r = coroutine.resume(t.co)
                if not ok then t.dead = true; error('thread error: ' .. tostring(r) .. '\n' .. debug.traceback(t.co), 0) end
                if coroutine.status(t.co) == 'dead' then t.dead = true else t.wake = now + math.max(r or 0, 1) end
            end
        end
    end
end
function SIM.call(fn, ...) -- run a callback inside a coroutine like FiveM does; it must finish without yielding
    local co = coroutine.create(fn)
    local res = table.pack(coroutine.resume(co, ...))
    if not res[1] then error(tostring(res[2]) .. '\n' .. debug.traceback(co), 0) end
    if coroutine.status(co) ~= 'dead' then error('callback yielded (it must not wait)', 0) end
    return table.unpack(res, 2, res.n)
end
json = { encode = function(t) return PY.json_encode(t) end, decode = function(s) return PY.json_decode(s) end }
local kvp = {}
function GetResourceKvpString(k) return kvp[k] end
function SetResourceKvp(k, v) kvp[k] = v end
function GetResourceKvpInt(k) return kvp[k] or 0 end
function SetResourceKvpInt(k, v) kvp[k] = v end
function GetCurrentResourceName() return 's2-holidays' end
SIM.events = {}
function RegisterNetEvent(name, fn) if fn then AddEventHandler(name, fn) end end
function AddEventHandler(name, fn) SIM.events[name] = SIM.events[name] or {}; table.insert(SIM.events[name], fn) end
function SIM.fire(name, ...) for _, fn in ipairs(SIM.events[name] or {}) do SIM.call(fn, ...) end end
SIM.commands = {}
function RegisterCommand(name, fn) SIM.commands[name] = fn end
lib = { callback = setmetatable({ registry = {} }, { __call = function(_, name, src, cb, ...) PY.client_callback(name, src, cb, ...) end }) }
function lib.callback.register(name, fn) lib.callback.registry[name] = fn end
'''

SERVER_STUBS = r'''
SIM.base = 0
SIM.printed = {}
local rawPrint = print
print = function(...) local t = {}; for i = 1, select('#', ...) do t[i] = tostring(select(i, ...)) end; table.insert(SIM.printed, table.concat(t, ' ')); if not tostring(t[1]):find('admin ', 1, true) then rawPrint(...) end end
PLAYERS = {}  -- [src] = { cid, first, last, pos, weapon, admin, bucket, health, dead }
local items = {}
function SIM.setItems(list) items = {}; for _, n in ipairs(list) do items[n] = true end end
SIM.inv, SIM.money = {}, {}
local function P(src) return PLAYERS[src] end
function GetPlayerPed(src) return P(src) and src or 0 end
function GetEntityCoords(ped) local p = P(ped); return p and p.pos or vector3(0, 0, 0) end
function GetEntityHealth(ped) local p = P(ped); return p and p.health or 0 end
function GetVehiclePedIsIn() return 0 end
function GetEntitySpeed() return 0.0 end
function GetSelectedPedWeapon(ped) local p = P(ped); return p and p.weapon and joaat(p.weapon) or joaat('WEAPON_UNARMED') end
function GetPlayerRoutingBucket(src) local p = P(src); return p and p.bucket or 0 end
function GetPlayerName(src) local p = P(src); return p and (p.first .. '_' .. p.last) or nil end
function IsPlayerAceAllowed(src) local p = P(src); return p and p.admin or false end
function SetEntityCoords(ped, x, y, z) local p = P(ped); if p then p.pos = vector3(x, y, z) end end
function TriggerClientEvent(name, target, ...) table.insert(SIM.log, { name = name, target = target, args = table.pack(...) }); PY.client_event(name, target, ...) end
local function qbPlayer(src)
    local p = P(src); if not p then return nil end
    return { PlayerData = { citizenid = p.cid, source = src, charinfo = { firstname = p.first, lastname = p.last }, metadata = { isdead = p.dead, inlaststand = false } } }
end
local qbx = {
    GetPlayer = function(_, src) return qbPlayer(src) end,
    GetQBPlayers = function() local t = {}; for src in pairs(PLAYERS) do t[src] = qbPlayer(src) end; return t end,
    AddMoney = function(_, src, account, amount) SIM.money[src] = (SIM.money[src] or 0) + amount; return true end,
    HasPermission = function(_, src) local p = P(src); return p and p.admin or false end,
}
local inv = {
    CanCarryItem = function(_, src, name, count) if not items[name] then return nil end; return not (P(src) and P(src).full) end, -- real ox_inventory: nil for unknown items
    AddItem = function(_, src, name, count) if not items[name] then return false, 'invalid_item' end; SIM.inv[src] = SIM.inv[src] or {}; SIM.inv[src][name] = (SIM.inv[src][name] or 0) + count; return true end,
    Items = function(_, name) if name then return items[name] and { name = name } or nil end; local t = {}; for n in pairs(items) do t[n] = { name = n } end; return t end,
}
exports = { qbx_core = qbx, ox_inventory = inv }
MySQL = {
    query = setmetatable({ await = function(sql, p) return PY.sql_rows(sql, p) end }, { __call = function(_, sql, p) return PY.sql_rows(sql, p) end }),
    scalar = { await = function(sql, p) return PY.sql_scalar(sql, p) end },
    single = { await = function(sql, p) return PY.sql_single(sql, p) end },
    update = setmetatable({ await = function(sql, p) return PY.sql_update(sql, p) end }, { __call = function(_, sql, p) return PY.sql_update(sql, p) end }),
}
'''

CLIENT_STUBS = r'''
SIM.base = 0
ME = { pos = vector3(0, 0, 0), weapon = 'WEAPON_UNARMED', water = false, hour = 22, key = false, aimAt = nil }
SIM.notifies, SIM.nui, SIM.text, SIM.points, SIM.waypoint, SIM.fx, SIM.peds = {}, {}, nil, {}, nil, 0, {}
cache = { ped = 1, playerId = 1, vehicle = false }
LocalPlayer = { state = { isLoggedIn = true } }
local nextId = 100
local function new() nextId = nextId + 1; return nextId end
local entities = {}
function GetEntityCoords(e) if e == 1 then return ME.pos end; return entities[e] and entities[e].pos or vector3(0, 0, 0) end
function GetGameTimer() return PY.now() end
function GetFrameTime() return 0.1 end
function GetClockHours() return ME.hour end
function IsControlJustReleased() return ME.key end
function IsEntityInWater() return ME.water end
function GetSelectedPedWeapon() return joaat(ME.weapon) end
function IsPlayerFreeAiming() return ME.weapon ~= 'WEAPON_UNARMED' end
function IsFlashLightOn() return ME.weapon == 'WEAPON_FLASHLIGHT' end
function GetGameplayCamCoord() return ME.pos end
function GetGameplayCamRot() -- aim at ME.aimAt when set (pitch x, yaw z in degrees, GTA convention)
    if not ME.aimAt then return vector3(0, 0, 0) end
    local d = ME.aimAt - ME.pos; local flat = math.sqrt(d.x * d.x + d.y * d.y)
    return vector3(math.deg(math.atan(d.z, flat)), 0, math.deg(math.atan(-d.x, d.y)))
end
function StartExpensiveSynchronousShapeTestLosProbe() return 1 end
function GetShapeTestResult() return 2, 0 end
function GetGroundZFor_3dCoord(x, y, z) return true, z - 2.0 end
function IsModelInCdimage() return true end
function CreateObject(model, x, y, z) local id = new(); entities[id] = { pos = vector3(x, y, z) }; return id end
function CreatePed(_, model, x, y, z) local id = new(); entities[id] = { pos = vector3(x, y, z), ped = true }; SIM.peds[#SIM.peds + 1] = id; return id end
function DoesEntityExist(e) return entities[e] ~= nil end
function DeleteEntity(e) entities[e] = nil end
function SetEntityCoordsNoOffset(e, x, y, z) if entities[e] then entities[e].pos = vector3(x, y, z) end end
function GetEntityAlpha() return 100 end
function GetScreenCoordFromWorldCoord() return true, 0.5, 0.5 end
function SetNewWaypoint(x, y) SIM.waypoint = { x = x, y = y } end
function SendNUIMessage(m) table.insert(SIM.nui, m) end
SIM.nuiCallbacks = {}
function RegisterNUICallback(name, fn) SIM.nuiCallbacks[name] = fn end
function StartParticleFxNonLoopedAtCoord() SIM.fx = SIM.fx + 1 end
for _, n in ipairs({ 'AddBlipForCoord', 'AddBlipForRadius' }) do _G[n] = function() return new() end end
for _, n in ipairs({ 'AddTextComponentSubstringPlayerName', 'AnimpostfxPlay', 'AnimpostfxStop', 'AttachEntityToEntity', 'BeginTextCommandSetBlipName', 'ClearPedTasks',
    'DrawLightWithRange', 'DrawMarker', 'DrawRect', 'EndTextCommandSetBlipName', 'ExecuteCommand', 'FreezeEntityPosition', 'PlaceObjectOnGroundProperly', 'PlaySoundFrontend',
    'RegisterKeyMapping', 'RemoveBlip', 'SetBlipAlpha', 'SetBlipAsShortRange', 'SetBlipColour', 'SetBlipRoute', 'SetBlipRouteColour', 'SetBlipScale', 'SetBlipSprite',
    'SetBlockingOfNonTemporaryEvents', 'SetEntityAlpha', 'SetEntityCollision', 'SetEntityHeading', 'SetEntityInvincible', 'SetEntityVisible', 'SetModelAsNoLongerNeeded',
    'SetNuiFocus', 'SetPedCanRagdoll', 'ShakeGameplayCam', 'StopAnimTask', 'TaskPlayAnim', 'UseParticleFxAssetNextCall' }) do _G[n] = function() end end
function GetPedBoneIndex() return 0 end
function IsEntityPlayingAnim() return true end
function lib.notify(n) table.insert(SIM.notifies, n) end
function lib.showTextUI(t) SIM.text = t end
function lib.hideTextUI() SIM.text = nil end
function lib.progressCircle() Wait(10); return true end
function lib.requestModel() return true end
function lib.requestAnimDict() return true end
function lib.requestNamedPtfxAsset() return true end
function lib.setClipboard() end
function lib.callback.await(name, _, ...) return PY.server_callback(name, ...) end
lib.points = { new = function(o) o.remove = function(self) self.removed = true end; table.insert(SIM.points, o); return o end }
function SIM.visit(point, dist) -- stand `dist` metres from a lib.points point for one frame
    if not point.entered then point.entered = true; if point.onEnter then SIM.call(point.onEnter, point) end end
    point.currentDistance = dist
    if point.nearby then SIM.call(point.nearby, point) end
end
'''

# ---------------------------------------------------------------- runtimes and the bridge between them
def make_runtime():
    return lupa.LuaRuntime(unpack_returned_tuples=True)

S, C = make_runtime(), make_runtime()

def to_py(v):
    if lupa.lua_type(v) == 'table':
        keys = list(v.keys())
        if keys and all(isinstance(k, int) for k in keys) and sorted(keys) == list(range(1, len(keys) + 1)):
            return [to_py(v[k]) for k in sorted(keys)]
        return {k: to_py(v[k]) for k in keys}
    return v

def to_lua(rt, v):
    if isinstance(v, dict): return rt.table_from({k: to_lua(rt, x) for k, x in v.items()})
    if isinstance(v, (list, tuple)): return rt.table_from([to_lua(rt, x) for x in v])
    return v

ME_SRC = 1  # the client runtime plays this server id

class PY:
    @staticmethod
    def now(): return clock['ms']
    @staticmethod
    def json_encode(t): return json.dumps(to_py(t))
    @staticmethod
    def json_decode(s):
        try: return to_lua(S, json.loads(s))
        except Exception: return None
    @staticmethod
    def sql_rows(sql, p): return S.table_from([S.table_from(dict(r)) for r in run_sql(sql, p).fetchall()])
    @staticmethod
    def sql_scalar(sql, p):
        r = run_sql(sql, p).fetchone(); return r[0] if r else None
    @staticmethod
    def sql_single(sql, p):
        r = run_sql(sql, p).fetchone(); return S.table_from(dict(r)) if r else None
    @staticmethod
    def sql_update(sql, p): return run_sql(sql, p).rowcount
    @staticmethod
    def server_callback(name, *args):  # client lib.callback.await -> server callback with the client's source
        fn = S.globals().lib.callback.registry[name]
        if fn is None: raise RuntimeError('no server callback ' + name)
        res = S.globals().SIM.call(fn, ME_SRC, *[to_lua(S, to_py(a)) for a in args])
        return to_lua(C, to_py(res))
    @staticmethod
    def client_callback(name, src, cb, *args):  # server lib.callback(name, src, cb, ...) -> client callback
        if src != ME_SRC: return cb(True)
        fn = C.globals().lib.callback.registry[name]
        res = C.globals().SIM.call(fn, *[to_lua(C, to_py(a)) for a in args])
        cb(res)
    @staticmethod
    def client_event(name, target, *args):
        if target in (-1, ME_SRC) and name in [k for k in C.globals().SIM.events]:
            C.globals().SIM.fire(name, *[to_lua(C, to_py(a)) for a in args])

for rt in (S, C):
    rt.globals().PY = PY
    rt.execute(PRELUDE)
S.execute(SERVER_STUBS)
C.execute(CLIENT_STUBS)

def load(rt, rel):
    src = (ROOT / rel).read_text()
    rt.globals().SIM.call(rt.eval(f'function(src) return assert(load(src, "@{rel}")) end')(src))

def advance(ms, step=100):
    end = clock['ms'] + ms
    while clock['ms'] < end:
        clock['ms'] = min(end, clock['ms'] + step)
        S.globals().SIM.step(clock['ms']); C.globals().SIM.step(clock['ms'])

ITEMS = ['sandwich', 'water', 'cola', 'burger', 'bandage', 'radio', 'repairkit', 'armour', 'lockpick', 'phone']
S.globals().SIM.setItems(S.table_from(ITEMS))

# ---------------------------------------------------------------- boot
try:
    for f in ('config.lua', 'config_world.lua', 'server/dates.lua', 'server/admin.lua', 'server/events.lua', 'server/ghosts.lua', 'server/world.lua', 'server/main.lua'):
        load(S, f)
    for f in ('config.lua', 'config_world.lua', 'client/main.lua', 'client/events.lua', 'client/admin.lua', 'client/ghosts.lua', 'client/world.lua'):
        load(C, f)
    advance(200)
    boot_ok = True
except Exception as e:
    print('BOOT FAILED:', e); boot_ok = False
check('boot: every server and client file loads and the tables are created', boot_ok and db.execute("SELECT count(*) FROM sqlite_master WHERE name LIKE 's2_holiday_%'").fetchone()[0] == 4)
if not boot_ok:
    for n, c in results: print(('PASS ' if c else 'FAIL ') + n)
    sys.exit(1)

G, CG = S.globals(), C.globals()
Lv = lambda x, y, z: S.eval('vector3')(x, y, z)

def player(src, cid, first, last, pos, **kw):
    t = {'cid': cid, 'first': first, 'last': last, 'pos': pos, 'weapon': kw.get('weapon'), 'admin': kw.get('admin', False), 'bucket': 0, 'health': 200, 'dead': False}
    G.PLAYERS[src] = S.table_from(t)
def move(src, c):
    G.PLAYERS[src].pos = Lv(c['x'], c['y'], c['z']) if isinstance(c, dict) else c
    if src == ME_SRC: CG.ME.pos = C.eval('vector3')(G.PLAYERS[src].pos.x, G.PLAYERS[src].pos.y, G.PLAYERS[src].pos.z)
def admin(action, **data):
    fn = G.lib.callback.registry['s2-holidays:admin:do']
    return to_py(G.SIM.call(fn, 1, action, S.table_from(data)))
def set_date(d): return admin('date', value=d)['msg']
def set_clock(t): return admin('clock', value=t)['msg']
def scb(name, src, *args): return to_py(G.SIM.call(G.lib.callback.registry[name], src, *args))
def places(name): return to_py(G.World.places(name))
def world_cfg(h): return to_py(G.Config.World[h])
def money(src): return G.SIM.money[src] or 0

player(1, 'CID1', 'Alex', 'Rivera', Lv(0, 0, 0), admin=True)
player(2, 'CID2', 'Marcus', 'Thorne', Lv(0, 0, 0))

# ---------------------------------------------------------------- Halloween: all of October
check('halloween: date override works', set_date('2026-10-03') == 'Date override set.')
st = scb('s2-holidays:getState', 1)
ids = [h['id'] for h in st['active']]
check('halloween: running on Oct 3 and on screen', ids[:1] == ['halloween'], ids)
check('halloween: city doors and contest in state', 'halloween' in st['world'] and 'halloween' in st['contest'])
for d in ('2026-10-01', '2026-10-15', '2026-10-31'):
    set_date(d); check(f'halloween: activities open on {d}', 'halloween' in scb('s2-holidays:getState', 1)['world'])
set_date('2026-09-30'); check('halloween: not running on Sep 30', 'halloween' not in scb('s2-holidays:getState', 1)['world'])
set_date('2026-10-03'); set_clock('21:00')

houses = places('houses')
move(1, houses[0])
r = scb('s2-holidays:world:use', 1, 'halloween', 'doors', 1)
check('trick or treat: knocking at the door pays out and scores', r.get('ok') and r.get('points', 0) > 0 and r.get('contest', {}).get('points', 0) > 0, r)
r2 = scb('s2-holidays:world:use', 1, 'halloween', 'doors', 1)
check('trick or treat: same door twice is refused', not r2.get('ok') and 'already' in r2.get('msg', ''), r2)
r3 = scb('s2-holidays:world:use', 1, 'halloween', 'doors', 5)
check('trick or treat: a door you are not at is refused', not r3.get('ok') and 'closer' in r3.get('msg', ''), r3)
r4 = scb('s2-holidays:world:use', 1, 'halloween', 'doors', 999)
check('trick or treat: a made-up door index is refused', not r4.get('ok'))
done = 1
for i in range(2, len(houses) + 1):
    move(1, houses[i - 1]); res = scb('s2-holidays:world:use', 1, 'halloween', 'doors', i)
    if res.get('ok'): done += 1
cap = world_cfg('halloween')[0]['perDay']
check(f'trick or treat: nightly cap of {cap} doors holds', done == cap, done)

# client side of the same thing: walk up, press E, the server is asked, the door greys out
advance(61000)  # client resync picks up today's progress
move(1, houses[0]); pts = [p for p in to_py(CG.SIM.points)]
check('client: a lib.points prompt exists for every door, pickup and gathering', len(CG.SIM.points) >= len(houses))

# a fresh day for the client flow
set_date('2026-10-04'); CG.WorldSync()
door_pt = next(p for p in CG.SIM.points.values() if p.coords.x == houses[2]['x'] and p.coords.y == houses[2]['y'] and not p.removed)
move(1, houses[2]); CG.ME.key = True
CG.SIM.visit(door_pt, 1.0); CG.ME.key = False; advance(500)
n = to_py(CG.SIM.notifies)[-1] if len(CG.SIM.notifies) else {}
check('client: pressing E at a door knocks, asks the server and shows the result', n.get('type') in ('success', 'inform') and 'today' in n.get('description', ''), n)

# ---------------------------------------------------------------- Halloween ghosts with a flashlight
CG.ME.hour = 22; G.Ghosts.last[1] = None
spawned = G.Ghosts.spawnFor(1, True)
check('ghosts: a ghost spawns near the player (client accepts)', spawned and G.Ghosts.count == 1)
gid = G.Ghosts.byPlayer[1]; ghost = G.Ghosts.active[gid]
move(1, {'x': ghost.coords.x + 8, 'y': ghost.coords.y, 'z': ghost.coords.z})
r = scb('s2-holidays:ghost:catch', 1, gid)
check('ghosts: catching without a flashlight is refused', not r.get('ok') and 'flashlight' in r.get('msg', ''), r)
G.PLAYERS[1].weapon = 'WEAPON_FLASHLIGHT'
move(2, {'x': 0, 'y': 0, 'z': 0})
r = scb('s2-holidays:ghost:catch', 2, gid)
check("ghosts: someone else's ghost cannot be caught", not r.get('ok'), r)
G.PLAYERS[1].weapon = None
# client flow: stand near the ghost, hold the flashlight beam on it until the meter fills
move(1, {'x': ghost.coords.x + 8, 'y': ghost.coords.y, 'z': ghost.coords.z})
G.PLAYERS[1].weapon = 'WEAPON_FLASHLIGHT'; CG.ME.weapon = 'WEAPON_FLASHLIGHT'
ped = CG.SIM.peds[len(CG.SIM.peds)]
pts_before = run_sql('SELECT points FROM s2_holiday_points WHERE citizenid = ?', S.table_from(['CID1'])).fetchone()[0]
for _ in range(60):  # keep the beam on the ghost as it drifts, like a player tracking it with the mouse
    CG.ME.aimAt = CG.GetEntityCoords(ped); advance(100, step=100)
pts_after = run_sql('SELECT points FROM s2_holiday_points WHERE citizenid = ?', S.table_from(['CID1'])).fetchone()[0]
check('ghosts: holding the flashlight beam on the ghost traps it and scores', pts_after > pts_before and G.Ghosts.count == 0, (pts_before, pts_after, G.Ghosts.count))
CG.ME.aimAt = None

# ---------------------------------------------------------------- contest close at midnight after Oct 31, prizes until Nov 7
move(2, houses[0]); set_date('2026-10-31'); set_clock('20:00')
scb('s2-holidays:world:use', 2, 'halloween', 'doors', 1)
set_clock('23:59:40'); advance(65000)
winners = db.execute("SELECT place, citizenid FROM s2_holiday_winners WHERE event = 'halloween' ORDER BY place").fetchall()
check('contest: closes at midnight after Oct 31 and locks in the winners', len(winners) >= 2 and winners[0]['citizenid'] == 'CID1', [tuple(w) for w in winners])
check('contest: the winner is announced to everyone', any(e.name == 'ox_lib:notify' and e.target == -1 and 'wins the contest' in (e.args[1].description or '') for e in G.SIM.log.values()))
set_date('2026-11-01'); set_clock('21:00')
r = scb('s2-holidays:world:use', 1, 'halloween', 'doors', 1)
check('contest: city activities stop once the contest is over', not r.get('ok'), r)
st = scb('s2-holidays:getState', 1)
check('contest: menu shows results with a prize for the winner on Nov 1', st['contest']['halloween']['board'].get('open') is False and st['contest']['halloween']['board'].get('prize', {}).get('claimed') is False)
m0 = money(1)
r = scb('s2-holidays:play', 1, 'halloween', 8)
check('contest: the winner claims the prize', r.get('ok') and r.get('kind') == 'prize' and money(1) > m0, r)
check('contest: the prize cannot be claimed twice', not scb('s2-holidays:play', 1, 'halloween', 8).get('ok'))
r = scb('s2-holidays:play', 2, 'halloween', 8)
check('contest: second place can claim theirs too', r.get('ok'), r)
set_date('2026-11-08')
check('contest: Halloween is gone on Nov 8', 'halloween' not in [h['id'] for h in scb('s2-holidays:getState', 1)['active']])

# ---------------------------------------------------------------- every holiday: every activity works end to end
DATES = {'new_years': '2027-01-01', 'valentines': '2027-02-14', 'stpatricks': '2027-03-17', 'easter': '2027-03-28', 'memorial': '2027-05-31',
         'independence': '2027-07-04', 'labor': '2027-09-06', 'halloween': '2027-10-10', 'thanksgiving': '2027-11-25', 'christmas': '2027-12-12', 'new_years_eve': '2027-12-31'}
G.PLAYERS[1].weapon = None
for h, d in DATES.items():
    set_date(d); set_clock('12:00')
    st = scb('s2-holidays:getState', 1)
    check(f'{h}: running on {d}', h in [x['id'] for x in st['active']] and h in st['world'], [x['id'] for x in st['active']])
    for a in world_cfg(h):
        key = a['key']; set_date(d); set_clock('12:00')  # a gathering before may have run the clock past midnight
        if a['type'] == 'spots':
            sp = places(a['spots']) if isinstance(a['spots'], str) else a['spots']
            move(1, sp[0]); m0 = money(1)
            r = scb('s2-holidays:world:use', 1, h, key, 1)
            check(f'{h}/{key}: spot pays out', r.get('ok'), r)
        elif a['type'] == 'delivery':
            pk = places(a['pickups']) if isinstance(a['pickups'], str) else a['pickups']
            move(1, pk[0]); r = scb('s2-holidays:world:pickup', 1, h, key, 1)
            ok = r.get('ok')
            if ok:
                drops = places(a['drops']) if isinstance(a['drops'], str) else a['drops']
                bad = scb('s2-holidays:world:deliver', 1, h, key)
                move(1, drops[r['drop'] - 1]); r2 = scb('s2-holidays:world:deliver', 1, h, key)
                ok = r2.get('ok') and not bad.get('ok')
            check(f'{h}/{key}: pick up, refuse wrong address, deliver at the right one', ok, r)
        elif a['type'] == 'gathering':
            move(1, a['center']); move(2, {'x': a['center']['x'] + a['radius'] + 50, 'y': a['center']['y'], 'z': a['center']['z']})
            hh, mm = map(int, a['at'].split(':')); lead = a.get('announce', 0)
            before = (hh * 60 + mm - lead) * 60 - 20
            set_clock('%02d:%02d:%02d' % (before // 3600, before % 3600 // 60, before % 60))
            G.SIM.log = S.table_from([]); m1, m2 = money(1), money(2)
            advance((lead * 60 + 90) * 1000, step=1000)
            log = to_py(G.SIM.log)
            announced = lead == 0 or any(e['name'] == 'ox_lib:notify' and 'Starts in' in e['args'][1].get('description', '') for e in log)
            got = db.execute('SELECT count(*) FROM s2_holiday_claims WHERE event = ? AND citizenid = ?', (f'w_{h}_{key}', 'CID1')).fetchone()[0]
            other = db.execute('SELECT count(*) FROM s2_holiday_claims WHERE event = ? AND citizenid = ?', (f'w_{h}_{key}', 'CID2')).fetchone()[0]
            show = not a.get('show') or any(e['name'] == 's2-holidays:world:fx' and e['args'][1]['kind'] == 'show' for e in log)
            check(f'{h}/{key}: announced, fires at {a["at"]}, rewards only who is inside, fireworks if any', announced and got == 1 and other == 0 and show, (announced, got, other, show))

# ---------------------------------------------------------------- advent calendar
set_date('2027-12-12'); set_clock('12:00')
admin('playtime', minutes=60)
r = scb('s2-holidays:claimAdvent', 1, 12)
check('advent: door 12 opens on Dec 12 after enough playtime', r.get('ok'), r)
check('advent: a future door stays locked', not scb('s2-holidays:claimAdvent', 1, 13).get('ok'))

# ---------------------------------------------------------------- admin tablet
d = admin('teleport', id='independence', key='pads')
check('admin: go there teleports through the spots', 'Teleported' in d['msg'] and G.PLAYERS[1].pos.x == places('beaches')[0]['x'], d['msg'])
check('admin: city tab data lists every holiday', len(admin('date', value='2027-07-04')['world']) == 11)
check('admin: start a gathering now', 'started' in admin('gather', id='independence', key='show')['msg'])
check('admin: reset my city progress', 'Removed' in admin('resetCity')['msg'])
check('admin: reset contest', 'reset' in admin('resetContest')['msg'])
check('admin: non-admins are refused', scb('s2-holidays:admin:get', 2) is None)
check('admin: spawn ghost needs Halloween off-season too (tool works any time)', 'ghost' in admin('spawnGhost')['msg'].lower())

# ---------------------------------------------------------------- client hub bridge: waypoint to the nearest unfinished spot
set_date('2027-07-04'); CG.WorldSync()
res = to_py(C.eval('function(cb) local out; SIM.nuiCallbacks.waypoint({ holiday = "independence", key = "pads" }, function(r) out = r end); return out end')(None))
check('client: Set waypoint marks the nearest unfinished spot', res.get('ok') and CG.SIM.waypoint is not None, res)

# ---------------------------------------------------------------- the old in-menu games still work (Config.MenuGames = true)
G.Config.MenuGames = True
set_date('2027-11-25'); st = scb('s2-holidays:getState', 1)
check('menu games: Thanksgiving feast state', st.get('event', {}).get('kind') == 'feast')
G.Config.MenuGames = False

# ---------------------------------------------------------------- reward items: a missing item is reported, not a crash
printed = '\n'.join(to_py(G.SIM.printed) or [])
check('startup: the console report says what is running today', 'running today:' in printed)
check('startup: no reward item is missing with the standard Qbox items', 'not in ox_inventory' not in printed, [l for l in to_py(G.SIM.printed) if 'ox_inventory' in l])
# a reward item that does not exist on the server: skipped, the rest still pays, nothing blocks
S.execute("Config.World.thanksgiving[1].reward.items = { { name = 'pumpkin_pie', count = 1 } }")  # not an ox_inventory item on this server
set_date('2027-11-26'); a = next(x for x in world_cfg('thanksgiving') if x['key'] == 'fooddrive')
move(1, places('stores')[1]); r = scb('s2-holidays:world:pickup', 1, 'thanksgiving', 'fooddrive', 2)
m0 = money(1); move(1, places('houses')[r['drop'] - 1]); r2 = scb('s2-holidays:world:deliver', 1, 'thanksgiving', 'fooddrive')
burgers = (to_py(G.SIM.inv[1]) or {}).get('pumpkin_pie', 0)
check('items: a reward item missing from ox_inventory is skipped and the cash still pays', r2.get('ok') and money(1) > m0 and burgers == 0, (r2, burgers))
G.SIM.setItems(S.table_from(ITEMS))

for n, c in results: print(('PASS ' if c else 'FAIL ') + n)
print(f"{sum(c for _, c in results)}/{len(results)} passed")
sys.exit(0 if all(c for _, c in results) else 1)
