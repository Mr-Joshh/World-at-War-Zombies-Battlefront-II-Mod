"""Weapon files for the SWBF2 Republic guns, and the overrides that put them on every wall / box / Pack-a-Punch slot.

Each SWBF2 gun is a template built on the stock weapon whose first-person animations it borrows
(rifle / shotgun / chaingun: Thompson, pistols: Colt, sniper: PTRS, launchers: Panzerschreck).

  * mod/weapons/sp/cw_<gun>       the gun under its own name (cw_dc15 is the start weapon; the others are listed in
                                  mod.csv so the linker pulls their models / animations / effects into mod.ff)
  * mod/weapons/sp/<stock name>   every WWII weapon of the four zombie maps re-written as the closest SWBF2 gun
                                  (weapon files are read loose from the iwd, so the map's walls, mystery box and
                                  Der Riese's Pack-a-Punch hand out SWBF2 guns without touching the map scripts).
                                  Each keeps its own ammo name; "_upgraded" files become "Elite" versions.
  * mod/maps/_cw_weapons.gsc      generated table: weapon name -> SWBF2 class (bolts, ADS reticle, sounds in script)

SWBF2 -> WaW slot mapping (CLASSES below):
  Blaster Pistol: Colts / Walther          Commando Pistol: .357
  DC-15A Blaster Rifle: every rifle / SMG  Shotgun: double-barrels, trench gun
  Chaingun: BAR, FG42, MG42, .30 cal       Sniper Rifle: PTRS, scoped Kar98k / Type 99
  Rocket Launcher: Panzerschreck           EMP Launcher: M2 flamethrower (the box's other "big" gun)
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wpn

RAW = os.path.join(paths.WAW, 'raw', 'weapons', 'sp')
MOD = paths.MOD

CLASSES = {
    'pistol': ['colt', 'colt_dirty_harry', 'walther', 'zombie_colt'],
    'commando': ['sw_357', 'zombie_sw_357'],
    'rifle': ['m1carbine', 'm1garand', 'gewehr43', 'stg44', 'thompson', 'mp40', 'ppsh', 'kar98k', 'springfield',
              'm1garand_gl', 'm1garand_gl_zombie', 'zombie_m1carbine', 'zombie_m1garand', 'zombie_gewehr43', 'zombie_kar98k',
              'zombie_type99_rifle', 'zombie_stg44', 'zombie_thompson', 'zombie_mp40', 'zombie_type100_smg', 'zombie_ppsh'],
    'shotgun': ['doublebarrel', 'doublebarrel_sawed_grip', 'shotgun', 'zombie_doublebarrel', 'zombie_doublebarrel_sawed',
                'zombie_shotgun'],
    'chaingun': ['fg42_bipod', 'mg42_bipod', '30cal_bipod', 'bar', 'bar_bipod', 'zombie_bar', 'zombie_30cal', 'zombie_fg42',
                 'zombie_mg42'],
    'sniper': ['ptrs41_zombie', 'kar98k_scoped_zombie', 'type99_rifle_scoped_zombie'],
    'rocket': ['panzerschrek', 'panzerschrek_zombie'],
    'emp': ['m2_flamethrower_zombie'],
}
# Der Riese's Pack-a-Punch results (only these "_upgraded" files exist in the stock game)
UPGRADED = ['zombie_colt', 'zombie_sw_357', 'zombie_kar98k', 'zombie_type99_rifle', 'zombie_m1carbine', 'zombie_m1garand',
            'zombie_gewehr43', 'zombie_stg44', 'zombie_thompson', 'zombie_mp40', 'zombie_type100_smg', 'm1garand_gl_zombie',
            'zombie_doublebarrel', 'zombie_shotgun', 'zombie_bar', 'zombie_fg42', 'zombie_30cal', 'zombie_mg42', 'zombie_ppsh',
            'ptrs41_zombie', 'panzerschrek_zombie', 'm2_flamethrower_zombie']

NAMES = {'rifle': 'DC15', 'pistol': 'PISTOL', 'commando': 'COMMANDO', 'shotgun': 'SHOTGUN', 'chaingun': 'CHAINGUN',
         'sniper': 'SNIPER', 'rocket': 'ROCKET', 'emp': 'EMP'}
MODEL = {'rifle': 'dc15', 'pistol': 'pistol', 'commando': 'pistol', 'shotgun': 'dc15', 'chaingun': 'chaingun',
         'sniper': 'sniper', 'rocket': 'launcher', 'emp': 'emp'}
DONOR = {'rifle': 'zombie_thompson', 'shotgun': 'zombie_thompson', 'chaingun': 'zombie_thompson', 'pistol': 'zombie_colt',
         'commando': 'zombie_colt', 'sniper': 'ptrs41_zombie', 'rocket': 'panzerschrek_zombie', 'emp': 'panzerschrek_zombie'}
# launchers keep the Panzerschreck's projectile weapon file but are held like the rifles (the Panzerschreck's
# shoulder pose put the SWBF2 launchers almost entirely off the bottom of the screen)
BLASTERS = ('rifle', 'pistol', 'commando', 'shotgun', 'chaingun', 'sniper')


def spread(k, lo, hi, fire_add=0.3, move_add=0.5):
    for key in ('hipSpreadStandMin', 'hipSpreadDuckedMin', 'hipSpreadProneMin'):
        k[key] = str(lo)
    for key in ('hipSpreadMax', 'hipSpreadDuckedMax', 'hipSpreadProneMax'):
        k[key] = str(hi)
    k.update({'hipSpreadFireAdd': str(fire_add), 'hipSpreadMoveAdd': str(move_add)})


def reticle(k):
    k.update({'reticleCenter': 'cw_reticle', 'reticleCenterSize': '32', 'reticleSide': '', 'reticleSideSize': '0',
              'crosshairColorChange': '1'})


TWO_HANDED = ('dc15', 'sniper', 'emp')      # must match hands=2 in build_viewmodels.py


def two_handed(k, model):
    """Held in both hands (left hand under the gun): the Thompson animations with the hands moved per gun and the reload
    a dip out of view (build_viewmodels.py anims_two: cw_<model>_t_<anim>)."""
    h, t = wpn.read(os.path.join(RAW, 'zombie_thompson'))
    for key in [x for x in k if x.endswith('Anim')]:
        v = t.get(key, '')
        if v.startswith('viewmodel_thompson_'):
            v = 'cw_%s_t_%s' % (model, v[len('viewmodel_thompson_'):].lower())
        k[key] = v
    k['reloadAnim'] = k['reloadEmptyAnim'] = 'cw_%s_t_reload' % model
    for key in ('raiseTime', 'dropTime', 'quickRaiseTime', 'quickDropTime', 'firstRaiseTime', 'adsTransInTime',
                'adsTransOutTime', 'sprintInTime', 'sprintLoopTime', 'sprintOutTime'):
        if key in t and key in k:
            k[key] = t[key]
    k.update({'reloadTime': '1.0', 'reloadEmptyTime': '1.0', 'reloadAddTime': '0.6', 'reloadEmptyAddTime': '0.6',
              'reloadStartAddTime': '0.6', 'reloadSound': '', 'reloadSoundPlayer': '', 'reloadEmptySound': '',
              'reloadEmptySoundPlayer': '', 'notetrackSoundMap': '', 'adsZoomFov': '45'})


def one_handed(k, model):
    """SWBF2 first person: right hand under the gun, animations from build_viewmodels.py (cw_<model>_<anim>).
    Aiming down sights keeps the hip pose (SWBF2 has no iron sights) and zooms; maps/_cw.gsc keeps the reticle up."""
    if model in TWO_HANDED:
        two_handed(k, model)
        return
    a = lambda n: 'cw_%s_%s' % (model, n)
    for key in ('idleAnim', 'emptyIdleAnim'):
        k[key] = a('idle')
    for key in ('adsFireAnim', 'adsLastShotAnim', 'adsUpAnim', 'adsDownAnim'):
        k[key] = a('ads')
    for key in ('fireAnim', 'lastShotAnim'):
        k[key] = a('fire')
    for key in ('reloadAnim', 'reloadEmptyAnim'):
        k[key] = a('reload')
    for key in ('raiseAnim', 'firstRaiseAnim', 'altRaiseAnim', 'emptyRaiseAnim'):
        k[key] = a('raise')
    for key in ('dropAnim', 'altDropAnim', 'emptyDropAnim'):
        k[key] = a('drop')
    k.update({'quickRaiseAnim': a('raise_fast'), 'quickDropAnim': a('drop_fast'),
              'reloadTime': '1.0', 'reloadEmptyTime': '1.0', 'reloadAddTime': '0.6', 'reloadEmptyAddTime': '0.6',
              'reloadStartAddTime': '0.6', 'reloadSound': '', 'reloadSoundPlayer': '', 'reloadEmptySound': '',
              'reloadEmptySoundPlayer': '', 'notetrackSoundMap': '', 'adsZoomFov': '45'})
    for key in ('sprintInAnim', 'sprintLoopAnim', 'sprintOutAnim', 'rechamberAnim', 'reloadStartAnim', 'reloadEndAnim'):
        if key in k:
            k[key] = ''


def blaster(k, sound):
    """Battlefront II reticle (static, turns red over droids), blue muzzle flash, no brass, blaster sound."""
    k.update({
        'reticleCenter': 'cw_reticle', 'reticleCenterSize': '32', 'reticleSide': '', 'reticleSideSize': '0',
        'crosshairColorChange': '1',
        'viewFlashEffect': 'weapon/muzzleflashes/fx_cw_blaster_view',
        'worldFlashEffect': 'weapon/muzzleflashes/fx_cw_blaster_world',
        'viewShellEjectEffect': '', 'worldShellEjectEffect': '', 'viewLastShotEjectEffect': '', 'worldLastShotEjectEffect': '',
        'fireSound': 'weap_cw_%s_fire' % sound, 'fireSoundPlayer': 'weap_cw_%s_fire_plr' % sound,
        'lastShotSound': 'weap_cw_%s_fire' % sound, 'lastShotSoundPlayer': 'weap_cw_%s_fire_plr' % sound,
    })


def rifle(k):
    blaster(k, 'rifle')
    k.update({'clipSize': '50', 'maxAmmo': '400', 'startAmmo': '250', 'damage': '160', 'minDamage': '115', 'playerDamage': '40',
              'fireTime': '0.2',
              'hipGunKickPitchMin': '10', 'hipGunKickPitchMax': '15', 'hipViewKickPitchMin': '15', 'hipViewKickPitchMax': '25',
              'adsViewKickPitchMin': '25', 'adsViewKickPitchMax': '35'})


def pistol(k):
    blaster(k, 'pistol')
    k.update({'clipSize': '16', 'maxAmmo': '128', 'startAmmo': '64', 'damage': '110', 'minDamage': '75', 'fireTime': '0.2',
              'reloadTime': '1.6', 'reloadEmptyTime': '2.2'})
    spread(k, 1.5, 4.0, 0.8, 2.0)


def commando(k):
    blaster(k, 'commando')
    k.update({'clipSize': '10', 'maxAmmo': '80', 'startAmmo': '40', 'damage': '90', 'minDamage': '65', 'fireTime': '0.1',
              'locHead': '3', 'penetrateType': 'medium',
              'hipViewKickPitchMin': '60', 'hipViewKickPitchMax': '80', 'adsViewKickPitchMin': '60', 'adsViewKickPitchMax': '80'})
    spread(k, 1.0, 3.5, 1.2, 2.0)


def shotgun(k):
    """SWBF2's Republic shotgun is the DC-15 body firing a burst of short-range bolts."""
    blaster(k, 'shotgun')
    k.update({'weaponClass': 'spread', 'fireType': 'Single Shot', 'shotCount': '8', 'clipSize': '8', 'maxAmmo': '64',
              'startAmmo': '40', 'damage': '170', 'minDamage': '25', 'maxDamageRange': '256', 'minDamageRange': '800',
              'fireTime': '1.0', 'adsSpread': '5', 'enemyCrosshairRange': '384',
              'hipViewKickPitchMin': '90', 'hipViewKickPitchMax': '120', 'adsViewKickPitchMin': '90', 'adsViewKickPitchMax': '120',
              'hipGunKickPitchMin': '40', 'hipGunKickPitchMax': '60'})
    spread(k, 5, 5, 0.0, 0.1)


def chaingun(k):
    blaster(k, 'chaingun')
    # sprint (no sprint animation: the engine's procedural sprint pose): the donor's turns the gun 45 deg in toward the
    # screen centre, which with this big gun covered most of the view - drop it low and to the right instead
    k.update({'sprintOfsF': '-3', 'sprintOfsR': '2', 'sprintOfsU': '-7', 'sprintRotP': '25', 'sprintRotY': '-10',
              'sprintRotR': '0', 'sprintScale': '1'})
    k.update({'weaponClass': 'mg', 'clipSize': '125', 'maxAmmo': '500', 'startAmmo': '375', 'damage': '95', 'minDamage': '70',
              'fireTime': '0.05', 'reloadTime': '3.0', 'reloadEmptyTime': '3.4', 'moveSpeedScale': '0.9',
              'hipGunKickPitchMin': '8', 'hipGunKickPitchMax': '12', 'hipViewKickPitchMin': '10', 'hipViewKickPitchMax': '20'})
    spread(k, 2.5, 6.0, 0.25, 1.0)


def sniper(k):
    blaster(k, 'sniper')
    k.update({'clipSize': '6', 'maxAmmo': '48', 'startAmmo': '24', 'damage': '1150', 'minDamage': '1150', 'fireTime': '0.8',
              'penetrateType': 'large',
              # zoom through a transparent overlay (it hides the gun); maps/_cw.gsc draws the Battlefront reticle
              'adsOverlayShader': 'cw_scope_clear', 'adsOverlayShaderLowRes': 'cw_scope_clear', 'adsOverlayReticle': 'none',
              'adsOverlayWidth': '8', 'adsOverlayHeight': '8', 'adsZoomFov': '15'})


def launcher_sound(k, sound):
    k.update({'fireSound': 'weap_cw_%s_fire' % sound, 'fireSoundPlayer': 'weap_cw_%s_fire_plr' % sound,
              'lastShotSound': 'weap_cw_%s_fire' % sound, 'lastShotSoundPlayer': 'weap_cw_%s_fire_plr' % sound})


def rocket(k):
    reticle(k)
    launcher_sound(k, 'rocket')
    k.update({'adsFire': '0',          # fires from the hip (the Panzerschreck file only fires while aiming)
              'projectileModel': 'weapon_cw_missile', 'clipSize': '1', 'maxAmmo': '16', 'startAmmo': '8',
              'explosionInnerDamage': '1200', 'explosionOuterDamage': '150', 'explosionRadius': '256'})


def emp(k):
    """EMP launcher: a blue blast that is murder on droids (they are all droids), nothing else.  Fires from the hip,
    one shot every 1.5 s from a 6-shot charge (no reload after every shot)."""
    reticle(k)
    launcher_sound(k, 'emp')
    k['projExplosionSound'] = 'weap_cw_emp_impact'      # SWBF2's EMP impact (build_weapon_data.py)
    k.update({'adsFire': '0', 'fireTime': '1.5', 'noPartialReload': '0',     # reload any time, not only when empty
              # blue blaster flash at the muzzle instead of the Panzerschreck's orange launch blast
              'viewFlashEffect': 'weapon/muzzleflashes/fx_cw_blaster_view', 'worldFlashEffect': 'weapon/muzzleflashes/fx_cw_blaster_world',
              'projectileModel': 'weapon_cw_empball', 'projectileSpeed': '1100', 'clipSize': '6', 'maxAmmo': '30', 'startAmmo': '18',
              'explosionInnerDamage': '1900', 'explosionOuterDamage': '300', 'explosionRadius': '220',
              'projExplosionEffect': 'misc/fx_cw_blaster_impact', 'impactType': 'none',
              'projTrailEffect': 'misc/fx_cw_blaster_bolt', 'projectileRed': '0.3', 'projectileGreen': '0.6', 'projectileBlue': '1'})


# fireTime of every blaster = SWBF2's ShotDelay (rep_weap_inf_*.odf); damage keeps roughly the pre-match WaW DPS
TEMPLATES = {'rifle': rifle, 'pistol': pistol, 'commando': commando, 'shotgun': shotgun, 'chaingun': chaingun,
             'sniper': sniper, 'rocket': rocket, 'emp': emp}


def upgrade(k):
    """Pack-a-Punch: Battlefront's award ("Elite") weapons - harder hitting, bigger magazines."""
    for key, f in (('damage', 2.5), ('minDamage', 2.5), ('explosionInnerDamage', 2.0), ('explosionOuterDamage', 2.0)):
        if key in k and k[key]:
            k[key] = str(int(float(k[key]) * f))
    for key in ('clipSize', 'maxAmmo', 'startAmmo'):
        if key in k and k[key]:
            k[key] = str(max(int(float(k[key]) * 1.5), int(k[key]) + 1))


def make(cls, name, stock=None, upgraded=False):
    header, k = wpn.read(os.path.join(RAW, DONOR[cls]))
    known = set(k)
    model = MODEL[cls]
    k.update({'displayName': 'CLONEWARS_%s%s' % (NAMES[cls], '_UP' if upgraded else ''),
              'gunModel': 'viewmodel_cw_' + model, 'worldModel': 'weapon_cw_' + model, 'altWeapon': ''})
    one_handed(k, model)
    TEMPLATES[cls](k)
    if stock:
        # keep the stock weapon's own ammo pool / cap so every script and pickup that counts its ammo still works
        sh, s = wpn.read(os.path.join(RAW, stock))
        for key in ('ammoName', 'clipName', 'sharedAmmoCapName', 'sharedAmmoCap'):
            if key in s:
                k[key] = s[key]
    else:
        k.update({'ammoName': name, 'clipName': name, 'sharedAmmoCapName': ''})
    if upgraded:
        upgrade(k)
    for extra in [x for x in k if x not in known]:
        print('   %s: dropping key %s (not in %s)' % (name, extra, DONOR[cls]))
        del k[extra]
    out = os.path.join(MOD, 'weapons', 'sp', name)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    wpn.write(out, header, k)


def gsc_table(table):
    lines = ['// generated by tools/build_weapon_files.py - weapon name -> SWBF2 class', '',
             'init()', '{', '\tlevel.cw_class = [];']
    for name, cls in sorted(table.items()):
        lines.append('\tlevel.cw_class["%s"] = "%s";' % (name, cls))
    lines += ['}', '']
    with open(os.path.join(MOD, 'maps', '_cw_weapons.gsc'), 'w', newline='\n') as f:
        f.write('\n'.join(lines))


if __name__ == '__main__':
    table = {}
    names = {'rifle': 'cw_dc15'}
    for cls in TEMPLATES:
        name = names.get(cls, 'cw_' + cls)
        make(cls, name)
        table[name] = cls
    n = 0
    for cls, stock_names in CLASSES.items():
        for s in stock_names:
            make(cls, s, stock=s)
            table[s] = cls
            n += 1
            if s in UPGRADED or True:     # Nacht's spawned Pack-a-Punch needs upgrades of its own gun names too
                stock_up = s + '_upgraded' if s in UPGRADED else s
                make(cls, s + '_upgraded', stock=stock_up, upgraded=True)
                table[s + '_upgraded'] = cls
                n += 1
    # the linker prefers raw/ over the mod dir: weapons linked into mod.ff whose name has a stock file in raw/ (Der Riese's
    # upgraded guns) go through mod/raw_override, or the stock file (and its WWII effects) would be linked
    import shutil
    ov = os.path.join(MOD, 'raw_override', 'weapons', 'sp')
    os.makedirs(ov, exist_ok=True)
    for name in ('zombie_colt_upgraded', 'ptrs41_zombie_upgraded', 'kar98k_scoped_zombie_upgraded'):
        shutil.copyfile(os.path.join(MOD, 'weapons', 'sp', name), os.path.join(ov, name))
    gsc_table(table)
    print('weapon files: %d SWBF2 guns + %d stock overrides; table maps/_cw_weapons.gsc' % (len(TEMPLATES), n))
