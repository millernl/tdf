"""BATTLE OF THE DISTRICTS → District98 — a 5-second outro, 9:16.

The Battle screen comes to life: the district borders draw outward from the centre, the
lockup settles in and a light passes over it. Then the two halves of the DD icon charge with
light at the seam, swing open like doors, a shockwave runs through the map, and in the opening
the District98 character is written by light — hot white at the pen, cooling into the icon's
orange. BATTLE and DISTRICTS make room for it; a last glint, and it holds.

  0.00–0.75  out of black: borders draw outward, BATTLE / OF THE / DISTRICTS settle, the D's close
  0.85–1.45  a light sweeps across the lockup
  1.55–1.95  the seam between the D's fills with light
  1.95–2.50  the D's swing open; the shockwave lights the map
  2.05–3.15  the character is written by light where the icon was
  3.15–5.00  it settles in orange, glows once, a glint crosses it; hold

Assets (not in git): work/bod/poster.webp (the screen), work/bod/lockup.webp (the lockup on
transparency, same canvas). The character is the vector glyph from brand/logo_glyph.svg.

    python edits/bod_outro.py                   # renders/bod_outro_9x16.mp4
    python edits/bod_outro.py --stills 1 2.2 4  # review frames
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from afterfilm import brand, fx, media  # noqa: E402
from afterfilm.timeline import Shot, Timeline  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "work" / "bod"
FPS, DURATION = 25, 5.0

GREEN = np.array([23, 65, 42], np.float32) / 255       # the screen's flat green
LINE = np.array([72, 106, 85], np.float32) / 255       # the district borders
ORANGE = np.array([254, 100, 24], np.float32) / 255    # the icon
HOT = np.array([1.0, 0.93, 0.80], np.float32)          # light at the pen
WHITE = np.array([1.0, 1.0, 1.0], np.float32)

# poster canvas geometry (1493 × 2000)
ICON = dict(x0=561, x1=930, y0=747, y1=1076, seam=746.0)
ROWS = {"battle": (425, 659), "ofthe": (687, 722), "districts": (1096, 1330)}
ICON_C = (746.0, 911.5)

T_SWEEP = (0.85, 1.45)
T_CHARGE = (1.55, 1.95)
T_SPLIT = 1.95
T_DRAW = (2.05, 3.15)
T_GLINT = (3.9, 4.45)
ROOM = 96.0                     # poster px the words move apart to make room for the character
GLYPH_H = 560.0                 # poster px


def ease_out(x):
    return 1 - (1 - fx.clamp01(x)) ** 3


class Scene:
    def __init__(self, w, h):
        self.w, self.h = w, h
        poster = np.asarray(Image.open(ASSETS / "poster.webp").convert("RGB")).astype(np.float32) / 255
        lock = np.asarray(Image.open(ASSETS / "lockup.webp").convert("RGBA")).astype(np.float32) / 255
        a, rgb = lock[..., 3], lock[..., :3]
        H, W = a.shape
        self.PW, self.PH = W, H
        # the background plate: the screen with the lockup painted out in its flat green
        cover = cv2.dilate((a > 0.01).astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
        bg = poster.copy()
        bg[cover] = GREEN
        self.bg = bg
        lum = lambda c: c @ np.array([0.299, 0.587, 0.114], np.float32)   # noqa: E731
        self.lines = fx.clamp01((lum(bg) - lum(GREEN)) / (lum(LINE) - lum(GREEN)))
        orange = a * fx.clamp01((rgb[..., 0] - rgb[..., 1]) / 0.4)
        white = a * (1 - fx.clamp01((rgb[..., 0] - rgb[..., 1]) / 0.4))
        yy = np.arange(H)[:, None]
        xx = np.arange(W)[None, :]
        self.text = {k: white * ((yy >= y0 - 4) & (yy <= y1 + 4)) for k, (y0, y1) in ROWS.items()}
        self.dl = orange * (xx < ICON["seam"])
        self.dr = orange * (xx >= ICON["seam"])
        # poster → frame: cover the 9:16 frame (the lockup stays centred)
        self.s0 = h / H
        self.ox = (w - W * self.s0) / 2
        self.icon_f = self.to_frame(*ICON_C)
        # the character: vector, rasterised once at its largest size, warped per frame
        gh = int(round(GLYPH_H * self.s0 * 1.08))
        self.g_alpha, self.g_tm = brand.glyph_drawon(gh)
        self.g_scale = GLYPH_H * self.s0 / gh
        # soft key light from above centre, and a radial distance map for the map effects
        Y, X = np.mgrid[0:h, 0:w].astype(np.float32)
        self.key = (0.82 + 0.34 * np.exp(-(((X - w / 2) / (0.65 * w)) ** 2 + ((Y - 0.40 * h) / (0.42 * h)) ** 2)))[..., None]
        self.dist = np.hypot(X - self.icon_f[0], Y - self.icon_f[1])
        self.X, self.Y = X, Y

    def to_frame(self, x, y):
        return self.ox + x * self.s0, y * self.s0

    def camera(self, t):
        return 1.0 + 0.045 * fx.ease_in_out(t / DURATION)

    def M(self, zoom, about=None, dx=0.0, dy=0.0, sx=1.0, hinge=None):
        """Affine poster → frame: optional per-layer scale about a poster point, x-squash about
        a hinge, offset, then the frame mapping and the camera push about the icon."""
        A = np.eye(3, dtype=np.float64)
        if about is not None and zoom != 1.0:
            ax, ay = about
            A = np.array([[zoom, 0, ax - zoom * ax], [0, zoom, ay - zoom * ay], [0, 0, 1]]) @ A
        if hinge is not None and sx != 1.0:
            A = np.array([[sx, 0, hinge - sx * hinge], [0, 1, 0], [0, 0, 1]]) @ A
        A = np.array([[1, 0, dx], [0, 1, dy], [0, 0, 1]]) @ A
        F = np.array([[self.s0, 0, self.ox], [0, self.s0, 0], [0, 0, 1]])
        return F @ A

    def warp(self, layer, M, cam, blur=0.0):
        cx, cy = self.icon_f
        C = np.array([[cam, 0, cx - cam * cx], [0, cam, cy - cam * cy], [0, 0, 1]])
        out = cv2.warpAffine(layer, (C @ M)[:2].astype(np.float32), (self.w, self.h), flags=cv2.INTER_LINEAR)
        if blur > 0.3:
            out = cv2.GaussianBlur(out, (0, 0), blur)
        return out

    def render(self, shot, lt, tl):
        t = shot.start + lt
        w, h = self.w, self.h
        cam = self.camera(t)
        # ── the map ──
        bgc = 1 + (cam - 1) * 0.5                                   # parallax: the ground moves less
        fade = fx.ease_in_out(fx.window(t, 0.0, 0.5))
        plate = self.warp(self.bg, self.M(1.0), bgc)
        lines = self.warp(self.lines, self.M(1.0), bgc)
        flat = GREEN * self.key
        front = fx.window(t, 0.05, 0.95) * 1.25 * max(w, h)          # the borders draw outward
        drawn = fx.clamp01((front - self.dist) / 90.0)
        frontglow = np.exp(-((self.dist - front) / 55.0) ** 2) * (0 < fx.window(t, 0.05, 0.95) < 1)
        ring_r = (t - T_SPLIT) * 1500.0                              # the shockwave
        ring = np.exp(-((self.dist - ring_r) / 70.0) ** 2) * (t > T_SPLIT) * max(0.0, 1 - (t - T_SPLIT) / 1.3)
        after = 0.35 * np.exp(-max(t - T_SPLIT, 0) / 0.9) * (t > T_SPLIT)
        r2 = (t - T_DRAW[1]) * 1100.0                                # a softer echo as the character lands
        ring2 = np.exp(-((self.dist - r2) / 90.0) ** 2) * (t > T_DRAW[1]) * max(0.0, 1 - (t - T_DRAW[1]) / 1.4)
        lit = lines * (drawn * (1 + after) + 1.6 * frontglow + 2.4 * ring + 1.1 * ring2)
        base = flat * (1 - lines[..., None]) + (plate * self.key) * lines[..., None]
        img = flat + (base - flat) * drawn[..., None]
        img = img + (lit * 0.35)[..., None] * np.array([0.55, 0.95, 0.7], np.float32)
        img = img * fade
        # ── the words ──
        cover = np.zeros((h, w), np.float32)
        room = ROOM * fx.ease_in_out(fx.window(t, T_SPLIT, T_SPLIT + 0.55))
        for k, (a0, a1, z0, dyk) in {"battle": (0.12, 0.50, 1.12, -room), "ofthe": (0.22, 0.55, 1.18, -room),
                                     "districts": (0.32, 0.68, 1.10, room)}.items():
            e = ease_out(fx.window(t, a0, a1))
            if e <= 0:
                continue
            y0, y1 = ROWS[k]
            about = (746.0, (y0 + y1) / 2)
            zoom = z0 + (1 - z0) * e
            m = self.warp(self.text[k], self.M(zoom, about, dy=dyk), cam, blur=7 * (1 - e)) * e
            cover = np.maximum(cover, m)
        img = img * (1 - cover[..., None]) + cover[..., None] * WHITE
        # ── the D's: they close, charge at the seam, and swing open like doors ──
        close = ease_out(fx.window(t, 0.28, 0.62))
        opn = fx.ease_in_out(fx.window(t, T_SPLIT, T_SPLIT + 0.55))
        gone = fx.ease_in(fx.window(t, T_SPLIT + 0.15, T_SPLIT + 0.55))
        charge = fx.ease_in(fx.window(t, *T_CHARGE))
        pulse = 1 + 0.03 * charge * (1 - opn)
        dmask = np.zeros((h, w), np.float32)
        dcol = np.zeros((h, w, 3), np.float32)
        for side, layer, hinge in ((-1, self.dl, ICON["x0"]), (1, self.dr, ICON["x1"])):
            dx = side * (70 * (1 - close) + 150 * opn)
            sx = 1 - 0.72 * opn
            m = self.warp(layer, self.M(pulse, ICON_C, dx=dx, sx=sx, hinge=hinge), cam, blur=5 * opn) \
                * min(1.0, 2.5 * close) * (1 - gone)
            shade = 1 - 0.35 * opn
            dcol = dcol * (1 - m[..., None]) + m[..., None] * ORANGE * shade
            dmask = np.maximum(dmask, m)
        img = img * (1 - dmask[..., None]) + dcol
        # light in the seam, bursting as the doors open
        sx_, sy_ = self.icon_f
        ih = (ICON["y1"] - ICON["y0"]) * self.s0 * cam
        seam_w = 3 + 60 * opn
        seam = np.exp(-((self.X - sx_) / seam_w) ** 2) * np.exp(-((self.Y - sy_) / (0.6 * ih)) ** 4)
        s_amt = charge * (1 - opn) + 1.2 * np.exp(-max(t - T_SPLIT, 0) / 0.14) * (t > T_SPLIT)
        img = img + (seam * s_amt * 0.9)[..., None] * HOT
        burst = np.exp(-max(t - T_SPLIT, 0) / 0.35) * (t > T_SPLIT)
        if burst > 0.01:
            glow = np.exp(-(self.dist / (0.35 * w)) ** 2) * burst * 0.45
            img = img + glow[..., None] * np.array([1.0, 0.75, 0.5], np.float32)
        # ── the character, written by light ──
        p = fx.window(t, *T_DRAW)
        if p > 0:
            soft = 0.06
            reveal = fx.clamp01((p * (1 + soft) - self.g_tm) / soft) * self.g_alpha
            heat = np.exp(-np.maximum(p - self.g_tm, 0) / 0.08) * (p < 1)
            settle = fx.window(t, T_DRAW[1], T_DRAW[1] + 0.35)
            head = np.exp(-((self.g_tm - p) / 0.03) ** 2) * self.g_alpha * (self.g_tm <= p + 0.02) * (p < 1)
            gh, gw = self.g_alpha.shape
            s = self.g_scale
            cx, cy = sx_, sy_
            # keep the character centred where the icon was, riding the camera push
            Mg = np.float32([[s * cam, 0, cx - s * cam * gw / 2], [0, s * cam, cy - s * cam * gh / 2]])

            def place(a):
                return cv2.warpAffine(a.astype(np.float32), Mg, (w, h), flags=cv2.INTER_LINEAR)
            m = place(reveal)
            ht = place(heat * self.g_alpha) * (1 - settle)
            col = ORANGE[None, None, :] * (1 - ht[..., None]) + HOT[None, None, :] * ht[..., None]
            img = img * (1 - m[..., None]) + m[..., None] * col
            hd = place(head)
            if hd.any():
                halo = cv2.GaussianBlur(hd, (0, 0), 9) * 2.2
                img = img + np.clip(halo, 0, 1.5)[..., None] * HOT * 0.8
            # it arrives: one glow, then a glint crosses it
            gpulse = np.exp(-max(t - T_DRAW[1], 0) / 0.4) * (t > T_DRAW[1])
            glow = 0.7 * gpulse + 0.16 * settle * (1 + 0.25 * np.sin(2 * np.pi * (t - T_DRAW[1]) / 1.8))
            if glow > 0.01:
                img = img + (cv2.GaussianBlur(m, (0, 0), 16) * glow)[..., None] * ORANGE
            g = fx.window(t, *T_GLINT)
            if 0 < g < 1:
                band = np.exp(-(((self.X - self.Y * 0.35) - (cx - cy * 0.35) - (-160 + 320 * fx.ease_in_out(g)) * cam) / 26) ** 2)
                img = img + (band * m * 0.55)[..., None] * WHITE
        # a light passes over the lockup
        g = fx.window(t, *T_SWEEP)
        if 0 < g < 1:
            band = np.exp(-(((self.X - self.Y * 0.35) - (-250 + (w + 500) * fx.ease_in_out(g))) / 60) ** 2)
            img = img + (band * np.maximum(cover, dmask) * 0.4)[..., None] * WHITE
        return np.clip(img, 0, 1)


def build(w=1080, h=1920):
    look = fx.Look(w, h)
    look.black = np.array([0.0, 0.0, 0.0], np.float32)
    tl = Timeline(w, h, FPS, DURATION, look)
    scene = Scene(w, h)
    tl.add(Shot(0.0, DURATION, render=scene.render))
    # no anamorphic streaks: type this bright would draw bars across the frame
    tl.cinema_at = lambda t: {"mono": 0.0, "streaks": 0.0, "halation": 0.4, "bloom": 0.85, "weave": 0.6}
    tl.grain_at = lambda t: 0.35
    tl.vignette_at = lambda t: 0.9
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
