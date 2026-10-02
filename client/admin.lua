-- /holidayadmin: simple testing panel (server checks permission on every call)
RegisterCommand('holidayadmin', function()
    local data = lib.callback.await('s2-holidays:admin:get', false)
    if not data then
        lib.notify({ type = 'error', description = 'You do not have access to the holiday admin panel.' })
        return
    end
    SetNuiFocus(true, true)
    SendNUIMessage({ action = 'admin', data = data })
end, false)

RegisterNUICallback('adminDo', function(data, cb)
    cb(lib.callback.await('s2-holidays:admin:do', false, data.action, data) or {})
end)

RegisterNUICallback('adminClose', function(_, cb)
    SetNuiFocus(false, false)
    cb({})
end)

RegisterNUICallback('adminPreview', function(_, cb) -- close the panel and open the player UI as a player would see it
    SetNuiFocus(false, false)
    cb({})
    ExecuteCommand(Config.Command)
end)
