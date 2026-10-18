# Aurora EMF: 3D netherite armour for Entity Model Features (+ Entity Texture Features, required by EMF).
# Optional pack; without the mods nothing changes.
#
# - Models are EMF "variant 2" of the per-slot armour models (helmet, chestplate, leggings, boots). The .properties
#   files pick variant 2 only while the entity wears that netherite piece (ETF "items=" rule); otherwise variant 1 =
#   vanilla model (EMF default when there is no base .jem). So diamond/iron/... armour keeps its vanilla shape.
# - Extra pieces are boxes attached to the vanilla parts ("attach": true keeps the vanilla armour boxes). Their faces use
#   per-face UVs pointing at material swatches that gear.py paints into texels no vanilla armour box ever samples.
# Box positions are written like EMF's own exporter: translate = (px, py - 24, -pz) and
# coordinates = (-mx - sx - px, -my - sy - (py - 24), mz + pz, sx, sy, sz) with invertAxis "xy", where p is the vanilla
# part pivot and m/s the box min/size in the vanilla part's local space (y down, front = -z).
import os, sys, json, math, shutil
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # build.py runs scripts with -I
from gear import EMF_SWATCHES

HOME = os.path.expanduser('~')
REF_ROOT = os.environ.get('AURORA_REF', HOME + '/ref63')
RP = os.environ.get('AURORA_RP', HOME + '/mnt/.minecraft/resourcepacks')
PACK = RP + '/Aurora EMF'
CEM = PACK + '/assets/minecraft/emf/cem/'
AURORA = RP + '/Aurora Pack/assets/minecraft/textures/'
PREVIEWS = os.environ.get('AURORA_PREVIEWS', PACK)

# vanilla part pivots (HumanoidModel / ElytraModel)
PIVOT = {'head': (0, 0, 0), 'body': (0, 0, 0), 'right_arm': (-5, 2, 0), 'left_arm': (5, 2, 0),
         'right_leg': (-1.9, 12, 0), 'left_leg': (1.9, 12, 0)}

# extra pieces: part -> [(min xyz, size xyz, swatch)] in the part's vanilla local space. Right-side pieces are written
# once; mirror() builds the left side (the right/left arm and leg boxes are mirror images around local x = 0).
def mirror(boxes):
    return [((-m[0] - s[0], m[1], m[2]), s, sw) for (m, s, sw) in boxes]

def sym(boxes):                      # piece on the entity's right (-x) plus its mirror on the left
    return boxes + mirror(boxes)

# helmet (outer armour, inflated by 1: head shell spans x/z -5..5, y -9..1). Kept light (2026-10 polish): a low
# two-step crest, three small feathers on each side, a small brow jewel and the brow band.
HELM = ([((-0.4, -10.1, -3.6), (0.8, 1.1, 7.4), 'trim'),          # crest, rising towards the back
         ((-0.4, -10.9, -0.6), (0.8, 0.8, 4.2), 'trim'),
         ((-1.2, -8.6, -5.3), (2.4, 1.8, 0.3), 'gold'),          # brow jewel in a gold setting
         ((-0.7, -8.2, -5.55), (1.4, 1.0, 0.3), 'gem2'),
         ((-5, -9.4, -5.3), (10, 0.6, 0.3), 'trim')]              # brow band
        + sym([((-5.5, -6.6, -1.6), (0.5, 1.2, 2.6), 'trim'),    # side wings: stepped feathers sweeping up and back
               ((-5.6, -8.0, -0.3), (0.6, 1.4, 2.6), 'trim'),
               ((-5.5, -9.5, 1.1), (0.5, 1.5, 2.2), 'trim')]))

# chestplate (body shell x -5..5, y -1..13, z -3..3): a small jewel, the collar and a slim spine (no shoulder blades)
CHEST = [((-1.3, 1.6, -3.35), (2.6, 2.6, 0.35), 'gold'), ((-0.8, 2.1, -3.7), (1.6, 1.6, 0.4), 'gem2'),   # chest jewel
         ((-4.6, -1.4, -3.4), (9.2, 0.8, 0.4), 'trim'), ((-4.6, -1.4, 3.0), (9.2, 0.8, 0.4), 'trim'),  # collar
         ((-0.4, 0.6, 3.0), (0.8, 9, 0.4), 'trimv')]                                                  # back spine

# pauldron on the right arm (arm shell x -4..2, y -3..11, z -3..3): a cap and one lame, close to the arm
PAULDRON = [((-4.35, -3.8, -3.25), (5.3, 0.9, 6.5), 'metal'),
            ((-4.75, -3.0, -3.5), (5.6, 1.4, 7.0), 'metal'),
            ((-4.8, -1.65, -3.55), (5.4, 0.4, 7.1), 'trim'),
            ((-5.1, -2.7, -0.45), (0.35, 0.9, 0.9), 'gem')]

# boots (leg shell x -3..3, y -1..13, z -3..3; the boot covers y 7..13)
BOOT = [((-2.6, 11.4, -3.45), (5.2, 1.6, 0.45), 'metal'),         # toe cap
        ((-3.4, 9.0, -1.2), (0.4, 1.3, 2.4), 'trim')]             # ankle wing on the outer side

OUTER = {'head': HELM, 'body': CHEST, 'right_arm': PAULDRON, 'left_arm': mirror(PAULDRON),
         'right_leg': BOOT, 'left_leg': mirror(BOOT)}

# leggings (inner armour, inflated by 0.5: body shell x -4.5..4.5 z -2.5..2.5, leg shell x/z -2.4..2.4 y -0.4..12.4).
# The belt sits a little higher than before (y 9.2..10.3): the thighs of a sitting player reach y 10, so a belt at the
# old 10..11.2 went through them in boats and minecarts.
BELT = [((-4.75, 9.2, -2.75), (9.5, 1.1, 5.5), 'trim'),           # belt wraps all the way round
        ((-1.1, 8.95, -3.0), (2.2, 1.6, 0.25), 'gold'), ((-0.55, 9.3, -3.2), (1.1, 0.9, 0.25), 'gem')]
TASSET = [((-2.4, -0.2, -2.85), (4.8, 2.6, 0.4), 'metal'),        # one lame over the thigh
          ((-2.4, 2.4, -2.9), (4.8, 0.4, 0.4), 'trim'),
          ((-1.5, 5.6, -2.8), (3.0, 1.8, 0.35), 'metal'),         # knee guard
          ((-0.4, 6.1, -3.0), (0.8, 0.8, 0.25), 'gem')]
INNER = {'body': BELT, 'right_leg': TASSET, 'left_leg': mirror(TASSET)}

def swatch_uv(name, w, h, d):
    """per-face UVs on a material swatch: a side of the face that is at least half the swatch stretches the whole
    swatch (outline included) so plates keep a crisp rim; thinner sides take a 1:1 strip just inside the top/left
    border, which shows the highlight row like a bevelled edge"""
    u0, v0, sw, sh = EMF_SWATCHES[name]
    def span(f, size):
        if f >= size / 2: return (0, size)
        a = min(1, (size - f) / 2)
        return (a, a + f)
    def r(fw, fh):
        a, b = span(fw, sw), span(fh, sh)
        return [round(u0 + a[0], 3), round(v0 + b[0], 3), round(u0 + a[1], 3), round(v0 + b[1], 3)]
    uv = {'uvNorth': r(w, h), 'uvSouth': r(w, h), 'uvEast': r(d, h), 'uvWest': r(d, h), 'uvUp': r(w, d), 'uvDown': r(w, d)}
    if name == 'metal' and h < 4:            # sides of a flat plate: highlight on top, outline underneath
        lu, lv, lw, lh = EMF_SWATCHES['lame']
        for k, fw in (('uvNorth', w), ('uvSouth', w), ('uvEast', d), ('uvWest', d)):
            a = (0, lw) if fw >= lw / 2 else ((lw - fw) / 2, (lw + fw) / 2)
            uv[k] = [round(lu + a[0], 3), lv, round(lu + a[1], 3), lv + lh]
    return uv

def cem_box(part, m, s, uv):
    px, py, pz = PIVOT[part]
    box = {'coordinates': [round(v, 4) for v in (-m[0] - s[0] - px, -m[1] - s[1] - (py - 24), m[2] + pz, s[0], s[1], s[2])]}
    box.update(uv if isinstance(uv, dict) else swatch_uv(uv, *s))
    return box

def cem_part(part, boxes, attach=True, pid=None):
    px, py, pz = PIVOT[part]
    return {'part': part, 'id': pid or 'aurora_' + part, 'attach': attach, 'invertAxis': 'xy',
            'translate': [px, py - 24, -pz], 'boxes': [cem_box(part, m, s, uv) for (m, s, uv) in boxes]}

def jem(pieces):
    return {'textureSize': [64, 32], 'models': [cem_part(p, b) for p, b in pieces.items()]}

def write(name, obj):
    os.makedirs(CEM, exist_ok=True)
    with open(CEM + name, 'w') as f:
        if name.endswith('.jem'): json.dump(obj, f, indent=2)
        else: f.write(obj)

# Since MC 1.21.9 the armour is one model per slot (layers player_helmet, player_chestplate, ...). EMF looks for
# "<mob>_<slot>.jem" and falls back to "<slot>.jem". The pack ships the exact player names (player_helmet,
# player_slim_helmet, ...) and the generic ones for every other biped. The old player_outer_armor / player_inner_armor names are ignored by EMF on 26.x.
PIECES = {   # slot file -> (parts, netherite item that switches it on)
    'helmet': ({'head': OUTER['head']}, 'netherite_helmet'),
    'chestplate': ({k: OUTER[k] for k in ('body', 'right_arm', 'left_arm')}, 'netherite_chestplate'),
    'leggings': (INNER, 'netherite_leggings'),
    'boots': ({k: OUTER[k] for k in ('right_leg', 'left_leg')}, 'netherite_boots'),
}

def build():
    shutil.rmtree(PACK + '/assets', ignore_errors=True)
    for (slot, (pieces, item)), who in ((p, w) for p in PIECES.items() for w in ('player_', 'player_slim_', '')):
        slot = who + slot                    # exact player names (as EMF lists them) + the generic fallback for mobs
        write('%s2.jem' % slot, jem(pieces))
        write('%s.properties' % slot,
              '# variant 2 (Aurora 3D netherite) only while wearing the netherite piece; otherwise vanilla\n'
              'models.1=2\nitems.1=%s\n' % item)
    if os.path.exists(RP + '/Aurora Pack/pack.png'):
        shutil.copyfile(RP + '/Aurora Pack/pack.png', PACK + '/pack.png')
    with open(PACK + '/pack.mcmeta', 'w') as f:
        json.dump({'pack': {'description': ['', {'text': 'Aurora EMF ', 'color': '#B9B9F8'},
                                            {'text': '· netherita 3D (requiere EMF + ETF)', 'color': '#F8B0EA'}],
                            'min_format': 84, 'max_format': 97}}, f, indent=2, ensure_ascii=False)

# ------------------------------------------------------------------ preview: small software renderer
# Orthographic, z-buffered, vectorised with numpy; celestial.py uses it too. It draws the vanilla HumanoidModel (skin,
# its second layer and the armour boxes) in the poses HumanoidModel.setupAnim gives in 26.3 (stand, walk, sneak, sit,
# head turned), lit like the game (two entity lights), 3x supersampled (thin rings stay smooth) and with optional ETF
# emissive layers, so clipping and glow can be checked without the game.
I3 = ((1, 0, 0), (0, 1, 0), (0, 0, 1))

def rot(rx, ry, rz):
    """Mojang ModelPart rotation, rotationZYX(z, y, x): v' = Rz * Ry * Rx * v"""
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    Rx = ((1, 0, 0), (0, cx, -sx), (0, sx, cx)); Ry = ((cy, 0, sy), (0, 1, 0), (-sy, 0, cy))
    Rz = ((cz, -sz, 0), (sz, cz, 0), (0, 0, 1))
    return mat_mul(mat_mul(Rz, Ry), Rx)

def mat_mul(A, B):
    return tuple(tuple(sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)) for i in range(3))

def apply(T, M, p):
    return tuple(T[i] + M[i][0] * p[0] + M[i][1] * p[1] + M[i][2] * p[2] for i in range(3))

def box_uv_faces(u, v, w, h, d, mirror=False):
    """vanilla box UV layout -> face rects (model space: -y = top, -z = front, -x = entity's right)"""
    f = {'top': (u + d, v, u + d + w, v + d), 'bottom': (u + d + w, v, u + d + 2 * w, v + d),
         'west': (u, v + d, u + d, v + d + h), 'front': (u + d, v + d, u + d + w, v + d + h),
         'east': (u + d + w, v + d, u + 2 * d + w, v + d + h), 'back': (u + 2 * d + w, v + d, u + 2 * d + 2 * w, v + d + h)}
    if mirror:
        f['west'], f['east'] = f['east'], f['west']
        f = {k: (r[2], r[1], r[0], r[3]) for k, r in f.items()}
    return f

def faces_from_cem(uv):
    g = lambda k: tuple(uv[k])
    return {'top': g('uvUp'), 'bottom': g('uvDown'), 'front': g('uvNorth'), 'back': g('uvSouth'), 'west': g('uvWest'), 'east': g('uvEast')}

def _unit(v):
    n = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / n for c in v)
LIGHTS = (_unit((0.2, -1.0, -0.7)), _unit((-0.2, -1.0, 0.7)))      # model space (y down, front -z), like the game's
FACE_N = {'front': (0, 0, -1), 'back': (0, 0, 1), 'west': (-1, 0, 0), 'east': (1, 0, 0), 'top': (0, -1, 0), 'bottom': (0, 1, 0)}

class Scene:
    def __init__(self, W, H, yaw, pitch, scale, cx, cy, ss=3, night=False):
        import numpy as np
        self.np, self.W, self.H, self.ss, self.night = np, W, H, ss, night
        self.w, self.h = W * ss, H * ss
        self.rgb = np.zeros((self.h, self.w, 3), np.float32)
        self.cov = np.zeros((self.h, self.w), bool)
        self.z = np.full((self.h, self.w), -1e9, np.float64)
        self.cy_, self.sy_ = math.cos(yaw), math.sin(yaw)
        self.cp, self.sp = math.cos(pitch), math.sin(pitch)
        self.s, self.cx, self.cy = scale * ss, cx * ss, cy * ss
        self.cache = {}
    def arr(self, tex):
        if id(tex) not in self.cache:
            self.cache[id(tex)] = (tex, self.np.asarray(tex.convert('RGBA'), self.np.float32))
        return self.cache[id(tex)][1]
    def project(self, p):
        x, y, z = p                                        # model space, y down, front -z
        x1 = x * self.cy_ - z * self.sy_; z1 = x * self.sy_ + z * self.cy_
        y1 = y * self.cp - z1 * self.sp; z2 = y * self.sp + z1 * self.cp
        return (self.cx + x1 * self.s, self.cy + y1 * self.s, -z2)   # depth: bigger = closer to the camera
    def quad(self, pts, tex, rect, normal=None, emi=None):
        """pts: 4 corners (tl, tr, br, bl as seen on the texture rect), rect (u1, v1, u2, v2)"""
        np = self.np
        P = [self.project(p) for p in pts]
        light = 1.0 if normal is None else min(1.0, 0.4 + 0.6 * sum(max(0.0, sum(a * b for a, b in zip(normal, L))) for L in LIGHTS))
        if self.night: light *= 0.28
        T = self.arr(tex); E = self.arr(emi) if emi is not None else None
        u1, v1, u2, v2 = rect
        uv = [(u1, v1), (u2, v1), (u2, v2), (u1, v2)]
        ulo, uhi = min(u1, u2), max(u1, u2) - 1e-4; vlo, vhi = min(v1, v2), max(v1, v2) - 1e-4
        for tri in ((0, 1, 2), (0, 2, 3)):
            (ax, ay, az), (bx, by, bz), (qx, qy, qz) = (P[i] for i in tri)
            den = (by - qy) * (ax - qx) + (qx - bx) * (ay - qy)
            if abs(den) < 1e-9: continue
            x0, x1 = max(0, int(math.floor(min(ax, bx, qx)))), min(self.w - 1, int(math.ceil(max(ax, bx, qx))))
            y0, y1 = max(0, int(math.floor(min(ay, by, qy)))), min(self.h - 1, int(math.ceil(max(ay, by, qy))))
            if x0 > x1 or y0 > y1: continue
            X, Y = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            l1 = ((by - qy) * (X - qx) + (qx - bx) * (Y - qy)) / den
            l2 = ((qy - ay) * (X - qx) + (ax - qx) * (Y - qy)) / den
            l3 = 1 - l1 - l2
            m = (l1 >= -1e-6) & (l2 >= -1e-6) & (l3 >= -1e-6)
            if not m.any(): continue
            depth = l1 * az + l2 * bz + l3 * qz
            zs = self.z[y0:y1 + 1, x0:x1 + 1]
            m &= depth >= zs - 1e-4                                   # LEQUAL like the game: coplanar faces drawn later win
            U = np.clip(l1 * uv[tri[0]][0] + l2 * uv[tri[1]][0] + l3 * uv[tri[2]][0], ulo, uhi)
            V = np.clip(l1 * uv[tri[0]][1] + l2 * uv[tri[1]][1] + l3 * uv[tri[2]][1], vlo, vhi)
            ui = np.clip(np.floor(U).astype(int), 0, T.shape[1] - 1); vi = np.clip(np.floor(V).astype(int), 0, T.shape[0] - 1)
            c = T[vi, ui]
            m &= c[..., 3] >= 10
            if not m.any(): continue
            col = c[..., :3] * light
            if E is not None:                                          # ETF emissive layer: drawn again at full light
                e = E[vi, ui]; a = e[..., 3:4] / 255.0
                col = col * (1 - a) + e[..., :3] * a
            zs[m] = depth[m]
            self.rgb[y0:y1 + 1, x0:x1 + 1][m] = col[m]
            self.cov[y0:y1 + 1, x0:x1 + 1][m] = True
    def box(self, T, M, m, s, inflate, tex, faces, emi=None):
        """box (min m, size s, grown by inflate) in a part whose transform is translation T + matrix M"""
        (x0, y0, z0), (w, h, d) = [c - inflate for c in m], [c + 2 * inflate for c in s]
        X0, X1, Y0, Y1, Z0, Z1 = x0, x0 + w, y0, y0 + h, z0, z0 + d
        quads = {'front': [(X0, Y0, Z0), (X1, Y0, Z0), (X1, Y1, Z0), (X0, Y1, Z0)],
                 'back': [(X1, Y0, Z1), (X0, Y0, Z1), (X0, Y1, Z1), (X1, Y1, Z1)],
                 'west': [(X0, Y0, Z1), (X0, Y0, Z0), (X0, Y1, Z0), (X0, Y1, Z1)],
                 'east': [(X1, Y0, Z0), (X1, Y0, Z1), (X1, Y1, Z1), (X1, Y1, Z0)],
                 'top': [(X0, Y0, Z1), (X1, Y0, Z1), (X1, Y0, Z0), (X0, Y0, Z0)],
                 'bottom': [(X0, Y1, Z0), (X1, Y1, Z0), (X1, Y1, Z1), (X0, Y1, Z1)]}
        for k, q in quads.items():
            n = _unit(apply((0, 0, 0), M, FACE_N[k]))
            if n[1] * self.sp + (n[0] * self.sy_ + n[2] * self.cy_) * self.cp > 1e-6:
                continue                                       # faces turned away from the camera (like the game's culling)
            self.quad([apply(T, M, p) for p in q], tex, faces[k], n, emi)
    def image(self, bg=None):
        np = self.np
        a = np.where(self.cov, 255, 0).astype(np.uint8)[..., None]
        img = Image.fromarray(np.concatenate([np.clip(self.rgb, 0, 255).astype(np.uint8), a], axis=2), 'RGBA')
        if self.ss > 1:
            img = img.resize((self.W, self.H), Image.BOX)
        if bg is not None:
            out = Image.new('RGBA', img.size, bg); out.alpha_composite(img); img = out
        return img

# ---- vanilla 26.3 HumanoidModel / PlayerModel: parts, skin boxes and a few poses (HumanoidModel.setupAnim)
def limbs(slim=False):
    """(part, box min, box size, armour uv, skin uv, skin 2nd-layer uv, mirror). Armour boxes are always 4 wide."""
    aw = 3 if slim else 4
    return [('head', (-4, -8, -4), (8, 8, 8), (0, 0), (0, 0), (32, 0), False),
            ('body', (-4, 0, -2), (8, 12, 4), (16, 16), (16, 16), (16, 32), False),
            ('right_arm', (-aw + 1, -2, -2), (aw, 12, 4), (40, 16), (40, 16), (40, 32), False),
            ('left_arm', (-1, -2, -2), (aw, 12, 4), (40, 16), (32, 48), (48, 48), True),
            ('right_leg', (-2, 0, -2), (4, 12, 4), (0, 16), (0, 16), (0, 32), False),
            ('left_leg', (-2, 0, -2), (4, 12, 4), (0, 16), (16, 48), (0, 48), True)]
LIMBS = limbs()

def pose(name='stand', phase=0.0, age=0.0):
    """part -> (pivot, rotation matrix) as HumanoidModel.setupAnim (26.3) leaves it. phase = walk cycle angle;
    'walk' uses animationSpeed 0.8 (a fast sprint), a bad case for clipping. Slim arms share the pivots."""
    P = {'head': [0, 0, 0], 'body': [0, 0, 0], 'right_arm': [-5, 2, 0], 'left_arm': [5, 2, 0],
         'right_leg': [-1.9, 12, 0], 'left_leg': [1.9, 12, 0]}
    R = {k: [0.0, 0.0, 0.0] for k in P}
    if name in ('walk', 'sneak_walk'):
        c, a = math.cos(phase), 0.8                             # 0.8 = a fast sprint
        R['right_arm'][0], R['left_arm'][0] = -a * c, a * c
        R['right_leg'][0], R['left_leg'][0] = 1.4 * a * c, -1.4 * a * c
    if name == 'sit':                                           # riding a boat / minecart / horse
        R['right_arm'][0] = R['left_arm'][0] = -math.pi / 5
        R['right_leg'] = [-1.4137167, math.pi / 10, 0.07853982]
        R['left_leg'] = [-1.4137167, -math.pi / 10, -0.07853982]
    if name == 'look':                                          # head turned 45 degrees: a corner reaches furthest out
        R['head'] = [math.radians(-10), math.radians(45), 0]
    if name.startswith('sneak'):
        R['body'][0] = 0.5
        R['right_arm'][0] += 0.4; R['left_arm'][0] += 0.4
        for k in ('right_leg', 'left_leg'): P[k][2] += 4.0
        P['head'][1] += 4.2; P['body'][1] += 3.2; P['right_arm'][1] += 3.2; P['left_arm'][1] += 3.2
    bob_z, bob_x = math.cos(age * 0.09) * 0.05 + 0.05, math.sin(age * 0.067) * 0.05   # AnimationUtils.bobModelPart
    R['right_arm'][2] += bob_z; R['left_arm'][2] -= bob_z
    R['right_arm'][0] += bob_x; R['left_arm'][0] -= bob_x
    return {k: (tuple(P[k]), rot(*R[k])) for k in P}

def draw_humanoid(sc, P, skin, armour=(), slim=False):
    """skin + 2nd layer, then vanilla armour boxes: armour = [(texture, emissive, inflate, parts)]"""
    for name, m, s, auv, suv, ouv, mir in limbs(slim):
        T, M = P[name]
        sc.box(T, M, m, s, 0, skin, box_uv_faces(*suv, *s))
        sc.box(T, M, m, s, 0.5 if name == 'head' else 0.25, skin, box_uv_faces(*ouv, *s))
    for tex, emi, infl, parts in armour:
        for name, m, s, auv, suv, ouv, mir in limbs(False):
            if name in parts:
                T, M = P[name]
                sc.box(T, M, m, s, infl - (0.1 if name.endswith('_leg') else 0), tex, box_uv_faces(*auv, *s, mirror=mir), emi)

def skins():
    """steve for the wide model, alex for the slim one (the reference may only ship the wide set: then the arms are cut)"""
    base = REF_ROOT + '/assets/minecraft/textures/entity/player/'
    out = []
    for name, dirs in (('steve', ('wide', 'slim')), ('alex', ('slim', 'wide'))):
        p = next((base + d + '/' + name + '.png' for d in dirs if os.path.exists(base + d + '/' + name + '.png')), None)
        out.append(Image.open(p).convert('RGBA') if p else Image.new('RGBA', (64, 64), (200, 150, 120, 255)))
    return out

VIEWS = {'front': (-30, 12), 'back': (150, 12), 'side_left': (-90, 6), 'side_right': (90, 6), 'front_high': (-25, 30)}   # side_left = the entity's left side

def render(view, emf, steve, hum, leg, posen='stand', phase=0.0, W=230, H=350, pieces=None):
    yaw, pitch = VIEWS[view]
    sc = Scene(W, H, math.radians(yaw), math.radians(pitch), 8, W / 2, 110)
    P = pose(posen, phase)
    draw_humanoid(sc, P, steve, [(leg, None, 0.5, ('body', 'right_leg', 'left_leg')),
                                 (hum, None, 1.0, ('head', 'body', 'right_arm', 'left_arm', 'right_leg', 'left_leg'))])
    if emf:
        outer, inner = pieces or (OUTER, INNER)          # pieces: another (OUTER, INNER) pair, for comparisons
        for group, tex in ((outer, hum), (inner, leg)):
            for part, boxes in group.items():
                T, M = P[part]
                for (m, s, swn) in boxes:
                    sc.box(T, M, m, s, 0, tex, faces_from_cem(swatch_uv(swn, *s)))
    return sc.image()

def preview():
    """emf_netherite.png: vanilla shape, then Aurora EMF front / back / walking side / sneaking"""
    ref = lambda p: Image.open(p).convert('RGBA')
    steve = skins()[0]
    hum = ref(AURORA + 'entity/equipment/humanoid/netherite.png'); leg = ref(AURORA + 'entity/equipment/humanoid_leggings/netherite.png')
    tiles = [render('front', False, steve, hum, leg), render('front', True, steve, hum, leg),
             render('back', True, steve, hum, leg), render('side_left', True, steve, hum, leg, 'walk', 0.0),
             render('front', True, steve, hum, leg, 'sneak')]
    k = 2; W, H = tiles[0].size
    out = Image.new('RGBA', (len(tiles) * (W * k + 10) + 20, H * k + 20), (34, 29, 52, 255))
    for i, t in enumerate(tiles):
        out.alpha_composite(t.resize((W * k, H * k), Image.NEAREST), (10 + i * (W * k + 10) + (10 if i >= 1 else 0), 10))
    os.makedirs(PREVIEWS, exist_ok=True)
    out.convert('RGB').save(PREVIEWS + '/emf_netherite.png')

if __name__ == '__main__':
    build()
    preview()
    print('emf ok')
