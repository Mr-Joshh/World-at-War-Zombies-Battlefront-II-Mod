"""SWBF2 land mine: the second grenade type (key 3 switches between it and the thermal detonator).

Viewmodel bound to the Mk2 grenade skeleton (thrown with the Mk2 animations like the detonator), one rigid
model for the world / projectile / planted mine (lying flat, base at the origin, red lamp glowing), the HUD
icon cut from the mine's own top-down texture, and the weapon file cw_mine.  The planting and the
proximity trigger are scripted (maps/_cw.gsc mine_*).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import sys, os
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xme, wpn
from build_weapon import load_rigid, AXES, AXES_WORLD
from build_thermal import skeleton_from_parts, pristine
from build_weapons import rigid_model, glow_texture

UI = os.path.join(paths.EXTRACT, 'ui_ingame')
B = paths.BUILD
MOD = paths.MOD
SCALE = 28.0
TEX = UI + r"\textures\com_weap_inf_landmine.png"


def add_halo(m, bone_index, centre, radius, flat, count=16):
    """Red halo like the thermal detonator's (build_thermal.add_glow): nested additive shells drawn inside-out, here
    squashed to the mine's flat shape (z x flat) and centred on it."""
    # twice the thermal's shells at half the brightness each: on the floor every shell meets the ground in a ring,
    # and fewer, brighter shells showed as visible bands
    GLOW_SHELLS = tuple(1.04 + 0.86 * (i / (count - 1.0)) ** 1.3 for i in range(count))
    m['objects'].append('halo')
    m['materials'].append(('mtl_cw_mine_halo', 'Phong', 'cw_mine_halo_c.tga'))
    obj, mat = len(m['objects']) - 1, len(m['materials']) - 1
    seg, rings = 16, 10
    for k in GLOW_SHELLS:
        R = radius * k
        base = len(m['verts'])
        for i in range(rings + 1):
            th = np.pi * i / rings
            for j in range(seg):
                ph = 2 * np.pi * j / seg
                u = np.array([np.sin(th) * np.cos(ph), np.sin(th) * np.sin(ph), np.cos(th)])
                m['verts'].append((centre + u * R * np.array([1, 1, flat]), [(bone_index, 1.0)]))

        def corner(i, j):
            v = base + i * seg + (j % seg)
            n = (m['verts'][v][0] - centre) / R
            return (v, n / (np.linalg.norm(n) or 1), (0.5, 0.5))

        for i in range(rings):
            for j in range(seg):
                a, b2, c, d = corner(i, j), corner(i, j + 1), corner(i + 1, j + 1), corner(i + 1, j)
                if i > 0:
                    m['faces'].append((obj, mat, [a, b2, c]))
                if i < rings - 1:
                    m['faces'].append((obj, mat, [a, c, d]))


def halo_texture():
    Image.new('RGB', (8, 8), (10, 1, 1)).save(os.path.join(B, 'textures', 'cw_mine_halo.png'))


def models():
    mask = glow_texture('mine', TEX)
    # in the hand: the first-person mesh, centred on the Mk2's gun bone
    P, N, UV, T, hp = load_rigid(UI + r"\msh\com_1st_weap_inf_landmine.msh")
    P = P - (P.max(0) + P.min(0)) / 2
    bones = skeleton_from_parts('viewmodel_usa_mk2_grenade1')
    m = rigid_model(P, N, UV, T, bones, bones[0]['name'], 'mine', 'mtl_cw_mine', 'cw_mine_c.tga', AXES, 22.0, (0, 0, 0), glow=mask)
    V = np.array([v[0] for v in m['verts']])
    add_halo(m, 0, (V.max(0) + V.min(0)) / 2, float(np.abs(V - (V.max(0) + V.min(0)) / 2).max()) * 0.8, 1.0, count=8)
    xme.write(B + r"\model_export\viewmodel_cw_mine.XMODEL_EXPORT", m, 'waw-clone-wars: land mine viewmodel')
    # thrown / planted: flat, base on the origin
    P, N, UV, T, hp = load_rigid(UI + r"\msh\com_weap_inf_landmine_placed.msh")
    P = P - np.array([(P[:, 0].max() + P[:, 0].min()) / 2, P[:, 1].min(), (P[:, 2].max() + P[:, 2].min()) / 2])
    root = [{'name': 'tag_origin', 'parent': -1, 'offset': np.zeros(3), 'rot': np.eye(3)}]
    m = rigid_model(P, N, UV, T, root, 'tag_origin', 'mine', 'mtl_cw_mine', 'cw_mine_c.tga', AXES_WORLD, SCALE, (0, 0, 0), glow=mask)
    V = np.array([v[0] for v in m['verts']])
    add_halo(m, 0, np.array([0, 0, V[:, 2].max() * 0.4]), float(np.abs(V[:, :2]).max()), 0.35)
    xme.write(B + r"\model_export\weapon_cw_mine.XMODEL_EXPORT", m, 'waw-clone-wars: land mine (planted)')
    Pw = np.array([v[0] for v in m['verts']])
    print('mine models: planted bbox', Pw.min(0).round(1), Pw.max(0).round(1))


def icon():
    """The texture is the mine seen from above: cut out the octagon."""
    im = Image.open(TEX).convert('RGB').resize((128, 128), Image.LANCZOS)
    mask = Image.new('L', (128 * 4, 128 * 4), 0)
    c, r = 64 * 4, 62 * 4
    pts = [(c + r * np.cos(np.radians(22.5 + 45 * k)), c + r * np.sin(np.radians(22.5 + 45 * k))) for k in range(8)]
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    mask = mask.resize((128, 128), Image.LANCZOS)
    mine = im.convert('RGBA')
    mine.putalpha(mask)
    # the HUD's offhand slot is about 0.73:1 (see the thermal icon): pre-squash so the mine stays round
    out = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
    h = int(128 * 0.73)
    out.alpha_composite(mine.resize((128, h), Image.LANCZOS), (0, (128 - h) // 2))
    out.save(B + r"\textures\cw_hud_mine.png")
    print('icon: cw_hud_mine.png')


def weapon():
    """Thrown like the thermal detonator (stick grenade file, Mk2 animations) but lobbed short and never
    timed out by the engine: the script plants it where it comes to rest."""
    h, frag = wpn.read(pristine('fraggrenade'))
    header, k = wpn.read(pristine('stielhandgranate'))
    for a in [x for x in frag if x.endswith('Anim')]:
        k[a] = frag[a]
    k.update({
        'displayName': 'CLONEWARS_MINE',
        'ammoName': 'cw_mine', 'clipName': 'cw_mine',
        'gunModel': 'viewmodel_cw_mine',
        'worldModel': 'weapon_cw_mine',
        'projectileModel': 'weapon_cw_mine',
        'hudIcon': 'cw_hud_mine', 'hudIconRatio': '1:1',
        'maxAmmo': '4', 'startAmmo': '4', 'clipSize': '4',
        'fuseTime': '60',
        'cookOffHold': '0', 'sharedAmmoCapName': 'cw_mine',
        'projectileSpeed': '220', 'projectileSpeedUp': '60',
        'altRaiseTime': frag.get('altRaiseTime', k.get('altRaiseTime', '1')),
    })
    out = os.path.join(MOD, 'weapons', 'sp', 'cw_mine')
    wpn.write(out, header, k)
    print('weapon: cw_mine (fuse %s, speed %s)' % (k['fuseTime'], k['projectileSpeed']))


if __name__ == '__main__':
    halo_texture(); models(); icon(); weapon()
