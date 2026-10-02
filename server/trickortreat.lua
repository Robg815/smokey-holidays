-- City-wide trick or treating: knock on real front doors around the map during Halloween.
-- Server checks: Halloween live, contest open, valid door, player standing at it, once per door per night, nightly cap.
local TT = Config.TrickOrTreat
local U = Events.util

local function halloweenLive(y, m, d)
    for _, h in ipairs((Dates.evaluate(Dates.toDays(y, m, d), y))) do
        if h.id == 'halloween' then return true end
    end
    return false
end

local function knock(src, cid, idx, y, m, d)
    local cfg = U.cfgFor('halloween')
    local door = TT.doors[idx]
    local ped = GetPlayerPed(src)
    if not ped or ped == 0 or #(GetEntityCoords(ped) - door.coords) > TT.verifyDistance then
        return { ok = false, msg = 'Walk up to the door first.' }
    end
    local knocked = Events.doorsToday(cid, y, m, d)
    local base = Dates.toDays(y, m, d) * 1000
    for _, r in ipairs(knocked) do
        if r.slot == base + idx then return { ok = false, msg = 'You already knocked here tonight.' } end
    end
    if #knocked >= TT.perNight then return { ok = false, msg = "Your candy bag is full for tonight. Come back tomorrow." } end

    local outcomes = TT.outcomes or cfg.outcomes
    local _, o = U.roll(outcomes)
    if not U.canCarry(src, o) then return U.FULL end
    if not U.insert(cid, 'halloween_door', y, base + idx) then return { ok = false, msg = 'Too slow.' } end
    U.give(src, o)
    local res = { ok = true, kind = o.kind, label = o.label, msg = o.msg, points = o.points, today = #knocked + 1, cap = TT.perNight }
    U.award(src, cid, 'halloween', cfg, y, o.points, res)
    return res
end

lib.callback.register('s2-holidays:door:knock', function(src, idx)
    idx = tonumber(idx)
    local cid = U.cidOf(src)
    if not TT or not TT.enabled or not cid or not idx or idx ~= math.floor(idx) or not TT.doors[idx] then
        return { ok = false, msg = 'Invalid request.' }
    end
    local y, m, d = Dates.today()
    if not halloweenLive(y, m, d) then return { ok = false, msg = 'Trick or treating is over for this year.' } end
    if not Events.contestOpen('halloween') then return { ok = false, msg = 'The Halloween contest has ended.' } end

    if U.busy[cid] then return { ok = false, msg = 'One moment...' } end
    U.busy[cid] = true
    local ok, res = pcall(knock, src, cid, idx, y, m, d)
    U.busy[cid] = nil
    if not ok then print(('[s2-holidays] %s'):format(res)); return { ok = false, msg = 'Something went wrong.' } end
    return res
end)

-- Which doors this player already knocked tonight (so the client can grey them out)
lib.callback.register('s2-holidays:door:state', function(src)
    local cid = U.cidOf(src)
    if not TT or not TT.enabled or not cid then return nil end
    local y, m, d = Dates.today()
    if not halloweenLive(y, m, d) or not Events.contestOpen('halloween') then return nil end
    local base, done = Dates.toDays(y, m, d) * 1000, {}
    for _, r in ipairs(Events.doorsToday(cid, y, m, d)) do done[#done + 1] = r.slot - base end
    return { done = done, cap = TT.perNight }
end)
