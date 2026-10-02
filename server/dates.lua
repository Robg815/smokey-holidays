-- Date rules. Pure Lua (no os.time for date math) so it works for any year.
-- server/admin.lua wraps Dates.today and Dates.evaluate at runtime; event logic must call those, not os.date.
Dates = {}

-- Days since 1970-01-01 for a proleptic Gregorian date (Howard Hinnant's days_from_civil)
function Dates.toDays(y, m, d)
    y = m <= 2 and y - 1 or y
    local era = (y >= 0 and y or y - 399) // 400
    local yoe = y - era * 400
    local doy = (153 * (m + (m > 2 and -3 or 9)) + 2) // 5 + d - 1
    local doe = yoe * 365 + yoe // 4 - yoe // 100 + doy
    return era * 146097 + doe - 719468
end

function Dates.fromDays(z)
    z = z + 719468
    local era = (z >= 0 and z or z - 146096) // 146097
    local doe = z - era * 146097
    local yoe = (doe - doe // 1460 + doe // 36524 - doe // 146096) // 365
    local doy = doe - (365 * yoe + yoe // 4 - yoe // 100)
    local mp = (5 * doy + 2) // 153
    local d = doy - (153 * mp + 2) // 5 + 1
    local m = mp < 10 and mp + 3 or mp - 9
    return yoe + era * 400 + (m <= 2 and 1 or 0), m, d
end

function Dates.key(y, m, d) return ('%04d-%02d-%02d'):format(y, m, d) end

local function weekday(days) return (days + 4) % 7 end -- 0 = Sunday; 1970-01-01 was a Thursday

local function lastDay(y, m)
    return m == 12 and 31 or Dates.toDays(y, m + 1, 1) - Dates.toDays(y, m, 1)
end

local function easter(y) -- anonymous Gregorian computus
    local a, b, c = y % 19, y // 100, y % 100
    local d, e = b // 4, b % 4
    local f = (b + 8) // 25
    local g = (b - f + 1) // 3
    local h = (19 * a + b - d - g + 15) % 30
    local i, k = c // 4, c % 4
    local l = (32 + 2 * e + 2 * i - h - k) % 7
    local m = (a + 11 * h + 22 * l) // 451
    local month = (h + l - 7 * m + 114) // 31
    return Dates.toDays(y, month, (h + l - 7 * m + 114) % 31 + 1)
end

-- Day number of a rule in year y, plus the observed day for federal fixed-date holidays on a weekend
local function resolve(rule, y, federal)
    local t = rule.type
    if t == 'fixed' then
        local day = Dates.toDays(y, rule.month, rule.day)
        local obs = day
        if federal and Config.UseObservedDates then
            local wd = weekday(day)
            if wd == 6 then obs = day - 1 elseif wd == 0 then obs = day + 1 end
        end
        return day, obs
    elseif t == 'nth' then
        local first = Dates.toDays(y, rule.month, 1)
        local day = first + (rule.weekday - weekday(first)) % 7 + (rule.n - 1) * 7
        return day, day
    elseif t == 'last' then
        local last = Dates.toDays(y, rule.month, lastDay(y, rule.month))
        local day = last - (weekday(last) - rule.weekday) % 7
        return day, day
    elseif t == 'easter' then
        local day = easter(y) + (rule.offset or 0)
        return day, day
    end
end

local function parseDate(s)
    local y, m, d = tostring(s or ''):match('^(%d%d%d%d)-(%d%d)-(%d%d)$')
    if y then return tonumber(y), tonumber(m), tonumber(d) end
end

function Dates.today()
    local y, m, d = parseDate(Config.DebugDate)
    if y then return y, m, d end
    local t = Config.UtcOffset and os.date('!*t', os.time() + Config.UtcOffset * 3600) or os.date('*t')
    return t.year, t.month, t.day
end

-- Holidays with their own experience win the headline spot over plain observance days that overlap them
local function hasExperience(id)
    return id == 'christmas' or (Config.Events and Config.Events[id] ~= nil)
end

-- active[]: holidays whose window covers `days`; upcoming[]: the next occurrence of everything else, soonest first
function Dates.evaluate(days, year)
    local def = Config.DefaultWindow or { before = 1, after = 0 }
    local active, upcoming, isActive, nextOf = {}, {}, {}, {}
    for _, h in ipairs(Config.Holidays) do
        if h.enabled ~= false then
            for y = year - 1, year + 1 do
                local day, obs = resolve(h.rule, y, h.federal)
                if day then
                    local from = math.min(day, obs) - (h.before or def.before or 0)
                    local to = math.max(day, obs) + (h.after or def.after or 0)
                    local ry, rm, rd = Dates.fromDays(day)
                    local entry = { id = h.id, label = h.label, blurb = h.blurb, daysUntil = day - days, date = Dates.key(ry, rm, rd),
                        theme = Config.Themes[h.theme] or Config.Themes.default }
                    if days >= from and days <= to then
                        if not isActive[h.id] then isActive[h.id] = true; active[#active + 1] = entry end
                    elseif day > days and (not nextOf[h.id] or day - days < nextOf[h.id].daysUntil) then
                        nextOf[h.id] = entry
                    end
                end
            end
        end
    end
    for id, e in pairs(nextOf) do
        if not isActive[id] then upcoming[#upcoming + 1] = e end
    end
    table.sort(active, function(a, b)
        local ea, eb = hasExperience(a.id), hasExperience(b.id)
        if ea ~= eb then return ea end
        return math.abs(a.daysUntil) < math.abs(b.daysUntil)
    end)
    table.sort(upcoming, function(a, b) return a.daysUntil < b.daysUntil end)
    return active, upcoming
end
