Events = {}
local busy = {}

local function cfgFor(id) return Config.Events and Config.Events[id] end
local function cidOf(src) local p = exports.qbx_core:GetPlayer(src); return p and p.PlayerData.citizenid end

local function roll(list)
    local total = 0
    for _, o in ipairs(list) do total = total + o.weight end
    local r = math.random() * total
    for i, o in ipairs(list) do
        r = r - o.weight
        if r <= 0 then return i, o end
    end
    return #list, list[#list]
end

local function canCarry(src, reward)
    for _, it in ipairs(reward.items or {}) do
        if not exports.ox_inventory:CanCarryItem(src, it.name, it.count) then return false end
    end
    return true
end

local function give(src, reward)
    for _, it in ipairs(reward.items or {}) do exports.ox_inventory:AddItem(src, it.name, it.count) end
    if reward.cash then exports.qbx_core:AddMoney(src, 'cash', reward.cash, 'holiday-event') end
end

local function minutesToday(cid, y, m, d)
    return MySQL.scalar.await('SELECT minutes FROM s2_holiday_playtime WHERE citizenid = ? AND day = ?', { cid, Dates.key(y, m, d) }) or 0
end

local function rows(cid, id, y, lo, hi)
    return MySQL.query.await('SELECT slot FROM s2_holiday_claims WHERE citizenid = ? AND event = ? AND year = ? AND slot BETWEEN ? AND ?', { cid, id, y, lo, hi }) or {}
end

local function insert(cid, id, y, slot)
    return MySQL.update.await('INSERT IGNORE INTO s2_holiday_claims (citizenid, event, year, slot) VALUES (?, ?, ?, ?)', { cid, id, y, slot }) > 0
end

local FULL = { ok = false, msg = 'Not enough inventory space for this reward.' }

CreateThread(function()
    MySQL.query.await([[CREATE TABLE IF NOT EXISTS s2_holiday_points (
        citizenid VARCHAR(50) NOT NULL, event VARCHAR(32) NOT NULL, year INT NOT NULL, points INT NOT NULL DEFAULT 0, name VARCHAR(80) NOT NULL DEFAULT '',
        updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (citizenid, event, year), KEY board (event, year, points))]])
    MySQL.query.await([[CREATE TABLE IF NOT EXISTS s2_holiday_winners (
        event VARCHAR(32) NOT NULL, year INT NOT NULL, place INT NOT NULL, citizenid VARCHAR(50) NOT NULL, name VARCHAR(80) NOT NULL,
        points INT NOT NULL, claimed TINYINT NOT NULL DEFAULT 0, PRIMARY KEY (event, year, place))]])
end)

local function nameOf(src)
    local p = exports.qbx_core:GetPlayer(src)
    local ci = p and p.PlayerData.charinfo
    return ci and ('%s %s'):format(ci.firstname or '', ci.lastname or '') or 'Unknown'
end

local function shown(name, fmt)
    if fmt == 'none' then return 'Player' end
    if fmt == 'full' then return name end
    local first, last = tostring(name):match('^(%S+)%s+(.+)$')
    return first and ('%s %s.'):format(first, last:sub(1, 1)) or name
end

-- Seconds until the contest closes (negative once closed). Honors the admin date/clock overrides.
local function contestLeft(cfg, y, m, d)
    local c = cfg.contest
    if not c then return nil end
    local days = Dates.toDays(y, c.endsMonth or 10, c.endsDay or 31) - Dates.toDays(y, m, d)
    return days * 86400 + (c.endsHour or 24) * 3600 - Admin.secondsOfDay()
end

local function addPoints(cid, id, y, name, pts)
    if not pts or pts <= 0 then return end
    MySQL.update.await('INSERT INTO s2_holiday_points (citizenid, event, year, points, name) VALUES (?, ?, ?, ?, ?) ON DUPLICATE KEY UPDATE points = points + VALUES(points), name = VALUES(name)', { cid, id, y, pts, name })
end

-- Top of the board, plus this player's points and rank (ties go to whoever got there first)
local function standing(cfg, id, y, cid)
    local c = cfg.contest
    local out = {}
    for i, r in ipairs(MySQL.query.await('SELECT citizenid, name, points FROM s2_holiday_points WHERE event = ? AND year = ? AND points > 0 ORDER BY points DESC, updated ASC LIMIT ?', { id, y, c.boardSize or 10 }) or {}) do
        out[i] = { rank = i, name = shown(r.name, c.names), points = r.points, you = r.citizenid == cid }
    end
    local pts = MySQL.scalar.await('SELECT points FROM s2_holiday_points WHERE citizenid = ? AND event = ? AND year = ?', { cid, id, y }) or 0
    local rank
    if pts > 0 then
        rank = MySQL.scalar.await([[SELECT COUNT(*) + 1 FROM s2_holiday_points p JOIN s2_holiday_points me ON me.citizenid = ? AND me.event = p.event AND me.year = p.year
            WHERE p.event = ? AND p.year = ? AND (p.points > me.points OR (p.points = me.points AND p.updated < me.updated))]], { cid, id, y })
    end
    return { board = out, points = pts, rank = rank }
end

local function award(src, cid, id, cfg, y, pts, res)
    if not cfg.contest then return end
    addPoints(cid, id, y, nameOf(src), pts)
    res.contest = standing(cfg, id, y, cid)
end

-- Lock in the winners once the contest has closed (idempotent; safe to call from anywhere)
local function finalize(id, cfg, y)
    if (MySQL.scalar.await('SELECT COUNT(*) FROM s2_holiday_winners WHERE event = ? AND year = ?', { id, y }) or 0) > 0 then return end
    local won
    for place, r in ipairs(MySQL.query.await('SELECT citizenid, name, points FROM s2_holiday_points WHERE event = ? AND year = ? AND points > 0 ORDER BY points DESC, updated ASC LIMIT ?', { id, y, #cfg.contest.prizes }) or {}) do
        if MySQL.update.await('INSERT IGNORE INTO s2_holiday_winners (event, year, place, citizenid, name, points) VALUES (?, ?, ?, ?, ?, ?)', { id, y, place, r.citizenid, r.name, r.points }) > 0 and place == 1 then won = r end
    end
    if won then
        TriggerClientEvent('ox_lib:notify', -1, { title = cfg.title, type = 'success', icon = 'ghost', duration = 12000,
            description = ('%s wins the contest with %d points! Winners can claim their prizes from the holiday menu.'):format(shown(won.name, cfg.contest.names), won.points) })
    end
end

local function claimPrize(src, cid, id, cfg, y)
    local row = MySQL.single.await('SELECT place, claimed FROM s2_holiday_winners WHERE event = ? AND year = ? AND citizenid = ?', { id, y, cid })
    if not row then return { ok = false, msg = 'You did not place in the contest.' } end
    if row.claimed == 1 then return { ok = false, msg = 'You already claimed your prize.' } end
    local prize = cfg.contest.prizes[row.place]
    if not prize then return { ok = false, msg = 'No prize for this place.' } end
    if not canCarry(src, prize) then return FULL end
    if MySQL.update.await('UPDATE s2_holiday_winners SET claimed = 1 WHERE event = ? AND year = ? AND place = ? AND claimed = 0', { id, y, row.place }) == 0 then return { ok = false, msg = 'Too slow.' } end
    give(src, prize)
    return { ok = true, kind = 'prize', label = prize.label, msg = prize.msg }
end

CreateThread(function() -- close the contest on time even if nobody has the UI open
    while true do
        Wait(60000)
        for id, cfg in pairs(Config.Events or {}) do
            if cfg.contest then
                local y, m, d = Dates.today()
                local left = contestLeft(cfg, y, m, d)
                if left <= 0 and left > -8 * 86400 then pcall(finalize, id, cfg, y) end
            end
        end
    end
end)

function Events.contestOpen(id)
    local cfg = cfgFor(id)
    if not cfg or not cfg.contest then return true end
    local y, m, d = Dates.today()
    return contestLeft(cfg, y, m, d) > 0
end
Events.nameOf, Events.addPoints = nameOf, addPoints

-- Shared building blocks for other server files (server/world.lua). Same rules: roll, check space, claim, pay, score.
Events.util = { cfgFor = cfgFor, cidOf = cidOf, roll = roll, canCarry = canCarry, give = give, rows = rows, insert = insert, award = award, busy = busy, FULL = FULL }


-- A ghost caught out in the world (verified by server/ghosts.lua before this is called)
function Events.worldCatch(src)
    local cfg, cid = cfgFor('halloween'), cidOf(src)
    local w = cfg and cfg.world
    if not w or not cid then return { ok = false, msg = 'Nothing to catch.' } end
    local y, m, d = Dates.today()
    if cfg.contest and contestLeft(cfg, y, m, d) <= 0 then return { ok = false, msg = 'The contest has ended.' } end
    local base = Dates.toDays(y, m, d) * 100
    local n = #rows(cid, 'halloween_ghost', y, base, base + 99)
    if n >= w.perDay then return { ok = false, msg = 'The ghosts have had enough of you today. Come back tomorrow.' } end
    if not canCarry(src, w) then return FULL end
    if not insert(cid, 'halloween_ghost', y, base + n + 1) then return { ok = false, msg = 'Too slow.' } end
    give(src, w)
    local res = { ok = true, kind = 'ghost', label = w.label, msg = w.msg, points = w.points }
    award(src, cid, 'halloween', cfg, y, w.points, res)
    return res
end

-- World ghosts this player can still catch today (the spawn loop skips players who hit the cap)
function Events.worldLeft(src)
    local cfg, cid = cfgFor('halloween'), cidOf(src)
    local w = cfg and cfg.world
    if not w or not cid then return 0 end
    local y, m, d = Dates.today()
    local base = Dates.toDays(y, m, d) * 100
    return w.perDay - #rows(cid, 'halloween_ghost', y, base, base + 99)
end

-- Contest board for a holiday (Halloween): standings, time left, and once closed the winners and this player's prize.
-- Second value: world ghosts caught today. Used by the city hub and by the in-menu games.
function Events.contest(src, id, y, m, d)
    local cfg, cid = cfgFor(id), cidOf(src)
    if not cfg or not cfg.contest or not cid then return end
    local left = contestLeft(cfg, y, m, d)
    local c = standing(cfg, id, y, cid)
    c.open, c.secondsLeft, c.hint = left > 0, math.max(left, 0), cfg.contest.hint
    if left <= 0 then
        finalize(id, cfg, y)
        c.winners = {}
        for _, r in ipairs(MySQL.query.await('SELECT place, citizenid, name, points, claimed FROM s2_holiday_winners WHERE event = ? AND year = ? ORDER BY place', { id, y }) or {}) do
            c.winners[#c.winners + 1] = { place = r.place, name = shown(r.name, cfg.contest.names), points = r.points, you = r.citizenid == cid }
            if r.citizenid == cid and cfg.contest.prizes[r.place] then c.prize = { place = r.place, label = cfg.contest.prizes[r.place].label, claimed = r.claimed == 1 } end
        end
    end
    local world
    if cfg.world then
        local base = Dates.toDays(y, m, d) * 100
        world = { today = #rows(cid, id .. '_ghost', y, base, base + 99), cap = cfg.world.perDay,
            flashlight = Config.Ghosts and Config.Ghosts.flashlight and Config.Ghosts.flashlight.required == true }
    end
    return c, world
end

-- What the UI shows when it opens. Spot slots are encoded as day*100 + spot*10 + outcome (spot 9 = ghost catch).
function Events.state(src, h, y, m, d)
    local cfg, cid = cfgFor(h.id), cidOf(src)
    if not cfg or not cid then return end
    local out = { id = h.id, kind = cfg.kind, title = cfg.title, style = cfg.style }

    if cfg.kind == 'spots' then
        local base = Dates.toDays(y, m, d) * 100
        local opened, used, ghostDone = {}, 0, false
        for _, r in ipairs(rows(cid, h.id, y, base, base + 99)) do
            local rest = r.slot - base
            local spot, oi = rest // 10, rest % 10
            if spot == 9 then ghostDone = true
            elseif cfg.outcomes[oi] then
                opened[#opened + 1] = { n = spot, kind = cfg.outcomes[oi].kind, label = cfg.outcomes[oi].label }
                used = used + 1
            end
        end
        out.spots, out.picks, out.used, out.opened = cfg.spots, cfg.picks, used, opened
        out.ghost = cfg.ghostCatch ~= nil and not ghostDone

        if cfg.contest then
            out.contest, out.world = Events.contest(src, h.id, y, m, d)
            if not out.contest.open then out.used, out.ghost = out.picks, false end
        end

    elseif cfg.kind == 'feast' then
        local served = {}
        for _, r in ipairs(rows(cid, h.id, y, 1, 7)) do served[r.slot] = true end
        local mins, all = minutesToday(cid, y, m, d), true
        out.dishes = {}
        for i, dish in ipairs(cfg.dishes) do
            if not served[i] then all = false end
            out.dishes[i] = { id = dish.id, label = dish.label, need = dish.need,
                status = served[i] and 'served' or (mins >= dish.need and 'ready' or 'waiting') }
        end
        out.minutes = mins
        out.final = served[7] and 'done' or (all and 'ready' or 'locked')

    elseif cfg.kind == 'countdown' then -- seconds to midnight, only meaningful on Dec 31
        out.secondsLeft = (m == 12 and d == 31) and (86400 - Admin.secondsOfDay()) or 0

    elseif cfg.kind == 'tribute' then
        local day = Dates.toDays(y, m, d)
        out.lit = #rows(cid, h.id, y, day, day) > 0
        out.total = MySQL.scalar.await('SELECT COUNT(*) FROM s2_holiday_claims WHERE event = ? AND year = ?', { h.id, y }) or 0
        out.text, out.button, out.done, out.unit = cfg.text, cfg.button, cfg.done, cfg.unit
        out.reward = cfg.reward and cfg.reward.label or nil
    end
    return out
end

local function play(src, cid, id, cfg, arg, y, m, d)
    if cfg.kind == 'spots' then
        local base = Dates.toDays(y, m, d) * 100
        if arg == 8 and cfg.contest then return claimPrize(src, cid, id, cfg, y) end
        if cfg.contest and contestLeft(cfg, y, m, d) <= 0 then return { ok = false, msg = 'The contest has ended.' } end
        local used, taken, ghostDone = 0, {}, false
        for _, r in ipairs(rows(cid, id, y, base, base + 99)) do
            local spot = (r.slot - base) // 10
            if spot == 9 then ghostDone = true else used = used + 1; taken[spot] = true end
        end

        if arg == 9 then -- ghost catch (once per day)
            local g = cfg.ghostCatch
            if not g then return { ok = false, msg = 'Invalid request.' } end
            if ghostDone then return { ok = false, msg = "You've already caught tonight's ghost." } end
            if not canCarry(src, g) then return FULL end
            if not insert(cid, id, y, base + 99) then return { ok = false, msg = 'Too slow.' } end
            give(src, g)
            local res = { ok = true, kind = 'ghost', label = g.label, msg = g.msg, points = g.points }
            award(src, cid, id, cfg, y, g.points, res)
            return res
        end

        if arg < 1 or arg > cfg.spots or arg ~= math.floor(arg) then return { ok = false, msg = 'Invalid request.' } end
        if taken[arg] then return { ok = false, msg = 'You already opened that one.' } end
        if used >= cfg.picks then return { ok = false, msg = 'No more tries today. Come back tomorrow.' } end

        local oi, o = roll(cfg.outcomes)
        if not canCarry(src, o) then return FULL end
        if not insert(cid, id, y, base + arg * 10 + oi) then return { ok = false, msg = 'Too slow.' } end
        give(src, o)
        local res = { ok = true, kind = o.kind, label = o.label, msg = o.msg, spot = arg, points = o.points }
        award(src, cid, id, cfg, y, o.points, res)
        return res

    elseif cfg.kind == 'feast' then
        local served = {}
        for _, r in ipairs(rows(cid, id, y, 1, 7)) do served[r.slot] = true end
        if arg < 1 or arg > 7 or arg ~= math.floor(arg) then return { ok = false, msg = 'Invalid request.' } end
        if served[arg] then return { ok = false, msg = 'Already done.' } end

        local reward
        if arg == 7 then
            for i = 1, #cfg.dishes do
                if not served[i] then return { ok = false, msg = 'Serve every dish first.' } end
            end
            reward = cfg.finale
        else
            local dish = cfg.dishes[arg]
            local mins = minutesToday(cid, y, m, d)
            if mins < dish.need then return { ok = false, msg = ('Play %d more minutes to serve this dish.'):format(dish.need - mins) } end
            reward = dish
        end
        if not canCarry(src, reward) then return FULL end
        if not insert(cid, id, y, arg) then return { ok = false, msg = 'Too slow.' } end
        give(src, reward)
        return { ok = true, label = reward.label, msg = reward.msg }

    elseif cfg.kind == 'tribute' then -- one candle per player per day; the reward is optional
        local day = Dates.toDays(y, m, d)
        if arg ~= 1 then return { ok = false, msg = 'Invalid request.' } end
        if #rows(cid, id, y, day, day) > 0 then return { ok = false, msg = 'Your candle is already lit.' } end
        if cfg.reward and not canCarry(src, cfg.reward) then return FULL end
        if not insert(cid, id, y, day) then return { ok = false, msg = 'Too slow.' } end
        if cfg.reward then give(src, cfg.reward) end
        return { ok = true, label = cfg.label or 'A candle burns for them', msg = cfg.thanks or 'Thank you.', kind = cfg.style == 'pledge' and 'pledge' or 'candle' }
    end
    return { ok = false, msg = 'Invalid request.' }
end

lib.callback.register('s2-holidays:play', function(src, id, arg)
    local cfg, cid = cfgFor(id), cidOf(src)
    arg = tonumber(arg)
    if not cfg or not cid or not arg then return { ok = false, msg = 'Invalid request.' } end

    local y, m, d = Dates.today()
    local live = false
    for _, h in ipairs((Dates.evaluate(Dates.toDays(y, m, d), y))) do if h.id == id then live = true end end
    if not live then return { ok = false, msg = 'This event is not running.' } end

    if busy[cid] then return { ok = false, msg = 'One moment...' } end
    busy[cid] = true
    local ok, res = pcall(play, src, cid, id, cfg, arg, y, m, d)
    busy[cid] = nil
    if not ok then print(('[s2-holidays] %s'):format(res)); return { ok = false, msg = 'Something went wrong.' } end
    return res
end)
