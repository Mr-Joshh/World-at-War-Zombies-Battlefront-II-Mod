"""Every SWBF2 Republic gun as WaW models: a viewmodel bound to a stock donor skeleton (so the donor's
first-person animations drive it), a third-person world model and, for the launchers, a projectile model.

SWBF2 weapon meshes all have their origin at the top of the pistol grip (where the hand goes), muzzle
towards +z, y up.  The full third-person meshes are used for the viewmodels too: the first-person meshes
only contain the faces SWBF2's own camera sees.

Lights painted into the textures (the DC-15's red ammo display / dial, the pistol's red LEDs, the
launcher's green lamp) get an additive copy of the faces that use them, so they glow instead of
disappearing into WaW's lighting like plain texture detail.

Writes build/model_export/{viewmodel,weapon}_cw_<gun>.XMODEL_EXPORT, the projectile model and
build/textures/cw_<gun>_glow.png; build_assets.py converts them.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import sys, os
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xme
from build_weapon import load_rigid, AXES, AXES_WORLD, THOMPSON, THOMPSON_WORLD
from build_thermal import skeleton_from_parts

EX = paths.EXTRACT
B = paths.BUILD
OUT = B + r"\model_export"

# donor -> (skeleton loader, bone the gun is bound to)
DONORS = {
    'thompson': (lambda: xme.read(THOMPSON)['bones'], 'J_Gun'),
    'colt': (lambda: skeleton_from_parts('viewmodel_usa_colt45_pistol1'), 'j_gun'),
    'ptrs': (lambda: skeleton_from_parts('viewmodel_rus_PTRS1'), 'j_gun'),
    'panzer': (lambda: skeleton_from_parts('viewmodel_ger_panzerschreck_at1'), 'j_gun'),
}

# view: offset = where the grip (mesh origin) lands, relative to the donor's gun bone, in inches
# (thompson: J_Gun is at (-7.31, -0.05, -1.89) in its export, so the DC-15's verified (-9.3, 0, -3.9) is (-2, 0, -2) from it)
GUNS = {
    'dc15': dict(mesh=r'msh\rep\msh\rep_weap_inf_rifle.msh', tex=r'rep\models\rep_1st_weap_inf_rifle.png',
                 donor='thompson', scale=28.0, grip=(-2.0, 0.05, -2.01), pitch=2.2, glow=True),
    'chaingun': dict(mesh=r'msh\rep\msh\rep_weap_inf_chaingun.msh', tex=r'rep\models\rep_weap_inf_chaingun.png',
                     donor='thompson', scale=22.0, grip=(-2.0, 0.05, -2.3), pitch=1.0),
    'pistol': dict(mesh=r'msh\rep\msh\rep_weap_inf_pistol.msh', tex=r'rep\models\rep_1st_weap_inf_pistol.png',
                   donor='colt', scale=17.0, grip=(0.0, 0.0, -1.2), pitch=0.0, glow=True),
    'sniper': dict(mesh=r'msh\rep\msh\rep_weap_inf_sniperrifle.msh', tex=r'rep\models\rep_1st_weap_inf_sniperrifle.png',
                   donor='ptrs', scale=28.0, grip=(-1.0, 0.0, -2.5), pitch=0.0),
    'launcher': dict(mesh=r'msh\rep\msh\rep_weap_inf_launcher.msh', tex=r'rep\models\rep_1st_weap_inf_launcher.png',
                     donor='thompson', scale=18.0, grip=(-2.0, 0.05, -2.0), pitch=0.0, glow=True),
    'emp': dict(mesh=r'ui_ingame\msh\com_weap_inf_torpedo.msh', tex=r'ui_ingame\textures\com_1st_weap_inf_torpedo.png',
                donor='thompson', scale=24.0, grip=(-2.0, 0.05, -2.0), pitch=0.0),
}
WORLD_OFFSET = (0.0, 8.5, -3.0)       # grip on tag_weapon (verified with the DC-15)
WORLD_SCALE = 28.0


def glow_mask(rgb):
    """Painted lights: bright and strongly saturated texels."""
    a = rgb.astype(float)
    s = np.sort(a, 2)
    return (s[..., 2] > 90) & (s[..., 1] < 0.45 * s[..., 2])


def glow_texture(key, tex_path, lens=None):
    rgb = np.asarray(Image.open(tex_path).convert('RGB'))
    m = glow_mask(rgb)
    if lens:
        # a lens that is painted too dull for glow_mask (the sniper scope's red eyepiece)
        yy, xx = np.mgrid[0:rgb.shape[0], 0:rgb.shape[1]]
        m = m | ((xx - lens[0]) ** 2 + (yy - lens[1]) ** 2 <= lens[2] ** 2)
    # additive colours render far brighter than their 8-bit value in WaW: keep it at about half
    out = np.zeros_like(rgb, dtype=float)
    out[m] = rgb[m] * 0.55
    os.makedirs(B + r"\textures", exist_ok=True)
    Image.fromarray(out.astype('uint8')).save(B + r"\textures\cw_%s_glow.png" % key)
    return m


def faces_on_mask(UV, T, mask):
    """Triangles whose UV footprint touches a glowing texel (the glow texture is black everywhere else)."""
    H, W = mask.shape
    keep = []
    for i, t in enumerate(T):
        uv = UV[list(t)]
        x = (uv[:, 0] % 1.0) * W
        y = ((-uv[:, 1]) % 1.0) * H        # msh v runs negative (see build/preview uv plot)
        if x.max() - x.min() > W / 2 or y.max() - y.min() > H / 2:
            continue                        # wraps across the texture edge: not a small decal
        x0, x1 = int(max(x.min() - 1, 0)), int(min(x.max() + 2, W))
        y0, y1 = int(max(y.min() - 1, 0)), int(min(y.max() + 2, H))
        if mask[y0:y1, x0:x1].any():
            keep.append(i)
    return keep


def rigid_model(P, N, UV, T, bones, bone, key, material, image, A, scale, offset, glow=None, flash=None, hp=None):
    Pw = (P @ A.T) * scale + np.array(offset)
    Nw = N @ A.T
    mirrored = np.linalg.det(A) < 0
    names = [b['name'] for b in bones]
    bi = names.index(bone)
    if flash and hp is not None and 'hp_fire' in hp and flash in names:
        bones[names.index(flash)]['offset'] = (A @ hp['hp_fire']) * scale + np.array(offset)
    verts = [(p, [(bi, 1.0)]) for p in Pw]
    m = {'bones': bones, 'verts': verts, 'faces': [], 'objects': [key], 'materials': [(material, 'Phong', image)]}

    def tri(a, b, c):
        return (a, b, c) if mirrored else (a, c, b)      # msh is CCW, export wants CW; a mirror flips it again

    for a, b, c in T:
        m['faces'].append((0, 0, [(v, Nw[v], tuple(UV[v])) for v in tri(a, b, c)]))
    if glow is not None:
        sel = faces_on_mask(UV, T, glow)
        m['objects'].append(key + '_glow')
        m['materials'].append(('mtl_cw_%s_glow' % key, 'Phong', 'cw_%s_glow_c.tga' % key))
        remap = {}
        for i in sel:
            for v in T[i]:
                if v not in remap:
                    remap[v] = len(m['verts'])
                    n = Nw[v] / (np.linalg.norm(Nw[v]) or 1.0)
                    m['verts'].append((Pw[v] + n * 0.015, [(bi, 1.0)]))     # just off the surface: no z-fighting
        for i in sel:
            a, b, c = T[i]
            m['faces'].append((1, 1, [(remap[v], Nw[v], tuple(UV[v])) for v in tri(a, b, c)]))
        print('  glow faces', len(sel))
    return m


def pitch_axes(A, deg):
    t = np.radians(deg)
    Rp = np.array([[np.cos(t), 0, np.sin(t)], [0, 1, 0], [-np.sin(t), 0, np.cos(t)]])
    return Rp @ A


def build(key, g):
    P, N, UV, T, hp = load_rigid(os.path.join(EX, g['mesh']), skip_materials=('rep_cockpit_fx',))
    tex = os.path.join(EX, g['tex'])
    mask = glow_texture(key, tex) if g.get('glow') else None
    material, image = 'mtl_cw_%s' % key, 'cw_%s_c.tga' % key

    load, bone = DONORS[g['donor']]
    bones = load()
    names = [b['name'] for b in bones]
    gun = bones[names.index(bone)]['offset']
    offset = np.array(gun) + np.array(g['grip'])
    # round 4: the viewmodels come from build_viewmodels.py (first-person meshes, one-handed); world models only here

    wbones = xme.read(THOMPSON_WORLD)['bones']
    m = rigid_model(P, N, UV, T, wbones, 'tag_weapon', key, material, image, AXES_WORLD, WORLD_SCALE, WORLD_OFFSET,
                    glow=mask, flash='tag_flash', hp=hp)
    out = OUT + r"\weapon_cw_%s.XMODEL_EXPORT" % key
    xme.write(out, m, 'waw-clone-wars: %s world model' % key)
    print('wrote', os.path.basename(out))


def projectile(key, mesh, scale, A=AXES):
    """Rigid model on a single tag_origin, centred, nose along +x (the direction of flight)."""
    P, N, UV, T, hp = load_rigid(os.path.join(EX, mesh))
    P = P - (P.max(0) + P.min(0)) / 2
    root = [{'name': 'tag_origin', 'parent': -1, 'offset': np.zeros(3), 'rot': np.eye(3)}]
    m = rigid_model(P, N, UV, T, root, 'tag_origin', key, 'mtl_cw_%s' % key, 'cw_%s_c.tga' % key, A, scale, (0, 0, 0))
    out = OUT + r"\weapon_cw_%s.XMODEL_EXPORT" % key
    xme.write(out, m, 'waw-clone-wars: %s projectile' % key)
    print('wrote', os.path.basename(out), 'tris', len(m['faces']))


if __name__ == '__main__':
    only = sys.argv[1:]
    for key, g in GUNS.items():
        if not only or key in only:
            build(key, g)
    if not only or 'missile' in only:
        projectile('missile', r'ui_ingame\msh\com_weap_missile.msh', 28.0)
