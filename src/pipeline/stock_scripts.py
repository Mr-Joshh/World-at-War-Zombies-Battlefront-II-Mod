"""The stock World at War script this mod changes (maps/_loadout.gsc), rebuilt on this PC from the user's own game files.

The package does not contain the stock script.  src/patches/<name>.json holds the SHA-256 of the
original text and a list of line-range edits that carry only the mod's new lines.  The original comes from the game's
fastfiles (zone/english/*.ff) or the Mod Tools' raw/ folder; if its hash differs (another game version), the build stops.

  python stock_scripts.py                 apply every patch -> work/mod/<path>
  python stock_scripts.py --make <dir>    maintainer: write src/patches/*.json from a finished mod folder
"""
import hashlib, json, os, re, sys, zlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths

# where each original lives: ('ff', <fastfile>, <script name>) or ('raw', <path under the Mod Tools' raw/>)
SOURCES = {
    'maps/_loadout.gsc': [('raw', 'maps/_loadout.gsc')],
}
_ff_cache = {}


def ff_scripts(ff_name):
    """{script name: text} of the rawfiles in a fastfile (same reading as tools/ff_scripts.py)."""
    if ff_name not in _ff_cache:
        p = None
        for root in (paths.WAW_GAME, paths.WAW):
            c = os.path.join(root, 'zone', 'english', ff_name + '.ff')
            if os.path.exists(c):
                p = c
                break
        if p is None:
            raise SystemExit('zone/english/%s.ff not found in %s' % (ff_name, paths.WAW_GAME))
        d = open(p, 'rb').read()
        z = zlib.decompress(d[12:])
        out = {}
        for m in re.finditer(rb'((?:maps|character|aitype|animscripts|clientscripts|mptype|xmodelalias|common_scripts)/[\w/]+\.(?:gsc|csc|atr))\x00', z):
            start = m.end()
            text = z[start:z.find(b'\x00', start)]
            if len(text) < 8 or not all(c in b'\t\r\n' or 32 <= c < 127 or c >= 160 for c in text[:200]):
                continue
            out.setdefault(m.group(1).decode(), text)
        _ff_cache[ff_name] = out
    return _ff_cache[ff_name]


def lines_of(data):
    return data.decode('latin1').replace('\r\n', '\n').split('\n')


def sha(lines):
    return hashlib.sha256('\n'.join(lines).encode('latin1')).hexdigest()


def original(name, want=None):
    """The original's lines from the first source that exists (and matches want, if given)."""
    tried = []
    for src in SOURCES[name]:
        if src[0] == 'ff':
            data = ff_scripts(src[1]).get(src[2])
        else:
            p = os.path.join(paths.WAW, 'raw', *src[1].split('/'))
            data = open(p, 'rb').read() if os.path.exists(p) else None
        if data is None:
            tried.append('%s: missing' % (src,))
            continue
        ls = lines_of(data)
        if want is None or sha(ls) == want:
            return ls
        tried.append('%s: different version' % (src,))
    raise SystemExit('Cannot rebuild %s - no matching original (%s).  The patches were made for the Steam '
                     'version of World at War (1.7) with Mod Tools 1.4.' % (name, '; '.join(tried)))


def make(mod_dir):
    import difflib
    os.makedirs(paths.PATCHES, exist_ok=True)
    for name in SOURCES:
        orig = original(name)
        mine_raw = open(os.path.join(mod_dir, *name.split('/')), 'rb').read()
        mine = lines_of(mine_raw)
        ops = []
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, orig, mine, autojunk=False).get_opcodes():
            if tag != 'equal':
                ops.append([i1, i2, mine[j1:j2]])
        p = {'file': name, 'sha256': sha(orig), 'lines': len(orig), 'eol': 'crlf' if b'\r\n' in mine_raw else 'lf',
             'result_sha256': sha(mine), 'edits': ops}
        out = os.path.join(paths.PATCHES, name.replace('/', '__') + '.json')
        json.dump(p, open(out, 'w', encoding='utf-8'), indent=0)
        print('%-32s %d edits, %d new lines' % (name, len(ops), sum(len(o[2]) for o in ops)))


def apply():
    for name in SOURCES:
        p = json.load(open(os.path.join(paths.PATCHES, name.replace('/', '__') + '.json'), encoding='utf-8'))
        ls = original(name, p['sha256'])
        for i1, i2, new in sorted(p['edits'], key=lambda e: e[0], reverse=True):
            ls[i1:i2] = new
        assert sha(ls) == p['result_sha256'], name
        out = os.path.join(paths.MOD, *name.split('/'))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        eol = '\r\n' if p['eol'] == 'crlf' else '\n'
        open(out, 'wb').write(eol.join(ls).encode('latin1'))
        print('rebuilt', name)


if __name__ == '__main__':
    if '--make' in sys.argv:
        make(sys.argv[sys.argv.index('--make') + 1])
    else:
        apply()
