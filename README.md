# District98 — Homecoming after-movie

A 30-second after-movie of **Homecoming**, the theatre show of dance school District98,
cut from the live registration and dressed in the District98 identity
(*Logo & Identity Design*, Phase 5, Bart de Graaff, Oct 2021).

## The final cut (`edits/homecoming_final.py`)

Cut to the Iron arrangement delivered by the client (`music/Iron_Homecoming_Edit.mp3`,
not in git): source bars 1–23 | 32 | 33–40 | 73–76 at 130 BPM. The mix is used as-is
(first downbeat trimmed onto the grid, a static −1.5 dB so it doesn't clip). We arrive
through the I on its last hit; the logo is written in silence. 69 s.

Two looks only: **Iron** (black & white) and **Ember** (red/orange). Ember renders a shot's
black & white tones through the palette measured from the red solo shots, so every colour
shot matches them; the three naturally red shots it was measured from keep the natural grade.
Both are in `brand/` as `.cube` LUTs.

| bars | time | beat |
|---|---|---|
| 1–8 | 0–14.8 | drone · the glyph door opens on the show's first shot, the cast standing silent · home in black & white: the table, a dancer in the spotlight, the window, hands through a sheet |
| 9–16 | 14.8–29.5 | drums · walking out, the singer turns — a silhouette's head-turn answers — raised arms, a hair flip against the light, grey haze, bowed heads, the cast in black |
| 17–23 | 29.5–42.5 | brass, Ember · silhouettes with raised arms, a girl pulled across the floor, arms up, the red beanie kids, the kids' crew, silhouettes bent low, amber kids, the glyph on their backs |
| 24 | 42.5–44.3 | a line of dancers stares down the lens · the frame closes in the drum gap |
| 25–32 | 44.3–59.1 | the drop · beams, the cast explodes, hair whipped through haze, the light snaps to red, light trails, a triptych of hair, silhouettes over the audience, the D98 shirts · the handstand freezes |
| 33–36 | 59.1–65.8 | black & white · two dancers entwined, a tower of bodies, the whole cast in one embrace · HOMECOMING · through the I on the last hit |
| — | 65.8–69 | silence · the glyph in '98 Green', the wordmark in ink |

`python edits/homecoming_final.py --verify` scans every clip's source range frame by
frame for camera cuts or stray frames from another angle.

**4K master** — the working copy is 720p; the 4K original was pulled only where the cut
needs it (`handover/HOMECOMING_segments.csv`, cut losslessly in LosslessCut and merged into
one file). `python -m afterfilm.conform work/hq_segments.json <720p> <4K segments>` finds
each segment in it by matching frames and writes `edits/data/hq_map.json`; clips are still
addressed in 720p time and read from the 4K file, downscaled with no rescue filtering. The
grain is back to a light texture.

**9:16** — `python edits/homecoming_final.py --vertical` renders 1080×1920. Clips decode at
the source's full 1280×720 and each shot places its vertical window per `V_FRAMING`
(suggested by `afterfilm/vertical.py` from motion and detail, corrected by eye on its review
sheets; more than one key pans to follow the dancer). The scope bars become a 4:5 window
that still closes in the drum gap and bursts open on the drop; the triptych stacks into
rows; the title, glyph and lockup are sized to the frame width.

## The 15-second teaser (`edits/homecoming_teaser.py`)

9:16, 1080×1920, built from the final cut's clips and grades. The music starts on the
vocal's "and faith" (bar 24), swelling in out of its own reverse reverb (the words reversed,
put through a synthetic hall, reversed back) and ringing in that hall until the drop. It runs
through the drop's first phrase (bars 25–28), then one equal-power splice to bar 35 for the
title and the last hit. It is read once and sliced in memory, because seeking into the MP3
garbles its first frame.

Effects borrowed from a reference edit (work/reference, not in git) and kept to the palette:
a backlight striking behind silhouettes, staccato punch-in cuts, single negative frames,
four-frame motion-blur whips (`smear`) and a single-frame strobe into a shot (`strobe`).

| bars | time | beat |
|---|---|---|
| 24 | 0–1.8 | black & white · out of black the backlight strikes behind the silent cast, flickering silhouettes as the reverb swells · "and": the light lands · "faith": three punch-ins to one dancer's profile · the frame closes to a slit, two negative frames |
| 25–28 | 1.8–9.2 | the drop bursts it open · the lights snap to beams, a whip into a lunge at the lens (D98 shirt), hair whipped through amber, the snap to red, a whip into the light trails, the triptych stacked in rows, the handstand strobing in and freezing |
| 35–36 | 9.2–12.2 | HOMECOMING written over the frozen handstand · through the I on the last hit |
| — | 12.2–15 | silence · the white burns down to black and the glyph writes itself, as at the film's door (`scenes.add_glyph_signoff`) |

Every clip decodes at the master's full 3840×2160, so a 9:16 window at zoom 1 is a
1215×2160 crop, downscaled rather than blown up (the triptych rows decode at 1920×1080).
The windows (`FRAMING`) are placed on the action for the teaser's own shot lengths.

## Stills (`edits/homecoming_stills.py`)

Twelve 16:9 PNGs rendered straight from the final cut, lossless, at 3840×2160 from the 4K
master (`--scale 1` for 1920×1080). The scope bars are left off, so each still is the full
frame. The cinema pass and the title's blur radii scale with the frame, so a 4K still has the
same halation and bloom as the 1080p film.

## C.I.T.Y. reel (`edits/city_reel.py`)

A 31-second 9:16 reel of Color In The Yard's set (show 1:37:47–1:52:12). It covers four
songs, each in its own light, played in sync with their live sound and cut downbeat to
downbeat. The beat grid comes from Essentia's multi-feature tracker (song tempos 150 / 86 /
79 / 100 BPM) with the bar phase read from kick, backbeat and chord changes
(`edits/data/city_grid.json`).

| time | what |
|---|---|
| 0–3.2 | walk-on · song 1's intro; the white beams strike on, the three walk into the light |
| 3.2–6.4 | song 1 · her close-up in the haze (stepped snap-in) |
| 6.4–12.0 | song 2 · purple · his close-up strobing in, the two of them together |
| 12.0–18.0 | song 3 · violet · a whip into the cap close-up, then the centre spot |
| 18.0–22.8 | song 4 · yellow beams striking on, a staccato punch-in on the cap |
| 22.8–25.2 | walk-off · song 4's last bar, cut on its final hit |
| 25.2–27.2 | the rig's own colour cycle (white, blue, yellow, purple, green, pink), sped up |
| 27.2–31.0 | the logo on the screen lifts off, letters flying forward (C first, Y on the impact), dots tick in; COLOR IN THE YARD writes on |

Sound: levels are matched per bar and splices are equal-power, just ahead of each
downbeat. Each change of song gets an echo-out, and the final hit rings into a hall. The
show's own low rumble builds under the logo, and one synthesized sub impact lands with the
letters. The logo mark is traced from the frames where it holds still on the screen:
about 11 s averaged, haze removed by a morphological opening, then thresholded. It is cached
in `work/city/`; the traced mark is theirs, so it stays out of git. The tagline is set in
Bebas Neue (`brand/fonts/city`, OFL).

The picture is offline until the 4K is pulled. `python edits/city_reel.py --segments` writes
`handover/CITY_segments.csv`; cut those spans from the original in LosslessCut and export
them as one file, `footage/CITY_4K.mp4`. Then `python -m afterfilm.conform` on that list
writes `edits/data/city_map.json`, and the reel reads every shot from the 4K.

## Battle of the Districts outro (`edits/bod_outro.py`)

A 5-second 9:16 outro on the cream Battle of the Districts screen: clean and flat, on a slow
hip-hop pulse (90 BPM, a hit every other beat).

| time | what |
|---|---|
| 0–0.67 | the screen; a reversed 808 swells into the first hit |
| 0.67 | hit 1 · the two D's start to unwind from the top of the seam behind a clean edge, round the right D and across the seam round the left one |
| 1.83–2.0 | a ghost kick, then hit 2 · the last of the orange goes, BATTLE / OF THE and DISTRICTS snap apart and leave the frame |
| 2.12–3.33 | the District98 character is written stroke by stroke in the screen's deep green (`brand.glyph_drawon`) |
| 3.33–5.0 | hit 3 · the character is complete and holds alone, centred on the district map, as the 808 rings out |

The camera pushes in slowly and punches in a touch on each hit; the map moves at half its
speed, for depth. There is no glow: the film pass keeps only its grain and gate weave, with
a soft vignette. The sound is synthesised in `mix()`: round sine kicks and 808s (G, then E
sliding to D, then E), warmed so they carry on a phone, gently low-passed from about 900 Hz,
with a little room on the last hit. The screen and the lockup are read from `work/bod/`,
which is not in git.

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
**Iron** (panchromatic B&W) and **Ember** (red/orange); the earlier cuts also used
**color** (stage purples → muted teal, reds/oranges → gold) and **silver**. On top: filmic tone curve, halation, anamorphic streaks on the stage
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
