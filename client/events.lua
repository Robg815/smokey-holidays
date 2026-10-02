-- NUI bridge for the per-holiday experiences (server rolls every outcome)
RegisterNUICallback('play', function(data, cb)
    cb(lib.callback.await('s2-holidays:play', false, data.event, data.arg) or { ok = false, msg = 'Try again.' })
end)
