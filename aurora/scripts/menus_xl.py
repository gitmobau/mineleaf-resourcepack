# Aurora HUD XL, themed container screens that stick out of their vanilla rectangle.
# Every container screen of 26.3 gets its own look (themes in menu_themes.py, list in SCREENS below).
#
# The game blits a fixed WxH UV window (usually 176x166) of the screen's texture. Here the texture holds the bigger art from (0,0)
# and every corner of every blit carries two marker texels (see position_tex_color.vsh):
#   marker (pad_x, pad_y, 167, role) at the corner texel, shift (du, dv, 168, role) one texel inward along x.
# The shader moves the vertex out by the pads and its UV by the shift, so the vanilla slots stay where the game
# expects them and the frame, crests and ornaments are drawn around them.
import os, sys, math, json, random
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # build.py runs scripts with -I
import magic
from hud_xl import cyc, mix, C, OUT, WHITE, MARK, TX, PREVIEWS, AURORA
from menu_themes import *

SHIFT = 168
rnd = random.Random

def ref(rel):
    return magic.ref(rel)


# ------------------------------------------------------------------ containers
# Each screen: theme, label plaques in vanilla coords (x0, y0, x1, y1), how it is blitted, and the label texts
# used by the preview (text, x, y; x None = centred). The vanilla texture gives size and slot layout.
# Plaques: a light plate with a rim in the theme's colour behind every title: the game draws container labels in
# dark grey (0x404040), which disappears on the dark panels of most themes.
HEAD = 'head'                                    # full-width title strip (5, 3, w - 6, 16)
def S(theme, plaques=(HEAD, 'inv'), kind='single', title=None, inv=True, origin=(0, 0)):
    return dict(theme=theme, plaques=plaques, kind=kind, title=title, inv=inv, origin=origin)
SCREENS = {
    'inventory':         S(Observatory(), [(94, 5, 170, 17)], title=('Fabricación', 97, 8), inv=False),
    'crafting_table':    S(Fabricator(), [(26, 3, 112, 16), 'inv'], title=('Fabricación', 29, 6)),
    'furnace':           S(Inferno(), [(38, 3, 138, 16), 'inv'], title=('Horno', None, 6)),
    'blast_furnace':     S(Supernova(), [(38, 3, 138, 16), 'inv'], title=('Alto horno', None, 6)),
    'smoker':            S(Clouds(), [(38, 3, 138, 16), 'inv'], title=('Ahumador', None, 6)),
    'generic_54':        S(Vault(), [(5, 3, 100, 16), (5, 127, 90, 139)], kind='chest', title=('Cofre grande', 8, 6)),
    'shulker_box':       S(EndShell(), [(5, 3, 100, 16), 'inv'], title=('Caja de shulker', 8, 6)),
    'anvil':             S(Smithy(), [(57, 3, 170, 16), 'inv'], title=('Reparar y renombrar', 60, 6)),
    'beacon':            S(Lighthouse(), [], title=None, inv=False),
    'brewing_stand':     S(Alchemy(), title=('Soporte para pociones', None, 6)),
    'cartography_table': S(Cartographer(), [(5, 1, 170, 13), 'inv'], title=('Mesa de cartografía', 8, 4)),
    'crafter':           S(Automaton(), title=('Crafteador', None, 6)),
    'dispenser':         S(Launcher(), title=('Dispensador', None, 6)),
    'enchanting_table':  S(Arcane(), title=('Encantar', 12, 5)),
    'grindstone':        S(Grinder(), title=('Reparar y desencantar', 8, 6)),
    'hopper':            S(StarHopper(), title=('Tolva', 8, 6)),
    'horse':             S(Stable(), title=('Caballo', 8, 6)),
    'loom':              S(Weaver(), [(5, 1, 170, 13), 'inv'], title=('Telar', 8, 4)),
    'nautilus':          S(Reef(), title=('Nautilus', 8, 6)),
    'smithing':          S(Armory(), [(40, 12, 130, 25), 'inv'], title=('Mejorar equipo', 44, 15)),
    'stonecutter':       S(Geode(), title=('Cortapiedras', 8, 6)),
    'villager':          S(Market(), [HEAD, (104, 69, 190, 81)], title=('Granjero - Aprendiz', None, 6), inv=(107, 72)),
    'creative_inventory/tab_items':       S(Creator(), [(5, 3, 120, 16)], title=('Buscar objetos', 8, 6), inv=False),
    'creative_inventory/tab_item_search': S(Creator(), [(5, 3, 85, 16)], title=('Buscar objetos', 8, 6), inv=False),
    'creative_inventory/tab_inventory':   S(Creator(), [], title=None, inv=False),
    # not containers, but drawn the same way (one blit of a fixed window)
    '../recipe_book':    S(Cookbook(), [], title=None, inv=False, origin=(1, 1)),
    'gamemode_switcher': S(ModePortal(), [], title=None, inv=False),
}

def geometry(name):
    """vanilla window (cropped to the blitted rectangle), its width/height, origin and the texture size"""
    v = ref('gui/container/%s.png' % name)
    u0, v0 = SCREENS[name]['origin']
    bb = v.getbbox()
    w, h = bb[2] - u0, bb[3] - v0
    return v.crop((u0, v0, u0 + w, v0 + h)), w, h, (u0, v0), v.size

def quads(kind, h):
    """vanilla blits as (v0, v1) texel rows; the chest draws rows*18+17 of the top part plus the bottom 96"""
    if kind == 'single': return [(0, h, 'tb')]
    return [(0, r * 18 + 17, 't') for r in range(1, 7)] + [(126, 222, 'b')]

def write_markers(img, kind, w, h, pads, origin=(0, 0)):
    l, t, r, b = pads; ou, ov = origin
    for (v0, v1, edge) in quads(kind, h):
        top_pad = t if 't' in edge else 0; bot_pad = b if 'b' in edge else 0
        dv_top = 0 if v0 == 0 else t                       # UV shift of this blit's top edge
        dv_bot = t + bot_pad                               # ... and of its bottom edge
        xl, xr, yt, yb = ou, ou + w - 1, ov + v0, ov + v1 - 1
        for (x, y, role, px_, py_, du, dv) in ((xl, yt, 1, l, top_pad, 0, dv_top), (xr, yt, 2, r, top_pad, l + r, dv_top),
                                               (xl, yb, 3, l, bot_pad, 0, dv_bot), (xr, yb, 4, r, bot_pad, l + r, dv_bot)):
            if role in (1, 2) and v0 != 0 and img.getpixel((x, y))[2] == MARK: continue
            img.putpixel((x, y), (px_, py_, MARK, role))
            img.putpixel((x + (1 if role in (1, 3) else -1), y), (du, dv, SHIFT, role))

def plaque_rects(cfg, w, h):
    out = []
    for p in cfg['plaques']:
        if p == HEAD: out.append((5, 3, w - 6, 16))
        elif p == 'inv': out.append((5, h - 97, 90, h - 85))
        else: out.append(p)
    return out

def build(name):
    cfg = SCREENS[name]; theme = cfg['theme']; kind = cfg['kind']
    v, w, h, origin, tsize = geometry(name)
    l, t, r, b = theme.pads
    AW, AH = w + l + r, h + t + b
    assert origin[0] + AW <= tsize[0] and origin[1] + AH <= tsize[1], (name, AW, AH, tsize)
    va = lambda x, y: v.getpixel((x, y))[3] if 0 <= x < w and 0 <= y < h else 255
    art = Image.new('RGBA', (AW, AH))
    used = set()
    # panel + frame band (rounded rect from -4 to +w+3 around the vanilla rectangle)
    band = theme.band; BW = len(band)
    x0, y0, x1, y1, R = l - 4, t - 4, l + w + 3, t + h + 3, 6
    for y in range(max(0, y0), min(AH, y1 + 1)):
        for x in range(max(0, x0), min(AW, x1 + 1)):
            cx = min(max(x, x0 + R), x1 - R); cy = min(max(y, y0 + R), y1 - R)
            d = math.hypot(x - cx, y - cy)
            if d > R + 0.4: continue
            e = min(x - x0, x1 - x, y - y0, y1 - y)
            if (x < x0 + R or x > x1 - R) and (y < y0 + R or y > y1 - R): e = int(R - d)
            if e < BW: art.putpixel((x, y), C(band[e])); continue
            a = va(x - l, y - t)                               # keep vanilla holes / translucency inside
            if a == 0: used.add((x, y)); continue
            c = theme.bg(x - l, y - t, w, h)
            art.putpixel((x, y), C(c) if a == 255 else C(*theme.translucent(c, a)))
    # label plaques first: slots and vanilla decorations are drawn over them, never hidden
    for (px0, py0, px1, py1) in plaque_rects(cfg, w, h):
        light, accent = theme.plaque
        fill = mix(light, accent, 0.14)                    # light plate: the game writes the labels in dark grey
        rim = mix(accent, (18, 10, 36), 0.35)
        m = rect(art.size, l + px0, t + py0, l + px1, t + py1)
        m -= {(l + px0, t + py0), (l + px1, t + py0), (l + px0, t + py1), (l + px1, t + py1)}
        paint(art, m, lambda x, y: mix(fill, WHITE, 0.6) if y == t + py0 + 1 else
              mix(fill, accent, 0.12) if y == t + py1 - 1 else fill, line=rim, bevel=False)
        used |= rect(art.size, l + px0 - 2, t + py0 - 2, l + px1 + 2, t + py1 + 2)
    # entity window (black area of the vanilla texture)
    blk = [(x + l, y + t) for y in range(h) for x in range(w) if magic.is_rgb(v.getpixel((x, y)), 0)]
    blk_set = set(blk)
    if blk: theme.window(art, blk); used |= blk_set
    # slots
    slots = magic.find_slots(v, w, h)
    in_slot = {(sx + i, sy + j) for (sx, sy, s) in slots for i in range(s) for j in range(s)}
    for (sx, sy, s) in slots:
        rim_tl, rim_br, top, bot = theme.slot
        for j in range(s):
            for i in range(s):
                if i in (0, s - 1) and j in (0, s - 1): continue
                if i == 0 or j == 0: c = rim_tl
                elif i == s - 1 or j == s - 1: c = rim_br
                else:
                    c = mix(top, bot, j / s)
                    if i + j in (3, 4): c = mix(c, WHITE, 0.25)
                art.putpixel((l + sx + i, t + sy + j), C(c))
        used |= rect(art.size, l + sx - 2, t + sy - 2, l + sx + s + 1, t + sy + s + 1)
    # other vanilla decorations (arrows, icons, list panels) in the theme colours
    feats = [(x, y) for y in range(4, h - 4) for x in range(4, w - 4)
             if v.getpixel((x, y))[3] and not magic.is_rgb(v.getpixel((x, y)), 198) and (x + l, y + t) not in blk_set
             and (x, y) not in in_slot]
    for (x, y) in feats:
        p = v.getpixel((x, y)); lum = (p[0] + p[1] + p[2]) / 765
        if magic.is_rgb(p, 139):          # slot grey the detector missed (joined to tubes, e.g. brewing bottles)
            rim_tl, rim_br, top, bot = theme.slot
            c = mix(top, bot, 0.5)
        else:
            c = theme.feature(lum, x, w)
        art.putpixel((x + l, y + t), C(c, p[3]))
    for (x, y) in feats:
        used |= rect(art.size, x + l - 1, y + t - 1, x + l + 1, y + t + 1)
    # small theme motifs in free panel space (not between chest rows: that part gets cut)
    rr = rnd(sum(map(ord, name)))
    placed = 0
    for _ in range(3000):
        x = rr.randint(l + 8, l + w - 9); y = rr.randint(t + 8, t + h - 9)
        if kind == 'chest' and t + 14 < y < t + 142: continue
        if all((xx, yy) not in used for xx in range(x - 3, x + 4) for yy in range(y - 3, y + 4)):
            theme.motif(art, x, y, rr); used |= rect(art.size, x - 4, y - 4, x + 4, y + 4); placed += 1
            if placed >= 10: break
    theme.ornaments(art, l, t, w, h)
    img = Image.new('RGBA', tsize); img.alpha_composite(art, origin)
    write_markers(img, kind, w, h, theme.pads, origin)
    p = os.path.normpath(TX + 'gui/container/%s.png' % name)
    os.makedirs(os.path.dirname(p), exist_ok=True); img.save(p, optimize=True)
    return img

# ------------------------------------------------------------------ shader emulation (preview + self-test)
ROLE = [1, 3, 4, 2]
def emulate(tex, quad, uv):
    """run position_tex_color.vsh on one GUI quad: quad/uv = (x0, y0, x1, y1) in GUI px / texels"""
    px = tex.load(); W, Hh = tex.size
    verts = [((quad[0], quad[1]), (uv[0], uv[1])), ((quad[0], quad[3]), (uv[0], uv[3])),
             ((quad[2], quad[3]), (uv[2], uv[3])), ((quad[2], quad[1]), (uv[2], uv[1]))]
    out = []
    for vid, ((x, y), (u, v)) in enumerate(verts):
        role = ROLE[vid % 4]; d = (1 if role in (1, 3) else -1, 1 if role <= 2 else -1)
        m = px[int(math.floor(u + d[0] * 0.5)), int(math.floor(v + d[1] * 0.5))]
        if m[2] == MARK and m[3] == role:
            x -= d[0] * m[0]; y -= d[1] * m[1]
            s = px[int(math.floor(u + d[0] * 1.5)), int(math.floor(v + d[1] * 0.5))]
            if s[2] == SHIFT and s[3] == role: u += s[0]; v += s[1]
        out.append((x, y, u, v))
    (qx0, qy0, u0, v0), (_, qy1, _, v1), (qx1, _, u1, _) = out[0], out[1], out[2]
    assert (qx1 - qx0, qy1 - qy0) == (u1 - u0, v1 - v0), (quad, uv, out)    # stays pixel perfect
    assert out[3] == (qx1, qy0, u1, v0) and out[1][0] == qx0 and out[2][1] == qy1, out
    piece = tex.crop((int(u0), int(v0), int(u1), int(v1))).copy()
    pp = piece.load()
    for y in range(piece.height):                              # fragment shader: hide marker texels
        for x in range(piece.width):
            q = pp[x, y]
            if q[2] in (MARK, SHIFT) and 1 <= q[3] <= 4:
                ny = y + (1 if q[3] <= 2 else -1)
                pp[x, y] = tex.getpixel((int(u0) + x, int(v0) + ny))
    return (int(qx0), int(qy0)), piece

def screen(name, tex, rows=6):
    _, w, h, (u0, v0), _ = geometry(name)
    hh = h if name != 'generic_54' else 114 + rows * 18
    W, Hh = 340, 290
    sc = Image.new('RGBA', (max(W, w + 64), Hh), (30, 26, 44, 255))
    lx, ly = (sc.width - w) // 2, (Hh - hh) // 2 + 6
    if name == 'generic_54':
        top = rows * 18 + 17
        for q, uv in (((lx, ly, lx + w, ly + top), (0, 0, w, top)),
                      ((lx, ly + top, lx + w, ly + top + 96), (0, 126, w, 222))):
            at, piece = emulate(tex, q, uv); sc.alpha_composite(piece, at)
    else:
        at, piece = emulate(tex, (lx, ly, lx + w, ly + h), (u0, v0, u0 + w, v0 + h)); sc.alpha_composite(piece, at)
    return sc, (lx, ly), w, hh

def previews(imgs):
    from PIL import ImageFont
    F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 8)
    tiles = []
    icons = ['diamond_sword', 'netherite_pickaxe', 'diamond_axe', 'diamond_chestplate', 'netherite_helmet']
    for name, cfg in SCREENS.items():
        for rows in ((6, 3) if name == 'generic_54' else (6,)):
            sc, (lx, ly), w, hh = screen(name, imgs[name], rows)
            d = ImageDraw.Draw(sc)
            if cfg['title']:
                title, tx, ty = cfg['title']
                if tx is None: tx = (w - d.textlength(title, font=F)) // 2
                d.text((lx + tx, ly + ty - 1), title, font=F, fill=(64, 64, 64))      # vanilla label colour 0x404040
            if cfg['inv']:
                ix, iy = cfg['inv'] if isinstance(cfg['inv'], tuple) else (8, hh - 94)
                d.text((lx + ix, ly + iy - 1), 'Inventario', font=F, fill=(64, 64, 64))
            v, _, h, _, _ = geometry(name)
            for k, (sx, sy, s) in enumerate(magic.find_slots(v, w, h)):
                if name == 'generic_54' and sy >= 17 + rows * 18 and sy < 126: continue
                yy = sy if not (name == 'generic_54' and sy >= 126) else sy - 126 + rows * 18 + 17
                if k % 3 == 0:
                    ic = Image.open(AURORA + 'item/%s.png' % icons[k % len(icons)]).convert('RGBA').crop((0, 0, 16, 16))
                    sc.alpha_composite(ic, (lx + sx + 1 + (s - 18) // 2, ly + yy + 1 + (s - 18) // 2))
            tiles.append(sc)
    k = 2; cols = 3
    W = max(t.width for t in tiles) * k; Hh = max(t.height for t in tiles) * k
    def sheet(ts, path):
        out = Image.new('RGB', (cols * W + (cols + 1) * 10, ((len(ts) + cols - 1) // cols) * (Hh + 10) + 10), (20, 18, 30))
        for i, tl in enumerate(ts):
            im = tl.resize((tl.width * k, tl.height * k), Image.NEAREST)
            out.paste(im, (10 + (i % cols) * (W + 10) + (W - im.width) // 2, 10 + (i // cols) * (Hh + 10)))
        out.save(path)
    os.makedirs(PREVIEWS, exist_ok=True)
    sheet(tiles[:8], PREVIEWS + '/menus_xl.png')
    sheet(tiles[8:20], PREVIEWS + '/menus_xl_2.png')
    sheet(tiles[20:], PREVIEWS + '/menus_xl_3.png')

if __name__ == '__main__':
    imgs = {n: build(n) for n in SCREENS}
    previews(imgs)
    print('menus ok', len(imgs))
