# Preview renderer for OptiFine/EMF .jem armor models (as used by 3D armor packs), drawn with the
# showcase renderer so third-party packs can be judged before installing them.
#   python3 jem_preview.py <pack_root> <out.png> [materials...]
import os, sys, json, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'scripts'))
from PIL import Image
from showcase import rot, mv, render, SHADE, PARTS, POSE, SKIN, BG, label, box_quads

def face_quads(tex, ts, rect, pt, n, R, pivot, shade_name):
    u1, v1, u2, v2 = rect
    sx, sy = tex.width / ts[0], tex.height / ts[1]
    W, H = abs(u2 - u1), abs(v2 - v1)
    out = []
    nx, ny = max(1, round(W * sx)), max(1, round(H * sy))
    for j in range(ny):
        for i in range(nx):
            tu = (u1 + (u2 - u1) * (i + 0.5) / nx) * sx
            tv = (v1 + (v2 - v1) * (j + 0.5) / ny) * sy
            c = tex.getpixel((min(tex.width - 1, int(tu)), min(tex.height - 1, int(tv))))
            if c[3] < 8:
                continue
            a, b, a2, b2 = i / nx, j / ny, (i + 1) / nx, (j + 1) / ny
            cs = [pt(a, b), pt(a2, b), pt(a2, b2), pt(a, b2)]
            cs = [tuple(pivot[k] + r[k] for k in range(3)) for r in (mv(R, p) for p in cs)]
            out.append((cs, mv(R, n), c, SHADE[shade_name]))
    return out

def box(tex, ts, b, T, Rpart, pivot, Rsub, subpivot, mirror):
    x, y, z, w, h, d = b['coordinates']
    g = b.get('sizeAdd', 0)
    # CEM inverted space -> vanilla space relative to the part pivot
    x0, x1 = -(T[0] + x + w) - g, -(T[0] + x) + g
    y0, y1 = -(T[1] + y + h) - g, -(T[1] + y) + g
    z0, z1 = T[2] + z - g, T[2] + z + d + g
    def place(p):        # submodel rotation about its pivot, then part rotation about the part pivot
        q = tuple(p[k] - subpivot[k] for k in range(3)); q = mv(Rsub, q)
        return tuple(q[k] + subpivot[k] for k in range(3))
    faces = {
        'north': (lambda a, c: (x0 + (x1 - x0) * a, y0 + (y1 - y0) * c, z0), (0, 0, -1)),
        'south': (lambda a, c: (x1 - (x1 - x0) * a, y0 + (y1 - y0) * c, z1), (0, 0, 1)),
        'west': (lambda a, c: (x0, y0 + (y1 - y0) * c, z1 - (z1 - z0) * a), (-1, 0, 0)),
        'east': (lambda a, c: (x1, y0 + (y1 - y0) * c, z0 + (z1 - z0) * a), (1, 0, 0)),
        'up': (lambda a, c: (x0 + (x1 - x0) * a, y0, z1 - (z1 - z0) * c), (0, -1, 0)),
        'down': (lambda a, c: (x0 + (x1 - x0) * a, y1, z0 + (z1 - z0) * c), (0, 1, 0)),
    }
    if 'textureOffset' in b:
        u, v = b['textureOffset']
        rects = {'up': (u + d, v, u + d + w, v + d), 'down': (u + d + w, v, u + d + 2 * w, v + d),
                 'west': (u, v + d, u + d, v + d + h), 'north': (u + d, v + d, u + d + w, v + d + h),
                 'east': (u + d + w, v + d, u + 2 * d + w, v + d + h), 'south': (u + 2 * d + w, v + d, u + 2 * d + 2 * w, v + d + h)}
        # vanilla x is CEM -x: the CEM "east" side is the vanilla west side
        rects['west'], rects['east'] = rects['east'], rects['west']
        if mirror:
            rects = {k: (r[2], r[1], r[0], r[3]) for k, r in rects.items()}
            rects['west'], rects['east'] = rects['east'], rects['west']
    else:
        m = {'north': 'uvNorth', 'south': 'uvSouth', 'west': 'uvEast', 'east': 'uvWest', 'up': 'uvUp', 'down': 'uvDown'}
        rects = {k: b[v] for k, v in m.items() if v in b}
    out = []
    for name, rect in rects.items():
        f, n = faces[name]
        pt = lambda a, c, f=f: place(f(a, c))
        out += face_quads(tex, ts, rect, pt, mv(Rsub, n), Rpart, pivot, name)
    return out

def walk(node, tex, ts, T, Rpart, pivot, Rsub, subpivot, mirror):
    T = tuple(T[k] + node.get('translate', [0, 0, 0])[k] for k in range(3))
    mirror = mirror or node.get('mirrorTexture') == 'u'
    r = node.get('rotate')
    if r:
        sp = (-T[0], -T[1], T[2])
        Rn = rot(math.radians(-r[0]), math.radians(-r[1]), math.radians(r[2]))
        # compose with the parent submodel rotation (about its own pivot)
        Rsub = tuple(tuple(sum(Rsub[i][k] * Rn[k][j] for k in range(3)) for j in range(3)) for i in range(3))
        subpivot = sp
    q = []
    for b in node.get('boxes', []):
        q += box(tex, ts, b, T, Rpart, pivot, Rsub, subpivot, mirror)
    for s in node.get('submodels', []):
        q += walk(s, tex, ts, T, Rpart, pivot, Rsub, subpivot, mirror)
    return q

def figure(root, mat):
    q = []
    R = {k: rot(*POSE[k]) for k in PARTS}
    for k, (pv, mn, sz, uv, mir) in PARTS.items():
        q += box_quads(None, uv, mn, sz, 0, pv, R[k], mir, solid=SKIN)
    cem = os.path.join(root, 'assets/minecraft/optifine/cem/')
    eq = os.path.join(root, 'assets/minecraft/textures/entity/equipment/')
    for piece, layer in (('helmet', 'humanoid'), ('chestplate', 'humanoid'), ('leggings', 'humanoid_leggings'), ('boots', 'humanoid')):
        jem = json.load(open(cem + 'player_%s.jem' % piece))
        tex = Image.open(eq + '%s/%s.png' % (layer, mat)).convert('RGBA')
        ts = jem.get('textureSize', [64, 32])
        for m in jem['models']:
            part = {'headwear': 'head'}.get(m['part'], m['part'])
            q += walk(m, tex, ts, (0, 0, 0), R[part], PARTS[part][0], rot(0, 0, 0), (0, 0, 0), False)
    return q

if __name__ == '__main__':
    root, out = sys.argv[1], sys.argv[2]
    mats = sys.argv[3:] or ['diamond', 'netherite', 'iron', 'gold']
    W, H = 300, 420
    sheet = Image.new('RGBA', (len(mats) * 2 * W + 20, H + 60), BG)
    for i, mat in enumerate(mats):
        q = figure(root, mat)
        sheet.alpha_composite(render(q, 0.55), (10 + i * 2 * W, 40))
        sheet.alpha_composite(render(q, math.pi + 0.6), (10 + i * 2 * W + W, 40))
        label(sheet, (20 + i * 2 * W, 10), mat, 20)
    sheet.save(out)
    print('ok')
