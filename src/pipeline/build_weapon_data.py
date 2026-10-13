"""Generate the DC-15's non-model data into mod/: weapon file, recoloured FX, synthesized blaster sounds,
sound aliases and the localized name."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import os, re, sys, wave
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wpn

GAME = paths.WAW
MOD = paths.MOD
RAW = os.path.join(GAME, 'raw')


# ---------------------------------------------------------------- weapon file
def weapon():
    header, k = wpn.read(os.path.join(RAW, 'weapons', 'sp', 'zombie_thompson'))
    k.update({
        'displayName': 'CLONEWARS_DC15',
        'gunModel': 'viewmodel_cw_dc15',
        'worldModel': 'weapon_cw_dc15',
        'ammoName': 'cw_dc15', 'clipName': 'cw_dc15',
        'clipSize': '50', 'maxAmmo': '400', 'startAmmo': '250',
        'damage': '110', 'minDamage': '80', 'playerDamage': '40',
        'fireTime': '0.13',
        # Battlefront II reticle: one static centre image, no spreading side ticks; turns red over enemies
        'reticleCenter': 'cw_reticle', 'reticleCenterSize': '32', 'reticleSide': '', 'reticleSideSize': '0',
        'crosshairColorChange': '1',
        'viewFlashEffect': 'weapon/muzzleflashes/fx_cw_blaster_view',
        'worldFlashEffect': 'weapon/muzzleflashes/fx_cw_blaster_world',
        'viewShellEjectEffect': '', 'worldShellEjectEffect': '',
        'viewLastShotEjectEffect': '', 'worldLastShotEjectEffect': '',
        'fireSound': 'weap_cw_blaster_fire', 'fireSoundPlayer': 'weap_cw_blaster_fire_plr',
        'lastShotSound': 'weap_cw_blaster_fire', 'lastShotSoundPlayer': 'weap_cw_blaster_fire_plr',
        # energy weapon: gentler kick than the Thompson
        'hipGunKickPitchMin': '10', 'hipGunKickPitchMax': '15', 'hipViewKickPitchMin': '15', 'hipViewKickPitchMax': '25',
        'adsViewKickPitchMin': '25', 'adsViewKickPitchMax': '35',
    })
    missing = [x for x in ('clipSize', 'maxAmmo', 'startAmmo', 'fireSoundPlayer', 'gunModel') if x not in wpn.read(os.path.join(RAW, 'weapons', 'sp', 'zombie_thompson'))[1]]
    if missing:
        print('WARNING keys not in the base weapon file:', missing)
    os.makedirs(os.path.join(MOD, 'weapons', 'sp'), exist_ok=True)
    wpn.write(os.path.join(MOD, 'weapons', 'sp', 'cw_dc15'), header, k)
    print('weapon file: cw_dc15 (%d keys)' % len(k))


# ---------------------------------------------------------------- fx recolour
NUMS = re.compile(r'^(\s*)(-?[\d.]+) (-?[\d.]+) (-?[\d.]+) (-?[\d.]+)\s*$')
NUMS2 = re.compile(r'^-?[\d.]+(e-?\d+)? -?[\d.]+(e-?\d+)?$')      # two-number graph key (time value)


def recolor(src, dst, tint=(0.25, 0.55, 1.0), life_scale=None, size_scale=None):
    """Copy an .efx, tinting every colorGraph key to blaster blue (keeps brightness)."""
    out, in_color = [], False
    for line in open(os.path.join(RAW, 'fx', src + '.efx'), errors='replace').read().replace('\r', '').split('\n'):
        s = line.strip()
        if s.startswith('colorGraph'):
            in_color = True
        elif s.startswith('alphaGraph'):
            in_color = False
        m = NUMS.match(line)
        if in_color and m:
            t, r, g, b = (float(m.group(i)) for i in range(2, 6))
            L = max(r, g, b)
            line = '%s%g %g %g %g' % (m.group(1), t, L * tint[0], L * tint[1], L * tint[2])
        if size_scale and s.split(' ')[0] in ('sizeGraph0', 'sizeGraph1', 'scaleGraph'):
            name, val = s.split()[:2]
            line = '\t%s %g' % (name, float(val) * size_scale)
        if s.startswith('emission ') and 'raygun' in s:
            line = '	emission "";'  # drop the ray gun's green ring child effect
        if life_scale and s.startswith('lifeSpanMsec'):
            a, b = s.rstrip(';').split()[1:3]
            line = '\tlifeSpanMsec %d %d;' % (max(1, int(float(a) * life_scale)), int(float(b) * life_scale))
        out.append(line)
    p = os.path.join(MOD, 'fx', dst + '.efx')
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', newline='\r\n') as f:
        f.write('\n'.join(out))
    print('fx:', dst)


def fx():
    # (round 7-8 recoloured the droid eye glow here; round 9 turned the glow off: _cw.gsc level.zombie_eye_glow)
    recolor('weapon/muzzleflashes/fx_raygun_view', 'weapon/muzzleflashes/fx_cw_blaster_view')
    recolor('weapon/muzzleflashes/fx_raygun_world', 'weapon/muzzleflashes/fx_cw_blaster_world')
    recolor('misc/fx_trail_raygun_geotrail', 'misc/fx_cw_blaster_bolt', life_scale=0.08)
    recolor('misc/fx_exp_raygun_impact', 'misc/fx_cw_blaster_impact', size_scale=0.3)


# ---------------------------------------------------------------- sound
def synth_blaster(seed, dur=0.42, sr=44100):
    """Classic blaster: a fast downward chirp with a metallic ring, a noise transient and a short tail."""
    rng = np.random.default_rng(seed)
    t = np.arange(int(dur * sr)) / sr
    f0 = 2600 + rng.uniform(-150, 150)
    f1 = 260 + rng.uniform(-30, 30)
    freq = f1 + (f0 - f1) * np.exp(-t * 16.0)
    phase = 2 * np.pi * np.cumsum(freq) / sr
    chirp = np.sin(phase) + 0.45 * np.sin(2.01 * phase) + 0.25 * np.sign(np.sin(0.5 * phase)) * np.exp(-t * 30)
    ring = 0.35 * np.sin(2 * np.pi * 3100 * t + 6 * np.sin(2 * np.pi * 140 * t)) * np.exp(-t * 22)
    noise = rng.normal(0, 1, len(t)) * np.exp(-t * 60) * 0.6
    env = np.minimum(t / 0.002, 1.0) * np.exp(-t * 9.5)
    x = (chirp * 0.7 + ring + noise) * env
    # cheap slap-back to give it some space
    d = int(0.045 * sr)
    y = x.copy()
    y[d:] += 0.25 * x[:-d]
    y = np.tanh(1.6 * y)
    return y / np.abs(y).max() * 0.89


def write_wav(path, x, sr=44100):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype('<i2').tobytes())


SWBF2_BANK = os.path.join(paths.SWBF2_LVL, 'sound', 'common.bnk')
# Each gun's own SWBF2 fire sample (common.bnk; sample names are hashes).  Found by matching recorded SWBF2 shots
# (recordings of SWBF2 gameplay) against the samples of every "weapons"-group SoundProperties in the munged sound
# configs (snd_ chunks): log-spectrogram + waveform correlation over each property's Pitch +- PitchDev.
# All of these properties play at pitch 1.0 +- 0.05.  The EMP and rocket launchers share one launch sample; the
# chaingun's is a 0.06 s loop (one copy per 0.05 s shot recreates it).  No recording of the commando pistol: it
# borrows the pistol sample, pitched down.
SWBF2_FIRE = {          # voice: (sample id, pitch min, pitch max, volume scale)
    'pistol': (0x6630e8c3, 0.95, 1.05, 0.9),
    'commando': (0x6630e8c3, 0.82, 0.88, 1.0),
    'rifle': (0x07f5df27, 0.95, 1.05, 1.0),
    'blaster': (0x07f5df27, 0.95, 1.05, 1.0),     # cw_dc15's own alias (build_weapon_data weapon())
    'shotgun': (0xa41baba0, 0.95, 1.05, 1.0),
    'chaingun': (0xdbcc96b6, 0.95, 1.05, 0.8),
    'sniper': (0x992ec6e7, 0.98, 1.02, 1.0),
    'rocket': (0x643bbc70, 0.95, 1.05, 1.0),
    'emp': (0x643bbc70, 0.95, 1.05, 1.0),
}
# EMP explosion (projExplosionSound): the EMP impact in the recording, one of the 6 random variants of
# SWBF2's explosion property aa6d9ff7 (pitch 1.0 +- 0.15).  alias weap_cw_emp_impact
SWBF2_IMPACT = (0x5e96c1c0, 0.85, 1.15)


def swbf2_samples(ids):
    """{id: (float mono, sample rate)} for the given SWBF2 sample ids (missing ones left out)."""
    import swbf_sound
    if not os.path.exists(SWBF2_BANK):
        return {}
    bank = next(swbf_sound.banks(SWBF2_BANK))
    off = bank['data_off']
    out = {}
    for s in bank['samples']:
        size = 0 if 'alias' in s else s['size']
        if s['id'] in ids:
            x = np.frombuffer(bank['buf'], '<i2', size // 2, off).astype(float) / 32768
            out[s['id']] = (x / np.abs(x).max() * 0.89, s['freq'])
        off += size
    return out


def sound():
    ids = {v[0] for v in SWBF2_FIRE.values()} | {SWBF2_IMPACT[0]}
    real = swbf2_samples(ids)
    files = {}
    for sid in sorted(ids):
        rel = 'clonewars/swbf2_%08x.wav' % sid
        if sid in real:
            x, sr = real[sid]
            print('sound: SWBF2 sample %08x, %.2f s @ %d Hz' % (sid, len(x) / sr, sr))
        else:
            x, sr = synth_blaster(100), 44100
            print('sound: SWBF2 sample %08x not found, using the synthesized blaster' % sid)
        # the linker reads loaded sounds from raw/sound, the game streams from the iwd
        write_wav(os.path.join(RAW, 'sound', rel.replace('/', os.sep)), x, sr)
        write_wav(os.path.join(MOD, 'sound', rel.replace('/', os.sep)), x, sr)
        files[sid] = rel
    header = open(os.path.join(RAW, 'soundaliases', 'weapons.csv'), errors='replace').readline().strip().split(',')
    base = {}
    for line in open(os.path.join(RAW, 'soundaliases', 'weapons.csv'), errors='replace'):
        c = line.rstrip('\r\n').split(',')
        if c[0] in ('weap_thompson_fire_plr', 'weap_thompson_fire'):
            base[c[0]] = dict(zip(header, c))
        elif c[0] == 'rpg_impact_boom' and 'all_mp' not in line:     # the SP Panzerschreck explosion
            base[c[0]] = dict(zip(header, c))
    rows = []
    for voice, (sid, lo, hi, vol) in SWBF2_FIRE.items():
        for suffix, tmpl in (('_plr', 'weap_thompson_fire_plr'), ('', 'weap_thompson_fire')):
            r = dict(base[tmpl])   # the linker rejects duplicate alias names; the pitch range gives the variation
            r.update({'name': 'weap_cw_%s_fire%s' % (voice, suffix), 'file': files[sid], 'loadspec': 'clonewars',
                      'secondaryaliasname': '', 'pitch_min': str(lo), 'pitch_max': str(hi), 'limit_count': '6'})
            for key in ('vol_min', 'vol_max'):
                if r.get(key):
                    r[key] = '%g' % (float(r[key]) * vol)
            rows.append(','.join(r.get(h, '') for h in header))
    sid, lo, hi = SWBF2_IMPACT
    r = dict(base['rpg_impact_boom'])
    r.update({'name': 'weap_cw_emp_impact', 'file': files[sid], 'sequence': '', 'loadspec': 'clonewars',
              'secondaryaliasname': '', 'pitch_min': str(lo), 'pitch_max': str(hi)})
    rows.append(','.join(r.get(h, '') for h in header))
    p = os.path.join(MOD, 'soundaliases', 'clonewars.csv')
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', newline='\r\n') as f:
        f.write(','.join(header) + '\n' + '\n'.join(rows) + '\n')
    print('sound: %d wavs, %d aliases' % (len(files), len(rows)))


# ---------------------------------------------------------------- localized strings
from build_strings import PRICE      # temporary flat prices (0 = stock)
GUN_NAMES = (('DC15', 'DC-15A Blaster Rifle'), ('PISTOL', 'Blaster Pistol'), ('COMMANDO', 'Commando Pistol'),
             ('SHOTGUN', 'Shotgun'), ('CHAINGUN', 'Chaingun'), ('SNIPER', 'Sniper Rifle'), ('ROCKET', 'Rocket Launcher'),
             ('EMP', 'EMP Launcher'))
STRINGS = list(GUN_NAMES) + [(k + '_UP', 'Elite ' + v) for k, v in GUN_NAMES] + [
    ('THERMAL', 'Thermal Detonator'), ('MINE', 'Land Mine'),
    ('BUY_MINES', 'Press [{+activate}] to buy Land Mines [Cost: %d]' % (PRICE or 250)),
    ('PAP', 'Press [{+activate}] to buy Pack-a-Punch Upgrade [Cost: %d]' % (PRICE or 5000)),
    ('PAP_TAKE', 'Press [{+activate}] to take your upgraded weapon'),
    ('NADE_THERMAL', 'Thermal Detonators'), ('NADE_MINE', 'Land Mines'),
]


def strings():
    # the linker only looks for .str files under raw/, not under the mod dir
    body = ''.join('REFERENCE           %s\nLANG_ENGLISH        "%s"\n\n' % kv for kv in STRINGS)
    for p in (os.path.join(MOD, 'english', 'localizedstrings', 'clonewars.str'),
              os.path.join(RAW, 'english', 'localizedstrings', 'clonewars.str')):
      os.makedirs(os.path.dirname(p), exist_ok=True)
      with open(p, 'w', newline='\r\n') as f:
        f.write('VERSION             "1"\nCONFIG              "C:\\trees\\cod3\\cod3\\bin\\StringEd.cfg"\nFILENOTES           ""\n\n'
                + body + 'ENDMARKER\n')
    print('strings: %d' % len(STRINGS))


if __name__ == '__main__':
    fx(); sound(); strings()   # weapon files: build_weapon_files.py
