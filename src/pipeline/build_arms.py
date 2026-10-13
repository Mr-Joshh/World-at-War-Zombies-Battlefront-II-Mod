"""Clone trooper first-person arms.

Stock WaW marine view arms (fully rigged fingers and sleeves) re-skinned as a black bodysuit with
black gloves, plus the SWBF2 first-person clone forearm armour bound rigidly to the elbow joints.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import sys, os, json
import numpy as np
from PIL import Image, ImageEnhance, ImageOps
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xme, retarget

GAME = paths.WAW
EX = os.path.join(paths.EXTRACT, 'msh')
OUT = paths.BUILD
STOCK = GAME + r"\model_export\viewmodels\viewmodel_usa_marine_arms.XMODEL_EXPORT"
FP_ARMS = EX + r"\reptroop\msh\rep_1st_trooper.msh"

# msh (x left, y up, z forward) -> viewmodel space (x forward, y left, z up)
AXES_VIEW = np.array([[0, 0, 1.0], [1.0, 0, 0], [0, 1.0, 0]])
ARM_MAP = {
    'bone_l_forearm': ('J_Elbow_LE', 'bone_l_wrist', 'J_Wrist_LE'),
    'bone_r_forearm': ('J_Elbow_RI', 'bone_r_wrist', 'J_Wrist_RI'),
    'bone_l_wrist': ('J_Wrist_LE', None, None),
    'bone_r_wrist': ('J_Wrist_RI', None, None),
}
ARM_ROT_PARENT = {'bone_l_wrist': 'bone_l_forearm', 'bone_r_wrist': 'bone_r_forearm'}


def build(cfg, debug_hands=False):
    m = xme.read(STOCK)
    # stock materials -> ours (same UV layout, re-coloured textures)
    remap = {'mtl_viewmodel_marine_cloth': ('mtl_cw_clone_sleeve', 'cw_clone_sleeve_c.tga'),
             'mtl_viewmodel_marine_skin': ('mtl_cw_clone_glove', 'cw_clone_glove_c.tga')}
    mats = []
    for name, typ, img in m['materials']:
        if name not in remap:
            print('NOTE stock material kept as-is:', name)
        mats.append((remap.get(name, (name, img))[0], typ, remap.get(name, (name, img))[1]))
    m['materials'] = mats

    # The marine's loose cloth forearm is as wide as the clone gauntlet: pull it in around the
    # elbow->wrist axis so it reads as a tight bodysuit under the armour.
    skin = [i for i, x in enumerate(mats) if x[0] == 'mtl_cw_clone_glove']
    sleeve_verts = set()
    for o, mi, corners in m['faces']:
        if mi not in skin:
            sleeve_verts.update(c[0] for c in corners)
    bone = {x['name']: x['offset'] for x in m['bones']}
    for side, sgn in (('LE', 1), ('RI', -1)):
        e, w = bone['J_Elbow_' + side], bone['J_Wrist_' + side]
        L = np.linalg.norm(w - e)
        ax = (w - e) / L
        for vi in sleeve_verts:
            p = m['verts'][vi][0]
            if p[1] * sgn <= 0:
                continue
            t = float((p - e) @ ax) / L
            k = np.clip((t + 0.25) / 0.30, 0.0, 1.0)  # 0 above the elbow, 1 along the forearm
            if k <= 0:
                continue
            radial = (p - e) - ((p - e) @ ax) * ax
            m['verts'][vi] = (p - radial * (1 - cfg['sleeve_shrink']) * k, m['verts'][vi][1])

    parts = ('bone_l_forearm', 'bone_r_forearm') + (('bone_l_wrist', 'bone_r_wrist') if debug_hands else ())
    keep = lambda mm: (mm['parent'] or '').lower() in parts
    roll = {'bone_l_forearm': cfg['roll_le'], 'bone_r_forearm': cfg['roll_ri']}
    verts, faces = retarget.refit(FP_ARMS, m, scale=cfg['scale'], thickness=cfg['thickness'], bmap=ARM_MAP, keep=keep,
                                  roll=roll, axes=AXES_VIEW, rot_parent=ARM_ROT_PARENT,
                                  obj=len(m['objects']), mat=len(m['materials']), vert_base=len(m['verts']))
    m['verts'].extend(verts)
    m['faces'].extend(faces)
    m['objects'].append('clone_gauntlets')
    m['materials'].append(('mtl_cw_clone_gauntlet', 'Phong', 'cw_clone_gauntlet_c.tga'))
    out = OUT + r"\model_export\viewmodel_cw_clone_arms%s.XMODEL_EXPORT" % ('_debug' if debug_hands else '')
    xme.write(out, m, 'waw-clone-wars: clone trooper view arms')
    print('wrote', out, 'verts', len(m['verts']), 'tris', len(m['faces']), 'gauntlet verts', len(verts))

    # gauntlet-only file for previews
    g = {'bones': m['bones'], 'verts': verts, 'objects': ['g'], 'materials': [('g', 'Phong', 'g.tga')],
         'faces': [(0, 0, [(c[0] - (len(m['verts']) - len(verts)), c[1], c[2]) for c in f[2]]) for f in faces]}
    xme.write(OUT + r"\model_export\_gauntlet_preview.XMODEL_EXPORT", g, 'preview only')


def textures():
    """Bodysuit sleeve and glove colour maps derived from the stock marine arm texture layout."""
    src = GAME + r"\model_export\viewmodels\textures\viewmodel_usa_marine_c.tga"
    im = Image.open(src).convert('RGB')
    grey = ImageOps.grayscale(im)
    os.makedirs(OUT + r"\textures", exist_ok=True)
    # black bodysuit: keep the folds as faint shading
    sleeve = ImageEnhance.Contrast(grey).enhance(0.6).point(lambda v: int(14 + v * 0.22)).convert('RGB')
    sleeve.save(OUT + r"\textures\cw_clone_sleeve_c.png")
    # black glove: slightly glossier / lighter than the suit so fingers read
    glove = ImageEnhance.Contrast(grey).enhance(0.9).point(lambda v: int(10 + v * 0.30)).convert('RGB')
    glove.save(OUT + r"\textures\cw_clone_glove_c.png")
    print('textures: sleeve + glove from', os.path.basename(src), im.size)


if __name__ == '__main__':
    cfg = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'arms_fit.json')))
    textures()
    build(cfg)
