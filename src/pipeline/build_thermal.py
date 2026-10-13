"""Thermal detonator: SWBF2 detonator meshes as the zombie-mode grenade.

Viewmodel is bound to the stock Mk2 frag grenade viewmodel skeleton (so the Mk2 pull-pin/throw
animations drive it); the world/projectile model is a plain rigid model.  Also writes the weapon
files that replace the two stock zombie grenades and the HUD icon texture.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import sys, os
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xme, xparts, wpn
from build_weapon import load_rigid, AXES

GAME = paths.WAW
RAW = GAME + r"\raw"
UI = os.path.join(paths.EXTRACT, 'ui_ingame')
OUT = paths.BUILD
MOD = paths.MOD
SCALE = 28.0     # inches per metre -> ~1.6 in radius, a little larger than the Mk2 it replaces


def skeleton_from_parts(name):
    ver, bones = xparts.read(os.path.join(RAW, 'xmodelparts', name))
    xparts.world(bones)
    return [{'name': b['name'], 'parent': b['parent'], 'offset': b['woff'], 'rot': b['wrot']} for b in bones]


GLOW_SHELLS = tuple(1.06 + 0.84 * (i / 7.0) ** 1.3 for i in range(8))     # shell radii, in ball radii
GLOW_RGB = (20, 2, 1)                               # additive colour of ONE shell; they stack toward the ball


def add_glow(m, bone_index, radius):
    """Red halo as part of the model itself: nested additive spheres drawn inside-out (front faces culled).
    Only the far side of each shell renders, and the ball hides the part behind it, so what is left is a
    soft ring of light around the silhouette from every angle - nothing is drawn over the ball itself."""
    m['objects'].append('glow')
    m['materials'].append(('mtl_cw_thermal_glow', 'Phong', 'cw_thermal_glow_c.tga'))
    seg, rings = 16, 10
    for k in GLOW_SHELLS:
        R = radius * k
        base = len(m['verts'])
        for i in range(rings + 1):
            th = np.pi * i / rings
            for j in range(seg):
                ph = 2 * np.pi * j / seg
                m['verts'].append((np.array([np.sin(th) * np.cos(ph), np.sin(th) * np.sin(ph), np.cos(th)]) * R, [(bone_index, 1.0)]))

        def corner(i, j):
            v = base + i * seg + (j % seg)
            n = m['verts'][v][0] / R
            return (v, n, (0.5, 0.5))

        for i in range(rings):
            for j in range(seg):
                a, b2, c, d = corner(i, j), corner(i, j + 1), corner(i + 1, j + 1), corner(i + 1, j)
                # clockwise seen from outside = front face in XMODEL_EXPORT
                if i > 0:
                    m['faces'].append((1, 1, [a, b2, c]))
                if i < rings - 1:
                    m['faces'].append((1, 1, [a, c, d]))


def glow_texture():
    """Flat dim red for additive blending; the falloff comes from the shells stacking."""
    os.makedirs(os.path.join(OUT, 'textures'), exist_ok=True)
    Image.new('RGB', (8, 8), GLOW_RGB).save(os.path.join(OUT, 'textures', 'cw_thermal_glow.png'))
    print('texture: cw_thermal_glow.png')


def model(src, out, bones, bone_index, material, image, recenter):
    P, N, UV, T, hp = load_rigid(src)
    if recenter:
        P = P - (P.max(0) + P.min(0)) / 2
    Pw = (P @ AXES.T) * SCALE
    Nw = N @ AXES.T
    verts = [(p, [(bone_index, 1.0)]) for p in Pw]
    faces = [(0, 0, [(v, Nw[v], tuple(UV[v])) for v in (a, c, b)]) for a, b, c in T]   # CCW -> CW
    m = {'bones': bones, 'verts': verts, 'faces': faces, 'objects': ['thermal'], 'materials': [(material, 'Phong', image)]}
    add_glow(m, bone_index, float(np.linalg.norm(Pw, axis=1).max()))
    xme.write(out, m, 'waw-clone-wars: thermal detonator from %s' % os.path.basename(src))
    print('wrote', os.path.basename(out), 'verts', len(verts), 'tris', len(faces), 'radius %.2f' % np.linalg.norm(Pw, axis=1).max(),
          'cw', round(1 - xme.winding_agreement(m), 2))


def models():
    view_bones = skeleton_from_parts('viewmodel_usa_mk2_grenade1')
    for b in view_bones:                 # the in-hand glow plays on tag_flash: put it at the ball's centre
        if b['name'] == 'tag_flash':
            b['offset'] = np.zeros(3)
    model(UI + r"\msh\com_1st_weap_inf_grenadethermal.msh", OUT + r"\model_export\viewmodel_cw_thermal.XMODEL_EXPORT",
          view_bones, 0, 'mtl_cw_thermal_view', 'cw_thermal_view_c.tga', recenter=True)
    root = [{'name': 'tag_origin', 'parent': -1, 'offset': np.zeros(3), 'rot': np.eye(3)}]
    model(UI + r"\msh\com_weap_inf_grenadethermal.msh", OUT + r"\model_export\weapon_cw_thermal.XMODEL_EXPORT",
          root, 0, 'mtl_cw_thermal', 'cw_thermal_c.tga', recenter=True)


def icon():
    """SWBF2's HUD icon sits on black for additive blending; give it a real alpha channel."""
    im = Image.open(UI + r"\textures\hud_thermaldetonator.png").convert('RGB').resize((128, 128), Image.LANCZOS)
    a = np.asarray(im, float)
    # the picture has a grey backdrop, so cut the ball out with a soft disc instead of keying on brightness
    yy, xx = np.mgrid[0:128, 0:128]
    r = np.hypot(xx - 63.5, yy - 65.0)
    alpha = np.clip((59.0 - r) / 2.5, 0, 1) * 255
    ball = Image.fromarray(np.dstack([a, alpha]).astype('uint8'), 'RGBA')
    # the HUD's offhand slot is narrower than it is tall (about 0.73:1); pre-squash vertically so the ball stays round
    out = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
    h = int(128 * 0.73)
    out.alpha_composite(ball.resize((128, h), Image.LANCZOS), (0, (128 - h) // 2))
    os.makedirs(OUT + r"\textures", exist_ok=True)
    out.save(OUT + r"\textures\cw_hud_thermal.png")
    print('icon: cw_hud_thermal.png')


def glow_fx():
    """Red glow that follows the detonator: the stock red light-glow effect, centred and sized for a grenade."""
    src = open(os.path.join(RAW, 'fx', 'maps', 'zombie', 'fx_zombie_light_glow_red.efx'), errors='replace').read()
    for name, scale in (('fx_cw_thermal_glow', 0.45),):
        out = []
        for line in src.splitlines():
            t = line.strip()
            if t.startswith('spawnOrgX'):
                line = chr(9) + 'spawnOrgX 0 0;'
            elif t.split(' ')[0] in ('sizeGraph0', 'sizeGraph1'):
                k, v = t.split()[:2]
                line = chr(9) + '%s %g' % (k, float(v) * scale)
            out.append(line)
        p = os.path.join(MOD, 'fx', 'misc', name + '.efx')
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'w', newline=chr(13) + chr(10)) as f:
            f.write(chr(10).join(out))
    print('fx: thermal glow (in flight)')


def pristine(name):
    """Stock weapon file, even while a previous build's override is sitting in raw/."""
    p = os.path.join(RAW, 'weapons', 'sp', name)
    return p + '.cw-orig' if os.path.exists(p + '.cw-orig') else p


def weapons():
    """Replace both stock zombie grenades in place (the scripts name them in ~70 places)."""
    h, frag = wpn.read(pristine('fraggrenade'))
    anim_keys = [k for k in frag if k.endswith('Anim')]
    for name in ('stielhandgranate', 'fraggrenade'):
        header, k = wpn.read(pristine(name))
        for a in anim_keys:                       # Mk2 animations fit a round grenade; the stick grenade's do not
            k[a] = frag[a]
        k.update({
            'displayName': 'CLONEWARS_THERMAL',
            'gunModel': 'viewmodel_cw_thermal',
            'worldModel': 'weapon_cw_thermal',
            'projectileModel': 'weapon_cw_thermal',
            'hudIcon': 'cw_hud_thermal', 'hudIconRatio': '1:1',
            # red glow: follows the thrown detonator, and sits on tag_flash while it is held
            'projTrailEffect': 'misc/fx_cw_thermal_glow',
            'altRaiseTime': frag.get('altRaiseTime', k.get('altRaiseTime', '1')),
        })
        out = os.path.join(MOD, 'weapons', 'sp', name)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        wpn.write(out, header, k)
        print('weapon override:', name)


if __name__ == '__main__':
    models(); icon(); glow_texture(); glow_fx(); weapons()
