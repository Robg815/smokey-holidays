-- Halloween ghosts out in the world. Only ever near an online player, created by that player's client as a local ped,
-- and every catch is checked here (owner, expiry, distance) before Events.worldCatch pays out.
Ghosts = { active = {}, count = 0, last = {}, byPlayer = {} }

local G = Config.Ghosts
local nextId = 0

function Ghosts.remove(id)
    local g = Ghosts.active[id]
    if not g then return end
    Ghosts.active[id] = nil
    Ghosts.count = Ghosts.count - 1
    if Ghosts.byPlayer[g.src] == id then Ghosts.byPlayer[g.src] = nil end
    return g
end

function Ghosts.clear()
    Ghosts.active, Ghosts.byPlayer, Ghosts.count = {}, {}, 0
    TriggerClientEvent('s2-holidays:ghost:clear', -1)
end

local function halloweenLive()
    local y, m, d = Dates.today()
    for _, h in ipairs((Dates.evaluate(Dates.toDays(y, m, d), y))) do
        if h.id == 'halloween' then return true end
    end
    return false
end

local function tooClose(c)
    for _, g in pairs(Ghosts.active) do
        if #(g.coords - c) < G.minSeparation then return true end
    end
    return false
end

-- force = admin spawn: skips the separation rule and the night-only check
function Ghosts.spawnFor(src, force)
    if not G or not src or Ghosts.byPlayer[src] then return false end
    local ped = GetPlayerPed(src)
    if not ped or ped == 0 then return false end
    local p = GetEntityCoords(ped)
    local a = math.random() * 2 * math.pi
    local r = G.radius[1] + math.random() * (G.radius[2] - G.radius[1])
    local c = vector3(p.x + math.cos(a) * r, p.y + math.sin(a) * r, p.z)
    if not force and tooClose(c) then return false end

    nextId = nextId + 1
    local id = nextId
    Ghosts.active[id] = { src = src, coords = c, expires = os.time() + G.lifetime }
    Ghosts.count = Ghosts.count + 1
    Ghosts.byPlayer[src] = id
    Ghosts.last[src] = os.time()
    lib.callback('s2-holidays:ghost:spawn', src, function(ok)
        if not ok then Ghosts.remove(id) end
    end, { id = id, x = c.x, y = c.y, z = c.z, ttl = G.lifetime, model = G.model, alpha = G.alpha, light = G.light, nightOnly = G.nightOnly and not force })
    return true
end

local function eligible(src, player, now)
    if Ghosts.byPlayer[src] or now - (Ghosts.last[src] or 0) < G.playerCooldown then return false end
    if GetPlayerRoutingBucket(src) ~= 0 then return false end
    local meta = player.PlayerData.metadata or {}
    if meta.isdead or meta.inlaststand then return false end
    local ped = GetPlayerPed(src)
    if not ped or ped == 0 or GetEntityHealth(ped) <= 0 then return false end
    local veh = GetVehiclePedIsIn(ped, false)
    if veh ~= 0 and GetEntitySpeed(veh) > G.skipVehicleSpeed then return false end
    return true
end

CreateThread(function()
    if not G or not G.enabled then return end
    while true do
        Wait(math.random(G.interval[1], G.interval[2]) * 1000)
        if Ghosts.count < G.maxActive and halloweenLive() and Events.contestOpen('halloween') then
            local now, pool = os.time(), {}
            for src, player in pairs(exports.qbx_core:GetQBPlayers()) do
                if eligible(src, player, now) then pool[#pool + 1] = src end
            end
            local src = pool[math.random(#pool > 0 and #pool or 1)]
            if src and Events.worldLeft(src) > 0 then Ghosts.spawnFor(src) end
        end
    end
end)

CreateThread(function() -- forget ghosts nobody caught
    while true do
        Wait(20000)
        local now = os.time()
        for id, g in pairs(Ghosts.active) do
            if now > g.expires + 15 then Ghosts.remove(id) end
        end
    end
end)

AddEventHandler('playerDropped', function()
    local src = source
    if Ghosts.byPlayer[src] then Ghosts.remove(Ghosts.byPlayer[src]) end
    Ghosts.last[src] = nil
end)

lib.callback.register('s2-holidays:ghost:catch', function(src, id)
    id = tonumber(id)
    local g = id and Ghosts.active[id]
    if not g then return { ok = false, final = true, msg = 'The ghost is gone.' } end
    if g.src ~= src then return { ok = false, msg = 'That ghost is not haunting you.' } end
    if os.time() > g.expires + 15 then
        Ghosts.remove(id)
        return { ok = false, final = true, msg = 'The ghost faded away.' }
    end
    local ped = GetPlayerPed(src)
    if not ped or ped == 0 or #(GetEntityCoords(ped) - g.coords) > G.catchRadius then
        return { ok = false, msg = 'Get closer to the ghost.' }
    end
    Ghosts.remove(id) -- removed before any await, so a second request can never pay out twice
    local res = Events.worldCatch(src)
    res.final = true
    return res
end)
