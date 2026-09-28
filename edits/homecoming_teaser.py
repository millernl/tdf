"""HOMECOMING — the 15-second teaser, 9:16, cut from the final film's strongest moments.

The music starts on the vocal's "and faith" (bar 24), swelling in out of its own
reversed reverb and ringing with it, runs through the first phrase of the drop (bars
25–28) and splices on a bar line to bar 35: the outro pattern, the title, the last hit.

  bar 24      out of black, the backlight behind the silent cast strikes like a failing
              stage light — silhouettes on blown-out haze, flickering faster as the reverb
              swells. On "and" the light lands; on "faith" three staccato punch-ins snap to
              one dancer's profile. The frame closes to a slit, two negative frames strobe.
  bars 25–28  the drop bursts the frame open to full height: the lights snap to beams, a
              whip into a lunge at the lens, hair whipped through amber, the light snaps to
              red, a whip into the powermove in light trails, a triptych of hair stacked in
              three rows, and the handstand strobing in and freezing.
  bars 35–36  HOMECOMING is written by light over the frozen handstand; on the last hit
              we fly through the I.
  after       silence. The white of the I burns down to black and the glyph writes itself,
              as it does at the door of the film.

Every shot is cropped from the 4K master (a 9:16 window at zoom 1 is 1215×2160, so the
picture is downscaled, never blown up); the windows are placed on the action, shot by shot.

    python edits/homecoming_teaser.py                      # renders/homecoming_teaser_9x16.mp4
    python edits/homecoming_teaser.py --stills 0.5 2.0     # review frames
"""
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from afterfilm import brand, fx, scenes  # noqa: E402
from afterfilm.score import BAR, BEAT, at  # noqa: E402
from afterfilm.timeline import Shot, Timeline  # noqa: E402

import homecoming_final as F  # noqa: E402  the film: its clips, grades, music and master

TITLE = F.TITLE
SRC_A = at(24)            # the teaser opens on the arrangement's bar 24 …
SPLICE = 5 * BAR          # … plays five bars (24–28) …
SRC_B = at(35)            # … and continues from bar 35
XF = 0.012                # half-length of the equal-power crossfade at the splice
LEAD = 0.02               # the crossfade sits just ahead of the bar line: the drums hit ~9 ms early


def q(bar, beat=0.0):
    """Teaser seconds on its own bar grid (teaser bar 1 = arrangement bar 24)."""
    return (bar - 1) * BAR + beat * BEAT


T_AND = 0.84              # "and": the light lands (the vocal starts at arrangement 43.30 s)
T_FAITH = 1.32            # "faith": the punch-ins land on her profile
T_CLOSE = 1.52            # the frame starts to close
T_DROP = q(2)
T_FREEZE = q(5)
T_TITLE = q(6)            # arrangement bar 35
T_WRITE = q(6, 1)
T_ZOOM = q(7)
T_WHITE = q(7, 2.5)       # the last hit: through the I
T_DRAW0, T_DRAW1 = T_WHITE + 0.12, T_WHITE + 1.8
DURATION = 15.0


def g(n=1.0):
    return n * BEAT


EARLY = {"lunge": 0.08, "trails": 0.08, "freeze": 0.16}


def cuts():
    C = []

    def add(start, dur, key, **extra):
        C.append((start, dur, key, extra))

    add(0.0, T_DROP, "open", opening=True)
    add(T_DROP, g(2), "drop", flash=0.45, shake=1.0)
    # a whip lands on the beat at full smear: the shot starts EARLY[key] ahead of it
    add(q(2, 2) - EARLY["lunge"], g(2) + EARLY["lunge"], "lunge", punch=0.05, trans=("smear", 0.16))
    add(q(3), g(2), "hairwhip")
    add(q(3, 2), g(2), "redlight")                  # the snap to red, exactly as in the film
    add(q(4) - EARLY["trails"], g(2) + EARLY["trails"], "trails", trans=("smear", 0.16))
    add(q(4, 2), g(2), "tri", triptych=True)
    add(T_FREEZE - EARLY["freeze"], T_WHITE - T_FREEZE + EARLY["freeze"] + 0.05, "freeze",
        freeze_at=g(2) + EARLY["freeze"], trans=("strobe", 0.16))
    add(T_WHITE - 0.04, DURATION - T_WHITE + 0.04, "door")  # seen only inside the glyph's strokes
    return C


# Where the 9:16 window sits in each shot, over the shot's teaser duration:
# [(shot progress, centre x of the 16:9 frame)]. Suggested by afterfilm.vertical
# (motion + detail), then placed by eye on work/teaser/frames_*.jpg.
FRAMING = {
    "open":      [(0, 0.56)],
    "drop":      [(0, 0.52)],
    "lunge":     [(0, 0.59), (0.5, 0.68), (1, 0.74)],
    "hairwhip":  [(0, 0.82), (1, 0.76)],
    "redlight":  [(0, 0.77)],
    "trails":    [(0, 0.53), (0.5, 0.64), (1, 0.72)],
    "freeze":    [(0, 0.515)],
    "door":      [(0, 0.50)],
}


def teaser_clips(decode, panel_decode):
    clips = F.footage_clips()
    # inside the glyph at the end: the film's own door footage, the cast standing in the haze
    clips["door"] = F.footage_clips()["open"]
    clips["door"].speed = 0.1
    keys = {k for _, _, k, _ in cuts()}
    out = {}
    for k in keys:
        c = clips[k]
        if isinstance(c, list):                      # triptych rows: near-full 16:9 frames
            for panel in c:
                panel.zoom, panel.center, panel.center_end = (1.0, 1.02), (0.5, 0.5), None
                panel.decode = panel_decode
            out[k] = c
            continue
        c.zoom = (1.0, c.zoom[1] / c.zoom[0])        # the vertical crop is the framing; keep the push
        c.track = FRAMING[k]
        c.decode = decode
        out[k] = c
    # shot-specific adjustments for the teaser's shorter durations
    out["open"].t_in, out["open"].speed = 1.0, 0.56
    # shots that start early for a whip or a strobe: the trails back up into their own
    # motion; the lunge and the handstand sit right after a camera change in the recording,
    # so they hold their first frame instead. Either way the same frame lands on the beat.
    out["trails"].t_in -= EARLY["trails"] * out["trails"].speed
    for k in ("lunge", "freeze"):
        e, sp = EARLY[k], out[k].speed
        out[k].speed = [(0, 0.0), (e, 0.0), (e + 1e-3, sp), (10.0, sp)]
    out["freeze"].hold = g(2) + EARLY["freeze"]      # never read past the freeze
    return out


# ── the opening ──────────────────────────────────────────────────────────────
LIGHT = np.array([0.97, 0.96, 0.93], np.float32)
# frame → light level while the backlight strikes (25 fps; frame 21 is "and")
STRIKES = {0: 0.55, 1: 0.15, 6: 0.7, 7: 0.35, 11: 0.5, 13: 0.9, 14: 0.6, 16: 1.0, 17: 0.85, 18: 0.95, 19: 0.3}
NEGATIVE = {43, 45}                                  # single negative frames in the closing slit


def open_framing(t):
    """(zoom, cx, cy) of the 9:16 window on the cast: a slow pull while the light strikes,
    the full line on "and", then three hard steps in to her profile on "faith"."""
    if t < T_AND:
        return 1.10 - 0.06 * t / T_AND, 0.56, 0.5
    if t < 1.20:
        return 1.04 + 0.03 * (t - T_AND) / (1.20 - T_AND), 0.56, 0.5
    if t < 1.28:
        return 1.25, 0.57, 0.42
    if t < T_FAITH:
        return 1.5, 0.58, 0.38
    return 1.8 + 0.12 * fx.window(t, T_FAITH, T_DROP), 0.59, 0.34


def opening(shot, lt, tl):
    c = shot.clip
    t = shot.start + lt
    n = int(round(t * tl.fps))
    z, cx, cy = open_framing(t)
    img = fx.reframe(c.buf.frame(c.src_time(lt)), z, cx, cy, out_size=(tl.w, tl.h))
    img = tl.look.grade(img, **c.grade)
    px = min(tl.w, tl.h) / 1080
    if t < T_AND:                                    # the backlight strikes: silhouettes on blown-out haze
        k = STRIKES.get(n, 0.0)
        if k <= 0:
            return np.zeros_like(img)
        two = fx.smoothstep(0.28, 0.52, fx.luma(img))
        glow = cv2.GaussianBlur(two, (0, 0), 14 * px)
        return np.clip(two * 0.9 + glow * 0.4, 0, 1)[..., None] * LIGHT * k
    if n in NEGATIVE:                                # her figure as a white matte on black
        m = 1 - fx.smoothstep(0.22, 0.45, fx.luma(img))
        glow = cv2.GaussianBlur(m, (0, 0), 10 * px)
        return np.clip(m * 0.95 + glow * 0.45, 0, 1)[..., None] * LIGHT
    k = float(np.exp(-(t - T_AND) / 0.1))           # the light lands, pure white, and settles
    img = img * (1 - k) + fx.luma(img)[..., None] * k
    return fx.flash(img, 0.5 * k, tint=(1.0, 1.0, 1.0))
    return out


def build(clips, w=1080, h=1920, fps=25):
    look = fx.Look(w, h, accent=brand.GOLD)
    tl = Timeline(w, h, fps, DURATION, look)
    tl.bar_ratio = 0.8
    for start, dur, key, extra in cuts():
        if extra.get("triptych"):
            tl.add(Shot(start, dur, clips=clips[key],
                        render=lambda s, lt, tl: scenes.triptych(s, lt, tl, stagger=BEAT / 4)))
        elif extra.get("opening"):
            tl.add(Shot(start, dur, clip=clips[key], render=opening))
        else:
            tl.add(Shot(start, dur, clip=clips[key],
                        **{k: v for k, v in extra.items() if k in ("punch", "flash", "freeze_at", "shake", "trans")}))

    close = (h / (h - w / tl.bar_ratio)) + 0.02      # letterbox amount that meets in the middle

    def bars(t):
        if t < T_CLOSE:
            return 0.0
        if t < T_DROP:                               # the eyes close in the drum gap
            return close * fx.ease_in(fx.window(t, T_CLOSE, T_DROP - 0.04))
        return close * (1 - fx.expo_out(fx.window(t, T_DROP, T_DROP + 0.3)))
    tl.bars = bars

    def drain(t):
        return fx.ease_in_out(fx.window(t, T_TITLE, T_WRITE + 0.4))

    def cinema_at(t):
        if t < T_DROP or t >= T_WHITE:
            return {"mono": 1.0, "streaks": 0.9, "halation": 0.7}
        if t < T_TITLE:
            return {"mono": 0.0, "streaks": 1.05, "halation": 1.05, "bloom": 1.05}
        d = drain(t)
        return {"mono": d, "streaks": 1.05 - 0.15 * d, "halation": 1.05 - 0.35 * d, "bloom": 1.05 - 0.05 * d}
    tl.cinema_at = cinema_at
    tl.grain_at = lambda t: 0.6 if t < T_DROP else (0.42 if t < T_TITLE else (0.55 if t < T_WHITE else 0.6))

    def vignette(t):
        if t < T_WHITE:
            return 1.0 - 0.9 * fx.smoothstep(T_ZOOM + 0.4, T_WHITE, t)
        return 0.1 + 0.9 * fx.smoothstep(T_WHITE, T_WHITE + 0.5, t)
    tl.vignette_at = vignette

    scenes.add_title_into_i(tl, TITLE, T_TITLE, T_WRITE, T_ZOOM, T_WHITE)
    scenes.add_glyph_signoff(tl, T_WHITE, T_DRAW0, T_DRAW1, DURATION, height=0.33)
    return tl


def verify(clips):
    """Scan every clip's source range frame by frame for camera cuts / stray frames."""
    from afterfilm import analyze
    bad = 0
    C = cuts()
    for i, (start, dur, key, extra) in enumerate(C):
        nxt = C[i + 1] if i + 1 < len(C) else None
        # a whip or strobe into the next shot keeps this one on screen a little longer
        handle = max(0.0, nxt[0] + nxt[3]["trans"][1] - (start + dur)) if nxt and "trans" in nxt[3] else 0.0
        cs = clips[key] if isinstance(clips[key], list) else [clips[key]]
        for j, c in enumerate(cs):
            a = c.src_time(0) - 0.04 - (5 * 0.07 if c.echo else 0.0)
            b = c.src_time(min(dur, extra["freeze_at"]) if "freeze_at" in extra else dur + handle)
            mx, at_t, flagged = analyze.frame_cuts(str(F.SHOW), a, b + 0.04)
            bad += bool(flagged)
            name = f"{key}{'.' + str(j + 1) if len(cs) > 1 else ''}"
            print(f"{'CUT?' if flagged else 'ok  '} {name:10s} src {analyze.tc(a)}–{analyze.tc(b)}  max {mx:.2f} "
                  f"@ {analyze.tc(at_t)}" + (f"  flagged {[analyze.tc(x) for x in flagged]}" if flagged else ""))
    print(f"{bad} clip(s) flagged")


WET_DB = -9.0             # the hall under "and faith"
OPEN_DB = -2.0            # the opening's level against the drop


def _ir(sr, rt60=2.4, predelay=0.018, seed=24):
    """A hall: decorrelated stereo noise, the highs dying faster than the body."""
    from scipy import signal
    rng = np.random.default_rng(seed)
    n = int(rt60 * 1.3 * sr)
    t = np.arange(n) / sr
    b, a = signal.butter(2, 2500 / (sr / 2))
    chans = []
    for _ in range(2):
        nz = rng.standard_normal(n)
        lo = signal.lfilter(b, a, nz)
        chans.append(lo * 10 ** (-3 * t / rt60) + 0.5 * (nz - lo) * 10 ** (-3 * t / (rt60 * 0.45)))
    ir = np.stack(chans, 1)
    k = int(0.004 * sr)
    ir[:k] *= np.linspace(0, 1, k)[:, None]
    ir = np.concatenate([np.zeros((int(predelay * sr), 2)), ir])
    return (ir / np.sqrt((ir ** 2).sum(0, keepdims=True))).astype(np.float32)


def _verb(x, ir, sr):
    from scipy import signal
    b, a = signal.butter(2, 180 / (sr / 2), "high")
    xh = signal.lfilter(b, a, x, axis=0)
    return np.stack([signal.fftconvolve(xh[:, c], ir[:, c]) for c in range(2)], 1).astype(np.float32)


def mix(sr=48000):
    """"and faith" → the drop → bar 28, an equal-power splice on the bar line, bar 35 →
    the last hit and the silence after it. The words swell in out of their own reversed
    reverb and ring in the hall until the drop takes over."""
    from afterfilm import media
    # one read from the top, sliced in memory: a seek into the MP3 garbles its first frame
    src = media.read_audio(str(F.MUSIC), t_in=F.MUSIC_T0, dur=SRC_B + DURATION - SPLICE + 1.0, sr=sr, channels=2)
    n, ns, nx = int(round(DURATION * sr)), int(round((SPLICE - LEAD) * sr)), int(round(XF * sr))
    t_dry = T_AND - 0.02                             # the music enters just ahead of "and"
    i0, j0 = int(round(t_dry * sr)), int(round((SRC_A + t_dry) * sr))
    ib = int(round((SRC_B - LEAD) * sr))
    y = np.zeros((n, 2), np.float32)
    a = src[j0:j0 + ns + nx - i0].copy()
    kf = int(0.012 * sr)
    a[:kf] *= np.linspace(0, 1, kf, dtype=np.float32)[:, None]
    y[i0:i0 + len(a)] += a
    k = np.linspace(0, np.pi / 2, 2 * nx, dtype=np.float32)[:, None]
    y[ns - nx:ns + nx] *= np.cos(k)                  # A out …
    b = src[ib - nx:ib - nx + n - (ns - nx)]
    fade_b = np.ones((len(b), 1), np.float32)
    fade_b[:2 * nx] = np.sin(k)                      # … B in
    y[ns - nx:ns - nx + len(b)] += b * fade_b

    ir = _ir(sr)
    i_drop = int(round(T_DROP * sr))
    phrase = src[j0:j0 + (i_drop - i0)].copy()       # "and faith", up to the drop
    kf = int(0.04 * sr)
    phrase[-kf:] *= np.linspace(1, 0, kf, dtype=np.float32)[:, None]
    phrase[:int(0.012 * sr)] *= np.linspace(0, 1, int(0.012 * sr), dtype=np.float32)[:, None]
    wet = _verb(phrase, ir, sr)[:n - i0]
    env = np.ones((len(wet), 1), np.float32)         # the hall clears as the drop takes over
    d0, d1 = i_drop - i0, i_drop - i0 + int(0.7 * sr)
    env[d0:d1, 0] = np.cos(np.linspace(0, np.pi / 2, d1 - d0)) ** 2
    env[d1:] = 0
    y[i0:i0 + len(wet)] += wet * env * 10 ** (WET_DB / 20)
    # reverse reverb: reverse the words, put them in the hall, reverse back — the hall now
    # rings *before* them and swells right up into "and"
    pre = _verb(phrase[::-1], ir, sr)[::-1][:len(ir) - 1]
    swell = pre[-i0:].copy()
    swell *= (np.linspace(0, 1, len(swell), dtype=np.float32) ** 1.2)[:, None]
    ref = np.sqrt(np.mean(phrase[:int(0.25 * sr)] ** 2))
    w = int(0.05 * sr)
    loudest = max(np.sqrt(np.mean(swell[i:i + w] ** 2)) for i in range(0, len(swell) - w, w))
    swell *= ref / (loudest + 1e-9) * 10 ** (-4 / 20)   # it crests just under the words
    y[:i0] += swell
    # the opening sits 2 dB under the drop: headroom for the hall, and the drop hits harder
    g = np.ones((n, 1), np.float32)
    r = int(0.03 * sr)
    g[:i_drop - r] = 10 ** (OPEN_DB / 20)
    g[i_drop - r:i_drop, 0] = np.linspace(10 ** (OPEN_DB / 20), 1, r)
    return (y * g * 10 ** (F.MUSIC_GAIN_DB / 20)).astype(np.float32)


if __name__ == "__main__":
    import argparse
    from afterfilm import media
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="renders/homecoming_teaser_9x16.mp4")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--stills", nargs="*", type=float)
    ap.add_argument("--edl", action="store_true")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    W, H = int(1080 * a.scale) // 2 * 2, int(1920 * a.scale) // 2 * 2
    full = (int(3840 * a.scale) // 2 * 2, int(2160 * a.scale) // 2 * 2)
    panel = (int(1920 * a.scale) // 2 * 2, int(1080 * a.scale) // 2 * 2)
    clips = teaser_clips(full, panel)
    if a.verify:
        verify(clips)
        sys.exit(0)
    tl = build(clips, W, H)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    if a.edl:
        print(tl.edl())
    elif a.stills:
        print(tl.stills(a.stills, str(Path(a.out).with_suffix("")) + "_{t:05.2f}.png"))
    else:
        wav = str(Path(a.out).with_suffix(".wav"))
        media.write_wav(wav, mix())
        tl.render(a.out, wav=wav)
