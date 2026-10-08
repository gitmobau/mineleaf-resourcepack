# Rebuild everything: Aurora Pack (generated) + validation + zips.
#   python3 build.py [--ref RUTA_A_REF63]
# The vanilla 26.3 reference (folder with assets/minecraft/...) is NOT in the repo (Mojang assets):
# extract it from versions/26.3/26.3.jar or from Aurora_handoff.zip (ref63/). Default: ~/ref63.
import os, sys, shutil, subprocess, zipfile, argparse

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
for script in ('gen.py', 'magic.py', 'gear.py', 'extra.py', 'menus.py', 'polish.py', 'validate.py'):   # order matters: later ones overwrite
    print('==>', script)
    subprocess.run([sys.executable, '-I', os.path.join(HERE, script)], env=env, cwd=HERE, check=True)

if not args.no_zip:
    dist = os.path.join(ROOT, 'dist'); os.makedirs(dist, exist_ok=True)
    for name in ('Aurora Pack', 'Aurora Outline'):
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
