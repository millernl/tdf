"""HOMECOMING — the one-minute after-movie, cut to the Iron mix.

The music is conformed on its 130 BPM bar grid to 32 bars — source bars 5–12 | 17–20 |
31–36 | 39–48 | 73–76, every splice on a downbeat — so the track's whole outro fill
plays out before its hard stop at 59.08 s. The logo is written in the silence after.
The drums play a 3-3-2 gallop (1 · 2& · 4); the fast sections cut on it.

  bars 1–4    drone. The glyph writes itself with the show inside; we fly through it and
              stay with the silhouettes walking out of the haze.
  bars 5–8    the drums. Home, in black & white: a girl alone at the table, the bedroom,
              the window, hands pressing through a sheet.
  bars 9–12   the journey: walking silhouettes, a singer turning away, the spotlight ring.
  bars 13–14  the build on the gallop; a stutter; in the drum gap the frame closes to black.
  bars 15–20  the drop bursts open in colour. Jerseys, kids, a triptych of three solos, a
              speed ramp — and a handstand that freezes as the drums fall away.
  bars 21–24  the heart: the whole-cast hug, faces, two voices, the District98 hoodies.
  bars 25–28  the return: the cast explodes out of the haze, a powermove in light trails,
              the audience on its feet.
  bars 29–32  the outro fill: the whole cast clapping; HOMECOMING is written over them;
              we fly into the I, onto a white page.
  59.1–62.3   silence. The glyph written in '98 Green', the wordmark in ink.
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
MUSIC_SPANS = [(5, 12), (17, 20), (31, 36), (39, 48), (73, 76)]

TITLE = "HOMECOMING"
T_LAND = 3.85             # through the glyph door
T_GAP = at(14, 2)         # the drums hold their breath
T_DROP = at(15)
T_BREAK = at(21)
T_RETURN = at(25)
T_OUTRO = at(29)
T_TITLE = at(30)
T_WRITE = at(30, 2)
T_ZOOM = at(32, 2)
T_WHITE = at(33)          # the music's hard stop
T_MARK = T_WHITE + 1.15
DURATION = T_WHITE + 3.2


def tc(s):
    v = 0.0
    for x in s.split(":"):
        v = v * 60 + float(x)
    return v


def g(n=1.0):
    return n * BEAT


def cuts():
    """(record start, duration, clip key, extras). Keys map to footage_clips()."""
    C = []

    def add(start, dur, key, **extra):
        C.append((start, dur, key, extra))

    def gallop(bar, keys, **extra):                 # 1 · 2& · 4
        add(at(bar), g(1.5), keys[0], **extra)
        add(at(bar, 1.5), g(1.5), keys[1])
        add(at(bar, 3), g(1), keys[2])

    # drone
    add(0.20, at(5) - 0.20, "open")
    # drums — home
    add(at(5), BAR, "table")
    add(at(6), BAR, "bedroom")
    add(at(7), BAR, "window")
    add(at(8), BAR, "hands")
    # brass — the journey
    add(at(9), BAR, "walk")
    add(at(10), BAR, "singer")
    add(at(11), g(1.5), "spot")
    add(at(11, 1.5), g(2.5), "beams")
    gallop(12, ("mound", "crowdpov", "pile"))
    # build
    gallop(13, ("rise", "lonely", "hairblack"))
    add(at(14), g(0.5), "s1")
    add(at(14, 0.5), g(1), "s2")
    add(at(14, 1.5), g(0.5), "s3")
    add(at(14, 2), g(2), "last")                         # the frame closes on this
    # drop
    add(T_DROP, BAR, "drop", flash=0.45, shake=1.0)
    gallop(16, ("rail", "98", "kids"))
    add(at(17), BAR, "tri", triptych=True)
    gallop(18, ("kidsgroup", "pink", "smile"))
    add(at(19), BAR, "ramp", flash=0.35)
    add(at(20), BAR, "freeze", freeze_at=g(2))
    # the heart
    add(T_BREAK, BAR, "hug", trans=("dip", 0.9))
    add(at(22), BAR, "faces")
    add(at(23), BAR, "voices")
    add(at(24), BAR, "hoodies")
    # the return
    add(T_RETURN, BAR, "explode", shake=0.8, flash=0.3)
    add(at(26), g(2), "jerseys")
    add(at(26, 2), g(2), "redlight")
    add(at(27), g(2), "trails")
    add(at(27, 2), g(2), "lasers")
    gallop(28, ("amber", "redkids", "audience"))
    # the outro: one shot, the title, the I
    add(T_OUTRO, T_WHITE - T_OUTRO + 0.05, "family")
    return C


def footage_clips(path=SHOW):
    src = VideoSource(str(path))
    steady = VideoSource(str(path), extra_pre="tmedian=radius=2")   # finale strobe removed
    iron, color, silver = {"look": "iron"}, {"look": "color"}, {"look": "silver"}

    def C(t, look=color, source=None, **k):
        return Clip(source or src, tc(t), grade=dict(look), **k)

    ramp = [(0, 1.3), (0.55, 0.28), (1.3, 0.28), (BAR, 1.4)]
    clips = {
        # drone
        "open":      C("0:00:07.30", iron, speed=0.4, zoom=(1.0, 1.08), note="silhouettes walk out of the haze"),
        # home
        "table":     C("1:05:35.90", iron, speed=0.6, zoom=(1.04, 1.12), note="a girl alone at the table"),
        "bedroom":   C("1:31:03.20", iron, speed=0.7, zoom=(1.38, 1.46), center=(0.5, 0.56), note="the bedroom, three girls"),
        "window":    C("1:20:59.30", iron, speed=0.75, zoom=(1.0, 1.12), center=(0.5, 0.45), note="the projected window of a home"),
        "hands":     C("1:15:04.60", iron, speed=0.7, zoom=(1.1, 1.18), note="hands pressing through a sheet"),
        # journey
        "walk":      C("1:23:59.30", iron, speed=0.7, zoom=(1.0, 1.05), note="silhouettes in caps, walking"),
        "singer":    C("1:47:39.00", iron, speed=0.8, zoom=(1.0, 1.06), note="a singer turns away"),
        "spot":      C("0:28:08.60", iron, speed=0.8, zoom=(1.05, 1.0), note="breaker in the spotlight ring"),
        "beams":     C("1:39:39.00", iron, zoom=(1.0, 1.03), note="white beams, three silhouettes"),
        "mound":     C("1:15:44.55", iron, speed=0.8, zoom=(1.0, 1.04), note="bodies under a white sheet"),
        "crowdpov":  C("1:22:25.30", iron, speed=0.9, zoom=(1.0, 1.04), note="seen over the audience's heads"),
        "pile":      C("2:13:29.00", iron, zoom=(1.12, 1.14), note="bodies piled in the spotlight"),
        # build
        "rise":      C("1:06:55.50", iron, speed=0.8, note="close · the group rises"),
        "lonely":    C("2:10:35.00", {**iron, "exposure": 0.9}, speed=0.8, zoom=(1.0, 1.03), note="the soloist, hand to his head"),
        "hairblack": C("1:06:22.85", iron, note="close · hair in black"),
        "s1":        C("1:08:30.40", iron, note="stutter · hair flip against the light"),
        "s2":        C("0:01:53.20", iron, zoom=(1.2, 1.2), center=(0.41, 0.5), note="stutter · opening number"),
        "s3":        C("2:10:17.30", iron, note="stutter · the soloist in a split"),
        "last":      C("0:01:29.00", iron, speed=0.5, zoom=(1.12, 1.18), center=(0.44, 0.5), note="the beams, slowing"),
        # drop
        "drop":      C("2:18:00.40", {**color, "exposure": -0.25}, note="the lights snap to beams"),
        "rail":      C("1:09:01.10", note="the group surges, dancers on the rail"),
        "98":        C("0:37:10.30", note="the '98' jerseys"),
        "kids":      C("0:55:35.30", zoom=(1.05, 1.08), note="kids, close, in coloured light"),
        "kidsgroup": C("0:17:35.70", note="kids' group"),
        "pink":      C("1:31:48.62", note="three dancers in pink light"),
        "smile":     C("0:37:58.90", zoom=(1.08, 1.1), note="a grin under a cap"),
        "ramp":      C("1:35:59.00", speed=ramp, note="hair flip · speed ramp"),
        "freeze":    C("2:09:59.70", {**color, "exposure": 0.7}, speed=0.6, note="red solo · handstand → freeze"),
        # heart
        "hug":       C("2:26:03.00", silver, speed=0.5, zoom=(1.02, 1.08), note="the whole cast, one hug"),
        "faces":     C("0:47:11.30", silver, speed=0.5, zoom=(1.0, 1.05), note="faces"),
        "voices":    C("1:43:17.50", silver, speed=0.6, zoom=(1.0, 1.05), note="two singers, face to face"),
        "hoodies":   C("2:25:09.10", silver, speed=0.5, zoom=(1.3, 1.38), center=(0.47, 0.55), note="the District98 hoodies"),
        # return
        "explode":   C("1:09:50.90", speed=0.8, note="the cast explodes out of the haze"),
        "jerseys":   C("0:36:48.42", note="close · the crew in jerseys, green light"),
        "redlight":  C("1:09:27.25", {**color, "exposure": 0.6}, speed=0.9, note="the light snaps to red over the cast"),
        "trails":    C("2:09:46.90", {**color, "exposure": 1.0}, speed=0.6, echo=1.0, note="powermove in light trails"),
        "lasers":    C("0:37:34.90", note="lasers over the crew"),
        "amber":     C("1:34:23.20", note="amber close · dancers whip past"),
        "redkids":   C("1:27:58.90", zoom=(1.12, 1.14), center=(0.44, 0.5), note="red stage, the kids"),
        "audience":  C("2:18:20.00", zoom=(1.16, 1.18), center=(0.43, 0.5), note="yellow beams over the audience"),
        # outro
        "family":    C("2:24:03.90", silver, source=steady, speed=0.5, zoom=(1.0, 1.06), note="the whole cast, clapping"),
    }
    clips["tri"] = [
        C("2:11:02.90", speed=0.8, zoom=(1.0, 1.02), center=(0.45, 0.5), note="the soloist, upside down"),
        C("1:16:00.40", speed=0.8, zoom=(1.0, 1.02), center=(0.40, 0.6), center_end=(0.52, 0.6), note="a sheet whipped through red"),
        C("1:10:14.30", speed=0.8, zoom=(1.0, 1.02), center=(0.5, 0.5), note="a hair flip in white haze"),
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
        if t < T_WHITE:
            return {"mono": 0.0, "streaks": 1.05, "halation": 1.05, "bloom": 1.05}
        return {"mono": 0.0, "streaks": 0.0, "halation": 0.0, "bloom": 0.0, "weave": 0.0}
    tl.cinema_at = cinema_at
    tl.grain_at = lambda t: 1.3 if t < T_DROP else (1.0 if t < T_WHITE else 0.45)
    tl.vignette_at = lambda t: 1.0 - 0.9 * fx.smoothstep(T_ZOOM + 0.4, T_WHITE, t)

    scenes.add_glyph_door(tl, 0.30, 2.45, 2.55, T_LAND)
    scenes.add_title_into_i(tl, TITLE, T_TITLE, T_WRITE, T_ZOOM, T_WHITE)
    scenes.add_paper_logo(tl, T_WHITE, T_MARK, DURATION)
    return tl


def verify(clips):
    """Scan every clip's source range frame by frame for camera cuts / stray frames."""
    from afterfilm import analyze
    C = cuts()
    bad = 0
    for i, (start, dur, key, extra) in enumerate(C):
        nxt = C[i + 1] if i + 1 < len(C) else None
        handle = nxt[3].get("trans", (None, 0.0))[1] if nxt else 0.0
        cs = clips[key] if isinstance(clips[key], list) else [clips[key]]
        for j, c in enumerate(cs):
            a = c.src_time(0) - 0.04
            b = c.src_time(min(dur + handle, extra.get("freeze_at", 1e9) if "freeze_at" in extra else dur + handle))
            if c.echo:
                a -= 5 * 0.07
            mx, at_t, flagged = analyze.frame_cuts(str(SHOW), a, b + 0.04)
            tag = "CUT?" if flagged else "ok  "
            bad += bool(flagged)
            name = f"{key}{'.' + str(j + 1) if len(cs) > 1 else ''}"
            print(f"{tag} {name:10s} src {analyze.tc(a)}–{analyze.tc(b)}  max {mx:.2f} @ {analyze.tc(at_t)}"
                  + (f"  flagged {[analyze.tc(x) for x in flagged]}" if flagged else ""))
    print(f"{bad} clip(s) flagged")


# ── sound ────────────────────────────────────────────────────────────────────
def logo_cues():
    """The logo's voice, low and soft: a deep breath of sub and a warm G-minor pad in
    the silence after the stop, a felt thud as the wordmark lands. Nothing above ~900 Hz."""
    from scipy import signal
    from afterfilm import score
    n = int(DURATION * score.SR)
    bus = np.zeros((n, 2))
    score._place(bus, score.sub(44, 27, 3.4, 0.30), T_WHITE)
    score._place(bus, score.brass(["G1", "D2", "G2"], 2.4, attack=0.06, release=1.9, bright=(90, 360),
                                  vib=0.0, gain=0.26), T_WHITE)
    score._place(bus, score.taiko(56, 38, 0.45, skin=0.04), T_MARK, 0.22)
    wet = score.reverb(bus, score.hall(3.0), 0.45)
    sos = signal.butter(4, 900 / (score.SR / 2), output="sos")
    return signal.sosfilt(sos, wet, axis=0).astype(np.float32)


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
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    W, H = int(1920 * a.scale) // 2 * 2, int(1080 * a.scale) // 2 * 2
    clips = footage_clips()
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
        stem = str(Path(a.out).with_suffix(""))
        for tag, music in (("", True), ("_nomusic", False)):
            raw = f"{stem}{tag}.raw.wav"
            media.write_wav(raw, mix(music))
            subprocess.run([media.ffmpeg(), "-v", "error", "-y", "-i", raw, "-af",
                            "loudnorm=I=-14:TP=-1.0:LRA=11", "-ar", "48000", f"{stem}{tag}.wav"], check=True)
            Path(raw).unlink()
        tl.render(a.out, wav=f"{stem}.wav")
        subprocess.run([media.ffmpeg(), "-v", "error", "-y", "-i", a.out, "-i", f"{stem}_nomusic.wav", "-map", "0:v",
                        "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart",
                        f"{stem}_nomusic.mp4"], check=True)
