"""HOMECOMING — the after-movie, cut to the Iron arrangement (music/Iron_Homecoming_Edit.mp3).

The arrangement plays source bars 1–23 | 32 | 33–40 | 73–76 of Iron at 130 BPM: an eight-bar
drone, the drums at bar 9, the brass at bar 17, one build bar with the drum gap, the drop,
and the outro fill. Its last hit (bar 36, the "and" of 3) is where we arrive through the I;
the logo is written in the silence after.

  bars 1–8    drone. The glyph writes itself with the show inside; we fly through it.
              Home, in black & white: the silhouettes, a girl alone at the table, the
              bedroom, the window, hands pressing through a sheet.
  bars 9–16   the drums: silhouettes walking out, a singer turning away — and her head-turn
              matched by a silhouette's; the crew behind a girl with raised arms, a hair
              flip against the light, hair flying in grey haze, bowed heads, the cast in black.
  bars 17–23  the brass, and colour (still in scope): a sheet whipped through red, a girl
              pulled across the floor, arms up, the red beanie kids, the kids' crew, a solo
              in magenta, amber kids, two girls walking off with the glyph on their backs.
  bar 24      a line of dancers stares down the lens; in the drum gap the frame closes.
  bars 25–32  the drop bursts open: the lights snap to beams, the cast explodes out of the
              haze, jerseys, the light snaps to red, a powermove in light trails, a triptych
              of hair in three colours, lasers, amber, the crew in D98 shirts — and a
              handstand that freezes as the drums fall away.
  bars 33–36  the whole cast in one embrace; HOMECOMING is written over it; on the last hit
              we're through the I and onto a white page.
  after       silence. The glyph written in '98 Green', the wordmark in ink.
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
MUSIC = ROOT / "music" / "Iron_Homecoming_Edit.mp3"
MUSIC_T0 = 0.020          # first downbeat in the file (measured); trimmed so bar n starts at at(n)
MUSIC_GAIN_DB = -1.5      # the mix peaks at +0.3 dBFS; a static trim keeps it clean, dynamics untouched

TITLE = "HOMECOMING"
T_LAND = 3.85             # through the glyph door
T_DRUMS = at(9)
T_COLOR = at(17)          # the brass — colour arrives
T_GAP = at(24, 2)         # the drums hold their breath
T_DROP = at(25)
T_OUTRO = at(33)
T_TITLE = at(34, 2)
T_WRITE = at(35)
T_ZOOM = at(36)
T_WHITE = at(36, 2.5)     # the arrangement's last hit
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

    def pair(bar, a, b, **extra):                    # two shots, a half bar each
        add(at(bar), g(2), a, **extra)
        add(at(bar, 2), g(2), b)

    # drone — home
    add(0.20, at(5) - 0.20, "open")
    add(at(5), BAR, "table")
    add(at(6), BAR, "bedroom")
    add(at(7), BAR, "window")
    add(at(8), BAR, "hands")
    # drums — the journey
    add(at(9), BAR, "walk", shake=0.5)
    add(at(10), BAR, "singer")
    add(at(11), BAR, "silhouette")
    add(at(12), BAR, "arms")
    add(at(13), BAR, "blonde")
    add(at(14), BAR, "greyhair")
    add(at(15), BAR, "bowed")
    add(at(16), BAR, "blackcast")
    # brass — colour
    add(at(17), BAR, "sheet", flash=0.25)
    pair(18, "pulled", "armsup")
    add(at(19), BAR, "beanies")
    pair(20, "kidscrew", "ambercrew")
    add(at(21), BAR, "magenta")
    add(at(22), BAR, "amberkids")
    add(at(23), BAR, "glyphbacks")
    add(at(24), BAR, "stare")                        # the frame closes on this
    # drop
    add(T_DROP, BAR, "drop", flash=0.45, shake=1.0)
    add(at(26), BAR, "explode", shake=0.6)
    pair(27, "jerseys", "redlight")
    add(at(28), BAR, "trails")
    add(at(29), BAR, "tri", triptych=True)
    pair(30, "lasers", "amber")
    pair(31, "d98crew", "lunge")
    add(at(32), BAR, "freeze", freeze_at=g(2))
    # outro — one embrace, the title, the I
    add(T_OUTRO, T_WHITE - T_OUTRO + 0.05, "hug", trans=("dip", 0.7))
    return C


def footage_clips(path=SHOW):
    src = VideoSource(str(path))
    iron, color, silver = {"look": "iron"}, {"look": "color"}, {"look": "silver"}

    def C(t, look=color, **k):
        return Clip(src, tc(t), grade=dict(look), **k)

    clips = {
        # drone
        "open":       C("0:00:07.30", iron, speed=0.4, zoom=(1.0, 1.08), note="silhouettes walk out of the haze"),
        "table":      C("1:05:35.90", iron, speed=0.6, zoom=(1.04, 1.12), note="a girl alone at the table"),
        "bedroom":    C("1:31:03.20", iron, speed=0.7, zoom=(1.38, 1.46), center=(0.5, 0.56), note="the bedroom, three girls"),
        "window":     C("1:20:59.30", iron, speed=0.75, zoom=(1.0, 1.12), center=(0.5, 0.45), note="the projected window of a home"),
        "hands":      C("1:15:04.60", iron, speed=0.7, zoom=(1.1, 1.18), note="hands pressing through a sheet"),
        # drums
        "walk":       C("1:23:59.30", iron, speed=0.7, zoom=(1.0, 1.05), note="silhouettes in caps, walking"),
        "singer":     C("1:47:39.00", iron, speed=0.8, zoom=(1.0, 1.06), note="a singer turns away"),
        "silhouette": C("1:23:07.30", iron, speed=0.8, zoom=(1.0, 1.06), note="a silhouette turns her head"),
        "arms":       C("1:24:06.48", iron, speed=0.8, zoom=(1.0, 1.05), note="the crew raises its arms behind her"),
        "blonde":     C("1:08:29.90", {**iron, "exposure": -0.7}, speed=0.8, zoom=(1.0, 1.04), note="a hair flip against the light"),
        "greyhair":   C("2:15:08.44", iron, speed=0.8, zoom=(1.06, 1.1), note="hair flying in grey haze"),
        "bowed":      C("1:22:50.30", iron, speed=0.7, zoom=(1.0, 1.05), note="a row of bowed heads"),
        "blackcast":  C("1:13:59.30", iron, speed=0.8, note="the cast in black, hair flying"),
        # brass
        "sheet":      C("1:16:00.70", speed=0.8, zoom=(1.0, 1.05), note="a sheet whipped through red"),
        "pulled":     C("0:42:09.58", note="a girl pulled across the floor"),
        "armsup":     C("0:43:49.70", note="arms up, white shirts"),
        "beanies":    C("0:40:09.50", speed=0.9, note="the red beanie kids"),
        "kidscrew":   C("0:17:35.70", note="the kids' crew"),
        "ambercrew":  C("1:56:05.40", note="amber, the crew in white"),
        "magenta":    C("1:33:16.50", speed=0.8, zoom=(1.0, 1.04), note="a solo in magenta"),
        "amberkids":  C("1:28:44.00", speed=0.8, zoom=(1.0, 1.04), note="amber, kids close"),
        "glyphbacks": C("2:06:42.40", {**color, "exposure": 0.8}, speed=0.8, zoom=(1.0, 1.05), note="two girls walk off, the glyph on their backs"),
        "stare":      C("1:06:35.80", speed=0.7, zoom=(1.0, 1.06), note="a line of dancers stares down the lens"),
        # drop
        "drop":       C("2:18:00.40", {**color, "exposure": -0.25}, note="the lights snap to beams"),
        "explode":    C("1:09:50.90", speed=0.8, note="the cast explodes out of the haze"),
        "jerseys":    C("0:36:48.42", note="close · the crew in jerseys, green light"),
        "redlight":   C("1:09:27.25", {**color, "exposure": 0.6}, speed=0.9, note="the light snaps to red over the cast"),
        "trails":     C("2:09:46.90", {**color, "exposure": 1.0}, speed=0.6, echo=1.0, note="powermove in light trails"),
        "lasers":     C("0:37:34.90", note="lasers over the crew"),
        "amber":      C("1:34:23.20", note="amber close · dancers whip past"),
        "d98crew":    C("2:07:05.00", note="the crew turns, D98 on their shirts"),
        "lunge":      C("2:07:21.80", note="a lunge into the lens"),
        "freeze":     C("2:09:59.70", {**color, "exposure": 0.7}, speed=0.6, note="red solo · handstand → freeze"),
        # outro
        "hug":        C("2:26:03.00", silver, speed=0.5, zoom=(1.02, 1.1), note="the whole cast, one embrace"),
    }
    clips["tri"] = [
        C("2:08:12.65", {**color, "exposure": 0.6}, speed=0.42, zoom=(1.05, 1.08), center=(0.34, 0.5),
          center_end=(0.3, 0.58), note="hair whipped in purple"),
        C("1:10:14.30", speed=0.8, zoom=(1.0, 1.02), center=(0.5, 0.5), note="a hair flip in white haze"),
        C("0:43:05.40", speed=0.8, zoom=(1.05, 1.08), center=(0.45, 0.5), center_end=(0.5, 0.5),
          note="a hair whirl in violet"),
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
        return close * (1 - fx.expo_out(fx.window(t, T_DROP, T_DROP + 0.3)))
    tl.bars = bars

    def cinema_at(t):
        if t < T_COLOR:
            return {"mono": 1.0, "streaks": 0.9, "halation": 0.7}
        if t < T_WHITE:
            return {"mono": 0.0, "streaks": 1.05, "halation": 1.05, "bloom": 1.05}
        return {"mono": 0.0, "streaks": 0.0, "halation": 0.0, "bloom": 0.0, "weave": 0.0}
    tl.cinema_at = cinema_at
    tl.grain_at = lambda t: 1.3 if t < T_COLOR else (1.0 if t < T_WHITE else 0.45)
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
            a = c.src_time(0) - 0.04 - (5 * 0.07 if c.echo else 0.0)
            b = c.src_time(min(dur + handle, extra["freeze_at"]) if "freeze_at" in extra else dur + handle)
            mx, at_t, flagged = analyze.frame_cuts(str(SHOW), a, b + 0.04)
            bad += bool(flagged)
            name = f"{key}{'.' + str(j + 1) if len(cs) > 1 else ''}"
            print(f"{'CUT?' if flagged else 'ok  '} {name:10s} src {analyze.tc(a)}–{analyze.tc(b)}  max {mx:.2f} "
                  f"@ {analyze.tc(at_t)}" + (f"  flagged {[analyze.tc(x) for x in flagged]}" if flagged else ""))
    print(f"{bad} clip(s) flagged")


def mix():
    """The arrangement as delivered: first downbeat trimmed onto the grid, a static
    level trim, silence after the last hit rings out."""
    from afterfilm import media
    y = media.read_audio(str(MUSIC), t_in=MUSIC_T0, dur=DURATION, sr=48000, channels=2)
    n = int(round(DURATION * 48000))
    y = np.concatenate([y, np.zeros((max(0, n - len(y)), 2), np.float32)])[:n]
    return (y * 10 ** (MUSIC_GAIN_DB / 20)).astype(np.float32)


if __name__ == "__main__":
    import argparse
    from afterfilm import media
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="renders/homecoming_final.mp4")
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
        wav = str(Path(a.out).with_suffix(".wav"))
        media.write_wav(wav, mix())
        tl.render(a.out, wav=wav)
