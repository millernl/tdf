# District98 — Homecoming after-movie

A 30-second after-movie of **Homecoming**, the theatre show of dance school District98,
cut from the live registration and dressed in the District98 identity
(*Logo & Identity Design*, Phase 5, Bart de Graaff, Oct 2021).

## The final cut (`edits/homecoming_final.py`)

Cut to the Iron arrangement delivered by the client (`music/Iron_Homecoming_Edit.mp3`,
not in git): source bars 1–23 | 32 | 33–40 | 73–76 at 130 BPM. The mix is used as-is
(first downbeat trimmed onto the grid, a static −1.5 dB so it doesn't clip). We arrive
through the I on its last hit; the logo is written in silence. 69 s.

| bars | time | beat |
|---|---|---|
| 1–8 | 0–14.8 | drone · the glyph door · home in black & white: silhouettes, the table, the bedroom, the window, hands through a sheet |
| 9–16 | 14.8–29.5 | drums · walking out, the singer turns — a silhouette's head-turn answers — raised arms, a hair flip against the light, grey haze, bowed heads, the cast in black |
| 17–23 | 29.5–42.5 | brass, colour in scope · a sheet whipped through red, a girl pulled across the floor, arms up, the red beanie kids, the kids' crew, magenta, amber kids, the glyph on their backs |
| 24 | 42.5–44.3 | a line of dancers stares down the lens · the frame closes in the drum gap |
| 25–32 | 44.3–59.1 | the drop · lights snap to beams, the cast explodes, jerseys, red light, light trails, a triptych of hair in three colours, lasers, amber, the D98 shirts · the handstand freezes |
| 33–36 | 59.1–65.8 | one embrace · HOMECOMING over it · through the I on the last hit |
| — | 65.8–69 | silence · the glyph in '98 Green', the wordmark in ink |

`python edits/homecoming_final.py --verify` scans every clip's source range frame by
frame for camera cuts or stray frames from another angle.

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
edits/homecoming_final.py the final cut, to the client's Iron arrangement (music/, not in git)
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
