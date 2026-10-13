"""Link mods/clonewars/mod.ff with the World at War Mod Tools, pack clonewars.iwd and install both for the game.

work/mod (scripts, weapon files, sounds, effects, strings) is mirrored into <Mod Tools>/mods/clonewars; the converted
models, materials and images are already in the Mod Tools' raw/ folder (build_assets.py).
"""
import os, shutil, struct, subprocess, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths

WAW = paths.WAW
SRC = paths.MOD
MODDIR = os.path.join(WAW, 'mods', paths.MOD_NAME)
IWD = paths.MOD_NAME + '.iwd'


def copytree(a, b):
    for dp, dn, fn in os.walk(a):
        d = os.path.join(b, os.path.relpath(dp, a))
        os.makedirs(d, exist_ok=True)
        for f in fn:
            shutil.copyfile(os.path.join(dp, f), os.path.join(d, f))


def laa_linker():
    """linker_pc.exe is a 32-bit program; on some PCs it cannot reserve its 256 MB hunk (EXE_ERR_HUNK_ALLOC_FAILED256).
    A copy with the Large Address Aware flag set gets a 4 GB address space."""
    src = os.path.join(WAW, 'bin', 'linker_pc.exe')
    dst = os.path.join(WAW, 'bin', 'linker_pc_laa.exe')
    if not os.path.exists(dst):
        b = bytearray(open(src, 'rb').read())
        pe = struct.unpack_from('<I', b, 0x3C)[0]
        assert b[pe:pe + 4] == b'PE\0\0', 'linker_pc.exe is not a PE file'
        ch = struct.unpack_from('<H', b, pe + 22)[0]
        struct.pack_into('<H', b, pe + 22, ch | 0x20)
        open(dst, 'wb').write(bytes(b))
    return dst


def main():
    # mirror, not copy over: a stale effect or weapon file left in the mod folder would be linked again
    if os.path.exists(MODDIR):
        shutil.rmtree(MODDIR)
    copytree(SRC, MODDIR)
    shutil.copyfile(os.path.join(SRC, 'mod.csv'), os.path.join(WAW, 'zone_source', 'mod.csv'))

    # The linker prefers raw/ over the mod folder, so files that replace stock assets (raw_override/...) go into raw/
    # only while linking, and the stock files are put back afterwards.
    ovr = os.path.join(SRC, 'raw_override')
    overrides = []
    for dp, dn, fn in os.walk(ovr):
        for f in fn:
            overrides.append(os.path.relpath(os.path.join(dp, f), ovr))
    ff = os.path.join(WAW, 'zone', 'english', 'mod.ff')
    log = os.path.join(MODDIR, 'linker.log')
    try:
        for rel in overrides:
            stock = os.path.join(WAW, 'raw', rel)
            if os.path.exists(stock) and not os.path.exists(stock + '.cw-orig'):
                shutil.copyfile(stock, stock + '.cw-orig')
            os.makedirs(os.path.dirname(stock), exist_ok=True)
            shutil.copyfile(os.path.join(ovr, rel), stock)
        linker = laa_linker()
        if os.path.exists(ff):
            os.remove(ff)                      # a stale one would hide a failed link
        with open(log, 'w') as lf:
            subprocess.run([linker, '-nopause', '-language', 'english', '-moddir', paths.MOD_NAME, 'mod'],
                           cwd=os.path.join(WAW, 'bin'), stdin=subprocess.DEVNULL, stdout=lf, stderr=subprocess.STDOUT)
    finally:
        for rel in overrides:
            stock = os.path.join(WAW, 'raw', rel)
            if os.path.exists(stock + '.cw-orig'):
                shutil.move(stock + '.cw-orig', stock)
    text = open(log, errors='replace').read()
    if not os.path.exists(ff):
        print(text[-4000:])
        raise SystemExit('The linker did not write mod.ff (log: %s)' % log)
    for line in text.splitlines():
        if any(w in line.lower() for w in ('error', 'missing', 'could not', "couldn't")):
            print('  linker:', line.strip())
    shutil.move(ff, os.path.join(MODDIR, 'mod.ff'))

    # the iwd: the images the materials use, plus the files the game reads loose (sounds, weapon files, scripts)
    iwd = os.path.join(MODDIR, IWD)
    with zipfile.ZipFile(iwd, 'w', zipfile.ZIP_DEFLATED, compresslevel=5) as z:
        for img in open(os.path.join(SRC, 'images.txt')).read().split():
            z.write(os.path.join(WAW, 'raw', 'images', img + '.iwi'), 'images/' + img + '.iwi')
        for d in ('sound', 'weapons', 'maps', 'character', 'mp'):
            for dp, dn, fn in os.walk(os.path.join(MODDIR, d)):
                for f in fn:
                    p = os.path.join(dp, f)
                    z.write(p, os.path.relpath(p, MODDIR).replace(os.sep, '/'))
        # Der Riese's stock upgraded files sit in raw/; ours (the same names) must win in the game too
        for dp, dn, fn in os.walk(os.path.join(MODDIR, 'raw_override', 'weapons')):
            for f in fn:
                p = os.path.join(dp, f)
                arc = os.path.relpath(p, os.path.join(MODDIR, 'raw_override')).replace(os.sep, '/')
                if arc not in z.namelist():
                    z.write(p, arc)
    os.makedirs(paths.INSTALL, exist_ok=True)
    for f in ('mod.ff', IWD):
        shutil.copyfile(os.path.join(MODDIR, f), os.path.join(paths.INSTALL, f))
        print('installed %s (%.1f MB)' % (os.path.join(paths.INSTALL, f), os.path.getsize(os.path.join(paths.INSTALL, f)) / 1e6))


if __name__ == '__main__':
    main()
