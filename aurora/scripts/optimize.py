# Lossless optimisation of the generated packs (runs after every generator, before validate.py).
# Nothing changes on screen:
#  1. Animations: identical frames are stored once and identical consecutive frames are merged into one longer frame
#     ("frames" list in the .mcmeta). The game uploads a sprite to the GPU every time its frame changes, so fewer
#     changes = less work every tick, and the strips take less texture memory. Interpolated animations are left as
#     they are (merging would change how they blend).
#  2. PNG: images with transparency and at most 256 colours are written as palette PNGs with exact RGBA entries
#     (PLTE + tRNS, so the game still decodes them as RGBA). Kept only when smaller and verified pixel-identical.
import os, io, json
from PIL import Image

HOME = os.path.expanduser('~')
RP = os.environ.get('AURORA_RP', HOME + '/mnt/.minecraft/resourcepacks')
PACKS = ['Aurora Pack', 'Aurora HUD XL', 'Aurora Outline', 'Aurora EMF'] + ['Aurora Celestial %d' % v for v in range(1, 5)]

def frame_size(a, w, h):
    fw, fh = a.get('width'), a.get('height')
    if fw and fh: return fw, fh
    if fw: return fw, h
    if fh: return w, fh
    m = min(w, h); return m, m

def dedupe_animation(png, meta_path):
    meta = json.load(open(meta_path))
    a = meta.get('animation')
    if a is None or 'frames' in a or a.get('interpolate'):
        return 0
    im = Image.open(png).convert('RGBA')
    fw, fh = frame_size(a, *im.size)
    cols, rows = im.width // fw, im.height // fh
    frames = [im.crop(((i % cols) * fw, (i // cols) * fh, (i % cols) * fw + fw, (i // cols) * fh + fh)) for i in range(cols * rows)]
    keys = [f.tobytes() for f in frames]
    unique = list(dict.fromkeys(keys))
    if len(unique) == len(keys):
        return 0
    ft = a.get('frametime', 1)
    order = []                                         # (unique index, duration) with consecutive repeats merged
    for k in keys:
        u = unique.index(k)
        if order and order[-1][0] == u: order[-1][1] += ft
        else: order.append([u, ft])
    strip = Image.new('RGBA', (fw, fh * len(unique)))  # vertical strip, frames in first-appearance order
    for u, k in enumerate(unique):
        strip.paste(frames[keys.index(k)], (0, u * fh))
    strip.save(png, optimize=True)
    a['frames'] = [u if t == ft else {'index': u, 'time': t} for u, t in order]
    if fw != fh or 'width' in a or 'height' in a:
        a['width'], a['height'] = fw, fh
    with open(meta_path, 'w') as f:
        json.dump(meta, f, indent=2)
    return len(keys) - len(order)                      # frame changes saved per loop

def palettize(png):
    im = Image.open(png)
    if im.mode == 'P':
        return 0
    rgba = im.convert('RGBA')
    colours = rgba.getcolors(256)
    if colours is None or all(c[1][3] == 255 for c in colours):
        return 0                                       # >256 colours, or fully opaque (no tRNS -> would load as RGB)
    raw = rgba.tobytes()
    data = [tuple(raw[i:i + 4]) for i in range(0, len(raw), 4)]
    pal = list(dict.fromkeys(data))                    # deterministic: first appearance order
    index = {c: i for i, c in enumerate(pal)}
    p = Image.new('P', rgba.size)
    p.putdata([index[c] for c in data])
    p.putpalette([v for c in pal for v in c[:3]])
    p.info['transparency'] = bytes(c[3] for c in pal)
    buf = io.BytesIO()
    p.save(buf, format='PNG', optimize=True, transparency=bytes(c[3] for c in pal))
    if Image.open(io.BytesIO(buf.getvalue())).convert('RGBA').tobytes() != rgba.tobytes():
        return 0                                       # never keep anything that is not pixel-identical
    old = os.path.getsize(png)
    if len(buf.getvalue()) >= old:
        return 0
    with open(png, 'wb') as f:
        f.write(buf.getvalue())
    return old - len(buf.getvalue())

if __name__ == '__main__':
    saved_changes = saved_bytes = anims = pngs = 0
    for pack in PACKS:
        root = os.path.join(RP, pack)
        for base, dirs, files in sorted(os.walk(root)):
            dirs.sort()
            for f in sorted(files):
                p = os.path.join(base, f)
                if f.endswith('.png.mcmeta') and os.path.exists(p[:-7]):
                    s = dedupe_animation(p[:-7], p)
                    if s: anims += 1; saved_changes += s
        for base, dirs, files in sorted(os.walk(root)):
            dirs.sort()
            for f in sorted(files):
                if f.endswith('.png') and f != 'pack.png':
                    b = palettize(os.path.join(base, f))
                    if b: pngs += 1; saved_bytes += b
    print('optimize: %d animations merged (%d frame changes less per loop), %d PNG palettised (-%d KB)'
          % (anims, saved_changes, pngs, saved_bytes // 1024))
