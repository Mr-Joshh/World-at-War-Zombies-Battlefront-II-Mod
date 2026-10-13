"""Stage textures / models / GDT entries into the WaW mod-tools tree and run the converter."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import os, shutil, subprocess, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gdt

GAME = paths.WAW
TEX_DIR = os.path.join(GAME, 'texture_assets', 'clonewars')
MODEL_DIR = os.path.join(GAME, 'model_export', 'clonewars')
GDT_PATH = os.path.join(GAME, 'source_data', 'clonewars.gdt')
_TEMPLATES = None
entries = {}


def gdt_path(p):
    """GDT strings use doubled backslashes as path separators."""
    return p.replace('/', chr(92) * 2)


def _templates():
    global _TEMPLATES
    if _TEMPLATES is None:
        _TEMPLATES = gdt.read(os.path.join(GAME, 'model_export', 'viewmodels.gdt'))
    return _TEMPLATES


def texture(src, name, transform=None):
    """Copy an image into texture_assets as an uncompressed TGA; returns the gdt-relative path."""
    os.makedirs(TEX_DIR, exist_ok=True)
    im = Image.open(src)
    im = im.convert('RGBA' if 'A' in im.getbands() else 'RGB')
    if transform:
        im = transform(im)
    im.save(os.path.join(TEX_DIR, name + '.tga'))
    return gdt_path('texture_assets/clonewars/%s.tga' % name)


def material(name, color, normal='', spec='', gloss='', mtype='model phong', template='mtl_viewmodel_marine_cloth', **extra):
    k = dict(_templates()[template]['keys'])
    for key in list(k):
        if key.startswith('colorMap') or key.startswith('colorLabel') or key in ('detailMap', 'normalMap', 'specColorMap', 'cosinePowerMap'):
            k[key] = ''
    k.update({'colorMap': color, 'normalMap': normal, 'specColorMap': spec, 'cosinePowerMap': gloss, 'materialType': mtype})
    k.update(extra)
    entries[name] = {'gdf': 'material.gdf', 'keys': k}


def xmodel(name, export_src, mtype='animated', **extra):
    os.makedirs(MODEL_DIR, exist_ok=True)
    shutil.copyfile(export_src, os.path.join(MODEL_DIR, os.path.basename(export_src)))
    k = dict(_templates()['viewmodel_base_viewhands']['keys'])
    k.update({'filename': gdt_path('clonewars/' + os.path.basename(export_src)), 'type': mtype})
    k.update(extra)
    entries[name] = {'gdf': 'xmodel.gdf', 'keys': k}


def flush():
    gdt.write(GDT_PATH, entries)


def convert(kind, name):
    r = subprocess.run([os.path.join(GAME, 'bin', 'converter.exe'), '-nopause', '-nocachedownload', '-single', kind, name],
                       cwd=os.path.join(GAME, 'bin'), capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=600)
    out = (r.stdout + r.stderr).strip()
    bad = r.returncode != 0 or 'ERROR' in out.upper()
    print('convert %s %s -> rc=%d%s' % (kind, name, r.returncode, ' !!' if bad else ''))
    if bad or '--verbose' in sys.argv:
        print(out[-3000:])
    return not bad


XANIM_DIR = os.path.join(GAME, 'xanim_export', 'clonewars')
THOMPSON_ANIMATED = 'american/weapons/SMGs/thompson/viewmodel_usa_thompson_smg_animated.XMODEL_EXPORT'


def xanim(name, export_src, model=THOMPSON_ANIMATED, looping='0'):
    """Stage a generated XANIM_EXPORT and register it (viewmodel animation, 'relative' type)."""
    os.makedirs(XANIM_DIR, exist_ok=True)
    shutil.copyfile(export_src, os.path.join(XANIM_DIR, os.path.basename(export_src)))
    entries[name] = {'gdf': 'xanim.gdf', 'keys': {
        'angleError': '0.05', 'boneStabilizers': '', 'filename': gdt_path('clonewars/' + os.path.basename(export_src)),
        'looping': looping, 'model': gdt_path(model), 'node': '', 'notetrackfile': '', 'translationError': '0.025',
        'type': 'relative', 'useBones': '0'}}
