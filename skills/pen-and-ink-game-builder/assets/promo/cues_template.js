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
