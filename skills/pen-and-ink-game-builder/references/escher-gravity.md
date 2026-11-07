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
