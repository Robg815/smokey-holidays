Config = {}

Config.Debug = false

Config.CashItem = 'cash'

Config.PropModels = {            -- change for what prop is needed for holiday (must have tstudios_legion_easter to use configured props)
    `tstudio_legionsquare_asset_egg01`,
    `tstudio_legionsquare_asset_egg02`,
    `tstudio_legionsquare_asset_egg03`,
    `tstudio_legionsquare_asset_egg04`,
    `tstudio_legionsquare_asset_egg05`,
    `tstudio_legionsquare_asset_egg06`,
    `tstudio_legionsquare_asset_egg07`,
    `tstudio_legionsquare_asset_egg08`,
    `tstudio_legionsquare_asset_egg09`,
    `tstudio_legionsquare_asset_egg10`,
    `prop_alien_egg_01`
}

Config.UseRare = true

Config.Admin = {
    LeaderboardCommand = 'holidayleaderboard',
    StatsCommand = 'myholidaystats',
    AcePermission = 'smokeyholidays.admin'
}

Config.Leaderboard = {
    EventKey = 'seasonal',
    Title = 'Holiday Leaderboard',
    StatsTitle = 'My Holiday Stats',
    NormalLabel = 'Collects',
    RareLabel = 'Rare Collects'
}

Config.Settings = {
    enabled = true,
    eventName = 'Holiday Hunt',

    interactionDistance = 2.0,
    maxCollectDistance = 3.0,
    collectDuration = 2500,
    scenario = 'PROP_HUMAN_BUM_BIN',

    respawnTime = 300,
    rareRespawnTime = 900,
    oneTimePerRestart = true,

    normalPoints = 1,

        rareCollectibles = {
        enabled = true,
        points = 5,
        rewardMultiplier = 2,

        normalGlow = {
            enabled = true,
            markerType = 1,
            markerScale = vec3(0.12, 0.12, 0.05),
            markerColor = { r = 120, g = 200, b = 255, a = 90 },
            lightColor = { r = 120, g = 200, b = 255 },
            lightRange = 1.75,
            lightIntensity = 2.5
        }, 

        glow = {
            enabled = true,
            markerType = 1,
            markerScale = vec3(0.18, 0.18, 0.08),
            markerColor = { r = 255, g = 215, b = 0, a = 180 },
            lightColor = { r = 255, g = 215, b = 80 },
            lightRange = 3.5,
            lightIntensity = 5.0
        },

        particles = {
            enabled = true,
            dict = 'core',
            name = 'ent_amb_sparking_wires_sp',
            scale = 0.20,
            offset = vec3(0.0, 0.0, -0.18),
            rotation = vec3(0.0, 0.0, 0.0)
        },

        rewards = {
            { type = 'item', name = 'repairkit', amount = 1, chance = 25 },
            { type = 'item', name = 'advancedlockpick', amount = 1, chance = 15 },
            { type = 'item', name = 'cash', amount = 1500, chance = 35 },
            { type = 'item', name = 'goldbar', amount = 1, chance = 15 },
            { type = 'item', name = 'medikit', amount = 1, chance = 10 }
        }
    }, 

    rewards = {
        { type = 'item', name = 'lc_coffee', amount = 1, chance = 20 },
        { type = 'item', name = 'lcgumbo', amount = 1, chance = 20 },
        { type = 'item', name = 'bandage', amount = 1, chance = 20 },
        { type = 'item', name = 'lockpick', amount = 1, chance = 10 },
        { type = 'item', name = 'cash', amount = 1000, chance = 10 },
        { type = 'item', name = 'cash', amount = 500, chance = 20 }
    }
}

Config.Coords = {
    [1] = { coords = vec3(182.92, -886.03, 29.21), heading = 0.0, rare = true },
    [2] = { coords = vec3(184.0253, -987.8967, 30.9098), heading = 0.0, rare = false },
    [3] = { coords = vec3(161.8425, -948.7531, 31.4095), heading = 0.0, rare = false },
    [4] = { coords = vec3(185.7218, -894.9673, 30.2113), heading = 0.0, rare = true },
    [5] = { coords = vec3(250.1366, -890.5364, 30.0377), heading = 0.0, rare = false },
    [6] = { coords = vec3(21.2130, -832.6239, 31.2661), heading = 0.0, rare = false },
    [7] = { coords = vec3(54.3495, -594.9211, 32.5827), heading = 0.0, rare = false },
    [8] = { coords = vec3(124.8617, -866.7628, 37.0431), heading = 0.0, rare = false },
    [9] = { coords = vec3(-2010.8252, -1326.1555, 2.5225), heading = 0.0, rare = false },
    [10] = { coords = vec3(-1917.3616, -1373.4999, 3.1613), heading = 0.0, rare = false },
    [11] = { coords = vec3(-1840.3177, -1339.7457, 1.6222), heading = 0.0, rare = false },
    [12] = { coords = vec3(-1830.9971, -1314.6339, 2.5024), heading = 0.0, rare = false },
    [13] = { coords = vec3(-1639.2811, -1070.6792, 13.1539), heading = 0.0, rare = false },
    [14] = { coords = vec3(-1474.1632, -959.3866, 10.1930), heading = 0.0, rare = false },
    [15] = { coords = vec3(-1555.8093, -1151.6647, 2.3379), heading = 0.0, rare = false },
    [16] = { coords = vec3(-1177.6646, -314.0897, 38.3075), heading = 0.0, rare = false },
    [17] = { coords = vec3(359.8471, -992.0363, 29.3451), heading = 0.0, rare = false },
    [18] = { coords = vec3(300.0072, -969.1445, 29.3856), heading = 0.0, rare = false },
    [19] = { coords = vec3(255.3408, -1016.6566, 29.6928), heading = 0.0, rare = false },
    [20] = { coords = vec3(144.1275, -1534.9612, 29.1417), heading = 0.0, rare = false },
    [21] = { coords = vec3(-51.6798, -1740.7732, 29.6400), heading = 0.0, rare = false },
    [22] = { coords = vec3(63.2235, -1852.8613, 22.8478), heading = 0.0, rare = false },
    [23] = { coords = vec3(558.2983, -892.7911, 13.2657), heading = 0.0, rare = false },
    [24] = { coords = vec3(891.3182, -175.2380, 22.8719), heading = 0.0, rare = false },
    [25] = { coords = vec3(617.6639, -415.3621, -1.2256), heading = 0.0, rare = false },
    [26] = { coords = vec3(301.8468, -1204.2306, 38.8924), heading = 0.0, rare = false },
    [27] = { coords = vec3(681.4825, -996.9814, 22.9111), heading = 0.0, rare = false },
    [28] = { coords = vec3(675.1328, -930.8517, 22.2361), heading = 0.0, rare = false },
    [29] = { coords = vec3(948.0574, 96.0657, 80.8748), heading = 0.0, rare = false },
    [30] = { coords = vec3(286.5584, 213.4559, 104.7229), heading = 0.0, rare = false }
}
