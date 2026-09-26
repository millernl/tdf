"""Temp score, synthesised: war drums, timpani, low brass, a hall — in the spirit of
Woodkid's 'Iron'. 130 BPM, D minor, resolving to D major on the logo.

It's a stand-in so the cut can be judged against a pulse; the real track replaces it.
Everything is placed on a bar/beat grid: bar(n, beat) → seconds.
"""
import numpy as np
from scipy import signal

SR = 48000
BPM = 130
BEAT = 60 / BPM
BAR = 4 * BEAT
_rng = np.random.default_rng(1998)

NOTE = {n: i for i, n in enumerate(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])}


def at(bar, beat=0.0):
    """Seconds of bar `bar` (1-based), beat offset `beat` (0-based, fractional ok)."""
    return (bar - 1) * BAR + beat * BEAT


def hz(name):
    """'D3' → Hz."""
    pitch, octave = name[:-1], int(name[-1])
    return 440.0 * 2 ** ((NOTE[pitch] + 12 * (octave + 1) - 69) / 12)


def _t(dur):
    return np.arange(int(dur * SR)) / SR


def _place(track, x, t, gain=1.0):
    i = int(round(t * SR))
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    j = min(len(track), i + len(x))
    if i < len(track) and j > i:
        track[i:j] += x[: j - i] * gain


def _lp(x, fc, order=2):
    return signal.sosfilt(signal.butter(order, min(fc, SR * 0.45) / (SR / 2), output="sos"), x)


def _bp(x, lo, hi, order=2):
    return signal.sosfilt(signal.butter(order, [lo / (SR / 2), hi / (SR / 2)], "band", output="sos"), x)


# ── drums ────────────────────────────────────────────────────────────────────
def taiko(f0=62, f1=44, decay=0.55, skin=0.35):
    t = _t(decay * 3.2)
    f = f1 + (f0 - f1) * np.exp(-t * 18)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t / decay) + 0.25 * np.sin(1.52 * ph) * np.exp(-t / (decay * 0.5))
    hit = _lp(_rng.standard_normal(len(t)), 1800) * np.exp(-t * 55) * skin
    return np.tanh((body + hit) * 1.8) / np.tanh(1.8)


def tom(f0=140, f1=95, decay=0.28):
    return taiko(f0, f1, decay, skin=0.5) * 0.8


def timpani(f=hz("D2"), decay=1.6):
    t = _t(decay * 2.5)
    modes = ((1.0, 1.0), (1.504, 0.5), (1.742, 0.35), (2.0, 0.25), (2.245, 0.15))
    y = sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t / (decay / r ** 0.7)) for r, a in modes)
    y += _lp(_rng.standard_normal(len(t)), 900) * np.exp(-t * 40) * 0.4
    return y * 0.6


def rim():
    t = _t(0.06)
    y = _bp(_rng.standard_normal(len(t)), 1800, 5000) * np.exp(-t * 90) + 0.3 * np.sin(2 * np.pi * 820 * t) * np.exp(-t * 70)
    return y * 0.45


def snare_roll(dur, start_gain=0.05, end_gain=0.5):
    out = np.zeros(int(dur * SR))
    n = int(dur / (BEAT / 8))
    for k in range(n):
        g = start_gain + (end_gain - start_gain) * (k / max(n - 1, 1)) ** 2
        t = _t(0.07)
        s = _bp(_rng.standard_normal(len(t)), 1200, 7000) * np.exp(-t * 60) + 0.2 * np.sin(2 * np.pi * 190 * t) * np.exp(-t * 50)
        i = int(k * BEAT / 8 * SR)
        out[i:i + len(s)] += s[: len(out) - i] * g
    return out


# ── tonal ────────────────────────────────────────────────────────────────────
def brass(notes, dur, attack=0.6, release=0.8, bright=(300, 2400), vib=0.004, gain=0.18):
    """Low brass / horn section: detuned saws through an opening low-pass."""
    t = _t(dur + release)
    env = np.clip(t / attack, 0, 1) ** 1.6 * np.clip((dur + release - t) / release, 0, 1)
    y = np.zeros(len(t))
    for name in notes:
        f = hz(name)
        for det in (-0.006, 0.0, 0.0065):
            fm = f * (1 + det) * (1 + vib * np.sin(2 * np.pi * 5.2 * t) * np.clip(t - 0.3, 0, 1))
            ph = np.cumsum(fm) / SR
            y += 2 * (ph % 1.0) - 1
    y /= len(notes) * 3
    # time-varying cutoff: blocks through a state-carrying filter
    out = np.zeros_like(y)
    zi = None
    blk = 512
    for s in range(0, len(y), blk):
        e = env[min(s, len(env) - 1)]
        fc = bright[0] + (bright[1] - bright[0]) * e ** 1.4
        sos = signal.butter(2, fc / (SR / 2), output="sos")
        if zi is None:
            zi = signal.sosfilt_zi(sos) * 0
        out[s:s + blk], zi = signal.sosfilt(sos, y[s:s + blk], zi=zi)
    return out * env * gain


def stab(notes, gain=0.22):
    return brass(notes, 0.35, attack=0.03, release=0.5, bright=(500, 3200), vib=0.0, gain=gain)


def drone(dur, gain=0.2):
    t = _t(dur)
    y = np.sin(2 * np.pi * hz("D1") * t) + 0.5 * np.sin(2 * np.pi * hz("D2") * t) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.2 * t))
    env = np.clip(t / 2.0, 0, 1) * np.clip((dur - t) / 1.5, 0, 1)
    return y * env * gain


def bell(f, dur=3.5, gain=0.12, ratio=3.5, index=2.2):
    """Clean FM bell — the logo's voice."""
    t = _t(dur)
    idx = index * np.exp(-t * 3)
    y = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * f * ratio * t)) * np.exp(-t * 1.4)
    return y * np.clip(t / 0.004, 0, 1) * gain


def shimmer(dur, freqs=(hz("D6"), hz("A6"), hz("F#6"), hz("D7")), gain=0.05):
    t = _t(dur)
    y = sum(np.sin(2 * np.pi * f * t + k) * (0.5 + 0.5 * np.sin(2 * np.pi * (0.7 + k * 0.3) * t + k))
            for k, f in enumerate(freqs))
    env = np.clip(t / (dur * 0.35), 0, 1) * np.clip((dur - t) / (dur * 0.45), 0, 1)
    return y * env * gain / len(freqs)


def sub(f0=48, f1=30, dur=2.6, gain=0.55):
    t = _t(dur)
    f = f1 + (f0 - f1) * np.exp(-t * 3)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.3) * np.clip(t / 0.01, 0, 1) * gain


# ── space ────────────────────────────────────────────────────────────────────
def hall(rt60=2.6, predelay=0.022):
    n = int(rt60 * 1.3 * SR)
    t = np.arange(n) / SR
    decay = np.exp(-6.9 * t / rt60)
    ir = []
    for ch in range(2):
        noise = _rng.standard_normal(n)
        hi = _lp(noise, 6000) * np.exp(-6.9 * t / (rt60 * 0.45))      # highs die first
        lo = _lp(noise, 1200) * decay
        x = (hi * 0.5 + lo) * np.clip(t / 0.03, 0, 1)
        ir.append(np.concatenate([np.zeros(int(predelay * SR)), x]))
    ir = np.stack(ir, 1)
    return ir / np.sqrt((ir ** 2).sum(0))


def reverb(dry, ir, wet):
    out = np.stack([signal.fftconvolve(dry[:, c], ir[:, c])[: len(dry)] for c in range(2)], 1)
    return dry + out * wet


# ── the cue ──────────────────────────────────────────────────────────────────
def compose(duration=30.0, music=True, logo=True, marks=None):
    """marks: dict of edit times — 'land' (door → first shot), 'drop', 'freeze',
    'heart', 'title', 'hit' (fly-through into the I), 'wordmark'."""
    m = {"land": at(3), "drop": at(7), "freeze": at(10, 2), "resume": at(11), "heart": at(13), "title": at(15),
         "hit": at(16), "wordmark": at(16, 2), **(marks or {})}
    n = int(duration * SR)
    drums = np.zeros((n, 2))
    tonal = np.zeros((n, 2))
    logo_bus = np.zeros((n, 2))
    pan = lambda x, p: np.stack([x * np.sqrt((1 - p) / 2), x * np.sqrt((1 + p) / 2)], 1)

    if music:
        _place(tonal, drone(m["hit"] + 0.4, 0.16), 0.0)
        # bars 1–2: brass swells out of the dark
        _place(tonal, brass(["D2", "A2", "D3"], m["land"] - 0.2, attack=2.6, release=0.6, bright=(180, 900)), 0.2)
        _place(drums, timpani(decay=2.0), m["land"], 0.9)
        # bars 3–6: the march
        chords = [["D2", "D3", "F3", "A3"], ["D2", "D3", "F3", "A3"], ["A#1", "A#2", "D3", "F3"], ["C2", "C3", "E3", "G3"]]
        for k in range(4):
            b = 3 + k
            _place(tonal, brass(chords[k], BAR - 0.05, attack=1.1, release=0.3, bright=(250, 1500), gain=0.15), at(b))
            _place(drums, taiko(), at(b, 0), 0.9)
            _place(drums, taiko(58, 42), at(b, 2), 0.75)
            _place(drums, pan(tom(150, 100), -0.4), at(b, 3.5), 0.45)
            for bt in (1, 3):
                _place(drums, pan(rim(), 0.3), at(b, bt), 0.35)
        for k in range(8):                                   # bar 6: toms march in eighths
            _place(drums, pan(tom(170 - 6 * k, 110), -0.5 + k * 0.14), at(6, k * 0.5), 0.3 + 0.05 * k)
        _place(drums, snare_roll(2 * BEAT), at(6, 2), 1.0)
        # bars 7–12: the drop — gallop + stabs
        stabs = [["D3", "F3", "A3", "D4"], ["A#2", "D3", "F3", "A#3"], ["F2", "A2", "C3", "F3"], ["C3", "E3", "G3", "C4"],
                 ["D3", "F3", "A3", "D4"], ["A2", "C#3", "E3", "A3"]]
        for k in range(6):
            b = 7 + k
            _place(tonal, stab(stabs[k]), at(b), 1.0)
            pad_len = min(BAR, max(m["freeze"] - at(b), 0.0)) if at(b) < m["freeze"] < at(b) + BAR else BAR
            _place(tonal, brass(stabs[k][:2], pad_len, attack=0.4, release=0.15, bright=(200, 900), gain=0.1), at(b))
            for bt in range(4):
                t_beat = at(b, bt)
                if m["freeze"] <= t_beat < m["resume"]:
                    continue                                   # the music stops with the picture
                _place(drums, taiko(66, 44, 0.45), t_beat, 0.95 if bt in (0, 2) else 0.7)
                _place(drums, pan(tom(160, 105, 0.2), -0.45), t_beat + BEAT * 0.5, 0.35)
                _place(drums, pan(tom(185, 120, 0.18), 0.45), t_beat + BEAT * 0.75, 0.3)
                _place(drums, pan(rim(), 0.2), t_beat + BEAT * 0.5, 0.18)
        _place(drums, sub(52, 34, 1.4, 0.5), m["drop"])
        _place(drums, timpani(decay=1.2), m["drop"], 0.8)
        _place(drums, taiko(70, 40, 0.8), m["resume"], 1.0)
        for k in range(16):                                    # bar 12: 16th fill
            _place(drums, pan(tom(200 - 5 * k, 110, 0.15), np.sin(k)), at(12, 2 + k * 0.125), 0.25 + 0.03 * k)
        # bars 13–14: the heart — drums out, warm major
        _place(drums, taiko(60, 38, 1.1), m["heart"], 1.0)
        _place(drums, sub(46, 30, 2.5, 0.45), m["heart"])
        _place(tonal, brass(["A#1", "A#2", "D3", "F3", "A#3"], BAR, attack=0.7, release=0.6, bright=(250, 1800), gain=0.17), at(13))
        _place(tonal, brass(["F2", "F3", "A3", "C4", "F4"], BAR, attack=0.7, release=0.9, bright=(250, 2000), gain=0.17), at(14))
        _place(drums, timpani(hz("F2"), 1.8), at(14), 0.5)
        # bars 15–16: title — tension, build, the hit
        _place(tonal, brass(["G2", "G3", "A#3", "D4"], 2 * BEAT, attack=0.5, release=0.1, bright=(250, 1600), gain=0.15), at(15))
        _place(tonal, brass(["A2", "A3", "C#4", "E4"], 2 * BEAT, attack=0.3, release=0.05, bright=(300, 2400), gain=0.17), at(15, 2))
        for k in range(8):
            _place(drums, pan(tom(150 + 4 * k, 100, 0.2), -0.3 + 0.08 * k), at(15, k * 0.25 + 2), 0.2 + 0.07 * k)
        _place(drums, taiko(72, 36, 1.3), m["hit"], 1.1)
        _place(tonal, brass(["D2", "D3", "F#3", "A3", "D4"], 1.8, attack=0.02, release=1.6, bright=(600, 2600), gain=0.2), m["hit"])

    if logo:
        # the door opens: a single clean bell over a soft sub
        _place(logo_bus, bell(hz("A5"), 4.0, 0.10), 0.3)
        _place(logo_bus, bell(hz("D5"), 4.0, 0.08, ratio=2.0), 1.85)
        _place(logo_bus, sub(40, 28, 3.0, 0.25), 0.3)
        # the fly-through into the I: a reversed bell swells into the hit
        rev = bell(hz("D6"), 1.2, 0.2)[::-1]
        _place(logo_bus, rev, m["hit"] - 1.2)
        _place(logo_bus, sub(50, 28, 3.0, 0.6), m["hit"])
        _place(logo_bus, bell(hz("D5"), 5.0, 0.12, ratio=2.0), m["hit"])
        _place(logo_bus, bell(hz("A5"), 5.0, 0.08, ratio=2.0), m["hit"] + 0.01)
        _place(logo_bus, shimmer(1.8), m["hit"] + 0.15)
        _place(logo_bus, bell(hz("F#5"), 4.0, 0.06, ratio=2.0), m["wordmark"])

    ir = hall()
    mix = reverb(drums, ir, 0.28) * 0.9 + reverb(tonal, ir, 0.45) * 0.8 + reverb(logo_bus, ir, 0.6)
    k = int(0.8 * SR)
    mix[-k:] *= np.linspace(1, 0, k)[:, None] ** 2
    return mix.astype(np.float32)
