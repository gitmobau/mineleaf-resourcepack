# Aurora HUD XL, themed container screens that stick out of their vanilla rectangle.
# Each screen gets its own look (inventory = star observatory, crafting = maker's workshop, furnace = celestial
# inferno, blast furnace = supernova forge, smoker = cloud smoker, chest = treasure vault, shulker = End shell).
#
# The game blits a fixed 176xN UV window of a 256x256 texture. Here the texture holds the bigger art from (0,0)
# and every corner of every blit carries two marker texels (see position_tex_color.vsh):
#   marker (pad_x, pad_y, 167, role) at the corner texel, shift (du, dv, 168, role) one texel inward along x.
# The shader moves the vertex out by the pads and its UV by the shift, so the vanilla slots stay where the game
# expects them and the frame, crests and ornaments are drawn around them.
import os, sys, math, json, random
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # build.py runs scripts with -I
import magic
from hud_xl import cyc, mix, C, over, put, star, OUT, WHITE, MARK, TX, PREVIEWS, AURORA

SHIFT = 168
rnd = random.Random

def ref(rel):
    return magic.ref(rel)

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

# ------------------------------------------------------------------ containers
# name: (theme, vanilla height, label plaques in vanilla coords (x0, y0, x1, y1), keep-clear areas, blits)
TITLE = (5, 3, 100, 16)
INV = (5, 69, 90, 81)
SCREENS = {
    'inventory':      (Observatory(), 166, [(94, 5, 170, 17)], [(102, 59, 126, 80)], 'single'),
    'crafting_table': (Fabricator(),  166, [(26, 3, 112, 16), INV], [(3, 32, 27, 54)], 'single'),
    'furnace':        (Inferno(),     166, [(38, 3, 138, 16), INV], [(18, 32, 42, 54)], 'single'),
    'blast_furnace':  (Supernova(),   166, [(38, 3, 138, 16), INV], [(18, 32, 42, 54)], 'single'),
    'smoker':         (Clouds(),      166, [(38, 3, 138, 16), INV], [(18, 32, 42, 54)], 'single'),
    'generic_54':     (Vault(),       222, [TITLE, (5, 127, 90, 139)], [], 'chest'),
    'shulker_box':    (EndShell(),    166, [TITLE, INV], [], 'single'),
}

def quads(kind, h):
    """vanilla blits as (v0, v1) texel rows; the chest draws rows*18+17 of the top part plus the bottom 96"""
    if kind == 'single': return [(0, h, 'tb')]
    return [(0, r * 18 + 17, 't') for r in range(1, 7)] + [(126, 222, 'b')]

def write_markers(img, kind, h, pads):
    l, t, r, b = pads
    for (v0, v1, edge) in quads(kind, h):
        top_pad = t if 't' in edge else 0; bot_pad = b if 'b' in edge else 0
        dv_top = 0 if v0 == 0 else t                       # UV shift of this blit's top edge
        dv_bot = t + bot_pad                               # ... and of its bottom edge
        for (x, y, role, px_, py_, du, dv) in ((0, v0, 1, l, top_pad, 0, dv_top), (175, v0, 2, r, top_pad, l + r, dv_top),
                                               (0, v1 - 1, 3, l, bot_pad, 0, dv_bot), (175, v1 - 1, 4, r, bot_pad, l + r, dv_bot)):
            if role in (1, 2) and v0 != 0 and img.getpixel((x, y))[2] == MARK: continue
            img.putpixel((x, y), (px_, py_, MARK, role))
            img.putpixel((x + (1 if role in (1, 3) else -1), y), (du, dv, SHIFT, role))

def build(name):
    theme, h, plaques, keep, kind = SCREENS[name]
    l, t, r, b = theme.pads
    w = 176; AW, AH = w + l + r, h + t + b
    assert AW <= 256 and AH <= 256, name
    v = ref('gui/container/%s.png' % name)
    art = Image.new('RGBA', (AW, AH))
    used = set()
    # panel + frame band (rounded rect from -4 to +w+3 around the vanilla rectangle)
    band = theme.band; BW = len(band)
    x0, y0, x1, y1, R = l - 4, t - 4, l + w + 3, t + h + 3, 6
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            cx = min(max(x, x0 + R), x1 - R); cy = min(max(y, y0 + R), y1 - R)
            d = math.hypot(x - cx, y - cy)
            if d > R + 0.4: continue
            e = min(x - x0, x1 - x, y - y0, y1 - y)
            if (x < x0 + R or x > x1 - R) and (y < y0 + R or y > y1 - R): e = int(R - d)
            sx, sy = x - l, y - t
            if e < BW:
                c = band[e]
            else:
                c = theme.bg(sx, sy, w, h)
            art.putpixel((x, y), C(c))
    # player window (black area of the vanilla texture)
    blk = [(x + l, y + t) for y in range(h) for x in range(w) if magic.is_rgb(v.getpixel((x, y)), 0)]
    if blk: theme.window(art, blk); used |= set(blk)
    # slots
    for (sx, sy, s) in magic.find_slots(v, w, h):
        rim_tl, rim_br, top, bot = theme.slot
        for j in range(s):
            for i in range(s):
                if i in (0, s - 1) and j in (0, s - 1): continue
                if i == 0 or j == 0: c = rim_tl
                elif i == s - 1 or j == s - 1: c = rim_br
                else:
                    c = mix(top, bot, j / s)
                    if i + j in (3, 4): c = mix(c, WHITE, 0.25)
                art.putpixel((l + sx + i, t + sy + j), C(c))
        used |= rect(art.size, l + sx - 2, t + sy - 2, l + sx + s + 1, t + sy + s + 1)
    # other vanilla decorations (arrows, flame icons) in the theme colours
    feats = [(x, y) for y in range(4, h - 4) for x in range(4, w - 4)
             if v.getpixel((x, y))[3] and not magic.is_rgb(v.getpixel((x, y)), 198) and (x + l, y + t) not in used]
    for (x, y) in feats:
        p = v.getpixel((x, y)); lum = (p[0] + p[1] + p[2]) / 765
        art.putpixel((x + l, y + t), C(theme.feature(lum, x, w)))
    for (x, y) in feats:
        used |= rect(art.size, x + l - 1, y + t - 1, x + l + 1, y + t + 1)
    # label plaques (vanilla text is dark grey, so it needs a light plate)
    for (px0, py0, px1, py1) in plaques:
        fill, line = theme.plaque
        m = rect(art.size, l + px0, t + py0, l + px1, t + py1)
        m -= {(l + px0, t + py0), (l + px1, t + py0), (l + px0, t + py1), (l + px1, t + py1)}
        paint(art, m, lambda x, y: mix(fill, WHITE, 0.3) if y == t + py0 + 1 else fill, line=line, bevel=False)
        used |= rect(art.size, l + px0 - 2, t + py0 - 2, l + px1 + 2, t + py1 + 2)
    for (kx0, ky0, kx1, ky1) in keep:
        used |= rect(art.size, l + kx0, t + ky0, l + kx1, t + ky1)
    # small theme motifs in free panel space (not between chest rows: that part gets cut)
    rr = rnd(sum(map(ord, name)))
    placed = 0
    for _ in range(3000):
        x = rr.randint(l + 8, l + w - 9); y = rr.randint(t + 8, t + h - 9)
        if kind == 'chest' and t + 14 < y < t + 142: continue
        if all((xx, yy) not in used for xx in range(x - 3, x + 4) for yy in range(y - 3, y + 4)):
            theme.motif(art, x, y, rr); used |= rect(art.size, x - 4, y - 4, x + 4, y + 4); placed += 1
            if placed >= 10: break
    theme.ornaments(art, l, t, w, h)
    img = Image.new('RGBA', (256, 256)); img.alpha_composite(art)
    write_markers(img, kind, h, theme.pads)
    p = TX + 'gui/container/%s.png' % name
    os.makedirs(os.path.dirname(p), exist_ok=True); img.save(p, optimize=True)
    return img

# ------------------------------------------------------------------ shader emulation (preview + self-test)
ROLE = [1, 3, 4, 2]
def emulate(tex, quad, uv):
    """run position_tex_color.vsh on one GUI quad: quad/uv = (x0, y0, x1, y1) in GUI px / texels"""
    px = tex.load(); W, Hh = tex.size
    verts = [((quad[0], quad[1]), (uv[0], uv[1])), ((quad[0], quad[3]), (uv[0], uv[3])),
             ((quad[2], quad[3]), (uv[2], uv[3])), ((quad[2], quad[1]), (uv[2], uv[1]))]
    out = []
    for vid, ((x, y), (u, v)) in enumerate(verts):
        role = ROLE[vid % 4]; d = (1 if role in (1, 3) else -1, 1 if role <= 2 else -1)
        m = px[int(math.floor(u + d[0] * 0.5)), int(math.floor(v + d[1] * 0.5))]
        if m[2] == MARK and m[3] == role:
            x -= d[0] * m[0]; y -= d[1] * m[1]
            s = px[int(math.floor(u + d[0] * 1.5)), int(math.floor(v + d[1] * 0.5))]
            if s[2] == SHIFT and s[3] == role: u += s[0]; v += s[1]
        out.append((x, y, u, v))
    (qx0, qy0, u0, v0), (_, qy1, _, v1), (qx1, _, u1, _) = out[0], out[1], out[2]
    assert (qx1 - qx0, qy1 - qy0) == (u1 - u0, v1 - v0), (quad, uv, out)    # stays pixel perfect
    assert out[3] == (qx1, qy0, u1, v0) and out[1][0] == qx0 and out[2][1] == qy1, out
    piece = tex.crop((int(u0), int(v0), int(u1), int(v1))).copy()
    pp = piece.load()
    for y in range(piece.height):                              # fragment shader: hide marker texels
        for x in range(piece.width):
            q = pp[x, y]
            if q[2] in (MARK, SHIFT) and 1 <= q[3] <= 4:
                ny = y + (1 if q[3] <= 2 else -1)
                pp[x, y] = tex.getpixel((int(u0) + x, int(v0) + ny))
    return (int(qx0), int(qy0)), piece

def screen(name, tex, rows=6):
    theme, h, *_ = SCREENS[name]
    W, Hh = 300, 290
    sc = Image.new('RGBA', (W, Hh), (30, 26, 44, 255))
    hh = h if name != 'generic_54' else 114 + rows * 18
    lx, ly = (W - 176) // 2, (Hh - hh) // 2 + 6
    if name == 'generic_54':
        top = rows * 18 + 17
        for q, uv in (((lx, ly, lx + 176, ly + top), (0, 0, 176, top)),
                      ((lx, ly + top, lx + 176, ly + top + 96), (0, 126, 176, 222))):
            at, piece = emulate(tex, q, uv); sc.alpha_composite(piece, at)
    else:
        at, piece = emulate(tex, (lx, ly, lx + 176, ly + h), (0, 0, 176, h)); sc.alpha_composite(piece, at)
    return sc, (lx, ly)

def previews(imgs):
    from PIL import ImageFont
    F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 8)
    tiles = []
    labels = {'inventory': ('Fabricación', 97, 8, None), 'crafting_table': ('Fabricación', 29, 6, 'Inventario'),
              'furnace': ('Horno', None, 6, 'Inventario'), 'blast_furnace': ('Alto horno', None, 6, 'Inventario'),
              'smoker': ('Ahumador', None, 6, 'Inventario'), 'generic_54': ('Cofre grande', 8, 6, 'Inventario'),
              'shulker_box': ('Caja de shulker', 8, 6, 'Inventario')}
    icons = ['diamond_sword', 'netherite_pickaxe', 'diamond_axe', 'diamond_chestplate', 'netherite_helmet']
    for name in SCREENS:
        for rows in ((6, 3) if name == 'generic_54' else (6,)):
            sc, (lx, ly) = screen(name, imgs[name], rows)
            d = ImageDraw.Draw(sc)
            title, tx, ty, inv = labels[name]
            if tx is None: tx = (176 - d.textlength(title, font=F)) // 2
            d.text((lx + tx, ly + ty - 1), title, font=F, fill=(64, 64, 64))
            hh = SCREENS[name][1] if name != 'generic_54' else 114 + rows * 18
            if inv: d.text((lx + 8, ly + hh - 95), inv, font=F, fill=(64, 64, 64))
            v = ref('gui/container/%s.png' % name)
            slots = magic.find_slots(v, 176, SCREENS[name][1])
            for k, (sx, sy, s) in enumerate(slots):
                if name == 'generic_54' and sy >= 17 + rows * 18 and sy < 126: continue
                yy = sy if not (name == 'generic_54' and sy >= 126) else sy - 126 + rows * 18 + 17
                if k % 3 == 0:
                    ic = Image.open(AURORA + 'item/%s.png' % icons[k % len(icons)]).convert('RGBA').crop((0, 0, 16, 16))
                    sc.alpha_composite(ic, (lx + sx + 1 + (s - 18) // 2, ly + yy + 1 + (s - 18) // 2))
            tiles.append(sc)
    k = 2; cols = 3
    W, Hh = tiles[0].width * k, tiles[0].height * k
    sheet = Image.new('RGB', (cols * W + (cols + 1) * 10, ((len(tiles) + cols - 1) // cols) * (Hh + 10) + 10), (20, 18, 30))
    for i, tl in enumerate(tiles):
        sheet.paste(tl.resize((W, Hh), Image.NEAREST), (10 + (i % cols) * (W + 10), 10 + (i // cols) * (Hh + 10)))
    os.makedirs(PREVIEWS, exist_ok=True)
    sheet.save(PREVIEWS + '/menus_xl.png')

if __name__ == '__main__':
    imgs = {n: build(n) for n in SCREENS}
    previews(imgs)
    print('menus ok')
