# Prototype (not shipped): "3D Armor"-style netherite knight for EMF, built like those packs are:
# many separate plates at different depths (relief), crisp dark outline on every plate edge,
# metal sheen, cloth tabard for contrast, 2x texture density. Rendered with the showcase renderer.
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'scripts'))
from PIL import Image, ImageDraw
from showcase import rot, mv, render, SHADE, PARTS, POSE, SKIN, BG, label, box_quads
from palette import cycle

VIVID = [(80,220,255),(120,175,255),(170,140,255),(220,130,255),(255,125,220),
         (255,150,175),(255,190,135),(255,228,120),(175,248,135),(110,245,205)]
WHITE = (255, 255, 255)
def mix(a, b, f): return tuple(a[k] + (b[k] - a[k]) * f for k in range(3))
def C(c, a=255): return tuple(int(max(0, min(255, round(v)))) for v in c[:3]) + (a,)
def cyc(t): return cycle(t, VIVID)
RES = 2

MAT = dict(out=(18, 10, 40), lo=(30, 20, 70), hi=(98, 72, 166), spec=(214, 206, 255),
           cloth_lo=(150, 110, 220), cloth_hi=(250, 190, 235), gem=((110, 235, 255), (255, 130, 220)))

def plate(w, h, face, kind, seed):
    """paint one face (w x h texels): outline, bevel, gradient, sheen, aurora trim"""
    im = Image.new('RGBA', (w, h))
    for j in range(h):
        for i in range(w):
            f = 1 - j / max(1, h - 1) * 0.55
            if face in ('west', 'east'): f *= 0.85
            if face == 'up': f = 1.1
            if face == 'down': f = 0.45
            if kind == 'cloth':
                c = mix(MAT['cloth_lo'], MAT['cloth_hi'], 1 - j / max(1, h - 1))
                if i % 4 == 1: c = mix(c, (60, 30, 110), 0.25)       # folds
                if i % 4 == 2: c = mix(c, WHITE, 0.12)
                if j >= h - 2: c = cyc(i / w * 0.6)
            else:
                c = mix(MAT['lo'], MAT['hi'], max(0, min(1, f)))
                d = (i + j * 0.9) / max(1, w + h * 0.9)             # one soft diagonal sheen per face
                k = max(0, 1 - abs(d - 0.32) / 0.09)
                if face not in ('down',):
                    c = mix(c, MAT['spec'], 0.5 * k)
            # bevel + outline (every plate edge gets the crisp dark line)
            if i == 0 or j == 0 or i == w - 1 or j == h - 1:
                c = MAT['out']
            elif kind != 'cloth' and (i == 1 or j == 1):
                c = mix(c, WHITE, 0.35)
            elif kind != 'cloth' and (i == w - 2 or j == h - 2):
                c = mix(cyc(i / w * 0.5 + seed * 0.13), c, 0.25) if kind == 'trim' else mix(c, MAT['out'], 0.4)
            im.putpixel((i, j), C(c))
    return im

class Atlas:
    def __init__(self, w=256, h=256):
        self.im = Image.new('RGBA', (w, h)); self.x = self.y = self.row = 0
    def alloc(self, tw, th):
        if self.x + tw > self.im.width:
            self.x, self.y, self.row = 0, self.y + self.row, 0
        u, v = self.x, self.y; self.x += tw; self.row = max(self.row, th)
        return u, v

def cube(atlas, mn, size, kind='plate', extra=None, seed=0):
    """allocate + paint box-UV region (RES texels per unit); returns (uv, mn, size)"""
    w, h, d = [max(1, round(s * RES)) for s in size]
    u, v = atlas.alloc(2 * (w + d), d + h)
    rects = {'up': (u + d, v, w, d), 'down': (u + d + w, v, w, d), 'west': (u, v + d, d, h),
             'north': (u + d, v + d, w, h), 'east': (u + d + w, v + d, d, h), 'south': (u + 2 * d + w, v + d, w, h)}
    for face, (x, y, fw, fh) in rects.items():
        atlas.im.paste(plate(fw, fh, face, kind, seed), (x, y))
    if extra:
        extra(atlas.im, rects)
    return (u, v), mn, size

def gem_at(cx, cy, r=2):
    def f(im, rects):
        x0, y0, fw, fh = rects['north']
        X, Y = x0 + int(cx * fw), y0 + int(cy * fh)
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if abs(dx) + abs(dy) <= r:
                    c = MAT['out'] if abs(dx) + abs(dy) == r else mix(*MAT['gem'], (dy + r) / (2 * r))
                    im.putpixel((X + dx, Y + dy), C(c))
        im.putpixel((X - 1, Y - 1), C(WHITE))
    return f

def visor(im, rects):
    x0, y0, fw, fh = rects['north']
    for j in range(int(fh * 0.38), int(fh * 0.5)):           # eye slit
        for i in range(2, fw - 2):
            im.putpixel((x0 + i, y0 + j), C((6, 2, 16)))
    for j in range(int(fh * 0.5), fh - 3):                     # breathing slit
        for i in (fw // 2 - 1, fw // 2):
            im.putpixel((x0 + i, y0 + j), C((6, 2, 16)))
    for i in range(2, fw - 2):                                 # aurora glow behind the eyes
        im.putpixel((x0 + i, y0 + int(fh * 0.38) + 1), C(cyc(i / fw * 0.4 + 0.1)))

def star(im, rects):
    x0, y0, fw, fh = rects['north']
    cx, cy = x0 + fw // 2, y0 + fh // 3
    for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (2, 0), (-2, 0), (0, 2), (0, -2)):
        im.putpixel((cx + dx, cy + dy), C(WHITE if (dx, dy) == (0, 0) else mix(WHITE, cyc(0.5), 0.5)))

def build():
    A = Atlas()
    m = {}
    m['head'] = [cube(A, (-5, -9, -5), (10, 9.5, 10), extra=visor, seed=1),
                 cube(A, (-0.75, -12.5, -4.5), (1.5, 4, 10), 'trim', seed=2),              # crest
                 cube(A, (-5.8, -7.5, -5.8), (11.6, 1.5, 1.2), 'trim', extra=gem_at(0.5, 0.5, 1), seed=3),
                 cube(A, (-0.6, -11.5, 5), (1.2, 1.5, 2.5), 'cloth', seed=15),                       # plume tail
                 cube(A, (-0.6, -10.5, 7), (1.2, 1.5, 2), 'cloth', seed=16),
                 cube(A, (-0.6, -9.2, 8.5), (1.2, 2, 1.5), 'cloth', seed=17)]
    m['body'] = [cube(A, (-4.8, -0.3, -2.8), (9.6, 9, 5.6), seed=4),
                 cube(A, (-4, 0.5, -4), (8, 6.5, 1.2), 'trim', extra=gem_at(0.5, 0.4, 2), seed=5),  # breastplate
                 cube(A, (-5.3, 8.5, -3.3), (10.6, 2, 6.6), 'trim', seed=6),                         # belt
                 cube(A, (-2.5, 10.5, -3.6), (5, 8, 1), 'cloth', extra=star, seed=7),                # tabard
                 cube(A, (-2.5, 10.5, 2.6), (5, 8, 1), 'cloth', seed=8)]
    for side, sx in (('right_arm', 1), ('left_arm', -1)):
        def X(x0, w): return (x0, w) if sx == 1 else (-x0 - w + (0 if True else 0), w)
        a0, aw = X(-3.6, 4.6); p0, pw = X(-4.8, 6.6); q0, qw = X(-4.4, 5.8)
        m[side] = [cube(A, (a0 if sx == 1 else -1.0, -2.4, -2.6), (4.6, 10, 5.2), seed=9),
                   cube(A, (p0 if sx == 1 else -1.8, -4, -3.6), (6.6, 2.6, 7.2), 'trim', seed=10),   # pauldron
                   cube(A, (q0 if sx == 1 else -1.4, -1.8, -3.2), (5.8, 2.2, 6.4), seed=11),
                   cube(A, (-3.7 if sx == 1 else -1.3, 6.5, -2.7), (5, 2.5, 5.4), 'trim', seed=18)]   # gauntlet cuff
    for side in ('right_leg', 'left_leg'):
        m[side] = [cube(A, (-2.6, -0.4, -2.6), (5.2, 12.6, 5.2), seed=12),
                   cube(A, (-2.9, 3.6, -3.6), (5.8, 3, 1.4), 'trim', seed=13),                    # knee
                   cube(A, (-2.9, 8.6, -2.9), (5.8, 1.6, 5.8), 'trim', seed=14)]                  # boot cuff
    return A.im, m

def scaled_box(tex, uv, mn, size, pivot, R):
    """like showcase.box_quads but with RES texels per unit"""
    w, h, d = [max(1, round(s * RES)) for s in size]
    big = Image.new('RGBA', (tex.width, tex.height)); big.paste(tex)
    q = box_quads(tex, uv, (0, 0, 0), (w, h, d), 0, (0, 0, 0), None, False)
    out = []
    sx, sy, sz = size[0] / w, size[1] / h, size[2] / d
    for corners, n, c, shade in q:
        cs = [(mn[0] + p[0] * sx, mn[1] + p[1] * sy, mn[2] + p[2] * sz) for p in corners]
        cs = [tuple(pivot[k] + r[k] for k in range(3)) for r in (mv(R, p) for p in cs)]
        out.append((cs, mv(R, n), c, shade))
    return out

if __name__ == '__main__':
    tex, model = build()
    quads = []
    R = {k: rot(*POSE[k]) for k in PARTS}
    for k, (pv, mn, sz, uv, mir) in PARTS.items():
        quads += box_quads(None, uv, mn, sz, 0, pv, R[k], mir, solid=SKIN)
    for k, cubes in model.items():
        for uv, mn, size in cubes:
            quads += scaled_box(tex, uv, mn, size, PARTS[k][0], R[k])
    W, H = 360, 480
    sheet = Image.new('RGBA', (3 * W + 300, H + 60), BG)
    for i, yaw in enumerate((0.55, -0.5, math.pi + 0.6)):
        sheet.alpha_composite(render(quads, yaw, scale=11, size=(W, H), origin=(W // 2, 150)), (i * W, 40))
    t = tex.crop(tex.getbbox()); sheet.alpha_composite(t.resize((t.width, t.height), Image.NEAREST), (3 * W + 20, 60))
    label(sheet, (12, 10), 'Prototipo: caballero de netherita (placas en relieve, contorno, brillo metálico, tabardo) — NO está en el pack', 18)
    sheet.save(os.path.join(HERE, 'knight_preview.png'))
    tex.save(os.path.join(HERE, 'knight_atlas.png'))
    print('ok')
