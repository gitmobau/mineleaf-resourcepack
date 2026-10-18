# Aurora base: crosshair, attack indicators, XP bar background, container slot, pack.png and pack.mcmeta.
# (Hotbar, selection, XP progress, inventory and tools used to be drawn here too; magic.py, gear.py and Aurora HUD XL
# replace all of them, so only what survives in the final pack is generated now. Water was removed on purpose.)
import os, sys, math, json
from PIL import Image, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # build.py runs scripts with -I
import gear

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
for n in ['hotbar_attack_indicator_background', 'hotbar_attack_indicator_progress',
          'crosshair_attack_indicator_background', 'crosshair_attack_indicator_full',
          'crosshair_attack_indicator_progress']:
    if os.path.exists(REF + '/' + H + n + '.png'):
        save(hud_map(load(H + n + '.png'), 0.1, 0.5, 1.2), H + n + '.png')

bg = load(H + 'experience_bar_background.png')
out = Image.new('RGBA', bg.size)
for y in range(bg.height):
    for x in range(bg.width):
        p = bg.getpixel((x, y))
        if p[3]:
            out.putpixel((x, y), clamp(mix((22, 17, 40), cyc(x / 182 * 0.9), 0.18 + lum(p) / 255 * 0.25), p[3]))
save(out, H + 'experience_bar_background.png')

# Crosshair. The game draws it with an INVERT blend (result = src * (1 - dst) + dst * (1 - src)), so near-white keeps
# the vanilla contrast everywhere and a light tint shows as pastel only against dark scenes. Small centre dot, 1 px gap,
# four short arms whose tips take a hint of cyan / lavender / pink / peach. No diagonal dots: clean and calm.
ch = Image.new('RGBA', (15, 15), (0, 0, 0, 0))
ch.putpixel((7, 7), (255, 255, 255, 255))
for (dx, dy), t in {(0, -1): 0.0, (1, 0): 0.2, (0, 1): 0.4, (-1, 0): 0.6}.items():
    for d in range(2, 6):
        ch.putpixel((7 + dx * d, 7 + dy * d), clamp(mix((255, 255, 255), cyc(t), (d - 2) * 0.22)))
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

save(inv_map(load('gui/sprites/container/slot.png'), 0, 0.3), 'gui/sprites/container/slot.png')

# pack.png: night sky with two soft aurora ribbons and the Aurora diamond pickaxe with a gentle glow.
S = 128
icon = Image.new('RGBA', (S, S))
for y in range(S):
    for x in range(S):
        c = mix((44, 34, 86), (18, 14, 36), y / S)
        for k, (y0, amp, ph, w) in enumerate(((44, 10, 0.0, 15.0), (70, 8, 1.7, 11.0))):
            yc = y0 + amp * math.sin(x / 21 + ph) + (x - 64) * 0.18
            g = math.exp(-((y - yc) / w) ** 2)
            c = mix(c, gear.cyc(x / 190 + k * 0.33, gear.P), 0.55 * g)
        icon.putpixel((x, y), clamp(c))
for x, y in ((14, 18), (101, 12), (116, 52), (22, 96), (108, 108), (60, 8), (8, 60)):
    icon.putpixel((x, y), (255, 255, 255, 255))
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        icon.putpixel((x + dx, y + dy), clamp(mix(icon.getpixel((x + dx, y + dy)), (255, 255, 255), 0.45)))
pick, _ = gear.recolor_tool('diamond_pickaxe', 'diamond')
big = pick.resize((96, 96), Image.NEAREST)
glow = Image.new('RGBA', (S, S), (0, 0, 0, 0))
halo = Image.new('RGBA', big.size, (236, 226, 255, 0))
halo.putalpha(big.getchannel('A'))
glow.alpha_composite(halo, (16, 16))
glow = glow.filter(ImageFilter.GaussianBlur(5))
glow.putalpha(glow.getchannel('A').point(lambda a: int(a * 0.8)))
icon.alpha_composite(glow)
icon.alpha_composite(big, (16, 16))
icon.save(PACK + '/pack.png', optimize=True)

with open(PACK + '/pack.mcmeta', 'w') as f:
    json.dump({"pack": {
        "description": ["", {"text": "Aurora ", "color": "#B9B9F8"},
                        {"text": "· menús, HUD, herramientas y armaduras", "color": "#F8B0EA"}],
        "min_format": 84,
        "max_format": 97
    }}, f, indent=2, ensure_ascii=False)
print('ok')
