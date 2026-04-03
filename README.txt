smokey-holidays generic package

What changed:
- single global prop model config
- single coords list in Config.Coords
- no named holiday config blocks
- generic leaderboard/stats labels
- client-spawned props with ox_target

Setup:
1. Import smokey_holidays.sql
2. Ensure ox_lib, ox_target, ox_inventory, qbx_core, oxmysql are started
3. Add the resource to your server.cfg
4. Give admins ACE permission:
   add_ace group.admin smokeyholidays.admin allow

Commands:
- /holidayleaderboard
- /myholidaystats
