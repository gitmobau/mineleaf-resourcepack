# Aurora Celestial (prototype): netherite and diamond armour that does not look like armour.
# Optional pack for Entity Model Features + Entity Texture Features; use it INSTEAD of Aurora EMF, above Aurora Pack.
#
# - The worn textures are almost transparent (the skin shows): only a thin necklace (a V with a spark). Netherite = pastel light, diamond = dark (deep violet with glowing points).
# - EMF models (one per armour slot, 26.x names) add floating, animated light: a halo over the head, a small star in
#   front of the chest, a ring around the hips and hoops around the ankles. The halo and rings are made of segments
#   of different colours, so the spin makes the colours flow (armour textures cannot be animated with .mcmeta).
# - The models are base models (no .properties): every face samples a colour swatch that only the Aurora Celestial
#   netherite/diamond textures paint, in texels no vanilla armour box uses. Other armour textures are transparent
#   there, so on iron, gold... the extra pieces are simply invisible.
# - <texture>_e.png = ETF emissive layer: the halo and the glowing points shine in the dark.
#
# EMF semantics used (EMFPartData / EMFModelPartCustom): a custom part is a child of the vanilla part (attach) or of
# its parent submodel; translate = its pivot offset, rotate = degrees, applied like vanilla ModelPart (rotationZYX);
# box coordinates = (x, y, z, w, h, d) in the part's space. invertAxis is left empty, so all numbers are plain vanilla
# model space (y down, front = -z). Animations assign tx/ty/.. (pixels) and rx/ry/.. (radians) directly.
import os, sys, json, math, shutil
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # build.py runs scripts with -I
from gear import cyc, mix, C, WHITE, VIVID

HOME = os.path.expanduser('~')
REF_ROOT = os.environ.get('AURORA_REF', HOME + '/ref63')
RP = os.environ.get('AURORA_RP', HOME + '/mnt/.minecraft/resourcepacks')
PACK = RP + '/Aurora Celestial'
PREVIEWS = os.environ.get('AURORA_PREVIEWS', PACK)

# ------------------------------------------------------------------ palettes
# 16 colours x (light, base, dark). The model only stores colour indices; each material paints its own palette into
# the swatch block, so the same geometry is pastel on netherite and dark on diamond.
#   0..11 = smooth gradient used around the rings, 12/13 = beads, 14/15 = light / lavender
#   16 fur, 17 fur patches, 18 eyes, 19 nose / inner ears, 20 bag, 21 straps, 22 gold, 23 white
SW = (0, 0)                                   # swatch block: 8x6 texels at the head-top corner (never sampled)
SW2 = (32, 0)                                 # colours 16..23: 8x3 texels at the hat's top-left corner (never sampled)
NGRAD = 12
def ramp(c, light=0.55, dark=0.25, ink=(30, 18, 60)):
    return (mix(c, WHITE, light), c, mix(c, ink, dark))
DARK = [(58, 30, 108), (40, 34, 118), (30, 46, 120), (22, 62, 96), (40, 30, 100), (84, 28, 92)]
PALETTES = {
    'netherite': [ramp(mix(cyc(i / NGRAD, VIVID), WHITE, 0.4)) for i in range(NGRAD)]
                 + [ramp((255, 255, 255), 0, 0.1), ramp((255, 228, 160), 0.45, 0.2),
                    ramp((255, 255, 255), 0, 0.1), ramp((214, 200, 255), 0.5, 0.2)],
    'diamond': [ramp(cyc(i / NGRAD, DARK), 0.22, 0.45, (8, 4, 16)) for i in range(NGRAD)]
               + [ramp((255, 96, 224), 0.35, 0.2), ramp((100, 232, 255), 0.35, 0.2),
                  ramp((255, 120, 230), 0.4, 0.2), ramp((70, 36, 120), 0.3, 0.4, (8, 4, 16))],
}
PALETTES['netherite'] += [ramp((250, 246, 255), 0.5, 0.12), ramp((214, 196, 248), 0.4, 0.2), ramp((70, 46, 120), 0.2, 0.2),
                          ramp((255, 170, 205), 0.4, 0.2), ramp((255, 204, 228), 0.45, 0.2), ramp((190, 170, 240), 0.4, 0.25),
                          ramp((255, 226, 150), 0.45, 0.2), ramp((255, 255, 255), 0, 0.1)]
PALETTES['diamond'] += [ramp((44, 38, 62), 0.3, 0.3, (8, 4, 16)), ramp((72, 62, 98), 0.3, 0.3, (8, 4, 16)),
                        ramp((130, 255, 205), 0.35, 0.2), ramp((255, 150, 200), 0.3, 0.2),
                        ramp((76, 44, 118), 0.3, 0.35, (8, 4, 16)), ramp((116, 74, 166), 0.3, 0.3, (8, 4, 16)),
                        ramp((255, 210, 120), 0.4, 0.2), ramp((235, 225, 255), 0.2, 0.15)]
# indices that also go to the emissive layer (netherite: everything light; diamond: only the glowing bits)
GLOW = {'netherite': set(range(16)) | {16, 17, 19, 20, 21, 22, 23}, 'diamond': {12, 13, 14, 18, 22}}

def texel(idx, row):
    if idx >= 16:
        return SW2[0] + idx % 8, SW2[1] + row
    return SW[0] + idx % 8, SW[1] + (idx // 8) * 3 + row

def uv(idx, row):
    u, v = texel(idx, row)
    return [u + 0.25, v + 0.25, u + 0.75, v + 0.75]        # inside one texel: a solid colour, no bleeding

def box(m, s, idx):
    side = uv(idx, 1)
    return {'coordinates': [round(c, 4) for c in (*m, *s)], 'uvNorth': side, 'uvSouth': side, 'uvEast': side,
            'uvWest': side, 'uvUp': uv(idx, 0), 'uvDown': uv(idx, 2)}

def sub(pid, translate=(0, 0, 0), rotate=(0, 0, 0), boxes=(), subs=()):
    return {'id': pid, 'invertAxis': '', 'translate': list(translate), 'rotate': list(rotate),
            'boxes': list(boxes), 'submodels': list(subs)}

def cube(c, size, idx):
    return box((c[0] - size / 2, c[1] - size / 2, c[2] - size / 2), (size, size, size), idx)

def turn90(m, s, k):
    """box (min, size) turned k quarter turns around the y axis (Mojang's rotationY: x' = x cos + z sin, z' = -x sin + z cos)"""
    x0, y0, z0 = m; x1, z1 = x0 + s[0], z0 + s[2]
    for _ in range(k % 4):
        x0, z0, x1, z1 = z0, -x1, z1, -x0
    return (min(x0, x1), y0, min(z0, z1)), (abs(x1 - x0), s[1], abs(z1 - z0))

def ring(pid, radius, n, thick, beads=(), bead=0.5, shift=0):
    """thin closed hoop around the y axis: n tangent segments coloured along the gradient, plus beads (angle in
    degrees, colour index) sitting on the hoop. Segments a quarter turn apart share one rotated submodel (their boxes
    are just turned by 90 degrees inside it), so the hoop costs n/4 parts instead of n: same picture, less to move."""
    assert n % 4 == 0
    q = n // 4
    seg = 2 * radius * math.tan(math.pi / n) + 0.03
    groups = {i: [] for i in range(q)}
    front = ((-seg / 2, -thick / 2, -radius - thick / 2), (seg, thick, thick))
    for j in range(n):
        m, sz = turn90(*front, j // q)
        groups[j % q].append(box(m, sz, (j * NGRAD // n + shift) % NGRAD))
    extra = []
    for k, (a, idx) in enumerate(beads):
        b = cube((0, 0, -radius), bead, idx)
        m, sz = (b['coordinates'][:3], b['coordinates'][3:])
        i = next((i for i in range(q) if abs(((a - 360 * i / n) / 90) - round((a - 360 * i / n) / 90)) < 1e-6), None)
        if i is None:
            extra.append(sub('%s_b%d' % (pid, k), rotate=(0, a, 0), boxes=[b]))
        else:
            m2, sz2 = turn90(m, sz, round((a - 360 * i / n) / 90))
            groups[i].append(box(m2, sz2, idx))
    subs = [sub('%s_%d' % (pid, i), rotate=(0, round(360 * i / n, 4), 0), boxes=groups[i]) for i in range(q)]
    return sub(pid, subs=subs + extra)

def top(part, pid, subs, anims):
    return {'part': part, 'id': pid, 'attach': True, 'invertAxis': '', 'translate': [0, 0, 0],
            'submodels': subs, 'animations': [anims]}

# ------------------------------------------------------------------ the pieces
# Rates are whole degrees per tick dividing 360, so the preview GIF loops (180 ticks = 9 s).
def helmet():
    # halo: a soft pastel ring with a thin bright core ring inside it and four twinkling sparkles riding on it
    outer = ring('halo_o', 4.55, 24, 0.26)
    core = ring('halo_c', 4.1, 24, 0.18, shift=0)
    for part in core['submodels']:                     # the core ring is white (dark glow on diamond)
        for b in part['boxes']:
            for k in ('uvNorth', 'uvSouth', 'uvEast', 'uvWest'): b[k] = uv(12, 1)
            b['uvUp'], b['uvDown'] = uv(12, 0), uv(12, 2)
    sparks = []
    for k, a in enumerate((45, 135, 225, 315)):
        r = math.radians(a)
        sparks.append(sub('spark_%d' % k, translate=(-4.55 * math.sin(r), 0, -4.55 * math.cos(r)), rotate=(0, a, 0),
                          boxes=[box((-0.12, -0.6, -0.12), (0.24, 1.2, 0.24), 13), box((-0.6, -0.12, -0.12), (1.2, 0.24, 0.24), 13)]))
    halo = sub('halo', subs=[outer, core] + sparks)
    tilt = sub('halo_tilt', translate=(0, -11.5, 0), rotate=(10, 0, -4), subs=[halo])
    anims = {'halo_tilt.ty': '-11.5 + sin(torad(age * 4)) * 0.35', 'halo.ry': 'torad(age * 2)'}
    for k in range(4):
        ex = '0.6 + 0.45 * sin(torad(age * 8 + %d))' % (k * 90)
        anims.update({'spark_%d.sx' % k: ex, 'spark_%d.sy' % k: ex, 'spark_%d.sz' % k: ex})
    return [top('head', 'cel_head', [tilt], anims)]

# ---- chestplate: cat prototypes (the necklace and pendant are gone: the user did not like them)
FUR, PATCH, EYE, PINK, BAG, STRAP, GOLD = 16, 17, 18, 19, 20, 21, 22

def cat_head(asleep=False):
    """cat head boxes around a neck pivot at (0, 0, 0), facing the front (-z); about 3 x 2.6 px"""
    b = [box((-1.5, -2.6, -1.4), (3.0, 2.6, 2.4), FUR),
         box((-1.45, -3.45, -0.55), (0.85, 0.9, 0.5), FUR), box((0.6, -3.45, -0.55), (0.85, 0.9, 0.5), FUR),
         box((-1.25, -3.2, -0.62), (0.45, 0.5, 0.1), PINK), box((0.8, -3.2, -0.62), (0.45, 0.5, 0.1), PINK),
         box((-0.2, -1.0, -1.5), (0.4, 0.3, 0.12), PINK)]
    if asleep:
        b += [box((-1.1, -1.5, -1.5), (0.6, 0.15, 0.12), EYE), box((0.5, -1.5, -1.5), (0.6, 0.15, 0.12), EYE)]
    else:
        b += [box((-1.05, -1.75, -1.5), (0.55, 0.55, 0.12), EYE), box((0.5, -1.75, -1.5), (0.55, 0.55, 0.12), EYE)]
    return b

def straps():
    """backpack straps over both shoulders and down the chest, with little gold buckles"""
    out = []
    for x in (-3.0, 2.1):
        out += [box((x, -0.25, -2.25), (0.9, 0.3, 4.5), STRAP), box((x, 0, -2.3), (0.9, 5.0, 0.25), STRAP),
                box((x + 0.15, 3.6, -2.45), (0.6, 0.6, 0.2), GOLD)]
    return out

def scaled(part, k, root=True):
    """the same submodel tree k times bigger around its own pivot"""
    out = dict(part)
    if not root:
        out['translate'] = [round(c * k, 4) for c in part['translate']]
    out['boxes'] = [dict(b, coordinates=[round(c * k, 4) for c in b['coordinates']]) for b in part['boxes']]
    out['submodels'] = [scaled(sp, k, False) for sp in part['submodels']]
    return out

def chest_cat_shoulder():
    """1. a little cat sitting on the right shoulder, wagging its tail and looking around"""
    head = sub('cat_head', translate=(0, -3.0, -0.1), boxes=cat_head())
    tail = sub('cat_tail', translate=(0, -0.5, 2.2), rotate=(55, 0, 0),      # curled up behind
               boxes=[box((-0.3, -0.3, 0), (0.6, 0.6, 2.2), FUR), box((-0.3, -0.3, 2.2), (0.6, 0.6, 1.0), PATCH)])
    cat = sub('cat', translate=(-6.6, 0, 0.3), subs=[head, tail],
              boxes=[box((-1.2, -3.1, -0.9), (2.4, 3.1, 2.4), FUR), box((-1.4, -1.3, -0.4), (2.8, 1.3, 2.8), FUR),
                     box((-0.65, -2.6, -0.98), (1.3, 1.6, 0.1), PATCH),
                     box((-1.0, -0.6, -1.45), (0.7, 0.6, 0.7), FUR), box((0.3, -0.6, -1.45), (0.7, 0.6, 0.7), FUR)])
    return [top('body', 'cel_body', [scaled(cat, 1.3)], {'cat_tail.ry': 'torad(sin(torad(age * 8)) * 25)',
                                           'cat_head.ry': 'torad(sin(torad(age * 2)) * 20)'})]

def chest_cat_sleeping():
    """2. a cat asleep lying on the left shoulder, breathing slowly, tail hanging down the back"""
    body = sub('cat_body', translate=(6, 0, 0.2),
               boxes=[box((-1.3, -1.8, -2.4), (2.6, 1.8, 5.0), FUR), box((-0.9, -1.85, -1.2), (1.8, 0.1, 2.0), PATCH),
                      box((-1.15, -0.6, -3.1), (0.7, 0.6, 0.8), FUR), box((0.45, -0.6, -3.1), (0.7, 0.6, 0.8), FUR)])
    head = sub('cat_head', translate=(6, 0.2, -2.0), rotate=(0, 0, 8), boxes=cat_head(asleep=True))
    tail = sub('cat_tail', translate=(6, -0.8, 2.7), rotate=(-65, 0, 0),     # hanging down the back
               boxes=[box((-0.3, -0.3, 0), (0.6, 0.6, 2.6), FUR), box((-0.3, -0.3, 2.6), (0.6, 0.6, 1.1), PATCH)])
    k = 1.12
    body, head, tail = (dict(scaled(p_, k), translate=p_['translate']) for p_ in (body, head, tail))
    return [top('body', 'cel_body', [body, head, tail], {'cat_body.sy': '1 + sin(torad(age * 4)) * 0.05',
                                                        'cat_tail.rz': 'torad(sin(torad(age * 4)) * 15)'})]

def chest_cat_backpack():
    """3. a backpack shaped like a cat's face (ears on top, face on the back), straps over the shoulders"""
    bag = sub('bag', translate=(0, 4.5, 2.0),
              boxes=[box((-2.6, -2.6, 0.05), (5.2, 5.4, 2.2), BAG), box((-2.2, -3.2, 0.15), (4.4, 0.7, 2.0), BAG),
                     box((-2.5, -4.2, 0.6), (1.3, 1.1, 1.0), BAG), box((1.2, -4.2, 0.6), (1.3, 1.1, 1.0), BAG),
                     box((-2.2, -3.95, 1.6), (0.65, 0.55, 0.12), PINK), box((1.55, -3.95, 1.6), (0.65, 0.55, 0.12), PINK),
                     box((-1.5, -0.9, 2.25), (0.75, 0.75, 0.12), EYE), box((0.75, -0.9, 2.25), (0.75, 0.75, 0.12), EYE),
                     box((-0.25, 0.0, 2.25), (0.5, 0.35, 0.12), PINK),
                     box((-2.05, 0.25, 2.25), (0.6, 0.4, 0.1), PINK), box((1.45, 0.25, 2.25), (0.6, 0.4, 0.1), PINK),
                     box((-2.65, 1.7, 0.05), (5.3, 0.5, 2.27), STRAP)])
    return [top('body', 'cel_body', [bag, sub('straps', boxes=straps())], {'bag.ty': '4.5 + sin(torad(age * 8)) * 0.12'})]

def chest_cat_peek():
    """4. a backpack with a cat peeking out of the top, looking around"""
    head = sub('cat_head', translate=(0, -2.3, 1.3), rotate=(0, 180, 0), boxes=cat_head())
    bag = sub('bag', translate=(0, 5.2, 2.0), subs=[head],
              boxes=[box((-2.4, -2.2, 0.05), (4.8, 5.0, 2.4), BAG), box((-2.6, -2.5, -0.05), (5.2, 0.6, 2.6), STRAP),
                     box((-1.6, 0.6, 2.45), (3.2, 1.8, 0.15), STRAP), box((-0.35, 1.15, 2.6), (0.7, 0.7, 0.1), GOLD),
                     box((-1.3, -2.95, 1.9), (0.7, 0.5, 0.7), FUR), box((0.6, -2.95, 1.9), (0.7, 0.5, 0.7), FUR)])
    return [top('body', 'cel_body', [bag, sub('straps', boxes=straps())],
                {'cat_head.ry': 'torad(180 + sin(torad(age * 3)) * 45)', 'cat_head.ty': '-2.3 + sin(torad(age * 6)) * 0.15'})]

CHESTS = [chest_cat_shoulder, chest_cat_sleeping, chest_cat_backpack, chest_cat_peek]
PROTOS = {1: 'gato en el hombro', 2: 'gato dormido en el hombro', 3: 'mochila cara de gato', 4: 'mochila con gato asomado'}

# ---- leggings: ribbon sash (the user's pick among 4 prototypes, asked bigger)
def leggings():
    """wide ribbon sash fitted round the hips, tied in a big bow on the left hip, two long tails swaying"""
    band = [box((-4.3, 10.2, -2.35), (8.6, 1.1, 0.3), 2), box((-4.3, 10.2, 2.05), (8.6, 1.1, 0.3), 5),
            box((-4.35, 10.2, -2.35), (0.3, 1.1, 4.7), 4), box((4.05, 10.2, -2.35), (0.3, 1.1, 4.7), 3)]
    bow = [box((1.0, 9.6, -2.75), (1.7, 1.4, 0.35), 3), box((3.2, 9.6, -2.75), (1.7, 1.4, 0.35), 3),
           box((1.35, 9.95, -2.95), (1.0, 0.7, 0.2), 4), box((3.55, 9.95, -2.95), (1.0, 0.7, 0.2), 4),
           cube((2.95, 10.75, -2.75), 0.8, 13)]
    tails = sub('sash_tails', translate=(2.95, 11.1, -2.7),
                boxes=[box((-0.85, 0, -0.1), (0.65, 4.6, 0.2), 4), box((0.25, 0, -0.1), (0.65, 3.8, 0.2), 2)])
    return [top('body', 'cel_waist', [sub('sash', boxes=band + bow, subs=[tails])],
                {'sash_tails.rz': 'torad(sin(torad(age * 6)) * 9)'})]

# ---- boots: little clouds round the feet (the user's pick, asked bigger)
def boots():
    """puffy clouds round each foot, as if walking on them, bobbing gently"""
    out = []
    puff = lambda s: [cube((dx * s, dy * s, dz * s), r * s, 14 if dy < 0 else 15)
                      for dx, dy, dz, r in ((0, 0, 0, 1.0), (-0.75, 0.15, 0.1, 0.75), (0.75, 0.15, -0.1, 0.8), (0.2, -0.5, 0, 0.7))]
    for side, o in (('right', -1), ('left', 1)):
        subs, anims = [], {}
        for k, (x, y, z, s) in enumerate(((3.4 * o, 11.2, -1.9, 1.9), (3.1 * o, 11.5, 2.3, 1.6),
                                          (-0.3 * o, 11.9, -3.9, 1.6), (-1.5 * o, 12.0, 3.7, 1.3))):
            pid = 'cloud_%s_%d' % (side, k)
            subs.append(sub(pid, translate=(x, y, z), boxes=puff(s)))
            anims[pid + '.ty'] = '%g + sin(torad(age * 4 + %d)) * 0.25' % (y, k * 90 + (0 if o < 0 else 45))
        out.append(top('%s_leg' % side, 'cel_%s_leg' % side, subs, anims))
    return out

def slots(v):
    return {'helmet': helmet, 'chestplate': CHESTS[v - 1], 'leggings': leggings, 'boots': boots}

# ------------------------------------------------------------------ textures
def worn(mat):
    """(humanoid, humanoid_leggings, and their emissive layers) for one material"""
    pal = PALETTES[mat]
    hum = Image.new('RGBA', (64, 32)); leg = Image.new('RGBA', (64, 32))
    hum_e = Image.new('RGBA', (64, 32)); leg_e = Image.new('RGBA', (64, 32))
    # the 2D armour is fully transparent: everything is in the 3D pieces (no necklace: the user did not like it)
    # swatches + emissive copies
    for img, emi in ((hum, hum_e), (leg, leg_e)):
        for idx, (light, base, dark) in enumerate(pal):
            for row, c in enumerate((light, base, dark)):
                img.putpixel(texel(idx, row), C(c))
                if idx in GLOW[mat]:
                    emi.putpixel(texel(idx, row), C(c))
    return hum, leg, hum_e, leg_e

# ------------------------------------------------------------------ build
def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(obj, f, indent=2)

def build(v):
    pack = '%s %d' % (PACK, v)
    cem, tex = pack + '/assets/minecraft/emf/cem/', pack + '/assets/minecraft/textures/entity/equipment/'
    shutil.rmtree(pack + '/assets', ignore_errors=True)
    for slot, fn in slots(v).items():
        model = {'textureSize': [64, 32], 'models': fn()}
        for who in ('player_', 'player_slim_', ''):             # exact player names + generic fallback for mobs
            write_json(cem + who + slot + '.jem', model)
    out = {}
    for mat in ('netherite', 'diamond'):
        hum, leg, hum_e, leg_e = worn(mat)
        for layer, img, emi in (('humanoid', hum, hum_e), ('humanoid_leggings', leg, leg_e)):
            os.makedirs(tex + layer, exist_ok=True)
            img.save(tex + '%s/%s.png' % (layer, mat), optimize=True)
            emi.save(tex + '%s/%s_e.png' % (layer, mat), optimize=True)
        out[mat] = (hum, leg)
    src = RP + '/Aurora Pack/pack.png'
    if os.path.exists(src):
        shutil.copyfile(src, pack + '/pack.png')
    with open(pack + '/pack.mcmeta', 'w') as f:
        json.dump({'pack': {'description': ['', {'text': 'Aurora Celestial %d ' % v, 'color': '#B9B9F8'},
                                            {'text': '· %s (EMF + ETF)' % PROTOS[v], 'color': '#F8B0EA'}],
                            'min_format': 84, 'max_format': 97}}, f, indent=2, ensure_ascii=False)
    return out

# ------------------------------------------------------------------ preview (animated)
def rot(rx, ry, rz):
    """Mojang rotationZYX(z, y, x): v' = Rz * Ry * Rx * v"""
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    Rx = ((1, 0, 0), (0, cx, -sx), (0, sx, cx)); Ry = ((cy, 0, sy), (0, 1, 0), (-sy, 0, cy))
    Rz = ((cz, -sz, 0), (sz, cz, 0), (0, 0, 1))
    mm = lambda A, B: tuple(tuple(sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)) for i in range(3))
    return mm(mm(Rz, Ry), Rx)

def evaluate(expr, age):
    env = {'age': age, 'sin': math.sin, 'cos': math.cos, 'torad': math.radians}
    return eval(expr, {'__builtins__': {}}, env)

def draw_part(scene, tex, part, M, T, anims, age):
    """M (3x3) and T (translation) = parent transform; part = submodel dict"""
    t = list(part.get('translate', [0, 0, 0])); r = [math.radians(v) for v in part.get('rotate', [0, 0, 0])]
    sc = [1, 1, 1]
    for k, ex in anims.items():
        pid, var = k.split('.')
        if pid != part['id']: continue
        v = evaluate(ex, age)
        if var[0] == 't': t['xyz'.index(var[1])] = v
        elif var[0] == 'r': r['xyz'.index(var[1])] = v
        elif var[0] == 's': sc['xyz'.index(var[1])] = v
    R = rot(*r)
    T2 = tuple(T[i] + sum(M[i][j] * t[j] for j in range(3)) for i in range(3))
    M2 = tuple(tuple(sum(M[i][k] * R[k][j] for k in range(3)) * sc[j] for j in range(3)) for i in range(3))
    for b in part.get('boxes', []):
        x0, y0, z0, w, h, d = b['coordinates']
        def P(x, y, z):
            return tuple(T2[i] + M2[i][0] * x + M2[i][1] * y + M2[i][2] * z for i in range(3))
        X0, X1, Y0, Y1, Z0, Z1 = x0, x0 + w, y0, y0 + h, z0, z0 + d
        quads = {'uvNorth': [(X0, Y0, Z0), (X1, Y0, Z0), (X1, Y1, Z0), (X0, Y1, Z0)],
                 'uvSouth': [(X1, Y0, Z1), (X0, Y0, Z1), (X0, Y1, Z1), (X1, Y1, Z1)],
                 'uvWest': [(X0, Y0, Z1), (X0, Y0, Z0), (X0, Y1, Z0), (X0, Y1, Z1)],
                 'uvEast': [(X1, Y0, Z0), (X1, Y0, Z1), (X1, Y1, Z1), (X1, Y1, Z0)],
                 'uvUp': [(X0, Y0, Z1), (X1, Y0, Z1), (X1, Y0, Z0), (X0, Y0, Z0)],
                 'uvDown': [(X0, Y1, Z0), (X1, Y1, Z0), (X1, Y1, Z1), (X0, Y1, Z1)]}
        for k, q in quads.items():
            scene.quad([P(*p) for p in q], tex, tuple(b[k]))
    for s in part.get('submodels', []):
        draw_part(scene, tex, s, M2, T2, anims, age)

PIVOTS = {'head': (0, 0, 0), 'body': (0, 0, 0), 'right_leg': (-1.9, 12, 0), 'left_leg': (1.9, 12, 0)}

def render(mat, textures, steve, age, yaw, proto):
    from emf import Scene, LIMBS, SKIN_UV, box_uv_faces
    hum, leg = textures
    sc = Scene(230, 360, math.radians(yaw), math.radians(12), 8, 115, 120)
    for name, piv, m, s, uvo, mir in LIMBS:
        sc.box(piv, 0, m, s, 0, steve, box_uv_faces(*SKIN_UV[name], *s))
    for name, piv, m, s, (u, v), mir in LIMBS:
        if name in ('right_leg', 'left_leg'):
            sc.box(piv, 0, m, s, 0.5, leg, box_uv_faces(u, v, *s, mirror=mir))
        if name == 'body':
            sc.box(piv, 0, m, s, 0.5, leg, box_uv_faces(u, v, *s))
        sc.box(piv, 0, m, s, 1.0, hum, box_uv_faces(u, v, *s, mirror=mir))
    I = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
    for slot, fn in slots(proto).items():
        tex = leg if slot == 'leggings' else hum
        for top in fn():
            anims = {}
            for a in top.get('animations', []): anims.update(a)
            draw_part(sc, tex, top, I, PIVOTS[top['part']], anims, age)
    return sc.img

def preview(textures):
    """celestial.gif: the 4 cat prototypes in netherite, front 3/4 (top row) and back (bottom row), animated;
    celestial.png: the same in diamond (first frame)"""
    sp = REF_ROOT + '/assets/minecraft/textures/entity/player/wide/steve.png'
    steve = Image.open(sp).convert('RGBA') if os.path.exists(sp) else Image.new('RGBA', (64, 64), (200, 150, 120, 255))
    os.makedirs(PREVIEWS, exist_ok=True)
    def sheet(mat, age):
        g = Image.new('RGBA', (4 * 240 + 10, 2 * 360 + 10), (30, 26, 48, 255))
        for v in range(1, 5):
            for row, yaw in enumerate((-35, 145)):
                g.alpha_composite(render(mat, textures[mat], steve, age, yaw, v), (10 + (v - 1) * 240, 5 + row * 360))
        return g.convert('RGB')
    frames = [sheet('netherite', f * 12) for f in range(15)]
    frames[0].save(PREVIEWS + '/celestial.gif', save_all=True, append_images=frames[1:], duration=450, loop=0)
    sheet('diamond', 30).save(PREVIEWS + '/celestial.png')

if __name__ == '__main__':
    shutil.rmtree(PACK, ignore_errors=True)                    # while choosing: 4 prototype packs instead of one
    for v in range(1, 5):
        tx = build(v)
    preview(tx)
    print('celestial ok: 4 prototypes')
