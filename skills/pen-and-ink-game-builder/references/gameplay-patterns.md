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
