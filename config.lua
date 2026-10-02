Config = {}

Config.Command = 'holidays'
Config.Key = 'F7'                 -- default keybind (players can rebind in settings)
Config.UtcOffset = nil            -- nil = server local time, or a number of hours from UTC (e.g. -6)
Config.UseObservedDates = true    -- federal fixed-date holidays shift to Fri/Mon when on a weekend
Config.LoginNotify = true         -- tell players about active holidays when they load in
Config.DebugDate = nil            -- 'YYYY-MM-DD' to fake today's date for testing, e.g. '2026-12-12'

Config.DefaultWindow = { before = 1, after = 0 } -- days a holiday counts as "active" around its date

-- Hologram colours. a = main projection colour, b = highlight/ready colour.
Config.Themes = {
    default      = { a = '#5ff3ff', b = '#8affc7' },
    winter       = { a = '#8fd8ff', b = '#ffffff' },
    christmas    = { a = '#ff5a6e', b = '#6dffb0' },
    halloween    = { a = '#ff8a1f', b = '#b06cff' },
    patriotic    = { a = '#5b8cff', b = '#ff6b6b' },
    autumn       = { a = '#ffb347', b = '#ff7a45' },
    valentines   = { a = '#ff6fb5', b = '#ffc2e0' },
    stpatricks   = { a = '#4dff8a', b = '#e6ff7a' },
    spring       = { a = '#c79bff', b = '#8affc7' },
    memorial     = { a = '#7fa8ff', b = '#ff7a7a' },
}

-- Rule types:
--   { type = 'fixed',  month = 7, day = 4 }
--   { type = 'nth',    month = 11, weekday = 4, n = 4 }   weekday: 0 = Sunday ... 6 = Saturday
--   { type = 'last',   month = 5, weekday = 1 }
--   { type = 'easter', offset = 0 }
-- Optional per holiday: before / after (window in days), federal (enables observed shifting), enabled = false
Config.Holidays = {
    { id = 'new_years',    label = "New Year's Day",             federal = true, theme = 'winter',     rule = { type = 'fixed', month = 1, day = 1 },            blurb = 'A fresh year on the streets of Los Santos.' },
    { id = 'mlk',          label = 'Martin Luther King Jr. Day', federal = true, theme = 'default',    rule = { type = 'nth', month = 1, weekday = 1, n = 3 },   blurb = 'A day on, not a day off.' },
    { id = 'valentines',   label = "Valentine's Day",            theme = 'valentines', rule = { type = 'fixed', month = 2, day = 14 },                          blurb = 'Flowers, dinners and questionable decisions.' },
    { id = 'presidents',   label = "Presidents' Day",            federal = true, theme = 'patriotic',  rule = { type = 'nth', month = 2, weekday = 1, n = 3 },   blurb = 'Big sales at every dealership in town.' },
    { id = 'stpatricks',   label = "St. Patrick's Day",          theme = 'stpatricks', rule = { type = 'fixed', month = 3, day = 17 },                          blurb = 'Green everything. Pubs will be busy.' },
    { id = 'easter',       label = 'Easter',                     theme = 'spring',     rule = { type = 'easter', offset = 0 }, before = 2,                      blurb = 'Egg hunts across the city.' },
    { id = 'mothers_day',  label = "Mother's Day",               theme = 'valentines', rule = { type = 'nth', month = 5, weekday = 0, n = 2 },                  blurb = 'Call your mom. Seriously.' },
    { id = 'memorial',     label = 'Memorial Day',               federal = true, theme = 'memorial',   rule = { type = 'last', month = 5, weekday = 1 },         blurb = 'Remembering those who served.' },
    { id = 'juneteenth',   label = 'Juneteenth',                 federal = true, theme = 'patriotic',  rule = { type = 'fixed', month = 6, day = 19 },           blurb = 'Freedom Day celebrations across the state.' },
    { id = 'fathers_day',  label = "Father's Day",               theme = 'default',    rule = { type = 'nth', month = 6, weekday = 0, n = 3 },                  blurb = 'Grills are lit. Dad jokes are mandatory.' },
    { id = 'independence', label = 'Independence Day',           federal = true, theme = 'patriotic',  rule = { type = 'fixed', month = 7, day = 4 }, before = 2, after = 1, blurb = 'Fireworks over the pier tonight.' },
    { id = 'labor',        label = 'Labor Day',                  federal = true, theme = 'autumn',     rule = { type = 'nth', month = 9, weekday = 1, n = 1 },   blurb = 'Last long weekend of summer.' },
    { id = 'columbus',     label = "Columbus / Indigenous Peoples' Day", federal = true, theme = 'autumn', rule = { type = 'nth', month = 10, weekday = 1, n = 2 }, blurb = 'Federal holiday. Government offices are closed.' },
    { id = 'halloween',    label = 'Halloween',                  theme = 'halloween',  rule = { type = 'fixed', month = 10, day = 31 }, before = 30, after = 7,  blurb = 'The city is not as empty as it looks after dark.' },
    { id = 'veterans',     label = 'Veterans Day',               federal = true, theme = 'memorial',   rule = { type = 'fixed', month = 11, day = 11 },          blurb = 'Honoring all who served.' },
    { id = 'thanksgiving', label = 'Thanksgiving',               federal = true, theme = 'autumn',     rule = { type = 'nth', month = 11, weekday = 4, n = 4 }, before = 2, after = 1, blurb = 'Turkey, family and a lot of traffic.' },
    { id = 'christmas',    label = 'Christmas',                  federal = true, theme = 'christmas',  rule = { type = 'fixed', month = 12, day = 25 }, before = 24, after = 1, blurb = 'Snow on the pier, lights on every block.' },
    { id = 'new_years_eve',label = "New Year's Eve",             theme = 'winter',     rule = { type = 'fixed', month = 12, day = 31 },                         blurb = 'Countdown at midnight.' },
}

-- Advent calendar (shown while the Christmas window is active)
Config.Advent = {
    enabled = true,
    startMonth = 12, startDay = 1,
    days = 24,
    requiredMinutes = 30,          -- minutes online that same day before a door can be opened
    overrides = { [24] = 60 },     -- per-door override of requiredMinutes
    allowCatchUp = false,          -- true = missed doors can still be opened later in the season
    skin = 'wood',                 -- 'wood' (matches the reference) or 'holo' (glass drawers with line art)
    images = { [1] = 'img/door1.svg', [4] = 'img/door4.svg', [5] = 'img/door5.svg', [7] = 'img/door7.svg', [8] = 'img/door8.svg', [11] = 'img/door11.svg', [12] = 'img/door12.svg', [13] = 'img/door13.svg', [16] = 'img/door16.svg', [19] = 'img/door19.svg', [22] = 'img/door22.svg' }, -- optional custom art per door, e.g. [1] = 'img/door1.png' (put files in web/img/)
    -- Drawer layout: one row per line, { door number, relative width, optional 'flip' to put the art on the left }. Any arrangement works as long as every door appears once.
    layout = {
        { {1, 4.6}, {2, 2.4}, {3, 2.4}, {4, 4.4} },
        { {5, 2.4}, {6, 2.4}, {7, 4.4, 'flip'}, {8, 4.3} },
        { {9, 2.3}, {10, 1.6}, {11, 2.4, 'flip'}, {12, 4.4, 'flip'}, {13, 2.4} },
        { {14, 1.6}, {15, 1.6}, {16, 4.4, 'flip'}, {17, 1.8}, {18, 1.6}, {19, 2.5, 'flip'} },
        { {20, 1.6}, {21, 4.4}, {22, 4.4, 'flip'}, {23, 1.7}, {24, 1.7} },
    },
    -- Icon per door (in door order). Available: snowflake star bell gift holly candycane wreath tree snowman hat ornament deer poinsettia ho
    icons = { 'snowflake', 'snowflake', 'snowflake', 'snowflake', 'snowflake', 'snowflake', 'snowflake', 'snowflake', 'snowflake', 'snowflake', 'snowflake', 'snowflake', 'snowflake', 'snowflake', 'snowflake', 'snowflake', 'snowflake', 'snowflake', 'snowflake', 'snowflake', 'ho', 'snowflake', 'snowflake', 'snowflake' },  -- pale snowflake decals on drawers without art
    rewards = {
        [1]  = { label = 'Snack pack',     items = { { name = 'sandwich', count = 2 }, { name = 'water', count = 2 } } },
        [2]  = { label = 'Pocket cash',    cash = 250 },
        [3]  = { label = 'First aid',      items = { { name = 'bandage', count = 3 } } },
        [4]  = { label = 'Hot cocoa',      items = { { name = 'cola', count = 3 } } },
        [5]  = { label = 'Lockpick',       items = { { name = 'lockpick', count = 1 } } },
        [6]  = { label = 'Stocking cash',  cash = 400 },
        [7]  = { label = 'Burger night',   items = { { name = 'burger', count = 3 } } },
        [8]  = { label = 'Radio',          items = { { name = 'radio', count = 1 } } },
        [9]  = { label = 'Cash gift',      cash = 500 },
        [10] = { label = 'Care package',   items = { { name = 'bandage', count = 5 }, { name = 'water', count = 3 } } },
        [11] = { label = 'Repair kit',     items = { { name = 'repairkit', count = 1 } } },
        [12] = { label = 'Cash gift',      cash = 750 },
        [13] = { label = 'Dinner',         items = { { name = 'burger', count = 2 }, { name = 'cola', count = 2 } } },
        [14] = { label = 'Lockpick set',   items = { { name = 'lockpick', count = 2 } } },
        [15] = { label = 'Cash gift',      cash = 900 },
        [16] = { label = 'Armor',          items = { { name = 'armour', count = 1 } } },
        [17] = { label = 'Snack pack',     items = { { name = 'sandwich', count = 4 } } },
        [18] = { label = 'Cash gift',      cash = 1000 },
        [19] = { label = 'Repair kits',    items = { { name = 'repairkit', count = 2 } } },
        [20] = { label = 'Phone upgrade',  items = { { name = 'phone', count = 1 } } },
        [21] = { label = 'Cash gift',      cash = 1250 },
        [22] = { label = 'Armor pair',     items = { { name = 'armour', count = 2 } } },
        [23] = { label = 'Cash gift',      cash = 1500 },
        [24] = { label = 'Christmas Eve',  cash = 3000, items = { { name = 'armour', count = 2 }, { name = 'repairkit', count = 2 } } },
    },
}

-- ==========================================================================
-- Per-holiday experiences. The server rolls every outcome; the UI only shows it.
--   kind = 'spots'  N things to open (doors, envelopes, eggs...), `picks` per day, weighted outcomes
--   kind = 'feast'  dishes unlocked by playtime, then a finale
-- Outcome kinds the UI reacts to: 'trick' = jump scare, 'empty'/'dud' = nothing, 'ghost' = ghost, anything else = a win.
-- Items must exist in ox_inventory; swap in your own (candy, roses, fireworks...).
-- ==========================================================================
Config.Events = {
    halloween = {
        kind = 'spots', title = 'Trick or Treat', spots = 5, picks = 5, -- 5 houses per night, all October
        outcomes = {
            { kind = 'treat', weight = 55, label = 'Candy haul',  points = 10, cash = 150, items = { { name = 'sandwich', count = 1 } }, msg = 'Full-size bars. Jackpot.' },
            { kind = 'trick', weight = 25, label = 'Jump scare',  points = 5,  cash = 50,  msg = 'Something jumped out. Here is a little hush money.' },
            { kind = 'ghost', weight = 8,  label = 'Ghost loot',  points = 25, cash = 600, msg = 'A ghost slipped you something.' },
            { kind = 'empty', weight = 12, label = 'Nobody home', points = 1,  msg = 'The lights are off. Nobody is home... probably.' },
        },
        -- The ghost that drifts across the trick-or-treat screen (once per night)
        ghostCatch = { label = 'Caught a ghost', points = 20, cash = 400, items = { { name = 'bandage', count = 2 } }, msg = 'It squeaked, then vanished.' },

        -- Points add up all month. The board closes at the end of `endsDay`; the top finishers can claim a prize until the window ends.
        contest = {
            endsMonth = 10, endsDay = 31, endsHour = 24, -- 24 = midnight at the end of Halloween night
            boardSize = 10,
            names = 'initial',                           -- how names show on the board: 'full' | 'initial' | 'none'
            hint = 'Treats +10, ghost loot +25, catch ghosts around the city +30.',
            prizes = {                                   -- index = final place
                { label = 'Halloween Champion', cash = 25000, items = { { name = 'armour', count = 3 } }, msg = 'You ruled the night. Congratulations!' },
                { label = 'Runner-up',          cash = 10000, items = { { name = 'armour', count = 1 } }, msg = 'So close. Impressive month.' },
                { label = 'Third place',        cash = 5000,  msg = 'On the podium. Well played.' },
            },
        },

        -- Ghosts caught out in the world (spawning rules live in Config.Ghosts)
        world = { label = 'Ghost caught', points = 30, cash = 250, items = { { name = 'bandage', count = 1 } }, perDay = 8, msg = 'It dissolved into a handful of cash.' },
    },
    valentines = {
        kind = 'spots', title = 'Secret Admirer', spots = 6, picks = 1,
        outcomes = {
            { kind = 'gift',    weight = 45, label = 'Chocolates',    items = { { name = 'sandwich', count = 2 } }, msg = 'A box of chocolates.' },
            { kind = 'cash',    weight = 35, label = 'Love note cash', cash = 500, msg = 'There was cash folded inside.' },
            { kind = 'jackpot', weight = 8,  label = 'Golden ticket',  cash = 2500, msg = 'Somebody really likes you.' },
            { kind = 'empty',   weight = 12, label = 'Wrong address',  msg = 'Return to sender.' },
        },
    },
    easter = {
        kind = 'spots', title = 'Egg Hunt', spots = 8, picks = 3,
        outcomes = {
            { kind = 'egg',    weight = 50, label = 'Pocket cash',   cash = 200, msg = 'A few dollars wrapped in foil.' },
            { kind = 'basket', weight = 20, label = 'Basket goodies', items = { { name = 'bandage', count = 2 }, { name = 'water', count = 2 } }, msg = 'Snacks and bandages.' },
            { kind = 'golden', weight = 6,  label = 'Golden egg',    cash = 1500, msg = 'A golden egg. Very rare.' },
            { kind = 'empty',  weight = 24, label = 'Cracked egg',   msg = 'Empty. Better luck with the next one.' },
        },
    },
    stpatricks = {
        kind = 'spots', title = 'Pot of Gold', spots = 5, picks = 2,
        outcomes = {
            { kind = 'coins', weight = 50, label = 'Gold coins',       cash = 300, msg = 'Shiny.' },
            { kind = 'lucky', weight = 10, label = 'Four-leaf clover', cash = 2000, msg = 'Luck of the Irish.' },
            { kind = 'dud',   weight = 40, label = 'Just clover',      msg = 'Nothing but clover.' },
        },
    },
    independence = {
        kind = 'spots', title = 'Fireworks Show', spots = 6, picks = 4,
        outcomes = {
            { kind = 'burst',  weight = 60, label = 'Big burst',   cash = 200, msg = 'Fireworks!' },
            { kind = 'finale', weight = 10, label = 'Grand finale', cash = 1500, items = { { name = 'radio', count = 1 } }, msg = 'The whole sky lit up.' },
            { kind = 'dud',    weight = 30, label = 'Fizzled',     msg = 'Dud. Try another one.' },
        },
    },
    thanksgiving = {
        kind = 'feast', title = 'The Feast',
        dishes = { -- need = minutes online today
            { id = 'turkey',    label = 'Roast turkey',    need = 5,  items = { { name = 'burger', count = 2 } },  msg = 'Golden brown.' },
            { id = 'stuffing',  label = 'Stuffing',        need = 10, items = { { name = 'sandwich', count = 2 } }, msg = 'Just like grandma made it.' },
            { id = 'pie',       label = 'Pumpkin pie',     need = 15, cash = 300, msg = 'Whipped cream on top.' },
            { id = 'corn',      label = 'Sweet corn',      need = 20, items = { { name = 'water', count = 2 } }, msg = 'Buttery.' },
            { id = 'rolls',     label = 'Dinner rolls',    need = 25, items = { { name = 'bandage', count = 2 } }, msg = 'Still warm.' },
            { id = 'cranberry', label = 'Cranberry sauce', need = 30, cash = 500, msg = 'From the can, ridges and all.' },
        },
        finale = { label = 'Give thanks', cash = 2000, items = { { name = 'armour', count = 1 } }, msg = 'Everyone at the table is thankful for you.' },
    },
}

-- New Year, remembrance and countdown experiences
Config.Events.new_years_eve = { kind = 'countdown', title = 'Midnight Countdown' } -- display only: the ball drops through the last hour

Config.Events.new_years = {
    kind = 'spots', title = 'Resolution Cards', spots = 3, picks = 1,
    outcomes = {
        { kind = 'gift',    weight = 40, label = 'Fresh start',       items = { { name = 'bandage', count = 2 }, { name = 'water', count = 2 } }, msg = 'Supplies for the year ahead.' },
        { kind = 'cash',    weight = 35, label = 'Savings goal',      cash = 800,  msg = 'A solid start to the year.' },
        { kind = 'jackpot', weight = 10, label = 'Lucky year',        cash = 3000, msg = 'This is your year.' },
        { kind = 'empty',   weight = 15, label = 'Same as last year', msg = 'Maybe next time.' },
    },
}

-- One candle per player per day. Add `reward = { cash = 100 }` if you want one; remembrance days work well without.
Config.Events.memorial = { kind = 'tribute', title = 'A Moment of Remembrance', text = 'Light a candle for those who gave everything.', thanks = 'Thank you for remembering.' }
Config.Events.veterans = { kind = 'tribute', title = 'Thank a Veteran', text = 'Light a candle for everyone who served.', thanks = 'Thank you for your support.' }

-- ==========================================================================
-- Ghosts in the world (Halloween). Deliberately conservative:
--  * a ghost only ever spawns near an online player, and only that player's client creates it (local ped, never networked)
--  * hard server-wide cap, per-player cooldown, and ghosts keep their distance from each other
--  * every catch is verified by the server (token, owner, distance, daily cap)
--  * players can opt out with /halloweenghosts
-- ==========================================================================
Config.Ghosts = {
    enabled = true,
    interval = { 45, 120 },    -- seconds between spawn attempts (server-wide; one ghost per attempt at most)
    maxActive = 10,            -- ghosts alive on the whole server at once
    playerCooldown = 150,      -- seconds before the same player can be haunted again
    radius = { 25.0, 60.0 },   -- how far from the player a ghost appears
    minSeparation = 120.0,     -- ghosts keep at least this far from each other
    lifetime = 240,            -- seconds before an uncaught ghost fades away
    catchRadius = 30.0,        -- server-side distance tolerance when catching
    nightOnly = true,          -- only between 20:00 and 06:00 on the in-game clock (checked on the client)
    skipVehicleSpeed = 8.0,    -- m/s; fast drivers are left alone
    model = 'u_m_y_zombie_01', alpha = 100, light = { 120, 200, 255 },
    -- Ghosts can only be caught with a flashlight: aim it at the ghost and hold the beam on it until it is trapped.
    flashlight = {
        required = true,               -- false = the old way (walk up and press E)
        weapon = 'WEAPON_FLASHLIGHT',  -- must be the weapon in hand (ox_inventory item WEAPON_FLASHLIGHT); the server checks it too
        range = 22.0,                  -- metres the beam reaches
        cone = 9.0,                    -- degrees either side of where you are aiming that still count as on target
        exposure = 3.5,                -- seconds the beam has to stay on the ghost
        decay = 0.6,                   -- exposure lost per second while the beam is off it
    },
}

-- ==========================================================================
-- City-wide trick or treating (Halloween). Walk up to any listed front door and knock.
-- Every door can be knocked once per night per player, up to `perNight` doors. Outcomes and points use
-- Config.Events.halloween.outcomes unless you give this its own `outcomes` list.
-- Door positions are where the player stands outside the door. Check them on your map; add your own with
-- /holidaydoor (prints a ready-to-paste line for where you are standing to F8 and copies it).
-- ==========================================================================
Config.TrickOrTreat = {
    enabled = true,
    perNight = 15,              -- doors per player per day
    distance = 2.0,             -- how close you need to be to knock (client prompt)
    verifyDistance = 6.0,       -- server-side tolerance for the same check
    knockTime = 2500,           -- ms the knock takes (cancelable)
    nightOnly = false,          -- true = only 18:00 to 06:00 on the in-game clock
    blips = { enabled = true, sprite = 40, colour = 47, scale = 0.65, label = 'Trick or treat' },
    outcomes = nil,
    doors = {
        { coords = vec3(-14.11, -1441.93, 31.10), area = 'Forum Drive' },
        { coords = vec3(126.81, -1929.98, 21.38), area = 'Grove Street' },
        { coords = vec3(118.42, -1920.95, 21.32), area = 'Grove Street' },
        { coords = vec3(100.91, -1912.19, 21.40), area = 'Grove Street' },
        { coords = vec3(72.21, -1938.63, 21.37),  area = 'Grove Street' },
        { coords = vec3(76.35, -1948.12, 21.17),  area = 'Grove Street' },
        { coords = vec3(85.78, -1959.66, 21.12),  area = 'Grove Street' },
        { coords = vec3(114.33, -1961.12, 21.33), area = 'Grove Street' },
        { coords = vec3(1273.90, -1720.70, 54.77), area = 'El Burro Heights' },
        { coords = vec3(1060.48, -378.29, 68.23), area = 'Mirror Park' },
        { coords = vec3(1010.47, -423.43, 65.35), area = 'Mirror Park' },
        { coords = vec3(987.75, -433.03, 64.04),  area = 'Mirror Park' },
        { coords = vec3(970.79, -701.33, 58.48),  area = 'Mirror Park' },
        { coords = vec3(979.27, -716.32, 58.22),  area = 'Mirror Park' },
        { coords = vec3(996.89, -729.56, 57.82),  area = 'Mirror Park' },
        { coords = vec3(1229.63, -725.41, 60.95), area = 'Mirror Park' },
        { coords = vec3(-816.70, 178.07, 72.22),  area = 'Rockford Hills' },
        { coords = vec3(-1896.30, 642.50, 130.20), area = 'Richman Glen' },
        { coords = vec3(-174.35, 502.60, 137.42), area = 'Vinewood Hills' },
        { coords = vec3(-853.00, 695.50, 148.80), area = 'Vinewood Hills' },
        { coords = vec3(1973.60, 3815.30, 33.43), area = 'Sandy Shores' },
    },
}
