# Download the vanilla 26.3 reference used by the generators from misode/mcmeta (tag 26.3-assets)
# into ~/ref63 (or the folder given as argument). Needs git; only the folders below are fetched.
#   python3 fetch_ref.py [DESTINO] [--tag 26.3-assets]
import os, sys, shutil, subprocess, tempfile

args = [a for a in sys.argv[1:] if not a.startswith('--')]
tag = sys.argv[sys.argv.index('--tag') + 1] if '--tag' in sys.argv else '26.3-assets'
if '--tag' in sys.argv: args.remove(tag)
dest = os.path.abspath(os.path.expanduser(args[0] if args else '~/ref63'))
FOLDERS = ['assets/minecraft/' + p for p in (
    'atlases', 'equipment', 'items', 'models/item', 'shaders',
    'textures/block', 'textures/entity/equipment', 'textures/entity/player/wide', 'textures/entity/shield',
    'textures/gui', 'textures/item', 'textures/misc')]

tmp = tempfile.mkdtemp()
try:
    run = lambda *c: subprocess.run(c, cwd=tmp, check=True)
    run('git', '-c', 'advice.detachedHead=false', 'clone', '-q', '--depth', '1', '--branch', tag, '--filter=blob:none', '--sparse',
        'https://github.com/misode/mcmeta', 'm')
    subprocess.run(['git', 'sparse-checkout', 'set'] + FOLDERS, cwd=tmp + '/m', check=True)
    for f in FOLDERS:
        shutil.copytree(os.path.join(tmp, 'm', f), os.path.join(dest, f), dirs_exist_ok=True)
    print('referencia vanilla (%s) en %s' % (tag, dest))
finally:
    shutil.rmtree(tmp, ignore_errors=True)
