# Aurora menus part 2: every remaining container screen, their sprites, and the shared widgets
# (buttons, sliders, text fields, tabs, checkboxes, tooltips). Runs after extra.py.
import os, sys, colorsys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
from magic import (build_container, CAT_PEEK, CAT_SIT, TITLE, inv_label, cyc, mix, C, OUT, WHITE,
                   VIVID, ref, save, REF, TX)
from extra import gui_recolor, pastel, copy_meta

# name: (w, h, cats)  -- sizes are the vanilla panel bounding boxes in 26.3
CONTAINERS = {
    'anvil': (176, 166, ()), 'beacon': (230, 219, ()), 'brewing_stand': (176, 166, ((CAT_PEEK, 150, 3),)),
    'cartography_table': (176, 166, ()), 'crafter': (176, 166, ((CAT_PEEK, 152, 3),)),
    'dispenser': (176, 166, ((CAT_SIT, 148, 6),)), 'enchanting_table': (176, 166, ()),
    'grindstone': (176, 166, ()), 'hopper': (176, 133, ((CAT_PEEK, 152, 3),)), 'horse': (176, 166, ()),
    'loom': (176, 166, ()), 'nautilus': (176, 166, ()), 'smithing': (176, 166, ()),
    'stonecutter': (176, 166, ()), 'villager': (276, 166, ()),
}
# per-container sprite folders already handled elsewhere
DONE_SPRITES = {'furnace', 'blast_furnace', 'smoker', 'creative_inventory'}

def containers():
    res = {}
    for i, (n, (w, h, cats)) in enumerate(sorted(CONTAINERS.items())):
        if not os.path.exists(REF + 'gui/container/%s.png' % n):
            continue
        img, sl = build_container(n, w, h, cats=cats,
                                  excl=[(0, 3, w, 17), (0, h - 97, w, h - 82)], seed=40 + i)
        save(img, 'gui/container/%s.png' % n); res[n] = (img, w, h, len(sl))
    return res

def container_sprites():
    base = 'gui/sprites/container/'
    for d in sorted(os.listdir(REF + base)):
        if not os.path.isdir(REF + base + d) or d in DONE_SPRITES:
            continue
        for f in sorted(os.listdir(REF + base + d)):
            if f.endswith('.png'):
                rel = base + d + '/' + f
                save(gui_recolor(rel, t0=0.07 * len(f), span=0.5, glass=False), rel); copy_meta(rel)

def dark_px(p, t, d, hi):
    """widget pixel -> dark aurora (white text must stay readable on top)"""
    if p[0] == p[1] == p[2]:
        g = p[0]
        if g == 0:
            return OUT
        if g == 255:                       # highlighted outline
            return cyc(t, VIVID)
        if g >= 150:                       # light borders (text field, checkbox)
            return mix((175, 155, 238), cyc(t), 0.3) if not hi else mix(cyc(t, VIVID), WHITE, 0.3)
        v = g / 255
        c = mix((30, 20, 64), (128, 104, 200), min(1, v * 1.7))
        c = mix(c, cyc(t), 0.16 if not hi else 0.28)
        if d == 1:                         # inner top/left bevel
            c = mix(c, WHITE, 0.18)
        return c
    return pastel(p, t)

def widgets():
    W = 'gui/sprites/widget/'
    for f in sorted(os.listdir(REF + W)):
        if not f.endswith('.png'):
            continue
        rel = W + f
        v = ref(rel); w, h = v.size; o = Image.new('RGBA', v.size)
        hi = 'highlighted' in f or 'selected' in f
        for y in range(h):
            for x in range(w):
                p = v.getpixel((x, y))
                if not p[3]:
                    continue
                d = min(x, y, w - 1 - x, h - 1 - y)
                t = x / max(1, w) * 0.6 + y / max(1, h) * 0.2
                o.putpixel((x, y), C(dark_px(p, t, d, hi), p[3]))
        save(o, rel); copy_meta(rel)

def tooltip():
    T = 'gui/sprites/tooltip/'
    bg = ref(T + 'background.png'); o = Image.new('RGBA', bg.size)
    for y in range(bg.height):
        for x in range(bg.width):
            p = bg.getpixel((x, y))
            if p[3]:
                o.putpixel((x, y), C(mix((20, 12, 46), (44, 26, 86), y / bg.height), p[3]))
    save(o, T + 'background.png'); copy_meta(T + 'background.png')
    fr = ref(T + 'frame.png'); o = Image.new('RGBA', fr.size)
    for y in range(fr.height):
        for x in range(fr.width):
            p = fr.getpixel((x, y))
            if p[3]:
                o.putpixel((x, y), C(cyc(x / fr.width * 0.35 + y / fr.height * 0.45, VIVID), 190))
    save(o, T + 'frame.png'); copy_meta(T + 'frame.png')

if __name__ == '__main__':
    res = containers(); container_sprites(); widgets(); tooltip()
    for k, (im, w, h, n) in res.items():
        print(k, 'slots', n)
    from magic import PREVIEWS
    order = sorted(res)
    S = 2; cols = 4
    sheet = Image.new('RGBA', (cols * (280 * S + 10) + 10, ((len(order) + cols - 1) // cols) * (222 * S + 10) + 140),
                      (60, 52, 84, 255))
    for i, k in enumerate(order):
        im, w, h, _ = res[k]
        sheet.alpha_composite(im.crop((0, 0, w, h)).resize((w * S, h * S), Image.NEAREST),
                              (10 + (i % cols) * (280 * S + 10), 10 + (i // cols) * (222 * S + 10)))
    y0 = sheet.height - 125
    for j, f in enumerate(('button', 'button_highlighted', 'button_disabled', 'text_field')):
        b = Image.open(TX + 'gui/sprites/widget/%s.png' % f)
        sheet.alpha_composite(b.resize((400, 40), Image.NEAREST), (10 + (j % 2) * 420, y0 + (j // 2) * 50))
    tb = Image.open(TX + 'gui/sprites/tooltip/background.png'); tf = Image.open(TX + 'gui/sprites/tooltip/frame.png')
    tip = tb.copy(); tip.alpha_composite(tf)
    sheet.alpha_composite(tip.resize((100, 100), Image.NEAREST), (860, y0))
    os.makedirs(PREVIEWS, exist_ok=True)
    sheet.save(PREVIEWS + '/preview_menus.png')
    print('ok')
