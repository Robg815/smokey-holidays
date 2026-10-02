-- Date rule checks. Run from the resource root: lua5.4 dev/dates_test.lua
dofile('config.lua'); dofile('server/dates.lua')
local function chk(name, c) print((c and 'PASS ' or 'FAIL ') .. name); if not c then FAILED = true end end
chk('epoch', Dates.toDays(1970,1,1) == 0)
for _, k in ipairs({0, 1, 59, 365, 10957, 20727, -1, 50000}) do local y,m,d = Dates.fromDays(k); chk('roundtrip '..k, Dates.toDays(y,m,d) == k) end
local function on(s) local y,m,d = s:match('(%d+)-(%d+)-(%d+)'); y,m,d=tonumber(y),tonumber(m),tonumber(d); local a,u = Dates.evaluate(Dates.toDays(y,m,d), y); return a,u end
local function ids(l) local t={} for _,e in ipairs(l) do t[#t+1]=e.id..'@'..e.date..'('..e.daysUntil..')' end return table.concat(t,' ') end
local a = on('2026-10-12'); chk('halloween headlines over columbus', a[1].id == 'halloween' and a[2].id == 'columbus')
chk('easter 2026 = Apr 5', ({on('2026-04-05')})[1][1].date == '2026-04-05')
chk('thanksgiving 2026 = Nov 26', ({on('2026-11-26')})[1][1].date == '2026-11-26')
chk('memorial 2026 = May 25', ({on('2026-05-25')})[1][1].date == '2026-05-25')
chk('MLK 2026 = Jan 19', ({on('2026-01-19')})[1][1].date == '2026-01-19')
local a2 = on('2026-07-03'); chk('july 4 2026 (sat) active on observed fri', a2[1].id == 'independence')
local a3 = on('2026-11-08'); chk('halloween over on nov 8', #a3 == 0 or a3[1].id ~= 'halloween')
local _, u = on('2026-12-29'); chk('upcoming wraps into next year', u[2].id == 'new_years' and u[2].date == '2027-01-01')
local y,m,d = Dates.today(); chk('today returns a date', y > 2000 and m >= 1 and d >= 1)
os.exit(FAILED and 1 or 0)
