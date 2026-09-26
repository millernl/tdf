"""HOMECOMING — the one-minute after-movie, cut to the Iron mix.

The music is conformed to 31 bars at 130 BPM (source bars 5–8 | 9–12 | 17–20 | 29–32 |
33–40 | 41–44 | 45–46 | 76) and stops dead at 57.23 s; the logo is written in the silence.
The drums play a 3-3-2 gallop — hits on 1, the "and" of 2, and 4 — and the fast
sections cut on exactly those.

  bars 1–4    drone. The glyph writes itself with the show inside; we fly through it.
              A girl alone at a table.
  bars 5–12   the drums. The journey, in black & white: walking silhouettes, the spotlight
              ring, the projected window of a home, beams, the audience's view.
  bars 13–16  the build: cuts ride the gallop; in the drum gap the frame closes to black.
  bars 17–24  the drop: the frame bursts open in colour. Jerseys, kids, lasers, a triptych,
              a speed ramp — and a handstand that freezes as the drums fall away.
  bars 25–28  the breakdown: through black into the heart — the group hug, faces, the
              District98 hoodies, the celebration building again.
  bars 29–31  everything returns: a leap in front of the whole cast; the cast clapping.
              HOMECOMING is written over them; we fly into the I, onto a white page.
  57.2–60.0   silence. The glyph is written in '98 Green'; the wordmark arrives.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from afterfilm import brand, fx, scenes  # noqa: E402
from afterfilm.score import BAR, BEAT, at  # noqa: E402
from afterfilm.timeline import Clip, Shot, Timeline, VideoSource  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SHOW = ROOT / "footage" / "HOMECOMING.2026.PVT.mp4"
MUSIC = ROOT / "music" / "iron_MIX.mp3"
MUSIC_BPM, MUSIC_T0 = 130.0, 0.0093          # first downbeat of the source mix (measured)
MUSIC_SPANS = [(5, 8), (9, 12), (17, 20), (29, 32), (33, 40), (41, 44), (45, 46), (76, 76)]

TITLE = "HOMECOMING"
DURATION = 60.0
T_LAND = at(4)            # through the glyph door
T_DRUMS = at(5)
T_GAP = at(16, 2)         # the drums hold their breath
T_DROP = at(17)
T_BREAK = at(25)
T_RETURN = at(29)
T_TITLE = at(30)
T_WRITE = at(30, 2)
T_ZOOM = at(31, 2)
T_WHITE = at(32)          # the music's hard stop
T_MARK = T_WHITE + 1.15


def tc(s):
    v = 0.0
    for x in s.split(":"):
        v = v * 60 + float(x)
    return v


def g(n=1.0):
    return n * BEAT


# (record start, duration, clip key, extras). Keys map to footage_clips().
def cuts():
    C = []

    def add(start, dur, key, **extra):
        C.append((start, dur, key, extra))

    # bars 1–4 — drone
    add(0.20, T_LAND - 0.20, "open")
    add(at(4), BAR, "table")
    # bars 5–8 — the drums enter
    add(at(5), BAR, "walk", shake=0.5)
    add(at(6), BAR, "spot")
    add(at(7), BAR, "window")
    add(at(8), g(2), "rise")
    add(at(8, 2), g(2), "beams")
    # bars 9–12 — brass joins
    add(at(9), BAR, "tableset", trans=("stripes", g(1)))
    add(at(10), g(1.5), "hairgrey")
    add(at(10, 1.5), g(1.5), "singer")
    add(at(10, 3), g(1), "pile")
    add(at(11), BAR, "crowdpov")
    add(at(12), g(1.5), "blackcast")
    add(at(12, 1.5), g(1.5), "dinner")
    add(at(12, 3), g(1), "bluesil")
    # bars 13–16 — the build rides the gallop (1 · 2& · 4)
    for bar, keys in ((13, ("crouch", "redclose", "hairblack")),
                      (14, ("orange", "beamsgroup", "ring")),
                      (15, ("flip", "castb", "ambergroup"))):
        add(at(bar), g(1.5), keys[0])
        add(at(bar, 1.5), g(1.5), keys[1])
        add(at(bar, 3), g(1), keys[2])
    add(at(16), g(0.5), "s1")
    add(at(16, 0.5), g(1), "s2")
    add(at(16, 1.5), g(0.5), "s3")
    add(at(16, 2), g(2), "last")                         # the frame closes on this
    # bars 17–24 — the drop, in colour
    add(T_DROP, BAR, "drop", flash=0.45, shake=1.0)
    add(at(18), g(1.5), "amber")
    add(at(18, 1.5), g(1.5), "98", punch=0.035)
    add(at(18, 3), g(1), "kids")
    add(at(19), BAR, "tri", triptych=True)
    add(at(20), g(1.5), "kidsgroup")
    add(at(20, 1.5), g(1.5), "lasers")
    add(at(20, 3), g(1), "smile")
    add(at(21), BAR, "ramp", flash=0.35)
    add(at(22), g(1.5), "redgroup")
    add(at(22, 1.5), g(1.5), "kidsamber")
    add(at(22, 3), g(1), "green")
    add(at(23), g(1.5), "floor")
    add(at(23, 1.5), g(1.5), "magenta")
    add(at(23, 3), g(1), "crowd")
    add(at(24), BAR, "freeze", freeze_at=g(2))
    # bars 25–28 — the heart
    add(T_BREAK, BAR, "hug", trans=("dip", 0.9))
    add(at(26), BAR, "faces")
    add(at(27), BAR, "hoodies")
    add(at(28), BAR, "celebrate")
    # bars 29–31 — everything returns
    add(T_RETURN, BAR, "leap", shake=0.8, flash=0.3)
    add(at(30), T_WHITE - at(30) + 0.05, "family")
    return C


def footage_clips(path=SHOW):
    src = VideoSource(str(path))
    iron, color, silver = {"look": "iron"}, {"look": "color"}, {"look": "silver"}

    def C(t, look=color, **k):
        return Clip(src, tc(t), grade=dict(look), **k)

    clips = {
        # drone
        "open":       C("0:00:07.30", iron, speed=0.4, zoom=(1.0, 1.06), note="silhouettes walk out of the haze"),
        "table":      C("1:05:35.90", iron, speed=0.6, zoom=(1.04, 1.12), note="a girl alone at the table"),
        # drums
        "walk":       C("1:23:59.30", iron, speed=0.7, zoom=(1.0, 1.05), note="silhouettes in caps, walking"),
        "spot":       C("0:28:08.60", iron, speed=0.8, zoom=(1.05, 1.0), note="breaker in the spotlight ring"),
        "window":     C("1:20:59.30", iron, speed=0.75, zoom=(1.0, 1.12), center=(0.5, 0.45), note="the projected window of a home"),
        "rise":       C("1:06:55.50", iron, speed=0.8, note="close · the group rises"),
        "beams":      C("1:39:39.00", iron, zoom=(1.0, 1.03), note="white beams, three silhouettes"),
        "tableset":   C("1:05:11.00", iron, speed=0.8, zoom=(1.0, 1.05), note="beams over the empty table"),
        "hairgrey":   C("2:15:10.90", iron, speed=0.8, note="hair flying in grey haze"),
        "singer":     C("1:39:59.10", iron, note="a singer, a beam behind her"),
        "pile":       C("2:13:29.00", iron, zoom=(1.12, 1.14), note="bodies piled in the spotlight"),
        "crowdpov":   C("1:22:25.30", iron, speed=0.9, zoom=(1.0, 1.04), note="seen over the audience's heads"),
        "blackcast":  C("1:13:59.60", iron, note="cast in black, hair flying"),
        "dinner":     C("1:03:08.90", iron, zoom=(1.05, 1.08), note="the family table, candles"),
        "bluesil":    C("1:07:30.90", iron, note="silhouettes against a flare"),
        # build
        "crouch":     C("0:01:40.00", iron, zoom=(1.18, 1.2), center=(0.41, 0.5), note="opening number, low under the beams"),
        "redclose":   C("2:10:47.00", iron, note="solo on the floor, close"),
        "hairblack":  C("1:06:22.85", iron, note="close · hair in black"),
        "orange":     C("2:16:47.00", iron, zoom=(1.14, 1.16), center=(0.42, 0.5), note="silhouettes against the backdrop"),
        "beamsgroup": C("0:01:53.20", iron, zoom=(1.18, 1.2), center=(0.41, 0.5), note="opening number, full out"),
        "ring":       C("2:15:18.50", iron, note="the spotlight ring, dancing"),
        "flip":       C("1:06:39.30", iron, zoom=(1.0, 1.04), note="close · faces in black, looking up"),
        "castb":      C("1:14:09.30", iron, note="cast in black, full out"),
        "ambergroup": C("1:04:47.30", iron, note="close · the group surges"),
        "s1":         C("0:01:54.20", iron, zoom=(1.2, 1.2), center=(0.41, 0.5), note="stutter"),
        "s2":         C("1:14:10.30", iron, note="stutter"),
        "s3":         C("2:16:48.10", iron, zoom=(1.16, 1.16), center=(0.42, 0.5), note="stutter"),
        "last":       C("0:01:29.00", iron, speed=0.5, zoom=(1.12, 1.18), center=(0.44, 0.5), note="the beams, slowing"),
        # drop
        "drop":       C("2:18:00.40", {**color, "exposure": -0.25}, note="the lights snap to beams"),
        "amber":      C("1:34:23.20", note="amber close · dancers whip past"),
        "98":         C("0:37:10.30", note="the '98' jerseys"),
        "kids":       C("0:55:35.30", zoom=(1.05, 1.08), note="kids, close, in coloured light"),
        "kidsgroup":  C("0:17:35.30", note="kids' group"),
        "lasers":     C("0:37:34.90", note="lasers over the crew"),
        "smile":      C("0:37:58.90", zoom=(1.08, 1.1), note="a grin under a cap"),
        "ramp":       C("1:35:59.00", speed=[(0, 1.3), (0.55, 0.28), (1.3, 0.28), (BAR, 1.4)], note="hair flip · speed ramp"),
        "redgroup":   C("1:27:58.90", zoom=(1.12, 1.14), center=(0.44, 0.5), note="red stage, the kids"),
        "kidsamber":  C("1:27:34.90", note="kids, close, amber"),
        "green":      C("1:58:19.00", zoom=(1.14, 1.16), center=(0.44, 0.5), note="green stage"),
        "floor":      C("0:09:35.40", note="floor work in amber haze"),
        "magenta":    C("1:31:40.30", zoom=(1.12, 1.14), center=(0.44, 0.5), note="magenta, the group"),
        "crowd":      C("2:18:20.00", zoom=(1.16, 1.18), center=(0.43, 0.5), note="yellow beams over the audience"),
        "freeze":     C("2:09:59.70", {**color, "exposure": 0.7}, speed=0.6, note="red solo · handstand → freeze"),
        # heart
        "hug":        C("2:26:03.00", silver, speed=0.5, zoom=(1.02, 1.08), note="the whole cast, one hug"),
        "faces":      C("0:47:11.30", silver, speed=0.5, zoom=(1.0, 1.05), note="faces"),
        "hoodies":    C("2:25:09.10", silver, speed=0.5, zoom=(1.3, 1.38), center=(0.47, 0.55), note="the District98 hoodies"),
        "celebrate":  C("2:26:40.00", silver, speed=0.6, zoom=(1.05, 1.12), note="the celebration"),
        # return
        "leap":       C("2:25:53.70", silver, speed=0.5, zoom=(1.04, 1.08), note="a leap in front of the whole cast"),
        "family":     C("2:24:03.90", silver, speed=0.5, zoom=(1.0, 1.06), note="the whole cast, clapping"),
    }
    clips["tri"] = [
        C("0:14:47.30", speed=0.8, zoom=(1.0, 1.03), center=(0.5, 0.5), note="close, purple"),
        C("0:42:45.90", speed=0.7, zoom=(1.0, 1.03), center=(0.45, 0.5), note="a dancer in white, haze"),
        C("1:34:49.20", speed=0.8, zoom=(1.2, 1.24), center=(0.55, 0.55), note="amber, the group"),
    ]
    return clips


def build(clips, w=1920, h=1080, fps=25):
    look = fx.Look(w, h, accent=brand.GOLD)
    tl = Timeline(w, h, fps, DURATION, look)
    for start, dur, key, extra in cuts():
        trans = extra.get("trans")
        if extra.get("triptych"):
            tl.add(Shot(start, dur, clips=clips[key], render=scenes.triptych, trans=trans))
        else:
            tl.add(Shot(start, dur, clip=clips[key], trans=trans,
                        **{k: v for k, v in extra.items() if k in ("punch", "flash", "freeze_at", "shake")}))

    close = (h / (h - w / 2.39)) + 0.02          # letterbox amount that meets in the middle

    def bars(t):
        if t < T_GAP:
            return 1.0
        if t < T_DROP:                            # the eyes close in the drum gap
            return 1 + (close - 1) * fx.ease_in(fx.window(t, T_GAP + 0.05, T_DROP - 0.04))
        if t < T_BREAK:                           # …and burst open on the drop
            return close * (1 - fx.expo_out(fx.window(t, T_DROP, T_DROP + 0.3)))
        if t < T_RETURN:
            return fx.ease_in_out(fx.window(t, T_BREAK, T_BREAK + 0.8))
        return 1 - fx.expo_out(fx.window(t, T_RETURN, T_RETURN + 0.35))
    tl.bars = bars

    def cinema_at(t):
        if t < T_DROP:
            return {"mono": 1.0, "streaks": 0.9, "halation": 0.7}
        if t < T_BREAK:
            return {"mono": 0.0, "streaks": 1.0, "halation": 1.0}
        if t < T_WHITE:
            return {"mono": 0.0, "streaks": 1.1, "halation": 1.1, "bloom": 1.1}
        return {"mono": 0.0, "streaks": 0.0, "halation": 0.0, "bloom": 0.0, "weave": 0.0}
    tl.cinema_at = cinema_at
    tl.grain_at = lambda t: 1.3 if t < T_DROP else (1.0 if t < T_WHITE else 0.45)
    tl.vignette_at = lambda t: 1.0 - 0.9 * fx.smoothstep(T_ZOOM + 0.4, T_WHITE, t)

    scenes.add_glyph_door(tl, 0.25, at(3) - 0.2, at(3), T_LAND)
    scenes.add_title_into_i(tl, TITLE, T_TITLE, T_WRITE, T_ZOOM, T_WHITE)
    scenes.add_paper_logo(tl, T_WHITE, T_MARK, DURATION)
    return tl


# ── sound ────────────────────────────────────────────────────────────────────
def logo_cues():
    """Clean tones for the logo, in the track's key (G minor): an open G–D fifth."""
    from afterfilm import score
    n = int(DURATION * score.SR)
    bus = np.zeros((n, 2))
    score._place(bus, score.sub(46, 28, 3.2, 0.26), T_WHITE)
    score._place(bus, score.bell(score.hz("G5"), 5.0, 0.085, ratio=2.0), T_WHITE + 0.02)
    score._place(bus, score.bell(score.hz("D6"), 5.0, 0.055, ratio=2.0), T_WHITE + 0.05)
    score._place(bus, score.shimmer(1.6, (score.hz("G6"), score.hz("D7"), score.hz("A6"), score.hz("G7")), 0.04),
                 T_WHITE + 0.2)
    score._place(bus, score.bell(score.hz("D5"), 4.0, 0.06, ratio=2.0), T_MARK)
    return score.reverb(bus, score.hall(3.2), 0.65).astype(np.float32)


def mix(music=True):
    from afterfilm.music import Track
    y = logo_cues()
    if music:
        track, _ = Track(MUSIC, MUSIC_BPM, MUSIC_T0).conform(MUSIC_SPANS, fade_in_bars=0.75, tail=DURATION)
        y = track * 0.9 + y[: len(track)]
    return (y / (np.abs(y).max() + 1e-9) * 0.89).astype(np.float32)


if __name__ == "__main__":
    import argparse
    import subprocess
    from afterfilm import media
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="renders/homecoming60.mp4")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--stills", nargs="*", type=float)
    ap.add_argument("--edl", action="store_true")
    a = ap.parse_args()
    W, H = int(1920 * a.scale) // 2 * 2, int(1080 * a.scale) // 2 * 2
    tl = build(footage_clips(), W, H)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    if a.edl:
        print(tl.edl())
    elif a.stills:
        print(tl.stills(a.stills, str(Path(a.out).with_suffix("")) + "_{t:05.2f}.png"))
    else:
        stem = str(Path(a.out).with_suffix(""))
        for tag, music in (("", True), ("_nomusic", False)):
            raw = f"{stem}{tag}.raw.wav"
            media.write_wav(raw, mix(music))
            subprocess.run([media.ffmpeg(), "-v", "error", "-y", "-i", raw, "-af",
                            "loudnorm=I=-14:TP=-1.0:LRA=11", "-ar", "48000", f"{stem}{tag}.wav"], check=True)
            Path(raw).unlink()
        tl.render(a.out, wav=f"{stem}.wav")
        subprocess.run([media.ffmpeg(), "-v", "error", "-y", "-i", a.out, "-i", f"{stem}_nomusic.wav", "-map", "0:v",
                        "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", f"{stem}_nomusic.mp4"], check=True)
