# Aurora worn armor v2: designed plate armor (own coverage per piece, outline, trim band, highlight
# and shadow columns, breastplate ridge, gems, short palettes) instead of recolouring vanilla noise.
# Runs after polish.py and overrides the worn humanoid textures of the four materials.
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
from gear import save_tex, mix, C, cyc, VIVID, WHITE, box_faces

def hsh(x, y, s=0):
    """well-mixed integer hash (gear.hsh has row-correlated low bits, which painted stripes)"""
    h = (x * 374761393 + y * 668265263 + s * 2246822519) & 0xffffffff
    h = ((h ^ (h >> 13)) * 1274126177) & 0xffffffff
    return h ^ (h >> 16)

MATS = {   # rim = outline, lo/hi = body ramp, trim = accent band (None = aurora iridescent)
    'netherite': dict(rim=(12, 6, 30), lo=(30, 18, 70), hi=(86, 60, 150), trim=None, stars=True,
                      gem=((120, 235, 255), (255, 140, 220))),
    'diamond': dict(rim=(44, 52, 132), lo=(96, 140, 222), hi=(214, 242, 255), trim=(255, 190, 236), stars=False,
                    gem=((255, 160, 225), (180, 140, 255))),
    'iron': dict(rim=(48, 42, 88), lo=(118, 112, 172), hi=(232, 228, 252), trim=(150, 225, 255), stars=False,
                 gem=((140, 220, 255), (200, 170, 255))),
    'gold': dict(rim=(96, 40, 70), lo=(196, 108, 128), hi=(255, 214, 190), trim=(255, 244, 214), stars=False,
                 gem=((110, 230, 215), (255, 150, 200))),
}
LIGHT = {'front': 1.0, 'back': 0.88, 'left': 0.92, 'right': 0.92, 'top': 1.08, 'bottom': 0.7}

# piece -> (u, v, w, h, d, first row, last row) ; rows refer to the vertical faces
SEAMS = {'helmet': (), 'chest': (5,), 'arm': (), 'boot': (), 'waist': (), 'leg': ()}

PIECES = {
    'humanoid': {'helmet': (0, 0, 8, 8, 8, 0, 7), 'chest': (16, 16, 8, 12, 4, 0, 10),
                 'arm': (40, 16, 4, 12, 4, 0, 6), 'boot': (0, 16, 4, 12, 4, 7, 11)},
    'humanoid_leggings': {'waist': (16, 16, 8, 12, 4, 7, 11), 'leg': (0, 16, 4, 12, 4, 0, 9)},
}

def covered(piece, face, i, j, w, h, r0, r1):
    if face in ('front', 'back', 'left', 'right'):
        if not r0 <= j <= r1:
            return False
        if piece == 'helmet' and face == 'front' and 2 <= j <= 7 and 1 <= i <= 6 and not (j == 2 and i in (3, 4)):
            return False                      # face opening with a nose guard
        if piece == 'helmet' and face in ('left', 'right') and j == 7 and 2 <= i <= 5:
            return False                      # cheek cut-out
        if piece == 'helmet' and face == 'back' and j == 7:
            return False
        return True
    if face == 'top':
        return piece in ('helmet', 'arm', 'chest')
    if face == 'bottom':
        return piece in ('boot',)
    return False

def paint(layer, mat):
    P = MATS[mat]
    out = Image.new('RGBA', (64, 32))
    for piece, (u, v, w, h, d, r0, r1) in PIECES[layer].items():
        faces = box_faces(u, v, w, h, d)
        for fname, (fx, fy, fw, fh) in faces.items():
            cov = lambda i, j: 0 <= j < fh and covered(piece, fname, max(0, min(fw - 1, i)), j, fw, fh, r0, r1)
            vertical = fname in ('front', 'back', 'left', 'right')
            for j in range(fh):
                for i in range(fw):
                    if not cov(i, j):
                        continue
                    t = (fx + i) / 64 * 0.7 + (fy + j) / 32 * 0.3
                    edge = not cov(i, j - 1) or not cov(i, j + 1) or (not cov(i - 1, j) and i > 0) or \
                           (not cov(i + 1, j) and i < fw - 1)
                    if vertical:
                        top_open = j > 0 and not cov(i, j - 1)
                        band = (cov(i, j + 1) and not cov(i, j + 2)) or top_open
                        f = 1 - (j - r0) / max(1, r1 - r0) * 0.6
                        if fname == 'front' and fw >= 8 and i in (fw // 2 - 1, fw // 2):
                            f += 0.12                         # breastplate / visor ridge
                        if i == 0:
                            f += 0.1                          # highlight column (light from the left)
                        if i == fw - 1:
                            f -= 0.12                         # shadow column
                    else:
                        band = False
                        f = 0.85
                    body = mix(P['lo'], P['hi'], max(0, min(1, f * LIGHT[fname])))
                    n = (hsh(fx + i, fy + j, 3) % 5 - 2) / 100              # subtle dither, no plastic look
                    body = tuple(q * (1 + n) for q in body)
                    if fname in ('front', 'back') and j in SEAMS[piece]:
                        body = mix(body, P['rim'], 0.45)                      # plate seam
                    elif fname == 'front' and j - 1 in SEAMS[piece]:
                        body = mix(body, WHITE, 0.18)                         # lit lip under the seam
                    if piece == 'chest' and fname == 'front' and j <= 2 and abs(i - 3.5) <= 1.5 - j + 1 and abs(i - 3.5) >= 1.5 - j:
                        body = P['trim'] or cyc(t, VIVID)                     # V collar
                    if piece == 'leg' and fname == 'front' and j in (5, 6) and 1 <= i <= 2:
                        body = mix(body, WHITE, 0.3 if j == 5 else 0.12)      # knee cap
                    if piece == 'helmet' and fname == 'top' and i in (3, 4):
                        body = mix(P['hi'], WHITE, 0.25) if i == 3 else P['hi'] # crest
                    if piece == 'arm' and vertical and j == 1 and i in (0, fw - 1):
                        body = mix(P['hi'], WHITE, 0.5)                       # pauldron rivets
                    if edge and (not vertical or not cov(i, j + 1) or (j > 0 and not cov(i, j - 1))
                                 or (fname == 'front' and piece == 'helmet')):
                        c = P['rim']
                    elif band:
                        trim = P['trim'] or cyc(t, VIVID)
                        c = mix(trim, WHITE, 0.25) if fname in ('front', 'left') else mix(trim, P['lo'], 0.25)
                    else:
                        c = body
                        if P['stars'] and hsh(fx + i, fy + j, 9) % 53 == 0:
                            c = mix(cyc(t + 0.4, VIVID), body, 0.35)
                    out.putpixel((fx + i, fy + j), C(c))
    g1, g2 = P['gem']
    def gem(x, y, w=2, h=2):
        for jj in range(h):
            for ii in range(w):
                out.putpixel((x + ii, y + jj), C(mix(g1, g2, (ii + jj) / max(1, w + h - 2))))
        out.putpixel((x, y), C(mix(g1, WHITE, 0.65)))
        if h > 1:
            out.putpixel((x + w - 1, y + h - 1), C(mix(g2, P['rim'], 0.3)))
    if layer == 'humanoid':
        gem(16 + 4 + 3, 16 + 4 + 2)            # chest
        gem(8 + 3, 8 + 0, 2, 1)                # helmet brow
    else:
        gem(16 + 4 + 3, 16 + 4 + 8, 2, 2)      # belt buckle
    return out

def cloak():
    """netherite cloak on the elytra geometry (wing box texOffs 22,0 size 10x20x2): night silk, aurora hem"""
    out = Image.new('RGBA', (64, 32))
    for fname, (fx, fy, fw, fh) in box_faces(22, 0, 10, 20, 2).items():
        for j in range(fh):
            for i in range(fw):
                vertical = fname in ('front', 'back', 'left', 'right')
                g = j / max(1, fh - 1) if vertical else 0.2
                c = mix((24, 14, 60), (92, 60, 160), 0.25 + 0.6 * g)
                if vertical and fname in ('front', 'back') and i % 3 == 1:
                    c = mix(c, (10, 6, 28), 0.25)                     # soft folds
                if vertical and fname in ('front', 'back') and i % 3 == 2:
                    c = mix(c, WHITE, 0.06)
                if vertical and j >= fh - 2:
                    c = mix(cyc(i / fw * 0.5 + j * 0.05, VIVID), WHITE, 0.15 if j == fh - 2 else 0.0)
                elif vertical and j == fh - 3:
                    c = (12, 6, 30)
                elif vertical and j == 0:
                    c = mix(cyc(0.6, VIVID), (40, 24, 84), 0.4)
                elif hsh(fx + i, fy + j, 11) % 37 == 0:
                    c = mix(cyc((i + j) / 20, VIVID), WHITE, 0.5)
                out.putpixel((fx + i, fy + j), C(c))
    return out

if __name__ == '__main__':
    save_tex(cloak(), 'entity/equipment/wings/aurora_cloak.png')
    for mat in MATS:
        for layer in PIECES:
            save_tex(paint(layer, mat), 'entity/equipment/%s/%s.png' % (layer, mat))
    print('ok')
