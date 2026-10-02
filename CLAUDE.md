# s2-holidays

FiveM resource for Qbox servers (replaces the old smokey-holidays resource): calendar-driven US holidays with a modern dark dashboard NUI, an advent calendar,
a different experience per major holiday, and an admin test panel. **The server is authoritative; the NUI only presents.**

## Stack and constraints
- Lua 5.4 (`lua54 'yes'`), ox_lib, qbx_core, ox_inventory, oxmysql. All SQL is parameterized.
- NUI is plain HTML/CSS/JS: no framework, no bundler, no runtime npm deps, no remote assets. System fonts only
  (Bahnschrift for display text and numbers, Segoe UI for body; both ship with Windows, which is what FiveM runs on).
  FiveM's embedded Chromium can lag behind desktop Chrome, so avoid brand-new CSS/JS features.
- All artwork is original SVG (`web/img`). Never add copyrighted art or reference photos to the repo.
- This code has only been exercised through the browser preview and a mock server. It has **not** been run in-game yet.

## Repo map
```
fxmanifest.lua  config.lua           all tunables: holidays, themes, advent, Config.Events, Config.Ghosts
server/dates.lua   date rules (fixed / nth / last / easter, observed weekend shifts, windows). See "Dates contract" below.
server/admin.lua   admin/test layer: wraps Dates.today + Dates.evaluate; ACE `s2-holidays.admin` or qbx_core admin
server/events.lua  event engine: spots / feast / countdown / tribute, points, leaderboard, winners, prize claim
server/ghosts.lua  world ghosts: spawn loop, caps, server-verified catch (calls Events.worldCatch)
server/main.lua    state callback, advent claims, playtime thread
client/main.lua    opens the UI (/holidays + keybind), `claim` + `close` NUI callbacks, login notify
client/ghosts.lua  local ghost ped, haunt loop, flashlight beam exposure meter (or E when flashlights are off), /halloweenghosts
server/trickortreat.lua  city-wide door knocking (Config.TrickOrTreat): verify, roll, pay, score
client/trickortreat.lua  door prompts, blips, knock animation, /holidaydoor (prints a config line for where you stand)
client/events.lua  `play` NUI callback          client/admin.lua  /holidayadmin + admin NUI callbacks
web/index.html     one shell; css/{base,advent,events,admin}.css; js/{core,advent,events,admin,preview}.js
web/img/<id>/{emblem,scene}.svg   per-holiday art;  web/img/door*.svg advent door art;  web/img/default/ shared emblem
dev/               art.py (regenerates the SVG art), shot.py (screenshots), smoke.py (click-through test)
docs/halloween-contest.md   spec and contracts for the month-long Halloween contest (implemented)
```

## Commands
```
pip install -r dev/requirements.txt && playwright install chromium   # once
python dev/smoke.py              # click-through test, must pass before you finish
python dev/shot.py [id ...]      # PNGs in web/screenshots/ (no args = everything + contact sheet)
python dev/art.py                # regenerate SVG scenes/emblems (deterministic)
node --check web/js/*.js         # quick syntax check
lua5.4 dev/dates_test.lua        # date rules (Easter, nth/last weekday, observed days, windows)
```
Browser preview: open `web/index.html?holiday=<id>` (christmas, halloween, valentines, easter, stpatricks, independence,
thanksgiving, new_years_eve, new_years, memorial, veterans). Extras: `&force=trick`, `&closed` (contest results), `&art`, `&skin=holo`, `?admin`.
Skills: `/preview [id]`, `/smoke-test`.

## How it fits together
- Lua to NUI messages: `open{state}`, `refresh{state}`, `close`, `admin{data}`, `adminHide`.
  NUI to Lua callbacks: `claim`, `play`, `close`, `adminDo`, `adminClose`, `adminPreview`.
- `getState` returns `{date, theme, active[], upcoming[], advent?, event?}`. `render()` in `core.js` dispatches:
  `advent` to `renderAdvent`, otherwise `EXPERIENCES[event.kind]`, otherwise the observance card.
- Experience kinds: `advent`, `spots` (pick-and-reveal), `feast`, `countdown`, `tribute`. To add a kind: config in
  `Config.Events`, a branch in `Events.state` and `play` (server/events.lua), a render fn registered in `EXPERIENCES`
  (js/events.js), scene CSS (css/events.css), art, preview data (js/preview.js) and a case in `dev/smoke.py`.
- Themes are just CSS tokens (`--a`, `--b`, rgb variants) set by `theme()`; holidays never fork the layout.

## Data model (oxmysql)
- `s2_holiday_claims(citizenid, event, year, slot)` unique per slot, inserted with `INSERT IGNORE` so claims are idempotent.
  Slot encodings: advent = day; spots = `toDays*100 + spot*10 + outcomeIndex` (spot 9 = UI ghost catch, slot `+99`);
  feast = dish 1..6, finale 7; tribute = `toDays`; world ghosts use event key `halloween_ghost`, slot `toDays*100 + n`;
  city doors use `halloween_door`, slot `toDays*1000 + doorIndex`.
- `s2_holiday_playtime(citizenid, day, minutes)`; `s2_holiday_points(citizenid, event, year, points, name, updated)`;
  `s2_holiday_winners(event, year, place, citizenid, name, points, claimed)`.
- `play` arg meanings for spots events: `1..spots` open a spot, `9` UI ghost, `8` claim contest prize. Feast: `1..6` dish, `7` finale.

## Dates contract (server/dates.lua)
`Dates.today() -> y, m, d`; `Dates.toDays(y, m, d) -> integer`; `Dates.key(y, m, d) -> 'YYYY-MM-DD'`;
`Dates.evaluate(days, year) -> active[], upcoming[]` where entries are `{id, label, blurb, daysUntil, date, theme = {a, b}}`.
`server/admin.lua` replaces `Dates.today` and `Dates.evaluate` at runtime. For event logic always call those and
`Admin.secondsOfDay()`, never `os.time()`/`os.date()`, or the admin date/clock overrides stop working.
`Dates.evaluate` checks the previous, current and next year, and sorts active holidays with an experience ahead of plain
observances (so Halloween keeps the headline on Columbus Day). Quick check: `lua5.4` can load config.lua + server/dates.lua directly.

## Look and feel (keep it)
- Modern dark glass dashboard (the style current FiveM UIs use): app window with a title bar, a hero header that shows the
  holiday's scene art behind a gradient, stat cards (`setStats`), sidebar cards (`setExtra`), rounded scenes and a toast.
  Holidays only change the accent tokens; the line icon set is `ICON` in `js/core.js`, reward art is `img/rewards/*.svg`.
- Halloween in the UI: the street is dark (`.lights-out`); the cursor is a flashlight beam and ghosts are trapped by holding
  the beam on them (no clicking). The admin panel is a tablet (bezel, status bar, tabs: overview, holidays, time, halloween).
- Restrained motion, one orchestrated entrance, glow only on interactive or ready things.
- The wood advent skin is faithful to the user's reference calendar; do not redesign it unprompted. Holo is the alternate skin.
- No emoji in the UI, no all-caps labels (the Independence Day title is the one deliberate exception).
- Respect `prefers-reduced-motion`. Every timer goes through `later()`/`timers` so `stopAmbient()` can cancel it
  (it runs on re-render and on hide). Never leave timers running while the UI is closed.

## Status
Done: advent (wood + holo), 11 holiday experiences, per-holiday SVG art, admin panel, event engine, smoke tests,
date rules, client UI bridge, month-long Halloween contest (leaderboard, podium, prize claim), world ghosts caught with
flashlights, city-wide trick or treating, modern dashboard UI, tablet admin panel.
Not yet run in-game. Read `docs/halloween-contest.md` before touching Halloween. Update this section when status changes.
