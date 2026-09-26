"""Swap the working copy for the master: find each needed moment in a file of pulled
segments (e.g. a LosslessCut 'merge cuts' export of the original) and read from there.

    python -m afterfilm.conform work/hq_segments.json footage/proxy.mp4 footage/master_segments.mp4

Each segment of the list is located in the pulled file by matching frames against the
working copy (tiny grey thumbnails, normalised per frame, so grade and scale differences
don't matter). The result, work/hq_map.json, maps working-copy time → master time per
segment: master_t = t + delta.
"""
import json
import sys
from pathlib import Path

import numpy as np

from . import media
from .timeline import FrameBuffer

FPS = 25
TW, TH = 48, 27


def _thumbs(path, t0, dur):
    fr = media.read_frames(path, max(t0, 0), dur, FPS, (TW, TH), deinterlace=False)
    g = fr.astype(np.float32).mean(-1).reshape(len(fr), -1)
    g -= g.mean(1, keepdims=True)
    g /= g.std(1, keepdims=True) + 1e-3
    return g


def align(segments, proxy, pulled):
    info = media.probe(pulled)
    M = _thumbs(pulled, 0, info["duration"] + 1)            # every frame of the pulled file
    out, cursor = [], 0
    for k, (a, b, keys) in enumerate(segments):
        core_a, core_b = a + 1.5, b - 1.5                     # skip the handles: the core must be present
        T = _thumbs(proxy, core_a, core_b - core_a)
        n = len(T)
        best = (1e9, 0)
        lo = max(0, cursor - 5 * FPS)                          # segments come in order
        for i in range(lo, len(M) - n):
            d = float(np.mean((M[i:i + n] - T) ** 2))
            if d < best[0]:
                best = (d, i)
            if best[0] < 0.05 and i > best[1] + 10 * FPS:       # found a clean match; stop early
                break
        err, i = best
        delta = i / FPS - core_a
        out.append({"seg": k + 1, "src_a": a, "src_b": b, "delta": round(delta, 3), "err": round(err, 4),
                    "keys": keys})
        cursor = i + n
        print(f"  {k + 1:02d} {', '.join(keys)[:40]:40s} src {a:8.2f}  → master {a + delta:7.2f}  err {err:.3f}", flush=True)
    return out


class MappedSource:
    """Reads working-copy times from the master segments file."""

    def __init__(self, path, mapping, filters=None):
        self.path = str(path)
        self.map = mapping
        self.info = media.probe(self.path)
        self.filters = filters

    def delta_for(self, t0, t1):
        for m in self.map:
            if m["src_a"] - 0.05 <= t0 and t1 <= m["src_b"] + 0.05:
                return m["delta"]
        raise KeyError(f"no master segment covers {t0:.2f}–{t1:.2f}")

    def read(self, t0, t1, fps, size):
        dfps = min(fps, self.info["fps"])
        d = self.delta_for(t0, t1)
        frames = media.read_frames(self.path, t0 + d, (t1 - t0) + 2 / dfps, dfps, size, pre=self.filters)
        return FrameBuffer(frames, t0, dfps)


if __name__ == "__main__":
    segs, proxy, pulled = sys.argv[1], sys.argv[2], sys.argv[3]
    mapping = align(json.load(open(segs)), proxy, pulled)
    Path("work").mkdir(exist_ok=True)
    json.dump(mapping, open("work/hq_map.json", "w"), indent=1)
    bad = [m for m in mapping if m["err"] > 0.3]
    print(f"{len(mapping)} segments aligned; {len(bad)} with a weak match")
