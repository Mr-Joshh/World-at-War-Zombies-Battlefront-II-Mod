"""Pull the rawfiles (scripts) out of a WaW fastfile so the scripts the game REALLY runs can be read.
raw/ from the mod tools is v1.4 and differs from what the shipped map fastfiles contain.

usage: ff_scripts.py <fastfile> <outdir> [name filter]
Rawfile payloads are stored as NUL-terminated text; the asset name follows the text.  Scripts are found by
their leading '#include' / comment text, and named by the 'maps/...gsc' string that follows them.
"""
import sys, zlib, os, re

d = open(sys.argv[1], 'rb').read()
z = zlib.decompress(d[12:])
out = sys.argv[2]
flt = sys.argv[3] if len(sys.argv) > 3 else ''
os.makedirs(out, exist_ok=True)
n = 0
# name strings of script rawfiles
for m in re.finditer(rb'((?:maps|character|aitype|animscripts|clientscripts|mptype|xmodelalias|common_scripts)/[\w/]+\.(?:gsc|csc|atr))\x00', z):
    name = m.group(1).decode()
    if flt and flt not in name:
        continue
    # layout: [XRawFile: name ptr, len, buffer ptr] name\0 buffer\0   -> text starts right after the name
    start = m.end()
    end = z.find(b'\x00', start)
    text = z[start:end]
    if len(text) < 8 or not all(c in b'\t\r\n' or 32 <= c < 127 or c >= 160 for c in text[:200]):
        continue
    p = os.path.join(out, name.replace('/', os.sep))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'wb') as f:
        f.write(text)
    n += 1
print(n, 'scripts written to', out)
