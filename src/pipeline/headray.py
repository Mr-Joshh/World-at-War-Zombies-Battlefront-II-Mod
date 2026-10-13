"""Ray-cast the front of a droid head (export space, faces -Y): first hit of a ray travelling +Y at (x, z)."""
import numpy as np


def head_tris(model, bone='J_Head'):
    names = [b['name'] for b in model['bones']]
    h = names.index(bone)
    V = [p for p, w in model['verts']]
    out = []
    for obj, mat, c in model['faces']:
        idx = [x[0] for x in c]
        if any(model['verts'][i][1][0][0] == h for i in idx):
            out.append(np.array([V[i] for i in idx]))
    return out


def front_y(tris, x, z):
    """Smallest y where the line (x, *, z) crosses a triangle, or None."""
    best = None
    for t in tris:
        a, b, c = t[:, [0, 2]]
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(d) < 1e-9:
            continue
        l1 = ((b[1] - c[1]) * (x - c[0]) + (c[0] - b[0]) * (z - c[1])) / d
        l2 = ((c[1] - a[1]) * (x - c[0]) + (a[0] - c[0]) * (z - c[1])) / d
        l3 = 1 - l1 - l2
        if min(l1, l2, l3) < -1e-6:
            continue
        y = l1 * t[0][1] + l2 * t[1][1] + l3 * t[2][1]
        if best is None or y < best:
            best = y
    return best
