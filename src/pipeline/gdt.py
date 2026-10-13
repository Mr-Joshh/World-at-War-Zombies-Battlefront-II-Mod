"""Read / write CoD asset-manager .gdt files (ordered dict of entries)."""
import re

ENTRY = re.compile(r'^\s*"([^"]+)"\s*\(\s*"([^"]+)"\s*\)\s*$')
INHERIT = re.compile(r'^\s*"([^"]+)"\s*\[\s*"([^"]+)"\s*\]\s*$')
KV = re.compile(r'^\s*"([^"]*)"\s+"(.*)"\s*$')


def read(path):
    entries = {}
    cur = None
    for line in open(path, errors='replace').read().replace('\r', '').split('\n'):
        m = ENTRY.match(line)
        if m:
            cur = {'gdf': m.group(2), 'keys': {}}
            entries[m.group(1)] = cur
            continue
        m = INHERIT.match(line)
        if m:
            cur = {'parent': m.group(2), 'keys': {}}
            entries[m.group(1)] = cur
            continue
        m = KV.match(line)
        if m and cur is not None:
            cur['keys'][m.group(1)] = m.group(2)
    return entries


def write(path, entries):
    o = ['{']
    for name, e in entries.items():
        o.append('\t"%s" ( "%s" )' % (name, e['gdf']) if 'gdf' in e else '\t"%s" [ "%s" ]' % (name, e['parent']))
        o.append('\t{')
        for k, v in e['keys'].items():
            o.append('\t\t"%s" "%s"' % (k, v))
        o.append('\t}')
    o.append('}')
    with open(path, 'w', newline='\r\n') as f:
        f.write('\n'.join(o) + '\n')
