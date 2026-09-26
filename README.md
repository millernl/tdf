# District98 — Homecoming after-movie

A 30-second after-movie of **Homecoming**, the theatre show of dance school District98,
cut from the live registration and dressed in the District98 identity
(*Logo & Identity Design*, Phase 5, Bart de Graaff, Oct 2021).

## The idea

The dancer glyph is the door. It writes itself stroke by stroke, we fly through it into
the show — and at the end the show shrinks back into the glyph on '98 Green'. The show
comes home.

| time | beat |
|---|---|
| 0.0–2.6 | glyph writes itself (brush draw-on) → zoom-through into the show |
| 2.6–9.6 | the story: scope letterbox, slow-mo, stripe / swoosh / light-slit transitions, footer labels in the bars |
| 9.6–12.0 | breath → **HOMECOMING**, the show seen through the letters → fly through the *I* |
| 12.0–22.0 | energy: bars open to full frame, cuts on the beat, whips, triptych, freeze-frame duotone, speed ramp |
| 22.0–26.6 | the heart: bars return, finale + bows, warm light dissolves, *Welkom thuis.* |
| 26.6–30.0 | the show shrinks into the glyph → white logo on '98 Green', wordmark tracks in, district98.nl |

## Layout

```
brand/            logo SVGs (extracted from the identity PDF), fonts, District98_GreenGold.cube
afterfilm/        the engine
  brand.py        palette, type, logo paths, glyph draw-on map
  fx.py           the grade (Look), bloom/grain/vignette, transitions
  gfx.py          Skia vector layer: type, glyph window/zoom, lockup, letterbox + labels
  timeline.py     clips (speed ramps, Ken Burns), shots, overlays, render loop
  sfx.py          synthesised sound design (whoosh, sub hit, riser, shutter, ticks)
  analyze.py      reads the full show → numbers, applause, tempo, top moments, contact sheets
  plates.py       stand-in plates for the animatic
edits/homecoming.py   the edit: structure, graphics, sound; animatic + footage casts
tools/            extract_logo.py, fetch_footage.py
```

## Workflow

```bash
pip install -r requirements.txt
python tools/fetch_footage.py                       # draft release → footage/
python -m afterfilm.analyze footage/*.mp4 --out work/analysis
python -m afterfilm.analyze --peek footage/show.mp4 1:12:40 1:12:43 --out work/peek
python edits/homecoming.py --animatic --out renders/animatic.mp4
python edits/homecoming.py --animatic --stills 2.2 11.7 27.2 --scale 0.5   # quick frames
```

`--scale 0.5` renders a half-size preview. `AFTERFILM_FFMPEG` points at a full ffmpeg build.

## Footage handover

Footage and renders never go in git (the repo is public). The recording is attached to a
**draft** release tagged `footage` — drafts are visible only to collaborators. Max 2 GB per
file; longer recordings go up in parts and are laid end to end on one show clock.
