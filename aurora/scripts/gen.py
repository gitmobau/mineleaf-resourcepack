import os, math, json, colorsys, shutil
from PIL import Image

HOME = os.path.expanduser('~')
# Paths can be overridden by build.py (AURORA_REF = folder holding assets/minecraft of vanilla 26.3,
# AURORA_RP = resourcepacks folder, AURORA_PREVIEWS = where preview images go).
REF_ROOT = os.environ.get('AURORA_REF', HOME + '/ref63')
RP = os.environ.get('AURORA_RP', HOME + '/mnt/.minecraft/resourcepacks')
REF = REF_ROOT + '/assets/minecraft/textures'
PACK = RP + '/Aurora Pack'
TX = PACK + '/assets/minecraft/textures'

P = [(123,225,249),(155,210,248),(187,185,248),(220,181,240),(248,176,234),
     (248,188,199),(248,201,173),(248,225,156),(209,248,145),(170,245,215)]

def cyc(t):
    t = (t % 1.0) * len(P); i = int(t) % len(P); f = t - int(t)
    a = P[i]; b = P[(i + 1) % len(P)]
    return tuple(a[k] + (b[k] - a[k]) * f for k in range(3))

def mix(a, b, f):
    return tuple(a[k] + (b[k] - a[k]) * f for k in range(3))

def clamp(c, a=255):
    return tuple(int(max(0, min(255, round(v)))) for v in c) + (int(a),)

def lum(p):
    return (0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2])

def load(rel):
    return Image.open(REF + '/' + rel).convert('RGBA')

def save(im, rel, mcmeta=None):
    path = TX + '/' + rel
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path, optimize=True)
    if mcmeta is not None:
        with open(path + '.mcmeta', 'w') as f:
            json.dump(mcmeta, f, indent=2)

DEEP = (26, 20, 46)

def hud_map(im, t0=0.0, span=0.9, bright=1.0, axis='x'):
    w, h = im.size
    out = Image.new('RGBA', im.size)
    for y in range(h):
        for x in range(w):
            p = im.getpixel((x, y))
            if p[3] == 0:
                continue
            t = t0 + span * ((x / max(1, w - 1)) if axis == 'x' else (x + y) / max(1, w + h - 2))
            c = cyc(t)
            l = lum(p) / 255
            if p[3] < 255:
                out.putpixel((x, y), clamp(mix((20, 15, 38), c, 0.10), min(255, p[3] + 20)))
                continue
            l2 = min(1, l * bright)
            col = mix(DEEP, c, min(1, l2 * 1.25))
            if l2 > 0.82:
                col = mix(col, (255, 255, 255), (l2 - 0.82) / 0.18 * 0.6)
            out.putpixel((x, y), clamp(col, p[3]))
    return out

H = 'gui/sprites/hud/'
save(hud_map(load(H + 'hotbar.png')), H + 'hotbar.png')
for n in ['hotbar_offhand_left', 'hotbar_offhand_right']:
    save(hud_map(load(H + n + '.png'), 0.2, 0.3), H + n + '.png')
for n in ['hotbar_attack_indicator_background', 'hotbar_attack_indicator_progress',
          'crosshair_attack_indicator_background', 'crosshair_attack_indicator_full',
          'crosshair_attack_indicator_progress']:
    if os.path.exists(REF + '/' + H + n + '.png'):
        save(hud_map(load(H + n + '.png'), 0.1, 0.5, 1.2), H + n + '.png')

sel = load(H + 'hotbar_selection.png')
FR = 16
anim = Image.new('RGBA', (sel.width, sel.height * FR))
for f in range(FR):
    fr = hud_map(sel, f / FR, 0.9, 1.3, axis='diag')
    anim.paste(fr, (0, f * sel.height))
save(anim, H + 'hotbar_selection.png', {"animation": {"frametime": 3, "interpolate": True}})

bg = load(H + 'experience_bar_background.png')
out = Image.new('RGBA', bg.size)
for y in range(bg.height):
    for x in range(bg.width):
        p = bg.getpixel((x, y))
        if p[3]:
            out.putpixel((x, y), clamp(mix((22, 17, 40), cyc(x / 182 * 0.9), 0.18 + lum(p) / 255 * 0.25), p[3]))
save(out, H + 'experience_bar_background.png')
pr = load(H + 'experience_bar_progress.png')
out = Image.new('RGBA', pr.size)
for y in range(pr.height):
    for x in range(pr.width):
        p = pr.getpixel((x, y))
        if p[3]:
            l = lum(p) / 255
            out.putpixel((x, y), clamp(mix((40, 30, 70), cyc(x / 182 * 0.9), 0.35 + l * 0.9), p[3]))
save(out, H + 'experience_bar_progress.png')

ch = Image.new('RGBA', (15, 15), (0, 0, 0, 0))
ch.putpixel((7, 7), (255, 255, 255, 255))
arms = {(0, -1): 0.0, (1, 0): 0.25, (0, 1): 0.5, (-1, 0): 0.75}
for (dx, dy), t in arms.items():
    for d in range(2, 7):
        a = 255 if d <= 5 else 150
        col = mix((255, 255, 255), cyc(t + d * 0.02), 0.35 + d * 0.06)
        ch.putpixel((7 + dx * d, 7 + dy * d), clamp(col, a))
for dx, dy in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
    ch.putpixel((7 + dx, 7 + dy), (235, 230, 255, 170))
save(ch, H + 'crosshair.png')

STOPS = [(0, (26, 20, 46)), (55, (60, 46, 96)), (85, (98, 80, 146)), (139, None), (198, None), (255, (255, 255, 255))]
def inv_color(l, t):
    c = cyc(t)
    stops = []
    for v, col in STOPS:
        if v == 139:
            col = mix((140, 122, 192), c, 0.30)
        elif v == 198:
            col = mix((236, 232, 250), c, 0.42)
        stops.append((v, col))
    for i in range(len(stops) - 1):
        v0, c0 = stops[i]; v1, c1 = stops[i + 1]
        if l <= v1:
            return mix(c0, c1, (l - v0) / (v1 - v0))
    return stops[-1][1]

def inv_map(im, scale_t=1.0, t0=0.0):
    w, h = im.size
    out = Image.new('RGBA', im.size)
    for y in range(h):
        for x in range(w):
            p = im.getpixel((x, y))
            if p[3] == 0:
                continue
            t = t0 + scale_t * (x / 176 * 0.55 + y / 166 * 0.35)
            out.putpixel((x, y), clamp(inv_color(lum(p), t), p[3]))
    return out

save(inv_map(load('gui/container/inventory.png')), 'gui/container/inventory.png')
save(inv_map(load('gui/sprites/container/slot.png'), 0, 0.3), 'gui/sprites/container/slot.png')
for n in ['slot_highlight_back', 'slot_highlight_front']:
    im = load('gui/sprites/container/' + n + '.png')
    out = Image.new('RGBA', im.size)
    for y in range(im.height):
        for x in range(im.width):
            p = im.getpixel((x, y))
            if p[3]:
                out.putpixel((x, y), clamp(mix((255, 255, 255), cyc((x + y) / 46 * 0.8), 0.75), p[3]))
    save(out, 'gui/sprites/container/' + n + '.png')
    shutil.copy(REF + '/gui/sprites/container/' + n + '.png.mcmeta', TX + '/gui/sprites/container/' + n + '.png.mcmeta')

TAU = 2 * math.pi
def water_px(u, v, ph, flow=False):
    if flow:
        band = u * 1 + v * 2 - ph * 2 + 0.12 * math.sin(TAU * (u + ph))
    else:
        band = u + v + 0.18 * math.sin(TAU * (v * 2 + ph)) + 0.10 * math.sin(TAU * (u - ph)) + ph
    c = cyc(band)
    w = 0.5 + 0.5 * math.sin(TAU * (u * 2 + v + ph * (2 if flow else 1)))
    w2 = 0.5 + 0.5 * math.sin(TAU * (v * 3 - u + ph * 3))
    l = 0.70 + 0.20 * w + 0.10 * w2
    col = mix((225, 235, 255), c, 0.80)
    col = tuple(min(255, q * l + 22 * w2) for q in col)
    if (int(u*97+v*61+ph*32*7) % 53) == 0: col = (255, 255, 255)
    a = 150 + 30 * w
    return clamp(col, a)

def water(size, frames, flow):
    im = Image.new('RGBA', (size, size * frames))
    for f in range(frames):
        ph = f / frames
        for y in range(size):
            for x in range(size):
                im.putpixel((x, f * size + y), water_px(x / size, y / size, ph, flow))
    return im

save(water(16, 32, False), 'block/water_still.png', {"animation": {"frametime": 2, "interpolate": True}})
save(water(32, 32, True), 'block/water_flow.png', {"animation": {"frametime": 2, "interpolate": True}})
ov = Image.new('RGBA', (16, 16))
for y in range(16):
    for x in range(16):
        ov.putpixel((x, y), clamp(mix((210, 225, 255), cyc((x + y) / 32), 0.5), 120))
save(ov, 'block/water_overlay.png')

def hsv(p):
    h, s, v = colorsys.rgb_to_hsv(*[q / 255 for q in p[:3]])
    return h * 360, s, v

def tool(name, kind):
    im = load('item/' + name + '.png')
    w, h = im.size
    out = Image.new('RGBA', im.size)
    W = (255, 255, 255)
    head = []
    for yy in range(h):
        for xx in range(w):
            q = im.getpixel((xx, yy))
            if q[3]:
                qh, qs, qv = hsv(q)
                if (kind == 'diamond' and (140 <= qh <= 200)) or (kind != 'diamond' and not ((qh >= 340 or qh <= 15) and qs >= 0.28)):
                    head.append(xx - yy)
    dmin, dmax = (min(head), max(head)) if head else (0, 1)
    for y in range(h):
        for x in range(w):
            p = im.getpixel((x, y))
            if p[3] == 0:
                continue
            hh, s, v = hsv(p)
            t = 0.5 * max(0, min(1, ((x - y) - dmin) / max(1, dmax - dmin)))
            t = round(t * 8) / 8
            c = cyc(t)
            if kind == 'diamond':
                if 140 <= hh <= 200 or s < 0.1:
                    if v < 0.2:   col = (46, 30, 92)
                    elif v < 0.3: col = (84, 62, 150)
                    elif v < 0.45: col = mix(c, (96, 74, 170), 0.55)
                    elif v < 0.6: col = mix(c, (120, 100, 200), 0.30)
                    elif v < 0.85: col = mix(c, (150, 130, 230), 0.10)
                    elif s > 0.4: col = mix(c, W, 0.30)
                    else: col = mix(c, W, 0.70)
                elif 10 <= hh < 30 and s > 0.6:
                    col = mix((90, 30, 80), (248, 176, 234), min(1, v * 1.5))
                else:
                    col = mix((40, 26, 44), (196, 140, 170), min(1, (v - 0.12) / 0.45))
            else:
                is_handle = (hh >= 340 or hh <= 15) and s >= 0.28
                if is_handle:
                    col = mix((26, 18, 34), (150, 110, 150), min(1, max(0, (v - 0.12) / 0.38)))
                elif 300 <= hh <= 330 and s > 0.35:
                    col = (72, 52, 116)
                else:
                    if v < 0.22:   col = (30, 24, 46)
                    elif v < 0.30: col = mix((52, 44, 74), c, 0.18)
                    elif v < 0.40: col = mix(c, (60, 50, 86), 0.50)
                    elif v < 0.48: col = mix(c, (70, 60, 100), 0.35)
                    else: col = mix(c, W, 0.15)
            out.putpixel((x, y), clamp(col, p[3]))
    save(out, 'item/' + name + '.png')
    return out

icons = {}
for mat in ['diamond', 'netherite']:
    for n in ['sword', 'pickaxe', 'axe', 'shovel', 'hoe', 'spear', 'spear_in_hand']:
        if os.path.exists(REF + '/item/%s_%s.png' % (mat, n)):
            icons[mat + '_' + n] = tool('%s_%s' % (mat, n), mat)

icon = Image.new('RGBA', (128, 128))
for y in range(128):
    for x in range(128):
        c = mix((20, 16, 38), cyc((x + y) / 256 + 0.05 * math.sin(x / 9)), 0.35 + 0.35 * (1 - y / 128))
        icon.putpixel((x, y), clamp(c))
icon.alpha_composite(icons['diamond_pickaxe'].resize((96, 96), Image.NEAREST), (16, 16))
icon.save(PACK + '/pack.png', optimize=True)

with open(PACK + '/pack.mcmeta', 'w') as f:
    json.dump({"pack": {
        "description": ["", {"text": "Aurora ", "color": "#B9B9F8"},
                        {"text": "· pastel HUD, agua y herramientas", "color": "#F8B0EA"}],
        "min_format": 84,
        "max_format": 97
    }}, f, indent=2, ensure_ascii=False)
print('ok')
