"""Refit a SWBF2 .msh character onto the stock WaW character skeleton.

SWBF2 characters are in a T-pose with their own proportions; WaW animations carry the bone
translations, so every WaW character must be bound to the stock skeleton exactly.  Each SWBF2
bone gets an affine transform that moves it onto its WaW counterpart (position, direction,
segment length), vertices are blended with their original skin weights, and the weights are
renamed to WaW joints.
"""
import numpy as np
import msh
import xme

# SWBF2 bone -> (WaW joint, SWBF2 child used for direction, WaW child used for direction)
BODY_MAP = {
    'bone_root':       ('J_MainRoot', None, None),
    'bone_pelvis':     ('J_MainRoot', None, None),
    'bone_a_spine':    ('J_SpineLower', 'bone_b_spine', 'J_SpineUpper'),
    'bone_b_spine':    ('J_SpineUpper', 'bone_ribcage', 'J_Spine4'),
    'bone_ribcage':    ('J_Spine4', None, None),
    'bone_neck':       ('J_Neck', None, None),
    'bone_head':       ('J_Head', None, None),
    'bone_l_clavicle': ('J_Clavicle_LE', None, None),
    'bone_l_upperarm': ('J_Shoulder_LE', 'bone_l_forearm', 'J_Elbow_LE'),
    'bone_l_forearm':  ('J_Elbow_LE', 'bone_l_hand', 'J_Wrist_LE'),
    'bone_l_hand':     ('J_Wrist_LE', None, None),
    'bone_r_clavicle': ('J_Clavicle_RI', None, None),
    'bone_r_upperarm': ('J_Shoulder_RI', 'bone_r_forearm', 'J_Elbow_RI'),
    'bone_r_forearm':  ('J_Elbow_RI', 'bone_r_hand', 'J_Wrist_RI'),
    'bone_r_hand':     ('J_Wrist_RI', None, None),
    'bone_l_thigh':    ('J_Hip_LE', 'bone_l_calf', 'J_Knee_LE'),
    'bone_l_calf':     ('J_Knee_LE', 'bone_l_foot', 'J_Ankle_LE'),
    'bone_l_foot':     ('J_Ankle_LE', 'bone_l_toe', 'J_Ball_LE'),
    'bone_l_toe':      ('J_Ball_LE', None, None),
    'bone_r_thigh':    ('J_Hip_RI', 'bone_r_calf', 'J_Knee_RI'),
    'bone_r_calf':     ('J_Knee_RI', 'bone_r_foot', 'J_Ankle_RI'),
    'bone_r_foot':     ('J_Ankle_RI', 'bone_r_toe', 'J_Ball_RI'),
    'bone_r_toe':      ('J_Ball_RI', None, None),
}
# Bones with no direction target inherit the rotation of this bone (None = keep upright).
ROT_PARENT = {
    'bone_l_hand': 'bone_l_forearm', 'bone_r_hand': 'bone_r_forearm',
    'bone_l_toe': 'bone_l_foot', 'bone_r_toe': 'bone_r_foot',
}

MSH_TO_WAW = np.array([[1.0, 0, 0], [0, 0, -1.0], [0, 1.0, 0]])  # (x, y, z) -> (x, -z, y): Y-up to Z-up


def arc(a, b):
    """Shortest rotation taking direction a onto direction b."""
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    v = np.cross(a, b)
    c = float(np.dot(a, b))
    if c < -0.999999:
        ax = np.cross(a, [1.0, 0, 0])
        if np.linalg.norm(ax) < 1e-6:
            ax = np.cross(a, [0, 1.0, 0])
        ax /= np.linalg.norm(ax)
        return 2 * np.outer(ax, ax) - np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K / (1 + c)


def load_msh_skin(path, keep=None, axes=None):
    """Flatten a msh into world-space arrays in WaW axes (metres).
    Returns bones {name: head}, positions, normals, uvs, weights [{bone: w}], tris [(a,b,c,material)], materials."""
    d = msh.load(path)
    X = MSH_TO_WAW if axes is None else axes
    bones = {m['name'].lower(): X @ m['world'][:3, 3] for m in d['models']}
    P, N, UV, W, T = [], [], [], [], []
    for m in d['models']:
        if m['hidden'] or not m['segments']:
            continue
        if keep and not keep(m):
            continue
        Mw = m['world']
        Rn = np.linalg.inv(Mw[:3, :3]).T
        for seg in m['segments']:
            if seg['pos'] is None or not seg['tris']:
                continue
            base = len(P)
            pos = (seg['pos'] @ Mw[:3, :3].T + Mw[:3, 3]) @ X.T
            nrm = (seg['nrm'] @ Rn.T) @ X.T if seg['nrm'] is not None else np.zeros_like(pos)
            uv = seg['uv'] if seg['uv'] is not None else np.zeros((len(pos), 2))
            for i in range(len(pos)):
                if seg['wght'] is not None:
                    w = {}
                    for bi, bw in zip(*[x[i] for x in seg['wght']]):
                        if bw > 1e-4:
                            name = d['by_index'][m['envl'][bi]]['name'].lower()
                            w[name] = w.get(name, 0.0) + bw
                else:
                    owner = m['name'].lower() if m['type'] == 3 else (m['parent'] or '').lower()
                    w = {owner: 1.0}
                P.append(pos[i]); N.append(nrm[i]); UV.append(uv[i]); W.append(w)
            for a, b, c in seg['tris']:
                T.append((base + a, base + b, base + c, seg['mat']))
    return bones, np.array(P), np.array(N), np.array(UV), W, T, d['materials']


def axis_angle(axis, deg):
    a = np.asarray(axis, float) / np.linalg.norm(axis)
    t = np.radians(deg)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + np.sin(t) * K + (1 - np.cos(t)) * (K @ K)


def bone_transforms(src, dst, bmap, scale, thickness=1.0, rot_parent=ROT_PARENT, overrides=None, roll=None, root_in=None):
    """root_in: {bone: inches} - the bone's root lands that far back from its WaW joint (towards the parent) and the
    segment is stretched to still reach the child joint (bridges a gap when the WaW joint is further out)."""
    """Per-source-bone 4x4 taking metres/T-pose space onto the WaW bind pose (inches).
    scale: inches per metre used for cross-section; segment lengths always follow the WaW skeleton."""
    out, rots = {}, {}

    def rot_of(name):
        if name in rots:
            return rots[name]
        joint, s_child, d_child = bmap[name]
        if s_child:
            s_dir = src[s_child] - src[name]
            d_dir = dst[d_child] - dst[joint]
            R = arc(s_dir, d_dir)
            if roll and name in roll:
                R = axis_angle(d_dir, roll[name]) @ R
        elif rot_parent.get(name):
            R = rot_of(rot_parent[name])
        else:
            R = np.eye(3)
        if overrides and name in overrides:
            R = overrides[name] @ R
        rots[name] = R
        return R

    for name, (joint, s_child, d_child) in bmap.items():
        if name not in src:
            continue
        R = rot_of(name)
        S = np.eye(3) * scale * thickness
        if s_child:
            s_dir = src[s_child] - src[name]
            L = (np.linalg.norm(dst[d_child] - dst[joint]) + (root_in or {}).get(name, 0.0)) / np.linalg.norm(s_dir)
            u = s_dir / np.linalg.norm(s_dir)
            S = scale * thickness * (np.eye(3) - np.outer(u, u)) + L * np.outer(u, u)
        A = np.eye(4)
        A[:3, :3] = R @ S
        root = dst[joint]
        if root_in and name in root_in and s_child:
            d = dst[d_child] - dst[joint]
            root = root - root_in[name] * d / np.linalg.norm(d)
        A[:3, 3] = root - A[:3, :3] @ src[name]
        out[name] = A
    return out


def refit(msh_path, skel, scale=33.0, thickness=1.0, bmap=BODY_MAP, keep=None, overrides=None, roll=None, root_in=None,
          axes=None, rot_parent=ROT_PARENT, obj=0, mat=0, vert_base=0, log=print):
    """Returns (verts, faces) in xme.py structures, bound to the bones of `skel`."""
    joint_index = {b['name']: i for i, b in enumerate(skel['bones'])}
    dst = {b['name']: b['offset'] for b in skel['bones']}
    src, P, N, UV, W, T, mats = load_msh_skin(msh_path, keep, axes)
    A = bone_transforms(src, dst, bmap, scale, thickness, rot_parent=rot_parent, overrides=overrides, roll=roll, root_in=root_in)
    flip_v = False

    verts, normals = [], []
    unmapped = set()
    for p, n, w in zip(P, N, W):
        acc_p = np.zeros(3); acc_n = np.zeros(3); tot = 0.0
        jw = {}
        for b, bw in w.items():
            if b not in A:
                unmapped.add(b)
                continue
            M = A[b]
            acc_p += bw * (M[:3, :3] @ p + M[:3, 3])
            acc_n += bw * (np.linalg.inv(M[:3, :3]).T @ n)
            tot += bw
            j = joint_index[bmap[b][0]]
            jw[j] = jw.get(j, 0.0) + bw
        if tot <= 0:
            raise ValueError('vertex with no mapped bones: %r' % w)
        ln = np.linalg.norm(acc_n)
        normals.append(acc_n / ln if ln > 1e-9 else np.array([0, 0, 1.0]))
        verts.append((acc_p / tot, sorted(((j, x / tot) for j, x in jw.items()), key=lambda t: -t[1])))
    if unmapped:
        log('WARNING unmapped bones ignored:', sorted(unmapped))

    # msh triangles are counter-clockwise, XMODEL_EXPORT wants clockwise
    faces = []
    for a, b, c, _ in T:
        corners = []
        for vi in (a, c, b):
            u, v = UV[vi]
            corners.append((vi + vert_base, normals[vi], (u, 1.0 - v if flip_v else v)))
        faces.append((obj, mat, corners))
    return verts, faces


def retarget(msh_path, skeleton_xme, out_path, material_name, image_name, object_name='body', log=print, **kw):
    skel = xme.read(skeleton_xme)
    verts, faces = refit(msh_path, skel, log=log, **kw)
    model = {'bones': skel['bones'], 'verts': verts, 'faces': faces,
             'objects': [object_name], 'materials': [(material_name, 'Phong', image_name)]}
    import os
    xme.write(out_path, model, 'waw-clone-wars: refit of %s' % os.path.basename(msh_path))
    Pn = np.array([v[0] for v in verts])
    log('wrote', out_path, 'verts', len(verts), 'tris', len(faces), 'bbox', Pn.min(0).round(1), Pn.max(0).round(1),
        'cw-agreement', round(1 - xme.winding_agreement(model), 3))
    return model
