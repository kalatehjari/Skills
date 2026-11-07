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
