"""Rasterize SWBF2's HUD reticule meshes (flat white geometry) into a crosshair texture."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import sys, os
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import msh

SRC = os.path.join(paths.EXTRACT, 'ui_ingame', 'msh')
OUT = os.path.join(paths.BUILD, 'textures')
SIZE, SS = 128, 8          # output size, supersampling


def tris2d(name):
    d = msh.load(os.path.join(SRC, name + '.msh'))
    out = []
    for m in d['models']:
        for seg in m['segments']:
            if seg['pos'] is None:
                continue
            P = seg['pos'] @ m['world'][:3, :3].T + m['world'][:3, 3]
            for t in seg['tris']:
                out.append(P[list(t)])
    return np.array(out)


def build():
    main = tris2d('hud_main_reticule')
    outline = tris2d('hud_main_reticule_outline')
    allp = np.concatenate([main.reshape(-1, 3), outline.reshape(-1, 3)])
    ext = allp.max(0) - allp.min(0)
    axes = [i for i in np.argsort(-ext)[:2]]
    axes.sort()                                   # keep (x, y) order
    # centre on SWBF2's aim point (the bullseye quad sits at the origin), not on the brackets' bounding box
    c = np.zeros(3)
    half = np.abs(allp).max() * 1.08
    print('extent', ext.round(4), 'plane axes', axes, 'tris', len(main), len(outline))

    def draw(tris, value, layer):
        dr = ImageDraw.Draw(layer)
        n = SIZE * SS
        for t in tris:
            pts = [((p[axes[0]] - c[axes[0]]) / half * 0.5 + 0.5, 0.5 - (p[axes[1]] - c[axes[1]]) / half * 0.5) for p in t]
            dr.polygon([(x * n, y * n) for x, y in pts], fill=value)

    n = SIZE * SS
    a_out = Image.new('L', (n, n), 0); draw(outline, 255, a_out)
    a_main = Image.new('L', (n, n), 0); draw(main, 255, a_main)
    # centre dot: SWBF2's hud_main_reticule_bullseye is a small quad at the aim point; draw it round, with the
    # same dark outline as the brackets
    bull = tris2d('hud_main_reticule_bullseye').reshape(-1, 3)
    r = np.abs(bull[:, axes]).max() / half * 0.5 * n * 2.0
    m = n / 2
    ImageDraw.Draw(a_out).ellipse([m - r - 2.2 * SS, m - r - 2.2 * SS, m + r + 2.2 * SS, m + r + 2.2 * SS], fill=255)
    ImageDraw.Draw(a_main).ellipse([m - r, m - r, m + r, m + r], fill=255)
    a_out = np.asarray(a_out.resize((SIZE, SIZE), Image.LANCZOS), float) / 255
    a_main = np.asarray(a_main.resize((SIZE, SIZE), Image.LANCZOS), float) / 255
    alpha = np.clip(np.maximum(a_main, a_out * 0.75), 0, 1)
    lum = np.where(alpha > 0, a_main / np.maximum(alpha, 1e-6), 1.0)      # white lines over a dark outline
    rgba = np.dstack([lum * 255] * 3 + [alpha * 255]).astype('uint8')
    os.makedirs(OUT, exist_ok=True)
    Image.fromarray(rgba, 'RGBA').save(os.path.join(OUT, 'cw_reticle.png'))
    # preview on a mid-grey background, enlarged
    bg = Image.new('RGBA', (SIZE, SIZE), (90, 110, 90, 255))
    bg.alpha_composite(Image.fromarray(rgba, 'RGBA'))
    bg.resize((384, 384), Image.NEAREST).save(os.path.join(paths.BUILD, 'preview', 'reticle.png'))
    print('wrote cw_reticle.png')
    # Sniper Rifle ADS overlay: fully transparent, so zooming hides the gun and only the Battlefront reticle shows
    Image.new('RGBA', (8, 8), (0, 0, 0, 0)).save(os.path.join(OUT, 'cw_scope_clear.png'))
    print('wrote cw_scope_clear.png')


if __name__ == '__main__':
    build()
