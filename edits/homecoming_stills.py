"""Stills from the final cut: 16:9 PNGs rendered straight from the edit — lossless, and at
3840×2160 by default, since the clips read from the 4K master. The scope bars are left off,
so every still is the full 16:9 frame; the grade, the cinema pass and the grain are the film's.

    python edits/homecoming_stills.py                 # renders/stills/*.png, 3840×2160
    python edits/homecoming_stills.py --scale 0.5     # 1920×1080
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import homecoming_final as F  # noqa: E402

# (film time, name) — each on the sharpest frame at the peak of the shot
STILLS = [
    (5.72, "01_cast_standing_silent"),
    (10.20, "02_spotlight"),
    (13.60, "03_hands_through_the_sheet"),
    (17.20, "04_singer"),
    (22.88, "05_hair_flip_against_the_light"),
    (41.16, "06_the_glyph_on_their_backs"),
    (45.00, "07_the_drop_beams"),
    (46.78, "08_the_cast_explodes"),
    (53.32, "09_triptych"),
    (58.12, "10_handstand_in_red"),
    (61.60, "11_tower_of_bodies"),
    (64.02, "12_homecoming_title"),
]

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=float, default=2.0, help="1.0 = 1920×1080")
    ap.add_argument("--out", default="renders/stills")
    ap.add_argument("--only", nargs="*", help="names (or prefixes) to render")
    a = ap.parse_args()
    W, H = int(1920 * a.scale) // 2 * 2, int(1080 * a.scale) // 2 * 2
    tl = F.build(F.footage_clips(), W, H)
    tl.bars = lambda t: 0.0                          # the full 16:9 frame
    Path(a.out).mkdir(parents=True, exist_ok=True)
    for t, name in STILLS:
        if a.only and not any(name.startswith(o) for o in a.only):
            continue
        print(tl.stills([t], f"{a.out}/HOMECOMING_{name}.png")[0], flush=True)
