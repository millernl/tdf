"""ENCORE98 — the logo intro for the dance video.

A 1-second overlay (1920×1080, 30 fps) that replaces the placeholder tag at the very start of the
edit, on its timing: the placeholder is there from the first frame, oversized and half transparent,
zooms out slowly and then fast, lands at 0.40 s, holds with a hand-drawn jitter, fades from 0.87 s
and is gone at 1.0 s, as the boots step in. The music comes in at 0.12 s.

The export is an H.264 MP4 of the white logo on black, which plays and downloads anywhere; with the
Screen blend mode it composites exactly like an alpha overlay (white over black is its own matte).
--format prores writes ProRes 4444 with alpha instead.

The logo (a raster PNG, white on transparent, the client's file; not in git) writes itself like a
signature. Each stroke follows a centreline routed along the logo's own skeleton between hand-placed
waypoints, and every pixel of the mark appears when the pen passes the nearest point of its stroke.
Meanwhile the whole logo zooms out from oversized on the placeholder's curve (with a zoom blur where
it moves fast), ENCORE98 comes in letter by letter, and on the way out it pushes in and fades.

    0.00–0.37  the stem (already under way on frame 0), the loop and swash, the inner stroke, the lasso
    0.00–0.40  zooms out from 2.8× and lands; from half to full opacity
    0.38–0.60  E N C O R E 9 8, each letter rising into place
    0.40–0.86  holds, with a slight stepped jitter (hand-drawn, like the placeholder)
    0.87–0.97  pushes in and fades; nothing left at 1.0 s

    python edits/encore_logo.py --logo LOGO.png --out renders/ENCORE98_logo_intro_1920x1080.mp4
    python edits/encore_logo.py --logo LOGO.png --format prores --out ....mov       # with alpha
    python edits/encore_logo.py --logo LOGO.png --debug work/encore/paths.png      # routed strokes
    python edits/encore_logo.py --logo LOGO.png --preview REFERENCE.mov --out renders/..._preview.mp4
"""
import argparse
import subprocess
import tempfile
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from scipy import ndimage

W, H, FPS, N = 1920, 1080, 30, 30
CENTER = (0.5 * W, 0.46 * H)
REST_H = 0.50 * H                  # the logo's height (mark and name) at rest: the mark is about as tall as the
                                   # placeholder tag (~0.42 H); scaling down in the edit stays sharp
TEXT_Y0 = 1335                     # rows of the PNG below this are the name
CROP = (560, 800, 1380, 1440)      # the logo's region of the 2000-px PNG (x0, y0, x1, y1)

# the strokes, in writing order: waypoints along each (x, y in the PNG), and when the pen draws it
STROKES = [
    ("stem", [(973, 842), (913, 987), (827, 1107), (760, 1200), (716, 1290)], -0.10, 0.06),
    ("loop", [(1060, 1000), (1100, 920), (1160, 850), (1182, 900), (1120, 990), (1010, 1060), (965, 1150),
              (975, 1250), (1080, 1290), (1230, 1250), (1310, 1150), (1337, 1050)], 0.00, 0.28),
    ("inner", [(873, 1107), (940, 1060), (1000, 1015), (1050, 1012), (1090, 1035), (1070, 1075), (1110, 1107)],
     0.14, 0.25),
    ("lasso", [(1133, 1033), (1007, 1007), (873, 997), (740, 1013), (640, 1047), (597, 1073), (640, 1080),
               (807, 1100), (940, 1120), (1040, 1123), (1110, 1107)], 0.18, 0.37),
]
SOFT = 0.015                       # the pen's soft leading edge, seconds
LAND = 0.40                        # where the zoom lands (the placeholder's frame 12)


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def smoother(x):
    x = np.clip(x, 0, 1)
    return x * x * x * (x * (6 * x - 15) + 10)


def expo_out(x):
    x = np.clip(x, 0, 1)
    return 1 - 2 ** (-10 * x) if x < 1 else 1.0


def window(t, a, b):
    return float(np.clip((t - a) / (b - a), 0, 1))


def load_logo(path):
    im = np.asarray(Image.open(path).convert("RGBA")).astype(np.float32) / 255
    x0, y0, x1, y1 = CROP
    return im[y0:y1, x0:x1, 3].copy()


def route(alpha):
    """Each stroke's centreline: shortest paths along the skeleton between its waypoints."""
    from skimage.graph import route_through_array
    from skimage.morphology import skeletonize
    x0, y0 = CROP[:2]
    mask = alpha > 0.35
    mask[TEXT_Y0 - y0:] = False
    skel = skeletonize(mask)
    near = ndimage.binary_dilation(skel, iterations=2)
    cost = np.where(near, 1.0, np.where(mask, 6.0, 400.0))
    sk_y, sk_x = np.nonzero(skel)
    paths = []
    for name, pts, t0, t1 in STROKES:
        snapped = []
        for x, y in pts:
            d = (sk_x - (x - x0)) ** 2 + (sk_y - (y - y0)) ** 2
            i = int(np.argmin(d))
            snapped.append((int(sk_y[i]), int(sk_x[i])))
        full = []
        for a, b in zip(snapped[:-1], snapped[1:]):
            seg, _ = route_through_array(cost, a, b, fully_connected=True, geometric=True)
            full += seg if not full else seg[1:]
        paths.append((name, np.array(full), t0, t1))
    return paths, mask


def reveal_times(alpha, paths):
    """When each pixel of the mark is drawn: the time the pen passes the nearest point of its stroke.
    Where strokes cross, a pixel belongs to the earliest stroke that runs through it."""
    h, w = alpha.shape
    u = np.linspace(0, 1, 2001)
    inv = lambda s: np.interp(s, smooth(u), u)                      # noqa: E731 (arc fraction → time fraction)
    D, T = [], []
    for name, p, t0, t1 in paths:
        seg = np.hypot(*np.diff(p, axis=0).T)
        arc = np.concatenate([[0], np.cumsum(seg)])
        tt = t0 + (t1 - t0) * inv(arc / arc[-1])
        r = np.full((h, w), np.inf, np.float32)
        r[p[:, 0], p[:, 1]] = np.minimum(r[p[:, 0], p[:, 1]], tt)
        d, idx = ndimage.distance_transform_edt(~np.isfinite(r), return_indices=True)
        D.append(d)
        T.append(r[idx[0], idx[1]])
    D, T = np.stack(D), np.stack(T)
    ok = D <= D.min(0, keepdims=True) + 7.0                  # crossings go to the first stroke through them
    T = np.where(ok, T, np.inf).min(0)
    T[D.min(0) > 30] = max(t1 for *_, t1 in STROKES)        # specks off every stroke: with the last one
    return T


def letters(alpha):
    """The name's letters (connected components below TEXT_Y0), left to right, as (y0, x0, cut-out)."""
    y0 = TEXT_Y0 - CROP[1]
    band = alpha[y0:]
    lab, n = ndimage.label(band > 0.04, structure=np.ones((3, 3)))
    out = []
    for sl, i in zip(ndimage.find_objects(lab), range(1, n + 1)):
        ys, xs = sl
        if (ys.stop - ys.start) * (xs.stop - xs.start) < 30:
            continue
        m = ndimage.binary_dilation(lab[sl] == i, iterations=1)
        out.append((ys.start + y0, xs.start, band[sl] * m))
    out.sort(key=lambda e: e[1])
    return out


def zoom_blur(img, cx, cy, ratio, n):
    if n <= 1:
        return img
    acc = np.zeros_like(img)
    for sc in ratio ** (-np.linspace(0, 1, n)):
        m = np.float32([[sc, 0, cx * (1 - sc)], [0, sc, cy * (1 - sc)]])
        acc += cv2.warpAffine(img, m, (img.shape[1], img.shape[0]), flags=cv2.INTER_LINEAR)
    return acc / n


class Logo:
    def __init__(self, path):
        self.alpha = load_logo(path)
        self.paths, self.mark = route(self.alpha)
        self.T = reveal_times(self.alpha, self.paths)
        self.mark_a = self.alpha.copy()
        self.mark_a[TEXT_Y0 - CROP[1]:] = 0
        self.letters = letters(self.alpha)
        ys, xs = np.nonzero(self.alpha > 0.05)
        self.c = ((xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2)        # logo centre, crop px
        self.s_rest = REST_H / (ys.max() - ys.min())
        tx = [x + a.shape[1] / 2 for _, x, a in self.letters]
        self.text_cx = (min(tx) + max(tx)) / 2

    def scale(self, t):
        """The placeholder's curve: 2.8× on frame 0, slow, then fast, landing at 0.40 s."""
        s = self.s_rest * (1 + 1.8 * (1 - smoother(t / LAND)))
        return s * (1 + 0.15 * smooth(window(t, 0.87, 0.97)) ** 1.5)

    def layer(self, t):
        """The logo at time t in its own (crop) space: alpha only — it is white."""
        a = self.mark_a * np.clip((t + SOFT - self.T) / SOFT, 0, 1)
        for i, (ly, lx, la) in enumerate(self.letters):
            x = expo_out(window(t, 0.38 + 0.02 * i, 0.48 + 0.02 * i))
            if x <= 0:
                continue
            cx = lx + la.shape[1] / 2
            dx = (cx - self.text_cx) * 0.25 * (1 - x)                            # the name tracks in
            dy = 14 * (1 - x)                                                     # and rises into place
            m = np.float32([[1, 0, dx], [0, 1, dy]])
            h, w = la.shape
            pad = 24
            buf = np.zeros((h + 2 * pad, w + 2 * pad), np.float32)
            buf[pad:pad + h, pad:pad + w] = la * x
            buf = cv2.warpAffine(buf, m, (w + 2 * pad, h + 2 * pad), flags=cv2.INTER_LINEAR)
            yy, xx = ly - pad, lx - pad
            y_0, x_0 = max(yy, 0), max(xx, 0)
            y_1, x_1 = min(yy + buf.shape[0], a.shape[0]), min(xx + buf.shape[1], a.shape[1])
            a[y_0:y_1, x_0:x_1] = np.maximum(a[y_0:y_1, x_0:x_1], buf[y_0 - yy:y_1 - yy, x_0 - xx:x_1 - xx])
        return a

    def frame(self, n):
        """Frame n on the 1920×1080 canvas: straight alpha (the colour is white everywhere)."""
        t = n / FPS
        s = self.scale(t)
        rot = np.deg2rad(-6.0 * (1 - smoother(t / LAND)))
        jx = jy = jr = 0.0
        hold = window(t, LAND, LAND + 0.08) * (1 - window(t, 0.83, 0.87))
        if hold > 0:                                                              # stepped, 10 per second
            rng = np.random.default_rng(int(t * 10) + 7)
            jx, jy = rng.uniform(-1.5, 1.5, 2) * hold
            jr = np.deg2rad(rng.uniform(-0.25, 0.25)) * hold
        c, sn = np.cos(rot + jr) * s, np.sin(rot + jr) * s
        cx, cy = CENTER[0] + jx, CENTER[1] + jy
        m = np.float32([[c, -sn, cx - (c * self.c[0] - sn * self.c[1])],
                        [sn, c, cy - (sn * self.c[0] + c * self.c[1])]])
        a = cv2.warpAffine(self.layer(t), m, (W, H), flags=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR)
        ratio = s / self.scale(max(t - 0.5 / FPS, 0))
        nb = int(np.clip(abs(np.log(ratio)) * 0.4 * W / 1.5, 1, 16))
        a = zoom_blur(a, cx, cy, ratio, nb)
        a *= 0.55 + 0.45 * smooth(t / 0.33)                                       # half transparent while oversized
        a *= 1 - smooth(window(t, 0.87, 0.97))
        return np.clip(a, 0, 1)

    def debug(self, path):
        rgb = np.stack([self.alpha * 0.35] * 3, -1)
        cols = [(1, 0.3, 0.3), (0.3, 1, 0.3), (0.3, 0.6, 1), (1, 0.85, 0.2)]
        for (name, p, _, _), col in zip(self.paths, cols):
            for y, x in p:
                rgb[max(y - 1, 0):y + 2, max(x - 1, 0):x + 2] = col
        Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).save(path)


def write_frames(logo, folder, alpha):
    for n in range(N):
        a = logo.frame(n)
        if alpha:
            img = Image.fromarray((np.dstack([np.ones((H, W, 3), np.float32), a]) * 255 + 0.5).astype(np.uint8), "RGBA")
        else:
            img = Image.fromarray((np.dstack([a] * 3) * 255 + 0.5).astype(np.uint8), "RGB")         # white on black
        img.save(Path(folder) / f"f{n:03d}.png")


def ffmpeg():
    import os
    return os.environ.get("AFTERFILM_FFMPEG", "ffmpeg")


def encode(folder, out, fmt):
    src = [ffmpeg(), "-v", "error", "-y", "-framerate", str(FPS), "-i", str(Path(folder) / "f%03d.png")]
    if fmt == "prores":
        args = ["-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", "-alpha_bits", "16",
                "-vendor", "apl0"]
    else:
        args = ["-c:v", "libx264", "-profile:v", "high", "-crf", "10", "-preset", "slow", "-pix_fmt", "yuv420p",
                "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-movflags", "+faststart"]
    subprocess.run(src + args + ["-r", str(FPS), str(out)], check=True)


def clean_opening(frames):
    """The reference's first second without its placeholder. The camera holds still, the tag only
    ever adds white, and from frame 12 it is small, thin and jittering, so each background pixel is
    uncovered in most of frames 12–29: their 30th percentile is the clean shot (frames 12–18 only on
    the right, where the legs come in from frame 19). Frames 0–11, where the oversized tag covers
    everything, are that clean shot; from frame 12 each frame keeps its own picture and only the
    tag's pixels are patched, with grain to match. The legs on the right are never touched."""
    h, w = frames[0].shape[:2]
    xx = np.arange(w, dtype=np.float32)[None, :, None] / w
    late = np.stack(frames[12:30])
    yy = np.arange(h, dtype=np.float32)[:, None, None] / h
    right = smooth((xx - 0.66) / 0.04)
    bg = (np.percentile(late, 30, axis=0) * (1 - right) +
          np.percentile(late[:7], 30, axis=0) * right).astype(np.float32)
    # where the tag's strokes pile up (its top, right of the pillar) take the darkest frames
    tag = (smooth((xx - 0.33) / 0.03) * (1 - smooth((xx - 0.68) / 0.02)) *
           smooth((yy - 0.04) / 0.03) * (1 - smooth((yy - 0.92) / 0.03)))
    dark = np.percentile(late, 4, axis=0).astype(np.float32)
    dark = dark + (np.median(bg - dark))                                       # the minimum's bias back out
    bg = bg * (1 - tag) + np.minimum(bg, dark) * tag
    rng = np.random.default_rng(98)
    resid = (late[:7] - bg).reshape(-1, 3)
    sigma = np.median(np.abs(resid), axis=0) * 1.4826                     # the footage's grain, robustly
    k = max(3, int(5 * w / 1280))
    out = []
    for n, f in enumerate(frames):
        grain = cv2.GaussianBlur(rng.standard_normal((h, w, 3)).astype(np.float32), (0, 0), 0.7) * sigma * 1.5
        if n < 12:
            out.append(np.clip(bg + grain, 0, 1))
            continue
        m = ((f - bg).mean(-1) > 0.05) & (xx[..., 0] < 0.70)
        m = cv2.dilate(m.astype(np.uint8), np.ones((2 * k + 1, 2 * k + 1), np.uint8)).astype(np.float32)
        m = cv2.GaussianBlur(m, (0, 0), k / 2)[..., None]
        out.append(np.clip(f * (1 - m) + (bg + grain) * m, 0, 1))
    return out


def preview(logo, ref, out):
    """The logo in the real opening shot (cleaned of the placeholder, clean_opening), with the
    reference carrying on from 1.0 s, with its own sound."""
    import os
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        subprocess.run([ffmpeg(), "-v", "error", "-y", "-t", f"{N / FPS}", "-i", str(ref), "-pix_fmt", "rgb24",
                        str(d / "r%03d.png")], check=True)
        frames = [np.asarray(Image.open(f)).astype(np.float32) / 255 for f in sorted(d.glob("r*.png"))][:N]
        for n, bg in enumerate(clean_opening(frames)):
            bg = cv2.resize(bg, (W, H), interpolation=cv2.INTER_LANCZOS4)
            a = logo.frame(n)[..., None]
            img = bg + a * (1 - bg)                                               # Screen = white over, with alpha a
            Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)).save(d / f"p{n:03d}.png")
        subprocess.run([ffmpeg(), "-v", "error", "-y", "-framerate", str(FPS), "-i", str(d / "p%03d.png"),
                        "-ss", f"{N / FPS}", "-i", str(ref), "-i", str(ref),
                        "-filter_complex", f"[1:v]scale={W}:{H}:flags=lanczos,fps={FPS},format=yuv420p,setsar=1[r];"
                                           "[0:v]format=yuv420p,setsar=1[l];[l][r]concat=n=2:v=1:a=0[v]",
                        "-map", "[v]", "-map", "2:a", "-c:v", "libx264", "-crf", "18", "-preset", "slow",
                        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
                        str(out)], check=True, env=os.environ)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--logo", required=True)
    ap.add_argument("--out", default="renders/ENCORE98_logo_intro_1920x1080.mp4")
    ap.add_argument("--format", choices=["mp4", "prores"], default="mp4")
    ap.add_argument("--debug", help="write the routed strokes to this image and stop")
    ap.add_argument("--stills", nargs="*", type=int, help="write these frames as PNGs next to --out and stop")
    ap.add_argument("--preview", help="the reference edit: write the logo in its opening shot to --out and stop")
    a = ap.parse_args()
    logo = Logo(a.logo)
    if a.debug:
        logo.debug(a.debug)
        raise SystemExit
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if a.preview:
        preview(logo, a.preview, out)
        raise SystemExit
    if a.stills:
        for n in a.stills:
            Image.fromarray((logo.frame(n) * 255).astype(np.uint8)).save(out.with_name(f"{out.stem}_{n:02d}.png"))
        raise SystemExit
    with tempfile.TemporaryDirectory() as d:
        write_frames(logo, d, alpha=a.format == "prores")
        encode(d, out, a.format)
