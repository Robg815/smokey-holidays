-- Opens the holiday UI and relays the advent claim. The server decides everything; this only shows it.
local open = false

-- Short jump scare used by tricks at doors and by ghosts (camera shake, dark flash, sting)
function HolidayScare()
    ShakeGameplayCam('SMALL_EXPLOSION_SHAKE', 0.18)
    AnimpostfxPlay('DeathFailMPDark', 0, false)
    PlaySoundFrontend(-1, 'Bed', 'WastedSounds', true)
    SetTimeout(900, function() AnimpostfxStop('DeathFailMPDark') end)
end

local function openUI()
    if open then return end
    local state = lib.callback.await('s2-holidays:getState', false)
    if not state then return end
    open = true
    SetNuiFocus(true, true)
    SendNUIMessage({ action = 'open', state = state })
end

RegisterCommand(Config.Command, openUI, false)
RegisterKeyMapping(Config.Command, 'Open the holiday calendar', 'keyboard', Config.Key)

RegisterNUICallback('claim', function(data, cb)
    cb(lib.callback.await('s2-holidays:claimAdvent', false, data.day) or { ok = false, msg = 'Try again.' })
end)

RegisterNUICallback('close', function(_, cb)
    open = false
    SetNuiFocus(false, false)
    cb({})
end)

-- Tell players what is on when their character loads in
RegisterNetEvent('QBCore:Client:OnPlayerLoaded', function()
    if not Config.LoginNotify then return end
    SetTimeout(8000, function()
        local state = lib.callback.await('s2-holidays:getState', false)
        local h = state and state.active and state.active[1]
        if not h then return end
        lib.notify({ title = h.label, description = ('%s Open the holiday menu with /%s.'):format(h.blurb or '', Config.Command), type = 'inform', duration = 9000 })
    end)
end)

AddEventHandler('onResourceStop', function(name)
    if name ~= GetCurrentResourceName() or not open then return end
    SetNuiFocus(false, false)
end)
