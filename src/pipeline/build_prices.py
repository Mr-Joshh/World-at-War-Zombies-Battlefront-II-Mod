"""Temporary flat prices: mod/mp/zombiemode.csv, the cost table every map's add_zombie_weapon() reads before its
own price (columns: weapon, cost, ammo cost).  One row per weapon any of the four maps registers.
PRICE must match level.cw_price in mod/maps/_cw.gsc and PRICE in build_strings.py; PRICE = 0 removes the table.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import glob, os, re

PRICE = 0
EX = paths.WAW_FF
OUT = os.path.join(paths.MOD, 'mp', 'zombiemode.csv')
MODCSV = os.path.join(paths.MOD, 'mod.csv')
# build_mod.sh only copies over its staging dir, so a removed table would be linked from there again
STAGED = os.path.join(paths.WAW, 'mods', paths.MOD_NAME, 'mp', 'zombiemode.csv')
LINE = 'stringtable,mp/zombiemode.csv'


def mod_csv(on):
    """Keep the table's mod.csv line in step with PRICE."""
    raw = open(MODCSV, newline='').read()
    eol = '\r\n' if '\r\n' in raw else '\n'
    lines = [l for l in raw.split(eol) if l != LINE]
    if on:
        while lines and lines[-1] == '':
            lines.pop()
        lines += [LINE, '']
    open(MODCSV, 'w', newline='').write(eol.join(lines))


def main():
    names = set()
    for f in glob.glob(os.path.join(EX, '*', 'maps', '*.gsc')):
        for m in re.finditer(r'(?:include_weapon|add_zombie_weapon)\(\s*"([a-z0-9_]+)"', open(f, errors='replace').read()):
            names.add(m.group(1))
    if PRICE <= 0:
        for p in (OUT, STAGED):
            if os.path.exists(p):
                os.remove(p)
        mod_csv(False)
        print('prices: stock (table removed)')
        return
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', newline='\n') as f:
        for n in sorted(names):
            f.write('%s,%d,%d\n' % (n, PRICE, PRICE))
    mod_csv(True)
    print('prices: %d weapons at %d' % (len(names), PRICE))


if __name__ == '__main__':
    main()
