"""Pixel work: the District98 grade, film finish, and transitions.

Frames are float32 HxWx3 in [0, 1], display-referred.
"""
import numpy as np
import cv2

from . import brand

LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)


# ── easing ────────────────────────────────────────────────────────────────────
def clamp01(x):
    return np.clip(x, 0.0, 1.0)


def smoothstep(e0, e1, x):
    t = clamp01((x - e0) / (e1 - e0))
    return t * t * (3 - 2 * t)


def ease_out(x):
    x = clamp01(x)
    return 1 - (1 - x) ** 3


def ease_in(x):
    return clamp01(x) ** 3


def ease_in_out(x):
    x = clamp01(x)
    return np.where(x < 0.5, 4 * x ** 3, 1 - (-2 * x + 2) ** 3 / 2) if isinstance(x, np.ndarray) else \
        (4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2)


def expo_out(x):
    x = float(clamp01(x))
    return 1.0 if x >= 1 else 1 - 2 ** (-10 * x)


def expo_in_out(x):
    x = float(clamp01(x))
    if x in (0.0, 1.0):
        return x
    return 2 ** (20 * x - 10) / 2 if x < 0.5 else (2 - 2 ** (-20 * x + 10)) / 2


def window(t, t0, t1):
    """Progress 0→1 of t across [t0, t1]."""
    return float(clamp01((t - t0) / max(t1 - t0, 1e-6)))


def luma(img):
    return img @ LUMA


def _chroma(color):
    c = brand.f32(color)
    return c - float(c @ LUMA)


# ── the grade ────────────────────────────────────────────────────────────────
class Look:
    """'98 Green / Gold' — matte blacks with green in the shadows, warm highlights,
    restrained saturation, stage lights that bloom. One place to tune the film."""

    def __init__(self, w, h, accent=brand.GOLD, seed=98):
        self.w, self.h = w, h
        self.shadow_tint = _chroma(brand.GREEN)
        self.high_tint = _chroma(accent)
        self.accent = brand.f32(accent)
        self.black = np.array([0.018, 0.026, 0.022], np.float32)   # off-black leaning green (#1C2120 family)
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) / np.sqrt(2)
        self.vignette = (1 - 0.34 * smoothstep(0.35, 1.0, r) ** 1.3)[..., None].astype(np.float32)
        rng = np.random.default_rng(seed)
        self.grain = []
        for _ in range(8):
            g = rng.standard_normal((h // 2, w // 2)).astype(np.float32)
            g = cv2.GaussianBlur(g, (0, 0), 0.7)
            g = cv2.resize(g, (w, h), interpolation=cv2.INTER_LINEAR)
            self.grain.append(g / (g.std() + 1e-6))

    def grade(self, img, exposure=0.0, sat=0.82, contrast=0.38, split=1.0, mono=0.0, warmth=0.0):
        if exposure:
            img = img * (2.0 ** exposure)
        if warmth:
            img = img * np.array([1 + 0.06 * warmth, 1.0, 1 - 0.06 * warmth], np.float32)
        img = np.clip(img, 0, 1)
        y = luma(img)[..., None]
        s = sat * (1 - mono)
        img = y + (img - y) * s
        # soft S-curve: toe and shoulder, no clipping
        img = img + contrast * (img * img * (3 - 2 * img) - img)
        y = luma(img)[..., None]
        if split:
            # tint the low-mids, not true black — black stays a clean off-black
            sh = (1 - smoothstep(0.05, 0.55, y)) * smoothstep(0.0, 0.18, y)
            hi = smoothstep(0.5, 1.0, y)
            img = img + split * (sh * self.shadow_tint * 0.38 + hi * self.high_tint * 0.2)
        if mono:
            # duotone for freeze frames: shadows into green-black, highlights to warm paper
            dark = self.black + brand.f32(brand.GREEN) * 0.18
            light = np.array([0.95, 0.94, 0.90], np.float32)
            y2 = smoothstep(0.04, 0.92, luma(img))[..., None]
            duo = dark + (light - dark) * y2
            img = img * (1 - mono) + duo * mono
        # matte: lift the floor to a tinted off-black
        img = self.black + img * (1 - self.black)
        return np.clip(img, 0, 1).astype(np.float32)

    def bloom(self, img, strength=0.32, threshold=0.68):
        small = cv2.resize(img, (self.w // 4, self.h // 4), interpolation=cv2.INTER_AREA)
        hot = np.clip(small - threshold, 0, None) / (1 - threshold)
        glow = cv2.GaussianBlur(hot, (0, 0), 6) * 0.6 + cv2.GaussianBlur(hot, (0, 0), 22) * 0.9
        glow = cv2.resize(glow, (self.w, self.h), interpolation=cv2.INTER_LINEAR)
        glow = glow * (0.55 + 0.45 * self.accent)           # warm the halo
        return 1 - (1 - img) * (1 - np.clip(glow * strength, 0, 1))  # screen

    def finish(self, img, frame_no, grain=1.0, vignette=1.0):
        if vignette:
            img = img * (1 - vignette + vignette * self.vignette)
        if grain:
            g = self.grain[frame_no % len(self.grain)]
            y = luma(img)
            amt = 0.02 * grain * (0.12 + 0.88 * (1 - np.abs(y - 0.45) * 1.6).clip(0, 1))
            img = img + (g * amt)[..., None]
        return np.clip(img, 0, 1)

    def write_cube(self, path, n=33):
        """Export the base grade as a .cube LUT for reuse in Premiere / Resolve."""
        r = np.linspace(0, 1, n, dtype=np.float32)
        b, g, rr = np.meshgrid(r, r, r, indexing="ij")
        grid = np.stack([rr, g, b], -1).reshape(1, -1, 3)
        out = self.grade(grid).reshape(-1, 3)
        with open(path, "w") as f:
            f.write('TITLE "District98 Green-Gold"\n')
            f.write(f"LUT_3D_SIZE {n}\n")
            for v in out:
                f.write(f"{v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")


# ── geometry helpers ─────────────────────────────────────────────────────────
def reframe(img, zoom=1.0, cx=0.5, cy=0.5, out_size=None, rot=0.0):
    """Crop/scale around a normalised centre — Ken Burns, punch-ins, pans."""
    h, w = img.shape[:2]
    ow, oh = out_size or (w, h)
    s = zoom * max(ow / w, oh / h)
    # keep the crop inside the frame
    half_w, half_h = ow / (2 * s), oh / (2 * s)
    px = float(np.clip(cx * w, half_w, w - half_w)) if half_w * 2 <= w else w / 2
    py = float(np.clip(cy * h, half_h, h - half_h)) if half_h * 2 <= h else h / 2
    m = cv2.getRotationMatrix2D((px, py), rot, s)
    m[0, 2] += ow / 2 - px
    m[1, 2] += oh / 2 - py
    return cv2.warpAffine(img, m, (ow, oh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def shift(img, dx=0, dy=0):
    m = np.float32([[1, 0, dx], [0, 1, dy]])
    h, w = img.shape[:2]
    return cv2.warpAffine(img, m, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)


def hblur(img, px):
    k = int(px)
    if k < 2:
        return img
    return cv2.blur(img, (k, 1))


def mix(a, b, m):
    if m.ndim == 2:
        m = m[..., None]
    return a + (b - a) * m


# ── transitions: f(A, B, p, ctx) → frame ─────────────────────────────────────
def t_slit(a, b, p, ctx):
    """A vertical slit of stage light opens from the centre (from black or from A)."""
    h, w = b.shape[:2]
    if a is None:
        a = np.zeros_like(b)
    e = ease_in_out(p) ** 1.15
    half = e * (w / 2 + 40)
    x = np.abs(np.arange(w, dtype=np.float32) - w / 2)
    m = clamp01((half - x) / 2.5)[None, :, None]
    rim = np.exp(-((x - half) / (6 + 40 * e)) ** 2)[None, :, None] * (1 - e) ** 0.6
    bz = reframe(b, 1.0 + 0.06 * (1 - e))
    out = a * (1 - m) + bz * m
    return np.clip(out + rim * np.array([1.0, 0.93, 0.8], np.float32) * 0.9, 0, 1)


def t_stripes(a, b, p, ctx, n=9, stagger=0.55):
    """Light blinds: vertical bands open from their centres, left to right, with a
    thin hot edge — the hard light-and-shadow stripes from the moodboard."""
    h, w = b.shape[:2]
    sw = w / n
    x = np.arange(w, dtype=np.float32)
    i = np.floor(x / sw)
    local = clamp01((p * (1 + stagger) - (i / n) * stagger))
    local = local * local * (3 - 2 * local)
    d = np.abs(x - (i + 0.5) * sw)
    half = local * sw / 2 + 0.5
    m = clamp01((half - d) / 1.5)
    edge = np.exp(-((d - half) / 2.2) ** 2) * (local > 0.01) * (local < 0.99)
    bz = shift(b, dx=(1 - ease_out(p)) * 50)
    az = shift(a, dx=-ease_in(p) * 30)
    out = mix(az, bz, np.broadcast_to(m[None, :], (h, w)))
    return np.clip(out + edge[None, :, None] * 0.55, 0, 1)


def t_swoosh(a, b, p, ctx, flip=False):
    """A calligraphic ribbon — the sweep of the glyph's arm — wipes A away."""
    h, w = b.shape[:2]
    e = expo_in_out(p)
    y = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    x = np.arange(w, dtype=np.float32)[None, :]
    base = -0.35 * w + e * 1.7 * w
    curve = base + 0.16 * w * np.sin(np.pi * (y * 1.15 + 0.15)) - 0.22 * w * (y - 0.5)
    if flip:
        x = w - x
    d = x - curve                                   # >0: still A, <0: B revealed
    m = clamp01(-d / 2.0 + 0.5)
    thick = 26 + 70 * np.sin(np.pi * y) ** 2        # brush pressure along the stroke
    ribbon = np.exp(-((d - thick * 0.6) / thick) ** 2) * np.sin(np.pi * p) ** 0.7
    green = brand.f32(brand.GREEN)
    az = shift(a, dx=(1 if flip else -1) * -e * 80)
    bz = reframe(b, 1.05 - 0.05 * e)
    out = mix(az, bz, m)
    col = green * 0.6 + 0.4 * np.clip(ribbon[..., None] * 1.4, 0, 1)
    return np.clip(out * (1 - ribbon[..., None] * 0.85) + col * ribbon[..., None] * 0.95, 0, 1)


def t_whip(a, b, p, ctx, direction=1):
    """Whip pan with motion blur."""
    h, w = b.shape[:2]
    e = ease_in_out(p)
    off = e * w * direction
    blur = np.sin(np.pi * p) ** 1.5 * 140
    out = shift(a, dx=-off) + shift(b, dx=direction * w - off)
    return np.clip(hblur(out, blur), 0, 1)


def t_cut(a, b, p, ctx):
    return b


def t_dissolve(a, b, p, ctx):
    e = smoothstep(0, 1, p)
    return a * (1 - e) + b * e


def t_burn(a, b, p, ctx):
    """Dissolve through warm light — for the slow, emotional section."""
    e = smoothstep(0.15, 0.85, p)
    glow = np.sin(np.pi * p) ** 2 * 0.45
    out = a * (1 - e) + b * e
    return np.clip(1 - (1 - out) * (1 - glow * np.array([1.0, 0.82, 0.55], np.float32)), 0, 1)


def flash(img, k, tint=(1.0, 0.95, 0.86)):
    """Exposure flash on a hit; k in [0, 1]."""
    if k <= 0:
        return img
    return np.clip(img * (1 + 1.6 * k) + k * 0.55 * np.array(tint, np.float32), 0, 1)


TRANSITIONS = {
    "slit": t_slit,
    "stripes": t_stripes,
    "swoosh": t_swoosh,
    "swoosh_r": lambda a, b, p, c: t_swoosh(a, b, p, c, flip=True),
    "whip": t_whip,
    "whip_l": lambda a, b, p, c: t_whip(a, b, p, c, direction=-1),
    "cut": t_cut,
    "dissolve": t_dissolve,
    "burn": t_burn,
}
