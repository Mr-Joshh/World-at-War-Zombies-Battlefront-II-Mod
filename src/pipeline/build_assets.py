"""Stage every clonewars texture/model into the mod-tools tree, write the GDT and run the converter."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import assets as A

EX = paths.EXTRACT
B = paths.BUILD
M = B + r"\model_export"
UI = EX + r"/ui_ingame/textures"
CIS = EX + r"/cis/models"
REP = EX + r"/rep/models"
ADD = dict(mtype='model unlit', blendFunc='Add', depthWrite='Off')


def silver(im):
    """SWBF2's first-person detonator texture is near-black (it relied on specular); lift it to a readable silver."""
    from PIL import ImageOps, ImageEnhance
    g = ImageOps.autocontrast(im.convert('L'), cutoff=1)
    return ImageEnhance.Brightness(g.point(lambda v: int(70 + v * 0.70))).enhance(1.0).convert('RGB')


def brighter(im):
    """SWBF2's gun textures are painted for its specular lighting and read as black shapes in WaW."""
    from PIL import ImageEnhance
    return ImageEnhance.Brightness(im.convert('RGB')).enhance(1.6)


def no_red(im):
    """The clone trooper's sniper rifle is black / grey: the sheet's red-brown wood parts are turned to grey.  The scope's
    eyepiece (a circle at 265,162 on the 512x256 sheet) and the small indicator light under the scope stay red - the lens
    a deeper red than painted."""
    import numpy as np
    from PIL import Image
    a = np.asarray(brighter(im), float)
    grey = a.mean(2, keepdims=True)
    red = ((a[..., 0] > a[..., 1] * 1.25) & (a[..., 0] > a[..., 2] * 1.25))
    yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    lens = (xx - 265) ** 2 + (yy - 162) ** 2 <= 17 ** 2
    led = (abs(xx - 249) <= 4) & (abs(yy - 114) <= 4)
    out = np.where((red & ~lens & ~led)[..., None], grey * 0.8, a)
    out[lens] = out[lens] * np.array([1.25, 0.45, 0.45])
    return Image.fromarray(out.clip(0, 255).astype('uint8'))


def rgb(im):
    return im.convert('RGB')


images = []


def mat(name, src, image, transform=None, **kw):
    A.material(name, A.texture(src, image, transform=transform), **kw)
    images.append(image)


# characters
mat('mtl_cw_bdroid', CIS + r"/cis_inf_battledroid.png", 'cw_bdroid_c')
for key, colour in (('eng', 'orange'), ('assault', 'red'), ('assassin', 'camo')):
    mat('mtl_cw_bdroid_' + key, CIS + r"/cis_inf_battledroid_%s.png" % colour, 'cw_bdroid_%s_c' % key)
mat('mtl_cw_sbdroid', CIS + r"/cis_inf_sbdroid.png", 'cw_sbdroid_c')
mat('mtl_cw_clone', REP + r"/rep_inf_ep3trooper.png", 'cw_clone_c')
mat('mtl_cw_clone_gauntlet', EX + r"\msh\reptroop\textures\rep_1st_inf_clonetrooper_arms.tga", 'cw_clone_gauntlet_c', rgb)
mat('mtl_cw_clone_sleeve', B + r"\textures\cw_clone_sleeve_c.png", 'cw_clone_sleeve_c')
mat('mtl_cw_clone_glove', B + r"\textures\cw_clone_glove_c.png", 'cw_clone_glove_c')

# guns (build_weapons.py): colour map + additive copy of the painted lights
GUNS = {'dc15': REP + r"/rep_1st_weap_inf_rifle.png", 'chaingun': REP + r"/rep_weap_inf_chaingun.png",
        'pistol': REP + r"/rep_1st_weap_inf_pistol.png", 'sniper': REP + r"/rep_1st_weap_inf_sniperrifle.png",
        'launcher': REP + r"/rep_1st_weap_inf_launcher.png", 'emp': UI + r"/com_1st_weap_inf_torpedo.png",
        'missile': UI + r"/missile.png", 'mine': UI + r"/com_weap_inf_landmine.png"}
GLOW = ('dc15', 'pistol', 'launcher', 'mine', 'sniper')
for key, src in GUNS.items():
    mat('mtl_cw_' + key, src, 'cw_%s_c' % key, None if key == 'mine' else no_red if key == 'sniper' else brighter)
    if key in GLOW:
        mat('mtl_cw_%s_glow' % key, B + r"\textures\cw_%s_glow.png" % key, 'cw_%s_glow_c' % key, **ADD)

# HUD: Battlefront II reticle (build_reticle.py), grenade icons, sniper scope frame
for name in ('cw_reticle', 'cw_hud_thermal', 'cw_hud_mine'):
    mat(name, B + r"/textures/%s.png" % name, name, mtype='2d', blendFunc='Blend')
mat('cw_scope_clear', B + r"/textures/cw_scope_clear.png", 'cw_scope_clear', mtype='2d', blendFunc='Blend')
# SWBF2 indicator lights on the first-person guns (build_viewmodels.py)
mat('mtl_cw_fx_red', B + r"/textures/cw_fx_red.png", 'cw_fx_red_c', cullFace='None', **ADD)
mat('mtl_cw_fx_green', B + r"/textures/cw_fx_green.png", 'cw_fx_green_c', cullFace='None', **ADD)
mat('mtl_cw_fx_redsolid', B + r"/textures/cw_fx_redsolid.png", 'cw_fx_redsolid_c', mtype='model unlit')

mat('mtl_cw_mine_halo', B + r"/textures/cw_mine_halo.png", 'cw_mine_halo_c',
    mtype='model unlit', blendFunc='Add', cullFace='Front', depthWrite='Off')

# EMP Launcher ball (build_empball.py)
mat('mtl_cw_emp_ball', B + r"/textures/cw_emp_ball.png", 'cw_emp_ball_c',
    mtype='model unlit', blendFunc='Add', cullFace='Front', depthWrite='Off')
A.xmodel('weapon_cw_empball', M + r"/weapon_cw_empball.XMODEL_EXPORT", mtype='rigid')

# thermal detonator
mat('mtl_cw_thermal', UI + r"/com_weap_inf_grenadethermal.png", 'cw_thermal_c', rgb)
mat('mtl_cw_thermal_view', UI + r"/com_1st_weap_inf_grenadethermal.png", 'cw_thermal_view_c', silver)
mat('mtl_cw_thermal_glow', B + r"/textures/cw_thermal_glow.png", 'cw_thermal_glow_c',
    mtype='model unlit', blendFunc='Add', cullFace='Front', depthWrite='Off')

# models
for name in ('cw_bdroid', 'cw_bdroid_eng', 'cw_bdroid_assault', 'cw_bdroid_assassin', 'cw_sbdroid'):
    A.xmodel(name, M + r"\%s.XMODEL_EXPORT" % name)
# player bodies need the torso/aim bone controllers that only the "multiplayer body" type sets up
A.xmodel('cw_clone_body', M + r"\cw_clone_body.XMODEL_EXPORT", mtype='multiplayer body')
A.xmodel('viewmodel_cw_clone_arms', M + r"\viewmodel_cw_clone_arms.XMODEL_EXPORT", mtype='viewhands')
for key in ('dc15', 'chaingun', 'pistol', 'sniper', 'launcher', 'emp', 'thermal', 'mine'):
    A.xmodel('viewmodel_cw_' + key, M + r"\viewmodel_cw_%s.XMODEL_EXPORT" % key)
for key in ('dc15', 'chaingun', 'pistol', 'sniper', 'launcher', 'emp', 'thermal', 'mine', 'missile'):
    A.xmodel('weapon_cw_' + key, M + r"\weapon_cw_%s.XMODEL_EXPORT" % key, mtype='rigid')
# one-handed first-person animation sets (build_viewmodels.py)
import json
for n in json.load(open(B + r"\xanim_export\cw_anims.json")):
    A.xanim(n, B + r"\xanim_export\%s.XANIM_EXPORT" % n, looping='1' if n.endswith('idle') else '0')
A.flush()

only = [a for a in sys.argv[1:] if not a.startswith('-')]
ok = True
for name, e in A.entries.items():
    if only and not any(o in name for o in only):
        continue
    ok &= A.convert({'material.gdf': 'material', 'xmodel.gdf': 'xmodel', 'xanim.gdf': 'xanim'}[e['gdf']], name)

# images the iwd must carry
with open(os.path.join(paths.MOD, 'images.txt'), 'w', newline='\n') as f:
    f.write('\n'.join(images) + '\n')
sys.exit(0 if ok else 1)
