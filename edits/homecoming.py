"""HOMECOMING — the 30-second after-movie.

Cut on a 130 BPM grid (0.4615 s a beat, 1.846 s a bar), scored like Woodkid's 'Iron'.

  bars 1–2   the dancer glyph writes itself with the show inside it, then becomes the door
  bars 3–6   the story, in high-contrast black & white, scope letterbox
  bars 7–12  the drop: colour floods in, frame opens to 16:9, cuts on the beat,
             triptych, a freeze that stops the music, a speed ramp
  bars 13–14 the heart: warm gold, the whole cast, frame closes again
  bars 15–17 HOMECOMING over the cast → fly into the I → it turns '98 Green' →
             the logo writes itself. No text but the title; no new shots after it.
"""
import sys
from pathlib import Path

import cv2
import numpy as np
import skia

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from afterfilm import brand, fx, gfx  # noqa: E402
from afterfilm.score import BAR, BEAT, at  # noqa: E402
from afterfilm.timeline import Clip, Shot, Timeline, VideoSource  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SHOW = ROOT / "footage" / "HOMECOMING.2026.PVT.mp4"
TITLE = "HOMECOMING"
DURATION = 30.0

T_LAND = at(3)          # through the glyph door
T_DROP = at(7)          # colour
T_HEART = at(13)        # gold
T_TITLE = at(15)        # HOMECOMING
T_ZOOM = at(16) - 1.5 * BEAT
T_GREEN = at(16)        # inside the I: '98 Green'
T_MARK = at(16, 2)      # wordmark


def tc(s):
    v = 0.0
    for x in s.split(":"):
        v = v * 60 + float(x)
    return v


# role, record start, record duration, transition-in, extras
CUTS = [
    ("open",   0.25,        at(4) - 0.25, None,              {}),
    ("spot",   at(4),       BAR,          ("stripes", BEAT), {}),
    ("table",  at(5),       2 * BEAT,     None,              {}),
    ("rise",   at(5, 2),    2 * BEAT,     None,              {}),
    ("beams",  at(6),       2 * BEAT,     ("slit", BEAT),    {}),
    ("pile",   at(6, 2),    BEAT,         None,              {}),
    ("hair",   at(6, 3),    BEAT,         None,              {}),
    ("drop",   T_DROP,      2 * BEAT,     None,              {"flash": 0.55}),
    ("amber",  at(7, 2),    2 * BEAT,     None,              {}),
    ("98",     at(8),       2 * BEAT,     None,              {"punch": 0.035}),
    ("cast",   at(8, 2),    2 * BEAT,     None,              {}),
    ("tri",    at(9),       BAR,          None,              {"triptych": True}),
    ("freeze", at(10),      BAR,          None,              {"freeze_at": 2 * BEAT}),
    ("ramp",   at(11),      BAR,          None,              {"flash": 0.5}),
    ("floor",  at(12),      BEAT,         None,              {}),
    ("green",  at(12, 1),   BEAT,         None,              {}),
    ("smile",  at(12, 2),   BEAT,         None,              {}),
    ("crowd",  at(12, 3),   BEAT,         None,              {}),
    ("leap",   T_HEART,     BAR,          ("burn", 0.6),     {}),
    ("family", at(14),      T_GREEN - at(14) + 0.1, ("burn", 0.9), {}),
]


def footage_clips(path=SHOW):
    src = VideoSource(str(path))
    iron = {"look": "iron"}
    color = {"look": "color"}
    gold = {"look": "gold"}

    def C(t, **k):
        return Clip(src, tc(t), **k)

    clips = {
        # the story — black & white
        "open":   C("0:00:07.30", speed=0.5, zoom=(1.0, 1.06), grade=iron, note="opening number · silhouettes walk out of the haze"),
        "spot":   C("0:28:08.60", speed=0.8, zoom=(1.04, 1.0), grade=iron, note="breaker in the spotlight ring"),
        "table":  C("1:05:35.90", speed=0.7, zoom=(1.06, 1.1), grade=iron, note="girl alone at the dinner table"),
        "rise":   C("1:06:55.50", speed=0.8, grade=iron, note="close · the group rises"),
        "beams":  C("1:39:39.00", speed=1.0, zoom=(1.0, 1.03), grade=iron, note="white beams, three silhouettes"),
        "pile":   C("2:13:29.00", speed=1.0, zoom=(1.12, 1.14), grade=iron, note="bodies piled in the spotlight"),
        "hair":   C("1:13:59.60", speed=1.0, grade=iron, note="cast in black, hair flying"),
        # the drop — colour
        "drop":   C("2:18:00.40", speed=1.0, grade={**color, "exposure": -0.25}, note="the lights snap to beams"),
        "amber":  C("1:34:23.20", speed=1.0, grade=color, note="amber close · dancers whip past"),
        "98":     C("0:37:10.30", speed=1.0, grade=color, note="the '98' jerseys"),
        "cast":   C("1:14:09.00", speed=1.0, grade=color, note="cast in black, full out"),
        "freeze": C("2:09:59.70", speed=0.6, grade={**color, "exposure": 0.7}, note="red solo · handstand → freeze"),
        "ramp":   C("1:35:59.00", speed=[(0, 1.3), (0.55, 0.28), (1.3, 0.28), (BAR, 1.4)], grade=color,
                    note="hair flip · speed ramp"),
        "floor":  C("0:09:35.40", speed=1.0, grade=color, note="floor work in amber haze"),
        "green":  C("1:58:19.00", speed=1.0, zoom=(1.14, 1.16), center=(0.44, 0.5), grade=color, note="green stage"),
        "smile":  C("0:37:58.90", speed=1.0, zoom=(1.08, 1.1), grade=color, note="a grin under a cap"),
        "crowd":  C("2:18:20.00", speed=1.0, zoom=(1.16, 1.18), center=(0.43, 0.5), grade=color, note="yellow beams over the audience"),
        # the heart — gold
        "leap":   C("2:25:53.70", speed=0.5, zoom=(1.04, 1.08), grade=gold, note="a leap in front of the whole cast"),
        "family": C("2:24:03.90", speed=0.5, zoom=(1.0, 1.05), grade=gold, note="the whole cast, clapping"),
    }
    clips["tri"] = [
        C("2:10:47.00", speed=0.8, zoom=(1.0, 1.02), center=(0.55, 0.5), grade=color, note="red solo, close"),
        C("0:48:43.30", speed=0.8, zoom=(1.0, 1.02), center=(0.5, 0.5), grade=color, note="dancers in white"),
        C("2:16:47.00", speed=0.8, zoom=(1.0, 1.02), center=(0.45, 0.5), grade=color, note="silhouettes on orange"),
    ]
    return clips


def build(clips, w=1920, h=1080, fps=25):
    look = fx.Look(w, h, accent=brand.GOLD)
    tl = Timeline(w, h, fps, DURATION, look)
    for role, start, dur, trans, extra in CUTS:
        if extra.get("triptych"):
            tl.add(Shot(start, dur, clips=clips[role], render=_triptych, trans=trans))
        else:
            tl.add(Shot(start, dur, clip=clips[role], trans=trans,
                        **{k: v for k, v in extra.items() if k in ("punch", "flash", "freeze_at")}))

    def bars(t):
        if t < T_DROP:
            return 1.0
        if t < T_HEART:
            return 1 - fx.expo_out(fx.window(t, T_DROP, T_DROP + 0.35))
        if t < T_ZOOM:
            return fx.ease_in_out(fx.window(t, T_HEART, T_HEART + 0.7))
        return 1 - fx.ease_in(fx.window(t, T_ZOOM + 0.2, T_GREEN))
    tl.bars = bars

    def cinema_at(t):
        if t < T_DROP:
            return {"mono": 1.0, "streaks": 0.9, "halation": 0.7}
        if t < T_HEART:
            return {"mono": 0.0, "streaks": 1.0, "halation": 1.0}
        if t < T_GREEN:
            return {"mono": 0.0, "streaks": 1.2, "halation": 1.3, "bloom": 1.2}
        return {"mono": 0.0, "streaks": 0.0, "halation": 0.0, "bloom": 0.0, "weave": 0.4}
    tl.cinema_at = cinema_at
    tl.grain_at = lambda t: 1.3 if t < T_DROP else (1.0 if t < T_HEART else (0.9 if t < T_GREEN else 0.55))

    # ── opening: the glyph writes itself, the show inside; then it's the door ──
    open_h = h * 0.26
    glyph_h = int(open_h)

    @tl.overlay(0.0, T_LAND)
    def opening(t, img, tl):
        black = np.zeros_like(img)
        if t < at(2):
            p = fx.window(t, 0.25, at(2) - 0.15)
            alpha, tm = brand.glyph_drawon(glyph_h)
            soft = 0.07
            reveal = fx.clamp01((p * (1 + soft) - tm) / soft) * alpha
            m = _paste_mask(np.zeros(img.shape[:2], np.float32), reveal, w / 2, h / 2)
            inside = 1 - (1 - img) * 0.75                     # lift so the window reads
            out = black * (1 - m[..., None]) + inside * m[..., None]
            if 0 < p < 1:
                head = np.exp(-((tm - p) / 0.035) ** 2) * alpha * (tm <= p + 0.02)
                halo = cv2.GaussianBlur(head, (0, 0), 6) * 2.0
                out = gfx.paste_alpha(out, np.clip(halo, 0, 1), np.array([1.0, 0.92, 0.8], np.float32),
                                      w / 2, h / 2, 0.6)
            return gfx.rim(out, m, 0.35)
        u = fx.window(t, at(2), T_LAND)
        p = fx.ease_in(u) ** 0.75
        # the draw-on raster carries an 8px pad either side; the vector window must match it
        m = gfx.glyph_window(tl.mask, w, h, p, glyph_h - 16, rot0=0.0)[..., None]
        inside = 1 - (1 - img) * (1 - 0.25 * (1 - u))
        return gfx.rim(black * (1 - m) + inside * m, m, 0.35 * (1 - u))

    # ── title: HOMECOMING written by light over the cast, then into the I ──
    title_font = brand.font(brand.DISPLAY_THIN, h * 0.118)
    track = 0.34
    tpath = gfx.text_path(TITLE, title_font, tracking=track)
    tb = tpath.computeTightBounds()
    i_idx = TITLE.index("I")
    glyphs = title_font.textToGlyphs(TITLE)
    widths = title_font.getWidths(glyphs)
    i_path = title_font.getPath(glyphs[i_idx])
    i_path.offset(float(sum(widths[:i_idx])) + track * title_font.getSize() * i_idx, 0)
    ib = i_path.computeTightBounds()
    pivot = ((ib.left() + ib.right()) / 2, (ib.top() + ib.bottom()) / 2)
    cx0, cy0 = (tb.left() + tb.right()) / 2, (tb.top() + tb.bottom()) / 2
    green = brand.f32(brand.GREEN)
    paper = np.array([0.96, 0.95, 0.92], np.float32)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    rad = np.sqrt(((xx - w / 2) / w) ** 2 + ((yy - h * 0.47) / h) ** 2)
    green_bg = (green * (1.14 - 0.42 * rad[..., None])).astype(np.float32)

    def title_matrix(z, drift=0.0, extra=1.0):
        # z: 0 → title at rest, 1 → deep inside the I (its stem covers the frame)
        s = (1 + drift) * extra * (260.0 ** (z ** 2.4))
        k = fx.smoothstep(0, 0.4, z)
        ax, ay = cx0 + (pivot[0] - cx0) * k, cy0 + (pivot[1] - cy0) * k
        m = skia.Matrix()
        m.preTranslate(w / 2, h / 2)
        m.preScale(s, s)
        m.preTranslate(-ax, -ay)
        return m

    def mask_of(path, m):
        def draw(c, paint):
            c.concat(m)
            c.drawPath(path, paint)
        return tl.mask.draw(draw).copy()

    @tl.overlay(T_TITLE, T_GREEN + 0.02, stage="post")
    def title(t, img, tl):
        # the cast recedes: defocus + dim
        d = fx.ease_in_out(fx.window(t, T_TITLE, T_TITLE + 0.6))
        if d > 0:
            img = cv2.GaussianBlur(img, (0, 0), 1 + 9 * d) * (1 - 0.45 * d)
        z = fx.window(t, T_ZOOM, T_GREEN)
        drift = fx.window(t, T_TITLE, T_ZOOM) * 0.02
        m = title_matrix(z, drift)
        letters = mask_of(tpath, m)
        imask = mask_of(i_path, m)
        # written left → right by a travelling band of light
        sweep = fx.window(t, T_TITLE + 0.05, T_TITLE + 0.95)
        band = -0.1 + 1.25 * fx.ease_in_out(sweep)
        x0p = w / 2 - (cx0 - tb.left()) * (1 + drift)
        x1p = w / 2 + (tb.right() - cx0) * (1 + drift)
        xn = (xx[0] - x0p) / max(x1p - x0p, 1)
        reveal = fx.clamp01((band - xn) / 0.08)[None, :]
        glint = np.exp(-((xn - band) / 0.035) ** 2)[None, :] * float(0 < sweep < 1)
        letters = letters * reveal
        i_here = imask * reveal
        others = np.clip(letters - i_here, 0, 1)
        if 0.04 < z < 0.98:
            # zoom blur on the fly-in: the other letters smear outward
            acc = others.copy()
            for k_ in (0.985, 0.97, 0.955):
                acc += np.clip(mask_of(tpath, title_matrix(z, drift, k_)) - imask, 0, 1)
            others = np.clip(acc / 4, 0, 1)
        glow = cv2.GaussianBlur(letters, (0, 0), 7) * 0.32 * (1 - z)
        out = img + glow[..., None] * paper * 0.8
        out = out * (1 - others[..., None]) + paper * others[..., None]
        g = fx.smoothstep(0.0, 0.35, z)                     # the I turns '98 Green'
        i_col = paper * (1 - g) + green_bg * g
        out = out * (1 - i_here[..., None]) + i_col * i_here[..., None]
        out = out + (glint * letters)[..., None] * 0.6
        out = gfx.rim(out, i_here, 0.6 * g * (1 - z))
        return np.clip(out, 0, 1)

    # ── outro: inside the I it's '98 Green'; the glyph writes itself, the wordmark arrives ──
    lock_h = h * 0.36
    gcx, gcy, gh = gfx.lockup_glyph_box(w, h, lock_h, 0.0)

    @tl.overlay(T_GREEN, DURATION + 1, stage="post")
    def outro(t, img, tl):
        out = green_bg.copy()
        out = gfx.glyph_drawon(out, fx.window(t, T_GREEN + 0.08, T_MARK + 0.35), gcx, gcy, gh)
        tl.layer.clear()
        gfx.draw_wordmark(tl.layer.c, w, h, lock_h, fx.window(t, T_MARK, T_MARK + 0.9))
        return tl.layer.over(out)

    return tl


def _paste_mask(m, alpha, cx, cy):
    ah, aw = alpha.shape
    x0, y0 = int(round(cx - aw / 2)), int(round(cy - ah / 2))
    H, W = m.shape
    sx, sy = max(0, -x0), max(0, -y0)
    dx0, dy0, dx1, dy1 = max(0, x0), max(0, y0), min(W, x0 + aw), min(H, y0 + ah)
    m[dy0:dy1, dx0:dx1] = alpha[sy:sy + dy1 - dy0, sx:sx + dx1 - dx0]
    return m


def _triptych(shot, lt, tl):
    w, h = tl.w, tl.h
    gap = int(h * 0.008)
    out = np.empty((h, w, 3), np.float32)
    out[:] = brand.f32(brand.INK)
    pw = (w - 2 * gap) // 3
    for i, c in enumerate(shot.clips):
        e = fx.expo_out(fx.window(lt, BEAT / 2 * i, BEAT / 2 * i + 0.5))
        if e <= 0:
            continue
        img = c.buf.frame(c.src_time(lt))
        z = c.zoom[0] + (c.zoom[1] - c.zoom[0]) * lt / shot.dur
        panel = fx.reframe(img, z, c.center[0], c.center[1], out_size=(pw, h))
        panel = tl.look.grade(panel, **c.grade)
        panel = fx.shift(panel, dy=(1 - e) * h * 0.05)
        half = int(e * h / 2)
        x0 = i * (pw + gap)
        out[h // 2 - half: h // 2 + half, x0:x0 + pw] = panel[h // 2 - half: h // 2 + half]
    return out


def mix(music=True):
    from afterfilm import score
    y = score.compose(DURATION, music=music, logo=True)
    return (y / (np.abs(y).max() + 1e-9) * 0.89).astype(np.float32)


if __name__ == "__main__":
    import argparse
    import subprocess
    from afterfilm import media
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="renders/homecoming.mp4")
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
            # social-media loudness: -14 LUFS integrated, -1 dBTP
            subprocess.run([media.ffmpeg(), "-v", "error", "-y", "-i", raw, "-af",
                            "loudnorm=I=-14:TP=-1.0:LRA=11", "-ar", "48000", f"{stem}{tag}.wav"], check=True)
            Path(raw).unlink()
        tl.render(a.out, wav=f"{stem}.wav")
        subprocess.run([media.ffmpeg(), "-v", "error", "-y", "-i", a.out, "-i", f"{stem}_nomusic.wav", "-map", "0:v",
                        "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", f"{stem}_nomusic.mp4"], check=True)
