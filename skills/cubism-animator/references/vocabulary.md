# The cubist vocabulary

## Contents
1. The core idea: emotion as geometry
2. Art-historical moves and what they mean on screen
3. Palettes as acts
4. Library API (cubism.js)
5. Composition rules
6. Worked example: Tan Be Tan (cubist cut)

## 1. The core idea: emotion as geometry

The character is never drawn "realistically". She is a set of planes, and **what happens to the planes is the story**.
Decide, for every section, which state the planes are in:

| inner state | what the planes do | parameters |
|---|---|---|
| whole, calm, at peace | locked together, tiny drift | `split: 0`, `snap: 0` |
| emptiness, loss, numbness | drift apart slowly, background shows through the gaps | `split` 0.1 → 0.55 over 4-8 bars |
| pressure, being watched, anxiety | shatter on every beat and snap back; extra eyes appear on the shards | `snap: 1`, `split: 0.18 + 0.2*kick(t)`, `extraEyes: 1` |
| being controlled | a plane-figure on red lines from a black bar, a new pose each beat | `figure(... pose:'custom', j)` + `redLines` |
| rupture / liberation | a Kandinsky burst on a downbeat; red line fragments fly; white flash | `burst`, `flash` |
| reconciliation with oneself | a dark half-face and a light half-face slide together into one | `face(... half:'dark')` + `face(... half:'light')` |
| rebirth | discs bloom in footprints; triangles sprout; dawn palette | `disc` growing with `E.outBack` |
| departure / transcendence | a white rectangle opens to fill the frame; the figure fades to white | Malevich white-on-white |

Identity survives through **signs**, not likeness: the bob as an angular black plane, one amber eye,
red lips, the white tee, a newsprint scrap with the title on her shoulder. Set them once with
`CUBE.setLook({ hair, iris, lips, tee })` from the user's reference photos.

## 2. Art-historical moves

- **Analytic cubism (Picasso, Braque):** `facets()` backgrounds — the world itself broken into jittered triangles with hatch, dots or gradient textures, drifting slowly. Use muted palettes for reflective sections.
- **Simultaneity:** the face shows frontal eye + profile eye and nose at once (built into `face`). Under pressure, multiply eyes (`extraEyes`).
- **Papier collé:** the newsprint scrap with a word in the song's language (`collage: true`, default). Swap the word per project in cubism.js.
- **Orphism (Robert & Sonia Delaunay):** `disc()` — concentric rings in quartered colour. Use it for suns, drums, hearts, flowers, targets. `split` and `burst` break it apart (a drum tearing).
- **Suprematism / Constructivism (Malevich, El Lissitzky):** the antagonist as a black `wedge()` with a red eye; a red triangle cutting the frame ("Beat the Whites with the Red Wedge"); the final white rectangle; the lyric strip as a tilted paper bar with a red or black edge.
- **Kandinsky:** point → line → plane as the opening title; `burst()` of circles, triangles and bars on the climactic downbeat; long black lines crossing the facets.

Push one idea per section. Avant-garde reads as bold, not busy: one big shape, one colour conflict, one motion.

## 3. Palettes as acts

`PAL` keys: `night` (indigo, waiting), `desert` (ochre, emptiness), `blood` (vermilion/black, siege), `storm` (teal, rupture), `ember` (orange/violet, resolve), `dawn` (pastel Orphic, rebirth), `gold` (warm green-gold, walking away), `white` (transcendence).
Each has `bg[]` for facets and roles `L M D A W R` for the face planes. Add new palettes by copying an entry; keep one hot accent per palette.

## 4. Library API (`globalThis.CUBE`, from cubism.js)

Timing: `B(bar, beat)` → seconds; `kick(t, decay)` 1 on each beat; `lastBeat(t)`, `sinceBeat(t)`, `prog(t,a,b)`, `sm(x)`.
Drawing: `plane(ctx, pts, fill, {alpha, tex, lw, stroke})`, `texture`, `line(ctx,a,b,lw,col)`, `circle(ctx,x,y,r,fill,{lw})`.
Scenes:
- `facets(ctx, t, palKey, seed, {nx, ny, drift, lines, alpha, tex})` — full-frame analytic background.
- `disc(ctx, x, y, R, rings, colours, rot, {split, burst, alpha})`.
- `burst(ctx, t, t0, x, y, n, colours, seed, dur)`.
- `face(ctx, x, y, t, {pal, s, split, snap, eyes 0-1.3, mouth 0-1, tears, extraEyes, half:'dark'|'light', rot, smile, collage})` — ~600 units tall at s=1, centred on the nose.
- `figure(ctx, x, yFeet, t, {pal, s, dir, pose:'stand|walk|run|kneel|hug|open|custom', phase, j:{hip,lean,legF,legB,armF,armB,head}, mono, split})` → `{head, wF, wB, hip}`.
- `wedge(ctx, x, yBase, t, {s, arm, dagger, stick, eye, broken, rot})` — the antagonist.
- `claw(ctx, fx, fy, hx, hy, colour, grip)`; `hands(ctx, t, t0, {dissolve})` — 8 hands landing one per beat.
- `redLines(ctx, fromPts, toPts, lw)`; `flash(ctx, a, 'r,g,b')`; `sand(ctx, t, n)`; `stormLines(ctx, t, n, a)`.
- `lyrics(ctx, t)` — reads `SCORE.subtitles` `{t, end, fa, en, key}`; `key: 'c'` (chorus) gets a red edge and larger type.

## 5. Composition rules

- Keep the face centred around y≈470 at s≈0.85 so the lyric strip (bottom 210 px) never covers the mouth.
- A strong silhouette needs a contrasting field: put dark figures on light discs, never black on black.
- RTL text: set `ctx.direction = 'rtl'` and use `textAlign: 'right'` when anchoring Persian text next to a shape.
- Cuts on bar lines; per-beat changes only in choruses and builds. Crossfades (`'fade'`) between reflective sections, `'flash'` into a chorus.
- Recurring motifs must return transformed (spears → blooming discs; shattered face → whole face).

## 6. Worked example: Tan Be Tan (Rosha), cubist cut

| bars | section | shots |
|---|---|---|
| 0-4 | title | red point grows, a black line slashes the frame, title type |
| 4-10 | intro | night facets; plane-face with closed eyes, a lit vertical rectangle (the door) |
| 10-18 | hook | the rectangle pulses red per beat, face trembles (`snap .25`); figure walks into it, it expands to white |
| 18-34 | verse 1 "emptied of your love, a desert" | tiny figure on a horizon under a drained disc-sun; the face drifts apart, sand pours through gaps; kneeling among black verticals with red pennants |
| 34-50 | bridge "you, chasing tricks… dagger… plans" | black wedge slides in, red wedge cuts the frame; split frame: light half-face vs wedge with dagger; marionette figure on red lines; red plan lines converge one per beat |
| 50-66 | chorus "no breath… no strength… at war with me, body to body" | face shatters per beat with extra eyes and 8 claw hands; marionette jerked against a giant disc; one huge eye with the wedge in the iris; duel against a disc |
| 66-79 | guitar solo | Kandinsky burst + white flash on the downbeat, figure runs through storm diagonals; face floating in teal; arms open |
| 79-83 | drum build | disc / wedge drumming / shattered face, one composition per beat |
| 83-99 | verse 3 "I made peace with myself, don't set fire to my soul" | drum shockwave arcs pass the face as it reassembles; open palms rise; dark and light half-faces slide into one; fire triangles bend around her, a blue ring protects her |
| 99-115 | bridge 2 | dawn palette, discs bloom in her footsteps; whole smiling face among Orphic discs; spears flower |
| 115-131 | chorus 2 | hands arrive and crumble into pastel shards; she pulls the red lines, the wedge tips over; eye with a sprout; she disarms it |
| 131-137 | build 2 | the drum disc splits and bursts apart on the last beat |
| 137-157 | outro | the broken wedge, small; she walks into a white rectangle; white on white; end card: red circle, black line, the key lyric |

Full code: `example-tan-be-tan-cubist.js` with `example-score.js`.
