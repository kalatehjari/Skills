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
