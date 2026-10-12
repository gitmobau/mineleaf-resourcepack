# Calculadora de yunque para Minecraft Java 26.3 (lógica de AnvilMenu.createResult).
# Datos de encantamientos sacados de misode/mcmeta, tag 26.3-data.
#
#   python3 yunque.py sword sharpness:5 looting:3 mending unbreaking:3 sweeping_edge:3 fire_aspect:2
#   python3 yunque.py pickaxe efficiency:5 fortune:3 mending unbreaking:3 --trabajo 1
#   python3 yunque.py --combinar sword:sharpness:4 book:sharpness:4
#
# Modo normal: un objeto limpio (o con --trabajo N usos previos de yunque) más un libro por
# encantamiento. Busca el orden de combinación que gasta menos niveles sin pasar nunca de 39.
import itertools, sys

# id: (nivel máx, anvil_cost, conjunto exclusivo, tags de objetos soportados)
E = {
    'aqua_affinity':        (1, 4, None,       ['head_armor']),
    'bane_of_arthropods':   (5, 2, 'damage',   ['weapon']),
    'binding_curse':        (1, 8, None,       ['equippable']),
    'blast_protection':     (4, 4, 'armor',    ['armor']),
    'breach':               (4, 4, 'damage',   ['mace']),
    'channeling':           (1, 8, None,       ['trident']),
    'density':              (5, 2, 'damage',   ['mace']),
    'depth_strider':        (3, 4, 'boots',    ['foot_armor']),
    'efficiency':           (5, 1, None,       ['mining']),
    'feather_falling':      (4, 2, None,       ['foot_armor']),
    'fire_aspect':          (2, 4, None,       ['fire_aspect']),
    'fire_protection':      (4, 2, 'armor',    ['armor']),
    'flame':                (1, 4, None,       ['bow']),
    'fortune':              (3, 4, 'mining',   ['mining_loot']),
    'frost_walker':         (2, 4, 'boots',    ['foot_armor']),
    'impaling':             (5, 4, 'damage',   ['trident']),
    'infinity':             (1, 8, 'bow',      ['bow']),
    'knockback':            (2, 2, None,       ['melee_weapon']),
    'looting':              (3, 4, None,       ['melee_weapon']),
    'loyalty':              (3, 2, None,       ['trident']),
    'luck_of_the_sea':      (3, 4, None,       ['fishing']),
    'lunge':                (3, 2, None,       ['lunge']),
    'lure':                 (3, 4, None,       ['fishing']),
    'mending':              (1, 4, None,       ['durability']),
    'multishot':            (1, 4, 'crossbow', ['crossbow']),
    'piercing':             (4, 1, 'crossbow', ['crossbow']),
    'power':                (5, 1, None,       ['bow']),
    'projectile_protection':(4, 2, 'armor',    ['armor']),
    'protection':           (4, 1, 'armor',    ['armor']),
    'punch':                (2, 4, None,       ['bow']),
    'quick_charge':         (3, 2, None,       ['crossbow']),
    'respiration':          (3, 4, None,       ['head_armor']),
    'riptide':              (3, 4, 'riptide',  ['trident']),
    'sharpness':            (5, 1, 'damage',   ['sharp_weapon']),
    'silk_touch':           (1, 8, 'mining',   ['mining_loot']),
    'smite':                (5, 2, 'damage',   ['weapon']),
    'soul_speed':           (3, 8, None,       ['foot_armor']),
    'sweeping_edge':        (3, 4, None,       ['sweeping']),
    'swift_sneak':          (3, 8, None,       ['leg_armor']),
    'thorns':               (3, 8, None,       ['armor']),
    'unbreaking':           (3, 2, None,       ['durability']),
    'vanishing_curse':      (1, 8, None,       ['vanishing']),
    'wind_burst':           (3, 4, None,       ['mace']),
}
# Tags enchantment/exclusive_set/*. La compatibilidad se mira en los dos sentidos (riptide excluye a
# loyalty y channeling, que no tienen conjunto propio y son compatibles entre sí).
EXCL = {
    'armor': {'protection', 'blast_protection', 'fire_protection', 'projectile_protection'},
    'boots': {'frost_walker', 'depth_strider'},
    'bow': {'infinity', 'mending'},
    'crossbow': {'multishot', 'piercing'},
    'damage': {'sharpness', 'smite', 'bane_of_arthropods', 'impaling', 'density', 'breach'},
    'mining': {'fortune', 'silk_touch'},
    'riptide': {'loyalty', 'channeling'},
}
EXCLUSIVE_OF = {e: EXCL[v[2]] if v[2] else set() for e, v in E.items()}

# Tags item/enchantable/* de la 26.3, resueltos por tipo de objeto.
DUR = {'helmet', 'turtle_helmet', 'chestplate', 'leggings', 'boots', 'elytra', 'shield', 'sword', 'axe',
       'pickaxe', 'shovel', 'hoe', 'bow', 'crossbow', 'trident', 'flint_and_steel', 'shears', 'brush',
       'fishing_rod', 'carrot_on_a_stick', 'warped_fungus_on_a_stick', 'mace', 'spear'}
TAGS = {
    'head_armor': {'helmet', 'turtle_helmet'}, 'chest_armor': {'chestplate'},
    'leg_armor': {'leggings'}, 'foot_armor': {'boots'},
    'armor': {'helmet', 'turtle_helmet', 'chestplate', 'leggings', 'boots'},
    'equippable': {'helmet', 'turtle_helmet', 'chestplate', 'leggings', 'boots', 'elytra', 'skull', 'carved_pumpkin'},
    'durability': DUR, 'vanishing': DUR | {'compass', 'carved_pumpkin', 'skull'},
    'melee_weapon': {'sword', 'spear'}, 'sharp_weapon': {'sword', 'spear', 'axe'},
    'weapon': {'sword', 'spear', 'axe', 'mace'}, 'fire_aspect': {'sword', 'spear', 'mace'},
    'sweeping': {'sword'}, 'lunge': {'spear'}, 'mace': {'mace'},
    'mining': {'axe', 'pickaxe', 'shovel', 'hoe', 'shears'}, 'mining_loot': {'axe', 'pickaxe', 'shovel', 'hoe'},
    'bow': {'bow'}, 'crossbow': {'crossbow'}, 'trident': {'trident'}, 'fishing': {'fishing_rod'},
}
KINDS = sorted(set().union(*TAGS.values()))


def can_enchant(kind, e):
    return kind == 'book' or any(kind in TAGS[t] for t in E[e][3])


def compatible(a, b):
    return a == b or (b not in EXCLUSIVE_OF[a] and a not in EXCLUSIVE_OF[b])


def anvil(left, right):
    """left/right = (tipo, {ench: nivel}, repair_cost). Devuelve (resultado, coste) o None si no se puede.
    Sin durabilidad ni renombrado: solo la parte de encantamientos y penalización."""
    lk, le, lrc = left
    rk, re_, rrc = right
    is_book = rk == 'book'
    if not is_book and rk != lk:
        return None
    ench = dict(le)
    cost, applied, rejected = 0, False, False
    for e, r in re_.items():
        q = ench.get(e, 0)
        r = r + 1 if q == r else max(r, q)
        ok = can_enchant(lk, e)
        for other in list(ench):
            if not compatible(e, other):
                ok = False
                cost += 1                       # +1 por cada encantamiento incompatible
        if not ok:
            rejected = True
            continue
        applied = True
        r = min(r, E[e][0])
        ench[e] = r
        mult = max(1, E[e][1] // 2) if is_book else E[e][1]
        cost += mult * r                        # se cobra el nivel FINAL, aunque no suba
    if rejected and not applied:
        return None
    if cost <= 0:
        return None
    total = lrc + rrc + cost
    rc = max(lrc, rrc) * 2 + 1
    return (lk, ench, rc), total


def key(item):
    return item[0], tuple(sorted(item[1].items())), item[2]


def optimize(target, books):
    """DP sobre subconjuntos. El objetivo siempre va a la izquierda; los libros pueden ir a cualquier lado."""
    items = [target] + books
    n = len(items)
    best = {}  # mask -> {key: (total, max_step, plan, item)}
    for i, it in enumerate(items):
        best[1 << i] = {key(it): (0, 0, label(it), it)}
    full = (1 << n) - 1
    for mask in sorted(range(1, full + 1), key=lambda m: bin(m).count('1')):
        if mask in best:
            continue
        states = {}
        sub = (mask - 1) & mask
        while sub:
            a, b = sub, mask ^ sub
            sub = (sub - 1) & mask
            if a not in best or b not in best:
                continue
            if b & 1:                            # el objetivo nunca se sacrifica
                continue
            for la in best[a].values():
                for lb in best[b].values():
                    r = anvil(la[3], lb[3])
                    if r is None:
                        continue
                    res, c = r
                    if c >= 40:
                        continue
                    tot = la[0] + lb[0] + c
                    k = key(res)
                    cand = (tot, max(la[1], lb[1], c), '(%s + %s = %d)' % (la[2], lb[2], c), res)
                    if k not in states or cand[:2] < states[k][:2]:
                        states[k] = cand
        if states:
            best[mask] = states
    return best.get(full, {})


def label(it):
    kind, ench, rc = it
    s = kind + '[' + ','.join('%s%s' % (e, '' if E[e][0] == 1 else ' ' + str(l)) for e, l in sorted(ench.items())) + ']'
    return s + ('{rc=%d}' % rc if rc else '')


def parse_ench(tok):
    e, _, lvl = tok.partition(':')
    if e not in E:
        sys.exit('encantamiento desconocido: %s' % e)
    return e, int(lvl or 1)


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__ or open(__file__).read().split('\nimport')[0]); return
    if argv[0] == '--combinar':
        def parse_item(s):
            kind, *rest = s.split(':', 1)
            ench, rc = {}, 0
            for t in (rest[0].split(',') if rest else []):
                if t.startswith('rc='):
                    rc = int(t[3:]); continue
                e, l = parse_ench(t); ench[e] = l
            return kind, ench, rc
        left, right = parse_item(argv[1]), parse_item(argv[2])
        r = anvil(left, right)
        if r is None:
            print('No se puede combinar.')
        else:
            res, c = r
            print('%s + %s -> %s  coste %d%s' % (label(left), label(right), label(res), c,
                                               '  (¡Demasiado caro!)' if c >= 40 else ''))
        return
    kind = argv[0]
    if kind not in KINDS:
        sys.exit('tipo de objeto desconocido: %s (válidos: %s)' % (kind, ', '.join(KINDS)))
    trabajo = 0
    if '--trabajo' in argv:
        i = argv.index('--trabajo'); trabajo = int(argv[i + 1]); argv = argv[:i] + argv[i + 2:]
    rc = 2 ** trabajo - 1
    books = []
    for tok in argv[1:]:
        e, l = parse_ench(tok)
        if not can_enchant(kind, e):
            sys.exit('%s no se puede poner en %s' % (e, kind))
        books.append(('book', {e: l}, 0))
    for a, b in itertools.combinations(books, 2):
        ea, eb = next(iter(a[1])), next(iter(b[1]))
        if not compatible(ea, eb):
            sys.exit('%s y %s son incompatibles' % (ea, eb))
    if len(books) > 10:
        sys.exit('máximo 10 libros')
    res = optimize((kind, {}, rc), books)
    want = {next(iter(b[1])): next(iter(b[1].values())) for b in books}
    done = [v for v in res.values() if v[3][1] == want]
    if not done:
        print('Imposible sin llegar a 40 niveles en algún paso.'); return
    tot, mx, plan, item = min(done, key=lambda v: (v[0], v[1]))
    print('Total: %d niveles  (paso más caro: %d, penalización final: %d)' % (tot, mx, item[2]))
    print(plan)


if __name__ == '__main__':
    main(sys.argv[1:])
