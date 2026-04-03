fx_version 'cerulean'
game 'gta5'
lua54 'yes'

version '1.2.0'

name 'smokey-holidays'
author 'Smokey'
description 'Configurable holiday collectible system for QBX with client-spawned props'

shared_scripts {
    '@ox_lib/init.lua',
    'config.lua'
}

client_scripts {
    'client.lua'
}

server_scripts {
    '@oxmysql/lib/MySQL.lua',
    'server.lua'
}

dependencies {
    'ox_lib',
    'ox_target',
    'ox_inventory',
    'oxmysql',
    'qbx_core'
}
