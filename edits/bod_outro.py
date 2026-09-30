"""BATTLE OF THE DISTRICTS → District98 — a 5-second outro, 9:16, on the cream screen.

One pen does it all. An ember ignites at the top of the seam between the two D's, runs
around the right D and across the seam around the left one, and the orange burns away behind
it. Without lifting, the pen flows on and writes the District98 character in the screen's
deep green — while BATTLE / OF THE and DISTRICTS part like curtains and leave. The character
ends alone, centred, on the district map.

  0.00–0.80  the screen, a light passing over the type
  0.72–0.85  the ember ignites at the top of the seam
  0.85–2.05  it unravels the right D, crosses the seam, unravels the left D
  1.90–2.45  the words part and leave the frame
  2.05–2.25  the pen travels to the character's raised hand
  2.25–3.65  the character is written
  3.65–5.00  the ember goes out, a sheen crosses the character; hold

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
EMBER, SPARK = rgb(255, 150, 60), rgb(255, 238, 205)

# poster canvas (1493 × 2000): the lockup rows and the D's, measured
ROWS = {"battle": (425, 659), "ofthe": (687, 722), "districts": (1096, 1330)}
D_LEFT = dict(outer=(732.0, 911.0, 171.0, 165.0), inner=(689.0, 913.0, 84.0, 115.0))
D_RIGHT = dict(outer=(760.0, 911.0, 170.0, 165.0), inner=(802.0, 913.0, 84.0, 115.5))
SMALL_CHAR_BOX = (660, 1700, 830, 1840)      # the poster's small character, painted out

T_SHEEN = (0.15, 0.8)
T_IGNITE = (0.72, 0.85)
T_UNRAVEL = (0.85, 2.05)
T_EXIT = (1.9, 2.45)
T_TRANSIT = (2.05, 2.25)
T_WRITE = (2.25, 3.65)
T_GLINT = (4.0, 4.5)
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
        # the pen's route over the D's, and the moment each orange pixel burns
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
        ga = self.g_alpha > 0.5
        i = np.argmin(np.where(ga, self.g_tm, 9))
        self.g_start = np.array(np.unravel_index(i, ga.shape)[::-1], np.float32)     # (x, y) in glyph px
        Y, X = np.mgrid[0:h, 0:w].astype(np.float32)
        self.X, self.Y = X, Y
        self.key = (0.985 + 0.03 * np.exp(-(((X - w / 2) / (0.7 * w)) ** 2 + ((Y - 0.42 * h) / (0.5 * h)) ** 2)))[..., None]

    # ── geometry ──
    def F(self):
        return np.array([[self.s0, 0, self.ox], [0, self.s0, 0], [0, 0, 1]], np.float64)

    def cam(self, t):
        z = 1.0 + 0.07 * fx.ease_in_out(t / DURATION)
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

    def pen_at(self, t, C):
        """Where the pen is, and how bright."""
        if t < T_UNRAVEL[1]:
            u = fx.ease_in_out(fx.window(t, *T_UNRAVEL))
            i = min(int(np.searchsorted(self.route_u, u)), len(self.route) - 1)
            return self.poster_pt(self.route[i], C), fx.ease_out(fx.window(t, *T_IGNITE))
        a = self.poster_pt(self.route[-1], C)
        b = (self.glyph_M(C) @ np.array([*self.g_start, 1.0]))[:2]
        if t < T_TRANSIT[1]:
            e = fx.ease_in_out(fx.window(t, *T_TRANSIT))
            ctrl = (a + b) / 2 + np.array([-0.08 * self.w, 0.05 * self.h])  # swing out low, under the parting words
            return (1 - e) ** 2 * a + 2 * (1 - e) * e * ctrl + e ** 2 * b, 1.0
        p = min(fx.window(t, *T_WRITE), 0.999)
        wgt = np.exp(-((self.g_tm - p) / 0.012) ** 2) * self.g_alpha
        ys, xs = np.nonzero(wgt > 1e-3)
        if len(xs):
            ww = wgt[ys, xs]
            q = np.array([(xs * ww).sum() / ww.sum(), (ys * ww).sum() / ww.sum()], np.float32)
        else:
            q = self.g_start
        out = fx.window(t, T_WRITE[1] - 0.05, T_WRITE[1] + 0.35)
        return (self.glyph_M(C) @ np.array([*q, 1.0]))[:2], 1.0 - fx.ease_in(out)

    # ── the picture ──
    def render(self, shot, lt, tl):
        t = shot.start + lt
        w, h = self.w, self.h
        C = self.cam(t)
        Cb = np.eye(3) + (C - np.eye(3)) * 0.5                    # the map moves less: depth
        img = CREAM * self.key * np.ones((h, w, 1), np.float32)
        lines = self.warp(self.lines, Cb @ self.F())
        img = img * (1 - lines[..., None]) + (LINE * self.key) * lines[..., None]
        # the words hold, a light passes over them, then they part like curtains
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
        g = fx.window(t, *T_SHEEN)
        if 0 < g < 1:
            band = np.exp(-(((self.X - self.Y * 0.4) - (-400 + (w + 900) * fx.ease_in_out(g))) / 70) ** 2)
            img = img + (band * cover * 0.28)[..., None] * (1 - INK)
        # the D's burn away behind the pen
        u = fx.ease_in_out(fx.window(t, *T_UNRAVEL)) if t >= T_UNRAVEL[0] else -1.0
        M = C @ self.F()
        vis = self.orange * fx.clamp01((self.dd_tm - u) / 0.01)
        vm = self.warp(vis.astype(np.float32), M)
        img = img * (1 - vm[..., None]) + vm[..., None] * ORANGE
        if u > 0:
            out = np.exp(-max(t - T_UNRAVEL[1], 0) / 0.1)         # the last embers die with the pen's turn
            ember = self.orange * np.exp(-np.maximum(u - self.dd_tm, 0) / 0.035) * (self.dd_tm <= u) * out
            em = self.warp(ember.astype(np.float32), M)
            if em.max() > 0.01:
                glow = np.clip(cv2.GaussianBlur(em, (0, 0), 7) * 1.4, 0, 1) * 0.7
                img = img * (1 - glow[..., None]) + glow[..., None] * EMBER
                img = img * (1 - em[..., None]) + em[..., None] * EMBER
        # the character, written in ink behind the pen
        p = fx.window(t, *T_WRITE)
        if p > 0:
            soft = 0.045
            reveal = fx.clamp01((p * (1 + soft) - self.g_tm) / soft) * self.g_alpha
            wet = np.exp(-np.maximum(p - self.g_tm, 0) / 0.05) * self.g_alpha * (p < 1)
            Mg = self.glyph_M(C)
            m = self.warp(reveal.astype(np.float32), Mg)
            wt = self.warp(wet.astype(np.float32), Mg)
            ink = INK[None, None, :] * (1 - 0.18 * wt[..., None]) + EMBER[None, None, :] * (0.18 * wt[..., None])
            img = img * (1 - m[..., None]) + m[..., None] * ink
            gg = fx.window(t, *T_GLINT)
            if 0 < gg < 1:
                cx, cy = self.pivot
                band = np.exp(-(((self.X - self.Y * 0.4) - (cx - cy * 0.4) - (-260 + 520 * fx.ease_in_out(gg))) / 34) ** 2)
                img = img + (band * m * 0.22)[..., None] * (1 - INK)
        # the pen: an ember with a white-hot core
        if T_IGNITE[0] <= t < T_WRITE[1] + 0.4:
            (px, py), b = self.pen_at(t, C)
            if b > 0.01:
                r2 = (self.X - px) ** 2 + (self.Y - py) ** 2
                halo = np.exp(-r2 / (2 * 16.0 ** 2)) * 0.75 * b
                core = np.exp(-r2 / (2 * 4.0 ** 2)) * b
                img = img * (1 - halo[..., None]) + halo[..., None] * EMBER
                img = img * (1 - core[..., None]) + core[..., None] * SPARK
        return np.clip(img, 0, 1)


def build(w=1080, h=1920):
    look = fx.Look(w, h)
    tl = Timeline(w, h, FPS, DURATION, look)
    scene = Scene(w, h)
    tl.add(Shot(0.0, DURATION, render=scene.render))
    tl.cinema_at = lambda t: {"mono": 0.0, "streaks": 0.0, "halation": 0.3, "bloom": 0.35, "weave": 0.5}
    tl.grain_at = lambda t: 0.28
    tl.vignette_at = lambda t: 0.3
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
        media.write_wav(wav, np.zeros((int(DURATION * 48000), 2), np.float32))   # a silent track, for editors
        tl.render(a.out, wav=wav)
