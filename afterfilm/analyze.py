"""Read a whole show recording and surface the moments worth cutting.

    python -m afterfilm.analyze footage/part1.mp4 footage/part2.mp4 --out work/analysis
    python -m afterfilm.analyze --peek footage/part1.mp4 1:12:40 1:12:43.5 --out work/peek

Produces, in --out:
  analysis.json     per-second picture/audio metrics, numbers (pieces between applause),
                    tempo per number, top moments per number, camera cuts
  timeline.png      the show's energy curve: loudness, applause, motion, numbers
  overview_*.jpg    one frame every N seconds across the show, timecoded
  number_*.jpg      the strongest moments of each number, timecoded
Parts are laid end to end on one show clock; timecodes in the sheets are that clock.
"""
import argparse
import json
import subprocess
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from . import brand, media

FPS = 4                 # analysis sample rate
AW, AH = 320, 180       # analysis resolution
TW, TH = 240, 135       # stored thumbnail size (1 per second)


def tc(s):
    s = max(0.0, s)
    return f"{int(s // 3600)}:{int(s % 3600 // 60):02d}:{s % 60:04.1f}"


def parse_tc(x):
    parts = [float(p) for p in str(x).split(":")]
    v = 0.0
    for p in parts:
        v = v * 60 + p
    return v


# ── picture ──────────────────────────────────────────────────────────────────
def scan_video(path, offset, info, rows, thumbs):
    vf = ("bwdif=mode=send_frame," if info["interlaced"] else "") + f"fps={FPS},scale={AW}:{AH}"
    proc = subprocess.Popen([media.ffmpeg(), "-v", "error", "-i", str(path), "-vf", vf, "-f", "rawvideo",
                             "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    size = AW * AH * 3
    prev_gray = prev_small = prev_hist = None
    k = 0
    while True:
        raw = proc.stdout.read(size)
        if len(raw) < size:
            break
        rgb = np.frombuffer(raw, np.uint8).reshape(AH, AW, 3)
        t = offset + k / FPS
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        g = cv2.GaussianBlur(gray, (5, 5), 0).astype(np.float32)
        f = rgb.astype(np.float32)
        rg, yb = f[..., 0] - f[..., 1], 0.5 * (f[..., 0] + f[..., 1]) - f[..., 2]
        colorful = float(np.hypot(rg.std(), yb.std()) + 0.3 * np.hypot(rg.mean(), yb.mean()))
        hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
        hist = cv2.calcHist([hsv], [0, 1, 2], None, [12, 6, 6], [0, 180, 0, 256, 0, 256])
        hist = cv2.normalize(hist, None).flatten()
        row = {
            "t": round(t, 3),
            "bright": float(gray.mean() / 255),
            "lit": float((gray > 90).mean()),                     # share of the frame that's stage-lit
            "p95": float(np.percentile(gray, 95) / 255),
            "sharp": float(cv2.Laplacian(gray, cv2.CV_32F).var()),
            "color": colorful,
            "motion": 0.0, "flow": 0.0, "mx": 0.5, "my": 0.5, "cut": 0.0,
        }
        if prev_gray is not None:
            diff = np.abs(g - prev_gray)
            row["motion"] = float(diff.mean() / 255)
            small = cv2.resize(gray, (160, 90))
            flow = cv2.calcOpticalFlowFarneback(prev_small, small, None, 0.5, 2, 9, 2, 5, 1.1, 0)
            mag = np.hypot(flow[..., 0], flow[..., 1])
            # dancer motion = flow minus the camera's global move
            row["flow"] = float(np.abs(mag - np.median(mag)).mean())
            wsum = diff.sum()
            if wsum > 0:
                ys, xs = np.mgrid[0:AH, 0:AW]
                row["mx"] = float((diff * xs).sum() / wsum / AW)
                row["my"] = float((diff * ys).sum() / wsum / AH)
            row["cut"] = float(1 - cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CORREL))
            prev_small = small
        else:
            prev_small = cv2.resize(gray, (160, 90))
        prev_gray, prev_hist = g, hist
        rows.append(row)
        if k % FPS == 0:
            thumbs.append(cv2.resize(rgb, (TW, TH), interpolation=cv2.INTER_AREA))
        k += 1
        if k % (FPS * 600) == 0:
            print(f"    {tc(t)}", flush=True)
    proc.wait()
    return k / FPS


# ── sound ────────────────────────────────────────────────────────────────────
def scan_audio(paths, offsets, total):
    import librosa
    sr = 16000
    hop = sr // FPS
    y = np.zeros(int(total * sr) + sr, np.float32)
    for p, off in zip(paths, offsets):
        if not media.probe(p)["audio"]:
            continue
        a = media.read_audio(p, sr=sr, channels=1)[:, 0]
        i = int(off * sr)
        y[i:i + len(a)] = a[: len(y) - i]
    rms = librosa.feature.rms(y=y, frame_length=hop * 2, hop_length=hop, center=True)[0]
    flat = librosa.feature.spectral_flatness(y=y, n_fft=1024, hop_length=hop)[0]
    onset = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    # 'tonalness': energy concentrated in harmonic peaks → music; applause is broadband
    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=hop))
    contrast = librosa.feature.spectral_contrast(S=S, sr=sr).mean(axis=0)
    n = min(len(rms), len(flat), len(onset), len(contrast))
    db = 20 * np.log10(rms[:n] + 1e-6)
    return y, sr, {"db": db, "flat": flat[:n], "onset": onset[:n], "contrast": contrast[:n]}


def smooth(x, n):
    if n < 2:
        return x
    k = np.ones(n) / n
    return np.convolve(np.pad(x, (n // 2, n - 1 - n // 2), mode="edge"), k, mode="valid")


def find_applause(a):
    """Applause: noisy (flat spectrum), little harmonic contrast, not silence, ≥2 s.
    Loudness alone can't tell it from music — a hall claps quieter than the PA plays —
    and percentiles fail because applause is a small share of a show, so the noise
    tests are anchored to the median."""
    db = smooth(a["db"], FPS)
    flat = smooth(a["flat"], FPS * 2)
    con = smooth(a["contrast"], FPS * 2)
    audible = db > min(np.percentile(db, 1), -50.0) + 12      # well above room tone / hiss
    noisy = flat > max(0.08, 8 * np.median(a["flat"]))
    atonal = con < np.median(con)
    cand = audible & noisy & atonal
    spans, i = [], 0
    while i < len(cand):
        if cand[i]:
            j = i
            while j < len(cand) and cand[j:j + FPS].any():
                j += 1
            if (j - i) / FPS >= 2.0:
                spans.append((i / FPS, j / FPS))
            i = j
        i += 1
    return spans


def numbers_from(applause, total, min_len=45.0):
    """Pieces = stretches between applause, long enough to be a dance number."""
    bounds = [0.0] + [x for s in applause for x in s] + [total]
    out = []
    for k in range(0, len(bounds) - 1, 2):
        a, b = bounds[k], bounds[k + 1]
        if b - a >= min_len:
            out.append((a, b))
    return out


# ── picking moments ──────────────────────────────────────────────────────────
def z(x):
    x = np.asarray(x, np.float64)
    return (x - np.median(x)) / (np.percentile(x, 90) - np.percentile(x, 10) + 1e-9)


def moment_scores(rows, a):
    n = min(len(rows), len(a["db"]))
    col = lambda k: np.array([r[k] for r in rows[:n]])
    vis = (1.3 * z(smooth(col("flow"), FPS)) + 0.6 * z(smooth(col("motion"), FPS)) + 0.7 * z(np.log1p(col("sharp")))
           + 0.6 * z(col("lit")) + 0.4 * z(col("color")))
    snd = 0.5 * z(smooth(a["onset"][:n], FPS)) + 0.4 * z(smooth(a["db"][:n], FPS * 2))
    usable = (col("bright") > 0.04) & (col("cut") < 0.5)   # not black, not mid-cut
    return np.where(usable, vis + snd, -9.0)


def top_moments(score, span, k=24, spacing=4.0):
    a, b = int(span[0] * FPS), int(span[1] * FPS)
    s = score[a:b].copy()
    picks = []
    for _ in range(k):
        if not len(s) or s.max() < -5:
            break
        i = int(np.argmax(s))
        picks.append(((a + i) / FPS, float(s[i])))
        lo, hi = max(0, i - int(spacing * FPS)), i + int(spacing * FPS)
        s[lo:hi] = -9
    return sorted(picks)


# ── sheets ───────────────────────────────────────────────────────────────────
def _font(size):
    return ImageFont.truetype(str(brand.FONTS / f"{brand.MONO}.ttf"), size)


def sheet(items, path, cols=6, title=""):
    """items: [(thumb uint8 HxWx3, caption)]"""
    rows = (len(items) + cols - 1) // cols
    head = 44 if title else 0
    img = Image.new("RGB", (cols * TW, head + rows * (TH + 20)), (18, 20, 20))
    d = ImageDraw.Draw(img)
    if title:
        d.text((10, 12), title, font=_font(18), fill=(235, 235, 230))
    f = _font(12)
    for i, (th, cap) in enumerate(items):
        x, y = (i % cols) * TW, head + (i // cols) * (TH + 20)
        img.paste(Image.fromarray(th), (x, y))
        d.text((x + 4, y + TH + 3), cap, font=f, fill=(200, 205, 200))
    img.save(path, quality=86)


def plot_timeline(path, rows, a, applause, numbers, total):
    W, H = 2400, 520
    img = Image.new("RGB", (W, H), (18, 20, 20))
    d = ImageDraw.Draw(img)
    X = lambda t: int(t / total * (W - 20)) + 10

    def curve(vals, y0, h, color):
        v = np.asarray(vals, np.float64)
        v = smooth(v, FPS * 10)
        v = (v - np.percentile(v, 2)) / (np.percentile(v, 98) - np.percentile(v, 2) + 1e-9)
        pts = [(X(i / FPS), y0 + h - float(np.clip(v[i], 0, 1)) * h) for i in range(0, len(v), FPS)]
        d.line(pts, fill=color, width=2)

    for s, e in applause:
        d.rectangle([X(s), 40, X(e), H - 40], fill=(70, 55, 30))
    for i, (s, e) in enumerate(numbers):
        d.rectangle([X(s), 20, X(e), 32], fill=brand.GREEN)
        d.text((X(s) + 3, 20), f"{i + 1}", font=_font(11), fill=(235, 235, 230))
    curve(a["db"], 50, 130, (247, 194, 124))
    curve([r["flow"] for r in rows], 200, 130, (140, 200, 150))
    curve([r["lit"] for r in rows], 350, 110, (200, 200, 220))
    f = _font(13)
    d.text((12, 52), "loudness", font=f, fill=(247, 194, 124))
    d.text((12, 202), "dancer motion", font=f, fill=(140, 200, 150))
    d.text((12, 352), "stage light", font=f, fill=(200, 200, 220))
    for m in range(0, int(total) + 1, 600):
        d.line([X(m), H - 34, X(m), H - 26], fill=(150, 150, 150))
        d.text((X(m) + 2, H - 24), tc(m)[:-2], font=f, fill=(150, 150, 150))
    img.save(path)


# ── main ─────────────────────────────────────────────────────────────────────
def analyze(paths, out):
    out.mkdir(parents=True, exist_ok=True)
    rows, thumbs, offsets, parts = [], [], [], []
    offset = 0.0
    for p in paths:
        info = media.probe(p)
        print(f"  {p}: {info['width']}x{info['height']} {info['fps']:.2f}fps "
              f"{'interlaced' if info['interlaced'] else 'progressive'} {tc(info['duration'])}", flush=True)
        offsets.append(offset)
        parts.append({"path": str(p), "offset": offset, **info})
        dur = scan_video(p, offset, info, rows, thumbs)
        offset += dur
    total = offset
    print("  audio…", flush=True)
    y, sr, a = scan_audio(paths, offsets, total)
    applause = find_applause(a)
    numbers = numbers_from(applause, total)
    score = moment_scores(rows, a)

    import librosa
    num_info = []
    for i, (s, e) in enumerate(numbers):
        seg = y[int(s * sr):int(e * sr)]
        tempo, beats = librosa.beat.beat_track(y=seg, sr=sr, hop_length=256)
        moments = top_moments(score, (s, e))
        num_info.append({"n": i + 1, "start": s, "end": e, "tempo": float(np.atleast_1d(tempo)[0]),
                         "moments": [{"t": t, "score": round(v, 2)} for t, v in moments]})
        items = [(thumbs[min(int(t), len(thumbs) - 1)], f"{tc(t)}  {v:+.1f}") for t, v in moments]
        sheet(items, out / f"number_{i + 1:02d}.jpg",
              title=f"NUMBER {i + 1}   {tc(s)} – {tc(e)}   ~{float(np.atleast_1d(tempo)[0]):.0f} BPM")

    step = max(5, int(total / 360))           # ~360 frames across the whole show
    ov = [(thumbs[i], tc(i)) for i in range(0, len(thumbs), step)]
    per = 72
    for k in range(0, len(ov), per):
        sheet(ov[k:k + per], out / f"overview_{k // per + 1:02d}.jpg", cols=8,
              title=f"OVERVIEW {k // per + 1}   every {step}s")
    plot_timeline(out / "timeline.png", rows, a, applause, numbers, total)

    cuts = [r["t"] for r in rows if r["cut"] > 0.55]
    json.dump({"parts": parts, "total": total, "applause": applause, "numbers": num_info, "cuts": cuts,
               "per_second": [{k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()}
                              for r in rows[::FPS]]},
              open(out / "analysis.json", "w"), indent=1)
    np.save(out / "thumbs.npy", np.stack(thumbs))
    print(f"  {len(numbers)} numbers, {len(applause)} applause spans, {len(cuts)} camera cuts → {out}")


def peek(path, times, out):
    """Full-resolution stills at given timecodes, for a close look before committing to a shot."""
    out.mkdir(parents=True, exist_ok=True)
    info = media.probe(path)
    for x in times:
        t = parse_tc(x)
        f = media.read_frames(path, t, 1 / info["fps"], info["fps"], (info["width"], info["height"]))[0]
        p = out / f"peek_{tc(t).replace(':', '-')}.jpg"
        Image.fromarray(f).save(p, quality=90)
        print(p)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--out", default="work/analysis")
    ap.add_argument("--peek", action="store_true", help="first input is the video, the rest are timecodes")
    args = ap.parse_args()
    if args.peek:
        peek(Path(args.inputs[0]), args.inputs[1:], Path(args.out))
    else:
        analyze([Path(p) for p in args.inputs], Path(args.out))
