-- Admin / testing layer. Wraps Dates.today and Dates.evaluate so every other script (state, claims,
-- playtime, events) sees the overrides without changes. Permission: ACE `s2-holidays.admin` or qbx_core admin.
Admin = { disabled = {}, forced = {}, date = nil, clock = nil }

local KVP = 's2-holidays:admin'
local origToday, origEvaluate = Dates.today, Dates.evaluate

local function save()
    local ids = {}
    for id in pairs(Admin.disabled) do ids[#ids + 1] = id end
    SetResourceKvp(KVP, json.encode({ disabled = ids, advent = Config.Advent and Config.Advent.enabled }))
end

do -- restore what was saved (only enabled/disabled and the advent switch persist; test overrides never do)
    local ok, saved = pcall(json.decode, GetResourceKvpString(KVP) or '{}')
    if ok and type(saved) == 'table' then
        for _, id in ipairs(saved.disabled or {}) do Admin.disabled[id] = true end
        if saved.advent ~= nil and Config.Advent then Config.Advent.enabled = saved.advent end
    end
end

function Dates.today()
    if Admin.date then return Admin.date.y, Admin.date.m, Admin.date.d end
    return origToday()
end

local function holidayCfg(id)
    for _, h in ipairs(Config.Holidays) do if h.id == id then return h end end
end

function Dates.evaluate(...)
    local active, upcoming = origEvaluate(...)
    local a, u, seen = {}, {}, {}
    for _, h in ipairs(active or {}) do
        if not Admin.disabled[h.id] then a[#a + 1] = h; seen[h.id] = true end
    end
    for _, h in ipairs(upcoming or {}) do
        if not Admin.disabled[h.id] then u[#u + 1] = h end
    end
    for id in pairs(Admin.forced) do
        local c = holidayCfg(id)
        if c and not Admin.disabled[id] and not seen[id] then
            local y, m, d = Dates.today()
            table.insert(a, 1, { id = id, label = c.label, blurb = c.blurb, daysUntil = 0, date = Dates.key(y, m, d),
                theme = Config.Themes[c.theme] or Config.Themes.default })
        end
    end
    return a, u
end

function Admin.secondsOfDay()
    if Admin.clock then return (Admin.clock.secs + (os.time() - Admin.clock.base)) % 86400 end
    local t = os.date(Config.UtcOffset and '!*t' or '*t', os.time() + (Config.UtcOffset or 0) * 3600)
    return t.hour * 3600 + t.min * 60 + t.sec
end

local function isAdmin(src)
    if IsPlayerAceAllowed(src, 's2-holidays.admin') then return true end
    local ok, res = pcall(function() return exports.qbx_core:HasPermission(src, 'admin') end)
    return ok and res == true
end

local function build()
    local y, m, d = Dates.today()
    local ry, rm, rd = origToday()
    local natural = {}
    for _, h in ipairs((origEvaluate(Dates.toDays(y, m, d), y)) or {}) do natural[h.id] = true end
    local list = {}
    for _, h in ipairs(Config.Holidays) do
        local ev = Config.Events and Config.Events[h.id]
        list[#list + 1] = {
            id = h.id, label = h.label, natural = natural[h.id] == true,
            kind = h.id == 'christmas' and 'advent' or (ev and (ev.style and (ev.kind .. ':' .. ev.style) or ev.kind)) or 'observance',
            enabled = not Admin.disabled[h.id], forced = Admin.forced[h.id] == true,
        }
    end
    local s = Admin.clock and Admin.secondsOfDay()
    return {
        year = y, date = Dates.key(y, m, d), real = Dates.key(ry, rm, rd), override = Admin.date ~= nil,
        clock = s and ('%02d:%02d:%02d'):format(s // 3600, s % 3600 // 60, s % 60) or nil,
        advent = Config.Advent and Config.Advent.enabled == true, holidays = list,
        ghosts = Ghosts and Ghosts.count or 0, ghostMax = Config.Ghosts and Config.Ghosts.maxActive or 0,
        doors = Config.Places and #Config.Places.houses or 0,
        flashlight = Config.Ghosts and Config.Ghosts.flashlight and Config.Ghosts.flashlight.required == true,
        world = (function()
            local out = {}
            for _, h in ipairs(Config.Holidays) do
                local acts = {}
                for _, a in ipairs((Config.World or {})[h.id] or {}) do
                    local n = a.type == 'spots' and #World.places(a.spots) or a.type == 'delivery' and #World.places(a.pickups) or 1
                    acts[#acts + 1] = { key = a.key, title = a.title, type = a.type, count = n, at = a.at }
                end
                if #acts > 0 then out[#out + 1] = { id = h.id, label = h.label, live = natural[h.id] == true or Admin.forced[h.id] == true, activities = acts } end
            end
            return out
        end)(),
    }
end

local function validDate(str)
    local y, m, d = tostring(str or ''):match('^(%d%d%d%d)-(%d%d)-(%d%d)$')
    y, m, d = tonumber(y), tonumber(m), tonumber(d)
    if not y or y < 1971 or y > 2100 then return end
    local t = os.time({ year = y, month = m, day = d, hour = 12 })
    if not t or os.date('%Y-%m-%d', t) ~= ('%04d-%02d-%02d'):format(y, m, d) then return end
    return { y = y, m = m, d = d }
end

local actions = {}

function actions.toggle(_, d)
    if not holidayCfg(d.id) then return 'Unknown holiday.' end
    Admin.disabled[d.id] = (d.enabled == false) or nil
    if d.enabled == false then Admin.forced[d.id] = nil end
    save()
    return d.enabled == false and 'Holiday disabled.' or 'Holiday enabled.'
end

function actions.force(_, d)
    if not holidayCfg(d.id) then return 'Unknown holiday.' end
    Admin.forced[d.id] = d.on and true or nil
    return d.on and 'Forced on until restart.' or 'No longer forced.'
end

function actions.date(_, d)
    if d.value == nil or d.value == '' then Admin.date = nil; return 'Using the real date.' end
    local v = validDate(d.value)
    if not v then return 'Use a valid date (YYYY-MM-DD).' end
    Admin.date = v
    return 'Date override set.'
end

function actions.clock(_, d)
    if d.value == nil or d.value == '' then Admin.clock = nil; return 'Using real time.' end
    local h, m, s = tostring(d.value):match('^(%d%d?):(%d%d):?(%d?%d?)$')
    h, m, s = tonumber(h), tonumber(m), tonumber(s) or 0
    if not h or h > 23 or m > 59 or s > 59 then return 'Use HH:MM or HH:MM:SS.' end
    Admin.clock = { secs = h * 3600 + m * 60 + s, base = os.time() }
    return 'Fake clock running.'
end

function actions.resetClaims(src, d)
    local p = exports.qbx_core:GetPlayer(src)
    if not p or not holidayCfg(d.id) then return 'Nothing to reset.' end
    local y = Dates.today()
    local n = MySQL.update.await('DELETE FROM s2_holiday_claims WHERE citizenid = ? AND year = ? AND event IN (?, ?, ?, ?)',
        { p.PlayerData.citizenid, y, d.id, d.id == 'christmas' and 'advent' or d.id, d.id .. '_door', d.id .. '_ghost' })
    return ('Removed %d of your claims.'):format(n or 0)
end

function actions.playtime(src, d)
    local p = exports.qbx_core:GetPlayer(src)
    local mins = math.floor(tonumber(d.minutes) or 0)
    if not p or mins < 1 or mins > 600 then return 'Nothing added.' end
    local y, m, day = Dates.today()
    MySQL.update.await('INSERT INTO s2_holiday_playtime (citizenid, day, minutes) VALUES (?, ?, ?) ON DUPLICATE KEY UPDATE minutes = minutes + VALUES(minutes)',
        { p.PlayerData.citizenid, Dates.key(y, m, day), mins })
    return ('Added %d minutes of playtime for today.'):format(mins)
end

function actions.advent(_, d)
    if not Config.Advent then return 'Advent is not configured.' end
    Config.Advent.enabled = d.enabled == true
    save()
    return Config.Advent.enabled and 'Advent calendar enabled.' or 'Advent calendar disabled.'
end

function actions.spawnGhost(src)
    if not Ghosts then return 'Ghosts are not loaded.' end
    if Ghosts.byPlayer[src] then return 'You already have a ghost nearby.' end
    if Ghosts.count >= Config.Ghosts.maxActive then return 'The ghost cap is reached. Clear some first.' end
    return Ghosts.spawnFor(src, true) and 'A ghost is on its way. Look around you.' or 'Could not spawn a ghost here.'
end

function actions.clearGhosts()
    if not Ghosts then return 'Ghosts are not loaded.' end
    local n = Ghosts.count
    Ghosts.clear()
    return ('Cleared %d ghosts.'):format(n)
end

function actions.addPoints(src, d)
    local p = exports.qbx_core:GetPlayer(src)
    local pts = math.floor(tonumber(d.points) or 100)
    if not p or pts < 1 or pts > 10000 then return 'Nothing added.' end
    Events.addPoints(p.PlayerData.citizenid, 'halloween', (Dates.today()), Events.nameOf(src), pts)
    return ('Added %d Halloween points to you.'):format(pts)
end

function actions.resetContest()
    local y = Dates.today()
    local a = MySQL.update.await('DELETE FROM s2_holiday_points WHERE event = ? AND year = ?', { 'halloween', y }) or 0
    MySQL.update.await('DELETE FROM s2_holiday_winners WHERE event = ? AND year = ?', { 'halloween', y })
    MySQL.update.await('DELETE FROM s2_holiday_claims WHERE event IN (?, ?) AND year = ?', { 'halloween_ghost', 'w_halloween_doors', y })
    return ('Halloween contest reset (%d scores removed).'):format(a)
end

-- City tab: go to the next spot of an activity (cycles), start a gathering now, reset your own city progress
function actions.teleport(src, d)
    local a = World.find(d.id, d.key)
    if not a then return 'Unknown activity.' end
    local list = a.type == 'spots' and World.places(a.spots) or a.type == 'delivery' and World.places(a.pickups) or { a.center }
    if #list == 0 then return 'No positions configured.' end
    local k = d.id .. ':' .. d.key .. ':' .. src
    local i = (World.tp[k] or 0) % #list + 1
    World.tp[k] = i
    local c = list[i]
    SetEntityCoords(GetPlayerPed(src), c.x, c.y, c.z + 1.0, false, false, false, false)
    return ('Teleported to %s, %d of %d.'):format(a.title, i, #list)
end

function actions.gather(_, d)
    local a = World.find(d.id, d.key)
    if not a or a.type ~= 'gathering' then return 'Not a gathering.' end
    return ('%s started: %d players rewarded.'):format(a.title, World.fire(d.id, a))
end

function actions.resetCity(src)
    local p = exports.qbx_core:GetPlayer(src)
    if not p then return 'Nothing to reset.' end
    local n = MySQL.update.await("DELETE FROM s2_holiday_claims WHERE citizenid = ? AND year = ? AND LEFT(event, 2) = 'w_'", { p.PlayerData.citizenid, (Dates.today()) })
    World.delivering[p.PlayerData.citizenid] = nil
    TriggerClientEvent('s2-holidays:world:resync', src)
    return ('Removed %d of your city activity claims.'):format(n or 0)
end

lib.callback.register('s2-holidays:admin:get', function(src)
    if not isAdmin(src) then return nil end
    return build()
end)

lib.callback.register('s2-holidays:admin:do', function(src, action, data)
    if not isAdmin(src) or type(data) ~= 'table' then return nil end
    local fn = actions[action]
    local msg = fn and fn(src, data) or 'Unknown action.'
    if action == 'date' or action == 'force' or action == 'toggle' then TriggerClientEvent('s2-holidays:world:resync', -1) end -- running holidays changed
    print(('[s2-holidays] admin %s (%s) -> %s'):format(GetPlayerName(src) or src, tostring(action), msg))
    local out = build()
    out.msg = msg
    return out
end)
