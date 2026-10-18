# Aurora screens without a container: book, signs, menu backgrounds (options, pause, world list...), widgets
# (buttons, sliders, text fields, checkboxes, tabs...), tooltips, game mode switcher icons and the title logo.
# All of these are recoloured in place (same size, same nine-slice settings), so they need no shader.
import os, math, json, colorsys, shutil
from PIL import Image

HOME = os.path.expanduser('~')
# Paths can be overridden by build.py (AURORA_REF = folder holding assets/minecraft of vanilla 26.3,
# AURORA_RP = resourcepacks folder).
REF_ROOT = os.environ.get('AURORA_REF', HOME + '/ref63')
RP = os.environ.get('AURORA_RP', HOME + '/mnt/.minecraft/resourcepacks')
REF = REF_ROOT + '/assets/minecraft/textures/'
TX = RP + '/Aurora Pack/assets/minecraft/textures/'

P = [(123, 225, 249), (155, 210, 248), (187, 185, 248), (220, 181, 240), (248, 176, 234),
     (248, 188, 199), (248, 201, 173), (248, 225, 156), (209, 248, 145), (170, 245, 215)]
WHITE = (255, 255, 255)
OUT = (52, 36, 98)

def mix(a, b, f): return tuple(a[k] + (b[k] - a[k]) * f for k in range(3))
def C(c, a=255): return tuple(int(max(0, min(255, round(v)))) for v in c[:3]) + (int(max(0, min(255, a))),)
def cyc(t, pal=P):
    t = (t % 1.0) * len(pal); i = int(t) % len(pal); f = t - int(t)
    return mix(pal[i], pal[(i + 1) % len(pal)], f)
def grad(stops, t):
    t = max(0.0, min(1.0, t)) * (len(stops) - 1); i = min(int(t), len(stops) - 2)
    return mix(stops[i], stops[i + 1], t - i)
def lum(p): return (p[0] + p[1] + p[2]) / 765

def ref(rel): return Image.open(REF + rel).convert('RGBA')

def save(im, rel):
    """write the texture and carry over the vanilla .mcmeta (nine-slice settings must survive)"""
    p = TX + rel
    os.makedirs(os.path.dirname(p), exist_ok=True)
    im.save(p, optimize=True)
    if os.path.exists(REF + rel + '.mcmeta'):
        shutil.copyfile(REF + rel + '.mcmeta', p + '.mcmeta')

def ramp_recolor(rel, stops):
    """per-pixel luminance -> colour ramp; nine-slice safe (colour never depends on position)"""
    v = ref(rel); o = Image.new('RGBA', v.size)
    for y in range(v.height):
        for x in range(v.width):
            p = v.getpixel((x, y))
            if p[3]: o.putpixel((x, y), C(grad(stops, lum(p)), p[3]))
    save(o, rel)

# ------------------------------------------------------------------ widgets
NORMAL = [OUT, (64, 46, 118), (112, 88, 186), (186, 170, 240), WHITE]
HIGH = [(70, 30, 90), (110, 56, 150), (200, 110, 210), (255, 196, 238), WHITE]
DISABLED = [(28, 24, 40), (54, 50, 72), (88, 84, 108), (132, 128, 152), (180, 176, 198)]

def widgets():
    n = 0
    for f in sorted(os.listdir(REF + 'gui/sprites/widget')):
        if not f.endswith('.png'): continue
        rel = 'gui/sprites/widget/' + f
        stops = DISABLED if 'disabled' in f else HIGH if ('highlighted' in f or 'selected' in f) else NORMAL
        ramp_recolor(rel, stops); n += 1
    for rel in ('gui/sprites/popup/background.png', 'gui/sprites/gamemode_switcher/slot.png'):
        ramp_recolor(rel, NORMAL); n += 1
    ramp_recolor('gui/sprites/gamemode_switcher/selection.png', HIGH); n += 1
    return n

# ------------------------------------------------------------------ tooltip
def tooltip():
    bg = ref('gui/sprites/tooltip/background.png'); o = Image.new('RGBA', bg.size)
    for y in range(bg.height):
        for x in range(bg.width):
            p = bg.getpixel((x, y))
            if p[3]: o.putpixel((x, y), C(mix((22, 14, 46), (40, 24, 70), y / bg.height), p[3]))
    save(o, 'gui/sprites/tooltip/background.png')
    fr = ref('gui/sprites/tooltip/frame.png'); o = Image.new('RGBA', fr.size)
    for y in range(fr.height):
        for x in range(fr.width):
            p = fr.getpixel((x, y))
            if p[3]: o.putpixel((x, y), C(grad([(255, 150, 220), (200, 160, 255), (120, 220, 255)], (y - 9) / 82), p[3]))
    save(o, 'gui/sprites/tooltip/frame.png')

# ------------------------------------------------------------------ menu backgrounds (options, pause, lists...)
def backgrounds():
    for rel, base, dark in (('gui/menu_background.png', (40, 28, 74), (22, 14, 46)),
                            ('gui/menu_list_background.png', (30, 20, 58), (16, 10, 36)),
                            ('gui/inworld_menu_background.png', (40, 28, 74), (22, 14, 46)),
                            ('gui/inworld_menu_list_background.png', (30, 20, 58), (16, 10, 36))):
        v = ref(rel); o = Image.new('RGBA', v.size)
        for y in range(v.height):
            for x in range(v.width):
                p = v.getpixel((x, y))
                c = mix(dark, base, min(1, lum(p) * 3))
                if (x * 7 + y * 5) % 37 == 0: c = mix(c, cyc((x + y) / 32), 0.6)       # tiny stars, tile-safe
                o.putpixel((x, y), C(c, p[3]))
        save(o, rel)
    for rel in ('gui/header_separator.png', 'gui/footer_separator.png',
                'gui/inworld_header_separator.png', 'gui/inworld_footer_separator.png'):
        v = ref(rel); o = Image.new('RGBA', v.size)
        for y in range(v.height):
            for x in range(v.width):
                p = v.getpixel((x, y))
                c = cyc(x / v.width) if lum(p) > 0.3 else (34, 22, 64)            # 32 px period: seamless
                o.putpixel((x, y), C(c, p[3]))
        save(o, rel)

# ------------------------------------------------------------------ signs (sign edit screen)
WOOD_TINT = {'oak': (255, 215, 170), 'spruce': (215, 170, 190), 'birch': (255, 245, 220), 'jungle': (255, 195, 175),
             'acacia': (255, 170, 150), 'dark_oak': (175, 130, 175), 'mangrove': (240, 140, 160), 'cherry': (255, 190, 215),
             'bamboo': (255, 240, 160), 'crimson': (230, 130, 200), 'warped': (130, 225, 210), 'pale_oak': (235, 230, 245),
             'poplar': (215, 240, 175)}

def signs():
    n = 0
    for folder in ('signs', 'hanging_signs'):
        for f in sorted(os.listdir(REF + 'gui/' + folder)):
            if not f.endswith('.png'): continue
            tint = WOOD_TINT.get(f[:-4], (235, 215, 240))
            v = ref('gui/%s/%s' % (folder, f)); o = Image.new('RGBA', v.size)
            for y in range(v.height):
                for x in range(v.width):
                    p = v.getpixel((x, y))
                    if not p[3]: continue
                    l = lum(p)
                    if folder == 'hanging_signs' and p[2] > p[0] + 10 and l < 0.45:   # chains stay metal
                        c = mix((90, 90, 130), (200, 200, 235), l * 2)
                    else:
                        c = mix(mix(tint, OUT, 0.55), mix(tint, WHITE, 0.35), min(1, l * 1.6))
                    o.putpixel((x, y), C(c, p[3]))
            for (x, y) in ((2, 2), (v.width - 4, 3)):                                # two sparkles
                if o.getpixel((x, y))[3]: o.putpixel((x, y), C(mix(tint, WHITE, 0.8)))
            save(o, 'gui/%s/%s' % (folder, f)); n += 1
    return n

# ------------------------------------------------------------------ book
def book():
    v = ref('gui/book.png'); o = Image.new('RGBA', v.size)
    for y in range(v.height):
        for x in range(v.width):
            p = v.getpixel((x, y))
            if not p[3]: continue
            l = lum(p); r, g, b = p[:3]
            if r > 150 and g < 90 and b < 90:                               # red stitching -> pink thread
                c = (255, 150, 205)
            elif l > 0.62:                                                  # page: pearl paper, still light for black text
                c = mix((236, 226, 248), (255, 252, 255), (l - 0.62) / 0.38)
            else:                                                           # leather cover -> violet leather
                c = grad([(40, 22, 70), (96, 60, 150), (160, 120, 215), (220, 190, 250)], l / 0.62)
            o.putpixel((x, y), C(c, p[3]))
    # gold corners on the cover, ribbon bookmark and a star charm in the free margins of the 192x192 window
    for (cx, cy) in ((22, 3), (163, 3), (22, 178), (163, 178)):
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                if abs(dx) + abs(dy) <= 2: o.putpixel((cx + dx, cy + dy), C((255, 220, 130) if abs(dx) + abs(dy) < 2 else (150, 100, 40)))
    for y in range(176, 191):                                               # ribbon
        for x in range(132, 137):
            if y > 187 and abs(x - 134) < (y - 187): continue
            o.putpixel((x, y), C((255, 120, 190) if x < 136 else (210, 80, 160)))
    for y in range(20, 40):                                                 # charm string + star on the right
        o.putpixel((169, y), C((220, 200, 240)))
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            if abs(dx) + abs(dy) <= 3 and (dx == 0 or dy == 0 or abs(dx) + abs(dy) <= 2):
                o.putpixel((169 + dx, 43 + dy), C(mix((255, 236, 150), WHITE, 0.5 if dx < 0 and dy < 0 else 0)))
    o.putpixel((168, 42), C(WHITE))
    save(o, 'gui/book.png')

# ------------------------------------------------------------------ title logo
def logo():
    for rel in ('gui/title/minecraft.png', 'gui/title/minceraft.png', 'gui/title/edition.png'):
        v = ref(rel); o = Image.new('RGBA', v.size)
        for y in range(v.height):
            for x in range(v.width):
                p = v.getpixel((x, y))
                if not p[3]: continue
                l = lum(p)
                if l < 0.18: c = mix(OUT, (20, 12, 40), 1 - l / 0.18)
                else: c = mix(cyc(x / v.width * 0.9 + y / v.height * 0.1), WHITE, max(0, l - 0.35) * 1.1)
                o.putpixel((x, y), C(c, p[3]))
        save(o, rel)

# ------------------------------------------------------------------ boss bars
BOSS = {'pink': [(255, 150, 210), (255, 190, 230), (240, 150, 255)], 'blue': [(120, 200, 255), (150, 225, 255), (170, 180, 255)],
        'red': [(255, 130, 140), (255, 170, 150), (255, 120, 185)], 'green': [(150, 240, 170), (195, 250, 160), (120, 230, 205)],
        'yellow': [(255, 230, 130), (255, 246, 175), (255, 205, 140)], 'purple': [(190, 150, 255), (222, 170, 255), (160, 140, 255)],
        'white': [(236, 238, 255), (255, 255, 255), (222, 228, 250)]}
BN, BFT = 16, 2

def bossbars():
    H = 'gui/sprites/boss_bar/'
    for col, pal in BOSS.items():
        v = ref(H + col + '_background.png'); o = Image.new('RGBA', v.size)
        for y in range(v.height):
            for x in range(v.width):
                p = v.getpixel((x, y)); t = max(p[:3]) / 73
                base = cyc(x / 182, pal)
                o.putpixel((x, y), C(grad([(20, 12, 36), mix(base, (20, 12, 36), 0.72), mix(base, (20, 12, 36), 0.5)], t), p[3]))
        save(o, H + col + '_background.png')
        v = ref(H + col + '_progress.png'); st = Image.new('RGBA', (182, 5 * BN))
        for f in range(BN):
            for y in range(5):
                for x in range(182):
                    p = v.getpixel((x, y))
                    if not p[3]: continue
                    t = max(p[:3]) / 236
                    base = cyc(x / 182 * 0.8 - f / BN, pal)
                    c = grad([mix(base, OUT, 0.55), base, mix(base, WHITE, 0.6)], t)
                    d = abs((x - f * 182 / BN * 2) % 364 - 6)
                    if d < 4: c = mix(c, WHITE, 0.6 * (1 - d / 4))            # shine running along the bar
                    st.putpixel((x, f * 5 + y), C(c, p[3]))
        p_ = TX + H + col + '_progress.png'; os.makedirs(os.path.dirname(p_), exist_ok=True); st.save(p_, optimize=True)
        json.dump({"animation": {"frametime": BFT, "interpolate": False, "width": 182, "height": 5}}, open(p_ + '.mcmeta', 'w'), indent=2)
    for n in (6, 10, 12, 20):
        for part in ('background', 'progress'):
            v = ref(H + 'notched_%d_%s.png' % (n, part)); o = Image.new('RGBA', v.size)
            for y in range(v.height):
                for x in range(v.width):
                    p = v.getpixel((x, y))
                    if p[3]: o.putpixel((x, y), C((40, 20, 72), min(255, p[3] * 1.4)))
            save(o, H + 'notched_%d_%s.png' % (n, part))

# ------------------------------------------------------------------ toasts
DARK = [(14, 8, 30), (34, 22, 64), (62, 44, 110), (150, 130, 220), WHITE]          # text on top is white/yellow
LIGHT = [(110, 60, 130), (200, 160, 230), (236, 224, 250), (250, 244, 255), WHITE]  # text on top is dark purple/black

def toast_panel(w, h, dark):
    """static toast background drawn from scratch: rounded panel, aurora rim, sparkles"""
    o = Image.new('RGBA', (w, h))
    for y in range(h):
        for x in range(w):
            if (x in (0, w - 1) and y in (0, h - 1)): continue
            e = min(x, y, w - 1 - x, h - 1 - y)
            if e == 0: c = OUT
            elif e == 1: c = cyc(x / w * 0.9)
            elif e == 2: c = mix(cyc(x / w * 0.9 + 0.05), WHITE, 0.45)
            else: c = mix((30, 20, 60), (48, 30, 88), y / h) if dark else mix((252, 246, 255), (236, 224, 250), y / h)
            o.putpixel((x, y), C(c))
    for (x, y) in ((w - 12, 6), (w - 22, h - 8), (w - 6, h - 12)):
        for dx, dy, a in ((0, 0, 1), (1, 0, .5), (-1, 0, .5), (0, 1, .5), (0, -1, .5)):
            o.putpixel((x + dx, y + dy), C(mix(o.getpixel((x + dx, y + dy))[:3], WHITE if dark else (255, 160, 210), a)))
    return o

def toasts():
    T = 'gui/sprites/toast/'
    # advancement toast stays vanilla (advancements are left untouched on purpose)
    save(toast_panel(160, 32, False), T + 'recipe.png')
    ramp_recolor(T + 'now_playing.png', DARK)          # nine-slice: colour only from luminance
    ramp_recolor(T + 'system.png', DARK)
    ramp_recolor(T + 'tutorial.png', LIGHT)
    for icon in ('mouse', 'movement_keys', 'right_click'):              # grey tutorial icons; block/item icons stay
        v = ref(T + icon + '.png'); o = Image.new('RGBA', v.size)
        for y in range(v.height):
            for x in range(v.width):
                p = v.getpixel((x, y))
                if not p[3]: continue
                grey = max(p[:3]) - min(p[:3]) < 20
                o.putpixel((x, y), C(grad(NORMAL, lum(p)) if grey else mix(p[:3], (255, 150, 210), 0.5), p[3]))
        save(o, T + icon + '.png')

# ------------------------------------------------------------------ preview (fake options screen, book, signs, logo)
def nine(rel, w, h):
    """draw a nine-slice sprite at w x h (stretching the middle is enough for a preview)"""
    im = Image.open(TX + rel).convert('RGBA'); m = json.load(open(TX + rel + '.mcmeta'))['gui']['scaling']['border']
    m = m if isinstance(m, int) else m['left']
    out = Image.new('RGBA', (w, h)); W, H = im.size
    for (sx0, sx1, dx0, dx1) in ((0, m, 0, m), (m, W - m, m, w - m), (W - m, W, w - m, w)):
        for (sy0, sy1, dy0, dy1) in ((0, m, 0, m), (m, H - m, m, h - m), (H - m, H, h - m, h)):
            if dx1 > dx0 and dy1 > dy0:
                out.alpha_composite(im.crop((sx0, sy0, sx1, sy1)).resize((dx1 - dx0, dy1 - dy0), Image.NEAREST), (dx0, dy0))
    return out

def preview(path):
    from PIL import ImageDraw, ImageFont
    F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 8)
    W, H = 420, 250
    sc = Image.new('RGBA', (W, H))
    for y in range(H):
        for x in range(W): sc.putpixel((x, y), C(mix((120, 170, 230), (250, 200, 220), y / H)))
    bg = Image.open(TX + 'gui/menu_background.png').convert('RGBA')
    for y in range(0, H, 16):
        for x in range(0, W, 16): sc.alpha_composite(bg, (x, y))
    sep = Image.open(TX + 'gui/header_separator.png').convert('RGBA')
    for x in range(0, W, 32): sc.alpha_composite(sep, (x, 30)); sc.alpha_composite(sep, (x, H - 34))
    d = ImageDraw.Draw(sc)
    d.text((W // 2 - 20, 12), 'Opciones', font=F, fill=(255, 255, 255))
    for i, (lab, kind) in enumerate((('Campo de visión: 70', 'slider'), ('Música y sonidos...', 'button'), ('Gráficos...', 'button_highlighted'),
                                     ('Controles...', 'button'), ('Idioma...', 'button_disabled'), ('Paquetes de recursos...', 'button'))):
        x = 60 + (i % 2) * 155; y = 45 + (i // 2) * 26
        sc.alpha_composite(nine('gui/sprites/widget/%s.png' % kind, 150, 20), (x, y))
        if kind == 'slider': sc.alpha_composite(nine('gui/sprites/widget/slider_handle.png', 8, 20), (x + 60, y))
        d.text((x + 75 - d.textlength(lab, font=F) / 2, y + 6), lab, font=F, fill=(160, 160, 160) if 'disabled' in kind else (255, 255, 255))
    sc.alpha_composite(nine('gui/sprites/widget/text_field.png', 150, 20), (60, 128)); d.text((64, 134), 'Nombre del mundo', font=F, fill=(224, 224, 224))
    sc.alpha_composite(Image.open(TX + 'gui/sprites/widget/checkbox_selected.png').convert('RGBA'), (215, 128)); d.text((240, 134), 'Subtítulos', font=F, fill=(255, 255, 255))
    for k, t in enumerate(('tab_selected', 'tab', 'tab_highlighted')):
        sc.alpha_composite(nine('gui/sprites/widget/%s.png' % t, 70, 24), (60 + k * 72, 156))
    tip = nine('gui/sprites/tooltip/background.png', 120, 30); tip.alpha_composite(nine('gui/sprites/tooltip/frame.png', 120, 30))
    sc.alpha_composite(tip, (250, 180)); d.text((262, 190), 'Espada de diamante', font=F, fill=(255, 255, 255))
    sc.alpha_composite(nine('gui/sprites/widget/button.png', 200, 20), (110, H - 26)); d.text((180, H - 20), 'Listo', font=F, fill=(255, 255, 255))
    # book, signs and logo
    bk = Image.open(TX + 'gui/book.png').convert('RGBA').crop((0, 0, 192, 192))
    db = ImageDraw.Draw(bk)
    for i, line in enumerate(('Querido diario:', 'hoy la aurora', 'pintó el cielo', 'de rosa y cian.')):
        db.text((36, 16 + i * 10), line, font=F, fill=(0, 0, 0))
    for n, rel in enumerate(('page_backward', 'page_forward')):
        bk.alpha_composite(Image.open(TX + 'gui/sprites/widget/%s.png' % rel).convert('RGBA'), (43 + n * 73, 157))
    signs_row = Image.new('RGBA', (13 * 30, 70))
    for i, f in enumerate(sorted(os.listdir(TX + 'gui/signs'))):
        s_ = Image.open(TX + 'gui/signs/' + f).convert('RGBA'); signs_row.alpha_composite(s_.resize((s_.width * 1, s_.height * 1)), (i * 30, 0))
        hs = Image.open(TX + 'gui/hanging_signs/' + f).convert('RGBA') if os.path.exists(TX + 'gui/hanging_signs/' + f) else None
        if hs: signs_row.alpha_composite(hs, (i * 30 + 4, 34))
    logo_ = Image.open(TX + 'gui/title/minecraft.png').convert('RGBA').crop((0, 0, 1024, 176)).resize((410, 70), Image.LANCZOS)
    k = 2
    sheet = Image.new('RGBA', (W * k + 192 * k + 30, max(H * k, 192 * k) + 70 * 2 + 180 + 40), (20, 18, 30, 255))
    sheet.alpha_composite(sc.resize((W * k, H * k), Image.NEAREST), (10, 10))
    sheet.alpha_composite(bk.resize((192 * k, 192 * k), Image.NEAREST), (W * k + 20, 10))
    sheet.alpha_composite(signs_row.resize((signs_row.width * k, signs_row.height * k), Image.NEAREST), (10, max(H, 192) * k + 20))
    sheet.alpha_composite(logo_.resize((logo_.width * 2, logo_.height * 2), Image.NEAREST), (10, max(H, 192) * k + 20 + 70 * k + 10))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sheet.convert('RGB').save(path)

# ------------------------------------------------------------------ no titles
# The user does not want the menu titles nor the "Inventory" label: blank their language keys (only these keys are
# overridden; everything else comes from the game's own language file). Titles that are entity or tab names (horse,
# villager, creative tabs) cannot be blanked without hiding those names everywhere, so they stay.
TITLE_KEYS = ('barrel', 'blast_furnace', 'brewing', 'cartography_table', 'chest', 'chestDouble', 'crafter', 'crafting',
              'dispenser', 'dropper', 'enchant', 'enderchest', 'furnace', 'grindstone_title', 'hopper', 'inventory',
              'loom', 'repair', 'shulkerBox', 'smoker', 'stonecutter', 'upgrade')
LANGS = ('en_us', 'en_gb', 'es_es', 'es_mx', 'es_ar', 'es_cl', 'es_uy', 'es_ve')

def hide_titles():
    d = RP + '/Aurora Pack/assets/minecraft/lang/'
    os.makedirs(d, exist_ok=True)
    for lang in LANGS:
        with open(d + lang + '.json', 'w', encoding='utf-8') as f:
            json.dump({'container.' + k: '' for k in TITLE_KEYS}, f, indent=2, sort_keys=True)
    return len(TITLE_KEYS)

if __name__ == '__main__':
    print('titles hidden', hide_titles())
    print('widgets', widgets())
    tooltip(); backgrounds(); book(); logo(); bossbars(); toasts()
    print('signs', signs())
    preview(os.environ.get('AURORA_PREVIEWS', RP + '/Aurora Pack') + '/pantallas.png')
    print('ok')
