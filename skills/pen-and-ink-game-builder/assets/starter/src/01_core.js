'use strict';
/* ===================== core: utilities, settings, synthesized audio ===================== */
const TAU = Math.PI * 2;
const clamp = (v, a, b) => v < a ? a : v > b ? b : v;
const lerp = (a, b, t) => a + (b - a) * t;
const smooth = t => t * t * (3 - 2 * t);
const damp = (a, b, k, dt) => lerp(a, b, 1 - Math.exp(-k * dt));
function mulberry32(a) { return function () { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
let RNG = mulberry32(1);
const seedRng = s => { RNG = mulberry32(s >>> 0); };      // level building uses RNG, so a level looks the same every time
const rnd = (a = 0, b = 1) => a + (b - a) * RNG();
const mrand = (a = 0, b = 1) => a + (b - a) * Math.random(); // sound and particles use Math.random
function hash1(n) { n = Math.sin(n * 127.1 + 11.7) * 43758.5453; return n - Math.floor(n); }
function noise1(x) { const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f); return lerp(hash1(i), hash1(i + 1), u) * 2 - 1; }
const $ = id => document.getElementById(id);
const IS_TOUCH = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0 && matchMedia('(pointer:coarse)').matches);

/* one prefix for everything this game saves, so games served from the same host (itch.io) never collide */
const Store = {
  get(k, d) { try { const v = localStorage.getItem('{{SLUG}}_' + k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } },
  set(k, v) { try { localStorage.setItem('{{SLUG}}_' + k, JSON.stringify(v)); } catch (e) { } }
};
const SET = Object.assign({ sens: 1, invert: 0, fov: 74, quality: IS_TOUCH ? 0 : 1, vol: 0.85, mus: 0.6, calm: 0 }, Store.get('set', {}));
function saveSet() { Store.set('set', SET); }

/* ===================== AUDIO: everything is synthesized, nothing is downloaded =====================
   Every sound schedules itself at ctx.currentTime (+ delay). Keep that pattern: the promo pipeline renders
   the same functions offline by swapping in an OfflineAudioContext whose "now" is the cue time. */
const AU = {
  ctx: null, ok: false, beds: [],
  init() {
    if (this.ctx) return;
    try { const C = window.AudioContext || window.webkitAudioContext; if (!C) return; this.ctx = new C(); } catch (e) { return; }
    const c = this.ctx;
    this.comp = c.createDynamicsCompressor(); this.comp.threshold.value = -16; this.comp.knee.value = 12; this.comp.ratio.value = 4;
    this.comp.attack.value = 0.004; this.comp.release.value = 0.25; this.comp.connect(c.destination);
    this.master = c.createGain(); this.master.connect(this.comp);
    this.music = c.createGain(); this.music.connect(this.master);
    this.sfx = c.createGain(); this.sfx.connect(this.master);
    this.bedBus = c.createGain(); this.bedBus.connect(this.master);
    this.rev = c.createConvolver(); this.rev.buffer = this.impulse(3.2, 2.6);
    this.revOut = c.createGain(); this.revOut.gain.value = 0.55; this.rev.connect(this.revOut); this.revOut.connect(this.master);
    this.revSend = c.createGain(); this.revSend.gain.value = 0.4; this.revSend.connect(this.rev);
    this.noiseBuf = this.makeNoise(3); this.brownBuf = this.makeBrown(4);
    this.ok = true; this.applyVol();
  },
  applyVol() { if (!this.ok) return; const t = this.ctx.currentTime; this.master.gain.setTargetAtTime(SET.vol, t, 0.05); this.music.gain.setTargetAtTime(SET.mus, t, 0.1); },
  resume() { if (this.ctx && this.ctx.state !== 'running') { try { this.ctx.resume(); } catch (e) { } } },
  impulse(sec, decay) {
    const c = this.ctx, n = Math.floor(c.sampleRate * sec), b = c.createBuffer(2, n, c.sampleRate);
    for (let ch = 0; ch < 2; ch++) { const d = b.getChannelData(ch); for (let i = 0; i < n; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / n, decay); }
    return b;
  },
  makeNoise(sec) { const c = this.ctx, n = c.sampleRate * sec, b = c.createBuffer(1, n, c.sampleRate), d = b.getChannelData(0); for (let i = 0; i < n; i++) d[i] = Math.random() * 2 - 1; return b; },
  makeBrown(sec) { const c = this.ctx, n = c.sampleRate * sec, b = c.createBuffer(1, n, c.sampleRate), d = b.getChannelData(0); let l = 0; for (let i = 0; i < n; i++) { l = (l + 0.02 * (Math.random() * 2 - 1)) / 1.02; d[i] = l * 3.5; } return b; },
  out(pan, dest) {
    const c = this.ctx, g = c.createGain(); let node = g;
    if (pan != null && c.createStereoPanner) { const p = c.createStereoPanner(); p.pan.value = clamp(pan, -1, 1); g.connect(p); node = p; }
    node.connect(dest || this.sfx); return g;
  },
  spatial(pos, ref = 1) { // pan and distance gain for a world position, from the camera
    if (!pos || !window.CAM) return { pan: 0, gain: 1, muf: 0 };
    const d = _au1.copy(pos).sub(CAM.position), dist = d.length(); d.normalize();
    const right = _au2.set(1, 0, 0).applyQuaternion(CAM.quaternion), fwd = _au3.set(0, 0, -1).applyQuaternion(CAM.quaternion);
    return { pan: clamp(d.dot(right), -1, 1) * 0.85, gain: ref / (1 + dist * 0.22 / ref), muf: d.dot(fwd) < -0.2 ? 1 : 0, dist };
  },
  noiseHit(o) { // {dur, f, q, type, gain, pan, rev, attack, fEnd, dest, brown, delay}
    if (!this.ok) return; const c = this.ctx, t = c.currentTime + (o.delay || 0);
    const s = c.createBufferSource(); s.buffer = o.brown ? this.brownBuf : this.noiseBuf; s.loop = true;
    const f = c.createBiquadFilter(); f.type = o.type || 'bandpass'; f.frequency.setValueAtTime(o.f || 1000, t); f.Q.value = o.q || 1;
    if (o.fEnd) f.frequency.exponentialRampToValueAtTime(o.fEnd, t + o.dur);
    const g = c.createGain(); g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(Math.max(0.0002, o.gain || 0.3), t + (o.attack || 0.004));
    g.gain.exponentialRampToValueAtTime(0.0001, t + o.dur);
    s.connect(f); f.connect(g); g.connect(this.out(o.pan, o.dest));
    if (o.rev) { const rs = c.createGain(); rs.gain.value = o.rev; g.connect(rs); rs.connect(this.revSend); }
    s.start(t, Math.random() * 2); s.stop(t + o.dur + 0.05);
  },
  tone(o) { // {f, fEnd, dur, type, gain, pan, attack, rev, dest, delay, lp}
    if (!this.ok) return; const c = this.ctx, t = c.currentTime + (o.delay || 0);
    const osc = c.createOscillator(); osc.type = o.type || 'sine'; osc.frequency.setValueAtTime(o.f, t);
    if (o.fEnd) osc.frequency.exponentialRampToValueAtTime(Math.max(1, o.fEnd), t + o.dur);
    const g = c.createGain(); g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(Math.max(0.0002, o.gain || 0.2), t + (o.attack || 0.005));
    g.gain.exponentialRampToValueAtTime(0.0001, t + o.dur);
    let last = osc; if (o.lp) { const f = c.createBiquadFilter(); f.type = 'lowpass'; f.frequency.value = o.lp; osc.connect(f); last = f; }
    last.connect(g); g.connect(this.out(o.pan, o.dest));
    if (o.rev) { const rs = c.createGain(); rs.gain.value = o.rev; g.connect(rs); rs.connect(this.revSend); }
    osc.start(t); osc.stop(t + o.dur + 0.05);
  },
  /* ---------- effects ---------- */
  step(surface, loud = 1) {
    const s = { stone: [1300, 0.07, 0.10], wood: [520, 0.09, 0.13], tile: [2100, 0.05, 0.08], carpet: [700, 0.06, 0.05] }[surface] || [1300, 0.07, 0.1];
    this.noiseHit({ f: s[0] * mrand(0.85, 1.15), q: 1.2, dur: s[1], gain: s[2] * loud, rev: 0.25 });
    this.tone({ f: surface === 'wood' ? 140 : 90, fEnd: 50, dur: 0.07, gain: 0.08 * loud });
  },
  land(h) { this.noiseHit({ f: 500, q: 0.8, dur: 0.15, gain: clamp(0.08 + h * 0.05, 0.08, 0.4), type: 'lowpass', rev: 0.3 }); this.tone({ f: 70, fEnd: 38, dur: 0.18, gain: clamp(0.1 + h * 0.05, 0.1, 0.45) }); },
  creak(pos, dur = 1.1, gain = 0.22) { // a door: a sawtooth wandering in pitch, chopped by a square LFO
    if (!this.ok) return; const c = this.ctx, t = c.currentTime, sp = this.spatial(pos);
    const o = c.createOscillator(); o.type = 'sawtooth'; let f = mrand(70, 120); o.frequency.setValueAtTime(f, t);
    for (let i = 1; i <= 12; i++) { f = clamp(f * mrand(0.82, 1.22), 55, 320); o.frequency.linearRampToValueAtTime(f, t + i * dur / 12); }
    const lfo = c.createOscillator(); lfo.type = 'square'; lfo.frequency.setValueAtTime(mrand(12, 26), t); lfo.frequency.linearRampToValueAtTime(mrand(20, 40), t + dur);
    const lg = c.createGain(); lg.gain.value = 0.5; lfo.connect(lg); const amp = c.createGain(); amp.gain.value = 0.5; lg.connect(amp.gain);
    const bp = c.createBiquadFilter(); bp.type = 'bandpass'; bp.frequency.value = mrand(700, 1300); bp.Q.value = 2.5;
    const env = c.createGain(); env.gain.setValueAtTime(0.0001, t); env.gain.exponentialRampToValueAtTime(gain * sp.gain, t + 0.06); env.gain.setValueAtTime(gain * sp.gain, t + dur * 0.7); env.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(bp); bp.connect(amp); amp.connect(env); env.connect(this.out(sp.pan)); const rs = c.createGain(); rs.gain.value = 0.3; env.connect(rs); rs.connect(this.revSend);
    o.start(t); lfo.start(t); o.stop(t + dur + 0.1); lfo.stop(t + dur + 0.1);
  },
  slam(pos, gain = 0.5) {
    const sp = this.spatial(pos);
    this.noiseHit({ f: 700, fEnd: 120, type: 'lowpass', q: 0.7, dur: 0.45, gain: gain * sp.gain, pan: sp.pan, rev: 0.9 });
    this.tone({ f: 62, fEnd: 30, dur: 0.4, gain: gain * 0.9 * sp.gain, pan: sp.pan });
  },
  knock(pos, n = 2, gain = 0.45) {
    const sp = this.spatial(pos);
    for (let i = 0; i < n; i++) {
      const d = i * 0.24;
      this.tone({ f: 170, fEnd: 120, dur: 0.11, gain: gain * sp.gain, pan: sp.pan, delay: d, rev: 0.6, lp: sp.muf ? 500 : 0 });
      this.noiseHit({ f: sp.muf ? 700 : 1600, q: 3, dur: 0.035, gain: gain * 0.5 * sp.gain, pan: sp.pan, delay: d });
    }
  },
  click() { this.noiseHit({ f: 2600, q: 2, dur: 0.03, gain: 0.06 }); },
  rattle(pos) { for (let i = 0; i < 5; i++) this.noiseHit({ f: mrand(1800, 3200), q: 6, dur: 0.04, gain: 0.12, delay: i * 0.06 + mrand(0, 0.02) }); },
  chime(gain = 0.18) { [1, 2.01, 3.03].forEach((m, i) => this.tone({ f: 1046 * m, dur: 0.9 - i * 0.2, gain: gain / (i + 1), rev: 0.6 })); },
  boom(gain = 0.5, delay = 0) { this.tone({ f: 70, fEnd: 24, dur: 1.6, gain, delay, rev: 0.9 }); this.noiseHit({ f: 400, fEnd: 60, type: 'lowpass', dur: 1.8, gain: gain * 0.6, delay, brown: true, rev: 0.9 }); },
  whoosh(pos, gain = 0.3) { const sp = this.spatial(pos, 2); this.noiseHit({ f: 300, fEnd: 1400, q: 1.5, dur: 0.6, gain: gain * sp.gain, pan: sp.pan, attack: 0.25 }); },
  grav() { this.tone({ f: 220, fEnd: 55, dur: 0.7, gain: 0.25, type: 'sine', rev: 0.5 }); this.noiseHit({ f: 800, fEnd: 200, q: 1, dur: 0.6, gain: 0.12, rev: 0.6 }); },
  shriek(pos) { const sp = this.spatial(pos, 2); this.noiseHit({ f: 1500, fEnd: 5200, q: 9, dur: 0.9, gain: 0.4 * sp.gain + 0.1, pan: sp.pan, rev: 0.7 }); this.tone({ f: 900, fEnd: 2300, dur: 0.8, type: 'square', gain: 0.07, pan: sp.pan, lp: 2500 }); },
  /* a slow, out-of-tune music box for the title (one call per note, so it can be scheduled offline too) */
  melody(on) {
    if (!this.ok) return; if (this._mel) { clearInterval(this._mel); this._mel = null; } if (!on) return;
    const notes = [64, 67, 71, 69, 67, 0, 64, 62, 64, 67, 66, 0, 64, 67, 71, 74, 72, 71, 69, 0];
    let i = 0;
    const play = () => {
      const n = notes[i++ % notes.length]; if (!n) return;
      const f = 440 * Math.pow(2, (n - 69) / 12) * mrand(0.992, 1.006);
      this.tone({ f, dur: 1.6, gain: 0.07, type: 'triangle', dest: this.music, rev: 0.7 });
      this.tone({ f: f * 2.01, dur: 0.7, gain: 0.025, dest: this.music });
    };
    this._mel = setInterval(play, 560);
  },
  /* an ambient drone per level: two detuned saws and a fifth through a breathing low-pass, plus optional noise */
  stopBeds(fade = 1.2) {
    if (!this.ok) return; const t = this.ctx.currentTime;
    for (const b of this.beds) { try { b.g.gain.cancelScheduledValues(t); b.g.gain.setTargetAtTime(0.0001, t, fade / 3); b.nodes.forEach(n => { try { n.stop(t + fade + 0.3); } catch (e) { } }); } catch (e) { } }
    this.beds = [];
  },
  bed(spec) { // {root, fifth, cut, noise, noiseF, gain}
    if (!this.ok || !spec) return; this.stopBeds(1.5);
    const c = this.ctx, t = c.currentTime, nodes = [];
    const g = c.createGain(); g.gain.setValueAtTime(0.0001, t); g.gain.setTargetAtTime(spec.gain || 0.45, t + 0.2, 1.2); g.connect(this.bedBus);
    const lp = c.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = spec.cut || 220; lp.Q.value = 1.4; lp.connect(g);
    const lfo = c.createOscillator(); lfo.frequency.value = 0.07; const lg = c.createGain(); lg.gain.value = (spec.cut || 220) * 0.35; lfo.connect(lg); lg.connect(lp.frequency); lfo.start(); nodes.push(lfo);
    const root = spec.root || 55;
    [root, root * 1.006, root * (spec.fifth || 1.5)].forEach((f, i) => { const o = c.createOscillator(); o.type = i < 2 ? 'sawtooth' : 'triangle'; o.frequency.value = f; const og = c.createGain(); og.gain.value = i < 2 ? 0.16 : 0.08; o.connect(og); og.connect(lp); o.start(); nodes.push(o); });
    if (spec.noise) { const s = c.createBufferSource(); s.buffer = this.brownBuf; s.loop = true; const nf = c.createBiquadFilter(); nf.type = 'bandpass'; nf.frequency.value = spec.noiseF || 400; nf.Q.value = 0.6; const ng = c.createGain(); ng.gain.value = spec.noise; s.connect(nf); nf.connect(ng); ng.connect(g); s.start(); nodes.push(s); }
    this.beds.push({ g, nodes });
  }
};
const _au1 = new THREE.Vector3(), _au2 = new THREE.Vector3(), _au3 = new THREE.Vector3();
