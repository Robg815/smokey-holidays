local EggState = {}
local CollectedState = {}
local SpawnedEntities = {}
local TargetedEntities = {}
local RareParticles = {}
local EggModels = {}

local function debugPrint(...)
    if Config.Debug then
        print('[smokey-holidays]', ...)
    end
end

local function loadModel(model)
    if not model then return false end

    if type(model) == 'string' then
        model = joaat(model)
    end

    if not IsModelInCdimage(model) then
        return false
    end

    RequestModel(model)
    local timeout = GetGameTimer() + 5000
    while not HasModelLoaded(model) do
        Wait(0)
        if GetGameTimer() > timeout then
            return false
        end
    end

    return model
end

local function loadPtfx(dict)
    if HasNamedPtfxAssetLoaded(dict) then
        return true
    end

    RequestNamedPtfxAsset(dict)
    local timeout = GetGameTimer() + 5000
    while not HasNamedPtfxAssetLoaded(dict) do
        Wait(0)
        if GetGameTimer() > timeout then
            return false
        end
    end

    return true
end

local function getEggModelForIndex(index)
    if EggModels[index] then
        return EggModels[index]
    end

    local models = Config.PropModels or {}
    if #models == 0 then
        return nil
    end

    local chosen = models[math.random(1, #models)]
    EggModels[index] = chosen
    return chosen
end

local function clearEggModelCache()
    EggModels = {}
end

local function stopRareParticle(index)
    if RareParticles[index] then
        StopParticleFxLooped(RareParticles[index], false)
        RareParticles[index] = nil
    end
end

local function startRareParticle(index, entity)
    local rareCfg = Config.Settings and Config.Settings.rareCollectibles
    if not rareCfg or not rareCfg.particles or not rareCfg.particles.enabled then return end
    if RareParticles[index] then return end
    if not entity or not DoesEntityExist(entity) then return end

    local p = rareCfg.particles
    if not loadPtfx(p.dict) then return end

    UseParticleFxAssetNextCall(p.dict)
    RareParticles[index] = StartParticleFxLoopedOnEntity(
        p.name,
        entity,
        p.offset.x, p.offset.y, p.offset.z,
        p.rotation.x, p.rotation.y, p.rotation.z,
        p.scale or 0.25,
        false, false, false
    )
end

local function removeEggTarget(index)
    local targetedEntity = TargetedEntities[index]
    if targetedEntity and DoesEntityExist(targetedEntity) then
        exports.ox_target:removeLocalEntity(targetedEntity, ('smokey_holidays_collectible_%s'):format(index))
    end
    TargetedEntities[index] = nil
end

local function clearEgg(index)
    stopRareParticle(index)
    removeEggTarget(index)

    local entity = SpawnedEntities[index]
    if entity and DoesEntityExist(entity) then
        DeleteObject(entity)
    end

    SpawnedEntities[index] = nil
end

local function canInteractEgg(index)
    local state = EggState[index]
    if not state then return false end
    if state.collected then return false end
    if CollectedState[index] then return false end
    return true
end

local function tryCollectItem(index)
    local cfg = Config.Settings or {}
    local state = EggState[index]
    if not cfg.enabled or not state then return end
    if not canInteractEgg(index) then return end

    local entity = SpawnedEntities[index]
    if not entity or not DoesEntityExist(entity) then return end

    local ped = PlayerPedId()
    local pedCoords = GetEntityCoords(ped)
    local eggCoords = GetEntityCoords(entity)

    if #(pedCoords - eggCoords) > ((cfg.interactionDistance or 2.0) + 1.0) then
        return
    end

    local success = lib.progressCircle({
        duration = cfg.collectDuration or 2500,
        position = 'bottom',
        label = state.rare and 'Collecting rare holiday item...' or 'Collecting holiday item...',
        useWhileDead = false,
        canCancel = true,
        disable = {
            move = true,
            car = true,
            combat = true,
            mouse = false
        },
        anim = false,
        scenario = cfg.scenario or 'PROP_HUMAN_BUM_BIN'
    })

    ClearPedTasks(ped)

    if not success then
        return
    end

    TriggerServerEvent('smokey-holidays:server:collectCollectible', index)
end

local function addEggTarget(index, entity, isRare)
    if not entity or not DoesEntityExist(entity) then return end

    local currentTargetEntity = TargetedEntities[index]
    if currentTargetEntity and currentTargetEntity == entity and DoesEntityExist(currentTargetEntity) then
        return
    end

    if currentTargetEntity and DoesEntityExist(currentTargetEntity) then
        exports.ox_target:removeLocalEntity(currentTargetEntity, ('smokey_holidays_collectible_%s'):format(index))
    end

    exports.ox_target:addLocalEntity(entity, {
        {
            name = ('smokey_holidays_collectible_%s'):format(index),
            icon = isRare and 'fa-solid fa-star' or 'fa-solid fa-gift',
            label = isRare and 'Collect Rare Holiday Item' or 'Collect Holiday Item',
            distance = (Config.Settings and Config.Settings.interactionDistance) or 2.0,
            canInteract = function()
                return canInteractEgg(index)
            end,
            onSelect = function()
                tryCollectItem(index)
            end
        }
    })

    TargetedEntities[index] = entity
end

local function spawnLocalEgg(index, state)
    if SpawnedEntities[index] and DoesEntityExist(SpawnedEntities[index]) then
        addEggTarget(index, SpawnedEntities[index], state.rare == true)
        return
    end

    local modelName = getEggModelForIndex(index)
    if not modelName then
        debugPrint(('no prop models configured for index %s'):format(index))
        return
    end

    local model = loadModel(modelName)
    if not model then
        debugPrint(('failed to load prop model for index %s'):format(index))
        return
    end

    local coords = state.coords
    local entity = CreateObject(model, coords.x, coords.y, coords.z - 0.98, false, false, false)
    if not entity or entity == 0 then
        return
    end

    SetEntityHeading(entity, state.heading or 0.0)
    FreezeEntityPosition(entity, true)
    SetEntityAsMissionEntity(entity, true, true)
    PlaceObjectOnGroundProperly(entity)

    SpawnedEntities[index] = entity

    if state.rare then
        startRareParticle(index, entity)
    end

    addEggTarget(index, entity, state.rare == true)
end

local function refreshEgg(index)
    local state = EggState[index]
    if not state or state.collected then
        clearEgg(index)
        return
    end

    spawnLocalEgg(index, state)
end

local function refreshAllEggs()
    for index in pairs(EggState) do
        refreshEgg(index)
    end

    for index in pairs(SpawnedEntities) do
        if not EggState[index] or EggState[index].collected then
            clearEgg(index)
        end
    end
end

RegisterNetEvent('smokey-holidays:client:notify', function(data)
    lib.notify(data)
end)

RegisterNetEvent('smokey-holidays:client:setCollectedState', function(state)
    CollectedState = state or {}
    refreshAllEggs()
end)

RegisterNetEvent('smokey-holidays:client:syncEggs', function(payload)
    EggState = payload or {}
    refreshAllEggs()
end)

RegisterNetEvent('smokey-holidays:client:playCollectFx', function(index, coords, isRare)
    if not coords then return end

    if isRare then
        local rareCfg = Config.Settings and Config.Settings.rareCollectibles
        if rareCfg and rareCfg.particles and rareCfg.particles.enabled then
            local p = rareCfg.particles
            if loadPtfx(p.dict) then
                UseParticleFxAssetNextCall(p.dict)
                StartParticleFxNonLoopedAtCoord(
                    p.name,
                    coords.x, coords.y, coords.z + 0.05,
                    0.0, 0.0, 0.0,
                    p.scale or 0.35,
                    false, false, false
                )
            end
        end
    end
end)

RegisterNetEvent('smokey-holidays:client:openLeaderboard', function(rows)
    local options = {}

    if not rows or #rows == 0 then
        options[#options + 1] = {
            title = 'No entries found',
            description = 'Nobody has collected any holiday items yet.',
            icon = 'circle-info'
        }
    else
        for i = 1, #rows do
            local row = rows[i]
            local boardCfg = Config.Leaderboard or {}
            options[#options + 1] = {
                title = ('#%s %s'):format(i, row.player_name or 'Unknown'),
                description = ('%s: %s | %s: %s | Points: %s'):format(
                    boardCfg.NormalLabel or 'Collects',
                    row.normal_collects or 0,
                    boardCfg.RareLabel or 'Rare Collects',
                    row.rare_collects or 0,
                    row.total_points or 0
                ),
                icon = 'trophy'
            }
        end
    end

    lib.registerContext({
        id = 'smokey_holidays_leaderboard',
        title = (Config.Leaderboard and Config.Leaderboard.Title) or 'Holiday Leaderboard',
        options = options
    })

    lib.showContext('smokey_holidays_leaderboard')
end)

RegisterNetEvent('smokey-holidays:client:openMyStats', function(data)
    lib.registerContext({
        id = 'smokey_holidays_my_stats',
        title = (Config.Leaderboard and Config.Leaderboard.StatsTitle) or 'My Holiday Stats',
        options = {
            { title = 'Rank', description = tostring(data.rank or 'Unranked'), icon = 'ranking-star' },
            { title = (Config.Leaderboard and Config.Leaderboard.NormalLabel) or 'Collects', description = tostring(data.normal_collects or 0), icon = 'gift' },
            { title = (Config.Leaderboard and Config.Leaderboard.RareLabel) or 'Rare Collects', description = tostring(data.rare_collects or 0), icon = 'star' },
            { title = 'Total Points', description = tostring(data.total_points or 0), icon = 'trophy' },
            { title = 'Last Collect', description = tostring(data.last_collect or 'Never'), icon = 'clock' }
        }
    })

    lib.showContext('smokey_holidays_my_stats')
end)

CreateThread(function()
    while true do
        Wait(1000)
        if Config.Settings and Config.Settings.enabled then
            refreshAllEggs()
        end
    end
end)

CreateThread(function()
    while true do
        local sleep = 1000
        local pedCoords = GetEntityCoords(PlayerPedId())

        local normalGlowCfg = Config.Settings and Config.Settings.normalGlow
        local rareCfg = Config.Settings and Config.Settings.rareCollectibles
        local rareGlowCfg = rareCfg and rareCfg.glow

        for index, entity in pairs(SpawnedEntities) do
            local state = EggState[index]

            if state and entity and DoesEntityExist(entity) and not state.collected then
                local entityCoords = GetEntityCoords(entity)
                local dist = #(pedCoords - entityCoords)

                if dist < 20.0 then
                    local glowCfg = nil

                    if state.rare and rareGlowCfg and rareGlowCfg.enabled then
                        glowCfg = rareGlowCfg
                    elseif not state.rare and normalGlowCfg and normalGlowCfg.enabled then
                        glowCfg = normalGlowCfg
                    end

                    if glowCfg then
                        sleep = 0

                        local minDim, maxDim = GetModelDimensions(GetEntityModel(entity))
                        local bottomZ = entityCoords.z + minDim.z + 0.02
                        local lightZ = bottomZ + 0.06

                        DrawMarker(
                            glowCfg.markerType or 1,
                            entityCoords.x, entityCoords.y, bottomZ,
                            0.0, 0.0, 0.0,
                            0.0, 0.0, 0.0,
                            glowCfg.markerScale.x, glowCfg.markerScale.y, glowCfg.markerScale.z,
                            glowCfg.markerColor.r, glowCfg.markerColor.g, glowCfg.markerColor.b, glowCfg.markerColor.a,
                            false, true, 2, false, nil, nil, false
                        )

                        DrawLightWithRange(
                            entityCoords.x, entityCoords.y, lightZ,
                            glowCfg.lightColor.r, glowCfg.lightColor.g, glowCfg.lightColor.b,
                            glowCfg.lightRange or 2.0,
                            glowCfg.lightIntensity or 1.0
                        )
                    end
                end
            end
        end

        Wait(sleep)
    end
end)

CreateThread(function()
    Wait(1500)
    math.randomseed(GetGameTimer())
    TriggerServerEvent('smokey-holidays:server:requestState')
end)

AddEventHandler('onResourceStop', function(resource)
    if resource ~= GetCurrentResourceName() then return end
    for index in pairs(SpawnedEntities) do
        clearEgg(index)
    end
    clearEggModelCache()
end)