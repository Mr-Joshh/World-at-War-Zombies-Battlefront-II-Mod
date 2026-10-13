"""First-person SWBF2 guns as SWBF2 shows them: the clone trooper's first-person meshes (rep_1st_* / com_1st_*), held in
the right hand only, the hand under the gun, posed to match the user's Battlefront II screenshots
(screenshots/<GunName>.png in the package folder - not shipped; only `fit` / `preview` read them).

  * viewmodels: rigid on j_gun of the stock Thompson viewmodel skeleton (viewmodel_usa_thompson_smg1), the mesh origin
    (SWBF2 puts it on top of the pistol grip) just above the Thompson's right fist.  Painted lights glow (additive copy
    of the faces touching bright saturated texels); the small "cockpit fx" quads (the DC-15's red dots) are additive red.
  * animations (cw_<gun>_<anim>): the Thompson's own idle / fire / raise / drop with the left arm dropped out of view and
    the right arm + gun re-posed per gun about the wrist (POSES); aim-down-sights keeps the idle pose (SWBF2 zooms, it
    has no iron sights), reload is a dip out of view.  Same method as waw-halo3/tools/build_onehand.py.
  * poses: `build_viewmodels.py fit` solves POSES (yaw, pitch, roll, fwd, left, up) + scale from screen landmarks read
    off the screenshots, through the offline projector calibrated for WaW's view model in the Halo project
    (waw-halo3/build/calib21.py); `build_viewmodels.py preview` draws the fitted guns over the screenshots.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import msh, xme, xanim
from build_weapon import AXES
from build_thermal import skeleton_from_parts
from build_weapons import glow_texture

EX = paths.EXTRACT
B = paths.BUILD
SHOTS = os.path.join(paths.PKG, 'screenshots')
POSE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'viewmodel_poses.json')
GRIP = np.array([-1.8, 0.0, -1.4])         # mesh origin in j_gun space: top of the grip, just above the Thompson fist
CAL = (40.68372471435353, np.array([7.338916929902481, 2.932897798153283, -0.007345135130756811]))   # fov, offset

# key -> mesh, colour texture, glow, screenshot, targets (screen fractions): muzzle, rear end, [grip top]
# hands=2: the stock Thompson animations hold it (left hand under the gun), mesh placed like the round-2 DC-15
#   (grip (-2, 0, -2) from j_gun, nose-down pitch so it clears the sights in ADS); no fit, no generated animations.
# hands=1: right hand only, generated animation set, pose fitted to the screenshot (fit bounds per gun).
# grip: where the mesh origin (top of SWBF2's pistol grip) sits in j_gun space; fx: mesh parts drawn as solid additive
# lights; lens: extra glowing circle on the colour sheet (x, y, r in pixels).
GUNS = {
    'dc15':     dict(mesh=r'msh\rep\msh\rep_1st_weap_inf_rifle.msh', tex=r'rep\models\rep_1st_weap_inf_rifle.png',
                     glow=True, hands=2, scale=28.0, pitch=2.2, grip=(-2.0, 0.05, -1.4),
                     left=(0.0, 0.0, -1.3), right=(0.0, 0.0, 0.0)),
    'sniper':   dict(mesh=r'msh\rep\msh\rep_1st_weap_inf_sniperrifle.msh', tex=r'rep\models\rep_1st_weap_inf_sniperrifle.png',
                     # round 7: on the Thompson set too (no PTRS animation sources to move its hands separately);
                     # `all` moves arms + gun together to keep the PTRS-era screen position
                     glow=True, hands=2, scale=28.0, pitch=1.0, grip=(-2.0, 0.05, -1.6),
                     all=(1.5, -1.0, -1.5), left=(0.0, 0.0, -0.9), right=(0.0, 0.0, -1.2),
                     # eyepiece (recessed, renders dark when lit) and the indicator under the scope: solid red lights
                     fx_uv=[(271, 164, 18, 'redsolid'), (249, 114, 7, 'red')]),
    'emp':      dict(mesh=r'ui_ingame\msh\com_1st_weap_inf_torpedo.msh', tex=r'ui_ingame\textures\com_1st_weap_inf_torpedo.png',
                     glow=False, hands=2, scale=26.0, pitch=1.5, grip=(-2.0, 0.05, -1.0),
                     left=(-2.0, 0.7, -1.2), right=(0.0, 0.0, -1.0)),
    'pistol':   dict(mesh=r'msh\rep\msh\rep_1st_weap_inf_pistol.msh', tex=r'rep\models\rep_1st_weap_inf_pistol.png',
                     glow=True, hands=1, shot='BlasterPistol', muzzle=(0.599, 0.653), rear=(0.80, 0.91), grip_pt=(0.69, 0.86),
                     # held level and upright like the screenshot (the free fit had it turned on its side, nose up)
                     lo=(-1.5, -1, -6, -6, -16, -16, 16.0), hi=(0.5, 3, 6, 30, 8, 10, 30.0),
                     grip=(-1.8, 0.6, -0.5), straight=True),   # gun raised in the fist: the hand wraps the handle   # handle centred in the fist; barrel kept parallel to the view
    'chaingun': dict(mesh=r'msh\rep\msh\rep_1st_weap_inf_chaingun.msh', tex=r'rep\models\rep_weap_inf_chaingun.png',
                     glow=False, hands=1, shot='Chaingun', muzzle=(0.655, 0.475), rear=(1.02, 0.22), grip_pt=(0.80, 0.67),
                     grip=(-1.8, 0.0, -0.4)),
    'launcher': dict(mesh=r'msh\rep\msh\rep_1st_weap_inf_launcher.msh', tex=r'rep\models\rep_1st_weap_inf_launcher.png',
                     glow=True, hands=1, shot='RocketLauncher', muzzle=(0.70, 0.42), rear=(1.15, 0.62), grip_pt=(0.80, 0.70),
                     # fist in the middle of the handle (2.6 in under its top) instead of just under the body
                     grip=(-1.8, 0.0, 0.1), fx={'mesh_part1': 'green'}),
}
TWO_HANDED = tuple(k for k, g in GUNS.items() if g['hands'] == 2)
# the Thompson animations the two-handed guns use (zombie_thompson's file); reload / reload_empty become a dip
THOMPSON_ANIMS = ('idle', 'idle_empty', 'fire', 'lastshot', 'pullout', 'putaway', 'switch', 'pullout_fast', 'putaway_fast',
                  'pullout_empty', 'putaway_empty', 'fire_ads', 'ADS_up', 'ADS_down')
FX_COLOURS = {'red': (96, 14, 8), 'green': (6, 70, 18), 'redsolid': (105, 8, 6)}   # redsolid: opaque, unlit
# red = the painted lights' glow colour (glow texture x0.55 of the sheet's red), so the dots match the other red accents      # additive: renders far brighter than the value


def rot(yaw=0.0, pitch=0.0, roll=0.0):
    """yaw: + turns left (about z); pitch: + raises the tip (about -y); roll: + tips the top to the right (about x)."""
    y, p, r = np.radians([yaw, -pitch, roll])
    Rz = np.array([[np.cos(y), -np.sin(y), 0], [np.sin(y), np.cos(y), 0], [0, 0, 1]])
    Ry = np.array([[np.cos(p), 0, np.sin(p)], [0, 1, 0], [-np.sin(p), 0, np.cos(p)]])
    Rx = np.array([[1, 0, 0], [0, np.cos(r), -np.sin(r)], [0, np.sin(r), np.cos(r)]])
    return Rz @ Ry @ Rx


def smooth(x):
    return x * x * (3 - 2 * x)


def load_poses():
    return json.load(open(POSE_FILE)) if os.path.exists(POSE_FILE) else {}


# ---------------------------------------------------------------- mesh
def load_mesh(path):
    """World-space msh geometry with the texture name of every triangle."""
    d = msh.load(path)
    P, N, UV, T, TEX = [], [], [], [], []
    load_mesh.parts = []
    hp = {m['name'].lower(): m['world'][:3, 3] for m in d['models']}
    for m in d['models']:
        if m['hidden'] or not m['segments']:
            continue
        Mw = m['world']
        for seg in m['segments']:
            if seg['pos'] is None or not seg['tris']:
                continue
            tex = (d['materials'][seg['mat']]['tex'] or [''])[0].lower()
            base = len(P)
            P.extend(seg['pos'] @ Mw[:3, :3].T + Mw[:3, 3])
            N.extend(seg['nrm'] @ np.linalg.inv(Mw[:3, :3]) if seg['nrm'] is not None else np.zeros((len(seg['pos']), 3)))
            UV.extend(seg['uv'] if seg['uv'] is not None else np.zeros((len(seg['pos']), 2)))
            for a, b, c in seg['tris']:
                T.append((base + a, base + b, base + c))
                TEX.append(tex)
                load_mesh.parts.append(m['name'].lower())
    return np.array(P), np.array(N), np.array(UV), T, TEX, hp


def grip(key):
    return np.array(GUNS[key].get('grip', GRIP))


def axes(key):
    t = np.radians(GUNS[key].get('pitch', 0.0))
    Rp = np.array([[np.cos(t), 0, np.sin(t)], [0, 1, 0], [-np.sin(t), 0, np.cos(t)]])
    return Rp @ AXES


def gun_points(key, scale):
    """Mesh vertices in j_gun space (inches) and the landmarks: muzzle, rear end, grip top."""
    P, N, UV, T, TEX, hp = load_mesh(os.path.join(EX, GUNS[key]['mesh']))
    GRIP = grip(key)
    V = (P @ axes(key).T) * scale + GRIP
    x0, x1 = V[:, 0].min(), V[:, 0].max()
    muzzle = (axes(key) @ hp['hp_fire']) * scale + GRIP if 'hp_fire' in hp else V[V[:, 0] > x1 - 0.04 * (x1 - x0)].mean(0)
    rear = V[V[:, 0] < x0 + 0.06 * (x1 - x0)].mean(0)
    return V, np.array([muzzle, rear, GRIP])


def build_model(key, scale):
    from build_weapons import faces_on_mask
    g = GUNS[key]
    P, N, UV, T, TEX, hp = load_mesh(os.path.join(EX, g['mesh']))
    PART = load_mesh.parts
    GRIP = grip(key)
    A = axes(key)
    V = (P @ A.T) * scale + GRIP
    Nw = N @ A.T
    # the sniper keeps the PTRS skeleton + animations it had in round 2 (two hands, rifle level); the rest the Thompson's
    bones = skeleton_from_parts({'ptrs': 'viewmodel_rus_PTRS1'}.get(g.get('donor'), 'viewmodel_usa_thompson_smg1'))
    names = [b['name'] for b in bones]
    bi = names.index('j_gun')
    if 'hp_fire' in hp and 'tag_flash' in names:
        bones[names.index('tag_flash')]['offset'] = (A @ hp['hp_fire']) * scale + GRIP
    m = {'bones': bones, 'verts': [(p, [(bi, 1.0)]) for p in V], 'faces': [], 'objects': [key, key + '_glow', key + '_fx'],
         'materials': [('mtl_cw_%s' % key, 'Phong', 'cw_%s_c.tga' % key)]}
    fxmap = dict(g.get('fx', {}))
    lights = {}
    tw, th = Image.open(os.path.join(EX, g['tex'])).size
    uvlit = set()
    for i, t in enumerate(TEX):
        colour = 'red' if 'cockpit_fx' in t else fxmap.get(PART[i])
        if not colour:
            uv = UV[list(T[i])]
            xs, ys = (uv[:, 0] % 1.0) * tw, ((-uv[:, 1]) % 1.0) * th
            for cx, cy, r, c in g.get('fx_uv', ()):
                # every corner inside the circle (a big face that merely crosses it is not part of the light)
                if (((xs - cx) ** 2 + (ys - cy) ** 2) <= (r * 1.15) ** 2).all():
                    colour = c
                    uvlit.add(i)
        if colour:
            lights.setdefault(colour, []).append(i)
    lit = set(i for v in lights.values() for i in v)
    body = [i for i in range(len(T)) if i not in lit]
    for i in body:
        a, b, c = T[i]
        m['faces'].append((0, 0, [(v, Nw[v], tuple(UV[v])) for v in (a, c, b)]))

    def overlay(sel, mat_index, obj, grow=1.0, lift=0.015):
        remap = {}
        centre = {}
        if grow != 1.0:
            # each light part grows about its own centre (the SWBF2 lights are tiny at WaW's view distance)
            byp = {}
            for i in sel:
                byp.setdefault(PART[i], set()).update(T[i])
            for part, vs in byp.items():
                c = V[list(vs)].mean(0)
                for v in vs:
                    centre[v] = c
        for i in sel:
            for v in T[i]:
                if v not in remap:
                    remap[v] = len(m['verts'])
                    n = Nw[v] / (np.linalg.norm(Nw[v]) or 1.0)
                    p = V[v] if v not in centre else centre[v] + (V[v] - centre[v]) * grow
                    m['verts'].append((p + n * lift, [(bi, 1.0)]))
        for i in sel:
            a, b, c = T[i]
            m['faces'].append((obj, mat_index, [(remap[v], Nw[v], tuple(UV[v])) for v in (a, c, b)]))

    if g['glow']:
        mask = glow_texture(key, os.path.join(EX, g['tex']), g.get('lens'))
        sel = faces_on_mask(UV, [T[i] for i in body], mask)
        m['materials'].append(('mtl_cw_%s_glow' % key, 'Phong', 'cw_%s_glow_c.tga' % key))
        overlay([body[i] for i in sel], len(m['materials']) - 1, 1)
    for colour, sel in sorted(lights.items()):
        m['materials'].append(('mtl_cw_fx_%s' % colour, 'Phong', 'cw_fx_%s_c.tga' % colour))
        # the solid light replaces the textured face: drawn on the body surface, slightly bigger
        # whole-part lights (cockpit fx quads, the launcher lens) grow about their part; texture-located ones stay put
        parts_sel = [i for i in sel if i not in uvlit]
        uv_sel = [i for i in sel if i in uvlit]
        if parts_sel:
            overlay(parts_sel, len(m['materials']) - 1, 2, grow=0.55 if colour == 'red' else 1.3, lift=0.18)
        if uv_sel:
            overlay(uv_sel, len(m['materials']) - 1, 2, grow=1.0, lift=0.02)
    out = os.path.join(B, 'model_export', 'viewmodel_cw_%s.XMODEL_EXPORT' % key)
    xme.write(out, m, 'waw-clone-wars: %s first-person mesh, %s-handed (scale %.1f)' % (key, 'two' if g['hands'] == 2 else 'one', scale))
    print('wrote', os.path.basename(out), 'tris', len(m['faces']), 'lights', {k: len(v) for k, v in lights.items()})


def fx_texture():
    os.makedirs(os.path.join(B, 'textures'), exist_ok=True)
    for colour, rgb in FX_COLOURS.items():
        Image.new('RGB', (8, 8), rgb).save(os.path.join(B, 'textures', 'cw_fx_%s.png' % colour))


# ---------------------------------------------------------------- animation
def groups(a):
    left = [i for i, p in enumerate(a['parts']) if p.upper().endswith('_LE') or '_LE_' in p.upper()]
    fixed = [i for i, p in enumerate(a['parts']) if p.lower() in ('tag_torso', 'tag_cambone', 'tag_camera', 'tag_gasmask')]
    right = [i for i in range(len(a['parts'])) if i not in left and i not in fixed]
    return left, right


def repose(a, R, t):
    ix = xanim.index(a)
    left, right = groups(a)
    frames = []
    for fr in a['frames']:
        wrist = fr[ix['j_wrist_ri']][0]
        fr = xanim.rigid(fr, np.eye(3), np.zeros(3), (-12, 6, -40), only=left)      # left arm out of view
        fr = xanim.rigid(fr, R, wrist, t, only=right)
        frames.append(fr)
    if len(frames) == 1:
        frames = frames * 2
    return {'parts': a['parts'], 'fps': a['fps'], 'frames': frames}


def dip(idle, nframes=30):
    """Reload: the gun dips out of view and comes back (no magazine to swap on a blaster)."""
    ix = xanim.index(idle)
    left, right = groups(idle)
    base = idle['frames'][0]
    pivot = base[ix['j_elbow_ri']][0].copy()
    keys = [(0, 0, (0, 0, 0)), (8, -34, (-3, 0, -10)), (20, -34, (-3, 0, -10)), (nframes - 1, 0, (0, 0, 0))]
    frames = []
    for f in range(nframes):
        k1 = next(i for i in range(1, len(keys)) if keys[i][0] >= f)
        a, b = keys[k1 - 1], keys[k1]
        u = smooth((f - a[0]) / float(b[0] - a[0]))
        frames.append(xanim.rigid(base, rot(0, a[1] + (b[1] - a[1]) * u, 0), pivot,
                                  np.array(a[2]) + (np.array(b[2]) - np.array(a[2])) * u, only=right))
    return {'parts': idle['parts'], 'fps': 30, 'frames': frames}


def kick(idle, pitch, back, up=0.5, nframes=10):
    """Heavy recoil (launchers, shotgun): the muzzle snaps up about the wrist and eases back."""
    ix = xanim.index(idle)
    left, right = groups(idle)
    base = idle['frames'][0]
    pivot = base[ix['j_wrist_ri']][0].copy()
    frames = []
    for f in range(nframes):
        u = f / 2.0 if f <= 2 else 1.0 - smooth((f - 2) / float(nframes - 3))
        u = min(1.0, max(0.0, u))
        frames.append(xanim.rigid(base, rot(0, pitch * u, 0), pivot, (-back * u, 0, up * u), only=right))
    return {'parts': idle['parts'], 'fps': 30, 'frames': frames}


KICKS = {'launcher': (10, 3.0), 'emp': (8, 2.5), 'sniper': (6, 2.0)}


def anims(key, pose):
    R, t = rot(*pose[:3]), tuple(pose[3:6])
    src = lambda n: xanim.read(xanim.find(n))
    idle = repose(src('thompson_idle'), R, t)
    out = {'idle': idle, 'ads': idle, 'reload': dip(idle)}
    for name, s in (('fire', 'thompson_fire'), ('raise', 'thompson_pullout'), ('drop', 'thompson_putaway'),
                    ('raise_fast', 'thompson_pullout_fast'), ('drop_fast', 'thompson_putaway_fast')):
        out[name] = repose(src(s), R, t)
    if key in KICKS:
        out['fire'] = kick(idle, *KICKS[key])
    d = os.path.join(B, 'xanim_export')
    os.makedirs(d, exist_ok=True)
    names = []
    for name, a in out.items():
        n = 'cw_%s_%s' % (key, name)
        xanim.write(os.path.join(d, n + '.XANIM_EXPORT'), a)
        names.append(n)
    return names


def groups3(a):
    """left arm / right arm / gun + tags (the camera tags stay put)"""
    left, right = groups(a)
    fixed = [i for i, p in enumerate(a['parts']) if p.lower() in ('tag_torso', 'tag_cambone', 'tag_camera', 'tag_gasmask')]
    rarm = [i for i, p in enumerate(a['parts']) if '_RI' in p.upper() and i not in fixed]
    gun = [i for i in right if i not in rarm]
    return left, rarm, gun


def shift_hands(a, g):
    """Thompson animation with the left / right arm moved relative to the gun, and everything by `all`."""
    left, rarm, gun = groups3(a)
    moving = left + rarm + gun
    I = np.eye(3)
    frames = []
    for fr in a['frames']:
        fr = xanim.rigid(fr, I, np.zeros(3), g.get('left', (0, 0, 0)), only=left)
        fr = xanim.rigid(fr, I, np.zeros(3), g.get('right', (0, 0, 0)), only=rarm)
        fr = xanim.rigid(fr, I, np.zeros(3), g.get('all', (0, 0, 0)), only=moving)
        frames.append(fr)
    if len(frames) == 1:
        frames = frames * 2
    return {'parts': a['parts'], 'fps': a['fps'], 'frames': frames}


def dip_all(idle, nframes=30):
    """Reload with both hands: the whole gun dips out of view (about the right elbow) and comes back."""
    ix = xanim.index(idle)
    left, rarm, gun = groups3(idle)
    moving = left + rarm + gun
    base = idle['frames'][0]
    pivot = base[ix['j_elbow_ri']][0].copy()
    keys = [(0, 0, (0, 0, 0)), (8, -34, (-3, 0, -12)), (20, -34, (-3, 0, -12)), (nframes - 1, 0, (0, 0, 0))]
    frames = []
    for f in range(nframes):
        k1 = next(i for i in range(1, len(keys)) if keys[i][0] >= f)
        a, b = keys[k1 - 1], keys[k1]
        u = smooth((f - a[0]) / float(b[0] - a[0]))
        frames.append(xanim.rigid(base, rot(0, a[1] + (b[1] - a[1]) * u, 0), pivot,
                                  np.array(a[2]) + (np.array(b[2]) - np.array(a[2])) * u, only=moving))
    return {'parts': idle['parts'], 'fps': 30, 'frames': frames}


def anims_two(key):
    g = GUNS[key]
    d = os.path.join(B, 'xanim_export')
    os.makedirs(d, exist_ok=True)
    names = []
    idle = None
    for n in THOMPSON_ANIMS:
        a = shift_hands(xanim.read(xanim.find('thompson_' + n)), g)
        if n == 'idle':
            idle = a
        name = 'cw_%s_t_%s' % (key, n.lower())
        xanim.write(os.path.join(d, name + '.XANIM_EXPORT'), a)
        names.append(name)
    name = 'cw_%s_t_reload' % key
    xanim.write(os.path.join(d, name + '.XANIM_EXPORT'), dip_all(idle))
    names.append(name)
    return names


# ---------------------------------------------------------------- projector / fit
_BASE = None


def jgun(pose):
    global _BASE
    if _BASE is None:
        _BASE = xanim.read(xanim.find('thompson_idle'))
    ix = xanim.index(_BASE)
    fr = _BASE['frames'][0]
    fr = xanim.rigid(fr, rot(*pose[:3]), fr[ix['j_wrist_ri']][0], tuple(pose[3:6]))
    return fr[ix['j_gun']]


def screen(world):
    world = world + CAL[1]
    tv = math.tan(math.radians(CAL[0] / 2)) * 0.75
    th = tv * 16 / 9.0
    x = world[:, 0]
    return np.stack([0.5 - (world[:, 1] / x) / th * 0.5, 0.5 - (world[:, 2] / x) / tv * 0.5], 1), x


def project(key, p):
    pos, R = jgun(p[:6])
    V, L = gun_points(key, p[6])
    return screen(pos + V @ R), screen(pos + L @ R)


def fit(key):
    g = GUNS[key]
    tgt = np.array([g['muzzle'], g['rear'], g['grip_pt']])
    pts = {22: gun_points(key, 22)[1]}
    GRIP = grip(key)

    def cost(p):
        pos, R = jgun(p[:6])
        s = p[6]
        # landmarks scale linearly about GRIP
        L = (pts[22] - GRIP) * (s / 22.0) + GRIP
        sc, x = screen(pos + L @ R)
        if (x < 4).any():
            return 1e9
        w = np.array([3.0, 1.0, 1.5])
        c = float((((sc - tgt) ** 2).sum(1) * w).sum())
        if g.get('straight'):
            d = R[0] / np.linalg.norm(R[0])          # barrel direction in camera space: no sideways lean
            c += 0.05 * (d[1] / max(d[0], 0.1)) ** 2
        return c

    rng = np.random.RandomState(1)
    lo = np.array(g.get('lo', (-45, -30, -40, -6, -16, -16, 16.0)))
    hi = np.array(g.get('hi', (45, 30, 40, 30, 8, 10, 36.0)))
    best = None
    for _ in range(6000):
        p = lo + rng.rand(7) * (hi - lo)
        c = cost(p)
        if best is None or c < best[0]:
            best = (c, p)
    c, p = best
    step = (hi - lo) * 0.1
    for it in range(6000):
        q = np.clip(p + rng.randn(7) * step, lo, hi)
        cq = cost(q)
        if cq < c:
            c, p = cq, q
        if it % 1500 == 1499:
            step *= 0.4
    print('%-9s cost %.5f pose %s' % (key, c, [round(float(v), 1) for v in p]))
    return [round(float(v), 2) for v in p]


def preview(key, p, out):
    g = GUNS[key]
    im = Image.open(os.path.join(SHOTS, g['shot'] + '.png')).convert('RGB').resize((960, 540))
    S, Lm = project(key, p)
    S = S[0] * np.array([960, 540])
    P, N, UV, T, TEX, hp = load_mesh(os.path.join(EX, g['mesh']))
    ov = Image.new('RGBA', im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for t in T:
        d.polygon([tuple(S[v]) for v in t], fill=(255, 40, 200, 40))
    im = Image.alpha_composite(im.convert('RGBA'), ov).convert('RGB')
    d = ImageDraw.Draw(im)
    for (x, y), c in zip(Lm[0] * np.array([960, 540]), ((0, 255, 0), (0, 160, 255), (255, 255, 0))):
        d.ellipse([x - 5, y - 5, x + 5, y + 5], outline=c, width=2)
    for (x, y) in np.array([g['muzzle'], g['rear'], g['grip_pt']]) * np.array([960, 540]):
        d.rectangle([x - 4, y - 4, x + 4, y + 4], outline=(255, 0, 0), width=2)
    im.save(out)


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'build'
    only = sys.argv[2:]
    keys = [k for k in GUNS if not only or k in only]
    poses = load_poses()
    for k in TWO_HANDED:
        poses.pop(k, None)
    if cmd == 'fit':
        keys = [k for k in keys if k not in TWO_HANDED]
        for k in keys:
            poses[k] = fit(k)
        json.dump(poses, open(POSE_FILE, 'w'), indent=1)
    if cmd in ('fit', 'preview'):
        for k in [k for k in keys if k not in TWO_HANDED]:
            preview(k, poses[k], os.path.join(B, 'preview', 'vm_fit_%s.png' % k))
    if cmd == 'build':
        fx_texture()
        names = []
        for k in keys:
            if k in TWO_HANDED:
                build_model(k, GUNS[k]['scale'])
                names += anims_two(k)
                continue
            p = poses[k]
            build_model(k, p[6])
            names += anims(k, p)
        prev = json.load(open(os.path.join(B, 'xanim_export', 'cw_anims.json'))) if os.path.exists(os.path.join(B, 'xanim_export', 'cw_anims.json')) else []
        json.dump(sorted(set(prev + names)), open(os.path.join(B, 'xanim_export', 'cw_anims.json'), 'w'))
        print('anims:', len(names))
