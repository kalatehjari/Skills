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
