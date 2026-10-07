# Aurora extra GUI: recipe book, creative inventory, HUD icons (hearts, food, armor, air).
# Runs after magic.py; reuses its palette and helpers.
import os, sys, math, json, random, colorsys, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
from magic import cyc, mix, C, OUT, WHITE, PEARL, sparkle, ref, save, REF, TX

SLOT_EDGE = (150, 128, 214)
SLOT_FILL = (230, 221, 251)
SHADOW = (110, 88, 170)

def copy_meta(rel):
    if os.path.exists(REF + rel + '.mcmeta'):
        shutil.copy(REF + rel + '.mcmeta', TX + rel + '.mcmeta')

def edge_dist(im):
    """distance (4-neighbour steps) from transparency / image border, capped at 4"""
    w, h = im.size
    d = [[9] * h for _ in range(w)]
    q = []
    for y in range(h):
        for x in range(w):
            if im.getpixel((x, y))[3] == 0:
                d[x][y] = 0
            elif x in (0, w - 1) or y in (0, h - 1):
                d[x][y] = 1; q.append((x, y))
    for y in range(h):
        for x in range(w):
            if d[x][y] == 9 and any(0 <= x + dx < w and 0 <= y + dy < h and d[x + dx][y + dy] == 0
                                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                d[x][y] = 1; q.append((x, y))
    for k in range(2, 5):
        nq = []
        for (x, y) in q:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < w and 0 <= yy < h and d[xx][yy] == 9:
                    d[xx][yy] = k; nq.append((xx, yy))
        q = nq
    return d

def pastel(p, t, tint=0.18, min_hue=None):
    """colored pixel -> pastel aurora version that keeps its hue (icons, hearts, food...)"""
    h, s, v = colorsys.rgb_to_hsv(*[q / 255 for q in p[:3]])
    if min_hue is not None and s >= 0.08:
        h = max(h, min_hue)
    if v < 0.13:
        return OUT
    if s < 0.08:                                   # greys -> crystal lavender
        if v < 0.3:  return (84, 62, 150)
        if v < 0.6:  return mix(cyc(t), (120, 100, 200), 0.4)
        if v < 0.85: return mix(cyc(t), (175, 155, 238), 0.15)
        return mix(cyc(t), WHITE, 0.6)
    r, g, b = colorsys.hsv_to_rgb(h, min(s, 0.8) * 0.78, 0.42 + 0.58 * v)
    return mix((r * 255, g * 255, b * 255), cyc(t), tint)

def sky(img, pts, seed=1):
    """aurora night sky over the given pixels (same look as the inventory player window)"""
    if not pts:
        return
    bx0 = min(p[0] for p in pts); bx1 = max(p[0] for p in pts)
    by0 = min(p[1] for p in pts); by1 = max(p[1] for p in pts)
    rnd = random.Random(seed)
    for (x, y) in pts:
        u = (x - bx0) / max(1, bx1 - bx0); vv = (y - by0) / max(1, by1 - by0)
        c = mix((22, 14, 58), (92, 58, 150), vv)
        for k, (amp, off, th) in enumerate(((5, 0.25, 4.5), (4, 0.42, 3.5))):
            cy = by0 + (by1 - by0) * off + amp * math.sin(u * 6.3 + k * 2)
            d = abs(y - cy)
            if d < th:
                c = mix(c, cyc(u * 0.6 + k * 0.3), (1 - d / th) * 0.55)
        img.putpixel((x, y), C(c))
    pset = set(pts)
    for _ in range(len(pts) // 90):
        x, y = rnd.choice(pts)
        if (x, y) in pset:
            img.putpixel((x, y), C(mix(WHITE, cyc(rnd.random()), 0.3)))

def gui_recolor(rel, t0=0.0, span=0.8, sky_value=None, seed=1, glass=True):
    """vanilla grey GUI art -> Aurora frame: aurora rim, pearl panel, lavender slots"""
    v = ref(rel); w, h = v.size
    bb = v.getbbox() or (0, 0, w, h)
    bw, bh = max(1, bb[2] - bb[0]), max(1, bb[3] - bb[1])
    d = edge_dist(v)
    out = Image.new('RGBA', v.size)
    skypts = []
    for y in range(h):
        for x in range(w):
            p = v.getpixel((x, y))
            if p[3] == 0:
                continue
            t = t0 + span * ((x - bb[0]) / bw * 0.7 + (y - bb[1]) / bh * 0.3)
            grey = p[0] == p[1] == p[2]
            g = p[0]
            if grey and sky_value is not None and g == sky_value and d[x][y] >= 3:
                skypts.append((x, y)); continue
            if not grey:
                c = pastel(p, t)
            elif g <= 31:
                c = OUT
            elif d[x][y] <= 2 and g == 255:
                c = cyc(t)                                  # aurora rim (vanilla white bevel)
            elif d[x][y] <= 3 and g == 85:
                c = mix(cyc(t + 0.1), OUT, 0.35)            # rim shadow side
            elif g == 255:
                c = WHITE
            elif g == 198:
                c = mix(PEARL, cyc(t + 0.1), 0.08)
                if glass and (x + y) % 29 in (0, 1, 2):
                    c = mix(c, WHITE, 0.8)
            elif g == 139:
                c = SLOT_FILL
            elif g == 55:
                c = SLOT_EDGE
            elif g == 85:
                c = SHADOW
            else:
                c = pastel(p, t)
            out.putpixel((x, y), C(c, p[3]))
    sky(out, skypts, seed)
    return out

def recipe_book():
    img = gui_recolor('gui/recipe_book.png', sky_value=55, seed=21)
    # a couple of sparkles on the frame
    for (x, y, t) in ((140, 8, 0.2), (8, 160, 0.6)):
        sparkle(img, x, y, t, big=False)
    save(img, 'gui/recipe_book.png')
    S = 'gui/sprites/recipe_book/'
    names = [f[:-4] for f in os.listdir(REF + S) if f.endswith('.png')]
    for n in sorted(names):
        if n in ('button', 'button_highlighted'):        # cat button lives in magic.py
            continue
        im = gui_recolor(S + n + '.png', t0=0.1 * len(n), span=0.5, glass=False)
        save(im, S + n + '.png'); copy_meta(S + n + '.png')

def creative():
    out = {}
    for i, n in enumerate(('tab_items', 'tab_inventory', 'tab_item_search')):
        rel = 'gui/container/creative_inventory/%s.png' % n
        img = gui_recolor(rel, sky_value=0, seed=31 + i)
        save(img, rel); out[n] = img
    S = 'gui/sprites/container/creative_inventory/'
    for f in sorted(os.listdir(REF + S)):
        if not f.endswith('.png'):
            continue
        k = int(f[-5]) if f[-5].isdigit() else 0
        im = gui_recolor(S + f, t0=k / 7, span=0.15, glass=False)
        save(im, S + f); copy_meta(S + f)
    return out

def hud_icons():
    H = 'gui/sprites/hud/'
    rels = [H + 'heart/' + f for f in os.listdir(REF + H + 'heart') if f.endswith('.png')]
    rels += [H + f for f in os.listdir(REF + H) if f.endswith('.png') and
             f.split('.')[0].split('_')[0] in ('food', 'armor', 'air')]
    for rel in sorted(rels):
        v = ref(rel); o = Image.new('RGBA', v.size)
        for y in range(v.height):
            for x in range(v.width):
                p = v.getpixel((x, y))
                if p[3]:
                    o.putpixel((x, y), C(pastel(p, 0.45 + (x + y) / 18 * 0.25, tint=0.06,
                                                   min_hue=0.3 if 'poisoned' in rel else None), p[3]))
        save(o, rel); copy_meta(rel)

if __name__ == '__main__':
    recipe_book(); cr = creative(); hud_icons()
    from magic import PREVIEWS
    rb = Image.open(TX + 'gui/recipe_book.png').crop((0, 0, 150, 168))
    sheet = Image.new('RGBA', (2 * 150 + 2 * 196 + 60, 2 * 168 + 120), (60, 52, 84, 255))
    sheet.alpha_composite(rb.resize((300, 336), Image.NEAREST), (10, 10))
    for i, n in enumerate(('tab_items', 'tab_inventory')):
        sheet.alpha_composite(cr[n].crop((0, 0, 195, 136)).resize((390, 272), Image.NEAREST), (330, 10 + i * 0))
        break
    sheet.alpha_composite(cr['tab_inventory'].crop((0, 0, 195, 136)).resize((390, 272), Image.NEAREST), (330, 290 - 10))
    x = 10
    for rel in ('heart/full', 'heart/half', 'heart/container', 'heart/poisoned_full', 'heart/frozen_full',
                'heart/withered_full', 'heart/absorbing_full', 'food_full', 'food_half', 'armor_full', 'air'):
        im = Image.open(TX + 'gui/sprites/hud/%s.png' % rel)
        sheet.alpha_composite(im.resize((27, 27), Image.NEAREST), (x, 360)); x += 30
    for i, f in enumerate(('tab_top_selected_1', 'tab_top_unselected_2', 'recipe/tab', 'recipe/tab_selected')):
        p = TX + ('gui/sprites/recipe_book/%s.png' % f[7:] if f.startswith('recipe/') else
                  'gui/sprites/container/creative_inventory/%s.png' % f)
        im = Image.open(p); sheet.alpha_composite(im.resize((im.width * 2, im.height * 2), Image.NEAREST), (10 + i * 80, 400))
    os.makedirs(PREVIEWS, exist_ok=True)
    sheet.save(PREVIEWS + '/preview_extra.png')
    print('ok')
