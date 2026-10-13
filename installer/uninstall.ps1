# Removes the installed mod and, if you agree, the files the build added to your World at War Mod Tools folder.
$ErrorActionPreference = 'Stop'
$Pkg = Split-Path -Parent $PSScriptRoot
$Work = Join-Path $Pkg 'work'
$mod = 'clonewars'
$cfg = $null
if (Test-Path (Join-Path $Work 'config.json')) { $cfg = Get-Content (Join-Path $Work 'config.json') -Raw | ConvertFrom-Json; if ($cfg.mod_name) { $mod = $cfg.mod_name } }
if (Get-Process CoDWaW -ErrorAction SilentlyContinue) { Write-Host 'Close Call of Duty: World at War first.' -ForegroundColor Red; exit 1 }

$inst = Join-Path $env:LOCALAPPDATA "Activision\CoDWaW\mods\$mod"
if (Test-Path $inst) { Remove-Item -Recurse -Force $inst; Write-Host "Removed $inst" }

if ($cfg -and (Test-Path $cfg.waw_tools)) {
    $t = $cfg.waw_tools
    $pat = '^(viewmodel_cw_|weapon_cw_|mtl_cw_|cw_)'
    $items = @()
    foreach ($d in 'xmodel', 'xmodelparts', 'xmodelsurfs', 'materials', 'material_properties', 'images', 'xanim') {
        $p = Join-Path $t "raw\$d"
        if (Test-Path $p) { $items += Get-ChildItem $p -File | Where-Object { $_.Name -match $pat } | ForEach-Object { $_.FullName } }
    }
    foreach ($rel in "model_export\clonewars", "texture_assets\clonewars", "xanim_export\clonewars", "source_data\clonewars.gdt", "mods\$mod",
                     "raw\english\localizedstrings\clonewars.str", "raw\sound\clonewars") {
        $p = Join-Path $t $rel
        if (Test-Path $p) { $items += $p }
    }
    if ($items.Count -gt 0) {
        Write-Host ''
        Write-Host "The build added $($items.Count) files / folders to your Mod Tools folder ($t):"
        Write-Host '  converted SWBF2 models, materials, images and animations (names starting with cw_ / mtl_cw_ / viewmodel_cw_ /'
        Write-Host '  weapon_cw_), the clonewars GDT and exports, the mod''s strings and sounds, and mods\' + $mod + '.'
        $a = Read-Host 'Delete them too? (y/N)'
        if ($a -eq 'y') {
            foreach ($i in $items) { Remove-Item -Recurse -Force $i }
            Write-Host 'Deleted.'
            # bin\linker_pc_laa.exe is left in place: other mods built with these Mod Tools may use it too
        }
    }
    $zs = Join-Path $t 'zone_source\mod.csv'
    if (Test-Path "$zs.before-wawcw") { Move-Item -Force "$zs.before-wawcw" $zs; Write-Host 'Restored your zone_source\mod.csv.' }
}
Write-Host ''
Write-Host "Done.  You can now delete the WaW-CloneWars folder (including $Work)."
Write-Host 'Key 3 stays bound to "set cw_nade_cycle 1" in your profile config.cfg; remove that line if you want it back.'
