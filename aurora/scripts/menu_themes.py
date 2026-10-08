# Drawing helpers and the per-screen themes of Aurora HUD XL (used by menus_xl.py).
# A theme gives the frame band, panel background, slot / plaque colours, how vanilla decorations are recoloured
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
    plaque = ((235, 230, 250), (120, 105, 175))                             # fill, line
    def bg(self, x, y, w, h): return (60, 50, 100)
    def feature(self, l, x, w): return mix(cyc(x / w), WHITE, max(0, l - 0.5))
    def window(self, img, cells): pass
    def ornaments(self, img, L, T, w, h): pass
    def motif(self, img, x, y, r): star(img, x, y, 0.8, cyc(r.random()))

class Observatory(Theme):
    band = [OUT, (110, 120, 190), (190, 200, 245), (245, 248, 255), (150, 160, 220), (70, 70, 140), OUT]
    slot = ((70, 70, 140), (200, 205, 250), (36, 30, 84), (22, 18, 56))
    plaque = ((226, 228, 250), (96, 96, 170))
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
    plaque = ((250, 240, 214), (150, 100, 50))
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
    plaque = ((255, 244, 220), (190, 110, 60))
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
    plaque = ((215, 222, 236), (70, 80, 110))
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
    plaque = ((255, 255, 255), (150, 130, 200))
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

class Vault(Theme):
    pads = (14, 20, 14, 12)
    band = [(70, 40, 10), (200, 150, 60), (255, 220, 120), (255, 245, 190), (230, 180, 80), (150, 100, 30), (70, 40, 10)]
    slot = ((60, 24, 70), (240, 200, 120), (64, 30, 82), (48, 20, 64))
    plaque = ((255, 246, 215), (170, 120, 50))
    def bg(self, x, y, w, h):
        yy = y % 18                                            # period 18: the chest is cut between rows
        c = (88, 38, 104) if (yy < 9) else (80, 34, 96)
        d = abs((x % 18) - 9) + abs(yy - 9)
        if d in (7, 8): c = mix(c, (150, 90, 170), 0.6)
        if d == 0: c = (230, 190, 110)
        return c
    def feature(self, l, x, w): return grad([(110, 70, 20), (230, 180, 80), (255, 245, 190)], l)
    def gemstone(self, img, S, cx, cy, r, col):
        paint(img, poly(S, [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]), lambda x, y: mix(col, WHITE, 0.4 if (x < cx and y < cy) else 0), line=(60, 30, 50), bevel=False)
    def ornaments(self, img, L, T, w, h):
        S = img.size
        gold = lambda x, y: grad([(255, 245, 190), (240, 195, 90), (170, 115, 40)], (y % 16) / 16)
        cx = L + w // 2
        paint(img, ellipse(S, cx, T - 10, 8, 9) - ellipse(S, cx, T - 10, 5, 6) - rect(S, 0, T - 9, S[0], S[1]), gold)   # shackle
        paint(img, rect(S, cx - 10, T - 10, cx + 10, T + 6), gold)                                                     # body
        paint(img, ellipse(S, cx, T - 4, 2, 2) | rect(S, cx - 1, T - 3, cx + 1, T + 2), lambda x, y: (60, 25, 50), line=None, bevel=False)
        for k, col in enumerate(((255, 120, 170), (120, 230, 200), (130, 170, 255))):
            self.gemstone(img, S, cx - 6 + k * 6, T + 3 if k != 1 else T + 4, 2, col)
        for (gx, gy) in ((L - 1, T - 1), (L + w, T - 1)):
            for k, col in enumerate(((255, 120, 170), (120, 230, 200), (130, 170, 255))):
                self.gemstone(img, S, gx + (k - 1) * 6, gy - (4 if k == 1 else 0), 4, col)
        for (px_, side) in ((L + 4, 1), (L + w - 5, -1)):      # coin piles at the bottom corners
            for k in range(4):
                for j in range(3 - k // 2):
                    paint(img, ellipse(S, px_ + side * j * 7, T + h + 7 - k * 2, 4, 2), lambda x, y: (255, 220, 110), line=(140, 90, 30), bevel=False)
        for gy in range(T + 17 + 9, T + 125, 18):             # gem studs on the sides, one per row
            for gx in (L - 1, L + w):
                self.gemstone(img, S, gx, gy, 2, (255, 150, 200))
    def motif(self, img, x, y, r): pass

class EndShell(Theme):
    band = [(40, 20, 60), (140, 90, 160), (200, 150, 215), (235, 205, 245), (170, 120, 190), (100, 60, 125), (40, 20, 60)]
    slot = ((50, 30, 80), (210, 180, 240), (30, 18, 54), (20, 12, 40))
    plaque = ((236, 222, 248), (130, 90, 160))
    def bg(self, x, y, w, h):
        c = grad([(46, 26, 76), (24, 14, 46), (14, 8, 30)], y / h)
        n = math.sin(x / 13 + y / 21) + math.sin(x / 7 - y / 17)
        if n > 1.2: c = mix(c, (140, 80, 180), (n - 1.2) * 0.5)
        if (x * 5 + y * 11) % 89 == 0: c = mix(c, WHITE, 0.8)
        return c
    def ornaments(self, img, L, T, w, h):
        S = img.size
        cx = L + w // 2
        dome = ellipse(S, cx, T + 2, 52, 20) - rect(S, 0, T + 3, S[0], S[1])
        shell = lambda x, y: mix(grad([(235, 205, 245), (190, 140, 210), (130, 80, 160)], (y - T + 18) / 22),
                                 (100, 60, 130), 0.35 if (x - cx) % 13 in (0, 1) else 0)
        paint(img, dome, shell, line=(60, 30, 80))
        head = ellipse(S, cx, T - 2, 9, 7) - rect(S, 0, T + 1, S[0], S[1])
        paint(img, head, lambda x, y: (200, 240, 160), line=(70, 110, 60))
        for ex in (cx - 4, cx + 3):
            put(img, ex, T - 4, C((40, 40, 70))); put(img, ex + 1, T - 4, C((40, 40, 70))); put(img, ex, T - 5, C(WHITE))
        for (fx, fy) in ((L - 2, T - 2), (L + w + 1, T - 2), (L - 2, T + h + 1), (L + w + 1, T + h + 1)):
            for k in range(5):
                a = k * 2 * math.pi / 5 - math.pi / 2
                paint(img, ellipse(S, fx + 4 * math.cos(a), fy + 4 * math.sin(a), 3, 3), lambda x, y: (220, 170, 240), line=(90, 50, 120), bevel=False)
            paint(img, ellipse(S, fx, fy, 3, 3), lambda x, y: (255, 230, 250), line=(90, 50, 120), bevel=False)
        for gy in range(T + 10, T + h - 4, 12):
            for gx in (L - 4, L + w + 3): put(img, gx, gy, C((90, 50, 120))); put(img, gx, gy + 1, C((90, 50, 120)))
    def motif(self, img, x, y, r): star(img, x, y, 0.4 + 0.6 * r.random(), (210, 170, 255))

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
def rivet(img, S, x, y, col=(225, 225, 240), line=(60, 58, 80)):
    paint(img, ellipse(S, x, y, 2.5, 2.5), lambda a, b: col, line=line)

def sparks(img, cx, cy, seed, n=7, spread=14, cols=((255, 210, 160), (255, 160, 210), (255, 245, 200))):
    r = rnd(seed)
    for k in range(n):
        a = r.uniform(-math.pi, 0); d = r.uniform(4, spread)
        star(img, int(cx + d * math.cos(a)), int(cy + d * math.sin(a)), r.uniform(0.5, 1.0), cols[k % len(cols)])

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
class Smithy(Theme):                      # anvil: celestial blacksmith
    band = [(30, 28, 44), (110, 108, 135), (175, 175, 200), (232, 232, 245), (140, 138, 165), (80, 78, 100), (30, 28, 44)]
    slot = ((50, 48, 66), (205, 205, 225), (72, 70, 94), (56, 54, 76))
    plaque = ((236, 236, 246), (90, 88, 120))
    def bg(self, x, y, w, h):
        c = grad([(128, 126, 160), (92, 90, 122)], y / h)
        if (x * 3 + y * 5) % 23 == 0: c = mix(c, (170, 168, 200), 0.6)
        if (x * 7 + y * 11) % 131 == 0: c = mix(c, (255, 200, 160), 0.8)
        return c
    def feature(self, l, x, w): return grad([(60, 58, 80), (200, 200, 228), (255, 255, 255)], l)
    def ornaments(self, img, L, T, w, h):
        S = img.size; cx = L + w // 2
        iron = lambda x, y: grad([(215, 215, 238), (130, 128, 160)], (y - (T - 12)) / 14)
        paint(img, poly(S, [(cx - 17, T - 12), (cx + 12, T - 12), (cx + 19, T - 9), (cx + 8, T - 7), (cx + 6, T - 3),
                            (cx + 11, T + 1), (cx - 11, T + 1), (cx - 6, T - 3), (cx - 8, T - 7), (cx - 17, T - 9)]), iron)
        paint(img, poly(S, [(cx + 6, T - 16), (cx + 22, T - 21), (cx + 23, T - 19), (cx + 7, T - 14)]), lambda x, y: (170, 120, 80))
        paint(img, poly(S, [(cx - 1, T - 20), (cx + 8, T - 21), (cx + 9, T - 13), (cx, T - 12)]), lambda x, y: (190, 190, 215))
        sparks(img, cx - 2, T - 13, 3, n=9, spread=16)
        for (x, y) in ((L - 1, T - 1), (L + w, T - 1), (L - 1, T + h), (L + w, T + h)): rivet(img, S, x, y)
        for side in (-1, 1):                                   # hanging chains
            x0 = L - 8 if side < 0 else L + w + 7
            for k, y in enumerate(range(T + 8, T + h - 6, 6)):
                ring = ellipse(S, x0, y, 2 if k % 2 else 1, 3) - ellipse(S, x0, y, 0.6 if k % 2 else 0.1, 1.6)
                paint(img, ring, lambda a, b: (190, 190, 215), line=(60, 58, 80), bevel=False)
    def motif(self, img, x, y, r): star(img, x, y, 0.6, (255, 200, 170))

class Lighthouse(Theme):                  # beacon: sanctuary of light
    pads = (12, 22, 12, 12)
    band = [(60, 50, 100), (200, 180, 110), (255, 238, 160), (255, 255, 240), (150, 225, 255), (90, 140, 200), (60, 50, 100)]
    slot = ((80, 100, 150), (240, 246, 255), (205, 218, 245), (182, 198, 236))
    plaque = ((245, 248, 255), (100, 120, 180))
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

class Alchemy(Theme):                     # brewing stand: alchemist's lab
    band = [(30, 40, 50), (80, 160, 150), (150, 230, 210), (230, 255, 248), (110, 190, 180), (50, 100, 110), (30, 40, 50)]
    slot = ((30, 50, 60), (175, 240, 225), (42, 66, 80), (30, 50, 64))
    plaque = ((236, 252, 247), (70, 140, 130))
    def bg(self, x, y, w, h):
        c = grad([(70, 92, 124), (52, 60, 102), (42, 42, 84)], y / h)
        for (ox, oy, rr) in ((30, 120, 5), (150, 100, 4), (20, 40, 3), (160, 30, 3), (120, 140, 6)):
            if abs(math.hypot(x - ox, y - oy) - rr) < 0.6: c = mix(c, (170, 240, 230), 0.5)
        return c
    def feature(self, l, x, w): return grad([(40, 60, 72), (140, 230, 210), (240, 255, 250)], l)
    def flask(self, img, S, cx, by, col):
        paint(img, ellipse(S, cx, by - 5, 6, 6) | rect(S, cx - 2, by - 15, cx + 2, by - 9), lambda x, y: col if y > by - 6 else (220, 245, 250))
        paint(img, rect(S, cx - 3, by - 18, cx + 3, by - 15), lambda x, y: (190, 140, 100))
        over(img, cx - 3, by - 8, WHITE, 0.9)
    def ornaments(self, img, L, T, w, h):
        S = img.size; cx = L + w // 2
        self.flask(img, S, L + 2, T + 2, (255, 140, 200)); self.flask(img, S, L + w - 3, T + 2, (120, 220, 255))
        for k, (dy, rr) in enumerate(((5, 3.5), (10, 3), (14, 2.5), (18, 2))):
            bx = cx + 4 * math.sin(k * 1.4)
            paint(img, ellipse(S, bx, T - 1 - dy, rr, rr), lambda x, y: (200, 255, 240), line=(60, 130, 130), bevel=True)
        for side in (-1, 1):                                   # shelves with vials
            x0 = L - 12 if side < 0 else L + w + 4
            for y in range(T + 30, T + h - 10, 34):
                paint(img, rect(S, x0, y, x0 + 8, y + 1), lambda a, b: (170, 120, 80), line=(80, 50, 30), bevel=False)
                for k, col in enumerate(((255, 150, 210), (150, 240, 200), (190, 160, 255))):
                    paint(img, rect(S, x0 + 1 + k * 3, y - 5, x0 + 2 + k * 3, y - 1), lambda a, b, col=col: col, line=None, bevel=False)
    def motif(self, img, x, y, r): paint(img, ellipse(img.size, x, y, 2, 2), lambda a, b: (190, 250, 235), line=(80, 150, 150), bevel=False)

class Cartographer(Theme):                # cartography table: explorer's map desk
    band = [(60, 36, 20), (150, 96, 56), (205, 150, 95), (242, 210, 155), (170, 110, 60), (110, 70, 35), (60, 36, 20)]
    slot = ((120, 85, 50), (252, 238, 205), (226, 206, 166), (210, 188, 146))
    plaque = ((255, 251, 238), (150, 100, 55))
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
    plaque = ((250, 238, 242), (150, 70, 90))
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

class Launcher(Theme):                    # dispenser / dropper: archery launcher
    band = [(40, 40, 50), (120, 120, 135), (180, 180, 196), (228, 228, 238), (150, 150, 166), (90, 90, 106), (40, 40, 50)]
    slot = ((70, 70, 86), (228, 228, 242), (152, 152, 172), (136, 136, 158))
    plaque = ((246, 246, 252), (100, 100, 125))
    def bg(self, x, y, w, h):
        row = y // 7; xx = x + (3 if row % 2 else 0)
        c = (196, 192, 216) if (xx // 9 + row) % 3 else (184, 180, 206)
        if y % 7 == 0 or xx % 9 == 0: c = (160, 156, 184)
        return c
    def arrow(self, img, S, x0, y0, x1, y1, col=(255, 170, 200)):
        n = int(max(abs(x1 - x0), abs(y1 - y0)))
        for i in range(n + 1):
            put(img, int(round(x0 + (x1 - x0) * i / n)), int(round(y0 + (y1 - y0) * i / n)), C((150, 110, 80)))
        ux, uy = (x1 - x0) / n, (y1 - y0) / n
        paint(img, poly(S, [(x1 + ux * 4, y1 + uy * 4), (x1 - uy * 2.5, y1 + ux * 2.5), (x1 + uy * 2.5, y1 - ux * 2.5)]), lambda a, b: (220, 225, 240), line=(70, 70, 90), bevel=False)
        for k in (0, 2):
            put(img, int(x0 - uy * 2 + ux * k), int(y0 + ux * 2 + uy * k), C(col)); put(img, int(x0 + uy * 2 + ux * k), int(y0 - ux * 2 + uy * k), C(col))
    def ornaments(self, img, L, T, w, h):
        S = img.size; cx = L + w // 2; cy = T - 7
        for k, rr in enumerate((12, 9, 6, 3)):
            paint(img, ellipse(S, cx, cy, rr, rr), lambda x, y, k=k: (255, 150, 190) if k % 2 == 0 else (255, 250, 252), line=(110, 60, 90) if k == 0 else None, bevel=False)
        self.arrow(img, S, cx + 16, cy - 10, cx + 3, cy - 1); self.arrow(img, S, cx - 17, cy - 6, cx - 4, cy + 1, (150, 220, 255))
        for side in (-1, 1):
            x0 = L - 1 if side < 0 else L + w
            self.arrow(img, S, x0 - side * 2, T - 2, x0 + side * 9, T - 13, (190, 170, 255))
            for y in (T + 50, T + h - 40):
                self.arrow(img, S, x0, y, x0 + side * 9, y, (255, 200, 150))
    def motif(self, img, x, y, r): pass

class Arcane(Theme):                      # enchanting table: arcane library
    band = [(20, 14, 40), (90, 60, 150), (160, 120, 220), (255, 232, 160), (120, 90, 190), (60, 40, 110), (20, 14, 40)]
    slot = ((40, 28, 70), (205, 175, 255), (50, 38, 92), (36, 26, 72))
    plaque = ((242, 234, 255), (110, 80, 170))
    GLYPHS = [(0, 0), (1, 1), (2, 0), (0, 2), (2, 2), (1, 0), (1, 2), (0, 1), (2, 1)]
    def bg(self, x, y, w, h):
        c = grad([(60, 44, 108), (40, 28, 78), (26, 20, 56)], y / h)
        cell = ((x // 9) * 7 + (y // 9) * 13) % 11
        if cell < 3 and ((x % 9, y % 9) in [(3 + a, 3 + b) for a, b in self.GLYPHS[cell:cell + 4]]): c = mix(c, (150, 240, 255), 0.45)
        return c
    def feature(self, l, x, w): return grad([(40, 28, 70), (150, 120, 220), (242, 232, 255)], l)
    def ornaments(self, img, L, T, w, h):
        S = img.size; cx = L + w // 2
        for rr, a in ((16, 0.15), (11, 0.25)):
            for dy in range(-rr, rr + 1):
                for dx in range(-rr, rr + 1):
                    if dx * dx + dy * dy * 2 <= rr * rr: over(img, cx + dx, T - 9 + dy, (190, 160, 255), a)
        paint(img, poly(S, [(cx, T - 4), (cx - 16, T - 8), (cx - 16, T - 17), (cx, T - 13)]), lambda x, y: (255, 250, 235), line=(110, 80, 170))
        paint(img, poly(S, [(cx, T - 4), (cx + 16, T - 8), (cx + 16, T - 17), (cx, T - 13)]), lambda x, y: (245, 238, 220), line=(110, 80, 170))
        for k in range(3):
            for x in range(cx - 13, cx - 3): put(img, x, T - 14 + k * 3 + (x - cx + 13) // 6, C((190, 170, 220)))
            for x in range(cx + 4, cx + 14): put(img, x, T - 14 + k * 3 + (cx + 13 - x) // 6, C((190, 170, 220)))
        sparks(img, cx, T - 16, 9, n=6, spread=14, cols=((180, 240, 255), (220, 190, 255)))
        for side in (-1, 1):                                   # bookshelves
            x0 = L - 13 if side < 0 else L + w + 3
            for y in range(T + 6, T + h - 12, 15):
                paint(img, rect(S, x0, y + 12, x0 + 10, y + 13), lambda a, b: (150, 100, 60), line=None, bevel=False)
                for k, col in enumerate(((255, 140, 180), (140, 200, 255), (255, 220, 140), (170, 240, 190), (210, 170, 255))):
                    hh = 9 + (k * 3 + y) % 3
                    paint(img, rect(S, x0 + k * 2, y + 12 - hh, x0 + k * 2 + 1, y + 11), lambda a, b, col=col: col, line=None, bevel=False)
        for (x, y) in ((L - 1, T + h), (L + w, T + h)):       # candles
            paint(img, rect(S, x - 2, y - 6, x + 2, y + 2), lambda a, b: (250, 240, 220), line=(110, 80, 170))
            paint(img, ellipse(S, x, y - 9, 1.5, 2.5), lambda a, b: (255, 220, 140), line=None, bevel=False)
    def motif(self, img, x, y, r): star(img, x, y, 0.6, (170, 230, 255))

class Grinder(Theme):                     # grindstone: moonstone grinder
    band = [(40, 30, 30), (130, 100, 80), (190, 160, 130), (236, 216, 192), (150, 120, 95), (90, 70, 55), (40, 30, 30)]
    slot = ((70, 66, 80), (232, 228, 242), (172, 170, 188), (152, 150, 170))
    plaque = ((252, 248, 242), (130, 100, 80))
    def bg(self, x, y, w, h):
        c = grad([(200, 196, 218), (180, 176, 200)], y / h)
        if (x * 13 + y * 7) % 17 == 0: c = mix(c, (150, 146, 172), 0.6)
        if (x * 5 + y * 3) % 29 == 0: c = mix(c, WHITE, 0.6)
        return c
    def ornaments(self, img, L, T, w, h):
        S = img.size; cx = L + w // 2; cy = T - 9
        for side in (-1, 1):
            paint(img, poly(S, [(cx + side * 5, cy), (cx + side * 8, cy), (cx + side * 13, T + 1), (cx + side * 10, T + 1)]), lambda x, y: (200, 150, 100), line=(90, 60, 40))
        paint(img, ellipse(S, cx, cy, 11, 11), lambda x, y: (205, 200, 225) if math.hypot(x - cx, y - cy) % 4 > 1 else (170, 165, 195))
        paint(img, ellipse(S, cx, cy, 2.5, 2.5), lambda x, y: (150, 110, 80), line=(70, 50, 40), bevel=False)
        sparks(img, cx + 12, cy - 2, 21, n=7, spread=12)
        for (x, y) in ((L - 1, T - 1), (L + w, T - 1), (L - 1, T + h), (L + w, T + h)):
            paint(img, ellipse(S, x, y, 4, 4), lambda a, b: (200, 150, 100), line=(90, 60, 40))
    def motif(self, img, x, y, r): put(img, x, y, C(WHITE)); put(img, x + 1, y + 1, C((170, 166, 196)))

class StarHopper(Theme):                  # hopper: star collector
    band = [(24, 24, 36), (80, 84, 104), (140, 145, 170), (208, 212, 232), (110, 114, 140), (60, 62, 80), (24, 24, 36)]
    slot = ((40, 40, 56), (195, 205, 232), (58, 60, 84), (44, 46, 66))
    plaque = ((238, 242, 252), (80, 86, 120))
    def bg(self, x, y, w, h):
        c = grad([(56, 54, 104), (36, 34, 74)], y / h)
        if (x - y // 2) % 37 == 0 and y % 13 < 6: c = mix(c, (255, 240, 200), 0.6)
        if (x * 7 + y * 13) % 89 == 0: c = mix(c, WHITE, 0.8)
        return c
    def ornaments(self, img, L, T, w, h):
        S = img.size; cx = L + w // 2
        paint(img, poly(S, [(cx - 18, T - 13), (cx + 18, T - 13), (cx + 6, T - 4), (cx + 6, T + 1), (cx - 6, T + 1), (cx - 6, T - 4)]),
              lambda x, y: grad([(205, 210, 232), (110, 114, 140)], (y - T + 13) / 14))
        for k in range(6):                                     # stars falling in
            a = k / 6
            star(img, int(cx - 24 + k * 9), int(T - 15 - 4 * math.sin(a * math.pi)), 0.6 + 0.4 * (k % 2), cyc(a))
        for (x, y) in ((L - 1, T - 1), (L + w, T - 1), (L - 1, T + h), (L + w, T + h)):
            paint(img, poly(S, star_pts(x, y, 6, 2.5, 5)), lambda a, b: (255, 236, 160), line=(120, 90, 40), bevel=False)
    def motif(self, img, x, y, r): star(img, x, y, 0.4 + 0.5 * r.random(), (255, 240, 200))

class Stable(Theme):                      # horse: meadow stable
    band = WOOD
    slot = ((110, 75, 45), (252, 238, 208), (232, 217, 188), (215, 198, 168))
    plaque = ((255, 250, 238), (140, 95, 60))
    def bg(self, x, y, w, h):
        c = grad([(210, 236, 255), (222, 242, 214), (192, 226, 172)], y / h)
        if (x * 11 + y * 7) % 61 == 0: c = (255, 170, 200)
        if (x * 13 + y * 5) % 73 == 0: c = (255, 240, 150)
        return c
    def window(self, img, cells):
        xs = [p[0] for p in cells]; ys = [p[1] for p in cells]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        for (x, y) in cells:
            v = (y - y0) / max(1, y1 - y0); u = (x - x0) / max(1, x1 - x0)
            c = grad([(255, 190, 210), (255, 220, 190), (250, 240, 210)], v / 0.7)
            hill = 0.72 + 0.08 * math.sin(u * 7)
            if v > hill: c = mix((150, 210, 140), (110, 180, 120), (v - hill) / 0.3)
            if math.hypot(u - 0.75, v - 0.35) < 0.08: c = (255, 245, 200)
            img.putpixel((x, y), C(c))
    def ornaments(self, img, L, T, w, h):
        S = img.size; cx = L + w // 2; cy = T - 9
        shoe = ellipse(S, cx, cy, 11, 11) - ellipse(S, cx, cy, 6, 6) - rect(S, cx - 12, cy - 12, cx + 12, cy - 4)
        shoe = {(x, 2 * cy - y) for (x, y) in shoe}             # upside-down U, the lucky way
        paint(img, shoe, lambda x, y: grad([(255, 240, 180), (230, 180, 80)], (y - cy + 11) / 22), line=(120, 80, 30))
        for (x, y) in ((cx - 8, cy - 3), (cx + 8, cy - 3), (cx - 6, cy - 7), (cx + 6, cy - 7)): put(img, x, y, C((120, 80, 30)))
        sparks(img, cx, cy - 8, 31, n=5, spread=13)
        for (x, y) in ((L - 3, T - 3), (L + w + 2, T - 3)):    # hay bales
            paint(img, rect(S, x - 7, y - 5, x + 7, y + 5), lambda a, b: (250, 220, 120) if a % 3 else (220, 185, 90), line=(140, 100, 40))
        for side in (-1, 1):                                   # fence
            x0 = L - 10 if side < 0 else L + w + 3
            for y in range(T + 20, T + h - 4, 24):
                paint(img, rect(S, x0 + 2, y - 10, x0 + 4, y + 6), lambda a, b: (200, 150, 100), line=(90, 60, 40), bevel=False)
            for y in range(T + 14, T + h - 8, 12):
                paint(img, rect(S, x0, y, x0 + 7, y + 1), lambda a, b: (220, 170, 120), line=None, bevel=False)
    def motif(self, img, x, y, r): put(img, x, y, C((255, 170, 200))); put(img, x, y + 1, C((120, 180, 110)))

class Weaver(Theme):                      # loom: weaver's workshop
    band = [(50, 30, 60), (170, 110, 170), (232, 172, 222), (255, 236, 250), (190, 130, 190), (110, 70, 120), (50, 30, 60)]
    slot = ((110, 70, 120), (255, 236, 250), (242, 222, 246), (228, 206, 238))
    plaque = ((255, 250, 255), (150, 90, 160))
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

class Reef(Theme):                        # nautilus: abyssal reef
    band = [(20, 40, 60), (60, 140, 160), (130, 210, 220), (222, 250, 250), (90, 170, 190), (40, 90, 120), (20, 40, 60)]
    slot = ((20, 50, 70), (175, 242, 242), (32, 72, 104), (24, 54, 84))
    plaque = ((238, 252, 252), (60, 130, 150))
    def bg(self, x, y, w, h):
        c = grad([(118, 206, 224), (64, 136, 194), (38, 72, 144)], y / h)
        if (x + y * 0.6) % 34 < 5: c = mix(c, WHITE, 0.12)
        return c
    def window(self, img, cells):
        ys = [p[1] for p in cells]; y0, y1 = min(ys), max(ys)
        for (x, y) in cells:
            img.putpixel((x, y), C(grad([(60, 150, 200), (20, 50, 110)], (y - y0) / max(1, y1 - y0))))
        r = rnd(4)
        for _ in range(12):
            x, y = r.choice(cells); over(img, x, y, (200, 250, 255), 0.8)
    def ornaments(self, img, L, T, w, h):
        S = img.size; cx = L + w // 2; cy = T - 8
        for k in range(26):                                     # nautilus spiral
            a = k * 0.45; rr = 1.0 + k * 0.42
            paint(img, ellipse(S, cx + rr * math.cos(a), cy + rr * math.sin(a), 1.2 + k * 0.12, 1.2 + k * 0.12),
                  lambda x, y, k=k: (255, 236, 220) if k % 4 < 2 else (240, 170, 140), line=None, bevel=False)
        for side in (-1, 1):                                   # coral
            bx = L - 1 if side < 0 else L + w
            for k, (dx, dy) in enumerate(((0, -12), (side * 6, -9), (-side * 4, -8), (side * 9, -3))):
                n = 12
                for i in range(n + 1):
                    put(img, int(bx + dx * i / n), int(T + dy * i / n), C((255, 150, 180)))
                    put(img, int(bx + dx * i / n) + 1, int(T + dy * i / n), C((255, 190, 210)))
            for y in range(T + 20, T + h - 10, 18):
                paint(img, ellipse(S, bx + side * 7, y, 2, 2), lambda a, b: (210, 250, 255), line=(70, 140, 170), bevel=False)
    def motif(self, img, x, y, r): paint(img, ellipse(img.size, x, y, 1.5, 1.5), lambda a, b: (220, 252, 255), line=(80, 160, 190), bevel=False)

class Armory(Theme):                      # smithing table: royal armory
    band = [(20, 14, 24), (70, 56, 70), (120, 100, 120), (255, 216, 125), (90, 72, 90), (50, 40, 52), (20, 14, 24)]
    slot = ((30, 24, 34), (242, 208, 135), (54, 46, 60), (40, 34, 46))
    plaque = ((255, 246, 226), (160, 120, 60))
    def bg(self, x, y, w, h):
        c = grad([(76, 64, 88), (48, 40, 58)], y / h)
        if abs((x % 24) - 12) + abs((y % 24) - 12) == 11: c = mix(c, (230, 190, 110), 0.5)
        return c
    def feature(self, l, x, w): return grad([(40, 32, 46), (200, 170, 110), (255, 245, 210)], l)
    def ornaments(self, img, L, T, w, h):
        S = img.size; cx = L + w // 2; cy = T - 8
        for side in (-1, 1):                                   # crossed swords behind the shield
            for i in range(26):
                x = cx + side * (-13 + i); y = cy + 9 - i * 0.8
                put(img, int(x), int(y), C((220, 225, 240))); put(img, int(x), int(y) + 1, C((140, 145, 170)))
            paint(img, rect(S, cx + side * 9 - 1, cy + 3, cx + side * 9 + 1, cy + 9), lambda a, b: (230, 190, 110), line=None, bevel=False)
        paint(img, poly(S, [(cx - 10, cy - 11), (cx + 10, cy - 11), (cx + 10, cy + 1), (cx, cy + 10), (cx - 10, cy + 1)]),
              lambda x, y: (80, 64, 90) if x < cx else (60, 48, 70), line=(240, 200, 120))
        paint(img, poly(S, [(cx - 7, cy - 1), (cx, cy - 7), (cx + 7, cy - 1), (cx + 7, cy + 2), (cx, cy - 4), (cx - 7, cy + 2)]), lambda x, y: (255, 220, 130), line=None, bevel=False)
        for (x, y) in ((L - 1, T - 1), (L + w, T - 1), (L - 1, T + h), (L + w, T + h)):
            for (dx, dy) in ((0, -3), (-3, 0), (3, 0)):
                paint(img, ellipse(S, x + dx, y + dy, 2, 2), lambda a, b: (255, 216, 125), line=(120, 80, 30), bevel=False)
    def motif(self, img, x, y, r): pass

class Geode(Theme):                       # stonecutter: geode mason
    band = STONE
    slot = ((60, 50, 80), (222, 204, 252), (102, 92, 128), (86, 76, 112))
    plaque = ((246, 242, 252), (110, 90, 140))
    def bg(self, x, y, w, h):
        c = grad([(178, 172, 196), (150, 144, 172)], y / h)
        if abs((y - 0.4 * x) % 53 - 26) < 0.7 or abs((y + 0.7 * x) % 71 - 35) < 0.6: c = mix(c, (200, 140, 255), 0.6)
        return c
    def feature(self, l, x, w): return grad([(60, 50, 80), (170, 140, 220), (250, 240, 255)], l)
    def ornaments(self, img, L, T, w, h):
        S = img.size; cx = L + w // 2; cy = T - 8
        paint(img, gear(S, cx, cy, 12, 20, hole=3), lambda x, y: grad([(240, 242, 252), (160, 165, 190)], (y - cy + 12) / 24))
        for k in range(3):
            a = -math.pi / 2 + k * 2.1
            put(img, int(cx + 15 * math.cos(a)), int(cy + 15 * math.sin(a)), C(WHITE))
        for (x, y, s) in ((L - 1, T, -1), (L + w, T, 1), (L - 1, T + h, -1), (L + w, T + h, 1)):
            for k, (dx, dy, wd) in enumerate(((0, -14, 3), (s * 6, -10, 2.5), (-s * 5, -9, 2.2))):
                crystal_shard(img, S, (x + dx * 0.2, y + 2), (x + dx, y + dy), wd, cyc(0.25 + k * 0.08), line=(60, 30, 90))
    def motif(self, img, x, y, r): crystal_shard(img, img.size, (x, y + 2), (x + r.randint(-2, 2), y - 4), 1.5, (210, 170, 255), line=(80, 50, 120))

class Market(Theme):                      # villager: trading market
    pads = (14, 22, 14, 10)
    band = WOOD
    slot = ((110, 75, 45), (252, 238, 208), (234, 218, 190), (216, 198, 168))
    plaque = ((255, 250, 238), (140, 95, 60))
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

class Creator(Theme):                     # creative inventory: creator's studio (only the sides stick out: tabs live above/below)
    pads = (14, 0, 14, 0)
    band = [OUT, (150, 140, 220), (222, 204, 255), (255, 255, 255), (170, 150, 230), (100, 80, 170), OUT]
    def feature(self, l, x, w): return grad([(24, 18, 50), (54, 44, 100), (150, 140, 220)], l)   # dark: the game writes white here
    slot = ((70, 60, 120), (230, 225, 252), (48, 40, 94), (36, 30, 74))
    plaque = ((240, 236, 252), (110, 100, 170))
    def bg(self, x, y, w, h):
        c = grad([(84, 68, 146), (62, 50, 118)], y / h)
        if abs((x - y) % 60 - 30) < 4: c = mix(c, cyc((x + y) / 200), 0.25)
        if (x * 7 + y * 13) % 83 == 0: c = mix(c, WHITE, 0.8)
        return c
    def ornaments(self, img, L, T, w, h):
        S = img.size
        for side in (-1, 1):
            x0 = L - 2 if side < 0 else L + w + 1
            for k, y in enumerate(range(T + 10, T + h - 6, 16)):
                crystal_shard(img, S, (x0, y + 3), (x0 + side * (11 - k % 2 * 3), y - 4), 2.6, cyc(k / 8), line=(60, 40, 110))
    def motif(self, img, x, y, r): star(img, x, y, 0.5 + 0.5 * r.random(), cyc(r.random()))
