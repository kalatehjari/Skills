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
