---
name: music-video-director
description: Direct and render a story-driven, hand-drawn animated music video (16:9 YouTube by default) for the user's own song, starring a character designed from their reference photos. Use this whenever the user uploads a song (mp3/wav) and asks for a music video, animated video, visualiser, story video or "something for YouTube" for it, especially Rosha songs, Persian/Farsi lyrics, or a recurring character from their images, even if they don't say "animation". Prefer it over photo slideshows or Ken Burns montages, which this user rejects.
---

# Music Video Director

You are the executive producer and creative director. The user hands over a song plus character reference
images and wants a film that tells the song's story, not a slideshow of their pictures. A previous attempt
that animated the photos with pans, grades and lyric text was rated "1/10, a cheap slideshow". The version
that worked built the character as an animated drawing, gave her an antagonist and a metaphor, and cut
every scene to the song's real beats. Aim for that.

## What you need
- The **animation-studio** skill/plugin (its engine renders canvas frames in headless Chromium and muxes with ffmpeg). Load it and skim its SKILL.md once; this skill adds the story method, a reusable cast rig and the fixes for this sandbox.
- This skill's bundle: `assets/cast.js`, `assets/film-skeleton.js`, `scripts/`, `references/`. If those files are not next to this SKILL.md, fetch them from the user's Dropbox at `/Claude Products/Skills/music-video-director/` (Dropbox `fetch` / `download_link`), and save them into the project.
- Python `librosa` (`pip install librosa --break-system-packages`).

## Workflow

### 1. Listen with your eyes
`python3 scripts/song_info.py song.mp3 work/` prints the embedded lyrics (Suno exports carry them as
ID3 `lyrics-*` tags, with [verse]/[chorus] labels) and writes `structure.png` + `similarity.png`.
Read both images. The similarity matrix shows repeated sections as off-diagonal stripes; the spectrogram
shows drops, breaks and the solo. Speech-recognition model hosts (Hugging Face etc.) are usually blocked
here, so don't burn time on Whisper. If there are no embedded lyrics, ask the user for them.

### 2. Write the treatment before any code
Read `references/story-craft.md`. Translate the lyrics, pick ONE central metaphor that the character can
act on, and map the arc onto sections in bars. Write a shot table (bars → what happens). Briefly tell
the user the concept in two or three sentences, then proceed. They have given you creative authority;
don't stall on questions.

### 3. Scaffold and wire the song
```bash
node <animation-studio>/scripts/new-project.js <kebab-title> --format 16:9
cd <kebab-title> && cp <song> assets/song.mp3
eval "$(sh <this-skill>/scripts/setup_env.sh . | tail -1)"   # Chromium no-sandbox wrapper + Vazirmatn/Cormorant fonts
node engine/render.js analyze assets/song.mp3       # beats.js, sections in bars
```
- `index.html`: add `<script src="beats.js"></script>` before `score.js`, and `<script src="cast.js"></script>` before `film.js`. Copy `assets/cast.js` into the project.
- `score.js`: clock from `beats.js` (`makeClock({ beats: A.beats, downbeat: A.downbeat, beatsPerBar: A.meter })`), `DURATION` = song length, `S` sections in bars, `subtitles` (4 bars per line from each section's first downbeat, `{t, end, fa, en, key}`), `ev` story events, `beats: A.beats`. `references/example-score-tan-be-tan.js` is a complete one.
- `song.js`: just `MIX.loadAudio('assets/song.mp3', {length: DURATION})` → `MIX.master(mix, 0.8, undefined, {lufs: -14})` → `writeWav('out/music.wav')`. Never re-synthesise the user's music.

### 4. Cast the character
Translate the photos into the rig: `R.setLook({ skin, skinSh, hair, iris, lip, tee })` at the top of
film.js. The rig's heroine has a chin-length black bob with side fringe, thick brows and amber eyes;
for other hair, edit the hair paths in `face()` and `profile()`. Render a cast sheet first (faces in 3
expressions, profile, walk/run/kneel/hug bodies, the antagonist, arms, door) with `render.js stills 1` and
look at it. Fix proportions before animating: viewers forgive simple backgrounds, not a wrong face.

Rig API (all origins in canvas px):
- `R.face(ctx,x,y,{s,eyes 0-1.3,look,lookY,brows:'neutral|worried|determined|calm|up',mouth:'closed|part|open|scream|smile',tears,wet,wind,light,tint,blush,reflect(ctx,x,y,r),tee,teeColor})`
- `R.profile(ctx,x,y,{s,dir,eyes,brows,mouth,tears,silhouette,color})`
- `R.body(ctx,x,y_feet,{s,dir,pose:'stand|walk|run|kneel|hug|custom',phase,j:{hip,lean,legF,legB,armF,armB,head},silhouette,color,noShadow,head:{…}})` → `{hip,head,wristF,wristB,sh}` (for attaching strings or props)
- `R.him(ctx,x,y,{s,dir,pose:'stand|walk|drum|dagger|puppet|kneel',strike 0-1,eyes glow 0-1})` → `{r,l,head}`: a faceless coat figure, reusable as any antagonist/"you"
- `R.arm(ctx,fromX,fromY,handX,handY,{grip,spread,mirror,sleeve,skin,w})`, `R.drum(...{hit,crack})`, `R.door(...{keyTurn,open})`

### 5. Build the film
Start from `assets/film-skeleton.js` (helpers: beat-locked `kick(t)`/`lastBeat`, `cam`, `shake`,
`desert()` with 7 palettes, `sandWind`, `rain`, `embers`, `lightning`, `redVoid`, `proscenium`,
`strings`, `hallway`, Persian+English `lyrics()` overlay, and a shot compositor with cut/fade/flash).
Write shots as `shot(bar0, bar1, (ctx,t,u)=>{...}, transition)`. The full Tan Be Tan film
(`references/example-film-tan-be-tan.js`) shows every pattern in use; borrow freely.

Principles that made it work:
- **Cut on bar lines; hit on beats.** In choruses and builds something lands on every beat (a hand, a pose snap, a drum cut, a flash). In verses, slow camera moves across 4 bars.
- **Mix scales.** Alternate tiny silhouettes in vast landscapes with extreme close-ups of her eyes and face; the close-ups carry emotion, the wides carry story.
- **Light is the cheapest drama.** A huge sun or glow behind a silhouette; colour by act (cold night → amber desert → blood red siege → teal storm → ember peace → dawn rebirth → gold outro).
- **Return images transformed** (the same desert, now sprouting).
- **Keep lyrics legible**: bottom gradient band; fade lines in/out within their own window so consecutive lines never overlap.

### 6. Review like a director
`node engine/render.js sheet 0 <DURATION> 48 8` then read `out/sheet.png`: is the story readable from
thumbnails alone? Then `render.js stills <t…>` at 8-12 key moments, combined into 2×2 grids with
OpenCV and read at full size. Check faces cropped, figures lost against same-coloured shapes (a black
silhouette on a black sun vanishes; use a pale sun), lyric collisions, and characters cut by frame edges.
Fix and re-check before the long render.

### 7. Render and deliver (sandbox-specific, these all bit before)
- Launch the render fully detached, or the tool harness may kill the encoders mid-render:
  `setsid nohup node engine/render.js video 3 > out/render.log 2>&1 < /dev/null & disown`
  It runs at ~3.3 fps with 3 workers (a 5-minute song ≈ 45 min). Poll `tail -c 120 out/render.log` with `sleep 590` calls. If two polls show identical output, check `ps -o etime` before assuming a stall: sleeps sometimes return early.
- Don't use `render.js mux` (it can exceed the 10-minute tool limit and leave a broken file). Run `setsid nohup sh scripts/finish.sh . "<Artist> - <Title> (Animated Music Video)" &`, which stream-copies the master into `/mnt/user-data/outputs/` and encodes a ~26 MB 720p preview (`out/finish.done` appears when finished).
- Send the preview with SendUserFile (the attachment limit is 30 MB). The 1080p master stays in the outputs panel.
- Sample 8 frames from the preview into one image and look at it before announcing.

### 8. Report
Two or three short paragraphs: the concept in one sentence, the arc beat by beat (sections → images),
and honest limits (flat vector style, lyric lines placed per 4 bars rather than word-synced, audio
checked by measurement not listening). Offer one concrete next step, such as another style pass, a 9:16 cut, or fixing named timestamps.
