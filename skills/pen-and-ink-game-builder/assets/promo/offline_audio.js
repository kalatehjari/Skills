// Offline renderer for the game's own synth (AU), used by render_audio.py. Runs inside the game scope (promo build).
// Trick: AU is re-initialised on an OfflineAudioContext seen through a proxy whose currentTime is whatever moment
// we are scheduling, so every AU call (which schedules at ctx.currentTime + delay) lands exactly on the cue time.
// AU.melody uses setInterval; the api captures that callback so a cue sheet can place each note by hand.
(() => {
  const SR = 48000;
  function mkCtx(dur) {
    const real = new OfflineAudioContext(2, Math.ceil(SR * dur), SR), st = { OFF: 0 };
    const wrap = n => { const s0 = n.start.bind(n); n.start = (w, ...r) => s0(w ? w : st.OFF, ...r); return n; };
    const px = new Proxy(real, {
      get(t, k) {
        if (k === 'currentTime') return st.OFF;
        if (k === 'createOscillator') return () => wrap(t.createOscillator());
        if (k === 'createBufferSource') return () => wrap(t.createBufferSource());
        const v = Reflect.get(t, k, t); return typeof v === 'function' ? v.bind(t) : v;
      }
    });
    return { real, px, st };
  }
  function toB64(buf) { // interleaved float32 stereo, base64
    const n = buf.length, L = buf.getChannelData(0), R = buf.numberOfChannels > 1 ? buf.getChannelData(1) : L;
    const out = new Float32Array(n * 2); for (let i = 0; i < n; i++) { out[2 * i] = L[i]; out[2 * i + 1] = R[i]; }
    const bytes = new Uint8Array(out.buffer); let s = ''; const CH = 0x8000;
    for (let i = 0; i < bytes.length; i += CH) s += String.fromCharCode.apply(null, bytes.subarray(i, i + CH));
    return btoa(s);
  }
  async function render(dur, play) {
    const { real, px, st } = mkCtx(dur);
    AU.ctx = null; AU.ok = false; AU.beds = []; AU._mel = null;
    const AC = window.AudioContext; window.AudioContext = function () { return px; };
    try { AU.init(); } finally { window.AudioContext = AC; }
    CAM.position.set(0, 0, 0); CAM.quaternion.identity(); CAM.updateMatrixWorld(); // positional sounds are heard from the origin
    const SI = window.setInterval, CI = window.clearInterval; let cap = null;
    window.setInterval = fn => { cap = fn; return 0; }; window.clearInterval = () => { };
    const at = (t, fn) => { st.OFF = Math.max(0, t); fn(); };
    const api = {
      at,                                                    // at(seconds, () => AU.slam(null, 0.5))
      bed: (t, spec) => at(t, () => AU.bed(spec)),           // an ambient drone (a level's env.bed)
      stopBeds: (t, fade) => at(t, () => AU.stopBeds(fade)),
      melody(times) { at(times[0], () => AU.melody(true)); const note = cap; cap = null; if (note) times.forEach(t => at(t, note)); },
      v: (x, y, z) => new V3(x, y, z)                         // a position to pan a sound from
    };
    try { play(api); } finally { window.setInterval = SI; window.clearInterval = CI; }
    return toB64(await real.startRendering());
  }
  // footsteps from a shot's per-frame log: a step every `every` metres walked on the ground, plus gravity flips
  function steps(E, shot, every = 0.8) {
    const L = E.logs[shot] || [], out = [], t0 = E.start[shot] || 0; let acc = every * 0.45;
    for (let i = 1; i < L.length; i++) {
      const a = L[i - 1], b = L[i]; if (String(a.up) !== String(b.up) || !b.gr) continue;
      const d = b.pos.map((v, k) => v - a.pos[k]), u = b.up, dot = d[0] * u[0] + d[1] * u[1] + d[2] * u[2];
      acc += Math.hypot(d[0] - dot * u[0], d[1] - dot * u[1], d[2] - dot * u[2]);
      if (acc >= every) { acc -= every; out.push(+(t0 + i / E.fps).toFixed(3)); }
    }
    return out;
  }
  function flips(E, shot) { const L = E.logs[shot] || [], t0 = E.start[shot] || 0; return L.map((f, i) => i && String(f.up) !== String(L[i - 1].up) ? +(t0 + i / E.fps).toFixed(3) : null).filter(t => t != null); }
  window.__snd = { render, steps, flips };
})();
