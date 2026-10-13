"""Build the whole mod on this PC, from the user's own World at War and Star Wars Battlefront II files.

  python build.py              every step
  python build.py --from N     resume at step N (see the list printed at the start)
  python build.py --only N     one step
"""
import os, shutil, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import paths


def own_files():
    """The mod's own scripts and fastfile list (src/mod) -> work/mod."""
    for dp, dn, fn in os.walk(paths.MOD_SRC):
        d = os.path.join(paths.MOD, os.path.relpath(dp, paths.MOD_SRC))
        os.makedirs(d, exist_ok=True)
        for f in fn:
            shutil.copyfile(os.path.join(dp, f), os.path.join(d, f))
    print('copied src/mod -> work/mod')


STEPS = [
    ('Read SWBF2 assets and WaW map scripts', 'extract.py'),
    ('Rebuild the changed stock script (_loadout.gsc)', 'stock_scripts.py'),
    ('Copy the mod\'s own scripts', own_files),
    ('Battle droids and clone trooper body', 'build_droid.py'),
    ('Gun world models', 'build_weapons.py'),
    ('First-person guns and animations', 'build_viewmodels.py'),
    ('EMP ball', 'build_empball.py'),
    ('Thermal detonator', 'build_thermal.py'),
    ('Land mine', 'build_mine.py'),
    ('First-person arms', 'build_arms.py'),
    ('Battlefront crosshair', 'build_reticle.py'),
    ('Effects, sounds, strings', 'build_weapon_data.py'),
    ('Weapon files', 'build_weapon_files.py'),
    ('Wall-gun price table', 'build_prices.py'),
    ('Wall-gun names', 'build_strings.py'),
    ('Convert models, animations, materials (Mod Tools converter)', 'build_assets.py'),
    ('Check script references on all four maps', 'check_refs.py'),
    ('Link mod.ff, pack the iwd, install', 'build_mod.py'),
]


def main():
    first, only = 1, None
    if '--from' in sys.argv:
        first = int(sys.argv[sys.argv.index('--from') + 1])
    if '--only' in sys.argv:
        only = int(sys.argv[sys.argv.index('--only') + 1])
    t0 = time.time()
    for i, (title, step) in enumerate(STEPS, 1):
        if (only and i != only) or i < first:
            continue
        print('\n=== [%d/%d] %s' % (i, len(STEPS), title), flush=True)
        t = time.time()
        if callable(step):
            step()
        else:
            r = subprocess.run([sys.executable, os.path.join(HERE, step)], cwd=HERE)
            if r.returncode != 0:
                print('\nStep %d (%s) failed.  Fix the problem above, then resume with:  Install.bat --from %d' % (i, title, i))
                sys.exit(1)
        print('    (%.0f s)' % (time.time() - t), flush=True)
    print('\nDone in %.1f minutes.' % ((time.time() - t0) / 60))


if __name__ == '__main__':
    main()
