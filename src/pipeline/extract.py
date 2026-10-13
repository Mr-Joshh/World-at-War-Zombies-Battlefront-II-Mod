"""Read what the build needs from the user's own games into work/extract (never shared).

  SWBF2  swbf-unmunge turns the munged .lvl files into .msh models and textures:
           side/rep.lvl, side/cis.lvl   -> extract/swbf2/rep, cis              (textures as .png, models as glTF)
           side/rep.lvl, side/cis.lvl,
           fpm/rep/reptroop.lvl         -> extract/swbf2/msh/<name>            (models as .msh with skin weights, .tga)
           ingame.lvl                   -> extract/swbf2/ui_ingame             (.msh + .png: HUD, grenades, mines, EMP)
         The gun sounds are read straight from sound/common.bnk by build_weapon_data.py.
  WaW    the scripts inside the zombie maps' fastfiles -> extract/waw_ff/<fastfile> (wall-gun names and hint strings).

swbf-unmunge writes its output next to the input file, so each .lvl is copied into a temporary folder first;
the SWBF2 install is only read.
"""
import os, shutil, subprocess, sys, zlib, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths

# (lvl under data/_lvl_pc, output folder under extract/swbf2, extra swbf-unmunge arguments)
LVLS = [
    ('side/rep.lvl', 'rep', ['-modelfmt', 'glTF', '-modeldiscard', 'lod_collision', '-imgfmt', 'png']),
    ('side/cis.lvl', 'cis', ['-modelfmt', 'glTF', '-modeldiscard', 'lod_collision', '-imgfmt', 'png']),
    ('side/rep.lvl', 'msh/rep', ['-modeldiscard', 'lod_collision', '-imgfmt', 'tga']),
    ('side/cis.lvl', 'msh/cis', ['-modeldiscard', 'lod_collision', '-imgfmt', 'tga']),
    ('fpm/rep/reptroop.lvl', 'msh/reptroop', ['-modeldiscard', 'lod_collision', '-imgfmt', 'tga']),
    ('ingame.lvl', 'ui_ingame', ['-imgfmt', 'png']),
]
# a file from each output that later steps read: when present, that extraction is done
DONE_MARK = {'rep': 'models/rep_1st_weap_inf_rifle.png', 'cis': 'models/cis_inf_battledroid_orange.png',
             'msh/rep': 'msh/rep_inf_ep3trooper.msh', 'msh/cis': 'msh/cis_inf_bdroid.msh',
             'msh/reptroop': 'msh/rep_1st_trooper.msh', 'ui_ingame': 'msh/hud_main_reticule.msh'}

FASTFILES = {'prototype': 'nazi_zombie_prototype', 'patch': 'patch',
             'nazi_zombie_asylum': 'nazi_zombie_asylum', 'nazi_zombie_asylum_patch': 'nazi_zombie_asylum_patch',
             'nazi_zombie_sumpf': 'nazi_zombie_sumpf', 'nazi_zombie_sumpf_patch': 'nazi_zombie_sumpf_patch',
             'nazi_zombie_factory': 'nazi_zombie_factory', 'nazi_zombie_factory_patch': 'nazi_zombie_factory_patch'}


def unmunge():
    tmp = os.path.join(paths.WORK, 'extract', '_in')
    for rel, out, args in LVLS:
        dst = os.path.join(paths.EXTRACT, *out.split('/'))
        if os.path.exists(os.path.join(dst, *DONE_MARK[out].split('/'))):
            print('%-14s already extracted' % out)
            continue
        src = os.path.join(paths.SWBF2_LVL, *rel.split('/'))
        if not os.path.exists(src):
            raise SystemExit('Missing %s - is this the Star Wars Battlefront II (2005) GameData folder?' % src)
        if os.path.exists(tmp):
            shutil.rmtree(tmp)
        os.makedirs(tmp)
        base = os.path.splitext(os.path.basename(src))[0]
        shutil.copyfile(src, os.path.join(tmp, base + '.lvl'))
        r = subprocess.run([paths.UNMUNGE, '-file', base + '.lvl'] + args, cwd=tmp, stdin=subprocess.DEVNULL,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors='replace')
        if not os.path.isdir(os.path.join(tmp, base)):
            print(r.stdout[-3000:])
            raise SystemExit('swbf-unmunge failed on %s' % src)
        if os.path.exists(dst):
            shutil.rmtree(dst)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(os.path.join(tmp, base), dst)
        if not os.path.exists(os.path.join(dst, *DONE_MARK[out].split('/'))):
            raise SystemExit('swbf-unmunge did not write %s from %s' % (DONE_MARK[out], src))
        print('%-14s <- %s' % (out, rel))
    if os.path.exists(tmp):
        shutil.rmtree(tmp)
    bank = os.path.join(paths.SWBF2_LVL, 'sound', 'common.bnk')
    if not os.path.exists(bank):
        raise SystemExit('Missing %s (the SWBF2 sound bank the gun sounds come from).' % bank)


def ff_scripts():
    """Scripts stored in WaW's zombie map fastfiles (same reading as ff_scripts.py)."""
    for out, ff in FASTFILES.items():
        dst = os.path.join(paths.WAW_FF, out)
        if os.path.isdir(os.path.join(dst, 'maps')):
            continue
        p = None
        for root in (paths.WAW_GAME, paths.WAW):
            c = os.path.join(root, 'zone', 'english', ff + '.ff')
            if os.path.exists(c):
                p = c
                break
        if p is None:
            raise SystemExit('zone/english/%s.ff not found in %s - all four zombie maps are needed.' % (ff, paths.WAW_GAME))
        z = zlib.decompress(open(p, 'rb').read()[12:])
        n = 0
        for m in re.finditer(rb'((?:maps|character|aitype|animscripts|clientscripts|mptype|xmodelalias|common_scripts)/[\w/]+\.(?:gsc|csc|atr))\x00', z):
            start = m.end()
            text = z[start:z.find(b'\x00', start)]
            if len(text) < 8 or not all(c in b'\t\r\n' or 32 <= c < 127 or c >= 160 for c in text[:200]):
                continue
            f = os.path.join(dst, *m.group(1).decode().split('/'))
            os.makedirs(os.path.dirname(f), exist_ok=True)
            open(f, 'wb').write(text)
            n += 1
        print('%-26s %d scripts' % (ff + '.ff', n))


if __name__ == '__main__':
    unmunge()
    ff_scripts()
