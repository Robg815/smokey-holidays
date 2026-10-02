-- Halloween ghosts: a local (never networked) ped near this player. Catching is verified by the server.
-- With Config.Ghosts.flashlight.required the ghost is faint until lit, and is trapped by holding a flashlight beam on it.
local G = Config.Ghosts
local FL = G.flashlight or {}
local NEED_LIGHT = FL.required == true
local FLASH = joaat(FL.weapon or 'WEAPON_FLASHLIGHT')
local KVP = 's2-holidays:ghostsOff'
local optedOut = GetResourceKvpInt(KVP) == 1
local ghost -- { id, ped, base, expires, scared, text, catching, exposure, hinted }

local function setText(g, text)
    if g.text == text then return end
    if text then lib.showTextUI(text, { icon = 'ghost' }) else lib.hideTextUI() end
    g.text = text
end

local function despawn(fade)
    local g = ghost
    if not g then return end
    ghost = nil
    if g.text then lib.hideTextUI() end
    if not DoesEntityExist(g.ped) then return end
    if not fade then return DeleteEntity(g.ped) end
    CreateThread(function()
        for a = GetEntityAlpha(g.ped), 0, -10 do
            if not DoesEntityExist(g.ped) then return end
            SetEntityAlpha(g.ped, a, false)
            Wait(40)
        end
        if DoesEntityExist(g.ped) then DeleteEntity(g.ped) end
    end)
end

RegisterCommand('halloweenghosts', function()
    optedOut = not optedOut
    SetResourceKvpInt(KVP, optedOut and 1 or 0)
    if optedOut then despawn(true) end
    lib.notify({ title = 'Halloween', type = 'inform', description = optedOut and 'Ghosts will leave you alone.' or 'Ghosts can find you again.' })
end, false)

RegisterNetEvent('s2-holidays:ghost:clear', function() despawn(true) end)

local function submit(g)
    local res = lib.callback.await('s2-holidays:ghost:catch', false, g.id) or { ok = false, msg = 'Try again.' }
    if res.ok then
        PlaySoundFrontend(-1, 'CHECKPOINT_PERFECT', 'HUD_MINI_GAME_SOUNDSET', true)
        lib.notify({ title = res.label or 'Ghost caught', description = ('%s +%d pts'):format(res.msg or '', res.points or 0), type = 'success', icon = 'ghost' })
    else
        lib.notify({ title = 'Halloween', description = res.msg, type = 'error' })
    end
    if (res.ok or res.final) and ghost == g then despawn(true) end
    return res.ok or res.final
end

local function catchByHand(g) -- only used when flashlights are not required
    g.catching = true
    setText(g, nil)
    CreateThread(function()
        local done = lib.progressCircle({ duration = 1800, label = 'Catching the ghost...', position = 'bottom', canCancel = true,
            disable = { move = true, car = true, combat = true } })
        if done and ghost == g then submit(g) end
        g.catching = false
    end)
end

local function camForward()
    local r = GetGameplayCamRot(2)
    local x, z = math.rad(r.x), math.rad(r.z)
    return vec3(-math.sin(z) * math.cos(x), math.cos(z) * math.cos(x), math.sin(x))
end

-- Is the flashlight in hand, switched on or aimed, pointed at the ghost, in range and not blocked by a wall?
local function lit(pos)
    local ped = cache.ped
    if GetSelectedPedWeapon(ped) ~= FLASH then return false, false end
    if not (IsPlayerFreeAiming(cache.playerId) or IsFlashLightOn(ped)) then return false, true end
    if #(GetEntityCoords(ped) - pos) > FL.range then return false, true end
    local cam = GetGameplayCamCoord()
    local to = pos - cam
    local len = #to
    local f = camForward()
    local dot = (to.x * f.x + to.y * f.y + to.z * f.z) / len
    if math.deg(math.acos(math.max(-1.0, math.min(1.0, dot)))) > FL.cone then return false, true end
    local probe = StartExpensiveSynchronousShapeTestLosProbe(cam.x, cam.y, cam.z, pos.x, pos.y, pos.z, 1, ped, 0)
    local _, hit = GetShapeTestResult(probe)
    return hit ~= 1, true
end

local function drawMeter(pos, p)
    local onScreen, sx, sy = GetScreenCoordFromWorldCoord(pos.x, pos.y, pos.z + 1.15)
    if not onScreen then return end
    DrawRect(sx, sy, 0.064, 0.009, 10, 6, 20, 170)
    DrawRect(sx - 0.031 + 0.031 * p, sy, 0.062 * p, 0.006, 150, 225, 255, 230)
end

local function haunt(g)
    local t0, l = GetGameTimer(), g.light or { 120, 200, 255 }
    local faint = math.floor((G.alpha or 100) * (NEED_LIGHT and 0.3 or 1.0))
    while ghost == g do
        local now, me = GetGameTimer(), GetEntityCoords(cache.ped)
        if now > g.expires or #(me - g.base) > 200.0 then despawn(true); break end
        local t = (now - t0) / 1000
        local speed = g.exposure > 0 and 0.9 or 0.35 -- it struggles while the beam is on it
        local pos = g.base + vec3(math.cos(t * speed) * 2.5, math.sin(t * speed) * 2.5, math.sin(t * 1.3) * 0.35)
        SetEntityCoordsNoOffset(g.ped, pos.x, pos.y, pos.z, false, false, false)
        SetEntityHeading(g.ped, (math.deg(t * speed) + 180.0) % 360.0)
        local dist = #(me - pos)
        if dist < 45.0 then DrawLightWithRange(pos.x, pos.y, pos.z + 0.6, l[1], l[2], l[3], 6.0, 2.0) end
        if dist < 12.0 and not g.scared then g.scared = true; HolidayScare() end

        if NEED_LIGHT then
            local on, holding = false, false
            if dist < FL.range + 15.0 and not g.catching then on, holding = lit(pos) end
            local dt = GetFrameTime()
            g.exposure = on and math.min(FL.exposure, g.exposure + dt) or math.max(0.0, g.exposure - FL.decay * dt)
            local p = g.exposure / FL.exposure
            SetEntityAlpha(g.ped, math.floor(faint + ((G.alpha or 100) - faint) * p), false)
            if p > 0 then drawMeter(pos, p) end
            if dist < 30.0 and not holding and not g.hinted then
                g.hinted = true
                lib.notify({ title = 'A ghost is nearby', description = 'You need a flashlight. Aim it at the ghost and hold the beam on it to trap it.', type = 'inform', icon = 'ghost', duration = 8000 })
            end
            setText(g, (holding and not on and dist < FL.range and not g.catching) and 'Shine your flashlight on the ghost' or nil)
            if p >= 1 and not g.catching then
                g.catching = true
                setText(g, nil)
                CreateThread(function()
                    if not submit(g) then g.exposure = 0.0 end
                    g.catching = false
                end)
            end
        elseif dist < 2.8 and not g.catching then
            setText(g, '[E] Catch the ghost')
            if IsControlJustReleased(0, 38) then catchByHand(g) end
        else
            setText(g, nil)
        end
        Wait(dist < 50.0 and 0 or 250)
    end
end

lib.callback.register('s2-holidays:ghost:spawn', function(data)
    if optedOut or ghost or type(data) ~= 'table' then return false end
    if data.nightOnly then
        local h = GetClockHours()
        if h >= 6 and h < 20 then return false end
    end
    local model = joaat(data.model)
    if not IsModelInCdimage(model) or not pcall(lib.requestModel, model, 5000) then return false end

    local found, gz = GetGroundZFor_3dCoord(data.x, data.y, data.z + 25.0, false)
    local z = (found and math.abs(gz - data.z) < 15.0 and gz or data.z) + 0.9
    local ped = CreatePed(4, model, data.x, data.y, z, math.random(0, 359) + 0.0, false, false)
    SetModelAsNoLongerNeeded(model)
    if not DoesEntityExist(ped) then return false end
    SetEntityAlpha(ped, NEED_LIGHT and math.floor((data.alpha or 100) * 0.3) or (data.alpha or 100), false)
    SetEntityInvincible(ped, true)
    FreezeEntityPosition(ped, true)
    SetEntityCollision(ped, false, false)
    SetBlockingOfNonTemporaryEvents(ped, true)
    SetPedCanRagdoll(ped, false)

    local g = { id = data.id, ped = ped, base = vec3(data.x, data.y, z), expires = GetGameTimer() + (data.ttl or 240) * 1000, light = data.light, exposure = 0.0 }
    ghost = g
    CreateThread(function() haunt(g) end)
    return true
end)

AddEventHandler('onResourceStop', function(name)
    if name == GetCurrentResourceName() then despawn(false) end
end)
