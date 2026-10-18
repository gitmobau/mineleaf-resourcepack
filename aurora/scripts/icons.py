# Aurora HUD icons: hearts in the Aurora palette (every status keeps its own colours) and food as stars.
import os, math, json
from PIL import Image

HOME = os.path.expanduser('~')
# Paths can be overridden by build.py (AURORA_REF = folder holding assets/minecraft of vanilla 26.3,
# AURORA_RP = resourcepacks folder).
REF_ROOT = os.environ.get('AURORA_REF', HOME + '/ref63')
RP = os.environ.get('AURORA_RP', HOME + '/mnt/.minecraft/resourcepacks')
REF = REF_ROOT + '/assets/minecraft/textures/'
TX = RP + '/Aurora Pack/assets/minecraft/textures/'
H = 'gui/sprites/hud/'
N, FT = 8, 4          # every animated heart/star shares this so they stay in sync on screen

WHITE = (255, 255, 255)
OUT = (40, 24, 82)

def mix(a, b, f):
    return tuple(a[k] + (b[k] - a[k]) * f for k in range(3))

def C(c, a=255):
    return tuple(int(max(0, min(255, round(v)))) for v in c[:3]) + (int(max(0, min(255, a))),)

def cyc(t, pal):
    t = (t % 1.0) * len(pal); i = int(t) % len(pal); f = t - int(t)
    return mix(pal[i], pal[(i + 1) % len(pal)], f)

def ref(rel):
    return Image.open(REF + rel).convert('RGBA')

def save(im, rel, animated):
    p = TX + rel
    os.makedirs(os.path.dirname(p), exist_ok=True)
    im.save(p, optimize=True)
    if animated:
        with open(p + '.mcmeta', 'w') as f:
            json.dump({"animation": {"frametime": FT, "interpolate": False}}, f, indent=2)
    elif os.path.exists(p + '.mcmeta'):
        os.remove(p + '.mcmeta')

# ------------------------------------------------------------------ hearts
# palette per status: (fill ramp, container outline, container inside)
HEARTS = {
    '':          ([(255, 125, 200), (225, 135, 255), (150, 160, 255), (110, 215, 255), (255, 150, 190)], OUT, (52, 30, 92)),
    'poisoned_': ([(150, 245, 170), (110, 235, 205), (190, 250, 140), (120, 220, 190)], (24, 60, 52), (30, 70, 64)),
    'withered_': ([(70, 50, 120), (40, 30, 90), (95, 60, 140), (55, 40, 105)], (12, 8, 30), (26, 18, 50)),
    'frozen_':   ([(200, 245, 255), (160, 225, 255), (235, 250, 255), (175, 210, 255)], (40, 80, 130), (60, 100, 150)),
    'absorbing_':([(255, 225, 130), (255, 195, 140), (255, 240, 170), (255, 205, 120)], (110, 70, 30), (120, 80, 40)),
    'vehicle_':  ([(225, 215, 255), (200, 200, 245), (240, 235, 255), (210, 220, 250)], (70, 60, 120), (90, 80, 140)),
}

def recolor_heart(src, pal, f, blink):
    o = Image.new('RGBA', src.size)
    for y in range(src.height):
        for x in range(src.width):
            p = src.getpixel((x, y))
            if p[3] == 0: continue
            l = (p[0] + p[1] + p[2]) / 3
            base = cyc((x + y) / 16 - f / N, pal)
            if l > 180: c = mix(WHITE, base, 0.1)                      # highlight
            elif l < 60: c = mix(base, OUT, 0.55)                      # hardcore marks
            elif l < 85: c = mix(base, OUT, 0.3)                       # lower shading
            else: c = mix(base, WHITE, 0.12 if y < 4 else 0.0)
            if blink: c = mix(c, WHITE, 0.45)
            o.putpixel((x, y), C(c, p[3]))
    if f % N in (1, 2) and src.getpixel((2, 2))[3]:                       # travelling glint
        o.putpixel((2 + (f % N), 2), C(WHITE))
    return o

def hearts():
    names = sorted(n[:-4] for n in os.listdir(REF + H + 'heart') if n.endswith('.png'))
    for n in names:
        src = ref(H + 'heart/%s.png' % n)
        blink = n.endswith('_blinking')
        if n.startswith('container') or n == 'vehicle_container':
            pal, line, inside = HEARTS['vehicle_' if n.startswith('vehicle') else '']
            o = Image.new('RGBA', src.size)
            for y in range(src.height):
                for x in range(src.width):
                    p = src.getpixel((x, y))
                    if p[3] == 0: continue
                    c = line if p[0] < 20 else inside
                    if blink: c = mix(c, WHITE, 0.7) if p[0] < 20 else mix(c, WHITE, 0.25)
                    o.putpixel((x, y), C(c, p[3]))
            save(o, H + 'heart/%s.png' % n, False)
            continue
        kind = next((k for k in HEARTS if k and n.startswith(k)), '')
        strip = Image.new('RGBA', (9, 9 * N))
        for f in range(N):
            strip.alpha_composite(recolor_heart(src, HEARTS[kind][0], f, blink), (0, f * 9))
        save(strip, H + 'heart/%s.png' % n, True)
    return len(names)

# ------------------------------------------------------------------ food -> stars
STAR = [
    "....#....",
    "...###...",
    "...###...",
    "#########",
    ".#######.",
    "..#####..",
    "..#####..",
    ".###.###.",
    ".##...##.",
]
GOLD = [(255, 236, 150), (255, 205, 160), (255, 175, 205), (240, 170, 255), (255, 215, 140)]
SICK = [(190, 230, 140), (150, 210, 130), (205, 235, 160), (160, 200, 120)]

def star_mask():
    m = {(x, y) for y, row in enumerate(STAR) for x, ch in enumerate(row) if ch == '#'}
    edge = {(x, y) for (x, y) in m if any((x + dx, y + dy) not in m for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    return m, edge

def food():
    m, edge = star_mask(); inner = m - edge
    for suffix, pal, line, inside in (('', GOLD, OUT, (52, 30, 92)), ('_hunger', SICK, (30, 56, 30), (44, 70, 40))):
        o = Image.new('RGBA', (9, 9))
        for (x, y) in m: o.putpixel((x, y), C(line if (x, y) in edge else inside))
        save(o, H + 'food_empty%s.png' % suffix, False)
        for half in (False, True):
            strip = Image.new('RGBA', (9, 9 * N))
            for f in range(N):
                tw = 0.5 + 0.5 * math.sin(f / N * 2 * math.pi)
                for (x, y) in inner:
                    if half and x < 4: continue
                    c = cyc((y * 1.2 + x * 0.4) / 14 - f / N, pal)
                    if (x, y) in ((4, 1), (4, 2), (3, 3)): c = mix(c, WHITE, 0.55 + 0.4 * tw)   # sparkle at the top
                    elif y >= 6: c = mix(c, OUT, 0.18)
                    strip.putpixel((x, f * 9 + y), C(c))
                if f % N == 0 and not half:
                    strip.putpixel((4, f * 9 + 4), C(WHITE))
            save(strip, H + 'food_%s%s.png' % ('half' if half else 'full', suffix), True)

if __name__ == '__main__':
    n = hearts(); food()
    print('hearts', n, 'ok')
