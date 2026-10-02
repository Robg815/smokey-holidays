-- City activities (config_world.lua): props, markers, blips, prompts, deliveries, gatherings and fireworks.
-- Everything here is local to this client; the server verifies every action in server/world.lua.
local W, P = Config.World or {}, Config.Places or {}
local state = {}          -- [holiday] = { [key] = progress from the server }
local built = {}          -- [holiday..key] = { points = {}, blips = {}, props = {} }
local signature = ''
local busy, textShown = false, false
local job                 -- active delivery { h, key, drop, coords, expires, prop, blip }

local function places(v) return type(v) == 'string' and (P[v] or {}) or (v or {}) end
local function find(h, key) for _, a in ipairs(W[h] or {}) do if a.key == key then return a end end end
local function showText(t, icon) if textShown ~= t then lib.showTextUI(t, { icon = icon or 'hand' }); textShown = t end end
local function hideText() if textShown then lib.hideTextUI(); textShown = false end end
local function night() local hr = GetClockHours(); return hr >= 20 or hr < 6 end
local function notifyResult(a, res)
    if not res.ok then return lib.notify({ title = a.title, description = res.msg, type = 'error' }) end
    local extra = res.points and res.points > 0 and ('  +%d pts'):format(res.points) or ''
    local count = res.cap and ('  (%d/%d today)'):format(res.today or 0, res.cap) or ''
    lib.notify({ title = res.label, description = (res.msg or '') .. extra .. count, type = res.kind == 'empty' and 'inform' or 'success', duration = 7000 })
end

-- Ground height near a point (props and markers sit on the ground even if the configured z is a little off)
local function ground(c)
    local found, z = GetGroundZFor_3dCoord(c.x, c.y, c.z + 2.0, false)
    return vec3(c.x, c.y, found and math.abs(z - c.z) < 8.0 and z or c.z)
end

local function blip(c, b, label, radius)
    local id
    if radius then
        id = AddBlipForRadius(c.x, c.y, c.z, radius)
        SetBlipColour(id, b.colour or 0); SetBlipAlpha(id, 90)
        return id
    end
    id = AddBlipForCoord(c.x, c.y, c.z)
    SetBlipSprite(id, b.sprite or 1); SetBlipColour(id, b.colour or 0); SetBlipScale(id, b.scale or 0.7); SetBlipAsShortRange(id, true)
    BeginTextCommandSetBlipName('STRING'); AddTextComponentSubstringPlayerName(label); EndTextCommandSetBlipName(id)
    return id
end

local function deleteProp(o) if o and DoesEntityExist(o) then DeleteEntity(o) end end

local function spawnProp(model, c)
    local hash = joaat(model)
    if not IsModelInCdimage(hash) or not pcall(lib.requestModel, hash, 4000) then return end
    local o = CreateObject(hash, c.x, c.y, c.z, false, false, false)
    SetModelAsNoLongerNeeded(hash)
    if not DoesEntityExist(o) then return end
    PlaceObjectOnGroundProperly(o); FreezeEntityPosition(o, true); SetEntityInvincible(o, true)
    return o
end

-- ---------- spots ----------
local function isDone(h, a, i)
    local p = state[h] and state[h][a.key]
    if not p then return true end
    for _, n in ipairs(p.done or {}) do if n == i then return true end end
    return (p.today or 0) >= (p.cap or 1)
end

local function markDone(h, a, i, b)
    local p = state[h] and state[h][a.key]
    if p then p.done = p.done or {}; p.done[#p.done + 1] = i; p.today = (p.today or 0) + 1 end
    if b.props[i] then deleteProp(b.props[i]); b.props[i] = nil end
    if b.blips[i] then SetBlipColour(b.blips[i], 40); SetBlipAlpha(b.blips[i], 120) end
end

local function useSpot(h, a, i, b)
    busy = true
    hideText()
    if a.water and not IsEntityInWater(cache.ped) then busy = false; return lib.notify({ title = a.title, description = 'Get in the water first.', type = 'error' }) end
    if a.nightOnly and not night() then busy = false; return lib.notify({ title = a.title, description = 'Come back after dark.', type = 'error' }) end
    if cache.vehicle then busy = false; return lib.notify({ title = a.title, description = 'Get out of the vehicle first.', type = 'error' }) end
    local opts = { duration = a.duration or 3000, label = (a.prompt or 'Working') .. '...', position = 'bottom', canCancel = true,
        disable = { move = true, car = true, combat = true } }
    if a.scenario then opts.anim = { scenario = a.scenario } elseif a.anim then opts.anim = { dict = a.anim.dict, clip = a.anim.clip, flag = 1 } end
    if lib.progressCircle(opts) then
        local res = lib.callback.await('s2-holidays:world:use', false, h, a.key, i) or { ok = false, msg = 'Try again.' }
        if res.ok or res.done then markDone(h, a, i, b) end
        if res.ok and a.effect == 'scare' and res.kind == 'trick' then HolidayScare() end
        notifyResult(a, res)
    end
    ClearPedTasks(cache.ped)
    busy = false
end

local function buildSpots(h, a, b)
    local mk = a.marker
    for i, c in ipairs(places(a.spots)) do
        if a.blip then
            if a.blip.mode == 'area' then -- show a search area, not the exact spot
                local ang = (i * 137.5) % 360
                local off = vec3(c.x + math.cos(math.rad(ang)) * 45.0, c.y + math.sin(math.rad(ang)) * 45.0, c.z)
                b.blips[#b.blips + 1] = blip(off, a.blip, a.title, 95.0)
            else
                b.blips[i] = blip(c, a.blip, a.title)
                if isDone(h, a, i) then SetBlipColour(b.blips[i], 40); SetBlipAlpha(b.blips[i], 120) end
            end
        end
        b.points[#b.points + 1] = lib.points.new({
            coords = c, distance = 60.0,
            onEnter = function(self) self.g = ground(c); if a.prop and not isDone(h, a, i) and not b.props[i] then b.props[i] = spawnProp(a.prop, self.g) end end,
            onExit = function() deleteProp(b.props[i]); b.props[i] = nil; hideText() end,
            nearby = function(self)
                if isDone(h, a, i) then return end
                local g = self.g or c
                if mk and (not a.prop or not b.props[i]) then
                    local col = mk.color or { r = 255, g = 255, b = 255, a = 160 }
                    DrawMarker(mk.type or 1, g.x, g.y, g.z + (mk.type == 1 and 0.0 or 0.6), 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, mk.scale or 1.0, mk.scale or 1.0, mk.type == 1 and 0.6 or (mk.scale or 1.0),
                        col.r, col.g, col.b, col.a or 160, mk.type ~= 1, true, 2, mk.type ~= 1, nil, nil, false)
                end
                if a.light then DrawLightWithRange(g.x, g.y, g.z + 0.6, a.light[1], a.light[2], a.light[3], 4.0, 3.0) end
                if self.currentDistance <= (a.distance or 2.0) and not busy then
                    showText(('[E] %s'):format(a.prompt or a.title))
                    if IsControlJustReleased(0, 38) then CreateThread(function() useSpot(h, a, i, b) end) end
                elseif textShown and self.currentDistance <= (a.distance or 2.0) + 2.0 then
                    hideText()
                end
            end,
        })
    end
end

-- ---------- deliveries ----------
local function clearJob(msg, kind)
    if not job then return end
    deleteProp(job.prop); if job.blip then RemoveBlip(job.blip) end
    StopAnimTask(cache.ped, 'anim@heists@box_carry@', 'idle', 1.0)
    job = nil
    hideText()
    if msg then lib.notify({ title = 'Delivery', description = msg, type = kind or 'inform' }) end
end

local function carry(model)
    local o = spawnProp(model or 'prop_cs_cardbox_01', GetEntityCoords(cache.ped))
    if not o then return end
    FreezeEntityPosition(o, false); SetEntityCollision(o, false, false)
    AttachEntityToEntity(o, cache.ped, GetPedBoneIndex(cache.ped, 28422), 0.0, -0.03, 0.0, 5.0, 0.0, 0.0, true, true, false, true, 1, true)
    return o
end

local function startJob(h, a, drop, limit)
    local c = places(a.drops)[drop]
    if not c then return end
    lib.requestAnimDict('anim@heists@box_carry@', 3000)
    job = { h = h, key = a.key, a = a, drop = drop, coords = c, expires = GetGameTimer() + limit * 1000, prop = carry(a.carry) }
    job.blip = blip(c, { sprite = 1, colour = (a.blip and a.blip.colour) or 5 }, a.title .. ': drop off')
    SetBlipRoute(job.blip, true); SetBlipRouteColour(job.blip, (a.blip and a.blip.colour) or 5)
    lib.notify({ title = a.title, description = ('Deliver it within %d minutes. Follow the route on your map.'):format(math.floor(limit / 60)), type = 'inform', duration = 8000 })
    CreateThread(function()
        local warned = false
        while job and job.key == a.key do
            local left = (job.expires - GetGameTimer()) / 1000
            if left <= 0 then lib.callback.await('s2-holidays:world:cancel', false); clearJob('Too late. The delivery expired.', 'error'); break end
            if left < 60 and not warned then warned = true; lib.notify({ title = a.title, description = 'One minute left!', type = 'warning' }) end
            if not cache.vehicle and not IsEntityPlayingAnim(cache.ped, 'anim@heists@box_carry@', 'idle', 3) then
                TaskPlayAnim(cache.ped, 'anim@heists@box_carry@', 'idle', 8.0, -8.0, -1, 49, 0, false, false, false)
            end
            if job.prop then SetEntityVisible(job.prop, not cache.vehicle, false) end
            local dist = #(GetEntityCoords(cache.ped) - job.coords)
            if dist < 30.0 then DrawMarker(1, job.coords.x, job.coords.y, job.coords.z - 1.0, 0, 0, 0, 0, 0, 0, 1.5, 1.5, 0.6, 255, 211, 107, 150, false, true, 2, false, nil, nil, false) end
            if dist < 3.0 and not busy and not cache.vehicle then
                showText(('[E] Deliver  \u{00B7}  %d:%02d left'):format(math.floor(left / 60), math.floor(left % 60)), 'box')
                if IsControlJustReleased(0, 38) then
                    busy = true; hideText()
                    if lib.progressCircle({ duration = 2000, label = 'Handing it over...', position = 'bottom', canCancel = true, disable = { move = true, car = true } }) then
                        local res = lib.callback.await('s2-holidays:world:deliver', false, job.h, job.key) or { ok = false, msg = 'Try again.' }
                        notifyResult(a, res)
                        if res.ok or res.final then
                            local p = state[job.h] and state[job.h][job.key]
                            if p and res.ok then p.today = (p.today or 0) + 1 end
                            clearJob()
                        end
                    end
                    busy = false
                end
            elseif textShown and dist < 6.0 then hideText() end
            Wait(dist < 40.0 and 0 or 250)
        end
    end)
end

local function buildDelivery(h, a, b)
    for i, c in ipairs(places(a.pickups)) do
        if a.blip then b.blips[#b.blips + 1] = blip(c, a.blip, a.title) end
        b.points[#b.points + 1] = lib.points.new({
            coords = c, distance = 30.0, onExit = hideText,
            nearby = function(self)
                if job then return end
                local p = state[h] and state[h][a.key]
                if not p or (p.today or 0) >= (p.cap or 1) then return end
                DrawMarker(39, c.x, c.y, c.z + 0.2, 0, 0, 0, 0, 0, 0, 0.8, 0.8, 0.8, 255, 211, 107, 180, true, true, 2, false, nil, nil, false)
                if self.currentDistance <= 2.0 and not busy then
                    showText(('[E] Pick up: %s'):format(a.title), 'box')
                    if IsControlJustReleased(0, 38) then
                        CreateThread(function()
                            busy = true; hideText()
                            if lib.progressCircle({ duration = 2000, label = 'Picking it up...', position = 'bottom', canCancel = true, disable = { move = true, car = true },
                                anim = { dict = 'pickup_object', clip = 'pickup_low' } }) then
                                local res = lib.callback.await('s2-holidays:world:pickup', false, h, a.key, i) or { ok = false, msg = 'Try again.' }
                                if res.ok then startJob(h, a, res.drop, res.timeLimit) else notifyResult(a, res) end
                            end
                            busy = false
                        end)
                    end
                elseif textShown and self.currentDistance <= 4.0 then hideText() end
            end,
        })
    end
end

-- ---------- gatherings ----------
local function buildGathering(h, a, b)
    local c = a.center
    if a.blip then
        b.blips[#b.blips + 1] = blip(c, a.blip, a.title)
        b.blips[#b.blips + 1] = blip(c, a.blip, a.title, a.radius)
    end
    b.points[#b.points + 1] = lib.points.new({
        coords = c, distance = a.radius + 60.0,
        nearby = function(self)
            local p = state[h] and state[h][a.key]
            if not p or (p.today or 0) >= 1 then return end
            local left = (p.startsIn or 0) - (GetGameTimer() - (p.at or GetGameTimer())) / 1000
            if left > 0 and left < 3600 then
                DrawMarker(1, c.x, c.y, c.z - 1.0, 0, 0, 0, 0, 0, 0, a.radius * 2.0, a.radius * 2.0, 1.0, 255, 211, 107, 35, false, false, 2, false, nil, nil, false)
            end
            if self.currentDistance <= a.radius and left > 0 and left <= 120 then
                showText(('%s in %d:%02d'):format(a.title, math.floor(left / 60), math.floor(left % 60)), 'clock')
            elseif textShown and type(textShown) == 'string' and textShown:find(a.title, 1, true) then
                hideText()
            end
        end,
    })
end

-- ---------- fireworks ----------
local SHOW_FX = { 'scr_indep_firework_trailburst', 'scr_indep_firework_starburst', 'scr_indep_firework_shotburst' }
local function burst(x, y, z, name, scale)
    UseParticleFxAssetNextCall('scr_indep_fireworks')
    StartParticleFxNonLoopedAtCoord(name, x, y, z, 0.0, 0.0, 0.0, scale or 1.5, false, false, false)
end
RegisterNetEvent('s2-holidays:world:fx', function(d)
    local c = vec3(d.x, d.y, d.z)
    if #(GetEntityCoords(cache.ped) - c) > 700.0 or not pcall(lib.requestNamedPtfxAsset, 'scr_indep_fireworks', 5000) then return end
    CreateThread(function()
        if d.kind == 'burst' then -- one launch pad: a fountain on the ground and a few bursts above it
            burst(c.x, c.y, c.z, 'scr_indep_firework_fountain', 1.0)
            for _ = 1, 5 do Wait(450); burst(c.x + math.random(-6, 6), c.y + math.random(-6, 6), c.z + math.random(28, 42), SHOW_FX[math.random(#SHOW_FX)], 1.6) end
        elseif d.kind == 'show' then
            local stop = GetGameTimer() + (d.duration or 180) * 1000
            while GetGameTimer() < stop do
                for _ = 1, math.random(1, 3) do
                    burst(c.x + math.random(-60, 60), c.y + math.random(-60, 60), c.z + math.random(-10, 25), SHOW_FX[math.random(#SHOW_FX)], math.random(15, 25) / 10)
                end
                Wait(math.random(300, 900))
            end
        end
    end)
end)

RegisterNetEvent('s2-holidays:world:done', function(h, key, res)
    local a = find(h, key)
    local p = state[h] and state[h][key]
    if p then p.today = 1 end
    if a then notifyResult(a, res) end
end)

-- ---------- build / sync ----------
local function teardown()
    for _, b in pairs(built) do
        for _, p in pairs(b.points) do p:remove() end
        for _, id in pairs(b.blips) do RemoveBlip(id) end
        for _, o in pairs(b.props) do deleteProp(o) end
    end
    built = {}
    hideText()
end

local function apply(raw)
    local now, sig = GetGameTimer(), {}
    state = {}
    for h, acts in pairs(raw or {}) do
        state[h] = {}
        for _, e in ipairs(acts) do
            e.at = now; state[h][e.key] = e
            sig[#sig + 1] = h .. ':' .. e.key
        end
    end
    table.sort(sig)
    local s = table.concat(sig, ',')
    if s == signature then return end -- same activities running: keep what is built, progress already updated
    signature = s
    teardown()
    for h, acts in pairs(state) do
        for key in pairs(acts) do
            local a = find(h, key)
            if a then
                local b = { points = {}, blips = {}, props = {} }
                built[h .. ':' .. key] = b
                if a.type == 'spots' then buildSpots(h, a, b)
                elseif a.type == 'delivery' then buildDelivery(h, a, b)
                elseif a.type == 'gathering' then buildGathering(h, a, b) end
            end
        end
    end
end

function WorldSync()
    apply(lib.callback.await('s2-holidays:world:state', false))
end

CreateThread(function()
    while not LocalPlayer.state.isLoggedIn do Wait(2000) end
    while true do
        WorldSync()
        Wait(60000) -- picks up holidays starting and ending (and admin date changes) within a minute
    end
end)

RegisterNetEvent('QBCore:Client:OnPlayerLoaded', function() -- new character: their own progress
    CreateThread(function() signature = ''; clearJob(); WorldSync() end)
end)

-- Menu hub: point the GPS at the nearest unfinished spot, the drop-off, the pickup, or the gathering
RegisterNUICallback('waypoint', function(data, cb)
    local a = find(data.holiday, data.key)
    if not a then return cb({ ok = false, msg = 'Nothing to point at.' }) end
    local me, best, bd = GetEntityCoords(cache.ped), nil, math.huge
    local function consider(c) local d = #(me - c); if d < bd then best, bd = c, d end end
    if a.type == 'spots' then
        for i, c in ipairs(places(a.spots)) do if not isDone(data.holiday, a, i) then consider(c) end end
    elseif a.type == 'delivery' then
        if job and job.key == a.key then consider(job.coords) else for _, c in ipairs(places(a.pickups)) do consider(c) end end
    elseif a.type == 'gathering' then
        consider(a.center)
    end
    if not best then return cb({ ok = false, msg = 'Nothing left for today.' }) end
    SetNewWaypoint(best.x, best.y)
    cb({ ok = true, msg = ('Waypoint set: %s (%.1f km)'):format(a.title, bd / 1000) })
end)

-- Stand somewhere and run /holidayspot to get a ready-to-paste vec3 for config_world.lua
RegisterCommand('holidayspot', function()
    local c = GetEntityCoords(cache.ped)
    local line = ('vec3(%.2f, %.2f, %.2f),'):format(c.x, c.y, c.z)
    print(line); lib.setClipboard(line)
    lib.notify({ title = 'Holidays', description = 'Position copied to your clipboard and printed to F8.', type = 'inform' })
end, false)

RegisterCommand('holidaycancel', function()
    if not job then return end
    lib.callback.await('s2-holidays:world:cancel', false)
    clearJob('Delivery cancelled.')
end, false)

-- Teleport from the admin tablet (server checks permission and picks the coordinates)
RegisterNetEvent('s2-holidays:world:resync', function() signature = ''; WorldSync() end)

AddEventHandler('onResourceStop', function(name)
    if name ~= GetCurrentResourceName() then return end
    teardown()
    if job then deleteProp(job.prop); StopAnimTask(cache.ped, 'anim@heists@box_carry@', 'idle', 1.0) end
end)
