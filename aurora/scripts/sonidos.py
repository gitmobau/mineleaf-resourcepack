# Aurora sounds: synthesised chimes for enchanting, anvil, level up and XP pickup.
# Mono 44.1 kHz Ogg Vorbis (mono keeps the positional attenuation). Needs numpy + ffmpeg (libvorbis).
import os, sys, json, subprocess, tempfile, wave
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # build.py runs scripts with -I
import gear

REF = gear.REF
PACK = gear.PACK
PREVIEWS = gear.PREVIEWS
SR = 44100

def note(n):
    """MIDI note number -> Hz"""
    return 440.0 * 2 ** ((n - 69) / 12)

def env(n, attack=0.004, decay=0.6):
    t = np.arange(n) / SR
    e = np.exp(-t / decay)
    a = int(attack * SR)
    if a: e[:a] *= np.linspace(0, 1, a)
    return e

def bell(f, dur, decay=0.5, partials=((1, 1.0), (2.0, 0.35), (3.01, 0.18), (4.2, 0.1), (5.43, 0.05)), detune=0.0):
    n = int(dur * SR); t = np.arange(n) / SR
    out = np.zeros(n)
    for k, (r, a) in enumerate(partials):
        out += a * np.sin(2 * np.pi * f * r * (1 + detune * (k % 2)) * t) * env(n, decay=decay / (1 + 0.6 * k))
    return out

def place(buf, snd, at):
    i = int(at * SR)
    j = min(len(buf), i + len(snd))
    buf[i:j] += snd[:j - i]

def reverb(x, seconds=1.2, mix=0.28, seed=1):
    rng = np.random.default_rng(seed)
    n = int(seconds * SR)
    ir = rng.standard_normal(n) * np.exp(-np.arange(n) / SR / (seconds / 5))
    ir[:int(0.012 * SR)] = 0                       # pre-delay
    ir /= np.sqrt(np.sum(ir ** 2))
    L = len(x) + n
    wet = np.fft.irfft(np.fft.rfft(x, 2 * L) * np.fft.rfft(ir, 2 * L))[:L]
    dry = np.concatenate([x, np.zeros(n)])
    return dry * (1 - mix) + wet * mix

def sparkle(dur, density, seed, lo=5000, hi=9000):
    rng = np.random.default_rng(seed)
    buf = np.zeros(int(dur * SR))
    for _ in range(int(dur * density)):
        f = rng.uniform(lo, hi)
        place(buf, bell(f, 0.08, decay=0.025, partials=((1, 1.0),)) * rng.uniform(0.05, 0.15), rng.uniform(0, dur * 0.9))
    return buf

def finish(x, peak=0.85, tail=0.02):
    x = x / max(1e-9, np.max(np.abs(x))) * peak
    loud = np.nonzero(np.abs(x) > 0.002)[0]          # drop the silent reverb tail
    x = x[:loud[-1] + int(0.05 * SR)] if len(loud) else x
    f = int(tail * SR)
    x[-f:] *= np.linspace(1, 0, f)
    return x

def write_ogg(x, rel):
    p = PACK + 'sounds/' + rel + '.ogg'
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as t:
        tmp = t.name
    with wave.open(tmp, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype('<i2').tobytes())
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', tmp, '-c:a', 'libvorbis', '-q:a', '5',
                    '-fflags', '+bitexact', '-flags:a', '+bitexact', '-map_metadata', '-1', p], check=True)
    os.unlink(tmp)
    return x

PENTA = [0, 2, 4, 7, 9]   # major pentatonic

def enchant(v):
    """rising pentatonic arpeggio + sparkles, three variants in different keys"""
    root = [79, 81, 84][v]          # G5, A5, C6
    seq = [root + 12 * (i // 5) + PENTA[i % 5] for i in range(8)]
    buf = np.zeros(int(1.6 * SR))
    for i, m in enumerate(seq):
        place(buf, bell(note(m), 1.2, decay=0.45) * (0.55 + 0.05 * i), 0.055 * i)
    place(buf, bell(note(root - 12), 1.5, decay=0.8, partials=((1, 1), (2, 0.3), (3, 0.1))) * 0.35, 0.0)
    buf += sparkle(1.6, 22, seed=10 + v)
    return finish(reverb(buf, 1.4, 0.32, seed=v))

def anvil():
    """crystal hammer: inharmonic bar partials + a soft click"""
    n = int(0.9 * SR)
    buf = bell(note(69), 0.9, decay=0.35, partials=((1, 1.0), (2.756, 0.5), (5.404, 0.25), (8.933, 0.12)))
    buf += bell(note(81), 0.9, decay=0.25, partials=((1, 0.4), (2.756, 0.2)))
    rng = np.random.default_rng(3)
    click = rng.standard_normal(int(0.01 * SR)) * np.linspace(1, 0, int(0.01 * SR)) * 0.6
    place(buf, click, 0)
    return finish(reverb(buf, 0.9, 0.22, seed=4))

def levelup():
    """major arpeggio and a shimmering chord"""
    buf = np.zeros(int(1.8 * SR))
    for i, m in enumerate([72, 76, 79, 84]):
        place(buf, bell(note(m), 1.4, decay=0.5) * 0.7, 0.09 * i)
    for m in (84, 88, 91, 96):
        place(buf, bell(note(m), 1.4, decay=0.7, detune=0.002) * 0.3, 0.38)
    buf += sparkle(1.8, 30, seed=7, lo=6000, hi=10000)
    return finish(reverb(buf, 1.6, 0.3, seed=8))

def orb(v):
    """short bright ping; the game already randomises its pitch"""
    m = [88, 91][v]
    buf = bell(note(m), 0.35, decay=0.09, partials=((1, 1.0), (2, 0.25), (3, 0.08)))
    buf += bell(note(m + 12), 0.35, decay=0.05, partials=((1, 0.25),))
    return finish(reverb(buf, 0.4, 0.15, seed=20 + v), peak=0.7)

def sounds():
    made = {}
    for v in range(3):
        made['enchant%d' % (v + 1)] = write_ogg(enchant(v), 'aurora/enchant%d' % (v + 1))
    made['anvil_use'] = write_ogg(anvil(), 'aurora/anvil_use')
    made['levelup'] = write_ogg(levelup(), 'aurora/levelup')
    for v in range(2):
        made['orb%d' % (v + 1)] = write_ogg(orb(v), 'aurora/orb%d' % (v + 1))
    van = json.load(open(REF + 'sounds.json'))
    def ev(key, files, volume=None):
        e = {"replace": True, "sounds": [dict({"name": "minecraft:aurora/" + f}, **({"volume": volume} if volume else {}))
                                         for f in files]}
        if 'subtitle' in van[key]: e['subtitle'] = van[key]['subtitle']
        return e
    sj = {
        "block.enchantment_table.use": ev("block.enchantment_table.use", ['enchant1', 'enchant2', 'enchant3']),
        "block.anvil.use": ev("block.anvil.use", ['anvil_use'], 0.5),
        "entity.player.levelup": ev("entity.player.levelup", ['levelup']),
        "entity.experience_orb.pickup": ev("entity.experience_orb.pickup", ['orb1', 'orb2']),
    }
    with open(PACK + 'sounds.json', 'w') as f:
        json.dump(sj, f, indent=2)
    return made

def preview(made):
    """waveform strip so the sounds can be eyeballed without playing them"""
    from PIL import Image, ImageDraw
    W, Hh = 900, 60
    im = Image.new('RGB', (W, Hh * len(made) + 10), (60, 52, 84))
    d = ImageDraw.Draw(im)
    for i, (k, x) in enumerate(made.items()):
        y0 = 5 + i * Hh + Hh // 2
        step = max(1, len(x) // (W - 140))
        for c in range(W - 140):
            seg = x[c * step:(c + 1) * step]
            if len(seg):
                a = float(np.max(np.abs(seg))) * (Hh // 2 - 4)
                d.line([(130 + c, y0 - a), (130 + c, y0 + a)], fill=tuple(int(v) for v in gear.cyc(c / W, gear.VIVID)))
        d.text((8, y0 - 6), '%s %.2fs' % (k, len(x) / SR), fill=(255, 255, 255))
    im.save(PREVIEWS + '/preview_sonidos.png')

if __name__ == '__main__':
    m = sounds()
    os.makedirs(PREVIEWS, exist_ok=True)
    preview(m)
    print('ok')
