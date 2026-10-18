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
# normal aura (gear.py) -> "rare": a thin gold ring with Mending -> "legendary": a thin pastel-rainbow ring with a soft
# glow and star twinkles with Mending + Unbreaking III + Sharpness/Smite/Bane V (swords, spears) or Efficiency V.
# The ring floats one pixel away from the item (the Enchantment Outlines mod draws its outline right on the edge).
# Auras are only shown where the item is an icon: inventory/hotbar (gui), item frames (fixed) and shelves (on_shelf).
ICON_CONTEXTS = ['gui', 'fixed', 'on_shelf']
N, FT = 32, 3                      # 32 frames x 3 ticks = 4.8 s per loop: slow and calm
W, OFF = 24, 4                     # 24x24 plane around the 16x16 item (same geometry as the aura of gear.py)
GOLD = [(255, 214, 110), (255, 236, 160), (246, 190, 96), (255, 226, 132)]
PASTEL = [(120, 214, 255), (170, 156, 255), (226, 146, 250), (255, 150, 206), (255, 196, 146), (255, 232, 140),
          (166, 244, 170), (120, 236, 220)]
STAR = (255, 248, 222)

def cyc(t, pal):
    return gear.cyc(t, pal)

def field(base):
    """distance from each free texel of the 24x24 plane to the item silhouette, and each texel's angle"""
    sil = {(x + OFF, y + OFF) for y in range(16) for x in range(16) if base.getpixel((x, y))[3]}
    cx = sum(p[0] for p in sil) / len(sil); cy = sum(p[1] for p in sil) / len(sil)
    dist, ang = {}, {}
    for y in range(W):
        for x in range(W):
            if (x, y) in sil: continue
            d = min(math.hypot(x - a, y - b) for a, b in sil)
            if d <= 3.3:
                dist[(x, y)] = d
                ang[(x, y)] = (math.atan2(y - cy, x - cx) / (2 * math.pi)) % 1.0
    return dist, ang

def adist(a, b):
    d = abs(a - b) % 1.0
    return min(d, 1 - d)

def star_spots(dist, ang, n, phase0):
    """n twinkle spots spread around the ring, just outside it (deterministic)"""
    cand = sorted((p for p, d in dist.items() if 2.3 < d <= 3.1), key=lambda p: (ang[p], p))
    spots = []
    for k in range(n):
        t = (phase0 + k / n) % 1.0
        spots.append(min(cand, key=lambda p: (adist(ang[p], t), p)))
    return spots

def aura_tier(base, kind):
    dist, ang = field(base)
    legend = kind == 'legend'
    strip = Image.new('RGBA', (W, W * N))
    spots = star_spots(dist, ang, 3 if legend else 2, 0.12 if legend else 0.3)
    for f in range(N):
        ph = f / N
        breath = 0.9 + 0.1 * math.cos(ph * 2 * math.pi)
        fr = Image.new('RGBA', (W, W))
        for p, d in dist.items():
            a = ang[p]
            if legend:
                col = cyc(a - ph, PASTEL)                       # the rainbow flows slowly around the item
            else:
                col = cyc(a * 2 + ph * 0.5, GOLD)
            glint = max(0.0, 1 - adist(a, ph) / 0.12)           # one soft light travelling around the ring
            if 1.5 < d <= 2.3:                                  # the ring: 1 px line, 1 px away from the item
                al = (175 if legend else 165) + 90 * glint
                col = mix(col, WHITE, (0.12 if legend else 0.04) + 0.7 * glint)
            elif d <= 1.5:                                      # faint fill between item and ring
                al = (46 if legend else 34) + 40 * glint
                col = mix(col, WHITE, 0.35)
            else:                                               # soft outer glow
                al = (40 if legend else 0) * (1 - (d - 2.3) / 1.0)
            if al > 0:
                fr.putpixel(p, C(col, al * breath))
        for k, (x, y) in enumerate(spots):                      # twinkles: fade in and out, one after another
            t = (ph - k / len(spots)) % 1.0
            if t < 0.2:
                s = math.sin(t / 0.2 * math.pi)
                fr.putpixel((x, y), C(mix(STAR, WHITE, s), 120 + 135 * s))
                if legend and s > 0.6:                          # tiny 4-point star at the peak
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        q = (x + dx, y + dy)
                        if 0 <= q[0] < W and 0 <= q[1] < W and q in dist and dist[q] > 1.5:
                            fr.putpixel(q, C(STAR, 110 * s))
        strip.paste(fr, (0, f * W))
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
