# Aurora HUD XL: oversized, more ornate HUD frames (hotbar, selection, offhand) that stick out of their
# vanilla rectangles. The game always squeezes a GUI sprite into its fixed rectangle, so the textures carry
# 4 invisible marker pixels (one per corner) and the pack's core shader position_tex_color.vsh grows the quad.
#
# Marker pixel at each corner of every frame: RGBA = (pad_x, pad_y, 167, role)
#   role 1 = top-left, 2 = top-right, 3 = bottom-left, 4 = bottom-right
#   pad_x = pixels the sprite sticks out horizontally on that side, pad_y = vertically.
# The shader reads the corner texel of each vertex, moves the vertex out by (pad_x, pad_y) and the fragment
# shader discards the marker pixels. Bottom pads are 0: those sprites sit on the bottom edge of the screen.
import os, math, json
from PIL import Image, ImageDraw

HOME = os.path.expanduser('~')
# Paths can be overridden by build.py (AURORA_REF = folder holding assets/minecraft of vanilla 26.3,
# AURORA_RP = resourcepacks folder, AURORA_PREVIEWS = where preview images go).
REF_ROOT = os.environ.get('AURORA_REF', HOME + '/ref63')
RP = os.environ.get('AURORA_RP', HOME + '/mnt/.minecraft/resourcepacks')
REF = REF_ROOT + '/assets/minecraft/textures/'
PACK = RP + '/Aurora HUD XL'
TX = PACK + '/assets/minecraft/textures/'
AURORA = RP + '/Aurora Pack/assets/minecraft/textures/'
PREVIEWS = os.environ.get('AURORA_PREVIEWS', RP + '/Aurora HUD XL')
H = 'gui/sprites/hud/'
MARK = 167

VIVID = [(80,220,255),(120,175,255),(170,140,255),(220,130,255),(255,125,220),
         (255,150,175),(255,190,135),(255,228,120),(175,248,135),(110,245,205)]
OUT = (58, 40, 108)
DEEP = (34, 22, 70)
WHITE = (255, 255, 255)

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

def put(img, x, y, c):
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((x, y), c)

def over(img, x, y, c, a):
    """alpha-blend colour c with opacity a (0..1) onto pixel x,y"""
    if not (0 <= x < img.width and 0 <= y < img.height) or a <= 0: return
    p = img.getpixel((x, y)); pa = p[3] / 255
    na = a + pa * (1 - a)
    rgb = mix(p[:3], c, a / na) if pa > 0 else c
    img.putpixel((x, y), C(rgb, na * 255))

def markers(img, pads, fh, n):
    """write the 4 corner markers into every frame of a vertical strip"""
    l, t, r, b = pads; w = img.width
    for f in range(n):
        y0 = f * fh
        img.putpixel((0, y0), (l, t, MARK, 1)); img.putpixel((w - 1, y0), (r, t, MARK, 2))
        img.putpixel((0, y0 + fh - 1), (l, b, MARK, 3)); img.putpixel((w - 1, y0 + fh - 1), (r, b, MARK, 4))

def save(im, rel, n, fw, fh, ft):
    p = TX + rel
    os.makedirs(os.path.dirname(p), exist_ok=True)
    im.save(p, optimize=True)
    with open(p + '.mcmeta', 'w') as f:
        json.dump({"animation": {"frametime": ft, "interpolate": False, "width": fw, "height": fh}}, f, indent=2)

# ------------------------------------------------------------------ shared pieces
def frame_recolor(src, ox, oy, dst, ph, span, shine):
    """ornate version of a vanilla frame sprite: bevelled iridescent metal + deep translucent slots"""
    w, h = src.size
    A = lambda x, y: src.getpixel((x, y))[3] if 0 <= x < w and 0 <= y < h else 0
    for y in range(h):
        for x in range(w):
            p = src.getpixel((x, y))
            if p[3] == 0: continue
            l = (p[0] + p[1] + p[2]) / 765
            if p[3] < 255:                                    # slot interior
                g = y / max(1, h - 1)
                c = mix((52, 34, 104), DEEP, g)
                a = p[3] + 30
                if A(x, y - 1) == 255 and y > 0:              # inner glow under the top rim
                    c = mix(c, cyc(x / span - ph), 0.55); a = 230
                elif A(x - 1, y) == 255 or A(x + 1, y) == 255:
                    c = mix(c, cyc(x / span - ph + 0.3), 0.25)
                put(dst, ox + x, oy + y, C(c, a)); continue
            if l < 0.2:
                c = OUT
            else:
                c = cyc(x / span * 0.9 - ph)
                if A(x, y - 1) == 0 or A(x - 1, y) == 0: c = mix(c, WHITE, 0.6)        # outer bevel light
                elif A(x, y + 1) < 255 and A(x, y + 1) > 0: c = mix(c, OUT, 0.35)      # rim over a slot
                elif A(x, y + 1) == 0 or A(x + 1, y) == 0: c = mix(c, OUT, 0.45)       # outer bevel shade
                else: c = mix(c, WHITE, 0.2 + max(0, l - 0.45))
                d = abs((x + (h - y) * 0.7) - shine)                                  # travelling shine
                if d < 4: c = mix(c, WHITE, 0.75 * (1 - d / 4))
            put(dst, ox + x, oy + y, C(c))

def crystal(dst, poly, ph, seed, bright=1.0):
    """filled crystal shard with outline, vertical iridescent ramp, facet highlight and a rising glint"""
    m = Image.new('L', dst.size); ImageDraw.Draw(m).polygon(poly, fill=255)
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
    cx = (min(xs) + max(xs)) / 2; y0, y1 = min(ys), max(ys)
    ins = lambda x, y: 0 <= x < dst.width and 0 <= y < dst.height and m.getpixel((x, y)) > 0
    glint_y = y1 - ((ph * 1.5 + seed) % 1.0) * (y1 - y0 + 6)
    for y in range(dst.height):
        for x in range(dst.width):
            if not ins(x, y): continue
            if not (ins(x - 1, y) and ins(x + 1, y) and ins(x, y - 1) and ins(x, y + 1)):
                put(dst, x, y, C(OUT)); continue
            t = (y - y0) / max(1, y1 - y0)
            c = cyc(seed + t * 0.45 - ph)
            c = mix(c, WHITE, 0.55 if x <= cx else 0.12)                      # two facets
            if not ins(x - 1, y - 1): c = mix(c, WHITE, 0.6)                    # top-left edge
            if abs(y - glint_y) < 1.5: c = mix(c, WHITE, 0.85)
            c = mix(c, OUT, max(0, t - 0.75) * 1.2) if bright >= 1 else mix(c, OUT, 0.25)
            put(dst, x, y, C(c))
    # tip sparkle
    tip = min(poly, key=lambda p: p[1])
    if math.sin((ph + seed) * 2 * math.pi) > 0.6:
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, -1)):
            if dy < 0 and tip[1] == 0: continue
            if dx == -1 and tip[0] == 0: continue
            over(dst, tip[0] + dx, tip[1] + dy, WHITE, 1.0 if (dx, dy) == (0, 0) else 0.6)

def gem(dst, cx, y, ph, k):
    """4-wide gem: 2 rows above the frame, 2 rows in it"""
    c = cyc(k / 9 - ph * 2)
    rows = [(cx, cx + 1, mix(c, WHITE, 0.7)), (cx - 1, cx + 2, c), (cx - 1, cx + 2, mix(c, OUT, 0.3)), (cx, cx + 1, OUT)]
    for j, (a, b, col) in enumerate(rows):
        for x in range(a, b + 1):
            put(dst, x, y + j, C(OUT if (x in (a, b) and j in (1, 2)) else col))
    if (ph * 9 + k) % 9 < 1.5: put(dst, cx, y + 1, C(WHITE))

def star(dst, x, y, b, col):
    """4-point twinkle of brightness b (0..1)"""
    if b <= 0.05: return
    over(dst, x, y, WHITE, b)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        over(dst, x + dx, y + dy, mix(WHITE, col, 0.5), b * 0.7)
    if b > 0.7:
        for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            over(dst, x + dx, y + dy, col, (b - 0.7) * 2)

def spires(dst, Hh, ph, seed, x0=0):
    """crystal cluster for the left end of a frame: a tall main spire, an outer shard and a star at the tip"""
    b = Hh - 1
    crystal(dst, [(x0 + 1, 13), (x0 + 3, 21), (x0 + 3, b - 6), (x0 + 1, b - 9), (x0 + 1, 18)], ph, seed + 0.35, 0.8)
    crystal(dst, [(x0 + 5, 1), (x0 + 8, 10), (x0 + 9, b), (x0 + 3, b), (x0 + 3, 10)], ph, seed)
    tw = max(0.0, math.sin((ph * 2 + seed) * 2 * math.pi))
    star(dst, x0 + 5, 1, 0.35 + 0.65 * tw, cyc(ph + seed))
    star(dst, x0 + 1, 9, max(0.0, math.sin((ph * 2 + seed + 0.5) * 2 * math.pi)) * 0.8, cyc(ph + 0.4))

def halo(layer, ph, a=0.38):
    """soft 1px glow around everything opaque in the layer"""
    src = layer.copy(); w, h = src.size
    for y in range(h):
        for x in range(w):
            if src.getpixel((x, y))[3]: continue
            n = sum(1 for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                    if 0 <= x + dx < w and 0 <= y + dy < h and src.getpixel((x + dx, y + dy))[3] == 255)
            if n: over(layer, x, y, cyc(y / h * 0.5 - ph), min(1.0, a * (0.6 + 0.2 * n)))

def wings(dst, Hh, ph):
    """fan of three crystal feathers for the left end of the hotbar (12 px out, 18 px up)"""
    b = Hh - 1; layer = Image.new('RGBA', dst.size)
    crystal(layer, [(0, 17), (3, 23), (3, b - 4), (1, b - 2), (0, b - 9)], ph, 0.55, 0.8)
    crystal(layer, [(5, 6), (8, 14), (8, b), (3, b), (2, 16)], ph, 0.3)
    crystal(layer, [(10, 0), (13, 10), (14, b), (7, b), (7, 10)], ph, 0.0)
    halo(layer, ph)
    dst.alpha_composite(layer)
    for i, (x, y) in enumerate(((10, 1), (5, 7), (1, 18))):
        tw = max(0.0, math.sin((ph * 2 + i / 3) * 2 * math.pi))
        star(dst, x, y, (0.4 if i == 0 else 0.0) + 0.6 * tw, cyc(ph + i / 3))

# ------------------------------------------------------------------ hotbar (182x22 -> 206x40)
HB_PADS = (12, 18, 12, 0)
def hotbar():
    src = ref(H + 'hotbar.png'); l, t, r, b = HB_PADS
    W, Hh, N = 182 + l + r, 22 + t + b, 24
    strip = Image.new('RGBA', (W, Hh * N))
    for f in range(N):
        ph = f / N
        fr = Image.new('RGBA', (W, Hh))
        # soft aurora glow line hugging the top rim (the part right above sits under the XP bar)
        for x in range(l, l + 182):
            g = cyc(x / 182 - ph)
            over(fr, x, t - 1, g, 0.55 + 0.25 * math.sin((x / 18 - ph) * 2 * math.pi))
            over(fr, x, t - 2, g, 0.22)
        frame_recolor(src, l, t, fr, ph, 182, ph * (182 + 60) - 30)
        for k in range(1, 9):
            gem(fr, l + 20 * k, t - 2, ph, k)
        # tall crystal spires at both ends, rising beside the XP bar and the hearts
        wing = Image.new('RGBA', (W, Hh))
        wings(wing, Hh, ph)
        fr.alpha_composite(wing); fr.alpha_composite(wing.transpose(Image.FLIP_LEFT_RIGHT))
        strip.alpha_composite(fr, (0, f * Hh))
    markers(strip, HB_PADS, Hh, N)
    save(strip, H + 'hotbar.png', N, W, Hh, 3)
    return strip, W, Hh

# ------------------------------------------------------------------ selection (24x23 -> 32x25)
SEL_PADS = (4, 2, 4, 0)
def selection():
    src = ref(H + 'hotbar_selection.png'); l, t, r, b = SEL_PADS
    W, Hh, N = 24 + l + r, 23 + t + b, 16
    strip = Image.new('RGBA', (W, Hh * N))
    perim = [(x, 0) for x in range(24)] + [(23, y) for y in range(23)] + [(x, 22) for x in range(23, -1, -1)] + [(0, y) for y in range(22, -1, -1)]
    for f in range(N):
        ph = f / N; pulse = 0.5 + 0.5 * math.sin(ph * 2 * math.pi)
        fr = Image.new('RGBA', (W, Hh))
        inside = lambda x, y: 0 <= x < 24 and 0 <= y < 23 and src.getpixel((x, y))[3] > 0
        # halo around the frame (inside the pads)
        for y in range(Hh):
            for x in range(W):
                sx, sy = x - l, y - t
                if inside(sx, sy): continue
                d = min((abs(sx - qx) + abs(sy - qy) for qx in (0, 23) for qy in range(0, 23) if inside(qx, qy)), default=9)
                d = min(d, min((abs(sx - qx) + abs(sy - qy) for qx in range(24) for qy in (0, 22)), default=9))
                if d <= 3 and not (4 <= sx <= 19 and 4 <= sy <= 19):
                    over(fr, x, y, cyc((x + y) / 50 + ph), (0.75, 0.42, 0.18)[d - 1] * (0.55 + 0.45 * pulse))
        for y in range(23):
            for x in range(24):
                p = src.getpixel((x, y))
                if p[3] == 0: continue
                lum = (p[0] + p[1] + p[2]) / 765
                if lum < 0.25: c = OUT
                else:
                    c = mix(cyc((x + y) / 47 + ph), WHITE, 0.35 + 0.5 * pulse * lum)
                    if x in (0, 1) or y in (0, 1): c = mix(c, WHITE, 0.4)
                put(fr, l + x, t + y, C(c, max(p[3], 200)))
        # corner spikes, side points and a little crown
        hot = mix(WHITE, cyc(ph), 0.25)
        for (x, y) in ((2, 1), (1, 0), (W - 3, 1), (W - 2, 0)):
            put(fr, x, y, C(hot))
        for side in (0, 1):
            for j, wdt in enumerate((1, 2, 3, 2, 1)):
                for i in range(wdt):
                    x = l - 1 - i if side == 0 else l + 24 + i
                    c = mix(cyc(ph + j / 10), WHITE, 0.3 if i < wdt - 1 else 0.8)
                    put(fr, x, t + 9 + j, C(OUT if i == wdt - 1 and wdt == 3 else c))
        cx = l + 11
        for x in (cx, cx + 1): put(fr, x, 0, C(WHITE))
        for x in range(cx - 1, cx + 3): put(fr, x, 1, C(mix(cyc(ph + 0.5), WHITE, 0.4)))
        # white spark running around the rim
        for k in range(3):
            px, py = perim[int((ph + k / 3) * len(perim)) % len(perim)]
            put(fr, l + px, t + py, C(WHITE))
        strip.alpha_composite(fr, (0, f * Hh))
    markers(strip, SEL_PADS, Hh, N)
    save(strip, H + 'hotbar_selection.png', N, W, Hh, 2)
    return strip, W, Hh

# ------------------------------------------------------------------ offhand (29x24 -> 34x42)
OFF_PADS = (5, 18, 0, 0)
def offhand():
    out = {}
    l, t, r, b = OFF_PADS
    W, Hh, N = 29 + l + r, 24 + t + b, 24
    left = Image.new('RGBA', (W, Hh * N))
    src = ref(H + 'hotbar_offhand_left.png')
    for f in range(N):
        ph = f / N
        fr = Image.new('RGBA', (W, Hh))
        frame_recolor(src, l, t, fr, ph, 60, ph * 90 - 30)
        sp = Image.new('RGBA', (W, Hh)); spires(sp, Hh, ph, 0.6, x0=-2); halo(sp, ph); fr.alpha_composite(sp)
        left.alpha_composite(fr, (0, f * Hh))
    right = Image.new('RGBA', left.size)
    for f in range(N):            # mirror frame by frame so the strip order is kept
        right.paste(left.crop((0, f * Hh, W, (f + 1) * Hh)).transpose(Image.FLIP_LEFT_RIGHT), (0, f * Hh))
    markers(left, OFF_PADS, Hh, N); markers(right, (r, t, l, b), Hh, N)
    save(left, H + 'hotbar_offhand_left.png', N, W, Hh, 3)
    save(right, H + 'hotbar_offhand_right.png', N, W, Hh, 3)
    return left, right, W, Hh

# ------------------------------------------------------------------ boss bar backgrounds (182x5 -> 198x11) + advancement toast
BOSS_PADS = (8, 3, 8, 3)
BOSS_GEM = {'pink': (255, 150, 210), 'blue': (120, 200, 255), 'red': (255, 130, 140), 'green': (150, 240, 170),
            'yellow': (255, 230, 130), 'purple': (190, 150, 255), 'white': (236, 238, 255)}

def save_static(im, rel):
    p = TX + rel
    os.makedirs(os.path.dirname(p), exist_ok=True)
    im.save(p, optimize=True)

def bossbars():
    """Aurora Pack's background in the middle, a gem cap with two small shards at each end"""
    l, t, r, b = BOSS_PADS
    for col, gc in BOSS_GEM.items():
        core = Image.open(AURORA + 'gui/sprites/boss_bar/%s_background.png' % col).convert('RGBA')
        W, Hh = 182 + l + r, 5 + t + b
        im = Image.new('RGBA', (W, Hh)); im.alpha_composite(core, (l, t))
        for side in (0, 1):                                    # everything stays inside the 8 px pad (the bar covers the rest)
            layer = Image.new('RGBA', (W, Hh))
            cx, cy = 4, Hh // 2
            crystal(layer, [(cx - 1, cy - 2), (cx + 2, 0), (cx + 3, cy - 2)], 0.0, 0.1, 0.8)
            crystal(layer, [(cx - 1, cy + 2), (cx + 2, Hh - 1), (cx + 3, cy + 2)], 0.0, 0.5, 0.8)
            for dy in range(-3, 4):                            # diamond gem in the bar's colour
                for dx in range(-3, 4):
                    d = abs(dx) + abs(dy)
                    if d > 3: continue
                    c = OUT if d == 3 else mix(gc, WHITE, 0.55 if dx < 0 and dy < 0 else 0.1) if dy < 1 else mix(gc, OUT, 0.2)
                    put(layer, cx + dx, cy + dy, C(c))
            put(layer, cx - 1, cy - 1, C(WHITE))
            im.alpha_composite(layer if side == 0 else layer.transpose(Image.FLIP_LEFT_RIGHT))
        markers(im, BOSS_PADS, Hh, 1)
        save_static(im, 'gui/sprites/boss_bar/%s_background.png' % col)

TOAST_PADS = (12, 0, 0, 0)
def advancement_toast():
    """Aurora Pack's advancement toast plus a crystal wing sticking out on the left (toasts slide in from the right)"""
    core = Image.open(AURORA + 'gui/sprites/toast/advancement.png').convert('RGBA')
    l = TOAST_PADS[0]; W, Hh = 160 + l, 32
    im = Image.new('RGBA', (W, Hh)); im.alpha_composite(core, (l, 0))
    layer = Image.new('RGBA', (W, Hh))
    for k, (ty, tx) in enumerate(((3, 1), (11, 0), (20, 1), (28, 3))):
        crystal(layer, [(l + 2, Hh // 2 - 6 + k * 3), (tx, ty), (l + 2, Hh // 2 - 2 + k * 3)], 0.0, k / 4, 0.9)
    halo(layer, 0.0)
    im.alpha_composite(layer, (0, 0)); im.alpha_composite(core.crop((0, 0, 3, 32)), (l, 0))   # keep the rim on top
    star(im, 4, 16, 1.0, (255, 236, 160))
    markers(im, TOAST_PADS, Hh, 1)
    save_static(im, 'gui/sprites/toast/advancement.png')

def pack_icon(hb, W, Hh):
    icon = Image.new('RGBA', (128, 128))
    for y in range(128):
        for x in range(128):
            icon.putpixel((x, y), C(mix(DEEP, cyc((x + y) / 256 + 0.1), 0.35 + 0.3 * (1 - y / 128))))
    crop = hb.crop((0, 0, 64, Hh)).resize((64 * 2, Hh * 2), Image.NEAREST)
    icon.alpha_composite(crop, (0, 128 - Hh * 2 - 20))
    icon.save(PACK + '/pack.png', optimize=True)

# ------------------------------------------------------------------ preview: simulated HUD in game
def frame_of(strip, fh, i):
    n = strip.height // fh; i %= n
    return strip.crop((0, i * fh, strip.width, (i + 1) * fh))

def hud_scene(xl, tick, survival=True, gw=300, gh=110):
    """draw the vanilla HUD layout at GUI scale 1; xl=True expands the marked sprites like the shader does"""
    sc = Image.new('RGBA', (gw, gh))
    grass = ref('block/grass_block_top.png')
    for y in range(0, gh, 16):
        for x in range(0, gw, 16):
            sc.alpha_composite(grass, (x, y))
    px = sc.load()
    for y in range(gh):
        for x in range(gw):
            r, g, b_, a = px[x, y]; px[x, y] = (r * 90 // 255, g * 175 // 255, b_ * 80 // 255, 255)
    cx, h = gw // 2, gh
    def spr(rel, x, y, std, idx=0):
        """std = vanilla size; if the sprite carries markers, grow it like position_tex_color.vsh"""
        base = XL if xl else AURORA
        im = Image.open(base + rel).convert('RGBA') if os.path.exists(base + rel) else Image.open(AURORA + rel).convert('RGBA')
        meta = base + rel + '.mcmeta'
        fh = json.load(open(meta))['animation'].get('height', im.width) if os.path.exists(meta) else im.height
        fr = frame_of(im, fh, idx)
        tl = fr.getpixel((0, 0)); br = fr.getpixel((fr.width - 1, fr.height - 1))
        if tl[2] == MARK and tl[3] == 1:
            x -= tl[0]; y -= tl[1]
            fr = fr.copy()
            for p in ((0, 0), (fr.width - 1, 0), (0, fr.height - 1), (fr.width - 1, fr.height - 1)):
                fr.putpixel(p, (0, 0, 0, 0))
        else:
            fr = fr.resize(std, Image.NEAREST)
        sc.alpha_composite(fr, (x, y))
    sel = (tick // 16) % 9
    spr(H + 'hotbar.png', cx - 91, h - 22, (182, 22), tick // 3)
    spr(H + 'hotbar_selection.png', cx - 91 - 1 + sel * 20, h - 23, (24, 23), tick // 2)
    spr(H + 'hotbar_offhand_left.png', cx - 91 - 29, h - 23, (29, 24), tick // 3)
    items = ['diamond_sword', 'netherite_pickaxe', 'diamond_axe', 'diamond_shovel', 'netherite_sword',
             'diamond_spear', 'netherite_hoe', 'diamond_pickaxe', 'netherite_axe']
    for k, it in enumerate(items):
        im = Image.open(AURORA + 'item/' + it + '.png').convert('RGBA')
        sc.alpha_composite(frame_of(im, 16, tick // 2), (cx - 90 + k * 20 + 2, h - 19))
    sc.alpha_composite(frame_of(Image.open(AURORA + 'item/netherite_chestplate.png').convert('RGBA'), 16, tick // 3), (cx - 91 - 26, h - 19))
    if survival:
        bg = Image.open(AURORA + H + 'experience_bar_background.png').convert('RGBA')
        pr = frame_of(Image.open(AURORA + H + 'experience_bar_progress.png').convert('RGBA'), 5, tick // 2)
        sc.alpha_composite(bg, (cx - 91, h - 29)); sc.alpha_composite(pr.crop((0, 0, 120, 5)), (cx - 91, h - 29))
        def icon(rel):        # Aurora Pack's (animated) icon if there is one, else vanilla
            p = AURORA + H + rel
            return frame_of(Image.open(p).convert('RGBA'), 9, tick // 4) if os.path.exists(p) else ref(H + rel)
        heart = icon('heart/full.png'); cont = icon('heart/container.png')
        food = icon('food_full.png'); fcont = icon('food_empty.png'); arm = icon('armor_full.png')
        for i in range(10):
            sc.alpha_composite(cont, (cx - 91 + i * 8, h - 39)); sc.alpha_composite(heart, (cx - 91 + i * 8, h - 39))
            sc.alpha_composite(fcont, (cx + 91 - 9 - i * 8, h - 39)); sc.alpha_composite(food, (cx + 91 - 9 - i * 8, h - 39))
            sc.alpha_composite(arm, (cx - 91 + i * 8, h - 49))
    return sc

XL = TX
def previews():
    os.makedirs(PREVIEWS, exist_ok=True)
    k = 3
    def both(tick, surv):
        a = hud_scene(False, tick, surv).resize((900, 330), Image.NEAREST)
        b = hud_scene(True, tick, surv).resize((900, 330), Image.NEAREST)
        out = Image.new('RGBA', (900, 676), (34, 29, 52, 255))
        out.alpha_composite(a, (0, 0)); out.alpha_composite(b, (0, 346)); return out
    both(0, True).convert('RGB').save(PREVIEWS + '/hud_xl.png')
    frames = [both(t, True).convert('RGB') for t in range(0, 144, 2)]
    frames[0].save(PREVIEWS + '/anim_hud_xl.gif', save_all=True, append_images=frames[1:], duration=100, loop=0, optimize=True)

if __name__ == '__main__':
    import shutil
    shutil.rmtree(TX, ignore_errors=True)     # textures are 100% generated; shaders + pack.mcmeta are hand-written
    hb, W, Hh = hotbar(); selection(); offhand(); bossbars(); advancement_toast()
    pack_icon(hb, W, Hh)
    previews()
    print('ok')
