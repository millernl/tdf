"""Pull the District98 logo out of the identity PDF as clean SVG paths.

Usage: python tools/extract_logo.py District98_Branding_Phase5.pdf
Writes brand/logo_glyph.svg, brand/logo_wordmark.svg, brand/logo_lockup.svg.
"""
import sys
from pathlib import Path

import pymupdf

OUT = Path(__file__).resolve().parent.parent / "brand"
PAGE = 2                      # four-up lockup page (green / black / white / off-black)
QUAD = pymupdf.Rect(0, 0, 1596, 798)   # top-left: white logo on '98 Green'


def to_svg_path(items):
    d, cur = [], None
    for it in items:
        kind = it[0]
        if kind == "re":
            r = it[1]
            d.append(f"M{r.x0:.3f} {r.y0:.3f}H{r.x1:.3f}V{r.y1:.3f}H{r.x0:.3f}Z")
            cur = None
            continue
        if kind == "qu":
            q = it[1]
            d.append("M{:.3f} {:.3f}L{:.3f} {:.3f}L{:.3f} {:.3f}L{:.3f} {:.3f}Z".format(
                q.ul.x, q.ul.y, q.ur.x, q.ur.y, q.lr.x, q.lr.y, q.ll.x, q.ll.y))
            cur = None
            continue
        start = it[1]
        if cur is None or abs(cur.x - start.x) > 1e-3 or abs(cur.y - start.y) > 1e-3:
            d.append(f"M{start.x:.3f} {start.y:.3f}")
        if kind == "l":
            d.append(f"L{it[2].x:.3f} {it[2].y:.3f}")
            cur = it[2]
        elif kind == "c":
            p1, p2, p3 = it[2], it[3], it[4]
            d.append(f"C{p1.x:.3f} {p1.y:.3f} {p2.x:.3f} {p2.y:.3f} {p3.x:.3f} {p3.y:.3f}")
            cur = p3
    return "".join(d) + "Z"


def write(name, paths, bbox, pad=0):
    x0, y0 = bbox.x0 - pad, bbox.y0 - pad
    w, h = bbox.width + 2 * pad, bbox.height + 2 * pad
    body = "\n".join(f'  <path d="{p}"/>' for p in paths)
    (OUT / name).write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.3f} {y0:.3f} {w:.3f} {h:.3f}" '
        f'fill="#FFFFFF">\n{body}\n</svg>\n')


def main(pdf):
    page = pymupdf.open(pdf)[PAGE]
    shapes = [dr for dr in page.get_drawings()
              if QUAD.contains(dr["rect"]) and dr["rect"].width < 400 and dr.get("fill") == (1.0, 1.0, 1.0)]
    shapes = [s for s in shapes if s["rect"].width > 1]          # drop the zero-size stray point
    glyph = [s for s in shapes if s["rect"].y1 < 420]
    word = [s for s in shapes if s["rect"].y0 > 420]
    union = lambda ss: pymupdf.Rect(min(s["rect"].x0 for s in ss), min(s["rect"].y0 for s in ss),
                                    max(s["rect"].x1 for s in ss), max(s["rect"].y1 for s in ss))
    gp = [to_svg_path(s["items"]) for s in glyph]
    wp = [to_svg_path(s["items"]) for s in word]
    write("logo_glyph.svg", gp, union(glyph))
    write("logo_wordmark.svg", wp, union(word))
    write("logo_lockup.svg", gp + wp, union(glyph + word))
    print(f"glyph {len(glyph)} path(s) {union(glyph)}\nwordmark {len(word)} letters {union(word)}")


if __name__ == "__main__":
    main(sys.argv[1])
