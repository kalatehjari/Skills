---
name: music-video-director
description: Direct and render a story-driven, hand-drawn animated music video (16:9 YouTube by default) for the user's own song, starring a character designed from their reference photos. Use this whenever the user uploads a song (mp3/wav) and asks for a music video, animated video, visualiser, story video or "something for YouTube" for it, especially Rosha songs, Persian/Farsi lyrics, or a recurring character from their images, even if they don't say "animation". Prefer it over photo slideshows or Ken Burns montages, which this user rejects.
---

**Single-file build.** This is the `music-video-director` skill packed into one file on 2026-11-07. The instructions below are its SKILL.md, unchanged. Its supporting files (1 reference file, 3 scripts and the licence) are embedded verbatim under "Bundled files" at the end, each with a SHA-256 checksum. You can read a reference there directly. Before you run a script or use an asset, unpack the files once:

```bash
python3 - "${CLAUDE_SKILL_DIR}/SKILL.md" "${TMPDIR:-/tmp}/music-video-director" <<'PY'
import hashlib, os, re, sys
src, out = sys.argv[1], sys.argv[2]
if not os.path.isfile(src):
    src = "/mnt/skills/user/music-video-director/SKILL.md"
text = open(src, encoding="utf-8", newline="").read()
rx = r"^<!-- bundle-file: (\S+) sha256=([0-9a-f]{64}) -->\n(`{3,})[^\n]*\n(.*?)^\3$"
n = 0
for path, sha, _, body in re.findall(rx, text, re.M | re.S):
    if path.startswith("/") or ".." in path.split("/"):
        continue
    data = next((b for b in (body, body[:-1]) if hashlib.sha256(b.encode()).hexdigest() == sha), None)
    if data is None:
        data = body
        print("warning: " + path + " was edited after packing (checksum differs)")
    dest = os.path.join(out, path)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8", newline="") as f:
        f.write(data)
    if data.startswith("#!"):
        os.chmod(dest, 0o755)
    n += 1
print(n, "files unpacked to", os.path.abspath(out))
PY
```

The first argument is the path of this file. Claude Code and Cowork fill it in for you; elsewhere, use the path you read this file from (on claude.ai the command also tries `/mnt/skills/user/music-video-director/SKILL.md`). The command prints the folder it wrote to. From then on, use that folder wherever the instructions mean this skill's folder: paths such as `scripts/...`, `references/...`, `assets/...` and `<this-skill>/...` all point into it.

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

---

## Bundled files

The skill's supporting files, verbatim. Unpack them with the command at the top, or read one here. Line is where each file starts in this document.

| File | Size | Line |
|---|---:|---:|
| `references/story-craft.md` | 6.3 KB | 141 |
| `scripts/finish.sh` | 1.0 KB | 237 |
| `scripts/setup_env.sh` | 1.2 KB | 257 |
| `scripts/song_info.py` | 2.2 KB | 280 |
| `LICENSE` | 1.1 KB | 314 |

### `references/story-craft.md`

<!-- bundle-file: references/story-craft.md sha256=7d421039eb23eaf89555e97c860c711b089b4ac605aeb753adbab2565194db95 -->
````markdown
# Story craft for a song film

## Contents
1. From lyrics to one central metaphor
2. Mapping the arc onto the song's sections
3. Shot vocabulary that works with the cast rig
4. Worked example: Tan Be Tan (Rosha)

## 1. From lyrics to one central metaphor

Translate every line first (keep a Persian→English table; the English goes under the Persian on screen).
Then ask: what is the *conflict*, and what *changes* by the last verse? Find one physical image that can
carry both. Good metaphors are objects the character can act on:

- control → marionette strings (she can be jerked by them, then cut or seize them)
- emptiness → desert, sand running out of a hand
- aggression → a war drum whose beats the picture literally hits
- a threshold / new life → a freestanding door with a key

Each metaphor gets introduced, intensified, and resolved. If an image appears only once it is decoration;
if it returns transformed (spears that later bloom, the same desert now sprouting) it is story.

Avoid literalising every line. One strong visual per 4-bar lyric line is plenty; the chorus can repeat
its visual language with an escalation.

## 2. Mapping the arc onto the song

Use the section map (from `song_info.py` + `render.js analyze`). A typical 3-5 minute song:

| section | job in the story |
|---|---|
| intro | world + longing; title card; one mystery (a sound behind a door) |
| verse 1 | the wound, shown small and lonely (wide shots, tiny figure) |
| pre/bridge | the antagonist arrives; the mechanism of control is revealed |
| chorus 1 | the siege: closest, most claustrophobic shots, cut on beats |
| instrumental / solo | the break: a physical act of rupture (strings snap on the first downbeat), weather |
| build | percussion = one cut per beat |
| verse / bridge 2 | the same imagery, transformed by what she learned |
| chorus 2 | the siege returns and fails; she reverses the power |
| outro | the walk away; the threshold; quiet end card with the key line |

Put the biggest visual hit on the first downbeat of the solo or final chorus. Keep the lyric overlay
off the busiest frames (bottom gradient band, 2-line Persian + English).

## 3. Shot vocabulary (all available in cast.js / film-skeleton.js)

- **Face close-up** `R.face` with eyes/brows/mouth/tears/wet/wind/tint; `reflect` paints into the irises
  (a figure, a sprout) for eye ECUs (`cam(ctx, 3.4, W/2, 452)`).
- **Profile two-shot** `R.profile` facing the antagonist's dark profile; a prop between them.
- **Silhouette wide** `R.body(... silhouette: true)` on dunes against a big sun: cheapest way to look cinematic.
- **Marionette** body with `pose: 'custom'` joint angles that change per beat + `strings()` to a control bar.
- **Grasping hands** `R.arm` from frame edges, each landing on a successive beat (`siegeFace`).
- **Per-beat montage** `drumShot`: rotate 3 framings on every beat with a flash.
- **Mirror** two bodies, one dark, one glowing (`shadowBlur`), palms meeting.
- **Transform pass**: re-use an earlier set with a new palette (`desert(...,'dawn')`) and growth (`sprout`).
- **Door** `R.door` with `keyTurn` and `open` (light floods out).

Palettes in `desert()`: day, dusk, blood, night, dawn, storm, gold. Weather: `sandWind`, `rain`,
`embers`, `lightning`. Backdrops: `hallway`, `corridorSide`, `redVoid`, `proscenium`.

## 4. Worked example: Tan Be Tan (Rosha, 293 s, 130 BPM)

Lyrics theme: "I am emptied of your love, a desert… you beat the war drum… I have made peace with myself,
do not set fire to my soul." Metaphor: a marionette who cuts her own strings.

| bars | section | shots |
|---|---|---|
| 0-10 | intro | ink-drop title; she hugs her knees in a night hallway; looks up at the door light |
| 10-18 | hook | red light + feet shadow under the door; her face flinching on beats; walks to the door, turns the key, white-out |
| 18-34 | verse 1 | tiny figure crossing dunes; walk past dead tree, footprints fill; kneels, sand pours from hand; face in sandstorm; pull back over spear field |
| 34-50 | bridge | he rises from the dunes (eyes ignite); profile face-off with dagger; puppet theatre; red war-plan arrows close on her |
| 50-66 | chorus 1 | 8 hands land on 8 beats; marionette jerked per beat against pale sun; his figure in her iris; body-to-body duel, poses snap per beat |
| 66-79 | solo | strings snap + lightning on the downbeat; running in rain; wet face, eyes open; arms open to the storm |
| 79-83 | build | drum skin / him drumming / her flinch, one cut per beat |
| 83-99 | verse 3 | his drum's shockwaves pass her and she does not move; palms raised; mirror self, palms touch on "peace with myself"; fire bends around her |
| 99-115 | bridge 2 | same desert at dawn, sprouts in her footprints; smiling close-up with petals; spears bloom |
| 115-131 | chorus 2 | hands return, she opens her eyes, hands crumble to sand; she pulls the strings and drags him down; sprout in her iris; she disarms him |
| 131-137 | build 2 | drum cuts again, skin cracks, tears on the last beat |
| 137-157 | outro | he kneels by the broken drum as she walks off; looking back; the door in the dunes; key, light, white-out; end card |

Full code: `example-film-tan-be-tan.js` and `example-score-tan-be-tan.js`.

## 5. Style modes

Two looks are proven on the same score and story:

- **Narrative** (`example-film-tan-be-tan.js` + `assets/cast.js`): a drawn heroine with expressions, silhouettes on dunes, dramatic light. Best when the user wants the character recognisable and the story literal.
- **Cubist / avant-garde** (`example-film-cubist.js`, self-contained, no cast.js): the heroine as planes (frontal and profile at once, Picasso-style simultaneity), the antagonist as a black wedge with a red eye (El Lissitzky), the drum and sun as Delaunay discs, Kandinsky bursts on the solo downbeat, analytic facet backgrounds per palette (night, desert, blood, storm, ember, dawn, gold, white), lyrics on a Constructivist paper strip. Emotion lives in the geometry: the face *splits apart* in the desert, *shatters per beat and grows extra eyes* in the siege, *reassembles* when she makes peace, and the two halves (dark and light) slide into one face on "من صلح کردم با خودم". Choose this when the user asks for artistic, conceptual, abstract, cubist, avant-garde or "not the exact person".

To build a new style, keep score.js and the shot timing and swap only the drawing layer; the story arc survives the change of look.
````

### `scripts/finish.sh`

<!-- bundle-file: scripts/finish.sh sha256=ad0734374da8ecc5b1e32799ae42dd35c5362bc6d959292c84f7374f53dbabd2 -->
````bash
#!/bin/sh
# Usage: sh finish.sh <project-dir> "<Output Title>"
# Muxes out/video.mp4 + out/music.wav by stream copy (seconds, never times out), then encodes a 720p
# preview under ~28 MB that fits a chat attachment. Run the preview step detached: it takes ~6 min.
set -e
P="${1:?project}"; NAME="${2:?title}"; OUT=/mnt/user-data/outputs; mkdir -p "$OUT"
M="$OUT/$NAME.mp4"; V="$OUT/$NAME - preview 720p.mp4"
ffmpeg -v error -y -i "$P/out/video.mp4" -i "$P/out/music.wav" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -shortest -movflags +faststart "$M"
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$M")
VB=$(python3 -c "print(max(300, int(26*8*1024/float($DUR) - 112)))")
cd /tmp
ffmpeg -v error -y -i "$M" -vf scale=1280:720 -c:v libx264 -preset medium -b:v ${VB}k -pass 1 -passlogfile /tmp/mvd2p -an -f mp4 /dev/null
ffmpeg -v error -y -i "$M" -vf scale=1280:720 -c:v libx264 -preset medium -b:v ${VB}k -pass 2 -passlogfile /tmp/mvd2p -c:a aac -b:a 112k -movflags +faststart "$V"
ls -la "$M" "$V"; echo FINISHED > "$P/out/finish.done"
````

### `scripts/setup_env.sh`

<!-- bundle-file: scripts/setup_env.sh sha256=fbe53510f4b306055d1e6586c36390241b6a7becdb23f8ca8c2228444624299e -->
````bash
#!/bin/sh
# Usage: sh setup_env.sh <project-dir>
# Makes headless Chromium usable as root (no-sandbox wrapper), downloads the lyric fonts into <project>/assets,
# and prints the CHROME_PATH to export. Safe to re-run.
set -e
P="${1:?project dir}"; mkdir -p "$P/assets"
CH=$(find /opt/pw-browsers -type f -name chrome -path '*chrome-linux*' 2>/dev/null | head -1)
[ -z "$CH" ] && CH=$(command -v chromium || command -v google-chrome || true)
[ -z "$CH" ] && { echo "no Chromium found"; exit 1; }
W="$HOME/chrome-ns"; printf '#!/bin/sh\nexec "%s" --no-sandbox --disable-dev-shm-usage "$@"\n' "$CH" > "$W"; chmod +x "$W"
cd "$P/assets"
if [ ! -f Vazirmatn-Light.ttf ]; then
  curl -sSL -o /tmp/vz.zip https://github.com/rastikerdar/vazirmatn/releases/download/v33.003/vazirmatn-v33.003.zip && \
  unzip -q -o -j /tmp/vz.zip 'fonts/ttf/Vazirmatn-Light.ttf' 'fonts/ttf/Vazirmatn-Medium.ttf' 'fonts/ttf/Vazirmatn-Bold.ttf' -d . || echo "Vazirmatn download failed (Persian text will fall back to Noto Naskh)"
fi
[ -f CormorantItalic.ttf ] || curl -sSL -o CormorantItalic.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/cormorantgaramond/CormorantGaramond-Italic%5Bwght%5D.ttf" || echo "Cormorant download failed"
echo "export CHROME_PATH=$W"
````

### `scripts/song_info.py`

<!-- bundle-file: scripts/song_info.py sha256=7d076f05a275d0a3bb13095ae3f499ecf7c20ecf851b9f768975816c9073f8ef -->
````python
"""Usage: python3 song_info.py <song.mp3> <out_dir>
Prints title/artist/duration and any embedded lyrics (ID3 'lyrics' tags, common for Suno exports),
and writes <out_dir>/structure.png: a mel spectrogram (5 rows x 60 s, 2 s grid) plus a self-similarity
matrix. Read both images to find where sections start and which sections repeat (chorus = off-diagonal
stripes). Speech-recognition models are usually unreachable in this sandbox, so this is how lyrics get placed."""
import sys, json, subprocess, os
import numpy as np
song, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
tags = json.loads(subprocess.run(['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration:format_tags', '-of', 'json', song], capture_output=True, text=True).stdout)['format']
print('duration', tags.get('duration'))
for k, v in tags.get('tags', {}).items(): print(f'--- {k} ---\n{v}')
import librosa, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
y, sr = librosa.load(song, sr=22050, mono=True)
M = librosa.power_to_db(librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmax=8000), ref=np.max)
t = librosa.frames_to_time(np.arange(M.shape[1]), sr=sr); L = 60; rows = int(np.ceil(t[-1] / L))
fig, axs = plt.subplots(rows, 1, figsize=(24, 3.6 * rows))
for k, ax in enumerate(np.atleast_1d(axs)):
    m = (t >= k * L) & (t < (k + 1) * L)
    ax.imshow(M[:, m], origin='lower', aspect='auto', extent=[k * L, min((k + 1) * L, t[-1]), 0, 128], cmap='magma')
    ax.set_xticks(np.arange(k * L, (k + 1) * L + 1, 2)); ax.grid(axis='x', alpha=.3)
plt.tight_layout(); plt.savefig(f'{out}/structure.png', dpi=60); plt.close()
C = librosa.feature.chroma_cqt(y=y, sr=sr); F = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
X = np.vstack([librosa.util.normalize(C), librosa.util.normalize(F)]); hop = int(0.5 * sr / 512); n = X.shape[1] // hop
Xd = np.stack([X[:, i * hop:(i + 1) * hop].mean(1) for i in range(n)], 1)
R = librosa.segment.recurrence_matrix(Xd, mode='affinity', width=4, sym=True)
plt.figure(figsize=(12, 12)); plt.imshow(R, cmap='gray_r', extent=[0, n / 2, n / 2, 0]); plt.xticks(np.arange(0, n / 2, 10)); plt.yticks(np.arange(0, n / 2, 10)); plt.grid(alpha=.3)
plt.savefig(f'{out}/similarity.png', dpi=70)
print('wrote', f'{out}/structure.png', f'{out}/similarity.png')
````

### `LICENSE`

<!-- bundle-file: LICENSE sha256=af7f621414b904053616a4ae3e0dacd5a1a9be9d2d90f558266627c2e8680859 -->
````text
MIT License

Copyright (c) 2026 Roohollah Kalatehjari

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
````
