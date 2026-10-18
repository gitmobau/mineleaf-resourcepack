# Aurora sounds: soft synthesised chimes for enchanting, anvil, level up and XP pickup.
# Mono 44.1 kHz Ogg Vorbis (mono keeps the positional attenuation). Needs numpy + ffmpeg (libvorbis).
# Everything is made from scratch (additive partials + filtered noise + a small synthetic room) and is
# deterministic: same numpy/ffmpeg -> same bytes.
#
# Design rules (the user plays hardcore for hours, with Enhanced Audio / Sound Physics style packs):
#   * every partial ends at zero (smooth attack, decay to silence, cosine fade) -> no clicks;
#   * nothing above ~11 kHz (the game resamples up to x1.25 pitch) -> no aliasing, no hiss;
#   * gentle presence band (2-5 kHz) and short, dark reverb tails (the game/mods add their own room);
#   * each file is normalised to a K-weighted loudness close to the vanilla sound it replaces.
import os, sys, json, subprocess, tempfile, wave
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # build.py runs scripts with -I
import gear

REF = gear.REF
PACK = gear.PACK
PREVIEWS = gear.PREVIEWS
SR = 44100
FMAX = 11000          # no partial above this

def note(m):
    """MIDI note number -> Hz"""
    return 440.0 * 2 ** ((m - 69) / 12)

def secs(n):
    return np.arange(n) / SR

# ---------------------------------------------------------------- filters (zero-phase, FFT domain)
def spectral(x, gain):
    """apply a real magnitude response gain(f) to x; zero-padded so nothing wraps around"""
    n = 1 << int(np.ceil(np.log2(2 * len(x) + 1)))
    f = np.fft.rfftfreq(n, 1 / SR)
    return np.fft.irfft(np.fft.rfft(x, n) * gain(f), n)[:len(x)]

def lp(fc, order=2):
    return lambda f: 1 / np.sqrt(1 + (f / fc) ** (2 * order))

def hp(fc, order=2):
    return lambda f: 1 / np.sqrt(1 + (fc / np.maximum(f, 1e-3)) ** (2 * order))

def bp(lo, hi, order=2):
    return lambda f: lp(hi, order)(f) * hp(lo, order)(f)

# ---------------------------------------------------------------- sources
def ramp(n):
    """raised-cosine 0 -> 1 over n samples"""
    return 0.5 - 0.5 * np.cos(np.pi * np.arange(n) / max(1, n))

def partials(f, dur, parts, decay, attack=0.004, trem=0.0):
    """additive tone. parts = (ratio, amp, decay factor). Each partial: smooth attack, exponential decay,
    cosine fade-out at the end so it always reaches exactly 0. Partials above FMAX are dropped."""
    n = int(dur * SR); t = secs(n)
    out = np.zeros(n)
    for r, a, dk in parts:
        if f * r > FMAX: continue
        out += a * np.sin(2 * np.pi * f * r * t) * np.exp(-t / (decay * dk))
    a = int(attack * SR)
    out[:a] *= ramp(a)
    if trem:                                          # slow vibraphone-like shimmer, fades in
        out *= 1 - trem * (0.5 - 0.5 * np.cos(2 * np.pi * 4.6 * t)) * np.minimum(1, t / 0.25)
    fo = min(n // 3, int(0.06 * SR))
    out[n - fo:] *= ramp(fo)[::-1]
    return out

def ring(f, dur, parts, decay, attack=0.004, beat=0.0, **kw):
    """partials() plus an optional twin a few cents away: the slow beating of a real bell or metal bar"""
    x = partials(f, dur, parts, decay, attack, **kw)
    if beat:
        x = 0.62 * x + 0.38 * partials(f * 2 ** (beat / 1200), dur, parts, decay * 0.9, attack)
    return x

def noise(dur, seed, band, attack=0.002, decay=0.01):
    """band-limited noise burst (hammer contact, air)"""
    n = int(dur * SR)
    x = spectral(np.random.default_rng(seed).standard_normal(n), band)
    e = np.exp(-secs(n) / decay); a = int(attack * SR)
    e[:a] *= ramp(a)
    return x * e / max(1e-9, np.max(np.abs(x)))

def mix(*items):
    """sum (sound, start time) pairs into a buffer long enough for all of them (nothing is ever cut off)"""
    starts = [int(round(at * SR)) for _, at in items]
    buf = np.zeros(max(i + len(x) for (x, _), i in zip(items, starts)))
    for (x, _), i in zip(items, starts):
        buf[i:i + len(x)] += x
    return buf

# Timbres: (ratio, amplitude, decay factor). Higher partials die sooner, as in real struck objects.
CELESTA = ((1, 1.0, 1.0), (2.0, 0.16, 0.45), (3.0, 0.05, 0.3), (4.02, 0.035, 0.22))
VIBES = ((1, 1.0, 1.0), (3.98, 0.12, 0.28), (9.9, 0.015, 0.1))               # tuned bar: warm, round
GLASS = ((1, 1.0, 1.0), (2.0, 0.22, 0.5), (2.98, 0.06, 0.35), (4.16, 0.03, 0.2), (5.43, 0.012, 0.12))
STEEL = ((1, 1.0, 1.0), (2.756, 0.7, 0.7), (5.404, 0.45, 0.35), (8.933, 0.14, 0.15))  # free bar modes
DROP = ((1, 1.0, 1.0), (2.0, 0.10, 0.4), (3.0, 0.025, 0.25))

# ---------------------------------------------------------------- room
def reverb(x, rt=1.0, mix=0.2, seed=1, predelay=0.014, dark=3500):
    """small synthetic room: noise impulse response whose highs die faster than its lows (a dark,
    natural tail), soft onset after the pre-delay, low end trimmed so the tail never booms."""
    rng = np.random.default_rng(seed)
    n = int(rt * 1.1 * SR); t = secs(n)
    w = rng.standard_normal(n)
    lo = spectral(w, lp(dark, 2)); hi = w - lo
    ir = lo * np.exp(-6.91 * t / rt) + 0.5 * hi * np.exp(-6.91 * t / (0.35 * rt))
    ir = spectral(ir, hp(250, 1))
    d = int(predelay * SR); s = int(0.02 * SR)
    ir[:d] = 0; ir[d:d + s] *= ramp(s)
    ir[n - n // 8:] *= ramp(n // 8)[::-1]
    ir /= np.sqrt(np.sum(ir ** 2))
    L = len(x) + n
    m = 1 << int(np.ceil(np.log2(L)))
    wet = np.fft.irfft(np.fft.rfft(x, m) * np.fft.rfft(ir, m), m)[:L]
    dry = np.concatenate([x, np.zeros(n)])
    return dry * (1 - mix) + wet * mix * 2.2   # IR has unit energy; 2.2 ~ matches the dry level

# ---------------------------------------------------------------- loudness
def kweight(x):
    """ITU-R BS.1770 K-weighting magnitude (high shelf + 38 Hz high-pass), bilinear at SR"""
    def biq(b, a):
        def g(f):
            z = np.exp(-2j * np.pi * f / SR)
            return np.abs((b[0] + b[1] * z + b[2] * z * z) / (1 + a[0] * z + a[1] * z * z))
        return g
    K = np.tan(np.pi * 1681.974450955533 / SR); Q = 0.7071752369554196
    Vh = 10 ** (3.999843853973347 / 20); Vb = Vh ** 0.4996667741545416; a0 = 1 + K / Q + K * K
    shelf = biq([(Vh + Vb * K / Q + K * K) / a0, 2 * (K * K - Vh) / a0, (Vh - Vb * K / Q + K * K) / a0],
                [2 * (K * K - 1) / a0, (1 - K / Q + K * K) / a0])
    K = np.tan(np.pi * 38.13547087602444 / SR); Q = 0.5003270373238773; a0 = 1 + K / Q + K * K
    high = biq([1, -2, 1], [2 * (K * K - 1) / a0, (1 - K / Q + K * K) / a0])
    return spectral(x, lambda f: shelf(f) * high(f))

def loudness(x):
    """max momentary loudness (400 ms window, LUFS-like) and gated integrated loudness"""
    y = kweight(x) ** 2
    w = int(0.4 * SR)
    y = np.concatenate([y, np.zeros(w)])
    c = np.concatenate([[0], np.cumsum(y)])
    ms = (c[w::441] - c[:-w:441])[:max(1, (len(x) + 441 - 1) // 441)] / w
    L = -0.691 + 10 * np.log10(ms + 1e-20)
    g = ms[L > -70]
    if len(g): g = g[L[L > -70] > -0.691 + 10 * np.log10(np.mean(g)) - 10]
    return float(L.max()), float(-0.691 + 10 * np.log10(np.mean(g))) if len(g) else -99.0

def finish(x, target, ceiling=0.89, floor_db=-52):
    """clean up and set the level: high-pass (no rumble/DC), low-pass (no hiss, no aliasing when the
    game pitches it up), loudness normalisation to `target` (max momentary, K-weighted) under a peak
    ceiling of -1 dBFS, trim the silent tail and fade it out smoothly."""
    x = spectral(x, lambda f: hp(90, 2)(f) * lp(9500, 3)(f))
    x *= 10 ** ((target - loudness(x)[0]) / 20)
    x *= min(1.0, ceiling / np.max(np.abs(x)))
    loud = np.nonzero(np.abs(x) > np.max(np.abs(x)) * 10 ** (floor_db / 20))[0]
    x = x[:loud[-1] + int(0.03 * SR)].copy()
    f = min(len(x) // 4, int(0.12 * SR))
    x[-f:] *= ramp(f)[::-1]
    a = int(0.0015 * SR)
    x[:a] *= ramp(a)
    return x

# ---------------------------------------------------------------- the sounds
# Loudness targets: max momentary K-weighted loudness (dB, LUFS-like) measured on the vanilla 26.3 files
# with the same sounds.json volume -> enchant -23.5, anvil -16.4 (file -10.4 at volume 0.5), levelup -13.6,
# orb -18.0. Aurora sits at or slightly below vanilla: the chimes are tonal and carry more than vanilla noise.
TARGET = {'enchant': -23.5, 'anvil': -17.5, 'levelup': -14.5, 'orb': -20.0}

ENCHANT = [  # (notes, low pad) -- all diatonic C major so the three variants are one family
    ((72, 76, 79, 83, 86), 60),    # Cmaj9   C E G B D
    ((69, 72, 76, 79, 84), 57),    # Am9     A C E G C
    ((65, 72, 76, 79, 81), 53),    # Fmaj9   F C E G A
]

def enchant(v):
    """magic air swell + a soft rising vibraphone/celesta arpeggio that blooms on its last note"""
    notes, pad = ENCHANT[v]
    # breath of air (the vanilla enchant is a whoosh): two noise bands cross-fading upwards
    t = secs(int(0.9 * SR))
    w = np.random.default_rng(40 + v).standard_normal(len(t))
    up = np.minimum(1, t / 0.6)
    air = (spectral(w, bp(350, 900)) * (1 - up) + 0.6 * spectral(w, bp(900, 2200)) * up) * np.sin(np.pi * t / 0.9) ** 2
    parts = [(0.05 * air / np.max(np.abs(air)), 0.0),
             # warm low pad note under everything
             (0.22 * ring(note(pad), 1.0, ((1, 1, 1), (2, 0.25, 0.6), (3, 0.06, 0.4)), 0.32, attack=0.06, beat=4), 0.02)]
    # the arpeggio, slightly humanised; vibraphone and celesta alternate
    at = (0.0, 0.072, 0.146, 0.224, 0.31)
    vel = (0.55, 0.62, 0.7, 0.78, 0.95)
    for i, m in enumerate(notes):
        last = i == len(notes) - 1
        parts.append((vel[i] * ring(note(m), 1.15 if last else 0.75, VIBES if i % 2 == 0 else CELESTA,
                                    0.42 if last else 0.22 - 0.01 * i, attack=0.005, beat=3 if last else 0,
                                    trem=0.18 if last else 0), 0.02 + at[i]))
    # two faint glints high above, a pure sine each
    for k, (dt, st) in enumerate(((0.38, 31), (0.5, 29))):
        parts.append((0.05 * partials(note(notes[-1 - k] + st), 0.25, ((1, 1, 1),), 0.05, attack=0.006), dt))
    return finish(reverb(mix(*parts), 1.1, 0.24, seed=v), TARGET['enchant'])

def anvil(v):
    """three hammer strikes like vanilla, but on a sweet-sounding steel bar: soft contact noise,
    inharmonic bar modes that fade fast, a short ring with a gentle beat and a small dark room"""
    f0 = [note(76), note(74)][v]                      # E5 / D5: bar modes at ~1.7 and ~3.4 kHz
    hits = [(0.0, 0.85, 0.0), (0.21, 0.7, 0.012), (0.42, 1.0, -0.006)] if v == 0 else \
           [(0.0, 0.8, 0.0), (0.2, 0.75, -0.01), (0.4, 1.0, 0.008)]
    parts = []
    for k, (at, amp, dpitch) in enumerate(hits):
        last = k == len(hits) - 1
        f = f0 * (1 + dpitch)
        parts += [(amp * ring(f, 0.75 if last else 0.4, STEEL, 0.2 if last else 0.09, attack=0.0012, beat=5), at),
                  (amp * 0.35 * partials(f * 0.25 * 1.007, 0.2, ((1, 1, 1),), 0.035, attack=0.002), at),   # body thud
                  (amp * 0.22 * noise(0.03, 70 + 3 * v + k, bp(600, 3200), attack=0.0008, decay=0.004), at)]  # contact
    return finish(reverb(mix(*parts), 0.55, 0.16, seed=10 + v, dark=3000), TARGET['anvil'])

def levelup():
    """quick rising G-C-E that lands on a glassy C6 major chord, with a short sparkle on top"""
    land = 0.17
    parts = [((0.42 + 0.06 * i) * ring(note(m), 0.45, CELESTA, 0.12), 0.055 * i) for i, m in enumerate((67, 72, 76))]
    parts.append((ring(note(84), 1.1, GLASS, 0.4, attack=0.004, beat=3, trem=0.12), land))
    parts += [(a * ring(note(m), 1.0, VIBES, 0.34, attack=0.012, beat=4), land + 0.012) for m, a in ((88, 0.34), (91, 0.3), (72, 0.36))]
    parts += [((0.07 - 0.01 * k) * partials(note(m), 0.2, ((1, 1, 1),), 0.045, attack=0.005), land + 0.05 + 0.045 * k)
              for k, m in enumerate((96, 98, 100, 103))]          # C7 D7 E7 G7: a tiny upward sparkle
    return finish(reverb(mix(*parts), 0.9, 0.22, seed=8), TARGET['levelup'])

ORB = [(88, 0.0), (91, 0.004), (86, -0.003)]   # E6, G6, D6 + a hint of pitch glide

def orb(v):
    """tiny round water-glass drop: soft attack, almost pure tone, 0.3 s. The game plays it very often
    and already randomises its pitch (x0.55-1.25), so it has to stay quiet, short and mellow."""
    m, glide = ORB[v]
    n = int(0.3 * SR); t = secs(n)
    f = note(m) * (1 + glide * np.exp(-t / 0.02))          # settles onto the note in ~20 ms
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.zeros(n)
    for r, a, dk in DROP:
        x += a * np.sin(r * ph) * np.exp(-t / (0.07 * dk))
    a = int(0.003 * SR); x[:a] *= ramp(a)
    fo = int(0.05 * SR); x[-fo:] *= ramp(fo)[::-1]
    return finish(reverb(x, 0.3, 0.12, seed=20 + v, predelay=0.008, dark=4000), TARGET['orb'])

FILES = {
    "block.enchantment_table.use": ['enchant1', 'enchant2', 'enchant3'],
    "block.anvil.use": ['anvil_use1', 'anvil_use2'],
    "entity.player.levelup": ['levelup'],
    "entity.experience_orb.pickup": ['orb1', 'orb2', 'orb3'],
}

def write_ogg(x, rel):
    p = PACK + 'sounds/' + rel + '.ogg'
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as t:
        tmp = t.name
    with wave.open(tmp, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(np.round(np.clip(x, -1, 1) * 32767).astype('<i2').tobytes())
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', tmp, '-c:a', 'libvorbis', '-q:a', '5',
                    '-fflags', '+bitexact', '-flags:a', '+bitexact', '-map_metadata', '-1', p], check=True)
    os.unlink(tmp)
    return x

def sounds():
    made = {}
    for v in range(3): made['enchant%d' % (v + 1)] = enchant(v)
    for v in range(2): made['anvil_use%d' % (v + 1)] = anvil(v)
    made['levelup'] = levelup()
    for v in range(3): made['orb%d' % (v + 1)] = orb(v)
    for k, x in made.items():
        write_ogg(x, 'aurora/' + k)
    van = json.load(open(REF + 'sounds.json'))
    sj = {}
    for key, files in FILES.items():
        sj[key] = {"replace": True, "sounds": [{"name": "minecraft:aurora/" + f} for f in files]}
        if 'subtitle' in van[key]: sj[key]['subtitle'] = van[key]['subtitle']
    with open(PACK + 'sounds.json', 'w') as f:
        json.dump(sj, f, indent=2)
    return made

def preview(made, path=None):
    """waveform + spectrogram (0-11 kHz) of each sound, so they can be eyeballed without playing them"""
    from PIL import Image, ImageDraw
    W, LBL, WH, SH, SEC = 760, 150, 24, 64, 1.9
    pps = (W - LBL) / SEC
    im = Image.new('RGB', (W, (WH + SH + 8) * len(made) + 6), (34, 28, 52))
    d = ImageDraw.Draw(im)
    nfft = 1024; win = np.hanning(nfft); fr = np.fft.rfftfreq(nfft, 1 / SR); rows = np.nonzero(fr <= FMAX)[0]
    for i, (k, x) in enumerate(made.items()):
        y0 = 6 + i * (WH + SH + 8)
        col = lambda c: tuple(int(v) for v in gear.cyc(c / W, gear.VIVID))
        for c in range(W - LBL):
            seg = x[int(c / pps * SR):int((c + 1) / pps * SR)]
            if len(seg):
                a = float(np.max(np.abs(seg))) * (WH // 2 - 1)
                d.line([(LBL + c, y0 + WH // 2 - a), (LBL + c, y0 + WH // 2 + a)], fill=col(c))
            j = int(c / pps * SR) - nfft // 2
            seg = x[max(0, j):max(0, j + nfft)]
            if j >= len(x): continue
            seg = np.pad(seg, (0, nfft - len(seg)))
            S = 20 * np.log10(np.abs(np.fft.rfft(seg * win))[rows] + 1e-9)
            S = np.clip((S + 20) / 60, 0, 1)
            for r in range(SH):
                v = S[min(len(S) - 1, int((SH - 1 - r) / SH * len(S)))]
                if v > 0.02:
                    im.putpixel((LBL + c, y0 + WH + r), (int(40 + 215 * v), int(30 + 170 * v ** 1.6), int(70 + 185 * v ** 0.7)))
        mx, _ = loudness(x)
        d.text((8, y0 + 8), k, fill=(255, 255, 255))
        d.text((8, y0 + 26), '%.2f s' % (len(x) / SR), fill=(200, 190, 230))
        d.text((8, y0 + 42), '%.1f LUFS-M' % mx, fill=(200, 190, 230))
    im.save(path or PREVIEWS + '/preview_sonidos.png')

if __name__ == '__main__':
    m = sounds()
    os.makedirs(PREVIEWS, exist_ok=True)
    preview(m)
    print('ok')
