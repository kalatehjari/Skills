---
name: cubism-animator
description: Make cubist / avant-garde animated films (music videos, poems, stories) where a character is drawn as planes of colour, lines and shapes rather than a likeness, cut to the beats of the user's own song. Use whenever the user asks for an artistic, abstract, conceptual, cubist, Picasso / Kandinsky / Delaunay / Malevich-style, avant-garde or "thought-provoking" animation or music video, or wants their character "not as the exact person", even if they don't say cubism.
---

# Cubism-Animator

Make a moving painting. The character is a set of coloured planes, the antagonist a black wedge, the
drum a Delaunay disc, and the story is told by **what happens to the planes**: they drift apart in
loss, shatter and grow extra eyes under pressure, burst on the moment of rupture, and slide back into one
face at peace. The user rated this mode "much better" than both a photo slideshow (1/10) and a literal
cartoon. Keep it bold, conceptual and readable: one big shape, one colour conflict and one motion per shot.

## What you need
- The **animation-studio** skill/plugin: its engine renders canvas frames in headless Chromium and muxes with ffmpeg. Skim its SKILL.md once.
- This bundle: `assets/cubism.js` (the library), `assets/film-template.js`, `scripts/`, `references/`. If they are not next to this file, look in the user's Dropbox at `/Claude Products/Skills/cubism-animator/`, or ask for `cubism-animator.zip`.
- `pip install librosa --break-system-packages` (song analysis).

## Workflow

### 1. Read the song
`python3 scripts/song_info.py song.mp3 work/` prints the embedded lyrics (Suno exports carry them as ID3
tags, with section labels) and writes `structure.png` + `similarity.png`. Read both images: repeated
sections show as off-diagonal stripes, while breaks and solos show in the spectrogram. Speech-recognition
model hosts are usually blocked here; if there are no embedded lyrics, ask the user for them. For a poem or
story with no song, use the engine's synthesized music instead (see animation-studio).

### 2. Write the concept, in geometry
Read `references/vocabulary.md`. Translate the lyrics, find the inner arc (for example wholeness → emptiness
→ siege → rupture → reconciliation → rebirth → departure), and assign each section a **plane state**, a
**palette** and **one art-historical move**. Write a shot table in bars. Tell the user the concept in two or
three sentences and proceed: they give creative authority and dislike being asked many questions.

### 3. Scaffold
```bash
node <animation-studio>/scripts/new-project.js <kebab-title> --format 16:9
cd <kebab-title> && mkdir -p assets && cp <song> assets/song.mp3
eval "$(sh <this-skill>/scripts/setup_env.sh . | tail -1)"   # Chromium no-sandbox wrapper + Vazirmatn/Cormorant fonts
node engine/render.js analyze assets/song.mp3                 # beats.js + sections in bars
cp <this-skill>/assets/cubism.js . && cp <this-skill>/assets/film-template.js film.js
```
- `index.html`: `<script src="beats.js"></script>` before `score.js`; `<script src="cubism.js"></script>` before `film.js`.
- `score.js` must export `beats: A.beats` and `subtitles` (`{t, end, fa, en, key}`, one line per 4 bars from each section's first downbeat; `key:'c'` for chorus lines), plus `DURATION`, `FPS`, `T`. Copy `references/example-score.js` and edit it.
- `song.js`: `MIX.loadAudio('assets/song.mp3', {length: DURATION})` → `MIX.master(mix, 0.8, undefined, {lufs: -14})` → `writeWav('out/music.wav')`. Never re-synthesise the user's music.
- For non-Persian lyrics, change the Vazir font in `lyrics()` and the newsprint word in `face()` (cubism.js) to suit the language.

### 4. Set the identity signs
From the reference photos, pick 3-4 signs and set them at the top of film.js:
`CUBE.setLook({ hair, iris, lips, tee })`. Do not chase likeness; the bob shape, eye colour, lips and
clothing colour are enough for viewers to know her.

### 5. Build the shots
Write `shot(bar0, bar1, (ctx, t, u) => {...}, 'cut'|'fade'|'flash', dur)` in film.js, using the CUBE API
(full list in vocabulary.md §4). `references/example-tan-be-tan-cubist.js` is a complete 4:53 film. Lift
whole scenes from it (the siege, the marionette, the mirror merge, the burst, the white rectangle) and
re-cast them for the new song. Then invent at least two moves that aren't in the example, so each film has
its own idea.

### 6. Review like a painter
`node engine/render.js sheet 0 <DURATION> 48 8`, then read `out/sheet.png`: is the arc readable from
thumbnails, and do the palettes change by act? Then `render.js stills <t…>` at 8-12 moments, tiled 2×2
with OpenCV, read at full size. Check that the lyric strip doesn't cover the mouth, that dark shapes aren't
lost on dark fields, that RTL text doesn't collide with discs, and that nothing busy competes with the
main shape. Fix and re-check before rendering.

### 7. Render (resumable) and deliver
- Container restarts kill long renders outright. Always use the chunked renderer, fully detached:
  `setsid nohup sh <this-skill>/scripts/chunk_render.sh . 3 > /dev/null 2>&1 < /dev/null & disown`
  It patches a `chunk` mode into the engine, renders 600-frame chunks (re-running resumes), joins them into `out/video.mp4`, and writes `ALLDONE n/n` to `out/chunks.log`. Expect ~3.5 fps with 3 workers (a 5-minute song ≈ 45 min). Poll with `sleep 590`; if a poll looks frozen, check `ps -o etime` and `uptime`, and relaunch the script if its process is gone.
- Then run `setsid nohup sh <this-skill>/scripts/finish.sh . "<Artist> - <Title> (Cubist Music Video)" > /dev/null 2>&1 < /dev/null & disown`. It writes a YouTube-ready 1080p master (CRF 20, ~150 MB; files near 700 MB can vanish from the outputs panel) and a ~26 MB 720p preview to `/mnt/user-data/outputs/`, then `out/finish.done`. Send the preview with SendUserFile.
- Sample 8 frames from the preview into one image and look at it before announcing.

### 8. Report
Explain the concept in one sentence, then the arc as plane states by section (for example, "in the chorus her face shatters
on every beat and grows extra eyes"). Add honest limits: lyrics change per 4 bars rather than being word-synced, and audio is checked by
measurement, not listening. Offer one next step, such as a 9:16 cut, another movement (Futurism, Bauhaus,
Persian-miniature geometry), or fixing named timestamps.
