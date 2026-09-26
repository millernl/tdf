"""Signature scenes: the glyph door, the triptych, the title that flies into its I,
and the logo written on paper. Each `add_*` registers overlays on a Timeline."""
import cv2
import numpy as np
import skia

from . import brand, fx, gfx

PAPER = np.array([0.957, 0.949, 0.925], np.float32)     # warm white page (#F4F2EC)


def paste_mask(m, alpha, cx, cy):
    ah, aw = alpha.shape
    x0, y0 = int(round(cx - aw / 2)), int(round(cy - ah / 2))
    H, W = m.shape
    sx, sy = max(0, -x0), max(0, -y0)
    dx0, dy0, dx1, dy1 = max(0, x0), max(0, y0), min(W, x0 + aw), min(H, y0 + ah)
    m[dy0:dy1, dx0:dx1] = alpha[sy:sy + dy1 - dy0, sx:sx + dx1 - dx0]
    return m


# ── the door: the glyph writes itself with the show inside, then we fly through ──
def add_glyph_door(tl, t_draw0, t_draw1, t_zoom0, t_land, height=0.26):
    w, h = tl.w, tl.h
    gh = int(min(h * height, w * 0.4))                 # vertical frames: sized to the width

    @tl.overlay(0.0, t_land)
    def door(t, img, tl):
        black = np.zeros_like(img)
        if t < t_zoom0:
            p = fx.window(t, t_draw0, t_draw1)
            alpha, tm = brand.glyph_drawon(gh)
            soft = 0.07
            reveal = fx.clamp01((p * (1 + soft) - tm) / soft) * alpha
            m = paste_mask(np.zeros(img.shape[:2], np.float32), reveal, w / 2, h / 2)
            inside = 1 - (1 - img) * 0.75                          # lift so the window reads
            out = black * (1 - m[..., None]) + inside * m[..., None]
            if 0 < p < 1:
                head = np.exp(-((tm - p) / 0.035) ** 2) * alpha * (tm <= p + 0.02)
                halo = cv2.GaussianBlur(head, (0, 0), 6) * 2.0
                out = gfx.paste_alpha(out, np.clip(halo, 0, 1), np.array([1.0, 0.94, 0.84], np.float32),
                                      w / 2, h / 2, 0.55)
            return gfx.rim(out, m, 0.35)
        u = fx.window(t, t_zoom0, t_land)
        p = fx.ease_in(u) ** 0.75
        # the draw-on raster carries an 8 px pad either side; the vector window matches it
        m = gfx.glyph_window(tl.mask, w, h, p, gh - 16, rot0=0.0)[..., None]
        inside = 1 - (1 - img) * (1 - 0.25 * (1 - u))
        return gfx.rim(black * (1 - m) + inside * m, m, 0.35 * (1 - u))


# ── triptych ──
def triptych(shot, lt, tl, stagger=None):
    """Three panels, each opening as a clean door from its centre line, one after another
    on the eighth notes — crisp edges, no drift. Side by side in a wide frame; stacked
    rows (each close to 16:9) in a vertical one."""
    from .score import BEAT
    stagger = BEAT / 2 if stagger is None else stagger
    w, h = tl.w, tl.h
    vertical = h > w
    gap = int(min(w, h) * 0.008)
    out = np.empty((h, w, 3), np.float32)
    out[:] = brand.f32(brand.INK)
    if vertical:
        ph, pw = (h - 2 * gap) // 3, w
    else:
        pw, ph = (w - 2 * gap) // 3, h
    for i, c in enumerate(shot.clips):
        e = fx.expo_out(fx.window(lt, stagger * i, stagger * i + 0.32))
        if e <= 0:
            continue
        img = c.buf.frame(c.src_time(lt))
        p = lt / shot.dur
        z = (c.zoom[0] + (c.zoom[1] - c.zoom[0]) * p) * (1 + 0.08 * (1 - e))
        cx, cy = c.center_at(min(p, 1.0))
        panel = fx.reframe(img, z, cx, cy, out_size=(pw, ph))
        panel = tl.look.grade(panel, **c.grade)
        if vertical:
            half = int(round(e * ph / 2))
            y0 = i * (ph + gap)
            a, b = ph // 2 - half, ph // 2 + half
            out[y0 + a:y0 + b, :] = panel[a:b, :]
        else:
            half = int(round(e * pw / 2))
            x0 = i * (pw + gap)
            a, b = pw // 2 - half, pw // 2 + half
            out[:, x0 + a:x0 + b] = panel[:, a:b]
    return out


# ── the title, written by light, then the flight into its I and out onto the page ──
def add_title_into_i(tl, text, t_title, t_write, t_zoom, t_white, size=0.118, track=0.34):
    w, h = tl.w, tl.h
    font = brand.font(brand.DISPLAY_THIN, min(h * size, w * 0.085))   # ~80% of a vertical frame's width
    tpath = gfx.text_path(text, font, tracking=track)
    tb = tpath.computeTightBounds()
    i_idx = text.index("I")
    glyphs = font.textToGlyphs(text)
    widths = font.getWidths(glyphs)
    i_path = font.getPath(glyphs[i_idx])
    i_path.offset(float(sum(widths[:i_idx])) + track * font.getSize() * i_idx, 0)
    ib = i_path.computeTightBounds()
    pivot = ((ib.left() + ib.right()) / 2, (ib.top() + ib.bottom()) / 2)
    cx0, cy0 = (tb.left() + tb.right()) / 2, (tb.top() + tb.bottom()) / 2
    xx = np.arange(w, dtype=np.float32)

    def matrix(z, drift, extra=1.0):
        s = (1 + drift) * extra * (320.0 ** (z ** 2.2))
        k = fx.smoothstep(0, 0.35, z)
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

    def scale_at(z):
        return 320.0 ** (z ** 2.2)

    def radial_blur(m, ratio):
        """Zoom blur about the frame centre: average the mask over the scales the
        camera passed through during this frame (ratio = previous/current scale)."""
        # enough samples that the smear steps < ~1.5 px at the frame edge
        n = int(np.clip((1 - ratio) * (w / 2) / 1.5, 1, 48))
        if n < 2:
            return m
        acc = np.zeros_like(m)
        for i in range(n):
            sc = ratio ** (i / (n - 1))
            acc += cv2.warpAffine(m, cv2.getRotationMatrix2D((w / 2, h / 2), 0, sc), (w, h))
        return acc / n

    def zoom_at(t):
        return fx.ease_in(fx.window(t, t_zoom, t_white)) ** 0.7

    @tl.overlay(t_title, t_white + 0.001, stage="post")
    def title(t, img, tl):
        z = zoom_at(t)
        # the cast recedes: colour drains to silver-grey, focus goes soft, light drops
        d = fx.ease_in_out(fx.window(t, t_title, t_write + 0.4))
        if d > 0:
            y = fx.luma(img)[..., None]
            img = img * (1 - d) + np.repeat(y, 3, -1) * d
            img = cv2.GaussianBlur(img, (0, 0), 1 + 8 * d) * (1 - 0.42 * d)
        if z > 0:
            # the camera travels: the room pushes in behind the letters, with zoom blur
            acc = np.zeros_like(img)
            for k in range(4):
                sc = 1 + 0.45 * z ** 2 + 0.035 * z * k
                acc += cv2.warpAffine(img, cv2.getRotationMatrix2D((w / 2, h / 2), 0, sc), (w, h),
                                      borderMode=cv2.BORDER_REFLECT)
            img = acc / 4
        drift = fx.window(t, t_write, t_zoom) * 0.025
        m = matrix(z, drift)
        letters = mask_of(tpath, m)
        imask = mask_of(i_path, m)
        # written left → right by a travelling band of light
        sweep = fx.window(t, t_write, t_write + 0.9)
        band = -0.1 + 1.25 * fx.ease_in_out(sweep)
        x0p = w / 2 - (cx0 - tb.left()) * (1 + drift)
        x1p = w / 2 + (tb.right() - cx0) * (1 + drift)
        xn = (xx - x0p) / max(x1p - x0p, 1)
        reveal = fx.clamp01((band - xn) / 0.08)[None, :]
        glint = np.exp(-((xn - band) / 0.035) ** 2)[None, :] * float(0 < sweep < 1)
        letters = letters * reveal
        i_here = imask * reveal
        others = np.clip(letters - i_here, 0, 1)
        z_prev = zoom_at(t - 0.5 / tl.fps)                  # 180° shutter
        if z > z_prev and z < 0.995:
            ratio = scale_at(z_prev) / scale_at(z)
            others = radial_blur(others, ratio) * (1 - z ** 3)
            i_here = radial_blur(i_here, ratio)
        glow = cv2.GaussianBlur(letters, (0, 0), 7) * 0.3 * (1 - z)
        out = img + glow[..., None] * PAPER * 0.8
        out = out * (1 - others[..., None]) + PAPER * others[..., None]
        # the I is a lit surface: it glows harder as we reach it
        halo = cv2.GaussianBlur(i_here, (0, 0), 10 + 40 * z) * (0.25 + 0.9 * z)
        out = out + halo[..., None] * PAPER * 0.6
        out = out * (1 - i_here[..., None]) + PAPER * i_here[..., None]
        out = out + (glint * letters)[..., None] * 0.6
        # arriving: the last frames flare to paper white
        wf = fx.smoothstep(0.7, 0.97, z)
        out = out + (PAPER - out) * wf
        return np.clip(out, 0, 1)


# ── the sign-off: out of the white of the I, the glyph writes itself as it did at the door ──
def add_glyph_signoff(tl, t_hit, t_draw0, t_draw1, end, height=0.28, push=0.05, afterglow=0.12):
    """The intro's glyph door as an ending: the flare of the I burns down to black, a point
    of light writes the glyph with the show glowing inside its strokes, and it holds while
    the camera keeps drifting in."""
    w, h = tl.w, tl.h
    gh = int(min(h * height, w * 0.6))
    alpha, tm = brand.glyph_drawon(gh)
    sigma = max(6.0, gh * 0.021)                      # the travelling light scales with the mark

    @tl.overlay(t_hit, end + 1)
    def signoff(t, img, tl):
        p = fx.window(t, t_draw0, t_draw1)
        soft = 0.07
        reveal = fx.clamp01((p * (1 + soft) - tm) / soft) * alpha
        m = paste_mask(np.zeros(img.shape[:2], np.float32), reveal, w / 2, h / 2)
        inside = 1 - (1 - img) * 0.75
        out = inside * m[..., None]
        if 0 < p < 1:
            head = np.exp(-((tm - p) / 0.035) ** 2) * alpha * (tm <= p + 0.02)
            halo = cv2.GaussianBlur(head, (0, 0), sigma) * 2.0
            out = gfx.paste_alpha(out, np.clip(halo, 0, 1), np.array([1.0, 0.94, 0.84], np.float32),
                                  w / 2, h / 2, 0.55)
        out = gfx.rim(out, m, 0.35)
        s = 1 + push * fx.ease_in_out(fx.window(t, t_hit, end))
        if s > 1.0005:
            out = cv2.warpAffine(out, cv2.getRotationMatrix2D((w / 2, h / 2), 0, s), (w, h), flags=cv2.INTER_LINEAR)
        e = float(np.exp(-max(t - t_hit, 0.0) / afterglow))
        return out * (1 - e) + PAPER * e


# ── the logo on paper: the glyph written in '98 Green', the wordmark in ink ──
def add_paper_logo(tl, t_white, t_mark, end, lock_h=0.36):
    w, h = tl.w, tl.h
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    rad = np.sqrt(((xx - w / 2) / w) ** 2 + ((yy - h * 0.48) / h) ** 2)
    page = (PAPER * (1.0 - 0.045 * rad[..., None] ** 1.6)).astype(np.float32)
    lh = min(h * lock_h, w * 0.34)                    # the lockup fits a vertical frame
    gcx, gcy, gh = gfx.lockup_glyph_box(w, h, lh, 0.0)

    @tl.overlay(t_white, end + 1, stage="post")
    def logo(t, img, tl):
        out = page.copy()
        out = gfx.glyph_drawon(out, fx.window(t, t_white + 0.06, t_mark + 0.3), gcx, gcy, gh,
                               color=brand.GREEN, glow=False)
        tl.layer.clear()
        gfx.draw_wordmark(tl.layer.c, w, h, lh, fx.window(t, t_mark, t_mark + 0.85), color=brand.INK)
        return tl.layer.over(out)
