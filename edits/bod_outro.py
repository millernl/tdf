"""BATTLE OF THE DISTRICTS → District98 — a 5-second outro, 9:16, on the cream screen.

Clean, flat, on a slow hip-hop pulse (90 BPM, a hit every other beat). On the first hit the
two D's start to unwind from the top of the seam behind a clean edge, round the right D and
across the seam round the left one. The last of the orange goes on the second hit, as
BATTLE / OF THE and DISTRICTS snap apart and leave, and the District98 character is written in
the screen's deep green. It is complete on the third hit and holds alone, centred on the
district map. The camera punches in a touch on each hit. No glow: the film pass keeps only
its grain and gate weave.

  0.00–0.67  the screen; a reversed 808 swells into the first hit
  0.67       hit 1: the D's start to unwind
  1.83–2.00  a ghost kick, then hit 2: the last of the orange goes, the words snap apart
  2.12–3.33  the character is written
  3.33       hit 3: the character is complete; the 808 rings out under the hold

The sound is synthesised here: sine kicks and 808s, warmed so they carry on a phone and
low-passed gently from ~900 Hz, a little room on the last one (`mix`).

Assets (not in git): work/bod/21.webp (the cream screen), work/bod/lockup.webp (the lockup on
transparency, same canvas). The character is the vector glyph from brand/logo_glyph.svg.

    python edits/bod_outro.py                   # renders/bod_outro_9x16.mp4
    python edits/bod_outro.py --stills 1 2 3    # review frames
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from afterfilm import brand, fx, media  # noqa: E402
from afterfilm.timeline import Shot, Timeline  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "work" / "bod"
FPS, DURATION = 25, 5.0


def rgb(*c):
    return np.array(c, np.float32) / 255


CREAM, LINE, INK, ORANGE = rgb(242, 239, 231), rgb(214, 213, 202), rgb(23, 65, 42), rgb(255, 100, 30)

# poster canvas (1493 × 2000): the lockup rows and the D's, measured
ROWS = {"battle": (425, 659), "ofthe": (687, 722), "districts": (1096, 1330)}
D_LEFT = dict(outer=(732.0, 911.0, 171.0, 165.0), inner=(689.0, 913.0, 84.0, 115.0))
D_RIGHT = dict(outer=(760.0, 911.0, 170.0, 165.0), inner=(802.0, 913.0, 84.0, 115.5))
SMALL_CHAR_BOX = (660, 1700, 830, 1840)      # the poster's small character, painted out

BEAT = 60 / 90
H1, H2, H3 = BEAT, 3 * BEAT, 5 * BEAT          # the three hits
T_UNRAVEL = (H1, H2)
T_EXIT = (H2 - 0.06, H2 + 0.28)
T_WRITE = (H2 + 0.12, H3)
PUNCH = ((H1, 0.006), (H2, 0.014), (H3, 0.008))   # camera punch-in on each hit
CHAR_H = 0.38                  # of the frame height
CHAR_CY = 0.47                 # the character's centre, of the frame height


def d_path(d, arc_first=True, n=400):
    """Centreline of one D ring (poster coords): arc_first — from the top junction round the
    curved side to the bottom, then the stem back up; otherwise the stem down, then the arc up."""
    (ox, oy, orx, ory), (ix, iy, irx, iry) = d["outer"], d["inner"]
    side = 1 if ox < ix else -1                 # the right D bulges right (+cos), the left D left

    def arc(th):
        c, s = np.cos(th), np.sin(th)
        return np.stack([(ox + side * orx * c + ix + side * irx * c) / 2, (oy + ory * s + iy + iry * s) / 2], -1)
    th_down = np.linspace(-np.pi / 2, np.pi / 2, n)          # top → curved side → bottom
    top, bot = arc(np.array([-np.pi / 2]))[0], arc(np.array([np.pi / 2]))[0]
    stem_x = (ox + ix) / 2

    def stem(a, b):
        return np.stack([np.full(n // 3, stem_x), np.linspace(a, b, n // 3)], -1)
    if arc_first:
        return np.concatenate([arc(th_down), stem(bot[1], top[1])])
    return np.concatenate([stem(top[1], bot[1]), arc(th_down[::-1])])


class Scene:
    def __init__(self, w, h):
        self.w, self.h = w, h
        poster = np.asarray(Image.open(ASSETS / "21.webp").convert("RGB")).astype(np.float32) / 255
        lock = np.asarray(Image.open(ASSETS / "lockup.webp").convert("RGBA")).astype(np.float32) / 255
        a, col = lock[..., 3], lock[..., :3]
        H, W = a.shape
        # the plate: cream and the district lines; the lockup and the small character painted out
        cover = cv2.dilate((a > 0.01).astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
        x0, y0, x1, y1 = SMALL_CHAR_BOX
        box = np.zeros_like(cover)
        box[y0:y1, x0:x1] = True
        dark = np.abs(poster - INK).sum(-1) < np.abs(poster - LINE).sum(-1)
        cover |= box & cv2.dilate(dark.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
        plate = poster.copy()
        plate[cover] = CREAM
        lum = lambda c: c @ np.array([0.299, 0.587, 0.114], np.float32)   # noqa: E731
        self.lines = fx.clamp01((lum(CREAM) - lum(plate)) / (lum(CREAM) - lum(LINE))).astype(np.float32)
        orange = a * fx.clamp01((col[..., 0] - col[..., 1]) / 0.4)
        white = a * (1 - fx.clamp01((col[..., 0] - col[..., 1]) / 0.4))
        yy = np.arange(H)[:, None]
        self.text = {k: (white * ((yy >= r0 - 4) & (yy <= r1 + 4))).astype(np.float32) for k, (r0, r1) in ROWS.items()}
        self.orange = orange.astype(np.float32)
        # the route that unwinds the D's, and the moment each orange pixel goes
        right = d_path(D_RIGHT, arc_first=True)                # top → right side → bottom → stem up
        left = d_path(D_LEFT, arc_first=False)                 # stem down → left side → up to the top
        hop = np.stack([np.linspace(right[-1][0], left[0][0], 30), np.linspace(right[-1][1], left[0][1], 30)], -1)
        route = np.concatenate([right, hop, left])
        seg = np.r_[0, np.cumsum(np.hypot(*np.diff(route, axis=0).T))]
        self.route, self.route_u = route, seg / seg[-1]
        tm = np.full((H, W), 2.0, np.float32)
        ys, xs = np.nonzero(orange > 0.02)
        pts = np.stack([xs, ys], -1).astype(np.float32)
        nR, nH = len(right), len(hop)
        for sel, lo, hi in ((xs >= 746, 0, nR), (xs < 746, nR + nH, len(route))):
            _, idx = cKDTree(route[lo:hi]).query(pts[sel])
            tm[ys[sel], xs[sel]] = self.route_u[lo + idx]
        self.dd_tm = tm
        # poster → frame (cover the 9:16 frame); the camera's pivot; the character
        self.s0 = h / H
        self.ox = (w - W * self.s0) / 2
        self.pivot = (w / 2, h * CHAR_CY)
        gh = int(round(CHAR_H * h * 1.1))
        self.g_alpha, self.g_tm = brand.glyph_drawon(gh)
        self.g_scale = CHAR_H * h / gh
        Y, X = np.mgrid[0:h, 0:w].astype(np.float32)
        self.key = (0.985 + 0.03 * np.exp(-(((X - w / 2) / (0.7 * w)) ** 2 + ((Y - 0.42 * h) / (0.5 * h)) ** 2)))[..., None]

    # ── geometry ──
    def F(self):
        return np.array([[self.s0, 0, self.ox], [0, self.s0, 0], [0, 0, 1]], np.float64)

    def cam(self, t):
        z = 1.0 + 0.07 * fx.ease_in_out(t / DURATION)
        z += sum(a * np.exp(-(t - th) / 0.16) for th, a in PUNCH if t >= th)
        px, py = self.pivot
        return np.array([[z, 0, px - z * px], [0, z, py - z * py], [0, 0, 1]], np.float64)

    def warp(self, layer, M):
        return cv2.warpAffine(layer, M[:2].astype(np.float32), (self.w, self.h), flags=cv2.INTER_LINEAR)

    def poster_pt(self, p, C):
        return (C @ self.F() @ np.array([p[0], p[1], 1.0]))[:2]

    def glyph_M(self, C):
        gh, gw = self.g_alpha.shape
        s = self.g_scale
        cx, cy = self.pivot
        return C @ np.array([[s, 0, cx - s * gw / 2], [0, s, cy - s * gh / 2], [0, 0, 1]], np.float64)

    # ── the picture ──
    def render(self, shot, lt, tl):
        t = shot.start + lt
        w, h = self.w, self.h
        C = self.cam(t)
        Cb = np.eye(3) + (C - np.eye(3)) * 0.5                    # the map moves less: depth
        img = CREAM * self.key * np.ones((h, w, 1), np.float32)
        lines = self.warp(self.lines, Cb @ self.F())
        img = img * (1 - lines[..., None]) + (LINE * self.key) * lines[..., None]
        # the words hold, then snap apart like curtains
        cover = np.zeros((h, w), np.float32)
        for k, (a0, a1, dist) in {"battle": (T_EXIT[0] + 0.06, T_EXIT[1], -1.0),
                                  "ofthe": (T_EXIT[0], T_EXIT[1] - 0.04, -1.0),
                                  "districts": (T_EXIT[0], T_EXIT[1], 1.0)}.items():
            vel = fx.window(t, a0, a1)
            e = fx.ease_in(vel) ** 1.4
            if vel >= 1:
                continue
            dy = dist * e * 0.72 * h / self.s0
            D = np.array([[1, 0, 0], [0, 1, dy], [0, 0, 1]], np.float64)
            m = self.warp(self.text[k], C @ self.F() @ D)
            k_blur = int(1 + 70 * vel ** 2) if 0 < vel < 1 else 1
            if k_blur > 2:
                m = cv2.blur(m, (1, k_blur))
            cover = np.maximum(cover, m)
        img = img * (1 - cover[..., None]) + cover[..., None] * INK
        # the D's unwind behind a clean edge, fast off the first hit, the last of them on the second
        w_ = fx.window(t, *T_UNRAVEL)
        u = 1 - (1 - w_) ** 1.7 if t >= T_UNRAVEL[0] else -1.0
        vis = self.orange * fx.clamp01((self.dd_tm - u) / 0.004)
        vm = self.warp(vis.astype(np.float32), C @ self.F())
        img = img * (1 - vm[..., None]) + vm[..., None] * ORANGE
        # the character, written in the screen's green
        p = fx.window(t, *T_WRITE)
        if p > 0:
            soft = 0.01                                          # a crisp pen front
            reveal = fx.clamp01((p * (1 + soft) - self.g_tm) / soft) * self.g_alpha
            m = self.warp(reveal.astype(np.float32), self.glyph_M(C))
            img = img * (1 - m[..., None]) + m[..., None] * INK
        return np.clip(img, 0, 1)


# ── the sound ────────────────────────────────────────────────────────────────
def _lp(x, hz, sr, order=4):
    from scipy import signal
    return signal.sosfilt(signal.butter(order, hz / (sr / 2), output="sos"), x)


def _warm(y, drive, sr):
    """Tape-ish saturation, a little lopsided so it adds the octave as well as the fifth above:
    what lets a sub be heard on a phone. The DC it leaves is filtered off."""
    from scipy import signal
    b = 0.18
    z = (np.tanh(drive * (y + b)) - np.tanh(drive * b)) / np.tanh(drive)
    return signal.sosfilt(signal.butter(2, 22 / (sr / 2), "high", output="sos"), z)


def _kick(sr, dur=0.7):
    """A round sine kick: a fast knock from ~190 Hz falling onto 44 Hz, no click."""
    t = np.arange(int(dur * sr)) / sr
    f = 44 + 146 * np.exp(-t / 0.024)
    y = np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-t / 0.2) * np.minimum(t / 0.002, 1)
    return _lp(_warm(y, 2.4, sr), 800, sr, 2)


def _808(sr, f0, tau, dur, slide=None):
    """A sine 808: a small pitch drop on the attack, saturated just enough to carry on a phone
    speaker, low-passed clean. slide=(when, to Hz, how long)."""
    t = np.arange(int(dur * sr)) / sr
    f = f0 * (1 + 0.25 * np.exp(-t / 0.025))
    if slide:
        ts, f1, ls = slide
        f = f * (1 + (f1 / f0 - 1) * fx.smoothstep(ts, ts + ls, t))
    from scipy import signal
    ph = np.sin(2 * np.pi * np.cumsum(f) / sr)
    env = np.exp(-t / tau) * np.minimum(t / 0.004, 1)
    body = _warm(ph * env, 3.2, sr)
    # in parallel, the same note driven evenly before its envelope, kept to its low harmonics:
    # the tail stays audible on small speakers without getting any brighter
    edge = signal.sosfilt(signal.butter(2, (90 / (sr / 2), 450 / (sr / 2)), "band", output="sos"), _warm(ph, 2.0, sr))
    k = np.minimum((dur - t) / 0.03, 1)                 # choked, never clicked off
    return _lp(body + 0.7 * edge * env, 900, sr, 2) * k


def _room(sr, rt60=1.4, seed=5):
    from scipy import signal
    rng = np.random.default_rng(seed)
    t = np.arange(int(rt60 * 1.2 * sr)) / sr
    ir = rng.standard_normal((len(t), 2)) * (10 ** (-3 * t / rt60))[:, None]
    ir = signal.sosfilt(signal.butter(2, 1200 / (sr / 2), output="sos"), ir, axis=0)
    ir = np.concatenate([np.zeros((int(0.015 * sr), 2)), ir])
    return ir / np.sqrt((ir ** 2).sum(0, keepdims=True))


def mix(sr=48000):
    """Three hits on the pulse, all low: G, E sliding to D, E. A reversed 808 swells into the
    first, a ghost kick leads into the second, the third rings out in a little room."""
    from scipy import signal
    E1, D1, G1 = 41.20, 36.71, 49.00
    y = np.zeros(int(DURATION * sr))

    def put(x, at, gain):
        i = int(round(at * sr))
        x = x[:len(y) - i]
        y[i:i + len(x)] += gain * x

    swell = _808(sr, E1, 0.3, 0.62)[::-1] * np.linspace(0, 1, int(0.62 * sr)) ** 2
    put(_lp(swell, 160, sr), H1 - 0.62, 0.45)
    put(_kick(sr), H1, 0.75)
    put(_808(sr, G1, 0.38, H2 - BEAT / 4 - H1), H1, 0.55)
    put(_kick(sr), H2 - BEAT / 4, 0.42)
    put(_kick(sr), H2, 1.0)
    put(_808(sr, E1, 0.7, H3 - H2, slide=(0.84, D1, 0.1)), H2, 0.8)
    put(_kick(sr), H3, 0.9)
    last = np.zeros(len(y))
    i3 = int(round(H3 * sr))
    tail = _808(sr, E1, 0.75, DURATION - H3)[:len(y) - i3]
    last[i3:i3 + len(tail)] = tail
    y += 0.85 * last
    st = np.stack([y, y], 1)
    wet = np.stack([signal.fftconvolve(last, c)[:len(y)] for c in _room(sr).T], 1)
    st += wet * 10 ** (-15 / 20)
    n = int(0.25 * sr)
    st[-n:] *= np.linspace(1, 0, n)[:, None] ** 2
    return (st / np.abs(st).max() * 10 ** (-1 / 20)).astype(np.float32)


def build(w=1080, h=1920):
    look = fx.Look(w, h)
    tl = Timeline(w, h, FPS, DURATION, look)
    scene = Scene(w, h)
    tl.add(Shot(0.0, DURATION, render=scene.render))
    tl.cinema_at = lambda t: {"mono": 0.0, "streaks": 0.0, "halation": 0.0, "bloom": 0.0, "weave": 0.35}
    tl.grain_at = lambda t: 0.22
    tl.vignette_at = lambda t: 0.25
    return tl


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="renders/bod_outro_9x16.mp4")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--stills", nargs="*", type=float)
    a = ap.parse_args()
    W, H = int(1080 * a.scale) // 2 * 2, int(1920 * a.scale) // 2 * 2
    tl = build(W, H)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    if a.stills:
        print(tl.stills(a.stills, str(Path(a.out).with_suffix("")) + "_{t:05.2f}.png"))
    else:
        wav = str(Path(a.out).with_suffix(".wav"))
        media.write_wav(wav, mix())
        tl.render(a.out, wav=wav)
