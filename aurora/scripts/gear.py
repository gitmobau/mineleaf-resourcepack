# Aurora gear: animated tools, enchantment aura, diamond crystal armor, light opal netherite armor.
import os, math, json, random, colorsys
from PIL import Image

HOME = os.path.expanduser('~')
# Paths can be overridden by build.py (AURORA_REF = folder holding assets/minecraft of vanilla 26.3,
# AURORA_RP = resourcepacks folder, AURORA_PREVIEWS = where preview images go).
REF_ROOT = os.environ.get('AURORA_REF', HOME + '/ref63')
RP = os.environ.get('AURORA_RP', HOME + '/mnt/.minecraft/resourcepacks')
REF = REF_ROOT + '/assets/minecraft/'
PACK = RP + '/Aurora Pack/assets/minecraft/'
PREVIEWS = os.environ.get('AURORA_PREVIEWS', RP + '/Aurora Pack')

P = [(123,225,249),(155,210,248),(187,185,248),(220,181,240),(248,176,234),
     (248,188,199),(248,201,173),(248,225,156),(209,248,145),(170,245,215)]
VIVID = [(80,220,255),(120,175,255),(170,140,255),(220,130,255),(255,125,220),
         (255,150,175),(255,190,135),(255,228,120),(175,248,135),(110,245,205)]
WHITE = (255, 255, 255)
OUT = (52, 36, 98)

def cyc(t, pal=P):
    t = (t % 1.0) * len(pal); i = int(t) % len(pal); f = t - int(t)
    a = pal[i]; b = pal[(i + 1) % len(pal)]
    return tuple(a[k] + (b[k] - a[k]) * f for k in range(3))

def mix(a, b, f):
    return tuple(a[k] + (b[k] - a[k]) * f for k in range(3))

def C(c, a=255):
    return tuple(int(max(0, min(255, round(v)))) for v in c[:3]) + (int(max(0, min(255, a))),)

def hsv(p):
    h, s, v = colorsys.rgb_to_hsv(*[q / 255 for q in p[:3]])
    return h * 360, s, v

def ref(rel):
    return Image.open(REF + 'textures/' + rel).convert('RGBA')

def save_tex(im, rel, mcmeta=None):
    p = PACK + 'textures/' + rel
    os.makedirs(os.path.dirname(p), exist_ok=True)
    im.save(p, optimize=True)
    if mcmeta is not None:
        json.dump(mcmeta, open(p + '.mcmeta', 'w'), indent=2)

def save_json(obj, rel):
    p = PACK + rel
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(obj, open(p, 'w'), indent=2)

def hsh(x, y, s=0):
    return ((x * 73856093) ^ (y * 19349663) ^ (s * 83492791)) & 0xffff

# ------------------------------------------------------------------ crystal painter
def crystal_px(p, t):
    """diamond-family pixel -> aurora crystal (by original brightness)"""
    hh, s, v = hsv(p)
    c = cyc(t)
    if v < 0.2:   return (46, 30, 92)
    if v < 0.3:   return (84, 62, 150)
    if v < 0.45:  return mix(c, (96, 74, 170), 0.55)
    if v < 0.6:   return mix(c, (120, 100, 200), 0.30)
    if v < 0.85:  return mix(c, (150, 130, 230), 0.10)
    if s > 0.4:   return mix(c, WHITE, 0.30)
    return mix(c, WHITE, 0.70)

# ------------------------------------------------------------------ tools
TOOLS = ['sword', 'pickaxe', 'axe', 'shovel', 'hoe', 'spear']

def recolor_tool(name, kind):
    im = ref('item/' + name + '.png')
    w, h = im.size
    out = Image.new('RGBA', im.size)
    head = [[False] * h for _ in range(w)]
    pts = []
    for y in range(h):
        for x in range(w):
            q = im.getpixel((x, y))
            if q[3]:
                qh, qs, qv = hsv(q)
                ish = (140 <= qh <= 200) if kind == 'diamond' else not ((qh >= 340 or qh <= 15) and qs >= 0.28)
                if ish:
                    pts.append(x - y); head[x][y] = True
    dmin, dmax = (min(pts), max(pts)) if pts else (0, 1)
    for y in range(h):
        for x in range(w):
            p = im.getpixel((x, y))
            if p[3] == 0:
                continue
            hh, s, v = hsv(p)
            t = round(0.5 * max(0, min(1, ((x - y) - dmin) / max(1, dmax - dmin))) * 8) / 8
            c = cyc(t)
            if kind == 'diamond':
                if head[x][y] or s < 0.1:
                    col = crystal_px(p, t); head[x][y] = True
                elif 10 <= hh < 30 and s > 0.6:
                    col = mix((90, 30, 80), (248, 176, 234), min(1, v * 1.5))
                else:
                    col = mix((40, 26, 44), (196, 140, 170), min(1, (v - 0.12) / 0.45))
            else:
                if not head[x][y]:
                    col = mix((26, 18, 34), (150, 110, 150), min(1, max(0, (v - 0.12) / 0.38)))
                elif 300 <= hh <= 330 and s > 0.35:
                    col = (72, 52, 116)
                elif v < 0.22: col = (30, 24, 46)
                elif v < 0.30: col = mix((52, 44, 74), c, 0.18)
                elif v < 0.40: col = mix(c, (60, 50, 86), 0.50)
                elif v < 0.48: col = mix(c, (70, 60, 100), 0.35)
                else: col = mix(c, WHITE, 0.15)
            out.putpixel((x, y), C(col, p[3]))
    return out, head

def animate(base, head, N=16, ft=2, seed=0):
    """shine sweep along the head + twinkles"""
    w, h = base.size
    strip = Image.new('RGBA', (w, h * N))
    pts = [(x, y) for y in range(h) for x in range(w) if head[x][y] and base.getpixel((x, y))[3]]
    rnd = random.Random(seed)
    tw = rnd.sample(pts, min(3, len(pts))) if pts else []
    if pts:
        dmin = min(x - y for x, y in pts); dmax = max(x - y for x, y in pts)
    for f in range(N):
        fr = base.copy()
        c = -0.3 + 1.6 * (f / (N * 0.7))      # sweep during first 70% of the loop
        for (x, y) in pts:
            s = ((x - y) - dmin) / max(1, dmax - dmin)
            d = abs(s - c)
            if d < 0.14:
                p = fr.getpixel((x, y))
                fr.putpixel((x, y), C(mix(p, WHITE, 0.65 * (1 - d / 0.14)), p[3]))
        for i, (x, y) in enumerate(tw):
            if (f + i * 5) % N in (0, 1):
                fr.putpixel((x, y), C(WHITE))
        strip.paste(fr, (0, f * h))
    return strip, {"animation": {"frametime": ft}}

def aura(base, N=16):
    """24x24 animated halo ring around a 16x16 silhouette (offset 4)"""
    W = 24
    sil = [[False] * W for _ in range(W)]
    for y in range(16):
        for x in range(16):
            if base.getpixel((x, y))[3]:
                sil[x + 4][y + 4] = True
    pts = [(x, y) for y in range(W) for x in range(W) if sil[x][y]]
    cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
    dist = {}
    for y in range(W):
        for x in range(W):
            if sil[x][y]:
                continue
            d = min(math.hypot(x - a, y - b) for a, b in pts)
            if d <= 3.6:
                dist[(x, y)] = d
    ring2 = sorted([k for k, d in dist.items() if 1.6 < d <= 2.6], key=lambda k: math.atan2(k[1] - cy, k[0] - cx))
    strip = Image.new('RGBA', (W, W * N))
    for f in range(N):
        ph = f / N
        pulse = 0.7 + 0.3 * math.sin(ph * 2 * math.pi)
        for (x, y), d in dist.items():
            ang = math.atan2(y - cy, x - cx) / (2 * math.pi)
            col = cyc(ang + ph, VIVID)
            if d <= 1.5:   a = 215; col = mix(col, WHITE, 0.35)
            elif d <= 2.6: a = 135
            else:          a = 55
            strip.putpixel((x, f * W + y), C(col, a * pulse))
        for k in range(3):
            if ring2:
                x, y = ring2[int((ph + k / 3) * len(ring2)) % len(ring2)]
                strip.putpixel((x, f * W + y), C(WHITE, 255))
    return strip, {"animation": {"frametime": 2}}

def aura_model(name):
    tex = "minecraft:item/aurora/aura_" + name
    return {
        "parent": "minecraft:item/handheld",
        "textures": {"aura": tex, "particle": tex},
        "elements": [{
            "from": [-4, -4, 8], "to": [20, 20, 8], "shade": False, "light_emission": 15,
            "faces": {"south": {"uv": [0, 0, 16, 16], "texture": "#aura"},
                      "north": {"uv": [16, 0, 0, 16], "texture": "#aura"}}
        }]
    }

def tools():
    out = {}
    for mat in ('diamond', 'netherite'):
        for t in TOOLS:
            n = '%s_%s' % (mat, t)
            base, head = recolor_tool(n, mat)
            strip, meta = animate(base, head, seed=len(n) * 7)
            save_tex(strip, 'item/%s.png' % n, meta)
            if os.path.exists(REF + 'textures/item/%s_in_hand.png' % n):
                b2, h2 = recolor_tool(n + '_in_hand', mat)
                s2, m2 = animate(b2, h2, seed=7)
                save_tex(s2, 'item/%s_in_hand.png' % n, m2)
            au, am = aura(base)
            save_tex(au, 'item/aurora/aura_%s.png' % n, am)
            save_json(aura_model(n), 'models/item/aurora/aura_%s.json' % n)
            vanilla = json.load(open(REF + 'items/%s.json' % n))
            aura_ref = {"type": "minecraft:model", "model": "minecraft:item/aurora/aura_" + n}
            vm = vanilla["model"]
            if vm.get("type") == "minecraft:select":      # spear: aura only for the icon/ground model
                on_true = json.loads(json.dumps(vm))
                for case in on_true["cases"]:
                    case["model"] = {"type": "minecraft:composite", "models": [case["model"], aura_ref]}
            else:
                on_true = {"type": "minecraft:composite", "models": [vm, aura_ref]}
            new = dict(vanilla)
            new["model"] = {"type": "minecraft:condition", "property": "minecraft:has_component",
                            "component": "minecraft:enchantments", "ignore_default": True,
                            "on_true": on_true, "on_false": vm}
            new["oversized_in_gui"] = True
            save_json(new, 'items/%s.json' % n)
            out[n] = (strip, au, base.size)
    return out

# ------------------------------------------------------------------ glint
def glint():
    for n in ('enchanted_glint_item', 'enchanted_glint_armor'):
        im = ref('misc/%s.png' % n); o = Image.new('RGBA', im.size)
        for y in range(im.height):
            for x in range(im.width):
                p = im.getpixel((x, y))
                l = max(p[:3]) / 255
                o.putpixel((x, y), C(tuple(q * l * 1.1 for q in cyc((x + y) / 256, VIVID)), p[3]))
        save_tex(o, 'misc/%s.png' % n)

# ------------------------------------------------------------------ armor icons
ARMOR = ['helmet', 'chestplate', 'leggings', 'boots']

def diamond_armor_icons():
    out = {}
    for a in ARMOR:
        n = 'diamond_' + a
        im = ref('item/%s.png' % n)
        base = Image.new('RGBA', im.size); head = [[False] * 16 for _ in range(16)]
        for y in range(16):
            for x in range(16):
                p = im.getpixel((x, y))
                if p[3]:
                    base.putpixel((x, y), C(crystal_px(p, (x + y) / 30 * 0.9), p[3])); head[x][y] = True
        strip, meta = animate(base, head, seed=len(a))
        save_tex(strip, 'item/%s.png' % n, meta); out[n] = strip
    return out

# ------------------------------------------------------------------ worn armor
def box_faces(u, v, w, h, d):
    return {'top': (u + d, v, w, d), 'bottom': (u + d + w, v, w, d), 'right': (u, v + d, d, h),
            'front': (u + d, v + d, w, h), 'left': (u + d + w, v + d, d, h), 'back': (u + 2 * d + w, v + d, w, h)}

def value_range(im):
    vs = [hsv(im.getpixel((x, y)))[2] for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3]]
    return min(vs), max(vs)

# Light opal netherite. One painter for icons and worn armour so they match: dark lavender outline where the plate
# ends, a pastel iridescent rim just inside it, and smooth pearl metal (4 posterised tones) inside. The vanilla
# brightness only decides which tone a pixel gets, after a light smoothing, so the netherite noise disappears.
OPAL_LINE = (112, 90, 178)          # plate outline on worn armour
OPAL_ICON_LINE = (66, 48, 124)      # icons need more contrast against the slot
OPAL_TONES = [(158, 142, 214), (192, 182, 236), (220, 214, 250), (243, 241, 255)]

def opal_regions(size, boxes):
    """pixel -> region rect; edges are only detected inside a region (box faces wrap, so a face border is no edge)"""
    W, H = size
    reg = {}
    for (u, v, w, h, d) in boxes:
        for fx, fy, fw, fh in box_faces(u, v, w, h, d).values():
            for yy in range(fy, fy + fh):
                for xx in range(fx, fx + fw):
                    reg[(xx, yy)] = (fx, fy, fw, fh)
    return lambda x, y: reg.get((x, y), (0, 0, W, H))

def opal_clean(im, region):
    """tidy the vanilla silhouette: drop opaque pixels hanging on by one side, fill notches closed on three sides"""
    W, H = im.size
    o = im.copy()
    N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
    def inside(x, y, nx, ny):
        fx, fy, fw, fh = region(x, y)
        return fx <= nx < fx + fw and fy <= ny < fy + fh
    for y in range(H):
        for x in range(W):
            ns = [im.getpixel((x + dx, y + dy)) for dx, dy in N4 if inside(x, y, x + dx, y + dy)]
            full = [q for q in ns if q[3]]
            if im.getpixel((x, y))[3] and len(full) <= 1 and len(ns) >= 3:
                o.putpixel((x, y), (0, 0, 0, 0))
            elif not im.getpixel((x, y))[3] and len(full) >= 3 and len(ns) == 4:
                o.putpixel((x, y), max(full, key=lambda q: sum(q[:3])))
    return o

def opal_layers(im, region=None):
    """-> (edge set, rim set, smoothed 0..1 brightness) of the opaque pixels"""
    W, H = im.size
    region = region or (lambda x, y: (0, 0, W, H))
    op = lambda x, y: 0 <= x < W and 0 <= y < H and im.getpixel((x, y))[3] > 0
    vr = value_range(im)
    t = {(x, y): (hsv(im.getpixel((x, y)))[2] - vr[0]) / max(1e-6, vr[1] - vr[0])
         for y in range(H) for x in range(W) if op(x, y)}
    def near(x, y, dx, dy):              # neighbour inside the same region, or None when it leaves the region
        fx, fy, fw, fh = region(x, y)
        nx, ny = x + dx, y + dy
        return (nx, ny) if fx <= nx < fx + fw and fy <= ny < fy + fh else None
    N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
    edge = {p for p in t if any((q := near(*p, dx, dy)) is not None and q not in t for dx, dy in N4)}
    rim = {p for p in t if p not in edge and any((q := near(*p, dx, dy)) in edge for dx, dy in N4)}
    smooth = {}
    for (x, y), v in t.items():
        ns = [t[q] for dx, dy in N4 if (q := near(x, y, dx, dy)) in t]
        smooth[(x, y)] = 0.5 * v + 0.5 * (sum(ns) / len(ns) if ns else v)
    return edge, rim, smooth

def opal_tone(s, x, y, region):
    """smoothed brightness + soft top-lit gradient inside the region -> one of the pearl tones"""
    fx, fy, fw, fh = region
    g = 1 - (y - fy) / max(1, fh - 1)
    k = s * 0.45 + g * 0.6
    i = 0 if k < 0.3 else 1 if k < 0.55 else 2 if k < 0.8 else 3
    c = OPAL_TONES[i]
    return mix(c, cyc((x * 0.5 + y) / 24, VIVID), 0.18) if i == 3 else c

def opal_paint(im, region=None, line=OPAL_LINE, ph=0.0):
    W, H = im.size
    region = region or (lambda x, y: (0, 0, W, H))
    edge, rim, smooth = opal_layers(im, region)
    o = Image.new('RGBA', im.size)
    for (x, y), s in smooth.items():
        if (x, y) in edge: c = line
        elif (x, y) in rim: c = mix(cyc((x + y) / 28 + ph, VIVID), WHITE, 0.42)
        else: c = opal_tone(s, x, y, region(x, y))
        o.putpixel((x, y), C(c, im.getpixel((x, y))[3]))
    return o

def netherite_armor_icons():
    """item icons painted like the worn armour; the rim shimmers and a few pixels twinkle (12 frames)"""
    out = {}
    N = 12
    for k, a in enumerate(ARMOR):
        n = 'netherite_' + a
        im = ref('item/%s.png' % n)
        edge, rim, smooth = opal_layers(im)
        stars = [p for p in sorted(smooth) if p not in edge and p not in rim and smooth[p] > 0.45 and hsh(*p, k) % 11 == 0][:3]
        strip = Image.new('RGBA', (16, 16 * N))
        for f in range(N):
            fr = opal_paint(im, line=OPAL_ICON_LINE, ph=f / N)
            for i, (x, y) in enumerate(stars):
                b = max(0.0, math.sin((f / N + i / len(stars)) * 2 * math.pi)) ** 3
                if b > 0.05:
                    fr.putpixel((x, y), C(mix(fr.getpixel((x, y)), WHITE, b)))
            strip.alpha_composite(fr, (0, f * 16))
        save_tex(strip, 'item/%s.png' % n, {"animation": {"frametime": 3}})
        out[n] = strip
    return out

# Material swatches for the optional Aurora EMF pack (3D netherite pieces). They live in texels that no vanilla armour
# box ever samples (corners of the box layouts), so without Entity Model Features they are never drawn.
EMF_SWATCHES = {'metal': (0, 0, 8, 8), 'trim': (24, 0, 8, 8), 'dark': (32, 0, 8, 8), 'gem': (56, 0, 4, 4),
                'gem2': (60, 0, 4, 4), 'gold': (56, 4, 4, 4), 'glow': (60, 4, 4, 4), 'trimv': (56, 16, 8, 16),
                'lame': (36, 16, 8, 3)}   # thin plate edge: highlight / metal / outline, for the sides of flat plates

def paint_swatches(o):
    def swatch(name, fn, border=True):
        x0, y0, w, h = EMF_SWATCHES[name]
        for j in range(h):
            for i in range(w):
                edge = border and (i in (0, w - 1) or j in (0, h - 1))
                o.putpixel((x0 + i, y0 + j), C(OPAL_LINE if edge else fn(i, j, w, h)))
    swatch('metal', lambda i, j, w, h: OPAL_TONES[3] if j == 1 else OPAL_TONES[2 if j < h // 2 else 1])
    swatch('trim', lambda i, j, w, h: mix(cyc((i + j) / (w + h) * 1.5, VIVID), WHITE, 0.4 if j > 1 else 0.7))
    swatch('dark', lambda i, j, w, h: OPAL_TONES[2] if j == 1 else OPAL_TONES[1 if j < h - 3 else 0])
    swatch('lame', lambda i, j, w, h: OPAL_TONES[3] if j == 0 else OPAL_TONES[2] if j == 1 else OPAL_LINE, border=False)
    for j in range(3):
        for i in (0, 7):
            o.putpixel((36 + i, 16 + j), C(OPAL_LINE))
    swatch('trimv', lambda i, j, w, h: mix(cyc(j / h, VIVID), WHITE, 0.6 if i == 1 else 0.35))
    for name, a, b in (('gem', (255, 170, 220), (210, 80, 170)), ('gem2', (170, 240, 255), (70, 150, 230)),
                       ('gold', (255, 236, 160), (210, 150, 60)), ('glow', (255, 255, 255), (220, 200, 255))):
        swatch(name, lambda i, j, w, h, a=a, b=b: WHITE if (i, j) == (0, 0) else mix(a, b, (i + j) / (w + h - 2)), border=False)

HUMANOID_BOXES = [(0, 0, 8, 8, 8), (32, 0, 8, 8, 8), (16, 16, 8, 12, 4), (40, 16, 4, 12, 4), (0, 16, 4, 12, 4)]

def netherite_worn():
    """player netherite armour, repainted in light opal over the vanilla shapes"""
    out = []
    for dst in ('entity/equipment/humanoid/netherite.png', 'entity/equipment/humanoid_leggings/netherite.png'):
        im = ref(dst); reg = opal_regions(im.size, HUMANOID_BOXES)
        if 'leggings' not in dst:                     # shoulder plates end on a straight line (no 1-2 px teeth)
            for y in range(20, 32):
                for x in range(40, 56):
                    if y > 25: im.putpixel((x, y), (0, 0, 0, 0))
                    elif not im.getpixel((x, y))[3]: im.putpixel((x, y), im.getpixel((x, y - 1)))
        o = opal_paint(opal_clean(im, reg), reg)
        paint_swatches(o)
        save_tex(o, dst); out.append(o)
    return tuple(out)

def diamond_worn():
    out = []
    for layer in ('humanoid', 'humanoid_leggings'):
        im = ref('entity/equipment/%s/diamond.png' % layer); o = Image.new('RGBA', im.size)
        for y in range(im.height):
            for x in range(im.width):
                p = im.getpixel((x, y))
                if p[3]:
                    o.putpixel((x, y), C(crystal_px(p, (x * 0.6 + y) / 64 * 0.6), p[3]))
        save_tex(o, 'entity/equipment/%s/diamond.png' % layer); out.append(o)
    return out

def other_worn():
    """baby humanoid, horse and nautilus armor: layout-agnostic recolor so every wearer matches"""
    out = {}
    for layer in ('humanoid_baby', 'horse_body', 'nautilus_body'):
        for mat in ('diamond', 'netherite'):
            rel = 'entity/equipment/%s/%s.png' % (layer, mat)
            if not os.path.exists(REF + 'textures/' + rel):
                continue
            im = ref(rel)
            if mat == 'netherite':
                o = opal_paint(im)
            else:
                o = Image.new('RGBA', im.size); W = im.width
                for y in range(im.height):
                    for x in range(W):
                        p = im.getpixel((x, y))
                        if p[3]:
                            o.putpixel((x, y), C(crystal_px(p, (x * 0.6 + y) / W * 0.6), p[3]))
            save_tex(o, rel); out[(layer, mat)] = o
    return out

# ------------------------------------------------------------------ preview
def player_preview(hum, leg):
    """flat front + back of the armour on a player silhouette"""
    def face(img, u, v, w, h, d, which):
        f = box_faces(u, v, w, h, d)[which]
        return img.crop((f[0], f[1], f[0] + f[2], f[1] + f[3]))
    def body(which):
        c = Image.new('RGBA', (16, 32), (0, 0, 0, 0))
        skin = (230, 190, 150, 255)
        for (x, y, w, h) in ((4, 0, 8, 8), (4, 8, 8, 12), (0, 8, 4, 12), (12, 8, 4, 12), (4, 20, 4, 12), (8, 20, 4, 12)):
            for yy in range(h):
                for xx in range(w):
                    c.putpixel((x + xx, y + yy), skin if y else (120, 80, 50, 255))
        for img, parts in ((leg, [((4, 20), (0, 16, 4, 12, 4)), ((8, 20), (0, 16, 4, 12, 4)), ((4, 8), (16, 16, 8, 12, 4))]),
                           (hum, [((4, 0), (0, 0, 8, 8, 8)), ((4, 8), (16, 16, 8, 12, 4)), ((0, 8), (40, 16, 4, 12, 4)),
                                  ((12, 8), (40, 16, 4, 12, 4)), ((4, 20), (0, 16, 4, 12, 4)), ((8, 20), (0, 16, 4, 12, 4))])):
            for at, (u, v, w, h, d) in parts:
                c.alpha_composite(face(img, u, v, w, h, d, which), at)
        return c
    out = Image.new('RGBA', (60, 40), (40, 34, 60, 255))
    out.alpha_composite(body('front'), (6, 4)); out.alpha_composite(body('back'), (34, 4))
    return out.resize((360, 240), Image.NEAREST)

if __name__ == '__main__':
    t = tools(); glint()
    di = diamond_armor_icons(); ni = netherite_armor_icons()
    hum, leg = netherite_worn(); diamond_worn(); ow = other_worn()
    sheet = Image.new('RGBA', (760, 560), (60, 52, 84, 255))
    for i, n in enumerate(['diamond_sword', 'diamond_pickaxe', 'diamond_axe', 'netherite_sword', 'netherite_pickaxe', 'netherite_spear']):
        strip, au, sz = t[n]
        fr = au.crop((0, 0, 24, 24)); fr.alpha_composite(strip.crop((0, 0, 16, 16)), (4, 4))
        sheet.alpha_composite(fr.resize((96, 96), Image.NEAREST), (10 + i * 122, 10))
        sheet.alpha_composite(strip.crop((0, 16 * 4, 16, 16 * 5)).resize((64, 64), Image.NEAREST), (26 + i * 122, 116))
    for i, n in enumerate(['diamond_helmet', 'diamond_chestplate', 'diamond_leggings', 'diamond_boots',
                           'netherite_helmet', 'netherite_chestplate', 'netherite_leggings', 'netherite_boots']):
        s = (di.get(n) or ni.get(n))
        sheet.alpha_composite(s.crop((0, 0, 16, 16)).resize((64, 64), Image.NEAREST), (10 + i * 92, 200))
    sheet.alpha_composite(player_preview(hum, leg), (10, 290))
    sheet.alpha_composite(hum.resize((256, 128), Image.NEAREST), (390, 290))
    os.makedirs(PREVIEWS, exist_ok=True)
    sheet.save(PREVIEWS + '/preview_gear.png')
    # gif of tool animation + aura
    frames = []
    for f in range(16):
        g = Image.new('RGBA', (500, 120), (60, 52, 84, 255))
        for i, n in enumerate(['diamond_sword', 'diamond_pickaxe', 'netherite_sword', 'netherite_axe']):
            strip, au, sz = t[n]
            fr = au.crop((0, f * 24, 24, f * 24 + 24)); fr.alpha_composite(strip.crop((0, f * 16, 16, f * 16 + 16)), (4, 4))
            g.alpha_composite(fr.resize((96, 96), Image.NEAREST), (10 + i * 122, 12))
        frames.append(g.convert('RGB'))
    frames[0].save(PREVIEWS + '/anim_gear.gif', save_all=True,
                   append_images=frames[1:], duration=100, loop=0)
    print('ok')
