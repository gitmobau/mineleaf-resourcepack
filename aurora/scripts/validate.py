# Static validation of the Aurora packs against the vanilla 26.3 reference (~/ref63).
# Checks: JSON syntax, animation frame layout, nine-slice sizes, model/texture references,
# item model definitions, equipment layers and (if glslangValidator exists) core shaders.
import os, sys, json, glob, shutil, subprocess, tempfile, re
from PIL import Image

HOME = os.path.expanduser('~')
REF = os.environ.get('AURORA_REF', HOME + '/ref63') + '/assets/minecraft/'
RP = os.environ.get('AURORA_RP', HOME + '/mnt/.minecraft/resourcepacks') + '/'
PACKS = [RP + 'Aurora Pack', RP + 'Aurora Outline', RP + 'Aurora HUD XL']
errors, warns = [], []
# every model id referenced by a vanilla item definition is known to exist in the jar
VANILLA_MODELS = set(re.findall(r'"model": "(minecraft:[^"]+)"',
                                ''.join(open(f).read() for f in glob.glob(REF + 'items/*.json'))))
err = lambda m: errors.append(m)
warn = lambda m: warns.append(m)

def rid(s):
    ns, _, p = s.partition(':') if ':' in s else ('minecraft', '', s)
    return ns, p

def exists_tex(pack, path):
    ns, p = rid(path)
    return os.path.exists('%s/assets/%s/textures/%s.png' % (pack, ns, p)) or \
        (ns == 'minecraft' and os.path.exists(REF + 'textures/%s.png' % p))

MARK = 167   # Aurora HUD XL corner markers, see hud_xl.py / position_tex_color.vsh

def oversize_pads(im, fw, fh):
    """(left, top, right, bottom) if every frame carries consistent corner markers, else None"""
    im = im.convert('RGBA'); pads = None
    for fy in range(0, im.height, fh):
        for fx in range(0, im.width, fw):
            c = [im.getpixel(p) for p in ((fx, fy), (fx + fw - 1, fy), (fx, fy + fh - 1), (fx + fw - 1, fy + fh - 1))]
            if any(q[2] != MARK or q[3] != i + 1 for i, q in enumerate(c)): return None
            if c[0][0] != c[2][0] or c[1][0] != c[3][0] or c[0][1] != c[1][1] or c[2][1] != c[3][1]: return None
            p = (c[0][0], c[0][1], c[1][0], c[2][1])
            if pads not in (None, p): return None
            pads = p
    return pads

def frame_size(meta, w, h):
    fw, fh = meta.get('width'), meta.get('height')
    if fw and fh: return fw, fh
    if fw: return fw, h
    if fh: return w, fh
    m = min(w, h); return m, m

for pack in PACKS:
    name = os.path.basename(pack)
    mc = json.load(open(pack + '/pack.mcmeta'))['pack']
    lo, hi = mc.get('min_format'), mc.get('max_format')
    lo0 = lo[0] if isinstance(lo, list) else lo
    hi0 = hi[0] if isinstance(hi, list) else hi
    if not (lo0 <= 97 <= hi0): err('%s: pack.mcmeta range %s..%s excludes 97' % (name, lo, hi))
    if not os.path.exists(pack + '/pack.png'): warn('%s: no pack.png' % name)
    for f in glob.glob(pack + '/**/*', recursive=True):
        if f.endswith(('.json', '.mcmeta')):
            try: json.load(open(f))
            except Exception as e: err('JSON %s: %s' % (f, e))
    A = pack + '/assets/minecraft/'
    # ---- textures + animations
    for png in glob.glob(A + 'textures/**/*.png', recursive=True):
        rel = os.path.relpath(png, A + 'textures')
        im = Image.open(png); w, h = im.size
        if im.mode not in ('RGBA', 'RGB', 'P', 'LA', 'L'): warn('mode %s %s' % (im.mode, rel))
        meta = json.load(open(png + '.mcmeta')) if os.path.exists(png + '.mcmeta') else {}
        refpng = REF + 'textures/' + rel
        a = meta.get('animation')
        if a is not None:
            fw, fh = frame_size(a, w, h)
            if w % fw or h % fh:
                err('%s: %dx%d not divisible into %dx%d frames' % (rel, w, h, fw, fh)); continue
            n = (w // fw) * (h // fh)
            for fr in a.get('frames', []):
                idx = fr['index'] if isinstance(fr, dict) else fr
                if idx >= n: err('%s: frame index %d >= %d' % (rel, idx, n))
            if n == 1: warn('%s: animation with a single frame' % rel)
        else:
            fw, fh = w, h
        if os.path.exists(refpng):
            rw, rh = Image.open(refpng).size
            rmeta = json.load(open(refpng + '.mcmeta')) if os.path.exists(refpng + '.mcmeta') else {}
            ra = rmeta.get('animation')
            rfw, rfh = frame_size(ra, rw, rh) if ra is not None else (rw, rh)
            # entity/misc textures may be any size; gui sprites & items must keep their aspect
            if rel.startswith('gui/') and (fw, fh) != (rfw, rfh):
                pads = oversize_pads(im, fw, fh) if rel.startswith('gui/sprites/') else None
                if pads is None:
                    err('%s: frame %dx%d differs from vanilla %dx%d' % (rel, fw, fh, rfw, rfh))
                elif (fw, fh) != (rfw + pads[0] + pads[2], rfh + pads[1] + pads[3]):
                    err('%s: oversized frame %dx%d != vanilla %dx%d + pads %s' % (rel, fw, fh, rfw, rfh, pads))
                elif 'gui' in rmeta:
                    err('%s: oversized sprites cannot use gui scaling (%s)' % (rel, rmeta['gui']))
                elif not os.path.exists(A + 'shaders/core/position_tex_color.vsh'):
                    err('%s: oversized sprite needs shaders/core/position_tex_color.vsh in the same pack' % rel)
            if rel.startswith('item/') and fw * rfh != fh * rfw:
                err('%s: aspect differs from vanilla' % rel)
            if 'gui' in rmeta and 'gui' not in meta:
                err('%s: vanilla gui scaling block lost (%s)' % (rel, rmeta['gui']))
        g = meta.get('gui', {}).get('scaling')
        if g and g.get('type') == 'nine_slice' and (g['width'], g['height']) != (fw, fh):
            warn('%s: nine_slice %sx%s vs frame %dx%d' % (rel, g['width'], g['height'], fw, fh))
        if rel.startswith('gui/container/') and (w, h) != (256, 256):
            err('%s: container background must stay 256x256' % rel)
        if rel.startswith('gui/container/') and a is not None:
            err('%s: container backgrounds cannot animate' % rel)
    # ---- models
    for mj in glob.glob(A + 'models/**/*.json', recursive=True):
        m = json.load(open(mj)); rel = os.path.relpath(mj, A)
        tex = m.get('textures', {})
        for k, v in tex.items():
            if not v.startswith('#') and not exists_tex(pack, v): err('%s: texture %s missing' % (rel, v))
        for el in m.get('elements', []):
            for c in el['from'] + el['to']:
                if not -16 <= c <= 32: err('%s: element coord %s out of [-16,32]' % (rel, c))
            for fn, face in el['faces'].items():
                t = face['texture']
                if t.startswith('#') and t[1:] not in tex: err('%s: face %s uses undefined %s' % (rel, fn, t))
            le = el.get('light_emission', 0)
            if not 0 <= le <= 15: err('%s: light_emission %s' % (rel, le))
    # ---- item model definitions
    def walk(node, rel):
        t = node.get('type', '').replace('minecraft:', '')
        if t == 'model':
            ns, p = rid(node['model'])
            if not (os.path.exists('%s/assets/%s/models/%s.json' % (pack, ns, p)) or
                    os.path.exists(REF + 'models/%s.json' % p) or '%s:%s' % (ns, p) in VANILLA_MODELS):
                err('%s: model %s missing' % (rel, node['model']))
        for k in ('on_true', 'on_false', 'fallback', 'model'):
            if isinstance(node.get(k), dict): walk(node[k], rel)
        for c in node.get('cases', []): walk(c['model'], rel)
        for c in node.get('models', []): walk(c, rel)
        for c in node.get('entries', []): walk(c['model'], rel)
        if t == 'condition' and node.get('property', '').endswith('has_component') and 'component' not in node:
            err('%s: has_component without component' % rel)
    for ij in glob.glob(A + 'items/*.json'):
        rel = os.path.relpath(ij, A); d = json.load(open(ij))
        if not os.path.exists(REF + 'items/' + os.path.basename(ij)): err('%s: not a vanilla item' % rel)
        walk(d['model'], rel)
        van = json.load(open(REF + 'items/' + os.path.basename(ij)))
        for k, v in van.items():
            if k != 'model' and d.get(k) != v: err('%s: vanilla field %s=%s lost' % (rel, k, v))
    # ---- equipment
    for ej in glob.glob(A + 'equipment/*.json'):
        d = json.load(open(ej))
        for layer, ls in d['layers'].items():
            for l in ls:
                ns, p = rid(l['texture'])
                if not exists_tex(pack, 'entity/equipment/%s/%s' % (layer, p)):
                    err('%s: %s texture %s missing' % (os.path.basename(ej), layer, l['texture']))
        van = REF + 'equipment/' + os.path.basename(ej)
        if os.path.exists(van):
            for layer in json.load(open(van))['layers']:
                if layer not in d['layers']: err('%s: vanilla layer %s dropped' % (ej, layer))
    # ---- shaders
    sh = A + 'shaders/core/'
    gv = shutil.which('glslangValidator')
    if os.path.isdir(sh):
        for f in os.listdir(sh):
            if not os.path.exists(REF + 'shaders/core/' + f): err('shader %s has no vanilla counterpart' % f)
            elif "Can't moj_import" in open(REF + 'shaders/core/' + f).read() and '#include' in open(sh + f).read():
                err('shader %s is used during startup and cannot #include' % f)
        if not gv:
            warn('glslangValidator missing: shaders not compiled')
        else:
            inc = {}
            for d in (REF + 'shaders/include/', A + 'shaders/include/'):
                if os.path.isdir(d):
                    for f in os.listdir(d): inc[f] = open(d + f).read()
            def expand(src):
                return re.sub(r'#include <minecraft:([\w.]+)>', lambda m: expand(inc[m.group(1)]), src)
            variants = [[], ['OIT', 'OIT_COEFF_COUNT 8', 'OIT_WAVELET_RANK 3', 'OIT_COEFF_ATTACHMENT_COUNT 2', 'OIT_ACCUMULATE'], ['OIT', 'OIT_COEFF_COUNT 8', 'OIT_WAVELET_RANK 3', 'OIT_COEFF_ATTACHMENT_COUNT 2', 'OIT_ALPHA_ONLY', 'OIT_DEPTH_BOUNDS'],
                        ['OIT', 'OIT_COEFF_COUNT 8', 'OIT_WAVELET_RANK 3', 'OIT_COEFF_ATTACHMENT_COUNT 2', 'OIT_ALPHA_ONLY', 'OIT_TRANSMITTANCE'], ['OIT', 'OIT_COEFF_COUNT 8', 'OIT_WAVELET_RANK 3', 'OIT_COEFF_ATTACHMENT_COUNT 2', 'OIT_ALPHA_ONLY', 'OIT_ADDITIVE']]
            for f in sorted(os.listdir(sh)):
                src = expand(open(sh + f).read())
                for defs in variants:
                    lines = src.split('\n')
                    lines[1:1] = ['#define %s' % d for d in defs]
                    with tempfile.NamedTemporaryFile('w', suffix='.' + ('vert' if f.endswith('vsh') else 'frag'), delete=False) as t:
                        t.write('\n'.join(lines))
                    r = subprocess.run([gv, '--target-env', 'vulkan1.2', '--auto-map-locations', '--auto-map-bindings', t.name],
                                       capture_output=True, text=True, cwd=tempfile.gettempdir())  # .spv output goes there
                    os.unlink(t.name)
                    if r.returncode: err('shader %s %s:\n%s' % (f, defs, r.stdout[-800:]))
            # vsh outputs must match fsh inputs
            for base in {f[:-4] for f in os.listdir(sh)}:
                v, fr = sh + base + '.vsh', sh + base + '.fsh'
                vs = REF + 'shaders/core/' + base + '.vsh' if not os.path.exists(v) else v
                fs = REF + 'shaders/core/' + base + '.fsh' if not os.path.exists(fr) else fr
                pat = r'layout\(location = (\d+)\)\s*(flat\s+)?%s\s+(\w+)\s+(\w+);'
                outs = {m[0]: (m[2], m[3]) for m in re.findall(pat % 'out', open(vs).read())}
                ins = {m[0]: (m[2], m[3]) for m in re.findall(pat % 'in', open(fs).read())}
                for loc, (ty, nm) in ins.items():
                    if outs.get(loc) != (ty, nm): err('%s: fsh in %s %s@%s not written by vsh' % (base, ty, nm, loc))

for w in warns: print('WARN ', w)
for e in errors: print('ERROR', e)
print('%d errors, %d warnings' % (len(errors), len(warns)))
sys.exit(1 if errors else 0)
