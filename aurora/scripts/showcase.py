# Aurora showcase: preview images of everything in the pack, rendered from the generated textures.
#   previews/showcase_armor.png  worn armor on a 3D mannequin (vanilla geometry, like the game draws it)
#   previews/showcase_hud.png    HUD mock-up: hotbar with items, hearts, food, armor, XP, crosshair
#   previews/showcase_items.png  every recoloured item, with enchantment aura
#   previews/showcase_menus.png  every menu background
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFont

HOME = os.path.expanduser('~')
RP = os.environ.get('AURORA_RP', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'packs'))
PREVIEWS = os.environ.get('AURORA_PREVIEWS', os.path.join(os.path.dirname(RP), 'previews'))
TX = os.path.join(RP, 'Aurora Pack', 'assets', 'minecraft', 'textures') + '/'
BG = (46, 38, 70, 255)
INK = (236, 230, 252, 255)

def font(size):
    for f in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 'C:/Windows/Fonts/segoeui.ttf'):
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()

def tex(rel, frame=True):
    im = Image.open(TX + rel + '.png').convert('RGBA')
    if frame and im.height > im.width and os.path.exists(TX + rel + '.png.mcmeta'):
        im = im.crop((0, 0, im.width, im.width))       # first animation frame
    return im

def label(img, xy, text, size=16, fill=INK):
    ImageDraw.Draw(img).text(xy, text, font=font(size), fill=fill)

# ------------------------------------------------------------------ tiny 3D box renderer
def rot(rx, ry, rz):
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    Rx = ((1, 0, 0), (0, cx, -sx), (0, sx, cx))
    Ry = ((cy, 0, sy), (0, 1, 0), (-sy, 0, cy))
    Rz = ((cz, -sz, 0), (sz, cz, 0), (0, 0, 1))
    mm = lambda A, B: tuple(tuple(sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)) for i in range(3))
    return mm(Rz, mm(Ry, Rx))                    # ModelPart order: Z, then Y, then X

def mv(M, p):
    return tuple(sum(M[i][k] * p[k] for k in range(3)) for i in range(3))

SHADE = {'north': 0.8, 'south': 0.8, 'west': 0.62, 'east': 0.62, 'up': 1.0, 'down': 0.5}

def box_quads(texture, uv, mn, size, grow=0.0, pivot=(0, 0, 0), R=None, mirror=False, solid=None, push=(0, 0, 0)):
    """texel quads of one model cube, mapped exactly like Minecraft's ModelPart.Cube"""
    u, v = uv; w, h, d = size
    x0, y0, z0 = mn[0] - grow, mn[1] - grow, mn[2] - grow
    x1, y1, z1 = mn[0] + w + grow, mn[1] + h + grow, mn[2] + d + grow
    sx, sy, sz = (x1 - x0) / w, (y1 - y0) / h, (z1 - z0) / d
    side_r, side_l = (u, v + d, d, h), (u + d + w, v + d, d, h)
    if mirror:
        side_r, side_l = side_l, side_r
    faces = {   # name: (rect, point(i, j), normal)
        'north': ((u + d, v + d, w, h), lambda i, j: (x0 + i * sx, y0 + j * sy, z0), (0, 0, -1)),
        'south': ((u + 2 * d + w, v + d, w, h), lambda i, j: (x1 - i * sx, y0 + j * sy, z1), (0, 0, 1)),
        'west': (side_r, lambda i, j: (x0, y0 + j * sy, z1 - i * sz), (-1, 0, 0)),
        'east': (side_l, lambda i, j: (x1, y0 + j * sy, z0 + i * sz), (1, 0, 0)),
        'up': ((u + d, v, w, d), lambda i, j: (x0 + i * sx, y0, z1 - j * sz), (0, -1, 0)),
        'down': ((u + d + w, v, w, d), lambda i, j: (x0 + i * sx, y1, z0 + j * sz), (0, 1, 0)),
    }
    R = R or rot(0, 0, 0)
    out = []
    for name, ((rx, ry, rw, rh), pt, n) in faces.items():
        for j in range(rh):
            for i in range(rw):
                if solid is not None:
                    c = solid
                else:
                    ti = rx + (rw - 1 - i if mirror else i)
                    c = texture.getpixel((ti, ry + j))
                    if c[3] < 8:
                        continue
                corners = [pt(i, j), pt(i + 1, j), pt(i + 1, j + 1), pt(i, j + 1)]
                corners = [tuple(pivot[k] + push[k] + q[k] for k in range(3)) for q in (mv(R, p) for p in corners)]
                out.append((corners, mv(R, n), c, SHADE[name]))
    return out

def render(quads, yaw, pitch=0.35, scale=10, size=(300, 420), origin=(150, 110)):
    img = Image.new('RGBA', size, (0, 0, 0, 0)); dr = ImageDraw.Draw(img)
    cy, sy, cp, sp = math.cos(yaw), math.sin(yaw), math.cos(pitch), math.sin(pitch)
    def view(p):
        x, y, z = p
        x2, z2 = x * cy - z * sy, x * sy + z * cy
        return x2, y * cp - z2 * sp, z2 * cp + y * sp
    drawn = []
    for corners, n, c, shade in quads:
        nv = view(n)
        if nv[2] >= -1e-6:                       # back face
            continue
        vs = [view(p) for p in corners]
        depth = sum(p[2] for p in vs) / 4
        light = shade * (0.85 + 0.15 * max(0, -nv[2]))
        col = tuple(int(min(255, c[k] * light)) for k in range(3)) + (255,)
        if c[3] < 255:   # translucent texel over whatever is behind
            col = col[:3] + (c[3],)
        drawn.append((depth, [(origin[0] + p[0] * scale, origin[1] + p[1] * scale) for p in vs], col))
    drawn.sort(key=lambda q: -q[0])
    for _, poly, col in drawn:
        if col[3] == 255:
            dr.polygon(poly, fill=col, outline=col)
        else:
            layer = Image.new('RGBA', size, (0, 0, 0, 0))
            ImageDraw.Draw(layer).polygon(poly, fill=col)
            img.alpha_composite(layer); dr = ImageDraw.Draw(img)
    return img

# humanoid parts: (pivot, box min, size, uv, mirror)
PARTS = {
    'head': ((0, 0, 0), (-4, -8, -4), (8, 8, 8), (0, 0), False),
    'body': ((0, 0, 0), (-4, 0, -2), (8, 12, 4), (16, 16), False),
    'right_arm': ((-5, 2, 0), (-3, -2, -2), (4, 12, 4), (40, 16), False),
    'left_arm': ((5, 2, 0), (-1, -2, -2), (4, 12, 4), (40, 16), True),
    'right_leg': ((-1.9, 12, 0), (-2, 0, -2), (4, 12, 4), (0, 16), False),
    'left_leg': ((1.9, 12, 0), (-2, 0, -2), (4, 12, 4), (0, 16), True),
}
POSE = {'head': (0, 0.15, 0), 'right_arm': (0.25, 0, 0.08), 'left_arm': (-0.25, 0, -0.08),
        'right_leg': (-0.22, 0, 0.03), 'left_leg': (0.22, 0, -0.03), 'body': (0, 0, 0)}
SKIN = (214, 168, 140, 255)

def figure(mat, cloak=False):
    eq = 'entity/equipment/'
    hum = tex(eq + 'humanoid/' + mat, False)
    leg = tex(eq + 'humanoid_leggings/' + mat, False)
    q = []
    R = {k: rot(*POSE[k]) for k in PARTS}
    for k, (pv, mn, sz, uv, mir) in PARTS.items():
        q += box_quads(None, uv, mn, sz, 0, pv, R[k], mir, solid=SKIN)                 # mannequin
    for k in ('body', 'right_leg', 'left_leg'):                                           # leggings layer
        pv, mn, sz, uv, mir = PARTS[k]
        q += box_quads(leg, uv, mn, sz, 0.5, pv, R[k], mir)
    for k in ('head', 'body', 'right_arm', 'left_arm', 'right_leg', 'left_leg'):           # helmet/chest/boots
        pv, mn, sz, uv, mir = PARTS[k]
        q += box_quads(hum, uv, mn, sz, 1.0, pv, R[k], mir)
    if cloak:                                                                             # elytra-shaped cloak
        wing = tex(eq + 'wings/aurora_cloak', False)
        q += box_quads(wing, (22, 0), (-10, 0, 0), (10, 20, 2), 1.0, (5, 0, 0), rot(0.2617994, 0, -0.2617994),
                       False, push=(0, 0, 2))
        q += box_quads(wing, (22, 0), (0, 0, 0), (10, 20, 2), 1.0, (-5, 0, 0), rot(0.2617994, 0, 0.2617994),
                       True, push=(0, 0, 2))
    return q

def showcase_armor():
    sets = [('diamond', 'Diamante: cristal', False), ('netherite', 'Netherita: noche aurora + capa', True),
            ('iron', 'Hierro: piedra lunar', False), ('gold', 'Oro: oro rosa', False)]
    W, H = 300, 420
    sheet = Image.new('RGBA', (len(sets) * (2 * W) + 20, H + 70), BG)
    for i, (mat, name, cloak) in enumerate(sets):
        q = figure(mat, cloak)
        x = 10 + i * 2 * W
        sheet.alpha_composite(render(q, yaw=0.55), (x, 40))
        sheet.alpha_composite(render(q, yaw=math.pi + 0.6), (x + W, 40))
        label(sheet, (x + 12, 10), name, 20)
    label(sheet, (10, H + 40), 'Render con la geometría vanilla de la armadura (la que usa el juego sin mods). Delante y detrás.', 15)
    return sheet

# ------------------------------------------------------------------ HUD mock-up
def showcase_hud():
    S = 4
    W, H = 182 * S + 80, 150 * S
    img = Image.new('RGBA', (W, H))
    for y in range(H):      # sky -> grass backdrop
        c = (126, 168, 238) if y < H * 0.55 else (92, 140, 70)
        k = y / H
        img.paste(c + (255,), (0, y, W, y + 1)) if True else None
    hud = Image.new('RGBA', (W // S, H // S))
    ox = (W // S - 182) // 2; oy = H // S - 26
    H_ = 'gui/sprites/hud/'
    hud.alpha_composite(tex(H_ + 'hotbar'), (ox, oy))
    items = ['diamond_sword', 'netherite_pickaxe', 'iron_axe', 'golden_shovel', 'diamond_spear',
             'netherite_sword', 'totem_of_undying', 'elytra', 'golden_hoe']
    for i, n in enumerate(items):
        x, y = ox + 3 + i * 20, oy + 3
        if i == 0:     # enchanted: aura
            au = tex('item/aurora/aura_' + n)
            hud.alpha_composite(au, (x - 4, y - 4))
        hud.alpha_composite(tex('item/' + n), (x, y))
    hud.alpha_composite(tex(H_ + 'hotbar_selection').crop((0, 0, 24, 23)), (ox - 1, oy - 1))
    xb = tex(H_ + 'experience_bar_background'); xp = tex(H_ + 'experience_bar_progress').crop((0, 0, 182, 5))
    hud.alpha_composite(xb, (ox, oy - 7)); hud.alpha_composite(xp.crop((0, 0, 110, 5)), (ox, oy - 7))
    for i in range(10):
        hud.alpha_composite(tex(H_ + 'heart/container'), (ox + i * 8, oy - 17))
        hud.alpha_composite(tex(H_ + ('heart/full' if i < 8 else 'heart/half' if i == 8 else 'heart/container')), (ox + i * 8, oy - 17))
        hud.alpha_composite(tex(H_ + ('armor_full' if i < 7 else 'armor_empty')), (ox + i * 8, oy - 27))
        fx = ox + 182 - 9 - i * 8
        hud.alpha_composite(tex(H_ + 'food_empty'), (fx, oy - 17))
        hud.alpha_composite(tex(H_ + ('food_full' if i < 9 else 'food_half')), (fx, oy - 17))
        hud.alpha_composite(tex(H_ + 'air'), (fx, oy - 27)) if i < 6 else None
    hud.alpha_composite(tex(H_ + 'crosshair'), ((W // S - 15) // 2, (H // S - 15) // 2 - 20))
    img.alpha_composite(hud.resize((W, H), Image.NEAREST))
    out = Image.new('RGBA', (W + 20, H + 50), BG)
    out.alpha_composite(img, (10, 40))
    label(out, (10, 10), 'HUD: hotbar, espada encantada con aura, corazones, armadura, comida, aire, XP y mira', 18)
    return out

# ------------------------------------------------------------------ items
def showcase_items():
    mats = ['diamond', 'netherite', 'iron', 'golden']
    kinds = ['sword', 'pickaxe', 'axe', 'shovel', 'hoe', 'spear', 'helmet', 'chestplate', 'leggings', 'boots',
             'horse_armor', 'nautilus_armor']
    S = 5; cell = 24 * S + 8
    W = 170 + len(kinds) * cell
    out = Image.new('RGBA', (W, 60 + len(mats) * cell + cell + 20), BG)
    names = {'diamond': 'Diamante', 'netherite': 'Netherita', 'iron': 'Hierro', 'golden': 'Oro'}
    for r, m in enumerate(mats):
        y = 50 + r * cell
        label(out, (10, y + cell // 2 - 12), names[m], 20)
        for c, k in enumerate(kinds):
            n = '%s_%s' % (m, k)
            if not os.path.exists(TX + 'item/%s.png' % n):
                continue
            cellimg = Image.new('RGBA', (24, 24))
            if os.path.exists(TX + 'item/aurora/aura_%s.png' % n):
                cellimg.alpha_composite(tex('item/aurora/aura_' + n))
            cellimg.alpha_composite(tex('item/' + n), (4, 4))
            out.alpha_composite(cellimg.resize((24 * S, 24 * S), Image.NEAREST), (170 + c * cell, y))
    y = 50 + len(mats) * cell
    label(out, (10, y + cell // 2 - 12), 'Otros', 20)
    for c, n in enumerate(['totem_of_undying', 'elytra']):
        out.alpha_composite(tex('item/' + n).resize((16 * S, 16 * S), Image.NEAREST), (170 + c * cell + 4 * S, y + 4 * S))
    label(out, (10, 12), 'Objetos (herramientas con el aura que sale al encantarlas; en el juego brillan animados)', 18)
    return out

# ------------------------------------------------------------------ menus
def showcase_menus():
    C = 'gui/container/'
    names = sorted(f[:-4] for f in os.listdir(TX + C) if f.endswith('.png'))
    shots = []
    for n in names:
        im = tex(C + n, False); bb = im.getbbox()
        shots.append((n, im.crop(bb)))
    for n in ('tab_items', 'tab_inventory', 'tab_item_search'):
        im = tex(C + 'creative_inventory/' + n, False); shots.append(('creativo: ' + n[4:], im.crop(im.getbbox())))
    rb = tex('gui/recipe_book', False); shots.append(('libro de recetas', rb.crop(rb.getbbox())))
    S = 2; cols = 5; cw, ch = 280 * S + 20, 222 * S + 40
    rows = (len(shots) + cols - 1) // cols
    out = Image.new('RGBA', (cols * cw + 20, rows * ch + 60), BG)
    label(out, (10, 12), 'Todos los menús (%d)' % len(shots), 22)
    for i, (n, im) in enumerate(shots):
        x, y = 10 + (i % cols) * cw, 50 + (i // cols) * ch
        label(out, (x, y), n, 16)
        out.alpha_composite(im.resize((im.width * S, im.height * S), Image.NEAREST), (x, y + 24))
    return out

if __name__ == '__main__':
    os.makedirs(PREVIEWS, exist_ok=True)
    for name, fn in (('showcase_armor', showcase_armor), ('showcase_hud', showcase_hud),
                     ('showcase_items', showcase_items), ('showcase_menus', showcase_menus)):
        fn().save(os.path.join(PREVIEWS, name + '.png'), optimize=True)
        print(name, 'ok')
