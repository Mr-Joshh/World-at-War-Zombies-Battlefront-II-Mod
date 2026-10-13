# WaW Clone Wars 1.0.0: Star Wars Battlefront II Zombies for Call of Duty: World at War

Nazi Zombies turned into the Clone Wars. You play as a 501st clone trooper with Republic blasters from Star Wars
Battlefront II (2005), and the zombies are B1 and super battle droids. It works on all four zombie maps: Nacht der
Untoten, Verrückt, Shi No Numa and Der Riese.

**This package contains no game files.** It has only the mod's own scripts and the build tools. When you run
`Install.bat`, it reads your own copies of World at War and Star Wars Battlefront II and converts the models,
textures, sounds and animations on your PC. **You must own both games.**

## What you need

| | |
|---|---|
| **Call of Duty: World at War** | Steam version (the scripts are matched to it, game version 1.7). |
| **World at War Mod Tools** | Version 1.0 plus the 1.1 – 1.4 updates, installed into a World at War folder (your Steam folder or a copy of it). Activision no longer hosts them; the community keeps copies (archive.org item `cod-waw-modtools` for 1.0, the updates via wiki.modme.co, which also explains how to install them). The installer checks for `bin\linker_pc.exe`, `bin\converter.exe`, `raw\`, `model_export\` and `xanim_export\`. |
| **Star Wars Battlefront II (2005)** | The original game, sold on Steam as "Star Wars Battlefront II (Classic, 2005)" or on GOG. The installer reads `GameData\data\_lvl_pc\side\rep.lvl`, `side\cis.lvl`, `fpm\rep\reptroop.lvl`, `ingame.lvl` and `sound\common.bnk`. The game is only read, never changed or launched. The 2024 *Star Wars: Battlefront Classic Collection* was not tested. |
| **Python 3.9 or newer** | From python.org, with "Add python.exe to PATH" ticked. |
| **Internet** | Once, to download numpy, Pillow and [swbf-unmunge](https://github.com/PrismaticFlower/swbf-unmunge) (about 40 MB). |
| **Disk space** | About 300 MB in this folder's `work\` (you can delete it after installing), and about 60 MB of converted files added to the Mod Tools folder. |

Windows only. Tested on Windows 11 with the Steam version of World at War and the GOG version of Battlefront II.

## Install

1. Put this folder anywhere you like. A path without special characters is safest.
2. Run **`Install.bat`**. It:
   - finds World at War and Battlefront II through Steam or GOG, and asks for any folder it cannot find (for example
     the Mod Tools, if you installed them into a copy of the game);
   - sets up a private Python environment and downloads swbf-unmunge into `work\tools`, without installing
     anything system-wide;
   - extracts the clone trooper, battle droids, guns, grenades, HUD art and gun sounds from your Battlefront II files,
     rebuilds the one stock WaW script the mod changes (`_loadout.gsc`) from your own Mod Tools, converts everything
     with the Mod Tools, links `mod.ff` and packs `clonewars.iwd`;
   - installs the mod to `%LOCALAPPDATA%\Activision\CoDWaW\mods\clonewars`.

   The build takes a few minutes.
3. Run **`Play.bat`** (Steam must be running) and pick a map. You can also pick "5" to open the game with the mod
   loaded and choose a map from the menus.

If a step fails, fix what the message says and run `Install.bat --from <step number>` to continue from that step.
`Install.bat --reconfigure` asks for the game folders again.

`Play.bat` starts the map with `devmap`, which also turns cheats on. That is the launch path that was tested.

## Controls

The stock World at War controls, plus:

| Key | Action |
|---|---|
| 3 | switch the grenade slot between thermal detonators and land mines (`Play.bat` binds it) |

## What's in it

- **Player:** a clone trooper body in third person, from SWBF2's `rep_inf_ep3trooper`. In first person you see
  white clone forearm armour over black gloves.
- **Droids:** B1 battle droids, the engineer (orange), assault (red) and assassin (camo) B1 variants, and super
  battle droids.
- **Start weapon:** the Blaster Pistol. Your first wall or box gun goes in the second slot instead of replacing it.
- **Battlefront II guns everywhere:** every WWII gun on all four maps is replaced, so the walls, the mystery box and
  Pack-a-Punch hand out SWBF2 Republic weapons. Wall hints use the SWBF2 names, and the SWBF2 model slides out of the wall.

  | You get | Instead of |
  |---|---|
  | Blaster Pistol | Colt, Walther (also the last-stand pistol) |
  | Commando Pistol | .357 Magnum |
  | DC-15A Blaster Rifle | every rifle and SMG |
  | Shotgun | double-barrel and trench gun |
  | Chaingun | BAR, FG42, MG42, .30 cal |
  | Sniper Rifle | PTRS-41, scoped Kar98k / Type 99 |
  | Rocket Launcher | Panzerschreck |
  | EMP Launcher (very hard on droids) | M2 flamethrower |

- **Battlefront II fire rates and sounds:** each gun fires at its SWBF2 rate with its own SWBF2 sound. Damage per
  shot is balanced so each gun keeps roughly the damage per second of the WWII gun it replaced, because zombie
  health climbs far beyond SWBF2's 300 HP.

  | Gun | Time between shots | Damage per shot |
  |---|---|---|
  | Blaster Pistol | 0.2 s | 110 (75 at range) |
  | Commando Pistol | 0.1 s | 90 (65 at range), x3 on headshots |
  | DC-15A Blaster Rifle | 0.2 s | 160 (115 at range) |
  | Shotgun | 1.0 s | 8 x 170 (25 at range) |
  | Chaingun | 0.05 s | 95 (70 at range) |
  | Sniper Rifle | 0.8 s | 1150 |
  | Rocket Launcher | 1 rocket, then reload | 1200 blast (150 at the edge) |
  | EMP Launcher | 1.5 s, 6 shots per charge | 1900 blast (300 at the edge) |

- **First person like Battlefront II:** every gun is the clone trooper's own first-person model. The Blaster Rifle,
  Shotgun, Sniper Rifle and EMP Launcher are held in both hands. The pistols, Chaingun and Rocket Launcher are held in
  the right hand, posed to match Battlefront II. Reloads dip the gun out of view. The guns' lights glow (the rifle's
  red sight dots, the sniper's red eyepiece, the Rocket Launcher's green sight). Blasters fire travelling blue bolts.
  The EMP Launcher fires a glowing blue energy ball.
- **Crosshair:** the Battlefront II reticle with its centre dot. It turns red over droids, and aiming down the sights
  keeps it up. The Sniper Rifle zooms in with the gun out of the way.
- **Pack-a-Punch** makes "Elite" versions with 2.5x bullet damage, 2x blast damage and bigger magazines. Der Riese
  uses its own machine. **Nacht der Untoten gets a Pack-a-Punch machine upstairs**, in the room past the corner wall
  next to the sawed-off double-barrel wall gun (5000 points). The Nacht machine upgrades every blaster but not the
  two launchers.
- **Grenades:** thermal detonators (every round, as before) and **land mines**, bought for 250 at the grenade wall
  (on Nacht: upstairs). A thrown mine plants itself where it lands, arms after a second and explodes when a droid
  walks over it. You can carry up to 12 mines.
- **Mystery box:** it only offers Battlefront guns you are not already holding, and only one EMP Launcher can be in
  play at a time. The Ray Gun, Wunderwaffe and monkey bombs keep their stock odds.
- **Prices:** each map's own prices.

## Known gaps

- **Sounds:** the Rocket Launcher's explosion and the land mines use WWII explosion sounds. Reload, equip and
  empty-click sounds are silent or WWII. Droids still make zombie noises.
- **Effects:** the EMP blast is the small blue blaster impact, not a big EMP effect, because Der Riese is at the
  engine's 400-effect limit. The rocket keeps the Panzerschreck's trail and explosion.
- **Animations** are adapted from WWII guns; none are SWBF2's own. The pistol body hides most of the wrist.
- **Unchanged from WWII:** hellhounds, wall chalk outlines and HUD weapon icons. There are no droid gibs.
- **Pack-a-Punch on Nacht** has no knuckle-crack animation or Pack-a-Punch sounds, and the gun disappears while it
  upgrades.
- **Tested solo only.** Co-op was not tested.

## What the installer changes on your PC

- `work\` in this folder holds the downloaded tools, the assets extracted from your Battlefront II install and the
  build output. **Do not share this folder**, because it contains converted game assets. You can delete it once the
  mod is installed.
- **Mod Tools folder:**
  - converted models, materials, images and animations in `raw\`, with names starting with `cw_`, `mtl_cw_`,
    `viewmodel_cw_` or `weapon_cw_`;
  - `model_export\clonewars`, `texture_assets\clonewars`, `xanim_export\clonewars`, `source_data\clonewars.gdt`
    and `mods\clonewars`;
  - `raw\english\localizedstrings\clonewars.str` and `raw\sound\clonewars`;
  - `bin\linker_pc_laa.exe`, a copy of the linker with the Large Address Aware flag, which avoids an out-of-memory
    error on some PCs;
  - `zone_source\mod.csv` (your previous one is kept as `mod.csv.before-wawcw`).

  A few stock files in `raw\` (`zombie.str` and three Der Riese weapon files) are swapped for the mod's versions only
  while linking and put back afterwards.
- `%LOCALAPPDATA%\Activision\CoDWaW\mods\clonewars` holds the installed mod (`mod.ff`, `clonewars.iwd`).
- Your WaW profile config gets the key 3 bind when you use `Play.bat`.

Nothing in the Steam or GOG installs of either game is modified.

## Uninstall

Run `Uninstall.bat`. It removes the installed mod, asks before deleting the files the build added to the Mod Tools
folder, and restores your `zone_source\mod.csv`. Then delete this folder.

## Troubleshooting

- **"Cannot rebuild maps/_loadout.gsc - no matching original"**: your Mod Tools are not version 1.4. Install the
  1.1 – 1.4 updates.
- **The linker reports `EXE_ERR_HUNK_ALLOC_FAILED`**: close other programs and run `Install.bat --from 18`.
- **"Exceeded limit of 400 'fx' assets" on Der Riese**: another mod's files are mixed into `mods\clonewars`. Run
  `Install.bat --from 18` to rebuild it cleanly.
- **The game asks to run in safe mode** after a crash: answer No.
- **Linker log:** `<Mod Tools>\mods\clonewars\linker.log`.

## Package layout

| | |
|---|---|
| `Install.bat`, `Play.bat`, `Uninstall.bat` | entry points (`installer\*.ps1`) |
| `src\mod` | the mod's own scripts (`maps\_cw.gsc`, the clone trooper and droid character scripts) and fastfile list |
| `src\patches` | the line edits to the stock `_loadout.gsc`. They carry only the mod's lines plus a SHA-256 of the original, which is read from your Mod Tools |
| `src\pipeline` | the Python build: SWBF2 extraction, model refitting onto WaW skeletons, first-person animations, textures, weapon files, effects, sounds, strings, conversion and linking (`build.py` runs it all) |

## Credits

- Mod, scripts and build tools: made by Mr-Joshh with AI assistance (Claude Code).
- Star Wars Battlefront II (2005) assets © Lucasfilm / LucasArts / Pandemic Studios. They are read from your own
  install and never distributed.
- Call of Duty: World at War, its Mod Tools, the Pack-a-Punch machine and the stock animations and effects
  © Activision / Treyarch. They are read from your own install and never distributed.
- [swbf-unmunge](https://github.com/PrismaticFlower/swbf-unmunge) by SleepKiller / PrismaticFlower (MIT) unpacks
  the Battlefront II `.lvl` files.
- Python, numpy and Pillow.

This is a fan project. It is not affiliated with or endorsed by Lucasfilm, Disney, Electronic Arts, Activision or
Treyarch. The mod you build is for your personal use. Do not upload the built `mod.ff` / `clonewars.iwd` or the
`work\` folder.
