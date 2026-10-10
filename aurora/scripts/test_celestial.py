"""Regresiones de pivotes, animación y fallback; no necesita arrancar Minecraft."""
import math
import unittest

import emf
from cem_math import box_coordinates, evaluate, states, transform, walk


def vertices(model, age):
    runtime = states(model, age)
    result = []
    def visit(n, parents, part):
        chain = parents + [runtime[n['id']]]
        for b in n.get('boxes', []):
            m, size = box_coordinates(n, b)
            for bits in ((0,0,0), (1,0,0), (0,1,0), (0,0,1), (1,1,1)):
                p = tuple(m[i]+bits[i]*size[i] for i in range(3))
                for st in reversed(chain): p = transform(p, st)
                result.append(tuple(p[i]+emf.PIVOT[part][i] for i in range(3)))
        for child in n.get('submodels', []): visit(child, chain, part)
    for n in model['models']: visit(n, [], n['part'])
    return result


class CelestialTests(unittest.TestCase):
    def test_export_formula_round_trip(self):
        # Real pivots, especially the legs at y=12: exporter signs must cancel.
        m, size = (-0.7, 2.3, -3.1), (1.2, 0.25, 2.1)
        for part in emf.PIVOT:
            parent = emf.cem_part(part)
            b = emf.cem_box(part, m, size)
            decoded, _ = box_coordinates(parent, b)
            got = transform(decoded, states({'models': [parent]}, 0)[parent['id']])
            for actual, want in zip(got, m): self.assertAlmostEqual(actual, want, places=4)

    def test_halo_clears_head_and_keeps_centre(self):
        model = emf.jem('helmet')
        for age in range(0, 320, 10):
            vs = vertices(model, age)
            self.assertLess(max(v[1] for v in vs), -9.0)  # skin top is y=-8
            self.assertLess(max(abs(v[0]) for v in vs), 5.4)
            self.assertGreater(min(v[1] for v in vs), -13.0)

    def test_boots_are_at_ankles_not_origin(self):
        vs = vertices(emf.jem('boots'), 0)
        self.assertGreater(min(v[1] for v in vs), 21.5)
        self.assertLess(max(v[1] for v in vs), 22.1)
        self.assertLess(min(v[0] for v in vs), -4.4)
        self.assertGreater(max(v[0] for v in vs), 4.4)

    def test_every_animation_loops_and_moves(self):
        for slot in emf.SLOTS:
            model = emf.jem(slot)
            first, last = vertices(model, 0), vertices(model, emf.PERIOD)
            for a, b in zip(first, last):
                for x, y in zip(a, b): self.assertAlmostEqual(x, y, places=7)
            self.assertNotEqual(first, vertices(model, 13), slot)

    def test_empty_base_preserves_all_vanilla_parts(self):
        for slot, (_, _, parts) in emf.SLOTS.items():
            model = emf.jem(slot, False)
            self.assertEqual({n['part'] for n in model['models']}, set(parts))
            self.assertEqual(vertices(model, 0), [])
            self.assertTrue(all(n['attach'] for n in model['models']))
            self.assertTrue(all(not n.get('animations') for n in walk(model['models'])))
            self.assertNotIn('texture', model)

    def test_animations_are_top_level_and_target_only_custom_nodes(self):
        for slot in emf.SLOTS:
            model = emf.jem(slot)
            self.assertTrue(any(n.get('animations') for n in model['models']))
            for n in walk(model['models']):
                if n not in model['models']: self.assertFalse(n.get('animations'))
            states(model, 20)  # checks every target and expression

    def test_expression_subset_rejects_unknown_code(self):
        for expr in ('__import__("os")', 'age.__class__', 'unknown+1', 'sin(age, 2)', 'True', 'age**2'):
            with self.assertRaises(ValueError): evaluate(expr, 0)
        with self.assertRaises(ZeroDivisionError): evaluate('1/0', 0)
        self.assertAlmostEqual(evaluate('2*sin(age*pi/40)', 20), 2)


if __name__ == '__main__':
    unittest.main()
