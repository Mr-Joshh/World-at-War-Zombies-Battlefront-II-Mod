# Starts Call of Duty: World at War through Steam with the Clone Wars mod loaded, on the zombie map you pick.
$ErrorActionPreference = 'Stop'
$mod = 'clonewars'
$cfgFile = Join-Path (Split-Path -Parent $PSScriptRoot) 'work\config.json'
if (Test-Path $cfgFile) { $c = Get-Content $cfgFile -Raw | ConvertFrom-Json; if ($c.mod_name) { $mod = $c.mod_name } }
$ff = Join-Path $env:LOCALAPPDATA "Activision\CoDWaW\mods\$mod\mod.ff"
if (-not (Test-Path $ff)) { Write-Host "The mod is not installed yet - run Install.bat first." -ForegroundColor Red; exit 1 }
$steam = $null
foreach ($k in 'HKCU:\Software\Valve\Steam', 'HKLM:\SOFTWARE\WOW6432Node\Valve\Steam') {
    try { $p = Get-ItemProperty $k -ErrorAction Stop; foreach ($v in 'SteamExe', 'InstallPath', 'SteamPath') { if ($p.$v -and -not $steam) { $steam = $p.$v } } } catch {}
}
if ($steam -and -not $steam.ToLower().EndsWith('.exe')) { $steam = Join-Path $steam 'steam.exe' }
if (-not $steam -or -not (Test-Path $steam)) { Write-Host 'Steam was not found.' -ForegroundColor Red; exit 1 }

Write-Host ''
Write-Host '  Clone Wars Zombies - pick a map:'
Write-Host '    1  Nacht der Untoten'
Write-Host '    2  Verruckt'
Write-Host '    3  Shi No Numa'
Write-Host '    4  Der Riese'
Write-Host '    5  Just open the game with the mod loaded (pick from the menus)'
Write-Host ''
$maps = @{ '1' = 'nazi_zombie_prototype'; '2' = 'nazi_zombie_asylum'; '3' = 'nazi_zombie_sumpf'; '4' = 'nazi_zombie_factory' }
$choice = (Read-Host 'Map number').Trim()
$launch = @('-applaunch', '10090', '+set', 'fs_game', "mods/$mod", '+bind', '3', 'set cw_nade_cycle 1')
if ($maps.ContainsKey($choice)) { $launch += @('+devmap', $maps[$choice]) }
# key 3 switches between thermal detonators and land mines: the launcher binds it (the bind is saved in your profile config)
& $steam @launch
