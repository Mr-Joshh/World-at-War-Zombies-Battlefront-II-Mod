"""Minimal reader for SWBF2 (2005) .msh files as written by swbf-unmunge.

Returns models (bone/mesh nodes with local transforms and parents), per-segment
geometry (positions, normals, uvs, triangles, skin weights) and materials.
Coordinates are returned in the file's own space (right-handed, Y up, metres).
"""
import struct
import numpy as np

CONTAINERS = {b'HEDR', b'MSH2', b'MATL', b'MATD', b'MODL', b'GEOM', b'SEGM', b'CLTH'}


def _chunks(buf, start, end):
    pos = start
    while pos + 8 <= end:
        tag = buf[pos:pos + 4]
        size = struct.unpack_from('<I', buf, pos + 4)[0]
        yield tag, pos + 8, pos + 8 + size
        pos += 8 + size
        pos += (-pos) % 4


def _str(buf, a, b):
    return buf[a:b].split(b'\0')[0].decode('latin1')


def quat_to_mat(x, y, z, w):
    n = (x * x + y * y + z * z + w * w) ** 0.5 or 1.0
    x, y, z, w = x / n, y / n, z / n, w / n
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def _strips_to_tris(idx):
    tris, strip = [], []

    def flush():
        for i in range(len(strip) - 2):
            a, b, c = strip[i], strip[i + 1], strip[i + 2]
            if a == b or b == c or a == c:
                continue
            tris.append((a, b, c) if i % 2 == 0 else (b, a, c))

    i = 0
    while i < len(idx):
        if idx[i] & 0x8000 and i + 1 < len(idx) and idx[i + 1] & 0x8000:
            flush()
            strip = [idx[i] & 0x7FFF, idx[i + 1] & 0x7FFF]
            i += 2
        else:
            strip.append(idx[i] & 0x7FFF)
            i += 1
    flush()
    return tris


def load(path):
    buf = open(path, 'rb').read()
    materials, models = [], []

    def parse_segm(a, b):
        seg = {'mat': 0, 'pos': None, 'nrm': None, 'uv': None, 'tris': [], 'wght': None}
        for tag, s, e in _chunks(buf, a, b):
            if tag == b'MATI':
                seg['mat'] = struct.unpack_from('<I', buf, s)[0]
            elif tag == b'POSL':
                n = struct.unpack_from('<I', buf, s)[0]
                seg['pos'] = np.frombuffer(buf, '<f4', n * 3, s + 4).reshape(n, 3).astype(float)
            elif tag == b'NRML':
                n = struct.unpack_from('<I', buf, s)[0]
                seg['nrm'] = np.frombuffer(buf, '<f4', n * 3, s + 4).reshape(n, 3).astype(float)
            elif tag == b'UV0L':
                n = struct.unpack_from('<I', buf, s)[0]
                seg['uv'] = np.frombuffer(buf, '<f4', n * 2, s + 4).reshape(n, 2).astype(float)
            elif tag == b'WGHT':
                n = struct.unpack_from('<I', buf, s)[0]
                raw = np.frombuffer(buf, np.dtype([('i', '<u4'), ('w', '<f4')]), n * 4, s + 4).reshape(n, 4)
                seg['wght'] = (raw['i'].astype(int), raw['w'].astype(float))
            elif tag == b'STRP' and not seg['tris']:
                n = struct.unpack_from('<I', buf, s)[0]
                seg['tris'] = _strips_to_tris(struct.unpack_from('<%dH' % n, buf, s + 4))
            elif tag == b'NDXT' and not seg['tris']:
                n = struct.unpack_from('<I', buf, s)[0]
                v = struct.unpack_from('<%dH' % (n * 3), buf, s + 4)
                seg['tris'] = [tuple(v[i:i + 3]) for i in range(0, n * 3, 3)]
        return seg

    def parse_modl(a, b):
        m = {'name': '', 'parent': None, 'type': 0, 'index': 0, 'hidden': False,
             'scale': np.ones(3), 'rot': np.eye(3), 'pos': np.zeros(3), 'segments': [], 'envl': []}
        for tag, s, e in _chunks(buf, a, b):
            if tag == b'MTYP':
                m['type'] = struct.unpack_from('<I', buf, s)[0]
            elif tag == b'MNDX':
                m['index'] = struct.unpack_from('<I', buf, s)[0]
            elif tag == b'NAME':
                m['name'] = _str(buf, s, e)
            elif tag == b'PRNT':
                m['parent'] = _str(buf, s, e)
            elif tag == b'FLGS':
                m['hidden'] = bool(struct.unpack_from('<I', buf, s)[0] & 1)
            elif tag == b'TRAN':
                v = struct.unpack_from('<10f', buf, s)
                m['scale'] = np.array(v[0:3])
                m['rot'] = quat_to_mat(*v[3:7])
                m['pos'] = np.array(v[7:10])
            elif tag == b'GEOM':
                for t2, s2, e2 in _chunks(buf, s, e):
                    if t2 == b'SEGM':
                        m['segments'].append(parse_segm(s2, e2))
                    elif t2 == b'ENVL':
                        n = struct.unpack_from('<I', buf, s2)[0]
                        m['envl'] = list(struct.unpack_from('<%dI' % n, buf, s2 + 4))
        return m

    def parse_matd(a, b):
        mat = {'name': '', 'tex': []}
        for tag, s, e in _chunks(buf, a, b):
            if tag == b'NAME':
                mat['name'] = _str(buf, s, e)
            elif tag[:2] == b'TX' and tag[3:] == b'D':
                mat['tex'].append(_str(buf, s, e))
        return mat

    def walk(a, b):
        for tag, s, e in _chunks(buf, a, b):
            if tag == b'MATL':
                for t2, s2, e2 in _chunks(buf, s + 4, e):
                    if t2 == b'MATD':
                        materials.append(parse_matd(s2, e2))
            elif tag == b'MODL':
                models.append(parse_modl(s, e))
            elif tag in CONTAINERS:
                walk(s, e)

    walk(0, len(buf))

    by_name = {m['name'].lower(): m for m in models}
    for m in models:
        chain, cur = [], m
        while cur is not None:
            chain.append(cur)
            cur = by_name.get(cur['parent'].lower()) if cur['parent'] else None
        M = np.eye(4)
        for c in reversed(chain):
            L = np.eye(4)
            L[:3, :3] = c['rot'] * c['scale'][None, :]
            L[:3, 3] = c['pos']
            M = M @ L
        m['world'] = M
    return {'models': models, 'materials': materials, 'by_index': {m['index']: m for m in models}}


if __name__ == '__main__':
    import sys
    d = load(sys.argv[1])
    print('materials:', [(m['name'], m['tex']) for m in d['materials']])
    for m in d['models']:
        nv = sum(len(s['pos']) for s in m['segments'] if s['pos'] is not None)
        nt = sum(len(s['tris']) for s in m['segments'])
        sk = any(s['wght'] is not None for s in m['segments'])
        p = m['world'][:3, 3]
        print(f"{m['index']:3d} {m['name']:<24} parent={m['parent'] or '-':<18} type={m['type']} hid={int(m['hidden'])} "
              f"world=({p[0]:.3f},{p[1]:.3f},{p[2]:.3f}) verts={nv} tris={nt} skinned={sk} envl={len(m['envl'])}")
