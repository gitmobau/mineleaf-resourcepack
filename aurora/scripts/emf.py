# Aurora EMF: 3D netherite armour for Entity Model Features (+ Entity Texture Features, required by EMF).
# Optional pack; without the mods nothing changes.
#
# - Models are EMF "variant 2" of the player armour models. The .properties files pick variant 2 only while the
#   entity wears the netherite piece (ETF "items=" rule); otherwise variant 1 = vanilla model (EMF default when there is
#   no base .jem). So diamond/iron/... armour keeps its vanilla shape.
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

# extra pieces: part -> [(min xyz, size xyz, swatch)] in the part's vanilla local space
OUTER = {   # helmet, chestplate, boots (outer armour is inflated by 1)
    'head': [((-0.5, -11.5, -4.5), (1, 2.6, 9), 'trimv'),                 # crest
             ((-4.5, -9.8, -5.6), (9, 1, 0.6), 'trim'),                    # crown band
             ((-3.5, -11, -5.6), (1, 1.3, 0.6), 'gem'), ((-0.5, -12.2, -5.6), (1, 2.5, 0.6), 'gem2'),
             ((2.5, -11, -5.6), (1, 1.3, 0.6), 'gem'),
             ((5, -8, -1), (0.8, 3, 4), 'trim'), ((5, -10, 0), (0.8, 2, 2), 'trim'),          # side fins
             ((-5.8, -8, -1), (0.8, 3, 4), 'trim'), ((-5.8, -10, 0), (0.8, 2, 2), 'trim')],
    'body': [((-1.5, 1.5, -3.5), (3, 3, 0.5), 'gold'), ((-1, 2, -3.8), (2, 2, 0.8), 'gem2'),   # chest gem
             ((-4.5, -1.6, -3.6), (9, 1.2, 0.6), 'trim'), ((-4.5, -1.6, 3), (9, 1.2, 0.6), 'trim'),   # collar
             ((-1, 1, 3), (2, 2, 0.8), 'metal'), ((-1, 4, 3), (2, 2, 0.8), 'metal'), ((-1, 7, 3), (2, 2, 0.8), 'metal')],
    'right_arm': [((-5, -4.2, -3.6), (6.5, 3, 7.2), 'metal'), ((-5.3, -1.4, -3.8), (6.8, 0.8, 7.6), 'trim'),
                  ((-3.5, -6.2, -0.5), (1, 2, 1), 'gem')],                 # pauldron
    'left_arm': [((-1.5, -4.2, -3.6), (6.5, 3, 7.2), 'metal'), ((-1.5, -1.4, -3.8), (6.8, 0.8, 7.6), 'trim'),
                 ((2.5, -6.2, -0.5), (1, 2, 1), 'gem')],
    'right_leg': [((-3.8, 7.5, -1.5), (0.8, 3, 3), 'trim'), ((-3.8, 6, -0.5), (0.8, 1.5, 1.5), 'trim'),
                  ((-3.2, 11, -3.8), (6.4, 2, 0.8), 'metal')],             # boot fins + toe cap
    'left_leg': [((3, 7.5, -1.5), (0.8, 3, 3), 'trim'), ((3, 6, -0.5), (0.8, 1.5, 1.5), 'trim'),
                 ((-3.2, 11, -3.8), (6.4, 2, 0.8), 'metal')],
}
INNER = {   # leggings (inner armour is inflated by 0.5)
    'body': [((-4.6, 10.2, -3), (9.2, 1.2, 0.5), 'trim'), ((-1, 9.8, -3.2), (2, 2, 0.7), 'gem')],   # belt + gem
    'right_leg': [((-2.7, -0.6, -3.2), (5.4, 5.5, 0.7), 'metal'), ((-2.7, 4.7, -3.25), (5.4, 0.8, 0.75), 'trim'),
                  ((-3.2, -0.6, -2.7), (0.7, 6, 5.4), 'dark'), ((-2, 6, -3.1), (4, 2, 0.6), 'metal')],
    'left_leg': [((-2.7, -0.6, -3.2), (5.4, 5.5, 0.7), 'metal'), ((-2.7, 4.7, -3.25), (5.4, 0.8, 0.75), 'trim'),
                 ((2.5, -0.6, -2.7), (0.7, 6, 5.4), 'dark'), ((-2, 6, -3.1), (4, 2, 0.6), 'metal')],
}
def swatch_uv(name, w, h, d):
    """per-face UVs on a material swatch: faces bigger than the swatch stretch it (keeps the outline), smaller ones
    take the centre at 1:1 so thin edges show the material, not the outline"""
    u0, v0, sw, sh = EMF_SWATCHES[name]
    def r(fw, fh):
        a = (0, sw) if fw >= sw else ((sw - fw) / 2, (sw + fw) / 2)
        b = (0, sh) if fh >= sh else ((sh - fh) / 2, (sh + fh) / 2)
        return [round(u0 + a[0], 3), round(v0 + b[0], 3), round(u0 + a[1], 3), round(v0 + b[1], 3)]
    return {'uvNorth': r(w, h), 'uvSouth': r(w, h), 'uvEast': r(d, h), 'uvWest': r(d, h), 'uvUp': r(w, d), 'uvDown': r(w, d)}

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

def build():
    shutil.rmtree(PACK + '/assets', ignore_errors=True)
    for base, pieces, item in (('outer_armor', OUTER, 'netherite_chestplate'), ('inner_armor', INNER, 'netherite_leggings')):
        for who in ('player', 'player_slim'):                 # normal and slim (Alex) skins
            write('%s_%s2.jem' % (who, base), jem(pieces))
            write('%s_%s.properties' % (who, base),
                  '# variant 2 (Aurora 3D netherite) only while wearing the netherite piece; otherwise vanilla\n'
                  'models.1=2\nitems.1=%s\n' % item)
    if os.path.exists(RP + '/Aurora Pack/pack.png'):
        shutil.copyfile(RP + '/Aurora Pack/pack.png', PACK + '/pack.png')
    with open(PACK + '/pack.mcmeta', 'w') as f:
        json.dump({'pack': {'description': ['', {'text': 'Aurora EMF ', 'color': '#B9B9F8'},
                                            {'text': '· netherita 3D (requiere EMF + ETF)', 'color': '#F8B0EA'}],
                            'min_format': 84, 'max_format': 97}}, f, indent=2, ensure_ascii=False)

# ------------------------------------------------------------------ preview: tiny software renderer (orthographic, z-buffer)
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

class Scene:
    def __init__(self, W, H, yaw, pitch, scale, cx, cy):
        self.W, self.H = W, H
        self.img = Image.new('RGBA', (W, H), (0, 0, 0, 0)); self.px = self.img.load()
        self.z = [[-1e9] * W for _ in range(H)]
        self.cy_, self.sy_ = math.cos(yaw), math.sin(yaw)
        self.cp, self.sp = math.cos(pitch), math.sin(pitch)
        self.s, self.cx, self.cy = scale, cx, cy
    def project(self, p):
        x, y, z = p                                        # model space, y down, front -z
        x1 = x * self.cy_ - z * self.sy_; z1 = x * self.sy_ + z * self.cy_
        y1 = y * self.cp - z1 * self.sp; z2 = y * self.sp + z1 * self.cp
        return (self.cx + x1 * self.s, self.cy + y1 * self.s, -z2)   # depth: bigger = closer to the camera
    def quad(self, pts, tex, rect):
        """pts: 4 corners (tl, tr, br, bl as seen on the texture rect), rect (u1, v1, u2, v2)"""
        P = [self.project(p) for p in pts]
        u1, v1, u2, v2 = rect
        uv = [(u1, v1), (u2, v1), (u2, v2), (u1, v2)]
        for tri in ((0, 1, 2), (0, 2, 3)):
            (ax, ay, az), (bx, by, bz), (qx, qy, qz) = (P[i] for i in tri)
            den = (by - qy) * (ax - qx) + (qx - bx) * (ay - qy)
            if abs(den) < 1e-9: continue
            for yy in range(max(0, int(min(ay, by, qy))), min(self.H, int(max(ay, by, qy)) + 1)):
                for xx in range(max(0, int(min(ax, bx, qx))), min(self.W, int(max(ax, bx, qx)) + 1)):
                    sx, sy = xx + 0.5, yy + 0.5
                    l1 = ((by - qy) * (sx - qx) + (qx - bx) * (sy - qy)) / den
                    l2 = ((qy - ay) * (sx - qx) + (ax - qx) * (sy - qy)) / den
                    l3 = 1 - l1 - l2
                    if min(l1, l2, l3) < -1e-6: continue
                    depth = l1 * az + l2 * bz + l3 * qz
                    if depth <= self.z[yy][xx]: continue
                    u = l1 * uv[tri[0]][0] + l2 * uv[tri[1]][0] + l3 * uv[tri[2]][0]
                    v = l1 * uv[tri[0]][1] + l2 * uv[tri[1]][1] + l3 * uv[tri[2]][1]
                    c = tex.getpixel((min(tex.width - 1, max(0, int(u))), min(tex.height - 1, max(0, int(v)))))
                    if c[3] < 10: continue
                    self.z[yy][xx] = depth; self.px[xx, yy] = c[:3] + (255,)
    def box(self, origin, rot_x, m, s, inflate, tex, faces):
        """axis-aligned box in a part (pivot origin, optional x rotation), corners rotated then drawn face by face"""
        (x0, y0, z0), (w, h, d) = [c - inflate for c in m], [c + 2 * inflate for c in s]
        ox, oy, oz = origin
        def T(x, y, z):
            if rot_x:
                c, sn = math.cos(rot_x), math.sin(rot_x)
                y, z = y * c - z * sn, y * sn + z * c
            return (ox + x, oy + y, oz + z)
        X0, X1, Y0, Y1, Z0, Z1 = x0, x0 + w, y0, y0 + h, z0, z0 + d
        quads = {'front': [(X0, Y0, Z0), (X1, Y0, Z0), (X1, Y1, Z0), (X0, Y1, Z0)],
                 'back': [(X1, Y0, Z1), (X0, Y0, Z1), (X0, Y1, Z1), (X1, Y1, Z1)],
                 'west': [(X0, Y0, Z1), (X0, Y0, Z0), (X0, Y1, Z0), (X0, Y1, Z1)],
                 'east': [(X1, Y0, Z0), (X1, Y0, Z1), (X1, Y1, Z1), (X1, Y1, Z0)],
                 'top': [(X0, Y0, Z1), (X1, Y0, Z1), (X1, Y0, Z0), (X0, Y0, Z0)],
                 'bottom': [(X0, Y1, Z0), (X1, Y1, Z0), (X1, Y1, Z1), (X0, Y1, Z1)]}
        for k, q in quads.items():
            self.quad([T(*p) for p in q], tex, faces[k])

LIMBS = [('head', (0, 0, 0), (-4, -8, -4), (8, 8, 8), (0, 0), False), ('body', (0, 0, 0), (-4, 0, -2), (8, 12, 4), (16, 16), False),
         ('right_arm', (-5, 2, 0), (-3, -2, -2), (4, 12, 4), (40, 16), False), ('left_arm', (5, 2, 0), (-1, -2, -2), (4, 12, 4), (40, 16), True),
         ('right_leg', (-1.9, 12, 0), (-2, 0, -2), (4, 12, 4), (0, 16), False), ('left_leg', (1.9, 12, 0), (-2, 0, -2), (4, 12, 4), (0, 16), True)]
SKIN_UV = {'head': (0, 0), 'body': (16, 16), 'right_arm': (40, 16), 'left_arm': (32, 48), 'right_leg': (0, 16), 'left_leg': (16, 48)}

def render(view, emf, steve, hum, leg, W=230, H=350):
    yaw = {'front': math.radians(-30), 'back': math.radians(150)}[view]
    sc = Scene(W, H, yaw, math.radians(12), 8, W / 2, 110)
    for name, piv, m, s, uv, mir in LIMBS:                    # skin
        u, v = SKIN_UV[name]
        sc.box(piv, 0, m, s, 0, steve, box_uv_faces(u, v, *s))
    for name, piv, m, s, (u, v), mir in LIMBS:                # vanilla armour boxes (helmet/chest/arms/boots outer, leggings inner)
        if name in ('right_leg', 'left_leg'):
            sc.box(piv, 0, m, s, 0.5, leg, box_uv_faces(u, v, *s, mirror=mir))
        if name == 'body':
            sc.box(piv, 0, m, s, 0.5, leg, box_uv_faces(u, v, *s))
        sc.box(piv, 0, m, s, 1.0, hum, box_uv_faces(u, v, *s, mirror=mir))
    if emf:
        for pieces, tex in ((OUTER, hum), (INNER, leg)):
            for part, boxes in pieces.items():
                for (m, s, swn) in boxes:
                    sc.box(PIVOT[part], 0, m, s, 0, tex, faces_from_cem(swatch_uv(swn, *s)))
    return sc.img

def preview():
    ref = lambda p: Image.open(p).convert('RGBA')
    sp = REF_ROOT + '/assets/minecraft/textures/entity/player/wide/steve.png'     # fetched by fetch_ref.py
    steve = ref(sp) if os.path.exists(sp) else Image.new('RGBA', (64, 64), (200, 150, 120, 255))
    hum = ref(AURORA + 'entity/equipment/humanoid/netherite.png'); leg = ref(AURORA + 'entity/equipment/humanoid_leggings/netherite.png')
    tiles = [render(v, e, steve, hum, leg) for e in (False, True) for v in ('front', 'back')]
    k = 2; W, H = tiles[0].size
    out = Image.new('RGBA', (4 * W * k + 50, H * k + 20), (34, 29, 52, 255))
    for i, t in enumerate(tiles):
        out.alpha_composite(t.resize((W * k, H * k), Image.NEAREST), (10 + i * (W * k + 10) + (10 if i >= 2 else 0), 10))
    os.makedirs(PREVIEWS, exist_ok=True)
    out.convert('RGB').save(PREVIEWS + '/emf_netherite.png')

if __name__ == '__main__':
    build()
    preview()
    print('emf ok')
