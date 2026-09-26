"""Vertical (9:16) reframing: where the window sits in each shot, and a sheet to review it.

    suggest(clips, cuts, path)  → {key: [(p, cx), ...]}  window centre across the shot
    sheet(clips, cuts, framing, path, out)  draws the window on the 16:9 frames

The window at zoom z covers (9/16)·(9/16)/z of a 16:9 frame's width. Its centre follows
where the dancers move and where the detail is (motion + edges); the path is smoothed and
held still unless the action really travels.
"""
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from . import brand, media

AW, AH = 320, 180
WIN = (9 / 16) * (9 / 16)          # window width as a fraction of a 16:9 frame, zoom 1


def _gray(path, t):
    f = media.read_frames(path, max(t, 0), 0.08, 25, (AW, AH), deinterlace=False)
    return cv2.cvtColor(f[0], cv2.COLOR_RGB2GRAY).astype(np.float32) if len(f) else None


def _best_cx(path, t, win):
    g1, g0 = _gray(path, t), _gray(path, t - 0.12)
    if g1 is None:
        return 0.5, 0.0
    mot = cv2.GaussianBlur(np.abs(g1 - (g0 if g0 is not None else g1)), (0, 0), 3)
    gx, gy = cv2.Sobel(g1, cv2.CV_32F, 1, 0), cv2.Sobel(g1, cv2.CV_32F, 0, 1)
    edge = cv2.GaussianBlur(np.hypot(gx, gy), (0, 0), 3)
    sal = mot / (mot.max() + 1e-6) * 0.7 + edge / (edge.max() + 1e-6) * 0.3
    col = sal.sum(0)
    k = max(int(win * AW), 1)
    run = np.convolve(col, np.ones(k), mode="valid")          # energy inside each window position
    i = int(np.argmax(run))
    conf = float(run[i] / (col.sum() + 1e-6))
    return (i + k / 2) / AW, conf


def suggest(clips, cuts, path, n=5):
    out = {}
    for start, dur, key, extra in cuts:
        cs = clips[key] if isinstance(clips[key], list) else [clips[key]]
        if len(cs) > 1:
            continue                                            # triptych rows show near-full frames
        c = cs[0]
        z = c.zoom[1] / c.zoom[0]
        win = WIN / max(z, 1.0)
        ps = np.linspace(0.05, 0.95, n)
        xs = np.array([_best_cx(path, c.src_time(p * dur), win)[0] for p in ps])
        xs = np.convolve(np.pad(xs, 1, mode="edge"), np.ones(3) / 3, mode="valid")   # smooth
        lo, hi = win / 2, 1 - win / 2
        xs = np.clip(xs, lo, hi)
        if xs.max() - xs.min() < 0.06:                          # hold still unless the action travels
            out[key] = [(0.0, round(float(np.median(xs)), 3))]
        else:
            out[key] = [(round(float(p), 2), round(float(x), 3)) for p, x in zip((0.0, 0.5, 1.0), xs[[0, n // 2, -1]])]
    return out


def sheet(clips, cuts, framing, path, out, per=12):
    """Each row: a shot at start / middle / end, with the vertical window drawn."""
    f = ImageFont.truetype(str(brand.FONTS / "dm-mono-400-normal.ttf"), 12)
    TW, TH = 320, 180
    rows = []
    for start, dur, key, extra in cuts:
        cs = clips[key] if isinstance(clips[key], list) else [clips[key]]
        if len(cs) > 1:
            continue
        c = cs[0]
        track = framing.get(key, [(0.0, 0.5)])
        z = c.zoom[1] / c.zoom[0]
        win = WIN / max(z, 1.0)
        thumbs = []
        for p in (0.05, 0.5, 0.95):
            fr = media.read_frames(path, c.src_time(p * dur), 0.08, 25, (TW, TH), deinterlace=False)
            im = Image.fromarray(fr[0]) if len(fr) else Image.new("RGB", (TW, TH))
            cx = float(np.interp(p, [k[0] for k in track], [k[1] for k in track]))
            d = ImageDraw.Draw(im)
            x0, x1 = (cx - win / 2) * TW, (cx + win / 2) * TW
            d.rectangle([0, 0, x0, TH], fill=None)
            shade = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))
            sd = ImageDraw.Draw(shade)
            sd.rectangle([0, 0, x0, TH], fill=(0, 0, 0, 150))
            sd.rectangle([x1, 0, TW, TH], fill=(0, 0, 0, 150))
            im = Image.alpha_composite(im.convert("RGBA"), shade).convert("RGB")
            ImageDraw.Draw(im).rectangle([x0, 0, x1, TH - 1], outline=(255, 190, 60), width=2)
            thumbs.append(im)
        rows.append((f"{key}  rec {start:5.2f}  {track}", thumbs))
    for k in range(0, len(rows), per):
        chunk = rows[k:k + per]
        img = Image.new("RGB", (3 * TW, len(chunk) * (TH + 16)), (18, 20, 20))
        d = ImageDraw.Draw(img)
        for r, (label, thumbs) in enumerate(chunk):
            y = r * (TH + 16)
            d.text((4, y + 2), label, font=f, fill=(230, 230, 225))
            for i, im in enumerate(thumbs):
                img.paste(im, (i * TW, y + 16))
        img.save(f"{out}_{k // per + 1:02d}.jpg", quality=84)
