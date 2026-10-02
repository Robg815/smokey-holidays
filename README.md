# s2-holidays

Calendar-driven US holidays for Qbox servers, covering the 11 most widely celebrated: New Year's Eve and Day,
Valentine's, St. Patrick's, Easter, Memorial Day, Independence Day, Labor Day, Halloween, Thanksgiving and Christmas. Each one brings **activities out in the city**: things to find,
places to go, jobs to run and live events to show up for. A modern menu (`/holidays`) works as the hub: what is on
today, your progress, countdowns, and a waypoint to the nearest spot. Admins get a tablet for testing.

## What happens in the city

| Holiday | In the city |
|---|---|
| New Year's Day | **Polar plunge** at any beach (get in the water), **Resolution run** checkpoints through the parks |
| Valentine's Day | **Rose delivery** from the flower stalls to doors around town (timed), **Secret admirer letters** hidden at romantic lookouts |
| St. Patrick's Day | **Pots of gold** in the hills, **Pub crawl** across every bar in the county |
| Easter | **City egg hunt** (glowing eggs in the parks, search areas on the map), **Easter baskets** delivered to families |
| Memorial Day | **Lay a wreath** at the memorials, **National moment of remembrance** at Legion Square at 3 pm |
| Independence Day | **Launch the fireworks** from beach pads (everyone nearby sees them), **Fireworks over the pier** show at 9 pm |
| Labor Day | **Holiday shifts** at construction sites, **Haul supplies** from stores to work sites |
| Halloween | **Trick or treat** at front doors all over the map, **Ghost hunt** with a flashlight at night, month-long leaderboard and prizes |
| Thanksgiving | **Food drive** deliveries to families, **Turkey trot** checkpoints |
| Christmas | **Present hunt** around the city, **Caroling** at doors, plus the advent calendar in the menu |
| New Year's Eve | **Midnight countdown** at Legion Square with a fireworks show, **Party supplies** runs |

Three kinds of activity, all configured in `config_world.lua`:
- **Spots**: go somewhere and interact (a prop, a door, a station). Each spot once a day, with a daily cap. Props are spawned
  only on your own client near you; markers, lights and map blips (exact spots or search areas) are configurable.
- **Deliveries**: pick something up, carry it (box in hand, GPS route on the map) and drop it off before the timer runs out.
- **Gatherings**: be inside the circle on the map at the set time (server clock). Everyone there is rewarded, the server
  announces it ahead of time, and fireworks shows play for everyone in range.

The server decides everything: what is running, whether you are really at the spot (2D distance check), daily caps, rolls
and payouts. Rewards are configurable per activity; Halloween activities also score contest points.

## Install
1. Put this folder in your resources as `s2-holidays`.
2. Dependencies: `ox_lib`, `qbx_core`, `ox_inventory`, `oxmysql`. Tables (`s2_holiday_*`) are created automatically.
3. `ensure s2-holidays`, then give admins access: `add_ace group.admin s2-holidays.admin allow` (Qbox admins also work).
4. Edit `config.lua` (holidays, dates, themes, Halloween contest, ghosts) and `config_world.lua` (city activities, places, rewards).
   Reward items must exist in ox_inventory.

Remove the old `smokey-holidays` resource from `server.cfg`; this replaces it and does not read its table.

## Commands
| Command | Who | What |
|---|---|---|
| `/holidays` (F7) | Players | The city hub: today's activities, progress, waypoints, Halloween leaderboard, advent calendar |
| `/holidaycancel` | Players | Drop the delivery you are carrying |
| `/halloweenghosts` | Players | Opt out of (or back into) world ghosts |
| `/holidayadmin` | Admins | The admin tablet |
| `/holidayspot` | Anyone | Copies a `vec3(...)` for where you stand, for adding or fixing positions |

## Before going live
- **Walk the positions.** Places in `config_world.lua` are a starting set from the map and may be a few metres off (props
  and markers snap to the ground, and the server checks distance in 2D, so small errors are fine). Use the tablet's
  **City activities** tab: **Go there** teleports you through every spot of an activity; fix any with `/holidayspot`.
- **Prop models.** Each activity can spawn a prop (`prop_bbq_1`, `prop_money_bag_01`, `ind_prop_firework_01` and so on). If a
  model does not exist on your server the activity falls back to its marker. Swap in your own props freely.
- **Flashlights.** Players need `WEAPON_FLASHLIGHT` to catch Halloween ghosts.
- **Menu mini games.** The earlier in-menu games are still there: set `Config.MenuGames = true` to use them instead of the hub.

## Admin tablet
Tabs: Overview, Holidays (enable, force on, reset your claims), **City activities** (go to every spot, start a gathering now,
reset your city progress), Time travel (fake date and clock, which also drive gatherings), and Halloween (ghosts, points,
contest reset).

Test a holiday end to end: force it on in the Holidays tab, open `/holidays`, use **Set waypoint** and do an activity; for
gatherings, set the fake clock a minute before the start time and stand in the circle.

## Halloween contest
Runs all October: knock on doors and trap ghosts with your flashlight to score points. The board locks at midnight after
Oct 31, the winner is announced to everyone, and the top three claim prizes from the menu until Nov 7.

## Develop and preview without the game
```
pip install -r dev/requirements.txt && playwright install chromium
python dev/smoke.py          # click-through tests
python dev/shot.py           # screenshots in web/screenshots/
lua5.4 dev/dates_test.lua    # date rules
lua5.4 dev/export_world.lua  # regenerate the preview's activity list after editing config_world.lua
```
Open `web/index.html?holiday=<id>` in a browser (`&closed` for contest results, `&games` for the old mini games, `?admin` for
the tablet). The art is original SVG, regenerated by `python dev/art.py`.

## Status
The UI is tested in the browser preview with a mock server; the date rules with Lua 5.4. The game side (props, blips,
deliveries, gatherings, fireworks, payouts) has not been run in-game yet. Run it on a test server before going live.
