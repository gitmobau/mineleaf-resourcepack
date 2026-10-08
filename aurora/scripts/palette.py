# Perceptual colour interpolation (OKLab) shared by the generators: smoother pastel gradients
# than plain sRGB mixing (no muddy midpoints between hues).
def _lin(c):
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def _srgb(c):
    c = 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
    return max(0.0, min(255.0, c * 255))

def to_oklab(rgb):
    r, g, b = (_lin(v) for v in rgb[:3])
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)

def from_oklab(lab):
    L, a, b = lab
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    return (_srgb(4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s),
            _srgb(-1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s),
            _srgb(-0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s))

_cache = {}
def cycle(t, pal):
    """position t (wraps at 1) along the closed palette loop, interpolated in OKLab"""
    key = id(pal)
    if key not in _cache:
        _cache[key] = [to_oklab(c) for c in pal]
    lab = _cache[key]
    t = (t % 1.0) * len(pal); i = int(t) % len(pal); f = t - int(t)
    a = lab[i]; b = lab[(i + 1) % len(pal)]
    return from_oklab(tuple(a[k] + (b[k] - a[k]) * f for k in range(3)))
