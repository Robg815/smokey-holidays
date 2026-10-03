local ADV = Config.Advent

CreateThread(function()
    MySQL.query.await([[CREATE TABLE IF NOT EXISTS s2_holiday_playtime (
        citizenid VARCHAR(50) NOT NULL, day VARCHAR(10) NOT NULL, minutes INT NOT NULL DEFAULT 0,
        PRIMARY KEY (citizenid, day))]])
    MySQL.query.await([[CREATE TABLE IF NOT EXISTS s2_holiday_claims (
        citizenid VARCHAR(50) NOT NULL, event VARCHAR(32) NOT NULL, year INT NOT NULL, slot INT NOT NULL,
        claimed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (citizenid, event, year, slot))]])
end)

local function requiredFor(day)
    return (ADV.overrides and ADV.overrides[day]) or ADV.requiredMinutes
end

local function adventStatus(y, m, d)
    if not ADV.enabled then return end
    local current = Dates.toDays(y, m, d) - Dates.toDays(y, ADV.startMonth, ADV.startDay) + 1
    return { year = y, current = current, active = current >= 1 and current <= ADV.days }
end

-- Count a minute of playtime for everyone online while the calendar is running
CreateThread(function()
    while true do
        Wait(60000)
        local y, m, d = Dates.today()
        local st = adventStatus(y, m, d)
        local act = Dates.evaluate(Dates.toDays(y, m, d), y)
        if (st and st.active) or (act and #act > 0) then
            local key = Dates.key(y, m, d)
            for _, p in pairs(exports.qbx_core:GetQBPlayers()) do
                MySQL.update('INSERT INTO s2_holiday_playtime (citizenid, day, minutes) VALUES (?, ?, 1) ON DUPLICATE KEY UPDATE minutes = minutes + 1',
                    { p.PlayerData.citizenid, key })
            end
        end
    end
end)

lib.callback.register('s2-holidays:getState', function(src)
    local y, m, d = Dates.today()
    local active, upcoming = Dates.evaluate(Dates.toDays(y, m, d), y)
    local state = {
        date = Dates.key(y, m, d),
        active = active,
        upcoming = { table.unpack(upcoming, 1, 4) },
        theme = (active[1] and active[1].theme) or (upcoming[1] and upcoming[1].theme) or Config.Themes.default,
    }

    local st = adventStatus(y, m, d)
    local player = exports.qbx_core:GetPlayer(src)
    if st and st.active and player then
        local cid = player.PlayerData.citizenid
        local minutes = MySQL.scalar.await('SELECT minutes FROM s2_holiday_playtime WHERE citizenid = ? AND day = ?', { cid, Dates.key(y, m, d) }) or 0
        local claimed = {}
        for _, row in ipairs(MySQL.query.await('SELECT slot FROM s2_holiday_claims WHERE citizenid = ? AND event = ? AND year = ?', { cid, 'advent', st.year }) or {}) do
            claimed[row.slot] = true
        end

        local doors = {}
        for i = 1, ADV.days do
            local status
            if claimed[i] then status = 'claimed'
            elseif i > st.current then status = 'locked'
            elseif i < st.current and not ADV.allowCatchUp then status = 'missed'
            else status = minutes >= requiredFor(i) and 'ready' or 'waiting' end
            doors[i] = { day = i, status = status, need = requiredFor(i), icon = ADV.icons and ADV.icons[i], image = ADV.images and ADV.images[i], label = claimed[i] and ADV.rewards[i].label or nil }
        end
        state.advent = { skin = ADV.skin, layout = ADV.layout, current = st.current, days = ADV.days, minutes = minutes, doors = doors }
    end
    -- City activities (the default) and contest boards for every running holiday
    state.world, state.contest = World.state(src), {}
    for _, h in ipairs(active) do
        local c, ghosts = Events.contest(src, h.id, y, m, d)
        if c then state.contest[h.id] = { board = c, ghosts = ghosts } end
    end
    if Config.MenuGames then -- the old in-menu mini games, one per running holiday, switchable when two overlap
        state.events = {}
        for _, h in ipairs(active) do
            if Config.Events and Config.Events[h.id] then state.events[h.id] = Events.state(src, h, y, m, d) end
        end
        if not state.advent and active[1] then state.event = state.events[active[1].id] end
    end
    return state
end)

lib.callback.register('s2-holidays:claimAdvent', function(src, day)
    day = tonumber(day)
    local player = exports.qbx_core:GetPlayer(src)
    if not player or not day then return { ok = false, msg = 'Invalid request.' } end

    local y, m, d = Dates.today()
    local st = adventStatus(y, m, d)
    if not st or not st.active then return { ok = false, msg = 'The advent calendar is closed.' } end
    if day < 1 or day > ADV.days or day > st.current then return { ok = false, msg = 'That door is still locked.' } end
    if day < st.current and not ADV.allowCatchUp then return { ok = false, msg = 'That door has passed.' } end

    local cid = player.PlayerData.citizenid
    local minutes = MySQL.scalar.await('SELECT minutes FROM s2_holiday_playtime WHERE citizenid = ? AND day = ?', { cid, Dates.key(y, m, d) }) or 0
    local need = requiredFor(day)
    if minutes < need then
        return { ok = false, msg = ('Play %d more minutes today to open this door.'):format(need - minutes) }
    end

    local reward = ADV.rewards[day]
    if not Events.util.canCarry(src, reward) then return { ok = false, msg = 'Not enough inventory space for this reward.' } end

    -- INSERT IGNORE makes the claim atomic: a double-click can never pay out twice
    local inserted = MySQL.update.await('INSERT IGNORE INTO s2_holiday_claims (citizenid, event, year, slot) VALUES (?, ?, ?, ?)', { cid, 'advent', st.year, day })
    if inserted == 0 then return { ok = false, msg = 'You already opened this door.' } end

    Events.util.give(src, reward)

    return { ok = true, label = reward.label, day = day }
end)

-- Startup report in the server console: what is running today, and any reward items missing from ox_inventory
CreateThread(function()
    Wait(3000)
    local names, missing = {}, {}
    local function scan(r)
        if type(r) ~= 'table' then return end
        for _, it in ipairs(r.items or {}) do names[it.name] = true end
    end
    for _, r in pairs(ADV.rewards or {}) do scan(r) end
    for _, cfg in pairs(Config.Events or {}) do
        for _, o in ipairs(cfg.outcomes or {}) do scan(o) end
        for _, o in ipairs(cfg.dishes or {}) do scan(o) end
        scan(cfg.finale); scan(cfg.ghostCatch); scan(cfg.world); scan(cfg.reward)
        for _, o in ipairs(cfg.contest and cfg.contest.prizes or {}) do scan(o) end
    end
    for _, acts in pairs(Config.World or {}) do
        for _, a in ipairs(acts) do
            scan(a.reward)
            if type(a.outcomes) == 'table' then for _, o in ipairs(a.outcomes) do scan(o) end end
        end
    end
    for name in pairs(names) do if not Events.util.itemExists(name) then missing[#missing + 1] = name end end
    table.sort(missing)
    local y, m, d = Dates.today()
    local active = {}
    for _, h in ipairs((Dates.evaluate(Dates.toDays(y, m, d), y))) do active[#active + 1] = h.label end
    print(('[s2-holidays] %s: running today: %s'):format(Dates.key(y, m, d), #active > 0 and table.concat(active, ', ') or 'nothing'))
    if #missing > 0 then
        print(('^3[s2-holidays] These reward items are not in ox_inventory and will be skipped (cash still pays): %s^7'):format(table.concat(missing, ', ')))
    end
end)
