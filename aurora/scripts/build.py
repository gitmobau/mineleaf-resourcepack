# Rebuild everything: Aurora Pack (generated) + validation + zips.
#   python3 build.py [--ref RUTA_A_REF63]
# The vanilla 26.3 reference (folder with assets/minecraft/...) is NOT in the repo (Mojang assets):
# extract it from versions/26.3/26.3.jar or from Aurora_handoff.zip (ref63/). Default: ~/ref63.
import os, sys, glob, json, shutil, subprocess, zipfile, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PACKS = os.path.join(ROOT, 'packs')
ap = argparse.ArgumentParser()
ap.add_argument('--ref', default=os.environ.get('AURORA_REF', os.path.expanduser('~/ref63')))
ap.add_argument('--no-zip', action='store_true')
args = ap.parse_args()
if not os.path.isdir(os.path.join(args.ref, 'assets/minecraft/textures')):
    sys.exit('No encuentro la referencia vanilla en %s (usa --ref)' % args.ref)

env = dict(os.environ, AURORA_REF=os.path.abspath(args.ref), AURORA_RP=PACKS,
           AURORA_PREVIEWS=os.path.join(ROOT, 'previews'))
# Aurora Pack is 100% generated: start clean so nothing stale survives.
shutil.rmtree(os.path.join(PACKS, 'Aurora Pack'), ignore_errors=True)
for script in ('gen.py', 'magic.py', 'gear.py', 'icons.py', 'extras.py', 'screens.py', 'hud_xl.py', 'menus_xl.py', 'emf.py', 'celestial.py', 'grimorio.py', 'hardcore.py', 'sonidos.py', 'optimize.py'):   # order matters: later ones overwrite
    print('==>', script)
    subprocess.run([sys.executable, '-I', os.path.join(HERE, script)], env=env, cwd=HERE, check=True)

# Aurora Extras: only the newer additions (rarity auras, dragon egg, magic particles, enchanting table book,
# sounds) as a small pack to stack on top of any Aurora version without touching water, hearts, menus or armour.
EXTRAS = ['items/diamond_*.json', 'items/netherite_*.json', 'models/item/aurora/aura_*', 'textures/item/aurora/aura_*',
          'textures/block/dragon_egg.png*', 'models/block/dragon_egg.json', 'textures/particle/*',
          'textures/entity/enchantment/*', 'sounds.json', 'sounds/aurora/*']
src = os.path.join(PACKS, 'Aurora Pack', 'assets', 'minecraft')
ext = os.path.join(PACKS, 'Aurora Extras')
shutil.rmtree(ext, ignore_errors=True)
for pat in EXTRAS:
    for f in sorted(glob.glob(os.path.join(src, pat))):
        d = os.path.join(ext, 'assets', 'minecraft', os.path.relpath(f, src))
        os.makedirs(os.path.dirname(d), exist_ok=True)
        shutil.copy2(f, d)
shutil.copy2(os.path.join(PACKS, 'Aurora Pack', 'pack.png'), os.path.join(ext, 'pack.png'))
mc = json.load(open(os.path.join(PACKS, 'Aurora Pack', 'pack.mcmeta')))
mc['pack']['description'] = ["", {"text": "Aurora Extras ", "color": "#B9B9F8"},
                             {"text": "· auras por rareza, huevo, magia y sonidos", "color": "#F8B0EA"}]
with open(os.path.join(ext, 'pack.mcmeta'), 'w') as f:
    json.dump(mc, f, indent=2, ensure_ascii=False)
print('==> validate.py')
subprocess.run([sys.executable, '-I', os.path.join(HERE, 'validate.py')], env=env, cwd=HERE, check=True)

if not args.no_zip:
    dist = os.path.join(ROOT, 'dist'); os.makedirs(dist, exist_ok=True)
    for old in tuple('Aurora Celestial %d.zip' % v for v in range(1, 5)):   # old prototypes
        if os.path.exists(os.path.join(dist, old)): os.remove(os.path.join(dist, old))
    for name in ('Aurora Pack', 'Aurora Outline', 'Aurora HUD XL', 'Aurora Celestial', 'Aurora Extras'):
        src = os.path.join(PACKS, name); out = os.path.join(dist, name + '.zip')
        with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for base, dirs, files in sorted(os.walk(src)):
                dirs.sort()
                for f in sorted(files):
                    p = os.path.join(base, f)
                    zi = zipfile.ZipInfo(os.path.relpath(p, src).replace(os.sep, '/'), (2026, 1, 1, 0, 0, 0))
                    zi.compress_type = zipfile.ZIP_DEFLATED
                    z.writestr(zi, open(p, 'rb').read())
        print('zip', out, os.path.getsize(out) // 1024, 'KB')
