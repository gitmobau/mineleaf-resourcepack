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
PACK = RP + '/Aurora Celestial'
CEM = PACK + '/assets/minecraft/emf/cem/'
TEX = PACK + '/assets/minecraft/textures/entity/equipment/'
PREVIEWS = os.environ.get('AURORA_PREVIEWS', PACK)

# ------------------------------------------------------------------ palettes
# 8 colours x (light, base, dark). The model only stores colour indices; each material paints its own palette into
# the swatch block, so the same geometry is pastel on netherite and dark on diamond.
SW = (0, 0)                                   # swatch block: 8x3 texels at the head-top corner (never sampled)
def ramp(c, light=0.55, dark=0.25, ink=(30, 18, 60)):
    return (mix(c, WHITE, light), c, mix(c, ink, dark))
PALETTES = {
    'netherite': [ramp(mix(VIVID[k], WHITE, 0.35)) for k in (0, 1, 2, 4, 6, 9)]
                 + [ramp((255, 255, 255), 0, 0.12), ramp((255, 226, 150), 0.4, 0.25)],
    'diamond': [ramp(c, 0.25, 0.4, (8, 4, 16)) for c in ((58, 30, 108), (38, 36, 112), (84, 28, 88), (22, 62, 86),
                                                          (100, 30, 80), (30, 46, 120))]
               + [ramp((255, 96, 224), 0.35, 0.2), ramp((100, 232, 255), 0.35, 0.2)],
}
GLOW = {'netherite': set(range(8)), 'diamond': {6, 7}}      # indices that also go to the emissive layer
LINE = {'netherite': lambda t: mix(cyc(t, VIVID), WHITE, 0.35), 'diamond': lambda t: (52, 26, 96)}
SPARK = {'netherite': lambda t: WHITE, 'diamond': lambda t: (255, 96, 224) if int(t * 10) % 2 else (100, 232, 255)}

def uv(idx, row):
    u, v = SW[0] + idx, SW[1] + row
    return [u + 0.25, v + 0.25, u + 0.75, v + 0.75]        # inside one texel: a solid colour, no bleeding

def box(m, s, idx):
    side = uv(idx, 1)
    return {'coordinates': [round(c, 4) for c in (*m, *s)], 'uvNorth': side, 'uvSouth': side, 'uvEast': side,
            'uvWest': side, 'uvUp': uv(idx, 0), 'uvDown': uv(idx, 2)}

def sub(pid, translate=(0, 0, 0), rotate=(0, 0, 0), boxes=(), subs=()):
    return {'id': pid, 'invertAxis': '', 'translate': list(translate), 'rotate': list(rotate),
            'boxes': list(boxes), 'submodels': list(subs)}

def ring(pid, radius, n, thick, height, pattern):
    """n tangent segments around the y axis (each one its own submodel turned by 360/n degrees)"""
    seg = 2 * radius * math.tan(math.pi / n) + 0.04
    return sub(pid, subs=[sub('%s_%d' % (pid, i), rotate=(0, 360 * i / n, 0),
                              boxes=[box((-seg / 2, -height / 2, -radius - thick / 2), (seg, height, thick),
                                         pattern[i % len(pattern)])]) for i in range(n)])

def cube(c, size, idx):
    return box((c[0] - size / 2, c[1] - size / 2, c[2] - size / 2), (size, size, size), idx)

# ------------------------------------------------------------------ the pieces
# Animation rates are whole degrees per tick dividing 360, so the preview GIF loops (180 ticks = 9 s).
HALO = [0, 1, 6, 2, 3, 7, 4, 5, 6, 0, 2, 7]                  # pastel ring with white/gold beads (dark: glowing beads)
def helmet():
    halo = ring('halo', 4.6, 12, 0.7, 0.55, HALO)
    tilt = sub('halo_tilt', translate=(0, -12, 0), rotate=(12, 0, 0), subs=[halo])
    return [{'part': 'head', 'id': 'cel_head', 'attach': True, 'invertAxis': '', 'translate': [0, 0, 0],
             'submodels': [tilt],
             'animations': [{'halo_tilt.ty': '-12 + sin(torad(age * 4)) * 0.5',
                             'halo.ry': 'torad(age * 2)'}]}]

def chestplate():
    star = sub('star', rotate=(0, 0, 45), boxes=[cube((0, 0, 0), 1.8, 6)],
               subs=[sub('star_x', rotate=(45, 0, 0), boxes=[cube((0, 0, 0), 1.3, 7)])])
    motes = sub('star_orbit', subs=[sub('mote_%d' % i, rotate=(0, a, 0), boxes=[cube((0, 0, -2.6), 0.45, 6 if i else 7)])
                                    for i, a in enumerate((0, 180))])
    pos = sub('star_pos', translate=(0, 5.5, -5.2), subs=[star, motes])
    return [{'part': 'body', 'id': 'cel_body', 'attach': True, 'invertAxis': '', 'translate': [0, 0, 0],
             'submodels': [pos],
             'animations': [{'star_pos.ty': '5.5 + sin(torad(age * 6)) * 0.35',
                             'star_pos.ry': 'torad(age * 6)',
                             'star.sx': '1 + sin(torad(age * 8)) * 0.15', 'star.sy': '1 + sin(torad(age * 8)) * 0.15',
                             'star.sz': '1 + sin(torad(age * 8)) * 0.15',
                             'star_orbit.ry': 'torad(age * -12)'}]}]

WAIST = [0, 1, 2, 3, 4, 5, 6]
def leggings():
    hips = ring('waist', 6.0, 14, 0.5, 0.4, WAIST)
    tilt = sub('waist_tilt', translate=(0, 13.5, 0), rotate=(0, 0, 4), subs=[hips])
    return [{'part': 'body', 'id': 'cel_waist', 'attach': True, 'invertAxis': '', 'translate': [0, 0, 0],
             'submodels': [tilt],
             'animations': [{'waist_tilt.ty': '13.5 + sin(torad(age * 4 + 90)) * 0.3',
                             'waist.ry': 'torad(age * -2)'}]}]

ANKLE = [2, 6, 3, 1, 7, 4, 0, 5, 6, 2]
def boots():
    out = []
    for side, sgn in (('right', 1), ('left', -1)):
        hoop = ring('ankle_' + side, 4.3, 10, 0.45, 0.4, ANKLE)
        out.append({'part': side + '_leg', 'id': 'cel_' + side + '_leg', 'attach': True, 'invertAxis': '',
                    'translate': [0, 0, 0], 'submodels': [sub('ankle_%s_pos' % side, translate=(0, 8.6, 0), subs=[hoop])],
                    'animations': [{'ankle_%s_pos.ty' % side: '8.6 + sin(torad(age * 8 + %d)) * 0.25' % (90 * (1 - sgn)),
                                    'ankle_%s.ry' % side: 'torad(age * %d)' % (4 * sgn)}]})
    return out

SLOTS = {'helmet': helmet, 'chestplate': chestplate, 'leggings': leggings, 'boots': boots}

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
                img.putpixel((SW[0] + idx, SW[1] + row), C(c))
                if idx in GLOW[mat]:
                    emi.putpixel((SW[0] + idx, SW[1] + row), C(c))
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

def build():
    shutil.rmtree(PACK + '/assets', ignore_errors=True)
    for slot, fn in SLOTS.items():
        model = {'textureSize': [64, 32], 'models': fn()}
        for who in ('player_', 'player_slim_', ''):             # exact player names + generic fallback for mobs
            write_json(CEM + who + slot + '.jem', model)
    out = {}
    for mat in ('netherite', 'diamond'):
        hum, leg, hum_e, leg_e = worn(mat)
        for layer, img, emi in (('humanoid', hum, hum_e), ('humanoid_leggings', leg, leg_e)):
            os.makedirs(TEX + layer, exist_ok=True)
            img.save(TEX + '%s/%s.png' % (layer, mat), optimize=True)
            emi.save(TEX + '%s/%s_e.png' % (layer, mat), optimize=True)
        out[mat] = (hum, leg)
    src = RP + '/Aurora Pack/pack.png'
    if os.path.exists(src):
        shutil.copyfile(src, PACK + '/pack.png')
    with open(PACK + '/pack.mcmeta', 'w') as f:
        json.dump({'pack': {'description': ['', {'text': 'Aurora Celestial ', 'color': '#B9B9F8'},
                                            {'text': '· aureolas (EMF + ETF, en lugar de Aurora EMF)', 'color': '#F8B0EA'}],
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

def render(mat, textures, steve, age, yaw):
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
    for slot, fn in SLOTS.items():
        tex = leg if slot == 'leggings' else hum
        for top in fn():
            anims = {}
            for a in top.get('animations', []): anims.update(a)
            draw_part(sc, tex, top, I, PIVOTS[top['part']], anims, age)
    return sc.img

def preview(textures):
    sp = REF_ROOT + '/assets/minecraft/textures/entity/player/wide/steve.png'
    steve = Image.open(sp).convert('RGBA') if os.path.exists(sp) else Image.new('RGBA', (64, 64), (200, 150, 120, 255))
    frames = []
    for f in range(30):
        age = f * 6
        g = Image.new('RGBA', (4 * 230 + 50, 380), (30, 26, 48, 255))
        for i, (mat, yaw) in enumerate((('netherite', -30), ('netherite', 150), ('diamond', -30), ('diamond', 150))):
            g.alpha_composite(render(mat, textures[mat], steve, age, yaw), (10 + i * 240 + (10 if i >= 2 else 0), 10))
        frames.append(g)
    os.makedirs(PREVIEWS, exist_ok=True)
    big = [fr.resize((fr.width * 2, fr.height * 2), Image.NEAREST).convert('RGB') for fr in frames]
    big[0].save(PREVIEWS + '/celestial.png')
    small = [fr.convert('RGB') for fr in frames]
    small[0].save(PREVIEWS + '/celestial.gif', save_all=True, append_images=small[1:], duration=300, loop=0)

if __name__ == '__main__':
    tx = build()
    preview(tx)
    print('celestial ok')
