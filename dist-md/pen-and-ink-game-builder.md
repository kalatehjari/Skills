---
name: pen-and-ink-game-builder
description: Build first-person 3D browser games that look like living pen-and-ink drawings (crosshatched shading, boiling lines, paper grain, one blue accent) as one offline HTML file, with doors that open straight onto the next level, Escher rooms where walls become floors, keyboard, mouse, touch and gamepad controls and synthesized sound; then test it headlessly and film a trailer, screenshots and a GIF from inside it. Use this whenever someone wants an ink, etching, engraving, sketch, woodcut, Escher, noir or hand-drawn look for a 3D or first-person game, a horror, exploration, puzzle or escape game in a single HTML file, portal doors or impossible architecture, a playable itch.io demo, or promo material for such a game, even if they never say "pen and ink".
license: MIT
---

**Single-file build.** This is the `pen-and-ink-game-builder` skill packed into one file on 2026-11-06. The instructions below are its SKILL.md, unchanged. Its supporting files (9 reference files, 11 assets, 9 scripts and the licence) are embedded verbatim under "Bundled files" at the end, each with a SHA-256 checksum. You can read a reference there directly. Before you run a script or use an asset, unpack the files once:

```bash
python3 - "${CLAUDE_SKILL_DIR}/SKILL.md" "${TMPDIR:-/tmp}/pen-and-ink-game-builder" <<'PY'
import hashlib, os, re, sys
src, out = sys.argv[1], sys.argv[2]
if not os.path.isfile(src):
    src = "/mnt/skills/user/pen-and-ink-game-builder/SKILL.md"
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

The first argument is the path of this file. Claude Code and Cowork fill it in for you; elsewhere, use the path you read this file from (on claude.ai the command also tries `/mnt/skills/user/pen-and-ink-game-builder/SKILL.md`). The command prints the folder it wrote to. From then on, use that folder wherever the instructions mean this skill's folder: paths such as `scripts/...`, `references/...`, `assets/...` and `<this-skill>/...` all point into it.

---


# Pen-and-Ink Game Builder

This skill turns a game idea into a playable, shippable, single-file HTML game drawn in ink. It comes from a
finished ten-level game, and contains its engine, cut down to what any game of this kind needs: the
ink renderer, portal doors, any-axis gravity, input on every device, a synth, and the tools that tested it
and filmed its trailer. `scripts/new_game.py` gives you a working three-level game in seconds, and you
reshape it from there. Paths below are relative to this skill's folder.

## Decision table

| Goal | Do this | Read |
|---|---|---|
| Start a game | `python3 scripts/new_game.py "Title" --dir <path>` (fetches three.js r147 + fonts, builds) | `references/architecture.md` |
| Rooms, stairs, doors, lights, signs | edit `<game>/src/05_levels.js` | `references/level-building.md` |
| Walk on walls and ceilings | `face()`, `fB()`, `L.gravZones`, doors with `upQ` | `references/escher-gravity.md` |
| Change the look, patterns, mood | `env`, `env.mood`, `src/02_ink.js` | `references/ink-rendering.md` |
| Enemies, keys, locks, triggers, puzzles | `Blot`, `Pickup`, `L.trigger`, `interact()` | `references/gameplay-patterns.md` |
| Sound and music | `AU` in `src/01_core.js` | `references/audio.md` |
| Controls, HUD, menus, phones | `src/04_player.js`, `src/00_head.html`, `UI` | `references/controls-and-ui.md` |
| Build | `python3 scripts/build_html.py <game>` | |
| Look at it, prove it is finishable | `scripts/shoot.py`, `scripts/playtest.py` | `references/testing.md` |
| Trailer, stills, GIF, itch.io page | `film_shots.py`, `render_audio.py`, `finish_trailer.py` | `references/trailer-and-release.md` |

## Workflow

1. **Write a one-page design first**: the premise in one line, what the blue accent means (it should mark the
   real and the way on), 3 to 10 levels with one new idea each, and the ending. A level that teaches nothing
   new is a corridor; cut it. Start with three levels and grow once those play well.
2. **Scaffold**: `python3 scripts/new_game.py "Title" --dir games/title`. Then take a baseline before you change
   anything: `python3 scripts/shoot.py games/title/dist/title.html` and look at the pictures. When something
   breaks later, you will know it was your change.
3. **Build levels** in `src/05_levels.js`, reusing the helpers. Rebuild with `scripts/build_html.py`; it
   syntax-checks the code with node, so a missing bracket fails there, not silently in a browser.
4. **After every level change**, run `scripts/playtest.py` (a robot opens and walks through every exit door and
   tries every gravity zone; it reports JavaScript errors) and `scripts/shoot.py` with a shots file for the
   views you care about. Look at the images: hatching that is too dark, a door hidden behind a column, or a
   spawn facing a wall is obvious in a picture and invisible in code.
5. **Tune feel**: speeds, mood per level (`env.mood`), sound beds, hints. Play it on a phone-sized viewport
   too (`--size 844x390`).
6. **Promo** (when asked): copy `assets/promo/director_template.js` and `cues_template.js`, film, mix, finish.
7. **Deliver** the single `dist/<slug>.html`. For itch.io, zip it as `index.html` (see the release reference).

## Principles, and why

- **One colour means one thing.** Everything is ink on paper except blue, which marks the real exit and the
  things that matter. Players learn it within a minute and then read every room at a glance. Spending the
  accent on decoration ruins that.
- **Shade with tone, not colour.** Each box has a tone (about 0.55 to 0.95 reads best) and a pattern; light
  decides how many hatch layers appear. Near-black (0.03 to 0.1) reads as a hole, which is right for wells and
  pits and wrong for walls; pure white loses its edges in the paper-coloured fog.
- **Build from boxes.** `L.B()` boxes are merged per level into one mesh and one set of boiling edge lines,
  and each solid one becomes an axis-aligned collider in a spatial hash. That keeps hundreds of objects at two
  draw calls and makes collisions reliable. Rotated pieces (`L.BM`, `decoChunk`) are decoration only.
- **Doors are portals, never loading screens.** The next level builds in the background and the exit door
  shows it; walking through carries position, velocity and gravity across, and the entrance slams behind you.
  Keep doors at the standard 1.1 x 2.25 m with `doorHole()`, because frames, colliders and portals assume it.
- **Gravity always points along a world axis.** Then colliders stay axis-aligned and the player code needs no
  special cases. Build on walls with face coordinates (`fW`, `fB`) as if they were floors.
- **Determinism.** Level building uses the seeded `rnd()`, sound and particles use `Math.random`. A level
  looks the same on every run, so screenshots, tests and trailer shots repeat exactly.
- **Test like a robot before asking a human.** Headless runs step the game frame by frame (no real time), so
  they are slow to render but exact. The playtest catches unreachable exits and broken portals in seconds.
- **Phones are first-class.** Touch devices start at low quality, the joystick appears under the thumb, and
  hints are worded for the device in use. `SET.calm` softens boil, warp and shake for players who need it.
- **Everything ships inside one file.** The fonts are embedded and the sound is synthesized, so the game runs
  offline, from itch.io, or from a USB stick, with nothing to license and nothing to download.

## Things that bit before

- Spawning inside or above a collider: `playtest.py` reports a spawn that is not on the ground. Spawn yaw comes
  from `stdEntrance` (`faceYaw`), so the player faces into the room.
- An open door showing the wrong picture: only one portal is rendered per frame, so a second open portal
  doorway shows nothing. Keep one exit per level, or close the other.
- Objects with `matrixAutoUpdate = false` have no valid `matrixWorld` until the first render. Set it yourself
  if a test or frustum check needs it before then (the starter does this for door apertures).
- `L.killU` is the height below which the player has fallen out of the world. Set `-1e9` in rooms where
  gravity can point anywhere, or the player dies on the ceiling.
- Browsers start sound and pointer lock only after a click or key press; the starter waits for one.
- itch.io serves many games from one origin; `Store` prefixes every saved key with the game's slug.
- Headless Chromium renders with SwiftShader: about 0.5 to 4 frames per second at 1080p, depending on the scene and CPU cores. Film short shots
  (2 to 4 s) and render them in separate calls if a tool time limit applies.

## Licences

The starter kit and scripts are MIT (this skill). Games embed three.js (MIT), IM Fell English and IM Fell
English SC (SIL OFL 1.1) and Special Elite (Apache 2.0); `get_deps.py` saves their licences in
`<game>/vendor/`. Credit them on the game page. A game you build is yours to license as you like.

## Report back

Say what was built and how to play it (controls on each device), give the file path, and summarise what the
tests showed (playtest result, the screenshots you looked at). Name the limits honestly, for example "no save
system yet" or "sound checked by measurement, not by listening".

---

## Bundled files

The skill's supporting files, verbatim. Unpack them with the command at the top, or read one here. Line is where each file starts in this document.

| File | Size | Line |
|---|---:|---:|
| `references/architecture.md` | 5.4 KB | 174 |
| `references/audio.md` | 3.6 KB | 281 |
| `references/controls-and-ui.md` | 3.5 KB | 355 |
| `references/escher-gravity.md` | 4.1 KB | 424 |
| `references/gameplay-patterns.md` | 4.8 KB | 503 |
| `references/ink-rendering.md` | 6.3 KB | 605 |
| `references/level-building.md` | 7.8 KB | 725 |
| `references/testing.md` | 3.5 KB | 859 |
| `references/trailer-and-release.md` | 6.3 KB | 933 |
| `assets/promo/cues_template.js` | 1.7 KB | 1039 |
| `assets/promo/director_template.js` | 5.7 KB | 1072 |
| `assets/promo/offline_audio.js` | 3.8 KB | 1151 |
| `assets/starter/src/00_head.html` | 5.4 KB | 1216 |
| `assets/starter/src/01_core.js` | 13.1 KB | 1295 |
| `assets/starter/src/02_ink.js` | 29.7 KB | 1459 |
| `assets/starter/src/03_world.js` | 38.3 KB | 1997 |
| `assets/starter/src/04_player.js` | 20.1 KB | 2587 |
| `assets/starter/src/05_levels.js` | 9.6 KB | 2912 |
| `assets/starter/src/06_game.js` | 15.8 KB | 3050 |
| `assets/starter/src/07_main.js` | 3.7 KB | 3292 |
| `scripts/_pen_ink_common.py` | 1.9 KB | 3347 |
| `scripts/build_html.py` | 4.2 KB | 3392 |
| `scripts/film_shots.py` | 5.0 KB | 3479 |
| `scripts/finish_trailer.py` | 5.9 KB | 3572 |
| `scripts/get_deps.py` | 4.6 KB | 3669 |
| `scripts/new_game.py` | 3.0 KB | 3760 |
| `scripts/playtest.py` | 4.3 KB | 3820 |
| `scripts/render_audio.py` | 4.9 KB | 3908 |
| `scripts/shoot.py` | 4.1 KB | 3999 |
| `LICENSE` | 1.1 KB | 4081 |

### `references/architecture.md`

<!-- bundle-file: references/architecture.md sha256=db143e8fd9a877ed6809bf969dbbc56483b9632821811bf82747d932eff1c2ca -->
````markdown
# Architecture of a pen-and-ink game

## Contents
- Folder layout
- Source files and what lives where
- The frame loop and game states
- How a level lives and dies
- Portal math (how doors connect levels)
- Test hooks (`window.__game`)

## Folder layout

`scripts/new_game.py "Title" --dir games/title` creates:

```
games/title/
├── game.json          {"title", "slug", "three"}; build_html.py reads the slug from here
├── src/               the game. Edit these files.
├── vendor/            three.min.js (r147) + fonts + their licences (get_deps.py)
└── dist/title.html    the built game: one file, everything inlined (build_html.py)
```

Rebuild after every edit: `python3 scripts/build_html.py games/title`. It concatenates `src/00_head.html` and
every `src/*.js` in name order inside one function scope, so top-level `const`s are shared between files but
are not on `window`. three.js is a separate, earlier script and is global (`THREE`).

## Source files

| File | Holds |
|---|---|
| `00_head.html` | page shell, CSS colour tokens, title/pause screens, HUD (crosshair, prompt, toast), touch controls |
| `01_core.js` | math helpers, seeded `rnd()`, `Store` (localStorage with a per-game prefix), `SET` settings, `AU` synth |
| `02_ink.js` | the renderer: shared uniforms `U`, INK/LINE/GLOW/SPILL/PORTAL materials, `POST` uniforms, `R` (render, shadows, quality) |
| `03_world.js` | `GeoAcc` (box merger), `SHash` (collider hash + raycast), `Level`, `Door`, `Pickup`, build helpers, Escher faces, `stdEntrance`, `exitDoor` |
| `04_player.js` | `IN` (keyboard, mouse, touch, gamepad) and `PL` (the player: physics, any-axis gravity, camera) |
| `05_levels.js` | `LEVELS[1..n]`, the example enemy `Blot`. Most of your work happens here |
| `06_game.js` | `GAME` (states, streaming, portals, interaction, mood, hints) and `UI` |
| `07_main.js` | boot, the frame loop, `window.__game` test hooks |

Add new files as `05b_monsters.js` and so on; the name decides the order. A file may use anything defined in
an earlier file at load time, and anything at all inside functions called later.

## Frame loop and states

`07_main.js` calls `GAME.update(dt)` then `GAME.render()` every animation frame, with `dt` clamped to 0.05 s
so a stall never becomes one huge physics step. States: `title` (camera orbits level 1 behind the title
screen) → `play` ↔ `pause`; `play` → `caught` (1.3 s) → `play`. Per frame in `play`:

1. build the next level if due (`needNext` counts down 0.4 s after a level starts);
2. close the entrance behind the player once they are clear (`reverse`);
3. input edges (`pause`, `lamp`), look, entity updates, player physics, doors, pickups, lights;
4. triggers, gravity zones, the level's own `update(L, dt)`;
5. camera, portal check (and crossing), interaction prompt, mood and post effects.

## Level lifecycle

`GAME.buildLevel(i)` seeds `rnd()` with the level number, makes `new Level(i, name)`, runs
`LEVELS[i].build(L)`, then `L.finalize()` (merges geometry, fills the collider hash) and `R.bakeShadow(L)`.
Nothing can be added to the merged geometry after `finalize`; dynamic things (`buildObj`, meshes, entities)
are added to `L.scene` with `L.add()`. `L.dispose()` frees geometry and any material marked
`material.userData.own = true`; mark materials you create per object, or they leak across levels.

A level definition:

```js
LEVELS[4] = {
  name: 'The Well', sub: 'shown under the name',     // the level card shows "IV. The Well"
  next: 2,                                            // optional: where its exit leads (default i + 1)
  titleView: t => ({ pos: [x, y, z], look: [x, y, z] }), // optional, level 1 only: title camera at time t
  build(L) { ... },                                   // geometry, doors, entities, triggers
  onStart(L, viaPortal) { ... },                      // optional: when it becomes the live level
  update(L, dt) { ... }                               // optional: every frame while live
};
```

The last level has no `exitDoor` (or `next: null`); its `update` decides when the game ends
(`GAME.toTitle()`).

## Portal math

A door's frame matrix `F` places door-local space (x across the opening, y up, z through it, origin at the
middle of the threshold) in the world. Linking exit `e` of level A to entrance `n` of level B:

```js
e.portal = { level: B, M: n.F * e.F⁻¹, plane: n.plane, hideLeaf: n.pivot, dir: 1 };
```

`M` maps any point near A's exit to the matching point near B's entrance. Each frame the portal camera is
`M × camera.matrixWorld`; B is rendered into a texture with B's entrance plane as a clipping plane (so nothing
between that camera and the doorway draws), and the exit's aperture box shows that texture in screen space.
When the camera's door-local z changes sign inside the door rectangle, `GAME.crossPortal` applies `M` to the
player's position, velocity and gravity frame, makes B the live level, and gives B's entrance a reverse portal
back into A until it slams. Doors may have any orientation (`upQ`), so a door on a wall leads to an upright
door and gravity turns with you.

## Test hooks

`window.__game` (always present) exposes `GAME, PL, R, U, POST, LEVELS, IN, SET, UI, AU, ERRS, V3, Q4, M4,
faceQ, CAM()` and helpers: `play(i)`, `step(n, dt, render)`, `tp(x, y, z)`, `look(yaw, pitch)`,
`hold(code, on)`, `openExit()`, `faceExit(back)`, `state()`. Scripts stub `requestAnimationFrame` before the
page loads, so nothing moves unless they call `step()`. See `references/testing.md`.
````

### `references/audio.md`

<!-- bundle-file: references/audio.md sha256=4426a4f202ca9fd4898f190fcd25895f41e0449c1c3a87289bfa320d02673973 -->
````markdown
# Sound: everything synthesized

`AU` in `src/01_core.js` makes every sound from oscillators and filtered noise. Nothing is downloaded or
licensed, the file stays small, and the trailer tools can render the very same sounds offline, in sync with
the picture.

## The one rule

Every sound schedules itself at `this.ctx.currentTime + (o.delay || 0)`. Keep that pattern in new sounds:
use `delay` for rhythm, never `setTimeout`. The offline renderer (`assets/promo/offline_audio.js`) works by
making `currentTime` report the cue time, so a sound written this way lands exactly where the cue sheet puts
it; one that waits on a timer plays at the wrong moment or not at all. The only exception is `AU.melody`,
whose `setInterval` the offline renderer captures and calls note by note.

## Building blocks

```js
AU.tone({ f, fEnd, dur, type: 'sine'|'triangle'|'square'|'sawtooth', gain, attack, lp, rev, pan, delay, dest })
AU.noiseHit({ f, fEnd, q, type: 'bandpass'|'lowpass'|'highpass', dur, gain, attack, brown, rev, pan, delay, dest })
AU.spatial(pos)          // { pan, gain, muf } for a world position as heard from the camera (muf: it is behind you)
AU.bed(spec)             // replace the ambient drone: { root Hz, fifth ratio, cut Hz, noise, noiseF, gain }
AU.stopBeds(fadeSeconds)
AU.melody(true|false)    // the title music box (20 notes, one every 0.56 s)
```

`rev` sends part of the sound to a long convolution reverb (0.3 a room, 0.9 a cathedral). Buses: `AU.sfx`,
`AU.music`, `AU.bedBus` into `AU.master` into a compressor; `SET.vol` and `SET.mus` set master and music level
through `AU.applyVol()`.

## Ready-made effects

`step(surface, loud)` (stone, wood, tile, carpet), `land(height)`, `creak(pos, dur, gain)` (a door),
`slam(pos, gain)`, `knock(pos, n, gain)`, `rattle(pos)` (a locked handle), `chime(gain)` (pickup), `boom(gain, delay)`,
`whoosh(pos, gain)`, `grav()` (gravity turning), `shriek(pos)` (an enemy), `click()` (UI).

## Adding a sound (tested)

Write it as a method on `AU`, from tones and noise, with `delay` for the rhythm:

```js
heartbeat(k = 0.5) { // two low thumps; k 0..1 = fear
  this.tone({ f: 58, fEnd: 40, dur: 0.16, gain: 0.25 + k * 0.2, lp: 300 });
  this.tone({ f: 52, fEnd: 36, dur: 0.18, gain: 0.18 + k * 0.15, lp: 300, delay: 0.24 });
},
```

Then call it from the game, for example every `60 / (62 + threat * 75)` seconds while `GAME.threatS > 0.05`,
counting the interval in `GAME.update` so it stops when the game pauses.

## Recipes

| Sound | Recipe |
|---|---|
| wind | `noiseHit({ brown: true, type: 'bandpass', f: 400, fEnd: 700, q: 0.5, dur: 4, attack: 1.5, gain: 0.1 })` |
| drip | `tone({ f: 1800, fEnd: 900, dur: 0.08, gain: 0.05, rev: 0.8 })` |
| distant bell | three `tone`s at f, 2.76f, 5.4f (sine, dur 3, falling gains, rev 0.9) |
| whisper | `noiseHit({ type: 'bandpass', f: 2500, q: 4, dur: 1.2, attack: 0.3, gain: 0.05 })`, twice, 0.3 s apart, panned |
| scrape | `noiseHit({ type: 'bandpass', f: 900, fEnd: 400, q: 6, dur: 0.7, gain: 0.12 })` |
| drone for a level | `E.bed = { root: 41, fifth: 1.26, cut: 160, noise: 0.06, noiseF: 220, gain: 0.5 }`: lower root and cut = heavier |

Ambient beds set the mood of a level more than anything else. A tritone (`fifth: 1.414`) unsettles, a fifth
(1.5) is calm, a minor third (1.19) is sad, a near-unison (1.059) grinds.

## Browsers

Sound can only start after a user gesture; `07_main.js` creates and resumes the context on the first pointer,
key or touch, and pausing suspends it. Test sound in a real browser: headless runs cannot listen, so trailer
audio is checked by measurement (loudness and peaks), and you should say so when you report.
````

### `references/controls-and-ui.md`

<!-- bundle-file: references/controls-and-ui.md sha256=abb12618f37277fda5e796019219388535241ac831758ecd3d5b4f19758e3a70 -->
````markdown
# Controls, HUD and menus

## Default controls

| Action | Keyboard + mouse | Touch | Gamepad (standard mapping) |
|---|---|---|---|
| move / look | WASD or arrows / mouse (pointer lock), or drag | left thumb anywhere on the left half (floating joystick) / drag on the right half | left stick / right stick |
| run | Shift | push the stick to the rim | left stick click |
| jump | Space | jump button | A |
| open, use | E or Enter | open button | X |
| crouch | C or Ctrl | duck button | B |
| lamp | F | (add a button) | LT |
| pause | Esc or P | pause button (top right); switching apps pauses too | Start |

Clicking the game requests pointer lock; pressing Esc releases it, which pauses the game (browsers reserve
Esc for that). Without pointer lock, dragging with the left button looks around. Touch controls appear only
after the player has touched the screen (`IN.usedTouch`), so desktop players never see them.

## Adding an action

1. Keyboard: add the key to the `KE` map in `IN.init` (`KeyQ: 'focus'`).
2. Touch: add `<div class="tb" id="tFocus">focus</div>` inside `#touch` in `00_head.html`, position it with
   CSS like `#tAct`, and add `tFocus: 'focus'` to the `btns` map in `IN.init`.
3. Gamepad: add the button index to `map` in `IN.pollPad` (`3: 'focus'` is Y).
4. Game: `if (IN.take('focus')) { ... }` in `GAME.update` (an edge: true once per press). For held actions
   read `IN.keys.KeyQ` (keyboard), keep a flag set in the touch start/end handlers, and read the pad button.

## HUD

`#xh` (crosshair dot), `#prompt` (the "Open" line under it, set by `UI.prompt(label)` from the interaction
check), `#toast` (`GAME.toast(text, seconds)`: level cards, hints, notes). Keep the HUD this sparse: the
drawing is the interface, and text over hatching is hard to read without the paper-coloured halo the CSS adds.

## Screens and a settings menu

Screens are `<section class="screen">` elements; `UI.show(id)` shows one and hides the rest, `UI.show(null)`
hides all. To add settings: a section with sliders and toggles, a button on the title and pause screens that
calls `UI.show('settings')`, and handlers that write `SET`, then apply and save:

```js
$('sens').oninput = e => { SET.sens = +e.target.value; saveSet(); };
$('qual').onchange = e => { SET.quality = +e.target.value; R.applyQuality(); saveSet(); };
$('vol').oninput = e => { SET.vol = +e.target.value; AU.applyVol(); saveSet(); };
$('calm').onchange = e => { SET.calm = e.target.checked ? 1 : 0; saveSet(); };
```

`SET` already holds `sens`, `invert`, `fov`, `quality`, `vol`, `mus` and `calm`, loaded from `Store` at start.

## Phones and tablets

- Touch devices start at quality 0 (lower pixel ratio, no MSAA); this matters more than anything else for
  frame rate. Test at a phone landscape size: `shoot.py --size 844x390 --quality 0`.
- Lay buttons out for right thumbs at the bottom-right corner, at least 60 px across, and keep the left half
  free for the joystick. `env(safe-area-inset-*)` variables keep them clear of notches.
- Phones in portrait: the game still runs, but suggest landscape on the title screen if your layout needs it.

## Accessibility that costs little

- `SET.calm`: softer boil, warp, swirl, wave and camera shake, for motion sensitivity.
- No flashing faster than three times a second; `GAME.flash` is a single decaying flash.
- Invert look, sensitivity and field of view in settings.
- Important sounds deserve a caption: show it with `GAME.toast('[two knocks behind you]')`.
- Every action reachable from keyboard alone, touch alone and gamepad alone.
````

### `references/escher-gravity.md`

<!-- bundle-file: references/escher-gravity.md sha256=a70467eea4f7b6520c199a5399ba3fee0463740623fe36b3d78601ca8585fa9f -->
````markdown
# Escher rooms: walls that become floors

Gravity in this engine always points along a world axis: `PL.ax` (0 = x, 1 = y, 2 = z) and `PL.sg` (+1 or -1)
give "up". Colliders therefore stay axis-aligned boxes whatever the gravity, and the same player code walks on
floors, walls and ceilings. The camera swings smoothly to the new up over about 0.65 s.

## Faces: build on a wall as if it were a floor

```js
const FLOOR = face([0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]);   // origin, X, Y (= up), Z
const NORTH = face([0, 0, 6], [1, 0, 0], [0, 0, -1], [0, 1, 0]);  // the inside of a wall at z = 6
```

A face is a local frame: `o` is its origin on the surface, `Y` is up for someone standing on it, `X` and `Z`
run along the surface. Choose `X`, then make `Z = X × Y`, so the frame is a proper rotation (`faceQ` needs
that; a mirrored frame turns doors inside out). `face()` works out `ax` and `sg` from `Y`.

```js
fW(NORTH, x, y, z)                          // face coordinates -> world V3 (y = height off the wall, z runs up it)
fB(L, NORTH, x0, y0, z0, x1, y1, z1, o)     // a box in face coordinates (same options as L.B)
fStairs(L, NORTH, x, y, z, n, rise, run, w) // a flight climbing along the face's +z
faceQ(NORTH)                                // the rotation that stands a door (or anything built y-up) on the face
onFace(NORTH)                               // is the player standing on this face now?
```

## Switching gravity

A zone is a world-space box on the face you leave. When the player's centre enters it, gravity turns to the
target face and the feet are moved to `place(feet)`:

```js
blueArch(L, new V3(0, 1.2, 4.7), new Q4());   // the marker players learn to read
L.gravZones.push({
  from: FLOOR, to: NORTH,
  box: [-1.3, 0, 4.4, 1.3, 2.6, 5.1],
  place: p => new V3(clamp(p.x, -1, 1), 1.0, 6),   // feet on the wall surface (z = 6), 1 m up from the floor
  onSwitch: () => GAME.hint('arch'),               // optional
  axis: new V3(1, 0, 0)                             // optional: the roll axis for a half turn (floor to ceiling)
});
```

`place` must put the feet exactly on the new floor's surface (here the wall's inner face, z = 6) and the body
somewhere empty: the player becomes a 1.72 m box standing out of that surface. Zones are ignored for 0.6 s
after a switch, so walking through an arch never flips twice. For a half turn (floor to ceiling), pass an axis
to roll around: `gravSwitch(CEIL, feet, new V3(1, 0, 0))`; otherwise the direction of the roll is arbitrary.

## Doors on walls

```js
const N = NORTH, DW = { pat: PAT.BRICK, tone: 0.86 };
fB(L, N, -6, 0, 7.75, -0.68, 5, 8.25, DW);         // a wall standing on the wall, left of the hole
fB(L, N, 0.68, 0, 7.75, 6, 5, 8.25, DW);           // right of the hole
fB(L, N, -0.68, 2.44, 7.75, 0.68, 5, 8.25, DW);    // above the hole
exitDoor(L, ...fW(N, 0, 0, 8).toArray(), 0, { upQ: faceQ(N) });  // you walk through it towards the face's +z
```

The hole is the standard door hole (`x ± 0.68`, height 2.44) written in face coordinates. `stdEntrance` takes
`{ upQ }` too, which spawns the player standing on that face. Portals carry gravity across: leaving through a
wall door into an upright entrance turns the player upright.

## Rules for rooms where down moves

- Set `L.killU = -1e9`: "below the floor" means nothing once gravity can point anywhere. If players can leave
  the room through a gap, bound it instead: `L.killBox = new THREE.Box3(new V3(-7, -1, -7), new V3(7, 13, 7))`.
- Give each face a different pattern (floor `PAT.BLOCKS`, walls `PAT.ASHLAR`, ceiling `PAT.WOOD`), so players
  can tell where they are standing from any angle.
- Put furniture on more than one face (`fB` on a wall, an upside-down table on the ceiling). It sells the idea
  before the first flip, and gives the player landmarks after it.
- Make the first switch safe and obvious: an arch on a clear floor, walking speed, the destination in view.
- Set `E.upW` (the "up" the ambient light treats as sky) to the room's main up; the default is +y.
- Pickups bob along the player's current up, so keys work on any face.

`assets/starter/src/05_levels.js` level II is a complete, tested example (`scripts/playtest.py` checks the zone).
````

### `references/gameplay-patterns.md`

<!-- bundle-file: references/gameplay-patterns.md sha256=e33a5928de71f5ba4d5dc7b2bf213012e475261deadd0ea908992996b0df3807 -->
````markdown
# Gameplay patterns

## Contents
- Entities
- Sight: line of sight, cones, "only moves when unseen"
- Keys, locks, notes, switches
- Triggers and timed sequences
- Moving platforms
- Getting caught, falling, respawning
- Hints, saving, difficulty

## Entities

An entity is any object with `update(dt)`, registered with `L.ent(e)`. `GAME` calls it every frame while
the level is live (before the player moves), skips it when `e.alive === false`, and calls `e.reset()` after a
respawn. Give it an `off` flag so tests and trailers can freeze it. `Blot` in `src/05_levels.js` is the
reference: it patrols a loop of points, turns to look where it goes, notices the player inside a cone and
range (shorter while crouching) with a clear line of sight, fills a suspicion meter, feeds that into
`GAME.threat` (so the drawing boils and ink creeps in as it watches you), warns with a falling tone, and calls
`GAME.caught(this)` when the meter is full.

Build its look with `buildObj()` and the ink materials (`PAT.MONSTER` reads as a living ink blot), add it with
`L.add()`, and mark any material you create `userData.own = true` so the level disposes it.

## Sight

```js
GAME.los(a, b, slack)       // true if nothing solid lies between points a and b (colliders with noRay are see-through)
GAME.isSeen(p, maxD)        // true if world point p is on screen, within maxD, and unblocked
L.ray(origin, dir, maxT)    // distance to the first collider along a unit direction, or Infinity
PL.center, CAM.position     // the player's middle and eye
```

A cone test is a dot product: `look.dot(toPlayer.normalize()) > 0.72` is about 44 degrees either side. For a
statue that only moves while unseen, move it in `update` only when `!GAME.isSeen(head, 40)`; test a point on
its head and one at its feet, or it creeps forward while half visible.

## Keys, locks, notes, switches

```js
exitDoor(L, x, y, z, yaw, { locked: true, lockMsg: 'Locked. Something blue opens it.' });
new Pickup(L, 'key', x, y, z, { onGet: () => { L.exitDoor.locked = false; GAME.toast('A lock gives.'); GAME.pulse = 0.6; } });
new Pickup(L, 'note', x, y, z, { text: 'Shown as a toast for six seconds.' });
interact(L, new V3(x, y, z), 'Pull', () => { L.data.lever = 1; AU.slam(null, 0.3); }, { r: 2.4, when: () => !L.data.lever });
```

`interact` shows its prompt when the player looks at the point (within `r` metres and a cone set by `cos`)
with nothing in between, and runs on E, the open button or the pad's X. `when` hides it until it applies.

## Triggers and timed sequences

`L.trigger(x0, y0, z0, x1, y1, z1, fn)` fires once when the player's centre enters the box; pass
`{ once: false }` to fire on every entry. For sequences, count time in the level's `update` with `L.t` or
`L.data`, not `setTimeout`: game time stops while paused and advances exactly in headless tests, while timers
keep running in both cases.

```js
update(L, dt) {
  if (L.data.alarm != null && (L.data.alarm += dt) > 2) { L.data.alarm = null; L.exitDoor.close(true); }
}
```

## Moving platforms (tested)

Dynamic colliders live in `L.dyn` (checked every frame, not hashed). Give one a `dv` vector holding this
frame's movement and a grounded player rides it.

```js
const lift = { min: [2, 0, -1.5], max: [4, 0, 0.5], on: true, surf: 'wood', _s: 0, dv: new V3() };
const liftObj = buildObj(a => a.box(-1, -0.15, -1, 1, 0, 1, 0.7, PAT.WOOD));
L.add(liftObj); L.dyn.push(lift);
L.ent({ t: 0, update(dt) {
  this.t += dt; const y = 1.5 - Math.cos(this.t * 0.6) * 1.5;      // 0 m to 3 m and back
  lift.dv.set(0, y - liftObj.position.y, 0); liftObj.position.set(3, y, -0.5);
  lift.min[1] = y - 0.15; lift.max[1] = y;
} });
```

## Getting caught, falling, respawning

- `GAME.caught(by)`: shriek, ink flash, fade; 1.3 s later the player is back at the level's spawn and every
  entity's `reset()` runs. Replace it with your own (`GAME.caught = by => ...`) for lives, checkpoints or a
  game-over screen.
- Falling below `L.killU` (or leaving `L.killBox`) calls `GAME.voidFall()`, which puts the player back on a
  recent safe spot (`PL.safe` records one every 0.35 s on still, non-hazard ground).
- Checkpoints: set `L.spawn = { pos: new V3(x, y, z), yaw }` in a trigger.

## Hints, saving, difficulty

- `HINTS` in `src/06_game.js` holds one line per hint, in `kb`, `touch` and `pad` wording (or `all`).
  `GAME.hint('name')` shows it once per run in the wording for the device the player last used.
- `Store.get(key, default)` and `Store.set(key, value)` save to localStorage under the game's own prefix.
  For a Continue button: `Store.set('level', L.idx)` in `startLevel`, and a title button that calls
  `GAME.newRun(Store.get('level', 1))`.
- Difficulty is easiest as multipliers read where they matter: `Blot` speed and range, `GAME.caught` timing,
  how many keys a level needs. Put the setting in `SET` so it is saved with the others.
````

### `references/ink-rendering.md`

<!-- bundle-file: references/ink-rendering.md sha256=8e15724191c9275c728567a3fb25da1878403b6cc16bc3fdf9ef24be0acde6a1 -->
````markdown
# The ink renderer

## Contents
- How a frame is drawn
- From light to hatching
- Patterns (`PAT`) and adding one
- Lines, glow and light pools
- Lights and shadows
- Mood and post effects
- Changing the palette
- Quality and performance

## How a frame is drawn

1. If an open portal door is on screen: render the linked level from the portal camera into `R.portalRT`,
   clipped at the destination doorway.
2. Render the live level into `R.mainRT` (multisampled on WebGL2 at quality 1 and 2).
3. Draw `R.mainRT` to the screen through `POST_FS`: paper grain, ink vignette and mood effects.

Every surface uses one of four `ShaderMaterial`s that share the uniform objects in `U` (time, boil, sun,
fog, lights, shadows), so changing `U.uBoil.value` changes every material at once.

## From light to hatching

`INK_FS` computes a tone `t` per pixel: `aTone` (the box's tone) times the pattern's factor, times light
(ambient hemisphere + sun x baked shadow + carried lamp + up to 8 point lights), then mixed towards
`uFogTone` with distance. Hatch layers switch on as `t` drops: one direction below 0.97, a second crossing
below 0.47, a third below 0.26, a fourth below 0.13, solid ink below 0.05. Lines are drawn in world space on
the plane the surface faces (x, y or z), so they stick to surfaces as you move, and their frequency doubles or
halves with distance (`log2` of the screen-space derivative) so spacing on screen stays about the same.
`env.hatch` sets the base density (lines per metre). Boil re-seeds the line phase 8 times a second by
`uBoil` (and jitters the edge lines), which is what makes the drawing look alive; `env.mood.boil` 0.03 is calm,
0.3 nervous, 0.8 and above frantic.

Tone guide: 1.0 plain paper, 0.85 to 0.95 light stone, 0.6 wood and furniture, 0.3 dark objects, 0.1 holes
and shadows. Patterns multiply it further.

## Patterns

| `PAT.` | look | | `PAT.` | look |
|---|---|---|---|---|
| `BRICK` 1 | running bond brick | | `ASHLAR` 9 | big cut stone, uneven tone |
| `BLOCKS` 2 | tumbling blocks (Escher cubes) | | `BOARDS` 10 | vertical wainscot boards |
| `CHECKER` 3 | checker floor | | `GRASS` 11 | stipple ground |
| `WOOD` 4 | planks with grain | | `MONSTER` 12 | black with boiling paper scribbles |
| `BOOKS` 5 | shelves of book spines | | `PAPER` 13 | blank bright paper (signs, notes) |
| `DAMASK` 6 | wallpaper motif | | `PLASTER` 14 | plaster with cracks |
| `TILES` 7 | small square tiles | | `CARPET` 15 | runner with border lines |
| `HEDGE` 8 | leafy noise | | `DIAL` 16 / `ROCK` 17 | clock ticks / rough rock |

To add pattern 18, edit `INK_FS` in `src/02_ink.js`: change the last branch `} else { // void rock` to
`} else if(pid < 17.5){ // void rock`, and add after it:

```glsl
} else { // 18: diagonal tiles
  vec2 q = vec2(p.x + p.y, p.x - p.y) / 0.5;
  pink = max(gridLine(q.x, (dp.x + dp.y) / 0.5, 0.02), gridLine(q.y, (dp.x + dp.y) / 0.5, 0.02)) * 0.8;
  tone *= 0.92;
}
```

Inside a branch `p` is the surface position in metres, `dp` its screen derivative (use it to anti-alias),
`tone` the tone to multiply, and `pink` extra ink from 0 to 1 (negative values draw paper lines on ink).
Then add `DIAGONAL: 18` to `PAT`. Rebuild; the node check does not parse GLSL, so take a screenshot to confirm.

## Lines, glow and light pools

- Box edges become `LineSegments` drawn with `LINE_VS/FS`; they boil and fog like the faces. Imported
  geometry gets edges from `EdgesGeometry` (angle threshold, default 35 degrees). `MAT.lineW` draws white lines.
- `makeGlowMat(color, { pulse, alpha, add, fog })`: unlit colour with a rim, for the accent (`MAT.glow` is
  BLUE). Keep it for what is real or important.
- `makeSpillMat(color, alpha, radial)`: a soft pool of light on a plane (used under real doors).
- `makeInkMat({ fade, toneMul, minTone, side })`: a private ink material; its `uFade` (0 to 1) dissolves the
  surface in noise, which is good for things that appear or vanish. Mark it `userData.own = true`.

## Lights and shadows

- The sun (`env.sun`, `env.sunDir`) casts one static shadow map baked when the level is built (1024 or
  2048 px fitted to the level's bounds). Moving objects do not cast shadows; that keeps frames cheap. Far
  `scatterDeco` fragments widen the bounds and soften shadows, so keep decoration within about 30 m.
- `L.light(x, y, z, radius, intensity)`: point lights, at most 8 per level reach the shader (a real door and a
  key pickup add one each). Intensity 0.5 to 0.9 reads as a lamp pool against ambient 0.5 (less in darker rooms); set `.i = 0` to switch one off.
- The player's lamp (`F` key) is a spot light from the camera, `PL.lampOn`; `env.lampMul` scales it per level.

## Mood and post effects

| Uniform | Effect | Set by |
|---|---|---|
| `U.uBoil` | line boil | `env.mood.boil` + threat + pulse |
| `U.uWarp` | geometry ripples (vertex warp) | `env.mood.warp` + pulse |
| `POST.uDouble` | double vision | `mood.double` + threat |
| `POST.uWave`, `uSwirl` | screen wobble, swirl | mood + pulse |
| `POST.uTendril`, `uTunnel` | ink creeping in from the edges | mood + threat |
| `POST.uChrom` | colour fringing | mood + pulse |
| `POST.uWarm`, `uRed` | firelight sepia, danger tint | set them directly |
| `POST.uInvert`, `uFlash`/`uFlashTone`, `uFade` | negative, flash (0 ink, 1 paper), fade to ink | `GAME.flash`, `GAME.fadeTo` |

`GAME.threat` (0 to 1) is rebuilt every frame from whatever enemies set it to, and `GAME.pulse` is a spike
that decays by 0.8 per second (`GAME.pulse = 0.6` after a scare). `SET.calm` scales warp, swirl, wave and
chromatic effects down for players sensitive to motion.

## Changing the palette

`PAPER`, `INK` and `BLUE` in `02_ink.js` and the CSS tokens `--paper`, `--ink`, `--blue` in `00_head.html` go
together. Tone 1 always means "paper colour", so a blueprint (paper `#1E3A5F`, ink `#E8EEF5`) or sepia
(`#E9DCC0` / `#3B2A1A`) works without touching the shaders; the accent should still contrast with both.

## Quality and performance

`R.qualityPreset()`: quality 0 (touch default) renders at 62 to 75 % pixel ratio without MSAA, 1024 px
shadows and a 60 % portal texture; 1 renders up to 1.5x pixel ratio with 2x MSAA; 2 up to 2x with 4x MSAA.
Change with `SET.quality = n; R.applyQuality(); saveSet();`. Cost is mostly fill rate (the hatch shader runs
two LOD levels per pixel) plus doubled scene cost while a portal is on screen; draw calls stay low because each
level is a few merged meshes. On a slow phone, pixel ratio is the lever that matters.
````

### `references/level-building.md`

<!-- bundle-file: references/level-building.md sha256=f6633b176f3156c9fd9ca1868e59317b5a877091827c6b4e5448c81aaa34e0b6 -->
````markdown
# Building levels

## Contents
- Units and conventions
- The Level API
- Build helpers
- Doors
- Environment (`L.env`)
- Worked example: a stair well (tested)
- Level design that works in ink
- Pitfalls

## Units and conventions

Metres; y is up on a normal floor. The player is 1.72 m tall (1.12 crouched), 0.56 m wide, walks 3.15 m/s,
runs 5.6, steps up 0.46 m without jumping and jumps about 2 m across at walking pace. Door openings are
1.1 x 2.25 m. Corridors feel right at 2 m wide or more, rooms at 3 m high or more. A door with yaw 0 faces +z:
you walk through it towards +z. `yawOf('+x')` gives the yaw for other directions.

## The Level API (`L` inside `build(L)`)

| Call | Does |
|---|---|
| `L.B(x0,y0,z0, x1,y1,z1, o)` | box by two corners: drawn and solid. `o`: `tone` (0.85), `pat` (`PAT.*`), `solid` (true), `surf` (footsteps: stone, wood, tile, carpet), `edges` (true), `faces` (bitmask), `vis: false` (collider only), `noRay` (sight passes through) |
| `L.BM(matrix4, hx,hy,hz, o)` | rotated box (decoration, no collider) |
| `L.cyl(x,y,z, r,h, o)` | cylinder standing on (x,y,z); collider is a box inside it unless `solid: false` |
| `L.addCol(x0,y0,z0, x1,y1,z1, o)` | invisible collider (railings, keeping players off a ledge) |
| `L.light(x,y,z, radius, intensity, {flicker})` | point light; returns an object whose `.i` you can change later |
| `L.trigger(x0,y0,z0, x1,y1,z1, fn, {once})` | runs `fn` when the player's centre enters the box (once by default) |
| `L.ent(obj)` / `L.add(object3d)` | an entity with `update(dt)` (and optional `reset()`, `off`) / any three.js object |
| `L.chunk('name')` | later boxes go into a separate mesh; hide it with `L.chunkObjs.name.visible = false` after build |
| `L.data`, `L.t`, `L.killU`, `L.surf` | free per-level state, seconds live, fall-out height, default footstep surface |

## Build helpers

```js
wallX(L, x0, x1, z0, z1, y0, y1, holes, o)   // wall running along x, thickness z0..z1; holes [{a0,a1,b0,b1}] in x and y
wallZ(L, z0, z1, x0, x1, y0, y1, holes, o)   // wall running along z
doorHole(c, y0)                              // the hole a standard door at position c (along the wall), floor y0, needs
stairs(L, x, y, z, dir, n, o)                // flight from the bottom of step 1 (centre of width); dir '+x'|'-x'|'+z'|'-z'
                                             // o: w 1.8, rise 0.22, run 0.34, rails, railSides [-1,1], solid (filled), tone, pat
                                             // returns {x, y, z}: the top end, so flights chain
rail(L, x0, z0, x1, z1, y)                   // balustrade with a collider
column(L, x, y, z, r, h, o)                  // base, shaft, capital
arch(L, cx, y, cz, axis, span, h, depth, o)  // piers and a round arch; axis 'x' spans along x
decoChunk(L, matrix4, kind, scale)           // floating fragment: 'stairs', 'arch', 'block', 'column', 'room'
scatterDeco(L, n, rmin, rmax, ymin, ymax, kinds, seed, centre)  // a ring of fragments drifting around the level
textPlane(L, x, y, z, nx, nz, w, h, scrawl('TEXT', 90))         // ink lettering on a wall facing (nx, nz)
lampVis(L, x, y, z, 'bulb'|'candle'|'panel'|'sconce')           // a visible lamp (pair it with L.light)
interact(L, pos, 'Prompt', fn, {r, cos, when})                  // "press E" on anything
buildObj(a => { a.box(...); a.cyl(...); }, {mat})               // a separate, movable inked object
```

## Doors

```js
stdEntrance(L, x, y, z, yaw)                 // where the player arrives; locked; sets L.spawn 1.35 m inside
exitDoor(L, x, y, z, yaw, { locked: true, lockMsg: 'Locked.' })  // the real way on: blue keyhole, light under it
new Door(L, { x, y, z, yaw, upQ, locked, onOpen, onTry, lockMsg, prompt, window: true, knocker: true, autoClose: 2 })
```

A door stands in a wall hole made with `doorHole()` at the same spot. `door.locked = false` unlocks it,
`door.open()`, `door.close(true)` (slam), `door.onOpen = d => ...`. Ordinary doors (no portal) just swing and
show whatever is behind them, so build a room there. Only the level's `exitDoor` leads to the next level.

## Environment (`L.env`)

```js
E.sunDir.set(-0.5, 0.8, 0.3); E.sun = 0.8;   // 0 = no sun and no baked shadow (indoors)
E.amb = 0.5;                                 // ambient light; 0.45-0.65 is the useful range
E.fogTone = 1; E.fogDen = 0.01;              // fog colour (1 paper, 0 ink) and density; 0.03+ swallows the distance
E.bgTone = null;                             // background tone (defaults to fogTone)
E.hatch = 9;                                 // hatch lines per metre at full size; 7 coarse, 11 fine
E.bed = { root: 55, fifth: 1.5, cut: 240, noise: 0.04, gain: 0.4 };  // ambient drone (see audio.md)
E.mood.boil = 0.1; E.mood.tendril = 0.2;     // post effects; see ink-rendering.md
```

## Worked example: a stair well (tested)

Four flights climb round an open shaft to an exit high in the east wall. Add it to `05_levels.js`, then set
`next: 4` on the level that should lead here.

```js
LEVELS[4] = {
  name: 'The Well', sub: 'up is the only way', next: 3,
  build(L) {
    const E = L.env; E.sunDir.set(0.2, 1, 0.1); E.sun = 0.9; E.amb = 0.45; E.fogDen = 0.014; L.killU = -12;
    const WALL = { pat: PAT.ASHLAR, tone: 0.88 }, SLAB = { pat: PAT.TILES, tone: 0.9 };
    L.B(-5, -0.5, -5, 5, 0, 5, SLAB);                                                   // floor
    wallX(L, -5.5, 5.5, -5.5, -5, 0, 14, [doorHole(0, 0)], WALL); stdEntrance(L, 0, 0, -5.25, 0);
    wallX(L, -5.5, 5.5, 5, 5.5, 0, 14, [], WALL);                                       // north
    L.B(-5.5, 0, -5, -5, 14, 5, WALL);                                                  // west
    let p = stairs(L, 4.2, 0, -3.0, '+z', 12, { w: 1.6, rails: true, railSides: [-1] }); // up the east side
    L.B(3.4, p.y - 0.4, p.z, 5, p.y, 5, SLAB);
    p = stairs(L, 3.4, p.y, 4.2, '-x', 12, { w: 1.6, rails: true, railSides: [-1] });     // along the north
    L.B(-5, p.y - 0.4, 3.4, p.x, p.y, 5, SLAB);
    p = stairs(L, -4.2, p.y, 3.4, '-z', 12, { w: 1.6, rails: true, railSides: [1] });     // down the west side
    L.B(-5, p.y - 0.4, -5, -3.4, p.y, p.z, SLAB);
    p = stairs(L, -3.4, p.y, -4.2, '+x', 12, { w: 1.6, rails: true, railSides: [1] });    // along the south
    L.B(p.x, p.y - 0.4, -5, 5, p.y, -3.4, SLAB);
    wallZ(L, -5, 5, 5, 5.5, 0, 14, [doorHole(-4.2, p.y)], WALL);                          // east wall, exit at the top
    exitDoor(L, 5.25, p.y, -4.2, yawOf('+x'));
    L.light(0, 12.5, 0, 16, 0.4); lampVis(L, 0, 12.5, 0, 'bulb');
  }
};
```

`stairs()` returns the top of each flight, so every landing and the next flight start from `p`; change one
number and the rest follows. The robot playtest walks through this exit in 10 frames.

## Level design that works in ink

- **One idea per level**: show it safely, test it, then twist it. Ink hides depth, so new ideas need room.
- **Show the blue early.** A glimpse of the exit from the start turns the level into a route puzzle instead
  of a search. Put a light where the player must make a decision.
- **Separate planes with light and fog.** Hatching flattens distance; a light pool (`L.light`) on a landing,
  a darker tone behind an opening, or denser fog behind the action restores it.
- **Vertical spaces read best**: stairs, galleries and shafts look superb in crosshatch; flat open fields
  look empty. Fill skies with `scatterDeco` fragments.
- **Two to five minutes per level**, and a quiet room after a scare.

## Pitfalls

- Only the first 8 lights in `L.plights` reach the shader. A real exit door adds one, and a key adds one.
- Coplanar faces flicker: offset decoration 1 to 2 cm off a wall (as `textPlane` does).
- A door without a matching `doorHole` sits inside a solid wall; one with a hole but no door leaves a gap.
- Everything under `y = L.killU` counts as fallen out of the world; keep it below your lowest floor.
- Boxes added after `L.finalize()` throw (the accumulator is gone); add moving things with `buildObj` + `L.add`.
````

### `references/testing.md`

<!-- bundle-file: references/testing.md sha256=e5f28242f97fcb2ab0a4830555c0868c2d40d0edeb04f2be48c914365b9b7b14 -->
````markdown
# Testing a pen-and-ink game

Headless Chromium with software WebGL (SwiftShader) renders the game exactly as a browser does, only slowly.
The scripts stub `requestAnimationFrame` before the page loads and drive the game with
`window.__game.step(n)`, so nothing depends on real time and every run produces the same frames.
Requirements: Python with `playwright` (Chromium installed) and, for video, `ffmpeg`.

## Pictures: `scripts/shoot.py`

```bash
python3 scripts/shoot.py games/title/dist/title.html                       # title + every level at its spawn
python3 scripts/shoot.py games/title/dist/title.html --shots views.json --size 1920x1080
python3 scripts/shoot.py games/title/dist/title.html --size 844x390 --quality 0   # a phone in landscape
```

`views.json` is a list of shots:

```json
[{"name": "gallery", "level": 1, "pos": [-3.5, 3.08, 6.8], "yaw": 3.14159, "pitch": 0.05, "steps": 12,
  "js": "const g = window.__game; g.step(30, 1/30, false); g.openExit();"}]
```

`level` 0 is the title screen. `pos` is the player's feet; `yaw` 0 looks towards -z and 3.14159 towards +z
(`look(yaw, pitch)`); `steps` frames are run before the picture (the level's fade-in is skipped). `js` runs
in the page after placing the player, with `window.__game` available (the game's own code is in a closed
scope; reach it through that object). Images go to `shots/` next to the html, with `shots.json` holding the
game state for each. Exit status 1 means a JavaScript error happened; the errors are printed.

Look at every image. Check: is the exit (blue) visible or findable, does the hatching leave enough paper to
read shapes, is anything clipping through a wall, is text legible, does a phone-size view still show the
crosshair and prompts.

## Proof it can be finished: `scripts/playtest.py`

```bash
python3 scripts/playtest.py games/title/dist/title.html
```

For every level it checks that the spawn stands on the ground, that the next level is built within about
a second, that walking through the opened exit reaches the next level, and that every gravity zone switches
gravity. Enemies are switched off. It does not check that a human can reach the exit (keys, jumps, puzzles);
for that, script the route: `hold('KeyW')` for held keys, `press('jump')` or `press('act')` for single presses,
and `step` to advance; or play it.

## Writing your own checks

```python
from playwright.sync_api import sync_playwright
import sys; sys.dont_write_bytecode = True; sys.path.insert(0, '<skill>/scripts')
from _pen_ink_common import open_game
with sync_playwright() as p:
    b, pg, errs = open_game(p, 'dist/title.html', 960, 540)
    print(pg.evaluate("""() => { const g = window.__game; g.play(1);
        g.tp(3, 0.02, -0.5); g.step(60, 1/30, false); return g.state(); }"""))
    b.close()
```

`window.__game`: `play(i)`, `step(n, dt, render)`, `tp(x,y,z)`, `look(yaw,pitch)`, `hold('KeyW', true)`, `press('jump')`,
`openExit()`, `faceExit(back)`, `state()` (state, level, position, up, grounded, errors), plus `GAME`, `PL`,
`LEVELS`, `U`, `POST`, `SET`, `AU`, `ERRS`.

## Before you hand it over

1. `playtest.py` passes, and `shoot.py` shows no errors.
2. You have looked at the title, every level, the key moments, and a phone-size frame at quality 0.
3. The file is one HTML of about 1 MB plus your code, and opens from disk with no network.
4. If you can, someone has played it in Chrome, Firefox and Safari, on a phone with touch, and with a pad.
   Headless tests cannot judge feel, difficulty, or sound; say which of these were not checked by a person.
````

### `references/trailer-and-release.md`

<!-- bundle-file: references/trailer-and-release.md sha256=f6ec4a112853960dbe2e8ce3ba81410aaa34f977c771cd52a91119ae78048035 -->
````markdown
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
````

### `assets/promo/cues_template.js`

<!-- bundle-file: assets/promo/cues_template.js sha256=c3a3743292dba225cba9fa12bc2997a6513d3c7d2a015ff4359b30e2774157ce -->
````javascript
// Cue sheet for the starter trailer (director_template.js). render_audio.py calls window.__cues(E) and renders each
// section offline with the game's own synth, then mixes them at their start times. Every sound is an AU call.
// E = { fps, start: {shot: seconds}, frames: {shot: n}, total, logs: {shot: [per-frame info]} }
// A section: { t0, dur, play(a), cut?, fade?, gain? }. Use a new section where the picture hard-cuts, so reverb
// tails from before the cut stop with it (cut = where to stop, fade = seconds of fade before the stop).
window.__cues = E => {
  const S = E.start;
  const BED1 = { root: 55, fifth: 1.5, cut: 260, noise: 0.05, noiseF: 600, gain: 0.42 }, BED2 = { root: 52, fifth: 1.414, cut: 240, gain: 0.4 };
  const cardAt = S['s05-card'];
  return [
    { t0: 0, dur: cardAt + 0.6, cut: cardAt, fade: 0.25, play: a => {
      a.bed(0, BED1);
      a.melody([0.3, 0.86, 1.42, 1.98, 2.54]);                                  // the title music box, one call per note
      __snd.steps(E, 's02-hall').forEach(t => a.at(t, () => AU.step('stone', 0.8)));
      a.at(S['s03-door'] + 24 / E.fps, () => AU.creak(null, 1.4, 0.25));        // the door opens on frame 24 of s03
      a.at(S['s03-door'] + 0.1, () => AU.chime(0.08));
      a.bed(S['s04-turn'], BED2);
      __snd.steps(E, 's04-turn').forEach(t => a.at(t, () => AU.step('wood', 0.7)));
      __snd.flips(E, 's04-turn').forEach(t => { a.at(t, () => AU.grav()); a.at(t + 0.05, () => AU.whoosh(null, 0.3)); });
    } },
    { t0: cardAt, dur: E.total - cardAt, play: a => {                            // the card: a slam, then the drone alone
      a.at(0.05, () => AU.slam(null, 0.6));
      a.bed(0.3, BED1);
      a.at(E.total - cardAt - 2.5, () => AU.stopBeds(2));
    } }
  ];
};
````

### `assets/promo/director_template.js`

<!-- bundle-file: assets/promo/director_template.js sha256=90c2cc5c903234f07130fb9f9152fd9868f9864052d57ee97f6176c09e1ae547 -->
````javascript
// Trailer director for a pen-and-ink game (works as-is with the starter's three levels; copy it and rewrite the shots).
// film_shots.py evaluates this inside the game's own scope (promo build), so GAME, PL, POST, LEVELS... are all here.
// A shot = { name, n (frames at 30 fps), prep() (set the scene once), frame(i) (pose, then draw()) }.
// Rules that keep shots repeatable: seed Math.random in prep, freeze or script the player, never wait on real time.
(() => {
  const FPS = 30, dt = 1 / FPS;
  const ease = t => t * t * (3 - 2 * t), mix = (a, b, t) => a + (b - a) * t, k01 = (i, a, b) => clamp((i - a) / (b - a), 0, 1);
  const PAPER_C = '#E4E0D5', INK_C = '#171511', TITLE = document.title;
  const css = document.createElement('style');
  css.textContent = '#ui,#loading{display:none!important}' +
    '#trText{position:fixed;left:0;right:0;bottom:11%;text-align:center;z-index:999;pointer-events:none;opacity:0;padding:0 9%;font:italic 5.2vh/1.25 "IM Fell English",Georgia,serif;color:' + INK_C + '}' +
    '#trCard{position:fixed;inset:0;z-index:998;display:flex;flex-direction:column;align-items:center;justify-content:center;opacity:0;pointer-events:none;' +
    'background:radial-gradient(ellipse 62% 58% at 50% 50%,rgba(228,224,213,.97) 0%,rgba(228,224,213,.9) 46%,rgba(228,224,213,0) 100%)}' +
    '#trCard h1{font:16.5vh/.9 "IM Fell English SC",Georgia,serif;margin:0 0 .3em;color:' + INK_C + '}' +
    '#trCard .c1{font:italic 4.3vh/1.2 "IM Fell English",Georgia,serif;color:' + INK_C + '}' +
    '#trCard .c2{font:3.3vh/1.5 "Special Elite","Courier New",monospace;color:' + INK_C + ';margin-top:.4em}';
  document.head.appendChild(css);
  const txt = document.createElement('div'); txt.id = 'trText'; document.body.appendChild(txt);
  const card = document.createElement('div'); card.id = 'trCard';
  card.innerHTML = `<h1>${TITLE}</h1><div class="c1">Play free in your browser</div><div class="c2">yourname.itch.io/your-game</div>`; // EDIT the card text
  document.body.appendChild(card);
  const cardEls = [...card.children];
  // a line of text, fading in over 0.4 s from frame a and out by frame b; paper halo so it reads over ink
  function say(s, o) { if (txt._s !== s) { txt.textContent = s; txt._s = s; } txt.style.opacity = (o || 0).toFixed(3); txt.style.textShadow = `0 0 6px ${PAPER_C},0 0 16px ${PAPER_C},0 0 30px ${PAPER_C}`; }
  function beat(i, a, b, s) { const t = i / FPS; say(s, clamp(Math.min((t - a / FPS) / 0.4, (b / FPS - t) / 0.4), 0, 1)); }
  const keepFov = SET.fov;
  function prep(level, seed, o = {}) { // level 0 = the title view
    Math.random = mulberry32(seed);
    SET.fov = o.fov || keepFov;
    if (level === 0) GAME.titleLevel(); else GAME.newRun(level);
    UI.show(null); UI.hud(false); GAME.toast = () => { }; GAME.hint = () => { }; GAME.caught = () => { };
    GAME.fadeT = null; POST.uFade.value = 0; CAM.fov = SET.fov; CAM.updateProjectionMatrix();
    for (const k in IN.keys) IN.keys[k] = false;
    PL.frozen = true; card.style.opacity = 0; say('', 0);
    for (let i = 0; i < (o.warm || 0); i++) GAME.update(dt); // e.g. warm: 30 lets the next level build behind the exit door
  }
  function place(x, y, z, yaw, pitch) { PL.pos.set(x, y, z); PL.vel.set(0, 0, 0); PL.yaw = yaw; PL.pitch = pitch || 0; }
  function draw(o = {}) {
    GAME.update(dt);
    if (o.post) o.post();
    GAME.fadeT = null; POST.uFade.value = o.fade || 0;
    if (o.flash != null) { POST.uFlash.value = o.flash; POST.uFlashTone.value = o.flashTone == null ? 1 : o.flashTone; }
    if (!window.__tr.noRender) GAME.render();
  }
  const quiet = () => { for (const e of GAME.L.ents) e.off = true; };
  const S = [];
  // 1. the title view, a line types itself out
  S.push({ name: 's01-title', n: 90, prep() { prep(0, 11); GAME.titleT = 30; },
    frame(i) { const line = 'Somewhere in the drawing there is a door.'; const k = Math.floor(k01(i, 8, 60) * line.length);
      say(line.slice(0, k), i < 8 ? 0 : clamp((89 - i) / 10, 0, 1)); draw({ fade: clamp(1 - i / 20, 0, 1) }); } });
  // 2. walking into the stair hall
  S.push({ name: 's02-hall', n: 75, prep() { prep(1, 12); place(0, 0, -5.4, Math.PI, 0.1); PL.frozen = false; IN.keys.KeyW = true; },
    frame(i) { PL.pitch = mix(0.1, 0.32, ease(i / 74)); beat(i, 6, 72, 'The walls draw themselves.'); draw(); } });
  // 3. the exit door opens onto the next level
  S.push({ name: 's03-door', n: 78, prep() { prep(1, 13, { warm: 30 }); place(-3.5, 3.08, 6.2, Math.PI, 0.02); },
    frame(i) { PL.pos.z = mix(6.2, 8.9, ease(i / 77)); if (i === 24) { const d = GAME.L.exitDoor; d.locked = false; GAME.linkNext(); d.open(); }
      beat(i, 2, 34, 'Blue is real.'); draw(); } });
  // 4. through the blue arch: down turns into the wall
  S.push({ name: 's04-turn', n: 70, prep() { prep(2, 14); quiet(); place(0, 0, 2.6, Math.PI, 0.18); PL.frozen = false; IN.keys.KeyW = true; },
    frame(i) { quiet(); if (i >= 40) PL.pitch = mix(0.18, 0.05, k01(i, 40, 69)); draw(); } });
  // 5. the title card over the title view
  S.push({ name: 's05-card', n: 120, prep() { prep(0, 15); GAME.titleT = 99; },
    frame(i) { say('', 0); card.style.opacity = 1; cardEls.forEach((e, k) => e.style.opacity = ease(k01(i, k * 10, k * 10 + 14)).toFixed(3));
      draw({ fade: clamp(1 - i / 10, 0, 1) }); } });
  window.__tr = {
    S, FPS, noRender: false,
    names() { return S.map(s => s.name + ':' + s.n); },
    prep(k) { txt.style.opacity = 0; txt._s = null; S[k].prep.call(S[k]); },
    frame(k, i) { S[k].frame.call(S[k], i); },
    // per-frame facts render_audio.py turns into sound timings (footsteps from pos, flips from up)
    info() { return JSON.stringify({ idx: GAME.idx, pos: PL.pos.toArray().map(v => +v.toFixed(2)), up: PL.up.toArray().map(v => Math.round(v)), gr: PL.grounded ? 1 : 0, state: GAME.state }); }
  };
})();
````

### `assets/promo/offline_audio.js`

<!-- bundle-file: assets/promo/offline_audio.js sha256=e3a1c5b6e2a34800a50c01c0f25f5acfe4b990edfc114c6d17509ba5edd15c9b -->
````javascript
// Offline renderer for the game's own synth (AU), used by render_audio.py. Runs inside the game scope (promo build).
// Trick: AU is re-initialised on an OfflineAudioContext seen through a proxy whose currentTime is whatever moment
// we are scheduling, so every AU call (which schedules at ctx.currentTime + delay) lands exactly on the cue time.
// AU.melody uses setInterval; the api captures that callback so a cue sheet can place each note by hand.
(() => {
  const SR = 48000;
  function mkCtx(dur) {
    const real = new OfflineAudioContext(2, Math.ceil(SR * dur), SR), st = { OFF: 0 };
    const wrap = n => { const s0 = n.start.bind(n); n.start = (w, ...r) => s0(w ? w : st.OFF, ...r); return n; };
    const px = new Proxy(real, {
      get(t, k) {
        if (k === 'currentTime') return st.OFF;
        if (k === 'createOscillator') return () => wrap(t.createOscillator());
        if (k === 'createBufferSource') return () => wrap(t.createBufferSource());
        const v = Reflect.get(t, k, t); return typeof v === 'function' ? v.bind(t) : v;
      }
    });
    return { real, px, st };
  }
  function toB64(buf) { // interleaved float32 stereo, base64
    const n = buf.length, L = buf.getChannelData(0), R = buf.numberOfChannels > 1 ? buf.getChannelData(1) : L;
    const out = new Float32Array(n * 2); for (let i = 0; i < n; i++) { out[2 * i] = L[i]; out[2 * i + 1] = R[i]; }
    const bytes = new Uint8Array(out.buffer); let s = ''; const CH = 0x8000;
    for (let i = 0; i < bytes.length; i += CH) s += String.fromCharCode.apply(null, bytes.subarray(i, i + CH));
    return btoa(s);
  }
  async function render(dur, play) {
    const { real, px, st } = mkCtx(dur);
    AU.ctx = null; AU.ok = false; AU.beds = []; AU._mel = null;
    const AC = window.AudioContext; window.AudioContext = function () { return px; };
    try { AU.init(); } finally { window.AudioContext = AC; }
    CAM.position.set(0, 0, 0); CAM.quaternion.identity(); CAM.updateMatrixWorld(); // positional sounds are heard from the origin
    const SI = window.setInterval, CI = window.clearInterval; let cap = null;
    window.setInterval = fn => { cap = fn; return 0; }; window.clearInterval = () => { };
    const at = (t, fn) => { st.OFF = Math.max(0, t); fn(); };
    const api = {
      at,                                                    // at(seconds, () => AU.slam(null, 0.5))
      bed: (t, spec) => at(t, () => AU.bed(spec)),           // an ambient drone (a level's env.bed)
      stopBeds: (t, fade) => at(t, () => AU.stopBeds(fade)),
      melody(times) { at(times[0], () => AU.melody(true)); const note = cap; cap = null; if (note) times.forEach(t => at(t, note)); },
      v: (x, y, z) => new V3(x, y, z)                         // a position to pan a sound from
    };
    try { play(api); } finally { window.setInterval = SI; window.clearInterval = CI; }
    return toB64(await real.startRendering());
  }
  // footsteps from a shot's per-frame log: a step every `every` metres walked on the ground, plus gravity flips
  function steps(E, shot, every = 0.8) {
    const L = E.logs[shot] || [], out = [], t0 = E.start[shot] || 0; let acc = every * 0.45;
    for (let i = 1; i < L.length; i++) {
      const a = L[i - 1], b = L[i]; if (String(a.up) !== String(b.up) || !b.gr) continue;
      const d = b.pos.map((v, k) => v - a.pos[k]), u = b.up, dot = d[0] * u[0] + d[1] * u[1] + d[2] * u[2];
      acc += Math.hypot(d[0] - dot * u[0], d[1] - dot * u[1], d[2] - dot * u[2]);
      if (acc >= every) { acc -= every; out.push(+(t0 + i / E.fps).toFixed(3)); }
    }
    return out;
  }
  function flips(E, shot) { const L = E.logs[shot] || [], t0 = E.start[shot] || 0; return L.map((f, i) => i && String(f.up) !== String(L[i - 1].up) ? +(t0 + i / E.fps).toFixed(3) : null).filter(t => t != null); }
  window.__snd = { render, steps, flips };
})();
````

### `assets/starter/src/00_head.html`

<!-- bundle-file: assets/starter/src/00_head.html sha256=14c28419e4bf01d7f1b4db0cc005d48f89888eaf82e807c836fe6295bcb6a0f5 -->
````html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover">
<meta name="theme-color" content="#171511">
<title>{{TITLE}}</title>
<!--FONTS-->
<style>
:root{
  --paper:#E4E0D5; --paper2:#D2CBBB; --ink:#171511; --ink2:#4A453B; --blue:#5C64FF;
  --fell:"IM Fell English",Georgia,"Times New Roman",serif;
  --fellsc:"IM Fell English SC","IM Fell English",Georgia,serif;
  --type:"Special Elite","Courier New",Courier,monospace;
  --safeL:env(safe-area-inset-left,0px); --safeR:env(safe-area-inset-right,0px); --safeB:env(safe-area-inset-bottom,0px);
}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{margin:0;height:100%;overflow:hidden;background:var(--ink);color:var(--ink);font-family:var(--fell);
  -webkit-user-select:none;user-select:none;touch-action:none;overscroll-behavior:none}
#gl{position:fixed;inset:0;width:100%;height:100%;display:block;outline:none;background:var(--paper)}
#ui{position:fixed;inset:0;pointer-events:none;z-index:5}
.screen{position:absolute;inset:0;display:none;pointer-events:auto}
.screen.show{display:flex}
#title{flex-direction:column;justify-content:center;padding:0 calc(7vw + var(--safeL));
  background:linear-gradient(90deg,rgba(228,224,213,.96) 0%,rgba(228,224,213,.86) 36%,rgba(228,224,213,0) 72%)}
.logo{font-family:var(--fellsc);font-size:clamp(44px,9vw,120px);line-height:.9;margin:0;letter-spacing:.03em;filter:url(#wob)}
.tag{font-style:italic;font-size:clamp(17px,2.2vw,24px);color:var(--ink2);margin:.5em 0 1.3em;max-width:30ch}
.btn{font:italic clamp(22px,2.8vw,32px)/1.25 var(--fell);background:none;border:0;color:var(--ink);cursor:pointer;padding:.1em 0;text-align:left}
.btn:hover,.btn:focus-visible{text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:5px;outline:none}
.fine{position:absolute;left:calc(7vw + var(--safeL));bottom:calc(18px + var(--safeB));font-size:14px;color:var(--ink2);max-width:52ch;line-height:1.35}
#pause{justify-content:center;align-items:center;background:rgba(228,224,213,.84)}
#pause .panel{text-align:center}
#hud{position:absolute;inset:0;display:none}
#hud.show{display:block}
#xh{position:absolute;left:50%;top:50%;width:5px;height:5px;margin:-2.5px;border-radius:50%;background:var(--ink);box-shadow:0 0 0 2px rgba(228,224,213,.7)}
#prompt{position:absolute;left:50%;top:57%;transform:translateX(-50%);font:italic 21px var(--fell);white-space:nowrap;
  text-shadow:0 0 6px var(--paper),0 0 14px var(--paper);opacity:0;transition:opacity .2s}
#prompt.show{opacity:1}
#toast{white-space:pre-line;position:absolute;left:50%;bottom:calc(17% + var(--safeB));transform:translateX(-50%);font:18px/1.4 var(--type);text-align:center;
  max-width:min(560px,86vw);text-shadow:0 0 5px var(--paper),0 0 12px var(--paper),0 0 20px var(--paper);opacity:0;transition:opacity .5s}
#toast.show{opacity:1}
#touch{position:absolute;inset:0;display:none}
#touch.show{display:block}
#joy{position:absolute;left:calc(26px + var(--safeL));bottom:calc(26px + var(--safeB));width:128px;height:128px;border-radius:50%;
  border:2px solid rgba(23,21,17,.55);background:rgba(228,224,213,.35)}
#joyK{position:absolute;left:37px;top:37px;width:50px;height:50px;border-radius:50%;background:rgba(23,21,17,.72)}
#joy.sprint #joyK{background:var(--ink)}
.tb{position:absolute;width:66px;height:66px;border-radius:50%;border:2px solid var(--ink);background:rgba(228,224,213,.82);
  font:italic 16px var(--fell);display:grid;place-items:center;pointer-events:auto}
#tAct{right:calc(26px + var(--safeR));bottom:calc(112px + var(--safeB))}
#tJump{right:calc(112px + var(--safeR));bottom:calc(26px + var(--safeB))}
#tCrouch{right:calc(26px + var(--safeR));bottom:calc(198px + var(--safeB))}
#tLamp{right:calc(198px + var(--safeR));bottom:calc(26px + var(--safeB))}
#tPause{right:calc(14px + var(--safeR));top:calc(14px + env(safe-area-inset-top,0px));width:46px;height:46px;font-size:14px}
.tb.on{background:var(--ink);color:var(--paper)}
#loading{position:fixed;inset:0;display:grid;place-items:center;background:var(--paper);font:40px var(--fellsc);z-index:9}
</style>
</head>
<body>
<svg width="0" height="0" style="position:absolute" aria-hidden="true"><filter id="wob"><feTurbulence type="fractalNoise" baseFrequency=".04" numOctaves="2" seed="3"/><feDisplacementMap in="SourceGraphic" scale="3"/></filter></svg>
<canvas id="gl" tabindex="0"></canvas>
<div id="ui">
  <section id="title" class="screen show">
    <h1 class="logo">{{TITLE}}</h1>
    <div class="tag">A world drawn in ink. Find the door with the blue keyhole.</div>
    <div><button class="btn" id="bBegin">Begin</button></div>
    <div class="fine" id="help">WASD or arrows to move, mouse to look, Shift to run, Space to jump, E to open. On a phone or tablet: left thumb moves, drag on the right to look.</div>
  </section>
  <section id="pause" class="screen"><div class="panel"><div class="logo" style="font-size:52px">Paused</div><button class="btn" id="bResume" style="text-align:center">Resume</button></div></section>
  <div id="hud"><div id="xh"></div><div id="prompt"></div><div id="toast"></div></div>
  <div id="touch"><div id="joy"><div id="joyK"></div></div><div class="tb" id="tAct">open</div><div class="tb" id="tJump">jump</div><div class="tb" id="tCrouch">duck</div><div class="tb" id="tLamp">lamp</div><div class="tb" id="tPause">pause</div></div>
</div>
<div id="loading">{{TITLE}}</div>
````

### `assets/starter/src/01_core.js`

<!-- bundle-file: assets/starter/src/01_core.js sha256=4a5e4f8e5fba86599cc54780d8ccc5640310e2029a988d4fd7a38ab7708b9c08 -->
````javascript
'use strict';
/* ===================== core: utilities, settings, synthesized audio ===================== */
const TAU = Math.PI * 2;
const clamp = (v, a, b) => v < a ? a : v > b ? b : v;
const lerp = (a, b, t) => a + (b - a) * t;
const smooth = t => t * t * (3 - 2 * t);
const damp = (a, b, k, dt) => lerp(a, b, 1 - Math.exp(-k * dt));
function mulberry32(a) { return function () { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
let RNG = mulberry32(1);
const seedRng = s => { RNG = mulberry32(s >>> 0); };      // level building uses RNG, so a level looks the same every time
const rnd = (a = 0, b = 1) => a + (b - a) * RNG();
const mrand = (a = 0, b = 1) => a + (b - a) * Math.random(); // sound and particles use Math.random
function hash1(n) { n = Math.sin(n * 127.1 + 11.7) * 43758.5453; return n - Math.floor(n); }
function noise1(x) { const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f); return lerp(hash1(i), hash1(i + 1), u) * 2 - 1; }
const $ = id => document.getElementById(id);
const IS_TOUCH = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0 && matchMedia('(pointer:coarse)').matches);

/* one prefix for everything this game saves, so games served from the same host (itch.io) never collide */
const Store = {
  get(k, d) { try { const v = localStorage.getItem('{{SLUG}}_' + k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } },
  set(k, v) { try { localStorage.setItem('{{SLUG}}_' + k, JSON.stringify(v)); } catch (e) { } }
};
const SET = Object.assign({ sens: 1, invert: 0, fov: 74, quality: IS_TOUCH ? 0 : 1, vol: 0.85, mus: 0.6, calm: 0 }, Store.get('set', {}));
function saveSet() { Store.set('set', SET); }

/* ===================== AUDIO: everything is synthesized, nothing is downloaded =====================
   Every sound schedules itself at ctx.currentTime (+ delay). Keep that pattern: the promo pipeline renders
   the same functions offline by swapping in an OfflineAudioContext whose "now" is the cue time. */
const AU = {
  ctx: null, ok: false, beds: [],
  init() {
    if (this.ctx) return;
    try { const C = window.AudioContext || window.webkitAudioContext; if (!C) return; this.ctx = new C(); } catch (e) { return; }
    const c = this.ctx;
    this.comp = c.createDynamicsCompressor(); this.comp.threshold.value = -16; this.comp.knee.value = 12; this.comp.ratio.value = 4;
    this.comp.attack.value = 0.004; this.comp.release.value = 0.25; this.comp.connect(c.destination);
    this.master = c.createGain(); this.master.connect(this.comp);
    this.music = c.createGain(); this.music.connect(this.master);
    this.sfx = c.createGain(); this.sfx.connect(this.master);
    this.bedBus = c.createGain(); this.bedBus.connect(this.master);
    this.rev = c.createConvolver(); this.rev.buffer = this.impulse(3.2, 2.6);
    this.revOut = c.createGain(); this.revOut.gain.value = 0.55; this.rev.connect(this.revOut); this.revOut.connect(this.master);
    this.revSend = c.createGain(); this.revSend.gain.value = 0.4; this.revSend.connect(this.rev);
    this.noiseBuf = this.makeNoise(3); this.brownBuf = this.makeBrown(4);
    this.ok = true; this.applyVol();
  },
  applyVol() { if (!this.ok) return; const t = this.ctx.currentTime; this.master.gain.setTargetAtTime(SET.vol, t, 0.05); this.music.gain.setTargetAtTime(SET.mus, t, 0.1); },
  resume() { if (this.ctx && this.ctx.state !== 'running') { try { this.ctx.resume(); } catch (e) { } } },
  impulse(sec, decay) {
    const c = this.ctx, n = Math.floor(c.sampleRate * sec), b = c.createBuffer(2, n, c.sampleRate);
    for (let ch = 0; ch < 2; ch++) { const d = b.getChannelData(ch); for (let i = 0; i < n; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / n, decay); }
    return b;
  },
  makeNoise(sec) { const c = this.ctx, n = c.sampleRate * sec, b = c.createBuffer(1, n, c.sampleRate), d = b.getChannelData(0); for (let i = 0; i < n; i++) d[i] = Math.random() * 2 - 1; return b; },
  makeBrown(sec) { const c = this.ctx, n = c.sampleRate * sec, b = c.createBuffer(1, n, c.sampleRate), d = b.getChannelData(0); let l = 0; for (let i = 0; i < n; i++) { l = (l + 0.02 * (Math.random() * 2 - 1)) / 1.02; d[i] = l * 3.5; } return b; },
  out(pan, dest) {
    const c = this.ctx, g = c.createGain(); let node = g;
    if (pan != null && c.createStereoPanner) { const p = c.createStereoPanner(); p.pan.value = clamp(pan, -1, 1); g.connect(p); node = p; }
    node.connect(dest || this.sfx); return g;
  },
  spatial(pos, ref = 1) { // pan and distance gain for a world position, from the camera
    if (!pos || !window.CAM) return { pan: 0, gain: 1, muf: 0 };
    const d = _au1.copy(pos).sub(CAM.position), dist = d.length(); d.normalize();
    const right = _au2.set(1, 0, 0).applyQuaternion(CAM.quaternion), fwd = _au3.set(0, 0, -1).applyQuaternion(CAM.quaternion);
    return { pan: clamp(d.dot(right), -1, 1) * 0.85, gain: ref / (1 + dist * 0.22 / ref), muf: d.dot(fwd) < -0.2 ? 1 : 0, dist };
  },
  noiseHit(o) { // {dur, f, q, type, gain, pan, rev, attack, fEnd, dest, brown, delay}
    if (!this.ok) return; const c = this.ctx, t = c.currentTime + (o.delay || 0);
    const s = c.createBufferSource(); s.buffer = o.brown ? this.brownBuf : this.noiseBuf; s.loop = true;
    const f = c.createBiquadFilter(); f.type = o.type || 'bandpass'; f.frequency.setValueAtTime(o.f || 1000, t); f.Q.value = o.q || 1;
    if (o.fEnd) f.frequency.exponentialRampToValueAtTime(o.fEnd, t + o.dur);
    const g = c.createGain(); g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(Math.max(0.0002, o.gain || 0.3), t + (o.attack || 0.004));
    g.gain.exponentialRampToValueAtTime(0.0001, t + o.dur);
    s.connect(f); f.connect(g); g.connect(this.out(o.pan, o.dest));
    if (o.rev) { const rs = c.createGain(); rs.gain.value = o.rev; g.connect(rs); rs.connect(this.revSend); }
    s.start(t, Math.random() * 2); s.stop(t + o.dur + 0.05);
  },
  tone(o) { // {f, fEnd, dur, type, gain, pan, attack, rev, dest, delay, lp}
    if (!this.ok) return; const c = this.ctx, t = c.currentTime + (o.delay || 0);
    const osc = c.createOscillator(); osc.type = o.type || 'sine'; osc.frequency.setValueAtTime(o.f, t);
    if (o.fEnd) osc.frequency.exponentialRampToValueAtTime(Math.max(1, o.fEnd), t + o.dur);
    const g = c.createGain(); g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(Math.max(0.0002, o.gain || 0.2), t + (o.attack || 0.005));
    g.gain.exponentialRampToValueAtTime(0.0001, t + o.dur);
    let last = osc; if (o.lp) { const f = c.createBiquadFilter(); f.type = 'lowpass'; f.frequency.value = o.lp; osc.connect(f); last = f; }
    last.connect(g); g.connect(this.out(o.pan, o.dest));
    if (o.rev) { const rs = c.createGain(); rs.gain.value = o.rev; g.connect(rs); rs.connect(this.revSend); }
    osc.start(t); osc.stop(t + o.dur + 0.05);
  },
  /* ---------- effects ---------- */
  step(surface, loud = 1) {
    const s = { stone: [1300, 0.07, 0.10], wood: [520, 0.09, 0.13], tile: [2100, 0.05, 0.08], carpet: [700, 0.06, 0.05] }[surface] || [1300, 0.07, 0.1];
    this.noiseHit({ f: s[0] * mrand(0.85, 1.15), q: 1.2, dur: s[1], gain: s[2] * loud, rev: 0.25 });
    this.tone({ f: surface === 'wood' ? 140 : 90, fEnd: 50, dur: 0.07, gain: 0.08 * loud });
  },
  land(h) { this.noiseHit({ f: 500, q: 0.8, dur: 0.15, gain: clamp(0.08 + h * 0.05, 0.08, 0.4), type: 'lowpass', rev: 0.3 }); this.tone({ f: 70, fEnd: 38, dur: 0.18, gain: clamp(0.1 + h * 0.05, 0.1, 0.45) }); },
  creak(pos, dur = 1.1, gain = 0.22) { // a door: a sawtooth wandering in pitch, chopped by a square LFO
    if (!this.ok) return; const c = this.ctx, t = c.currentTime, sp = this.spatial(pos);
    const o = c.createOscillator(); o.type = 'sawtooth'; let f = mrand(70, 120); o.frequency.setValueAtTime(f, t);
    for (let i = 1; i <= 12; i++) { f = clamp(f * mrand(0.82, 1.22), 55, 320); o.frequency.linearRampToValueAtTime(f, t + i * dur / 12); }
    const lfo = c.createOscillator(); lfo.type = 'square'; lfo.frequency.setValueAtTime(mrand(12, 26), t); lfo.frequency.linearRampToValueAtTime(mrand(20, 40), t + dur);
    const lg = c.createGain(); lg.gain.value = 0.5; lfo.connect(lg); const amp = c.createGain(); amp.gain.value = 0.5; lg.connect(amp.gain);
    const bp = c.createBiquadFilter(); bp.type = 'bandpass'; bp.frequency.value = mrand(700, 1300); bp.Q.value = 2.5;
    const env = c.createGain(); env.gain.setValueAtTime(0.0001, t); env.gain.exponentialRampToValueAtTime(gain * sp.gain, t + 0.06); env.gain.setValueAtTime(gain * sp.gain, t + dur * 0.7); env.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(bp); bp.connect(amp); amp.connect(env); env.connect(this.out(sp.pan)); const rs = c.createGain(); rs.gain.value = 0.3; env.connect(rs); rs.connect(this.revSend);
    o.start(t); lfo.start(t); o.stop(t + dur + 0.1); lfo.stop(t + dur + 0.1);
  },
  slam(pos, gain = 0.5) {
    const sp = this.spatial(pos);
    this.noiseHit({ f: 700, fEnd: 120, type: 'lowpass', q: 0.7, dur: 0.45, gain: gain * sp.gain, pan: sp.pan, rev: 0.9 });
    this.tone({ f: 62, fEnd: 30, dur: 0.4, gain: gain * 0.9 * sp.gain, pan: sp.pan });
  },
  knock(pos, n = 2, gain = 0.45) {
    const sp = this.spatial(pos);
    for (let i = 0; i < n; i++) {
      const d = i * 0.24;
      this.tone({ f: 170, fEnd: 120, dur: 0.11, gain: gain * sp.gain, pan: sp.pan, delay: d, rev: 0.6, lp: sp.muf ? 500 : 0 });
      this.noiseHit({ f: sp.muf ? 700 : 1600, q: 3, dur: 0.035, gain: gain * 0.5 * sp.gain, pan: sp.pan, delay: d });
    }
  },
  click() { this.noiseHit({ f: 2600, q: 2, dur: 0.03, gain: 0.06 }); },
  rattle(pos) { for (let i = 0; i < 5; i++) this.noiseHit({ f: mrand(1800, 3200), q: 6, dur: 0.04, gain: 0.12, delay: i * 0.06 + mrand(0, 0.02) }); },
  chime(gain = 0.18) { [1, 2.01, 3.03].forEach((m, i) => this.tone({ f: 1046 * m, dur: 0.9 - i * 0.2, gain: gain / (i + 1), rev: 0.6 })); },
  boom(gain = 0.5, delay = 0) { this.tone({ f: 70, fEnd: 24, dur: 1.6, gain, delay, rev: 0.9 }); this.noiseHit({ f: 400, fEnd: 60, type: 'lowpass', dur: 1.8, gain: gain * 0.6, delay, brown: true, rev: 0.9 }); },
  whoosh(pos, gain = 0.3) { const sp = this.spatial(pos, 2); this.noiseHit({ f: 300, fEnd: 1400, q: 1.5, dur: 0.6, gain: gain * sp.gain, pan: sp.pan, attack: 0.25 }); },
  grav() { this.tone({ f: 220, fEnd: 55, dur: 0.7, gain: 0.25, type: 'sine', rev: 0.5 }); this.noiseHit({ f: 800, fEnd: 200, q: 1, dur: 0.6, gain: 0.12, rev: 0.6 }); },
  shriek(pos) { const sp = this.spatial(pos, 2); this.noiseHit({ f: 1500, fEnd: 5200, q: 9, dur: 0.9, gain: 0.4 * sp.gain + 0.1, pan: sp.pan, rev: 0.7 }); this.tone({ f: 900, fEnd: 2300, dur: 0.8, type: 'square', gain: 0.07, pan: sp.pan, lp: 2500 }); },
  /* a slow, out-of-tune music box for the title (one call per note, so it can be scheduled offline too) */
  melody(on) {
    if (!this.ok) return; if (this._mel) { clearInterval(this._mel); this._mel = null; } if (!on) return;
    const notes = [64, 67, 71, 69, 67, 0, 64, 62, 64, 67, 66, 0, 64, 67, 71, 74, 72, 71, 69, 0];
    let i = 0;
    const play = () => {
      const n = notes[i++ % notes.length]; if (!n) return;
      const f = 440 * Math.pow(2, (n - 69) / 12) * mrand(0.992, 1.006);
      this.tone({ f, dur: 1.6, gain: 0.07, type: 'triangle', dest: this.music, rev: 0.7 });
      this.tone({ f: f * 2.01, dur: 0.7, gain: 0.025, dest: this.music });
    };
    this._mel = setInterval(play, 560);
  },
  /* an ambient drone per level: two detuned saws and a fifth through a breathing low-pass, plus optional noise */
  stopBeds(fade = 1.2) {
    if (!this.ok) return; const t = this.ctx.currentTime;
    for (const b of this.beds) { try { b.g.gain.cancelScheduledValues(t); b.g.gain.setTargetAtTime(0.0001, t, fade / 3); b.nodes.forEach(n => { try { n.stop(t + fade + 0.3); } catch (e) { } }); } catch (e) { } }
    this.beds = [];
  },
  bed(spec) { // {root, fifth, cut, noise, noiseF, gain}
    if (!this.ok || !spec) return; this.stopBeds(1.5);
    const c = this.ctx, t = c.currentTime, nodes = [];
    const g = c.createGain(); g.gain.setValueAtTime(0.0001, t); g.gain.setTargetAtTime(spec.gain || 0.45, t + 0.2, 1.2); g.connect(this.bedBus);
    const lp = c.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = spec.cut || 220; lp.Q.value = 1.4; lp.connect(g);
    const lfo = c.createOscillator(); lfo.frequency.value = 0.07; const lg = c.createGain(); lg.gain.value = (spec.cut || 220) * 0.35; lfo.connect(lg); lg.connect(lp.frequency); lfo.start(); nodes.push(lfo);
    const root = spec.root || 55;
    [root, root * 1.006, root * (spec.fifth || 1.5)].forEach((f, i) => { const o = c.createOscillator(); o.type = i < 2 ? 'sawtooth' : 'triangle'; o.frequency.value = f; const og = c.createGain(); og.gain.value = i < 2 ? 0.16 : 0.08; o.connect(og); og.connect(lp); o.start(); nodes.push(o); });
    if (spec.noise) { const s = c.createBufferSource(); s.buffer = this.brownBuf; s.loop = true; const nf = c.createBiquadFilter(); nf.type = 'bandpass'; nf.frequency.value = spec.noiseF || 400; nf.Q.value = 0.6; const ng = c.createGain(); ng.gain.value = spec.noise; s.connect(nf); nf.connect(ng); ng.connect(g); s.start(); nodes.push(s); }
    this.beds.push({ g, nodes });
  }
};
const _au1 = new THREE.Vector3(), _au2 = new THREE.Vector3(), _au3 = new THREE.Vector3();
````

### `assets/starter/src/02_ink.js`

<!-- bundle-file: assets/starter/src/02_ink.js sha256=f8e6b156f842d0eda863db535cd530e811d60bfabfcb0f32a6d39bcd350e4f93 -->
````javascript
/* ===================== ink renderer: crosshatch shaders, boiling lines, portals, baked shadows, post =====================
   Everything is drawn by four materials sharing the uniforms in U: INK (faces, hatched by light), LINE (boiling
   edges), GLOW (the one colour, BLUE, for things that are real), SPILL (soft light pools). POST adds paper and mood. */
const _v3a = new THREE.Vector3(), _v3b = new THREE.Vector3(), _v3c = new THREE.Vector3();
const V3 = THREE.Vector3, Q4 = THREE.Quaternion, M4 = THREE.Matrix4;
const PAPER = new THREE.Color('#E4E0D5'), INK = new THREE.Color('#171511'), BLUE = new THREE.Color('#5C64FF');
// surface patterns drawn by INK_FS (the aPat vertex attribute). Pass { pat: PAT.BRICK } to L.B() and friends.
const PAT = { NONE: 0, BRICK: 1, BLOCKS: 2, CHECKER: 3, WOOD: 4, BOOKS: 5, DAMASK: 6, TILES: 7, HEDGE: 8, ASHLAR: 9, BOARDS: 10,
  GRASS: 11, MONSTER: 12, PAPER: 13, PLASTER: 14, CARPET: 15, DIAL: 16, ROCK: 17 };

// shared global uniforms (objects shared by reference between all ink materials)
const U = {
  uTime: { value: 0 }, uWarp: { value: 0 }, uBoil: { value: 0 }, uBoilRate: { value: 8 }, uHatch: { value: 9 },
  uPaper: { value: new V3(PAPER.r, PAPER.g, PAPER.b) }, uInk: { value: new V3(INK.r, INK.g, INK.b) },
  uSunDir: { value: new V3(0.4, 0.8, 0.3).normalize() }, uSun: { value: 0.8 }, uAmb: { value: 0.45 },
  uFogTone: { value: 1 }, uFogDen: { value: 0.02 }, uCamPos: { value: new V3() },
  uLampPos: { value: new V3() }, uLampDir: { value: new V3(0, 0, -1) }, uLamp: { value: 0 }, uLampRange: { value: 14 },
  uPL: { value: Array.from({ length: 8 }, () => new THREE.Vector4(0, -999, 0, 1)) }, uPLi: { value: new Array(8).fill(0) },
  uShadowMap: { value: null }, uShadowMat: { value: new M4() }, uShadowOn: { value: 0 }, uShadowTexel: { value: 1 / 2048 },
  uCalm: { value: 0 }, uLod: { value: 1 }, uUpW: { value: new V3(0, 1, 0) }, uPatScale: { value: 1 }
};
const GLSL_COMMON = `
float h21(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float h11(float p){ return fract(sin(p * 91.345 + 7.13) * 43758.5453); }
vec3 warpP(vec3 p){ return p + uWarp * 0.11 * vec3(sin(p.y*0.6+uTime*1.3+p.z*0.21), sin(p.z*0.5+uTime*1.1+p.x*0.33), sin(p.x*0.55+uTime*0.9+p.y*0.27)); }
`;
const INK_VS = `
attribute float aTone; attribute float aPat;
uniform float uTime; uniform float uWarp;
varying vec3 vWP; varying vec3 vN; varying float vTone; varying float vPat;
#include <clipping_planes_pars_vertex>
${GLSL_COMMON}
void main(){
  vec4 wp = modelMatrix * vec4(position, 1.0);
  wp.xyz = warpP(wp.xyz);
  vWP = wp.xyz;
  vN = normalize(mat3(modelMatrix) * normal);
  vTone = aTone; vPat = aPat;
  vec4 mvPosition = viewMatrix * wp;
  gl_Position = projectionMatrix * mvPosition;
  #include <clipping_planes_vertex>
}`;
const INK_FS = `
precision highp float;
#include <packing>
uniform float uTime, uWarp, uBoil, uBoilRate, uHatch, uSun, uAmb, uFogTone, uFogDen, uLamp, uLampRange, uShadowOn, uShadowTexel, uCalm, uLod;
uniform float uFade, uToneMul, uFlash, uInvert, uMinTone, uPatScale;
uniform vec3 uPaper, uInk, uSunDir, uCamPos, uLampPos, uLampDir, uUpW;
uniform vec4 uPL[8]; uniform float uPLi[8];
uniform sampler2D uShadowMap; uniform mat4 uShadowMat;
varying vec3 vWP; varying vec3 vN; varying float vTone; varying float vPat;
#include <clipping_planes_pars_fragment>
${GLSL_COMMON}
float vnoise(vec2 p){ vec2 i=floor(p), f=fract(p); vec2 u=f*f*(3.0-2.0*f);
  return mix(mix(h21(i),h21(i+vec2(1.0,0.0)),u.x), mix(h21(i+vec2(0.0,1.0)),h21(i+vec2(1.0,1.0)),u.x), u.y); }
float sat1(float x){ return clamp(x, 0.0, 1.0); }
float hline(vec2 p, vec2 dp, vec2 dir, float freq, float w, float ph){
  if(w <= 0.0005) return 0.0;
  vec2 perp = vec2(-dir.y, dir.x);
  float along = dot(p, perp) * freq;
  float x = dot(p, dir) * freq + ph + 0.05*sin(along*0.29 + ph*3.1) + 0.025*sin(along*1.17 + ph);
  float fw = (abs(dir.x)*dp.x + abs(dir.y)*dp.y) * freq + 1e-4;
  float d = abs(fract(x) - 0.5);
  float l = 1.0 - smoothstep(w - fw, w + fw, d);
  return mix(l, sat1(2.0*w), smoothstep(0.3, 0.75, fw));
}
float gridLine(float x, float fw, float w){
  float d = abs(fract(x + 0.5) - 0.5);
  float l = 1.0 - smoothstep(w - fw, w + fw, d);
  return mix(l, sat1(2.0*w), smoothstep(0.3, 0.7, fw));
}
float hatchInk(vec2 p, vec2 dp, float t, float freq, float ph, float a0){
  float c1 = clamp((0.97 - t) * 1.05, 0.0, 0.6);
  float c2 = clamp((0.47 - t) * 1.3, 0.0, 0.5);
  float c3 = clamp((0.26 - t) * 1.6, 0.0, 0.45);
  float c4 = clamp((0.13 - t) * 2.5, 0.0, 0.4);
  float ink = hline(p, dp, vec2(cos(a0), sin(a0)), freq, c1*0.5, ph);
  ink = max(ink, hline(p, dp, vec2(cos(a0 - 1.45), sin(a0 - 1.45)), freq * 1.07, c2*0.5, ph + 1.7));
  ink = max(ink, hline(p, dp, vec2(cos(a0 + 0.62), sin(a0 + 0.62)), freq * 1.16, c3*0.5, ph + 3.1));
  ink = max(ink, hline(p, dp, vec2(cos(a0 - 0.75), sin(a0 - 0.75)), freq * 1.3, c4*0.5, ph + 4.3));
  return max(ink, smoothstep(0.05, 0.015, t));
}
float shadowF(vec3 N){
  if(uShadowOn < 0.5) return 1.0;
  vec4 sc = uShadowMat * vec4(vWP + N * 0.06, 1.0);
  vec3 c = sc.xyz / sc.w * 0.5 + 0.5;
  if(c.x < 0.0 || c.x > 1.0 || c.y < 0.0 || c.y > 1.0 || c.z > 1.0) return 1.0;
  float s = 0.0; float b = 0.0015; float o = uShadowTexel;
  s += step(c.z - b, unpackRGBAToDepth(texture2D(uShadowMap, c.xy + vec2(-o, -o))));
  s += step(c.z - b, unpackRGBAToDepth(texture2D(uShadowMap, c.xy + vec2( o, -o))));
  s += step(c.z - b, unpackRGBAToDepth(texture2D(uShadowMap, c.xy + vec2(-o,  o))));
  s += step(c.z - b, unpackRGBAToDepth(texture2D(uShadowMap, c.xy + vec2( o,  o))));
  return s * 0.25;
}
void main(){
  #include <clipping_planes_fragment>
  vec3 N = normalize(vN);
  // dissolve: uFade 0..1 eats the surface away in noise (things appearing / vanishing)
  if(uFade > 0.001){
    float n = vnoise(vWP.xy * 3.1 + vWP.z * 1.7) * 0.6 + vnoise(vWP.zx * 9.0) * 0.4;
    if(n < uFade) discard;
  }
  vec3 an = abs(N);
  vec2 p; float a0;
  if(an.x > an.y && an.x > an.z) { p = vWP.zy; a0 = 1.05; } else if(an.y > an.z) { p = vWP.xz; a0 = 0.785; } else { p = vWP.xy; a0 = 0.5; }
  vec2 dp = fwidth(p);
  float pid = floor(vPat + 0.5);
  float tone = vTone * uToneMul;
  float pink = 0.0;
  vec2 p0 = p; vec2 dp0 = dp;
  // ---------- patterns ----------
  if(pid > 0.5){
    p = p * uPatScale; dp = dp * uPatScale;
    if(pid < 1.5){ // brick
      vec2 b = p / vec2(0.5, 0.25); float row = floor(b.y); b.x += mod(row, 2.0) * 0.5;
      pink = max(gridLine(b.y, dp.y / 0.25, 0.05), gridLine(b.x, dp.x / 0.5, 0.03)) * 0.9;
      tone *= 0.9 + 0.12 * h21(floor(b));
    } else if(pid < 2.5){ // tumbling blocks (rhombille)
      vec2 q = p / 0.42;
      vec2 s = vec2(1.0, 1.7320508);
      vec4 hC = floor(vec4(q, q - vec2(0.5, 0.8660254)) / s.xyxy) + 0.5;
      vec2 h1 = q - hC.xy * s; vec2 h2 = q - (hC.zw * s + vec2(0.5, 0.8660254));
      vec2 lc = dot(h1, h1) < dot(h2, h2) ? h1 : h2;
      float a = atan(lc.y, lc.x);
      float face = (a > 0.5236 && a < 2.618) ? 0.0 : ((a >= 2.618 || a < -1.5708) ? 1.0 : 2.0);
      tone *= face < 0.5 ? 1.0 : (face < 1.5 ? 0.5 : 0.2);
      float fwq = length(dp) / 0.42 + 1e-4;
      vec2 u1 = vec2(0.8660254, 0.5), u2 = vec2(-0.8660254, 0.5), u3 = vec2(0.0, -1.0);
      float sp = 9.0;
      if(dot(lc, u1) > 0.0) sp = min(sp, abs(lc.x * u1.y - lc.y * u1.x));
      if(dot(lc, u2) > 0.0) sp = min(sp, abs(lc.x * u2.y - lc.y * u2.x));
      if(dot(lc, u3) > 0.0) sp = min(sp, abs(lc.x * u3.y - lc.y * u3.x));
      float hd = max(abs(lc.x), dot(abs(lc), vec2(0.5, 0.8660254)));
      float e = min(sp, abs(hd - 0.5));
      pink = (1.0 - smoothstep(0.025 - fwq, 0.025 + fwq, e)) * (1.0 - smoothstep(0.35, 0.8, fwq));
    } else if(pid < 3.5){ // checker floor
      vec2 c = floor(p / 0.6);
      float ch = mod(c.x + c.y, 2.0);
      if(uInvert > 0.5) ch = 1.0 - ch;
      tone *= ch > 0.5 ? 0.38 : 1.0;
      pink = max(gridLine(p.x / 0.6, dp.x / 0.6, 0.015), gridLine(p.y / 0.6, dp.y / 0.6, 0.015)) * 0.8;
    } else if(pid < 4.5){ // wood planks
      float row = floor(p.y / 0.18);
      pink = gridLine(p.y / 0.18, dp.y / 0.18, 0.035) * 0.85;
      pink = max(pink, gridLine((p.x + h11(row) * 5.0) / 2.2, dp.x / 2.2, 0.006) * 0.8);
      tone *= 0.86 + 0.14 * h11(row * 3.7);
      pink = max(pink, hline(p, dp, vec2(0.0, 1.0), 26.0, 0.04 * h11(row), row) * 0.35);
    } else if(pid < 5.5){ // books
      float row = floor(p.y / 0.45);
      float sx = p.x / 0.075 + h11(row) * 13.0;
      float sid = floor(sx);
      float ht = 0.62 + 0.3 * h21(vec2(sid, row));
      float fy = fract(p.y / 0.45);
      tone *= (0.3 + 0.7 * h21(vec2(sid * 1.3, row + 2.0)));
      if(fy > ht) tone *= 0.15;
      pink = max(gridLine(p.y / 0.45, dp.y / 0.45, 0.05), gridLine(sx, dp.x / 0.075, 0.05) * step(fy, ht)) * 0.9;
      pink = max(pink, (1.0 - smoothstep(0.0, 0.02, abs(fy - ht * 0.8))) * 0.5 * step(0.5, h21(vec2(sid, row * 7.0))));
    } else if(pid < 6.5){ // damask wallpaper
      vec2 l = fract(p / 0.5) - 0.5; vec2 cl = floor(p / 0.5);
      float fq = length(dp) / 0.5 + 1e-4;
      float dmd = abs(abs(l.x) + abs(l.y) - 0.34);
      float ci = abs(length(l) - 0.09);
      float st = abs(l.x);
      pink = max(1.0 - smoothstep(0.012 - fq, 0.012 + fq, dmd), 1.0 - smoothstep(0.01 - fq, 0.01 + fq, ci)) * (1.0 - smoothstep(0.3, 0.7, fq));
      pink = max(pink, (1.0 - smoothstep(0.004, 0.004 + fq, st)) * 0.5 * (1.0 - smoothstep(0.3, 0.7, fq)));
      tone *= 0.93;
    } else if(pid < 7.5){ // small tiles
      pink = max(gridLine(p.x / 0.3, dp.x / 0.3, 0.02), gridLine(p.y / 0.3, dp.y / 0.3, 0.02)) * 0.75;
      tone *= 0.95 + 0.05 * h21(floor(p / 0.3));
    } else if(pid < 8.5){ // hedge
      float n = vnoise(p * 5.0) * 0.6 + vnoise(p * 13.0) * 0.4;
      tone *= 0.38 + 0.55 * n;
      pink = smoothstep(0.66, 0.74, 1.0 - n) * 0.7;
    } else if(pid < 9.5){ // ashlar stone
      vec2 b = p / vec2(1.2, 0.6); float row = floor(b.y); b.x += mod(row, 2.0) * 0.37;
      pink = max(gridLine(b.y, dp.y / 0.6, 0.025), gridLine(b.x, dp.x / 1.2, 0.012)) * 0.85;
      tone *= 0.88 + 0.12 * h21(floor(b)) - 0.08 * vnoise(p * 4.0);
    } else if(pid < 10.5){ // wainscot boards
      pink = gridLine(p.x / 0.24, dp.x / 0.24, 0.03) * 0.8;
      tone *= 0.8 + 0.08 * h11(floor(p.x / 0.24));
    } else if(pid < 11.5){ // grass / earth stipple
      tone *= 0.72 + 0.28 * vnoise(p * 0.7);
      vec2 cc = floor(p * 9.0); vec2 lc2 = fract(p * 9.0) - 0.5;
      float on = step(0.55, h21(cc));
      float fq = length(dp) * 9.0 + 1e-4;
      pink = on * (1.0 - smoothstep(0.07 - fq, 0.07 + fq, length(lc2 + (vec2(h21(cc + 3.0), h21(cc + 7.0)) - 0.5) * 0.5))) * (1.0 - smoothstep(0.3, 0.7, fq));
    } else if(pid < 12.5){ // monster ink: black with paper scribbles
      tone = 0.03;
      float bp = floor(uTime * 10.0);
      float sc = hline(p, dp, normalize(vec2(0.8, 0.6 + 0.3 * sin(bp))), 22.0, 0.05, bp * 1.7);
      sc = max(sc, hline(p, dp, normalize(vec2(-0.5, 0.86)), 15.0, 0.035, bp * 2.3));
      pink = -sc;
    } else if(pid < 13.5){ // plain paper (signs)
      tone = 1.25;
    } else if(pid < 14.5){ // plaster with cracks
      tone *= 0.9 + 0.1 * vnoise(p * 1.5);
      float cr = abs(vnoise(p * 1.1 + 3.0) - 0.5);
      pink = (1.0 - smoothstep(0.006, 0.006 + length(dp) * 1.1 + 0.004, cr)) * 0.55;
    } else if(pid < 15.5){ // carpet runner
      float e = abs(fract(p.x / 1.6) - 0.5);
      pink = (1.0 - smoothstep(0.42, 0.43, e)) * 0.0 + gridLine(p.x / 1.6 + 0.5, dp.x / 1.6, 0.012) * 0.8;
      tone *= 0.55 + 0.1 * vnoise(p * 8.0);
    } else if(pid < 16.5){ // clock face / dial ticks (radial in plane)
      float ang = atan(p.y, p.x); float r = length(p);
      tone = 0.95;
      pink = (1.0 - smoothstep(0.0, 0.02, abs(fract(ang / 0.5236 + 0.5) - 0.5) * r)) * step(0.8, fract(r));
    } else { // void rock
      tone *= 0.55 + 0.45 * vnoise(p * 1.7);
      pink = smoothstep(0.7, 0.75, vnoise(p * 3.0 + 9.0)) * 0.6;
    }
    p = p0; dp = dp0;
  }
  // ---------- lighting ----------
  float sh = shadowF(N);
  float hemi = uAmb * (0.72 + 0.28 * dot(N, uUpW));
  float sun = max(dot(N, uSunDir), 0.0) * uSun * sh;
  vec3 Ld = uLampPos - vWP; float dl = length(Ld) + 1e-4; vec3 Ln = Ld / dl;
  float att = sat1(1.0 - dl / uLampRange); att *= att;
  float cone = smoothstep(0.8, 0.95, dot(-Ln, uLampDir));
  float lamp = uLamp * att * (0.18 + 0.82 * cone) * (0.35 + 0.65 * max(dot(N, Ln), 0.0)) * 1.6;
  float pl = 0.0;
  for(int i = 0; i < 8; i++){
    vec3 d = uPL[i].xyz - vWP; float dd = length(d) + 1e-4;
    float a = sat1(1.0 - dd / uPL[i].w); a *= a;
    pl += uPLi[i] * a * (0.3 + 0.7 * max(dot(N, d / dd), 0.0));
  }
  float light = hemi + sun + lamp + pl;
  float t = max(tone * light, uMinTone);
  // fog
  float dist = length(vWP - uCamPos);
  float fd = dist * uFogDen;
  float fog = 1.0 - exp(-fd * fd);
  t = mix(t, uFogTone, fog);
  t = clamp(t, 0.0, 1.3);
  // ---------- hatching ----------
  float boil = uBoil * (1.0 - uCalm * 0.7);
  float bs = floor(uTime * uBoilRate) * step(0.002, boil);
  float ph = boil * h11(bs) * 6.2831;
  vec2 hp = p + boil * 0.025 * (vec2(h11(bs + 1.0), h11(bs + 2.0)) - 0.5);
  float px = max(max(min(dp.x, dp.y), length(dp) * 0.45), 1e-5) * uHatch;
  float l = clamp(log2(0.19 / px), 0.0, 3.5) * uLod;
  float lf = floor(l); float fr = l - lf;
  float f1 = uHatch * exp2(lf);
  float ink = hatchInk(hp, dp, t, f1, ph, a0);
  if(fr > 0.02){ ink = mix(ink, hatchInk(hp, dp, t, f1 * 2.0, ph, a0), fr); }
  if(pink < 0.0) ink = min(ink, 1.0 + pink * 0.9 * (1.0 - fog));
  else ink = max(ink, pink * (1.0 - fog) * smoothstep(0.02, 0.25, t + 0.2));
  vec3 col = mix(uPaper, uInk, ink);
  col = mix(col, uPaper * 1.06, uFlash);
  gl_FragColor = vec4(col, 1.0);
}`;
function makeInkMat(o = {}) {
  const u = Object.assign({}, U, {
    uFade: { value: o.fade || 0 }, uToneMul: { value: o.toneMul == null ? 1 : o.toneMul }, uFlash: { value: 0 },
    uInvert: { value: 0 }, uMinTone: { value: o.minTone || 0 }
  });
  const m = new THREE.ShaderMaterial({
    uniforms: u, vertexShader: INK_VS, fragmentShader: INK_FS, clipping: true,
    extensions: { derivatives: true }, side: o.side || THREE.FrontSide,
    polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1
  });
  return m;
}
const LINE_VS = `
attribute float aSeed;
uniform float uTime; uniform float uWarp; uniform float uBoil; uniform float uBoilRate; uniform float uCalm;
varying vec3 vWP;
#include <clipping_planes_pars_vertex>
${GLSL_COMMON}
void main(){
  vec4 wp = modelMatrix * vec4(position, 1.0);
  wp.xyz = warpP(wp.xyz);
  float b = uBoil * (1.0 - uCalm * 0.7);
  float st = floor(uTime * uBoilRate) * step(0.002, b);
  vec3 j = vec3(h11(aSeed * 12.99 + st * 7.23), h11(aSeed * 39.35 + st * 1.13), h11(aSeed * 73.16 + st * 5.22)) - 0.5;
  wp.xyz += j * (0.01 + b * 0.06);
  vWP = wp.xyz;
  vec4 mvPosition = viewMatrix * wp;
  gl_Position = projectionMatrix * mvPosition;
  #include <clipping_planes_vertex>
}`;
const LINE_FS = `
precision highp float;
uniform vec3 uInk; uniform vec3 uPaper; uniform vec3 uCamPos; uniform float uFogDen; uniform float uFogTone; uniform float uLineTone; uniform float uFade;
varying vec3 vWP;
#include <clipping_planes_pars_fragment>
void main(){
  #include <clipping_planes_fragment>
  if(uFade > 0.5) discard;
  float d = length(vWP - uCamPos); float fd = d * uFogDen; float f = 1.0 - exp(-fd * fd);
  vec3 c = mix(mix(uInk, uPaper, uLineTone), mix(uInk, uPaper, uFogTone), f);
  gl_FragColor = vec4(c, 1.0);
}`;
function makeLineMat(o = {}) {
  const u = Object.assign({}, U, { uLineTone: { value: o.tone || 0 }, uFade: { value: 0 } });
  return new THREE.ShaderMaterial({ uniforms: u, vertexShader: LINE_VS, fragmentShader: LINE_FS, clipping: true, depthWrite: false });
}
const GLOW_VS = `
uniform float uTime; uniform float uWarp;
varying vec3 vWP; varying vec3 vN;
#include <clipping_planes_pars_vertex>
${GLSL_COMMON}
void main(){
  vec4 wp = modelMatrix * vec4(position, 1.0);
  vWP = wp.xyz; vN = normalize(mat3(modelMatrix) * normal);
  vec4 mvPosition = viewMatrix * wp;
  gl_Position = projectionMatrix * mvPosition;
  #include <clipping_planes_vertex>
}`;
const GLOW_FS = `
precision highp float;
uniform vec3 uColor; uniform float uTime; uniform float uPulse; uniform vec3 uCamPos; uniform float uFogDen; uniform float uFogTone; uniform vec3 uInk; uniform vec3 uPaper; uniform float uFade; uniform float uAlpha; uniform float uFogMul;
varying vec3 vWP; varying vec3 vN;
#include <clipping_planes_pars_fragment>
void main(){
  #include <clipping_planes_fragment>
  if(uFade > 0.5) discard;
  vec3 V = normalize(uCamPos - vWP);
  float fr = pow(1.0 - clamp(abs(dot(normalize(vN), V)), 0.0, 1.0), 2.0);
  vec3 c = uColor * (0.9 + 0.25 * sin(uTime * 4.0) * uPulse) + vec3(0.35) * fr;
  float d = length(vWP - uCamPos); float fd = d * uFogDen * 0.6 * uFogMul; float f = 1.0 - exp(-fd * fd);
  c = mix(c, mix(uInk, uPaper, uFogTone), f);
  gl_FragColor = vec4(c, uAlpha);
}`;
function makeGlowMat(color = BLUE, o = {}) {
  const u = Object.assign({}, U, { uColor: { value: new V3(color.r, color.g, color.b) }, uPulse: { value: o.pulse == null ? 1 : o.pulse }, uFade: { value: 0 }, uAlpha: { value: o.alpha == null ? 1 : o.alpha }, uFogMul: { value: o.fog === false ? 0 : 1 } });
  return new THREE.ShaderMaterial({ uniforms: u, vertexShader: GLOW_VS, fragmentShader: GLOW_FS, clipping: true, transparent: !!o.alpha, depthWrite: !o.alpha, side: o.side || THREE.FrontSide, blending: o.add ? THREE.AdditiveBlending : THREE.NormalBlending });
}
// soft light pool spilling from under a real door (alpha falls off away from the door and to the sides)
const SPILL_VS = `
uniform float uTime; uniform float uWarp;
varying vec2 vUv;
#include <clipping_planes_pars_vertex>
${GLSL_COMMON}
void main(){
  vUv = uv;
  vec4 wp = modelMatrix * vec4(position, 1.0);
  wp.xyz = warpP(wp.xyz);
  vec4 mvPosition = viewMatrix * wp;
  gl_Position = projectionMatrix * mvPosition;
  #include <clipping_planes_vertex>
}`;
const SPILL_FS = `
precision highp float;
uniform vec3 uColor; uniform float uTime; uniform float uA; uniform float uRadial;
varying vec2 vUv;
#include <clipping_planes_pars_fragment>
void main(){
  #include <clipping_planes_fragment>
  float fx = 1.0 - smoothstep(0.1, 0.5, abs(vUv.x - 0.5));
  float fz = pow(1.0 - vUv.y, 1.7);
  float fr = pow(1.0 - clamp(length(vUv - 0.5) * 2.0, 0.0, 1.0), 2.2);
  float a = uA * mix(fx * fz, fr, uRadial) * (0.78 + 0.22 * sin(uTime * 1.7));
  if(a < 0.004) discard;
  gl_FragColor = vec4(uColor, a);
}`;
function makeSpillMat(color = BLUE, a = 0.5, radial = 0) {
  const u = Object.assign({}, U, { uColor: { value: new V3(color.r, color.g, color.b) }, uA: { value: a }, uRadial: { value: radial } });
  return new THREE.ShaderMaterial({ uniforms: u, vertexShader: SPILL_VS, fragmentShader: SPILL_FS, clipping: true, transparent: true, depthWrite: false });
}
const PORTAL_FS = `
precision highp float; uniform sampler2D tPortal; uniform vec2 uRes;
void main(){ gl_FragColor = texture2D(tPortal, gl_FragCoord.xy / uRes); }`;
const PORTAL_VS = `void main(){ gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`;

/* ---------- post (final) pass ---------- */
const POST_FS = `
precision highp float;
uniform sampler2D tScene; uniform vec2 uRes; uniform float uTime;
uniform float uDouble, uSwirl, uWave, uTendril, uTunnel, uInvert, uFlash, uFlashTone, uFade, uGrain, uWarm, uRed, uCalm, uChrom;
uniform vec3 uPaper, uInk;
varying vec2 vUv;
float h21(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vn(vec2 p){ vec2 i=floor(p), f=fract(p); vec2 u=f*f*(3.0-2.0*f); return mix(mix(h21(i),h21(i+vec2(1.,0.)),u.x), mix(h21(i+vec2(0.,1.)),h21(i+vec2(1.,1.)),u.x), u.y); }
void main(){
  vec2 uv = vUv;
  vec2 c = uv - 0.5; c.x *= uRes.x / uRes.y;
  float r = length(c);
  float sw = uSwirl * (1.0 - uCalm);
  if(sw > 0.001){ float a = sw * sin(uTime * 0.6) * smoothstep(0.75, 0.0, r); float ca = cos(a), sa = sin(a); vec2 cc = uv - 0.5; uv = 0.5 + vec2(ca * cc.x - sa * cc.y, sa * cc.x + ca * cc.y); }
  float wv = uWave * (1.0 - uCalm);
  if(wv > 0.001) uv += wv * vec2(sin(uv.y * 13.0 + uTime * 2.1), cos(uv.x * 11.0 + uTime * 1.7)) * 0.0045;
  vec3 col = texture2D(tScene, uv).rgb;
  if(uChrom > 0.001){ col.r = texture2D(tScene, uv + vec2(uChrom * 0.004, 0.0)).r; col.b = texture2D(tScene, uv - vec2(uChrom * 0.004, 0.0)).b; }
  if(uDouble > 0.001){
    vec2 o = vec2(sin(uTime * 0.83), cos(uTime * 0.61)) * 0.011 * uDouble * (1.0 - uCalm * 0.7);
    vec3 c2 = texture2D(tScene, uv + o).rgb;
    col = mix(col, min(col, c2), 0.75 * clamp(uDouble, 0.0, 1.0));
  }
  // paper grain & fibres
  vec2 gp = gl_FragCoord.xy;
  float g = h21(floor(gp * 0.5)) * 0.5 + vn(gp * 0.035) * 0.35 + vn(gp * vec2(0.004, 0.02)) * 0.15;
  col *= 1.0 - uGrain * (g - 0.5) * 0.16;
  // ink tendrils / vignette
  float n = vn(uv * 5.0 + vec2(uTime * 0.05, -uTime * 0.04)) * 0.65 + vn(uv * 17.0 - uTime * 0.1) * 0.35;
  float edge = r * (1.0 + uTunnel * 0.9) + (n - 0.5) * 0.35 * uTendril;
  float v = smoothstep(0.98 - uTendril * 0.32, 0.58 - uTendril * 0.3, edge);
  col = mix(uInk, col, mix(1.0, v, clamp(0.35 + uTendril, 0.0, 1.0)));
  if(uRed > 0.001) col = mix(col, col * vec3(1.25, 0.7, 0.62), uRed);
  if(uWarm > 0.001){
    float lum = dot(col, vec3(0.333));
    vec3 warm = mix(vec3(0.16, 0.07, 0.04), vec3(1.0, 0.72, 0.42), lum);
    col = mix(col, warm, uWarm);
  }
  col = mix(col, uPaper + uInk - col, uInvert);
  col = mix(col, mix(uInk, uPaper * 1.05, uFlashTone), uFlash);
  col = mix(col, uInk * 0.5, uFade);
  gl_FragColor = vec4(col, 1.0);
}`;
const POST = {
  tScene: { value: null }, uRes: { value: new THREE.Vector2(1, 1) }, uTime: U.uTime,
  uDouble: { value: 0 }, uSwirl: { value: 0 }, uWave: { value: 0 }, uTendril: { value: 0 }, uTunnel: { value: 0 }, uInvert: { value: 0 },
  uFlash: { value: 0 }, uFlashTone: { value: 1 }, uFade: { value: 1 }, uGrain: { value: 1 }, uWarm: { value: 0 },
  uRed: { value: 0 }, uCalm: U.uCalm, uChrom: { value: 0 },
  uPaper: U.uPaper, uInk: U.uInk
};

const R = {
  renderer: null, mainRT: null, portalRT: null, w: 1, h: 1, pr: 1, q: null,
  pcam: new THREE.PerspectiveCamera(70, 1, 0.05, 900),
  init(canvas) {
    let r;
    try { r = new THREE.WebGLRenderer({ canvas, antialias: false, alpha: false, stencil: false, powerPreference: 'high-performance', preserveDrawingBuffer: false }); }
    catch (e) { throw new Error('WebGL is not available on this device/browser.'); }
    r.autoClear = false; r.outputEncoding = THREE.LinearEncoding; r.sortObjects = true;
    this.renderer = r; this.isGL2 = r.capabilities.isWebGL2;
    this.postCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
    this.postMat = new THREE.ShaderMaterial({ uniforms: POST, vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }', fragmentShader: POST_FS, depthTest: false, depthWrite: false });
    this.postScene = new THREE.Scene();
    const tri = new THREE.BufferGeometry(); tri.setAttribute('position', new THREE.Float32BufferAttribute([-1, -1, 0, 3, -1, 0, -1, 3, 0], 3)); tri.setAttribute('uv', new THREE.Float32BufferAttribute([0, 0, 2, 0, 0, 2], 2));
    const quad = new THREE.Mesh(tri, this.postMat); quad.frustumCulled = false; this.postScene.add(quad);
    this.depthMat = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking });
    this.shadowCam = new THREE.OrthographicCamera(-10, 10, 10, -10, 0.1, 100); this.shadowCam.layers.set(1);
    this.portalUniforms = { tPortal: { value: null }, uRes: POST.uRes };
    this.applyQuality();
  },
  qualityPreset() {
    const dpr = window.devicePixelRatio || 1;
    const q = SET.quality;
    if (q === 0) return { pr: Math.min(dpr, 1.5) * (IS_TOUCH ? 0.62 : 0.75), samples: 0, shadow: 1024, lod: 0, portalScale: 0.6 };
    if (q === 1) return { pr: Math.min(dpr, IS_TOUCH ? 1.25 : 1.5), samples: this.isGL2 ? 2 : 0, shadow: 2048, lod: 1, portalScale: 1 };
    return { pr: Math.min(dpr, 2), samples: this.isGL2 ? 4 : 0, shadow: 2048, lod: 1, portalScale: 1 };
  },
  applyQuality() {
    this.q = this.qualityPreset(); U.uLod.value = 1; this.resize(true);
  },
  resize(force) {
    const w = window.innerWidth, h = window.innerHeight;
    if (!force && w === this.cw && h === this.ch) return;
    this.cw = w; this.ch = h;
    const pr = this.q.pr; this.renderer.setPixelRatio(pr); this.renderer.setSize(w, h, false);
    const W = Math.max(2, Math.floor(w * pr)), H = Math.max(2, Math.floor(h * pr));
    this.w = W; this.h = H; POST.uRes.value.set(W, H);
    if (this.mainRT) this.mainRT.dispose(); if (this.portalRT) this.portalRT.dispose();
    const opt = { minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter, depthBuffer: true, stencilBuffer: false };
    this.mainRT = new THREE.WebGLRenderTarget(W, H, opt); if (this.q.samples) this.mainRT.samples = this.q.samples;
    const ps = this.q.portalScale;
    this.portalRT = new THREE.WebGLRenderTarget(Math.max(2, Math.floor(W * ps)), Math.max(2, Math.floor(H * ps)), opt); if (this.q.samples) this.portalRT.samples = this.q.samples;
    POST.tScene.value = this.mainRT.texture; this.portalUniforms.tPortal.value = this.portalRT.texture;
    if (window.CAM) { CAM.aspect = w / h; CAM.updateProjectionMatrix(); }
  },
  bakeShadow(level) {
    const env = level.env; if (!env.sun || env.noShadow) { level.shadowRT = null; return; }
    const size = this.q.shadow;
    const rt = new THREE.WebGLRenderTarget(size, size, { minFilter: THREE.NearestFilter, magFilter: THREE.NearestFilter, depthBuffer: true, stencilBuffer: false });
    const bb = level.bounds; const c = bb.getCenter(new V3()); const rad = bb.getSize(new V3()).length() * 0.5 + 2;
    const cam = this.shadowCam; const sd = env.sunDir.clone().normalize();
    cam.position.copy(c).addScaledVector(sd, rad + 10); cam.up.set(Math.abs(sd.y) > 0.95 ? 1 : 0, Math.abs(sd.y) > 0.95 ? 0 : 1, 0); cam.lookAt(c);
    cam.updateMatrixWorld();
    // fit to bounds in light space
    const inv = cam.matrixWorldInverse; const pts = [];
    for (let i = 0; i < 8; i++) pts.push(new V3(i & 1 ? bb.max.x : bb.min.x, i & 2 ? bb.max.y : bb.min.y, i & 4 ? bb.max.z : bb.min.z).applyMatrix4(inv));
    let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9, z0 = 1e9, z1 = -1e9;
    for (const p of pts) { x0 = Math.min(x0, p.x); x1 = Math.max(x1, p.x); y0 = Math.min(y0, p.y); y1 = Math.max(y1, p.y); z0 = Math.min(z0, p.z); z1 = Math.max(z1, p.z); }
    cam.left = x0 - 1; cam.right = x1 + 1; cam.bottom = y0 - 1; cam.top = y1 + 1; cam.near = Math.max(0.1, -z1 - 2); cam.far = -z0 + 2;
    cam.updateProjectionMatrix();
    const r = this.renderer; const ov = level.scene.overrideMaterial; level.scene.overrideMaterial = this.depthMat;
    const oldClear = r.getClearColor(new THREE.Color()), oldA = r.getClearAlpha();
    r.setRenderTarget(rt); r.setClearColor(0xffffff, 1); r.clear(); r.render(level.scene, cam);
    r.setRenderTarget(null); r.setClearColor(oldClear, oldA);
    level.scene.overrideMaterial = ov;
    level.shadowRT = rt; level.shadowMat = new M4().multiplyMatrices(cam.projectionMatrix, cam.matrixWorldInverse); level.shadowTexel = 1 / size;
  },
  applyEnv(level, M) { // M: optional matrix mapping current coords → this level coords (for the lamp)
    const e = level.env;
    U.uSunDir.value.copy(e.sunDir).normalize(); U.uSun.value = e.sun; U.uAmb.value = e.amb * (e.ambMul == null ? 1 : e.ambMul);
    U.uFogTone.value = e.fogTone; U.uFogDen.value = e.fogDen * (e.fogMul == null ? 1 : e.fogMul); U.uHatch.value = e.hatch || 9;
    U.uUpW.value.copy(e.upW || _up0); U.uPatScale.value = e.patScale || 1;
    if (level.shadowRT) { U.uShadowMap.value = level.shadowRT.texture; U.uShadowMat.value.copy(level.shadowMat); U.uShadowOn.value = 1; U.uShadowTexel.value = level.shadowTexel; }
    else { U.uShadowOn.value = 0; U.uShadowMap.value = null; }
    const L = level.plights;
    for (let i = 0; i < 8; i++) {
      const pl = L[i];
      if (pl && pl.i > 0.001) { U.uPL.value[i].set(pl.pos.x, pl.pos.y, pl.pos.z, pl.r); U.uPLi.value[i] = pl.i * (pl.flick == null ? 1 : pl.flick); }
      else { U.uPL.value[i].set(0, -9999, 0, 1); U.uPLi.value[i] = 0; }
    }
    U.uLampPos.value.copy(PL.lampPos); U.uLampDir.value.copy(PL.lampDir);
    if (M) { U.uLampPos.value.applyMatrix4(M); U.uLampDir.value.transformDirection(M); }
    U.uLamp.value = PL.lampI * (e.lampMul == null ? 1 : e.lampMul); U.uLampRange.value = PL.lampRange;
  },
  clearColor(env) { const t = env.bgTone == null ? env.fogTone : env.bgTone; return _cc.copy(INK).lerp(PAPER, t); },
  render(level, cam, portal) {
    const r = this.renderer;
    // ---- portal pass ----
    if (portal) {
      const tl = portal.level;
      this.pcam.projectionMatrix.copy(cam.projectionMatrix); this.pcam.projectionMatrixInverse.copy(cam.projectionMatrixInverse);
      _m4a.multiplyMatrices(portal.M, cam.matrixWorld);
      _m4a.decompose(this.pcam.position, this.pcam.quaternion, this.pcam.scale);
      this.pcam.updateMatrixWorld(true);
      this.applyEnv(tl, portal.M);
      U.uCamPos.value.copy(this.pcam.position);
      r.clippingPlanes = [portal.plane];
      const hidden = [];
      for (const d of tl.doors) { if (d.aperture && d.aperture.visible !== false) { d.aperture.visible = false; hidden.push(d.aperture); } }
      if (!tl._apScan || tl._apScan !== tl.scene.children.length) { tl._apScan = tl.scene.children.length; tl._aps = tl.scene.children.filter(o => o.material === MAT.portal); }
      for (const o of tl._aps) if (o.visible !== false) { o.visible = false; hidden.push(o); }
      if (portal.hideLeaf) { hidden.push(portal.hideLeaf); portal.hideLeaf.visible = false; }
      for (const o of (tl.portalHide || [])) if (o.visible) { o.visible = false; hidden.push(o); }
      r.setRenderTarget(this.portalRT); r.setClearColor(this.clearColor(tl.env), 1); r.clear(); r.render(tl.scene, this.pcam);
      for (const o of hidden) o.visible = true;
      r.clippingPlanes = [];
    }
    // ---- main pass ----
    this.applyEnv(level, null);
    U.uCamPos.value.copy(cam.position);
    r.setRenderTarget(this.mainRT); r.setClearColor(this.clearColor(level.env), 1); r.clear(); r.render(level.scene, cam);
    // ---- post ----
    r.setRenderTarget(null); r.clear(); r.render(this.postScene, this.postCam);
  }
};
const _cc = new THREE.Color(), _m4a = new M4(), _m4b = new M4(), _up0 = new V3(0, 1, 0);
````

### `assets/starter/src/03_world.js`

<!-- bundle-file: assets/starter/src/03_world.js sha256=37169f89c9182e619eb8d0a9904000923103ba705dfcc46008914620fa592c11 -->
````javascript
/* ===================== world: geometry, colliders, levels, doors, pickups, build helpers =====================
   Levels are built from boxes. GeoAcc merges every box of a level into one mesh plus one set of boiling edge
   lines (two draw calls), and every solid box is also an axis-aligned collider in a spatial hash. */
let MAT = null;
function initMats() {
  MAT = {
    ink: makeInkMat(), inkDouble: makeInkMat({ side: THREE.DoubleSide }), line: makeLineMat(), lineW: makeLineMat({ tone: 1 }),
    glow: makeGlowMat(BLUE), glowWhite: makeGlowMat(new THREE.Color(1.0, 0.98, 0.9), { pulse: 0.3 }), glowWarm: makeGlowMat(new THREE.Color(1.0, 0.85, 0.55), { pulse: 0.5 }),
    portal: new THREE.ShaderMaterial({ uniforms: R.portalUniforms, vertexShader: PORTAL_VS, fragmentShader: PORTAL_FS, side: THREE.DoubleSide })
  };
}
const FACE_DEF = [ // n, u, v
  [[1, 0, 0], [0, 0, -1], [0, 1, 0]], [[-1, 0, 0], [0, 0, 1], [0, 1, 0]],
  [[0, 1, 0], [1, 0, 0], [0, 0, -1]], [[0, -1, 0], [1, 0, 0], [0, 0, 1]],
  [[0, 0, 1], [1, 0, 0], [0, 1, 0]], [[0, 0, -1], [-1, 0, 0], [0, 1, 0]]
];
const _bv = new V3(), _bn = new V3(), _nm3 = new THREE.Matrix3();
class GeoAcc {
  constructor() { this.P = []; this.N = []; this.T = []; this.A = []; this.I = []; this.L = []; this.S = []; this.vc = 0; }
  vert(x, y, z, nx, ny, nz, tone, pat) { this.P.push(x, y, z); this.N.push(nx, ny, nz); this.T.push(tone); this.A.push(pat); return this.vc++; }
  line(a, b, os = 0.04) {
    const dx = b.x - a.x, dy = b.y - a.y, dz = b.z - a.z, l = Math.sqrt(dx * dx + dy * dy + dz * dz) || 1;
    const e = Math.min(os, l * 0.08) / l;
    this.L.push(a.x - dx * e, a.y - dy * e, a.z - dz * e, b.x + dx * e, b.y + dy * e, b.z + dz * e);
    this.S.push(Math.random() * 100, Math.random() * 100);
  }
  // oriented box: m (Matrix4 or null), centre at local origin, half sizes hx,hy,hz
  boxM(m, hx, hy, hz, tone, pat, edges = true, faces = 63) {
    const hs = [hx, hy, hz];
    if (m) _nm3.getNormalMatrix(m);
    for (let f = 0; f < 6; f++) {
      if (!(faces & (1 << f))) continue;
      const [n, u, v] = FACE_DEF[f];
      const ax = n[0] ? 0 : n[1] ? 1 : 2, uax = u[0] ? 0 : u[1] ? 1 : 2, vax = v[0] ? 0 : v[1] ? 1 : 2;
      const cn = [n[0] * hs[ax], n[1] * hs[ax], n[2] * hs[ax]];
      const us = hs[uax], vs = hs[vax];
      _bn.set(n[0], n[1], n[2]); if (m) _bn.applyMatrix3(_nm3).normalize();
      const base = this.vc;
      for (const [su, sv] of [[-1, -1], [1, -1], [1, 1], [-1, 1]]) {
        _bv.set(cn[0] + u[0] * us * su + v[0] * vs * sv, cn[1] + u[1] * us * su + v[1] * vs * sv, cn[2] + u[2] * us * su + v[2] * vs * sv);
        if (m) _bv.applyMatrix4(m);
        this.vert(_bv.x, _bv.y, _bv.z, _bn.x, _bn.y, _bn.z, tone, pat);
      }
      this.I.push(base, base + 1, base + 2, base, base + 2, base + 3);
    }
    if (edges) {
      const c = []; for (let i = 0; i < 8; i++) { const p = new V3(i & 1 ? hx : -hx, i & 2 ? hy : -hy, i & 4 ? hz : -hz); if (m) p.applyMatrix4(m); c.push(p); }
      const E = [[0, 1], [2, 3], [4, 5], [6, 7], [0, 2], [1, 3], [4, 6], [5, 7], [0, 4], [1, 5], [2, 6], [3, 7]];
      for (const [a, b] of E) this.line(c[a], c[b]);
    }
  }
  box(x0, y0, z0, x1, y1, z1, tone, pat, edges = true, faces = 63) {
    _m4b.makeTranslation((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2);
    this.boxM(_m4b, Math.abs(x1 - x0) / 2, Math.abs(y1 - y0) / 2, Math.abs(z1 - z0) / 2, tone, pat, edges, faces);
  }
  geo(g, m, tone, pat, edgeAngle = 35) { // import a THREE geometry
    const gg = g.index ? g.toNonIndexed() : g;
    const p = gg.attributes.position, n = gg.attributes.normal; if (m) _nm3.getNormalMatrix(m);
    for (let i = 0; i < p.count; i++) {
      _bv.set(p.getX(i), p.getY(i), p.getZ(i)); if (m) _bv.applyMatrix4(m);
      _bn.set(n.getX(i), n.getY(i), n.getZ(i)); if (m) _bn.applyMatrix3(_nm3).normalize();
      const k = this.vert(_bv.x, _bv.y, _bv.z, _bn.x, _bn.y, _bn.z, tone, pat); this.I.push(k);
    }
    if (edgeAngle) {
      const eg = new THREE.EdgesGeometry(g, edgeAngle); const ep = eg.attributes.position;
      for (let i = 0; i < ep.count; i += 2) { const a = new V3(ep.getX(i), ep.getY(i), ep.getZ(i)), b = new V3(ep.getX(i + 1), ep.getY(i + 1), ep.getZ(i + 1)); if (m) { a.applyMatrix4(m); b.applyMatrix4(m); } this.line(a, b, 0.02); }
      eg.dispose();
    }
    if (gg !== g) gg.dispose();
  }
  cyl(x, y, z, r, h, seg, tone, pat, edges = true, m = null) {
    const g = new THREE.CylinderGeometry(r, r, h, seg, 1, false);
    const mm = new M4().makeTranslation(x, y + h / 2, z); if (m) mm.premultiply(m);
    this.geo(g, mm, tone, pat, edges ? 30 : 0); g.dispose();
  }
  empty() { return this.vc === 0 && this.L.length === 0; }
  build() {
    let mesh = null, lines = null;
    if (this.vc) {
      const g = new THREE.BufferGeometry();
      g.setAttribute('position', new THREE.Float32BufferAttribute(this.P, 3));
      g.setAttribute('normal', new THREE.Float32BufferAttribute(this.N, 3));
      g.setAttribute('aTone', new THREE.Float32BufferAttribute(this.T, 1));
      g.setAttribute('aPat', new THREE.Float32BufferAttribute(this.A, 1));
      g.setIndex(this.vc > 65535 ? new THREE.Uint32BufferAttribute(this.I, 1) : new THREE.Uint16BufferAttribute(this.I, 1));
      g.computeBoundingSphere(); g.computeBoundingBox(); mesh = g;
    }
    if (this.L.length) {
      const lg = new THREE.BufferGeometry();
      lg.setAttribute('position', new THREE.Float32BufferAttribute(this.L, 3));
      lg.setAttribute('aSeed', new THREE.Float32BufferAttribute(this.S, 1));
      lg.computeBoundingSphere(); lines = lg;
    }
    return { mesh, lines };
  }
}
// build a standalone object (dynamic) from an accumulator callback
function buildObj(fn, o = {}) {
  const a = new GeoAcc(); fn(a); const b = a.build(); const grp = new THREE.Group();
  if (b.mesh) { const m = new THREE.Mesh(b.mesh, o.mat || MAT.ink); m.renderOrder = 1; grp.add(m); grp.userData.mesh = m; }
  if (b.lines && !o.noLines) { const l = new THREE.LineSegments(b.lines, o.lineMat || MAT.line); l.renderOrder = 2; grp.add(l); grp.userData.lines = l; }
  return grp;
}

/* ---------- spatial hash of AABB colliders ---------- */
class SHash {
  constructor(c = 4) { this.c = c; this.m = new Map(); this.st = 1; }
  k(x, y, z) { return ((x + 600) * 1300 + (y + 600)) * 1300 + (z + 600); }
  insert(col) {
    const c = this.c;
    for (let x = Math.floor(col.min[0] / c); x <= Math.floor(col.max[0] / c); x++)
      for (let y = Math.floor(col.min[1] / c); y <= Math.floor(col.max[1] / c); y++)
        for (let z = Math.floor(col.min[2] / c); z <= Math.floor(col.max[2] / c); z++) {
          const k = this.k(x, y, z); let a = this.m.get(k); if (!a) { a = []; this.m.set(k, a); } a.push(col);
        }
  }
  query(mn, mx, out) {
    const c = this.c; this.st++;
    for (let x = Math.floor(mn[0] / c); x <= Math.floor(mx[0] / c); x++)
      for (let y = Math.floor(mn[1] / c); y <= Math.floor(mx[1] / c); y++)
        for (let z = Math.floor(mn[2] / c); z <= Math.floor(mx[2] / c); z++) {
          const a = this.m.get(this.k(x, y, z)); if (!a) continue;
          for (const col of a) if (col._s !== this.st) { col._s = this.st; if (col.on) out.push(col); }
        }
    return out;
  }
  ray(o, d, maxT) { // returns nearest t or Infinity
    const c = this.c; let x = Math.floor(o.x / c), y = Math.floor(o.y / c), z = Math.floor(o.z / c);
    const sx = d.x > 0 ? 1 : -1, sy = d.y > 0 ? 1 : -1, sz = d.z > 0 ? 1 : -1;
    const tdx = d.x !== 0 ? Math.abs(c / d.x) : Infinity, tdy = d.y !== 0 ? Math.abs(c / d.y) : Infinity, tdz = d.z !== 0 ? Math.abs(c / d.z) : Infinity;
    let tmx = d.x !== 0 ? ((x + (sx > 0 ? 1 : 0)) * c - o.x) / d.x : Infinity;
    let tmy = d.y !== 0 ? ((y + (sy > 0 ? 1 : 0)) * c - o.y) / d.y : Infinity;
    let tmz = d.z !== 0 ? ((z + (sz > 0 ? 1 : 0)) * c - o.z) / d.z : Infinity;
    this.st++; let best = Infinity, t = 0, guard = 0;
    while (t <= maxT && guard++ < 400) {
      const a = this.m.get(this.k(x, y, z));
      if (a) for (const col of a) {
        if (col._s === this.st || !col.on || col.noRay) continue; col._s = this.st;
        const h = rayBox(o, d, col.min, col.max); if (h < best) best = h;
      }
      const tn = Math.min(tmx, tmy, tmz);
      if (best <= tn) break;
      t = tn;
      if (tmx <= tmy && tmx <= tmz) { x += sx; tmx += tdx; } else if (tmy <= tmz) { y += sy; tmy += tdy; } else { z += sz; tmz += tdz; }
    }
    return best <= maxT ? best : Infinity;
  }
}
function rayBox(o, d, mn, mx) {
  let t0 = -Infinity, t1 = Infinity;
  for (let i = 0; i < 3; i++) {
    const oi = i === 0 ? o.x : i === 1 ? o.y : o.z, di = i === 0 ? d.x : i === 1 ? d.y : d.z;
    if (Math.abs(di) < 1e-9) { if (oi < mn[i] || oi > mx[i]) return Infinity; continue; }
    let a = (mn[i] - oi) / di, b = (mx[i] - oi) / di; if (a > b) { const t = a; a = b; b = t; }
    if (a > t0) t0 = a; if (b < t1) t1 = b; if (t0 > t1) return Infinity;
  }
  if (t1 < 0) return Infinity;
  return t0 >= 0 ? t0 : 0;
}

/* ---------- Level ---------- */
// env: sun direction and strength, ambient, fog (tone 1 = paper, 0 = ink), hatch density, ambient sound bed, mood (post effects)
const ENV_DEF = () => ({ sunDir: new V3(-0.45, 0.8, 0.35), sun: 0.75, amb: 0.48, fogTone: 1, fogDen: 0.012, hatch: 9, bgTone: null, lampMul: 1, upW: new V3(0, 1, 0),
  bed: { root: 55, fifth: 1.5, cut: 240, noise: 0.04, gain: 0.4 }, mood: { boil: 0.08, warp: 0, double: 0, wave: 0, swirl: 0, tendril: 0.15, chrom: 0 } });
class Level {
  constructor(idx, name) {
    this.idx = idx; this.name = name; this.scene = new THREE.Scene(); this.scene.matrixAutoUpdate = false;
    this.acc = { main: new GeoAcc() }; this.cur = 'main'; this.chunkObjs = {};
    this.cols = []; this.hash = new SHash(4); this.ents = []; this.doors = []; this.plights = []; this.dyn = [];
    this.triggers = []; this.pickups = []; this.inter = []; this.gravZones = [];
    this.bounds = new THREE.Box3(); this.env = ENV_DEF(); this.killU = -30; this.t = 0;
    this.portalHide = []; this.surf = 'stone';
    this.data = {};
  }
  get a() { return this.acc[this.cur]; }
  chunk(n) { if (!this.acc[n]) this.acc[n] = new GeoAcc(); this.cur = n; return this; }
  addCol(x0, y0, z0, x1, y1, z1, o = {}) {
    const c = { min: [Math.min(x0, x1), Math.min(y0, y1), Math.min(z0, z1)], max: [Math.max(x0, x1), Math.max(y0, y1), Math.max(z0, z1)], on: true, surf: o.surf || this.surf, chunk: this.cur, hazard: o.hazard || 0, noRay: !!o.noRay, tag: o.tag, _s: 0 };
    this.cols.push(c); return c;
  }
  // box by corners. o: tone, pat, solid(true), surf, edges, faces
  B(x0, y0, z0, x1, y1, z1, o = {}) {
    if (o.vis !== false) this.a.box(x0, y0, z0, x1, y1, z1, o.tone == null ? 0.85 : o.tone, o.pat || 0, o.edges !== false, o.faces == null ? 63 : o.faces);
    if (o.solid !== false) return this.addCol(x0, y0, z0, x1, y1, z1, o);
    return null;
  }
  // oriented decor box (non-colliding unless o.solid and axis-aligned)
  BM(m, hx, hy, hz, o = {}) { this.a.boxM(m, hx, hy, hz, o.tone == null ? 0.85 : o.tone, o.pat || 0, o.edges !== false); }
  cyl(x, y, z, r, h, o = {}) {
    this.a.cyl(x, y, z, r, h, o.seg || 10, o.tone == null ? 0.85 : o.tone, o.pat || 0, o.edges !== false, o.m || null);
    if (o.solid !== false && !o.m) this.addCol(x - r * 0.85, y, z - r * 0.85, x + r * 0.85, y + h, z + r * 0.85, o);
  }
  light(x, y, z, r, i, o = {}) { const pl = { pos: new V3(x, y, z), r, i, base: i, flick: 1, flicker: o.flicker || 0, phase: Math.random() * 10, on: true, kind: o.kind }; this.plights.push(pl); return pl; }
  add(obj) { this.scene.add(obj); return obj; }
  ent(e) { this.ents.push(e); return e; }
  trigger(x0, y0, z0, x1, y1, z1, fn, o = {}) { const t = { min: [Math.min(x0, x1), Math.min(y0, y1), Math.min(z0, z1)], max: [Math.max(x0, x1), Math.max(y0, y1), Math.max(z0, z1)], fn, once: o.once !== false, done: false, inside: false, exit: o.exit }; this.triggers.push(t); return t; }
  finalize() {
    for (const n in this.acc) {
      const b = this.acc[n].build(); const grp = new THREE.Group(); grp.name = 'chunk_' + n;
      if (b.mesh) { const m = new THREE.Mesh(b.mesh, MAT.ink); m.layers.enable(1); m.renderOrder = 1; grp.add(m); this.bounds.union(b.mesh.boundingBox); }
      if (b.lines) { const l = new THREE.LineSegments(b.lines, MAT.line); l.renderOrder = 2; grp.add(l); }
      this.scene.add(grp); this.chunkObjs[n] = grp;
    }
    for (const c of this.cols) this.hash.insert(c);
    if (this.bounds.isEmpty()) this.bounds.set(new V3(-10, -10, -10), new V3(10, 10, 10));
    this.acc = null;
  }
  ray(o, d, maxT) { return this.hash.ray(o, d, maxT); }
  dispose() {
    this.scene.traverse(o => {
      if (o.geometry) o.geometry.dispose();
      if (o.material && o.material.userData && o.material.userData.own) o.material.dispose();
    });
    if (this.shadowRT) this.shadowRT.dispose();
    for (const e of this.ents) if (e.dispose) e.dispose();
    this.disposed = true;
  }
}

/* ---------- frame helper: matrix from position/yaw/up ---------- */
function frameMatrix(x, y, z, yaw, upQ) {
  const m = new M4().makeRotationY(yaw);
  if (upQ) m.premultiply(new M4().makeRotationFromQuaternion(upQ));
  m.setPosition(x, y, z); return m;
}
function aabbOfBoxM(m, hx, hy, hz) {
  const mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9];
  for (let i = 0; i < 8; i++) { const p = new V3(i & 1 ? hx : -hx, i & 2 ? hy : -hy, i & 4 ? hz : -hz).applyMatrix4(m); const a = [p.x, p.y, p.z]; for (let k = 0; k < 3; k++) { if (a[k] < mn[k]) mn[k] = a[k]; if (a[k] > mx[k]) mx[k] = a[k]; } }
  return [mn, mx];
}

/* ---------- Door ---------- */
let DOOR_ID = 0;
class Door {
  constructor(L, o) {
    this.L = L; this.id = DOOR_ID++; this.kind = o.kind || 'plain'; this.w = o.w || 1.1; this.h = o.h || 2.25;
    this.locked = !!o.locked; this.real = !!o.real; this.onOpen = o.onOpen; this.onTry = o.onTry; this.lockMsg = o.lockMsg;
    this.F = frameMatrix(o.x, o.y, o.z, o.yaw || 0, o.upQ || null); this.Finv = this.F.clone().invert();
    this.pos = new V3().setFromMatrixPosition(this.F);
    this.upQ = o.upQ || null; this.fwd = new V3(0, 0, 1).transformDirection(this.F); this.upV = new V3(0, 1, 0).transformDirection(this.F);
    this.angle = o.startOpen ? (o.swingIn ? -1.6 : 1.6) : 0; this.target = this.angle; this.swingIn = !!o.swingIn; this.speed = 2.2;
    this.portal = null; this.auto = o.autoClose || 0; this.openT = 0; this.hidden = false;
    this.interactive = o.interactive !== false; this.prompt = o.prompt || 'Open';
    const w = this.w, h = this.h, ft = 0.13, fd = o.frameDepth || 0.34;
    // ---- frame (merged into the level mesh) ----
    const frameFn = a => {
      const t = o.frameTone == null ? 0.62 : o.frameTone;
      const mk = (cx, cy, cz, hx, hy, hz) => { const m = this.F.clone().multiply(new M4().makeTranslation(cx, cy, cz)); a.boxM(m, hx, hy, hz, t, 4, true); return m; };
      this._jambs = [mk(-w / 2 - ft / 2, h / 2 + 0.06, 0, ft / 2, h / 2 + 0.06, fd / 2), mk(w / 2 + ft / 2, h / 2 + 0.06, 0, ft / 2, h / 2 + 0.06, fd / 2), mk(0, h + ft / 2 + 0.06, 0, w / 2 + ft, ft / 2, fd / 2)];
      if (o.ornate) { mk(0, h + ft + 0.2, 0, w / 2 + ft + 0.08, 0.06, fd / 2 + 0.04); mk(0, h + ft + 0.36, 0, w / 2 + ft - 0.05, 0.1, fd / 2 - 0.02); }
    };
    frameFn(L.a);
    if (o.frameSolid !== false) for (const jm of this._jambs.slice(0, 2)) { const [mn, mx] = aabbOfBoxM(jm, ft / 2, h / 2 + 0.06, fd / 2); L.addCol(mn[0], mn[1], mn[2], mx[0], mx[1], mx[2]); }
    // ---- leaf ----
    this.pivot = new THREE.Group(); this.pivot.matrixAutoUpdate = false;
    this.base = new M4().copy(this.F).multiply(new M4().makeTranslation(-w / 2, 0, 0));
    const lt = o.leafTone == null ? 0.72 : o.leafTone;
    this.leaf = buildObj(a => {
      const lw = w - 0.03, lh = h - 0.02;
      a.box(0.01, 0.01, -0.035, lw, lh, 0.035, lt, 4, true);
      for (const s of [-1, 1]) {
        a.box(0.14, lh * 0.55, s * 0.035, lw - 0.14, lh - 0.16, s * 0.05, lt * 0.92, 0, true);
        a.box(0.14, 0.18, s * 0.035, lw - 0.14, lh * 0.5, s * 0.05, lt * 0.92, 0, true);
        a.box(lw - 0.16, h * 0.46, s * 0.05, lw - 0.08, h * 0.46 + 0.05, s * 0.11, 0.3, 0, true);
        if (o.window) a.box(lw * 0.3, lh * 0.66, s * 0.036, lw * 0.7, lh * 0.86, s * 0.052, 0.08, 0, true);
      }
    }, { mat: this.ownMat() });
    if (this.real) {
      const kh = new THREE.Mesh(new THREE.BoxGeometry(0.05, 0.1, 0.14), MAT.glow); kh.position.set(w - 0.15, h * 0.46 - 0.1, 0); this.leaf.add(kh);
      this.keyGlow = kh; this.markReal();
    }
    if (o.knocker) { this.leaf.add(buildObj(a => a.box(w * 0.42, h * 0.62, -0.09, w * 0.58, h * 0.66, 0.09, 0.2, 0, true))); }
    this.pivot.add(this.leaf); L.add(this.pivot);
    // ---- leaf collider (dynamic) ----
    const [lmn, lmx] = aabbOfBoxM(new M4().copy(this.F).multiply(new M4().makeTranslation(0, h / 2, 0)), w / 2, h / 2, 0.06);
    this.col = { min: lmn, max: lmx, on: true, surf: 'wood', _s: 0, door: this }; L.dyn.push(this.col);
    // ---- portal aperture (box beyond the plane) ----
    this.aperture = new THREE.Mesh(new THREE.BoxGeometry(w + 0.02, h + 0.02, 0.6), MAT.portal);
    // the portal box sits beyond the doorway as seen by the viewer: +z for exits, -z for entrances (seen from inside the room)
    this.aperture.matrixAutoUpdate = false; this.aperture.matrix.copy(this.F).multiply(new M4().makeTranslation(0, h / 2, this.kind === 'entrance' ? -0.31 : 0.31));
    this.aperture.matrixWorld.copy(this.aperture.matrix); // valid before the first render (frustum tests use it)
    this.aperture.matrixWorldNeedsUpdate = true; this.aperture.visible = false; this.aperture.renderOrder = 0; L.add(this.aperture);
    // local plane (for portal clipping when this door is a destination)
    this.plane = new THREE.Plane().setFromNormalAndCoplanarPoint(this.fwd.clone(), this.pos.clone());
    this.prevLocal = null;
    { const [bmn, bmx] = aabbOfBoxM(new M4().copy(this.F).multiply(new M4().makeTranslation(0, h / 2, -0.45)), w / 2 + 0.1, h / 2, 0.12); this.block = { min: bmn, max: bmx, on: false, _s: 0 }; L.dyn.push(this.block); }
    this.update(0);
    L.doors.push(this);
  }
  markReal() {
    if (this.leak) return;
    // a thin line of light in the gap under the leaf, and a soft blue pool on the floor in front of it
    const lk = new THREE.Mesh(new THREE.BoxGeometry(this.w - 0.12, 0.014, 0.035), MAT.glow); lk.matrixAutoUpdate = false;
    lk.matrix.copy(this.F).multiply(new M4().makeTranslation(0, 0.007, -0.055)); lk.matrixWorldNeedsUpdate = true; this.L.add(lk); this.leak = lk;
    this.spillMat = makeSpillMat(BLUE, 0.75);
    const pool = new THREE.Mesh(new THREE.PlaneGeometry(this.w + 1.3, 2.3), this.spillMat); pool.matrixAutoUpdate = false; pool.renderOrder = 2;
    pool.matrix.copy(this.F).multiply(new M4().makeTranslation(0, 0.014, -1.2)).multiply(new M4().makeRotationX(-Math.PI / 2)); pool.matrixWorldNeedsUpdate = true; this.L.add(pool); this.pool = pool;
    // a soft halo around the keyhole on both faces of the leaf, so the real door reads from across a room
    if (this.keyGlow) {
      const hm = makeSpillMat(BLUE, 0.6, 1), kp = this.keyGlow.position;
      for (const sd of [1, -1]) { const h = new THREE.Mesh(new THREE.PlaneGeometry(0.62, 0.62), hm); h.position.set(kp.x, kp.y, sd * 0.085); if (sd < 0) h.rotation.y = Math.PI; h.renderOrder = 2; this.leaf.add(h); }
    }
    const sp = new V3(0, 0.6, -1.3).applyMatrix4(this.F); this.spill = this.L.light(sp.x, sp.y, sp.z, 3.6, 0.32, { flicker: 0.04 });
  }
  ownMat() { if (!this._mat) { this._mat = makeInkMat(); this._mat.userData.own = true; } return this._mat; }
  local(p, out) { return (out || new V3()).copy(p).applyMatrix4(this.Finv); }
  get isOpen() { return Math.abs(this.angle) > 0.12; }
  interactPoint() { return _v3a.set(0, this.h * 0.46, 0).applyMatrix4(this.F); }
  canInteract() { return this.interactive && !this.hidden && Math.abs(this.target) < 0.01; }
  tryOpen() {
    if (this.locked) {
      AU.rattle(this.pos); if (this.onTry) this.onTry(this); else if (this.lockMsg) GAME.toast(this.lockMsg);
      this.shake = 0.35; return false;
    }
    this.open(); return true;
  }
  open(fast) {
    this.target = this.swingIn ? -1.62 : 1.62; this.speed = fast ? 6 : 1.9; AU.creak(this.pos, 1.1);
    this.openT = 0; if (this.onOpen) this.onOpen(this);
  }
  slamWhenClear() { this.slamPending = true; }
  close(slam) { this.slamPending = false; this.target = 0; this.speed = slam ? 9 : 2.2; this._slam = slam; if (!slam) AU.creak(this.pos, 0.9, 0.15); }
  update(dt) {
    const prev = this.angle;
    if (this.angle !== this.target) {
      const d = this.target - this.angle, s = this.speed * dt;
      this.angle = Math.abs(d) < s ? this.target : this.angle + Math.sign(d) * s;
      if (this.target === 0 && this.angle === 0 && prev !== 0 && this._slam) { AU.slam(this.pos, 0.55); GAME.shake(0.25); this._slam = false; if (this.onSlam) this.onSlam(this); }
    }
    let sh = 0; if (this.shake > 0) { this.shake -= dt; sh = Math.sin(this.shake * 90) * 0.02 * this.shake; }
    this.pivot.matrix.copy(this.base).multiply(_m4b.makeRotationY(this.angle + sh)); this.pivot.matrixWorldNeedsUpdate = true;
    this.col.on = Math.abs(this.angle) < 0.25 && !this.hidden;
    if (this.spillMat) { const o = 1 - Math.min(1, Math.abs(this.angle) / 0.9); this.spillMat.uniforms.uA.value = 0.5 * o; this.pool.visible = o > 0.01; this.leak.visible = o > 0.6; }
    if (this.slamPending) { this.slamT = (this.slamT || 0) + dt; const lz = this.local(PL.pos, _v3c).z; if (Math.abs(lz) > 0.95 || PL.pos.distanceTo(this.pos) > 2.6 || (this.slamT > 3 && Math.abs(lz) > 0.4)) { this.slamT = 0; this.close(true); } }
    if (this.auto && this.isOpen && this.target !== 0) { this.openT += dt; if (this.openT > this.auto) this.close(true); }
  }
}

/* ---------- pickups: 'key' (a blue octahedron, lit) or 'note' (a sheet of paper). o.onGet(p) runs on collect ---------- */
class Pickup {
  constructor(L, kind, x, y, z, o = {}) {
    this.L = L; this.kind = kind; this.pos = new V3(x, y, z); this.o = o; this.alive = true; this.t = Math.random() * 6;
    this.obj = new THREE.Group(); this.obj.position.copy(this.pos);
    if (kind === 'key') this.obj.add(new THREE.Mesh(new THREE.OctahedronGeometry(0.14, 0), MAT.glow));
    else this.obj.add(buildObj(a => { a.box(-0.15, -0.2, -0.004, 0.15, 0.2, 0.004, 1.2, PAT.PAPER, true); for (let i = 0; i < 6; i++) a.line(new V3(-0.11, 0.13 - i * 0.05, 0.006), new V3(0.1 - (i === 5 ? 0.08 : 0), 0.13 - i * 0.05, 0.006), 0); }));
    if (kind === 'key' && o.light !== false) this.pl = L.light(x, y + 0.1, z, 4.5, 0.55);
    L.add(this.obj); L.pickups.push(this);
  }
  update(dt) {
    if (!this.alive) return;
    this.t += dt; this.obj.position.copy(this.pos).addScaledVector(PL.up, Math.sin(this.t * 2) * 0.05);
    this.obj.rotation.y += dt * (this.kind === 'note' ? 0.6 : 1.2);
    if (PL.center.distanceTo(this.obj.position) < (this.o.r || 1.25)) this.collect();
  }
  collect() { this.alive = false; this.obj.visible = false; if (this.pl) this.pl.i = 0; AU.chime(0.14); if (this.o.onGet) this.o.onGet(this); GAME.onPickup(this); }
}

/* ---------- build helpers ---------- */
const DIRS = { '+x': [1, 0], '-x': [-1, 0], '+z': [0, 1], '-z': [0, -1] };
const yawOf = d => ({ '+z': 0, '+x': Math.PI / 2, '-z': Math.PI, '-x': -Math.PI / 2 })[d];
const faceYaw = doorYaw => doorYaw + Math.PI; // player yaw that looks along a door's walking direction
// wall spanning x0..x1 (thickness z0..z1) with rectangular holes [{a0,a1,b0,b1}] (x and y)
function wallX(L, x0, x1, z0, z1, y0, y1, holes = [], o = {}) {
  holes = holes.slice().sort((a, b) => a.a0 - b.a0); let cur = x0;
  for (const h of holes) {
    if (h.a0 > cur + 0.001) L.B(cur, y0, z0, h.a0, y1, z1, o);
    if (h.b1 < y1 - 0.001) L.B(h.a0, h.b1, z0, h.a1, y1, z1, o);
    if (h.b0 > y0 + 0.001) L.B(h.a0, y0, z0, h.a1, h.b0, z1, o);
    cur = h.a1;
  }
  if (cur < x1 - 0.001) L.B(cur, y0, z0, x1, y1, z1, o);
}
function wallZ(L, z0, z1, x0, x1, y0, y1, holes = [], o = {}) {
  holes = holes.slice().sort((a, b) => a.a0 - b.a0); let cur = z0;
  for (const h of holes) {
    if (h.a0 > cur + 0.001) L.B(x0, y0, cur, x1, y1, h.a0, o);
    if (h.b1 < y1 - 0.001) L.B(x0, h.b1, h.a0, x1, y1, h.a1, o);
    if (h.b0 > y0 + 0.001) L.B(x0, y0, h.a0, x1, h.b0, h.a1, o);
    cur = h.a1;
  }
  if (cur < z1 - 0.001) L.B(x0, y0, cur, x1, y1, z1, o);
}
const doorHole = (c, y0, w = 1.1, h = 2.25) => ({ a0: c - w / 2 - 0.13, a1: c + w / 2 + 0.13, b0: y0, b1: y0 + h + 0.19 });
// straight flight of stairs. Starts at (x,y,z): bottom of first step, centre of width. Returns end point.
function stairs(L, x, y, z, dir, n, o = {}) {
  const w = o.w || 1.8, rise = o.rise || 0.22, run = o.run || 0.34, tone = o.tone == null ? 0.88 : o.tone, pat = o.pat || 0;
  const [dx, dz] = DIRS[dir], skip = o.skip || [];
  const steps = [];
  for (let i = 0; i < n; i++) {
    if (skip.includes(i)) continue;
    const top = y + rise * (i + 1), bot = o.solid ? y : top - Math.max(o.thick || 0.24, rise + 0.03);
    const a0 = i * run, a1 = (i + 1) * run;
    let c;
    if (dx) c = [x + dx * a0, bot, z - w / 2, x + dx * a1, top, z + w / 2]; else c = [x - w / 2, bot, z + dz * a0, x + w / 2, top, z + dz * a1];
    if (o.collapse) steps.push(c); else L.B(Math.min(c[0], c[3]), c[1], Math.min(c[2], c[5]), Math.max(c[0], c[3]), c[4], Math.max(c[2], c[5]), { tone, pat, surf: o.surf });
  }
  const len = n * run, H = n * rise;
  // stringers (sloped side beams)
  if (o.stringers !== false && !o.solid) {
    const ang = Math.atan2(H, len), sl = Math.hypot(H, len);
    for (const s of [-1, 1]) {
      const cx = x + dx * len / 2 + (dz ? s * (w / 2 + 0.06) : 0), cz = z + dz * len / 2 + (dx ? s * (w / 2 + 0.06) : 0), cy = y + H / 2 - 0.12;
      const m = new M4().makeTranslation(cx, cy, cz);
      if (dx) m.multiply(new M4().makeRotationZ(dx * ang)); else m.multiply(new M4().makeRotationX(-dz * ang));
      L.BM(m, dx ? sl / 2 : 0.06, 0.2, dx ? 0.06 : sl / 2, { tone: o.stringerTone == null ? 0.62 : o.stringerTone });
    }
  }
  if (o.rails) for (const s of (o.railSides || [-1, 1])) stairRail(L, x, y, z, dir, n, rise, run, w, s, o);
  return { x: x + dx * len, y: y + H, z: z + dz * len, steps };
}
function stairRail(L, x, y, z, dir, n, rise, run, w, side, o = {}) {
  const [dx, dz] = DIRS[dir]; const off = w / 2 - 0.05;
  for (let i = 0; i < n; i += 2) {
    const a = (i + 0.5) * run, top = y + rise * (i + 1);
    const px = x + dx * a + (dz ? side * off : 0), pz = z + dz * a + (dx ? side * off : 0);
    L.B(px - 0.03, top, pz - 0.03, px + 0.03, top + 0.92, pz + 0.03, { tone: 1, pat: 13, solid: false });
  }
  const len = n * run, H = n * rise, ang = Math.atan2(H, len), sl = Math.hypot(H, len);
  const cx = x + dx * len / 2 + (dz ? side * off : 0), cz = z + dz * len / 2 + (dx ? side * off : 0);
  const m = new M4().makeTranslation(cx, y + H / 2 + 0.95, cz);
  if (dx) m.multiply(new M4().makeRotationZ(dx * ang)); else m.multiply(new M4().makeRotationX(-dz * ang));
  L.BM(m, dx ? sl / 2 : 0.05, 0.04, dx ? 0.05 : sl / 2, { tone: 0.55 });
  // invisible colliders per step to stop falls
  for (let i = 0; i < n; i++) {
    const a0 = i * run, a1 = (i + 1) * run, top = y + rise * (i + 1);
    const px = x + (dz ? side * off : 0), pz = z + (dx ? side * off : 0);
    if (dx) L.addCol(px + dx * a0, top, pz - 0.05, px + dx * a1, top + 1.0, pz + 0.05, { noRay: true });
    else L.addCol(px - 0.05, top, pz + dz * a0, px + 0.05, top + 1.0, pz + dz * a1, { noRay: true });
  }
}
// straight balustrade along a horizontal segment at height y
function rail(L, x0, z0, x1, z1, y, o = {}) {
  const len = Math.hypot(x1 - x0, z1 - z0), n = Math.max(1, Math.round(len / 0.42));
  for (let i = 0; i <= n; i++) { const t = i / n, px = lerp(x0, x1, t), pz = lerp(z0, z1, t); L.B(px - 0.035, y, pz - 0.035, px + 0.035, y + 0.92, pz + 0.035, { tone: 1, pat: 13, solid: false, edges: true }); }
  const t = 0.05;
  L.B(Math.min(x0, x1) - t, y + 0.9, Math.min(z0, z1) - t, Math.max(x0, x1) + t, y + 0.98, Math.max(z0, z1) + t, { tone: 0.6, solid: false });
  L.addCol(Math.min(x0, x1) - t, y, Math.min(z0, z1) - t, Math.max(x0, x1) + t, y + 1.0, Math.max(z0, z1) + t, { noRay: true });
}
function column(L, x, y, z, r, h, o = {}) {
  L.B(x - r * 1.35, y, z - r * 1.35, x + r * 1.35, y + 0.3, z + r * 1.35, { tone: o.tone || 0.8, solid: o.solid !== false });
  L.cyl(x, y + 0.3, z, r, h - 0.6, { seg: o.seg || 10, tone: o.tone || 0.85, solid: o.solid !== false });
  L.B(x - r * 1.35, y + h - 0.3, z - r * 1.35, x + r * 1.35, y + h, z + r * 1.35, { tone: o.tone || 0.8, solid: o.solid !== false });
}
// arch: axis 'x' spans along x (opening faces z). centre at (cx, y, cz)
function arch(L, cx, y, cz, axis, span, h, depth, o = {}) {
  const pw = o.pw || 0.5, tone = o.tone == null ? 0.82 : o.tone, pat = o.pat || 9, r = span / 2;
  const sx = axis === 'x';
  for (const s of [-1, 1]) {
    const px = sx ? cx + s * (r + pw / 2) : cx, pz = sx ? cz : cz + s * (r + pw / 2);
    L.B(px - (sx ? pw / 2 : depth / 2), y, pz - (sx ? depth / 2 : pw / 2), px + (sx ? pw / 2 : depth / 2), y + h, pz + (sx ? depth / 2 : pw / 2), { tone, pat, solid: o.solid !== false });
  }
  const N = o.n || 9;
  for (let i = 0; i < N; i++) {
    const a = Math.PI * (i + 0.5) / N; const rr = r + pw / 2;
    const ox = Math.cos(a) * rr, oy = Math.sin(a) * rr;
    const m = new M4().makeTranslation(sx ? cx + ox : cx, y + h + oy, sx ? cz : cz + ox);
    if (sx) m.multiply(new M4().makeRotationZ(a - Math.PI / 2)); else m.multiply(new M4().makeRotationX(-(a - Math.PI / 2)));
    const seg = Math.PI * rr / N * 0.52;
    L.BM(m, sx ? seg : depth / 2, pw / 2, sx ? depth / 2 : seg, { tone: tone * (i % 2 ? 0.95 : 1), pat: 0 });
  }
}
// local-frame builder for oriented decor (non-colliding)
function frameB(L, m) {
  return {
    box(x0, y0, z0, x1, y1, z1, o = {}) {
      const mm = m.clone().multiply(new M4().makeTranslation((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2));
      L.BM(mm, Math.abs(x1 - x0) / 2, Math.abs(y1 - y0) / 2, Math.abs(z1 - z0) / 2, o);
    }
  };
}
// a decorative Escher fragment in an arbitrary orientation
function decoChunk(L, m, kind, s = 1) {
  const f = frameB(L, m);
  if (kind === 'stairs' || kind === 'flight') {
    const n = 9; for (let i = 0; i < n; i++) f.box(-0.9 * s, i * 0.24 * s, i * 0.34 * s, 0.9 * s, (i + 1) * 0.24 * s, (i + 1) * 0.34 * s, { tone: 0.88 });
    f.box(-1.0 * s, 0, -1.6 * s, 1.0 * s, 0.24 * s, 0, { tone: 0.85, pat: 9 });
    f.box(-1.0 * s, n * 0.24 * s - 0.24 * s, n * 0.34 * s, 1.0 * s, n * 0.24 * s, n * 0.34 * s + 1.6 * s, { tone: 0.85, pat: 9 });
    for (let i = 0; i < n; i += 2) f.box(-0.95 * s, (i + 1) * 0.24 * s, (i + 0.4) * 0.34 * s, -0.9 * s, (i + 1) * 0.24 * s + 0.9 * s, (i + 0.6) * 0.34 * s, { tone: 0.7 });
  } else if (kind === 'arch') {
    f.box(-2.2 * s, 0, -0.4 * s, -1.6 * s, 3.4 * s, 0.4 * s, { pat: 9, tone: 0.82 }); f.box(1.6 * s, 0, -0.4 * s, 2.2 * s, 3.4 * s, 0.4 * s, { pat: 9, tone: 0.82 });
    for (let i = 0; i < 7; i++) { const a = Math.PI * (i + 0.5) / 7, rr = 1.9 * s; const mm = m.clone().multiply(new M4().makeTranslation(Math.cos(a) * rr, 3.4 * s + Math.sin(a) * rr, 0)).multiply(new M4().makeRotationZ(a - Math.PI / 2)); L.BM(mm, 0.45 * s, 0.3 * s, 0.4 * s, { tone: 0.8 }); }
    f.box(-2.4 * s, -0.4 * s, -0.6 * s, 2.4 * s, 0, 0.6 * s, { tone: 0.75, pat: 9 });
  } else if (kind === 'block') {
    f.box(-2 * s, -2 * s, -2 * s, 2 * s, 2 * s, 2 * s, { pat: 1, tone: 0.86 });
    f.box(-0.6 * s, -0.9 * s, 2 * s, 0.6 * s, 0.9 * s, 2.06 * s, { tone: 0.1 });
    f.box(-2.3 * s, 2 * s, -2.3 * s, 2.3 * s, 2.3 * s, 2.3 * s, { tone: 0.75 });
  } else if (kind === 'column') {
    f.box(-0.5 * s, 0, -0.5 * s, 0.5 * s, 0.3 * s, 0.5 * s, { tone: 0.8 });
    f.box(-0.32 * s, 0.3 * s, -0.32 * s, 0.32 * s, 7.4 * s, 0.32 * s, { tone: 0.88 });
    f.box(-0.5 * s, 7.4 * s, -0.5 * s, 0.5 * s, 7.7 * s, 0.5 * s, { tone: 0.8 });
  } else if (kind === 'room') {
    f.box(-3 * s, 0, -3 * s, 3 * s, 0.3 * s, 3 * s, { pat: 3, tone: 0.9 });
    f.box(-3 * s, 0.3 * s, 2.7 * s, 3 * s, 3.5 * s, 3 * s, { pat: 6, tone: 0.85 });
    f.box(-3 * s, 0.3 * s, -3 * s, -2.7 * s, 3.5 * s, 2.7 * s, { pat: 6, tone: 0.85 });
    f.box(-0.5 * s, 0.3 * s, 2.6 * s, 0.5 * s, 2.4 * s, 2.7 * s, { tone: 0.6, pat: 4 });
  }
}
function scatterDeco(L, n, rmin, rmax, ymin, ymax, kinds, seed, center = new V3()) {
  const r = mulberry32(seed);
  for (let i = 0; i < n; i++) {
    const a = r() * TAU, d = rmin + r() * (rmax - rmin), y = ymin + r() * (ymax - ymin);
    const m = new M4().makeTranslation(center.x + Math.cos(a) * d, y, center.z + Math.sin(a) * d);
    const ro = [0, Math.PI / 2, Math.PI, -Math.PI / 2];
    m.multiply(new M4().makeRotationY(r() * TAU)).multiply(new M4().makeRotationX(ro[Math.floor(r() * 4)] * (r() < 0.6 ? 1 : 0))).multiply(new M4().makeRotationZ(ro[Math.floor(r() * 4)] * (r() < 0.5 ? 1 : 0)));
    decoChunk(L, m, kinds[Math.floor(r() * kinds.length)], 0.8 + r() * 1.6);
  }
}
/* ---------- canvas textures ---------- */
function canvasTex(w, h, draw) {
  const c = document.createElement('canvas'); c.width = w; c.height = h; const g = c.getContext('2d');
  draw(g, w, h); const t = new THREE.CanvasTexture(c); t.minFilter = THREE.LinearMipmapLinearFilter; t.anisotropy = 4; t.userData = { c, g, draw }; return t;
}
const PAPER_HEX = '#E4E0D5', INK_HEX = '#171511';
function textPlane(L, x, y, z, nx, nz, w, h, draw, parent) {
  const tex = canvasTex(Math.round(w * 200), Math.round(h * 200), draw);
  const mat = new THREE.MeshBasicMaterial({ map: tex, transparent: true }); mat.userData.own = true;
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), mat);
  m.position.set(x + nx * 0.025, y, z + nz * 0.025); m.rotation.y = Math.atan2(nx, nz);
  (parent || L.scene).add(m); m.userData.tex = tex; return m;
}
function redrawText(m, draw) { const t = m.userData.tex; const c = t.userData.c; draw(t.userData.g, c.width, c.height); t.needsUpdate = true; }
function scrawl(text, size = 64, font = '"Special Elite"') {
  return (g, w, h) => {
    g.clearRect(0, 0, w, h); g.fillStyle = INK_HEX; g.textAlign = 'center'; g.textBaseline = 'middle';
    const lines = text.split('\n'); const fs = Math.min(size, h / (lines.length * 1.25));
    g.font = `${fs}px ${font}, "Courier New", monospace`;
    lines.forEach((ln, i) => {
      const y = h / 2 + (i - (lines.length - 1) / 2) * fs * 1.2;
      g.save(); g.translate(w / 2, y); g.rotate((Math.random() - 0.5) * 0.04); g.fillText(ln, 0, 0); g.restore();
      for (let k = 0; k < ln.length / 3; k++) { const x = w / 2 + (Math.random() - 0.5) * fs * ln.length * 0.5; g.fillRect(x, y + fs * 0.3, 2, Math.random() * fs * 0.9); }
    });
  };
}
/* ---------- interactables ---------- */
function interact(L, pos, prompt, fn, o = {}) {
  const it = { pos: pos.clone(), prompt, fn, on: true, r: o.r || 2.4, cos: o.cos || 0.9, when: o.when }; (L.inter || (L.inter = [])).push(it); return it;
}
/* ---------- simple point-light lamp visuals ---------- */
function lampVis(L, x, y, z, kind = 'bulb', parent) {
  let m;
  if (kind === 'candle') { const g = new THREE.Group(); g.add(buildObj(a => a.cyl(0, -0.25, 0, 0.035, 0.22, 8, 0.95, 0, true))); const f = new THREE.Mesh(new THREE.SphereGeometry(0.035, 8, 6), MAT.glowWarm); f.scale.y = 1.8; f.position.y = 0.03; g.add(f); m = g; }
  else if (kind === 'panel') m = new THREE.Mesh(new THREE.BoxGeometry(1.4, 0.05, 0.35), MAT.glowWhite);
  else if (kind === 'sconce') { const g = new THREE.Group(); g.add(buildObj(a => { a.box(-0.06, -0.12, -0.04, 0.06, 0.0, 0.04, 0.4, 0, true); })); const b = new THREE.Mesh(new THREE.SphereGeometry(0.08, 10, 8), MAT.glowWarm); b.position.y = 0.06; g.add(b); m = g; }
  else m = new THREE.Mesh(new THREE.SphereGeometry(0.1, 10, 8), MAT.glowWhite);
  m.position.set(x, y, z); (parent || L.scene).add(m); return m;
}

/* ---------- Escher rooms: every wall can be a floor ----------
   A face is a local frame on one side of a room: o = origin, X/Y/Z = its axes in world space, Y = that face's "up".
   fW(face, x, y, z) turns face coordinates into world coordinates, so you build on a wall exactly as on a floor.
   Gravity is always along a world axis (PL.ax 0/1/2, PL.sg ±1), so every collider stays an axis-aligned box. */
function face(o, X, Y, Z) { const ax = Y[0] ? 0 : Y[1] ? 1 : 2; return { o, X, Y, Z, ax, sg: Y[ax] > 0 ? 1 : -1 }; }
function fW(f, x, y, z) { return new V3(f.o[0] + f.X[0] * x + f.Y[0] * y + f.Z[0] * z, f.o[1] + f.X[1] * x + f.Y[1] * y + f.Z[1] * z, f.o[2] + f.X[2] * x + f.Y[2] * y + f.Z[2] * z); }
function fB(L, f, x0, y0, z0, x1, y1, z1, o) { const a = fW(f, x0, y0, z0), b = fW(f, x1, y1, z1); return L.B(Math.min(a.x, b.x), Math.min(a.y, b.y), Math.min(a.z, b.z), Math.max(a.x, b.x), Math.max(a.y, b.y), Math.max(a.z, b.z), o); }
function fStairs(L, f, x, y, z, n, rise, run, w, o = {}) { for (let i = 0; i < n; i++) fB(L, f, x - w / 2, y, z + i * run, x + w / 2, y + rise * (i + 1), z + (i + 1) * run, Object.assign({ tone: 0.88 }, o)); return { y: y + n * rise, z: z + n * run }; }
// rotation that stands a door (or anything built for +y up) on face f. Door yaw then turns it about the face's up.
function faceQ(f) { const m = new M4().makeBasis(new V3(...f.X), new V3(...f.Y), new V3(...f.Z)); return new Q4().setFromRotationMatrix(m); }
function onFace(f) { return PL.ax === f.ax && PL.sg === f.sg; }
// switch "down" to face f, keeping the eye where it was (the camera swings round smoothly over ~0.65 s)
function gravSwitch(f, feet, axisOverride) {
  const oldEye = CAM.position.clone();
  PL.setGravity(f.ax, f.sg, false, true, axisOverride);
  PL.pos.copy(feet); PL.vel.multiplyScalar(0.25);
  const eyeH = lerp(PL.eye, PL.eyeC, PL.ch);
  PL.eyeOff.copy(oldEye).sub(_v3a.copy(PL.pos).addScaledVector(PL.up, eyeH));
  PL.peakU = PL.u(); PL.grounded = false; PL.safe = [];
  AU.grav(); GAME.shake(0.18);
}
// a glowing half-ring that marks a gravity switch. Pair it with a zone: L.gravZones.push({ from, to, box, place })
function blueArch(L, center, rot, r = 1.35) {
  const g = new THREE.Mesh(new THREE.TorusGeometry(r, 0.09, 6, 22, Math.PI), MAT.glow);
  g.position.copy(center); g.quaternion.copy(rot); L.add(g);
  for (const s of [-1, 1]) { const p = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.09, 1.2, 6), MAT.glow); p.position.set(s * r, -0.6, 0); g.add(p); }
  return g;
}
/* ---------- doors every level needs ---------- */
// the door you came in by: locked behind you; you spawn 1.35 m in front of it, facing into the room
function stdEntrance(L, x, y, z, yaw, o = {}) {
  L.entrance = new Door(L, Object.assign({ x, y, z, yaw, kind: 'entrance', locked: true, swingIn: true, lockMsg: 'It will not open. There is no going back.' }, o));
  const f = new V3(Math.sin(yaw), 0, Math.cos(yaw)); if (o.upQ) f.applyQuaternion(o.upQ);
  L.spawn = { pos: new V3(x, y, z).addScaledVector(f, 1.35), yaw: faceYaw(yaw), q: o.upQ ? o.upQ.clone() : null };
}
// the real way on: blue keyhole, blue light under the leaf. Walking through it once it is open crosses into the next level.
function exitDoor(L, x, y, z, yaw, o = {}) { L.exitDoor = new Door(L, Object.assign({ x, y, z, yaw, kind: 'exit', real: true, ornate: true }, o)); return L.exitDoor; }
````

### `assets/starter/src/04_player.js`

<!-- bundle-file: assets/starter/src/04_player.js sha256=51e5f31080eee22777db5a77150c6510d21127a40c5307220139c8ec75256425 -->
````javascript
/* ===================== input: keyboard + mouse (pointer lock), touch (floating joystick + drag to look), gamepad =====================
   Actions are edges: IN.edge(name) when pressed, IN.take(name) once per press in the game loop. */
const IN = {
  keys: {}, mdx: 0, mdy: 0, rmb: false, lmb: false, locked: false, lockTried: false, drag: false,
  joy: { x: 0, y: 0, id: null, ox: 0, oy: 0, sprint: false }, lookId: null, lx: 0, ly: 0,
  edges: {}, gp: null, gpOK: true, gpPrev: {}, gpLook: { x: 0, y: 0 }, gpMove: { x: 0, y: 0 }, gpSprint: false,
  usedTouch: IS_TOUCH, lastDevice: IS_TOUCH ? 'touch' : 'kb',
  edge(n) { this.edges[n] = true; },
  take(n) { const v = !!this.edges[n]; this.edges[n] = false; return v; },
  clearEdges() { this.edges = {}; },
  init(canvas) {
    const KE = { Space: 'jump', KeyE: 'act', Enter: 'act', KeyF: 'lamp', KeyP: 'pause', Escape: 'pause', KeyC: 'crouch', ControlLeft: 'crouch' };
    addEventListener('keydown', e => {
      if (e.repeat) { if (GAME.state === 'play' && e.code === 'Space') e.preventDefault(); return; }
      this.keys[e.code] = true; this.lastDevice = 'kb';
      if (GAME.state === 'play' && ['Space', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.code)) e.preventDefault();
      const n = KE[e.code]; if (n) this.edge(n);
      AU.init(); AU.resume();
      UI.onKey(e);
    });
    addEventListener('keyup', e => { this.keys[e.code] = false; });
    addEventListener('blur', () => { this.keys = {}; this.rmb = false; this.lmb = false; });
    canvas.addEventListener('mousedown', e => {
      AU.init(); AU.resume(); this.lastDevice = 'kb';
      if (e.button === 2) this.rmb = true;
      if (e.button === 0) { this.lmb = true; this.drag = true; }
      if (GAME.state === 'play' && !this.locked && !IS_TOUCH_ONLY()) this.requestLock();
    });
    addEventListener('mouseup', e => { if (e.button === 2) this.rmb = false; if (e.button === 0) { this.lmb = false; this.drag = false; } });
    addEventListener('mousemove', e => {
      if (GAME.state !== 'play') return;
      if (this.locked) { this.mdx += e.movementX || 0; this.mdy += e.movementY || 0; }
      else if (this.drag) { this.mdx += (e.movementX || 0) * 1.2; this.mdy += (e.movementY || 0) * 1.2; }
    });
    canvas.addEventListener('contextmenu', e => e.preventDefault());
    document.addEventListener('pointerlockchange', () => { this.locked = document.pointerLockElement === canvas; if (!this.locked && GAME.state === 'play' && this._wasLocked && !GAME.ignoreUnlock) GAME.pause(); this._wasLocked = this.locked; });
    document.addEventListener('pointerlockerror', () => { this.locked = false; });
    // ---- touch ----
    const joy = $('joy'), knob = $('joyK');
    const btns = { tAct: 'act', tJump: 'jump', tLamp: 'lamp', tCrouch: 'crouch', tPause: 'pause' }; // add .tb buttons with these ids in 00_head.html
    const onStart = e => {
      AU.init(); AU.resume(); this.usedTouch = true; this.lastDevice = 'touch';
      if (GAME.state !== 'play') return;
      for (const t of e.changedTouches) {
        const el = t.target.closest ? t.target.closest('.tb') : null;
        if (el) {
          if (btns[el.id]) { this.edge(btns[el.id]); el.classList.add('on'); setTimeout(() => el.classList.remove('on'), 140); }
          continue;
        }
        const leftSide = SET.lefty ? t.clientX > innerWidth * 0.55 : t.clientX < innerWidth * 0.45;
        if (leftSide && this.joy.id === null) {
          this.joy.id = t.identifier;
          const r = 64, x = clamp(t.clientX, r + 8, innerWidth - r - 8), y = clamp(t.clientY, r + 8, innerHeight - r - 8);
          this.joy.ox = x; this.joy.oy = y; joy.style.left = (x - r) + 'px'; joy.style.top = (y - r) + 'px'; joy.style.bottom = 'auto';
          this.joy.x = 0; this.joy.y = 0; knob.style.transform = 'translate(0px,0px)';
        } else if (this.lookId === null) { this.lookId = t.identifier; this.lx = t.clientX; this.ly = t.clientY; }
      }
      if (e.cancelable) e.preventDefault();
    };
    const onMove = e => {
      if (GAME.state !== 'play') return;
      for (const t of e.changedTouches) {
        if (t.identifier === this.joy.id) {
          let dx = t.clientX - this.joy.ox, dy = t.clientY - this.joy.oy; const l = Math.hypot(dx, dy), mx = 56;
          if (l > mx) { dx *= mx / l; dy *= mx / l; }
          this.joy.x = dx / mx; this.joy.y = -dy / mx; knob.style.transform = `translate(${dx}px,${dy}px)`;
          this.joy.sprint = l > mx * 0.97; joy.classList.toggle('sprint', this.joy.sprint);
        } else if (t.identifier === this.lookId) {
          this.mdx += (t.clientX - this.lx) * 2.1; this.mdy += (t.clientY - this.ly) * 2.1; this.lx = t.clientX; this.ly = t.clientY;
        }
      }
      if (e.cancelable) e.preventDefault();
    };
    const onEnd = e => {
      for (const t of e.changedTouches) {
        if (t.identifier === this.joy.id) { this.joy.id = null; this.joy.x = 0; this.joy.y = 0; this.joy.sprint = false; knob.style.transform = 'translate(0px,0px)'; joy.classList.remove('sprint'); resetJoy(); }
        if (t.identifier === this.lookId) this.lookId = null;
      }
    };
    const resetJoy = () => { joy.style.left = ''; joy.style.top = ''; joy.style.bottom = ''; };
    const tl = $('touch');
    for (const el of [canvas, tl]) { el.addEventListener('touchstart', onStart, { passive: false }); el.addEventListener('touchmove', onMove, { passive: false }); el.addEventListener('touchend', onEnd); el.addEventListener('touchcancel', onEnd); }
  },
  requestLock() {
    const c = $('gl'); if (!c.requestPointerLock) return;
    try { const p = c.requestPointerLock(); if (p && p.catch) p.catch(() => { this.locked = false; }); } catch (e) { }
  },
  pollPad() {
    if (!this.gpOK) return;
    let pads;
    try {
      if (document.featurePolicy && document.featurePolicy.allowsFeature && !document.featurePolicy.allowsFeature('gamepad')) { this.gpOK = false; return; }
      pads = navigator.getGamepads ? navigator.getGamepads() : null;
    } catch (e) { this.gpOK = false; return; }
    if (!pads) return;
    let gp = null; for (const p of pads) if (p && p.connected) { gp = p; break; }
    this.gp = gp; if (!gp) { this.gpMove.x = this.gpMove.y = this.gpLook.x = this.gpLook.y = 0; return; }
    const dz = v => Math.abs(v) < 0.16 ? 0 : (v - Math.sign(v) * 0.16) / 0.84;
    this.gpMove.x = dz(gp.axes[0] || 0); this.gpMove.y = -dz(gp.axes[1] || 0);
    this.gpLook.x = dz(gp.axes[2] || 0); this.gpLook.y = dz(gp.axes[3] || 0);
    const b = i => !!(gp.buttons[i] && (gp.buttons[i].pressed || gp.buttons[i].value > 0.5));
    const map = { 0: 'jump', 2: 'act', 1: 'crouch', 9: 'pause', 6: 'lamp' }; // standard mapping: A, X, B, Start, LT
    for (const k in map) { const v = b(+k); if (v && !this.gpPrev[k]) { this.lastDevice = 'pad'; this.edge(map[k]); UI.onPad(map[k]); } this.gpPrev[k] = v; }
    for (const k of [12, 13, 14, 15]) { const v = b(k); if (v && !this.gpPrev[k]) UI.onPad(k === 12 ? 'up' : k === 13 ? 'down' : k === 14 ? 'left' : 'right'); this.gpPrev[k] = v; }
    this.gpSprint = b(10);
    if (Math.abs(this.gpMove.x) + Math.abs(this.gpMove.y) + Math.abs(this.gpLook.x) > 0.2) this.lastDevice = 'pad';
  }
};
function IS_TOUCH_ONLY() { return IN.lastDevice === 'touch'; }

/* ===================== player: capsule-ish AABB, any-axis gravity (PL.ax 0/1/2, PL.sg ±1), stairs step-up, coyote time =====================
   PL.pos is the feet. qG rotates the world-up frame onto the current gravity; yaw/pitch are relative to it. */
const PL = {
  pos: new V3(), vel: new V3(), up: new V3(0, 1, 0), ax: 1, sg: 1,
  qG: new Q4(), qGfrom: new Q4(), qGto: new Q4(), gT: 1, yaw: 0, pitch: 0, roll: 0,
  grounded: false, coyote: 0, jumpBuf: 0, crouch: false, ch: 0, sprinting: false, stamina: 1,
  H: 1.72, Hc: 1.12, eye: 1.6, eyeC: 0.98, R: 0.28, stepH: 0.46,
  lampOn: false,
  stepAcc: 0, bob: 0, bobAmt: 0, eyeOff: new V3(), trauma: 0, fovKick: 0, center: new V3(), eyePos: new V3(),
  lampPos: new V3(), lampDir: new V3(0, 0, -1), lampI: 0, lampRange: 15,
  slow: 1, safe: [], safeT: 0, peakU: 0, groundCol: null, frozen: false,
  gravLock: 0, lastSurf: 'stone',
  reset(L, pos, yaw, opts = {}) {
    this.pos.copy(pos); this.vel.set(0, 0, 0); this.yaw = yaw; this.pitch = opts.pitch || 0; this.roll = 0;
    this.qG.identity(); this.qGto.identity(); this.qGfrom.identity(); this.gT = 1; this.ax = 1; this.sg = 1; this.up.set(0, 1, 0); this.gravLock = 0; this.grounded = false; this.eyeOff.set(0, 0, 0); this.safe = []; this.safeT = 0;
    this.slow = 1; this.crouch = false; this.ch = 0; this.trauma = 0; this.peakU = this.u(); this.center.copy(pos).addScaledVector(this.up, this.H * 0.5);
  },
  axisVec(ax, sg, out) { return (out || new V3()).set(ax === 0 ? sg : 0, ax === 1 ? sg : 0, ax === 2 ? sg : 0); },
  setGravity(ax, sg, instant, rotateVel = true, axisOverride) {
    const nu = this.axisVec(ax, sg);
    const q = (axisOverride && this.up.dot(nu) < -0.99) ? new Q4().setFromAxisAngle(axisOverride.clone().normalize(), Math.PI) : new Q4().setFromUnitVectors(this.up, nu);
    if (instant) { this.qG.premultiply(q); this.qGto.copy(this.qG); this.qGfrom.copy(this.qG); this.gT = 1; }
    else { this.qGfrom.copy(this.curQG()); this.qGto.premultiply(q); this.gT = 0; }
    if (rotateVel) this.vel.applyQuaternion(q);
    this.ax = ax; this.sg = sg; this.up.copy(nu); this.gravLock = 0.6;
  },
  setFrameQ(q) { // set gravity frame directly (portal transitions)
    this.qG.copy(q); this.qGto.copy(q); this.qGfrom.copy(q); this.gT = 1;
    const u = new V3(0, 1, 0).applyQuaternion(q);
    const a = [Math.abs(u.x), Math.abs(u.y), Math.abs(u.z)]; const ax = a[0] > a[1] && a[0] > a[2] ? 0 : a[1] > a[2] ? 1 : 2;
    this.ax = ax; this.sg = (ax === 0 ? u.x : ax === 1 ? u.y : u.z) > 0 ? 1 : -1; this.up.copy(this.axisVec(this.ax, this.sg));
    // snap the frame to the exact axis
    const fix = new Q4().setFromUnitVectors(u.normalize(), this.up); this.qG.premultiply(fix); this.qGto.copy(this.qG); this.qGfrom.copy(this.qG);
  },
  curQG() { return this.gT >= 1 ? this.qGto : _q4a.copy(this.qGfrom).slerp(this.qGto, smooth(this.gT)); },
  comp(v, i) { return i === 0 ? v.x : i === 1 ? v.y : v.z; },
  setComp(v, i, x) { if (i === 0) v.x = x; else if (i === 1) v.y = x; else v.z = x; },
  u() { return this.comp(this.pos, this.ax) * this.sg; },
  height() { return lerp(this.H, this.Hc, this.ch); },
  box(H, mn, mx) {
    for (let i = 0; i < 3; i++) {
      const c = this.comp(this.pos, i);
      if (i === this.ax) { if (this.sg > 0) { mn[i] = c; mx[i] = c + H; } else { mn[i] = c - H; mx[i] = c; } }
      else { mn[i] = c - this.R; mx[i] = c + this.R; }
    }
  },
  gather(L, mn, mx) {
    _cands.length = 0;
    const e = 0.6; _qmn[0] = mn[0] - e; _qmn[1] = mn[1] - e; _qmn[2] = mn[2] - e; _qmx[0] = mx[0] + e; _qmx[1] = mx[1] + e; _qmx[2] = mx[2] + e;
    L.hash.query(_qmn, _qmx, _cands);
    for (const c of L.dyn) if (c.on) _cands.push(c);
    return _cands;
  },
  overlap(mn, mx, c) { return mn[0] < c.max[0] && mx[0] > c.min[0] && mn[1] < c.max[1] && mx[1] > c.min[1] && mn[2] < c.max[2] && mx[2] > c.min[2]; },
  anyOverlap(L, mn, mx) { const cs = this.gather(L, mn, mx); for (const c of cs) if (!c.ghost && this.overlap(mn, mx, c)) return c; return null; },
  moveAxis(L, i, d, out) {
    if (d === 0) return;
    this.setComp(this.pos, i, this.comp(this.pos, i) + d);
    const H = this.height(); this.box(H, _mn, _mx);
    const cs = this.gather(L, _mn, _mx).slice();
    for (const c of cs) {
      if (c.ghost || !this.overlap(_mn, _mx, c)) continue;
      if (i === this.ax) {
        if (d * this.sg < 0) { this.setComp(this.pos, i, this.sg > 0 ? c.max[i] : c.min[i]); out.landed = c; }
        else { this.setComp(this.pos, i, this.sg > 0 ? c.min[i] - H : c.max[i] + H); out.head = true; }
      } else {
        const topU = this.sg > 0 ? c.max[this.ax] : -c.min[this.ax];
        const rise = topU - this.u();
        if (rise > 0 && rise <= this.stepH && out.canStep && !c.noStep) { // even a hair-thin seam is a step, not a wall
          const save = this.comp(this.pos, this.ax);
          this.setComp(this.pos, this.ax, (topU + 0.002) * this.sg);
          this.box(H, _mn2, _mx2);
          if (!this.anyOverlap(L, _mn2, _mx2)) { out.stepped = Math.max(out.stepped || 0, rise); this.box(H, _mn, _mx); continue; }
          this.setComp(this.pos, this.ax, save);
        }
        this.setComp(this.pos, i, d > 0 ? c.min[i] - this.R - 0.0005 : c.max[i] + this.R + 0.0005);
        out.hit = true; out.hitCol = c; out['h' + i] = true;
      }
      this.box(H, _mn, _mx);
    }
  },
  look(dt) {
    const s = 0.0022 * SET.sens;
    let dx = IN.mdx, dy = IN.mdy; IN.mdx = 0; IN.mdy = 0;
    const k = IN.keys; const kl = 2.2 * SET.sens * dt;
    if (k.ArrowLeft) this.yaw += kl; if (k.ArrowRight) this.yaw -= kl;
    if (k.ArrowUp) this.pitch += kl * 0.8 * (SET.invert ? -1 : 1); if (k.ArrowDown) this.pitch -= kl * 0.8 * (SET.invert ? -1 : 1);
    const gl = 2.6 * SET.sens * dt;
    this.yaw -= IN.gpLook.x * Math.abs(IN.gpLook.x) * gl * 1.3; this.pitch -= IN.gpLook.y * Math.abs(IN.gpLook.y) * gl * (SET.invert ? -1 : 1);
    this.yaw -= dx * s; this.pitch -= dy * s * (SET.invert ? -1 : 1);
    this.pitch = clamp(this.pitch, -1.5, 1.5);
  },
  basis() { // forward/right on the gravity plane (target frame)
    const q = this.qGto;
    _fwd.set(-Math.sin(this.yaw), 0, -Math.cos(this.yaw)).applyQuaternion(q);
    _rgt.set(Math.cos(this.yaw), 0, -Math.sin(this.yaw)).applyQuaternion(q);
  },
  physics(L, dt) {
    if (this.frozen) return;
    if (this.gravLock > 0) this.gravLock -= dt;
    // input
    let mx = 0, my = 0; const k = IN.keys;
    if (k.KeyW) my += 1; if (k.KeyS) my -= 1; if (k.KeyA) mx -= 1; if (k.KeyD) mx += 1;
    mx += IN.joy.x + IN.gpMove.x; my += IN.joy.y + IN.gpMove.y;
    const ml = Math.hypot(mx, my); if (ml > 1) { mx /= ml; my /= ml; }
    if (IN.take('crouch')) this.crouch = !this.crouch;
    if (this.crouch && IN.take('jump')) { this.crouch = false; }
    const wantSprint = (k.ShiftLeft || k.ShiftRight || IN.joy.sprint || IN.gpSprint) && my > 0.2 && !this.crouch;
    if (wantSprint && this.stamina > 0.02) { this.sprinting = true; this.stamina = Math.max(0, this.stamina - dt / 5.5); }
    else { this.sprinting = false; this.stamina = Math.min(1, this.stamina + dt / (wantSprint ? 9 : 3.2)); }
    // can we stand up?
    if (!this.crouch && this.ch > 0.01) { this.box(this.H, _mn2, _mx2); if (this.anyOverlap(L, _mn2, _mx2)) this.crouch = true; }
    this.ch = damp(this.ch, this.crouch ? 1 : 0, 10, dt);
    let speed = this.crouch ? 1.55 : this.sprinting ? 5.6 : 3.15;
    speed *= this.slow;
    this.basis();
    const wish = _w.set(0, 0, 0).addScaledVector(_fwd, my * speed).addScaledVector(_rgt, mx * speed);
    const up = this.up;
    let vUp = this.vel.dot(up);
    const vH = _vh.copy(this.vel).addScaledVector(up, -vUp);
    const accel = this.grounded ? 13 : 3.2;
    vH.lerp(wish, 1 - Math.exp(-accel * dt));
    vUp -= 15.5 * dt; if (vUp < -32) vUp = -32;
    if (IN.take('jump')) this.jumpBuf = 0.14;
    if (this.jumpBuf > 0) this.jumpBuf -= dt;
    let jumped = false;
    if (this.jumpBuf > 0 && (this.grounded || this.coyote > 0) && !this.crouch) { vUp = 5.0; this.jumpBuf = 0; this.coyote = 0; this.grounded = false; jumped = true; AU.noiseHit({ f: 1200, q: 1, dur: 0.06, gain: 0.05 }); }
    this.vel.copy(vH).addScaledVector(up, vUp);
    // carry on moving platform
    if (this.grounded && this.groundCol && this.groundCol.dv) this.pos.add(this.groundCol.dv);
    // integrate (sub-steps)
    const wasG = this.grounded; const preU = this.u();
    const steps = Math.ceil(this.vel.length() * dt / 0.25) || 1; const sd = dt / steps;
    const out = { canStep: wasG || this.coyote > 0, landed: null, head: false, hit: false, stepped: 0 };
    for (let s = 0; s < steps; s++) {
      for (const i of [0, 1, 2]) if (i !== this.ax) this.moveAxis(L, i, this.comp(this.vel, i) * sd, out);
      this.moveAxis(L, this.ax, this.comp(this.vel, this.ax) * sd, out);
    }
    let landed = out.landed;
    // snap down for stairs / slopes
    if (!landed && wasG && !jumped && this.vel.dot(up) <= 0.01) {
      const save = this.pos.clone(); const o2 = { canStep: false };
      this.moveAxis(L, this.ax, -this.sg * (this.stepH + 0.06), o2);
      if (o2.landed) landed = o2.landed; else this.pos.copy(save);
    }
    if (out.stepped) this.eyeOff.addScaledVector(up, -out.stepped);
    if (landed) {
      const fall = this.peakU - this.u();
      if (!this.grounded && fall > 0.6) { AU.land(fall); this.trauma = Math.min(1, this.trauma + Math.min(0.5, fall * 0.04)); if (fall > 7) GAME.shake(0.5); }
      this.grounded = true; this.coyote = 0.13; this.groundCol = landed; this.lastSurf = landed.surf || L.surf;
      const vu = this.vel.dot(up); if (vu < 0) this.vel.addScaledVector(up, -vu);
      this.peakU = this.u();
    } else {
      if (this.grounded) this.coyote = 0.13;
      this.grounded = false; this.groundCol = null; if (this.coyote > 0) this.coyote -= dt;
      this.peakU = Math.max(this.peakU, this.u());
    }
    if (out.head) { const vu = this.vel.dot(up); if (vu > 0) this.vel.addScaledVector(up, -vu); }
    // block velocity into walls
    for (const i of [0, 1, 2]) if (out['h' + i]) this.setComp(this.vel, i, 0);
    // footsteps & bob
    const hs = vH.length();
    if (this.grounded && hs > 0.4) {
      this.stepAcc += hs * dt; this.bob += hs * dt * 2.1; this.bobAmt = damp(this.bobAmt, Math.min(1, hs / 3), 8, dt);
      const stride = this.sprinting ? 0.95 : this.crouch ? 0.6 : 0.78;
      if (this.stepAcc > stride) { this.stepAcc = 0; AU.step(this.lastSurf, this.crouch ? 0.45 : this.sprinting ? 1.25 : 0.9); }
    } else this.bobAmt = damp(this.bobAmt, 0, 6, dt);
    // safe points
    this.safeT -= dt;
    if (this.grounded && this.safeT <= 0 && landed && !landed.dv && !landed.hazard && !landed.noSafe) {
      this.safeT = 0.35; this.safe.push({ p: this.pos.clone(), ax: this.ax, sg: this.sg, q: this.qGto.clone(), yaw: this.yaw }); if (this.safe.length > 24) this.safe.shift();
    }
    this.center.copy(this.pos).addScaledVector(up, this.height() * 0.5); // triggers and zones read this
    // fell into the void
    if (this.u() < L.killU || (L.killBox && !L.killBox.containsPoint(this.pos))) GAME.voidFall();
  },
  respawnSafe(back = 5) {
    const s = this.safe[Math.max(0, this.safe.length - 1 - back)];
    if (!s) return false;
    this.pos.copy(s.p); this.vel.set(0, 0, 0); this.qG.copy(s.q); this.qGto.copy(s.q); this.qGfrom.copy(s.q); this.gT = 1;
    this.ax = s.ax; this.sg = s.sg; this.up.copy(this.axisVec(s.ax, s.sg)); this.eyeOff.set(0, 0, 0); this.peakU = this.u();
    this.safe.length = Math.max(0, this.safe.length - back);
    return true;
  },
  camera(cam, dt) {
    if (this.gT < 1) this.gT = Math.min(1, this.gT + dt / 0.65);
    const q = this.curQG(); if (this.gT >= 1) this.qG.copy(this.qGto);
    this.eyeOff.multiplyScalar(Math.exp(-dt * 11));
    const eyeH = lerp(this.eye, this.eyeC, this.ch);
    const bobY = Math.sin(this.bob * 2) * 0.035 * this.bobAmt * (SET.calm ? 0.4 : 1), bobX = Math.cos(this.bob) * 0.025 * this.bobAmt * (SET.calm ? 0.4 : 1);
    this.basis();
    cam.position.copy(this.pos).addScaledVector(this.up, eyeH + bobY).addScaledVector(_rgt, bobX).add(this.eyeOff);
    // trauma shake
    this.trauma = Math.max(0, this.trauma - dt * 1.3);
    const sh = this.trauma * this.trauma * (SET.calm ? 0.35 : 1), tt = GAME.time * 31;
    const sy = noise1(tt * 0.37) * 0.035 * sh, sx = noise1(tt * 0.31 + 9) * 0.035 * sh;
    cam.quaternion.copy(q).multiply(_q4b.setFromAxisAngle(_Y, this.yaw + sx)).multiply(_q4c.setFromAxisAngle(_X, this.pitch + sy)).multiply(_q4d.setFromAxisAngle(_Z, this.roll + noise1(tt * 0.23 + 4) * 0.05 * sh));
    this.eyePos.copy(cam.position);
    this.center.copy(this.pos).addScaledVector(this.up, this.height() * 0.5);
    // lamp
    _v3a.set(0.22, -0.18, 0).applyQuaternion(cam.quaternion);
    this.lampPos.copy(cam.position).add(_v3a);
    this.lampDir.set(0, 0, -1).applyQuaternion(cam.quaternion);
  },
  forward(out) { return (out || new V3()).set(0, 0, -1).applyQuaternion(CAM.quaternion); }
};
const _cands = [], _qmn = [0, 0, 0], _qmx = [0, 0, 0], _mn = [0, 0, 0], _mx = [0, 0, 0], _mn2 = [0, 0, 0], _mx2 = [0, 0, 0];
const _fwd = new V3(), _rgt = new V3(), _w = new V3(), _vh = new V3(), _X = new V3(1, 0, 0), _Y = new V3(0, 1, 0), _Z = new V3(0, 0, 1);
const _q4a = new Q4(), _q4b = new Q4(), _q4c = new Q4(), _q4d = new Q4();
````

### `assets/starter/src/05_levels.js`

<!-- bundle-file: assets/starter/src/05_levels.js sha256=482161868dc5be8886e759961b50e2d845996eed228e53d61daafd82cf54e85f -->
````javascript
/* ===================== levels: LEVELS[i] = { name, sub, build(L), onStart?(L, viaPortal), update?(L, dt), titleView?(t) } =====================
   Units are metres, y is up, the player is 1.72 m tall and walks 3.15 m/s. Every level needs an entrance
   (stdEntrance: where you appear) and, unless it is the last, an exitDoor (the way on). Walking through an open
   exit door crosses straight into the next level, which GAME builds in the background while you play. */
const LEVELS = [];

/* ---------- an example enemy: patrols a loop, sees in a cone, catches you if it watches too long ---------- */
class Blot {
  constructor(L, path, o = {}) {
    this.L = L; this.path = path.map(p => new V3(...p)); this.speed = o.speed || 1.1; this.range = o.range || 7.5;
    this.obj = new THREE.Group();
    this.obj.add(buildObj(a => { const g = new THREE.IcosahedronGeometry(0.5, 1); a.geo(g, null, 0.2, PAT.MONSTER, 25); g.dispose(); }));
    const white = makeGlowMat(new THREE.Color(0.93, 0.91, 0.85), { pulse: 0 }), dark = makeGlowMat(INK, { pulse: 0 });
    white.userData.own = dark.userData.own = true;
    const eye = new THREE.Mesh(new THREE.CircleGeometry(0.2, 18), white); eye.position.z = 0.49; this.obj.add(eye);
    this.pupil = new THREE.Mesh(new THREE.CircleGeometry(0.08, 12), dark); this.pupil.position.z = 0.5; this.obj.add(this.pupil);
    L.add(this.obj); this.reset();
  }
  reset() { this.seg = 0; this.pos = this.path[0].clone(); this.look = this.path[1].clone().sub(this.pos).normalize(); this.sus = 0; this.t = 0; this.warned = false;
    this.obj.position.copy(this.pos); this.obj.lookAt(_v3c.copy(this.pos).add(this.look)); } // placed even while off
  update(dt) {
    if (this.off) return;
    this.t += dt;
    const P = this.path, tgt = P[(this.seg + 1) % P.length], d = _v3a.copy(tgt).sub(this.pos), dist = d.length();
    if (this.sus < 0.35) { // it stops to stare once it has noticed you
      if (dist < this.speed * dt) { this.pos.copy(tgt); this.seg = (this.seg + 1) % P.length; } else this.pos.addScaledVector(d, this.speed * dt / dist);
    }
    const toP = _v3b.copy(PL.center).sub(this.pos), pd = toP.length(); toP.divideScalar(pd || 1);
    const want = this.sus > 0.2 ? toP : dist > 0.01 ? d.divideScalar(dist) : this.look;
    this.look.lerp(want, 1 - Math.exp(-dt * 3)).normalize();
    // a cone, a range (shorter while you crouch) and a clear line of sight
    const range = this.range * (PL.crouch ? 0.55 : 1);
    const sees = pd < range && this.look.dot(toP) > 0.72 && GAME.los(this.pos, PL.center, 0.3);
    this.sus = clamp(this.sus + (sees ? dt * (1.9 - pd / range) : -dt * 0.4), 0, 1);
    GAME.threat = Math.max(GAME.threat, this.sus);
    if (sees && this.sus > 0.25 && !this.warned) { this.warned = true; AU.tone({ f: 330, fEnd: 170, dur: 0.7, gain: 0.14, type: 'triangle', rev: 0.5 }); }
    if (this.sus < 0.05) this.warned = false;
    if (this.sus >= 1) { this.sus = 0; GAME.caught(this); }
    this.obj.position.copy(this.pos); this.obj.position.y += Math.sin(this.t * 2.1) * 0.12;
    this.obj.lookAt(_v3c.copy(this.obj.position).add(this.look));
    this.pupil.scale.setScalar(1 + this.sus * 0.8);
  }
}

/* ---------------- I. THE STAIR HALL: move, climb, jump a gap for the key, open the locked door ---------------- */
LEVELS[1] = {
  name: 'The Stair Hall', sub: 'find the blue key',
  titleView: t => ({ pos: [Math.sin(t * 0.05) * 19, 11 + Math.sin(t * 0.08) * 2, 1.5 + Math.cos(t * 0.05) * 19], look: [0, 2.5, 1.5] }),
  build(L) {
    const E = L.env; E.sunDir.set(-0.5, 0.8, 0.32); E.sun = 0.8; E.amb = 0.5; E.fogDen = 0.009; E.hatch = 8.5; L.killU = -20; L.surf = 'stone';
    E.bed = { root: 55, fifth: 1.5, cut: 260, noise: 0.05, noiseF: 600, gain: 0.42 };
    const WALL = { pat: PAT.BRICK, tone: 0.86 }, SLAB = { pat: PAT.ASHLAR, tone: 0.9 };
    L.B(-6.5, -0.5, -7.25, 6.5, 0, 10.25, { pat: PAT.CHECKER, tone: 0.92 });                  // floor
    wallX(L, -6.5, 6.5, -7.25, -6.75, 0, 8, [doorHole(0, 0)], WALL);                          // south wall, with the entrance
    stdEntrance(L, 0, 0, -7, 0);
    L.B(-7, -0.5, -7.25, -6.5, 8, 10.25, WALL); L.B(6.5, -0.5, -7.25, 7, 8, 10.25, WALL);      // west, east
    const st = stairs(L, -4.8, 0, -1.5, '+z', 14, { w: 2, rise: 0.22, run: 0.34, rails: true, railSides: [1] });
    wallX(L, -6.5, 6.5, 9.75, 10.25, 0, 8, [doorHole(-3.5, st.y)], WALL);                     // north wall, the exit is up on the gallery
    // two galleries with a gap between them; the key is across the gap
    L.B(-6.5, st.y - 0.5, st.z, -0.8, st.y, 9.75, SLAB);
    L.B(0.8, st.y - 0.5, st.z, 6.5, st.y, 9.75, SLAB);
    rail(L, -6.45, st.z + 0.05, -5.85, st.z + 0.05, st.y); rail(L, -3.75, st.z + 0.05, -0.85, st.z + 0.05, st.y); rail(L, 0.85, st.z + 0.05, 6.45, st.z + 0.05, st.y);
    for (const x of [-1.2, 1.2]) column(L, x, 0, st.z + 0.4, 0.28, st.y - 0.5);
    for (const z of [-4, 0.5]) arch(L, 6.3, 0, z, 'z', 2.2, 2.6, 0.4, { solid: false });
    exitDoor(L, -3.5, st.y, 10.0, 0, { locked: true, lockMsg: 'Locked. Something blue opens it.' });
    new Pickup(L, 'key', 4.6, st.y + 0.95, 7.2, { onGet: () => { L.exitDoor.locked = false; GAME.toast('The blue key. Somewhere, a lock gives.', 3); GAME.pulse = 0.6; } });
    L.B(2, 0, -4, 3, 0.75, -3, { pat: PAT.WOOD, tone: 0.6 });
    new Pickup(L, 'note', 2.5, 1.1, -3.5, { text: 'Every door here opens one way. Blue means real.' });
    L.trigger(-2.6, st.y, st.z, -0.8, st.y + 3, 9.75, () => GAME.hint('jump'));
    textPlane(L, -3.5, 6.3, 9.75, 0, -1, 2.6, 0.7, scrawl('THE WAY ON', 90));
    lampVis(L, 0, 6.2, 1.5, 'bulb'); L.light(0, 6.2, 1.5, 12, 0.3, { flicker: 0.05 });
    scatterDeco(L, 9, 15, 28, 4, 20, ['stairs', 'arch', 'column', 'block'], 7, new V3(0, 0, 1.5));
  }
};

/* ---------------- II. THE TURNED ROOM: slip past the watcher, walk through the arch, the north wall becomes the floor ---------------- */
const FLOOR2 = face([0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]);
const NORTH2 = face([0, 0, 6], [1, 0, 0], [0, 0, -1], [0, 1, 0]); // y = height off the wall, z runs up the wall
LEVELS[2] = {
  name: 'The Turned Room', sub: 'down is a suggestion',
  build(L) {
    const E = L.env; E.sun = 0; E.amb = 0.64; E.fogDen = 0.012; E.hatch = 9; L.killU = -1e9; L.surf = 'wood';
    E.bed = { root: 52, fifth: 1.414, cut: 240, gain: 0.4 }; E.mood.boil = 0.12; E.mood.tendril = 0.22;
    L.B(-6.5, -0.5, -6.5, 6.5, 0, 6.5, { pat: PAT.BLOCKS, tone: 0.95 });                     // floor
    L.B(-6.5, 12, -6.5, 6.5, 12.5, 6.5, { pat: PAT.WOOD, tone: 0.86 });                      // ceiling
    wallX(L, -6.5, 6.5, -6.5, -6, 0, 12, [doorHole(0, 0)], { pat: PAT.BRICK, tone: 0.86 });  // south, with the entrance
    stdEntrance(L, 0, 0, -6.25, 0);
    L.B(-6.5, 0, 6, 6.5, 12, 6.5, { pat: PAT.ASHLAR, tone: 0.9 });                           // north: you will walk on it
    L.B(-6.5, 0, -6, -6, 12, 6, { pat: PAT.DAMASK, tone: 0.9 }); L.B(6, 0, -6, 6.5, 12, 6, { pat: PAT.DAMASK, tone: 0.9 });
    // the floor: furniture to hide behind, and a watcher
    L.B(-4.6, 0, -2.4, -2.6, 0.95, -1.4, { pat: PAT.WOOD, tone: 0.6 }); L.B(2.4, 0, 0.6, 3.6, 1.4, 1.6, { pat: PAT.BOOKS, tone: 0.8 });
    L.ent(new Blot(L, [[-4, 1.4, -0.4], [4, 1.4, -0.4], [4, 1.4, 3.0], [-4, 1.4, 3.0]], { speed: 1.2 }));
    L.trigger(-6, 0, -4.4, 6, 3, -3.2, () => GAME.hint('crouch'));
    // the arch: walk through it and the north wall is the floor
    blueArch(L, new V3(0, 1.2, 4.7), new Q4());
    L.gravZones.push({ from: FLOOR2, to: NORTH2, box: [-1.3, 0, 4.4, 1.3, 2.6, 5.1], place: p => new V3(clamp(p.x, -1, 1), 1.0, 6) });
    L.trigger(-3, 0, 2.6, 3, 3, 4.3, () => GAME.hint('arch'));
    // on the north wall, built in that wall's own coordinates
    const N = NORTH2, DW = { pat: PAT.BRICK, tone: 0.86 };
    fB(L, N, -6, 0, 7.75, -0.68, 5, 8.25, DW); fB(L, N, 0.68, 0, 7.75, 6, 5, 8.25, DW); fB(L, N, -0.68, 2.44, 7.75, 0.68, 5, 8.25, DW);
    exitDoor(L, ...fW(N, 0, 0, 8).toArray(), 0, { upQ: faceQ(N) });
    fB(L, N, -2, 0, 2.2, 2, 0.04, 7.4, { pat: PAT.CARPET, tone: 0.5, solid: false });
    fB(L, N, -5.8, 0, 3.5, -5.1, 2.6, 7.2, { pat: PAT.BOOKS, tone: 0.85 });
    fB(L, N, 3, 0, 3.2, 4.6, 0.8, 4.4, { pat: PAT.WOOD, tone: 0.6 });
    const lp = fW(N, 0, 4.2, 5); lampVis(L, lp.x, lp.y, lp.z, 'bulb'); L.light(lp.x, lp.y, lp.z, 9, 0.3);
    // a third floor nobody uses: the ceiling, and stairs lying on the west wall
    L.B(-1, 11.2, -1, 1, 12, 1, { pat: PAT.WOOD, tone: 0.6, solid: false });
    decoChunk(L, new M4().makeTranslation(-6, 4.5, -2).multiply(new M4().makeRotationZ(-Math.PI / 2)), 'stairs', 0.9);
    lampVis(L, 0, 9, -1, 'bulb'); L.light(0, 9, -1, 14, 0.35);
  }
};

/* ---------------- III. THE MARGIN: the end. A door standing alone on blank paper ---------------- */
LEVELS[3] = {
  name: 'The Margin', sub: 'where the drawing stops',
  build(L) {
    const E = L.env; E.sunDir.set(0.3, 0.9, -0.2); E.sun = 0.45; E.amb = 0.85; E.fogDen = 0.035; E.hatch = 7; L.killU = -20;
    E.bed = { root: 65.4, fifth: 1.5, cut: 520, gain: 0.25 }; E.mood.boil = 0.03; E.mood.tendril = 0;
    L.B(-40, -0.5, -40, 40, 0, 40, { pat: PAT.PAPER, tone: 1, edges: false });
    stdEntrance(L, 0, 0, 0, 0);
    const tex = canvasTex(1024, 256, scrawl('YOU WALKED OUT\nOF THE DRAWING', 96));
    const m = new THREE.Mesh(new THREE.PlaneGeometry(8, 2), new THREE.MeshBasicMaterial({ map: tex, transparent: true }));
    m.material.userData.own = true; m.rotation.set(-Math.PI / 2, 0, Math.PI); // lie flat, reading away from the door
    m.position.set(0, 0.02, 7.5); L.add(m);
    scatterDeco(L, 6, 12, 30, 2, 14, ['stairs', 'arch', 'column'], 3);
  },
  update(L) {
    if (L.t > 3 && !L.data.thanks) { L.data.thanks = 1; GAME.toast('Thank you for playing.', 4); }
    if (L.t > 8 && !L.data.out) { L.data.out = 1; GAME.fadeTo(1, 2.5); }
    if (L.t > 11) GAME.toTitle();
  }
};
````

### `assets/starter/src/06_game.js`

<!-- bundle-file: assets/starter/src/06_game.js sha256=0984465380756606c9708f836f25a1a3a126e097803373f552e7c25b1a3c29d3 -->
````javascript
/* ===================== game: states, level streaming through portal doors, interaction, mood, UI =====================
   States: title -> play <-> pause, play -> caught -> play. One level is live (GAME.L); the next one is built in the
   background (GAME.next) and linked to the exit door, so opening it shows the next level through the doorway. */
let CAM = null;
const roman = n => { let s = ''; for (const [k, r] of [[10, 'X'], [9, 'IX'], [5, 'V'], [4, 'IV'], [1, 'I']]) while (n >= k) { s += r; n -= k; } return s; };
// one-time tutorial lines, worded for the device the player is actually using
const HINTS = {
  move: { kb: 'WASD to move, the mouse to look. Click to capture the mouse.', touch: 'Left thumb moves. Drag on the right to look.', pad: 'Left stick moves, right stick looks.' },
  jump: { kb: 'Space jumps. Shift runs.', touch: 'The jump button jumps. Push the stick all the way to run.', pad: 'A jumps. Click the left stick to run.' },
  open: { kb: 'E opens doors.', touch: 'The open button opens doors.', pad: 'X opens doors.' },
  crouch: { kb: 'Something watches the floor. C crouches; it sees less of you.', touch: 'Something watches the floor. Duck, and it sees less of you.', pad: 'Something watches the floor. B crouches.' },
  arch: { all: 'Walk through the blue arch. Down will change.' }
};
const GAME = {
  state: 'boot', time: 0, L: null, next: null, idx: 1, reverse: null, shown: new Set(), threat: 0, threatS: 0, pulse: 0, portalDoor: null,
  init() { CAM = new THREE.PerspectiveCamera(SET.fov, innerWidth / innerHeight, 0.05, 900); window.CAM = CAM; this.titleLevel(); },
  nextIdx(i) { const d = LEVELS[i]; if (d && d.next !== undefined) return d.next; return LEVELS[i + 1] ? i + 1 : null; },
  buildLevel(i) {
    const def = LEVELS[i]; seedRng(i * 7919 + 13); // the same level always builds the same way
    const L = new Level(i, def.name); L.def = def; def.build(L);
    L.finalize(); R.bakeShadow(L); return L;
  },
  disposeLevel(L) { if (L && !L.disposed) L.dispose(); },
  disposeAll() { for (const l of [this.L, this.next, this.reverse && this.reverse.old]) this.disposeLevel(l); this.L = this.next = this.reverse = null; this.portalDoor = null; },
  /* ---------- flow ---------- */
  titleLevel() {
    this.state = 'title'; this.disposeAll(); this.idx = 1; this.L = this.buildLevel(1); this.titleT = 0;
    this.spawnAt(this.L); POST.uFade.value = 1; UI.show('title'); UI.hud(false);
    if (AU.ok) { AU.bed(this.L.env.bed); AU.melody(true); }
  },
  newRun(startIdx = 1) { this.shown = new Set(); this.playLevel(startIdx); },
  playLevel(i) {
    AU.melody(false); this.disposeAll(); this.idx = i; this.L = this.buildLevel(i); this.spawnAt(this.L);
    const ent = this.L.entrance; if (ent) { ent.angle = ent.target = 0; ent.locked = true; ent.update(0); }
    this.startLevel(this.L, false);
  },
  spawnAt(L) { const sp = L.spawn || { pos: new V3(), yaw: 0 }; PL.reset(L, sp.pos, sp.yaw); if (sp.q) PL.setFrameQ(sp.q); PL.frozen = false; },
  startLevel(L, viaPortal) {
    this.state = 'play'; this.lvlTime = 0; L.started = true;
    UI.show(null); UI.hud(true);
    if (AU.ok) AU.bed(L.env.bed);
    this.toast(`${roman(L.idx)}. ${L.def.name}` + (L.def.sub ? `\n${L.def.sub}` : ''), 2.6);
    this.fadeTo(0, viaPortal ? 0 : 0.8);
    if (L.def.onStart) L.def.onStart(L, viaPortal);
    this.moveHintT = L.idx === 1 && !viaPortal ? 2.6 : null; // counted in game time (pauses, and exact in tests)
    this.needNext = this.nextIdx(L.idx) != null && L.exitDoor ? (viaPortal ? 1.6 : 0.4) : -1;
  },
  linkNext() { // the exit door of this level now looks into the entrance of the next
    const L = this.L, n = this.next; if (!L || !n || !L.exitDoor || !n.entrance) return;
    const e = L.exitDoor; e.portal = { level: n, M: new M4().multiplyMatrices(n.entrance.F, e.Finv), plane: n.entrance.plane, hideLeaf: n.entrance.pivot, dir: 1 };
    n.entrance.angle = n.entrance.target = 0; n.entrance.update(0);
  },
  crossPortal(door) { // the camera passed through an open exit door: carry the player (and gravity) across
    const P = door.portal, M = P.M, qM = new Q4().setFromRotationMatrix(M);
    PL.pos.applyMatrix4(M); PL.vel.applyQuaternion(qM); PL.eyeOff.applyQuaternion(qM);
    PL.setFrameQ(qM.clone().multiply(PL.qGto)); PL.safe = [];
    CAM.position.applyMatrix4(M); CAM.quaternion.premultiply(qM);
    const old = this.L, nl = P.level;
    this.L = nl; this.next = null; this.idx = nl.idx;
    const ent = nl.entrance;
    ent.angle = ent.target = ent.swingIn ? -1.62 : 1.62; ent.locked = true; ent.update(0);
    // look back and you see where you came from, until the entrance slams behind you
    ent.portal = { level: old, M: new M4().copy(M).invert(), plane: new THREE.Plane().setFromNormalAndCoplanarPoint(door.fwd.clone().negate(), door.pos), hideLeaf: door.pivot, dir: -1, reverse: true };
    if (ent.block) ent.block.on = true;
    this.reverse = { ent, old, t: 0 };
    this.startLevel(nl, true);
  },
  toTitle() { UI.hud(false); AU.resume(); this.titleLevel(); },
  /* ---------- per frame ---------- */
  update(dt) {
    this.time += dt; U.uTime.value = this.time;
    if (this.state === 'title') return this.updateTitle(dt);
    if (this.state === 'caught') { this.caughtT -= dt; this.updateFx(dt); if (this.caughtT <= 0) this.respawn(); return; }
    if (this.state !== 'play') return;
    const L = this.L; if (!L) return;
    this.lvlTime += dt; L.t += dt; this.threat = 0;
    if (this.needNext > 0) { this.needNext -= dt; if (this.needNext <= 0) { if (this.reverse) this.needNext = 0.2; else { this.next = this.buildLevel(this.nextIdx(L.idx)); this.linkNext(); } } }
    if (this.reverse) {
      const r = this.reverse; r.t += dt;
      if (!r.closing && (r.t > 1.1 || PL.pos.distanceTo(r.ent.pos) > 2.4)) {
        r.closing = true; r.ent.slamWhenClear();
        r.ent.onSlam = () => { r.ent.portal = null; if (r.ent.block) r.ent.block.on = false; r.ent.onSlam = null; r.done = true; };
      }
      if (r.done) { this.disposeLevel(r.old); this.reverse = null; }
    }
    if (this.moveHintT != null && (this.moveHintT -= dt) <= 0) { this.moveHintT = null; this.hint('move'); }
    if (IN.take('pause')) return this.pause();
    if (IN.take('lamp')) { PL.lampOn = !PL.lampOn; AU.click(); }
    PL.lampI = damp(PL.lampI, PL.lampOn ? 1 : 0, 12, dt);
    PL.look(dt);
    for (const e of L.ents) if (e.alive !== false && e.update) e.update(dt);
    PL.physics(L, dt);
    for (const d of L.doors) d.update(dt);
    for (const p of L.pickups) p.update(dt);
    for (const pl of L.plights) if (pl.flicker) pl.flick = 1 - pl.flicker * (Math.random() < 0.08 ? Math.random() : 0) * (0.5 + 0.5 * Math.sin(this.time * 23 + pl.phase));
    this.updateTriggers(L); this.updateGravZones(L);
    if (L.def.update) L.def.update(L, dt);
    if (this.L !== L || this.state !== 'play') return; // the level's update may have ended the level
    PL.camera(CAM, dt);
    this.portalCheck(L);
    this.updateInteract(L);
    this.updateFx(dt);
  },
  updateTitle(dt) {
    this.titleT += dt; const L = this.L;
    const v = L.def.titleView ? L.def.titleView(this.titleT) : (() => { const c = L.bounds.getCenter(new V3()), t = this.titleT * 0.05; return { pos: [c.x + Math.sin(t) * 18, c.y + 8, c.z + Math.cos(t) * 18], look: [c.x, c.y, c.z] }; })();
    CAM.position.set(...v.pos); CAM.lookAt(...v.look);
    U.uBoil.value = 0.22; U.uWarp.value = 0.05; POST.uTendril.value = 0.3; POST.uDouble.value = POST.uSwirl.value = POST.uWave.value = POST.uTunnel.value = POST.uChrom.value = 0;
    POST.uFade.value = Math.max(0, POST.uFade.value - dt * 0.6); POST.uFlash.value = 0; POST.uInvert.value = 0;
    for (const d of L.doors) d.update(dt);
  },
  updateTriggers(L) {
    const c = PL.center;
    for (const t of L.triggers) {
      if (t.done) continue;
      const inside = c.x > t.min[0] && c.x < t.max[0] && c.y > t.min[1] && c.y < t.max[1] && c.z > t.min[2] && c.z < t.max[2];
      if (inside && !t.inside) { t.fn(); if (t.once) t.done = true; }
      t.inside = inside;
    }
  },
  updateGravZones(L) { // { from: face, to: face, box: [x0,y0,z0,x1,y1,z1], place: feet => new feet }
    if (PL.gravLock > 0) return; const c = PL.center;
    for (const z of L.gravZones) {
      if (!onFace(z.from)) continue; const b = z.box;
      if (c.x > b[0] && c.x < b[3] && c.y > b[1] && c.y < b[4] && c.z > b[2] && c.z < b[5]) { gravSwitch(z.to, z.place(PL.pos), z.axis); if (z.onSwitch) z.onSwitch(); break; }
    }
  },
  portalCheck(L) { // show the portal of the nearest visible open door, and cross it when the camera passes its plane
    let best = null, bd = 1e9; CAM.updateMatrixWorld();
    _frust.setFromProjectionMatrix(_m4a.multiplyMatrices(CAM.projectionMatrix, CAM.matrixWorldInverse));
    for (const d of L.doors) {
      const P = d.portal, show = !!P && (d.isOpen || !!P.reverse);
      d.aperture.visible = show;
      if (!show) { d.prevLocal = null; continue; }
      const lp = d.local(CAM.position, _v3c), dir = P.dir || 1;
      if (d.prevLocal && Math.abs(lp.x) < d.w / 2 + 0.05 && lp.y > -0.4 && lp.y < d.h + 0.4 && d.prevLocal.z * dir < 0 && lp.z * dir >= 0 && !P.reverse && d.isOpen) {
        d.prevLocal = null; this.crossPortal(d); return this.portalCheck(this.L);
      }
      d.prevLocal = (d.prevLocal || new V3()).copy(lp);
      const dist = d.pos.distanceTo(CAM.position);
      if (dist < 80 && _frust.intersectsObject(d.aperture) && dist < bd) { bd = dist; best = d; }
    }
    for (const d of L.doors) if (d !== best) d.aperture.visible = false; // one portal is rendered per frame: only its doorway shows it
    this.portalDoor = best;
  },
  updateInteract(L) {
    let best = null, bs = -1; const eye = CAM.position, fw = PL.forward(_v3b);
    const consider = (p, r, cos, label, fn, isDoor) => {
      const d = _v3a.copy(p).sub(eye), dist = d.length(); if (dist > r) return; d.normalize(); const c = d.dot(fw);
      if (c < cos) return; const score = c - dist * 0.02; if (score <= bs) return;
      if (this.los(eye, p, 0.3)) { bs = score; best = { label, fn, isDoor }; }
    };
    for (const d of L.doors) if (d.canInteract() && d.kind !== 'entrance') consider(d.interactPoint().clone(), 2.7, 0.84, d.prompt, () => d.tryOpen(), true);
    for (const d of L.doors) if (d.kind === 'entrance' && d.canInteract() && !d.portal) consider(d.interactPoint().clone(), 2.2, 0.9, 'Open', () => d.tryOpen(), true);
    for (const it of L.inter) if (it.on && (!it.when || it.when())) consider(it.pos, it.r, it.cos, it.prompt, it.fn);
    UI.prompt(best && best.label); if (best && best.isDoor) this.hint('open');
    if (IN.take('act') && best) { best.fn(); AU.click(); }
  },
  los(a, b, slack = 0.25) { const d = _v3d.copy(b).sub(a), len = d.length(); if (len < 0.01) return true; d.divideScalar(len); return this.L.ray(a, d, len) >= len - slack; },
  isSeen(p, maxD) { // is world point p on screen and unblocked?
    if (_v3d.copy(p).sub(CAM.position).length() > maxD) return false;
    _v3e.copy(p).project(CAM); if (_v3e.z > 1 || Math.abs(_v3e.x) > 1.05 || Math.abs(_v3e.y) > 1.05) return false;
    return this.los(CAM.position, p, 0.4);
  },
  /* ---------- mood: each level's env.mood, raised by threat (0..1, set each frame by enemies) and pulse (a decaying spike) ---------- */
  updateFx(dt) {
    const L = this.L; if (!L) return;
    const m = L.env.mood, calm = SET.calm ? 1 : 0;
    this.threatS = damp(this.threatS, this.threat, 3, dt); this.pulse = Math.max(0, this.pulse - dt * 0.8);
    const k = this.threatS, p = this.pulse;
    U.uBoil.value = clamp(m.boil + k * 0.55 + p * 0.6, 0, 1.3);
    U.uWarp.value = (m.warp + p * 0.4) * (calm ? 0.25 : 1);
    POST.uDouble.value = m.double + k * 0.35; POST.uSwirl.value = m.swirl + p * 0.3; POST.uWave.value = m.wave + p * 0.5;
    POST.uTendril.value = m.tendril + k * 0.65; POST.uTunnel.value = k * 0.3; POST.uChrom.value = (m.chrom + p * 0.5) * (calm ? 0 : 1);
    U.uCalm.value = calm;
    if (this.flashT > 0) { this.flashT -= dt; POST.uFlash.value = Math.max(0, this.flashA * this.flashT / this.flashD); } else POST.uFlash.value = 0;
    if (this.state === 'play' && this.fadeT == null) POST.uFade.value = damp(POST.uFade.value, 0, 3, dt);
    if (this.fadeT != null) { this.fadeT -= dt; const t = clamp(1 - this.fadeT / this.fadeD, 0, 1); POST.uFade.value = lerp(this.fadeFrom, this.fadeTarget, t); if (this.fadeT <= 0) this.fadeT = null; }
    CAM.fov = damp(CAM.fov, SET.fov + (PL.sprinting ? 6 : 0), 6, dt); CAM.updateProjectionMatrix();
  },
  /* ---------- events ---------- */
  onPickup(p) { if (p.kind === 'note' && p.o.text) this.toast(p.o.text, 6); },
  caught(by) { // an enemy got you: ink flash, then back to the level's start
    if (this.state !== 'play') return; this.state = 'caught'; this.caughtT = 1.3;
    AU.shriek(by && by.pos); this.flash(0.6, 0); this.shake(0.6); this.fadeTo(1, 1.1); PL.frozen = true; UI.prompt(null);
  },
  respawn() {
    const L = this.L; this.state = 'play'; this.spawnAt(L);
    for (const e of L.ents) if (e.reset) e.reset();
    this.fadeTo(0, 0.6); this.toast('Again.', 1.4);
  },
  voidFall() { // fell off the world: back to a recent safe spot
    if (this.voidT) return; this.voidT = 1; AU.whoosh(null, 0.4); this.fadeTo(1, 0.25);
    setTimeout(() => { if (this.L && this.state === 'play' && !PL.respawnSafe(4)) this.spawnAt(this.L); this.fadeTo(0, 0.5); this.voidT = 0; }, 260);
  },
  pause() {
    if (this.state !== 'play') return; this.state = 'pause'; this.ignoreUnlock = true;
    if (document.exitPointerLock) try { document.exitPointerLock(); } catch (e) { }
    setTimeout(() => this.ignoreUnlock = false, 200); UI.show('pause'); if (AU.ctx) try { AU.ctx.suspend(); } catch (e) { }
  },
  resume() { this.state = 'play'; UI.show(null); IN.clearEdges(); if (AU.ctx) AU.resume(); if (!IS_TOUCH_ONLY()) IN.requestLock(); },
  /* ---------- feedback ---------- */
  shake(a) { PL.trauma = Math.min(1, PL.trauma + a); },
  flash(a, tone) { this.flashA = a; this.flashD = 0.35; this.flashT = 0.35; POST.uFlashTone.value = tone; }, // tone 0 = ink, 1 = paper
  fadeTo(target, dur) { this.fadeFrom = POST.uFade.value; this.fadeTarget = target; this.fadeD = Math.max(0.001, dur); this.fadeT = dur; if (!dur) { POST.uFade.value = target; this.fadeT = null; } },
  toast(msg, dur = 2.2) { UI.toast(msg, dur); },
  hint(k) {
    if (this.shown.has(k)) return; this.shown.add(k); const h = HINTS[k]; if (!h) return;
    const dev = IN.lastDevice === 'touch' ? 'touch' : IN.lastDevice === 'pad' ? 'pad' : 'kb';
    this.toast(h.all || h[dev] || h.kb, 4.2);
  },
  render() {
    if (!this.L) return;
    CAM.updateMatrixWorld();
    const pd = this.state === 'title' ? null : this.portalDoor;
    R.render(this.L, CAM, pd ? pd.portal : null);
  }
};
const _frust = new THREE.Frustum(), _v3d = new V3(), _v3e = new V3();

/* ===================== UI: the screens live in 00_head.html; this only shows, hides and fills them ===================== */
const UI = {
  init() {
    $('bBegin').addEventListener('click', () => { AU.init(); AU.resume(); GAME.newRun(1); if (!IS_TOUCH_ONLY()) IN.requestLock(); });
    $('bResume').addEventListener('click', () => GAME.resume());
  },
  show(id) { for (const s of document.querySelectorAll('.screen')) s.classList.toggle('show', s.id === id); $('touch').classList.toggle('show', !id && $('hud').classList.contains('show') && IN.usedTouch); },
  hud(on) { $('hud').classList.toggle('show', on); $('touch').classList.toggle('show', on && IN.usedTouch); },
  toast(msg, dur) { const t = $('toast'); t.textContent = msg; t.classList.add('show'); clearTimeout(this._tt); this._tt = setTimeout(() => t.classList.remove('show'), dur * 1000); },
  prompt(label) { if (label === this._pl) return; this._pl = label; const p = $('prompt'); p.textContent = label || ''; p.classList.toggle('show', !!label); },
  onKey(e) { if (GAME.state === 'pause' && (e.code === 'Escape' || e.code === 'KeyP')) GAME.resume(); },
  onPad(a) {
    if (GAME.state === 'pause' && (a === 'pause' || a === 'jump')) GAME.resume();
    else if (GAME.state === 'title' && (a === 'jump' || a === 'act')) $('bBegin').click();
  }
};
````

### `assets/starter/src/07_main.js`

<!-- bundle-file: assets/starter/src/07_main.js sha256=76540a8042f4dcd93805389746aa91676b6200815adc7c9666f2b1afff2fa582 -->
````javascript
/* ===================== boot, frame loop, test hooks ===================== */
const ERRS = [];
function oops(e) { const m = String(e && (e.stack || e.message) || e); if (ERRS.includes(m)) return; ERRS.push(m); console.error(e); }
function boot() {
  try { R.init($('gl')); }
  catch (e) { $('loading').innerHTML = '<div style="max-width:30ch;text-align:center;font:20px/1.4 var(--fell)">This game needs WebGL. Try another browser, or turn on hardware acceleration.</div>'; return; }
  initMats(); IN.init($('gl')); UI.init(); GAME.init();
  addEventListener('resize', () => R.resize());
  // browsers only allow sound after a gesture: start it on the first one
  const startAudio = () => { AU.init(); AU.resume(); if (GAME.state === 'title' && !AU._titleOn) { AU._titleOn = 1; AU.bed(GAME.L.env.bed); AU.melody(true); } };
  addEventListener('pointerdown', startAudio); addEventListener('keydown', startAudio); addEventListener('touchstart', startAudio, { passive: true });
  document.addEventListener('visibilitychange', () => { if (document.hidden && GAME.state === 'play') GAME.pause(); });
  let last = performance.now();
  const frame = t => {
    requestAnimationFrame(frame);
    const dt = clamp((t - last) / 1000, 0, 0.05); last = t; // a long hitch never becomes one giant physics step
    try { IN.pollPad(); } catch (e) { IN.gpOK = false; }
    try { GAME.update(dt); } catch (e) { oops(e); }
    try { GAME.render(); } catch (e) { oops(e); }
  };
  requestAnimationFrame(frame);
  setTimeout(() => { const l = $('loading'); if (!l) return; l.style.transition = 'opacity .8s'; l.style.opacity = 0; setTimeout(() => l.remove(), 900); }, 250);
  // test hooks: scripts/shoot.py and the smoke test drive the game through these (stub requestAnimationFrame, then step())
  window.__game = {
    GAME, PL, R, U, POST, LEVELS, IN, SET, UI, AU, ERRS, V3, Q4, M4, faceQ, CAM: () => CAM,
    play(i = 1) { GAME.newRun(i); return GAME.idx; },
    step(n = 1, dt = 1 / 30, render = true) { for (let k = 0; k < n; k++) GAME.update(dt); if (render) GAME.render(); return this.state(); },
    tp(x, y, z) { PL.pos.set(x, y, z); PL.vel.set(0, 0, 0); },
    look(yaw, pitch = 0) { PL.yaw = yaw; PL.pitch = pitch; },
    hold(code, on = true) { IN.keys[code] = on; },                 // held keys: KeyW/A/S/D, ShiftLeft
    press(action) { IN.edge(action); },                             // one press: 'jump', 'act', 'crouch', 'lamp', 'pause'
    openExit() { const d = GAME.L.exitDoor; if (!d) return 'no exit'; d.locked = false; if (GAME.next) GAME.linkNext(); d.open(true); d.angle = d.target; d.update(0); return GAME.next ? 'open, next linked' : 'open, next not built yet'; },
    faceExit(back = 0.8) { // stand in front of the exit door, looking through it
      const d = GAME.L.exitDoor; PL.setFrameQ(d.upQ ? d.upQ.clone() : new Q4());
      PL.pos.copy(d.pos).addScaledVector(d.fwd, -back); PL.vel.set(0, 0, 0);
      const fl = d.fwd.clone().applyQuaternion(PL.qGto.clone().invert()); PL.yaw = Math.atan2(-fl.x, -fl.z); PL.pitch = 0; return 'placed';
    },
    state() {
      return { state: GAME.state, idx: GAME.idx, level: GAME.L && GAME.L.name, pos: PL.pos.toArray().map(v => +v.toFixed(2)), up: PL.up.toArray().map(v => Math.round(v)),
        grounded: PL.grounded, next: !!GAME.next, portal: !!GAME.portalDoor, errs: ERRS.slice(0, 5) };
    }
  };
}
// wait briefly for the embedded typefaces, so text drawn onto canvases uses them from the first frame
{
  let booted = false; const go = () => { if (booted) return; booted = true; boot(); };
  try { Promise.all(['24px "IM Fell English"', 'italic 24px "IM Fell English"', '24px "IM Fell English SC"', '24px "Special Elite"'].map(f => document.fonts.load(f))).then(go, go); } catch (e) { go(); }
  setTimeout(go, 1500);
}
````

### `scripts/_pen_ink_common.py`

<!-- bundle-file: scripts/_pen_ink_common.py sha256=7122226bae8726f7521506faf8d2bab012d28ced38f758515d964fa05a8ad580 -->
````python
"""Shared helpers for the pen-and-ink-game-builder scripts (imported from the scripts' own folder)."""
import sys
sys.dont_write_bytecode = True
import os

GL_ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']


def open_game(p, html, w, h, quality=1):
    b = p.chromium.launch(headless=True, args=GL_ARGS)
    pg = b.new_page(viewport={'width': w, 'height': h})
    pg.set_default_timeout(180000)
    errs = []
    pg.on('pageerror', lambda e: errs.append('pageerror: ' + str(e)))
    pg.on('console', lambda m: m.type == 'error' and errs.append('console: ' + m.text[:400]))
    # no animation loop: the script steps the game itself, so every run renders the same frames
    pg.add_init_script('window.requestAnimationFrame = () => 0;')
    pg.add_init_script(f"try {{ for (const k in localStorage) if (k.endsWith('_set')) localStorage.removeItem(k); }} catch (e) {{}}")
    pg.goto('file://' + os.path.abspath(html))
    pg.wait_for_function('window.__game', polling=200, timeout=60000)
    pg.evaluate(f'() => {{ const g = window.__game; g.SET.quality = {quality}; g.R.applyQuality(); }}')
    pg.wait_for_function('!document.getElementById("loading")', polling=200, timeout=10000)  # the cover fades out after ~1 s
    return b, pg, errs


END = '\n})();\n</script>\n</body>\n</html>\n'
HOOK = '\nwindow.__ev = s => eval(s); // promo build only'


def promo_copy(html):
    s = open(html, encoding='utf-8').read()
    if 'window.__ev' in s:
        return html
    if not s.endswith(END):
        raise SystemExit('this html was not made by build_html.py; rebuild it with: build_html.py <game> --promo')
    import tempfile  # keep the eval hook out of dist/, the folder you ship
    out = os.path.join(tempfile.gettempdir(), os.path.basename(html)[:-5] + '-promo.html')
    open(out, 'w', encoding='utf-8').write(s[:-len(END)] + HOOK + END)
    return out
````

### `scripts/build_html.py`

<!-- bundle-file: scripts/build_html.py sha256=517428e725e4e7d3eec203293d4c883c8baed374328da78480709c4ca61b1a96 -->
````python
#!/usr/bin/env python3
"""Build a pen-and-ink game into ONE self-contained HTML file (three.js, fonts and all code inlined; no network needed).

  python3 build_html.py path/to/my-game              -> path/to/my-game/dist/<slug>.html
  python3 build_html.py path/to/my-game --promo      -> dist/<slug>-promo.html (adds window.__ev for trailer tools)

Order: src/00_head.html, then every src/*.js in name order, wrapped in one function scope (so nothing leaks onto
window except what the code puts there on purpose). The JS is syntax-checked with `node --check` when node exists,
which catches a missing bracket before a browser ever loads the page.
"""
import sys
sys.dont_write_bytecode = True
import argparse, base64, json, os, shutil, subprocess, tempfile

FONTS = [('IM Fell English', 'normal', 'im-fell-english-latin-400-normal.woff2'),
         ('IM Fell English', 'italic', 'im-fell-english-latin-400-italic.woff2'),
         ('IM Fell English SC', 'normal', 'im-fell-english-sc-latin-400-normal.woff2'),
         ('Special Elite', 'normal', 'special-elite-latin-400-normal.woff2')]
END = '\n})();\n</script>\n</body>\n</html>\n'   # film_shots.py looks for this exact ending to add its hook


def slug_of(game):
    p = os.path.join(game, 'game.json')
    if os.path.exists(p):
        return json.load(open(p)).get('slug') or os.path.basename(os.path.abspath(game))
    return os.path.basename(os.path.abspath(game))


def build(game, out=None, promo=False, check=True):
    src = os.path.join(game, 'src')
    head = open(os.path.join(src, '00_head.html'), encoding='utf-8').read()
    warn = []
    css = ''
    for fam, sty, fn in FONTS:
        p = os.path.join(game, 'vendor', 'fonts', fn)
        if os.path.exists(p):
            css += '@font-face{font-family:"%s";font-style:%s;font-weight:400;font-display:swap;src:url(data:font/woff2;base64,%s) format("woff2")}\n' % (
                fam, sty, base64.b64encode(open(p, 'rb').read()).decode())
        else:
            warn.append(f'font missing ({fn}): the page falls back to Georgia/Courier. Run get_deps.py.')
    head = head.replace('<!--FONTS-->', '<style id="fonts">\n' + css + '</style>')
    tp = os.path.join(game, 'vendor', 'three.min.js')
    if not os.path.exists(tp):
        raise SystemExit(f'{tp} is missing. Run: python3 scripts/get_deps.py {game}')
    three = open(tp, encoding='utf-8').read()
    js = ''
    for f in sorted(os.listdir(src)):
        if f.endswith('.js'):
            js += f'\n/* ---- {f} ---- */\n' + open(os.path.join(src, f), encoding='utf-8').read()
    if check and shutil.which('node'):
        with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t:
            t.write('(function(){\n' + js + '\n})();\n'); tmp = t.name
        r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)
        os.unlink(tmp)
        if r.returncode:
            msg = r.stderr.strip().replace(tmp, '<game js>')
            raise SystemExit('syntax error in the game code (line numbers count from the first src/*.js file, +1):\n' + msg)
    hook = '\nwindow.__ev = s => eval(s); // promo build only: lets trailer scripts run inside the game scope' if promo else ''
    html = head + '<script>\n' + three + '\n</script>\n<script>\n(function(){\n' + js + hook + END
    slug = slug_of(game)
    out = out or os.path.join(game, 'dist', f'{slug}-promo.html' if promo else f'{slug}.html')
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    open(out, 'w', encoding='utf-8').write(html)
    return out, len(html.encode('utf-8')), warn


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('game_dir')
    ap.add_argument('-o', '--out', help='output file (default: <game>/dist/<slug>.html)')
    ap.add_argument('--promo', action='store_true', help='add the window.__ev hook used by film_shots.py and render_audio.py')
    ap.add_argument('--no-check', action='store_true', help='skip the node syntax check')
    a = ap.parse_args()
    out, size, warn = build(a.game_dir, a.out, a.promo, not a.no_check)
    for w in warn:
        print('warning: ' + w, file=sys.stderr)
    print(f'built {out}  {size / 1e6:.2f} MB', file=sys.stderr)


if __name__ == '__main__':
    main()
````

### `scripts/film_shots.py`

<!-- bundle-file: scripts/film_shots.py sha256=d61c8be083288ce325c41fa7c2b89229b6c3c87189bb53e57e7362f965294cd4 -->
````python
#!/usr/bin/env python3
"""Film trailer shots from inside the game: one MP4 per shot, rendered frame by frame (no dropped frames, ever).

  python3 film_shots.py dist/my-game.html promo/director.js                 -> promo/shots/<shot>.mp4 + <shot>.json
  python3 film_shots.py dist/my-game.html promo/director.js --stills        -> first/middle/last frame of each shot as JPEG
  python3 film_shots.py dist/my-game.html promo/director.js --only s03-door,s04-turn --size 1280x720

The director file defines window.__tr (start from assets/promo/director_template.js). It runs inside the game's
scope through window.__ev, which a promo build has; if the html lacks it, a <slug>-promo.html copy with the hook is
written next to it. Frames are JPEG q92 screenshots piped into ffmpeg (libx264 crf 18, 30 fps, yuv420p); each shot is
written to a .part.mp4 first and renamed only when ffmpeg succeeds, so a half-rendered shot never looks finished.
<shot>.json holds per-frame player facts (position, up, grounded) for render_audio.py to time footsteps and flips.
Rendering is software WebGL: expect roughly 1-4 frames per second at 1080p.
"""
import sys
sys.dont_write_bytecode = True
import argparse, json, os, subprocess, time
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pen_ink_common import GL_ARGS, promo_copy

ENC = ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', '30', '-video_track_timescale', '15360']


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('html'); ap.add_argument('director')
    ap.add_argument('--out', help='folder for the shot files (default: shots/ next to the director file)')
    ap.add_argument('--size', default='1920x1080')
    ap.add_argument('--only', help='comma-separated shot names to (re)render')
    ap.add_argument('--stills', action='store_true', help='only save first/middle/last frames as JPEG (fast check)')
    a = ap.parse_args()
    W, H = map(int, a.size.lower().split('x'))
    out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.director)), 'shots')
    os.makedirs(out, exist_ok=True)
    page = promo_copy(a.html)
    only = set(a.only.split(',')) if a.only else None
    T0 = time.time()
    log = lambda *m: print('%7.1fs' % (time.time() - T0), *m, file=sys.stderr, flush=True)
    errs = []
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, args=GL_ARGS)
        pg = b.new_page(viewport={'width': W, 'height': H}); pg.set_default_timeout(600000)
        pg.on('pageerror', lambda e: errs.append(str(e)) or log('PAGE ERROR', e))
        pg.on('console', lambda m: m.type == 'error' and (errs.append(m.text) or log('CONSOLE', m.text[:300])))
        pg.add_init_script('window.requestAnimationFrame = () => 0;')
        pg.goto('file://' + os.path.abspath(page))
        pg.wait_for_function('window.__ev && window.__game', polling=200, timeout=60000)
        pg.wait_for_timeout(1500)  # fonts and the loading cover
        pg.evaluate('s => __ev(s)', open(a.director, encoding='utf-8').read())
        names = pg.evaluate('__tr.names()')
        timeline, start = [], 0.0
        for si, nm in enumerate(names):
            name, n = nm.rsplit(':', 1); n = int(n)
            timeline.append({'name': name, 'frames': n, 'start': round(start, 3)}); start += n / 30
            if only and name not in only:
                continue
            pg.evaluate(f'__tr.prep({si})')
            if a.stills:
                keep = {0, n // 2, n - 1}
                for i in range(n):
                    pg.evaluate(f'__tr.noRender = {str(i not in keep).lower()}; __tr.frame({si},{i})')
                    if i in keep:
                        pg.screenshot(path=os.path.join(out, f'{name}-{i:03d}.jpg'), type='jpeg', quality=90)
                pg.evaluate('__tr.noRender = false')
                log(name, 'stills'); continue
            part, final = os.path.join(out, f'{name}.part.mp4'), os.path.join(out, f'{name}.mp4')
            ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'image2pipe', '-framerate', '30', '-c:v', 'mjpeg', '-i', '-'] + ENC + [part], stdin=subprocess.PIPE)
            info = []
            for i in range(n):
                pg.evaluate(f'__tr.frame({si},{i})')
                ff.stdin.write(pg.screenshot(type='jpeg', quality=92))
                info.append(json.loads(pg.evaluate('__tr.info()')))
                if i % 30 == 0: log('  ', name, f'{i}/{n}')
            ff.stdin.close(); rc = ff.wait()
            if rc == 0: os.replace(part, final)
            json.dump(info, open(os.path.join(out, f'{name}.json'), 'w'))
            log(name, f'{n} frames', 'ok' if rc == 0 else f'ffmpeg failed ({rc})')
        b.close()
    json.dump(timeline, open(os.path.join(out, 'shots.json'), 'w'), indent=1)
    log(f'shots in {out}; order and lengths in shots.json')
    if errs:
        print('ERRORS during filming:\n  ' + '\n  '.join(dict.fromkeys(errs)), file=sys.stderr); sys.exit(1)


if __name__ == '__main__':
    main()
````

### `scripts/finish_trailer.py`

<!-- bundle-file: scripts/finish_trailer.py sha256=7150057691517ded68c585c9e4a3781be89ece285ddb6f7032139eeb2b18a643 -->
````python
#!/usr/bin/env python3
"""Join filmed shots into the finished trailer: picture, black gaps, loudness-normalised sound, plus store extras.

  python3 finish_trailer.py promo/shots --audio promo/mix.wav                 -> promo/trailer-1080p.mp4
  python3 finish_trailer.py promo/shots --edit promo/edit.json --audio promo/mix.wav --small \
          --gif s03-door:0.8:1.6 --thumb s03-door:40

  --edit    edit.json {"timeline": ["s01-title", {"black": 14}, "s02-hall", ...]} (default: shots.json order)
  --small   also a 1280x720 copy (smaller upload, for pages that embed video)
  --gif     shot:start_seconds:duration -> a looping GIF under 3 MB for store pages (640 px, 15 fps)
  --thumb   shot:frame -> a JPEG still at the shot's size (YouTube thumbnail base)

Shots are joined with the concat demuxer and stream copy (no re-encode: all shots share size, rate and encoder
settings). Sound is measured, then normalised to -14 LUFS integrated, -2 dBTP (two-pass loudnorm), AAC 192 kb/s.
"""
import sys
sys.dont_write_bytecode = True
import argparse, json, os, subprocess

ENC = ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', '30', '-video_track_timescale', '15360']


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: raise SystemExit('ffmpeg failed: ' + ' '.join(cmd[:6]) + '...\n' + r.stderr[-1500:])
    return r


def size_of(f):
    r = run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', f])
    w, h = r.stdout.strip().split(',')[:2]; return int(w), int(h)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('shots'); ap.add_argument('--edit'); ap.add_argument('--audio')
    ap.add_argument('-o', '--out', help='default: trailer-1080p.mp4 (or -<height>p) next to the shots folder')
    ap.add_argument('--small', action='store_true'); ap.add_argument('--gif'); ap.add_argument('--thumb')
    a = ap.parse_args()
    meta = [s['name'] for s in json.load(open(os.path.join(a.shots, 'shots.json')))]
    items = json.load(open(a.edit))['timeline'] if a.edit else meta
    first = next(i for i in items if not isinstance(i, dict))
    W, H = size_of(os.path.join(a.shots, f'{first}.mp4'))
    base = os.path.dirname(os.path.abspath(a.shots.rstrip('/')))
    out = a.out or os.path.join(base, f'trailer-{H}p.mp4')
    lst = os.path.join(a.shots, 'concat.txt')
    with open(lst, 'w') as f:
        for it in items:
            if isinstance(it, dict):
                n = int(it['black']); bf = os.path.join(a.shots, f'black-{n}-{W}x{H}.mp4')
                if not os.path.exists(bf):
                    run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', f'color=c=black:s={W}x{H}:r=30', '-frames:v', str(n)] + ENC + [bf + '.part.mp4'])
                    os.replace(bf + '.part.mp4', bf)
                f.write(f"file '{os.path.abspath(bf)}'\n")
            else:
                f.write(f"file '{os.path.abspath(os.path.join(a.shots, it + '.mp4'))}'\n")
    pic = os.path.join(a.shots, 'picture.mp4')
    run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', pic + '.part.mp4']); os.replace(pic + '.part.mp4', pic)
    if a.audio:
        r = run(['ffmpeg', '-hide_banner', '-i', a.audio, '-af', 'loudnorm=I=-14:TP=-2:LRA=11:print_format=json', '-f', 'null', '-'])
        j = json.loads(r.stderr[r.stderr.rindex('{'):r.stderr.rindex('}') + 1])
        norm = os.path.join(a.shots, 'mix-norm.wav')
        run(['ffmpeg', '-v', 'error', '-y', '-i', a.audio, '-af',
             f"loudnorm=I=-14:TP=-2:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true",
             '-ar', '48000', norm])
        run(['ffmpeg', '-v', 'error', '-y', '-i', pic, '-i', norm, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out + '.part.mp4'])
    else:
        run(['ffmpeg', '-v', 'error', '-y', '-i', pic, '-c', 'copy', '-movflags', '+faststart', out + '.part.mp4'])
    os.replace(out + '.part.mp4', out)
    print(f'trailer: {out}  {os.path.getsize(out) / 1e6:.1f} MB', file=sys.stderr)
    if a.small:
        sm = os.path.join(os.path.dirname(out), 'trailer-720p.mp4')
        run(['ffmpeg', '-v', 'error', '-y', '-i', out, '-vf', 'scale=1280:-2:flags=lanczos', '-c:v', 'libx264', '-preset', 'slow', '-crf', '23', '-pix_fmt', 'yuv420p', '-c:a', 'copy', '-movflags', '+faststart', sm + '.part.mp4'])
        os.replace(sm + '.part.mp4', sm); print(f'small:   {sm}  {os.path.getsize(sm) / 1e6:.1f} MB', file=sys.stderr)
    if a.gif:
        shot, ss, dur = a.gif.split(':'); src = os.path.join(a.shots, shot + '.mp4')
        gif = os.path.join(os.path.dirname(out), f'{shot}.gif'); pal = os.path.join(a.shots, 'palette.png')
        for w, cols in ((640, 96), (560, 64), (480, 48)):   # shrink until it fits the 3 MB most store pages allow
            run(['ffmpeg', '-v', 'error', '-y', '-ss', ss, '-t', dur, '-i', src, '-vf', f'fps=15,scale={w}:-1:flags=lanczos,palettegen=max_colors={cols}:stats_mode=full', pal])
            run(['ffmpeg', '-v', 'error', '-y', '-ss', ss, '-t', dur, '-i', src, '-i', pal, '-lavfi',
                 f'fps=15,scale={w}:-1:flags=lanczos,tpad=stop_mode=clone:stop_duration=0.8[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle', '-loop', '0', gif])
            if os.path.getsize(gif) < 3e6: break
        print(f'gif:     {gif}  {os.path.getsize(gif) / 1e6:.2f} MB', file=sys.stderr)
    if a.thumb:
        shot, fr = a.thumb.split(':'); th = os.path.join(os.path.dirname(out), f'{shot}-frame{int(fr)}.jpg')
        run(['ffmpeg', '-v', 'error', '-y', '-i', os.path.join(a.shots, shot + '.mp4'), '-vf', f'select=eq(n\\,{int(fr)})', '-frames:v', '1', '-q:v', '2', th])
        print(f'thumb:   {th}', file=sys.stderr)


if __name__ == '__main__':
    main()
````

### `scripts/get_deps.py`

<!-- bundle-file: scripts/get_deps.py sha256=1ab6c191acf2e3dbed384dcca41a9452f3417b73a4a4b34b86a93a0a025ef068 -->
````python
#!/usr/bin/env python3
"""Fetch the pinned third-party files a pen-and-ink game embeds into its single HTML file.

  three.js r147 (MIT)              -> <game>/vendor/three.min.js
  IM Fell English + SC (OFL-1.1)   -> <game>/vendor/fonts/*.woff2
  Special Elite (Apache-2.0)       -> <game>/vendor/fonts/*.woff2      (+ every licence file next to them)

Each npm tarball is checked against its registry sha512 integrity before anything is extracted.
Files that already exist are kept (use --force to fetch again). Offline? Use --from DIR: a folder that already
holds three.min.js and the four .woff2 files (for example another game's vendor folder).

  python3 get_deps.py path/to/my-game
  python3 get_deps.py path/to/my-game --from ../other-game/vendor
"""
import sys
sys.dont_write_bytecode = True
import argparse, base64, hashlib, io, os, shutil, tarfile, urllib.request

REG = 'https://registry.npmjs.org'
# (package, version, sha512 integrity, {path in tarball: path under vendor/})
PKGS = [
    ('three', '0.147.0', 'sha512-LPTOslYQXFkmvceQjFTNnVVli2LaVF6C99Pv34fJypp8NbQLbTlu3KinZ0zURghS5zEehK+VQyvWuPZ/Sm8fzw==',
     {'package/build/three.min.js': 'three.min.js', 'package/LICENSE': 'LICENSE-three.txt'}),
    ('@fontsource/im-fell-english', '5.3.0', 'sha512-FcgdWfY9WeUM2gQkfmwhn4Ed9LVtlll8LSSZvHfbsUrnHK5tHHnGg6BgwAfHogp52adU3eE89J/3B52qV3b+Vw==',
     {'package/files/im-fell-english-latin-400-normal.woff2': 'fonts/im-fell-english-latin-400-normal.woff2',
      'package/files/im-fell-english-latin-400-italic.woff2': 'fonts/im-fell-english-latin-400-italic.woff2',
      'package/LICENSE': 'fonts/OFL-IM-Fell-English.txt'}),
    ('@fontsource/im-fell-english-sc', '5.3.0', 'sha512-jKnCJ22tgVwxWVs1YQ/GCWmP60ulVq49IJZ7c0wgv0MXHe8T8LPbl0sOteYLOkCURW5+ZKwFiLNU2h/l9fHgrg==',
     {'package/files/im-fell-english-sc-latin-400-normal.woff2': 'fonts/im-fell-english-sc-latin-400-normal.woff2',
      'package/LICENSE': 'fonts/OFL-IM-Fell-English-SC.txt'}),
    ('@fontsource/special-elite', '5.3.0', 'sha512-fOQ9XU8m4KnqzcLibAXCxTsKzbxePNDjPqVss5GSMcPVCY1TuCv+Wq8gm1ebqIR6XS1rhMbQ7ECP9ocKVEEpTA==',
     {'package/files/special-elite-latin-400-normal.woff2': 'fonts/special-elite-latin-400-normal.woff2',
      'package/LICENSE': 'fonts/LICENSE-Special-Elite.txt'}),
]
REQUIRED = [dst for _, _, _, files in PKGS for dst in files.values() if not dst.endswith('.txt')]


def tarball_url(name, ver):
    base = name.split('/')[-1]
    return f'{REG}/{name}/-/{base}-{ver}.tgz'


def fetch(name, ver, integrity):
    data = urllib.request.urlopen(tarball_url(name, ver), timeout=60).read()
    got = 'sha512-' + base64.b64encode(hashlib.sha512(data).digest()).decode()
    if got != integrity:
        raise SystemExit(f'integrity mismatch for {name}@{ver}: expected {integrity}, got {got}')
    return data


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('game_dir', help='the game folder (vendor/ is created inside it)')
    ap.add_argument('--from', dest='src', help='copy from this folder instead of downloading (offline)')
    ap.add_argument('--force', action='store_true', help='fetch again even if the files exist')
    a = ap.parse_args()
    vendor = os.path.join(a.game_dir, 'vendor')
    os.makedirs(os.path.join(vendor, 'fonts'), exist_ok=True)
    done = []
    if a.src:
        for dst in REQUIRED + [d for _, _, _, f in PKGS for d in f.values() if d.endswith('.txt')]:
            cand = [os.path.join(a.src, dst), os.path.join(a.src, os.path.basename(dst))]
            src = next((c for c in cand if os.path.exists(c)), None)
            out = os.path.join(vendor, dst)
            if src and (a.force or not os.path.exists(out)) and os.path.abspath(src) != os.path.abspath(out):
                shutil.copyfile(src, out); done.append(dst)
    else:
        for name, ver, integ, files in PKGS:
            if not a.force and all(os.path.exists(os.path.join(vendor, d)) for d in files.values()):
                continue
            tf = tarfile.open(fileobj=io.BytesIO(fetch(name, ver, integ)), mode='r:gz')
            for member, dst in files.items():
                out = os.path.join(vendor, dst)
                with tf.extractfile(member) as f, open(out, 'wb') as o:
                    o.write(f.read())
                done.append(dst)
    missing = [d for d in REQUIRED if not os.path.exists(os.path.join(vendor, d))]
    print(f'vendor: {vendor}  fetched {len(done)} file(s)', file=sys.stderr)
    if missing:
        print('missing: ' + ', '.join(missing), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
````

### `scripts/new_game.py`

<!-- bundle-file: scripts/new_game.py sha256=1c4d009f83c8b3a7cac66e656c993f3976a96a29cb13746ba8509914f0125b9d -->
````python
#!/usr/bin/env python3
"""Start a new pen-and-ink game from the starter kit: a playable three-level game you then reshape.

  python3 new_game.py "The Quiet Stair"                    -> ./the-quiet-stair/ (src, vendor, dist/the-quiet-stair.html)
  python3 new_game.py "The Quiet Stair" --dir games/stair  -> games/stair/
  python3 new_game.py "X" --vendor-from other-game/vendor  -> offline: copy three.js and fonts instead of downloading

Refuses to write into a folder that already has files in it, so it never overwrites anyone's work.
"""
import sys
sys.dont_write_bytecode = True
import argparse, json, os, re, shutil, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
STARTER = os.path.join(HERE, '..', 'assets', 'starter', 'src')


def slugify(t):
    return re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-') or 'ink-game'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('title', help='the game title, shown on the title screen and the browser tab')
    ap.add_argument('--dir', help='where to create the game (default: ./<slug>)')
    ap.add_argument('--slug', help='file and save-key name (default: from the title)')
    ap.add_argument('--vendor-from', help='copy vendor files from this folder instead of downloading')
    ap.add_argument('--no-deps', action='store_true', help='do not fetch three.js and the fonts (and do not build)')
    a = ap.parse_args()
    slug = a.slug or slugify(a.title)
    game = a.dir or slug
    if os.path.exists(game) and os.listdir(game):
        raise SystemExit(f'{game} already exists and is not empty; pick another --dir')
    os.makedirs(os.path.join(game, 'src'), exist_ok=True)
    esc = a.title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    for f in sorted(os.listdir(STARTER)):
        s = open(os.path.join(STARTER, f), encoding='utf-8').read()
        s = s.replace('{{TITLE}}', esc if f.endswith('.html') else a.title).replace('{{SLUG}}', slug.replace('-', '_'))
        open(os.path.join(game, 'src', f), 'w', encoding='utf-8').write(s)
    json.dump({'title': a.title, 'slug': slug, 'three': '0.147.0'}, open(os.path.join(game, 'game.json'), 'w'), indent=2)
    print(f'created {game}/src ({len(os.listdir(STARTER))} files)', file=sys.stderr)
    if a.no_deps:
        print('next: python3 scripts/get_deps.py %s && python3 scripts/build_html.py %s' % (game, game), file=sys.stderr)
        return
    dep = [sys.executable, os.path.join(HERE, 'get_deps.py'), game] + (['--from', a.vendor_from] if a.vendor_from else [])
    if subprocess.run(dep).returncode:
        raise SystemExit('could not fetch three.js/fonts; retry get_deps.py, or pass --vendor-from')
    if subprocess.run([sys.executable, os.path.join(HERE, 'build_html.py'), game]).returncode:
        raise SystemExit('build failed')
    print(f'play: open {os.path.join(game, "dist", slug + ".html")} in a browser', file=sys.stderr)


if __name__ == '__main__':
    main()
````

### `scripts/playtest.py`

<!-- bundle-file: scripts/playtest.py sha256=4e87894986410d8394668f4e5565bc1890155ba574e6dcf0c5dd4bf555beb225 -->
````python
#!/usr/bin/env python3
"""Robot playtest for a built pen-and-ink game: proves every level loads, every exit door leads on, and every
gravity zone flips gravity. Runs headless in a few seconds; use it after every change to levels or doors.

  python3 playtest.py dist/my-game.html            -> one line per check, exit status 1 if anything failed
  python3 playtest.py dist/my-game.html --shots    -> also saves a picture just after each crossing (dist/playtest/)

For each level i: start it, wait for the next level to build, open the exit, stand 0.8 m in front of it, hold W and
step frames until the game reports level i+1. Enemies are switched off (e.off = true) so the robot is not caught.
"""
import sys
sys.dont_write_bytecode = True
import argparse, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
from _pen_ink_common import open_game

ROUTE = r'''async (shots) => {
  const g = window.__game, G = g.GAME, out = [], pics = [];
  const quiet = () => { for (const e of G.L.ents) e.off = true; };
  const n = g.LEVELS.length - 1;
  for (let i = 1; i <= n; i++) {
    g.play(i); quiet(); g.step(36, 1 / 30, false);
    const L = G.L, r = { level: i, name: L.name, spawn: L.spawn ? L.spawn.pos.toArray().map(v => +v.toFixed(2)) : null };
    r.grounded = g.step(10).grounded;               // the spawn point stands on something
    const nxt = G.nextIdx(i);
    if (!L.exitDoor || nxt == null) { r.exit = 'none (final level)'; out.push(r); continue; }
    r.nextBuilt = !!G.next;
    g.openExit(); g.faceExit(0.8); g.hold('KeyW');
    let k = 0; while (G.idx === i && k < 120) { g.step(1, 1 / 30, false); k++; }
    g.hold('KeyW', false);
    r.crossed = G.idx === nxt; r.frames = k; r.after = g.step(20);
    if (shots) pics.push(i);
    // gravity zones of level i (checked on a fresh copy of it)
    g.play(i); quiet(); g.step(5, 1 / 30, false);
    r.zones = G.L.gravZones.map(z => {
      const b = z.box, c = new g.V3((b[0] + b[3]) / 2, (b[1] + b[4]) / 2, (b[2] + b[5]) / 2);
      g.PL.gravLock = 0; g.PL.setFrameQ(g.faceQ(z.from)); g.PL.pos.copy(c).addScaledVector(g.PL.up, -g.PL.height() / 2); g.PL.vel.set(0, 0, 0);
      g.step(3, 1 / 30, false);
      return { from: [z.from.ax, z.from.sg], to: [z.to.ax, z.to.sg], ok: g.PL.ax === z.to.ax && g.PL.sg === z.to.sg };
    });
    out.push(r);
  }
  return { out, errs: g.ERRS.slice(0, 5) };
}'''


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('html')
    ap.add_argument('--shots', action='store_true', help='save a picture after each crossing')
    a = ap.parse_args()
    fails = []
    with sync_playwright() as p:
        b, pg, errs = open_game(p, a.html, 960, 540)
        res = pg.evaluate(ROUTE, a.shots)
        if a.shots:
            d = os.path.join(os.path.dirname(os.path.abspath(a.html)), 'playtest'); os.makedirs(d, exist_ok=True)
            pg.screenshot(path=os.path.join(d, 'last.jpg'), type='jpeg', quality=90)
        b.close()
    for r in res['out']:
        line = f"level {r['level']} ({r['name']}): spawn {'on ground' if r['grounded'] else 'IN THE AIR'}"
        if not r['grounded']: fails.append(f"level {r['level']} spawn is not on the ground")
        if 'crossed' in r:
            line += f", next level {'built' if r['nextBuilt'] else 'NOT BUILT'}, exit {'crossed' if r['crossed'] else 'NOT CROSSED'} in {r['frames']} frames"
            if not r['crossed']: fails.append(f"level {r['level']}: walking through the open exit did not reach the next level (stuck at {r['after']['pos']})")
            if not r['nextBuilt']: fails.append(f"level {r['level']}: the next level was not built 1.2 s after start")
        else:
            line += ', ' + r['exit']
        for z in r.get('zones', []):
            line += f", gravity zone {z['from']}->{z['to']} {'ok' if z['ok'] else 'FAILED'}"
            if not z['ok']: fails.append(f"level {r['level']}: gravity zone {z['from']}->{z['to']} did not switch gravity")
        print(line, file=sys.stderr)
    errs += [f'game: {e}' for e in res['errs']]
    for e in dict.fromkeys(errs): fails.append(e)
    if fails:
        print('FAILED:\n  ' + '\n  '.join(fails), file=sys.stderr); sys.exit(1)
    print('playtest passed', file=sys.stderr)


if __name__ == '__main__':
    main()
````

### `scripts/render_audio.py`

<!-- bundle-file: scripts/render_audio.py sha256=7e87e8fe2f94bb09fa838ed565bf70b948b197e154f966aba7866081e9d9623f -->
````python
#!/usr/bin/env python3
"""Render a trailer soundtrack offline from the game's own synthesizer, timed to the filmed shots.

  python3 render_audio.py dist/my-game.html promo/cues.js --shots promo/shots   -> promo/mix.wav (48 kHz stereo)
  python3 render_audio.py dist/my-game.html promo/cues.js --shots promo/shots --edit promo/edit.json

The cue sheet (start from assets/promo/cues_template.js) defines window.__cues(E) -> sections; inside a section's
play(a), times are seconds from that section's t0. E gives every shot's start time on the trailer timeline and the
per-frame logs film_shots.py wrote, so footsteps and gravity flips land on the picture (__snd.steps / __snd.flips).
The timeline is shots.json order with no gaps, or edit.json: {"timeline": ["s01", {"black": 14}, "s02", ...]}
(the same file finish_trailer.py reads, so sound and picture agree). Peak is normalised to -1 dBFS; loudness is
set later by finish_trailer.py.
"""
import sys
sys.dont_write_bytecode = True
import argparse, base64, json, math, os, wave
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
from _pen_ink_common import GL_ARGS, promo_copy

HERE = os.path.dirname(os.path.abspath(__file__))
FPS, SR = 30, 48000


def timeline(shots_dir, edit=None):
    """[(kind, name_or_frames, start_seconds, frames)] for every item on the trailer timeline."""
    meta = {s['name']: s['frames'] for s in json.load(open(os.path.join(shots_dir, 'shots.json')))}
    items = json.load(open(edit))['timeline'] if edit else list(meta)
    out, f = [], 0
    for it in items:
        if isinstance(it, dict):
            out.append(('black', None, f / FPS, int(it['black']))); f += int(it['black'])
        else:
            if it not in meta: raise SystemExit(f'{it} is not in {shots_dir}/shots.json')
            out.append(('shot', it, f / FPS, meta[it])); f += meta[it]
    return out, f / FPS


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('html'); ap.add_argument('cues')
    ap.add_argument('--shots', required=True, help='the folder film_shots.py wrote (shots.json + <shot>.json logs)')
    ap.add_argument('--edit', help='edit.json with the timeline (default: every shot, in order, no gaps)')
    ap.add_argument('-o', '--out', help='output WAV (default: mix.wav next to the cue sheet)')
    a = ap.parse_args()
    tl, total = timeline(a.shots, a.edit)
    E = {'fps': FPS, 'total': total, 'start': {}, 'frames': {}, 'logs': {}}
    for kind, name, t, n in tl:
        if kind == 'shot':
            E['start'][name] = round(t, 4); E['frames'][name] = n
            lp = os.path.join(a.shots, f'{name}.json')
            E['logs'][name] = json.load(open(lp)) if os.path.exists(lp) else []
    out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.cues)), 'mix.wav')
    mix = np.zeros((int(math.ceil(total * SR)) + SR, 2), np.float32)
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, args=GL_ARGS + ['--autoplay-policy=no-user-gesture-required'])
        pg = b.new_page(viewport={'width': 640, 'height': 360}); pg.set_default_timeout(600000)
        pg.on('pageerror', lambda e: print('PAGE ERROR', e, file=sys.stderr))
        pg.add_init_script('window.requestAnimationFrame = () => 0;')
        pg.goto('file://' + os.path.abspath(promo_copy(a.html)))
        pg.wait_for_function('window.__ev && window.__game', polling=200, timeout=60000)
        for js in (os.path.join(HERE, '..', 'assets', 'promo', 'offline_audio.js'), a.cues):
            pg.evaluate('s => __ev(s)', open(js, encoding='utf-8').read())
        meta = pg.evaluate('E => __cues(E).map(s => ({ t0: s.t0, dur: s.dur, cut: s.cut, fade: s.fade || 0, gain: s.gain || 1 }))', E)
        for k, s in enumerate(meta):
            b64 = pg.evaluate('async ([E, k]) => { const s = __cues(E)[k]; return await __snd.render(s.dur, s.play); }', [E, k])
            x = np.frombuffer(base64.b64decode(b64), np.float32).reshape(-1, 2).copy() * s['gain']
            if s.get('cut') is not None:
                x = x[:max(0, int(round((s['cut'] - s['t0']) * SR)))]
            fn = int(s['fade'] * SR)
            if fn and len(x) >= fn: x[-fn:] *= np.linspace(1, 0, fn, dtype=np.float32)[:, None]
            i0 = int(round(s['t0'] * SR)); x = x[:max(0, len(mix) - i0)]; mix[i0:i0 + len(x)] += x
            print(f"section {k}: t0 {s['t0']:.2f}s  {len(x) / SR:.2f}s  peak {float(np.abs(x).max()) if len(x) else 0:.3f}", file=sys.stderr)
        b.close()
    mix = mix[:int(round(total * SR))]
    pk = float(np.abs(mix).max()); mix *= 0.89 / max(pk, 1e-6)
    with wave.open(out, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(mix, -1, 1) * 32767).astype('<i2').tobytes())
    print(f'wrote {out}  {len(mix) / SR:.2f}s (timeline {total:.2f}s)', file=sys.stderr)


if __name__ == '__main__':
    main()
````

### `scripts/shoot.py`

<!-- bundle-file: scripts/shoot.py sha256=cc7e6c60de146ea4ed9b58e471b9db9eb4c24eaaf4d04189710bb6c66532660d -->
````python
#!/usr/bin/env python3
"""Screenshot a built pen-and-ink game headlessly, and fail loudly on any JavaScript error.

  python3 shoot.py dist/my-game.html                      -> dist/shots/title.jpg, level-1.jpg, level-2.jpg ...
  python3 shoot.py dist/my-game.html --shots shots.json   -> your own camera positions
  python3 shoot.py dist/my-game.html --size 1920x1080 --png

shots.json is a list of {"name", "level", "pos": [x,y,z], "yaw", "pitch", "steps", "js"}; every key but name is
optional. "level": 0 is the title screen. "js" runs inside the page after placing the player (window.__game is there).
The game runs in software WebGL (SwiftShader), frame by frame through window.__game.step(), so shots are repeatable.
Exit status 1 if the page threw, logged an error, or the game caught one (window.__game.ERRS).
"""
import sys
sys.dont_write_bytecode = True
import argparse, json, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
from _pen_ink_common import open_game

def default_shots(pg):
    n = pg.evaluate('() => window.__game.LEVELS.length - 1')
    return [{'name': 'title', 'level': 0, 'steps': 75}] + [{'name': f'level-{i}', 'level': i, 'steps': 45} for i in range(1, n + 1)]


def take(pg, s):
    lvl = s.get('level', 1)
    if lvl == 0:
        pg.evaluate('() => window.__game.GAME.titleLevel()')
    else:
        pg.evaluate(f'() => window.__game.play({lvl})')
        # skip the fade-in a level start plays, so short shots are not dark
        pg.evaluate("() => { const g = window.__game; g.UI.show(null); g.GAME.fadeTo(0, 0); g.GAME.toast = () => {}; g.GAME.hint = () => {}; g.GAME.caught = () => {}; document.getElementById('toast').classList.remove('show'); for (const k in g.IN.keys) g.IN.keys[k] = false; }")
    if 'pos' in s:
        x, y, z = s['pos']
        pg.evaluate(f'() => window.__game.tp({x}, {y}, {z})')
    if 'yaw' in s or 'pitch' in s:
        pg.evaluate(f"() => window.__game.look({s.get('yaw', 0)}, {s.get('pitch', 0)})")
    if s.get('js'):
        pg.evaluate('code => (0, eval)(code)', s['js'])
    return pg.evaluate(f"() => window.__game.step({int(s.get('steps', 45))})")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('html', help='the built game (dist/<slug>.html)')
    ap.add_argument('--shots', help='JSON list of shots (default: title + every level at its spawn)')
    ap.add_argument('--out', help='folder for the images (default: <game>/shots/)')
    ap.add_argument('--size', default='1280x720')
    ap.add_argument('--quality', type=int, default=1, help='0 low (phone), 1 medium, 2 high')
    ap.add_argument('--png', action='store_true', help='PNG instead of JPEG (q92)')
    a = ap.parse_args()
    w, h = map(int, a.size.lower().split('x'))
    d = os.path.dirname(os.path.abspath(a.html))
    out = a.out or os.path.join(os.path.dirname(d) if os.path.basename(d) == 'dist' else d, 'shots')  # never inside dist/, the folder you ship
    os.makedirs(out, exist_ok=True)
    t0 = time.time(); report = []
    with sync_playwright() as p:
        b, pg, errs = open_game(p, a.html, w, h, a.quality)
        shots = json.load(open(a.shots)) if a.shots else default_shots(pg)
        for s in shots:
            st = take(pg, s)
            fn = os.path.join(out, s['name'] + ('.png' if a.png else '.jpg'))
            pg.screenshot(path=fn, type='png' if a.png else 'jpeg', **({} if a.png else {'quality': 92}))
            errs += [f'game: {e}' for e in st.get('errs', []) if f'game: {e}' not in errs]
            report.append({'name': s['name'], 'file': fn, 'state': st})
            print(f"{s['name']:>16}  level {st.get('idx')}  {st.get('state')}  pos {st.get('pos')}  up {st.get('up')}", file=sys.stderr)
        b.close()
    json.dump(report, open(os.path.join(out, 'shots.json'), 'w'), indent=1)
    print(f'{len(report)} shot(s) in {out}  ({time.time() - t0:.0f}s)', file=sys.stderr)
    if errs:
        print('ERRORS:\n  ' + '\n  '.join(dict.fromkeys(errs)), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
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
