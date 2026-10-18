# Aurora dragon egg trophy: a night sky with a slow aurora curtain and a few stars, softly glowing.
# (The hardcore hearts / hunger / armour icons that used to live here are done by icons.py.)
import os, sys, math, json
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # build.py runs scripts with -I
import gear
from gear import mix, C, WHITE

REF = gear.REF
PACK = gear.PACK
PREVIEWS = gear.PREVIEWS
save_tex, save_json = gear.save_tex, gear.save_json

N, FT = 32, 4                      # 32 frames x 4 ticks (interpolated) = 6.4 s per loop
SKY_TOP, SKY_BOTTOM = (54, 34, 104), (14, 9, 34)
# aurora colours from the bottom of the curtain to the top: mint -> cyan -> lavender -> pink
CURTAIN = [(160, 246, 214), (140, 216, 255), (190, 168, 255), (250, 170, 236)]
STARS = [(4, 3, 0.0), (11, 5, 0.35), (2, 13, 0.6), (13, 14, 0.82), (7, 1, 0.18)]     # (x, y, when it twinkles in the loop)
EMISSION = 8                       # a gentle glow: the egg reads as a trophy at night without looking like a lamp

def ramp(t, pal):
    t = max(0.0, min(1.0, t)) * (len(pal) - 1)
    i = min(int(t), len(pal) - 2)
    return mix(pal[i], pal[i + 1], t - i)

def egg_px(x, y, ph):
    # night sky: vertical gradient with a faint, slowly drifting nebula
    c = mix(SKY_TOP, SKY_BOTTOM, y / 15)
    neb = 0.5 + 0.5 * math.sin(0.55 * x + 0.35 * y + 2 * math.pi * ph) * math.sin(0.3 * x - 0.5 * y + 1.3)
    c = mix(c, (92, 60, 150), 0.18 * neb)
    # aurora curtain: a soft band across the middle of the egg, brighter at its lower edge, with vertical folds
    # that drift sideways
    mid = 9.5 + 1.2 * math.sin(2 * math.pi * (x / 16 + ph))
    u = y - mid                                            # < 0 above the lower edge, > 0 below it
    band = math.exp(-(u / 5.0) ** 2) if u < 0 else math.exp(-(u / 1.4) ** 2)
    folds = 0.5 + 0.5 * math.sin(2 * math.pi * (x / 7 - ph) + 0.9 * math.sin(2 * math.pi * (y / 16 + ph)))
    a = band * (0.3 + 0.7 * folds ** 1.5)
    col = ramp((mid + 0.5 - y) / 7.5, CURTAIN)
    return mix(c, col, 0.74 * a)

def dragon_egg():
    st = Image.new('RGBA', (16, 16 * N))
    for f in range(N):
        ph = f / N
        for y in range(16):
            for x in range(16):
                c = egg_px(x, y, ph)
                for sx, sy, t0 in STARS:                       # each star twinkles once per loop, softly
                    if (sx, sy) == (x, y):
                        d = min(abs(ph - t0), 1 - abs(ph - t0))
                        c = mix(c, WHITE, max(0.18, 1 - d / 0.08) * 0.85)
                st.putpixel((x, f * 16 + y), C(c))
    save_tex(st, 'block/dragon_egg.png', {"animation": {"frametime": FT, "interpolate": True}})
    m = json.load(open(REF + 'models/block/dragon_egg.json'))
    for el in m['elements']:
        el['light_emission'] = EMISSION
    save_json(m, 'models/block/dragon_egg.json')
    return st

# ------------------------------------------------------------------ preview
def preview(egg):
    frames = []
    for f in range(N):
        g = Image.new('RGBA', (110, 110), (60, 52, 84, 255))
        g.alpha_composite(egg.crop((0, f * 16, 16, f * 16 + 16)).resize((96, 96), Image.NEAREST), (7, 7))
        frames.append(g.convert('RGB'))
    frames[0].save(PREVIEWS + '/anim_huevo.gif', save_all=True, append_images=frames[1:], duration=FT * 50, loop=0)

if __name__ == '__main__':
    egg = dragon_egg()
    os.makedirs(PREVIEWS, exist_ok=True)
    preview(egg)
    print('ok')
