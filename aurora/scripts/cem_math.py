"""Subconjunto CEM usado por Aurora; evaluador seguro para validar y previsualizar.

EMFPartData.prepare invierte los ejes, convierte grados a radianes y prepara cada
submodelo por separado. Las animaciones asignan después valores de runtime.
"""
import ast
import math
import operator
from functools import lru_cache

OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}
PROPERTIES = ('tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz')


@lru_cache(maxsize=128)
def expression(text):
    tree = ast.parse(text, mode='eval').body

    def check(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return
        if isinstance(node, ast.Name) and node.id in ('age', 'pi'):
            return
        if isinstance(node, ast.BinOp) and type(node.op) in OPS:
            check(node.left); check(node.right); return
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            check(node.operand); return
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ('sin', 'cos') and len(node.args) == 1 and not node.keywords:
            check(node.args[0]); return
        raise ValueError('Expresión fuera del subconjunto CEM de Aurora: ' + text)
    check(tree)
    return tree


def evaluate(text, age):
    def visit(node):
        if isinstance(node, ast.Constant): return node.value
        if isinstance(node, ast.Name): return age if node.id == 'age' else math.pi
        if isinstance(node, ast.BinOp): return OPS[type(node.op)](visit(node.left), visit(node.right))
        if isinstance(node, ast.UnaryOp): return visit(node.operand) * (-1 if isinstance(node.op, ast.USub) else 1)
        return getattr(math, node.func.id)(visit(node.args[0]))
    result = visit(expression(text))
    if not math.isfinite(result): raise ValueError('Resultado CEM no finito')
    return result


def walk(nodes):
    for node in nodes:
        yield node
        yield from walk(node.get('submodels', []))


def states(model, age):
    out = {}
    nodes = list(walk(model['models']))
    for node in nodes:
        inv = node.get('invertAxis', '')
        state = {p: 1.0 if p.startswith('s') else 0.0 for p in PROPERTIES}
        for i, axis in enumerate('xyz'):
            sign = -1 if axis in inv else 1
            state['t' + axis] = node.get('translate', [0, 0, 0])[i] * sign
            state['r' + axis] = math.radians(node.get('rotate', [0, 0, 0])[i] * sign)
        out[node['id']] = state
    for node in nodes:
        for group in node.get('animations', []):
            for key, value in group.items():
                ident, prop = key.rsplit('.', 1)
                if ident not in out or prop not in PROPERTIES:
                    raise ValueError('Destino CEM desconocido: ' + key)
                out[ident][prop] = evaluate(value, age)
    return out


def transform(point, state):
    """ModelPart: traslación * Rz * Ry * Rx * escala (rotationZYX)."""
    x, y, z = (point[i] * state['s' + a] for i, a in enumerate('xyz'))
    c, s = math.cos(state['rx']), math.sin(state['rx']); y, z = y*c-z*s, y*s+z*c
    c, s = math.cos(state['ry']), math.sin(state['ry']); x, z = x*c+z*s, -x*s+z*c
    c, s = math.cos(state['rz']), math.sin(state['rz']); x, y = x*c-y*s, x*s+y*c
    return x + state['tx'], y + state['ty'], z + state['tz']


def box_coordinates(node, box):
    m, size = list(box['coordinates'][:3]), box['coordinates'][3:]
    for i, axis in enumerate('xyz'):
        if axis in node.get('invertAxis', ''): m[i] = -m[i] - size[i]
    return m, size
