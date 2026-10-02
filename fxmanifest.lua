fx_version 'cerulean'
game 'gta5'
lua54 'yes'

name 's2-holidays'
description 'Calendar-driven US holidays with a hologram NUI, advent calendar, seasonal experiences and an admin test panel'
version '1.0.0'
author 'Smokey'

ui_page 'web/index.html'

shared_scripts { '@ox_lib/init.lua', 'config.lua' }
client_scripts { 'client/main.lua', 'client/events.lua', 'client/admin.lua', 'client/ghosts.lua', 'client/trickortreat.lua' }
server_scripts { '@oxmysql/lib/MySQL.lua', 'server/dates.lua', 'server/admin.lua', 'server/events.lua', 'server/ghosts.lua', 'server/trickortreat.lua', 'server/main.lua' }

files { 'web/index.html', 'web/css/*.css', 'web/js/*.js', 'web/img/*.svg', 'web/img/**/*.svg' }

dependencies { 'ox_lib', 'qbx_core', 'ox_inventory', 'oxmysql' }
