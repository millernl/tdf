# District98 — Homecoming after-movie

A 30-second after-movie of **Homecoming**, the theatre show of dance school District98,
cut from the live registration and dressed in the District98 identity
(*Logo & Identity Design*, Phase 5, Bart de Graaff, Oct 2021).

## The one-minute cut (`edits/homecoming60.py`)

Cut to the Iron mix, conformed on its bar grid to 32 bars (source bars 5–12 | 17–20 |
31–36 | 39–48 | 73–76, splices on downbeats) so the track's whole outro fill plays out
before its hard stop at 59.1 s; the logo is written in the silence after (62.3 s total).
The drums play a 3-3-2 gallop (1 · 2& · 4) and the fast sections cut on it.

| bars | time | beat |
|---|---|---|
| 1–4 | 0–7.4 | drone · the glyph writes itself with the show inside, we fly through and stay with the silhouettes |
| 5–8 | 7.4–14.8 | the drums · home, in black & white: a girl alone at the table, the bedroom, the window, hands pressing through a sheet |
| 9–12 | 14.8–22.2 | the journey: walking silhouettes, a singer turning away, the spotlight ring, bodies under the sheet |
| 13–14 | 22.2–25.8 | the build on the gallop · a stutter · in the drum gap the frame closes to black |
| 15–20 | 25.8–36.9 | the drop bursts open in colour · jerseys, kids, a triptych of three solos, a speed ramp · a handstand freezes |
| 21–24 | 36.9–44.3 | the heart: the whole-cast hug, faces, two voices, the District98 hoodies |
| 25–28 | 44.3–51.7 | the return: the cast explodes out of the haze, a powermove in light trails, the audience |
| 29–32 | 51.7–59.1 | the outro fill: the cast clapping (finale strobe removed) · HOMECOMING · into the I, onto a white page |
| — | 59.1–62.3 | silence · the glyph in '98 Green', the wordmark in ink, a low breath of sound |

`python edits/homecoming60.py --verify` scans every clip's source range frame by frame for
camera cuts or stray frames from another angle.

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
