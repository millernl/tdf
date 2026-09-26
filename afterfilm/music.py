"""Cut a music track to length on its bar grid.

A conform is a list of (first_bar, last_bar) spans of the source, played back to back.
Splices sit on downbeats: the outgoing bar fades over a few milliseconds while the
incoming bar starts a hair early, so its drum transient stays whole.
"""
import numpy as np

from . import media

SR = 48000


class Track:
    def __init__(self, path, bpm, first_downbeat):
        self.path = str(path)
        self.beat = 60.0 / bpm
        self.bar = 4 * self.beat
        self.t0 = first_downbeat
        self.audio = media.read_audio(self.path, sr=SR, channels=2)

    def bar_time(self, n):
        """Source seconds of bar n (1-based)."""
        return self.t0 + (n - 1) * self.bar

    def conform(self, spans, fade_in_bars=0.0, pre=0.015, tail=None):
        """→ (stereo float32 @48k, list of (record_s, source_bar) for every bar).

        Each incoming span starts `pre` seconds early; over that window the outgoing
        span's natural continuation fades out and the new one fades in, finishing
        exactly on the downbeat, so the new bar's transient is untouched and every
        downbeat lands on the record grid.
        """
        out, bars_map, rec, e_prev = [], [], 0.0, None
        n = int(pre * SR)
        up = np.sin(np.linspace(0, np.pi / 2, n))[:, None]
        down = np.cos(np.linspace(0, np.pi / 2, n))[:, None]
        for k, (a, b) in enumerate(spans):
            s = self.bar_time(a) - (pre if k else 0.0)
            e = self.bar_time(b + 1) - pre
            seg = self.audio[int(round(s * SR)):int(round(e * SR))].copy()
            if k:
                i = int(round(e_prev * SR))
                seg[:n] = seg[:n] * up + self.audio[i:i + n] * down
            for m in range(a, b + 1):
                bars_map.append((rec + (m - a) * self.bar, m))
            out.append(seg)
            rec += (b + 1 - a) * self.bar
            e_prev = e
        y = np.concatenate(out)
        if fade_in_bars:
            k = int(fade_in_bars * self.bar * SR)
            y[:k] *= (np.linspace(0, 1, k) ** 2)[:, None]
        if tail is not None:
            y = np.concatenate([y, np.zeros((max(0, int(tail * SR) - len(y)), 2), np.float32)])[: int(tail * SR)]
        return y.astype(np.float32), bars_map
