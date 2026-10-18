"""Armas Aurora: recoloreado estático, sin cambiar ningún texel de la silueta.

Usa AURORA_REF, AURORA_RP y AURORA_PREVIEWS igual que gear.py.
Los estados del arco/ballesta comparten un pintor independiente de la posición.
"""
import os
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # build.py usa -I
from gear import C, OUT, P, VIVID, WHITE, crystal_px, cyc, hsv, mix

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
# combat / magic / utility items repainted with the generic Aurora painter (hue families -> pastel anchors)
GENERIC = (
    'trident', 'elytra', 'elytra_broken', 'firework_rocket', 'firework_star', 'wind_charge', 'breeze_rod',
    'blaze_rod', 'blaze_powder', 'ender_eye', 'golden_apple', 'nether_star', 'echo_shard', 'experience_bottle',
    'enchanted_book', 'potion', 'splash_potion', 'lingering_potion', 'spyglass', 'fishing_rod', 'fishing_rod_cast',
    'shears', 'flint_and_steel', 'goat_horn', 'name_tag', 'lead', 'brush',
)
WORN = ('entity/equipment/wings/elytra.png',)
SHIELDS = ('shield_base', 'shield_base_nopattern')


def pearl(v):
    """Madera/cuerda lavanda-perla; los valores más oscuros son el contorno."""
    if v < 0.23:
        return OUT
    if v < 0.34:
        return (111, 87, 164)
    return mix(P[2], WHITE, min(0.9, max(0, (v - 0.34) / 0.5)))


# Pastel anchors for the generic painter: every vanilla hue family lands on the closest Aurora colour.
ANCHORS = ((0, (255, 150, 190)), (28, (255, 186, 150)), (50, (255, 226, 150)), (85, (190, 244, 160)),
           (140, (130, 238, 205)), (185, (120, 214, 255)), (225, (150, 170, 255)), (265, (186, 150, 255)),
           (305, (236, 150, 236)), (360, (255, 150, 190)))


def aurora_hue(h):
    for (h0, c0), (h1, c1) in zip(ANCHORS, ANCHORS[1:]):
        if h <= h1:
            return mix(c0, c1, (h - h0) / (h1 - h0))
    return ANCHORS[-1][1]


def aurora_px(p):
    """Generic Aurora repaint: dark -> violet outline, greys -> pearl lavender, colours -> pastel family,
    keeping the vanilla light and shade so every item stays recognisable."""
    hue, sat, value = hsv(p)
    if value < 0.2:
        return OUT
    if sat < 0.15:
        return mix((118, 98, 186), WHITE, min(1, max(0, (value - 0.2) / 0.75)) ** 0.8)
    base = aurora_hue(hue)
    if value < 0.55:
        return mix(base, OUT, min(0.75, (0.55 - value) / 0.35 * 0.75))
    return mix(base, WHITE, min(0.85, (value - 0.55) * 1.6))


GOLDEN = ('totem_of_undying', 'golden_apple')


def gold_px(p):
    """golden items keep their gold: deep rose-gold shade -> honey -> cream highlight; greens become mint gems"""
    hue, sat, value = hsv(p)
    if value < 0.2:
        return OUT
    if 90 < hue < 170 and sat > 0.3:
        return mix((120, 240, 210), WHITE, 0.35 if value > 0.8 else 0)
    if sat < 0.15:
        return mix((255, 240, 210), WHITE, value)
    ramp = ((0.2, (110, 60, 120)), (0.5, (214, 120, 120)), (0.65, (246, 168, 112)), (0.8, (255, 206, 120)),
            (0.92, (255, 232, 160)), (1.0, (255, 250, 222)))
    for (v0, c0), (v1, c1) in zip(ramp, ramp[1:]):
        if value <= v1:
            return mix(c0, c1, (value - v0) / (v1 - v0))
    return ramp[-1][1]


def weapon_pixel(p):
    """El mismo color vanilla siempre produce el mismo color en cada estado."""
    hue, sat, value = hsv(p)
    if 15 <= hue <= 55 and sat > 0.3:  # madera y astil
        return pearl(value)
    if sat < 0.12 and 0.25 <= value <= 0.7:  # cuerda y herrajes grises: claros, que se vean sobre fondo oscuro
        return mix((196, 186, 244), WHITE, (value - 0.25) / 0.45 * 0.8)
    if value < 0.28:
        return OUT
    if value > 0.82 and sat < 0.12:
        return mix(P[0], WHITE, 0.85) if value < 0.98 else WHITE
    # Metal, cuerda y cohete: bandas de cristal estables al tensar/cargar.
    return crystal_px(p, 0.08 + value * 0.55)


def paint_pixel(p, name, x, y, width, height):
    hue, sat, value = hsv(p)
    phase = 0.04 + 0.9 * (x - y + height - 1) / max(1, width + height - 2)
    if name.startswith(('bow', 'crossbow')) or name in ('arrow', 'tipped_arrow_base'):
        return weapon_pixel(p)
    if name == 'tipped_arrow_head':
        # El juego multiplica esta capa por el color de la poción. Perla casi
        # neutra conserva su lectura; no se cambia el modelo ni el tinte vanilla.
        return mix((166, 159, 184), WHITE, value) if value >= 0.3 else (72, 68, 82)
    if name.startswith('shield_base'):
        # No se inventan bordes en las costuras UV ni se recolorean los patrones.
        if value < 0.27:
            return OUT
        if sat < 0.12:
            return crystal_px(p, phase)
        return mix(pearl(value), cyc(phase), 0.32)
    if name in GOLDEN:
        return gold_px(p)
    if name in GENERIC or name == 'elytra':
        return aurora_px(p)
    if name == 'spectral_arrow':
        if value < 0.5:
            return OUT
        if value > 0.98 and sat < 0.1:
            return WHITE
        return mix(cyc(0.12 + (value - 0.5) * 0.8), WHITE, 0.35 if value > 0.95 else 0.05)
    if name == 'mace' and sat > 0.3:  # mango azul vanilla -> lavanda
        return pearl(value)
    col = crystal_px(p, phase)
    if value > 0.9:
        col = mix(col, WHITE, 0.65)
    return col


def recolor(original, name):
    result = original.copy()  # incluso el RGB de los píxeles transparentes se conserva
    for y in range(original.height):
        for x in range(original.width):
            pixel = original.getpixel((x, y))
            if pixel[3]:
                result.putpixel((x, y), C(paint_pixel(
                    pixel, name, x, y, original.width, original.height), pixel[3]))
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
