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
