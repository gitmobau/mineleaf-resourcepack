# Aurora polish: iron ("moonstone") and gold ("sunstone") gear, totem, elytra.
# Runs after menus.py.
import os, sys, colorsys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
from gear import (finish_tool, animate, save_tex, ref, mix, C, cyc, VIVID, WHITE, TOOLS, ARMOR, REF, PACK)

RAMPS = {   # dark -> light, 5 stops
    'iron':   [(40, 34, 78), (98, 92, 150), (164, 158, 218), (218, 214, 250), (255, 255, 255)],
    'golden': [(86, 40, 70), (186, 96, 118), (246, 160, 148), (255, 210, 168), (255, 246, 222)],
}
SHIMMER = {'iron': 0.22, 'golden': 0.14}
STICK = {p[:3] for p in ref('item/stick.png').getdata() if p[3]}

def ramp(stops, f):
    f = max(0.0, min(1.0, f)) * (len(stops) - 1)
    i = min(int(f), len(stops) - 2)
    return mix(stops[i], stops[i + 1], f - i)

def lum(p):
    return 0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]

def recolor(rel, mat, shimmer=True):
    """luminance-rank recolor: robust for any vanilla iron/gold texture layout"""
    im = ref(rel); w, h = im.size
    levels = sorted({round(lum(p)) for p in im.getdata() if p[3] and p[:3] not in STICK})
    rank = {l: i / max(1, len(levels) - 1) for i, l in enumerate(levels)}
    out = Image.new('RGBA', im.size); head = [[False] * h for _ in range(w)]
    for y in range(h):
        for x in range(w):
            p = im.getpixel((x, y))
            if not p[3]:
                continue
            if p[:3] in STICK:          # wooden handle, same look as the diamond tools
                v = colorsys.rgb_to_hsv(*[q / 255 for q in p[:3]])[2]
                c = mix((40, 26, 44), (196, 140, 170), min(1, max(0, (v - 0.12) / 0.45)))
            else:
                f = rank[round(lum(p))]
                c = ramp(RAMPS[mat], f)
                if shimmer and 0.25 < f < 0.95:
                    c = mix(c, cyc((x - y) / (w + h) + 0.3, VIVID), SHIMMER[mat])
                head[x][y] = True
            out.putpixel((x, y), C(c, p[3]))
    return out, head

def gear_icons():
    out = {}
    for mat in RAMPS:
        for t in TOOLS:
            n = '%s_%s' % (mat, t)
            if os.path.exists(REF + 'textures/item/%s.png' % n):
                out[n] = finish_tool(n, lambda name, mat=mat: recolor('item/%s.png' % name, mat))
        for a in ARMOR + ['horse_armor', 'nautilus_armor']:
            n = '%s_%s' % (mat, a)
            if os.path.exists(REF + 'textures/item/%s.png' % n):
                base, head = recolor('item/%s.png' % n, mat)
                strip, meta = animate(base, head, seed=len(n))
                save_tex(strip, 'item/%s.png' % n, meta); out[n] = (strip, None, base.size)
    return out

def worn():
    for layer in ('humanoid', 'humanoid_leggings', 'humanoid_baby', 'horse_body', 'nautilus_body'):
        for mat, fname in (('iron', 'iron'), ('golden', 'gold')):
            rel = 'entity/equipment/%s/%s.png' % (layer, fname)
            if os.path.exists(REF + 'textures/' + rel):
                save_tex(recolor(rel, mat)[0], rel)

def misc():
    """totem and elytra: keep their shapes, pastel aurora colours"""
    for rel in ('item/totem_of_undying.png', 'item/elytra.png', 'item/broken_elytra.png',
                'entity/equipment/wings/elytra.png'):
        if not os.path.exists(REF + 'textures/' + rel):
            continue
        im = ref(rel); o = Image.new('RGBA', im.size); w, h = im.size
        for y in range(h):
            for x in range(w):
                p = im.getpixel((x, y))
                if not p[3]:
                    continue
                l = lum(p) / 255
                c = mix(cyc(x / w * 0.7 + y / h * 0.3, VIVID), (46, 30, 92), max(0, 0.55 - l) * 1.4)
                if l > 0.75:
                    c = mix(c, WHITE, (l - 0.75) * 2)
                o.putpixel((x, y), C(c, p[3]))
        save_tex(o, rel)

if __name__ == '__main__':
    icons = gear_icons(); worn(); misc()
    from gear import PREVIEWS
    names = [n for n in icons if not n.endswith('in_hand')]
    sheet = Image.new('RGBA', (20 + 72 * 12, 20 + 80 * 2 + 140), (60, 52, 84, 255))
    for i, n in enumerate(sorted(names)):
        strip = icons[n][0]
        sheet.alpha_composite(strip.crop((0, 0, 16, 16)).resize((64, 64), Image.NEAREST),
                              (10 + (i % 12) * 72, 10 + (i // 12) * 80))
    x = 10
    for rel in ('item/totem_of_undying.png', 'item/elytra.png'):
        sheet.alpha_composite(Image.open(PACK + 'textures/' + rel).resize((64, 64), Image.NEAREST), (x, 180)); x += 72
    for rel in ('entity/equipment/humanoid/iron.png', 'entity/equipment/humanoid/gold.png', 'entity/equipment/wings/elytra.png'):
        im = Image.open(PACK + 'textures/' + rel); sheet.alpha_composite(im.resize((256, 128), Image.NEAREST), (x, 170)); x += 266
    sheet = sheet.crop((0, 0, max(x, sheet.width), sheet.height))
    os.makedirs(PREVIEWS, exist_ok=True)
    sheet.save(PREVIEWS + '/preview_polish.png')
    print('ok')
