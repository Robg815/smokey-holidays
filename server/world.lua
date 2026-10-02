-- City activities from config_world.lua. The server owns every rule: what is running, where the player is,
-- what they already did today, the daily caps and what they get. Clients only draw props, markers and prompts.
-- Claims: event key 'w_<holiday>_<activity>', slot = day * 1000 + spot index (spots), + n (deliveries), + 0 (gatherings).
World = { delivering = {}, fired = {}, fxLast = {}, tp = {} }

local U = Events.util
local W = Config.World or {}

local function places(v) return type(v) == 'string' and (Config.Places[v] or {}) or (v or {}) end
local function claimKey(h, a) return ('w_%s_%s'):format(h, a.key) end
local function flat(a, b) local dx, dy = a.x - b.x, a.y - b.y; return math.sqrt(dx * dx + dy * dy) end -- 2D, so a slightly wrong z never matters
local function secs(hhmm) local h, m = tostring(hhmm or '0:0'):match('^(%d+):(%d+)$'); return (tonumber(h) or 0) * 3600 + (tonumber(m) or 0) * 60 end
local function posOf(src) local ped = GetPlayerPed(src); return ped and ped ~= 0 and GetEntityCoords(ped) or nil end

function World.find(h, key)
    for _, a in ipairs(W[h] or {}) do if a.key == key then return a end end
end
World.places = places

local function live() -- running holidays (admin overrides apply) whose contest, if any, is still open
    local y, m, d = Dates.today()
    local set = {}
    for _, h in ipairs((Dates.evaluate(Dates.toDays(y, m, d), y))) do
        if W[h.id] and Events.contestOpen(h.id) then set[h.id] = true end
    end
    return set, y, m, d
end

local function today(cid, h, a, y, m, d)
    local base = Dates.toDays(y, m, d) * 1000
    return U.rows(cid, claimKey(h, a), y, base, base + 999), base
end

local function rewardFor(h, a)
    local list = a.outcomes == 'event' and Config.Events[h] and Config.Events[h].outcomes or a.outcomes
    if type(list) == 'table' then local _, o = U.roll(list); return o end
    return a.reward or {}
end

local function pay(src, cid, h, y, o, res)
    U.give(src, o)
    local cfg = Config.Events[h]
    if cfg and cfg.contest and o.points then U.award(src, cid, h, cfg, y, o.points, res) end
    res.points = o.points
    return res
end

local function result(o, extra)
    local r = { ok = true, kind = o.kind or 'gift', label = o.label or 'Reward', msg = o.msg }
    for k, v in pairs(extra or {}) do r[k] = v end
    return r
end

-- Fireworks and other effects, drawn by every client within range
function World.fx(kind, c, duration)
    TriggerClientEvent('s2-holidays:world:fx', -1, { kind = kind, x = c.x, y = c.y, z = c.z, duration = duration })
end

local function useSpot(src, cid, h, a, idx, y, m, d)
    local spot, me = places(a.spots)[idx], posOf(src)
    if not spot or not me then return { ok = false, msg = 'Invalid request.' } end
    if flat(me, spot) > (a.distance or 2.0) + 6.0 then return { ok = false, msg = 'Get closer.' } end
    local rows, base = today(cid, h, a, y, m, d)
    for _, r in ipairs(rows) do
        if r.slot == base + idx then return { ok = false, msg = 'You already did this one today.', done = true } end
    end
    if #rows >= (a.perDay or 1) then return { ok = false, msg = "That's all for today. Come back tomorrow." } end
    local o = rewardFor(h, a)
    if not U.canCarry(src, o) then return U.FULL end
    if not U.insert(cid, claimKey(h, a), y, base + idx) then return { ok = false, msg = 'Too slow.' } end
    local res = pay(src, cid, h, y, o, result(o, { today = #rows + 1, cap = a.perDay, idx = idx }))
    if a.effect == 'fireworks' and (World.fxLast[src] or 0) + 8 <= os.time() then
        World.fxLast[src] = os.time()
        World.fx('burst', spot)
    end
    return res
end

local function pickup(src, cid, h, a, idx, y, m, d)
    local p, me = places(a.pickups)[idx], posOf(src)
    if not p or not me then return { ok = false, msg = 'Invalid request.' } end
    if World.delivering[cid] then return { ok = false, msg = 'You are already carrying a delivery.' } end
    if flat(me, p) > 8.0 then return { ok = false, msg = 'Get closer.' } end
    if #today(cid, h, a, y, m, d) >= (a.perDay or 1) then return { ok = false, msg = "That's all the deliveries for today." } end
    local drops, options = places(a.drops), {}
    for i, c in ipairs(drops) do if flat(c, p) > 150.0 then options[#options + 1] = i end end -- no next-door drops
    if #options == 0 then for i in ipairs(drops) do options[#options + 1] = i end end
    if #options == 0 then return { ok = false, msg = 'Nowhere to deliver to.' } end
    local di, limit = options[math.random(#options)], a.timeLimit or 600
    World.delivering[cid] = { h = h, key = a.key, drop = di, expires = os.time() + limit }
    return { ok = true, drop = di, timeLimit = limit }
end

local function deliver(src, cid, h, a, y, m, d)
    local job, me = World.delivering[cid], posOf(src)
    if not job or job.h ~= h or job.key ~= a.key then return { ok = false, final = true, msg = 'You are not carrying anything.' } end
    if os.time() > job.expires then World.delivering[cid] = nil; return { ok = false, final = true, msg = 'Too late. The delivery expired.' } end
    local drop = places(a.drops)[job.drop]
    if not me or not drop or flat(me, drop) > 10.0 then return { ok = false, msg = 'This is not the address.' } end
    local rows, base = today(cid, h, a, y, m, d)
    if #rows >= (a.perDay or 1) then World.delivering[cid] = nil; return { ok = false, final = true, msg = "That's all the deliveries for today." } end
    local o = rewardFor(h, a)
    if not U.canCarry(src, o) then return U.FULL end
    if not U.insert(cid, claimKey(h, a), y, base + #rows + 1) then return { ok = false, msg = 'Too slow.' } end
    World.delivering[cid] = nil
    return pay(src, cid, h, y, o, result(o, { today = #rows + 1, cap = a.perDay, final = true }))
end

-- Reward everyone inside a gathering's area right now (also the admin tablet's "Start now")
function World.fire(h, a)
    local y, m, d = Dates.today()
    local base, n, o = Dates.toDays(y, m, d) * 1000, 0, a.reward or {}
    for src, p in pairs(exports.qbx_core:GetQBPlayers()) do
        local me = posOf(src)
        if me and flat(me, a.center) <= a.radius and U.canCarry(src, o) and U.insert(p.PlayerData.citizenid, claimKey(h, a), y, base) then
            local res = pay(src, p.PlayerData.citizenid, h, y, o, result(o))
            TriggerClientEvent('s2-holidays:world:done', src, h, a.key, res)
            n = n + 1
        end
    end
    if a.show then World.fx('show', a.show.center or a.center, a.show.duration) end
    TriggerClientEvent('ox_lib:notify', -1, { title = a.title, type = 'success', icon = 'champagne-glasses', duration = 10000,
        description = n > 0 and ('%d %s there. %s'):format(n, n == 1 and 'player was' or 'players were', a.reward and a.reward.msg or '') or (a.reward and a.reward.msg or 'It is happening now.') })
    return n
end

CreateThread(function() -- gatherings: announce ahead of time, then fire once per day at the set time (server clock, admin clock applies)
    while true do
        Wait(5000)
        local set, y, m, d = live()
        local day, now = Dates.key(y, m, d), Admin.secondsOfDay()
        for h in pairs(set) do
            for _, a in ipairs(W[h]) do
                if a.type == 'gathering' then
                    local at, tag, lead = secs(a.at), h .. ':' .. a.key .. ':' .. day, (a.announce or 0) * 60
                    if lead > 0 and now >= at - lead and now < at - lead + 30 and not World.fired['pre:' .. tag] then
                        World.fired['pre:' .. tag] = true
                        TriggerClientEvent('ox_lib:notify', -1, { title = a.title, type = 'inform', icon = 'bullhorn', duration = 12000,
                            description = ('Starts in %d minutes. %s'):format(a.announce, a.desc) })
                    end
                    if now >= at and now < at + 60 and not World.fired[tag] then
                        World.fired[tag] = true
                        local ok, err = pcall(World.fire, h, a)
                        if not ok then print(('[s2-holidays] gathering %s: %s'):format(tag, err)) end
                    end
                end
            end
        end
    end
end)

CreateThread(function() -- forget expired deliveries
    while true do
        Wait(60000)
        local now = os.time()
        for cid, job in pairs(World.delivering) do
            if now > job.expires + 30 then World.delivering[cid] = nil end
        end
    end
end)

-- Progress for every running holiday's activities: used by the client (props, blips) and the menu hub
function World.state(src)
    local cid = U.cidOf(src)
    if not cid then return {} end
    local set, y, m, d = live()
    local now, out = Admin.secondsOfDay(), {}
    for h in pairs(set) do
        local acts = {}
        for _, a in ipairs(W[h]) do
            local rows, base = today(cid, h, a, y, m, d)
            local e = { key = a.key, type = a.type, today = #rows, cap = a.perDay or 1, title = a.title, desc = a.desc, icon = a.icon, at = a.at, timeLimit = a.timeLimit }
            if a.type == 'spots' then
                e.done, e.total = {}, #places(a.spots)
                for _, r in ipairs(rows) do e.done[#e.done + 1] = r.slot - base end
            elseif a.type == 'delivery' then
                local job = World.delivering[cid]
                if job and job.h == h and job.key == a.key then e.job = { drop = job.drop, left = job.expires - os.time() } end
            elseif a.type == 'gathering' then
                e.cap, e.startsIn = 1, secs(a.at) - now
            end
            acts[#acts + 1] = e
        end
        out[h] = acts
    end
    return out
end

local function guarded(fn)
    return function(src, h, key, idx)
        local cid = U.cidOf(src)
        if type(h) ~= 'string' or type(key) ~= 'string' or not cid then return { ok = false, msg = 'Invalid request.' } end
        local a = World.find(h, key)
        local set, y, m, d = live()
        if not a or not set[h] then return { ok = false, final = true, msg = 'This activity is not running.' } end
        if U.busy[cid] then return { ok = false, msg = 'One moment...' } end
        U.busy[cid] = true
        local ok, res = pcall(fn, src, cid, h, a, tonumber(idx), y, m, d)
        U.busy[cid] = nil
        if not ok then print(('[s2-holidays] world: %s'):format(res)); return { ok = false, msg = 'Something went wrong.' } end
        return res
    end
end

lib.callback.register('s2-holidays:world:state', function(src) return World.state(src) end)
lib.callback.register('s2-holidays:world:use', guarded(function(src, cid, h, a, idx, y, m, d)
    if a.type ~= 'spots' or not idx then return { ok = false, msg = 'Invalid request.' } end
    return useSpot(src, cid, h, a, idx, y, m, d)
end))
lib.callback.register('s2-holidays:world:pickup', guarded(function(src, cid, h, a, idx, y, m, d)
    if a.type ~= 'delivery' or not idx then return { ok = false, msg = 'Invalid request.' } end
    return pickup(src, cid, h, a, idx, y, m, d)
end))
lib.callback.register('s2-holidays:world:deliver', guarded(function(src, cid, h, a, _, y, m, d)
    if a.type ~= 'delivery' then return { ok = false, msg = 'Invalid request.' } end
    return deliver(src, cid, h, a, y, m, d)
end))
lib.callback.register('s2-holidays:world:cancel', function(src)
    local cid = U.cidOf(src)
    if cid then World.delivering[cid] = nil end
    return true
end)
