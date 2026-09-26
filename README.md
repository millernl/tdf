# District98 — Homecoming after-movie

A 30-second after-movie of **Homecoming**, the theatre show of dance school District98,
cut from the live registration and dressed in the District98 identity
(*Logo & Identity Design*, Phase 5, Bart de Graaff, Oct 2021).

## The one-minute cut (`edits/homecoming60.py`)

Cut to the Iron mix, conformed on its bar grid to 31 bars (source bars 5–8 | 9–12 | 17–20 |
29–32 | 33–40 | 41–44 | 45–46 | 76, splices on downbeats). The drums play a 3-3-2 gallop
(1 · 2& · 4) and the fast sections cut on it. The music stops dead at 57.2 s; the logo is
written in the silence.

| bars | time | beat |
|---|---|---|
| 1–4 | 0–7.4 | drone · the glyph writes itself with the show inside, we fly through · a girl alone at a table |
| 5–12 | 7.4–22.2 | the drums · black & white journey: walking silhouettes, the spotlight ring, the projected window of a home, the audience's view |
| 13–16 | 22.2–29.5 | the build rides the gallop · in the drum gap the frame closes to black |
| 17–24 | 29.5–44.3 | the drop bursts open in colour · jerseys, kids, lasers, triptych, speed ramp · a handstand freezes as the drums fall away |
| 25–28 | 44.3–51.7 | through black into the heart: the group hug, faces, the District98 hoodies |
| 29–31 | 51.7–57.2 | everything returns: a leap in front of the cast · HOMECOMING written over them · into the I, onto a white page |
| — | 57.2–60 | silence · the glyph written in '98 Green', the wordmark in ink |

## The 30-second cut (`edits/homecoming.py`)

130 BPM (scored in the spirit of Woodkid's *Iron*), 30 s, English, no text but the title.

| bars | time | beat |
|---|---|---|
| 1–2 | 0.0–3.7 | the dancer glyph writes itself with the show inside it → the camera flies through it |
| 3–6 | 3.7–11.1 | the story in high-contrast black & white, 2.39 scope: silhouettes, the spotlight ring, the girl at the table |
| 7–12 | 11.1–22.2 | the drop: the stage lights snap to beams, colour floods in (remapped to green/gold), 16:9, cuts on the beat, triptych, freeze (the music stops with it), speed ramp |
| 13–14 | 22.2–25.8 | the heart: warm gold, a leap in front of the whole cast, the cast clapping |
| 15–17 | 25.8–30.0 | HOMECOMING written by light over the cast → fly into the *I* → it turns '98 Green' → the logo writes itself |

Looks (`afterfilm/fx.py` → `PRESETS`, also exported as `.cube` in `brand/`):
**Iron** (panchromatic B&W), **GreenGold** (stage purples → muted teal, reds/oranges → gold),
**Silver** (clean, faded colour for the heart — no sepia). On top: filmic tone curve, halation, anamorphic streaks on the stage
lights, bloom, lens fringing, gate weave, grain. The low-bitrate export is deblocked,
denoised and CAS-sharpened on decode (`media.RESCUE_PRE/POST`).

## Layout

```
brand/            logo SVGs (extracted from the identity PDF), fonts, District98_GreenGold.cube
afterfilm/        the engine
  brand.py        palette, type, logo paths, glyph draw-on map
  fx.py           the grade (Look), bloom/grain/vignette, transitions
  gfx.py          Skia vector layer: type, glyph window/zoom, lockup, letterbox + labels
  timeline.py     clips (speed ramps, Ken Burns), shots, overlays, render loop
  score.py        synthesised temp score, 130 BPM (drums, timpani, low brass, clean logo bells)
  music.py        conform a track to length on its bar grid (downbeat splices)
  scenes.py       glyph door, triptych, title-into-the-I, logo on paper
  analyze.py      reads the full show → numbers, applause, tempo, top moments, contact sheets
edits/homecoming60.py the one-minute edit, cut to the Iron mix (music/iron_MIX.mp3, not in git)
edits/homecoming.py   the 30-second edit
tools/            extract_logo.py, fetch_footage.py
```

## Workflow

```bash
pip install -r requirements.txt
python tools/fetch_footage.py                       # draft release → footage/
python -m afterfilm.analyze footage/*.mp4 --out work/analysis
python -m afterfilm.analyze --strips footage/show.mp4 A=1:12:40 B=2:18:00 --out work/strips
python edits/homecoming.py --edl                                   # cut list
python edits/homecoming.py --stills 2.9 11.5 27.4 --scale 0.5      # quick frames
python edits/homecoming.py --out renders/homecoming.mp4            # master + _nomusic version
```

`--scale 0.5` renders a half-size preview. `AFTERFILM_FFMPEG` points at a full ffmpeg build.

## Footage handover

Footage and renders never go in git (the repo is public). The recording is attached to a
**draft** release tagged `footage` — drafts are visible only to collaborators. Max 2 GB per
file; longer recordings go up in parts and are laid end to end on one show clock.
