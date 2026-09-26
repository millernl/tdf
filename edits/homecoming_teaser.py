"""HOMECOMING — the 15-second teaser, 9:16, cut from the final film's strongest moments.

The music is the Iron arrangement from bar 24 through the first half of the drop (bars
25–28, one four-bar phrase), then straight to bar 35: the outro pattern, the title and
the last hit. One splice, on a bar line.

  bar 24      the calm before: a lone dancer in a beam of light, then the cast standing
              silent in the haze, in black & white; the frame closes to a slit as the
              drums hold their breath.
  bars 25–28  the drop bursts the frame open to full height: the lights snap to beams, a
              lunge into the lens, hair whipped through amber, the light snaps to red,
              a powermove in light trails, a triptych of hair stacked in three rows, and
              the handstand that freezes.
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


T_GAP = q(1, 2)           # the drums hold their breath; the frame closes
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


def cuts():
    C = []

    def add(start, dur, key, **extra):
        C.append((start, dur, key, extra))

    add(0.0, g(2), "spotlight")
    add(T_GAP, g(2), "open")
    add(T_DROP, g(2), "drop", flash=0.45, shake=1.0)
    add(q(2, 2), g(2), "lunge", punch=0.05)
    add(q(3), g(2), "hairwhip")
    add(q(3, 2), g(2), "redlight")                  # the snap to red, exactly as in the film
    add(q(4), g(2), "trails")
    add(q(4, 2), g(2), "tri", triptych=True)
    add(T_FREEZE, T_WHITE - T_FREEZE + 0.05, "freeze", freeze_at=g(2))
    add(T_WHITE - 0.04, DURATION - T_WHITE + 0.04, "door")  # seen only inside the glyph's strokes
    return C


# Where the 9:16 window sits in each shot, over the shot's teaser duration:
# [(shot progress, centre x of the 16:9 frame)]. Suggested by afterfilm.vertical
# (motion + detail), then placed by eye on work/teaser/frames_*.jpg.
FRAMING = {
    "spotlight": [(0, 0.50)],
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
    out["spotlight"].zoom, out["spotlight"].center, out["spotlight"].center_end = (1.06, 1.18), (0.5, 0.57), None
    out["open"].t_in, out["open"].speed, out["open"].zoom = 1.0, 0.56, (1.0, 1.04)
    out["freeze"].hold = g(2)                        # never read past the freeze
    return out


def build(clips, w=1080, h=1920, fps=25):
    look = fx.Look(w, h, accent=brand.GOLD)
    tl = Timeline(w, h, fps, DURATION, look)
    tl.bar_ratio = 0.8
    for start, dur, key, extra in cuts():
        if extra.get("triptych"):
            tl.add(Shot(start, dur, clips=clips[key],
                        render=lambda s, lt, tl: scenes.triptych(s, lt, tl, stagger=BEAT / 4)))
        else:
            tl.add(Shot(start, dur, clip=clips[key],
                        **{k: v for k, v in extra.items() if k in ("punch", "flash", "freeze_at", "shake")}))

    close = (h / (h - w / tl.bar_ratio)) + 0.02      # letterbox amount that meets in the middle

    def bars(t):
        if t < T_GAP:
            return 0.0
        if t < T_DROP:                               # the eyes close in the drum gap
            return close * fx.ease_in(fx.window(t, T_GAP + 0.05, T_DROP - 0.04))
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
    for start, dur, key, extra in cuts():
        cs = clips[key] if isinstance(clips[key], list) else [clips[key]]
        for j, c in enumerate(cs):
            a = c.src_time(0) - 0.04 - (5 * 0.07 if c.echo else 0.0)
            b = c.src_time(min(dur, extra["freeze_at"]) if "freeze_at" in extra else dur)
            mx, at_t, flagged = analyze.frame_cuts(str(F.SHOW), a, b + 0.04)
            bad += bool(flagged)
            name = f"{key}{'.' + str(j + 1) if len(cs) > 1 else ''}"
            print(f"{'CUT?' if flagged else 'ok  '} {name:10s} src {analyze.tc(a)}–{analyze.tc(b)}  max {mx:.2f} "
                  f"@ {analyze.tc(at_t)}" + (f"  flagged {[analyze.tc(x) for x in flagged]}" if flagged else ""))
    print(f"{bad} clip(s) flagged")


def mix(sr=48000):
    """Bars 24–28, an equal-power splice on the bar line, bars 35 → the last hit and the
    silence after it."""
    from afterfilm import media
    # one read from the top, sliced in memory: a seek into the MP3 garbles its first frame
    src = media.read_audio(str(F.MUSIC), t_in=F.MUSIC_T0, dur=SRC_B + DURATION - SPLICE + 1.0, sr=sr, channels=2)
    n, ns, nx = int(round(DURATION * sr)), int(round((SPLICE - LEAD) * sr)), int(round(XF * sr))
    ia, ib = int(round(SRC_A * sr)), int(round((SRC_B - LEAD) * sr))
    a = src[ia:ia + ns + nx]
    b = src[ib - nx:ib - nx + n - (ns - nx)]
    y = np.zeros((n, 2), np.float32)
    y[:len(a)] += a
    k = np.linspace(0, np.pi / 2, 2 * nx, dtype=np.float32)[:, None]
    y[ns - nx:ns + nx] *= np.cos(k)                  # A out …
    fade_b = np.ones((len(b), 1), np.float32)
    fade_b[:2 * nx] = np.sin(k)                      # … B in
    y[ns - nx:ns - nx + len(b)] += b * fade_b
    y[:int(0.004 * sr)] *= np.linspace(0, 1, int(0.004 * sr), dtype=np.float32)[:, None]
    return (y * 10 ** (F.MUSIC_GAIN_DB / 20)).astype(np.float32)


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
