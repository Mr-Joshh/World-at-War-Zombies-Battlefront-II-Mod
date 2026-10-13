"""Every maps\\<file>::<function> the mod's scripts call must exist in the script each map really runs (cross-file
calls are resolved when the script compiles: one missing function = a compile error on that map, e.g. Nacht has
no _zombiemode_perks).  Map scripts come from the fastfiles (extract_ff.py -> work/extract/waw_ff)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import os, re, glob

MOD = paths.MOD
EX = paths.WAW_FF
RAW = os.path.join(paths.WAW, 'raw')
MAPS = {'prototype': ['prototype', 'patch'], 'asylum': ['nazi_zombie_asylum_patch', 'nazi_zombie_asylum', 'patch'],
        'sumpf': ['nazi_zombie_sumpf_patch', 'nazi_zombie_sumpf', 'patch'],
        'factory': ['nazi_zombie_factory_patch', 'nazi_zombie_factory']}


def find(script, dirs):
    p = os.path.join(MOD, script.replace('\\', os.sep) + '.gsc')
    if os.path.exists(p):
        return p
    for d in dirs:
        p = os.path.join(EX, d, script.replace('\\', os.sep) + '.gsc')
        if os.path.exists(p):
            return p
    p = os.path.join(RAW, script.replace('\\', os.sep) + '.gsc')
    return p if os.path.exists(p) else None


bad = 0
for f in glob.glob(os.path.join(MOD, 'maps', '_cw*.gsc')) + glob.glob(os.path.join(MOD, 'character', '*.gsc')):
    refs = set(re.findall(r'((?:maps|character)\\[A-Za-z0-9_]+)::([A-Za-z0-9_]+)', open(f).read()))
    for m, dirs in MAPS.items():
        for script, fn in sorted(refs):
            src = find(script, dirs)
            if not src or not re.search(r'^' + fn + r'\s*\(', open(src, errors='replace').read(), re.M | re.I):
                print('MISSING on %-9s %s::%s (%s) used in %s' % (m, script, fn, src, os.path.basename(f)))
                bad += 1
print('checked; %d missing' % bad)
sys.exit(1 if bad else 0)
