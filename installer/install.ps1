# WaW Clone Wars 1.0.0 installer.
# Builds the mod on THIS PC from your own Call of Duty: World at War and Star Wars Battlefront II (2005) files,
# then installs it to %LOCALAPPDATA%\Activision\CoDWaW\mods\clonewars.  Nothing from either game ships with this package.
#
#   Install.bat                 everything (asks for folders it cannot find)
#   Install.bat --from N        resume the build at step N after fixing a problem
#   Install.bat --reconfigure   ask for the folders again
param([Parameter(ValueFromRemainingArguments = $true)] $Rest)
# 'Continue': Windows PowerShell 5.1 turns any stderr line of a native program into an error under 'Stop'.
# Cmdlets that must not fail silently use -ErrorAction Stop; native programs are checked with $LASTEXITCODE.
$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$Pkg = Split-Path -Parent $PSScriptRoot
$Work = Join-Path $Pkg 'work'
$Tools = Join-Path $Work 'tools'
$Config = Join-Path $Work 'config.json'
New-Item -ItemType Directory -Force $Tools -ErrorAction Stop | Out-Null

# pinned third-party tool (open source, downloaded from its official release page)
$UnmungeUrl = 'https://github.com/PrismaticFlower/swbf-unmunge/releases/download/v1.3.0/swbf-unmunge-v1.3.0.zip'
$UnmungeSha256 = '919b56f0b98d05e65248a3b7893096f7cbcd0737d627b99d25b8f31fc787b6cf'

function Say($msg) { Write-Host $msg -ForegroundColor Cyan }
function Fail($msg) { Write-Host ''; Write-Host $msg -ForegroundColor Red; Write-Host ''; exit 1 }

# ---------------------------------------------------------------- folders
function Steam-Libraries {
    $roots = @()
    foreach ($k in 'HKCU:\Software\Valve\Steam', 'HKLM:\SOFTWARE\WOW6432Node\Valve\Steam', 'HKLM:\SOFTWARE\Valve\Steam') {
        try {
            $p = Get-ItemProperty $k -ErrorAction Stop
            foreach ($v in 'SteamPath', 'InstallPath') { if ($p.$v) { $roots += ($p.$v -replace '/', '\') } }
        } catch {}
    }
    $libs = @()
    foreach ($r in ($roots | Select-Object -Unique)) {
        $libs += $r
        $vdf = Join-Path $r 'steamapps\libraryfolders.vdf'
        if (Test-Path $vdf) {
            foreach ($m in [regex]::Matches((Get-Content $vdf -Raw), '"path"\s+"([^"]+)"')) { $libs += ($m.Groups[1].Value -replace '\\\\', '\') }
        }
    }
    return $libs | Select-Object -Unique
}

function Steam-Game($folder) {
    foreach ($l in Steam-Libraries) {
        $p = Join-Path $l "steamapps\common\$folder"
        if (Test-Path $p) { return $p }
    }
    return $null
}

function Ask-Folder($what, $check, $hint) {
    while ($true) {
        Write-Host ''
        Write-Host "Could not find $what." -ForegroundColor Yellow
        if ($hint) { Write-Host $hint }
        $p = (Read-Host "Paste the folder path (or press Enter to cancel)").Trim('"', ' ')
        if (-not $p) { Fail 'Cancelled.' }
        $q = & $check $p
        if ($q) { return $q }
        Write-Host "That folder does not look right." -ForegroundColor Yellow
    }
}

# each check returns the folder to use (or $null)
$IsWawGame = { param($p) if ((Test-Path (Join-Path $p 'CoDWaW.exe')) -and (Test-Path (Join-Path $p 'zone\english\nazi_zombie_factory.ff'))) { $p } else { $null } }
$IsModTools = { param($p) if ((Test-Path (Join-Path $p 'bin\linker_pc.exe')) -and (Test-Path (Join-Path $p 'bin\converter.exe')) -and
                (Test-Path (Join-Path $p 'raw\maps\_loadout.gsc')) -and (Test-Path (Join-Path $p 'model_export\viewmodels.gdt')) -and
                (Test-Path (Join-Path $p 'xanim_export')) -and (Test-Path (Join-Path $p 'raw\weapons\sp\zombie_thompson'))) { $p } else { $null } }
$SwbfFiles = 'data\_lvl_pc\side\rep.lvl', 'data\_lvl_pc\side\cis.lvl', 'data\_lvl_pc\fpm\rep\reptroop.lvl', 'data\_lvl_pc\ingame.lvl',
             'data\_lvl_pc\sound\common.bnk'
# accepts the game folder or its GameData folder
$IsSwbf2 = { param($p)
    foreach ($c in @((Join-Path $p 'GameData'), $p)) {
        if (($SwbfFiles | Where-Object { -not (Test-Path (Join-Path $c $_)) }).Count -eq 0) { return $c }
    }
    return $null
}

function Find-Swbf2 {
    foreach ($f in 'Star Wars Battlefront II', 'Star Wars Battlefront II Classic', 'STAR WARS Battlefront II') {
        $g = Steam-Game $f
        if ($g) { $q = & $IsSwbf2 $g; if ($q) { return $q } }
    }
    # GOG Galaxy / GOG installer
    foreach ($k in 'HKLM:\SOFTWARE\WOW6432Node\GOG.com\Games', 'HKLM:\SOFTWARE\GOG.com\Games') {
        try {
            foreach ($g in Get-ChildItem $k -ErrorAction Stop) {
                $p = Get-ItemProperty $g.PSPath
                if ($p.gameName -match 'Battlefront II' -and $p.path) { $q = & $IsSwbf2 $p.path; if ($q) { return $q } }
            }
        } catch {}
    }
    return $null
}

$cfg = $null
if ((Test-Path $Config) -and -not ($Rest -contains '--reconfigure')) { $cfg = Get-Content $Config -Raw | ConvertFrom-Json }
if (-not $cfg) {
    Say 'Looking for your games ...'
    $waw = Steam-Game 'Call of Duty World at War'
    if (-not ($waw -and (& $IsWawGame $waw))) {
        $waw = Ask-Folder 'Call of Duty: World at War' $IsWawGame 'The folder that contains CoDWaW.exe.'
    }
    $tools = & $IsModTools $waw
    if (-not $tools) {
        $tools = Ask-Folder 'the World at War Mod Tools' $IsModTools ("The Mod Tools (1.0 with the 1.1 - 1.4 updates) must be installed into a World at War folder:`n" +
            "  it needs bin\linker_pc.exe, bin\converter.exe, raw\, model_export\ and xanim_export\.`n" +
            "  You can install them into your Steam World at War folder ($waw) or into a copy of it.  See README.md.")
    }
    $swbf = Find-Swbf2
    if (-not $swbf) {
        $swbf = Ask-Folder 'Star Wars Battlefront II (2005)' $IsSwbf2 ("The original 2005 game (Steam or GOG): the folder that contains GameData\.`n" +
            "  The installer needs GameData\data\_lvl_pc\side\rep.lvl, side\cis.lvl, fpm\rep\reptroop.lvl, ingame.lvl and sound\common.bnk.")
    }
    $cfg = [ordered]@{ waw_tools = $tools; waw_game = $waw; swbf2 = $swbf; work = $Work; mod_name = 'clonewars' }
    $cfg | ConvertTo-Json | Set-Content -Encoding UTF8 $Config -ErrorAction Stop
    $cfg = Get-Content $Config -Raw | ConvertFrom-Json
}
Write-Host ''
Write-Host "World at War:      $($cfg.waw_game)"
Write-Host "Mod Tools:         $($cfg.waw_tools)"
Write-Host "Battlefront II:    $($cfg.swbf2)"
Write-Host "Work folder:       $Work"
Write-Host ''
if (Get-Process CoDWaW -ErrorAction SilentlyContinue) { Fail 'Close Call of Duty: World at War first.' }

# ---------------------------------------------------------------- Python
function Find-Python {
    foreach ($c in @(@('py', '-3'), @('python'), @('python3'))) {
        try {
            $exe = $c[0]; $args2 = @($c | Select-Object -Skip 1)
            # no quotes in the code: Windows PowerShell 5.1 strips them from native command arguments
            $v = & $exe @args2 -c 'import sys; print(sys.version_info[0] * 100 + sys.version_info[1])' 2>$null
            if ($LASTEXITCODE -eq 0 -and $v -and [int]("$v".Trim()) -ge 309 -and [int]("$v".Trim()) -lt 400) { return , $c }
        } catch {}
    }
    return $null
}
$Venv = Join-Path $Work 'venv'
$Py = Join-Path $Venv 'Scripts\python.exe'
if (-not (Test-Path $Py)) {
    $sys = Find-Python
    if (-not $sys) { Fail 'Python 3.9 or newer is needed.  Install it from https://www.python.org/downloads/ (tick "Add python.exe to PATH"), then run Install.bat again.' }
    Say 'Creating a Python environment ...'
    $exe = $sys[0]; $args2 = @($sys | Select-Object -Skip 1)
    & $exe @args2 -m venv $Venv
    if ($LASTEXITCODE -ne 0) { Fail 'Could not create the Python environment.' }
}
& $Py -c 'import numpy, PIL' 2>$null
if ($LASTEXITCODE -ne 0) {
    Say 'Installing numpy and Pillow ...'
    & $Py -m pip install --disable-pip-version-check -q numpy pillow
    if ($LASTEXITCODE -ne 0) { Fail 'pip could not install numpy / Pillow.' }
}

# ---------------------------------------------------------------- tools
function Download($url, $out) {
    if (-not (Test-Path $out)) {
        Say "Downloading $url"
        try { Invoke-WebRequest -UseBasicParsing $url -OutFile "$out.part" -ErrorAction Stop }
        catch { Fail "Download failed: $url`n$($_.Exception.Message)`nCheck your internet connection and run Install.bat again." }
        Move-Item "$out.part" $out -ErrorAction Stop
    }
}
$Dl = Join-Path $Tools 'downloads'
New-Item -ItemType Directory -Force $Dl | Out-Null

$Unmunge = Join-Path $Tools 'swbf-unmunge\swbf-unmunge.exe'
if (-not (Test-Path $Unmunge)) {
    $z = Join-Path $Dl 'swbf-unmunge-v1.3.0.zip'
    Download $UnmungeUrl $z
    if ((Get-FileHash -Algorithm SHA256 $z).Hash -ne $UnmungeSha256) { Remove-Item $z; Fail 'swbf-unmunge download is corrupt (hash mismatch) - run Install.bat again.' }
    Expand-Archive $z (Join-Path $Tools 'swbf-unmunge') -ErrorAction Stop
    if (-not (Test-Path $Unmunge)) { Fail 'swbf-unmunge.exe was not in the download.' }
}

# ---------------------------------------------------------------- build
$zs = Join-Path $cfg.waw_tools 'zone_source\mod.csv'
$zsBackup = "$zs.before-wawcw"
if ((Test-Path $zs) -and -not (Test-Path $zsBackup) -and -not ((Get-Content $zs -TotalCount 1) -match 'clonewars')) {
    Copy-Item $zs $zsBackup       # the Mod Tools' own mod.csv is replaced while linking; keep the user's
}
Say 'Building the mod (about 15 minutes) ...'
$env:WAWCW_CONFIG = $Config
$BuildArgs = @($Rest | Where-Object { $_ -and $_ -ne '--reconfigure' })
& $Py (Join-Path $Pkg 'src\pipeline\build.py') @BuildArgs
if ($LASTEXITCODE -ne 0) { Fail 'The build stopped.  Fix the problem shown above and run Install.bat again (add --from <step> to resume).' }

Write-Host ''
Write-Host 'Installed.  Start the game with Play.bat (Steam must be running).' -ForegroundColor Green
Write-Host 'The work folder can be deleted to free space; Install.bat recreates it if you rebuild.'
