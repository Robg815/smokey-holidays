---
paths:
  - "server/**/*.lua"
  - "client/**/*.lua"
  - "config.lua"
---
# Lua rules
- The server is authoritative. Validate every value that comes from a client or the NUI (type, range, ownership).
  Never trust client-supplied rewards, coordinates, counts or timing.
- Parameterized SQL only (`?` placeholders). Make claims idempotent with `INSERT IGNORE` on the unique key and check
  `canCarry` before consuming an attempt. Serialize per player with the `busy` lock in server/events.lua.
- Event logic must use `Dates.today()`, `Dates.evaluate()` and `Admin.secondsOfDay()` so the admin overrides apply.
- New tunables go in `config.lua` with a one-line comment. Items referenced in config must exist in ox_inventory.
- Keep functions short and local; export only what other files need via the `Events` / `Admin` / `Ghosts` tables.
