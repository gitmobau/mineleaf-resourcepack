# Aurora HUD icons: hearts in the Aurora palette (every status keeps its own colour family) and food as stars.
# Calm by design (on screen all the time): each icon is a soft two-tone pastel gradient with a pearl highlight and a
# deeper lower edge, no colour cycling. The only motion is a short pearl glint that crosses every heart and star at
# the same moment once per loop (all of them share N/FT, so they stay in sync).
import os, json
from PIL import Image

HOME = os.path.expanduser('~')
# Paths can be overridden by build.py (AURORA_REF = folder holding assets/minecraft of vanilla 26.3,
# AURORA_RP = resourcepacks folder).
REF_ROOT = os.environ.get('AURORA_REF', HOME + '/ref63')
RP = os.environ.get('AURORA_RP', HOME + '/mnt/.minecraft/resourcepacks')
REF = REF_ROOT + '/assets/minecraft/textures/'
TX = RP + '/Aurora Pack/assets/minecraft/textures/'
H = 'gui/sprites/hud/'
N, FT = 20, 4         # 80 ticks = 4 s per loop; every animated heart/star shares this so they stay in sync
GLINT = {0: 1.0, 1: 0.55}   # frame -> strength of the pearl glint (the other frames are identical and get merged)

WHITE = (255, 255, 255)
OUT = (40, 24, 82)

def mix(a, b, f):
    return tuple(a[k] + (b[k] - a[k]) * f for k in range(3))

def C(c, a=255):
    return tuple(int(max(0, min(255, round(v)))) for v in c[:3]) + (int(max(0, min(255, a))),)

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
# vanilla 9x9 heart layout (the fill sprites leave a 1 px ring for the container's outline)
HEART = {(x, y) for y, row in enumerate([
    ".........",
    "..##.##..",
    ".#######.",
    ".#######.",
    ".#######.",
    "..#####..",
    "...###...",
    "....#....",
    ".........",
]) for x, ch in enumerate(row) if ch == '#'}
LOWER = {(1, 4), (7, 4), (2, 5), (6, 5), (3, 6), (5, 6), (4, 7)}          # vanilla's darker lower rim
HARDCORE = {(2, 2), (6, 2), (2, 3), (3, 3), (5, 3), (6, 3), (3, 4), (5, 4)}  # vanilla hardcore marks
SHINE = (2, 2)                                                               # vanilla highlight pixel
SOFT = ((3, 2), (2, 3))                                                      # gentle gloss next to it

# per status: top colour, bottom colour, lower rim, highlight, hardcore marks
HEARTS = {
    '':          ((255, 158, 205), (212, 146, 250), (160, 104, 214), (255, 238, 248), (138, 72, 168)),
    'poisoned_': ((196, 240, 150), (112, 214, 168), (60, 160, 128), (240, 255, 222), (46, 120, 98)),
    'withered_': ((108, 96, 134), (76, 66, 104), (52, 42, 76), (184, 174, 204), (34, 26, 52)),
    'frozen_':   ((228, 247, 255), (156, 208, 252), (104, 160, 226), (255, 255, 255), (96, 146, 214)),
    'absorbing_':((255, 236, 158), (255, 194, 136), (228, 146, 104), (255, 251, 226), (196, 118, 70)),
    'vehicle_':  ((238, 232, 255), (196, 186, 246), (148, 136, 214), (255, 255, 255), (120, 108, 190)),
}
CONTAINER = (OUT, (64, 48, 100))            # outline, inside: a quiet plum slot that still reads on dark worlds
VEHICLE_CONTAINER = ((62, 52, 112), (92, 82, 138))

def heart_colour(x, y, pal, hardcore):
    top, bot, rim, hi, mark = pal
    t = min(1.0, max(0.0, ((y - 1) + (x - 1) * 0.3) / 7.5))           # soft diagonal gradient, top-left lighter
    c = mix(top, bot, t)
    if hardcore and (x, y) in HARDCORE: return mix(mark, c, 0.15)
    if (x, y) in LOWER: return mix(c, rim, 0.75)
    if not hardcore:
        if (x, y) == SHINE: return hi
        if (x, y) in SOFT: return mix(c, hi, 0.4)
    elif (x, y) in ((4, 2), (4, 3)): return mix(c, hi, 0.45)              # pearl seam between the marks
    if y == 1: return mix(c, hi, 0.25)
    return c

def paint_heart(src, pal, hardcore, blink, f):
    o = Image.new('RGBA', src.size)
    g = GLINT.get(f, 0.0)
    for (x, y) in HEART:
        a = src.getpixel((x, y))[3]
        if a == 0: continue
        c = heart_colour(x, y, pal, hardcore)
        if g:                                                            # pearl glint sweeping the upper-left lobe
            d = abs((x + y) - (5 if f == 0 else 7))
            if d == 0: c = mix(c, WHITE, 0.55 * g)
            elif d == 1: c = mix(c, WHITE, 0.2 * g)
        if blink: c = mix(c, WHITE, 0.42)
        o.putpixel((x, y), C(c, 255))
    return o

def container(src, line, inside, blink):
    o = Image.new('RGBA', src.size)
    for y in range(src.height):
        for x in range(src.width):
            p = src.getpixel((x, y))
            if p[3] == 0: continue
            edge = p[0] < 20 or p[0] > 200 and p[1] > 200        # black outline (white when blinking)
            c = line if edge else inside
            if blink: c = mix(line, WHITE, 0.8) if edge else mix(inside, WHITE, 0.12)
            o.putpixel((x, y), C(c, p[3]))
    return o

def hearts():
    names = sorted(n[:-4] for n in os.listdir(REF + H + 'heart') if n.endswith('.png'))
    for n in names:
        src = ref(H + 'heart/%s.png' % n)
        blink = n.endswith('_blinking')
        if n.startswith('container') or n == 'vehicle_container':
            line, inside = VEHICLE_CONTAINER if n.startswith('vehicle') else CONTAINER
            save(container(src, line, inside, blink), H + 'heart/%s.png' % n, False)
            continue
        kind = next((k for k in HEARTS if k and n.startswith(k)), '')
        hardcore = 'hardcore' in n
        strip = Image.new('RGBA', (9, 9 * N))
        for f in range(N):
            strip.alpha_composite(paint_heart(src, HEARTS[kind], hardcore, blink, f), (0, f * 9))
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
# top colour, bottom colour, lower shade, highlight
GOLD = ((255, 240, 170), (255, 186, 160), (236, 140, 150), (255, 252, 232))
SICK = ((210, 232, 150), (150, 200, 128), (98, 150, 96), (240, 250, 214))

def star_mask():
    m = {(x, y) for y, row in enumerate(STAR) for x, ch in enumerate(row) if ch == '#'}
    edge = {(x, y) for (x, y) in m if any((x + dx, y + dy) not in m for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    return m, edge

def food():
    m, edge = star_mask(); inner = m - edge
    lowest = {(x, y) for (x, y) in inner if (x, y + 1) not in inner}
    for suffix, pal, line, inside in (('', GOLD, OUT, CONTAINER[1]), ('_hunger', SICK, (30, 56, 34), (58, 82, 52))):
        top, bot, shade, hi = pal
        o = Image.new('RGBA', (9, 9))
        for (x, y) in m: o.putpixel((x, y), C(line if (x, y) in edge else inside))
        save(o, H + 'food_empty%s.png' % suffix, False)
        for half in (False, True):
            strip = Image.new('RGBA', (9, 9 * N))
            for f in range(N):
                g = GLINT.get(f, 0.0)
                for (x, y) in inner:
                    if half and x < 4: continue                              # the bar empties from the left
                    c = mix(top, bot, min(1.0, (y - 1) / 6))
                    if (x, y) in lowest: c = mix(c, shade, 0.6)
                    if (x, y) in ((4, 1), (4, 2)): c = mix(c, hi, 0.7)       # pearl tip
                    if g and (x, y) in ((4, 3), (3, 3), (5, 3), (4, 4)):
                        c = mix(c, WHITE, (0.7 if (x, y) == (4, 3) else 0.35) * g)   # glint in the heart of the star
                    strip.putpixel((x, f * 9 + y), C(c))
            save(strip, H + 'food_%s%s.png' % ('half' if half else 'full', suffix), True)

if __name__ == '__main__':
    n = hearts(); food()
    print('hearts', n, 'ok')
