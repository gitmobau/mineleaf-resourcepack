# Aurora "Grimorio": rarity auras for tools, enchanting table / anvil / grindstone menus and sprites,
# the enchanting table book and magic particles. (Enchanted book items are left to the user's own pack.)
# Runs after gear.py: it rewrites the tool item definitions that gear.py wrote.
import os, sys, math, json, random
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # build.py runs scripts with -I
import gear, magic
from gear import mix, C, WHITE, OUT

REF = gear.REF                     # .../assets/minecraft/
PACK = gear.PACK
PREVIEWS = gear.PREVIEWS
save_tex, save_json = gear.save_tex, gear.save_json
VIVID = gear.VIVID

def ref(rel):
    return Image.open(REF + 'textures/' + rel).convert('RGBA')

def cyc(t, pal=VIVID):
    return gear.cyc(t, pal)

GOLD = (255, 222, 120)

# ------------------------------------------------------------------ rarity auras
RARE = [(255, 230, 140), (255, 205, 160), (255, 245, 190), (255, 220, 120), (255, 252, 225)]          # gold
LEGEND = [(255, 120, 220), (130, 220, 255), (255, 240, 140), (170, 140, 255), (120, 255, 200), (255, 255, 255)]

def aura_tier(base, pal, N=16, reach=3.6, sparks=3, speed=1, alpha=(215, 135, 55)):
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
            if not sil[x][y]:
                d = min(math.hypot(x - a, y - b) for a, b in pts)
                if d <= reach:
                    dist[(x, y)] = d
    ring = sorted([k for k, d in dist.items() if 1.6 < d <= reach], key=lambda k: math.atan2(k[1] - cy, k[0] - cx))
    strip = Image.new('RGBA', (W, W * N))
    for f in range(N):
        ph = f / N
        pulse = 0.72 + 0.28 * math.sin(ph * 2 * math.pi)
        for (x, y), d in dist.items():
            ang = math.atan2(y - cy, x - cx) / (2 * math.pi)
            col = cyc(ang + ph * speed, pal)
            if d <= 1.5:   a = alpha[0]; col = mix(col, WHITE, 0.35)
            elif d <= 2.6: a = alpha[1]
            else:          a = alpha[2]
            strip.putpixel((x, f * W + y), C(col, a * pulse))
        for k in range(sparks):
            if ring:
                x, y = ring[int((ph * speed + k / sparks) * len(ring)) % len(ring)]
                strip.putpixel((x, f * W + y), C(WHITE, 255))
    return strip, {"animation": {"frametime": 2}}

def legendary_pred(tool):
    main = ([{"enchantments": ["minecraft:sharpness", "minecraft:smite", "minecraft:bane_of_arthropods"], "levels": 5}]
            if tool in ('sword', 'spear') else [{"enchantments": "minecraft:efficiency", "levels": 5}])
    return [{"enchantments": "minecraft:mending"}, {"enchantments": "minecraft:unbreaking", "levels": {"min": 3}}] + main

def rarity():
    out = {}
    for mat in ('diamond', 'netherite'):
        for t in gear.TOOLS:
            n = '%s_%s' % (mat, t)
            base, _ = gear.recolor_tool(n, mat)
            tiers = {'rare': aura_tier(base, RARE, sparks=4, alpha=(240, 170, 75)),
                     'legend': aura_tier(base, LEGEND, reach=4.4, sparks=6, speed=2, alpha=(235, 165, 80))}
            d = json.load(open(PACK + 'items/%s.json' % n))
            cond = d['model']                      # gear.py: has_component enchantments -> normal aura
            vm = cond['on_false']
            normal = cond['on_true']
            def with_aura(kind):
                aid = 'minecraft:item/aurora/aura_%s_%s' % (kind, n)
                s = json.dumps(normal).replace('"minecraft:item/aurora/aura_%s"' % n, '"%s"' % aid)
                return json.loads(s)
            for kind, (st, meta) in tiers.items():
                save_tex(st, 'item/aurora/aura_%s_%s.png' % (kind, n), meta)
                m = gear.aura_model(n)
                tex = 'minecraft:item/aurora/aura_%s_%s' % (kind, n)
                m['textures'] = {"aura": tex, "particle": tex}
                save_json(m, 'models/item/aurora/aura_%s_%s.json' % (kind, n))
            comp = lambda value, on_true, on_false: {"type": "minecraft:condition", "property": "minecraft:component",
                                                    "predicate": "minecraft:enchantments", "value": value,
                                                    "on_true": on_true, "on_false": on_false}
            cond['on_true'] = comp(legendary_pred(t), with_aura('legend'),
                                   comp([{"enchantments": "minecraft:mending"}], with_aura('rare'), normal))
            save_json(d, 'items/%s.json' % n)
            out[n] = (base, tiers)
    return out

# ------------------------------------------------------------------ menus + sprites
def menus():
    res = {}
    S = magic
    for name, excl, cats, seed in (
            ('enchanting_table', [S.TITLE, S.inv_label(166), (59, 13, 169, 72), (10, 12, 58, 44)], [], 21),
            ('anvil', [(58, 18, 170, 36), S.inv_label(166), (58, 66, 170, 80), (0, 0, 60, 46)], [], 23),
            ('grindstone', [S.TITLE, S.inv_label(166), (40, 2, 104, 76)], [(S.CAT_PEEK, 138, 4)], 25)):
        img, sl = S.build_container(name, 176, 166, cats=cats, excl=excl, seed=seed)
        if name == 'anvil':   # keep the hammer readable: aurora hammer over the panel
            v = ref('gui/container/anvil.png')
            for y in range(6, 42):
                for x in range(10, 50):
                    p = v.getpixel((x, y))
                    if p[3] and not magic.is_rgb(p, 198):
                        l = sum(p[:3]) / 765
                        c = OUT if l < 0.25 else mix(cyc(x / 50 + y / 60), WHITE, max(0, l - 0.4) * 1.4)
                        img.putpixel((x, y), C(c))
        S.save(img, 'gui/container/%s.png' % name)
        res[name] = img
    return res

def button(w, h, kind, N=1, ph0=0.0):
    """pearl glass buttons. kind: normal | hi (animated, dark enough for yellow text) | off"""
    st = Image.new('RGBA', (w, h * N))
    for f in range(N):
        ph = f / max(1, N)
        for y in range(h):
            for x in range(w):
                e = min(x, y, w - 1 - x, h - 1 - y)
                t = x / w * 0.8 + ph
                if kind == 'normal':
                    c = OUT if e == 0 else (mix(cyc(t), WHITE, 0.3) if e == 1 else mix((238, 232, 253), (214, 202, 246), y / h))
                    if e > 1 and (x + y) % 23 in (0, 1): c = mix(c, WHITE, 0.6)
                elif kind == 'hi':
                    c = OUT if e == 0 else (mix(cyc(t), WHITE, 0.15) if e <= 1 else mix((92, 62, 160), (126, 84, 196), y / h))
                    if e > 1:
                        s = (x / w - y / h * 0.15)
                        dd = abs(s - (ph * 1.4 - 0.2))
                        if dd < 0.05: c = mix(c, (190, 160, 255), 1 - dd / 0.05)
                else:
                    c = OUT if e == 0 else mix((84, 72, 118), (70, 60, 100), y / h)
                st.putpixel((x, f * h + y), C(c))
    return st

def level_icon(n, enabled, N=12):
    """16x16 gem + numeral."""
    digits = {1: [".#.", "##.", ".#.", ".#.", "###"], 2: ["##.", "..#", ".#.", "#..", "###"], 3: ["##.", "..#", ".#.", "..#", "##."]}
    st = Image.new('RGBA', (16, 16 * N))
    for f in range(N):
        ph = f / N
        im = Image.new('RGBA', (16, 16))
        cx, cy, r = 6, 8, 4.6
        for y in range(16):
            for x in range(11):
                d = math.hypot(x - cx, y - cy)
                if d <= r + 0.5:
                    if d > r - 0.6:
                        c = OUT
                    elif enabled:
                        c = mix(cyc(ph + (x + y) / 20), WHITE, 0.45 - (y - cy) / 20)
                        if (x - cx + 1.5) ** 2 + (y - cy + 1.5) ** 2 < 2: c = WHITE
                    else:
                        c = (110, 100, 140)
                    im.putpixel((x, y), C(c))
        for j, row in enumerate(digits[n]):
            for i, ch in enumerate(row):
                if ch == '#':
                    im.putpixel((11 + i, 6 + j), C((255, 236, 140) if enabled else (120, 110, 140)))
        for j, row in enumerate(digits[n]):          # drop shadow under the numeral
            for i, ch in enumerate(row):
                if ch == '#' and im.getpixel((12 + i, 7 + j))[3] == 0:
                    im.putpixel((12 + i, 7 + j), C(OUT))
        if enabled and f % N in (0, 1):
            im.putpixel((9, 4), C(WHITE))
        st.paste(im, (0, f * 16))
    return st

def sprites():
    E = 'gui/sprites/container/enchanting_table/'
    save_tex(button(108, 19, 'normal'), E + 'enchantment_slot.png')
    save_tex(button(108, 19, 'off'), E + 'enchantment_slot_disabled.png')
    N = 16
    save_tex(button(108, 19, 'hi', N), E + 'enchantment_slot_highlighted.png', magic.anim_meta(N, 2, None, 108, 19))
    for n in (1, 2, 3):
        save_tex(level_icon(n, True), E + 'level_%d.png' % n, magic.anim_meta(12, 3))
        save_tex(level_icon(n, False, 1), E + 'level_%d_disabled.png' % n)
    A = 'gui/sprites/container/anvil/'
    tf = Image.new('RGBA', (110, 16))
    for y in range(16):
        for x in range(110):
            e = min(x, y, 109 - x, 15 - y)
            c = OUT if e == 0 else (mix(cyc(x / 110), WHITE, 0.2) if e == 1 else mix((96, 70, 160), (78, 56, 136), y / 16))
            tf.putpixel((x, y), C(c))
    save_tex(tf, A + 'text_field.png')
    tfd = Image.new('RGBA', (110, 16))
    for y in range(16):
        for x in range(110):
            e = min(x, y, 109 - x, 15 - y)
            tfd.putpixel((x, y), C(OUT if e == 0 else (70, 60, 100)))
    save_tex(tfd, A + 'text_field_disabled.png')
    # error cross (anvil + grindstone): pastel arrow with a soft red cross
    for d in ('anvil', 'grindstone'):
        v = ref('gui/sprites/container/%s/error.png' % d)
        o = Image.new('RGBA', v.size)
        for y in range(v.height):
            for x in range(v.width):
                p = v.getpixel((x, y))
                if p[3] == 0: continue
                hh, s, vv = gear.hsv(p)
                if s > 0.4:   c = mix((255, 110, 150), WHITE, max(0, vv - 0.7))
                else:         c = mix((150, 130, 210), WHITE, max(0, vv - 0.5))
                o.putpixel((x, y), C(c, p[3]))
        save_tex(o, 'gui/sprites/container/%s/error.png' % d)

# ------------------------------------------------------------------ enchanting table book + particles
def table_book():
    v = ref('entity/enchantment/enchanting_table_book.png')
    o = Image.new('RGBA', v.size)
    for y in range(v.height):
        for x in range(v.width):
            p = v.getpixel((x, y))
            if p[3] == 0: continue
            hh, s, vv = gear.hsv(p)
            if vv < 0.08:                                # unused black area of the sheet
                o.putpixel((x, y), p); continue
            if s < 0.35 and vv > 0.6:                   # pages
                c = mix((236, 230, 252), WHITE, (vv - 0.6) * 1.5)
            elif 40 <= hh <= 62 and s > 0.6 and vv > 0.7:   # gold corners
                c = mix(GOLD, WHITE, 0.3)
            else:                                        # leather cover
                c = mix(mix((70, 44, 130), cyc(x / 64 + y / 32 * 0.3), 0.55), WHITE, max(0, vv - 0.45) * 0.8)
            o.putpixel((x, y), C(c, p[3]))
    save_tex(o, 'entity/enchantment/enchanting_table_book.png')
    return o

def particles():
    out = []
    letters = 'abcdefghijklmnopqrstuvwxyz'
    for i, ch in enumerate(letters):
        v = ref('particle/sga_%s.png' % ch)
        o = Image.new('RGBA', v.size)
        col = cyc(i / len(letters))
        for y in range(v.height):
            for x in range(v.width):
                p = v.getpixel((x, y))
                if p[3]: o.putpixel((x, y), C(mix(col, WHITE, 0.25 * (p[0] / 255)), p[3]))
        save_tex(o, 'particle/sga_%s.png' % ch)
        out.append(o)
    # hit particles: the game tints them, so keep them light with a pastel core
    for n, core in (('enchanted_hit', (200, 160, 255)), ('critical_hit', (255, 225, 170))):
        v = ref('particle/%s.png' % n)
        o = Image.new('RGBA', v.size)
        for y in range(v.height):
            for x in range(v.width):
                p = v.getpixel((x, y))
                if p[3]:
                    l = p[0] / 255
                    o.putpixel((x, y), C(mix(core, WHITE, l * 0.7), p[3]))
        save_tex(o, 'particle/%s.png' % n)
        out.append(o)
    return out

# ------------------------------------------------------------------ preview
def preview(rar, mn, parts, tbook):
    sheet = Image.new('RGBA', (1240, 760), (60, 52, 84, 255))
    x0, y = 10, 10
    for i, n in enumerate(['diamond_sword', 'diamond_pickaxe', 'netherite_sword', 'netherite_pickaxe']):
        base, tiers = rar[n]
        strip = Image.open(PACK + 'textures/item/%s.png' % n).convert('RGBA').crop((0, 0, 16, 16))
        normal = Image.open(PACK + 'textures/item/aurora/aura_%s.png' % n).convert('RGBA').crop((0, 0, 24, 24))
        for k, au in enumerate([normal, tiers['rare'][0].crop((0, 0, 24, 24)), tiers['legend'][0].crop((0, 0, 24, 24))]):
            fr = au.copy(); fr.alpha_composite(strip, (4, 4))
            sheet.alpha_composite(fr.resize((72, 72), Image.NEAREST), (x0 + k * 84 + i * 280, y))
    y += 100
    for i, n in enumerate(['enchanting_table', 'anvil', 'grindstone']):
        sheet.alpha_composite(mn[n].crop((0, 0, 176, 166)).resize((352, 332), Image.NEAREST), (x0 + i * 400, y))
    E = PACK + 'textures/gui/sprites/container/enchanting_table/'
    for k, nm in enumerate(['enchantment_slot', 'enchantment_slot_highlighted', 'enchantment_slot_disabled']):
        b = Image.open(E + nm + '.png').convert('RGBA').crop((0, 0, 108, 19))
        sheet.alpha_composite(b.resize((216, 38), Image.NEAREST), (x0 + 60 * 2, y + (14 + 19 * k) * 2))
        lv = Image.open(E + 'level_%d%s.png' % (k + 1, '' if k < 2 else '_disabled')).convert('RGBA').crop((0, 0, 16, 16))
        sheet.alpha_composite(lv.resize((32, 32), Image.NEAREST), (x0 + 61 * 2, y + (15 + 19 * k) * 2))
    tf = Image.open(PACK + 'textures/gui/sprites/container/anvil/text_field.png').convert('RGBA')
    sheet.alpha_composite(tf.resize((220, 32), Image.NEAREST), (x0 + 400 + 59 * 2, y + 20 * 2))
    y += 350
    for i, p in enumerate(parts):
        sheet.alpha_composite(p.resize((32, 32), Image.NEAREST), (x0 + i * 40, y))
    sheet.alpha_composite(tbook.resize((256, 128), Image.NEAREST), (x0, y + 50))
    sheet.save(PREVIEWS + '/preview_grimorio.png')
    frames = []
    for f in range(16):
        g = Image.new('RGBA', (3 * 84 * 2 + 20, 90), (60, 52, 84, 255))
        for i, n in enumerate(['diamond_sword', 'netherite_pickaxe']):
            base, tiers = rar[n]
            tool = Image.open(PACK + 'textures/item/%s.png' % n).convert('RGBA').crop((0, f * 16, 16, f * 16 + 16))
            normal = Image.open(PACK + 'textures/item/aurora/aura_%s.png' % n).convert('RGBA')
            for k, au in enumerate([normal, tiers['rare'][0], tiers['legend'][0]]):
                fr = au.crop((0, f * 24, 24, f * 24 + 24)); fr.alpha_composite(tool, (4, 4))
                g.alpha_composite(fr.resize((72, 72), Image.NEAREST), (10 + (i * 3 + k) * 84, 8))
        frames.append(g.convert('RGB'))
    frames[0].save(PREVIEWS + '/anim_grimorio.gif', save_all=True, append_images=frames[1:], duration=100, loop=0)

if __name__ == '__main__':
    rar = rarity()
    mn = menus(); sprites()
    tb = table_book(); pa = particles()
    os.makedirs(PREVIEWS, exist_ok=True)
    preview(rar, mn, pa, tb)
    print('ok')
