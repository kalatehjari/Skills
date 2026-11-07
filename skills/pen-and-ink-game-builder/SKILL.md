---
name: pen-and-ink-game-builder
description: Build first-person 3D browser games that look like living pen-and-ink drawings (crosshatched shading, boiling lines, paper grain, one blue accent) as one offline HTML file, with doors that open straight onto the next level, Escher rooms where walls become floors, keyboard, mouse, touch and gamepad controls and synthesized sound; then test it headlessly and film a trailer, screenshots and a GIF from inside it. Use this whenever someone wants an ink, etching, engraving, sketch, woodcut, Escher, noir or hand-drawn look for a 3D or first-person game, a horror, exploration, puzzle or escape game in a single HTML file, portal doors or impossible architecture, a playable itch.io demo, or promo material for such a game, even if they never say "pen and ink".
license: MIT
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
