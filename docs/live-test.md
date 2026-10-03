# Live test checklist

Everything below has been run through `python dev/sim.py`, which runs the real server and client Lua against stand-ins for
FiveM, ox_lib, Qbox and ox_inventory (73 checks). What it cannot check is GTA itself: props, animations, blips, markers,
particles and how the menu looks in the game's browser. That is what this list is for.

Keep **F8** (client console) and the **server console** open the whole time. Any red Lua error is worth a screenshot.

## 1. Install
1. Copy the folder into `resources` as **`s2-holidays`** (the folder name matters: it is the NUI address).
2. Remove `smokey-holidays` from `server.cfg`.
3. Add, after ox_lib, qbx_core, ox_inventory and oxmysql:
   ```
   ensure s2-holidays
   add_ace group.admin s2-holidays.admin allow
   ```
4. Start the server. Within a few seconds the server console prints:
   ```
   [s2-holidays] 2026-10-03: running today: Halloween
   ```
   If it also prints a yellow line listing reward items that are not in ox_inventory, either add those items or change them
   in `config.lua` / `config_world.lua`. Until then they are skipped and the cash part of the reward still pays.
5. The four tables `s2_holiday_claims`, `s2_holiday_playtime`, `s2_holiday_points` and `s2_holiday_winners` are created
   automatically on first start.

## 2. Halloween (live now, all of October)
Halloween runs **Oct 1 to Oct 31** for activities and the contest, and stays in the menu until **Nov 7** so the top three
can claim prizes.

- [ ] Press **F7** (or `/holidays`). The menu opens on Halloween: leaderboard on the left, "Trick or treat" and "Ghost hunt" cards.
- [ ] **Set waypoint** on Trick or treat puts a waypoint on the nearest door. Pumpkin blips are on the map.
- [ ] At a door: a pumpkin sits on the doorstep, `[E] Trick or treat` shows, E plays the knock, then a notification with
      the reward, points and `(1/15 today)`. The door's blip turns grey. A trick gives a short screen scare.
- [ ] The same door again says you already knocked. Points appear on the leaderboard (reopen the menu).
- [ ] **Ghosts** (in-game night, 20:00 to 06:00, or the tablet's Spawn ghost near me at any time): a faint ghost
      drifts nearby. Without a flashlight you get a hint. With `WEAPON_FLASHLIGHT` aimed at it, a meter fills over it; when
      full it is trapped, with a notification and +30 pts.
- [ ] `/halloweenghosts` turns ghosts off and on for you.

**Contest close (do this on a test server, it locks the winners for the year):** admin tablet, Time travel, date
`Oct 31`, clock `23:59:30`. Wait about a minute. Everyone gets "<name> wins the contest", the menu shows the podium, and
first to third can press Claim. Activities stop. Afterwards: Halloween tab, **Reset contest** (asks twice), Time travel,
**Use real date** and **Use real time**.

## 3. Admin tablet (`/holidayadmin`)
- [ ] Opens as a tablet. Overview shows the server date, clock, active holidays and ghost count.
- [ ] **City activities** tab: every holiday with its activities. **Go there** teleports you to each spot in turn. Walk a
      few of them for each holiday; if one is off, stand where it should be, run `/holidayspot`, and paste the line into
      `config_world.lua` (replace the matching `vec3`).
- [ ] **Start now** on a live event (for example Independence Day, Fireworks over the pier) fires it immediately:
      players inside the circle get the reward and the fireworks show plays.
- [ ] **Reset my city progress** lets you redo today's activities.

## 4. Every other holiday
Use the tablet: Holidays tab, **Force on now** for one holiday (turn Halloween's force off if you set it), then open the
menu. Or set the date in Time travel. For each holiday, do one of each activity type it has:

| Holiday | Try |
|---|---|
| New Year's Day | Polar plunge (must be in the water), Resolution run |
| Valentine's Day | Rose delivery (box in hand, route, timer), Secret admirer letters |
| St. Patrick's Day | Pots of gold, Pub crawl |
| Easter | City egg hunt (search areas, glowing eggs), Easter baskets |
| Memorial Day | Lay a wreath; Moment of remembrance (set clock to 14:59, stand in Legion Square) |
| Independence Day | Launch pad (fireworks for everyone nearby); pier show (clock 20:59) |
| Labor Day | Holiday shifts, Haul supplies |
| Thanksgiving | Food drive, Turkey trot |
| Christmas | Present hunt, Caroling, advent calendar card in the menu |
| New Year's Eve | Party supplies; Midnight countdown (clock 23:58, Legion Square) |

For each, check: the prop or marker shows, the prompt and animation play, the notification shows the reward, the money or
item arrives, the daily count goes up in the menu, and blips grey out. For deliveries: `/holidaycancel` drops the job.

## 5. What to send back if something is off
- The F8 or server console error (screenshot), and what you were doing.
- For a spot in the wrong place: the holiday, activity, and the `/holidayspot` line for where it should be.
- For a missing prop: the activity. It falls back to a glowing marker, and a different model can be set in `config_world.lua`.
