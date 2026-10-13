"""EMP Launcher projectile: a ball of blue energy.  Nested additive spheres drawn inside-out (the thermal detonator's
glow technique, build_thermal.add_glow): every shell adds its far side, so the ball is brightest in the middle and fades
to its edge from every angle.  Model weapon_cw_empball (rigid, tag_origin), material mtl_cw_emp_ball."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xme

B = paths.BUILD
RADIUS = 4.5                     # inches
SHELLS = tuple(0.25 + 0.75 * (i / 9.0) ** 1.2 for i in range(10))
RGB = (3, 9, 30)                 # one shell; additive renders far brighter than the 8-bit value


def build():
    m = {'bones': [{'name': 'tag_origin', 'parent': -1, 'offset': np.zeros(3), 'rot': np.eye(3)}],
         'verts': [], 'faces': [], 'objects': ['empball'], 'materials': [('mtl_cw_emp_ball', 'Phong', 'cw_emp_ball_c.tga')]}
    seg, rings = 14, 9
    for k in SHELLS:
        R = RADIUS * k
        base = len(m['verts'])
        for i in range(rings + 1):
            th = np.pi * i / rings
            for j in range(seg):
                ph = 2 * np.pi * j / seg
                m['verts'].append((np.array([np.sin(th) * np.cos(ph), np.sin(th) * np.sin(ph), np.cos(th)]) * R, [(0, 1.0)]))

        def corner(i, j):
            v = base + i * seg + (j % seg)
            return (v, m['verts'][v][0] / R, (0.5, 0.5))

        for i in range(rings):
            for j in range(seg):
                a, b, c, d = corner(i, j), corner(i, j + 1), corner(i + 1, j + 1), corner(i + 1, j)
                if i > 0:
                    m['faces'].append((0, 0, [a, b, c]))
                if i < rings - 1:
                    m['faces'].append((0, 0, [a, c, d]))
    xme.write(os.path.join(B, 'model_export', 'weapon_cw_empball.XMODEL_EXPORT'), m, 'waw-clone-wars: EMP ball')
    os.makedirs(os.path.join(B, 'textures'), exist_ok=True)
    Image.new('RGB', (8, 8), RGB).save(os.path.join(B, 'textures', 'cw_emp_ball.png'))
    print('weapon_cw_empball: %d shells, %d tris' % (len(SHELLS), len(m['faces'])))


if __name__ == '__main__':
    build()
