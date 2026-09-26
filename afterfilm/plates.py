"""Stand-in footage for the animatic: stage light through haze, silhouettes, a label
naming the shot the real edit will put there. Clearly placeholder — never shipped."""
import cv2
import numpy as np
import skia

from . import brand, gfx

STAGE_COLOURS = {
    "tungsten": (1.00, 0.72, 0.42),
    "magenta": (0.95, 0.25, 0.65),
    "cyan": (0.30, 0.75, 1.00),
    "amber": (1.00, 0.55, 0.15),
    "white": (0.95, 0.95, 1.00),
    "violet": (0.55, 0.35, 1.00),
    "green": (0.35, 0.95, 0.55),
}


class PlateSource:
    def __init__(self, shot_id, note, colours=("tungsten", "cyan"), beams=3, figures=4, energy=0.5,
                 seed=0, key=0.85, crowd=False):
        self.shot_id, self.note = shot_id, note
        self.colours = [np.array(STAGE_COLOURS[c], np.float32) for c in colours]
        self.nb, self.nf, self.energy, self.key, self.crowd = beams, figures, energy, key, crowd
        self.rng = np.random.default_rng(seed)
        r = self.rng
        self.beam = [dict(ox=r.uniform(0.1, 0.9), a0=r.uniform(-0.5, 0.5), amp=r.uniform(0.1, 0.35),
                          w=r.uniform(0.05, 0.11), ph=r.uniform(0, 6.28), sp=r.uniform(0.3, 0.9),
                          col=self.colours[i % len(self.colours)]) for i in range(beams)]
        self.fig = [dict(x=(i + 0.5) / figures + r.uniform(-0.05, 0.05), s=r.uniform(0.85, 1.1),
                         ph=r.uniform(0, 6.28)) for i in range(figures)]
        self.noise = cv2.resize(r.random((24, 40)).astype(np.float32), (640, 360), interpolation=cv2.INTER_CUBIC)

    def read(self, t0, t1, fps, size):
        return _PlateBuffer(self, size)


class _PlateBuffer:
    def __init__(self, src, size):
        self.s, (self.w, self.h) = src, size
        self.lw, self.lh = self.w // 4, self.h // 4
        yy, xx = np.mgrid[0:self.lh, 0:self.lw].astype(np.float32)
        self.xx, self.yy = xx / self.lw, yy / self.lh
        self.layer = gfx.Layer(self.w, self.h)

    def frame(self, t):
        s = self.s
        xx, yy = self.xx, self.yy
        img = np.zeros((self.lh, self.lw, 3), np.float32)
        img += (0.012 + 0.03 * yy)[..., None] * np.array([0.8, 0.9, 1.0], np.float32)
        shift = int(t * 18) % 640
        haze = np.roll(s.noise, shift, axis=1)
        haze = cv2.resize(haze, (self.lw, self.lh))
        haze = 0.55 + 0.45 * haze
        for b in s.beam:
            ang = b["a0"] + b["amp"] * np.sin(t * b["sp"] * (1 + 2 * s.energy) + b["ph"])
            dx, dy = xx - b["ox"], (yy + 0.12) * (self.lh / self.lw)
            diff = np.arctan2(dx, dy) - ang
            beam = np.exp(-(diff / b["w"]) ** 2) * (0.25 + 0.75 * yy) * haze
            hit = b["ox"] + np.tan(ang) * (0.97 * self.lh / self.lw)
            pool = np.exp(-(((xx - hit) / 0.12) ** 2 + ((yy - 0.86) / 0.035) ** 2))
            img += (beam * 0.55 * s.key + pool * 0.9 * s.key)[..., None] * b["col"]
        img = cv2.resize(img, (self.w, self.h), interpolation=cv2.INTER_CUBIC)
        # silhouettes, drawn crisp at full res
        L = self.layer
        L.clear()
        c = L.c
        dark = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0.01, 0.012, 0.012, 0.96))
        H, W = self.h, self.w
        floor = 0.86 * H
        if s.crowd:
            for i in range(26):
                x = (i + 0.5) / 26 * W
                bob = np.sin(t * 7 + i) * 0.006 * H * s.energy
                c.drawCircle(x, 0.83 * H + bob, 0.045 * H, dark)
                c.drawRect(skia.Rect.MakeLTRB(x - 0.05 * H, 0.86 * H + bob, x + 0.05 * H, H), dark)
        for f in s.fig:
            jump = max(0.0, np.sin(t * (2 + 5 * s.energy) + f["ph"])) ** 3 * 0.09 * H * s.energy
            sway = np.sin(t * 1.3 + f["ph"]) * 0.012 * W
            hh = 0.36 * H * f["s"]
            x, base = f["x"] * W + sway, floor - jump
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x - hh * 0.09, base - hh * 0.82, x + hh * 0.09, base),
                                              hh * 0.08, hh * 0.08), dark)
            c.drawCircle(x, base - hh * 0.9, hh * 0.075, dark)
            arm = np.sin(t * 3 + f["ph"]) * 0.6 + 0.9
            p = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0.01, 0.012, 0.012, 0.96),
                           Style=skia.Paint.kStroke_Style, StrokeWidth=hh * 0.045, StrokeCap=skia.Paint.kRound_Cap)
            c.drawLine(x, base - hh * 0.72, x - hh * 0.35 * np.cos(arm), base - hh * (0.72 + 0.3 * np.sin(arm)), p)
            c.drawLine(x, base - hh * 0.72, x + hh * 0.35 * np.cos(arm), base - hh * (0.72 + 0.3 * np.sin(arm)), p)
        # label
        big = brand.font(brand.DISPLAY_THIN, H * 0.085)
        small = brand.font(brand.MONO, H * 0.02)
        gfx.text(c, s.shot_id, big, W * 0.5, H * 0.47, (235, 235, 230), 0.85, tracking=0.04, align="center")
        gfx.text(c, s.note.upper(), small, W * 0.5, H * 0.47 + H * 0.05, (235, 235, 230), 0.75, tracking=0.08,
                 align="center")
        gfx.text(c, "PLACEHOLDER — REAL FOOTAGE GOES HERE", brand.font(brand.MONO, H * 0.014), W * 0.5, H * 0.2,
                 (235, 235, 230), 0.45, tracking=0.12, align="center")
        return np.clip(L.over(img), 0, 1)
