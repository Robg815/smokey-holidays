# Halloween: month-long contest and world ghosts

Halloween runs all October. Players earn points trick-or-treating and catching ghosts; the board closes at the end of
Halloween night and the top three can claim prizes. Ghosts also appear in the world, but only where players are.

## Decisions (already made)
- Window: Oct 1 to Nov 7 (`before = 30, after = 7` on the holiday row). Contest closes at the end of Oct 31
  (`contest.endsHour = 24` means midnight). After close, houses and ghosts are disabled and the UI shows results.
- Points live in config: per outcome (`points`), UI ghost (`ghostCatch.points`), world ghost (`world.points`).
  Ties go to whoever reached the score first (`updated` column).
- Winners are locked in by `finalize` (called when the UI opens after close and by a 60 s thread), announced to everyone
  with `ox_lib:notify`, and claim prizes with `play` arg `8` until the holiday window ends.
- Names on the board follow `contest.names` (`'initial'` by default: "Alex R.").
- Ghosts are deliberately conservative: only near an online player who can still catch one today, local (non-networked) ped on that player's client
  only, hard server cap, per-player cooldown, minimum separation, night only, skip fast drivers, server-verified catch
  (owner, token, distance, daily cap), player opt-out via `/halloweenghosts`.

## Done
Everything below is implemented. The Lua has not been run in-game yet; use the test recipe at the end.
- [x] `config.lua`: halloween window, `Config.Events.halloween` (outcomes with points, `ghostCatch`, `contest`, `world`), `Config.Ghosts`.
- [x] `server/events.lua`: tables `s2_holiday_points` / `s2_holiday_winners`, `addPoints`, `standing`, `finalize`, `claimPrize`,
      `Events.contestOpen(id)`, `Events.worldCatch(src)`, `Events.nameOf`, contest data in `Events.state`, points on every play.

## Also done
- [x] `server/ghosts.lua` (add to fxmanifest after `server/events.lua`). Global `Ghosts = { active = {}, count = 0, last = {}, byPlayer = {} }`.
  - Spawn loop: wait `math.random(interval[1], interval[2])` s; proceed only if Halloween is in `Dates.evaluate` active AND
    `Events.contestOpen('halloween')` AND `Ghosts.count < maxActive`. Pick a random eligible player: logged-in char, routing bucket 0,
    alive, no ghost yet (`byPlayer`), past `playerCooldown`, not in a vehicle faster than `skipVehicleSpeed`.
  - `Ghosts.spawnFor(src, force)`: position = player coords + random angle, radius in `radius`; refuse if within `minSeparation` of another
    ghost (unless `force`). Register `active[id] = { src, coords, expires }`, then
    `lib.callback('s2-holidays:ghost:spawn', src, cb, { id, x, y, z, ttl, model, alpha, light, nightOnly })`; if the client answers false, `Ghosts.remove(id)`.
  - `lib.callback.register('s2-holidays:ghost:catch', function(src, id) ...)`: ghost exists, `g.src == src`, not expired (+15 s grace),
    player within `catchRadius` of `g.coords`; remove it, then `local r = Events.worldCatch(src); r.final = true; return r`.
    Failures before removal return `{ ok = false, msg = ... }`; an expired or missing ghost returns `final = true` too.
  - Cleanup thread every 20 s for expired ghosts; `playerDropped` removes that player's ghost; `Ghosts.clear()` also fires
    `TriggerClientEvent('s2-holidays:ghost:clear', -1)`.
- [x] `client/ghosts.lua` (add to fxmanifest `client_scripts`).
  - Callback `s2-holidays:ghost:spawn`: return false if the player opted out (`/halloweenghosts`, stored with `SetResourceKvpInt`),
    a ghost already exists, or `nightOnly` and the in-game hour is outside 20:00 to 06:00. Otherwise `CreatePed(4, model, x, y, groundZ + 0.9, heading, false, false)`
    (isNetwork = false), alpha from config, invincible, frozen, no collision. Return true.
  - Haunt loop: slow orbit and bob around the spawn point; `DrawLightWithRange` with `light` when within 45 m; once within 12 m fire a
    short scare (camera shake + `AnimpostfxPlay` + sound); within 2.8 m show `lib.showTextUI('[E] Catch the ghost')`.
    `Wait(250)` when far, `Wait(0)` only when close. Despawn (fade alpha) on expiry, distance > 200 m, catch, or the clear event.
  - On E: `lib.progressCircle` (about 1.8 s, cancelable), then `lib.callback.await('s2-holidays:ghost:catch', false, id)`;
    `lib.notify` with label and `+points`. Clear the ghost when `res.ok` or `res.final`; otherwise let the player retry.
  - Delete the ped and hide the text UI on resource stop.
- [x] `server/admin.lua`: `build()` also returns `ghosts = Ghosts.count`, `ghostMax = Config.Ghosts.maxActive`.
      Actions: `spawnGhost` (`Ghosts.spawnFor(src, true)`), `clearGhosts`, `addPoints` (to the admin, default 100, via `Events.addPoints`),
      `resetContest` (delete this year's `s2_holiday_points`, `s2_holiday_winners`, and `halloween_ghost` claims for everyone).
- [x] `fxmanifest.lua`: add `server/ghosts.lua` and `client/ghosts.lua`.
- [x] Web, `js/core.js`: in `render()` reset the sidebar (`h2` to "Coming up", `#upcoming` className to '') before building the list.
- [x] Web, `js/events.js`:
  - `renderSpots`: if `ev.contest`, call `renderBoard(ev.contest)` and, when `!ev.contest.open`, return `renderResults(ev)`.
    Progress line adds `Your score: N pts, rank #R`, plus the hint and `Ghosts caught today: today/cap` from `ev.world`.
  - `renderBoard`: sidebar becomes "Leaderboard" (top 5, your row pinned below with a dashed border if you are outside the top 5),
    and `#countdown` shows `Ends in 12 days` / `Ends in 5h 12m` / `Contest closed`.
  - `renderResults`: podium (2nd, 1st, 3rd) over the Halloween backdrop with `img/halloween/trophy.svg`; a claim button
    (`class="grace ready" data-arg="8"`) when `ev.contest.prize && !claimed`.
  - Click handler: `arg = ... p.dataset.arg ? +p.dataset.arg : ...`; for `arg === 8` mark claimed, re-render, and `reveal`. After a normal play,
    merge `res.contest` (board, points, rank) into `ev.contest` and show `+N pts` in the toast/reveal.
- [x] `css/events.css`: `#upcoming.board` list (rank medals, `.you`, `.gap`; neutralize the timeline dots with `content: none`), `.results`, `.podium`, `.pod`.
- [x] Art: `web/img/halloween/trophy.svg` (original: golden cup topped with a pumpkin). Add it to `dev/art.py`.
- [x] `js/admin.js` and `css/admin.css`: header shows `Ghosts active n/max`; Tools row with Spawn ghost near me, Clear ghosts,
      +100 points, and Reset contest (two-step confirm: first click changes the label to "Click again to confirm").
- [x] `js/preview.js`: halloween preview gets `contest` + `world`; `?closed` shows winners and an unclaimed prize; mock `play` arg 8; mock the new admin actions.
- [x] `dev/smoke.py`: board renders with your row, results view shows the podium and the claim button, claim marks it claimed.
- [x] Update `README.md` and the Status section of `CLAUDE.md`.

## Contracts
`state.event` for Halloween (open contest):
```json
{ "id": "halloween", "kind": "spots", "spots": 5, "picks": 5, "used": 2, "opened": [{ "n": 2, "kind": "treat", "label": "Candy haul" }], "ghost": true,
  "contest": { "open": true, "secondsLeft": 1047600, "points": 85, "rank": 3, "hint": "Treats +10, ...",
               "board": [{ "rank": 1, "name": "Marcus T.", "points": 240, "you": false }] },
  "world": { "today": 2, "cap": 8 } }
```
Closed contest: `contest.open = false`, `secondsLeft = 0`, `used = picks`, `ghost = false`, plus
`contest.winners = [{ place, name, points, you }]` and `contest.prize = { place, label, claimed }` (only for a winner).
`play` response for spots/ghost: `{ ok, kind, label, msg, points, contest = { board, points, rank } }`.
Prize claim (`play` arg 8): `{ ok = true, kind = 'prize', label, msg }`.

## Test recipe (admin panel, `/holidayadmin`)
1. Force Halloween on, spawn a ghost near yourself, walk up and catch it (+30 pts, daily cap 8).
2. Add points to a few characters, then set the date to Oct 31 and the fake time to 23:59:30.
3. Watch the contest close at midnight: results view, city-wide announcement, winners can claim once.
