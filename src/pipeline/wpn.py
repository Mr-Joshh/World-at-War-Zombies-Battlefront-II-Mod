"""Weapon file helpers: read()/write() the backslash-delimited key/value format; CLI diffs two weapon files."""
import sys
BS = chr(92)

def read(path):
    t = open(path, errors='replace').read().strip().split(BS)
    return t[0], dict(zip(t[1::2], t[2::2]))

def write(path, header, kv):
    with open(path, 'w', newline='') as f:
        f.write(header + ''.join(BS + k + BS + v for k, v in kv.items()))

if __name__ == '__main__':
    h1, a = read(sys.argv[1])
    if len(sys.argv) > 2:
        h2, b = read(sys.argv[2])
        print(h1, h2)
        for k in a:
            if a.get(k) != b.get(k):
                print('%-28s %-45s | %s' % (k, a.get(k)[:45], (b.get(k) or '<none>')[:60]))
        for k in b:
            if k not in a:
                print('%-28s %-45s | %s' % (k, '<none>', b[k][:60]))
    else:
        print(h1)
        for k, v in a.items():
            if v not in ('', '0'):
                print('%-28s %s' % (k, v[:90]))
