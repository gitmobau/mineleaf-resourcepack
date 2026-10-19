# Aurora "Grimorio": rarity auras for diamond / netherite tools, the enchanting table book and the magic particles
# (enchanting glyphs + hit particles). Enchanted book items and the enchanting menus are left to other packs/scripts.
# Runs after gear.py: it wraps the tool item definitions that gear.py wrote.
import os, sys, math, json
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # build.py runs scripts with -I
import gear
from gear import mix, C, WHITE

REF = gear.REF                     # .../assets/minecraft/
PACK = gear.PACK
PREVIEWS = gear.PREVIEWS
save_tex, save_json = gear.save_tex, gear.save_json

def ref(rel):
    return Image.open(REF + 'textures/' + rel).convert('RGBA')

# ------------------------------------------------------------------ rarity auras
# normal aura (gear.py) -> "rare": a gold ring with Mending -> "legendary": a wider rainbow ring with more sparks with
# Mending + Unbreaking III + Sharpness/Smite/Bane V (swords, spears) or Efficiency V.
# Auras are only shown where the item is an icon: inventory/hotbar (gui), item frames (fixed) and shelves (on_shelf).
ICON_CONTEXTS = ['gui', 'fixed', 'on_shelf']
N, FT = 16, 2                      # 16 frames x 2 ticks = 1.6 s per loop (the first version's speed)
W, OFF = 24, 4                     # 24x24 plane around the 16x16 item (same geometry as the aura of gear.py)
GOLD = [(255, 214, 110), (255, 236, 160), (246, 190, 96), (255, 226, 132)]

def cyc(t, pal):
    return gear.cyc(t, pal)

# The tier look itself is the first version (the user preferred it): a wide ring of colour flowing round the item,
# brighter next to it, with white sparks running round. Only where it shows (icons only) and the predicates changed.
RARE = [(255, 230, 140), (255, 205, 160), (255, 245, 190), (255, 220, 120), (255, 252, 225)]          # gold
LEGEND = [(255, 120, 220), (130, 220, 255), (255, 240, 140), (170, 140, 255), (120, 255, 200), (255, 255, 255)]
TIERS = {'rare': dict(pal=RARE, sparks=4, alpha=(240, 170, 75)),
         'legend': dict(pal=LEGEND, reach=4.4, sparks=6, speed=2, alpha=(235, 165, 80))}

def aura_tier(base, kind):
    return _aura_tier(base, **TIERS[kind])

def _aura_tier(base, pal, N=N, reach=3.6, sparks=3, speed=1, alpha=(215, 135, 55)):
    sil = [[False] * W for _ in range(W)]
    for y in range(16):
        for x in range(16):
            if base.getpixel((x, y))[3]:
                sil[x + OFF][y + OFF] = True
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
    return strip, {"animation": {"frametime": FT}}

def legendary_pred(tool):
    main = ([{"enchantments": ["minecraft:sharpness", "minecraft:smite", "minecraft:bane_of_arthropods"],
              "levels": {"min": 5}}]
            if tool in ('sword', 'spear') else [{"enchantments": "minecraft:efficiency", "levels": {"min": 5}}])
    return [{"enchantments": "minecraft:mending"}, {"enchantments": "minecraft:unbreaking", "levels": {"min": 3}}] + main

def aura_model(tex):
    """flat 24x24 plane behind the item; same geometry as gear.aura_model, kept here so the tiers own it"""
    return {
        "parent": "minecraft:item/handheld",
        "textures": {"aura": tex, "particle": tex},
        "elements": [{
            "from": [-4, -4, 8], "to": [20, 20, 8], "shade_direction_override": "up", "light_emission": 15,
            "faces": {"south": {"uv": [0, 0, 16, 16], "texture": "#aura"},
                      "north": {"uv": [16, 0, 0, 16], "texture": "#aura"}}
        }]
    }

def is_enchant_cond(node):
    return (isinstance(node, dict) and node.get('type') == 'minecraft:condition'
            and node.get('property') == 'minecraft:has_component' and node.get('component') == 'minecraft:enchantments')

def rewrite(node, fn):
    """apply fn to the first has_component(enchantments) condition found (depth first); returns a new tree"""
    if is_enchant_cond(node):
        return fn(node)
    if isinstance(node, dict):
        return {k: rewrite(v, fn) for k, v in node.items()}
    if isinstance(node, list):
        return [rewrite(v, fn) for v in node]
    return node

def rarity():
    out = {}
    for mat in ('diamond', 'netherite'):
        for t in gear.TOOLS:
            n = '%s_%s' % (mat, t)
            base, _ = gear.recolor_tool(n, mat)
            tiers = {kind: aura_tier(base, kind) for kind in ('rare', 'legend')}
            for kind, (st, meta) in tiers.items():
                tex = 'minecraft:item/aurora/aura_%s_%s' % (kind, n)
                save_tex(st, 'item/aurora/aura_%s_%s.png' % (kind, n), meta)
                save_json(aura_model(tex), 'models/item/aurora/aura_%s_%s.json' % (kind, n))
            d = json.load(open(PACK + 'items/%s.json' % n))
            normal_ref = '"minecraft:item/aurora/aura_%s"' % n

            def tiered(cond):                     # gear.py: enchanted -> normal aura, else plain model
                normal = cond['on_true']
                s = json.dumps(normal)
                assert normal_ref in s, 'gear.py no longer references %s' % normal_ref
                with_aura = lambda kind: json.loads(s.replace(normal_ref, '"minecraft:item/aurora/aura_%s_%s"' % (kind, n)))
                comp = lambda value, on_true, on_false: {
                    "type": "minecraft:condition", "property": "minecraft:component",
                    "predicate": "minecraft:enchantments", "value": value, "on_true": on_true, "on_false": on_false}
                new = dict(cond)
                new['on_true'] = comp(legendary_pred(t), with_aura('legend'),
                                      comp([{"enchantments": "minecraft:mending"}], with_aura('rare'), normal))
                return new

            icon = rewrite(d['model'], tiered)
            hand = rewrite(d['model'], lambda cond: cond['on_false'])    # held / worn / dropped: no aura at all
            d['model'] = {"type": "minecraft:select", "property": "minecraft:display_context",
                          "cases": [{"when": ICON_CONTEXTS, "model": icon}], "fallback": hand}
            save_json(d, 'items/%s.json' % n)
            out[n] = (base, tiers)
    return out

# ------------------------------------------------------------------ enchanting table book + particles
def ramp(t, pal):
    t = max(0.0, min(1.0, t)) * (len(pal) - 1)
    i = min(int(t), len(pal) - 2)
    return mix(pal[i], pal[i + 1], t - i)

LEATHER = [(58, 38, 106), (92, 64, 156), (144, 118, 208)]     # plum -> violet -> lavender, by vanilla brightness
PAPER = [(150, 138, 198), (214, 206, 242), (250, 247, 255)]   # lavender ink -> pearl paper

def table_book():
    """the book floating over the enchanting table: plum leather with a faint sheen, pastel gold corners and pearl
    pages. Keeps every shade of the vanilla sheet (leather grain, text lines), only the colours change."""
    v = ref('entity/enchantment/enchanting_table_book.png')
    o = Image.new('RGBA', v.size)
    for y in range(v.height):
        for x in range(v.width):
            p = v.getpixel((x, y))
            if p[3] == 0: continue
            hh, s, vv = gear.hsv(p)
            l = (0.3 * p[0] + 0.59 * p[1] + 0.11 * p[2]) / 255
            if vv < 0.08:                                       # unused black area of the sheet
                o.putpixel((x, y), p); continue
            if y >= 10:                                         # pages
                c = ramp((l - 0.5) / 0.42, PAPER)
            elif 35 <= hh <= 62 and s > 0.6 and vv > 0.7:       # gold corners
                c = mix(GOLD[1], GOLD[2], (1 - vv) * 3)
            elif s < 0.2:                                       # light bands on the spine
                c = mix((232, 224, 252), WHITE, (l - 0.8) * 3)
            else:                                               # leather cover
                c = ramp((l - 0.3) / 0.25, LEATHER)
                c = mix(c, cyc(x / 28 * 0.5 + 0.1, gear.P), 0.14)   # faint iridescent sheen across the cover
            o.putpixel((x, y), C(c, p[3]))
    save_tex(o, 'entity/enchantment/enchanting_table_book.png')
    return o

def particles():
    """enchanting glyphs and hit particles. The game multiplies them by its own colour (glyphs get darkened at random,
    hits get tinted), so they stay light: soft pastels close to white."""
    out = []
    letters = 'abcdefghijklmnopqrstuvwxyz'
    for i, ch in enumerate(letters):
        v = ref('particle/sga_%s.png' % ch)
        o = Image.new('RGBA', v.size)
        col = mix(cyc(i / len(letters), gear.P), WHITE, 0.2)
        for y in range(v.height):
            for x in range(v.width):
                p = v.getpixel((x, y))
                if p[3]: o.putpixel((x, y), C(mix(col, WHITE, 0.2 * (p[0] / 255)), p[3]))
        save_tex(o, 'particle/sga_%s.png' % ch)
        out.append(o)
    for n, core in (('enchanted_hit', (206, 182, 255)), ('critical_hit', (255, 222, 178))):
        v = ref('particle/%s.png' % n)
        o = Image.new('RGBA', v.size)
        for y in range(v.height):
            for x in range(v.width):
                p = v.getpixel((x, y))
                if p[3]:
                    o.putpixel((x, y), C(mix(core, WHITE, (p[0] / 255) ** 2 * 0.8), p[3]))
        save_tex(o, 'particle/%s.png' % n)
        out.append(o)
    return out

# ------------------------------------------------------------------ preview
def preview(rar, parts, tbook):
    names = ['diamond_sword', 'diamond_pickaxe', 'netherite_sword', 'netherite_pickaxe']
    sheet = Image.new('RGBA', (1140, 420), (60, 52, 84, 255))
    for i, n in enumerate(names):
        base, tiers = rar[n]
        tool = Image.open(PACK + 'textures/item/%s.png' % n).convert('RGBA').crop((0, 0, 16, 16))
        normal = Image.open(PACK + 'textures/item/aurora/aura_%s.png' % n).convert('RGBA').crop((0, 0, 24, 24))
        for k, au in enumerate([normal, tiers['rare'][0].crop((0, 0, 24, 24)), tiers['legend'][0].crop((0, 0, 24, 24))]):
            fr = au.copy(); fr.alpha_composite(tool, (4, 4))
            sheet.alpha_composite(fr.resize((72, 72), Image.NEAREST), (10 + k * 84 + i * 280, 10))
    for i, p in enumerate(parts):
        sheet.alpha_composite(p.resize((32, 32), Image.NEAREST), (10 + i * 40, 110))
    sheet.alpha_composite(tbook.resize((256, 128), Image.NEAREST), (10, 160))
    sheet.save(PREVIEWS + '/preview_grimorio.png')
    frames = []
    for f in range(N):
        g = Image.new('RGBA', (3 * 84 * 2 + 20, 90), (60, 52, 84, 255))
        for i, n in enumerate(['diamond_sword', 'netherite_pickaxe']):
            base, tiers = rar[n]
            tool = Image.open(PACK + 'textures/item/%s.png' % n).convert('RGBA')
            tool = tool.crop((0, 0, 16, 16)) if tool.height == 16 else tool.crop((0, (f % (tool.height // 16)) * 16, 16, (f % (tool.height // 16)) * 16 + 16))
            normal = Image.open(PACK + 'textures/item/aurora/aura_%s.png' % n).convert('RGBA')
            nf = normal.height // 24
            for k, au in enumerate([normal.crop((0, (f % nf) * 24, 24, (f % nf) * 24 + 24)),
                                    tiers['rare'][0].crop((0, f * 24, 24, f * 24 + 24)),
                                    tiers['legend'][0].crop((0, f * 24, 24, f * 24 + 24))]):
                fr = au.copy(); fr.alpha_composite(tool, (4, 4))
                g.alpha_composite(fr.resize((72, 72), Image.NEAREST), (10 + (i * 3 + k) * 84, 8))
        frames.append(g.convert('RGB'))
    frames[0].save(PREVIEWS + '/anim_grimorio.gif', save_all=True, append_images=frames[1:], duration=FT * 50, loop=0)

if __name__ == '__main__':
    rar = rarity()
    tb = table_book(); pa = particles()
    os.makedirs(PREVIEWS, exist_ok=True)
    preview(rar, pa, tb)
    print('ok')
