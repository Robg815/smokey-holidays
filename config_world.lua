-- ==========================================================================
-- City activities: every holiday has things to do out in Los Santos.
--
-- Activity types
--   spots      go to places and interact (find a prop, knock on a door, work a station). Each spot once per day per player.
--   delivery   pick something up at one place and carry it to another before the timer runs out.
--   gathering  be inside the area when the moment comes (server clock, HH:MM). Everyone there is rewarded, and an
--              optional fireworks show plays for the whole area.
--
-- Common fields: key (unique per holiday, short), title, desc, icon (menu icon), perDay, outcomes or reward.
--   outcomes = 'event'  uses Config.Events[holiday].outcomes; or a weighted list like Config.Events; or reward = { ... }.
--   points on an outcome/reward count toward the holiday contest when it has one (Halloween).
-- Spot fields: spots (list or name of a Config.Places list), prompt, scenario or anim = { dict, clip }, duration (ms),
--   prop (model, spawned locally on each client; falls back to the marker if the model does not exist),
--   marker = { type, color = { r, g, b, a }, scale }, light = { r, g, b }, blip = { sprite, colour, mode = 'spots' | 'area' },
--   distance (interaction metres), nightOnly (in-game 20:00 to 06:00), water (player must be in the water), effect = 'fireworks' | 'scare'.
-- Positions are approximate starting points: props and markers snap to the ground, and the server checks distance in 2D.
-- Walk them once on your server (admin tablet > City > Go there) and fix any with /holidayspot.
-- Reward items must exist in ox_inventory.
-- ==========================================================================

-- Shared place lists, referenced by name from activities
Config.Places = {
    houses = {
        vec3(-14.11, -1441.93, 31.10), vec3(126.81, -1929.98, 21.38), vec3(118.42, -1920.95, 21.32), vec3(100.91, -1912.19, 21.40),
        vec3(72.21, -1938.63, 21.37), vec3(76.35, -1948.12, 21.17), vec3(85.78, -1959.66, 21.12), vec3(114.33, -1961.12, 21.33),
        vec3(1273.90, -1720.70, 54.77), vec3(1060.48, -378.29, 68.23), vec3(1010.47, -423.43, 65.35), vec3(987.75, -433.03, 64.04),
        vec3(970.79, -701.33, 58.48), vec3(979.27, -716.32, 58.22), vec3(996.89, -729.56, 57.82), vec3(1229.63, -725.41, 60.95),
        vec3(-816.70, 178.07, 72.22), vec3(-1896.30, 642.50, 130.20), vec3(-174.35, 502.60, 137.42), vec3(-853.00, 695.50, 148.80),
        vec3(1973.60, 3815.30, 33.43),
    },
    parks = {
        vec3(195.0, -935.0, 30.7), vec3(1090.0, -650.0, 57.0), vec3(-1200.0, -1580.0, 4.6), vec3(-1600.0, -1020.0, 13.0),
        vec3(-1330.0, 60.0, 53.5), vec3(-425.0, 1125.0, 325.8), vec3(-150.0, 6400.0, 31.5), vec3(1700.0, 3600.0, 35.4),
        vec3(-1090.0, -1640.0, 4.4), vec3(2550.0, 380.0, 108.6),
    },
    beaches = {
        vec3(-1380.0, -1520.0, 3.0), vec3(-1290.0, -1770.0, 2.5), vec3(-1660.0, -1040.0, 8.0), vec3(-3150.0, 940.0, 3.0),
        vec3(-260.0, 6620.0, 2.0), vec3(-2980.0, 40.0, 3.0), vec3(1310.0, 3990.0, 30.5), vec3(-1500.0, -1350.0, 2.5),
    },
    piers = { vec3(-1850.0, -1240.0, 8.6), vec3(-3420.0, 965.0, 8.3), vec3(-275.0, 6635.0, 7.4), vec3(1300.0, 4220.0, 33.9) },
    bars = { vec3(-565.0, 274.0, 83.0), vec3(-1388.0, -587.0, 30.2), vec3(128.0, -1297.0, 29.3), vec3(1985.0, 3050.0, 47.2), vec3(-2192.0, 4285.0, 49.2) },
    memorials = { vec3(-1745.0, -200.0, 57.5), vec3(190.0, -920.0, 30.7), vec3(-1590.0, 2795.0, 17.0) },
    stores = { vec3(25.7, -1347.3, 29.5), vec3(-48.5, -1757.5, 29.4), vec3(373.9, 326.3, 103.6), vec3(1961.5, 3740.7, 32.3), vec3(1728.7, 6414.1, 35.0) },
    construction = { vec3(-150.0, -955.0, 29.2), vec3(-470.0, -950.0, 23.9), vec3(1000.0, -3000.0, 5.9), vec3(2950.0, 2790.0, 41.0) },
    government = { vec3(-545.0, -205.0, 38.2), vec3(440.0, -980.0, 30.7), vec3(-70.0, -800.0, 44.2), vec3(195.0, -935.0, 30.7) },
    dealers = { vec3(-56.0, -1097.0, 26.4), vec3(-800.0, -220.0, 37.1) },
    lookouts = { vec3(-425.0, 1125.0, 325.8), vec3(710.0, 1200.0, 345.0), vec3(500.0, 5590.0, 795.0), vec3(-1850.0, -1240.0, 8.6) },
    stalls = { vec3(175.0, -925.0, 30.7), vec3(-1640.0, -1010.0, 13.0) },
}

local snacks = { { name = 'sandwich', count = 2 }, { name = 'water', count = 2 } }

Config.World = {
    new_years = {
        { key = 'plunge', type = 'spots', title = 'Polar plunge', icon = 'wave', desc = 'Wade into the ocean at any beach and take the New Year plunge.',
          spots = 'beaches', water = true, distance = 40.0, prompt = 'Take the plunge', duration = 3500, perDay = 1,
          marker = { type = 1, color = { r = 140, g = 210, b = 255, a = 90 }, scale = 6.0 }, blip = { sprite = 404, colour = 3, mode = 'spots' },
          reward = { label = 'Brave soul', cash = 1000, msg = 'Freezing, and worth it.' } },
        { key = 'run', type = 'spots', title = 'Resolution run', icon = 'run', desc = 'Jog through the city parks. Every checkpoint counts toward your resolution.',
          spots = 'parks', scenario = 'WORLD_HUMAN_JOG_STANDING', prompt = 'Stretch and log your run', duration = 5000, perDay = 5,
          marker = { type = 4, color = { r = 143, g = 216, b = 255, a = 160 }, scale = 1.2 }, blip = { sprite = 126, colour = 3, mode = 'spots' },
          outcomes = { { kind = 'cash', weight = 70, label = 'Personal best', cash = 200, msg = 'New year, new you.' }, { kind = 'gift', weight = 30, label = 'Water break', items = snacks, msg = 'Hydrate.' } } },
    },
    mlk = {
        { key = 'cleanup', type = 'spots', title = 'Day of service: clean up', icon = 'trash', desc = 'Pick up litter around the parks and streets. A day on, not a day off.',
          spots = 'parks', prop = 'prop_rub_binbag_01', scenario = 'WORLD_HUMAN_JANITOR', prompt = 'Clean up', duration = 6000, perDay = 6,
          blip = { sprite = 318, colour = 3, mode = 'spots' }, reward = { label = 'Thank you, volunteer', cash = 250, msg = 'The block looks better already.' } },
        { key = 'garden', type = 'spots', title = 'Community garden', icon = 'flower', desc = 'Plant something that will still be growing next year.',
          spots = 'memorials', scenario = 'WORLD_HUMAN_GARDENER_PLANT', prompt = 'Plant a tree', duration = 7000, perDay = 3,
          marker = { type = 25, color = { r = 120, g = 220, b = 120, a = 160 }, scale = 1.2 }, blip = { sprite = 285, colour = 2, mode = 'spots' },
          reward = { label = 'Volunteer lunch', items = snacks, cash = 150, msg = 'Something good is growing.' } },
    },
    valentines = {
        { key = 'roses', type = 'delivery', title = 'Rose delivery', icon = 'heart', desc = 'Pick up roses at a flower stall and deliver them before they wilt.',
          pickups = 'stalls', drops = 'houses', timeLimit = 600, perDay = 4, carry = 'prop_cs_box_clothes',
          blip = { sprite = 489, colour = 48 },
          outcomes = { { kind = 'cash', weight = 75, label = 'Delivery tip', cash = 400, msg = 'They were thrilled.' }, { kind = 'jackpot', weight = 25, label = 'Big tipper', cash = 1200, msg = 'Somebody is in love.' } } },
        { key = 'letters', type = 'spots', title = 'Secret admirer letters', icon = 'mail', desc = 'Love letters are hidden at the most romantic spots in town.',
          spots = 'lookouts', prop = 'prop_cs_envolope_01', prompt = 'Read the letter', duration = 2500, perDay = 4,
          marker = { type = 0, color = { r = 255, g = 111, b = 181, a = 180 }, scale = 0.5 }, light = { 255, 120, 180 }, blip = { sprite = 489, colour = 48, mode = 'area' },
          outcomes = { { kind = 'gift', weight = 50, label = 'Chocolates', items = snacks, msg = 'A box of chocolates.' }, { kind = 'cash', weight = 40, label = 'Love note cash', cash = 500, msg = 'Cash folded inside.' }, { kind = 'jackpot', weight = 10, label = 'Golden ticket', cash = 2500, msg = 'Somebody really likes you.' } } },
    },
    presidents = {
        { key = 'coins', type = 'spots', title = 'Presidential coin hunt', icon = 'coin', desc = 'Commemorative coins were left near government buildings. Find them.',
          spots = 'government', prop = 'prop_gold_bar', prompt = 'Pick up the coin', duration = 2000, perDay = 4,
          light = { 255, 211, 107 }, blip = { sprite = 431, colour = 5, mode = 'area' },
          outcomes = { { kind = 'silver', weight = 60, label = 'Silver dollar', cash = 400, msg = 'Freshly struck.' }, { kind = 'gold', weight = 15, label = 'Gold presidential coin', cash = 2500, msg = 'One in a thousand.' }, { kind = 'dud', weight = 25, label = 'Wooden nickel', cash = 25, msg = 'Somebody is having a laugh.' } } },
        { key = 'sale', type = 'spots', title = "Presidents' Day sale", icon = 'car', desc = 'Every dealership is running a holiday sale. Stop by for a voucher.',
          spots = 'dealers', scenario = 'WORLD_HUMAN_CLIPBOARD', prompt = 'Grab a sale voucher', duration = 4000, perDay = 2,
          marker = { type = 29, color = { r = 111, g = 155, b = 255, a = 180 }, scale = 1.0 }, blip = { sprite = 326, colour = 38, mode = 'spots' },
          reward = { label = 'Sale voucher', cash = 750, msg = 'Holiday pricing, cash back.' } },
    },
    stpatricks = {
        { key = 'gold', type = 'spots', title = 'Pots of gold', icon = 'coin', desc = 'The rainbow ends in the hills this year. Find the pots of gold.',
          spots = 'lookouts', prop = 'prop_money_bag_01', prompt = 'Grab the gold', duration = 2500, perDay = 4,
          light = { 120, 255, 140 }, blip = { sprite = 207, colour = 2, mode = 'area' },
          outcomes = { { kind = 'coins', weight = 70, label = 'Gold coins', cash = 400, msg = 'Shiny.' }, { kind = 'lucky', weight = 10, label = 'Four-leaf clover', cash = 2500, msg = 'Luck of the Irish.' }, { kind = 'dud', weight = 20, label = 'Fool\'s gold', cash = 50, msg = 'Painted rocks.' } } },
        { key = 'pubs', type = 'spots', title = 'Pub crawl', icon = 'beer', desc = 'Raise a glass at every bar in the county. Take a taxi home.',
          spots = 'bars', scenario = 'WORLD_HUMAN_DRINKING', prompt = 'Raise a glass', duration = 6000, perDay = 5,
          marker = { type = 2, color = { r = 77, g = 255, b = 138, a = 170 }, scale = 0.5 }, blip = { sprite = 93, colour = 2, mode = 'spots' },
          reward = { label = 'Round on the house', cash = 300, msg = 'Slainte!' } },
    },
    easter = {
        { key = 'eggs', type = 'spots', title = 'City egg hunt', icon = 'egg', desc = 'Eggs are hidden in parks across the city. Look for the glow.',
          spots = 'parks', prompt = 'Pick up the egg', duration = 1500, perDay = 10, anim = { dict = 'pickup_object', clip = 'pickup_low' },
          marker = { type = 28, color = { r = 199, g = 155, b = 255, a = 200 }, scale = 0.28 }, light = { 200, 160, 255 }, blip = { sprite = 615, colour = 27, mode = 'area' },
          outcomes = { { kind = 'egg', weight = 55, label = 'Pocket cash', cash = 200, msg = 'Wrapped in foil.' }, { kind = 'basket', weight = 30, label = 'Basket goodies', items = snacks, msg = 'Snacks and treats.' }, { kind = 'golden', weight = 15, label = 'Golden egg', cash = 1500, msg = 'Very rare.' } } },
        { key = 'baskets', type = 'delivery', title = 'Easter baskets', icon = 'gift', desc = 'Bring baskets from the store to families around town.',
          pickups = 'stores', drops = 'houses', timeLimit = 600, perDay = 3, carry = 'prop_cs_box_clothes', blip = { sprite = 478, colour = 27 },
          reward = { label = 'Basket delivered', cash = 500, msg = 'The kids went wild.' } },
    },
    mothers_day = {
        { key = 'bouquet', type = 'delivery', title = 'Bouquet for Mom', icon = 'flower', desc = 'Pick up a bouquet and get it to her door before it wilts.',
          pickups = 'stalls', drops = 'houses', timeLimit = 600, perDay = 3, carry = 'prop_cs_box_clothes', blip = { sprite = 280, colour = 48 },
          outcomes = { { kind = 'rose', weight = 70, label = 'Delivered with love', cash = 500, msg = 'She cried. Good tears.' }, { kind = 'orchid', weight = 30, label = 'Favorite child', cash = 1500, msg = 'You are the favorite now.' } } },
        { key = 'flowers', type = 'spots', title = 'Wildflowers', icon = 'flower', desc = 'Pick wildflowers in the parks for her bouquet.',
          spots = 'parks', anim = { dict = 'pickup_object', clip = 'pickup_low' }, prompt = 'Pick flowers', duration = 2000, perDay = 6,
          marker = { type = 28, color = { r = 255, g = 143, b = 200, a = 200 }, scale = 0.22 }, light = { 255, 150, 200 }, blip = { sprite = 285, colour = 48, mode = 'spots' },
          reward = { label = 'A handful of flowers', cash = 200, msg = 'She will love these.' } },
    },
    memorial = {
        { key = 'wreath', type = 'spots', title = 'Lay a wreath', icon = 'flame', desc = 'Visit the memorials and pay your respects.',
          spots = 'memorials', anim = { dict = 'amb@medic@standing@kneel@base', clip = 'base' }, prompt = 'Lay a wreath', duration = 6000, perDay = 3,
          marker = { type = 27, color = { r = 255, g = 210, b = 120, a = 140 }, scale = 1.2 }, light = { 255, 200, 120 }, blip = { sprite = 84, colour = 3, mode = 'spots' },
          reward = { label = 'Remembered', msg = 'Thank you for remembering.' } },
        { key = 'silence', type = 'gathering', title = 'National moment of remembrance', icon = 'clock', desc = 'At 3 pm the city pauses for a moment of silence at Legion Square.',
          center = vec3(195.0, -935.0, 30.7), radius = 70.0, at = '15:00', announce = 10, blip = { sprite = 84, colour = 3 },
          reward = { label = 'A moment of silence', cash = 250, msg = 'Thank you for being there.' } },
    },
    juneteenth = {
        { key = 'grills', type = 'spots', title = 'Freedom Day cookout', icon = 'grill', desc = 'Grills are fired up at parks across town. Help cook for the neighborhood.',
          spots = 'parks', prop = 'prop_bbq_1', scenario = 'PROP_HUMAN_BBQ', prompt = 'Work the grill', duration = 8000, perDay = 4,
          blip = { sprite = 93, colour = 1, mode = 'spots' },
          outcomes = { { kind = 'cookout', weight = 70, label = 'Plates for everyone', items = { { name = 'burger', count = 2 }, { name = 'cola', count = 2 } }, msg = 'Ribs, red drinks and good company.' }, { kind = 'cash', weight = 30, label = 'Pitmaster tip', cash = 600, msg = 'Best plate at the park.' } } },
        { key = 'celebration', type = 'gathering', title = 'Freedom celebration', icon = 'firework', desc = 'Fireworks over Legion Square at 8 pm. Be there.',
          center = vec3(195.0, -935.0, 30.7), radius = 120.0, at = '20:00', announce = 10, show = { duration = 150, center = vec3(195.0, -935.0, 90.0) }, blip = { sprite = 489, colour = 1 },
          reward = { label = 'Celebrated together', cash = 1000, items = { { name = 'armour', count = 1 } }, msg = 'Happy Juneteenth.' } },
    },
    fathers_day = {
        { key = 'grill', type = 'spots', title = 'Grill master', icon = 'grill', desc = 'Backyard grills are waiting. Flip some burgers like Dad taught you.',
          spots = 'houses', prop = 'prop_bbq_1', scenario = 'PROP_HUMAN_BBQ', prompt = 'Man the grill', duration = 8000, perDay = 4,
          blip = { sprite = 93, colour = 17, mode = 'area' },
          outcomes = { { kind = 'burger', weight = 60, label = 'Perfect burger', items = { { name = 'burger', count = 2 } }, msg = 'Dad would be proud.' }, { kind = 'steak', weight = 25, label = 'Prime steak', cash = 500, msg = 'Resting like a pro.' }, { kind = 'burnt', weight = 15, label = 'Burnt to a crisp', cash = 25, msg = 'Charcoal. Tell nobody.' } } },
        { key = 'fishing', type = 'spots', title = 'Fishing with Dad', icon = 'fish', desc = 'Cast a line off any pier in the county.',
          spots = 'piers', scenario = 'WORLD_HUMAN_STAND_FISHING', prompt = 'Cast a line', duration = 12000, perDay = 3,
          marker = { type = 1, color = { r = 95, g = 176, b = 255, a = 120 }, scale = 1.4 }, blip = { sprite = 68, colour = 3, mode = 'spots' },
          outcomes = { { kind = 'cash', weight = 55, label = 'Good-sized bass', cash = 400, msg = 'Photo for the fridge.' }, { kind = 'jackpot', weight = 10, label = 'The one that did not get away', cash = 2000, msg = 'Dad is speechless.' }, { kind = 'empty', weight = 35, label = 'An old boot', cash = 25, msg = 'Classic.' } } },
    },
    independence = {
        { key = 'pads', type = 'spots', title = 'Launch the fireworks', icon = 'firework', desc = 'Launch pads are set up on the beaches. Light one and the whole beach sees it.',
          spots = 'beaches', prop = 'ind_prop_firework_01', anim = { dict = 'anim@mp_fireworks', clip = 'place_firework_3_box' }, prompt = 'Light the fuse', duration = 3000, perDay = 4,
          effect = 'fireworks', blip = { sprite = 489, colour = 38, mode = 'spots' },
          outcomes = { { kind = 'burst', weight = 75, label = 'Big burst', cash = 300, msg = 'The beach cheered.' }, { kind = 'finale', weight = 25, label = 'Grand finale', cash = 1200, msg = 'The whole sky lit up.' } } },
        { key = 'show', type = 'gathering', title = 'Fireworks over the pier', icon = 'firework', desc = 'The big show starts at 9 pm at Del Perro Pier.',
          center = vec3(-1700.0, -1150.0, 13.0), radius = 180.0, at = '21:00', announce = 15, show = { duration = 240, center = vec3(-1820.0, -1250.0, 70.0) }, blip = { sprite = 489, colour = 38 },
          reward = { label = 'Front row seats', cash = 1000, msg = 'Happy Independence Day.' } },
    },
    labor = {
        { key = 'shifts', type = 'spots', title = 'Holiday shifts', icon = 'hardhat', desc = 'Construction sites pay double today. Put in a shift at each one.',
          spots = 'construction', scenario = 'WORLD_HUMAN_HAMMERING', prompt = 'Work a shift', duration = 10000, perDay = 4,
          marker = { type = 30, color = { r = 255, g = 194, b = 71, a = 180 }, scale = 1.0 }, blip = { sprite = 566, colour = 46, mode = 'spots' },
          reward = { label = 'Holiday pay', cash = 600, msg = 'Time and a half.' } },
        { key = 'haul', type = 'delivery', title = 'Haul supplies', icon = 'box', desc = 'Carry supplies from the store to a work site.',
          pickups = 'stores', drops = 'construction', timeLimit = 900, perDay = 3, carry = 'prop_cs_cardbox_01', blip = { sprite = 478, colour = 46 },
          reward = { label = 'Supplies delivered', cash = 700, items = { { name = 'repairkit', count = 1 } }, msg = 'Foreman owes you one.' } },
    },
    columbus = {
        { key = 'dig', type = 'spots', title = 'Beachcombing', icon = 'compass', desc = 'Dig along the beaches for sea glass, old maps and the odd sunken chest.',
          spots = 'beaches', scenario = 'WORLD_HUMAN_GARDENER_PLANT', prompt = 'Dig here', duration = 7000, perDay = 4,
          marker = { type = 27, color = { r = 63, g = 214, b = 198, a = 160 }, scale = 1.4 }, blip = { sprite = 587, colour = 47, mode = 'area' },
          outcomes = { { kind = 'glass', weight = 50, label = 'Sea glass', cash = 250, msg = 'Smoothed by the tide.' }, { kind = 'map', weight = 30, label = 'Old map fragment', items = { { name = 'radio', count = 1 } }, msg = 'Someone hid a radio with it.' }, { kind = 'chest', weight = 20, label = 'Sunken chest', cash = 2000, msg = 'Waterlogged, and full.' } } },
        { key = 'lookouts', type = 'spots', title = 'Coastal lookouts', icon = 'binoculars', desc = 'Take in the view from the high points and learn the land\'s history.',
          spots = 'lookouts', scenario = 'WORLD_HUMAN_BINOCULARS', prompt = 'Take in the view', duration = 6000, perDay = 4,
          marker = { type = 32, color = { r = 63, g = 214, b = 198, a = 180 }, scale = 1.0 }, blip = { sprite = 184, colour = 47, mode = 'spots' },
          reward = { label = 'Explorer', cash = 400, msg = 'People lived here long before the city.' } },
    },
    halloween = {
        { key = 'doors', type = 'spots', title = 'Trick or treat', icon = 'door', desc = 'Knock on doors with a pumpkin on your map. Every door scores contest points.',
          spots = 'houses', prop = 'prop_veg_crop_03_pump', anim = { dict = 'timetable@jimmy@doorknock@', clip = 'knockdoor_idle' }, prompt = 'Trick or treat', duration = 2500, perDay = 15,
          effect = 'scare', blip = { sprite = 484, colour = 47, mode = 'spots' }, outcomes = 'event' },
    },
    veterans = {
        { key = 'salute', type = 'spots', title = 'Salute at the memorials', icon = 'flag', desc = 'Visit each memorial and salute those who served.',
          spots = 'memorials', anim = { dict = 'anim@mp_player_intincarsalutestd@ds@', clip = 'idle_a' }, prompt = 'Salute', duration = 4000, perDay = 3,
          marker = { type = 27, color = { r = 127, g = 168, b = 255, a = 150 }, scale = 1.2 }, light = { 200, 210, 255 }, blip = { sprite = 84, colour = 38, mode = 'spots' },
          reward = { label = 'Honored', msg = 'Thank you for your support.' } },
        { key = 'packages', type = 'delivery', title = 'Care packages', icon = 'box', desc = 'Bring care packages from the store to veterans around town.',
          pickups = 'stores', drops = 'houses', timeLimit = 600, perDay = 3, carry = 'prop_cs_cardbox_01', blip = { sprite = 478, colour = 38 },
          reward = { label = 'Package delivered', cash = 500, items = { { name = 'bandage', count = 2 } }, msg = 'They wanted to tell you a story. You listened.' } },
    },
    thanksgiving = {
        { key = 'fooddrive', type = 'delivery', title = 'Food drive', icon = 'box', desc = 'Pick up donated food at a store and deliver it to a family in need.',
          pickups = 'stores', drops = 'houses', timeLimit = 600, perDay = 4, carry = 'prop_cs_cardbox_01', blip = { sprite = 478, colour = 17 },
          reward = { label = 'Meal delivered', cash = 500, items = { { name = 'burger', count = 1 } }, msg = 'A family eats well tonight because of you.' } },
        { key = 'trot', type = 'spots', title = 'Turkey trot', icon = 'run', desc = 'Run the turkey trot checkpoints through the parks before dinner.',
          spots = 'parks', scenario = 'WORLD_HUMAN_JOG_STANDING', prompt = 'Check in', duration = 4000, perDay = 5,
          marker = { type = 4, color = { r = 255, g = 179, b = 71, a = 160 }, scale = 1.2 }, blip = { sprite = 126, colour = 17, mode = 'spots' },
          reward = { label = 'Checkpoint', cash = 200, msg = 'Earned that second plate.' } },
    },
    christmas = {
        { key = 'presents', type = 'spots', title = 'Present hunt', icon = 'gift', desc = 'Presents fell off a sleigh all over the city. Find them.',
          spots = 'parks', prop = 'prop_cs_box_clothes', prompt = 'Open the present', duration = 2500, perDay = 6,
          light = { 255, 90, 110 }, blip = { sprite = 781, colour = 1, mode = 'area' },
          outcomes = { { kind = 'gift', weight = 60, label = 'Something warm', items = snacks, msg = 'Socks. And snacks.' }, { kind = 'cash', weight = 30, label = 'Stocking cash', cash = 600, msg = 'Santa pays cash.' }, { kind = 'jackpot', weight = 10, label = 'The big present', cash = 2500, msg = 'Best Christmas ever.' } } },
        { key = 'carols', type = 'spots', title = 'Caroling', icon = 'music', desc = 'Sing carols at doors around the neighborhood.',
          spots = 'houses', scenario = 'WORLD_HUMAN_MUSICIAN', prompt = 'Sing a carol', duration = 6000, perDay = 6,
          marker = { type = 32, color = { r = 255, g = 90, b = 110, a = 170 }, scale = 0.8 }, blip = { sprite = 781, colour = 1, mode = 'spots' },
          outcomes = { { kind = 'gift', weight = 60, label = 'Cookies and cocoa', items = { { name = 'cola', count = 2 } }, msg = 'They asked for an encore.' }, { kind = 'cash', weight = 40, label = 'Tip jar', cash = 300, msg = 'Fa la la.' } } },
    },
    new_years_eve = {
        { key = 'countdown', type = 'gathering', title = 'Midnight countdown', icon = 'firework', desc = 'Ring in the new year at Legion Square. The countdown starts at 23:59.',
          center = vec3(195.0, -935.0, 30.7), radius = 120.0, at = '23:59', announce = 15, show = { duration = 300, center = vec3(195.0, -935.0, 95.0) }, blip = { sprite = 489, colour = 5 },
          reward = { label = 'Happy New Year!', cash = 2000, items = { { name = 'armour', count = 1 } }, msg = 'You rang it in with the whole city.' } },
        { key = 'supplies', type = 'delivery', title = 'Party supplies', icon = 'box', desc = 'Run supplies from the store to the party at Legion Square.',
          pickups = 'stores', drops = { vec3(195.0, -935.0, 30.7) }, timeLimit = 900, perDay = 3, carry = 'prop_cs_cardbox_01', blip = { sprite = 478, colour = 5 },
          reward = { label = 'Party saved', cash = 600, items = { { name = 'cola', count = 3 } }, msg = 'The DJ owes you a shout-out.' } },
    },
}
