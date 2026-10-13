"""Wall-buy hints name the SWBF2 guns: a copy of the stock zombie.str with the WWII weapon names in the
"Press & hold F to buy <name> [Cost: n]" strings replaced (the prices stay the map's).

Written to mod/raw_override/english/localizedstrings/zombie.str; build_mod.sh swaps it into raw/ for the link
and mod.csv links it as "localize,zombie" into mod.ff.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import os, re, glob

RAW = os.path.join(paths.WAW, 'raw', 'english', 'localizedstrings', 'zombie.str')
OUT = os.path.join(paths.MOD, 'raw_override', 'english', 'localizedstrings', 'zombie.str')
EX = paths.WAW_FF

# reference (after WEAPON_) prefix -> SWBF2 name; first match wins, so the scoped / special ones come first
NAMES = [
    (r'.*_S(_B)?_\d+$', 'Sniper Rifle'), (r'PTRS41', 'Sniper Rifle'),
    (r'(COLT|NAMBU|TOKAREV|WALTHER|ZOMBIECOLT)', 'Blaster Pistol'), (r'SW357', 'Commando Pistol'),
    (r'(DOUBLEBARREL|SHOTGUN)', 'Shotgun'),
    (r'(30CAL|BAR_|DP28|FG42|MG42|TYPE99_LMG)', 'Chaingun'),
    (r'(PANZERSCHREK|BAZOOKA)', 'Rocket Launcher'), (r'M2_FLAMETHROWER', 'EMP Launcher'),
    (r'(FRAGGRENADE|STICKGRENADE|STIELHANDGRANATE|TYPE97FRAG)', 'Thermal Detonators'),
    (r'(KAR98K|MOSIN|SPRINGFIELD|TYPE99|GEWEHR43|M1CARBINE|M1GARAND|SVT40|MP40|PPSH|STG44|THOMPSON|TYPE100)',
     'DC-15A Blaster Rifle'),
]


# Temporary flat prices (user request 2026-10-07): the cost shown in these hints.  Must match level.cw_price in
# mod/maps/_cw.gsc and PRICE in build_prices.py; 0 = the maps' own prices.
PRICE = 0
PRICED = re.compile(r'(WEAPON_|RANDOM_WEAPON_|BUTTON_BUY_OPEN_DOOR_|BUTTON_BUY_CLEAR_DEBRIS_|CABINET_OPEN_|PERK_PACKAPUNCH)')


def main():
    src = os.path.join(os.path.dirname(RAW), 'zombie.str.cw-orig')
    src = src if os.path.exists(src) else RAW
    lines = open(src, encoding='latin1').read().split('\n')
    ref, n, p = None, 0, 0
    for i, line in enumerate(lines):
        m = re.match(r'REFERENCE\s+(\S+)', line)
        if m:
            ref = m.group(1)
            continue
        if ref and ref.startswith('WEAPON_') and line.startswith('LANG_ENGLISH'):
            key = ref[len('WEAPON_'):]
            for pat, name in NAMES:
                if re.match(pat, key):
                    new = re.sub(r'buy (.*?) \[Cost', 'buy %s [Cost' % name, line)
                    if new != line:
                        lines[i] = new
                        n += 1
                    break
        # temporary flat prices: the "[Cost: n]" baked into the buy hints
        if PRICE > 0 and ref and PRICED.match(ref) and line.startswith('LANG_ENGLISH'):
            new = re.sub(r'\[Cost: \d+\]', '[Cost: %d]' % PRICE, lines[i])
            if new != lines[i]:
                lines[i] = new
                p += 1
    # hint strings the map scripts use that the mod tools' zombie.str does not have (Nacht's thompson is
    # ZOMBIE_WEAPON_THOMPSON_1500, shipped only in the map's own strings): add them with the SWBF2 name
    have = set(re.findall(r'REFERENCE\s+(\S+)', '\n'.join(lines)))
    used = set()
    for f in glob.glob(os.path.join(EX, '*', 'maps', '*.gsc')):
        used |= set(re.findall(r'&"ZOMBIE_(WEAPON_[A-Z0-9_]+)"', open(f, errors='replace').read()))
    end = max(i for i, l in enumerate(lines) if l.startswith('ENDMARKER'))
    added = []
    for ref in sorted(used - have):
        key = ref[len('WEAPON_'):]
        name = next((nm for pat, nm in NAMES if re.match(pat, key)), None)
        cost = re.search(r'_(\d+)$', key)
        if not name or not cost:
            continue
        price = PRICE if PRICE > 0 else int(cost.group(1))
        added += ['REFERENCE           %s' % ref, 'LANG_ENGLISH        "Press & hold &&1 to buy %s [Cost: %d]"' % (name, price), '']
    eol = chr(13) if lines[0].endswith(chr(13)) else ''        # keep the file's line ends
    lines[end:end] = [a + eol for a in added]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='latin1', newline='') as f:
        f.write('\n'.join(lines))
    print('zombie.str: %d weapon hints renamed, %d prices set to %d, added %s' % (n, p, PRICE, [a.strip() for a in added if a.startswith('REF')]))


if __name__ == '__main__':
    main()
