"""Parse a compiled xmodelparts file: bone names, parents, local offsets, local quats."""
import struct, sys
def read(path):
    d = open(path, 'rb').read()
    ver, nb, nroot = struct.unpack_from('<HHH', d, 0)
    p = 6
    bones = [{'parent': -1, 'off': (0.0, 0.0, 0.0), 'q': (0, 0, 0)} for _ in range(nroot)]
    for i in range(nb):
        par = struct.unpack_from('<b', d, p)[0]; p += 1
        off = struct.unpack_from('<3f', d, p); p += 12
        q = struct.unpack_from('<3h', d, p); p += 6
        bones.append({'parent': par, 'off': off, 'q': q})
    for b in bones:
        e = d.index(b'\0', p)
        b['name'] = d[p:e].decode('latin1'); p = e + 1
    return ver, bones
if __name__ == '__main__':
    ver, bones = read(sys.argv[1])
    print('version', ver, 'bones', len(bones))
    for i, b in enumerate(bones):
        print(i, b['parent'], b['name'], tuple(round(x, 2) for x in b['off']))


def world(bones):
    """Adds 'woff' (world offset) and 'wrot' (3x3, rows = bone X/Y/Z axes in world) to each bone."""
    import numpy as np
    for b in bones:
        x, y, z = (c / 32767.0 for c in b['q'])
        w = max(0.0, 1.0 - x * x - y * y - z * z) ** 0.5
        R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                      [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                      [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])  # columns = local axes in parent space
        if b['parent'] < 0:
            b['wR'] = R; b['woff'] = np.array(b['off'])
        else:
            p = bones[b['parent']]
            b['wR'] = p['wR'] @ R
            b['woff'] = p['woff'] + p['wR'] @ np.array(b['off'])
        b['wrot'] = b['wR'].T
    return bones
