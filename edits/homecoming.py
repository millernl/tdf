"""HOMECOMING — the 30-second after-movie.

One structure, two casts: `animatic_clips()` fills it with labelled stand-in plates,
`footage_clips()` with moments picked from the live registration. Times are on a
120 BPM grid (0.5 s per beat) so cuts land on the music.

Idea: the District98 dancer glyph is the door. It writes itself, we fly through it
into the show — and at the end the show shrinks back into the glyph on '98 Green'.
The show comes home.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from afterfilm import brand, fx, gfx  # noqa: E402
from afterfilm.timeline import Clip, Shot, Timeline  # noqa: E402

CFG = {
    "title": "HOMECOMING",
    "presents": "DISTRICT98 PRESENTEERT",
    "subtitle": "THEATERSHOW  ·  DISTRICT98",
    "tagline": "Welkom thuis.",
    "url": "district98.nl",
    "labels": ("DISTRICT98", "HOMECOMING"),
    "accent": brand.GOLD,
}

# role, start, dur, transition-in, extras
CUTS = [
    ("open",    1.40, 2.60, None,             {}),               # through the glyph door
    ("atmos",   3.60, 1.80, ("stripes", .8),  {}),
    ("detail",  5.40, 1.60, ("swoosh", .7),   {}),
    ("solo",    7.00, 1.60, ("slit", .8),     {}),
    ("build",   8.60, 1.00, None,             {"punch": .06}),
    # 9.6–10.0 black: the breath before the drop
    ("drop",   10.00, 3.00, None,             {}),               # seen through the title, then full frame
    ("hit1",   13.00, 0.50, ("whip", .3),     {}),
    ("hit2",   13.50, 0.50, ("whip_l", .3),   {}),
    ("tri",    14.00, 1.60, None,             {"triptych": True}),
    ("freeze", 15.60, 1.00, None,             {"freeze_at": .5, "punch": .05}),
    ("hit3",   16.60, 0.50, None,             {"flash": .8}),
    ("hit4",   17.10, 0.50, None,             {"punch": .07}),
    ("hit5",   17.60, 0.60, ("swoosh_r", .4), {}),
    ("spin",   18.20, 1.40, None,             {"punch": .05}),
    ("hit6",   19.60, 0.60, ("stripes", .4),  {}),
    ("hit7",   20.20, 0.70, ("whip", .3),     {}),
    ("lift",   20.90, 1.30, None,             {"flash": .5}),
    ("finale", 22.20, 2.20, ("burn", .8),     {}),
    ("bow",    24.40, 4.10, ("burn", .6),     {}),               # shrinks into the glyph from 26.6
]

T_TITLE, T_ZOOM, T_FULL = 10.0, 11.35, 12.0
T_END, T_END_WHITE = 26.6, 27.55
DURATION = 30.0


def build(clips, w=1920, h=1080, fps=25, cfg=CFG):
    look = fx.Look(w, h, accent=cfg["accent"])
    tl = Timeline(w, h, fps, DURATION, look)
    for role, start, dur, trans, extra in CUTS:
        if extra.get("triptych"):
            tl.add(Shot(start, dur, clips=clips[role], render=_triptych, trans=trans))
        else:
            tl.add(Shot(start, dur, clip=clips[role], trans=trans,
                        **{k: v for k, v in extra.items() if k in ("punch", "flash", "freeze_at")}))

    # ── letterbox: scope for the story, full frame for the energy ──
    def bars(t):
        if t < T_ZOOM + 0.45:
            return 1.0
        if t < 21.7:
            return 1 - fx.expo_in_out(fx.window(t, T_ZOOM + 0.45, T_FULL + 0.3))
        if t < T_END:
            return fx.expo_in_out(fx.window(t, 21.7, 22.2))
        return 1 - fx.ease_in_out(fx.window(t, T_END, T_END + 0.6))
    tl.bars = bars

    shots_sorted = sorted(tl.shots, key=lambda s: s.start)

    def labels(t):
        spans = [(2.4, 11.6), (22.3, T_END - 0.2)]
        for a, b in spans:
            if a <= t < b + 0.2:
                p = fx.window(t, a, a + 0.6)
                alpha = 1 - fx.window(t, b, b + 0.2)
                cur = next((s for s in reversed(shots_sorted) if s.start <= t), None)
                clip = cur.all_clips()[0] if cur else None
                st = clip.src_time(t - cur.start) if clip else t
                tc = f"LIVE  {int(st // 3600):02d}:{int(st % 3600 // 60):02d}:{int(st % 60):02d}"
                strs = [s[: int(round(len(s) * p))] for s in (*cfg["labels"], tc)]
                return strs, alpha
        return None, 0.0
    tl.labels = labels

    # ── opening: the glyph writes itself, then becomes the door ──
    open_h = h * 0.2

    @tl.overlay(0.0, 2.6)
    def opening(t, img, tl):
        black = np.zeros_like(img)
        if t < 1.4:
            out = gfx.glyph_drawon(black, fx.window(t, 0.12, 1.25), w / 2, h / 2, open_h)
            tl.layer.clear()
            f = brand.font(brand.MONO, h * 0.0165)
            a = 1 - fx.window(t, 1.18, 1.38)
            gfx.typewriter(tl.layer.c, cfg["presents"], f, w / 2, h / 2 + open_h * 0.78,
                           fx.window(t, 0.5, 1.1), alpha=a, tracking=0.14, align="center")
            return tl.layer.over(out)
        u = fx.window(t, 1.4, 2.6)
        p = fx.ease_in(u) ** 0.8
        m = gfx.glyph_window(tl.mask, w, h, p, open_h, rot0=0.0)[..., None]
        v = fx.smoothstep(0.18, 0.5, u)                 # white ink turns into the show
        inside = (1 - v) + img * v
        return gfx.rim(black * (1 - m) + inside * m, m, 0.8 * (1 - u))

    # ── title: the show seen through the letters, then we fly through the I ──
    title_font = brand.font(brand.DISPLAY_THIN, h * 0.135)

    @tl.overlay(T_TITLE, T_FULL)
    def title(t, img, tl):
        track = 0.62 - 0.30 * fx.expo_out(fx.window(t, T_TITLE, T_TITLE + 1.0))
        path = gfx.text_path(cfg["title"], title_font, tracking=track)
        b = path.computeTightBounds()
        i_idx = cfg["title"].index("I")
        ib = gfx.text_path(cfg["title"][: i_idx + 1], title_font, tracking=track).computeTightBounds()
        pivot_x = ib.right() - title_font.getSize() * 0.035   # centre of the I stem
        pivot_y = (b.top() + b.bottom()) / 2
        z = fx.window(t, T_ZOOM, T_FULL)
        s = 1.0 * (90.0 ** (z ** 2.2))                  # exponential fly-through
        k = fx.smoothstep(0, 0.35, z)
        ax = (b.left() + b.right()) / 2 + (pivot_x - (b.left() + b.right()) / 2) * k
        n = len(cfg["title"])

        def draw(c, paint):
            c.translate(w / 2, h / 2)
            c.scale(s, s)
            c.translate(-ax, -pivot_y)
            # letters arrive one by one
            x = 0.0
            glyphs = title_font.textToGlyphs(cfg["title"])
            widths = title_font.getWidths(glyphs)
            for i, (g, gw) in enumerate(zip(glyphs, widths)):
                li = fx.window(t, T_TITLE + 0.05 * i, T_TITLE + 0.05 * i + 0.5)
                gp = title_font.getPath(g)
                if gp is not None and li > 0:
                    gp.offset(x, (1 - fx.expo_out(li)) * h * 0.02)
                    c.drawPath(gp, skia_paint(li))
                x += gw + track * title_font.getSize()

        m = tl.mask.draw(draw)[..., None]
        lifted = 1 - (1 - img) * (1 - 0.38 * (1 - z))   # lift the picture so the letters read
        out = gfx.rim(lifted * m, m, 0.55 * (1 - z))
        tl.layer.clear()
        if z < 0.05:
            sub = brand.font(brand.MONO, h * 0.0165)
            a = 1 - fx.window(t, T_ZOOM - 0.25, T_ZOOM)
            gfx.typewriter(tl.layer.c, cfg["subtitle"], sub, w / 2, h / 2 + b.height() * 0.5 + h * 0.07,
                           fx.window(t, T_TITLE + 0.45, T_TITLE + 1.0), alpha=a, tracking=0.14, align="center")
        return tl.layer.over(out)

    # ── triptych numbers + freeze caption ──
    @tl.overlay(14.0, 15.6, stage="post")
    def tri_labels(t, img, tl):
        tl.layer.clear()
        f = brand.font(brand.MONO, h * 0.0145)
        pw = w / 3
        for i in range(3):
            a = fx.window(t, 14.0 + 0.12 * i + 0.25, 14.0 + 0.12 * i + 0.55) * (1 - fx.window(t, 15.4, 15.6))
            gfx.text(tl.layer.c, f"0{i + 1}", f, pw * i + w * 0.02, h * 0.06, brand.WHITE, a, tracking=0.1)
        return tl.layer.over(img)

    @tl.overlay(16.1, 16.6, stage="post")
    def freeze_caption(t, img, tl):
        tl.layer.clear()
        c = tl.layer.c
        f = brand.font(brand.MONO, h * 0.0165)
        p = fx.window(t, 16.12, 16.4)
        x0, y = w * 0.06, h * 0.9
        c.drawRect(skia_rect(x0, y - h * 0.045, w * 0.22 * fx.expo_out(p), 1.5), skia_paint(1.0))
        gfx.typewriter(c, "Nº 01  ·  " + cfg["title"], f, x0, y, fx.window(t, 16.18, 16.45), tracking=0.12)
        return tl.layer.over(img)

    # ── tagline over the bows ──
    tag_font = brand.font(brand.DISPLAY_ITALIC, h * 0.062)

    @tl.overlay(24.8, T_END, stage="post")
    def tagline(t, img, tl):
        tl.layer.clear()
        p = fx.window(t, 24.9, 25.9)
        a = fx.smoothstep(0, 0.6, p) * (1 - fx.window(t, T_END - 0.35, T_END))
        gfx.text(tl.layer.c, cfg["tagline"], tag_font, w / 2, h * 0.7, brand.WHITE, a,
                 tracking=0.02 + 0.10 * (1 - fx.expo_out(p)), align="center")
        return tl.layer.over(img)

    # ── end: the show shrinks back into the glyph — home ──
    lock_h = h * 0.34
    lock_dy = -h * 0.035
    gcx, gcy, gh = gfx.lockup_glyph_box(w, h, lock_h, lock_dy)
    green = brand.f32(brand.GREEN)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    rad = np.sqrt(((xx - w / 2) / w) ** 2 + ((yy - h * 0.45) / h) ** 2)
    green_bg = (green * (1.12 - 0.35 * rad[..., None])).astype(np.float32)

    @tl.overlay(T_END, DURATION + 1, stage="post")
    def endcard(t, img, tl):
        u = fx.window(t, T_END, T_END + 1.3)
        p = 1 - fx.ease_out(u) ** 0.9
        m = gfx.glyph_window(tl.mask, w, h, p, gh, center=(gcx / w, gcy / h))[..., None]
        white = fx.smoothstep(0.0, 1.0, fx.window(t, T_END_WHITE, T_END_WHITE + 0.45))
        inside = img * (1 - white) + white
        out = gfx.rim(green_bg * (1 - m) + inside * m, m, 0.5 * (1 - white))
        tl.layer.clear()
        gfx.draw_wordmark(tl.layer.c, w, h, lock_h, fx.window(t, 28.15, 29.05), cy_offset=lock_dy)
        f = brand.font(brand.MONO, h * 0.02)
        gfx.typewriter(tl.layer.c, cfg["url"], f, w / 2, h / 2 + lock_h * 0.5 + lock_dy + h * 0.085,
                       fx.window(t, 28.95, 29.45), tracking=0.12, align="center", cursor=t < 29.9)
        return tl.layer.over(out)

    return tl


def _triptych(shot, lt, tl):
    w, h = tl.w, tl.h
    gap = int(h * 0.009)
    out = np.empty((h, w, 3), np.float32)
    out[:] = brand.f32(brand.GREEN) * 0.9
    pw = (w - 2 * gap) // 3
    for i, c in enumerate(shot.clips):
        e = fx.expo_out(fx.window(lt, 0.12 * i, 0.12 * i + 0.55))
        if e <= 0:
            continue
        img = c.buf.frame(c.src_time(lt))
        z = c.zoom[0] + (c.zoom[1] - c.zoom[0]) * lt / shot.dur
        panel = fx.reframe(img, z, c.center[0], c.center[1], out_size=(pw, h))
        panel = tl.look.grade(panel, **c.grade)
        panel = fx.shift(panel, dy=(1 - e) * h * 0.06)
        half = int(e * h / 2)
        x0 = i * (pw + gap)
        out[h // 2 - half: h // 2 + half, x0:x0 + pw] = panel[h // 2 - half: h // 2 + half]
    return out


def skia_paint(a):
    import skia
    return skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, 1, 1, float(a)))


def skia_rect(x, y, w, h):
    import skia
    return skia.Rect.MakeXYWH(x, y, w, h)


# ── sound ────────────────────────────────────────────────────────────────────
def sound(bed=None, cfg=CFG):
    """Sound design on the cut. `bed`: stereo music (the show's own audio, conformed to
    the edit); without one, a temp 120 BPM pulse stands in."""
    from afterfilm import sfx
    n = int(DURATION * sfx.SR)
    fxt = np.zeros((n, 2), np.float32)

    def ticks(t0, t1, chars, every=2):
        for k in range(0, chars, every):
            sfx.place(fxt, sfx.tick(), t0 + (t1 - t0) * k / chars)

    sfx.place(fxt, sfx.shimmer(1.3), 0.12)
    ticks(0.5, 1.1, len(cfg["presents"]))
    sfx.place(fxt, sfx.whoosh(1.2, 150, 5000, (0, 0), 0.55), 1.4)
    ticks(2.4, 3.0, 24, 3)
    for role, start, dur, trans, extra in CUTS:
        if trans:
            name, d = trans
            if name.startswith("whip"):
                w = sfx.whoosh(0.4, 600, 8000, (-0.8, 0.8) if name == "whip" else (0.8, -0.8), 0.5)
            elif name.startswith("swoosh"):
                w = sfx.whoosh(d * 1.1, 300, 4500, (-0.7, 0.7) if name == "swoosh" else (0.7, -0.7), 0.5)
            elif name == "burn":
                w = sfx.whoosh(d * 1.4, 120, 1200, (0, 0), 0.3)
            else:
                w = sfx.whoosh(d * 1.1, 400, 6000, (-0.3, 0.3), 0.4)
            sfx.place(fxt, w, start - 0.1)
        if extra.get("punch") or extra.get("flash"):
            sfx.place(fxt, sfx.sub_hit(0.6, 70, 45, 0.35), start)
        if extra.get("freeze_at") is not None:
            sfx.place(fxt, sfx.shutter(0.45), start + extra["freeze_at"])
    sfx.place(fxt, sfx.riser(1.0, 0.4), 9.0)
    sfx.place(fxt, sfx.sub_hit(1.8, 62, 32, 0.95), T_TITLE)
    ticks(T_TITLE + 0.45, T_TITLE + 1.0, len(cfg["subtitle"]), 3)
    sfx.place(fxt, sfx.whoosh(0.75, 200, 9000, (0, 0), 0.6), T_ZOOM)
    sfx.place(fxt, sfx.sub_hit(1.0, 60, 40, 0.6), T_FULL)
    ticks(22.3, 22.9, 24, 3)
    sfx.place(fxt, sfx.whoosh(1.3, 5000, 180, (0, 0), 0.45), T_END)
    sfx.place(fxt, sfx.shimmer(1.2, 0.2), T_END_WHITE)
    sfx.place(fxt, sfx.sub_hit(1.4, 55, 35, 0.45), 28.15)
    ticks(28.95, 29.45, len(cfg["url"]), 1)
    if bed is None:
        bed = sfx.pulse_bed(DURATION, 120, ((1.5, 9.5, 0.2), (T_TITLE, 21.9, 1.0), (22.2, 26.5, 0.35)))
    mix = bed[:n] * 0.8 + fxt
    # tail: fade everything out over the last second and a half
    fade = np.ones(n, np.float32)
    k = int(1.5 * sfx.SR)
    fade[-k:] = np.linspace(1, 0, k) ** 1.5
    return sfx.master(mix * fade[:, None])


# ── casts ────────────────────────────────────────────────────────────────────
def animatic_clips():
    from afterfilm.plates import PlateSource as P
    spec = {
        "open":   (P("S01", "opening tableau · backlit silhouettes", ("tungsten", "white"), 2, 5, 0.1, 1, 0.5), 0.5, (1.0, 1.08)),
        "atmos":  (P("S02", "wide · full stage in haze", ("cyan", "violet"), 4, 6, 0.2, 2), 0.8, (1.06, 1.0)),
        "detail": (P("S03", "close · hands / feet / fabric", ("amber",), 2, 1, 0.3, 3), 0.7, (1.1, 1.14)),
        "solo":   (P("S04", "solo · slow push-in", ("white", "violet"), 1, 1, 0.3, 4, 0.7), 0.6, (1.0, 1.1)),
        "build":  (P("S05", "formation builds", ("magenta", "cyan"), 3, 7, 0.5, 5), 1.0, (1.0, 1.03)),
        "drop":   (P("S06", "the drop · whole cast hits", ("white", "amber"), 5, 8, 1.0, 6, 0.8), 1.0, (1.04, 1.0)),
        "hit1":   (P("S07", "jump", ("magenta",), 3, 3, 1.0, 7), 1.0, (1.0, 1.0)),
        "hit2":   (P("S08", "turn", ("cyan",), 3, 2, 1.0, 8), 1.0, (1.0, 1.0)),
        "freeze": (P("S10", "peak of a leap → freeze", ("amber", "white"), 3, 3, 1.0, 10), 0.8, (1.0, 1.0)),
        "hit3":   (P("S11", "floor work", ("violet",), 2, 4, 0.9, 11), 1.0, (1.0, 1.0)),
        "hit4":   (P("S12", "faces · joy", ("tungsten",), 2, 2, 0.8, 12), 1.0, (1.1, 1.1)),
        "hit5":   (P("S13", "lift", ("magenta", "white"), 3, 3, 0.9, 13), 1.0, (1.0, 1.0)),
        "spin":   (P("S14", "spin · speed ramp", ("cyan", "white"), 3, 1, 1.0, 14), [(0, 1.6), (0.45, 0.3), (1.0, 0.3), (1.4, 1.6)], (1.0, 1.05)),
        "hit6":   (P("S15", "group canon", ("green", "white"), 4, 7, 0.9, 15), 1.0, (1.0, 1.0)),
        "hit7":   (P("S16", "audience reaction", ("tungsten",), 2, 0, 0.7, 16, 0.4, True), 1.0, (1.0, 1.0)),
        "lift":   (P("S17", "signature lift · slow-mo", ("white", "amber"), 3, 2, 0.8, 17), 0.5, (1.0, 1.06)),
        "finale": (P("S18", "finale tableau", ("tungsten", "amber", "white"), 5, 9, 0.3, 18, 0.8), 0.8, (1.0, 1.05)),
        "bow":    (P("S19", "bows · standing ovation", ("tungsten", "white"), 4, 9, 0.4, 19, 0.8), 1.0, (1.0, 1.04)),
    }
    clips = {k: Clip(src, 0.0, speed=sp, zoom=z, note=src.note) for k, (src, sp, z) in spec.items()}
    clips["tri"] = [Clip(P(f"S09.{i + 1}", "dancer close-up", (c,), 2, 1, 0.9, 90 + i), 0.0, note="dancer close-up")
                    for i, c in enumerate(("magenta", "amber", "cyan"))]
    return clips


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--animatic", action="store_true")
    ap.add_argument("--out", default="renders/homecoming.mp4")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--stills", nargs="*", type=float)
    a = ap.parse_args()
    W, H = int(1920 * a.scale) // 2 * 2, int(1080 * a.scale) // 2 * 2
    if not a.animatic:
        raise SystemExit("footage cast not picked yet — run the analysis on the show first (see README); "
                         "use --animatic for the stand-in version")
    tl = build(animatic_clips(), W, H)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    if a.stills:
        print(tl.stills(a.stills, str(Path(a.out).with_suffix("")) + "_{t:05.2f}.png"))
    else:
        from afterfilm import media
        wav = str(Path(a.out).with_suffix(".wav"))
        media.write_wav(wav, sound())
        tl.render(a.out, wav=wav)
