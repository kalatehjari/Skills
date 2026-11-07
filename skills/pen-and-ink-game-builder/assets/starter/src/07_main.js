/* ===================== boot, frame loop, test hooks ===================== */
const ERRS = [];
function oops(e) { const m = String(e && (e.stack || e.message) || e); if (ERRS.includes(m)) return; ERRS.push(m); console.error(e); }
function boot() {
  try { R.init($('gl')); }
  catch (e) { $('loading').innerHTML = '<div style="max-width:30ch;text-align:center;font:20px/1.4 var(--fell)">This game needs WebGL. Try another browser, or turn on hardware acceleration.</div>'; return; }
  initMats(); IN.init($('gl')); UI.init(); GAME.init();
  addEventListener('resize', () => R.resize());
  // browsers only allow sound after a gesture: start it on the first one
  const startAudio = () => { AU.init(); AU.resume(); if (GAME.state === 'title' && !AU._titleOn) { AU._titleOn = 1; AU.bed(GAME.L.env.bed); AU.melody(true); } };
  addEventListener('pointerdown', startAudio); addEventListener('keydown', startAudio); addEventListener('touchstart', startAudio, { passive: true });
  document.addEventListener('visibilitychange', () => { if (document.hidden && GAME.state === 'play') GAME.pause(); });
  let last = performance.now();
  const frame = t => {
    requestAnimationFrame(frame);
    const dt = clamp((t - last) / 1000, 0, 0.05); last = t; // a long hitch never becomes one giant physics step
    try { IN.pollPad(); } catch (e) { IN.gpOK = false; }
    try { GAME.update(dt); } catch (e) { oops(e); }
    try { GAME.render(); } catch (e) { oops(e); }
  };
  requestAnimationFrame(frame);
  setTimeout(() => { const l = $('loading'); if (!l) return; l.style.transition = 'opacity .8s'; l.style.opacity = 0; setTimeout(() => l.remove(), 900); }, 250);
  // test hooks: scripts/shoot.py and the smoke test drive the game through these (stub requestAnimationFrame, then step())
  window.__game = {
    GAME, PL, R, U, POST, LEVELS, IN, SET, UI, AU, ERRS, V3, Q4, M4, faceQ, CAM: () => CAM,
    play(i = 1) { GAME.newRun(i); return GAME.idx; },
    step(n = 1, dt = 1 / 30, render = true) { for (let k = 0; k < n; k++) GAME.update(dt); if (render) GAME.render(); return this.state(); },
    tp(x, y, z) { PL.pos.set(x, y, z); PL.vel.set(0, 0, 0); },
    look(yaw, pitch = 0) { PL.yaw = yaw; PL.pitch = pitch; },
    hold(code, on = true) { IN.keys[code] = on; },                 // held keys: KeyW/A/S/D, ShiftLeft
    press(action) { IN.edge(action); },                             // one press: 'jump', 'act', 'crouch', 'lamp', 'pause'
    openExit() { const d = GAME.L.exitDoor; if (!d) return 'no exit'; d.locked = false; if (GAME.next) GAME.linkNext(); d.open(true); d.angle = d.target; d.update(0); return GAME.next ? 'open, next linked' : 'open, next not built yet'; },
    faceExit(back = 0.8) { // stand in front of the exit door, looking through it
      const d = GAME.L.exitDoor; PL.setFrameQ(d.upQ ? d.upQ.clone() : new Q4());
      PL.pos.copy(d.pos).addScaledVector(d.fwd, -back); PL.vel.set(0, 0, 0);
      const fl = d.fwd.clone().applyQuaternion(PL.qGto.clone().invert()); PL.yaw = Math.atan2(-fl.x, -fl.z); PL.pitch = 0; return 'placed';
    },
    state() {
      return { state: GAME.state, idx: GAME.idx, level: GAME.L && GAME.L.name, pos: PL.pos.toArray().map(v => +v.toFixed(2)), up: PL.up.toArray().map(v => Math.round(v)),
        grounded: PL.grounded, next: !!GAME.next, portal: !!GAME.portalDoor, errs: ERRS.slice(0, 5) };
    }
  };
}
// wait briefly for the embedded typefaces, so text drawn onto canvases uses them from the first frame
{
  let booted = false; const go = () => { if (booted) return; booted = true; boot(); };
  try { Promise.all(['24px "IM Fell English"', 'italic 24px "IM Fell English"', '24px "IM Fell English SC"', '24px "Special Elite"'].map(f => document.fonts.load(f))).then(go, go); } catch (e) { go(); }
  setTimeout(go, 1500);
}
