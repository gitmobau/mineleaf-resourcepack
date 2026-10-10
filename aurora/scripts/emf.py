# Aurora celestial: per-slot EMF models, empty vanilla base + netherite variant.
# Format/animation semantics checked against EMF/ETF sources; see HANDOFF.md.
import os, sys, json, math, shutil
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gear import EMF_SWATCHES
from cem_math import states, transform, box_coordinates, walk

HOME = os.path.expanduser('~')
REF_ROOT = os.environ.get('AURORA_REF', HOME + '/ref63')
RP = os.environ.get('AURORA_RP', HOME + '/mnt/.minecraft/resourcepacks')
PACK = RP + '/Aurora EMF'
CEM = PACK + '/assets/minecraft/emf/cem/'
AURORA = RP + '/Aurora Pack/assets/minecraft/textures/'
PREVIEWS = os.environ.get('AURORA_PREVIEWS', PACK)
PIVOT = {'head': (0, 0, 0), 'body': (0, 0, 0), 'right_arm': (-5, 2, 0), 'left_arm': (5, 2, 0),
         'right_leg': (-1.9, 12, 0), 'left_leg': (1.9, 12, 0)}
SLOTS = {'helmet': ('head', 'netherite_helmet', ('head',)),
         'chestplate': ('chest', 'netherite_chestplate', ('body', 'right_arm', 'left_arm')),
         'leggings': ('legs', 'netherite_leggings', ('body', 'right_leg', 'left_leg')),
         'boots': ('feet', 'netherite_boots', ('right_leg', 'left_leg'))}
PERIOD = 320  # ticks = 16 seconds; bob and pulse divide this period, so the GIF loops exactly


def light_uv(color, white=False):
    u, v, w, h = EMF_SWATCHES['light']
    u += color % w; v += 0 if white else 3
    return {key: [u, v, u+1, v+1] for key in ('uvNorth', 'uvSouth', 'uvEast', 'uvWest', 'uvUp', 'uvDown')}


def cem_box(part, m, size, color=0, white=False):
    # Exporter formula. Nested local boxes use the neutral export pivot (0,24,0).
    px, py, pz = PIVOT[part] if part else (0, 24, 0)
    box = {'coordinates': [round(v, 5) for v in
           (-m[0]-size[0]-px, -m[1]-size[1]-(py-24), m[2]+pz, *size)]}
    box.update(light_uv(color, white))
    return box


def node(ident, position=(0, 0, 0), rotation=(0, 0, 0), boxes=(), children=()):
    # Desired local runtime coordinates -> CEM invertAxis xy coordinates.
    x, y, z = position; rx, ry, rz = rotation
    return {'id': ident, 'invertAxis': 'xy', 'translate': [-x, -y, z],
            'rotate': [-rx, -ry, rz], 'boxes': list(boxes), 'submodels': list(children)}


def ring(ident, radius, thickness, count=16):
    parts = []
    for i in range(count):
        a = 2 * math.pi * i / count
        length = 2 * radius * math.tan(math.pi/count) + 0.025
        # Tangent segments meet to form a closed polygon, not a solid disk.
        segment = node(ident + '_%02d' % i, (radius*math.cos(a), 0, radius*math.sin(a)),
                       (0, -math.degrees(a), 0),
                       [cem_box(None, (-thickness/2, -thickness/2, -length/2),
                                (thickness, thickness, length), i*8//count, white=i == 0)])
        parts.append(segment)
    return node(ident, children=parts)


def effect(slot, part):
    if slot == 'helmet':
        rotor = ring('halo_spin', 5.0, 0.22)
        halo = node('halo', (0, -11.2, 0), (9, 0, -5), children=[rotor])
        halo['animations'] = [{'halo.ty': '-11.2 + 0.25*sin(age*2*pi/80)',
                               'halo_spin.ry': 'age*2*pi/320'}]
        return halo
    if slot == 'chestplate' and part == 'body':
        # Four-point star, airy rather than a plate; bevel-free white centre.
        boxes = [cem_box(None, (-0.13, -1.0, -0.12), (0.26, 2.0, 0.24), 0),
                 cem_box(None, (-0.65, -0.13, -0.12), (1.3, 0.26, 0.24), 3),
                 cem_box(None, (-0.2, -0.2, -0.19), (0.4, 0.4, 0.38), 0, True)]
        star = node('star', (0, 4.5, -3.25), (0, 0, 8), boxes=boxes)
        star['animations'] = [{'star.ty': '4.5 + 0.12*sin(age*2*pi/80)',
                               'star.sx': '1 + 0.08*sin(age*2*pi/40)',
                               'star.sy': '1 + 0.08*sin(age*2*pi/40)',
                               'star.sz': '1 + 0.08*sin(age*2*pi/40)'}]
        return star
    if slot == 'leggings' and part == 'body':
        belt = node('waist', (0, 10.5, 0), (7, 0, 0), children=[ring('waist_spin', 5.6, 0.18)])
        belt['animations'] = [{'waist_spin.ry': '-age*2*pi/320'}]
        return belt
    if slot == 'boots':
        ident = 'ankle_' + part
        ankle = node(ident, (0, 9.8, 0), children=[ring(ident + '_spin', 2.6, 0.17, 12)])
        ankle['animations'] = [{ident + '_spin.ry': 'age*2*pi/320'}]
        return ankle
    return None


def cem_part(part, child=None):
    px, py, pz = PIVOT[part]
    parent = {'part': part, 'id': 'aurora_' + part, 'attach': True, 'invertAxis': 'xy',
              'translate': [px, py-24, -pz], 'boxes': []}
    if child:
        # Undo the export frame in a STATIC anchor; animate the local child, not
        # the exported parent (which would otherwise orbit around y=24).
        parent['submodels'] = [node('local_' + part, (px, py-24, pz), children=[child])]
        # EMFJemData collects animations on TOP-LEVEL models only. Targets may
        # name any descendant; nested animation blocks themselves are ignored.
        parent['animations'] = [group for n in walk([child]) for group in n.pop('animations', [])]
    return parent


def jem(slot, active=True):
    return {'textureSize': [64, 32], 'models': [cem_part(part, effect(slot, part) if active else None)
                                               for part in SLOTS[slot][2]]}


def write(name, obj):
    os.makedirs(CEM, exist_ok=True)
    with open(CEM + name, 'w', encoding='utf-8', newline='\n') as f:
        if name.endswith('.jem'): json.dump(obj, f, indent=2)
        else: f.write(obj)


def build():
    shutil.rmtree(PACK + '/assets', ignore_errors=True)
    for slot, (equipment, item, parts) in SLOTS.items():
        for prefix in ('player_', 'player_slim_', ''):
            name = prefix + slot
            write(name + '.jem', jem(slot, False))
            write(name + '2.jem', jem(slot))
            # ETF items also matches held items. The NBT slot check is essential.
            write(name + '.properties', '# Aurora solo con netherita en su ranura; base vacia = vanilla.\n'
                  'models.1=2\nitems.1=%s\nnbt.1.equipment.%s.id=minecraft:%s\nmodels.2=1\n' % (item, equipment, item))
    if os.path.exists(RP + '/Aurora Pack/pack.png'):
        shutil.copyfile(RP + '/Aurora Pack/pack.png', PACK + '/pack.png')
    with open(PACK + '/pack.mcmeta', 'w', encoding='utf-8') as f:
        json.dump({'pack': {'description': ['', {'text': 'Aurora EMF ', 'color': '#B9B9F8'},
                                            {'text': '· aureola y anillos de luz (EMF + ETF)', 'color': '#F8B0EA'}],
                            'min_format': 84, 'max_format': 97}}, f, indent=2, ensure_ascii=False)


# Preview: consumes the ACTUAL emitted .jem hierarchy, including its expressions.
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
                    if depth < self.z[yy][xx] - 1e-4: continue          # LEQUAL like the game: coplanar faces drawn later win
                    u = l1 * uv[tri[0]][0] + l2 * uv[tri[1]][0] + l3 * uv[tri[2]][0]
                    v = l1 * uv[tri[0]][1] + l2 * uv[tri[1]][1] + l3 * uv[tri[2]][1]
                    c = tex.getpixel((min(tex.width - 1, max(0, int(u))), min(tex.height - 1, max(0, int(v)))))
                    if c[3] < 10: continue
                    self.z[yy][xx] = depth; self.px[xx, yy] = c[:3] + (255,)
    def box(self, origin, rot_x, m, s, inflate, tex, faces, custom_transform=None):
        """axis-aligned box in a part (pivot origin, optional x rotation), corners rotated then drawn face by face"""
        (x0, y0, z0), (w, h, d) = [c - inflate for c in m], [c + 2 * inflate for c in s]
        ox, oy, oz = origin
        def T(x, y, z):
            if custom_transform is not None: return custom_transform((x, y, z))
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

def draw_model(scene, model, texture, age, poses=None):
    poses = poses or {}
    state = states(model, age)
    def draw_node(n, parents, part):
        chain = parents + [state[n['id']]]
        def T(point):
            for st in reversed(chain): point = transform(point, st)
            rx = poses.get(part, 0)
            x, y, z = point
            y, z = y*math.cos(rx)-z*math.sin(rx), y*math.sin(rx)+z*math.cos(rx)
            return tuple(a+b for a, b in zip((x, y, z), PIVOT[part]))
        for box in n.get('boxes', []):
            m, size = box_coordinates(n, box)
            scene.box((0, 0, 0), 0, m, size, 0, texture, faces_from_cem(box), T)
        for child in n.get('submodels', []): draw_node(child, chain, part)
    for n in model['models']: draw_node(n, [], n['part'])


def render(view, emf, steve, hum, leg, W=230, H=350, age=0, models=None, poses=None, night=False):
    yaw = {'front': math.radians(-30), 'back': math.radians(150)}[view]
    sc = Scene(W, H, yaw, math.radians(12), 8, W / 2, 112)
    poses = poses or {}
    if night:
        channels = steve.split()
        steve = Image.merge('RGBA', tuple(c.point(lambda v: int(v*0.24)) for c in channels[:3]) + (channels[3],))
    for name, piv, m, s, uv, mir in LIMBS:
        u, v = SKIN_UV[name]
        sc.box(piv, poses.get(name, 0), m, s, 0, steve, box_uv_faces(u, v, *s))
    for name, piv, m, s, (u, v), mir in LIMBS:
        if name in ('right_leg', 'left_leg', 'body'):
            sc.box(piv, poses.get(name, 0), m, s, 0.5, leg, box_uv_faces(u, v, *s, mirror=mir))
        sc.box(piv, poses.get(name, 0), m, s, 1.0, hum, box_uv_faces(u, v, *s, mirror=mir))
    if emf:
        for slot, model in models.items():
            draw_model(sc, model, leg if slot == 'leggings' else hum, age, poses)
    return sc.img


def preview():
    ref = lambda p: Image.open(p).convert('RGBA')
    steve = ref(REF_ROOT + '/assets/minecraft/textures/entity/player/wide/steve.png')
    hum = ref(AURORA + 'entity/equipment/humanoid/netherite.png')
    leg = ref(AURORA + 'entity/equipment/humanoid_leggings/netherite.png')
    # Read disk so the preview cannot accidentally show geometry absent in the pack.
    models = {slot: json.load(open(CEM + 'player_' + slot + '2.jem', encoding='utf-8')) for slot in SLOTS}
    font = ImageFont.load_default(size=16)
    tiles = [render('front', False, steve, hum, leg),
             render('front', True, steve, hum, leg, models=models),
             render('back', True, steve, hum, leg, models=models),
             render('front', True, steve, hum, leg, models=models, night=True)]
    out = Image.new('RGB', (4*250, 398), (29, 25, 44))
    draw = ImageDraw.Draw(out)
    for i, (label, tile) in enumerate(zip(('SIN EMF / detalles 2D', 'EMF / frente', 'EMF / espalda', 'ETF / noche simulada'), tiles)):
        draw.text((i*250+10, 12), label, font=font, fill=(211, 220, 255))
        out.paste(tile, (i*250+10, 40), tile)
    os.makedirs(PREVIEWS, exist_ok=True)
    out.save(PREVIEWS + '/emf_netherite.png')
    frames = []
    for frame in range(64):
        age = frame * PERIOD / 64
        out = Image.new('RGB', (500, 398), (29, 25, 44))
        draw = ImageDraw.Draw(out)
        for i, view in enumerate(('front', 'back')):
            tile = render(view, True, steve, hum, leg, models=models, age=age)
            out.paste(tile, (i*250+10, 40), tile)
        draw.text((12, 12), 'AURORA / 16 s por vuelta / animacion CEM', font=font, fill=(211, 220, 255))
        frames.append(out)
    # A shared palette prevents shimmer caused by per-frame GIF quantization.
    palette = out.quantize(colors=256)
    frames = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
    frames[0].save(PREVIEWS + '/emf_netherite.gif', save_all=True, append_images=frames[1:],
                   duration=250, loop=0, optimize=False, disposal=2)


if __name__ == '__main__':
    build()
    preview()
    print('emf celestial ok')
