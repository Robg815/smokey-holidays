local CollectibleState = {}
local PlayerCollected = {}

local function debugPrint(...)
    if Config.Debug then
        print('[smokey-holidays]', ...)
    end
end

local function eventConfig()
    return Config.Settings or {}
end

local function leaderboardConfig()
    return Config.Leaderboard or {}
end

local function leaderboardKey()
    return leaderboardConfig().EventKey or 'seasonal'
end

local function notify(src, description, ntype, duration)
    TriggerClientEvent('smokey-holidays:client:notify', src, {
        title = eventConfig().eventName or 'Holiday Event',
        description = description,
        type = ntype or 'inform',
        duration = duration or 5000
    })
end

local function getIdentifier(src)
    for _, identifier in ipairs(GetPlayerIdentifiers(src)) do
        if identifier:find('license:') then
            return identifier
        end
    end

    return ('src:%s'):format(src)
end

local function getPlayerNameSafe(src)
    local name = GetPlayerName(src)
    return (name and name ~= '') and name or ('Player %s'):format(src)
end

local function cloneTable(tbl)
    local new = {}
    for k, v in pairs(tbl or {}) do
        new[k] = v
    end
    return new
end

local function normalizeReward(reward)
    if not reward then return nil end

    local normalized = cloneTable(reward)
    if normalized.type == 'money' then
        normalized.type = 'item'
        normalized.name = Config.CashItem or 'cash'
        normalized.account = nil
    end

    return normalized
end

local function getRandomReward(rewards)
    if not rewards or #rewards == 0 then return nil end

    local totalChance = 0
    for i = 1, #rewards do
        totalChance = totalChance + (rewards[i].chance or 0)
    end

    if totalChance <= 0 then
        return rewards[1]
    end

    local roll = math.random(1, totalChance)
    local current = 0

    for i = 1, #rewards do
        current = current + (rewards[i].chance or 0)
        if roll <= current then
            return rewards[i]
        end
    end

    return rewards[1]
end

local function getItemLabel(itemName)
    local items = exports.ox_inventory:Items()
    local itemData = items and items[itemName]
    return (itemData and itemData.label) or itemName or 'Unknown Item'
end

local function rewardPlayer(src, reward, isRare)
    reward = normalizeReward(reward)

    if not reward or reward.type ~= 'item' or not reward.name then
        notify(src, 'Invalid reward configuration.', 'error')
        return false
    end

    local amount = reward.amount or 1
    if isRare then
        local rareCfg = eventConfig().rareCollectibles
        amount = amount * ((rareCfg and rareCfg.rewardMultiplier) or 1)
    end

    local added = exports.ox_inventory:AddItem(src, reward.name, amount)
    if not added then
        notify(src, 'Could not receive reward. Your inventory may be full.', 'error')
        return false
    end

    notify(src, ('You found %sx %s%s'):format(
        amount,
        getItemLabel(reward.name),
        isRare and ' from a rare item!' or ''
    ), 'success')

    return true
end

local function getCollectibleConfig(index)
    return Config.Coords and Config.Coords[index]
end

local function getPointsForCollectible(isRare)
    local cfg = eventConfig()
    if isRare then
        return (cfg.rareCollectibles and cfg.rareCollectibles.points) or 5
    end
    return cfg.normalPoints or 1
end

local function getRewardForCollectible(collectibleConfig)
    local cfg = eventConfig()
    if collectibleConfig.rare and cfg.rareCollectibles and cfg.rareCollectibles.enabled then
        return getRandomReward(cfg.rareCollectibles.rewards), true
    end
    return getRandomReward(cfg.rewards), false
end

local function buildPublicState()
    local payload = {}
    for index, collectible in pairs(CollectibleState) do
        payload[index] = {
            index = index,
            coords = collectible.coords,
            heading = collectible.heading,
            model = collectible.model,
            rare = collectible.rare,
            collected = collectible.collected
        }
    end
    return payload
end

local function buildCollectedStateForPlayer(src)
    local state = {}
    local cfg = eventConfig()
    local identifier = getIdentifier(src)

    PlayerCollected[identifier] = PlayerCollected[identifier] or {}

    for index, collectible in pairs(CollectibleState) do
        local alreadyCollected = cfg.oneTimePerRestart and PlayerCollected[identifier][index] == true
        state[index] = collectible.collected or alreadyCollected
    end

    return state
end

local function syncState(target)
    TriggerClientEvent('smokey-holidays:client:syncEggs', target or -1, buildPublicState())
end

local function syncPlayerState(src)
    TriggerClientEvent('smokey-holidays:client:setCollectedState', src, buildCollectedStateForPlayer(src))
    TriggerClientEvent('smokey-holidays:client:syncEggs', src, buildPublicState())
end

local function addLeaderboardProgress(src, isRare)
    local identifier = getIdentifier(src)
    local playerName = getPlayerNameSafe(src)

    local normalCollects = isRare and 0 or 1
    local rareCollects = isRare and 1 or 0
    local totalPoints = getPointsForCollectible(isRare)

    MySQL.insert([[ 
        INSERT INTO smokey_holiday_leaderboard
            (holiday, identifier, player_name, normal_eggs, rare_eggs, total_points, last_collect)
        VALUES
            (?, ?, ?, ?, ?, ?, NOW())
        ON DUPLICATE KEY UPDATE
            player_name = VALUES(player_name),
            normal_eggs = normal_eggs + VALUES(normal_eggs),
            rare_eggs = rare_eggs + VALUES(rare_eggs),
            total_points = total_points + VALUES(total_points),
            last_collect = NOW()
    ]], {
        leaderboardKey(),
        identifier,
        playerName,
        normalCollects,
        rareCollects,
        totalPoints
    })
end

local function isAdmin(src)
    return IsPlayerAceAllowed(src, Config.Admin.AcePermission)
end

local function initializeState()
    local cfg = eventConfig()
    if not cfg.enabled then
        print('[smokey-holidays] system disabled or config missing')
        return
    end

    CollectibleState = {}

    for index, collectibleCfg in pairs(Config.Coords or {}) do
        CollectibleState[index] = {
            index = index,
            coords = collectibleCfg.coords,
            heading = collectibleCfg.heading or 0.0,
            model = (Config.PropModels and Config.PropModels[1]) or Config.PropModel,
            rare = collectibleCfg.rare == true,
            collected = false
        }
    end

    debugPrint('Initialized collectible state')
    syncState(-1)
end

local function respawnCollectible(index)
    local collectible = CollectibleState[index]
    if not collectible then return end
    collectible.collected = false
    syncState(-1)
end

local function scheduleRespawnCollectible(index)
    local collectible = CollectibleState[index]
    local cfg = eventConfig()
    if not collectible or not cfg then return end

    local delay = collectible.rare and (cfg.rareRespawnTime or cfg.respawnTime or 300) or (cfg.respawnTime or 300)

    SetTimeout(delay * 1000, function()
        respawnCollectible(index)
    end)
end

CreateThread(function()
    Wait(1000)
    initializeState()
end)

RegisterNetEvent('smokey-holidays:server:requestState', function()
    local src = source
    local cfg = eventConfig()
    if not cfg.enabled then return end
    syncPlayerState(src)
end)

RegisterNetEvent('smokey-holidays:server:collectCollectible', function(index)
    local src = source
    local cfg = eventConfig()
    if not cfg.enabled then return end

    index = tonumber(index)

    local collectible = CollectibleState[index]
    local collectibleCfg = getCollectibleConfig(index)

    if not collectible or not collectibleCfg then
        debugPrint(('Rejected collect from %s invalid index %s'):format(src, tostring(index)))
        return
    end

    if collectible.collected then
        debugPrint(('Rejected collect from %s item %s already collected'):format(src, index))
        return
    end

    local ped = GetPlayerPed(src)
    if not ped or ped == 0 then
        debugPrint(('Rejected collect from %s missing ped'):format(src))
        return
    end

    local playerCoords = GetEntityCoords(ped)
    local distToConfig = #(playerCoords - collectibleCfg.coords)

    if distToConfig > (cfg.maxCollectDistance or 3.0) then
        debugPrint(('Rejected collect from %s too far from config %.2f'):format(src, distToConfig))
        return
    end

    local identifier = getIdentifier(src)
    PlayerCollected[identifier] = PlayerCollected[identifier] or {}

    if cfg.oneTimePerRestart and PlayerCollected[identifier][index] then
        notify(src, 'You already collected this item.', 'error')
        return
    end

    local reward, isRare = getRewardForCollectible(collectibleCfg)
    local rewarded = rewardPlayer(src, reward, isRare)
    if not rewarded then return end

    PlayerCollected[identifier][index] = true
    collectible.collected = true

    addLeaderboardProgress(src, isRare)

    syncState(-1)
    syncPlayerState(src)
    TriggerClientEvent('smokey-holidays:client:playCollectFx', -1, index, collectibleCfg.coords, isRare)

    scheduleRespawnCollectible(index)
end)

RegisterCommand(Config.Admin.LeaderboardCommand, function(source)
    local rows = MySQL.query.await([[ 
        SELECT player_name, normal_eggs AS normal_collects, rare_eggs AS rare_collects, total_points
        FROM smokey_holiday_leaderboard
        WHERE holiday = ?
        ORDER BY total_points DESC, rare_eggs DESC, normal_eggs DESC, updated_at ASC
        LIMIT 50
    ]], { leaderboardKey() })

    if source == 0 then
        print(('----- %s -----'):format(leaderboardConfig().Title or 'Holiday Leaderboard'))
        if not rows or #rows == 0 then
            print('No entries found.')
            return
        end

        for i = 1, #rows do
            local row = rows[i]
            print(('#%s %s | Collects: %s | Rare: %s | Points: %s'):format(
                i,
                row.player_name or 'Unknown',
                row.normal_collects or 0,
                row.rare_collects or 0,
                row.total_points or 0
            ))
        end

        return
    end

    if not isAdmin(source) then
        notify(source, 'You do not have permission to open the leaderboard.', 'error')
        return
    end

    TriggerClientEvent('smokey-holidays:client:openLeaderboard', source, rows or {})
end, false)

RegisterCommand(Config.Admin.StatsCommand, function(source)
    if source == 0 then return end

    local identifier = getIdentifier(source)

    local row = MySQL.single.await([[ 
        SELECT player_name, normal_eggs AS normal_collects, rare_eggs AS rare_collects, total_points, last_collect
        FROM smokey_holiday_leaderboard
        WHERE holiday = ? AND identifier = ?
        LIMIT 1
    ]], { leaderboardKey(), identifier })

    local rankRow = MySQL.single.await([[ 
        SELECT ranked.rank_pos
        FROM (
            SELECT identifier,
                   ROW_NUMBER() OVER (ORDER BY total_points DESC, rare_eggs DESC, normal_eggs DESC, updated_at ASC) AS rank_pos
            FROM smokey_holiday_leaderboard
            WHERE holiday = ?
        ) AS ranked
        WHERE ranked.identifier = ?
        LIMIT 1
    ]], { leaderboardKey(), identifier })

    TriggerClientEvent('smokey-holidays:client:openMyStats', source, {
        normal_collects = row and row.normal_collects or 0,
        rare_collects = row and row.rare_collects or 0,
        total_points = row and row.total_points or 0,
        last_collect = row and tostring(row.last_collect) or 'Never',
        rank = rankRow and rankRow.rank_pos or 'Unranked'
    })
end, false)
