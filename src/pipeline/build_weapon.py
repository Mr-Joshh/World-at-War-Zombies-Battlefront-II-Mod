"""DC-15 blaster: SWBF2 first-person rifle mesh bound to the stock Thompson viewmodel skeleton,
so the stock Thompson first-person animations drive it.  Also writes the third-person world model."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import msh, xme

GAME = paths.WAW
EX = os.path.join(paths.EXTRACT, 'msh')
OUT = os.path.join(paths.BUILD, 'model_export')
THOMPSON = GAME + r"\model_export\american\weapons\SMGs\thompson\viewmodel_usa_thompson_smg.XMODEL_EXPORT"
THOMPSON_WORLD = GAME + r"\model_export\american\weapons\SMGs\thompson\weapon_usa_thompson_smg_LOD0.XMODEL_EXPORT"

# msh (x right, y up, z toward the stock; muzzle at -z after the Blender check) -> viewmodel (x forward, y left, z up)
AXES = np.array([[0, 0, 1.0], [1.0, 0, 0], [0, 1.0, 0]])
# world models are authored facing -Y like character bodies
AXES_WORLD = np.array([[1.0, 0, 0], [0, 0, -1.0], [0, 1.0, 0]])


def load_rigid(path, skip_materials=()):
    d = msh.load(path)
    P, N, UV, T = [], [], [], []
    for m in d['models']:
        if m['hidden'] or not m['segments']:
            continue
        Mw = m['world']
        for seg in m['segments']:
            if seg['pos'] is None or not seg['tris']:
                continue
            mat = d['materials'][seg['mat']]
            if any(s in (mat['tex'][0] if mat['tex'] else '') for s in skip_materials):
                continue
            base = len(P)
            pos = seg['pos'] @ Mw[:3, :3].T + Mw[:3, 3]
            nrm = seg['nrm'] @ np.linalg.inv(Mw[:3, :3]) if seg['nrm'] is not None else np.zeros_like(pos)
            uv = seg['uv'] if seg['uv'] is not None else np.zeros((len(pos), 2))
            P.extend(pos); N.extend(nrm); UV.extend(uv)
            T.extend((base + a, base + b, base + c) for a, b, c in seg['tris'])
    hp = {m['name'].lower(): m['world'][:3, 3] for m in d['models']}
    return np.array(P), np.array(N), np.array(UV), T, hp


def build(src, skeleton, out, material, image, scale, offset, sign_x=1.0, bone='J_Gun', flash_bone='tag_flash', axes=None, pitch_deg=0.0):
    """offset: where the msh origin lands in viewmodel space (inches); scale: inches per metre."""
    P, N, UV, T, hp = load_rigid(src, skip_materials=('rep_cockpit_fx',))
    A = (AXES if axes is None else axes).copy()
    A[0] *= sign_x
    # optional nose-down pitch about the grip (the msh origin) so the muzzle clears the line of sight in ADS
    t = np.radians(pitch_deg)
    Rp = np.array([[np.cos(t), 0, np.sin(t)], [0, 1, 0], [-np.sin(t), 0, np.cos(t)]])
    A = Rp @ A
    Pw = (P @ A.T) * scale + np.array(offset)
    Nw = N @ A.T
    mirrored = np.linalg.det(A) < 0
    skel = xme.read(skeleton)
    bones = skel['bones']
    bi = [b['name'] for b in bones].index(bone)
    if 'hp_fire' in hp and flash_bone in [b['name'] for b in bones]:
        fb = bones[[b['name'] for b in bones].index(flash_bone)]
        fb['offset'] = (A @ hp['hp_fire']) * scale + np.array(offset)
    verts = [(p, [(bi, 1.0)]) for p in Pw]
    faces = []
    for a, b, c in T:
        order = (a, b, c) if mirrored else (a, c, b)  # msh is CCW, export wants CW; a mirror flips it again
        faces.append((0, 0, [(v, Nw[v], tuple(UV[v])) for v in order]))
    model = {'bones': bones, 'verts': verts, 'faces': faces, 'objects': ['dc15'], 'materials': [(material, 'Phong', image)]}
    xme.write(out, model, 'waw-clone-wars: DC-15 from %s' % os.path.basename(src))
    print('wrote', out, 'verts', len(verts), 'tris', len(faces), 'bbox', Pw.min(0).round(2), Pw.max(0).round(2),
          'cw', round(1 - xme.winding_agreement(model), 3),
          'flash', bones[[b['name'] for b in bones].index(flash_bone)]['offset'].round(2) if flash_bone in [b['name'] for b in bones] else None)


if __name__ == '__main__':
    import json
    cfg = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'weapon_fit.json')))
    v = cfg['view']
    # the SWBF2 first-person rifle only has the faces its own camera sees; use the full third-person mesh
    build(EX + r"\rep\msh\rep_weap_inf_rifle.msh", THOMPSON,OUT + r"\viewmodel_cw_dc15.XMODEL_EXPORT",
          'mtl_cw_dc15', 'cw_dc15_c.tga', v['scale'], v['offset'], v.get('sign_x', 1.0), pitch_deg=v.get('pitch_deg', 0.0))
    w = cfg['world']
    build(EX + r"\rep\msh\rep_weap_inf_rifle.msh", THOMPSON_WORLD, OUT + r"\weapon_cw_dc15.XMODEL_EXPORT",
          'mtl_cw_dc15', 'cw_dc15_c.tga', w['scale'], w['offset'], w.get('sign_x', 1.0),
          bone=w['bone'], flash_bone='tag_flash', axes=AXES_WORLD)
