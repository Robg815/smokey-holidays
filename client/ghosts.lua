-- Halloween ghosts: a local (never networked) ped near this player. Catching is verified by the server.
local G = Config.Ghosts
local KVP = 's2-holidays:ghostsOff'
local optedOut = GetResourceKvpInt(KVP) == 1
local ghost -- { id, ped, base, expires, scared, text, catching }

local function despawn(fade)
    local g = ghost
    if not g then return end
    ghost = nil
    if g.text then lib.hideTextUI() end
    if not DoesEntityExist(g.ped) then return end
    if not fade then return DeleteEntity(g.ped) end
    CreateThread(function()
        for a = G.alpha, 0, -10 do
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

local function scare()
    ShakeGameplayCam('SMALL_EXPLOSION_SHAKE', 0.18)
    AnimpostfxPlay('DeathFailMPDark', 0, false)
    PlaySoundFrontend(-1, 'Bed', 'WastedSounds', true)
    SetTimeout(900, function() AnimpostfxStop('DeathFailMPDark') end)
end

local function catch(g)
    g.catching = true
    if g.text then lib.hideTextUI(); g.text = false end
    CreateThread(function()
        local done = lib.progressCircle({ duration = 1800, label = 'Catching the ghost...', position = 'bottom', canCancel = true,
            disable = { move = true, car = true, combat = true } })
        if done and ghost == g then
            local res = lib.callback.await('s2-holidays:ghost:catch', false, g.id) or { ok = false, msg = 'Try again.' }
            if res.ok then
                lib.notify({ title = res.label or 'Ghost caught', description = ('%s +%d pts'):format(res.msg or '', res.points or 0), type = 'success', icon = 'ghost' })
            else
                lib.notify({ title = 'Halloween', description = res.msg, type = 'error' })
            end
            if (res.ok or res.final) and ghost == g then despawn(true) end
        end
        g.catching = false
    end)
end

local function haunt(g)
    local t0, l = GetGameTimer(), g.light or { 120, 200, 255 }
    while ghost == g do
        local now, me = GetGameTimer(), GetEntityCoords(cache.ped)
        if now > g.expires or #(me - g.base) > 200.0 then despawn(true); break end
        local t = (now - t0) / 1000
        local pos = g.base + vec3(math.cos(t * 0.35) * 2.5, math.sin(t * 0.35) * 2.5, math.sin(t * 1.3) * 0.35)
        SetEntityCoordsNoOffset(g.ped, pos.x, pos.y, pos.z, false, false, false)
        SetEntityHeading(g.ped, (math.deg(t * 0.35) + 180.0) % 360.0)
        local dist = #(me - pos)
        if dist < 45.0 then DrawLightWithRange(pos.x, pos.y, pos.z + 0.6, l[1], l[2], l[3], 6.0, 2.0) end
        if dist < 12.0 and not g.scared then g.scared = true; scare() end
        if dist < 2.8 and not g.catching then
            if not g.text then lib.showTextUI('[E] Catch the ghost'); g.text = true end
            if IsControlJustReleased(0, 38) then catch(g) end
        elseif g.text then
            lib.hideTextUI(); g.text = false
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
    SetEntityAlpha(ped, data.alpha or 100, false)
    SetEntityInvincible(ped, true)
    FreezeEntityPosition(ped, true)
    SetEntityCollision(ped, false, false)
    SetBlockingOfNonTemporaryEvents(ped, true)
    SetPedCanRagdoll(ped, false)

    local g = { id = data.id, ped = ped, base = vec3(data.x, data.y, z), expires = GetGameTimer() + (data.ttl or 240) * 1000, light = data.light }
    ghost = g
    CreateThread(function() haunt(g) end)
    return true
end)

AddEventHandler('onResourceStop', function(name)
    if name == GetCurrentResourceName() then despawn(false) end
end)
