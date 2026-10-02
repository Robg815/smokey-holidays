-- City-wide trick or treating: prompts and blips at every front door in Config.TrickOrTreat. The server rolls and verifies.
local TT = Config.TrickOrTreat
local points, blips, done, live = {}, {}, {}, false
local busy, shown = false, false

local function hideText()
    if shown then lib.hideTextUI(); shown = false end
end

local function clear()
    for _, p in pairs(points) do p:remove() end
    for _, b in pairs(blips) do RemoveBlip(b) end
    points, blips, live = {}, {}, false
    hideText()
end

local function greyOut(i)
    done[i] = true
    if blips[i] then SetBlipColour(blips[i], 40); SetBlipAlpha(blips[i], 140) end
end

local function nightOk()
    if not TT.nightOnly then return true end
    local h = GetClockHours()
    return h >= 18 or h < 6
end

local function knock(i)
    busy = true
    hideText()
    local ok = lib.progressCircle({ duration = TT.knockTime, label = 'Knocking...', position = 'bottom', canCancel = true,
        disable = { move = true, car = true, combat = true }, anim = { dict = 'timetable@jimmy@doorknock@', clip = 'knockdoor_idle' } })
    if ok then
        local res = lib.callback.await('s2-holidays:door:knock', false, i) or { ok = false, msg = 'Try again.' }
        if res.ok then
            greyOut(i)
            if res.kind == 'trick' then HolidayScare() end
            local pts = res.points and res.points > 0 and (' +%d pts'):format(res.points) or ''
            lib.notify({ title = res.label, description = ('%s%s  (%d/%d doors tonight)'):format(res.msg or '', pts, res.today or 0, res.cap or 0),
                type = res.kind == 'empty' and 'inform' or 'success', icon = res.kind == 'trick' and 'skull' or 'candy-cane', duration = 6500 })
        else
            lib.notify({ title = 'Trick or treat', description = res.msg, type = 'error' })
            if res.msg == 'You already knocked here tonight.' then greyOut(i) end
        end
    end
    busy = false
end

local function nearby(self)
    local i = self.idx
    if done[i] then return end
    local c = TT.doors[i].coords
    DrawMarker(2, c.x, c.y, c.z + 0.35, 0.0, 0.0, 0.0, 180.0, 0.0, 0.0, 0.22, 0.22, 0.18, 255, 138, 31, 170, true, true, 2, false, nil, nil, false)
    if self.currentDistance <= TT.distance and not busy and nightOk() then
        if not shown then lib.showTextUI('[E] Trick or treat', { icon = 'candy-cane' }); shown = true end
        if IsControlJustReleased(0, 38) then CreateThread(function() knock(i) end) end
    elseif shown and self.currentDistance <= TT.distance + 1.5 then
        hideText()
    end
end

local function build(state)
    clear()
    done = {}
    for _, i in ipairs(state.done or {}) do done[i] = true end
    for i, door in ipairs(TT.doors) do
        points[i] = lib.points.new({ coords = door.coords, distance = 18.0, idx = i, nearby = nearby, onExit = hideText })
        if TT.blips and TT.blips.enabled then
            local b = AddBlipForCoord(door.coords.x, door.coords.y, door.coords.z)
            SetBlipSprite(b, TT.blips.sprite); SetBlipColour(b, TT.blips.colour); SetBlipScale(b, TT.blips.scale)
            SetBlipAsShortRange(b, true)
            BeginTextCommandSetBlipName('STRING'); AddTextComponentSubstringPlayerName(TT.blips.label); EndTextCommandSetBlipName(b)
            blips[i] = b
        end
        if done[i] then greyOut(i) end
    end
    live = true
end

local function sync()
    local state = lib.callback.await('s2-holidays:door:state', false)
    if state and not live then build(state) elseif not state and live then clear() end
end

CreateThread(function()
    if not TT or not TT.enabled then return end
    while not LocalPlayer.state.isLoggedIn do Wait(2000) end
    while true do
        sync()
        Wait(60000) -- picks up the start and end of Halloween (and admin date changes) within a minute
    end
end)

RegisterNetEvent('QBCore:Client:OnPlayerLoaded', function() -- new character: rebuild with their own knocked doors
    CreateThread(function() clear(); sync() end)
end)

-- Record a new door: stand outside it and run /holidaydoor, then paste the line into Config.TrickOrTreat.doors
RegisterCommand('holidaydoor', function()
    local c = GetEntityCoords(cache.ped)
    local street = GetStreetNameFromHashKey((GetStreetNameAtCoord(c.x, c.y, c.z)))
    local line = ("{ coords = vec3(%.2f, %.2f, %.2f), area = '%s' },"):format(c.x, c.y, c.z, street)
    print(line)
    lib.setClipboard(line)
    lib.notify({ title = 'Trick or treat', description = 'Door position copied to your clipboard and printed to F8.', type = 'inform' })
end, false)

AddEventHandler('onResourceStop', function(name)
    if name == GetCurrentResourceName() then clear() end
end)
