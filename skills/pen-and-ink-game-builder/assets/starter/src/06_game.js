/* ===================== game: states, level streaming through portal doors, interaction, mood, UI =====================
   States: title -> play <-> pause, play -> caught -> play. One level is live (GAME.L); the next one is built in the
   background (GAME.next) and linked to the exit door, so opening it shows the next level through the doorway. */
let CAM = null;
const roman = n => { let s = ''; for (const [k, r] of [[10, 'X'], [9, 'IX'], [5, 'V'], [4, 'IV'], [1, 'I']]) while (n >= k) { s += r; n -= k; } return s; };
// one-time tutorial lines, worded for the device the player is actually using
const HINTS = {
  move: { kb: 'WASD to move, the mouse to look. Click to capture the mouse.', touch: 'Left thumb moves. Drag on the right to look.', pad: 'Left stick moves, right stick looks.' },
  jump: { kb: 'Space jumps. Shift runs.', touch: 'The jump button jumps. Push the stick all the way to run.', pad: 'A jumps. Click the left stick to run.' },
  open: { kb: 'E opens doors.', touch: 'The open button opens doors.', pad: 'X opens doors.' },
  crouch: { kb: 'Something watches the floor. C crouches; it sees less of you.', touch: 'Something watches the floor. Duck, and it sees less of you.', pad: 'Something watches the floor. B crouches.' },
  arch: { all: 'Walk through the blue arch. Down will change.' }
};
const GAME = {
  state: 'boot', time: 0, L: null, next: null, idx: 1, reverse: null, shown: new Set(), threat: 0, threatS: 0, pulse: 0, portalDoor: null,
  init() { CAM = new THREE.PerspectiveCamera(SET.fov, innerWidth / innerHeight, 0.05, 900); window.CAM = CAM; this.titleLevel(); },
  nextIdx(i) { const d = LEVELS[i]; if (d && d.next !== undefined) return d.next; return LEVELS[i + 1] ? i + 1 : null; },
  buildLevel(i) {
    const def = LEVELS[i]; seedRng(i * 7919 + 13); // the same level always builds the same way
    const L = new Level(i, def.name); L.def = def; def.build(L);
    L.finalize(); R.bakeShadow(L); return L;
  },
  disposeLevel(L) { if (L && !L.disposed) L.dispose(); },
  disposeAll() { for (const l of [this.L, this.next, this.reverse && this.reverse.old]) this.disposeLevel(l); this.L = this.next = this.reverse = null; this.portalDoor = null; },
  /* ---------- flow ---------- */
  titleLevel() {
    this.state = 'title'; this.disposeAll(); this.idx = 1; this.L = this.buildLevel(1); this.titleT = 0;
    this.spawnAt(this.L); POST.uFade.value = 1; UI.show('title'); UI.hud(false);
    if (AU.ok) { AU.bed(this.L.env.bed); AU.melody(true); }
  },
  newRun(startIdx = 1) { this.shown = new Set(); this.playLevel(startIdx); },
  playLevel(i) {
    AU.melody(false); this.disposeAll(); this.idx = i; this.L = this.buildLevel(i); this.spawnAt(this.L);
    const ent = this.L.entrance; if (ent) { ent.angle = ent.target = 0; ent.locked = true; ent.update(0); }
    this.startLevel(this.L, false);
  },
  spawnAt(L) { const sp = L.spawn || { pos: new V3(), yaw: 0 }; PL.reset(L, sp.pos, sp.yaw); if (sp.q) PL.setFrameQ(sp.q); PL.frozen = false; },
  startLevel(L, viaPortal) {
    this.state = 'play'; this.lvlTime = 0; L.started = true;
    UI.show(null); UI.hud(true);
    if (AU.ok) AU.bed(L.env.bed);
    this.toast(`${roman(L.idx)}. ${L.def.name}` + (L.def.sub ? `\n${L.def.sub}` : ''), 2.6);
    this.fadeTo(0, viaPortal ? 0 : 0.8);
    if (L.def.onStart) L.def.onStart(L, viaPortal);
    this.moveHintT = L.idx === 1 && !viaPortal ? 2.6 : null; // counted in game time (pauses, and exact in tests)
    this.needNext = this.nextIdx(L.idx) != null && L.exitDoor ? (viaPortal ? 1.6 : 0.4) : -1;
  },
  linkNext() { // the exit door of this level now looks into the entrance of the next
    const L = this.L, n = this.next; if (!L || !n || !L.exitDoor || !n.entrance) return;
    const e = L.exitDoor; e.portal = { level: n, M: new M4().multiplyMatrices(n.entrance.F, e.Finv), plane: n.entrance.plane, hideLeaf: n.entrance.pivot, dir: 1 };
    n.entrance.angle = n.entrance.target = 0; n.entrance.update(0);
  },
  crossPortal(door) { // the camera passed through an open exit door: carry the player (and gravity) across
    const P = door.portal, M = P.M, qM = new Q4().setFromRotationMatrix(M);
    PL.pos.applyMatrix4(M); PL.vel.applyQuaternion(qM); PL.eyeOff.applyQuaternion(qM);
    PL.setFrameQ(qM.clone().multiply(PL.qGto)); PL.safe = [];
    CAM.position.applyMatrix4(M); CAM.quaternion.premultiply(qM);
    const old = this.L, nl = P.level;
    this.L = nl; this.next = null; this.idx = nl.idx;
    const ent = nl.entrance;
    ent.angle = ent.target = ent.swingIn ? -1.62 : 1.62; ent.locked = true; ent.update(0);
    // look back and you see where you came from, until the entrance slams behind you
    ent.portal = { level: old, M: new M4().copy(M).invert(), plane: new THREE.Plane().setFromNormalAndCoplanarPoint(door.fwd.clone().negate(), door.pos), hideLeaf: door.pivot, dir: -1, reverse: true };
    if (ent.block) ent.block.on = true;
    this.reverse = { ent, old, t: 0 };
    this.startLevel(nl, true);
  },
  toTitle() { UI.hud(false); AU.resume(); this.titleLevel(); },
  /* ---------- per frame ---------- */
  update(dt) {
    this.time += dt; U.uTime.value = this.time;
    if (this.state === 'title') return this.updateTitle(dt);
    if (this.state === 'caught') { this.caughtT -= dt; this.updateFx(dt); if (this.caughtT <= 0) this.respawn(); return; }
    if (this.state !== 'play') return;
    const L = this.L; if (!L) return;
    this.lvlTime += dt; L.t += dt; this.threat = 0;
    if (this.needNext > 0) { this.needNext -= dt; if (this.needNext <= 0) { if (this.reverse) this.needNext = 0.2; else { this.next = this.buildLevel(this.nextIdx(L.idx)); this.linkNext(); } } }
    if (this.reverse) {
      const r = this.reverse; r.t += dt;
      if (!r.closing && (r.t > 1.1 || PL.pos.distanceTo(r.ent.pos) > 2.4)) {
        r.closing = true; r.ent.slamWhenClear();
        r.ent.onSlam = () => { r.ent.portal = null; if (r.ent.block) r.ent.block.on = false; r.ent.onSlam = null; r.done = true; };
      }
      if (r.done) { this.disposeLevel(r.old); this.reverse = null; }
    }
    if (this.moveHintT != null && (this.moveHintT -= dt) <= 0) { this.moveHintT = null; this.hint('move'); }
    if (IN.take('pause')) return this.pause();
    if (IN.take('lamp')) { PL.lampOn = !PL.lampOn; AU.click(); }
    PL.lampI = damp(PL.lampI, PL.lampOn ? 1 : 0, 12, dt);
    PL.look(dt);
    for (const e of L.ents) if (e.alive !== false && e.update) e.update(dt);
    PL.physics(L, dt);
    for (const d of L.doors) d.update(dt);
    for (const p of L.pickups) p.update(dt);
    for (const pl of L.plights) if (pl.flicker) pl.flick = 1 - pl.flicker * (Math.random() < 0.08 ? Math.random() : 0) * (0.5 + 0.5 * Math.sin(this.time * 23 + pl.phase));
    this.updateTriggers(L); this.updateGravZones(L);
    if (L.def.update) L.def.update(L, dt);
    if (this.L !== L || this.state !== 'play') return; // the level's update may have ended the level
    PL.camera(CAM, dt);
    this.portalCheck(L);
    this.updateInteract(L);
    this.updateFx(dt);
  },
  updateTitle(dt) {
    this.titleT += dt; const L = this.L;
    const v = L.def.titleView ? L.def.titleView(this.titleT) : (() => { const c = L.bounds.getCenter(new V3()), t = this.titleT * 0.05; return { pos: [c.x + Math.sin(t) * 18, c.y + 8, c.z + Math.cos(t) * 18], look: [c.x, c.y, c.z] }; })();
    CAM.position.set(...v.pos); CAM.lookAt(...v.look);
    U.uBoil.value = 0.22; U.uWarp.value = 0.05; POST.uTendril.value = 0.3; POST.uDouble.value = POST.uSwirl.value = POST.uWave.value = POST.uTunnel.value = POST.uChrom.value = 0;
    POST.uFade.value = Math.max(0, POST.uFade.value - dt * 0.6); POST.uFlash.value = 0; POST.uInvert.value = 0;
    for (const d of L.doors) d.update(dt);
  },
  updateTriggers(L) {
    const c = PL.center;
    for (const t of L.triggers) {
      if (t.done) continue;
      const inside = c.x > t.min[0] && c.x < t.max[0] && c.y > t.min[1] && c.y < t.max[1] && c.z > t.min[2] && c.z < t.max[2];
      if (inside && !t.inside) { t.fn(); if (t.once) t.done = true; }
      t.inside = inside;
    }
  },
  updateGravZones(L) { // { from: face, to: face, box: [x0,y0,z0,x1,y1,z1], place: feet => new feet }
    if (PL.gravLock > 0) return; const c = PL.center;
    for (const z of L.gravZones) {
      if (!onFace(z.from)) continue; const b = z.box;
      if (c.x > b[0] && c.x < b[3] && c.y > b[1] && c.y < b[4] && c.z > b[2] && c.z < b[5]) { gravSwitch(z.to, z.place(PL.pos), z.axis); if (z.onSwitch) z.onSwitch(); break; }
    }
  },
  portalCheck(L) { // show the portal of the nearest visible open door, and cross it when the camera passes its plane
    let best = null, bd = 1e9; CAM.updateMatrixWorld();
    _frust.setFromProjectionMatrix(_m4a.multiplyMatrices(CAM.projectionMatrix, CAM.matrixWorldInverse));
    for (const d of L.doors) {
      const P = d.portal, show = !!P && (d.isOpen || !!P.reverse);
      d.aperture.visible = show;
      if (!show) { d.prevLocal = null; continue; }
      const lp = d.local(CAM.position, _v3c), dir = P.dir || 1;
      if (d.prevLocal && Math.abs(lp.x) < d.w / 2 + 0.05 && lp.y > -0.4 && lp.y < d.h + 0.4 && d.prevLocal.z * dir < 0 && lp.z * dir >= 0 && !P.reverse && d.isOpen) {
        d.prevLocal = null; this.crossPortal(d); return this.portalCheck(this.L);
      }
      d.prevLocal = (d.prevLocal || new V3()).copy(lp);
      const dist = d.pos.distanceTo(CAM.position);
      if (dist < 80 && _frust.intersectsObject(d.aperture) && dist < bd) { bd = dist; best = d; }
    }
    for (const d of L.doors) if (d !== best) d.aperture.visible = false; // one portal is rendered per frame: only its doorway shows it
    this.portalDoor = best;
  },
  updateInteract(L) {
    let best = null, bs = -1; const eye = CAM.position, fw = PL.forward(_v3b);
    const consider = (p, r, cos, label, fn, isDoor) => {
      const d = _v3a.copy(p).sub(eye), dist = d.length(); if (dist > r) return; d.normalize(); const c = d.dot(fw);
      if (c < cos) return; const score = c - dist * 0.02; if (score <= bs) return;
      if (this.los(eye, p, 0.3)) { bs = score; best = { label, fn, isDoor }; }
    };
    for (const d of L.doors) if (d.canInteract() && d.kind !== 'entrance') consider(d.interactPoint().clone(), 2.7, 0.84, d.prompt, () => d.tryOpen(), true);
    for (const d of L.doors) if (d.kind === 'entrance' && d.canInteract() && !d.portal) consider(d.interactPoint().clone(), 2.2, 0.9, 'Open', () => d.tryOpen(), true);
    for (const it of L.inter) if (it.on && (!it.when || it.when())) consider(it.pos, it.r, it.cos, it.prompt, it.fn);
    UI.prompt(best && best.label); if (best && best.isDoor) this.hint('open');
    if (IN.take('act') && best) { best.fn(); AU.click(); }
  },
  los(a, b, slack = 0.25) { const d = _v3d.copy(b).sub(a), len = d.length(); if (len < 0.01) return true; d.divideScalar(len); return this.L.ray(a, d, len) >= len - slack; },
  isSeen(p, maxD) { // is world point p on screen and unblocked?
    if (_v3d.copy(p).sub(CAM.position).length() > maxD) return false;
    _v3e.copy(p).project(CAM); if (_v3e.z > 1 || Math.abs(_v3e.x) > 1.05 || Math.abs(_v3e.y) > 1.05) return false;
    return this.los(CAM.position, p, 0.4);
  },
  /* ---------- mood: each level's env.mood, raised by threat (0..1, set each frame by enemies) and pulse (a decaying spike) ---------- */
  updateFx(dt) {
    const L = this.L; if (!L) return;
    const m = L.env.mood, calm = SET.calm ? 1 : 0;
    this.threatS = damp(this.threatS, this.threat, 3, dt); this.pulse = Math.max(0, this.pulse - dt * 0.8);
    const k = this.threatS, p = this.pulse;
    U.uBoil.value = clamp(m.boil + k * 0.55 + p * 0.6, 0, 1.3);
    U.uWarp.value = (m.warp + p * 0.4) * (calm ? 0.25 : 1);
    POST.uDouble.value = m.double + k * 0.35; POST.uSwirl.value = m.swirl + p * 0.3; POST.uWave.value = m.wave + p * 0.5;
    POST.uTendril.value = m.tendril + k * 0.65; POST.uTunnel.value = k * 0.3; POST.uChrom.value = (m.chrom + p * 0.5) * (calm ? 0 : 1);
    U.uCalm.value = calm;
    if (this.flashT > 0) { this.flashT -= dt; POST.uFlash.value = Math.max(0, this.flashA * this.flashT / this.flashD); } else POST.uFlash.value = 0;
    if (this.state === 'play' && this.fadeT == null) POST.uFade.value = damp(POST.uFade.value, 0, 3, dt);
    if (this.fadeT != null) { this.fadeT -= dt; const t = clamp(1 - this.fadeT / this.fadeD, 0, 1); POST.uFade.value = lerp(this.fadeFrom, this.fadeTarget, t); if (this.fadeT <= 0) this.fadeT = null; }
    CAM.fov = damp(CAM.fov, SET.fov + (PL.sprinting ? 6 : 0), 6, dt); CAM.updateProjectionMatrix();
  },
  /* ---------- events ---------- */
  onPickup(p) { if (p.kind === 'note' && p.o.text) this.toast(p.o.text, 6); },
  caught(by) { // an enemy got you: ink flash, then back to the level's start
    if (this.state !== 'play') return; this.state = 'caught'; this.caughtT = 1.3;
    AU.shriek(by && by.pos); this.flash(0.6, 0); this.shake(0.6); this.fadeTo(1, 1.1); PL.frozen = true; UI.prompt(null);
  },
  respawn() {
    const L = this.L; this.state = 'play'; this.spawnAt(L);
    for (const e of L.ents) if (e.reset) e.reset();
    this.fadeTo(0, 0.6); this.toast('Again.', 1.4);
  },
  voidFall() { // fell off the world: back to a recent safe spot
    if (this.voidT) return; this.voidT = 1; AU.whoosh(null, 0.4); this.fadeTo(1, 0.25);
    setTimeout(() => { if (this.L && this.state === 'play' && !PL.respawnSafe(4)) this.spawnAt(this.L); this.fadeTo(0, 0.5); this.voidT = 0; }, 260);
  },
  pause() {
    if (this.state !== 'play') return; this.state = 'pause'; this.ignoreUnlock = true;
    if (document.exitPointerLock) try { document.exitPointerLock(); } catch (e) { }
    setTimeout(() => this.ignoreUnlock = false, 200); UI.show('pause'); if (AU.ctx) try { AU.ctx.suspend(); } catch (e) { }
  },
  resume() { this.state = 'play'; UI.show(null); IN.clearEdges(); if (AU.ctx) AU.resume(); if (!IS_TOUCH_ONLY()) IN.requestLock(); },
  /* ---------- feedback ---------- */
  shake(a) { PL.trauma = Math.min(1, PL.trauma + a); },
  flash(a, tone) { this.flashA = a; this.flashD = 0.35; this.flashT = 0.35; POST.uFlashTone.value = tone; }, // tone 0 = ink, 1 = paper
  fadeTo(target, dur) { this.fadeFrom = POST.uFade.value; this.fadeTarget = target; this.fadeD = Math.max(0.001, dur); this.fadeT = dur; if (!dur) { POST.uFade.value = target; this.fadeT = null; } },
  toast(msg, dur = 2.2) { UI.toast(msg, dur); },
  hint(k) {
    if (this.shown.has(k)) return; this.shown.add(k); const h = HINTS[k]; if (!h) return;
    const dev = IN.lastDevice === 'touch' ? 'touch' : IN.lastDevice === 'pad' ? 'pad' : 'kb';
    this.toast(h.all || h[dev] || h.kb, 4.2);
  },
  render() {
    if (!this.L) return;
    CAM.updateMatrixWorld();
    const pd = this.state === 'title' ? null : this.portalDoor;
    R.render(this.L, CAM, pd ? pd.portal : null);
  }
};
const _frust = new THREE.Frustum(), _v3d = new V3(), _v3e = new V3();

/* ===================== UI: the screens live in 00_head.html; this only shows, hides and fills them ===================== */
const UI = {
  init() {
    $('bBegin').addEventListener('click', () => { AU.init(); AU.resume(); GAME.newRun(1); if (!IS_TOUCH_ONLY()) IN.requestLock(); });
    $('bResume').addEventListener('click', () => GAME.resume());
  },
  show(id) { for (const s of document.querySelectorAll('.screen')) s.classList.toggle('show', s.id === id); $('touch').classList.toggle('show', !id && $('hud').classList.contains('show') && IN.usedTouch); },
  hud(on) { $('hud').classList.toggle('show', on); $('touch').classList.toggle('show', on && IN.usedTouch); },
  toast(msg, dur) { const t = $('toast'); t.textContent = msg; t.classList.add('show'); clearTimeout(this._tt); this._tt = setTimeout(() => t.classList.remove('show'), dur * 1000); },
  prompt(label) { if (label === this._pl) return; this._pl = label; const p = $('prompt'); p.textContent = label || ''; p.classList.toggle('show', !!label); },
  onKey(e) { if (GAME.state === 'pause' && (e.code === 'Escape' || e.code === 'KeyP')) GAME.resume(); },
  onPad(a) {
    if (GAME.state === 'pause' && (a === 'pause' || a === 'jump')) GAME.resume();
    else if (GAME.state === 'title' && (a === 'jump' || a === 'act')) $('bBegin').click();
  }
};
