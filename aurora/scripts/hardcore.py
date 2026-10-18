# Aurora dragon egg trophy. hearts()/hunger_armor() are kept for reference; the build only runs dragon_egg().
import os, sys, math, json, colorsys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # build.py runs scripts with -I
import gear
from gear import mix, C, WHITE, OUT

REF = gear.REF
PACK = gear.PACK
PREVIEWS = gear.PREVIEWS
save_tex, save_json = gear.save_tex, gear.save_json
H = 'gui/sprites/hud/'

def ref(rel):
    return Image.open(REF + 'textures/' + rel).convert('RGBA')

def lum(p):
    return (0.3 * p[0] + 0.59 * p[1] + 0.11 * p[2]) / 255

# heart fill colours per state: (main A, main B for the shimmer gradient, mark colour)
HEART = {
    '':          ((255, 120, 190), (185, 140, 255), (70, 26, 110)),
    'poisoned':  ((150, 235, 150), (110, 220, 200), (30, 90, 60)),
    'withered':  ((96, 84, 120), (70, 58, 96), (30, 20, 40)),
    'frozen':    ((170, 235, 255), (150, 200, 255), (40, 90, 150)),
    'absorbing': ((255, 225, 120), (255, 190, 150), (130, 80, 20)),
    'vehicle':   ((255, 185, 140), (255, 150, 170), (110, 50, 40)),
}

def heart_fill(v, state, blinking, N=12):
    """recolour a vanilla heart fill sprite. Brightest pixel = highlight, darkest = hardcore marks."""
    a, b, mark = HEART[state]
    px = [(x, y, v.getpixel((x, y))) for y in range(v.height) for x in range(v.width) if v.getpixel((x, y))[3] > 8]
    from collections import Counter
    main = Counter(p[2][:3] for p in px).most_common(1)[0][0]
    lm = max(0.05, lum(main))
    st = Image.new('RGBA', (v.width, v.height * N))
    for f in range(N):
        ph = f / N
        for (x, y, p) in px:
            r = lum(p) / lm
            g = (x + y) / 16
            c = mix(a, b, 0.5 + 0.5 * math.sin((g - ph) * 2 * math.pi))
            if r > 1.25 and lum(p) > 0.5: c = WHITE         # highlight
            elif r < 0.55: c = mark                        # hardcore marks / deep shade
            elif r < 0.9:  c = mix(c, (60, 30, 100), 0.35)  # shade
            # shimmer sweep
            d = abs((x - y + 9) / 18 - (ph * 1.5 - 0.25))
            if d < 0.08 and r >= 0.55: c = mix(c, WHITE, 0.6 * (1 - d / 0.08))
            if blinking: c = mix(c, WHITE, 0.45)
            st.putpixel((x, f * v.height + y), C(c, p[3]))
    return st

def hearts():
    out = {}
    d = REF + 'textures/' + H + 'heart/'
    for fn in sorted(os.listdir(d)):
        if not fn.endswith('.png'): continue
        n = fn[:-4]
        v = ref(H + 'heart/' + fn)
        if n.startswith('container') or n == 'vehicle_container':
            o = Image.new('RGBA', v.size)
            for y in range(v.height):
                for x in range(v.width):
                    p = v.getpixel((x, y))
                    if p[3] == 0: continue
                    if p[:3] == (255, 255, 255): c = (255, 236, 250)        # blinking outline
                    elif lum(p) < 0.05:          c = OUT
                    else:                        c = (36, 24, 66)
                    o.putpixel((x, y), C(c, p[3]))
            save_tex(o, H + 'heart/' + fn)
            out[n] = o
            continue
        state = next((s for s in ('poisoned', 'withered', 'frozen', 'absorbing', 'vehicle') if n.startswith(s)), '')
        st = heart_fill(v, state, n.endswith('_blinking'))
        save_tex(st, H + 'heart/' + fn, {"animation": {"frametime": 3}})
        out[n] = st
    return out

def recolor_icon(v, pal):
    """hue-keyed recolour for hunger / armor icons. pal: list of (hue range, target colour)."""
    o = Image.new('RGBA', v.size)
    for y in range(v.height):
        for x in range(v.width):
            p = v.getpixel((x, y))
            if p[3] == 0: continue
            h, s, val = colorsys.rgb_to_hsv(*[q / 255 for q in p[:3]])
            h *= 360
            if val < 0.12:
                c = OUT
            elif s < 0.18:
                c = mix(OUT, mix((150, 130, 210), WHITE, val), min(1, val * 1.4))
            else:
                tgt = next((t for (lo, hi), t in pal if lo <= h < hi), pal[-1][1])
                c = mix(mix(tgt, (50, 30, 90), 0.55), mix(tgt, WHITE, 0.25), val)
            o.putpixel((x, y), C(c, p[3]))
    return o

def hunger_armor():
    out = {}
    FOOD = [((0, 18), (255, 130, 175)), ((18, 50), (255, 195, 145)), ((50, 200), (150, 235, 170)), ((200, 361), (255, 130, 175))]
    HUNGER = [((0, 361), (150, 235, 170))]
    for n in ('food_full', 'food_half', 'food_empty', 'food_full_hunger', 'food_half_hunger', 'food_empty_hunger'):
        o = recolor_icon(ref(H + n + '.png'), HUNGER if 'hunger' in n else FOOD)
        save_tex(o, H + n + '.png'); out[n] = o
    for n in ('armor_full', 'armor_half', 'armor_empty'):
        v = ref(H + n + '.png')
        o = Image.new('RGBA', v.size)
        for y in range(v.height):
            for x in range(v.width):
                p = v.getpixel((x, y))
                if p[3] == 0: continue
                l = lum(p)
                if l < 0.12:   c = OUT
                elif l < 0.3:  c = (36, 24, 66)          # empty slot interior
                else:          c = mix(gear.cyc(0.45 + (x - y) / 30, gear.VIVID), WHITE, max(0, l - 0.45) * 1.4)
                o.putpixel((x, y), C(c, p[3]))
        save_tex(o, H + n + '.png'); out[n] = o
    return out

# ------------------------------------------------------------------ dragon egg
def galaxy_px(x, y, seed=0, phase=0.0):
    """deep violet nebula with soft drifting clouds (independent of gear.py)"""
    n = 0.0
    for k, (fx, fy, a) in enumerate(((0.35, 0.22, 0.5), (0.7, 0.5, 0.3), (1.3, 1.1, 0.2))):
        n += a * math.sin(fx * x + fy * y * 1.3 + seed * (k + 1) + phase * 2 * math.pi * (1 if k % 2 else -1))
    n = 0.5 + 0.5 * n
    base = mix((18, 10, 40), (72, 36, 120), n)
    return mix(base, gear.cyc(n * 0.5 + 0.55, gear.VIVID), 0.12 * n)

def dragon_egg(N=24):
    st = Image.new('RGBA', (16, 16 * N))
    for f in range(N):
        ph = f / N
        for y in range(16):
            for x in range(16):
                c = galaxy_px(x, y, seed=5, phase=ph)
                # two drifting aurora veins
                for k, (amp, off, th) in enumerate(((2.2, 5.0, 1.1), (1.8, 10.5, 0.9))):
                    cy = off + amp * math.sin((x / 16 + ph + k * 0.4) * 2 * math.pi)
                    d = abs(y - cy)
                    if d < th:
                        c = mix(c, gear.cyc(x / 16 * 0.6 + k * 0.35 + ph, gear.VIVID), (1 - d / th) * 0.85)
                if gear.hsh(x, y, 9) % 41 == 0 and (f + x) % 8 < 2:
                    c = WHITE
                st.putpixel((x, f * 16 + y), C(c))
    save_tex(st, 'block/dragon_egg.png', {"animation": {"frametime": 3, "interpolate": True}})
    m = json.load(open(REF + 'models/block/dragon_egg.json'))
    for el in m['elements']:
        el['light_emission'] = 10        # a soft glow: the egg reads as a trophy in a dark room
    save_json(m, 'models/block/dragon_egg.json')
    return st

# ------------------------------------------------------------------ preview
def preview(egg):
    frames = []
    for f in range(24):
        g = Image.new('RGBA', (110, 110), (60, 52, 84, 255))
        g.alpha_composite(egg.crop((0, f * 16, 16, f * 16 + 16)).resize((96, 96), Image.NEAREST), (7, 7))
        frames.append(g.convert('RGB'))
    frames[0].save(PREVIEWS + '/anim_huevo.gif', save_all=True, append_images=frames[1:], duration=150, loop=0)

if __name__ == '__main__':
    egg = dragon_egg()      # hearts()/hunger_armor() are left out: icons.py already styles the HUD
    os.makedirs(PREVIEWS, exist_ok=True)
    preview(egg)
    print('ok')
