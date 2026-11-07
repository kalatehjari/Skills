# Trailer, screenshots and release

## Contents
- The pipeline
- Directing shots
- Sound from the game's own synth
- Finishing: join, loudness, GIF, thumbnail
- Screenshots and store images
- itch.io
- YouTube text

## The pipeline (tested end to end)

```bash
mkdir promo && cp <skill>/assets/promo/director_template.js promo/director.js \
             && cp <skill>/assets/promo/cues_template.js promo/cues.js        # then edit both
python3 <skill>/scripts/film_shots.py dist/game.html promo/director.js --stills       # 3 frames per shot, fast: check framing
python3 <skill>/scripts/film_shots.py dist/game.html promo/director.js               # promo/shots/<shot>.mp4 + logs
python3 <skill>/scripts/render_audio.py dist/game.html promo/cues.js --shots promo/shots --edit promo/edit.json
python3 <skill>/scripts/finish_trailer.py promo/shots --edit promo/edit.json --audio promo/mix.wav \
        --small --gif s03-door:0.8:1.6 --thumb s03-door:40
```

`promo/edit.json` is the cut: shot names in order, with black gaps in frames at 30 fps.

```json
{"timeline": ["s01-title", "s02-hall", "s03-door", "s04-turn", {"black": 10}, "s05-card", {"black": 20}]}
```

The template director and cue sheet work on the starter game as they are (a 15 s trailer); rewrite the shots
for your levels. Rendering is software WebGL: about 0.5 to 4 frames per second at 1920x1080, so a 35 s trailer
takes 5 to 30 minutes, and crf 18 hatching runs to 30-50 Mb/s (use `--small` for anything but YouTube). Re-render one shot with `--only s03-door`. If a tool call has a time limit, film one or
two shots per call; each shot is written to `.part.mp4` and renamed only when complete.

## Directing shots

A shot is `{ name, n, prep(), frame(i) }`. `prep` calls `prep(level, seed, { warm })` (level 0 is the title
view; `warm: 30` runs a second of game time so the next level is built behind the exit), then places the
player with `place(x, y, z, yaw, pitch)`. `frame(i)` poses the camera or the world for frame `i` and calls
`draw()`, which advances the game by 1/30 s and renders. Scripted walking: set `PL.frozen = false` and
`IN.keys.KeyW = true` in `prep`, and the real player physics climb stairs and walk through arches. Text:
`beat(i, a, b, 'line')` fades a line in at frame `a` and out by `b`; `say()` sets it directly (typewriter
effects). The card (`#trCard`) carries the title and your store link: edit its text in the template.

What makes a good trailer of an ink game:
- 25 to 40 s, 6 to 12 shots of 2 to 3 s. One idea per shot: the drawing, the door, the turn, the threat.
- Open on the title view with a typed line; close on the card over the title view.
- Show the portal: a door swinging open onto a different place is the hook. To walk through it on camera, move
  the player relatively (`PL.pos.addScaledVector(dir, speed * dt)`), because crossing re-expresses the position
  in the next level's coordinates. For a store GIF, film a separate static shot of the door opening and closing.
- Move the camera slowly (ease in and out); the hatching shimmers on fast pans.
- Raise `env.mood` in the scary shots and cut to black on a flash.
- Keep enemies switched off (`e.off = true`) unless the shot is about them, and pose them by hand.
- `info()` logs position, up and grounded per frame; the cue sheet turns those into footsteps and flips.

## Sound

`cues.js` returns sections. A section renders the game's own `AU` sounds offline, then is mixed at its
`t0`; inside `play(a)` times are seconds from the section start. `a.at(t, () => AU.slam(null, 0.6))`,
`a.bed(t, spec)`, `a.melody([t1, t2, ...])` (one note per time), `__snd.steps(E, 'shot')` (footstep times from
the log), `__snd.flips(E, 'shot')` (gravity flips). Start a new section where the picture hard-cuts, with
`cut` (when to stop) and `fade`, so reverb tails stop with the picture. `E.start['shot']` is that shot's start
on the timeline, `E.total` the length. The mix is peak-normalised; loudness comes next.

## Finishing

`finish_trailer.py` joins the shot files without re-encoding (all share size, rate and encoder settings),
adds the black gaps, normalises the sound to -14 LUFS integrated and -2 dBTP (two passes; the margin absorbs AAC overshoot), and writes
`trailer-<height>p.mp4` next to the shots folder. `--small` adds a 720p copy, `--gif shot:start:duration` a
looping GIF under 3 MB (it shrinks itself until it fits), `--thumb shot:frame` a JPEG still. Check the result:
pull 5 frames into one image and look at it, and measure loudness with
`ffmpeg -i trailer-1080p.mp4 -af ebur128=peak=true -f null -`.

## Screenshots and store images

- Screenshots: `shoot.py --shots views.json --size 1920x1080` with 5 to 15 views; keep the HUD (it shows
  the game is playable) but pick moments without toasts. Mark spoilers in the file name.
- Cover (630 x 500 on itch.io): a screenshot with the title in the game's own fonts, cropped. A YouTube
  thumbnail (1280 x 720) is the same idea: one striking frame, the title in IM Fell English SC, a few words.
- The demo GIF: a door opening onto the next level, 1.5 s, looping.

## itch.io

- Upload a zip that contains the game renamed `index.html` (plus a short README.txt if you like). Kind of
  project: HTML; tick "This file will be played in the browser".
- Embed in page at 960 x 540; tick "Mobile friendly" (landscape) and "Fullscreen button" (the starter has no
  fullscreen control of its own).
- Images, GIFs included, must be under 3 MB each; the trailer field takes a YouTube or Vimeo link only.
- Theme in the game's colours: background `#E4E0D5`, text `#171511`, links `#5C64FF`, IM Fell English from
  Google Fonts; set the Screenshots layout to Sidebar, or itch may hide them.
- Leave the page as a draft for the owner to publish. Uploading a zip with the same file name replaces the
  old upload; tick "played in the browser" again afterwards.
- Credit three.js, IM Fell English (Igino Marini) and Special Elite (Astigmatic) with their licences.

## YouTube text

Title: `GAME NAME | Trailer (free browser horror game)` or similar, under 70 characters. Description: the
hook in the first line, the play link in the second (only about 150 characters show before "more"), then the
premise, controls, credits and 3 hashtags. Tags: the genre words people search ("first person horror",
"escape room", "browser game", "indie horror", "Escher", "pen and ink"), your title, and your studio name.
