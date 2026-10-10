# Drawing helpers and the per-screen themes of Aurora HUD XL (used by menus_xl.py).
# A theme gives the frame band, panel background, slot colours, how vanilla decorations are recoloured
# and the ornaments that stick out of the vanilla rectangle (crests, corner pieces, side details).
import math, random
from PIL import Image, ImageDraw
from hud_xl import cyc, mix, C, over, put, star, OUT, WHITE

rnd = random.Random

# ------------------------------------------------------------------ masks + shading
def mask_draw(size, fn):
    m = Image.new('L', size); fn(ImageDraw.Draw(m))
    px = m.load()
    return {(x, y) for y in range(size[1]) for x in range(size[0]) if px[x, y] > 127}

def poly(size, pts): return mask_draw(size, lambda d: d.polygon([tuple(p) for p in pts], fill=255))
def ellipse(size, cx, cy, rx, ry): return mask_draw(size, lambda d: d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=255))
def rect(size, x0, y0, x1, y1): return {(x, y) for y in range(max(0, y0), min(size[1], y1 + 1)) for x in range(max(0, x0), min(size[0], x1 + 1))}

def star_pts(cx, cy, ro, ri, n, rot=-math.pi / 2):
    return [(cx + (ro if k % 2 == 0 else ri) * math.cos(rot + k * math.pi / n),
             cy + (ro if k % 2 == 0 else ri) * math.sin(rot + k * math.pi / n)) for k in range(2 * n)]

def gear(size, cx, cy, r, teeth, rot=0.0, hole=0.0):
    pts = []
    for k in range(teeth * 4):
        a = rot + k * 2 * math.pi / (teeth * 4)
        rr = r if (k % 4) in (0, 1) else r - max(2, r * 0.22)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    m = poly(size, pts)
    if hole: m -= ellipse(size, cx, cy, hole, hole)
    return m

def edge_of(m):
    return {(x, y) for (x, y) in m if any((x + dx, y + dy) not in m for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}

def paint(img, m, colfn, line=OUT, bevel=True):
    """fill a mask: outline + bevel (light top-left, dark bottom-right) + colour function"""
    e = edge_of(m)
    for (x, y) in m:
        if not (0 <= x < img.width and 0 <= y < img.height): continue
        if line is not None and (x, y) in e:
            img.putpixel((x, y), C(line)); continue
        c = colfn(x, y)
        if bevel:
            if (x, y - 1) in e or (x - 1, y) in e: c = mix(c, WHITE, 0.45)
            elif (x, y + 1) in e or (x + 1, y) in e: c = mix(c, OUT, 0.3)
        img.putpixel((x, y), C(c))

def grad(stops, t):
    t = max(0.0, min(1.0, t)) * (len(stops) - 1); i = min(int(t), len(stops) - 2)
    return mix(stops[i], stops[i + 1], t - i)

# ------------------------------------------------------------------ themes
class Theme:
    pads = (14, 20, 14, 10)
    band = [OUT, (150, 140, 200), (210, 205, 240), WHITE, (120, 110, 170), OUT]
    slot = ((70, 60, 120), (225, 220, 250), (40, 32, 80), (28, 22, 60))      # rim tl, rim br, inner top, inner bottom
    def bg(self, x, y, w, h): return (60, 50, 100)
    def feature(self, l, x, w): return mix(cyc(x / w), WHITE, max(0, l - 0.5))
    def window(self, img, cells): pass
    def ornaments(self, img, L, T, w, h): pass
    def motif(self, img, x, y, r): star(img, x, y, 0.8, cyc(r.random()))
    def translucent(self, c, a): return c, a       # colour for vanilla's see-through pixels

class Observatory(Theme):
    band = [OUT, (110, 120, 190), (190, 200, 245), (245, 248, 255), (150, 160, 220), (70, 70, 140), OUT]
    slot = ((70, 70, 140), (200, 205, 250), (36, 30, 84), (22, 18, 56))
    def bg(self, x, y, w, h):
        c = grad([(58, 46, 120), (36, 28, 86), (22, 18, 58)], y / h)
        a = abs(y - (h * 0.42 + 9 * math.sin(x / 23)))
        if a < 7: c = mix(c, cyc(x / w * 0.7 + 0.1), (1 - a / 7) * 0.35)
        if (x * 7 + y * 13) % 97 == 0: c = mix(c, WHITE, 0.8)
        return c
    def window(self, img, cells): magic_sky(img, cells, 3)
    def ornaments(self, img, L, T, w, h):
        S = img.size
        for (cx, cy, r) in ((L - 1, T - 1, 8), (L + w, T - 1, 8), (L - 1, T + h, 7), (L + w, T + h, 7)):
            m = ellipse(S, cx, cy, r, r) - ellipse(S, cx + (3 if cx < L else -3), cy - 2, r - 1, r - 1)
            paint(img, m, lambda x, y: grad([(255, 250, 215), (255, 225, 160)], (y - cy + r) / (2 * r)))
        cx, cy = L + w // 2, T - 7
        paint(img, poly(S, star_pts(cx, cy, 13, 4, 4, rot=-math.pi / 2)), lambda x, y: mix((220, 225, 255), cyc((x + y) / 40), 0.3))
        paint(img, poly(S, star_pts(cx, cy, 9, 3, 4, rot=-math.pi / 4)), lambda x, y: (255, 236, 170))
        paint(img, ellipse(S, cx, cy, 2, 2), lambda x, y: WHITE, line=(200, 150, 80))
        for k, (dx, dy) in enumerate(((-30, -9), (26, -12), (-52, -4), (48, -5), (-18, -15), (14, -16))):
            star(img, cx + dx, T + dy, 0.6 + 0.4 * (k % 2), cyc(k / 6))
        for gx in range(L + 24, L + w - 20, 32):
            paint(img, poly(S, star_pts(gx, T - 2, 4, 1.6, 4)), lambda x, y: (240, 240, 255), line=(70, 70, 140), bevel=False)
            paint(img, poly(S, star_pts(gx, T + h + 1, 4, 1.6, 4)), lambda x, y: (240, 240, 255), line=(70, 70, 140), bevel=False)
    def motif(self, img, x, y, r): star(img, x, y, 0.5 + 0.5 * r.random(), cyc(r.random()))

class Fabricator(Theme):
    band = [(70, 40, 20), (190, 130, 60), (245, 205, 120), (255, 235, 170), (215, 160, 80), (140, 90, 40), (70, 40, 20)]
    slot = ((60, 66, 84), (200, 205, 220), (88, 98, 120), (70, 78, 100))
    def bg(self, x, y, w, h):
        c = grad([(160, 200, 245), (130, 175, 235)], y / h)
        if x % 8 == 0 or y % 8 == 0: c = mix(c, WHITE, 0.25)
        if x % 32 == 0 or y % 32 == 0: c = mix(c, WHITE, 0.45)
        d = math.hypot(x - w * 0.78, y - h * 0.3)
        if abs(d - 18) < 0.6 or abs(d - 11) < 0.6: c = mix(c, WHITE, 0.5)
        return c
    def feature(self, l, x, w): return grad([(120, 80, 40), (230, 180, 90), (255, 240, 180)], l)
    def ornaments(self, img, L, T, w, h):
        S = img.size
        brass = lambda x, y: grad([(255, 230, 160), (220, 165, 80), (160, 105, 45)], (y % 24) / 24)
        steel = lambda x, y: grad([(225, 230, 240), (150, 160, 180)], (y % 20) / 20)
        for (cx, cy, r, t, f) in ((L - 2, T - 2, 11, 9, brass), (L + w + 1, T - 2, 11, 9, brass),
                                  (L - 1, T + h, 8, 8, steel), (L + w, T + h, 8, 8, steel), (L + 14, T - 9, 7, 7, steel)):
            paint(img, gear(S, cx, cy, r, t, rot=cx * 0.1, hole=r * 0.32), f)
        cx, cy = L + w // 2, T - 8
        paint(img, gear(S, cx, cy, 12, 10, hole=4), brass)
        # crossed hammer + wrench over the big gear
        paint(img, poly(S, [(cx - 13, cy + 10), (cx - 11, cy + 12), (cx + 9, cy - 8), (cx + 7, cy - 10)]), lambda x, y: (150, 100, 60))
        paint(img, poly(S, [(cx + 4, cy - 13), (cx + 13, cy - 4), (cx + 10, cy - 1), (cx + 1, cy - 10)]), steel)
        paint(img, poly(S, [(cx + 12, cy + 11), (cx + 14, cy + 9), (cx - 6, cy - 11), (cx - 8, cy - 9)]), steel)
        paint(img, ellipse(S, cx - 9, cy - 11, 4, 4) - ellipse(S, cx - 10, cy - 13, 2, 2), steel)
        for gx in range(L + 6, L + w - 4, 12):
            for gy in (T - 2, T + h + 1):
                put(img, gx, gy, C((255, 240, 190))); put(img, gx + 1, gy + 1, C((120, 80, 40)))
    def motif(self, img, x, y, r):
        paint(img, gear(img.size, x, y, 3, 6, rot=r.random(), hole=1), lambda a, b: (235, 245, 255), line=(90, 120, 180), bevel=False)

class Inferno(Theme):
    pads = (14, 22, 14, 10)
    band = [(90, 20, 50), (220, 120, 60), (255, 215, 120), (255, 250, 220), (255, 180, 110), (180, 60, 80), (90, 20, 50)]
    slot = ((90, 30, 50), (255, 210, 150), (70, 22, 46), (48, 14, 36))
    def bg(self, x, y, w, h):
        c = grad([(255, 196, 170), (240, 130, 140), (160, 50, 100), (100, 24, 72)], y / h)
        if (x * 11 + y * 7) % 83 == 0: c = mix(c, (255, 240, 180), 0.8)
        return c
    def feature(self, l, x, w): return grad([(150, 40, 70), (255, 150, 90), (255, 240, 170)], l)
    def tongue(self, S, fx, base, hgt, wid, lean):
        """teardrop flame: round belly at the base, curling tip"""
        left = [(fx - wid * math.sin(math.pi * min(1, (1 - u) * 1.25)) * (1 - u) ** 0.35 + lean * u * u * wid, base - hgt * u) for u in [i / 10 for i in range(11)]]
        right = [(fx + wid * math.sin(math.pi * min(1, (1 - u) * 1.25)) * (1 - u) ** 0.35 + lean * u * u * wid, base - hgt * u) for u in [i / 10 for i in range(10, -1, -1)]]
        return poly(S, left + right)
    def flames(self, img, L, T, w, S):
        r = rnd(5)
        outer = [(255, 175, 150), (250, 120, 160), (215, 75, 170)]
        core = [(255, 255, 240), (255, 235, 150), (255, 190, 120)]
        for fx in range(L - 4, L + w + 5, 10):
            mid = 1 - min(1, abs(fx - (L + w / 2)) / (w / 2))
            hgt = r.randint(10, 15) + int(6 * mid)
            lean = r.choice((-0.7, 0.7))
            m = self.tongue(S, fx, T + 2, hgt, 6.5, lean)
            paint(img, m, lambda x, y, t0=T + 2 - hgt, hh=hgt: grad(outer, 1 - (y - t0) / hh), line=(120, 30, 90), bevel=False)
            c = self.tongue(S, fx + lean, T + 2, hgt * 0.62, 3.4, lean)
            paint(img, c, lambda x, y, t0=T + 2 - hgt * 0.62, hh=hgt * 0.62: grad(core, 1 - (y - t0) / hh), line=None, bevel=False)
    def feather_wing(self, img, S, bx, by, side):
        """angel wing of five feathers fanning out of the top corner"""
        for k in range(5):
            ang = math.radians(200 - k * 17) if side < 0 else math.radians(-20 + k * 17)
            ln = 19 - k * 2.0; wd = 3.0
            ux, uy = math.cos(ang), math.sin(ang); nx, ny = -uy, ux
            pts = [(bx + nx * wd * 0.6, by + ny * wd * 0.6), (bx + ux * ln * 0.55 + nx * wd, by + uy * ln * 0.55 + ny * wd),
                   (bx + ux * ln, by + uy * ln), (bx + ux * ln * 0.55 - nx * wd, by + uy * ln * 0.55 - ny * wd),
                   (bx - nx * wd * 0.6, by - ny * wd * 0.6)]
            paint(img, poly(S, pts), lambda x, y, k=k: mix((255, 255, 255), (255, 225, 200), k / 6), line=(180, 130, 170), bevel=False)
    def ornaments(self, img, L, T, w, h):
        S = img.size
        for side in (-1, 1):
            self.feather_wing(img, S, L - 1 if side < 0 else L + w, T - 1, side)
        self.flames(img, L, T, w, S)
        cx = L + w // 2
        halo = ellipse(S, cx, 3, 13, 3) - ellipse(S, cx, 3, 10, 1)
        paint(img, halo, lambda x, y: (255, 236, 150), line=(200, 140, 60), bevel=False)
        for side in (-1, 1):
            for k in range(3):                                 # flame tongues down the sides
                fy = T + h - 10 - k * 14
                x0 = L - 1 if side < 0 else L + w
                paint(img, poly(S, [(x0, fy - 4), (x0, fy + 4), (x0 + side * (8 + k * 2), fy - 2 - k)]),
                      lambda x, y: (255, 190, 150), line=(130, 30, 80), bevel=False)
    def motif(self, img, x, y, r):
        for dx, dy, c in ((0, 0, (255, 245, 200)), (0, -1, (255, 200, 140)), (1, 0, (255, 160, 150))):
            over(img, x + dx, y + dy, c, 0.9)

class Supernova(Theme):
    band = [(20, 20, 40), (90, 100, 130), (170, 180, 205), (120, 255, 250), (170, 180, 205), (80, 86, 115), (20, 20, 40)]
    slot = ((40, 44, 64), (130, 240, 255), (54, 58, 80), (36, 38, 58))
    def bg(self, x, y, w, h):
        c = grad([(78, 82, 104), (52, 56, 76)], y / h)
        if x % 44 == 0 or y % 30 == 0: c = mix(c, (24, 26, 40), 0.6)
        if (x % 44 in (2, 41)) and (y % 30 in (3, 27)): c = (180, 190, 210)
        crack = abs((y - 0.5 * x - 20) % 70 - 35)
        if crack < 0.8: c = mix(c, (140, 255, 250), 0.6)
        return c
    def feature(self, l, x, w): return grad([(40, 50, 90), (140, 200, 255), (240, 255, 255)], l)
    def ornaments(self, img, L, T, w, h):
        S = img.size
        cx, cy = L + w // 2, T - 7
        paint(img, poly(S, star_pts(cx, cy, 17, 5, 8)), lambda x, y: mix((200, 160, 255), (120, 240, 255), (x - cx + 17) / 34), line=(60, 40, 110), bevel=False)
        paint(img, poly(S, star_pts(cx, cy, 10, 4, 8, rot=-math.pi / 2 + math.pi / 8)), lambda x, y: (235, 250, 255), line=(80, 160, 220), bevel=False)
        paint(img, ellipse(S, cx, cy, 3, 3), lambda x, y: WHITE, line=(150, 230, 255), bevel=False)
        steel = lambda x, y: grad([(220, 226, 240), (130, 140, 165)], 0.5)
        for (bx, by) in ((L - 1, T - 1), (L + w, T - 1), (L - 1, T + h), (L + w, T + h)):
            paint(img, poly(S, star_pts(bx, by, 7, 7 * 0.87, 3, rot=0)), steel)
            paint(img, ellipse(S, bx, by, 2, 2), lambda x, y: (150, 255, 250), line=(40, 80, 110), bevel=False)
        for side in (-1, 1):                                   # glowing vents
            x0 = L - 10 if side < 0 else L + w + 2
            for k in range(4):
                vy = T + 30 + k * 30
                paint(img, rect(S, x0, vy, x0 + 7, vy + 4), lambda x, y: (60, 64, 88))
                for xx in range(x0 + 1, x0 + 7): put(img, xx, vy + 2, C((140, 255, 250)))
    def motif(self, img, x, y, r):
        over(img, x, y, (160, 255, 250), 0.9); over(img, x + 1, y, (120, 200, 255), 0.6); over(img, x, y + 1, (120, 200, 255), 0.6)

class Clouds(Theme):
    pads = (14, 22, 14, 10)
    band = [(120, 100, 170), (230, 215, 245), (255, 250, 255), (250, 235, 245), (210, 190, 230), (120, 100, 170)]
    slot = ((170, 150, 210), (255, 255, 255), (238, 230, 252), (222, 212, 246))
    def bg(self, x, y, w, h):
        c = grad([(205, 215, 255), (235, 210, 245), (255, 220, 215)], y / h)
        for (ox, oy, r) in ((30, 40, 14), (140, 70, 18), (80, 130, 16), (20, 110, 10)):
            if math.hypot((x - ox) * 0.6, y - oy) < r: c = mix(c, WHITE, 0.35)
        return c
    def cloud(self, img, S, cx, cy, s):
        m = set()
        for dx, dy, r in ((-1.1, 0.3, 0.55), (0, 0, 0.75), (1.1, 0.25, 0.6), (0.5, -0.5, 0.55), (-0.5, -0.35, 0.5)):
            m |= ellipse(S, cx + dx * s, cy + dy * s, r * s, r * s)
        paint(img, m, lambda x, y: grad([(255, 255, 255), (240, 225, 250), (220, 200, 240)], (y - cy + s) / (2 * s)), line=(150, 130, 200))
    def ornaments(self, img, L, T, w, h):
        S = img.size
        for i, (fx, fy, s) in enumerate(((L + 8, T - 6, 9), (L + 40, T - 3, 7), (L + w - 8, T - 6, 9), (L + w - 40, T - 3, 7),
                                         (L - 3, T + h - 6, 7), (L + w + 2, T + h - 6, 7), (L - 4, T + 60, 6), (L + w + 3, T + 70, 6))):
            self.cloud(img, S, fx, fy, s)
        cx = L + w // 2
        for k, off in enumerate((-14, 0, 14)):                 # smoke puffs rising and curling
            for j, (dy, rr_) in enumerate(((4, 3.2), (9, 2.8), (13, 2.3), (17, 1.8))):
                px_ = cx + off + 3 * math.sin(j * 1.3 + k * 2)
                paint(img, ellipse(S, px_, T - 1 - dy, rr_, rr_), lambda x, y, j=j: mix((255, 255, 255), (225, 210, 245), j / 4),
                      line=(170, 150, 210), bevel=False)
        m = ellipse(S, cx + 30, 6, 5, 5) - ellipse(S, cx + 32, 4, 4, 4)
        paint(img, m, lambda x, y: (255, 245, 200), line=(190, 160, 110), bevel=False)
    def motif(self, img, x, y, r):
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, -1), (1, -1)): over(img, x + dx, y + dy, WHITE, 0.55)

# ------------------------------------------------------------------ cloudy family (the user's favourite look)
# The smoker's style for any screen: pastel sky gradient with soft cloud puffs, light slots, pearl frame and clouds
# sticking out of the corners. Each screen keeps its own sky tint and a small emblem of what it does on top.
LAV = (150, 130, 200)                        # outline lavender shared by the whole family

def cloud_puff(img, S, cx, cy, s, line=LAV):
    m = set()
    for dx, dy, r in ((-1.1, 0.3, 0.55), (0, 0, 0.75), (1.1, 0.25, 0.6), (0.5, -0.5, 0.55), (-0.5, -0.35, 0.5)):
        m |= ellipse(S, cx + dx * s, cy + dy * s, r * s, r * s)
    paint(img, m, lambda x, y: grad([(255, 255, 255), (240, 225, 250), (220, 200, 240)], (y - cy + s) / (2 * s)), line=line)

# emblems: (img, S, cx, cy, theme) -> small pastel drawing centred on (cx, cy), about 20 px wide
def em_lock(img, S, cx, cy, t):
    paint(img, ellipse(S, cx, cy - 3, 5, 5) - ellipse(S, cx, cy - 3, 3, 3), lambda x, y: (230, 220, 245), line=LAV, bevel=False)
    paint(img, rect(S, int(cx - 6), int(cy - 1), int(cx + 6), int(cy + 7)), lambda x, y: (255, 232, 170), line=(190, 150, 90))
    paint(img, rect(S, int(cx), int(cy + 1), int(cx), int(cy + 4)), lambda x, y: (150, 110, 70), line=None, bevel=False)

def em_shell(img, S, cx, cy, t):
    paint(img, ellipse(S, cx, cy + 2, 9, 7) - rect(S, int(cx - 10), int(cy + 3), int(cx + 10), int(cy + 12)),
          lambda x, y: (232, 210, 250), line=LAV)
    paint(img, rect(S, int(cx - 7), int(cy + 3), int(cx + 7), int(cy + 6)), lambda x, y: (215, 190, 240), line=LAV, bevel=False)
    paint(img, ellipse(S, cx, cy - 1, 2, 2), lambda x, y: (190, 240, 200), line=None, bevel=False)

def em_anvil(img, S, cx, cy, t):
    paint(img, poly(S, [(cx - 9, cy - 4), (cx + 7, cy - 4), (cx + 9, cy - 2), (cx + 3, cy), (cx + 3, cy + 3), (cx + 6, cy + 6),
                        (cx - 6, cy + 6), (cx - 3, cy + 3), (cx - 3, cy), (cx - 7, cy - 1)]), lambda x, y: (225, 222, 245), line=LAV)

def em_flask(img, S, cx, cy, t):
    paint(img, ellipse(S, cx, cy + 3, 5.5, 5.5) | rect(S, int(cx - 2), int(cy - 7), int(cx + 2), int(cy - 1)),
          lambda x, y: (170, 240, 220) if y > cy + 2 else (235, 250, 252), line=(90, 160, 160))
    paint(img, rect(S, int(cx - 3), int(cy - 9), int(cx + 3), int(cy - 7)), lambda x, y: (220, 180, 150), line=None, bevel=False)

def em_arrow(img, S, cx, cy, t):
    paint(img, rect(S, int(cx - 8), int(cy), int(cx + 4), int(cy + 1)), lambda x, y: (230, 225, 250), line=None, bevel=False)
    paint(img, poly(S, [(cx + 9, cy + 0.5), (cx + 3, cy - 4), (cx + 3, cy + 5)]), lambda x, y: (255, 255, 255), line=LAV, bevel=False)
    paint(img, poly(S, [(cx - 8, cy + 0.5), (cx - 11, cy - 3), (cx - 6, cy - 3)]), lambda x, y: (255, 180, 210), line=None, bevel=False)
    paint(img, poly(S, [(cx - 8, cy + 0.5), (cx - 11, cy + 4), (cx - 6, cy + 4)]), lambda x, y: (180, 220, 255), line=None, bevel=False)

def em_book(img, S, cx, cy, t):
    paint(img, poly(S, [(cx, cy - 2), (cx - 10, cy - 5), (cx - 10, cy + 4), (cx, cy + 7)]), lambda x, y: (255, 252, 245), line=LAV)
    paint(img, poly(S, [(cx, cy - 2), (cx + 10, cy - 5), (cx + 10, cy + 4), (cx, cy + 7)]), lambda x, y: (245, 238, 252), line=LAV)
    paint(img, poly(S, star_pts(cx, cy - 8, 3.5, 1.4, 4)), lambda x, y: (220, 190, 255), line=None, bevel=False)

def em_wheel(img, S, cx, cy, t):
    paint(img, ellipse(S, cx, cy, 7, 7) - ellipse(S, cx, cy, 2, 2), lambda x, y: (238, 232, 248), line=LAV)
    paint(img, ellipse(S, cx, cy, 4.5, 4.5) - ellipse(S, cx, cy, 3.5, 3.5), lambda x, y: (215, 200, 240), line=None, bevel=False)

def em_funnel(img, S, cx, cy, t):
    paint(img, poly(S, [(cx - 9, cy - 5), (cx + 9, cy - 5), (cx + 2, cy + 2), (cx + 2, cy + 6), (cx - 2, cy + 6), (cx - 2, cy + 2)]),
          lambda x, y: (225, 225, 248), line=LAV)
    for k, dx in enumerate((-6, 0, 6)):
        paint(img, poly(S, star_pts(cx + dx, cy - 9 - (k % 2) * 2, 2.5, 1, 4)), lambda x, y: WHITE, line=None, bevel=False)

def em_horseshoe(img, S, cx, cy, t):
    paint(img, (ellipse(S, cx, cy, 7, 7) - ellipse(S, cx, cy, 4, 4)) - rect(S, int(cx - 3), int(cy + 2), int(cx + 3), int(cy + 8)),
          lambda x, y: (255, 230, 170), line=(190, 150, 90))

def em_nautilus(img, S, cx, cy, t):
    paint(img, ellipse(S, cx, cy, 7, 6.5), lambda x, y: (255, 225, 215), line=(200, 140, 150))
    for r in (4.5, 2.5):
        paint(img, ellipse(S, cx + 1, cy - 0.5, r, r) - ellipse(S, cx + 1, cy - 0.5, r - 1, r - 1), lambda x, y: (220, 150, 160), line=None, bevel=False)

def em_crown(img, S, cx, cy, t):
    paint(img, poly(S, [(cx - 9, cy + 5), (cx - 9, cy - 4), (cx - 4, cy), (cx, cy - 7), (cx + 4, cy), (cx + 9, cy - 4), (cx + 9, cy + 5)]),
          lambda x, y: (255, 232, 170), line=(190, 150, 90))
    for dx in (-9, 0, 9):
        paint(img, ellipse(S, cx + dx, cy - 5 - (2 if dx == 0 else 0), 1.6, 1.6), lambda x, y: (200, 230, 255), line=None, bevel=False)

def em_gem(img, S, cx, cy, t):
    paint(img, poly(S, [(cx - 7, cy - 2), (cx - 3, cy - 6), (cx + 3, cy - 6), (cx + 7, cy - 2), (cx, cy + 7)]),
          lambda x, y: mix((215, 200, 255), WHITE, max(0, (cy - y) / 10)), line=LAV)

class Cloudy(Theme):
    pads = (14, 22, 14, 10)
    def __init__(self, sky, emblem=None, seed=0):
        self.sky, self.emblem = sky, emblem
        self.band = [(120, 100, 170), mix(sky[0], WHITE, 0.55), (255, 250, 255), mix(sky[2], WHITE, 0.5),
                     mix(sky[1], LAV, 0.35), (120, 100, 170)]
        self.slot = ((170, 150, 210), (255, 255, 255), mix(sky[0], WHITE, 0.62), mix(sky[1], WHITE, 0.5))
        rr = random.Random(seed)
        self.puffs = [(rr.uniform(10, 170), rr.uniform(25, 150), rr.uniform(9, 17)) for _ in range(4)]
    def bg(self, x, y, w, h):
        c = grad(self.sky, y / h)
        for (ox, oy, r) in self.puffs:
            if math.hypot((x - ox) * 0.6, y - oy) < r: c = mix(c, WHITE, 0.35)
        return c
    def feature(self, l, x, w):                    # vanilla arrows / icons / panels: soft lavender on the light sky
        return grad([(120, 100, 170), LAV, mix(self.sky[1], WHITE, 0.35), WHITE], l)
    def window(self, img, cells):                  # entity windows (player, horse...): a bright patch of sky
        ys = [y for _, y in cells]; y0, y1 = min(ys), max(ys)
        for (x, y) in cells:
            img.putpixel((x, y), C(mix(grad(self.sky, (y - y0) / max(1, y1 - y0)), WHITE, 0.45)))
    def ornaments(self, img, L, T, w, h):
        S = img.size
        for (fx, fy, s) in ((L + 8, T - 6, 9), (L + 36, T - 3, 7), (L + w - 8, T - 6, 9), (L + w - 36, T - 3, 7),
                            (L - 3, T + h - 6, 7), (L + w + 2, T + h - 6, 7), (L - 4, T + h - 80, 6), (L + w + 3, T + h - 72, 6)):
            if h < 130 and fy > T and fy < T + h - 20: continue   # small screens: no side clouds in the middle
            cloud_puff(img, S, fx, fy, s)
        if self.emblem:
            self.emblem(img, S, L + w // 2, T - 9, self)
    def motif(self, img, x, y, r):
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, -1), (1, -1)): over(img, x + dx, y + dy, WHITE, 0.55)

def magic_sky(img, cells, seed):
    """aurora night sky in the inventory's player window"""
    xs = [p[0] for p in cells]; ys = [p[1] for p in cells]
    bx0, bx1, by0, by1 = min(xs), max(xs), min(ys), max(ys)
    r = rnd(seed)
    for (x, y) in cells:
        u = (x - bx0) / max(1, bx1 - bx0); vv = (y - by0) / max(1, by1 - by0)
        c = mix((18, 12, 50), (80, 50, 140), vv)
        for k, (amp, off, th) in enumerate(((5, 0.25, 4.5), (4, 0.42, 3.5))):
            d = abs(y - (by0 + (by1 - by0) * off + amp * math.sin(u * 6.3 + k * 2)))
            if d < th: c = mix(c, cyc(u * 0.6 + k * 0.3), (1 - d / th) * 0.75)
        img.putpixel((x, y), C(c))
    for _ in range(int((bx1 - bx0) * (by1 - by0) / 40)):
        img.putpixel((r.randint(bx0 + 1, bx1 - 1), r.randint(by0 + 1, by1 - 1)), C(mix(WHITE, cyc(r.random()), 0.3)))

# ------------------------------------------------------------------ small shared ornaments
def crystal_shard(img, S, base, tip, wid, col, line=OUT):
    """pointed crystal from a base point to a tip, two facets"""
    bx, by = base; tx, ty = tip
    dx, dy = tx - bx, ty - by; ln = math.hypot(dx, dy) or 1; nx, ny = -dy / ln, dx / ln
    pts = [(bx + nx * wid, by + ny * wid), (bx + dx * 0.7 + nx * wid, by + dy * 0.7 + ny * wid), (tx, ty),
           (bx + dx * 0.7 - nx * wid, by + dy * 0.7 - ny * wid), (bx - nx * wid, by - ny * wid)]
    mid = (bx + tx) / 2
    paint(img, poly(S, pts), lambda x, y: mix(col, WHITE, 0.5 if (x - mid) * nx + (y - (by + ty) / 2) * ny > 0 else 0.05), line=line, bevel=False)

WOOD = [(50, 30, 20), (140, 95, 60), (200, 150, 100), (240, 205, 160), (165, 115, 70), (100, 65, 40), (50, 30, 20)]
STONE = [(36, 32, 44), (110, 104, 125), (170, 165, 185), (222, 218, 235), (140, 134, 160), (80, 74, 96), (36, 32, 44)]

# ------------------------------------------------------------------ the other screens
class Lighthouse(Theme):                  # beacon: sanctuary of light
    pads = (12, 22, 12, 12)
    band = [(60, 50, 100), (200, 180, 110), (255, 238, 160), (255, 255, 240), (150, 225, 255), (90, 140, 200), (60, 50, 100)]
    slot = ((80, 100, 150), (240, 246, 255), (205, 218, 245), (182, 198, 236))
    def bg(self, x, y, w, h):
        c = grad([(232, 240, 255), (242, 230, 252), (252, 240, 226)], y / h)
        if (x + y) % 40 < 3: c = mix(c, cyc((x + y) / 300), 0.25)
        return c
    def feature(self, l, x, w): return grad([(24, 28, 70), (60, 80, 150), (170, 225, 255), (255, 255, 255)], l)
    def ornaments(self, img, L, T, w, h):
        S = img.size; cx = L + w // 2
        for y in range(0, T - 3):                              # beam of light
            for dx in range(-6, 7):
                a = (1 - abs(dx) / 7) ** 1.3 * (0.55 + 0.45 * y / T)
                over(img, cx + dx, y, mix(WHITE, (150, 230, 255), abs(dx) / 6), a)
        for side in (-1, 1):                                   # little pyramids of blocks
            bx = L + (6 if side < 0 else w - 7)
            for row, (n, col) in enumerate(((3, (120, 230, 240)), (2, (255, 220, 120)), (1, (130, 240, 170)))):
                for k in range(n):
                    x = bx + side * 0 + (k - (n - 1) / 2) * 6; y = T - 4 - row * 5
                    paint(img, rect(S, int(x - 3), y - 4, int(x + 2), y), lambda a, b, col=col: col, line=(50, 50, 90))
        for (x, y) in ((L - 1, T + h), (L + w, T + h)):
            paint(img, poly(S, [(x, y - 5), (x + 5, y), (x, y + 5), (x - 5, y)]), lambda a, b: (150, 235, 255), line=(50, 70, 130), bevel=False)
    def motif(self, img, x, y, r): star(img, x, y, 0.5, (150, 220, 255))

class Cartographer(Theme):                # cartography table: explorer's map desk
    band = [(60, 36, 20), (150, 96, 56), (205, 150, 95), (242, 210, 155), (170, 110, 60), (110, 70, 35), (60, 36, 20)]
    slot = ((120, 85, 50), (252, 238, 205), (226, 206, 166), (210, 188, 146))
    def bg(self, x, y, w, h):
        c = grad([(247, 234, 202), (234, 216, 176)], y / h)
        if abs(y - (h * 0.55 + 10 * math.sin(x / 17) + 4 * math.sin(x / 5))) < 0.7: c = mix(c, (120, 160, 200), 0.6)
        if abs(y - (h * 0.3 + 8 * math.cos(x / 21))) < 0.6 and x % 4 < 2: c = mix(c, (200, 90, 110), 0.6)
        return c
    def feature(self, l, x, w): return grad([(110, 75, 40), (200, 160, 110), (255, 246, 222)], l)
    def ornaments(self, img, L, T, w, h):
        S = img.size; cx = L + w // 2; cy = T - 7
        paint(img, ellipse(S, cx, cy, 11, 11) - ellipse(S, cx, cy, 9, 9), lambda x, y: (200, 150, 90), line=(90, 55, 25), bevel=False)
        paint(img, poly(S, star_pts(cx, cy, 13, 3, 4)), lambda x, y: (255, 245, 220) if x < cx else (210, 160, 100), line=(90, 55, 25), bevel=False)
        paint(img, poly(S, star_pts(cx, cy, 7, 2, 4, rot=-math.pi / 4)), lambda x, y: (120, 170, 220), line=(60, 80, 120), bevel=False)
        put(img, cx, cy - 13, C((220, 70, 90)))
        for side in (-1, 1):                                   # rolled maps at the corners
            x0 = L - 10 if side < 0 else L + w - 7
            paint(img, rect(S, x0, T - 7, x0 + 17, T - 2), lambda x, y: (245, 230, 195), line=(120, 80, 40))
            paint(img, ellipse(S, x0 if side < 0 else x0 + 17, T - 4.5, 2, 3), lambda x, y: (215, 190, 145), line=(120, 80, 40), bevel=False)
        for side in (-1, 1):                                   # dotted rope down the sides
            x0 = L - 7 if side < 0 else L + w + 6
            for y in range(T + 4, T + h - 2, 3): put(img, x0, y, C((190, 140, 90))); put(img, x0 + side, y + 1, C((120, 80, 40)))
    def motif(self, img, x, y, r):
        for dx in (-1, 0, 1): put(img, x + dx, y + dx, C((200, 90, 110))); put(img, x + dx, y - dx, C((200, 90, 110)))

class Automaton(Theme):                   # crafter: redstone automaton workshop
    band = [(30, 20, 26), (110, 60, 70), (190, 110, 120), (255, 170, 180), (140, 70, 80), (80, 40, 50), (30, 20, 26)]
    slot = ((40, 30, 36), (245, 175, 185), (66, 52, 60), (50, 38, 46))
    def bg(self, x, y, w, h):
        c = grad([(78, 66, 80), (54, 46, 60)], y / h)
        if (x % 16 == 8 and (y // 8) % 3 != 1) or (y % 16 == 8 and (x // 8) % 3 != 1): c = mix(c, (255, 110, 140), 0.45)
        if x % 16 == 8 and y % 16 == 8: c = (255, 190, 200)
        return c
    def feature(self, l, x, w): return grad([(50, 40, 46), (240, 140, 160), (255, 236, 240)], l)
    def torch(self, img, S, x, y):
        paint(img, rect(S, x - 1, y - 8, x + 1, y), lambda a, b: (150, 100, 70), line=(60, 40, 30), bevel=False)
        for rr, a in ((5, 0.25), (3.5, 0.45)):
            for dy in range(-6, 7):
                for dx in range(-6, 7):
                    if dx * dx + dy * dy <= rr * rr: over(img, x + dx, y - 10 + dy, (255, 120, 150), a)
        paint(img, ellipse(S, x, y - 10, 2, 2), lambda a, b: (255, 200, 210), line=(160, 30, 60), bevel=False)
    def ornaments(self, img, L, T, w, h):
        S = img.size; cx = L + w // 2
        paint(img, rect(S, cx - 16, T - 7, cx + 16, T), lambda x, y: (190, 190, 205))       # repeater slab
        for k in (-9, 0, 9): self.torch(img, S, cx + k, T - 7)
        for x in range(cx - 14, cx + 15): over(img, x, T - 3, (255, 110, 140), 0.8)
        self.torch(img, S, L - 1, T + 1); self.torch(img, S, L + w, T + 1)
        for side in (-1, 1):                                   # pistons on the sides
            x0 = L - 12 if side < 0 else L + w + 4
            for y in (T + 40, T + h - 40):
                paint(img, rect(S, x0, y - 6, x0 + 7, y + 6), lambda a, b: (170, 170, 185))
                fx = x0 if side < 0 else x0 + 6
                paint(img, rect(S, fx - (1 if side < 0 else 0), y - 7, fx + (0 if side < 0 else 1), y + 7), lambda a, b: (200, 160, 110), line=(90, 60, 30), bevel=False)
    def motif(self, img, x, y, r): over(img, x, y, (255, 150, 170), 0.9); over(img, x + 1, y, (255, 110, 140), 0.5)

class Weaver(Theme):                      # loom: weaver's workshop
    band = [(50, 30, 60), (170, 110, 170), (232, 172, 222), (255, 236, 250), (190, 130, 190), (110, 70, 120), (50, 30, 60)]
    slot = ((110, 70, 120), (255, 236, 250), (242, 222, 246), (228, 206, 238))
    def feature(self, l, x, w): return grad([(110, 70, 120), (230, 170, 215), (255, 240, 250)], l)
    def bg(self, x, y, w, h):
        c = (238, 222, 246) if (x // 2 + y // 2) % 2 else (226, 206, 238)
        if x % 16 == 0: c = (255, 180, 210)
        if y % 16 == 0: c = (170, 220, 245)
        return c
    def ornaments(self, img, L, T, w, h):
        S = img.size
        x0, x1 = L - 4, L + w + 3
        cols = [(255, 160, 200), (150, 220, 255), (210, 180, 255), (255, 210, 160), (170, 240, 200)]
        prev = None
        for x in range(x0, x1 + 1):                             # bunting string
            y = int(T - 14 + 8 * math.sin(math.pi * (x - x0) / (x1 - x0)))
            put(img, x, y, C((120, 80, 130)))
        for k, x in enumerate(range(x0 + 6, x1 - 4, 12)):
            y = T - 14 + 8 * math.sin(math.pi * (x - x0) / (x1 - x0))
            paint(img, poly(S, [(x - 4, y), (x + 4, y), (x, y + 8)]), lambda a, b, k=k: cols[k % len(cols)], line=(110, 70, 120), bevel=False)
        for (x, y, col) in ((L - 2, T - 2, (255, 160, 200)), (L + w + 1, T - 2, (150, 220, 255)), (L - 2, T + h + 1, (210, 180, 255)), (L + w + 1, T + h + 1, (255, 210, 160))):
            paint(img, ellipse(S, x, y, 6, 6), lambda a, b, col=col: col if (a + b) % 4 else mix(col, WHITE, 0.5), line=(100, 60, 110))
        for side in (-1, 1):                                   # spools
            x0_ = L - 11 if side < 0 else L + w + 4
            for y in (T + 50, T + h - 50):
                paint(img, rect(S, x0_, y - 6, x0_ + 7, y + 6), lambda a, b: (255, 180, 210) if b % 2 else (240, 150, 190), line=None, bevel=False)
                for yy in (y - 7, y + 7): paint(img, rect(S, x0_ - 1, yy, x0_ + 8, yy + 1), lambda a, b: (200, 150, 100), line=(90, 60, 40), bevel=False)
    def motif(self, img, x, y, r): pass

class Market(Theme):                      # villager: trading market
    pads = (14, 22, 14, 10)
    band = WOOD
    slot = ((110, 75, 45), (252, 238, 208), (234, 218, 190), (216, 198, 168))
    def bg(self, x, y, w, h):
        c = grad([(252, 242, 222), (240, 224, 196)], y / h)
        if y % 12 == 0: c = mix(c, (200, 160, 110), 0.35)
        return c
    def feature(self, l, x, w): return grad([(120, 85, 50), (226, 202, 162), (255, 246, 226)], l)
    def ornaments(self, img, L, T, w, h):
        S = img.size
        x0, x1 = L - 6, L + w + 5
        cols = [(255, 170, 200), (255, 250, 240), (150, 220, 255), (255, 250, 240)]
        for x in range(x0, x1 + 1):                             # striped awning with a scalloped edge
            k = (x - x0) // 8; col = cols[k % len(cols)]
            sx = (x - x0) % 8
            bottom = T + 1 + int(2.5 * math.sin(math.pi * sx / 8))
            for y in range(4, bottom + 1):
                c = mix(col, OUT, 0.15 * (y - 4) / (bottom - 3))
                put(img, x, y, C((120, 70, 90) if y in (4, bottom) else c))
        for x in range(x0, x1 + 1): put(img, x, 3, C((120, 70, 90)))
        cx = L + w // 2
        paint(img, poly(S, [(cx, -1), (cx + 7, 4), (cx + 4, 9), (cx - 4, 9), (cx - 7, 4)]), lambda x, y: (120, 240, 160) if x < cx else (70, 200, 120), line=(30, 90, 60))
        for (x, y) in ((L - 2, T + h - 1), (L + w + 1, T + h - 1)):   # crates
            paint(img, rect(S, x - 7, y - 7, x + 7, y + 7), lambda a, b: (210, 160, 100), line=(100, 60, 30))
            for i in range(-6, 7): put(img, x + i, y + i, C((150, 100, 50))); put(img, x + i, y - i, C((150, 100, 50)))
    def motif(self, img, x, y, r): paint(img, poly(img.size, [(x, y - 2), (x + 2, y), (x, y + 2), (x - 2, y)]), lambda a, b: (120, 235, 160), line=(30, 90, 60), bevel=False)

class Creator(Theme):                     # creative inventory: creator's studio
    # Only the right side sticks out: tabs live above/below, and the game blits the slot grid again as a sub-window
    # of the same texture, so the vanilla area must stay at its vanilla texels (no left/top padding).
    pads = (0, 0, 14, 0)
    band = [OUT, (150, 140, 220), (222, 204, 255), (255, 255, 255), (170, 150, 230), (100, 80, 170), OUT]
    def feature(self, l, x, w): return grad([(24, 18, 50), (54, 44, 100), (150, 140, 220)], l)   # dark: the game writes white here
    slot = ((70, 60, 120), (230, 225, 252), (48, 40, 94), (36, 30, 74))
    def bg(self, x, y, w, h):
        c = grad([(84, 68, 146), (62, 50, 118)], y / h)
        if abs((x - y) % 60 - 30) < 4: c = mix(c, cyc((x + y) / 200), 0.25)
        if (x * 7 + y * 13) % 83 == 0: c = mix(c, WHITE, 0.8)
        return c
    def ornaments(self, img, L, T, w, h):
        S = img.size
        for side in (1,):
            x0 = L + w + 1
            for k, y in enumerate(range(T + 10, T + h - 6, 16)):
                crystal_shard(img, S, (x0, y + 3), (x0 + side * (11 - k % 2 * 3), y - 4), 2.6, cyc(k / 8), line=(60, 40, 110))
    def motif(self, img, x, y, r): star(img, x, y, 0.5 + 0.5 * r.random(), cyc(r.random()))

# ------------------------------------------------------------------ non-container windows
class Cookbook(Theme):                    # recipe book panel: starry cookbook (inside stays dark: white text)
    pads = (6, 16, 6, 10)
    band = [(50, 26, 60), (150, 90, 150), (225, 165, 215), (255, 238, 250), (185, 120, 180), (100, 55, 110), (50, 26, 60)]
    def bg(self, x, y, w, h): return grad([(250, 236, 248), (236, 218, 240)], y / h)
    def feature(self, l, x, w): return grad([(26, 18, 44), (52, 38, 84), (200, 180, 240), (255, 255, 255)], l)
    def ornaments(self, img, L, T, w, h):
        S = img.size; cx = L + w // 2
        paint(img, poly(S, [(cx, T - 3), (cx - 13, T - 6), (cx - 13, T - 14), (cx, T - 11)]), lambda x, y: (255, 250, 238), line=(110, 60, 120))
        paint(img, poly(S, [(cx, T - 3), (cx + 13, T - 6), (cx + 13, T - 14), (cx, T - 11)]), lambda x, y: (246, 236, 226), line=(110, 60, 120))
        paint(img, poly(S, star_pts(cx - 6, T - 9, 3, 1.3, 5)), lambda x, y: (255, 160, 200), line=None, bevel=False)
        paint(img, poly(S, star_pts(cx + 6, T - 9, 3, 1.3, 5)), lambda x, y: (150, 220, 255), line=None, bevel=False)
        for (x, y) in ((L - 1, T - 1), (L + w, T - 1)):
            paint(img, poly(S, [(x, y - 5), (x + 5, y), (x, y + 5), (x - 5, y)]), lambda a, b: (255, 220, 140), line=(130, 90, 40), bevel=False)
        for k, (x, col) in enumerate(((L + 30, (255, 150, 200)), (L + 40, (150, 210, 255)))):   # ribbon bookmarks
            paint(img, poly(S, [(x - 2, T + h - 1), (x + 2, T + h - 1), (x + 2, T + h + 8), (x, T + h + 6), (x - 2, T + h + 8)]),
                  lambda a, b, col=col: col, line=(110, 60, 120), bevel=False)
    def motif(self, img, x, y, r): pass

class ModePortal(Theme):                  # F3+F4 game mode switcher: portal of modes (dark: white text)
    pads = (1, 16, 2, 12)
    band = [(20, 12, 40), (90, 60, 160), (170, 140, 240), (240, 230, 255), (120, 90, 200), (60, 40, 120), (20, 12, 40)]
    def bg(self, x, y, w, h): return (40, 28, 80)
    def feature(self, l, x, w): return grad([(22, 14, 46), (60, 40, 110), (200, 180, 255)], l)
    def ornaments(self, img, L, T, w, h):
        S = img.size; cx = L + w // 2
        paint(img, poly(S, star_pts(cx, T - 7, 9, 3, 4)), lambda x, y: mix((200, 180, 255), (150, 230, 255), (x - cx + 9) / 18), line=(60, 40, 110), bevel=False)
        paint(img, ellipse(S, cx, T - 7, 2.5, 2.5), lambda x, y: WHITE, line=(120, 90, 200), bevel=False)
        for side in (-1, 1):
            star(img, cx + side * 20, T - 6, 0.8, cyc(0.3 + side * 0.2))
            star(img, cx + side * 40, T - 3, 0.6, cyc(0.6 + side * 0.2))
        for k, x in enumerate(range(L + 12, L + w - 8, 18)):    # crystal fringe hanging below
            crystal_shard(img, S, (x, T + h + 1), (x + (1 if k % 2 else -1), T + h + 7 + (k % 3) * 2), 1.8, cyc(k / 7), line=(60, 40, 110))
    def motif(self, img, x, y, r): pass
