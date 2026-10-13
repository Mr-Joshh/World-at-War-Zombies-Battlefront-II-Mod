"""Where everything lives on this PC.  The installer writes work/config.json; every pipeline script imports this.

  waw_tools  World at War folder that has the Mod Tools installed (bin/linker_pc.exe, raw/, model_export/ ...)
  waw_game   World at War game folder used to play (zone/english/*.ff, main/*.iwd) - often the same folder
  swbf2      Star Wars Battlefront II (2005) GameData folder (data/_lvl_pc/side/rep.lvl ...)
  work       scratch folder for downloaded tools, extracted SWBF2 assets and build output
"""
import json, os

_HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(os.path.dirname(_HERE))                     # WaW-CloneWars/
SRC = os.path.join(PKG, 'src')
CONFIG = os.environ.get('WAWCW_CONFIG') or os.path.join(PKG, 'work', 'config.json')

try:
    _cfg = json.load(open(CONFIG, encoding='utf-8-sig'))      # PowerShell 5.1 writes a BOM
except FileNotFoundError:
    raise SystemExit('No %s - run Install.bat first (it writes the folder settings).' % CONFIG)

WAW = _cfg['waw_tools']
WAW_GAME = _cfg.get('waw_game') or WAW
SWBF2 = _cfg['swbf2']
SWBF2_LVL = os.path.join(SWBF2, 'data', '_lvl_pc')
WORK = _cfg.get('work') or os.path.join(PKG, 'work')

TOOLS = os.path.join(WORK, 'tools')                  # downloaded open-source tools
EXTRACT = os.path.join(WORK, 'extract', 'swbf2')     # SWBF2 assets read from the user's game (never shared)
WAW_FF = os.path.join(WORK, 'extract', 'waw_ff')     # the scripts inside the user's WaW zombie fastfiles
BUILD = os.path.join(WORK, 'build')                  # generated models / animations / textures
MOD = os.path.join(WORK, 'mod')                      # the assembled mod source tree (scripts, weapon files, sounds ...)
MOD_SRC = os.path.join(SRC, 'mod')
PATCHES = os.path.join(SRC, 'patches')

UNMUNGE = os.path.join(TOOLS, 'swbf-unmunge', 'swbf-unmunge.exe')

MOD_NAME = _cfg.get('mod_name', 'clonewars')         # the game loads it with +set fs_game mods/<MOD_NAME>
INSTALL = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Activision', 'CoDWaW', 'mods', MOD_NAME)

for _d in (TOOLS, EXTRACT, WAW_FF, BUILD, MOD) + tuple(os.path.join(BUILD, x) for x in ('model_export', 'textures', 'xanim_export', 'preview')):
    os.makedirs(_d, exist_ok=True)
