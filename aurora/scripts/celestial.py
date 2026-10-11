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
from gear import cyc, mix, C, WHITE, VIVID, box_faces, HUMANOID_BOXES

HOME = os.path.expanduser('~')
REF_ROOT = os.environ.get('AURORA_REF', HOME + '/ref63')
RP = os.environ.get('AURORA_RP', HOME + '/mnt/.minecraft/resourcepacks')
PACK = RP + '/Aurora Celestial'                  # prototypes: 'Aurora Celestial 1' ... 'Aurora Celestial 4'
PREVIEWS = os.environ.get('AURORA_PREVIEWS', PACK)

# ------------------------------------------------------------------ palettes
# 16 colours x (light, base, dark). The model only stores colour indices; each material paints its own palette into
# the swatch block, so the same geometry is pastel on netherite and dark on diamond.
#   0..11 = smooth gradient used around the rings, 12/13 = beads, 14/15 = pendant
SW = (0, 0)                                   # swatch block: 8x6 texels at the head-top corner (never sampled)
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
GLOW = {'netherite': set(range(16)), 'diamond': {12, 13, 14}}   # indices that also go to the emissive layer
LINE = {'netherite': lambda t: mix(cyc(t, VIVID), WHITE, 0.35), 'diamond': lambda t: (52, 26, 96)}
SPARK = {'netherite': lambda t: WHITE, 'diamond': lambda t: (255, 96, 224) if int(t * 10) % 2 else (100, 232, 255)}

def texel(idx, row):
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
def flat_star(c, size, thick, idx, core=None, depth=0.18):
    """4-point star facing the front: a long and a tall bar plus an optional core bead"""
    x, y, z = c
    out = [box((x - size / 2, y - thick / 2, z - depth / 2), (size, thick, depth), idx),
           box((x - thick / 2, y - size / 2, z - depth / 2), (thick, size, depth), idx)]
    if core is not None:
        out.append(cube((x, y, z - depth / 2), thick * 1.5, core))
    return out

def beam(pid, p0, p1, thick, idx, z):
    """thin bar from p0 to p1 (x, y) in the front plane at depth z"""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    length = math.hypot(dx, dy)
    return sub(pid, translate=(p0[0], p0[1], 0), rotate=(0, 0, math.degrees(math.atan2(dy, dx))),
               boxes=[box((0, -thick / 2, z - thick / 2), (length, thick, thick), idx)])

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

def chestplate():
    # pendant: a FLAT jewel lying on the chest under the necklace (barely 0.45 px in front of it), swinging softly
    # like a pendulum from the bottom of the V and gently pulsing
    jewel = sub('pend', translate=(0, 1.25, 0), rotate=(0, 0, 45),
                boxes=[box((-0.6, -0.6, -0.12), (1.2, 1.2, 0.24), 15), box((-0.33, -0.33, -0.26), (0.66, 0.66, 0.14), 14),
                       cube((0.55, -0.55, -0.2), 0.22, 13)])
    pivot = sub('pend_pivot', translate=(0, 4.2, -3.2), subs=[jewel])
    return [top('body', 'cel_body', [pivot], {'pend_pivot.rz': 'torad(sin(torad(age * 4)) * 7)',
                                             'pend.sx': '1 + sin(torad(age * 8)) * 0.07',
                                             'pend.sy': '1 + sin(torad(age * 8)) * 0.07'})]

# ---- leggings prototypes (not halos)
def leg_sash():
    """1. ribbon sash fitted round the hips, tied in a bow on the left hip, two tails swaying"""
    band = [box((-4.25, 10.6, -2.3), (8.5, 0.6, 0.25), 2), box((-4.25, 10.6, 2.05), (8.5, 0.6, 0.25), 5),
            box((-4.3, 10.6, -2.3), (0.25, 0.6, 4.6), 4), box((4.05, 10.6, -2.3), (0.25, 0.6, 4.6), 3)]
    bow = [box((1.7, 10.2, -2.65), (1.0, 0.8, 0.3), 3), box((3.1, 10.2, -2.65), (1.0, 0.8, 0.3), 3), cube((2.9, 10.9, -2.55), 0.55, 13)]
    tails = sub('sash_tails', translate=(2.9, 11.1, -2.55),
                boxes=[box((-0.55, 0, -0.08), (0.4, 3.4, 0.16), 4), box((0.2, 0, -0.08), (0.4, 2.8, 0.16), 2)])
    return [top('body', 'cel_waist', [sub('sash', boxes=band + bow, subs=[tails])],
                {'sash_tails.rz': 'torad(sin(torad(age * 6)) * 9)'})]

def leg_knee_stars():
    """2. a small twinkling star floating just in front of each knee, plus a tiny one on the thigh"""
    out = []
    for side, o in (('right', -1), ('left', 1)):
        star = sub('knee_%s' % side, translate=(0.2 * o, 6.3, -2.45), boxes=flat_star((0, 0, 0), 1.7, 0.36, 2, core=12))
        small = sub('thigh_%s' % side, translate=(1.0 * o, 2.6, -2.3), boxes=flat_star((0, 0, 0), 0.9, 0.22, 4))
        ph = 0 if o < 0 else 180
        ex = '1 + sin(torad(age * 6 + %d)) * 0.22' % ph
        ex2 = '0.8 + sin(torad(age * 6 + %d)) * 0.3' % (ph + 90)
        out.append(top('%s_leg' % side, 'cel_%s_leg' % side, [star, small],
                       {'knee_%s.sx' % side: ex, 'knee_%s.sy' % side: ex, 'knee_%s.rz' % side: 'torad(sin(torad(age * 2)) * 12)',
                        'thigh_%s.sx' % side: ex2, 'thigh_%s.sy' % side: ex2}))
    return out

def leg_feathers():
    """3. three small light feathers at each hip, fluttering"""
    subs, anims = [], {}
    for side, o in (('r', -1), ('l', 1)):
        subs.append(sub('hipwing_%s' % side, translate=(4.75 * o, 10.0, 0.6), rotate=(-25, 0, 0),
                        boxes=[box((-0.1, k * 0.65, 0), (0.2, 0.5, 3.0 - k * 0.6), 12 if k == 0 else (3 + k) % NGRAD)
                               for k in range(3)]))
        anims['hipwing_%s.ry' % side] = 'torad(%d + sin(torad(age * 12)) * 12)' % (15 * o)
    return [top('body', 'cel_waist', subs, anims)]

def leg_constellation():
    """4. a little constellation on the front of each thigh: twinkling points joined by fine lines"""
    out = []
    pts = ((-0.9, 1.2), (0.8, 2.6), (-0.2, 4.4), (1.0, 5.6))
    for side, o in (('right', -1), ('left', 1)):
        P = [(x * -o, y) for x, y in pts]
        lines = [beam('cst_%s_l%d' % (side, k), P[k], P[k + 1], 0.12, 15, -2.12) for k in range(len(P) - 1)]
        dots = [sub('cst_%s_p%d' % (side, k), translate=(x, y, -2.18), boxes=[cube((0, 0, 0), 0.42, 12 if k % 2 else 13)])
                for k, (x, y) in enumerate(P)]
        anims = {}
        for k in range(len(P)):
            ex = '0.7 + sin(torad(age * 8 + %d)) * 0.45' % (k * 90 + (0 if o < 0 else 45))
            anims.update({'cst_%s_p%d.sx' % (side, k): ex, 'cst_%s_p%d.sy' % (side, k): ex, 'cst_%s_p%d.sz' % (side, k): ex})
        out.append(top('%s_leg' % side, 'cel_%s_leg' % side, lines + dots, anims))
    return out

# ---- boots prototypes (not halos)
def boot_wings():
    """1. little wings of light on the outer side of each heel, flapping"""
    out = []
    for side, o in (('right', -1), ('left', 1)):
        feathers = [box((-0.1, -k * 0.6, 0), (0.2, 0.5, 2.6 - k * 0.5), 12 if k == 0 else (2 + k) % NGRAD) for k in range(3)]
        wing = sub('heelwing_%s' % side, translate=(2.25 * o, 9.6, 0.9), rotate=(-30, 0, 0), boxes=feathers)
        out.append(top('%s_leg' % side, 'cel_%s_leg' % side, [wing],
                       {'heelwing_%s.ry' % side: 'torad(%d + sin(torad(age * 12)) * 18)' % (20 * o)}))
    return out

def boot_trail():
    """2. a trail of three sparkles behind each heel, bobbing one after another"""
    out = []
    for side, o in (('right', -1), ('left', 1)):
        subs, anims = [], {}
        for k, (z, y, s) in enumerate(((3.5, 10.6, 1.2), (4.7, 9.9, 0.9), (5.7, 9.3, 0.6))):
            pid = 'trail_%s_%d' % (side, k)
            subs.append(sub(pid, translate=(0.4 * o, y, z), boxes=flat_star((0, 0, 0), s, 0.2, 12 if k == 0 else 3 + k)))
            anims[pid + '.ty'] = '%g + sin(torad(age * 8 + %d)) * 0.3' % (y, k * 60 + (0 if o < 0 else 180))
            ex = '0.75 + sin(torad(age * 8 + %d)) * 0.3' % (k * 60)
            anims.update({pid + '.sx': ex, pid + '.sy': ex})
        out.append(top('%s_leg' % side, 'cel_%s_leg' % side, subs, anims))
    return out

def boot_ribbon():
    """3. a ribbon tied snugly round each ankle (hugging the leg, not floating), bow at the back, two tails swaying"""
    out = []
    for side, o in (('right', -1), ('left', 1)):
        band = [box((-2.25, 8.4, -2.25), (4.5, 0.5, 0.22), 2), box((-2.25, 8.4, 2.03), (4.5, 0.5, 0.22), 4),
                box((-2.25, 8.4, -2.25), (0.22, 0.5, 4.5), 3), box((2.03, 8.4, -2.25), (0.22, 0.5, 4.5), 3)]
        bow = [box((-1.3, 7.95, 2.2), (0.9, 0.7, 0.3), 4), box((0.4, 7.95, 2.2), (0.9, 0.7, 0.3), 4), cube((0, 8.65, 2.35), 0.45, 13)]
        tails = sub('rtail_%s' % side, translate=(0, 8.85, 2.35),
                    boxes=[box((-0.5, 0, -0.07), (0.35, 2.2, 0.14), 2), box((0.15, 0, -0.07), (0.35, 1.8, 0.14), 4)])
        out.append(top('%s_leg' % side, 'cel_%s_leg' % side, [sub('ribbon_%s' % side, boxes=band + bow, subs=[tails])],
                       {'rtail_%s.rx' % side: 'torad(%d + sin(torad(age * 6 + %d)) * 10)' % (15, 0 if o < 0 else 180)}))
    return out

def boot_clouds():
    """4. tiny clouds round each foot, as if walking on them, bobbing gently"""
    out = []
    puff = lambda c, s: [cube((c[0] + dx * s, c[1] + dy * s, c[2] + dz * s), r * s, 14 if dy < 0 else 15)
                         for dx, dy, dz, r in ((0, 0, 0, 1.0), (-0.75, 0.15, 0.1, 0.75), (0.75, 0.15, -0.1, 0.8), (0.2, -0.5, 0, 0.7))]
    for side, o in (('right', -1), ('left', 1)):
        subs, anims = [], {}
        for k, (x, y, z, s) in enumerate(((2.9 * o, 11.5, -1.8, 1.2), (2.7 * o, 11.8, 1.9, 1.0), (-0.3 * o, 12.2, -3.4, 0.9))):
            pid = 'cloud_%s_%d' % (side, k)
            subs.append(sub(pid, translate=(x, y, z), boxes=puff((0, 0, 0), s)))
            anims[pid + '.ty'] = '%g + sin(torad(age * 4 + %d)) * 0.25' % (y, k * 120 + (0 if o < 0 else 60))
        out.append(top('%s_leg' % side, 'cel_%s_leg' % side, subs, anims))
    return out

LEGGINGS = [leg_sash, leg_knee_stars, leg_feathers, leg_constellation]
BOOTS = [boot_wings, boot_trail, boot_ribbon, boot_clouds]
PROTOS = {1: 'cinta + alitas', 2: 'estrellas en las rodillas + estela', 3: 'plumas + lazos', 4: 'constelación + nubecitas'}

def slots(v):
    return {'helmet': helmet, 'chestplate': chestplate, 'leggings': LEGGINGS[v - 1], 'boots': BOOTS[v - 1]}

# ------------------------------------------------------------------ textures
def faces_of(boxes):
    out = []
    for (u, v, w, h, d) in boxes:
        f = box_faces(u, v, w, h, d)
        out.append(f)
    return out

def hline(img, x0, x1, y, col, a=255):
    for x in range(x0, x1):
        img.putpixel((x, y), C(col(x), a))

def worn(mat):
    """(humanoid, humanoid_leggings, and their emissive layers) for one material"""
    pal = PALETTES[mat]; line = LINE[mat]; spark = SPARK[mat]
    hum = Image.new('RGBA', (64, 32)); leg = Image.new('RGBA', (64, 32))
    hum_e = Image.new('RGBA', (64, 32)); leg_e = Image.new('RGBA', (64, 32))
    head, hat, body, arm, legb = faces_of(HUMANOID_BOXES)
    col = lambda x: line(x / 32)
    # neckline: a thin V on the chest front, one spark at the bottom
    fx, fy = body['front'][:2]
    for i in range(4):
        hum.putpixel((fx + i, fy + i), C(col(fx + i))); hum.putpixel((fx + 7 - i, fy + i), C(col(fx + 7 - i)))
    hum.putpixel((fx + 3, fy + 4), C(spark(0.3))); hum.putpixel((fx + 4, fy + 4), C(spark(0.3)))
    # swatches + emissive copies
    for img, emi in ((hum, hum_e), (leg, leg_e)):
        for idx, (light, base, dark) in enumerate(pal):
            for row, c in enumerate((light, base, dark)):
                img.putpixel(texel(idx, row), C(c))
                if idx in GLOW[mat]:
                    emi.putpixel(texel(idx, row), C(c))
        if mat == 'netherite':                                  # light lines glow softly too
            for y in range(8, 32):
                for x in range(64):
                    p = img.getpixel((x, y))
                    if p[3]: emi.putpixel((x, y), p)
        else:                                                   # dark lines; only the sparks glow
            for (x, y) in ((fx + 3, fy + 4), (fx + 4, fy + 4)):
                if img is hum: emi.putpixel((x, y), img.getpixel((x, y)))
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

def render(mat, textures, steve, age, yaw, proto=1):
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
    """celestial.gif: the 4 prototypes in netherite (front 3/4 view), animated; celestial.png: front + back of each
    prototype in netherite and diamond"""
    sp = REF_ROOT + '/assets/minecraft/textures/entity/player/wide/steve.png'
    steve = Image.open(sp).convert('RGBA') if os.path.exists(sp) else Image.new('RGBA', (64, 64), (200, 150, 120, 255))
    os.makedirs(PREVIEWS, exist_ok=True)
    frames = []
    for f in range(20):
        age = f * 9
        g = Image.new('RGBA', (4 * 240 + 10, 380), (30, 26, 48, 255))
        for v in range(1, 5):
            g.alpha_composite(render('netherite', textures['netherite'], steve, age, -30, v), (10 + (v - 1) * 240, 10))
        frames.append(g.convert('RGB'))
    frames[0].save(PREVIEWS + '/celestial.gif', save_all=True, append_images=frames[1:], duration=450, loop=0)
    sheet = Image.new('RGBA', (4 * 240 + 10, 4 * 370 + 10), (30, 26, 48, 255))
    for v in range(1, 5):
        for row, (mat, yaw) in enumerate((('netherite', -30), ('netherite', 150), ('diamond', -30), ('diamond', 150))):
            sheet.alpha_composite(render(mat, textures[mat], steve, 30, yaw, v), (10 + (v - 1) * 240, 10 + row * 370))
    sheet.convert('RGB').save(PREVIEWS + '/celestial.png')

if __name__ == '__main__':
    shutil.rmtree(PACK, ignore_errors=True)                    # the single pack of the first prototype is gone
    for v in range(1, 5):
        tx = build(v)
    preview(tx)
    print('celestial ok: 4 prototypes')
