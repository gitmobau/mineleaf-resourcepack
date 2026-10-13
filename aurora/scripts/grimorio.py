# Aurora "Grimorio": one enchanted book per enchantment and level, rarity auras for tools,
# enchanting table / anvil / grindstone menus and sprites, enchanting book, magic particles.
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

# ------------------------------------------------------------------ enchantments
# id: (max level, category, treasure)
ENCH = {
    'protection': (4, 'armor', 0), 'fire_protection': (4, 'armor', 0), 'blast_protection': (4, 'armor', 0),
    'projectile_protection': (4, 'armor', 0), 'thorns': (3, 'armor', 0), 'respiration': (3, 'armor', 0),
    'aqua_affinity': (1, 'armor', 0), 'feather_falling': (4, 'armor', 0), 'depth_strider': (3, 'armor', 0),
    'frost_walker': (2, 'armor', 1), 'soul_speed': (3, 'armor', 1), 'swift_sneak': (3, 'armor', 1),
    'sharpness': (5, 'melee', 0), 'smite': (5, 'melee', 0), 'bane_of_arthropods': (5, 'melee', 0),
    'knockback': (2, 'melee', 0), 'fire_aspect': (2, 'melee', 0), 'looting': (3, 'melee', 0),
    'sweeping_edge': (3, 'melee', 0), 'lunge': (3, 'melee', 0),
    'efficiency': (5, 'tool', 0), 'silk_touch': (1, 'tool', 0), 'fortune': (3, 'tool', 0),
    'unbreaking': (3, 'any', 0), 'mending': (1, 'any', 1),
    'power': (5, 'bow', 0), 'punch': (2, 'bow', 0), 'flame': (1, 'bow', 0), 'infinity': (1, 'bow', 0),
    'multishot': (1, 'bow', 0), 'piercing': (4, 'bow', 0), 'quick_charge': (3, 'bow', 0),
    'impaling': (5, 'sea', 0), 'loyalty': (3, 'sea', 0), 'channeling': (1, 'sea', 0), 'riptide': (3, 'sea', 0),
    'luck_of_the_sea': (3, 'sea', 0), 'lure': (3, 'sea', 0),
    'density': (5, 'mace', 0), 'breach': (4, 'mace', 0), 'wind_burst': (3, 'mace', 1),
    'binding_curse': (1, 'curse', 1), 'vanishing_curse': (1, 'curse', 1),
}
CAT = {   # cover colour
    'armor': (110, 175, 255), 'melee': (255, 125, 160), 'tool': (255, 185, 105), 'any': (95, 220, 175),
    'bow': (175, 140, 255), 'sea': (70, 200, 220), 'mace': (160, 105, 225), 'curse': (62, 30, 62),
}
GOLD = (255, 222, 120)

# 7x7 icons. '#' light, '+' accent (second value), 'o' dark outline, '.' cover shows through.
ICONS = {
 'protection': ((".#####.", "#+++++#", "#+++++#", "#+++++#", ".#+++#.", "..#+#..", "...#..."), (190, 220, 255)),
 'fire_protection': ((".#####.", "#++.++#", "#+.o.+#", "#+ooo+#", ".#+o+#.", "..#+#..", "...#..."), (255, 150, 90)),
 'blast_protection': ((".#####.", "#+.+.+#", "#..o..#", "#+ooo+#", ".#.o.#.", "..#+#..", "...#..."), (255, 120, 120)),
 'projectile_protection': ((".#####.", "#+++++#", "#oooo+#", "#+++o+#", ".#++o#.", "..#+#..", "...#..."), (200, 255, 200)),
 'thorns': (("#..#..#", ".#.#.#.", "..###..", "###+###", "..###..", ".#.#.#.", "#..#..#"), (120, 230, 120)),
 'respiration': (("....##.", "...#..#", "...#..#", "##..##.", "#.#....", "##..+..", "...+.+."), (180, 240, 255)),
 'aqua_affinity': (("...#...", "..#+#..", ".#+++#.", ".#+++#.", "#++#++#", ".#+++#.", "..###.."), (120, 210, 255)),
 'feather_falling': (("....###", "...##+#", "..##+#.", ".##+#..", ".#+#...", "#.#....", "#......"), (255, 255, 255)),
 'depth_strider': ((".......", ".##..##", "#++##++", ".......", ".##..##", "#++##++", "......."), (150, 220, 255)),
 'frost_walker': (("...#...", ".#.#.#.", "..###..", "###+###", "..###..", ".#.#.#.", "...#..."), (190, 240, 255)),
 'soul_speed': (("...+...", "..+#+..", "..+#+..", ".+###+.", ".+###+.", "..###..", "......."), (110, 230, 240)),
 'swift_sneak': ((".......", ".#####.", "#.+++.#", "#+o+o+#", "#.+++.#", ".#####.", "......."), (180, 160, 255)),
 'sharpness': (("......#", ".....##", "....##.", "#..##..", ".###...", ".+#....", "+..#..."), (255, 210, 140)),
 'smite': (("..###..", ".#####.", ".#o#o#.", ".#####.", "..#+#..", "..#.#..", "......."), (255, 240, 170)),
 'bane_of_arthropods': (("#.....#", ".#.#.#.", "..###..", "##o#o##", "..###..", ".#.#.#.", "#.....#"), (120, 60, 90)),
 'knockback': (("...#...", "..##...", ".######", "#######", ".######", "..##...", "...#..."), (255, 255, 255)),
 'fire_aspect': (("...#...", "..##...", "..#+#..", ".#++#..", ".#+++#.", "#++o++#", ".#####."), (255, 150, 70)),
 'looting': ((".......", "..###..", ".#+++#.", "#++#++#", "#+++++#", ".#+++#.", "..###.."), (255, 220, 90)),
 'sweeping_edge': ((".###...", "....#..", ".....#.", ".....#.", "....#..", "..##...", "++....."), (200, 240, 255)),
 'lunge': (("....##.", "....###", "...#.#.", "..#....", "+#.....", "#.+....", "+..+..."), (255, 210, 160)),
 'efficiency': (("....##.", "...##..", "..##...", ".######", "...##..", "..##...", ".##...."), (255, 240, 120)),
 'silk_touch': (("...#...", "..#+#..", ".#+++#.", "#+++++#", ".#+++#.", "..#+#..", "...#..."), (230, 220, 255)),
 'fortune': ((".##.##.", "#++#++#", "#+++++#", ".##+##.", "#+++++#", "#++#++#", ".##.##."), (120, 235, 130)),
 'unbreaking': ((".......", "#######", ".#+++#.", "..###..", "..###..", ".#####.", "#######"), (210, 210, 235)),
 'mending': ((".##.##.", "#++#++#", "#+++++#", "#++#++#", ".#+#+#.", "..#+#..", "...#..."), (255, 130, 170)),
 'power': (("....###", ".....##", "+...#.#", "...#...", "..#..+.", ".#.....", "#.+...."), (255, 236, 140)),
 'punch': (("...#...", "..#+#..", ".#+++#.", "#+++++#", ".#+++#.", "..#+#..", "...#..."), (255, 180, 120)),
 'flame': (("......#", "...+.#.", "..+.#..", ".+.#...", "..#+...", ".#+++..", "#..+..."), (255, 150, 70)),
 'infinity': ((".......", ".##.##.", "#..#..#", "#..#..#", "#..#..#", ".##.##.", "......."), (255, 255, 255)),
 'multishot': (("#..#..#", ".#.#.#.", "..###..", "...#...", "...#...", "..+#+..", "...+..."), (255, 220, 170)),
 'piercing': (("...#...", "...#...", "#######", "...#...", "..###..", ".#.#.#.", "...#..."), (255, 255, 255)),
 'quick_charge': ((".#####.", "#..#..#", "#..#..#", "#..##.#", "#.....#", "#.....#", ".#####."), (255, 255, 255)),
 'impaling': (("#..#..#", "#..#..#", "#######", "...#...", "...#...", "...#...", "...#..."), (180, 245, 230)),
 'loyalty': (("..###..", ".#...#.", "#.....#", "#.....#", "#...#.#", ".#..##.", "...###."), (255, 255, 255)),
 'channeling': ((".#####.", "#######", "...#...", "..#....", "..###..", "....#..", "...#..."), (255, 240, 120)),
 'riptide': ((".####..", "#....#.", "#.##..#", "#.#.#.#", "#..#..#", ".#...#.", "..###.."), (150, 230, 255)),
 'luck_of_the_sea': ((".......", "...##..", ".##++#.", "#++++o#", ".##++#.", "...##..", "......."), (130, 220, 255)),
 'lure': (("...#...", "...#...", "...#...", "...#...", ".#.#...", ".#.#...", "..#...."), (255, 255, 255)),
 'density': ((".......", "..###..", ".#####.", "#######", "#######", ".#####.", "......."), (200, 190, 230)),
 'breach': ((".#####.", "#++.++#", "#+..++#", "#++..+#", ".#+.+#.", "..#.#..", "...#..."), (255, 160, 160)),
 'wind_burst': ((".####..", "#....#.", ".....#.", "####...", ".......", "######.", "......#"), (220, 250, 255)),
 'binding_curse': ((".##.##.", "#..#..#", ".##.##.", ".......", ".##.##.", "#..#..#", ".##.##."), (255, 90, 120)),
 'vanishing_curse': ((".#####.", "#######", "#o#o###", "#######", "#######", "#.#.#.#", "......."), (255, 90, 120)),
}

def book(eid, lvl, N=16):
    """16x16 grimoire, front-facing. Returns an animation strip 16 x 16*N."""
    mx, cat, treasure = ENCH[eid]
    rows, acc = ICONS[eid]
    base = CAT[cat]
    curse = cat == 'curse'
    strip = Image.new('RGBA', (16, 16 * N))
    for f in range(N):
        ph = f / N
        im = Image.new('RGBA', (16, 16))
        P = lambda x, y, c, a=255: im.putpixel((x, y), C(c, a))
        # outline 1..14 x 1..14
        for y in range(1, 15):
            for x in range(1, 15):
                edge = x in (1, 14) or y in (1, 14)
                if edge:
                    if (x, y) in ((1, 1), (14, 1), (1, 14), (14, 14)):
                        continue
                    P(x, y, OUT)
        # spine
        for y in range(2, 14):
            for x in (2, 3):
                c = mix(base, (30, 20, 60), 0.45 if x == 2 else 0.3)
                if y in (3, 12): c = GOLD if treasure else mix(base, WHITE, 0.55)
                P(x, y, c)
        # pages (right + bottom)
        for y in range(2, 14):
            P(13, y, (236, 230, 250) if y % 2 else (214, 206, 240))
        for x in range(3, 14):
            P(x, 13, (236, 230, 250) if x % 2 else (214, 206, 240))
        # cover 4..12 x 2..12
        for y in range(2, 13):
            for x in range(4, 13):
                g = ((x - 4) + (y - 2)) / 18
                c = mix(mix(base, WHITE, 0.32), mix(base, (40, 26, 80), 0.25), g)
                if curse:
                    c = mix((40, 18, 44), (90, 30, 70), g * (0.6 + 0.4 * math.sin(ph * 2 * math.pi)))
                # diagonal shine sweep
                s = ((x - 4) - (y - 2) + 10) / 20
                d = abs(s - (ph * 1.6 - 0.3))
                if d < 0.09 and not curse:
                    c = mix(c, WHITE, 0.55 * (1 - d / 0.09))
                P(x, y, c)
        if treasure and not curse:   # gold frame on the cover
            for x in range(4, 13):
                for y in (2, 12):
                    P(x, y, mix(GOLD, WHITE, 0.4 * (0.5 + 0.5 * math.sin((x / 9 + ph) * 2 * math.pi))))
            for y in range(2, 13):
                for x in (4, 12):
                    P(x, y, mix(GOLD, WHITE, 0.4 * (0.5 + 0.5 * math.sin((y / 11 + ph) * 2 * math.pi))))
        # icon 7x7 at (5,3)
        light = (255, 252, 255) if not curse else (230, 200, 220)
        dark = (40, 26, 80) if not curse else (20, 8, 20)
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch == '#': P(5 + i, 3 + j, light)
                elif ch == '+': P(5 + i, 3 + j, acc)
                elif ch == 'o': P(5 + i, 3 + j, dark)
        # level pips on row 11 (only for enchantments with more than one level)
        if mx > 1:
            for i in range(lvl):
                x = 8 - (lvl - 1) + 2 * i
                P(x, 11, mix(GOLD, WHITE, 0.3) if not curse else (255, 120, 150))
        # twinkles
        if treasure or lvl == mx and mx > 1:
            for k in range(2):
                tx, ty = [(12, 2), (4, 12), (12, 12), (4, 2)][(f // 4 + k * 2) % 4]
                if (f + k * 8) % 16 < 3:
                    P(tx, ty, WHITE)
        strip.paste(im, (0, f * 16))
    return strip, {"animation": {"frametime": 2}}

def books():
    """item/grimorio/<id>_<lvl> textures + models, and the enchanted_book item definition."""
    sheet = {}
    for eid, (mx, cat, tr) in ENCH.items():
        for l in range(1, mx + 1):
            st, meta = book(eid, l)
            name = '%s_%d' % (eid, l)
            save_tex(st, 'item/grimorio/%s.png' % name, meta)
            save_json({"parent": "minecraft:item/generated",
                       "textures": {"layer0": "minecraft:item/grimorio/" + name}},
                      'models/item/grimorio/%s.json' % name)
            sheet[name] = st
    def has(eid, lvl=None):
        v = {"enchantments": "minecraft:" + eid}
        if lvl is not None: v["levels"] = lvl
        return {"type": "minecraft:condition", "property": "minecraft:component",
                "predicate": "minecraft:stored_enchantments", "value": [v]}
    def per_level(eid):
        mx = ENCH[eid][0]
        node = {"type": "minecraft:model", "model": "minecraft:item/grimorio/%s_%d" % (eid, mx)}  # above max: show max
        for l in range(mx, 0, -1):
            if mx == 1:
                break
            c = has(eid, l); c["on_true"] = {"type": "minecraft:model", "model": "minecraft:item/grimorio/%s_%d" % (eid, l)}
            c["on_false"] = node; node = c
        return node
    # priority: curses, treasure, then the rest in tooltip order (first match wins on multi-enchant books)
    order = [e for e in ENCH if ENCH[e][1] == 'curse'] + [e for e in ENCH if ENCH[e][2] and ENCH[e][1] != 'curse'] + \
            [e for e in ENCH if not ENCH[e][2]]
    node = json.load(open(REF + 'items/enchanted_book.json'))['model']   # fallback: vanilla book
    for eid in reversed(order):
        c = has(eid); c["on_true"] = per_level(eid); c["on_false"] = node; node = c
    van = json.load(open(REF + 'items/enchanted_book.json'))
    van['model'] = node
    with open(PACK + 'items/enchanted_book.json', 'w') as f:   # 43 nested conditions: compact, not indented
        json.dump(van, f, separators=(',', ':'))
    return sheet

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
            ('enchanting_table', [S.TITLE, S.inv_label(166), (59, 13, 169, 72)], [(S.CAT_SIT, 6, 18)], 21),
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
def preview(bk, rar, mn, parts, tbook):
    order = list(ENCH)
    cols = 15
    sheet = Image.new('RGBA', (1240, 1120), (60, 52, 84, 255))
    x0, y0 = 10, 10
    for i, eid in enumerate(order):
        mx = ENCH[eid][0]
        st = bk['%s_%d' % (eid, mx)]
        fr = st.crop((0, 0, 16, 16)).resize((64, 64), Image.NEAREST)
        sheet.alpha_composite(fr, (x0 + (i % cols) * 80, y0 + (i // cols) * 80))
    y = y0 + 3 * 80 + 10
    for i, l in enumerate(range(1, 6)):
        fr = bk['sharpness_%d' % l].crop((0, 0, 16, 16)).resize((64, 64), Image.NEAREST)
        sheet.alpha_composite(fr, (x0 + i * 80, y))
    for i, n in enumerate(['diamond_sword', 'diamond_pickaxe', 'netherite_sword', 'netherite_pickaxe']):
        base, tiers = rar[n]
        strip = Image.open(PACK + 'textures/item/%s.png' % n).convert('RGBA').crop((0, 0, 16, 16))
        normal = Image.open(PACK + 'textures/item/aurora/aura_%s.png' % n).convert('RGBA').crop((0, 0, 24, 24))
        for k, au in enumerate([normal, tiers['rare'][0].crop((0, 0, 24, 24)), tiers['legend'][0].crop((0, 0, 24, 24))]):
            fr = au.copy(); fr.alpha_composite(strip, (4, 4))
            sheet.alpha_composite(fr.resize((72, 72), Image.NEAREST), (440 + k * 84 + (i % 2) * 260, y + (i // 2) * 84 - 4))
    y += 180
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
    sheet.alpha_composite(tbook.resize((256, 128), Image.NEAREST), (x0 + 900, y - 120))
    sheet.save(PREVIEWS + '/preview_grimorio.png')
    frames = []
    show = ['mending_1', 'sharpness_5', 'protection_4', 'soul_speed_3', 'efficiency_5', 'binding_curse_1', 'wind_burst_3', 'unbreaking_3']
    for f in range(16):
        g = Image.new('RGBA', (8 * 72 + 10, 80), (60, 52, 84, 255))
        for i, nm in enumerate(show):
            g.alpha_composite(bk[nm].crop((0, f * 16, 16, f * 16 + 16)).resize((64, 64), Image.NEAREST), (8 + i * 72, 8))
        frames.append(g.convert('RGB'))
    frames[0].save(PREVIEWS + '/anim_grimorio.gif', save_all=True, append_images=frames[1:], duration=100, loop=0)

if __name__ == '__main__':
    bk = books()
    rar = rarity()
    mn = menus(); sprites()
    tb = table_book(); pa = particles()
    os.makedirs(PREVIEWS, exist_ok=True)
    preview(bk, rar, mn, pa, tb)
    print('ok')
