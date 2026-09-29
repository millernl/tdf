"""C.I.T.Y. — a reel of their set at HOMECOMING, 9:16.

Color In The Yard played four songs (show 1:37:47–1:51:52), each in its own light: white
beams, purple, violet under three spots, yellow beams. The reel walks them on, plays the
best bar or two of every song — in sync, their own live sound — walks them off, lets the
rig cycle through every colour the way the show did, and lifts their logo off the screen.

  0.0   walk-on     song 1's intro: the white beams strike on; the three walk into the light
  3.2   song 1      her close-up in the haze
  6.4   song 2      purple: his close-up (strobing in), then the two of them together
  12.0  song 3      violet: the cap, close (a whip in), then the three spots
  18.0  song 4      yellow beams striking on; the two of them close
  22.8  walk-off    song 4's last bar; they leave the light on its final hit
  25.2  the rig cycles through every colour, sped up
  27.2  the logo on the screen; at 27.7 it lifts off and lands (28.2) as a clean lockup; COLOR IN THE YARD

Sound: their live mix, cut downbeat to downbeat on an Essentia beat grid
(edits/data/city_grid.json), equal-power splices just ahead of each downbeat, levels matched
per bar, an echo-out at every change of song, the final hit ringing into a hall, the show's
own low rumble building under the logo and one clean sub impact on the landing.

Picture: the show's 720p copy is the offline source; with footage/CITY_4K.mp4 and
edits/data/city_map.json (afterfilm.conform on the segments in handover/CITY_segments.csv)
every shot reads from the 4K original instead. The logo is traced from the frames where it
sits still on the screen (averaged, background removed) and cached in work/city/.

    python edits/city_reel.py                     # renders/city_reel_9x16.mp4
    python edits/city_reel.py --stills 1 5 27.9   # review frames
    python edits/city_reel.py --segments          # handover/CITY_segments.csv for the 4K pull
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np
import skia

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from afterfilm import fx, gfx, media  # noqa: E402
from afterfilm.timeline import Clip, Shot, Timeline, VideoSource  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SHOW = ROOT / "footage" / "HOMECOMING.2026.PVT.mp4"          # 720p: timing reference, offline picture, sound
MASTER = ROOT / "footage" / "CITY_4K.mp4"                     # the 4K segments, once pulled
MASTER_MAP = ROOT / "edits" / "data" / "city_map.json"
GRID = json.load(open(ROOT / "edits" / "data" / "city_grid.json"))
TAGLINE_FONT = ROOT / "brand" / "fonts" / "city" / "BebasNeue-Regular.ttf"
CACHE = ROOT / "work" / "city"
FPS = 25
LEAD = 0.02               # splices sit just ahead of the downbeat: drums hit a hair early
XF = 0.012                # half-length of each equal-power splice


def tc(s):
    if isinstance(s, (int, float)):
        return float(s)
    v = 0.0
    for x in s.split(":"):
        v = v * 60 + float(x)
    return v


def _grid(song):
    """Downbeats, extended one steady bar either side of the analysed range."""
    d = np.array(GRID[song]["downbeats"])
    bar = float(np.median(np.diff(d)))
    return np.concatenate([[d[0] - 2 * bar, d[0] - bar], d]), bar


def downbeat(song, t):
    d, _ = _grid(song)
    return float(d[np.argmin(np.abs(d - t))])


def bars_after(song, t, n):
    d, _ = _grid(song)
    i = int(np.argmin(np.abs(d - t)))
    if i + n < len(d):
        return float(d[i + n])
    bar = float(np.median(np.diff(d[-8:])))       # past the analysed range: the song's steady bar
    return float(d[-1] + (i + n - len(d) + 1) * bar)


# ── the music: (key, song, show time of its first downbeat, bars) ────────────────
SEGMENTS = [
    ("walkon", "song1", "1:37:46.96", 2),
    ("s1", "song1", "1:39:56.96", 2),
    ("s2a", "song2", "1:44:43.58", 1),
    ("s2b", "song2", "1:45:17.01", 1),
    ("s3", "song3", "1:47:02.37", 2),
    ("s4a", "song4", "1:50:40.02", 1),
    ("s4b", "song4", "1:51:20.81", 1),
    ("walkoff", "song4", "1:51:49.61", 1),
]


def layout():
    out, rec = {}, 0.0
    for key, song, t, n in SEGMENTS:
        a = downbeat(song, tc(t))
        b = bars_after(song, a, n)
        out[key] = dict(song=song, src=a, end=b, rec=rec, dur=b - a)
        rec += b - a
    return out


L = layout()
T_HIT = L["walkoff"]["rec"] + L["walkoff"]["dur"]    # song 4's final hit
T_LOGO = T_HIT + 2.0                                  # after the colour cycle: the logo on the screen
T_SLAM = T_HIT + 3.0                                  # the last letter lands: the impact
LIFT = T_SLAM - 0.36 - 3 * 0.05                       # the letters lift off the screen, C first
DURATION = T_HIT + 5.8
SRC_CYCLE = tc("1:51:52.40")                          # the rig's colour cycle (5.2 s → 2.0 s)
SRC_LOGO = tc("1:51:58.40")
SRC_RUMBLE = (tc("1:51:58.90"), tc("1:52:01.30"))     # the show's low swell under its logo
EARLY = {"him": 0.16, "cap": 0.08}                    # shots that start early for a strobe / a whip


# ── the picture ──────────────────────────────────────────────────────────────
def source():
    if MASTER.exists() and MASTER_MAP.exists():
        from afterfilm.conform import MappedSource
        return MappedSource(MASTER, json.load(open(MASTER_MAP))), (3840, 2160), False
    return VideoSource(str(SHOW)), (1280, 720), True


def footage_clips(src, decode):
    def C(t, **k):
        return Clip(src, tc(t), grade={"look": "stage"}, decode=decode, **k)

    half = L["walkoff"]["dur"] / 2
    c = {
        "stage":  C(L["walkon"]["src"], track=[(0, 0.5)], zoom=(1.0, 1.05), note="the white beams strike on"),
        "walkin": C("1:37:52.90", track=[(0, 0.66), (1, 0.6)], zoom=(1.0, 1.04), note="the three walk into the light"),
        "her":    C(L["s1"]["src"], track=[(0, 0.58)], zoom=(1.06, 1.12), center=(0.5, 0.45), note="her close-up in the haze"),
        "him":    C(L["s2a"]["src"], track=[(0, 0.40)], zoom=(1.04, 1.1), center=(0.5, 0.45), note="purple: his close-up"),
        "duo":    C(L["s2b"]["src"], track=[(0, 0.40)], zoom=(1.0, 1.05), center=(0.5, 0.45), note="the two of them together"),
        "cap":    C(L["s3"]["src"], track=[(0, 0.64)], zoom=(1.04, 1.1), center=(0.5, 0.45), note="violet: the cap, close"),
        "spots":  C("1:47:05.00", track=[(0, 0.36), (1, 0.64)], note="the three spots"),
        "yellow": C(L["s4a"]["src"], track=[(0, 0.5)], zoom=(1.0, 1.05), note="yellow beams"),
        "yduo":   C(L["s4b"]["src"] - 0.10, track=[(0, 0.62), (1, 0.72)], zoom=(1.03, 1.08), center=(0.5, 0.45),
                    note="the two of them in yellow"),
        "leave":  C("1:51:43.60", track=[(0, 0.42), (1, 0.50)], note="they walk off"),
        "last":   C(L["walkoff"]["src"] + half, track=[(0, 0.52), (1, 0.62)], note="the last one leaves the light"),
        "cycle":  C(SRC_CYCLE, speed=2.6, track=[(0, 0.5)], note="the rig cycles through every colour"),
        "screen": C(SRC_LOGO, speed=0.6, note="the logo on the screen"),
    }
    for k, dt in EARLY.items():
        c[k].t_in -= dt * c[k].speed
    return c


def cuts():
    C = []

    def add(start, dur, key, **extra):
        C.append((start, dur, key, extra))

    w, bar1 = L["walkon"], L["walkon"]["dur"] / 2
    add(0.0, bar1, "stage", fx_kind="strike_open")
    add(bar1, w["dur"] - bar1, "walkin")
    add(L["s1"]["rec"], L["s1"]["dur"], "her", fx_kind="snap_in")
    add(L["s2a"]["rec"] - EARLY["him"], L["s2a"]["dur"] + EARLY["him"], "him", trans=("strobe", 0.16))
    add(L["s2b"]["rec"], L["s2b"]["dur"], "duo", punch=0.05)
    d_cut = L["s3"]["rec"] + (tc("1:47:05.00") - L["s3"]["src"])   # the live cut to the wide, in sync
    add(L["s3"]["rec"] - EARLY["cap"], d_cut - L["s3"]["rec"] + EARLY["cap"], "cap", trans=("smear", 0.16))
    add(d_cut, L["s3"]["rec"] + L["s3"]["dur"] - d_cut, "spots")
    add(L["s4a"]["rec"], L["s4a"]["dur"], "yellow", fx_kind="strike_short")
    add(L["s4b"]["rec"], L["s4b"]["dur"], "yduo", fx_kind="staccato")
    h = L["walkoff"]["dur"] / 2
    add(L["walkoff"]["rec"], h, "leave")
    add(L["walkoff"]["rec"] + h, h, "last")
    add(T_HIT, T_LOGO - T_HIT, "cycle", flash=0.45)
    add(T_LOGO, DURATION - T_LOGO, "screen", logo=True)
    return C


# per-frame light levels: the rig striking on (25 fps)
STRIKES = {
    "strike_open": {0: 1.0, 1: 0.7, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.9, 6: 0.25, 7: 0.0, 8: 0.0, 9: 0.0,
                    10: 1.0, 11: 0.5, 12: 0.0, 13: 0.85},
    "strike_short": {0: 1.0, 1: 0.15, 2: 0.0, 3: 1.0, 4: 0.3},
}
ZOOM_STEPS = {"snap_in": [(2, 1.6), (4, 1.3), (6, 1.12)],       # (until frame, zoom): the scale snaps out
              "staccato": [(2, 1.35), (4, 1.15)]}


def effected(kind):
    def render(shot, lt, tl):
        img = shot.clip.frame(lt, shot.dur, tl.look, out_size=(tl.w, tl.h))
        n = int(round(lt * tl.fps))
        if kind in STRIKES:
            return img * STRIKES[kind].get(n, 1.0)
        for until, z in ZOOM_STEPS.get(kind, []):
            if n < until:
                return fx.reframe(img, z, 0.5, 0.42)
        return img
    return render


# ── the logo: traced from the frames where it holds still on the screen ─────────
LOGO_BOX = (0.387, 0.326, 0.707, 0.597)       # normalised crop around the letters on the screen
MINT = np.array([0.80, 0.90, 0.87], np.float32)


def trace_logo(src_path=SHOW, size=(1280, 720), t0="1:51:59.00", dur=11.0, up=6):
    """Average ~11 s of the static projection, remove the haze and beams (a morphological
    opening wider than the strokes), threshold at half the letters' brightness. Returns the
    mask (crop coords × up), the crop origin in normalised frame coords and the components."""
    cache = CACHE / f"logo_{Path(src_path).stem}_{size[0]}.npz"
    if cache.exists():
        z = np.load(cache, allow_pickle=True)
        return z["mask"], tuple(z["origin"]), list(z["comps"]), float(z["px"])
    fr = media.read_frames(str(src_path), tc(t0), dur, 25, size, deinterlace=False).astype(np.float32)
    avg = fr.mean(-1).mean(0)
    W, H = size
    x0, y0, x1, y1 = int(LOGO_BOX[0] * W), int(LOGO_BOX[1] * H), int(LOGO_BOX[2] * W), int(LOGO_BOX[3] * H)
    crop = avg[y0:y1, x0:x1]
    upi = cv2.resize(crop, (crop.shape[1] * up, crop.shape[0] * up), interpolation=cv2.INTER_CUBIC)
    small = cv2.resize(upi, None, fx=0.25, fy=0.25, interpolation=cv2.INTER_AREA)
    k = int(round(12.5 * up * W / 1280)) | 1                      # wider than a stroke
    bg = cv2.morphologyEx(small, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    bg = cv2.resize(cv2.GaussianBlur(bg, (0, 0), 10), (upi.shape[1], upi.shape[0]), interpolation=cv2.INTER_CUBIC)
    fg = upi - bg
    soft = fx.clamp01((fg - 0.4 * np.percentile(fg, 99.5)) / (0.2 * np.percentile(fg, 99.5)))
    m = (soft > 0.5).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m)
    big = max(stats[1:, 3]) if n > 1 else 1
    comps = []
    for i in range(1, n):
        x, y, w, h, a = stats[i]
        if a < 0.01 * big * big or y > 0.8 * upi.shape[0]:          # specks, and the tagline row below
            continue
        kind = "letter" if h > 0.5 * big else "dot"
        comps.append(dict(kind=kind, box=(int(x), int(y), int(w), int(h)), label=i))
    comps.sort(key=lambda c: c["box"][0])
    mask = np.zeros(m.shape, np.float32)
    for c in comps:
        mask[lab == c["label"]] = 1.0
    mask = cv2.GaussianBlur(mask, (0, 0), 1.2)                     # anti-aliased edge
    for c in comps:
        del c["label"]
    CACHE.mkdir(parents=True, exist_ok=True)
    px = 1.0 / (up * W)                                            # one mask pixel, in frame widths
    np.savez(cache, mask=mask, origin=np.array([LOGO_BOX[0], LOGO_BOX[1]]), comps=np.array(comps, dtype=object), px=px)
    return mask, (LOGO_BOX[0], LOGO_BOX[1]), comps, px


def zoom_about(img, s, x, y):
    """Scale the picture by s about the pixel (x, y), which stays put."""
    h, w = img.shape[:2]
    M = np.float32([[s, 0, x - s * x], [0, s, y - s * y]])
    return cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)


class LogoScene:
    """The projection, fitted to the frame's width (the dark stage runs out to black), then
    the letters lift off the screen and fly forward into a full-width lockup."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.mask, self.origin, self.comps, self.px = trace_logo()
        ys, xs = np.nonzero(self.mask > 0.5)
        self.bx0, self.bx1, self.by0, self.by1 = xs.min(), xs.max(), ys.min(), ys.max()
        self.band_h = int(round(w * 9 / 16))
        # the band sits so the projected logo's centre is where the lockup will land
        self.land = (w / 2, h * 0.455)
        lcx = self.origin[0] + (self.bx0 + self.bx1) / 2 * self.px              # normalised frame x
        lcy = self.origin[1] * 1.0 + (self.by0 + self.by1) / 2 * self.px * 16 / 9   # normalised frame y
        self.band_y0 = self.land[1] - lcy * self.band_h
        self.band_x0 = self.land[0] - lcx * w
        self.s_proj = self.px * w                                  # frame px per mask px, on the screen
        self.s_land = 0.84 * w / (self.bx1 - self.bx0)             # frame px per mask px, landed
        self.font = skia.Font(skia.Typeface.MakeFromFile(str(TAGLINE_FONT)), w * 0.072)
        self.font.setEdging(skia.Font.Edging.kAntiAlias)
        self.gmask = gfx.Mask(w, h)

    def _place(self, alpha, cx_m, cy_m, s, ox, oy):
        """Warp mask region so mask point (cx_m, cy_m) lands on (ox, oy) at scale s."""
        M = np.float32([[s, 0, ox - s * cx_m], [0, s, oy - s * cy_m]])
        return cv2.warpAffine(alpha, M, (self.w, self.h), flags=cv2.INTER_LINEAR)

    def push(self, t):
        """The camera creeps toward the screen, then flies into it as the letters lift."""
        return (1.3 + 0.15 * fx.ease_in_out(fx.window(t, T_LOGO, T_SLAM))
                + 0.8 * fx.ease_in(fx.window(t, LIFT, T_SLAM + 0.3)))

    def on_screen(self, mx, my, push):
        """Where mask point (mx, my) sits in the frame while it is still on the screen."""
        nx = self.origin[0] + mx * self.px
        ny = self.origin[1] + my * self.px * 16 / 9
        X, Y = self.band_x0 + nx * self.w, self.band_y0 + ny * self.band_h
        return self.land[0] + (X - self.land[0]) * push, self.land[1] + (Y - self.land[1]) * push

    def letters(self, t, t0):
        """Coverage of the letters at time t; they lift off the screen from t0 on."""
        out = np.zeros((self.h, self.w), np.float32)
        lcx, lcy = (self.bx0 + self.bx1) / 2, (self.by0 + self.by1) / 2
        p0 = self.push(t0)
        n_letter = 0
        for c in self.comps:
            x, y, bw, bh = c["box"]
            mx, my = x + bw / 2, y + bh / 2
            part = np.zeros_like(self.mask)
            part[y:y + bh, x:x + bw] = self.mask[y:y + bh, x:x + bw]
            if c["kind"] == "letter":
                a = t0 + 0.05 * n_letter                           # C first … Y lands on the impact
                n_letter += 1
                e = fx.ease_in_out(fx.window(t, a, a + 0.36))
                pop = 1.0
            else:                                                  # the dots tick in after the landing
                k = sum(1 for d in self.comps if d["kind"] == "dot" and d["box"][0] < x)
                q = fx.window(t, T_SLAM + 0.04 + 0.07 * k, T_SLAM + 0.22 + 0.07 * k)
                if q <= 0:
                    continue
                e, pop = 1.0, 1.0 + 0.25 * np.sin(np.pi * min(q * 1.4, 1.0))
            sx, sy = self.on_screen(mx, my, p0)
            lx, ly = self.land[0] + (mx - lcx) * self.s_land, self.land[1] + (my - lcy) * self.s_land
            s = (self.s_proj * p0 * (1 - e) + self.s_land * e) * (1 + 0.1 * np.sin(np.pi * e)) * pop
            ox, oy = sx + (lx - sx) * e, sy + (ly - sy) * e
            out = np.maximum(out, self._place(part, mx, my, s, ox, oy))
        return out

    def render(self, shot, lt, tl):
        t = shot.start + lt
        w, h = self.w, self.h
        c = shot.clip
        f16 = tl.look.grade(c.buf.frame(c.src_time(lt)), **c.grade)
        band = cv2.resize(f16, (w, self.band_h), interpolation=cv2.INTER_AREA)
        push = self.push(t)
        frame = np.zeros((h, w, 3), np.float32)
        frame[int(self.band_y0):int(self.band_y0) + self.band_h] = band[:h - int(self.band_y0)][:self.band_h]
        frame = zoom_about(frame, push, self.land[0], self.land[1])
        # the screen fades as its letters lift off, and falls away behind them
        lift = fx.ease_in_out(fx.window(t, LIFT, T_SLAM))
        frame *= 1 - 0.9 * lift
        if lift > 0:
            frame = cv2.GaussianBlur(frame, (0, 0), 1 + 14 * lift)
        # the flying letters, with motion blur over the frame's exposure
        if t >= LIFT:
            acc = np.zeros((h, w), np.float32)
            for k in range(4):
                acc += self.letters(t - k * 0.25 / tl.fps, LIFT)
            m = acc / 4
            land = fx.window(t, T_SLAM - 0.02, T_SLAM + 0.5)
            col = MINT + (1 - MINT) * (1 - land) * (land > 0) * 0.8
            glow = cv2.GaussianBlur(m, (0, 0), w * 0.02) * (0.35 + 0.5 * (1 - land))
            frame = frame * (1 - m[..., None]) + m[..., None] * col
            frame = frame + glow[..., None] * MINT * 0.6
        # COLOR IN THE YARD, written in by a band of light
        if t >= T_SLAM + 0.4:
            sweep = fx.ease_in_out(fx.window(t, T_SLAM + 0.4, T_SLAM + 1.1))
            y = self.land[1] + (self.by1 - self.by0) / 2 * self.s_land + w * 0.13
            txt = "COLOR IN THE YARD"
            total, _ = gfx.measure(txt, self.font, 0.32)

            def draw(cv, paint):
                gfx.text(cv, txt, self.font, w / 2, y, color=(255, 255, 255), tracking=0.32, align="center")
            tm = self.gmask.draw(draw)
            xx = (np.arange(w, dtype=np.float32) - (w - total) / 2) / max(total, 1)
            band_l = -0.1 + 1.2 * sweep
            reveal = fx.clamp01((band_l - xx) / 0.08)[None, :]
            glint = np.exp(-((xx - band_l) / 0.04) ** 2)[None, :] * float(0 < sweep < 1)
            frame = frame * (1 - (tm * reveal)[..., None]) + (tm * reveal)[..., None] * MINT * 0.92
            frame = frame + (tm * glint)[..., None] * 0.6
        # the landing: a camera jolt and a breath of light
        k = max(0.0, 1 - (t - T_SLAM) / 0.18) if t >= T_SLAM else 0.0
        if k > 0:
            frame = fx.flash(frame, 0.22 * k, tint=(0.9, 1.0, 0.97))
            frame = fx.reframe(frame, 1 + 0.02 * k, 0.5 + 0.006 * k * np.sin(t * 90), 0.5 + 0.006 * k * np.cos(t * 70))
        hold = fx.window(t, T_SLAM + 0.5, DURATION)
        if hold > 0:
            frame = zoom_about(frame, 1 + 0.025 * fx.ease_in_out(hold), self.land[0], self.land[1])
        return np.clip(frame, 0, 1)


def build(clips, w=1080, h=1920, fps=FPS, offline=False):
    look = fx.Look(w, h)
    look.black = np.array([0.012, 0.012, 0.012], np.float32)
    tl = Timeline(w, h, fps, DURATION, look)
    logo = LogoScene(w, h)
    for start, dur, key, extra in cuts():
        if extra.get("logo"):
            tl.add(Shot(start, dur, clip=clips[key], render=logo.render))
        elif extra.get("fx_kind"):
            tl.add(Shot(start, dur, clip=clips[key], render=effected(extra["fx_kind"]),
                        **{k: v for k, v in extra.items() if k in ("punch", "flash", "shake", "trans")}))
        else:
            tl.add(Shot(start, dur, clip=clips[key],
                        **{k: v for k, v in extra.items() if k in ("punch", "flash", "shake", "trans")}))
    # the logo gets no anamorphic streaks: a lockup that bright would draw a bar across the frame
    tl.cinema_at = lambda t: {"mono": 0.0, "streaks": 0.8, "halation": 0.8, "bloom": 0.9} if t < T_LOGO else \
        {"mono": 0.6, "streaks": 0.0, "halation": 0.35, "bloom": 0.7}
    tl.grain_at = lambda t: 0.75 if offline else 0.45
    tl.vignette_at = lambda t: 0.8
    return tl


# ── the sound ────────────────────────────────────────────────────────────────
def _hall(sr, rt60=2.4, predelay=0.02, seed=7):
    from scipy import signal
    rng = np.random.default_rng(seed)
    n = int(rt60 * 1.3 * sr)
    t = np.arange(n) / sr
    b, a = signal.butter(2, 3000 / (sr / 2))
    ch = []
    for _ in range(2):
        nz = rng.standard_normal(n)
        lo = signal.lfilter(b, a, nz)
        ch.append(lo * 10 ** (-3 * t / rt60) + 0.4 * (nz - lo) * 10 ** (-3 * t / (rt60 * 0.4)))
    ir = np.concatenate([np.zeros((int(predelay * sr), 2)), np.stack(ch, 1)])
    return (ir / np.sqrt((ir ** 2).sum(0, keepdims=True))).astype(np.float32)


def _verb(x, ir):
    from scipy import signal
    return np.stack([signal.fftconvolve(x[:, c], ir[:, c]) for c in range(2)], 1).astype(np.float32)


def _impact(sr, dur=2.2):
    """One clean, deep landing: a sub that drops 58 → 34 Hz, a soft felt transient."""
    t = np.arange(int(dur * sr)) / sr
    f = 34 + 24 * np.exp(-t / 0.18)
    sub = np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-t / 0.55)
    rng = np.random.default_rng(3)
    from scipy import signal
    b, a = signal.butter(2, 900 / (sr / 2))
    click = signal.lfilter(b, a, rng.standard_normal(len(t))) * np.exp(-t / 0.012) * 0.35
    y = (sub * 0.9 + click)[:, None].repeat(2, 1)
    return y.astype(np.float32)


def mix(sr=48000):
    a0 = L["walkon"]["src"] - 2.0
    src = media.read_audio(str(SHOW), t_in=a0, dur=tc("1:52:03") - a0, sr=sr, channels=2)

    def S(t):                                   # show time → sample index in src
        return int(round((t - a0) * sr))

    n = int(round(DURATION * sr))
    y = np.zeros((n, 2), np.float32)
    nx, nl = int(XF * sr), int(LEAD * sr)
    rms = {k: np.sqrt(np.mean(src[S(v["src"]):S(v["end"])] ** 2)) for k, v in L.items()}
    ref = float(np.median(list(rms.values())))
    order = [k for k, *_ in SEGMENTS]
    ir = _hall(sr, 1.8, 0.03)
    for i, k in enumerate(order):
        v = L[k]
        g = float(np.clip(ref / (rms[k] + 1e-9), 10 ** (-5 / 20), 10 ** (5 / 20)))
        last = k == "walkoff"
        tail = 2.6 if last else 0.0             # the final hit rings on
        s0, s1 = S(v["src"]) - nl - nx, S(v["end"] + tail) - nl + nx
        seg = src[s0:s1].copy() * g
        r0 = int(round(v["rec"] * sr)) - nl - nx
        ramp = np.sin(np.linspace(0, np.pi / 2, 2 * nx, dtype=np.float32))[:, None]
        seg[:2 * nx] *= ramp
        if last:
            fade = int(1.0 * sr)
            seg[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)[:, None] ** 2
        else:
            seg[-2 * nx:] *= ramp[::-1]
        a, b = max(r0, 0), min(r0 + len(seg), n)
        y[a:b] += seg[a - r0:b - r0]
        # an echo-out where the song changes: the outgoing last beat rings into a room
        nxt = order[i + 1] if i + 1 < len(order) else None
        if nxt and L[nxt]["song"] != v["song"]:
            beat = 60 / GRID[v["song"]]["bpm"]
            thr = src[S(v["end"] - beat):S(v["end"])].copy() * g
            wet = _verb(thr, ir)
            at = int(round(L[nxt]["rec"] * sr))
            env = np.exp(-np.arange(len(wet)) / (0.45 * sr))[:, None]
            m = min(len(wet), n - at)
            y[at:at + m] += (wet * env)[:m] * 10 ** (-11 / 20)
    # the final hit into a hall
    big = _hall(sr, 3.2, 0.03, seed=11)
    h0 = L["walkoff"]["end"]
    hit = src[S(h0 - 0.5):S(h0 + 0.4)].copy() * float(np.clip(ref / (rms["walkoff"] + 1e-9), 0.56, 1.8))
    hit[:int(0.01 * sr)] *= np.linspace(0, 1, int(0.01 * sr), dtype=np.float32)[:, None]
    wet = _verb(hit, big)
    at = int(round((T_HIT - 0.5) * sr))
    m = min(len(wet), n - at)
    env = np.ones((m, 1), np.float32)
    cut = int(round((T_SLAM + 0.6 - (T_HIT - 0.5)) * sr))
    if cut < m:
        env[cut:] = np.exp(-np.arange(m - cut) / (0.25 * sr))[:, None]
    y[at:at + m] += wet[:m] * env * 10 ** (-9 / 20)
    # the show's own low swell, building into the landing
    ru = src[S(SRC_RUMBLE[0]):S(SRC_RUMBLE[1])].copy() * 10 ** (15 / 20)
    ru *= np.linspace(0, 1, len(ru), dtype=np.float32)[:, None] ** 1.5
    e = int(round(T_SLAM * sr))
    y[e - len(ru):e] += ru[:len(ru)]
    # one clean landing
    imp = _impact(sr)
    imp = imp + _verb(imp, big)[:len(imp)] * 0.25
    m = min(len(imp), n - e)
    y[e:e + m] += imp[:m] * 10 ** (-7 / 20)
    y[:int(0.005 * sr)] *= np.linspace(0, 1, int(0.005 * sr), dtype=np.float32)[:, None]
    peak = np.abs(y).max()
    return (y * (10 ** (-1 / 20) / peak if peak > 10 ** (-1 / 20) else 1.0)).astype(np.float32)


# ── housekeeping ─────────────────────────────────────────────────────────────
def segments_csv(path=ROOT / "handover" / "CITY_segments.csv", handle=1.5):
    """Every stretch of the show the reel reads, with handles, merged: the list to cut from
    the 4K original in LosslessCut (keyframe cut, 'merge cuts', export as one file)."""
    clips = footage_clips(VideoSource(str(SHOW)), None)
    spans = []
    for start, dur, key, extra in cuts():
        c = clips[key]
        a, b = c.src_time(0), c.src_time(dur)
        spans.append((a - handle, b + handle, key))
    spans.append((tc("1:51:58.5"), tc("1:52:12.5"), "logo (still on screen: traced)"))
    spans.sort()
    merged = []
    for a, b, k in spans:
        if merged and a <= merged[-1][1] + 1.0:
            merged[-1][1] = max(merged[-1][1], b)
            merged[-1][2].append(k)
        else:
            merged.append([a, b, [k]])
    with open(path, "w") as f:
        for i, (a, b, ks) in enumerate(merged, 1):
            f.write(f"{a:.3f},{b:.3f},{i:02d} {' + '.join(dict.fromkeys(ks))}\n")
    total = sum(b - a for a, b, _ in merged)
    print(f"{len(merged)} segments, {total:.1f} s → {path}")
    return merged


def verify(clips):
    from afterfilm import analyze
    bad = 0
    C = cuts()
    for i, (start, dur, key, extra) in enumerate(C):
        nxt = C[i + 1] if i + 1 < len(C) else None
        handle = max(0.0, nxt[0] + nxt[3]["trans"][1] - (start + dur)) if nxt and "trans" in nxt[3] else 0.0
        c = clips[key]
        a, b = c.src_time(0) - 0.04, c.src_time(dur + handle)
        mx, at_t, flagged = analyze.frame_cuts(str(SHOW), a, b + 0.04)
        bad += bool(flagged)
        print(f"{'CUT?' if flagged else 'ok  '} {key:7s} src {analyze.tc(a)}–{analyze.tc(b)}  max {mx:.2f} @ {analyze.tc(at_t)}"
              + (f"  flagged {[analyze.tc(x) for x in flagged]}" if flagged else ""))
    print(f"{bad} clip(s) flagged")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="renders/city_reel_9x16.mp4")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--stills", nargs="*", type=float)
    ap.add_argument("--edl", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--segments", action="store_true")
    a = ap.parse_args()
    if a.segments:
        segments_csv()
        sys.exit(0)
    W, H = int(1080 * a.scale) // 2 * 2, int(1920 * a.scale) // 2 * 2
    src, decode, offline = source()
    clips = footage_clips(src, decode)
    if a.verify:
        verify(clips)
        sys.exit(0)
    tl = build(clips, W, H, offline=offline)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    print(f"{'offline (720p)' if offline else '4K'} · {DURATION:.2f} s · hit {T_HIT:.2f} · slam {T_SLAM:.2f}")
    if a.edl:
        print(tl.edl())
    elif a.stills:
        print(tl.stills(a.stills, str(Path(a.out).with_suffix("")) + "_{t:05.2f}.png"))
    else:
        wav = str(Path(a.out).with_suffix(".wav"))
        media.write_wav(wav, mix())
        tl.render(a.out, wav=wav)
