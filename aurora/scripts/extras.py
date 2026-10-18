"""Armas Aurora: recoloreado estático, sin cambiar ningún texel de la silueta.

Usa AURORA_REF, AURORA_RP y AURORA_PREVIEWS igual que gear.py.

Todo se pinta con unas pocas rampas de 5 tonos que comparten el contorno violeta (OUT) de las
herramientas de diamante y netherita de gear.py: madera lavanda, hilo celeste, metal perla
(los mismos tonos ópalo de la netherita), oro pastel y rosa. Cada objeto conserva el reparto de
luces y sombras vanilla (así se sigue reconociendo) pero con menos colores compitiendo: nada de
arcoíris por píxel ni lavados a blanco. Los estados del arco/ballesta usan un pintor que solo mira
el color vanilla (nunca la posición), así que el mismo color sale igual en todos los estados.
El libro encantado NO se toca: el usuario usa "Enchanted Books: Re-covered".
"""
import os
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # build.py usa -I
import gear
from gear import C, OUT, P, WHITE, hsv, mix

ROOT = Path(__file__).resolve().parents[1]
REF = Path(os.environ.get('AURORA_REF', Path.home() / 'ref63')) / 'assets/minecraft/textures'
TX = Path(os.environ.get('AURORA_RP', ROOT / 'packs')) / 'Aurora Pack/assets/minecraft/textures'
PREVIEWS = Path(os.environ.get('AURORA_PREVIEWS', ROOT / 'previews'))

ITEMS = (
    'bow', 'bow_pulling_0', 'bow_pulling_1', 'bow_pulling_2',
    'crossbow_standby', 'crossbow_pulling_0', 'crossbow_pulling_1',
    'crossbow_pulling_2', 'crossbow_arrow', 'crossbow_firework',
    'mace', 'totem_of_undying', 'arrow', 'spectral_arrow', 'ender_pearl',
)
OPTIONAL = ('tipped_arrow_head', 'tipped_arrow_base')
# combat / magic / utility items repainted with the generic Aurora painter (hue families -> pastel anchors).
# enchanted_book is left out on purpose: the user stacks "Enchanted Books: Re-covered" for the books.
GENERIC = (
    'trident', 'elytra', 'elytra_broken', 'firework_rocket', 'firework_star', 'wind_charge', 'breeze_rod',
    'blaze_rod', 'blaze_powder', 'ender_eye', 'golden_apple', 'nether_star', 'echo_shard', 'experience_bottle',
    'potion', 'splash_potion', 'lingering_potion', 'spyglass', 'fishing_rod', 'fishing_rod_cast',
    'shears', 'flint_and_steel', 'goat_horn', 'name_tag', 'lead', 'brush',
)
WORN = ('entity/equipment/wings/elytra.png',)
SHIELDS = ('shield_base', 'shield_base_nopattern')

# ------------------------------------------------------------------ shared Aurora ramps (dark -> light)
# Every ramp starts at (or near) the violet outline of gear.py so all items read as one family.
WOOD = (OUT, (92, 70, 156), (134, 110, 206), (178, 162, 240), (220, 212, 255))        # lavender wood
THREAD = ((70, 64, 140), (110, 124, 200), (152, 188, 238), (204, 228, 255), WHITE)    # sky string / flint
PEARL = (OUT, (96, 84, 160), (142, 134, 206), (194, 190, 240), (246, 244, 255))       # neutral greys
GOLD = ((96, 52, 98), (204, 134, 92), (246, 198, 100), (255, 224, 128), (255, 242, 196))
ROSE = ((106, 44, 108), (190, 88, 152), (236, 132, 184), (255, 174, 210), (255, 224, 238))
MINT = ((44, 92, 110), (70, 170, 160), (120, 232, 200), (190, 252, 228), (236, 255, 246))
NAVY = (OUT, (72, 54, 128), (98, 76, 160))                                            # firework body
# pearl metal = the opal tones of the netherite in gear.py (fallback keeps this script working on its own)
_OPAL = getattr(gear, 'OPAL_TONES', [(158, 142, 214), (192, 182, 236), (220, 214, 250), (243, 241, 255)])
METAL = (OUT, (98, 82, 164)) + tuple(_OPAL)


def clamp01(t):
    return 0.0 if t < 0 else 1.0 if t > 1 else t


def ramp(stops, t):
    t = clamp01(t) * (len(stops) - 1)
    i = min(int(t), len(stops) - 2)
    return mix(stops[i], stops[i + 1], t - i)


def family(base):
    """5-tone ramp for one pastel colour: violet outline -> darker shades that keep their saturation (mixing a
    pastel straight into violet gives grey mud) -> the pastel -> soft highlight (never pure white)"""
    dark = tuple(c * 0.42 for c in base)
    mid = tuple(c * 0.7 for c in base)
    return (OUT, mix(dark, OUT, 0.3), mix(mid, OUT, 0.1), base, mix(base, WHITE, 0.55))


# Pastel anchors for the generic painter: every vanilla hue family lands on the closest Aurora colour.
ANCHORS = ((0, (255, 150, 190)), (28, (255, 180, 146)), (50, (255, 218, 136)), (85, (188, 240, 150)),
           (140, (124, 232, 196)), (185, (118, 208, 250)), (225, (146, 166, 250)), (265, (182, 150, 250)),
           (305, (232, 150, 232)), (360, (255, 150, 190)))


def aurora_hue(h):
    for (h0, c0), (h1, c1) in zip(ANCHORS, ANCHORS[1:]):
        if h <= h1:
            return mix(c0, c1, (h - h0) / (h1 - h0))
    return ANCHORS[-1][1]


def is_oak(p):
    """the oak wood shared by bow, arrow, fishing rod, brush... (and the crossbow's darker wood)"""
    h, s, v = hsv(p)
    return 26 <= h <= 42 and 0.55 <= s <= 0.82 and v < 0.75


def wood(v):
    return ramp(WOOD, (v - 0.16) / 0.5)


def thread(v):
    """string and grey fittings: light enough to read on a dark slot, a soft sky tone so they never turn white"""
    return ramp(THREAD, 0.42 + (v - 0.25) / 0.75 * 0.58)


def luma(p):
    return (0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]) / 255


def tone(p, lo, hi):
    """perceived brightness (a saturated dark orange is dark even if its HSV value is high), slightly stretched
    inside the item: pale items stay pale (wind charge) and outline-less ones still get a shade (blaze rod)"""
    lum = luma(p)
    return clamp01(0.8 * (lum - 0.06) / 0.82 + 0.2 * (lum - lo) / max(1e-6, hi - lo))


# ------------------------------------------------------------------ painters
def weapon_pixel(p):
    """El mismo color vanilla siempre produce el mismo color en cada estado del arco/ballesta."""
    hue, sat, value = hsv(p)
    if is_oak(p) or (15 <= hue <= 55 and sat > 0.3 and value < 0.5):
        return wood(value)
    if sat < 0.12:                                   # cuerda, herrajes y punta de flecha
        return thread(value)
    if (hue < 12 or hue > 340) and sat > 0.5:        # papel del cohete cargado
        return ramp(ROSE, (value - 0.35) / 0.55)
    if 200 <= hue <= 250:                            # cuerpo azul marino del cohete
        return ramp(NAVY, (value - 0.12) / 0.2)
    if 170 <= hue < 200:                             # mecha del cohete
        return thread(0.45 + value * 0.55)
    return thread(value)


def gold_px(p, lo, hi):
    """golden items stay gold (plum shade -> honey -> cream); greens become mint gems"""
    hue, sat, value = hsv(p)
    if 90 < hue < 170 and sat > 0.3:
        return ramp(MINT, 0.15 + 0.5 * value)
    return ramp(GOLD, tone(p, lo, hi) ** 1.3)


def generic_px(p, lo, hi):
    """dark -> violet outline, oak -> lavender wood, greys -> pearl, colours -> their pastel family, keeping the
    vanilla light and shade so every item stays recognisable"""
    hue, sat, value = hsv(p)
    if value < 0.16:
        return OUT
    if is_oak(p):
        return wood(value)
    t = tone(p, lo, hi)
    if sat < 0.15:
        return ramp(PEARL, t)
    if (hue < 14 or hue > 340) and sat > 0.5:          # vanilla reds -> the same rose as the loaded crossbow
        return ramp(ROSE, (value - 0.35) / 0.55)
    # colours sit a step higher than greys: vanilla browns/teals are dark and would turn to mud as pastels
    return ramp(family(aurora_hue(hue)), 0.2 + 0.85 * t)


def mace_px(p):
    hue, sat, value = hsv(p)
    if sat > 0.35:                                   # mango azul -> madera lavanda
        return ramp(WOOD, (value - 0.3) / 0.8)
    return ramp(METAL, (value - 0.16) / 0.5)        # cabeza: metal perla de la netherita


def shield_px(p):
    """lavender boards + pearl metal rim; the banner area (near white) stays almost white for the patterns"""
    hue, sat, value = hsv(p)
    if value < 0.27:
        return OUT
    if sat > 0.3:
        return ramp(WOOD, 0.2 + (value - 0.3) / 0.25 * 0.55)
    if value > 0.88:
        return mix(METAL[-1], WHITE, 0.6)
    return ramp(METAL, 0.15 + (value - 0.27) / 0.45 * 0.75)


GOLDEN = ('totem_of_undying', 'golden_apple', 'spectral_arrow')
WARM_METAL = ('spyglass', 'blaze_rod', 'blaze_powder')   # copper / fire -> the same pastel gold, cyan lens kept


def paint_pixel(p, name, lo, hi):
    if name.startswith(('bow', 'crossbow')) or name in ('arrow', 'tipped_arrow_base'):
        return weapon_pixel(p)
    if name == 'tipped_arrow_head':
        # El juego multiplica esta capa por el color de la poción. Perla casi
        # neutra conserva su lectura; no se cambia el modelo ni el tinte vanilla.
        value = hsv(p)[2]
        return mix((166, 159, 184), WHITE, value) if value >= 0.3 else (72, 68, 82)
    if name.startswith('shield_base'):
        return shield_px(p)
    if name in GOLDEN:
        return gold_px(p, lo, hi)
    if name in WARM_METAL and hsv(p)[0] < 60 and hsv(p)[1] > 0.3:
        return gold_px(p, lo, hi)
    if name == 'mace':
        return mace_px(p)
    return generic_px(p, lo, hi)


def recolor(original, name):
    result = original.copy()  # incluso el RGB de los píxeles transparentes se conserva
    pixels = [original.getpixel((x, y)) for y in range(original.height) for x in range(original.width)]
    values = [luma(q) for q in pixels if q[3]]
    lo, hi = min(values), max(values)
    for y in range(original.height):
        for x in range(original.width):
            pixel = original.getpixel((x, y))
            if pixel[3]:
                result.putpixel((x, y), C(paint_pixel(pixel, name, lo, hi), pixel[3]))
    if result.size != original.size or result.getchannel('A').tobytes() != original.getchannel('A').tobytes():
        raise ValueError('La silueta vanilla ha cambiado: ' + name)
    return result


def texture_paths():
    paths = ['item/' + name + '.png' for name in ITEMS]
    paths += ['item/' + name + '.png' for name in OPTIONAL if (REF / 'item' / (name + '.png')).is_file()]
    paths += ['item/' + name + '.png' for name in GENERIC if (REF / 'item' / (name + '.png')).is_file()]
    paths += [rel for rel in WORN if (REF / rel).is_file()]
    for name in SHIELDS:
        # La 26.3 los tiene dentro de entity/shield/ (ver atlases/shield_patterns.json).
        candidates = ('entity/shield/' + name + '.png', 'entity/' + name + '.png')
        path = next((rel for rel in candidates if (REF / rel).is_file()), None)
        if path is None:
            raise FileNotFoundError('Falta ' + name + '; vuelve a ejecutar fetch_ref.py')
        paths.append(path)
    return paths


def preview(rows):
    items = [row for row in rows if row[0].startswith('item/')]
    shields = [row for row in rows if row[0].startswith('entity/')]
    item_height = ((len(items) + 3) // 4) * 166
    shield_height = ((len(shields) + 1) // 2) * 304
    sheet = Image.new('RGBA', (1088, 78 + item_height + shield_height), (25, 21, 42, 255))
    draw = ImageDraw.Draw(sheet)
    title = ImageFont.load_default(size=23)
    font = ImageFont.load_default(size=14)
    draw.text((20, 12), 'AURORA / ARMAS, MAGIA Y UTILIDAD', font=title, fill=C(P[0]))
    draw.text((20, 46), 'Vanilla a la izquierda / Aurora a la derecha / Mismo tamano y transparencia', font=font, fill=C(P[2]))

    def cell(row, left, top, cell_width, scale):
        rel, before, after = row
        draw.text((left + 12, top), Path(rel).stem, font=font, fill=C(WHITE))
        for i, im in enumerate((before, after)):
            enlarged = im.resize((im.width * scale, im.height * scale), Image.Resampling.NEAREST)
            x = left + i * (cell_width // 2) + (cell_width // 2 - enlarged.width) // 2
            y = top + 26
            draw.rectangle((x, y, x + enlarged.width - 1, y + enlarged.height - 1), fill=(49, 42, 70, 255))
            sheet.alpha_composite(enlarged, (x, y))
            draw.text((x, y + enlarged.height + 5), ('VANILLA', 'AURORA')[i], font=font, fill=C(P[2]))

    for i, row in enumerate(items):
        cell(row, (i % 4) * 272, 78 + (i // 4) * 166, 272, 6)
    for i, row in enumerate(shields):
        cell(row, (i % 2) * 544, 78 + item_height + (i // 2) * 304, 544, 3)
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    sheet.convert('RGB').save(PREVIEWS / 'extras.png', optimize=True)


def main():
    rows = []
    for rel in texture_paths():
        with Image.open(REF / rel) as source:
            before = source.convert('RGBA')
        after = recolor(before, Path(rel).stem)
        dest = TX / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        after.save(dest, optimize=True)
        # Permite regenerar sin que sobreviva una animación de una versión anterior.
        dest.with_suffix('.png.mcmeta').unlink(missing_ok=True)
        rows.append((rel, before, after))
    preview(rows)
    print('extras: %d texturas; tamaños y canales alpha idénticos a vanilla' % len(rows))


if __name__ == '__main__':
    main()
