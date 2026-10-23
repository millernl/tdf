"""ENCORE98 — the logo intro for the dance video.

A 1-second overlay (1920×1080, 30 fps, alpha) that replaces the placeholder tag at the very start of
the edit. The placeholder starts huge, settles near the centre, holds with a hand-drawn jitter and is
gone by 1.0 s, as the boots step in; this keeps that slot exactly.

The logo (a raster PNG, white on transparent, the client's file; not in git) writes itself like a
signature. Each stroke follows a centreline routed along the logo's own skeleton between hand-placed
waypoints, and every pixel of the mark appears when the pen passes the nearest point of its stroke.
Meanwhile the whole logo settles from close up (a zoom-out with a zoom blur, as the placeholder
does), ENCORE98 comes in letter by letter, and on the way out it pushes towards the camera and
fades.

    0.00–0.45  the stem, the loop and swash, the inner stroke, then the lasso flourish
    0.30–0.55  E N C O R E 9 8, each letter rising into place
    0.45–0.86  holds, with a slight stepped jitter (hand-drawn, like the placeholder)
    0.86–0.99  pushes in and fades; nothing left at 1.0 s

    python edits/encore_logo.py --logo LOGO.png --out renders/ENCORE98_logo_intro_1920x1080.mov
    python edits/encore_logo.py --logo LOGO.png --debug work/encore/paths.png      # routed strokes
    python edits/encore_logo.py --logo LOGO.png --preview REFERENCE.mov --out ...   # + in-context mp4
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
CENTER = (0.5 * W, 0.48 * H)
REST_H = 0.50 * H                  # the logo's height (mark and name) at rest: the mark is about as tall as the
                                   # placeholder tag (~0.42 H); scaling down in the edit stays sharp
TEXT_Y0 = 1335                     # rows of the PNG below this are the name
CROP = (560, 800, 1380, 1440)      # the logo's region of the 2000-px PNG (x0, y0, x1, y1)

# the strokes, in writing order: waypoints along each (x, y in the PNG), and when the pen draws it
STROKES = [
    ("stem", [(973, 842), (913, 987), (827, 1107), (760, 1200), (716, 1290)], 0.00, 0.13),
    ("loop", [(1060, 1000), (1100, 920), (1160, 850), (1182, 900), (1120, 990), (1010, 1060), (965, 1150),
              (975, 1250), (1080, 1290), (1230, 1250), (1310, 1150), (1337, 1050)], 0.08, 0.34),
    ("inner", [(873, 1107), (940, 1060), (1000, 1015), (1050, 1012), (1090, 1035), (1070, 1075), (1110, 1107)],
     0.20, 0.30),
    ("lasso", [(1133, 1033), (1007, 1007), (873, 997), (740, 1013), (640, 1047), (597, 1073), (640, 1080),
               (807, 1100), (940, 1120), (1040, 1123), (1110, 1107)], 0.24, 0.42),
]
SOFT = 0.015                       # the pen's soft leading edge, seconds


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


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
    ok = D <= D.min(0, keepdims=True) + 3.0
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
        s = self.s_rest * (1 + 0.5 * (1 - expo_out(t / 0.45)))
        return s * (1 + 0.2 * smooth(window(t, 0.86, 0.99)) ** 1.5)

    def layer(self, t):
        """The logo at time t in its own (crop) space: alpha only — it is white."""
        a = self.mark_a * np.clip((t + SOFT - self.T) / SOFT, 0, 1)
        for i, (ly, lx, la) in enumerate(self.letters):
            x = expo_out(window(t, 0.30 + 0.022 * i, 0.42 + 0.022 * i))
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
        rot = np.deg2rad(-4.0 * (1 - expo_out(t / 0.45)))
        jx = jy = jr = 0.0
        hold = window(t, 0.45, 0.55) * (1 - window(t, 0.82, 0.86))
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
        a *= 1 - smooth(window(t, 0.86, 0.99))
        return np.clip(a, 0, 1)

    def debug(self, path):
        rgb = np.stack([self.alpha * 0.35] * 3, -1)
        cols = [(1, 0.3, 0.3), (0.3, 1, 0.3), (0.3, 0.6, 1), (1, 0.85, 0.2)]
        for (name, p, _, _), col in zip(self.paths, cols):
            for y, x in p:
                rgb[max(y - 1, 0):y + 2, max(x - 1, 0):x + 2] = col
        Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).save(path)


def write_frames(logo, folder):
    for n in range(N):
        a = logo.frame(n)
        rgba = np.concatenate([np.ones((H, W, 3), np.float32), a[..., None]], -1)
        Image.fromarray((rgba * 255 + 0.5).astype(np.uint8), "RGBA").save(Path(folder) / f"f{n:03d}.png")


def ffmpeg():
    import os
    return os.environ.get("AFTERFILM_FFMPEG", "ffmpeg")


def encode_prores(folder, out):
    subprocess.run([ffmpeg(), "-v", "error", "-y", "-framerate", str(FPS), "-i", str(Path(folder) / "f%03d.png"),
                    "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", "-alpha_bits", "16",
                    "-vendor", "apl0", "-r", str(FPS), str(out)], check=True)


def preview(logo, ref, out):
    """The overlay in place: over a still of the garage from just before the boots (the reference's
    frame at 0.967 s, where the placeholder has faded), then the reference itself from 1.0 s."""
    import os
    with tempfile.TemporaryDirectory() as d:
        bg = Path(d) / "bg.png"
        subprocess.run([ffmpeg(), "-v", "error", "-y", "-ss", "0.967", "-i", str(ref), "-frames:v", "1",
                        "-vf", f"scale={W}:{H}", str(bg)], check=True)
        base = np.asarray(Image.open(bg).convert("RGB")).astype(np.float32) / 255
        for n in range(N):
            a = logo.frame(n)[..., None]
            Image.fromarray(((base * (1 - a) + a) * 255 + 0.5).astype(np.uint8)).save(Path(d) / f"p{n:03d}.png")
        subprocess.run([ffmpeg(), "-v", "error", "-y", "-framerate", str(FPS), "-i", str(Path(d) / "p%03d.png"),
                        "-ss", f"{N / FPS}", "-i", str(ref), "-i", str(ref),
                        "-filter_complex", f"[1:v]scale={W}:{H},fps={FPS},format=yuv420p[r];[0:v]format=yuv420p[l];"
                                           "[l][r]concat=n=2:v=1:a=0[v]",
                        "-map", "[v]", "-map", "2:a", "-c:v", "libx264", "-crf", "18", "-preset", "slow",
                        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
                        str(out)], check=True, env=os.environ)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--logo", required=True)
    ap.add_argument("--out", default="renders/ENCORE98_logo_intro_1920x1080.mov")
    ap.add_argument("--preview", help="the reference edit: also write <out>_preview.mp4")
    ap.add_argument("--debug", help="write the routed strokes to this image and stop")
    ap.add_argument("--stills", nargs="*", type=int, help="write these frames as PNGs next to --out and stop")
    a = ap.parse_args()
    logo = Logo(a.logo)
    if a.debug:
        logo.debug(a.debug)
        raise SystemExit
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if a.stills:
        for n in a.stills:
            Image.fromarray((logo.frame(n) * 255).astype(np.uint8)).save(out.with_name(f"{out.stem}_{n:02d}.png"))
        raise SystemExit
    with tempfile.TemporaryDirectory() as d:
        write_frames(logo, d)
        encode_prores(d, out)
    if a.preview:
        preview(logo, a.preview, out.with_name(out.stem + "_preview.mp4"))
