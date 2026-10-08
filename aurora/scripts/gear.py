# Aurora gear: animated tools, enchantment aura, diamond crystal armor, netherite galactic robe + 3D cloak.
import os, sys, math, json, random, colorsys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from palette import cycle

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
    return cycle(t, pal)

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

# ------------------------------------------------------------------ crystal / galaxy painters
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

def galaxy_px(x, y, seed=0, scale=1.0, phase=0.0):
    u, v = x * scale, y * scale
    base = mix((18, 10, 44), (58, 28, 104), 0.5 + 0.5 * math.sin(u * 0.21 + v * 0.13 + seed))
    neb = (math.sin(u * 0.33 + seed * 1.7 + phase * 6.283) + math.sin(v * 0.27 - u * 0.11 + seed)
           + math.sin((u + v) * 0.19 + seed * 0.5)) / 3
    if neb > 0.15:
        base = mix(base, cyc(u * 0.02 + v * 0.015 + seed * 0.1 + phase, VIVID), min(0.42, (neb - 0.15) * 1.0))
    r = hsh(x, y, seed) % 97
    if r == 0:
        base = WHITE
    elif r in (1, 2):
        base = mix(base, cyc(r * 0.3 + seed, P), 0.85)
    return base

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

def finish_tool(n, recolor):
    """animated icon (+ in-hand variant), enchantment aura and item definition for one tool"""
    base, head = recolor(n)
    strip, meta = animate(base, head, seed=len(n) * 7)
    save_tex(strip, 'item/%s.png' % n, meta)
    if os.path.exists(REF + 'textures/item/%s_in_hand.png' % n):
        b2, h2 = recolor(n + '_in_hand')
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
    return strip, au, base.size

def tools():
    out = {}
    for mat in ('diamond', 'netherite'):
        for t in TOOLS:
            n = '%s_%s' % (mat, t)
            out[n] = finish_tool(n, lambda name, mat=mat: recolor_tool(name, mat))
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

def netherite_armor_icons():
    out = {}
    N = 12
    for k, a in enumerate(ARMOR):
        n = 'netherite_' + a
        im = ref('item/%s.png' % n)
        mask = [[im.getpixel((x, y))[3] > 0 for y in range(16)] for x in range(16)]
        strip = Image.new('RGBA', (16, 16 * N))
        for f in range(N):
            ph = f / N
            for y in range(16):
                for x in range(16):
                    if not mask[x][y]:
                        continue
                    def inside(xx, yy):
                        return 0 <= xx < 16 and 0 <= yy < 16 and mask[xx][yy]
                    edge = any(not inside(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                    inner = (not edge) and any(not inside(x + dx, y + dy) for dx in (-2, 0, 2) for dy in (-2, 0, 2) if abs(dx) + abs(dy) == 2)
                    if edge:
                        c = OUT
                    elif inner:
                        c = mix(cyc((x + y) / 32 + ph, VIVID), WHITE, 0.25)
                    else:
                        c = mix((20, 12, 48), (54, 30, 100), (x + y) / 30)
                        if hsh(x, y, k) % 9 == 0:
                            b = max(0, math.sin((ph + (hsh(y, x) % 7) / 7) * 2 * math.pi)) ** 2
                            c = mix(mix(c, cyc(x / 16, VIVID), 0.5), WHITE, b)
                    strip.putpixel((x, f * 16 + y), C(c))
        save_tex(strip, 'item/%s.png' % n, {"animation": {"frametime": 3}})
        out[n] = strip
    return out

# ------------------------------------------------------------------ worn armor
def box_faces(u, v, w, h, d):
    return {'top': (u + d, v, w, d), 'bottom': (u + d + w, v, w, d), 'right': (u, v + d, d, h),
            'front': (u + d, v + d, w, h), 'left': (u + d + w, v + d, d, h), 'back': (u + 2 * d + w, v + d, w, h)}

def paint_face(img, face, fn):
    x0, y0, w, h = face
    for j in range(h):
        for i in range(w):
            c = fn(i, j, w, h, x0 + i, y0 + j)
            if c is not None:
                img.putpixel((x0 + i, y0 + j), C(c[:3], c[3] if len(c) > 3 else 255))

def trim(t):
    return mix(cyc(t, VIVID), WHITE, 0.2)

def galaxy_robe():
    S = 4
    hum = Image.new('RGBA', (64, 32)); leg = Image.new('RGBA', (64, 32))
    g = lambda gx, gy, s=S: galaxy_px(gx, gy, seed=s)
    # --- hood (head 0,0 8x8x8)
    hf = box_faces(0, 0, 8, 8, 8)
    for name, face in hf.items():
        if name == 'front':
            def fn(i, j, w, h, X, Y):
                inner = 1 <= i <= 6 and 2 <= j <= 7
                if inner:
                    return None                      # face opening
                rim = (i in (1, 6) and j >= 2) or (j == 1 and 1 <= i <= 6)
                return trim(i / 8 + 0.1) if rim else g(X, Y)
        elif name == 'bottom':
            fn = lambda i, j, w, h, X, Y: None
        else:
            def fn(i, j, w, h, X, Y, name=name):
                if name != 'top' and j == h - 1:
                    return trim(i / w * 0.3 + 0.4)
                return g(X, Y)
        paint_face(hum, face, fn)
    gem = lambda: (120, 235, 255)
    # --- robe torso (body 16,16 8x12x4)
    for name, face in box_faces(16, 16, 8, 12, 4).items():
        def fn(i, j, w, h, X, Y, name=name):
            if name == 'bottom':
                return g(X, Y)
            if name == 'front':
                if j <= 2 and (i == 3 - j or i == 4 + j):
                    return trim(0.2 + j * 0.05)          # V collar
                if 3 <= i <= 4 and j == 3:
                    return WHITE if i == 3 else gem()    # crystal clasp
                if i in (3, 4) and j > 3:
                    return trim(0.55 + j / 40)           # front opening trim
                if j == 8:
                    return trim(0.8 + i / 30)            # sash
            if name in ('left', 'right', 'back') and j == 8:
                return trim(0.8 + i / 30)
            return g(X, Y)
        paint_face(hum, face, fn)
    # --- sleeves (arm 40,16 4x12x4)
    for name, face in box_faces(40, 16, 4, 12, 4).items():
        def fn(i, j, w, h, X, Y, name=name):
            if name not in ('top', 'bottom') and j >= h - 2:
                return trim(0.35 + i / 12 + (j - h) * 0.05)
            return g(X, Y)
        paint_face(hum, face, fn)
    # --- boots (leg 0,16 4x12x4) lower part only
    for name, face in box_faces(0, 16, 4, 12, 4).items():
        def fn(i, j, w, h, X, Y, name=name):
            if name == 'top':
                return None
            if name == 'bottom':
                return trim(0.6)
            if j < 7:
                return None
            if j == 7:
                return trim(0.15 + i / 10)
            if j == h - 1:
                return trim(0.6 + i / 10)
            return g(X, Y)
        paint_face(hum, face, fn)
    # --- leggings layer: robe skirt over legs + waist
    for name, face in box_faces(0, 16, 4, 12, 4).items():
        def fn(i, j, w, h, X, Y, name=name):
            if name == 'top':
                return g(X, Y)
            if name == 'bottom':
                return None
            if j >= h - 2:
                return trim(0.05 + i / 10 + j * 0.02)    # glowing hem
            if j == h - 3 and (i + X) % 2 == 0:
                return mix(g(X, Y), WHITE, 0.5)
            return g(X, Y)
        paint_face(leg, face, fn)
    for name, face in box_faces(16, 16, 8, 12, 4).items():
        def fn(i, j, w, h, X, Y, name=name):
            if name in ('top',):
                return None
            if name == 'bottom':
                return g(X, Y)
            if j < 7:
                return None
            if j == 8:
                return trim(0.8 + i / 30)
            return g(X, Y)
        paint_face(leg, face, fn)
    save_tex(hum, 'entity/equipment/humanoid/netherite.png')
    save_tex(leg, 'entity/equipment/humanoid_leggings/netherite.png')
    # --- 3D cloak on the elytra geometry (wing box texOffs 22,0 size 10x20x2)
    cloak = Image.new('RGBA', (64, 32))
    for name, face in box_faces(22, 0, 10, 20, 2).items():
        def fn(i, j, w, h, X, Y, name=name):
            if name in ('front', 'back'):
                if j >= h - 2:
                    return trim(0.1 + i / 20 + j * 0.03)
                if (name == 'front' and i == 0) or (name == 'back' and i == w - 1):
                    return trim(0.4 + j / 40)
                if j == 0:
                    return trim(0.7)
            return galaxy_px(X * 2, Y * 2, seed=9)
        paint_face(cloak, face, fn)
    save_tex(cloak, 'entity/equipment/wings/aurora_cloak.png')
    eq = json.load(open(REF + 'equipment/netherite.json'))
    eq["layers"]["wings"] = [{"texture": "minecraft:aurora_cloak"}]
    save_json(eq, 'equipment/netherite.json')
    return hum, leg, cloak

def crystal_worn(im):
    """worn diamond armor: rank the vanilla shades so the crystal keeps real contrast on the body"""
    W, H = im.size
    lv = lambda p: round(0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2])
    levels = sorted({lv(p) for p in im.getdata() if p[3]})
    rank = {l: i / max(1, len(levels) - 1) for i, l in enumerate(levels)}
    stops = [(52, 36, 112), (118, 98, 200), None, (232, 226, 254), (255, 255, 255)]
    POS = [0.0, 0.12, 0.42, 0.85, 1.0]   # most vanilla shades land on the aurora colour
    o = Image.new('RGBA', im.size)
    for y in range(H):
        for x in range(W):
            p = im.getpixel((x, y))
            if not p[3]:
                continue
            t = (x * 0.6 + y) / W * 0.6
            sts = [c if c else cyc(t) for c in stops]
            r = rank[lv(p)]
            i = max(k for k in range(len(POS) - 1) if POS[k] <= r)
            o.putpixel((x, y), C(mix(sts[i], sts[i + 1], (r - POS[i]) / (POS[i + 1] - POS[i])), p[3]))
    return o

def diamond_worn():
    out = []
    for layer in ('humanoid', 'humanoid_leggings'):
        o = crystal_worn(ref('entity/equipment/%s/diamond.png' % layer))
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
            im = ref(rel); o = Image.new('RGBA', im.size); W, H = im.size
            if mat == 'diamond':
                save_tex(crystal_worn(im), rel); out[(layer, mat)] = None
                continue
            vs = [hsv(im.getpixel((x, y)))[2] for y in range(H) for x in range(W) if im.getpixel((x, y))[3]]
            vmean = sum(vs) / max(1, len(vs))
            for y in range(H):
                for x in range(W):
                    p = im.getpixel((x, y))
                    if not p[3]:
                        continue
                    if mat == 'diamond':
                        c = crystal_px(p, (x * 0.6 + y) / W * 0.6)
                    else:
                        v = hsv(p)[2]
                        c = galaxy_px(x, y, seed=4)
                        c = tuple(q * max(0.45, min(1.6, 1 + (v - vmean) * 2.2)) for q in c)
                        if v > vmean + 0.16:
                            c = mix(c, trim((x + y) / (W + H)), 0.65)
                    o.putpixel((x, y), C(c, p[3]))
            save_tex(o, rel); out[(layer, mat)] = o
    return out

# ------------------------------------------------------------------ preview
def player_preview(hum, leg, cloak, skin_front=None):
    """flat front + back of the robe on a player silhouette, plus cloak panel"""
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
        if which == 'back':
            cl = cloak.crop((36, 2, 46, 22)).resize((14, 26), Image.NEAREST)
        for img, parts in ((leg, [((4, 20), (0, 16, 4, 12, 4)), ((8, 20), (0, 16, 4, 12, 4)), ((4, 8), (16, 16, 8, 12, 4))]),
                           (hum, [((4, 0), (0, 0, 8, 8, 8)), ((4, 8), (16, 16, 8, 12, 4)), ((0, 8), (40, 16, 4, 12, 4)),
                                  ((12, 8), (40, 16, 4, 12, 4)), ((4, 20), (0, 16, 4, 12, 4)), ((8, 20), (0, 16, 4, 12, 4))])):
            for at, (u, v, w, h, d) in parts:
                c.alpha_composite(face(img, u, v, w, h, d, which), at)
        if which == 'back':
            c.alpha_composite(cl, (1, 8))
        return c
    out = Image.new('RGBA', (60, 40), (40, 34, 60, 255))
    out.alpha_composite(body('front'), (6, 4)); out.alpha_composite(body('back'), (34, 4))
    return out.resize((360, 240), Image.NEAREST)

if __name__ == '__main__':
    t = tools(); glint()
    di = diamond_armor_icons(); ni = netherite_armor_icons()
    hum, leg, cloak = galaxy_robe(); diamond_worn(); ow = other_worn()
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
    sheet.alpha_composite(player_preview(hum, leg, cloak), (10, 290))
    sheet.alpha_composite(hum.resize((256, 128), Image.NEAREST), (390, 290))
    sheet.alpha_composite(cloak.crop((22, 0, 46, 22)).resize((96, 88), Image.NEAREST), (650, 290))
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
