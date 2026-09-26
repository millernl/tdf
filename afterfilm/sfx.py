"""Synthesised sound design — whooshes, hits, risers, ticks. No sample library needed.

All functions return stereo float32 at SR; `place()` mixes a cue into a track.
"""
import numpy as np
from scipy import signal

SR = 48000
_rng = np.random.default_rng(98)


def _env(n, attack, release, curve=2.0):
    t = np.linspace(0, 1, n, dtype=np.float32)
    a = np.clip(t / max(attack, 1e-4), 0, 1) ** curve
    r = np.clip((1 - t) / max(release, 1e-4), 0, 1) ** curve
    return a * r


def _band_sweep(noise, f0, f1, width=0.6):
    """Noise through a band-pass whose centre glides f0→f1 (log), via STFT masking."""
    f, t, Z = signal.stft(noise, SR, nperseg=1024)
    centre = np.geomspace(f0, f1, Z.shape[1])
    logf = np.log2(np.maximum(f, 20))[:, None]
    mask = np.exp(-((logf - np.log2(centre)[None, :]) / width) ** 2)
    _, y = signal.istft(Z * mask, SR, nperseg=1024)
    return y[: len(noise)].astype(np.float32)


def whoosh(dur=0.6, f0=250, f1=3500, pan=(-0.7, 0.7), gain=0.5):
    n = int(dur * SR)
    y = _band_sweep(_rng.standard_normal(n).astype(np.float32), f0, f1)
    y *= _env(n, 0.65, 0.35, 1.6)
    y /= np.abs(y).max() + 1e-9
    p = np.linspace(pan[0], pan[1], n)
    return np.stack([y * np.sqrt((1 - p) / 2), y * np.sqrt((1 + p) / 2)], 1) * gain


def sub_hit(dur=1.8, f0=62, f1=34, gain=0.9):
    n = int(dur * SR)
    t = np.arange(n) / SR
    freq = f1 + (f0 - f1) * np.exp(-t * 6)
    y = np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-t * 2.2)
    click = _rng.standard_normal(n) * np.exp(-t * 90) * 0.25
    y = (y + signal.lfilter(*signal.butter(2, 3000 / (SR / 2)), click)).astype(np.float32)
    y = np.tanh(y * 1.4) / np.tanh(1.4)
    return np.stack([y, y], 1) * gain


def riser(dur=1.2, gain=0.35):
    n = int(dur * SR)
    t = np.linspace(0, 1, n)
    y = _band_sweep(_rng.standard_normal(n).astype(np.float32), 400, 9000, 0.9) * t ** 2.5
    tone = np.sin(2 * np.pi * np.cumsum(200 + 900 * t ** 2) / SR) * t ** 3 * 0.25
    y = (y / (np.abs(y).max() + 1e-9) + tone).astype(np.float32)
    return np.stack([y, y], 1) * gain


def shutter(gain=0.4):
    out = np.zeros((int(0.12 * SR), 2), np.float32)
    for k, at in enumerate((0.0, 0.055)):
        n = int(0.03 * SR)
        b = signal.lfilter(*signal.butter(2, [1500 / (SR / 2), 7000 / (SR / 2)], "band"),
                           _rng.standard_normal(n)) * np.exp(-np.arange(n) / (SR * 0.004))
        i = int(at * SR)
        out[i:i + n] += (b * (1.0 if k == 0 else 0.6))[:, None]
    return out / (np.abs(out).max() + 1e-9) * gain


def tick(gain=0.08):
    n = int(0.012 * SR)
    b = signal.lfilter(*signal.butter(2, 4000 / (SR / 2), "high"), _rng.standard_normal(n))
    b *= np.exp(-np.arange(n) / (SR * 0.0015))
    return np.stack([b, b], 1).astype(np.float32) * gain


def shimmer(dur=1.4, gain=0.18):
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = sum(np.sin(2 * np.pi * f * t + ph) for f, ph in ((1320, 0), (1980, 1), (2640, 2), (3300, 3)))
    y = y * _env(n, 0.35, 0.6, 1.5) * (0.6 + 0.4 * np.sin(2 * np.pi * 5 * t))
    return np.stack([y, np.roll(y, 240)], 1).astype(np.float32) * gain / 4


def pulse_bed(duration, bpm=120, sections=((0, 30, 0.5),), gain=0.35):
    """Temp rhythm for the animatic: kick + hat. sections: (t0, t1, density 0..1)."""
    out = np.zeros((int(duration * SR), 2), np.float32)
    beat = 60 / bpm
    n = int(0.18 * SR)
    tt = np.arange(n) / SR
    kick = (np.sin(2 * np.pi * np.cumsum(45 + 90 * np.exp(-tt * 35)) / SR) * np.exp(-tt * 14)).astype(np.float32)
    hat = signal.lfilter(*signal.butter(2, 7000 / (SR / 2), "high"), _rng.standard_normal(int(0.04 * SR)))
    hat = (hat * np.exp(-np.arange(len(hat)) / (SR * 0.008))).astype(np.float32)
    for t0, t1, dens in sections:
        b = t0
        k = 0
        while b < t1:
            if dens >= 0.9 or (k % 2 == 0):
                place(out, np.stack([kick, kick], 1) * gain, b)
            if dens > 0.3:
                place(out, np.stack([hat, hat], 1) * gain * 0.35 * dens, b + beat / 2)
            b += beat
            k += 1
    return out


def place(track, cue, at):
    i = int(round(at * SR))
    if i >= len(track):
        return track
    j = min(len(track), i + len(cue))
    s = max(0, -i)
    track[max(i, 0):j] += cue[s:j - i]
    return track


def master(track, ceiling=0.89):
    """Gentle glue: soft-clip and peak-normalise."""
    y = np.tanh(track * 1.2) / np.tanh(1.2)
    return (y / (np.abs(y).max() + 1e-9) * ceiling).astype(np.float32)
