# Aurora Celestial: netherite and diamond armour that does not look like armour.
# Optional pack for Entity Model Features + Entity Texture Features; use it INSTEAD of Aurora EMF, above Aurora Pack.
#
# - The worn textures are transparent (the skin shows); everything is in small 3D pieces, one per armour slot:
#   helmet = a double halo, chestplate = a cat on the left shoulder + its cat-face backpack, leggings = a ribbon sash
#   with a bow, boots = little clouds round each foot. Netherite = pastel / white cat, diamond = dark / black cat.
# - EMF models (one per armour slot, 26.x names) with age-driven animations. The halo is made of segments of the
#   colour gradient, so its slow spin makes the colours flow (armour textures cannot be animated with .mcmeta).
# - The models are base models (no .properties): every face samples a colour swatch that only the Aurora Celestial
#   netherite/diamond textures paint, in texels no vanilla armour box uses. Other armour textures are transparent
#   there, so on iron, gold... the extra pieces are simply invisible.
# - <texture>_e.png = ETF emissive layer. The halo glows softly (partial alpha); the cat and the clouds glow as in
#   the first version (the user preferred them); the backpack and the sash do not glow.
#
# 2026-10 polish ("más elegante, más simple, que nada atraviese el cuerpo"): poses checked against 26.3's
# HumanoidModel.setupAnim with the renderer in emf.py (walk at sprint swing, sneak, sit, head turned 45 degrees):
# - the sash is higher (y 8.6-9.6: a sitting player's thighs reach y 10) and its tails are short (a long tail on the
#   front of the hip is crossed by the thigh at every step);
# - the halo: two clearly separate thin rings, two small sparkles instead of four, slower spin, no gold buckles.
# Afterwards the user asked for the previous cat and clouds back (a full ring of clouds round each foot): those two
# are the first version again; halo, backpack and sash keep the polish.
#
# EMF semantics used (EMFPartData / EMFModelPartCustom): a custom part is a child of the vanilla part (attach) or of
# its parent submodel; translate = its pivot offset, rotate = degrees, applied like vanilla ModelPart (rotationZYX);
# box coordinates = (x, y, z, w, h, d) in the part's space. invertAxis is left empty, so all numbers are plain vanilla
# model space (y down, front = -z). Animations assign tx/ty/.. (pixels), rx/ry/.. (radians), sx/sy/sz and visible.
# Parts per slot in 26.3 (HumanoidModel.ADULT_ARMOR_PARTS_PER_SLOT): helmet head; chestplate body + arms; leggings
# body + legs; boots legs.
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
# 24 colours x (light, base, dark). The model only stores colour indices; each material paints its own palette into
# the swatch block, so the same geometry is pastel on netherite and dark on diamond.
#   0..11 = smooth gradient used around the halo, 12 = halo core / bow knot, 13 = sparkles, 14 (spare), 15 = cloud
#   underside, 16 fur, 17 fur patches, 18 eyes, 19 nose / inner ears / ribbon shade, 20 bag / ribbon, 21 straps,
#   22 gold (spare), 23 white (clouds)
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
               + [ramp((240, 120, 220), 0.35, 0.2), ramp((120, 225, 255), 0.35, 0.2),
                  ramp((255, 120, 230), 0.4, 0.2), ramp((70, 36, 120), 0.3, 0.4, (8, 4, 16))],
}
PALETTES['netherite'] += [ramp((250, 246, 255), 0.5, 0.12), ramp((214, 196, 248), 0.4, 0.2), ramp((70, 46, 120), 0.2, 0.2),
                          ramp((255, 170, 205), 0.4, 0.2), ramp((255, 204, 228), 0.45, 0.2), ramp((190, 170, 240), 0.4, 0.25),
                          ramp((255, 226, 150), 0.45, 0.2), ramp((255, 255, 255), 0, 0.1)]
PALETTES['diamond'] += [ramp((44, 38, 62), 0.3, 0.3, (8, 4, 16)), ramp((72, 62, 98), 0.3, 0.3, (8, 4, 16)),
                        ramp((130, 255, 205), 0.35, 0.2), ramp((255, 150, 200), 0.3, 0.2),
                        ramp((76, 44, 118), 0.3, 0.35, (8, 4, 16)), ramp((116, 74, 166), 0.3, 0.3, (8, 4, 16)),
                        ramp((255, 210, 120), 0.4, 0.2), ramp((235, 225, 255), 0.2, 0.15)]
# colour index -> emissive alpha (ETF _e layer). Partial alpha = a softer glow (with shaders too) on the halo; the
# cat (netherite: the whole cat, diamond: its eyes) and the clouds glow fully, as in the first version.
HALO_GLOW = 150
GLOW = {'netherite': {**{i: HALO_GLOW for i in range(NGRAD)}, 12: 190, 13: 230,
                     15: 255, 16: 255, 17: 255, 19: 255, 23: 255},       # cat and clouds: as before (user's pick)
        'diamond': {12: 190, 13: 230, 18: 255}}

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
    return {'id': pid, 'invertAxis': '', 'translate': [round(c, 4) for c in translate],
            'rotate': [round(c, 4) for c in rotate], 'boxes': list(boxes), 'submodels': list(subs)}

def cube(c, size, idx):
    return box((c[0] - size / 2, c[1] - size / 2, c[2] - size / 2), (size, size, size), idx)

def turn90(m, s, k):
    """box (min, size) turned k quarter turns around the y axis (Mojang's rotationY: x' = x cos + z sin, z' = -x sin + z cos)"""
    x0, y0, z0 = m; x1, z1 = x0 + s[0], z0 + s[2]
    for _ in range(k % 4):
        x0, z0, x1, z1 = z0, -x1, z1, -x0
    return (min(x0, x1), y0, min(z0, z1)), (abs(x1 - x0), s[1], abs(z1 - z0))

def ring(pid, radius, n, thick, colour=None, shift=0):
    """thin closed hoop around the y axis: n tangent segments coloured along the gradient (or all one colour).
    Segments a quarter turn apart share one rotated submodel (their boxes are just turned by 90 degrees inside it),
    so the hoop costs n/4 parts instead of n: same picture, less to move."""
    assert n % 4 == 0
    q = n // 4
    seg = 2 * radius * math.tan(math.pi / n) + 0.03
    groups = {i: [] for i in range(q)}
    front = ((-seg / 2, -thick / 2, -radius - thick / 2), (seg, thick, thick))
    for j in range(n):
        m, sz = turn90(*front, j // q)
        groups[j % q].append(box(m, sz, colour if colour is not None else (j * NGRAD // n + shift) % NGRAD))
    return sub(pid, subs=[sub('%s_%d' % (pid, i), rotate=(0, 360 * i / n, 0), boxes=groups[i]) for i in range(q)])

def top(part, pid, subs, anims):
    return {'part': part, 'id': pid, 'attach': True, 'invertAxis': '', 'translate': [0, 0, 0],
            'submodels': subs, 'animations': [anims]}

# ------------------------------------------------------------------ the pieces
# Rates are whole degrees per tick dividing 360, so the preview GIF (360 ticks = 18 s) loops.
HALO_Y = -11.3                     # 2.8 px above the hat layer; the head (with hat) is 9 px wide, the halo 8.8

def helmet():
    """double halo: a pastel gradient ring and a thin pearl ring inside it, clearly apart, with two small sparkles
    riding on the outer ring. Slow spin (20 s a turn) and a gentle float."""
    outer = ring('halo_o', 4.4, 24, 0.26)
    inner = ring('halo_c', 3.7, 20, 0.18, colour=12)
    sparks = []
    for k, a in enumerate((60, 240)):
        r = math.radians(a)
        sparks.append(sub('spark_%d' % k, translate=(-4.4 * math.sin(r), 0, -4.4 * math.cos(r)), rotate=(0, a, 0),
                          boxes=[box((-0.1, -0.45, -0.1), (0.2, 0.9, 0.2), 13), box((-0.45, -0.1, -0.1), (0.9, 0.2, 0.2), 13)]))
    halo = sub('halo', subs=[outer, inner] + sparks)
    tilt = sub('halo_tilt', translate=(0, HALO_Y, 0), rotate=(8, 0, -4), subs=[halo])
    anims = {'halo_tilt.ty': '%g + sin(torad(age * 4)) * 0.25' % HALO_Y, 'halo.ry': 'torad(age * 1)'}
    for k in range(2):
        ex = '0.7 + 0.25 * sin(torad(age * 6 + %d))' % (k * 180)
        anims.update({'spark_%d.sx' % k: ex, 'spark_%d.sy' % k: ex, 'spark_%d.sz' % k: ex})
    return [top('head', 'cel_head', [tilt], anims)]

# ---- chestplate: the cat and its backpack
FUR, PATCH, EYE, PINK, BAG, STRAP, GOLD = 16, 17, 18, 19, 20, 21, 22

def cat_head():
    """cat head boxes around a neck pivot at (0, 0, 0), facing the front (-z); about 3 x 2.6 px (eyes are separate)"""
    return [box((-1.5, -2.6, -1.4), (3.0, 2.6, 2.4), FUR),
            box((-1.45, -3.45, -0.55), (0.85, 0.9, 0.5), FUR), box((0.6, -3.45, -0.55), (0.85, 0.9, 0.5), FUR),
            box((-1.25, -3.2, -0.62), (0.45, 0.5, 0.1), PINK), box((0.8, -3.2, -0.62), (0.45, 0.5, 0.1), PINK),
            box((-0.2, -1.0, -1.5), (0.4, 0.3, 0.12), PINK)]

def straps():
    """slim backpack straps down the chest. They start below the hat layer (it hangs 0.5 px under the neck line), so
    nothing runs over the shoulders inside the head"""
    return [box((x, 0.6, -2.3), (0.7, 4.0, 0.22), STRAP) for x in (-2.9, 2.2)]

def scaled(part, k, root=True):
    """the same submodel tree k times bigger around its own pivot"""
    out = dict(part)
    if not root:
        out['translate'] = [round(c * k, 4) for c in part['translate']]
    out['boxes'] = [dict(b, coordinates=[round(c * k, 4) for c in b['coordinates']]) for b in part['boxes']]
    out['submodels'] = [scaled(sp, k, False) for sp in part['submodels']]
    return out

BAG_Y = 5.6          # backpack a little lower: when sneaking the head drops 4.2 px and its back reached the bag's ears

def chestplate():
    """one cat: it rides in a cat-face backpack, has climbed out onto the left shoulder (lying on it, front paws
    tucked at the front edge), looks around and now and then dozes off (eyes shut for a while)"""
    bag = sub('bag', translate=(1.0, BAG_Y, 2.0),
              boxes=[box((-2.6, -2.6, 0.05), (5.2, 5.4, 2.2), BAG), box((-2.2, -3.2, 0.15), (4.4, 0.7, 2.0), BAG),
                     box((-2.75, -4.2, 0.6), (1.2, 1.1, 1.0), BAG), box((1.55, -4.2, 0.6), (1.2, 1.1, 1.0), BAG),
                     box((-2.45, -3.95, 1.6), (0.6, 0.55, 0.12), PINK), box((1.85, -3.95, 1.6), (0.6, 0.55, 0.12), PINK),
                     box((-1.5, -0.9, 2.25), (0.75, 0.75, 0.12), EYE), box((0.75, -0.9, 2.25), (0.75, 0.75, 0.12), EYE),
                     box((-0.25, 0.0, 2.25), (0.5, 0.35, 0.12), PINK),
                     box((-2.65, 1.7, 0.05), (5.3, 0.5, 2.27), STRAP)])
    bag = dict(scaled(bag, 0.9), translate=bag['translate'])
    eyes_open = sub('cat_eyes', boxes=[box((-1.05, -1.75, -1.5), (0.55, 0.55, 0.12), EYE), box((0.5, -1.75, -1.5), (0.55, 0.55, 0.12), EYE)])
    eyes_shut = sub('cat_sleepy', boxes=[box((-1.1, -1.5, -1.5), (0.6, 0.15, 0.12), EYE), box((0.5, -1.5, -1.5), (0.6, 0.15, 0.12), EYE)])
    head = sub('cat_head', translate=(6.3, -0.8, -1.7), subs=[eyes_open, eyes_shut], boxes=cat_head())
    tail = sub('cat_tail', translate=(6.1, -0.9, 3.3), rotate=(-70, 0, 0),     # hanging down behind the shoulder
               boxes=[box((-0.3, -0.3, 0), (0.6, 0.6, 2.8), FUR), box((-0.3, -0.3, 2.8), (0.6, 0.6, 1.1), PATCH)])
    body = sub('cat_body', translate=(6.1, 0.1, 0),
               boxes=[box((-1.1, -2.0, -1.4), (2.2, 2.0, 4.6), FUR),                 # lying on the shoulder
                      box((-1.3, -1.8, 1.7), (2.6, 1.8, 1.6), FUR),                  # haunches over the back
                      box((-0.75, -2.05, -0.6), (1.5, 0.1, 2.2), PATCH),             # a patch on its back
                      box((-0.95, -0.6, -2.0), (0.65, 1.1, 0.65), FUR), box((0.3, -0.6, -2.0), (0.65, 1.1, 0.65), FUR)])
    nap, awake = 'sin(torad(age * 2)) > 0.9', 'sin(torad(age * 2)) <= 0.9'   # dozes off for a while every 9 s
    body, head, tail = (dict(scaled(p_, 1.25), translate=p_['translate']) for p_ in (body, head, tail))
    return [top('body', 'cel_body', [bag, sub('straps', boxes=straps()), body, head, tail], {
        'bag.ty': '%g + sin(torad(age * 4)) * 0.08' % BAG_Y,
        'cat_body.sy': '1 + sin(torad(age * 4)) * 0.04',
        'cat_head.ry': 'torad(sin(torad(age * 3)) * 15)',
        'cat_head.rx': 'torad(if(%s, 12, 0))' % nap,
        'cat_eyes.visible': awake,
        'cat_sleepy.visible': nap,
        'cat_tail.rz': 'torad(sin(torad(age * 6)) * 18)'})]

# ---- leggings: ribbon sash with a bow on the left hip
RIBBON, RIB_SHADE, KNOT = 20, 19, 12
SASH_Y = 8.2                      # top of the band; a sitting player's thighs reach y 10 (boats, minecarts, horses)
                                  # and a sneaking player's thighs cover the front of the body below y ~9

def leggings():
    """one-colour ribbon round the waist, a neat bow at the front of the left hip with a small knot and two little
    tails that sway (little: the thighs cross anything hanging lower than y ~10.5 when walking or sitting)"""
    y0, h = SASH_Y, 1.0
    band = [box((-4.3, y0, -2.35), (8.6, h, 0.3), RIBBON), box((-4.3, y0, 2.05), (8.6, h, 0.3), RIBBON),
            box((-4.35, y0, -2.35), (0.3, h, 4.7), RIBBON), box((4.05, y0, -2.35), (0.3, h, 4.7), RIBBON)]
    bx, by = 2.0, y0 + 0.5        # bow centre
    bow = [box((bx - 1.75, by - 0.6, -2.7), (1.4, 1.2, 0.35), RIBBON), box((bx + 0.35, by - 0.6, -2.7), (1.4, 1.2, 0.35), RIBBON),
           box((bx - 1.35, by - 0.25, -2.8), (0.7, 0.5, 0.1), RIB_SHADE), box((bx + 0.65, by - 0.25, -2.8), (0.7, 0.5, 0.1), RIB_SHADE),
           cube((bx, by, -2.75), 0.65, KNOT)]
    tails = sub('sash_tails', translate=(bx, by + 0.3, -2.62),
                boxes=[box((-0.6, 0, -0.08), (0.45, 1.1, 0.16), RIBBON), box((0.15, 0, -0.08), (0.45, 0.9, 0.16), RIBBON)])
    return [top('body', 'cel_waist', [sub('sash', boxes=band + bow, subs=[tails])],
                {'sash_tails.rz': 'torad(sin(torad(age * 6)) * 6)'})]

# ---- boots: little clouds round each foot
CLOUD_BODY, CLOUD_UNDER = 23, 15

def cloud_blob(r):
    """a round puff from three crossed boxes (reads as a ball at this size), flat lavender underside"""
    return [box((-r, -0.55 * r, -0.7 * r), (2 * r, 1.1 * r, 1.4 * r), CLOUD_BODY),
            box((-0.7 * r, -0.55 * r, -r), (1.4 * r, 1.1 * r, 2 * r), CLOUD_BODY),
            box((-0.75 * r, -0.95 * r, -0.75 * r), (1.5 * r, 1.6 * r, 1.5 * r), CLOUD_BODY),
            box((-0.85 * r, 0.45 * r, -0.85 * r), (1.7 * r, 0.25 * r, 1.7 * r), CLOUD_UNDER)]

def boots():
    """a ring of round puffs round each foot, as if walking on a cloud; every puff bobs on its own (the previous
    clouds: the user prefers one separate ring per foot)"""
    out = []
    for side, o in (('right', -1), ('left', 1)):
        subs, anims = [], {}
        for k in range(8):
            a = math.radians(k * 45 + 22.5)
            r = (1.4, 0.95, 1.25, 0.85)[k % 4] * (1.15 if k in (0, 7) else 1.0)    # bumpy, biggest at the front
            x, z, y = 3.0 * math.sin(a) * -1, -3.0 * math.cos(a), 11.7 - (0.35 if k % 2 else 0)
            pid = 'cloud_%s_%d' % (side, k)
            subs.append(sub(pid, translate=(round(x, 3), y, round(z, 3)), boxes=cloud_blob(r)))
            anims[pid + '.ty'] = '%g + sin(torad(age * 4 + %d)) * 0.2' % (y, k * 45 + (0 if o < 0 else 90))
        out.append(top('%s_leg' % side, 'cel_%s_leg' % side, subs, anims))
    return out

SLOTS = {'helmet': helmet, 'chestplate': chestplate, 'leggings': leggings, 'boots': boots}

# ------------------------------------------------------------------ textures
def worn(mat):
    """(humanoid, humanoid_leggings, and their emissive layers) for one material"""
    pal = PALETTES[mat]
    hum = Image.new('RGBA', (64, 32)); leg = Image.new('RGBA', (64, 32))
    hum_e = Image.new('RGBA', (64, 32)); leg_e = Image.new('RGBA', (64, 32))
    # the 2D armour is fully transparent: everything is in the 3D pieces; swatches + soft emissive copies
    for img, emi in ((hum, hum_e), (leg, leg_e)):
        for idx, (light, base, dark) in enumerate(pal):
            for row, c in enumerate((light, base, dark)):
                img.putpixel(texel(idx, row), C(c))
                if idx in GLOW[mat]:
                    emi.putpixel(texel(idx, row), C(c)[:3] + (GLOW[mat][idx],))
    return hum, leg, hum_e, leg_e

# ------------------------------------------------------------------ build
def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(obj, f, indent=2)

def build():
    pack = PACK
    cem, tex = pack + '/assets/minecraft/emf/cem/', pack + '/assets/minecraft/textures/entity/equipment/'
    shutil.rmtree(pack + '/assets', ignore_errors=True)
    for slot, fn in SLOTS.items():
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
        out[mat] = (hum, leg, hum_e, leg_e)
    src = RP + '/Aurora Pack/pack.png'
    if os.path.exists(src):
        shutil.copyfile(src, pack + '/pack.png')
    with open(pack + '/pack.mcmeta', 'w') as f:
        json.dump({'pack': {'description': ['', {'text': 'Aurora Celestial ', 'color': '#B9B9F8'},
                                            {'text': '· aureola, gato, cinta y nubes (EMF + ETF)', 'color': '#F8B0EA'}],
                            'min_format': 84, 'max_format': 97}}, f, indent=2, ensure_ascii=False)
    return out

# ------------------------------------------------------------------ preview (animated, posed)
def evaluate(expr, age):
    """tiny evaluator for the expressions used here (OptiFine/EMF syntax: if(c, a, b), !, comparisons)"""
    env = {'age': age, 'sin': math.sin, 'cos': math.cos, 'torad': math.radians, 'if_': lambda c, a, b: a if c else b}
    py = expr.replace('if(', 'if_(').replace('!(', ' not (')
    return eval(py, {'__builtins__': {}}, env)

def draw_part(scene, tex, emi, part, M, T, anims, age):
    """M (3x3) and T (translation) = parent transform; part = submodel dict"""
    from emf import rot
    t = list(part.get('translate', [0, 0, 0])); r = [math.radians(v) for v in part.get('rotate', [0, 0, 0])]
    sc = [1, 1, 1]
    for k, ex in anims.items():
        pid, var = k.split('.')
        if pid != part['id']: continue
        v = evaluate(ex, age)
        if var[0] == 't': t['xyz'.index(var[1])] = v
        elif var[0] == 'r': r['xyz'.index(var[1])] = v
        elif var[0] == 's': sc['xyz'.index(var[1])] = v
        elif var == 'visible' and not v: return
    R = rot(*r)
    T2 = tuple(T[i] + sum(M[i][j] * t[j] for j in range(3)) for i in range(3))
    M2 = tuple(tuple(sum(M[i][k] * R[k][j] for k in range(3)) * sc[j] for j in range(3)) for i in range(3))
    for b in part.get('boxes', []):
        x0, y0, z0, w, h, d = b['coordinates']
        scene.box(T2, M2, (x0, y0, z0), (w, h, d), 0, tex, {'front': tuple(b['uvNorth']), 'back': tuple(b['uvSouth']),
                  'west': tuple(b['uvWest']), 'east': tuple(b['uvEast']), 'top': tuple(b['uvUp']), 'bottom': tuple(b['uvDown'])}, emi)
    for s in part.get('submodels', []):
        draw_part(scene, tex, emi, s, M2, T2, anims, age)

def render(textures, skin, age, view='front', posen='stand', phase=0.0, slim=False, slots=None, night=False,
           W=200, H=300, scale=7, ss=3):
    """one figure wearing the four pieces; textures = (humanoid, leggings, humanoid_e, leggings_e)"""
    from emf import Scene, VIEWS, pose, draw_humanoid
    hum, leg, hum_e, leg_e = textures
    yaw, pitch = VIEWS[view]
    sc = Scene(W, H, math.radians(yaw), math.radians(pitch), scale, W / 2, H * 0.36, ss=ss, night=night)
    P = pose(posen, phase, age)
    draw_humanoid(sc, P, skin, [(leg, leg_e, 0.5, ('body', 'right_leg', 'left_leg')),
                                (hum, hum_e, 1.0, ('head', 'body', 'right_arm', 'left_arm', 'right_leg', 'left_leg'))], slim)
    for slot, fn in (slots or SLOTS).items():
        tex, emi = (leg, leg_e) if slot == 'leggings' else (hum, hum_e)
        for part in fn():
            anims = {}
            for a in part.get('animations', []): anims.update(a)
            T, M = P[part['part']]
            draw_part(sc, tex, emi, part, M, T, anims, age)
    return sc.image()

BG = (30, 26, 48, 255)
# (material, slim, view, pose) per tile of the GIF: idle front / back, walking side, and one more pose per row
GIF_TILES = [('netherite', False, 'front', 'stand'), ('netherite', False, 'back', 'stand'),
             ('netherite', False, 'side_left', 'walk'), ('netherite', False, 'front', 'sneak'),
             ('diamond', True, 'front', 'stand'), ('diamond', True, 'back', 'stand'),
             ('diamond', True, 'side_right', 'walk'), ('diamond', True, 'front_high', 'look')]

def sheet(tiles, cols, W=200, H=300):
    g = Image.new('RGBA', (cols * W, ((len(tiles) + cols - 1) // cols) * H), BG)
    for i, t in enumerate(tiles):
        g.alpha_composite(t, ((i % cols) * W, (i // cols) * H))
    return g

def preview(textures, frames=16, ticks=360):
    """celestial.gif: netherite (wide) and diamond (slim), idle / walking / sneaking / head turned, animated;
    celestial.png: its first frame, bigger"""
    steve, alex = __import__('emf').skins()
    os.makedirs(PREVIEWS, exist_ok=True)
    out = []
    for f in range(frames):
        age, phase = f * ticks / frames, f * 4 * math.pi / frames          # two strides per loop
        tiles = [render(textures[m], alex if slim else steve, age, v, p, phase, slim, W=160, H=240, scale=5.6, ss=2)
                 for m, slim, v, p in GIF_TILES]
        out.append(sheet(tiles, 4, 160, 240).convert('RGB'))
    out[0].resize((out[0].width * 2, out[0].height * 2), Image.NEAREST).save(PREVIEWS + '/celestial.png')
    pal = out[0].quantize(96, method=Image.Quantize.MEDIANCUT)                       # one shared palette: small GIF
    gif = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in out]
    gif[0].save(PREVIEWS + '/celestial.gif', save_all=True, append_images=gif[1:], loop=0,
                duration=1000 * ticks // 20 // frames // 2)                            # twice real speed

if __name__ == '__main__':
    for v in range(1, 5):                                      # the cat prototypes are mixed into one pack now
        shutil.rmtree('%s %d' % (PACK, v), ignore_errors=True)
    tx = build()
    preview(tx)
    print('celestial ok')
