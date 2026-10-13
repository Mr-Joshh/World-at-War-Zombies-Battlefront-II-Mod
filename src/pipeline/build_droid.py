"""B1 battle droid (zombie body) and clone trooper (player body), refit onto the WaW character skeleton."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import retarget, xme

EX = os.path.join(paths.EXTRACT, 'msh')
SK = os.path.join(paths.WAW, 'model_export', 'american', 'characters', 'multiplayer', 'char_usa_marine_player_body_assault_LOD0.XMODEL_EXPORT')
OUT = os.path.join(paths.BUILD, 'model_export')


def add_eye_bones(model):
    """Zombie scripts hang the glowing-eye FX on J_Eyeball_LE; give the droid head that tag at its photoreceptors."""
    names = [b['name'] for b in model['bones']]
    head = names.index('J_Head')
    P = np.array([p for p, w in model['verts'] if w[0][0] == head])
    if not len(P):
        # the super battle droid's "head" is a dome on the chest, skinned to the ribcage: use the top middle of the body
        A = np.array([p for p, w in model['verts']])
        top = A[:, 2].max()
        P = A[(A[:, 2] > top - 7) & (np.abs(A[:, 0]) < 4)]
    front = P[:, 1].min()                       # characters face -Y
    tip = P[P[:, 1].argmin()]
    snout = P[P[:, 1] < front + 4.0]
    if len(snout) > 10 and tip[2] < P[:, 2].min() + 0.4 * (P[:, 2].max() - P[:, 2].min()):
        # B1: the face is one sloped plate from the top of the head down to the snout tip.  Its two round photoreceptors
        # are ~36 % of the way down from the top, x +-0.8.  The surface is found by ray-casting the head triangles (the
        # mesh is too sparse to sample vertices: round 7a put the tag inside the plate, where the glow was hidden) and the
        # tag sits 0.5 out along the plate's normal (forward-up).
        import headray
        tris = headray.head_tris(model)
        z = P[:, 2].max() - 0.36 * (P[:, 2].max() - P[:, 2].min())
        ex = 0.8
        y_hit = headray.front_y(tris, ex, z)
        n = np.array([0.0, -1.0, 1.0]) / np.sqrt(2.0)
        e = np.array([ex, y_hit, z]) + 1.1 * n        # round 8: 0.5 still looked sunk into the plate
        eyes = (tuple(e), (-e[0], e[1], e[2]))
    else:
        z = P[:, 2].min() + 0.55 * (P[:, 2].max() - P[:, 2].min())
        eyes = ((0.9, front + 0.4, z), (-0.9, front + 0.4, z))
    for name, e in zip(('J_Eyeball_LE', 'J_Eyeball_RI'), eyes):
        model['bones'].append({'name': name, 'parent': head, 'offset': np.array(e),
                               'rot': model['bones'][head]['rot'].copy()})
    print('eye bones at %s (head bbox %s .. %s)' % (np.round(eyes[0], 2), P.min(0).round(1), P.max(0).round(1)))


def add_sp_bones(model):
    """The single-player AI rig has J_Head_End / J_Helmet (the engine's aim-assist looks up j_helmet on
    every AI and errors out without it); the MP body skeleton used as our base does not."""
    names = [b['name'] for b in model['bones']]
    head = model['bones'][names.index('J_Head')]
    X, Y = head['rot'][0], head['rot'][1]
    end = head['offset'] + 6.37 * X - 0.29 * Y      # local offsets taken from the stock SP body rigs
    model['bones'].append({'name': 'J_Head_End', 'parent': names.index('J_Head'), 'offset': end, 'rot': head['rot'].copy()})
    model['bones'].append({'name': 'J_Helmet', 'parent': len(model['bones']) - 1,
                           'offset': end + 1.18 * X - 1.32 * Y, 'rot': head['rot'].copy()})


def raise_head(model, dz=2.5):
    """WaW's neck is much shorter than the B1's, which left the head ~3 in lower against the backpack than in SWBF2
    (the antenna and pack top stood well over the head).  Lift the head geometry back to SWBF2's proportion."""
    head = [b['name'] for b in model['bones']].index('J_Head')
    for i, (p, w) in enumerate(model['verts']):
        if w[0][0] == head:
            model['verts'][i] = (p + np.array([0, 0, dz * w[0][1]]), w)


def droid_bones(model):
    raise_head(model)
    add_sp_bones(model)
    add_eye_bones(model)


# The B1's neck is a 0.24 m rod with the head on top; WaW's J_Neck -> J_Head is ~3 in.  Mapped rigidly (no
# direction target) the rod stuck ~5 in out of the top of the head and showed as a spike / crown whenever the
# head turned.  Aim the neck at J_Head so the rod is squeezed to the WaW neck length.
DROID_MAP = dict(retarget.BODY_MAP)
DROID_MAP['bone_neck'] = ('J_Neck', 'bone_head', 'J_Head')


# B1: WaW's shoulder joints are ~2.4 in further out than the B1's narrow torso (its upper arms start inside the torso
# edge in SWBF2); mapped joint-to-joint the arms floated beside the body.  Start them 2.4 in inside the joint instead.
B1_ROOT_IN = {'bone_l_upperarm': 2.4, 'bone_r_upperarm': 2.4}


def build(src, out, material, image, post=None, bmap=retarget.BODY_MAP, root_in=None):
    skel = xme.read(SK)
    verts, faces = retarget.refit(src, skel, bmap=bmap, root_in=root_in)
    model = {'bones': skel['bones'], 'verts': verts, 'faces': faces, 'objects': ['body'],
             'materials': [(material, 'Phong', image)]}
    if post:
        post(model)
    xme.write(out, model, 'waw-clone-wars: refit of %s' % os.path.basename(src))
    P = np.array([v[0] for v in verts])
    print('wrote', os.path.basename(out), 'verts', len(verts), 'tris', len(faces), 'bbox', P.min(0).round(1), P.max(0).round(1))


# SWBF2's B1 classes are one mesh with OverrideTexture: engineer orange, assault (rocketeer) red, assassin (sniper) camo
B1_VARIANTS = (('eng', 'orange'), ('assault', 'red'), ('assassin', 'camo'))


def variants():
    src = xme.read(OUT + r"\cw_bdroid.XMODEL_EXPORT")
    for key, colour in B1_VARIANTS:
        src['materials'] = [('mtl_cw_bdroid_' + key, 'Phong', 'cw_bdroid_%s_c.tga' % key)]
        xme.write(OUT + r"\cw_bdroid_%s.XMODEL_EXPORT" % key, src, 'waw-clone-wars: B1 %s droid (%s texture)' % (key, colour))
        print('wrote cw_bdroid_%s' % key)


if __name__ == '__main__':
    build(EX + r"\cis\msh\cis_inf_bdroid.msh", OUT + r"\cw_bdroid.XMODEL_EXPORT", 'mtl_cw_bdroid', 'cw_bdroid_c.tga', droid_bones, DROID_MAP, B1_ROOT_IN)
    variants()
    build(EX + r"\cis\msh\cis_inf_sbdroid.msh", OUT + r"\cw_sbdroid.XMODEL_EXPORT", 'mtl_cw_sbdroid', 'cw_sbdroid_c.tga', droid_bones, DROID_MAP)
    build(EX + r"\rep\msh\rep_inf_ep3trooper.msh", OUT + r"\cw_clone_body.XMODEL_EXPORT", 'mtl_cw_clone', 'cw_clone_c.tga', add_sp_bones)
