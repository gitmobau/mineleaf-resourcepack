# Aurora EMF: optional add-on for Entity Model Features + Entity Texture Features (Fabric, MC 26.3).
#   python3 -I aurora/scripts/emf.py        (run build.py / gear.py first: it reads Aurora Pack's textures)
# Writes packs/Aurora EMF/ (100% generated) and previews/preview_emf.png.
#
# What it adds on top of Aurora Pack (activate ABOVE it):
#   * 3D shape for the netherite "galactic robe": flared skirt (leggings model), bell sleeves (chestplate
#     model) and a curled hood point (helmet model), as EMF .jem variants that are only selected when the
#     wearer has the matching netherite piece (ETF "nbt" property on the equipment slot).
#   * ETF emissive maps (suffix _e) so the robe trims, crystal clasp, stars, cloak hem and the diamond
#     crystal highlights glow in the dark.
# Every format detail is checked against the EMF/ETF sources (see aurora/emf/README.md).
import os, sys, json, math, shutil
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from gear import galaxy_px, trim, mix, C, cyc, hsv, box_faces, VIVID, P, WHITE   # noqa: E402

RP = os.environ.get('AURORA_RP', os.path.join(ROOT, 'packs'))
PREVIEWS = os.environ.get('AURORA_PREVIEWS', os.path.join(ROOT, 'previews'))
MAIN = os.path.join(RP, 'Aurora Pack')
OUT = os.path.join(RP, 'Aurora EMF')
MC = 'assets/minecraft/'
EQ = 'textures/entity/equipment/'
FLARE_TEX = EQ + 'humanoid/aurora_robe_flare'          # texture of the sleeve + hood boxes (64x32)
CEM = MC + 'optifine/cem/'

def main_tex(rel):
    p = os.path.join(MAIN, MC, rel + '.png')
    if not os.path.exists(p):
        sys.exit('Falta %s: ejecuta antes build.py (o gear.py) para generar Aurora Pack' % p)
    return Image.open(p).convert('RGBA')

def save_png(im, rel):
    p = os.path.join(OUT, MC, rel + '.png')
    os.makedirs(os.path.dirname(p), exist_ok=True)
    im.save(p, optimize=True)

WRITTEN_JSON = []
def save_json(obj, rel):
    p = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w') as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write('\n')
    WRITTEN_JSON.append(p)

def save_text(text, rel):
    p = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w') as f:
        f.write(text)

# ================================================================== textures
G = lambda x, y, s=4: galaxy_px(x, y, seed=s)
DIM = lambda c, f=0.7: tuple(q * f for q in c[:3])

class Painter:
    """paints a texture and records which pixels glow (emissive map, ETF _e)"""
    def __init__(self, base):
        self.im = base.copy()
        self.glow = Image.new('RGBA', base.size)

    def px(self, x, y, c, glow=0):
        self.im.putpixel((x, y), C(c[:3]))
        if glow:
            self.glow.putpixel((x, y), C(c[:3], glow))

    def box(self, u, v, w, h, d, fn):
        """fn(face, i, j, w, h, X, Y) -> (rgb, glow_alpha) or None, over the vanilla box-UV layout"""
        for face, (x0, y0, fw, fh) in box_faces(u, v, w, h, d).items():
            for j in range(fh):
                for i in range(fw):
                    r = fn(face, i, j, fw, fh, x0 + i, y0 + j)
                    if r is not None:
                        self.px(x0 + i, y0 + j, r[0], r[1])

# Skirt fabric lives in the free top band of humanoid_leggings/netherite.png (the leggings model has no
# head, so vanilla never samples rows 0-15 there; the band is safe even without EMF).
# Both regions are laid out for boxes with depth 1 and height 12 at any width <= 10:
#   row 0      : top/bottom faces of the panel -> glowing waist band / hem edge
#   rows 1..12 : side faces, galaxy with a dotted line and a 2-row glowing hem
# Region F additionally carries the robe's front-opening trim in columns 5-6 (centre of a 10-wide panel,
# inner edge of the two 5-wide half panels used by the per-leg variant).
SKIRT_F = (0, 0)      # front panels
SKIRT_P = (22, 0)     # back + side panels
SKIRT_W = 22          # region width (box UV footprint of a 10x12x1 box)
SKIRT_H = 13

def paint_skirt(pt, u0, v0, front):
    for y in range(SKIRT_H):
        for x in range(SKIRT_W):
            X, Y = u0 + x, v0 + y
            if y == 0:
                pt.px(X, Y, trim(0.05 + x / 30), 230)
                continue
            j = y - 1                                  # 0..11 down the panel
            if j >= 10:
                pt.px(X, Y, trim(0.05 + x / 24 + j * 0.02), 255)          # hem
            elif front and x in (5, 6) and j < 10:
                pt.px(X, Y, trim(0.55 + j / 40), 255)                     # front opening
            elif j == 9 and (x + X) % 2 == 0:
                pt.px(X, Y, mix(G(X, Y + 40), WHITE, 0.5), 150)            # dotted line
            else:
                pt.px(X, Y, G(X, Y + 40))

# Sleeves + hood point use their own 64x32 texture, bound per part with the .jem "texture" field.
SLEEVE_A = (0, 0, 7, 4, 8)     # u, v, w, h, d  upper bell
SLEEVE_B = (0, 12, 8, 3, 10)   # wide cuff (flares outwards/front/back, flush on the body side)
HOOD = [(32, 0, 6, 4, 4), (46, 8, 4, 3, 3), (52, 0, 2, 3, 2), (60, 0, 1, 1, 1)]

def flare_texture():
    pt = Painter(Image.new('RGBA', (64, 32)))
    u, v, w, h, d = SLEEVE_A
    def sleeve_a(face, i, j, fw, fh, X, Y):
        if face in ('top', 'bottom'):
            return DIM(G(X, Y, 6)), 0
        if j == fh - 1 and (i + X) % 2 == 0:
            return mix(G(X, Y, 6), WHITE, 0.45), 140
        return G(X, Y, 6), 0
    pt.box(u, v, w, h, d, sleeve_a)
    u, v, w, h, d = SLEEVE_B
    def sleeve_b(face, i, j, fw, fh, X, Y):
        if face == 'bottom':                          # seen from below: trim ring, dark inside
            ring = i in (0, fw - 1) or j in (0, fh - 1)
            return (trim(0.1 + (i + j) / 40), 255) if ring else (DIM(G(X, Y, 6), 0.5), 0)
        if face == 'top':
            return DIM(G(X, Y, 6)), 0
        if j == fh - 1:
            return trim(0.35 + i / 30), 255
        if j == 0 and face in ('front', 'back', 'left', 'right'):
            return mix(G(X, Y, 6), trim(0.6 + i / 40), 0.35), 0
        return G(X, Y, 6), 0
    pt.box(u, v, w, h, d, sleeve_b)
    for k, (u, v, w, h, d) in enumerate(HOOD):
        last = k == len(HOOD) - 1
        def hood(face, i, j, fw, fh, X, Y, k=k, last=last):
            if last:
                return mix(trim(0.7), WHITE, 0.35), 255           # glowing tassel
            if face not in ('top', 'bottom') and j == fh - 1:
                return trim(0.15 + k * 0.2 + i / 30), 255         # ring at the base of each segment
            return G(X, Y, 8), 0
        pt.box(u, v, w, h, d, hood)
    return pt

def emissive_by_colour(im, star_alpha=220, skip=None):
    """glow map from a robe texture: aurora trims (bright + saturated) and white stars / crystal clasp"""
    out = Image.new('RGBA', im.size)
    for y in range(im.height):
        for x in range(im.width):
            p = im.getpixel((x, y))
            if p[3] < 128 or (skip and skip(x, y)):
                continue
            _, s, v = hsv(p)
            if v > 0.93 and s > 0.22:
                out.putpixel((x, y), p[:3] + (255,))
            elif v > 0.96 and s < 0.12:
                out.putpixel((x, y), p[:3] + (star_alpha,))
    return out

def emissive_diamond(im, alpha=110):
    """subtle: only the brightest crystal facets, half transparent (ETF DULL mode blends alpha)"""
    out = Image.new('RGBA', im.size)
    for y in range(im.height):
        for x in range(im.width):
            p = im.getpixel((x, y))
            if p[3] < 128:
                continue
            _, s, v = hsv(p)
            if v > 0.9 and s < 0.45:
                out.putpixel((x, y), C(mix(p, WHITE, 0.2), alpha))
    return out

def merge_glow(a, b):
    out = a.copy()
    out.alpha_composite(b)
    return out

# ================================================================== model tree -> .jem
# Nodes are written in vanilla model space (pixels, +y down, -z = front, rotations in radians, applied
# Z*Y*X like ModelPart.translateAndRotate). to_jem() converts to the OptiFine/EMF format with
# invertAxis "xy": translate = (-x, -y, z), rotate = (-rx, -ry, rz) in degrees and box coordinates
# [-(mx+w), -(my+h), mz, w, h, d] (the inversion EMFPartData/EMFBoxData.prepare() undo on load).
def node(nid, offset=(0, 0, 0), rot=(0, 0, 0), boxes=(), children=(), tex=None, mirror=False):
    return dict(id=nid, offset=tuple(offset), rot=tuple(rot), boxes=list(boxes), children=list(children),
                tex=tex, mirror=mirror)

def bx(uv, mn, size):
    return dict(uv=uv, min=tuple(mn), size=tuple(size))

def r6(x):
    x = round(x, 4)
    return int(x) if x == int(x) else x

def to_jem_part(n):
    o, r = n['offset'], n['rot']
    d = {"id": n['id'], "invertAxis": "xy", "translate": [r6(-o[0]), r6(-o[1]), r6(o[2])]}
    if any(r):
        d["rotate"] = [r6(-math.degrees(r[0])), r6(-math.degrees(r[1])), r6(math.degrees(r[2]))]
    if n['tex']:
        d["texture"] = n['tex'][0]
        d["textureSize"] = list(n['tex'][1])
    if n['mirror']:
        d["mirrorTexture"] = "u"
    if n['boxes']:
        d["boxes"] = [{"textureOffset": list(b['uv']),
                       "coordinates": [r6(-(b['min'][0] + b['size'][0])), r6(-(b['min'][1] + b['size'][1])),
                                       r6(b['min'][2])] + [r6(s) for s in b['size']]} for b in n['boxes']]
    if n['children']:
        d["submodels"] = [to_jem_part(c) for c in n['children']]
    return d

TOP_ORIGIN = (0, 24, 0)   # OptiFine convention: top-level submodels are placed in "Blockbench space"

def top(part, pivot, children, anims=None):
    """jem top-level entry attached (attach=true keeps the vanilla armour box) to vanilla part `part`
    whose default pivot is `pivot`. Children are given with ABSOLUTE rest offsets (model space)."""
    kids = []
    for c in children:
        c = dict(c)
        c['offset'] = tuple(c['offset'][i] - TOP_ORIGIN[i] for i in range(3))
        kids.append(c)
    n = node('aurora_' + part, offset=tuple(TOP_ORIGIN[i] - pivot[i] for i in range(3)), children=kids)
    n['part'] = part
    n['pivot'] = pivot
    n['anims'] = anims
    return n

def to_jem(tops):
    models = []
    for t in tops:
        d = {"part": t['part']}
        d.update(to_jem_part(t))
        d["attach"] = True
        if t.get('anims'):
            d["animations"] = [dict((k, v[0]) for k, v in t['anims'].items())]
        models.append(d)
    return {"credit": "Aurora EMF (generated by aurora/scripts/emf.py)", "textureSize": [64, 32], "models": models}

# ----- wearers (pivots from 26.3 HumanoidModel / ArmorStandArmorModel / ZombieVillagerModel armour meshes)
STD = dict(head=(0, 0, 0), body=(0, 0, 0), right_arm=(-5, 2, 0), left_arm=(5, 2, 0),
           right_leg=(-1.9, 12, 0), left_leg=(1.9, 12, 0), head_dy=0)
def wearer(**kw):
    w = dict(STD); w.update(kw); return w
WEARERS = {
    'player': wearer(anim=True), 'player_slim': wearer(anim=True),
    'armor_stand': wearer(head=(0, 1, 0), right_leg=(-1.9, 11, 0), left_leg=(1.9, 11, 0)),
    'zombie_villager': wearer(right_leg=(-2, 12, 0), left_leg=(2, 12, 0), head_dy=-2),
}
for m in ('zombie', 'husk', 'drowned', 'skeleton', 'stray', 'wither_skeleton', 'bogged', 'parched', 'giant',
          'piglin', 'piglin_brute', 'zombified_piglin'):
    WEARERS[m] = wearer()

FLARE = ('textures/entity/equipment/humanoid/aurora_robe_flare', (64, 32))
FLARE_REF = (FLARE_TEX, (64, 32))
FLARE_ANGLE = 0.12            # rest flare of the skirt panels (rad)

# Skirt animation (player only). EMF writes these straight into ModelPart.xRot (model space, radians);
# the vanilla leg/body rotations are already set by setupAnim when EMF evaluates them.
# Each entry: (EMF expression, python twin used by the preview renderer).
SKIRT_ANIMS = {
    "skirt_front.rx": ("min(0, min(left_leg.rx, right_leg.rx)) - body.rx - 0.12",
                       lambda p: min(0, min(p['left_leg'], p['right_leg'])) - p['body'] - 0.12),
    "skirt_back.rx": ("max(0, max(left_leg.rx, right_leg.rx)) - body.rx + 0.12",
                      lambda p: max(0, max(p['left_leg'], p['right_leg'])) - p['body'] + 0.12),
    "skirt_hinge_l.rx": ("(left_leg.rx + right_leg.rx) * 0.5 - body.rx",
                         lambda p: (p['left_leg'] + p['right_leg']) * 0.5 - p['body']),
    "skirt_hinge_r.rx": ("(left_leg.rx + right_leg.rx) * 0.5 - body.rx",
                         lambda p: (p['left_leg'] + p['right_leg']) * 0.5 - p['body']),
}

def panel(nid, pivot, w, uv, rot):
    """1px thick skirt panel hanging 12px from its top-centre pivot"""
    return node(nid, pivot, rot, [bx(uv, (-w / 2, 0, -0.5), (w, 12, 1))])

def leggings_animated(wr):
    a = FLARE_ANGLE
    side = lambda s: node('skirt_hinge_' + s, (4.75 if s == 'l' else -4.75, 11, 0), children=[
        node('skirt_' + s, (0, 0, 0), (-a, -math.pi / 2 if s == 'l' else math.pi / 2, 0),
             [bx(SKIRT_P, (-3.5, 0, -0.5), (7, 12, 1))])])
    kids = [panel('skirt_front', (0, 11, -2.75), 10, SKIRT_F, (-a, 0, 0)),
            panel('skirt_back', (0, 11, 2.75), 10, SKIRT_P, (a, 0, 0)),
            side('l'), side('r')]
    return [top('body', wr['body'], kids, anims=SKIRT_ANIMS)]

def leggings_static(wr):
    """no animations (keeps EMF's copy of the base model pose, e.g. Fresh Animations mobs):
    half panels ride on each leg"""
    a = FLARE_ANGLE
    out = []
    for s, sign in (('r', -1), ('l', 1)):
        leg = 'right_leg' if s == 'r' else 'left_leg'
        kids = [panel('skirt_front_' + s, (2.5 * sign, 11, -2.75), 5,
                      SKIRT_F if s == 'r' else (SKIRT_F[0] + 5, SKIRT_F[1]), (-a, 0, 0)),
                panel('skirt_back_' + s, (2.5 * sign, 11, 2.75), 5, SKIRT_P, (a, 0, 0)),
                node('skirt_side_' + s, (4.75 * sign, 11, 0), (-a, sign * -math.pi / 2, 0),
                     [bx(SKIRT_P, (-3.5, 0, -0.5), (7, 12, 1))])]
        out.append(top(leg, wr[leg], kids))
    return out

def chestplate(wr):
    out = []
    for s, sign in (('r', -1), ('l', 1)):
        arm = 'right_arm' if s == 'r' else 'left_arm'
        # 1.0-inflated arm box spans abs x -9..-3 (right). The bell only grows outwards, to the front and
        # to the back; its inner face stays flush with the arm so it does not cut into the torso/skirt.
        inner = 3 * sign
        def xr(w):
            return (inner - w, w) if sign < 0 else (inner, w)
        (ax, aw), (bx_, bw) = xr(7), xr(8)
        kids = [node('sleeve_bell_' + s, (0, 7, 0), boxes=[bx(SLEEVE_A[:2], (ax, 0, -4), (aw, 4, 8))], tex=FLARE_REF),
                node('sleeve_cuff_' + s, (0, 11, 0), boxes=[bx(SLEEVE_B[:2], (bx_, 0, -5), (bw, 3, 10))], tex=FLARE_REF)]
        out.append(top(arm, wr[arm], kids))
    return out

def helmet(wr):
    hx, hy, hz = wr['head']
    dy = wr['head_dy']
    (u0, v0, *_), (u1, v1, *_), (u2, v2, *_), (u3, v3, *_) = HOOD
    tassel = node('hood_tassel', (0, -3, 0), (-0.35, 0, 0), [bx((u3, v3), (-0.5, -1, -0.5), (1, 1, 1))], tex=FLARE_REF)
    seg3 = node('hood_tip', (0, -3, 0), (-0.6, 0, 0), [bx((u2, v2), (-1, -3, -1), (2, 3, 2))], [tassel], tex=FLARE_REF)
    seg2 = node('hood_mid', (0, -4, 0), (-0.5, 0, 0), [bx((u1, v1), (-2, -3, -1.5), (4, 3, 3))], [seg3], tex=FLARE_REF)
    seg1 = node('hood_base', (hx, hy - 8.5 + dy, hz + 3.5), (-0.6, 0, 0), [bx((u0, v0), (-3, -4, -2), (6, 4, 4))],
                [seg2], tex=FLARE_REF)
    return [top('head', wr['head'], [seg1])]

PIECES = {   # model suffix -> (equipment slot in entity NBT, netherite item, builder)
    'helmet': ('head', 'minecraft:netherite_helmet', helmet),
    'chestplate': ('chest', 'minecraft:netherite_chestplate', chestplate),
    'leggings': ('legs', 'minecraft:netherite_leggings', None),
}

def properties_text(name, slot, item):
    return ('# Aurora EMF: use %s2.jem only while the wearer has %s in the "%s" slot.\n'
            '# ETF "nbt" property, read from the client entity NBT (LivingEntity saves "equipment").\n'
            '# Entities that match no rule keep the vanilla armour model (EMF maps variant 1 to vanilla\n'
            '# when there is no %s.jem).\n'
            'models.1=2\n'
            'nbt.1.equipment.%s.id=%s\n') % (name, item, slot, name, slot, item)

# ================================================================== tiny software renderer (preview)
def rot_m(rx, ry, rz):
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    Rx = ((1, 0, 0), (0, cx, -sx), (0, sx, cx))
    Ry = ((cy, 0, sy), (0, 1, 0), (-sy, 0, cy))
    Rz = ((cz, -sz, 0), (sz, cz, 0), (0, 0, 1))
    mm = lambda A, B: tuple(tuple(sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)) for i in range(3))
    return mm(Rz, mm(Ry, Rx))

def apply(M, t, p):
    return tuple(sum(M[i][k] * p[k] for k in range(3)) + t[i] for i in range(3))

def compose(M, t, off, rot):
    R = rot_m(*rot)
    M2 = tuple(tuple(sum(M[i][k] * R[k][j] for k in range(3)) for j in range(3)) for i in range(3))
    return M2, apply(M, t, off)

def cube_quads(u, v, mn, size, grow, mirror):
    """vanilla ModelPart.Cube: 6 faces as (4 corners, (u0,v0,u1,v1)) with the same vertex/UV pairing"""
    w, h, d = size
    x0, y0, z0 = mn[0] - grow, mn[1] - grow, mn[2] - grow
    x1, y1, z1 = mn[0] + w + grow, mn[1] + h + grow, mn[2] + d + grow
    if mirror:
        x0, x1 = x1, x0
    t0, t1, t2, t3 = (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)
    l0, l1, l2, l3 = (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)
    U0, U1, U2, U22, U3, U4 = u, u + d, u + d + w, u + d + w + w, u + d + w + d, u + d + w + d + w
    V0, V1, V2 = v, v + d, v + d + h
    faces = [((l1, l0, t0, t1), (U1, V0, U2, V1)), ((t2, t3, l3, l2), (U2, V1, U22, V0)),
             ((t0, l0, l3, t3), (U0, V1, U1, V2)), ((t1, t0, t3, t2), (U1, V1, U2, V2)),
             ((l1, t1, t2, l2), (U2, V1, U3, V2)), ((l0, l1, l2, l3), (U3, V1, U4, V2))]
    out = []
    for verts, (a, b, c, e) in faces:
        # Polygon: v0->(u1,v0) v1->(u0,v0) v2->(u0,v1) v3->(u1,v1)
        out.append((verts, ((c, b), (a, b), (a, e), (c, e))))
    return out

class Scene:
    def __init__(self):
        self.quads = []   # (world corners, uv corners, texture)

    def add_cube(self, M, t, u, v, mn, size, tex, grow=0.0, mirror=False):
        for verts, uvs in cube_quads(u, v, mn, size, grow, mirror):
            self.quads.append(([apply(M, t, p) for p in verts], uvs, tex))

    def add_node(self, n, M, t, pose, texmap, default_tex):
        rot = n['rot']
        if n['id'] in pose:
            rot = (pose[n['id']], rot[1], rot[2])
        M2, t2 = compose(M, t, n['offset'], rot)
        tex = texmap[n['tex'][0]] if n['tex'] else default_tex
        for b in n['boxes']:
            self.add_cube(M2, t2, b['uv'][0], b['uv'][1], b['min'], b['size'], tex, mirror=n['mirror'])
        for c in n['children']:
            self.add_node(c, M2, t2, pose, texmap, default_tex)

    def render(self, view, scale, size, night=False, glowmap=None, bg=(0, 0, 0, 0)):
        img = Image.new('RGBA', size, bg)
        dr = ImageDraw.Draw(img)
        cx, cy = size[0] / 2, 4 + 15 * scale       # model y = -15 (hood tip) at the top edge
        def proj(p):
            if view == 'front':
                return p[0], p[1], p[2]
            if view == 'back':
                return -p[0], p[1], -p[2]
            return -p[2], p[1], p[0]             # 'side': seen from the entity's right (-x)
        polys = []
        light = (0.35, -0.75, -0.55)
        for verts, uvs, tex in self.quads:
            im = tex
            e1 = [verts[1][k] - verts[0][k] for k in range(3)]
            e2 = [verts[3][k] - verts[0][k] for k in range(3)]
            nrm = (e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0])
            ln = math.sqrt(sum(q * q for q in nrm)) or 1
            shade = 0.72 + 0.28 * abs(sum(nrm[k] * light[k] for k in range(3)) / ln)
            u0 = min(q[0] for q in uvs); u1 = max(q[0] for q in uvs)
            v0 = min(q[1] for q in uvs); v1 = max(q[1] for q in uvs)
            nu, nv = int(round(u1 - u0)), int(round(v1 - v0))
            if nu <= 0 or nv <= 0:
                continue
            # bilinear map texel grid -> quad (corner order matches uvs)
            def at(su, sv):
                # su, sv in UV space -> world point
                fu = (su - uvs[1][0]) / (uvs[0][0] - uvs[1][0])   # 0 at corner1(u0), 1 at corner0(u1)
                fv = (sv - uvs[1][1]) / (uvs[2][1] - uvs[1][1])   # 0 at top, 1 at bottom
                top_ = [verts[1][k] + (verts[0][k] - verts[1][k]) * fu for k in range(3)]
                bot_ = [verts[2][k] + (verts[3][k] - verts[2][k]) * fu for k in range(3)]
                return [top_[k] + (bot_[k] - top_[k]) * fv for k in range(3)]
            for j in range(nv):
                for i in range(nu):
                    tu, tv = int(u0) + i, int(v0) + j
                    if not (0 <= tu < im.width and 0 <= tv < im.height):
                        continue
                    c = im.getpixel((tu, tv))
                    if c[3] < 128:
                        continue
                    corners = [at(u0 + i + a, v0 + j + b) for a, b in ((0, 0), (1, 0), (1, 1), (0, 1))]
                    pr = [proj(p) for p in corners]
                    depth = sum(p[2] for p in pr) / 4
                    col = tuple(q * shade for q in c[:3])
                    if night:
                        col = tuple(q * 0.28 for q in col)
                        g = glowmap.get(id(im)) if glowmap else None
                        if g is not None:
                            e = g.getpixel((tu, tv))
                            if e[3]:
                                col = mix(col, e[:3], e[3] / 255)
                    polys.append((depth, [(cx + p[0] * scale, cy + p[1] * scale) for p in pr], C(col)))
        polys.sort(key=lambda q: -q[0])
        for _, pts, col in polys:
            dr.polygon(pts, fill=col)
        return img

def vanilla_armor(scene, pose, hum, leg, wr=STD):
    """the vanilla armour boxes of the 4 pieces (26.3 deformations: outer 1.0, inner 0.5, legs -0.1)"""
    I = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
    def part(name, piv, rx):
        return compose(I, (0, 0, 0), piv, (rx, 0, 0))
    M, t = part('head', wr['head'], 0)
    scene.add_cube(M, t, 0, 0, (-4, -8, -4), (8, 8, 8), hum, 1.0)
    M, t = part('body', wr['body'], pose['body'])
    scene.add_cube(M, t, 16, 16, (-4, 0, -2), (8, 12, 4), hum, 1.0)
    scene.add_cube(M, t, 16, 16, (-4, 0, -2), (8, 12, 4), leg, 0.5)
    M, t = part('right_arm', wr['right_arm'], pose['right_arm'])
    scene.add_cube(M, t, 40, 16, (-3, -2, -2), (4, 12, 4), hum, 1.0)
    M, t = part('left_arm', wr['left_arm'], pose['left_arm'])
    scene.add_cube(M, t, 40, 16, (-1, -2, -2), (4, 12, 4), hum, 1.0, mirror=True)
    for s in ('right_leg', 'left_leg'):
        M, t = part(s, wr[s], pose[s])
        scene.add_cube(M, t, 0, 16, (-2, 0, -2), (4, 12, 4), leg, 0.4, mirror=(s == 'left_leg'))
        scene.add_cube(M, t, 0, 16, (-2, 0, -2), (4, 12, 4), hum, 0.9, mirror=(s == 'left_leg'))

def robe_scene(pose, tops, hum, leg, flare, wr=STD):
    sc = Scene()
    vanilla_armor(sc, pose, hum, leg, wr)
    I = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
    anim_vals = {}
    for t_ in tops:
        if t_.get('anims'):
            for k, (_, fn) in t_['anims'].items():
                anim_vals[k.split('.')[0]] = fn(pose)
    for t_ in tops:
        M, t = compose(I, (0, 0, 0), t_['pivot'], (pose.get(t_['part'], 0), 0, 0))
        sc.add_node(t_, M, t, anim_vals, {FLARE_TEX: flare}, leg)
    return sc

# ================================================================== build
def build():
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(OUT)

    # --- textures
    hum = main_tex(EQ + 'humanoid/netherite')
    leg_main = main_tex(EQ + 'humanoid_leggings/netherite')
    if leg_main.crop((0, 0, 64, 16)).getbbox() is not None:
        sys.exit('humanoid_leggings/netherite.png ya usa la banda superior: mueve SKIRT_F/SKIRT_P')
    lp = Painter(leg_main)
    paint_skirt(lp, *SKIRT_F, front=True)
    paint_skirt(lp, *SKIRT_P, front=False)
    leg = lp.im
    save_png(leg, EQ + 'humanoid_leggings/netherite')
    fp = flare_texture()
    flare = fp.im
    save_png(flare, FLARE_TEX)
    save_png(fp.glow, FLARE_TEX + '_e')

    glow = {}
    glow['hum'] = emissive_by_colour(hum)
    save_png(glow['hum'], EQ + 'humanoid/netherite_e')
    glow['leg'] = merge_glow(emissive_by_colour(leg_main), lp.glow)
    save_png(glow['leg'], EQ + 'humanoid_leggings/netherite_e')
    cloak = main_tex(EQ + 'wings/aurora_cloak')
    glow['cloak'] = emissive_by_colour(cloak, star_alpha=200)
    save_png(glow['cloak'], EQ + 'wings/aurora_cloak_e')
    dia = {}
    for layer in ('humanoid', 'humanoid_leggings'):
        dia[layer] = main_tex(EQ + layer + '/diamond')
        glow['dia_' + layer] = emissive_diamond(dia[layer])
        save_png(glow['dia_' + layer], EQ + layer + '/diamond_e')
    glow['flare'] = fp.glow

    # --- models: <wearer>_<piece>.properties + <wearer>_<piece>2.jem (no base .jem -> variant 1 = vanilla)
    jems = {}
    for name, wr in sorted(WEARERS.items()):
        for piece, (slot, item, fn) in PIECES.items():
            if piece == 'leggings':
                fn = leggings_animated if wr.get('anim') else leggings_static
            model = '%s_%s' % (name, piece)
            tops = fn(wr)
            jem = to_jem(tops)
            save_json(jem, CEM + model + '2.jem')
            save_text(properties_text(model, slot, item), CEM + model + '.properties')
            jems[model] = (jem, tops)

    # --- pack meta + icon
    save_json({"pack": {
        "description": ["", {"text": "Aurora EMF ", "color": "#B9B9F8"},
                        {"text": "· túnica 3D y brillo · requiere EMF + ETF", "color": "#F8B0EA"}],
        "min_format": 84, "max_format": 97}}, 'pack.mcmeta')

    pose_stand = dict(head=0, body=0, right_arm=0, left_arm=0, right_leg=0, left_leg=0)
    pose_walk = dict(head=0, body=0, right_arm=-0.55, left_arm=0.55, right_leg=0.6, left_leg=-0.6)
    pose_ride = dict(head=0, body=0, right_arm=-0.6, left_arm=-0.6, right_leg=-1.4137, left_leg=-1.4137)
    tops_player = jems['player_helmet'][1] + jems['player_chestplate'][1] + jems['player_leggings'][1]
    tops_mob = jems['zombie_helmet'][1] + jems['zombie_chestplate'][1] + jems['zombie_leggings'][1]

    icon = Image.new('RGBA', (128, 128))
    for y in range(128):
        for x in range(128):
            c = mix((20, 16, 38), cyc((x + y) / 256 + 0.05 * math.sin(x / 9)), 0.35 + 0.35 * (1 - y / 128))
            icon.putpixel((x, y), C(c))
    fig = robe_scene(pose_walk, tops_player, hum, leg, flare).render('front', 3.0, (128, 128))
    icon.alpha_composite(fig, (0, 2))
    icon.save(os.path.join(OUT, 'pack.png'), optimize=True)

    # --- preview sheet
    gm = {id(hum): glow['hum'], id(leg): glow['leg'], id(flare): glow['flare']}
    W, H = 1180, 820
    sheet = Image.new('RGBA', (W, H), (60, 52, 84, 255))
    dr = ImageDraw.Draw(sheet)
    renders = [('frente, quieto', robe_scene(pose_stand, tops_player, hum, leg, flare), 'front', False),
               ('lado, andando', robe_scene(pose_walk, tops_player, hum, leg, flare), 'side', False),
               ('frente, andando', robe_scene(pose_walk, tops_player, hum, leg, flare), 'front', False),
               ('lado, montando', robe_scene(pose_ride, tops_player, hum, leg, flare), 'side', False),
               ('noche (emisivo ETF)', robe_scene(pose_walk, tops_player, hum, leg, flare), 'front', True),
               ('mobs: falda en piernas', robe_scene(pose_walk, tops_mob, hum, leg, flare), 'side', False)]
    for i, (label, sc, view, night) in enumerate(renders):
        x0 = 10 + i * 195
        bg = (14, 10, 30, 255) if night else (40, 34, 60, 255)
        im = sc.render(view, 5.2, (185, 260), night=night, glowmap=gm, bg=bg)
        sheet.alpha_composite(im, (x0, 26))
        dr.text((x0 + 4, 8), label, fill=(240, 230, 255))
    def flat(img, scale, pos, label, dark=False):
        bgc = (10, 8, 20, 255) if dark else (40, 34, 60, 255)
        b = Image.new('RGBA', (img.width * scale, img.height * scale), bgc)
        b.alpha_composite(img.resize(b.size, Image.NEAREST))
        sheet.alpha_composite(b, pos)
        dr.text((pos[0], pos[1] - 14), label, fill=(240, 230, 255))
    flat(leg, 4, (10, 320), 'leggings/netherite.png + falda')
    flat(glow['leg'], 4, (280, 320), 'leggings/netherite_e.png', True)
    flat(flare, 4, (550, 320), 'aurora_robe_flare.png (mangas, capucha)')
    flat(glow['flare'], 4, (820, 320), 'aurora_robe_flare_e.png', True)
    flat(hum, 4, (10, 480), 'humanoid/netherite.png (base)')
    flat(glow['hum'], 4, (280, 480), 'humanoid/netherite_e.png', True)
    flat(cloak.crop((0, 0, 64, 32)), 4, (550, 480), 'wings/aurora_cloak.png (base)')
    flat(glow['cloak'], 4, (820, 480), 'wings/aurora_cloak_e.png', True)
    flat(dia['humanoid'], 4, (10, 640), 'humanoid/diamond.png (base)')
    flat(glow['dia_humanoid'], 4, (280, 640), 'humanoid/diamond_e.png (alfa 110)', True)
    flat(dia['humanoid_leggings'], 4, (550, 640), 'leggings/diamond.png (base)')
    flat(glow['dia_humanoid_leggings'], 4, (820, 640), 'leggings/diamond_e.png', True)
    os.makedirs(PREVIEWS, exist_ok=True)
    sheet.convert('RGB').save(os.path.join(PREVIEWS, 'preview_emf.png'), optimize=True)
    return jems

# ================================================================== validation
def validate(jems):
    errors = []
    for p in WRITTEN_JSON:
        try:
            json.load(open(p))
        except Exception as e:
            errors.append('JSON roto %s: %s' % (p, e))
    def tex_exists(path):
        rel = MC + path + ('' if path.endswith('.png') else '.png')
        return os.path.exists(os.path.join(OUT, rel)) or os.path.exists(os.path.join(MAIN, rel))
    known_parts = {'head', 'headwear', 'body', 'left_arm', 'right_arm', 'left_leg', 'right_leg'}  # EMF genericNonPlayerBiped
    leg_regions = [(SKIRT_F[0], SKIRT_F[1], SKIRT_F[0] + SKIRT_W, SKIRT_F[1] + SKIRT_H),
                   (SKIRT_P[0], SKIRT_P[1], SKIRT_P[0] + SKIRT_W, SKIRT_P[1] + SKIRT_H)]
    def walk(d, tsize, tex, where):
        tsize = d.get('textureSize', tsize)
        own = d.get('texture')
        if own and not tex_exists(own):
            errors.append('%s: textura %s no existe' % (where, own))
        for b in d.get('boxes', []):
            u, v = b['textureOffset']
            w, h, dd = b['coordinates'][3:]
            fw, fh = 2 * (dd + w), dd + h
            if u + fw > tsize[0] or v + fh > tsize[1]:
                errors.append('%s: UV fuera de la textura %s' % (where, b))
            if not own:   # samples the vanilla-bound leggings texture: must stay inside the painted band
                if not any(u >= r[0] and v >= r[1] and u + fw <= r[2] and v + fh <= r[3] for r in leg_regions):
                    errors.append('%s: UV fuera de las regiones de falda %s' % (where, b))
        for s in d.get('submodels', []):
            walk(s, tsize, own, where + '/' + s['id'])
    for model, (jem, _) in jems.items():
        ids = set()
        for m in jem['models']:
            if m['part'] not in known_parts:
                errors.append('%s: parte desconocida %s' % (model, m['part']))
            walk(m, jem['textureSize'], None, model + ':' + m['id'])
            def collect(d):
                ids.add(d['id']); [collect(s) for s in d.get('submodels', [])]
            collect(m)
            for anim in m.get('animations', []):
                for k in anim:
                    if k.split('.')[0] not in ids:
                        errors.append('%s: animación sobre id inexistente %s' % (model, k))
        if not model.startswith('player') and any(m.get('animations') for m in jem['models']):
            errors.append('%s: los mobs no deben llevar animaciones (EMF dejaría de copiar la pose)' % model)
        prop = os.path.join(OUT, CEM + model + '.properties')
        txt = open(prop).read()
        if 'models.1=2' not in txt or not os.path.exists(os.path.join(OUT, CEM + model + '2.jem')):
            errors.append('%s: properties/variante incoherentes' % model)
        if os.path.exists(os.path.join(OUT, CEM + model + '.jem')):
            errors.append('%s: no debe haber jem base (la variante 1 es la vanilla)' % model)
    # every _e has its base texture in this pack or in Aurora Pack, with the same size
    for base, dirs, files in os.walk(os.path.join(OUT, MC, 'textures')):
        for f in files:
            if f.endswith('_e.png'):
                rel = os.path.relpath(os.path.join(base, f[:-6] + '.png'), os.path.join(OUT, MC))
                src = os.path.join(OUT, MC, rel) if os.path.exists(os.path.join(OUT, MC, rel)) else os.path.join(MAIN, MC, rel)
                if not os.path.exists(src):
                    errors.append('emisivo sin base: ' + rel)
                elif Image.open(src).size != Image.open(os.path.join(base, f)).size:
                    errors.append('emisivo de tamaño distinto: ' + rel)
    return errors

if __name__ == '__main__':
    jems = build()
    errs = validate(jems)
    n_files = sum(len(f) for _, _, f in os.walk(OUT))
    for e in errs:
        print('ERROR', e)
    print('Aurora EMF: %d archivos, %d modelos, %d errores' % (n_files, len(jems), len(errs)))
    if errs:
        sys.exit(1)
    print('ok')
