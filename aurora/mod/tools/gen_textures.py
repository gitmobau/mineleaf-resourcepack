#!/usr/bin/env python3
"""Genera las texturas del mod Aurora FX.

    pip install pillow
    python3 aurora/mod/tools/gen_textures.py

Escribe (deterministas, mismos bytes en cada ejecución):
  src/main/resources/assets/aurora_fx/textures/entity/aurora_overlay.png
      64x64, sin costuras en X e Y (se desplaza con UV scroll por tiempo).
      Fondo negro + cortinas de aurora: se dibuja con mezcla ADITIVA
      (pipeline energy_swirl de vanilla), así que el negro no se ve y solo brillan las cintas.
  src/main/resources/assets/aurora_fx/icon.png
      128x128, icono del mod para fabric.mod.json / Mod Menu.

La paleta es la misma que aurora/scripts/gear.py (P, VIVID y cyc()).
"""
import math
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, '..', 'src', 'main', 'resources', 'assets', 'aurora_fx')

# --- paleta Aurora (copiada de aurora/scripts/gear.py) ---------------------------------
P = [(123, 225, 249), (155, 210, 248), (187, 185, 248), (220, 181, 240), (248, 176, 234),
     (248, 188, 199), (248, 201, 173), (248, 225, 156), (209, 248, 145), (170, 245, 215)]
VIVID = [(80, 220, 255), (120, 175, 255), (170, 140, 255), (220, 130, 255), (255, 125, 220),
         (255, 150, 175), (255, 190, 135), (255, 228, 120), (175, 248, 135), (110, 245, 205)]
WHITE = (255, 255, 255)
OUT = (52, 36, 98)


def cyc(t, pal=P):
    t = (t % 1.0) * len(pal); i = int(t) % len(pal); f = t - int(t)
    a = pal[i]; b = pal[(i + 1) % len(pal)]
    return tuple(a[k] + (b[k] - a[k]) * f for k in range(3))


def mix(a, b, f):
    return tuple(a[k] + (b[k] - a[k]) * f for k in range(3))


def hsh(x, y, s=0):
    h = (x * 374761393 + y * 668265263 + s * 2147483647) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return h ^ (h >> 16)


def C(c, a=255):
    return tuple(max(0, min(255, int(round(v)))) for v in c) + (max(0, min(255, int(round(a)))),)


TAU = 2 * math.pi


def overlay(size=64):
    """Cortinas de aurora periódicas en u y v (todas las frecuencias son enteras)."""
    img = Image.new('RGBA', (size, size))
    # (frecuencia de la ondulación en u, fase, centro v, grosor, frecuencia de la ondulación fina, peso)
    bands = [
        (1, 0.00, 0.20, 0.060, 3, 1.00),
        (2, 0.35, 0.55, 0.050, 5, 0.85),
        (1, 0.70, 0.82, 0.045, 4, 0.70),
    ]
    for y in range(size):
        v = y / size
        for x in range(size):
            u = x / size
            lum = 0.0
            for fu, ph, vc, w, ff, wt in bands:
                c = vc + 0.12 * math.sin(TAU * (fu * u + ph)) + 0.03 * math.sin(TAU * (ff * u + 2 * ph))
                d = (v - c + 0.5) % 1.0 - 0.5          # distancia envuelta (sin costura en v)
                lum += wt * math.exp(-(d / w) ** 2)
                # rayos verticales de la cortina: brillo extra que cae por debajo de la cinta
                if 0 < -d < 0.22:
                    ray = 0.5 + 0.5 * math.sin(TAU * (7 * u + 3 * ph))
                    lum += wt * 0.28 * ray * (1 + d / 0.22)
            lum = min(1.0, lum)
            col = cyc(u + 0.35 * v, VIVID)
            col = mix(col, WHITE, 0.25 * lum)              # los núcleos de la cinta tiran a blanco
            col = tuple(q * lum * 0.92 for q in col)
            r = hsh(x, y, 7) % 157                         # estrellitas sueltas
            if r == 0:
                col = mix(col, WHITE, 0.9)
            elif r == 1:
                col = mix(col, cyc(u, P), 0.7)
            img.putpixel((x, y), C(col))                   # alfa 255: la mezcla aditiva ignora el alfa
    return img


def icon(size=128):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    cx = cy = (size - 1) / 2
    R = size * 0.47
    for y in range(size):
        for x in range(size):
            dx, dy = x - cx, y - cy
            d = math.hypot(dx, dy)
            if d > R:
                continue
            # fondo: cielo nocturno con un degradado de la paleta en diagonal
            sky = mix((20, 12, 48), (54, 30, 100), (y / size) * 0.9)
            u = x / size
            band = math.exp(-(((y / size) - (0.45 + 0.12 * math.sin(TAU * (u * 1.2 + 0.1)))) / 0.11) ** 2)
            col = mix(sky, cyc(u * 0.8 + 0.05, VIVID), min(1.0, band * 0.95))
            if hsh(x // 3, y // 3, 3) % 41 == 0 and band < 0.3:
                col = mix(col, WHITE, 0.8)
            a = 255
            if d > R - 4:                                  # borde lavanda oscuro
                col = mix(col, OUT, 0.85)
            if d > R - 1:
                a = int(255 * max(0.0, R - d))
            img.putpixel((x, y), C(col, a))
    # destello de 4 puntas en el centro-arriba
    sx, sy = int(size * 0.68), int(size * 0.30)
    for k in range(-14, 15):
        f = 1 - abs(k) / 15
        for (px, py) in ((sx + k, sy), (sx, sy + k)):
            base = img.getpixel((px, py))
            col = mix(base[:3], WHITE, f)
            img.putpixel((px, py), C(col, max(base[3], int(255 * f))))
    return img


def save(img, rel):
    path = os.path.normpath(os.path.join(ASSETS, rel))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, optimize=True)
    print('escrito', os.path.relpath(path, os.path.join(HERE, '..')), img.size)


if __name__ == '__main__':
    save(overlay(), 'textures/entity/aurora_overlay.png')
    save(icon(), 'icon.png')
