# Aurora "Marco magico" redesign: containers (static, detailed) + animated GUI sprites.
import os, math, json, random
from PIL import Image

HOME = os.path.expanduser('~')
# Paths can be overridden by build.py (AURORA_REF = folder holding assets/minecraft of vanilla 26.3,
# AURORA_RP = resourcepacks folder, AURORA_PREVIEWS = where preview images go).
REF_ROOT = os.environ.get('AURORA_REF', HOME + '/ref63')
RP = os.environ.get('AURORA_RP', HOME + '/mnt/.minecraft/resourcepacks')
REF = REF_ROOT + '/assets/minecraft/textures/'
PACK = RP + '/Aurora Pack'
PREVIEWS = os.environ.get('AURORA_PREVIEWS', RP + '/Aurora Pack')
TX = PACK + '/assets/minecraft/textures/'

VIVID = [(80,220,255),(120,175,255),(170,140,255),(220,130,255),(255,125,220),
         (255,150,175),(255,190,135),(255,228,120),(175,248,135),(110,245,205)]
OUT = (58, 40, 108)        # outline violet
WHITE = (255, 255, 255)
PEARL = (250, 248, 255)

def cyc(t, pal=VIVID):
    t = (t % 1.0) * len(pal); i = int(t) % len(pal); f = t - int(t)
    a = pal[i]; b = pal[(i + 1) % len(pal)]
    return tuple(a[k] + (b[k] - a[k]) * f for k in range(3))

def mix(a, b, f):
    return tuple(a[k] + (b[k] - a[k]) * f for k in range(3))

def C(c, a=255):
    return tuple(int(max(0, min(255, round(v)))) for v in c[:3]) + (int(max(0, min(255, a))),)

def ref(rel):
    return Image.open(REF + rel).convert('RGBA')

def save(im, rel, mcmeta=None):
    p = TX + rel
    os.makedirs(os.path.dirname(p), exist_ok=True)
    im.save(p, optimize=True)
    if mcmeta is not None:
        with open(p + '.mcmeta', 'w') as f:
            json.dump(mcmeta, f, indent=2)

# ------------------------------------------------------------------ pixel art
CAT_PAL = {'o': OUT, 'w': (252, 250, 255), 'l': (214, 200, 246), 'p': (255, 160, 205),
           'e': (90, 215, 255), 'k': OUT, 'y': (255, 120, 210), 'g': (120, 235, 255),
           's': (255, 236, 140), 'z': (170, 150, 235), 'm': (255, 248, 200)}

CAT_SIT = [
    ".o.........o....",
    "opo.......opo...",
    "owwo..s..owwo...",
    "owwwoooooowwo...",
    "owwwwwwwwwwwo...",
    "oweewwwwwweewo..",
    "owwwwwwpwwwwwo..",
    "owlwwwkwkwwwlo..",
    ".owwwwwwwwwwo...",
    "..ooyygyyyoo....",
    "..owwwwwwwwo..o.",
    ".owwwwwwwwwwo.lo",
    ".owlwwwwwwwlwolo",
    ".owlwwwwwwwlwwlo",
    ".owwwwwwwwwwwwo.",
    ".oowwowwowwwoo..",
    "..oooooooooo....",
]
CAT_PEEK = [
    ".o...........o.",
    "opo....s....opo",
    "owwo.......owwo",
    "owwwoooooooowwo",
    "owwwwwwwwwwwwwo",
    "oweewwwwwwweewo",
    "owwwwwwpwwwwwwo",
    "owwwwwkwkwwwwwo",
    "oowwwwwwwwwwwoo",
    "owwo.......owwo",
]
CAT_SLEEP = [
    "..............z.....",
    "...o..o.....z.......",
    "..opoopo...........",
    "..owwwwwoooooooo....",
    ".owwwwwwwwwwwwwwwo..",
    ".owkkwwkkwwwwwwwwwo.",
    ".owwwpwwwwwwwwlwwwwo",
    "..owwwwwwwwwwwlwwwwo",
    "..oyygywwwwwwwlwwwo.",
    "...owwwwlllllwwwwwo.",
    "....ooooooooooooooo.",
]

def draw_art(img, art, x0, y0, pal=CAT_PAL):
    for j, row in enumerate(art):
        for i, ch in enumerate(row):
            if ch in pal and 0 <= x0 + i < img.width and 0 <= y0 + j < img.height:
                img.putpixel((x0 + i, y0 + j), C(pal[ch]))

def sparkle(img, x, y, t, big=True):
    col = cyc(t)
    pts = [((0, 0), WHITE)]
    pts += [((dx, dy), mix(WHITE, col, 0.55)) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
    if big:
        pts += [((dx, dy), col) for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2))]
    for (dx, dy), c in pts:
        if 0 <= x + dx < img.width and 0 <= y + dy < img.height:
            img.putpixel((x + dx, y + dy), C(c))

def gem(img, cx, cy, r=3):
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            d = abs(dx) + abs(dy)
            if d > r:
                continue
            if d == r:
                c = OUT
            else:
                c = mix((110, 235, 255), (255, 130, 220), (dy + r) / (2 * r))
                if dx < 0 and dy < 0:
                    c = mix(c, WHITE, 0.45)
            img.putpixel((cx + dx, cy + dy), C(c))
    img.putpixel((cx - 1, cy - 1), C(WHITE))

# ------------------------------------------------------------------ containers
def is_rgb(p, v):
    return p[3] == 255 and p[0] == v and p[1] == v and p[2] == v

def find_slots(v, w, h):
    slots = []
    for y in range(h - 17):
        for x in range(w - 17):
            if not is_rgb(v.getpixel((x, y)), 55):
                continue
            if (x > 0 and is_rgb(v.getpixel((x - 1, y)), 55)) or (y > 0 and is_rgb(v.getpixel((x, y - 1)), 55)):
                continue
            for s in (26, 18):
                if x + s - 1 >= w or y + s - 1 >= h:
                    continue
                if all(is_rgb(v.getpixel((x + i, y)), 55) for i in range(s - 1)) \
                        and all(is_rgb(v.getpixel((x, y + j)), 55) for j in range(s - 1)) \
                        and is_rgb(v.getpixel((x + 1, y + 1)), 139) \
                        and is_rgb(v.getpixel((x + s - 2, y + s - 2)), 139) \
                        and is_rgb(v.getpixel((x + s - 1, y + s - 1)), 255):
                    slots.append((x, y, s))
                    break
    # dedupe overlapping detections (keep first)
    out = []
    for s in slots:
        if not any(abs(s[0] - o[0]) < 2 and abs(s[1] - o[1]) < 2 for o in out):
            out.append(s)
    return out

def build_container(name, w, h, cut_safe=False, cats=(), excl=(), stars=True, seed=1):
    v = ref('gui/container/%s.png' % name)
    img = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    slots = find_slots(v, w, h)
    used = [[False] * h for _ in range(w)]
    # --- panel fill + frame
    R = 3
    for y in range(h):
        for x in range(w):
            # rounded corners
            cx = R if x < R else (w - 1 - R if x > w - 1 - R else x)
            cy = R if y < R else (h - 1 - R if y > h - 1 - R else y)
            dist = math.hypot(x - cx, y - cy)
            if dist > R + 0.5:
                continue
            e = min(x, y, w - 1 - x, h - 1 - y)
            if dist > R - 0.5 and (x < R or x > w - 1 - R) and (y < R or y > h - 1 - R):
                e = 0
            t = x / w * 0.85 if cut_safe else (x / w * 0.6 + y / h * 0.3)
            if e == 0:
                c = OUT
            elif e == 1:
                c = cyc(t)
            elif e == 2:
                c = mix(cyc(t + 0.05), WHITE, 0.35)
            elif e == 3:
                c = WHITE
            else:
                c = mix(PEARL, cyc(t + 0.1), 0.07)
                if not cut_safe and (x + y) % 29 in (0, 1, 2):
                    c = mix(c, WHITE, 0.8)
            img.putpixel((x, y), C(c))
            if e <= 3:
                used[x][y] = True
    # --- player window / black areas -> aurora night sky
    blk = [(x, y) for y in range(h) for x in range(w) if is_rgb(v.getpixel((x, y)), 0)]
    if blk:
        bx0 = min(p[0] for p in blk); bx1 = max(p[0] for p in blk)
        by0 = min(p[1] for p in blk); by1 = max(p[1] for p in blk)
        rnd = random.Random(seed)
        for (x, y) in blk:
            u = (x - bx0) / max(1, bx1 - bx0); vv = (y - by0) / max(1, by1 - by0)
            c = mix((22, 14, 58), (92, 58, 150), vv)
            for k, (amp, off, th) in enumerate(((5, 0.25, 4.5), (4, 0.42, 3.5))):
                cyy = by0 + (by1 - by0) * off + amp * math.sin(u * 6.3 + k * 2)
                d = abs(y - cyy)
                if d < th:
                    c = mix(c, cyc(u * 0.6 + k * 0.3), (1 - d / th) * 0.75)
            img.putpixel((x, y), C(c))
            used[x][y] = True
        for _ in range(int((bx1 - bx0) * (by1 - by0) / 45)):
            sx = rnd.randint(bx0 + 1, bx1 - 1); sy = rnd.randint(by0 + 1, by1 - 1)
            img.putpixel((sx, sy), C(mix(WHITE, cyc(rnd.random()), 0.3)))
        # crescent moon
        mx, my = bx1 - 9, by0 + 6
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                if dx * dx + dy * dy <= 9 and (dx - 1.5) ** 2 + (dy + 1) ** 2 > 6:
                    img.putpixel((mx + dx, my + dy), C((255, 246, 200)))
    # --- slots
    for (sx, sy, s) in slots:
        big = s == 26
        for j in range(s):
            for i in range(s):
                x, y = sx + i, sy + j
                used[x][y] = True
                corner = (i in (0, s - 1)) and (j in (0, s - 1))
                if corner:
                    continue   # keep panel colour -> rounded slot
                if i == 0 or j == 0:
                    c = cyc(sx / w * 0.8) if big else (150, 128, 214)
                elif i == s - 1 or j == s - 1:
                    c = WHITE
                else:
                    c = mix((238, 232, 253), (222, 210, 249), j / s)
                    if (i + j) in (3, 4) or (i + j) in (s + 6, s + 7):
                        c = mix(c, WHITE, 0.7)     # glassy shine
                img.putpixel((x, y), C(c))
        if big:
            sparkle(img, sx + s - 3, sy + 2, 0.4, big=False)
    # --- remaining vanilla decorations (arrows, flame icons, labels art): aurora
    for y in range(h):
        for x in range(w):
            if used[x][y]:
                continue
            p = v.getpixel((x, y))
            if p[3] == 0 or is_rgb(p, 198):
                continue
            l = (p[0] + p[1] + p[2]) / 765
            c = mix(cyc(x / w * 0.9 + 0.2), WHITE, max(0, (l - 0.55)) * 1.6) if l > 0.3 else mix(OUT, cyc(x / w), 0.3)
            img.putpixel((x, y), C(c))
            used[x][y] = True
    # --- corner gems + edge ornaments
    for (gx, gy) in ((3, 3), (w - 4, 3), (3, h - 4), (w - 4, h - 4)):
        gem(img, gx, gy)
    for gx in range(28, w - 24, 30):
        gem(img, gx, 2, r=2)
        gem(img, gx, h - 3, r=2)
    if not cut_safe:
        for gy in range(30, h - 24, 34):
            gem(img, 2, gy, r=2)
            gem(img, w - 3, gy, r=2)
    # --- cats
    for art, cx, cy in cats:
        draw_art(img, art, cx, cy)
        for j in range(len(art)):
            for i in range(len(art[0])):
                if 0 <= cx + i < w and 0 <= cy + j < h:
                    used[cx + i][cy + j] = True
    # --- sparkles in free space
    if stars:
        rnd = random.Random(seed * 7)
        def free(x, y, r):
            for yy in range(y - r, y + r + 1):
                for xx in range(x - r, x + r + 1):
                    if not (0 <= xx < w and 0 <= yy < h) or used[xx][yy]:
                        return False
            for (ex0, ey0, ex1, ey1) in excl:
                if ex0 - r <= x <= ex1 + r and ey0 - r <= y <= ey1 + r:
                    return False
            return True
        placed = 0
        for _ in range(4000):
            x = rnd.randint(4, w - 5); y = rnd.randint(4, h - 5)
            big = rnd.random() < 0.45
            if free(x, y, 3 if big else 2):
                sparkle(img, x, y, rnd.random(), big)
                for yy in range(y - 2, y + 3):
                    for xx in range(x - 2, x + 3):
                        used[xx][yy] = True
                placed += 1
                if placed >= 14:
                    break
    return img, slots

TITLE = (0, 3, 176, 16)
def inv_label(h):
    return (0, h - 96, 120, h - 83)

def containers():
    res = {}
    img, sl = build_container('inventory', 176, 166, cats=[(CAT_SLEEP, 128, 63)],
                              excl=[(96, 5, 160, 17), inv_label(166), (102, 59, 126, 80)], seed=3)
    save(img, 'gui/container/inventory.png'); res['inventory'] = (img, 166, len(sl))
    img, sl = build_container('crafting_table', 176, 166, cats=[(CAT_SIT, 150, 52)],
                              excl=[TITLE, inv_label(166), (3, 32, 27, 54)], seed=5)
    save(img, 'gui/container/crafting_table.png'); res['crafting_table'] = (img, 166, len(sl))
    for n, s in (('furnace', 7), ('blast_furnace', 8), ('smoker', 9)):
        img, sl = build_container(n, 176, 166, cats=[(CAT_SIT, 148, 6)],
                                  excl=[(20, 3, 156, 16), inv_label(166), (18, 32, 42, 54)], seed=s)
        save(img, 'gui/container/%s.png' % n); res[n] = (img, 166, len(sl))
    img, sl = build_container('generic_54', 176, 222, cut_safe=True, cats=[(CAT_PEEK, 152, 3)],
                              excl=[TITLE], stars=False, seed=11)
    save(img, 'gui/container/generic_54.png'); res['generic_54'] = (img, 222, len(sl))
    img, sl = build_container('shulker_box', 176, 166, cats=[(CAT_PEEK, 152, 3)],
                              excl=[TITLE, inv_label(166)], seed=13)
    save(img, 'gui/container/shulker_box.png'); res['shulker_box'] = (img, 166, len(sl))
    return res

# ------------------------------------------------------------------ animated sprites
def anim_meta(n, ft, extra=None, w=None, h=None):
    a = {"frametime": ft, "interpolate": False}
    if w: a["width"] = w; a["height"] = h
    m = {"animation": a}
    if extra: m.update(extra)
    return m

def slot_highlights():
    N = 16
    back = Image.new('RGBA', (24, 24 * N)); front = Image.new('RGBA', (24, 24 * N))
    ring = [(x, 0) for x in range(24)] + [(23, y) for y in range(1, 24)] + \
           [(x, 23) for x in range(22, -1, -1)] + [(0, y) for y in range(22, 0, -1)]
    for f in range(N):
        ph = f / N
        pulse = 0.5 + 0.5 * math.sin(ph * 2 * math.pi)
        for y in range(24):
            for x in range(24):
                e = min(x, y, 23 - x, 23 - y)
                if 3 <= e:
                    c = mix(WHITE, cyc((x + y) / 46 + ph), 0.35 + 0.15 * pulse)
                    back.putpixel((x, f * 24 + y), C(c, 150 + 40 * pulse))
                elif e >= 1:
                    back.putpixel((x, f * 24 + y), C(cyc((x + y) / 46 + ph), 70 + 50 * pulse * (e / 3)))
        # front: aurora ring with travelling sparkle
        for i, (x, y) in enumerate(ring):
            front.putpixel((x, f * 24 + y), C(cyc(i / len(ring) + ph), 230))
            if 0 < x < 23 and 0 < y < 23:
                pass
        for k in range(2):
            i = int((ph + k * 0.5) * len(ring)) % len(ring)
            x, y = ring[i]
            front.putpixel((x, f * 24 + y), C(WHITE))
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < 24 and 0 <= yy < 24:
                    front.putpixel((xx, f * 24 + yy), C(mix(WHITE, cyc(ph), 0.3), 240))
    gui = {"gui": {"scaling": {"type": "nine_slice", "width": 24, "height": 24, "border": 4}}}
    save(back, 'gui/sprites/container/slot_highlight_back.png', anim_meta(N, 2, gui, 24, 24))
    save(front, 'gui/sprites/container/slot_highlight_front.png', anim_meta(N, 2, gui, 24, 24))
    return back, front

CAT_FACE_OPEN = [
    ".o.......o.",
    "opo.....opo",
    "owwooooowwo",
    "owwwwwwwwwo",
    "oweewwweewo",
    "owwwwpwwwwo",
    "owwwkwkwwwo",
    ".owwwwwwwo.",
    "..ooyyyoo..",
]
CAT_FACE_BLINK = [r.replace('ee', 'kk') for r in CAT_FACE_OPEN]
CAT_FACE_HAPPY = [r.replace('ee', 'kk') if i == 4 else r for i, r in enumerate(CAT_FACE_OPEN)]

def recipe_button():
    def frame(face, hi, ph):
        im = Image.new('RGBA', (20, 18))
        for y in range(18):
            for x in range(20):
                corner = (x in (0, 19)) and (y in (0, 17))
                if corner:
                    continue
                e = min(x, y, 19 - x, 17 - y)
                if e == 0:
                    c = OUT
                elif e == 1:
                    c = cyc(x / 20 * 0.6 + ph) if hi else mix(cyc(x / 20 * 0.6), WHITE, 0.3)
                else:
                    c = mix(WHITE, cyc((x + y) / 40 + ph), 0.22 if hi else 0.12)
                im.putpixel((x, y), C(c))
        draw_art(im, face, 4, 5)
        if hi:
            sparkle(im, 3, 3, ph, big=False); sparkle(im, 16, 3, ph + 0.5, big=False)
        return im
    # normal: blink every ~4s
    frames = [frame(CAT_FACE_OPEN, False, 0), frame(CAT_FACE_BLINK, False, 0)]
    strip = Image.new('RGBA', (20, 18 * 2))
    for i, f in enumerate(frames): strip.paste(f, (0, i * 18))
    save(strip, 'gui/sprites/recipe_book/button.png',
         {"animation": {"width": 20, "height": 18, "frames": [
             {"index": 0, "time": 70}, {"index": 1, "time": 3}, {"index": 0, "time": 6}, {"index": 1, "time": 3}]}})
    N = 8
    strip2 = Image.new('RGBA', (20, 18 * N))
    for i in range(N):
        strip2.paste(frame(CAT_FACE_HAPPY, True, i / N), (0, i * 18))
    save(strip2, 'gui/sprites/recipe_book/button_highlighted.png', anim_meta(N, 2, None, 20, 18))
    return strip, strip2

def furnace_sprites():
    out = {}
    for kind in ('furnace', 'blast_furnace', 'smoker'):
        lit = ref('gui/sprites/container/%s/lit_progress.png' % kind)
        N = 8
        st = Image.new('RGBA', (14, 14 * N))
        for f in range(N):
            for y in range(14):
                for x in range(14):
                    p = lit.getpixel((x, y))
                    if p[3] == 0 or (p[0] == p[1] == p[2] and p[0] in (198, 139)):
                        continue
                    l = (p[0] + p[1] + p[2]) / 765
                    flick = 0.5 + 0.5 * math.sin((y / 14 + f / N) * 2 * math.pi * 2 + x)
                    c = mix(cyc(0.95 - y / 14 * 0.5 + f / N * 0.3), WHITE, max(0, l - 0.5) + 0.25 * flick)
                    st.putpixel((x, f * 14 + y), C(c, p[3]))
        save(st, 'gui/sprites/container/%s/lit_progress.png' % kind, anim_meta(N, 2, None, 14, 14))
        arr = ref('gui/sprites/container/%s/burn_progress.png' % kind)
        N2 = 12
        st2 = Image.new('RGBA', (24, 16 * N2))
        for f in range(N2):
            for y in range(16):
                for x in range(24):
                    p = arr.getpixel((x, y))
                    if p[3] == 0 or (p[0] == p[1] == p[2] and p[0] in (198, 139)):
                        continue
                    l = (p[0] + p[1] + p[2]) / 765
                    c = cyc(x / 24 * 0.7 - f / N2)
                    if (x - f * 2) % 24 in (0, 1):
                        c = mix(c, WHITE, 0.8)
                    c = mix(c, WHITE, max(0, l - 0.6))
                    st2.putpixel((x, f * 16 + y), C(c, p[3]))
        save(st2, 'gui/sprites/container/%s/burn_progress.png' % kind, anim_meta(N2, 2, None, 24, 16))
        out[kind] = (st, st2)
    return out

def hud():
    H = 'gui/sprites/hud/'
    hb = ref(H + 'hotbar.png')
    N = 24
    rnd = random.Random(42)
    twinkles = [(rnd.randint(0, 181), rnd.choice([0, 1, 20, 21]), rnd.random()) for _ in range(14)]
    st = Image.new('RGBA', (182, 22 * N))
    for f in range(N):
        ph = f / N
        for y in range(22):
            for x in range(182):
                p = hb.getpixel((x, y))
                if p[3] == 0:
                    continue
                l = (p[0] + p[1] + p[2]) / 765
                if p[3] < 255:   # slot interiors (translucent)
                    st.putpixel((x, f * 22 + y), C((44, 30, 86), p[3] + 10))
                    continue
                if l < 0.2:
                    c = OUT
                else:
                    c = mix(cyc(x / 182 * 0.9 - ph), WHITE, 0.15 + max(0, l - 0.45) * 1.2)
                st.putpixel((x, f * 22 + y), C(c))
        for (tx, ty, tp) in twinkles:
            b = max(0, math.sin((ph + tp) * 2 * math.pi)) ** 3
            if b > 0.05 and hb.getpixel((tx, ty))[3] == 255:
                st.putpixel((tx, f * 22 + ty), C(mix(st.getpixel((tx, f * 22 + ty)), WHITE, b)))
    save(st, H + 'hotbar.png', anim_meta(N, 3, None, 182, 22))
    sel = ref(H + 'hotbar_selection.png')
    N = 16
    st2 = Image.new('RGBA', (24, 23 * N))
    for f in range(N):
        ph = f / N
        pulse = 0.5 + 0.5 * math.sin(ph * 2 * math.pi)
        for y in range(23):
            for x in range(24):
                p = sel.getpixel((x, y))
                if p[3] == 0:
                    continue
                l = (p[0] + p[1] + p[2]) / 765
                if l < 0.25:
                    c = OUT
                else:
                    c = mix(cyc((x + y) / 47 + ph), WHITE, 0.25 + 0.55 * pulse * l)
                st2.putpixel((x, f * 23 + y), C(c, p[3]))
        for k, (cx, cy) in enumerate(((1, 1), (22, 1), (22, 21), (1, 21))):
            if int(ph * 4) == k:
                st2.putpixel((cx, f * 23 + cy), C(WHITE))
    save(st2, H + 'hotbar_selection.png', anim_meta(N, 2, None, 24, 23))
    for n in ('hotbar_offhand_left', 'hotbar_offhand_right'):
        im = ref(H + n + '.png'); o = Image.new('RGBA', im.size)
        for y in range(im.height):
            for x in range(im.width):
                p = im.getpixel((x, y))
                if p[3] == 0: continue
                l = (p[0] + p[1] + p[2]) / 765
                if p[3] < 255: c = C((44, 30, 86), p[3] + 10)
                elif l < 0.2: c = C(OUT)
                else: c = C(mix(cyc(x / im.width * 0.4 + 0.3), WHITE, 0.15 + max(0, l - 0.45) * 1.2))
                o.putpixel((x, y), c)
        save(o, H + n + '.png')
    xp = ref(H + 'experience_bar_progress.png')
    N = 16
    st3 = Image.new('RGBA', (182, 5 * N))
    for f in range(N):
        for y in range(5):
            for x in range(182):
                p = xp.getpixel((x, y))
                if p[3] == 0: continue
                l = (p[0] + p[1] + p[2]) / 765
                c = mix(cyc(x / 182 * 0.9 - f / N), WHITE, 0.1 + l * 0.5)
                if (x - f * 12) % 182 in (0, 1, 2): c = mix(c, WHITE, 0.7)
                st3.putpixel((x, f * 5 + y), C(c, p[3]))
    save(st3, H + 'experience_bar_progress.png', anim_meta(N, 2, None, 182, 5))
    return st, st2, st3

if __name__ == '__main__':
    res = containers()
    for k, (im, h, n) in res.items():
        print(k, 'slots', n)
    sh = slot_highlights(); rb = recipe_button(); fs = furnace_sprites(); hh = hud()
    # ---------------- preview sheet
    S = 2
    sheet = Image.new('RGBA', (3 * 176 * S + 80, 2 * 222 * S + 300), (70, 60, 90, 255))
    order = ['inventory', 'crafting_table', 'furnace', 'generic_54', 'shulker_box', 'blast_furnace']
    for i, k in enumerate(order):
        im, h, _ = res[k]
        sheet.alpha_composite(im.crop((0, 0, 176, h)).resize((176 * S, h * S), Image.NEAREST),
                              (20 + (i % 3) * (176 * S + 20), 20 + (i // 3) * (222 * S + 20)))
    # overlay recipe button + slot highlight on inventory to see them in context
    ix, iy = 20, 20
    sheet.alpha_composite(rb[1].crop((0, 0, 20, 18)).resize((40, 36), Image.NEAREST), (ix + 104 * S, iy + 61 * S))
    sheet.alpha_composite(sh[0].crop((0, 0, 24, 24)).resize((48, 48), Image.NEAREST), (ix + (8 - 4) * S, iy + (84 - 4) * S))
    sheet.alpha_composite(sh[1].crop((0, 0, 24, 24)).resize((48, 48), Image.NEAREST), (ix + (8 - 4) * S, iy + (84 - 4) * S))
    fx, fy = 20 + 2 * (176 * S + 20), 20
    sheet.alpha_composite(fs['furnace'][0].crop((0, 0, 14, 14)).resize((28, 28), Image.NEAREST), (fx + 56 * S, fy + 36 * S))
    sheet.alpha_composite(fs['furnace'][1].crop((0, 0, 16, 16)).resize((32, 32), Image.NEAREST), (fx + 79 * S, fy + 34 * S))
    by = 2 * 222 * S + 60
    for f in range(4):
        sheet.alpha_composite(hh[0].crop((0, f * 6 * 22, 182, f * 6 * 22 + 22)).resize((364, 44), Image.NEAREST), (20, by + f * 52))
    sheet.alpha_composite(hh[1].crop((0, 0, 24, 23)).resize((48, 46), Image.NEAREST), (20 - 2, by - 2))
    for f in range(4):
        sheet.alpha_composite(hh[2].crop((0, f * 4 * 5, 182, f * 4 * 5 + 5)).resize((364, 10), Image.NEAREST), (420, by + f * 16))
    for f in range(4):
        sheet.alpha_composite(rb[0].crop((0, (f % 2) * 18, 20, (f % 2) * 18 + 18)).resize((60, 54), Image.NEAREST), (420 + f * 70, by + 80))
    os.makedirs(PREVIEWS, exist_ok=True)
    sheet.save(PREVIEWS + '/preview.png')
    frames = []
    for f in range(48):
        g = Image.new('RGBA', (420, 150), (60, 52, 84, 255))
        hbN = hh[0].height // 22
        g.alpha_composite(hh[0].crop((0, (f % hbN) * 22, 182, (f % hbN) * 22 + 22)).resize((364, 44), Image.NEAREST), (28, 10))
        sN = hh[1].height // 23
        g.alpha_composite(hh[1].crop((0, (f % sN) * 23, 24, (f % sN) * 23 + 23)).resize((48, 46), Image.NEAREST), (26 + 40 * 2 * 2, 8))
        xN = hh[2].height // 5
        g.alpha_composite(hh[2].crop((0, (f % xN) * 5, 140, (f % xN) * 5 + 5)).resize((280, 10), Image.NEAREST), (28, 60))
        bN = sh[0].height // 24
        for im_ in (sh[0], sh[1]):
            g.alpha_composite(im_.crop((0, (f % bN) * 24, 24, (f % bN) * 24 + 24)).resize((72, 72), Image.NEAREST), (28, 76))
        rN = rb[1].height // 18
        g.alpha_composite(rb[1].crop((0, (f % rN) * 18, 20, (f % rN) * 18 + 18)).resize((60, 54), Image.NEAREST), (120, 84))
        blink = 1 if f % 24 in (20, 21) else 0
        g.alpha_composite(rb[0].crop((0, blink * 18, 20, blink * 18 + 18)).resize((60, 54), Image.NEAREST), (196, 84))
        lit, arr = fs['furnace']
        g.alpha_composite(lit.crop((0, (f % 8) * 14, 14, (f % 8) * 14 + 14)).resize((42, 42), Image.NEAREST), (280, 90))
        g.alpha_composite(arr.crop((0, (f % 12) * 16, 24, (f % 12) * 16 + 16)).resize((72, 48), Image.NEAREST), (330, 88))
        frames.append(g.convert('RGB'))
    frames[0].save(PREVIEWS + '/anim_preview.gif', save_all=True, append_images=frames[1:], duration=100, loop=0)
    print('ok')
