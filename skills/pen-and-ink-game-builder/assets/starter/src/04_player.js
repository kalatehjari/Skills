/* ===================== input: keyboard + mouse (pointer lock), touch (floating joystick + drag to look), gamepad =====================
   Actions are edges: IN.edge(name) when pressed, IN.take(name) once per press in the game loop. */
const IN = {
  keys: {}, mdx: 0, mdy: 0, rmb: false, lmb: false, locked: false, lockTried: false, drag: false,
  joy: { x: 0, y: 0, id: null, ox: 0, oy: 0, sprint: false }, lookId: null, lx: 0, ly: 0,
  edges: {}, gp: null, gpOK: true, gpPrev: {}, gpLook: { x: 0, y: 0 }, gpMove: { x: 0, y: 0 }, gpSprint: false,
  usedTouch: IS_TOUCH, lastDevice: IS_TOUCH ? 'touch' : 'kb',
  edge(n) { this.edges[n] = true; },
  take(n) { const v = !!this.edges[n]; this.edges[n] = false; return v; },
  clearEdges() { this.edges = {}; },
  init(canvas) {
    const KE = { Space: 'jump', KeyE: 'act', Enter: 'act', KeyF: 'lamp', KeyP: 'pause', Escape: 'pause', KeyC: 'crouch', ControlLeft: 'crouch' };
    addEventListener('keydown', e => {
      if (e.repeat) { if (GAME.state === 'play' && e.code === 'Space') e.preventDefault(); return; }
      this.keys[e.code] = true; this.lastDevice = 'kb';
      if (GAME.state === 'play' && ['Space', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.code)) e.preventDefault();
      const n = KE[e.code]; if (n) this.edge(n);
      AU.init(); AU.resume();
      UI.onKey(e);
    });
    addEventListener('keyup', e => { this.keys[e.code] = false; });
    addEventListener('blur', () => { this.keys = {}; this.rmb = false; this.lmb = false; });
    canvas.addEventListener('mousedown', e => {
      AU.init(); AU.resume(); this.lastDevice = 'kb';
      if (e.button === 2) this.rmb = true;
      if (e.button === 0) { this.lmb = true; this.drag = true; }
      if (GAME.state === 'play' && !this.locked && !IS_TOUCH_ONLY()) this.requestLock();
    });
    addEventListener('mouseup', e => { if (e.button === 2) this.rmb = false; if (e.button === 0) { this.lmb = false; this.drag = false; } });
    addEventListener('mousemove', e => {
      if (GAME.state !== 'play') return;
      if (this.locked) { this.mdx += e.movementX || 0; this.mdy += e.movementY || 0; }
      else if (this.drag) { this.mdx += (e.movementX || 0) * 1.2; this.mdy += (e.movementY || 0) * 1.2; }
    });
    canvas.addEventListener('contextmenu', e => e.preventDefault());
    document.addEventListener('pointerlockchange', () => { this.locked = document.pointerLockElement === canvas; if (!this.locked && GAME.state === 'play' && this._wasLocked && !GAME.ignoreUnlock) GAME.pause(); this._wasLocked = this.locked; });
    document.addEventListener('pointerlockerror', () => { this.locked = false; });
    // ---- touch ----
    const joy = $('joy'), knob = $('joyK');
    const btns = { tAct: 'act', tJump: 'jump', tLamp: 'lamp', tCrouch: 'crouch', tPause: 'pause' }; // add .tb buttons with these ids in 00_head.html
    const onStart = e => {
      AU.init(); AU.resume(); this.usedTouch = true; this.lastDevice = 'touch';
      if (GAME.state !== 'play') return;
      for (const t of e.changedTouches) {
        const el = t.target.closest ? t.target.closest('.tb') : null;
        if (el) {
          if (btns[el.id]) { this.edge(btns[el.id]); el.classList.add('on'); setTimeout(() => el.classList.remove('on'), 140); }
          continue;
        }
        const leftSide = SET.lefty ? t.clientX > innerWidth * 0.55 : t.clientX < innerWidth * 0.45;
        if (leftSide && this.joy.id === null) {
          this.joy.id = t.identifier;
          const r = 64, x = clamp(t.clientX, r + 8, innerWidth - r - 8), y = clamp(t.clientY, r + 8, innerHeight - r - 8);
          this.joy.ox = x; this.joy.oy = y; joy.style.left = (x - r) + 'px'; joy.style.top = (y - r) + 'px'; joy.style.bottom = 'auto';
          this.joy.x = 0; this.joy.y = 0; knob.style.transform = 'translate(0px,0px)';
        } else if (this.lookId === null) { this.lookId = t.identifier; this.lx = t.clientX; this.ly = t.clientY; }
      }
      if (e.cancelable) e.preventDefault();
    };
    const onMove = e => {
      if (GAME.state !== 'play') return;
      for (const t of e.changedTouches) {
        if (t.identifier === this.joy.id) {
          let dx = t.clientX - this.joy.ox, dy = t.clientY - this.joy.oy; const l = Math.hypot(dx, dy), mx = 56;
          if (l > mx) { dx *= mx / l; dy *= mx / l; }
          this.joy.x = dx / mx; this.joy.y = -dy / mx; knob.style.transform = `translate(${dx}px,${dy}px)`;
          this.joy.sprint = l > mx * 0.97; joy.classList.toggle('sprint', this.joy.sprint);
        } else if (t.identifier === this.lookId) {
          this.mdx += (t.clientX - this.lx) * 2.1; this.mdy += (t.clientY - this.ly) * 2.1; this.lx = t.clientX; this.ly = t.clientY;
        }
      }
      if (e.cancelable) e.preventDefault();
    };
    const onEnd = e => {
      for (const t of e.changedTouches) {
        if (t.identifier === this.joy.id) { this.joy.id = null; this.joy.x = 0; this.joy.y = 0; this.joy.sprint = false; knob.style.transform = 'translate(0px,0px)'; joy.classList.remove('sprint'); resetJoy(); }
        if (t.identifier === this.lookId) this.lookId = null;
      }
    };
    const resetJoy = () => { joy.style.left = ''; joy.style.top = ''; joy.style.bottom = ''; };
    const tl = $('touch');
    for (const el of [canvas, tl]) { el.addEventListener('touchstart', onStart, { passive: false }); el.addEventListener('touchmove', onMove, { passive: false }); el.addEventListener('touchend', onEnd); el.addEventListener('touchcancel', onEnd); }
  },
  requestLock() {
    const c = $('gl'); if (!c.requestPointerLock) return;
    try { const p = c.requestPointerLock(); if (p && p.catch) p.catch(() => { this.locked = false; }); } catch (e) { }
  },
  pollPad() {
    if (!this.gpOK) return;
    let pads;
    try {
      if (document.featurePolicy && document.featurePolicy.allowsFeature && !document.featurePolicy.allowsFeature('gamepad')) { this.gpOK = false; return; }
      pads = navigator.getGamepads ? navigator.getGamepads() : null;
    } catch (e) { this.gpOK = false; return; }
    if (!pads) return;
    let gp = null; for (const p of pads) if (p && p.connected) { gp = p; break; }
    this.gp = gp; if (!gp) { this.gpMove.x = this.gpMove.y = this.gpLook.x = this.gpLook.y = 0; return; }
    const dz = v => Math.abs(v) < 0.16 ? 0 : (v - Math.sign(v) * 0.16) / 0.84;
    this.gpMove.x = dz(gp.axes[0] || 0); this.gpMove.y = -dz(gp.axes[1] || 0);
    this.gpLook.x = dz(gp.axes[2] || 0); this.gpLook.y = dz(gp.axes[3] || 0);
    const b = i => !!(gp.buttons[i] && (gp.buttons[i].pressed || gp.buttons[i].value > 0.5));
    const map = { 0: 'jump', 2: 'act', 1: 'crouch', 9: 'pause', 6: 'lamp' }; // standard mapping: A, X, B, Start, LT
    for (const k in map) { const v = b(+k); if (v && !this.gpPrev[k]) { this.lastDevice = 'pad'; this.edge(map[k]); UI.onPad(map[k]); } this.gpPrev[k] = v; }
    for (const k of [12, 13, 14, 15]) { const v = b(k); if (v && !this.gpPrev[k]) UI.onPad(k === 12 ? 'up' : k === 13 ? 'down' : k === 14 ? 'left' : 'right'); this.gpPrev[k] = v; }
    this.gpSprint = b(10);
    if (Math.abs(this.gpMove.x) + Math.abs(this.gpMove.y) + Math.abs(this.gpLook.x) > 0.2) this.lastDevice = 'pad';
  }
};
function IS_TOUCH_ONLY() { return IN.lastDevice === 'touch'; }

/* ===================== player: capsule-ish AABB, any-axis gravity (PL.ax 0/1/2, PL.sg ±1), stairs step-up, coyote time =====================
   PL.pos is the feet. qG rotates the world-up frame onto the current gravity; yaw/pitch are relative to it. */
const PL = {
  pos: new V3(), vel: new V3(), up: new V3(0, 1, 0), ax: 1, sg: 1,
  qG: new Q4(), qGfrom: new Q4(), qGto: new Q4(), gT: 1, yaw: 0, pitch: 0, roll: 0,
  grounded: false, coyote: 0, jumpBuf: 0, crouch: false, ch: 0, sprinting: false, stamina: 1,
  H: 1.72, Hc: 1.12, eye: 1.6, eyeC: 0.98, R: 0.28, stepH: 0.46,
  lampOn: false,
  stepAcc: 0, bob: 0, bobAmt: 0, eyeOff: new V3(), trauma: 0, fovKick: 0, center: new V3(), eyePos: new V3(),
  lampPos: new V3(), lampDir: new V3(0, 0, -1), lampI: 0, lampRange: 15,
  slow: 1, safe: [], safeT: 0, peakU: 0, groundCol: null, frozen: false,
  gravLock: 0, lastSurf: 'stone',
  reset(L, pos, yaw, opts = {}) {
    this.pos.copy(pos); this.vel.set(0, 0, 0); this.yaw = yaw; this.pitch = opts.pitch || 0; this.roll = 0;
    this.qG.identity(); this.qGto.identity(); this.qGfrom.identity(); this.gT = 1; this.ax = 1; this.sg = 1; this.up.set(0, 1, 0); this.gravLock = 0; this.grounded = false; this.eyeOff.set(0, 0, 0); this.safe = []; this.safeT = 0;
    this.slow = 1; this.crouch = false; this.ch = 0; this.trauma = 0; this.peakU = this.u(); this.center.copy(pos).addScaledVector(this.up, this.H * 0.5);
  },
  axisVec(ax, sg, out) { return (out || new V3()).set(ax === 0 ? sg : 0, ax === 1 ? sg : 0, ax === 2 ? sg : 0); },
  setGravity(ax, sg, instant, rotateVel = true, axisOverride) {
    const nu = this.axisVec(ax, sg);
    const q = (axisOverride && this.up.dot(nu) < -0.99) ? new Q4().setFromAxisAngle(axisOverride.clone().normalize(), Math.PI) : new Q4().setFromUnitVectors(this.up, nu);
    if (instant) { this.qG.premultiply(q); this.qGto.copy(this.qG); this.qGfrom.copy(this.qG); this.gT = 1; }
    else { this.qGfrom.copy(this.curQG()); this.qGto.premultiply(q); this.gT = 0; }
    if (rotateVel) this.vel.applyQuaternion(q);
    this.ax = ax; this.sg = sg; this.up.copy(nu); this.gravLock = 0.6;
  },
  setFrameQ(q) { // set gravity frame directly (portal transitions)
    this.qG.copy(q); this.qGto.copy(q); this.qGfrom.copy(q); this.gT = 1;
    const u = new V3(0, 1, 0).applyQuaternion(q);
    const a = [Math.abs(u.x), Math.abs(u.y), Math.abs(u.z)]; const ax = a[0] > a[1] && a[0] > a[2] ? 0 : a[1] > a[2] ? 1 : 2;
    this.ax = ax; this.sg = (ax === 0 ? u.x : ax === 1 ? u.y : u.z) > 0 ? 1 : -1; this.up.copy(this.axisVec(this.ax, this.sg));
    // snap the frame to the exact axis
    const fix = new Q4().setFromUnitVectors(u.normalize(), this.up); this.qG.premultiply(fix); this.qGto.copy(this.qG); this.qGfrom.copy(this.qG);
  },
  curQG() { return this.gT >= 1 ? this.qGto : _q4a.copy(this.qGfrom).slerp(this.qGto, smooth(this.gT)); },
  comp(v, i) { return i === 0 ? v.x : i === 1 ? v.y : v.z; },
  setComp(v, i, x) { if (i === 0) v.x = x; else if (i === 1) v.y = x; else v.z = x; },
  u() { return this.comp(this.pos, this.ax) * this.sg; },
  height() { return lerp(this.H, this.Hc, this.ch); },
  box(H, mn, mx) {
    for (let i = 0; i < 3; i++) {
      const c = this.comp(this.pos, i);
      if (i === this.ax) { if (this.sg > 0) { mn[i] = c; mx[i] = c + H; } else { mn[i] = c - H; mx[i] = c; } }
      else { mn[i] = c - this.R; mx[i] = c + this.R; }
    }
  },
  gather(L, mn, mx) {
    _cands.length = 0;
    const e = 0.6; _qmn[0] = mn[0] - e; _qmn[1] = mn[1] - e; _qmn[2] = mn[2] - e; _qmx[0] = mx[0] + e; _qmx[1] = mx[1] + e; _qmx[2] = mx[2] + e;
    L.hash.query(_qmn, _qmx, _cands);
    for (const c of L.dyn) if (c.on) _cands.push(c);
    return _cands;
  },
  overlap(mn, mx, c) { return mn[0] < c.max[0] && mx[0] > c.min[0] && mn[1] < c.max[1] && mx[1] > c.min[1] && mn[2] < c.max[2] && mx[2] > c.min[2]; },
  anyOverlap(L, mn, mx) { const cs = this.gather(L, mn, mx); for (const c of cs) if (!c.ghost && this.overlap(mn, mx, c)) return c; return null; },
  moveAxis(L, i, d, out) {
    if (d === 0) return;
    this.setComp(this.pos, i, this.comp(this.pos, i) + d);
    const H = this.height(); this.box(H, _mn, _mx);
    const cs = this.gather(L, _mn, _mx).slice();
    for (const c of cs) {
      if (c.ghost || !this.overlap(_mn, _mx, c)) continue;
      if (i === this.ax) {
        if (d * this.sg < 0) { this.setComp(this.pos, i, this.sg > 0 ? c.max[i] : c.min[i]); out.landed = c; }
        else { this.setComp(this.pos, i, this.sg > 0 ? c.min[i] - H : c.max[i] + H); out.head = true; }
      } else {
        const topU = this.sg > 0 ? c.max[this.ax] : -c.min[this.ax];
        const rise = topU - this.u();
        if (rise > 0 && rise <= this.stepH && out.canStep && !c.noStep) { // even a hair-thin seam is a step, not a wall
          const save = this.comp(this.pos, this.ax);
          this.setComp(this.pos, this.ax, (topU + 0.002) * this.sg);
          this.box(H, _mn2, _mx2);
          if (!this.anyOverlap(L, _mn2, _mx2)) { out.stepped = Math.max(out.stepped || 0, rise); this.box(H, _mn, _mx); continue; }
          this.setComp(this.pos, this.ax, save);
        }
        this.setComp(this.pos, i, d > 0 ? c.min[i] - this.R - 0.0005 : c.max[i] + this.R + 0.0005);
        out.hit = true; out.hitCol = c; out['h' + i] = true;
      }
      this.box(H, _mn, _mx);
    }
  },
  look(dt) {
    const s = 0.0022 * SET.sens;
    let dx = IN.mdx, dy = IN.mdy; IN.mdx = 0; IN.mdy = 0;
    const k = IN.keys; const kl = 2.2 * SET.sens * dt;
    if (k.ArrowLeft) this.yaw += kl; if (k.ArrowRight) this.yaw -= kl;
    if (k.ArrowUp) this.pitch += kl * 0.8 * (SET.invert ? -1 : 1); if (k.ArrowDown) this.pitch -= kl * 0.8 * (SET.invert ? -1 : 1);
    const gl = 2.6 * SET.sens * dt;
    this.yaw -= IN.gpLook.x * Math.abs(IN.gpLook.x) * gl * 1.3; this.pitch -= IN.gpLook.y * Math.abs(IN.gpLook.y) * gl * (SET.invert ? -1 : 1);
    this.yaw -= dx * s; this.pitch -= dy * s * (SET.invert ? -1 : 1);
    this.pitch = clamp(this.pitch, -1.5, 1.5);
  },
  basis() { // forward/right on the gravity plane (target frame)
    const q = this.qGto;
    _fwd.set(-Math.sin(this.yaw), 0, -Math.cos(this.yaw)).applyQuaternion(q);
    _rgt.set(Math.cos(this.yaw), 0, -Math.sin(this.yaw)).applyQuaternion(q);
  },
  physics(L, dt) {
    if (this.frozen) return;
    if (this.gravLock > 0) this.gravLock -= dt;
    // input
    let mx = 0, my = 0; const k = IN.keys;
    if (k.KeyW) my += 1; if (k.KeyS) my -= 1; if (k.KeyA) mx -= 1; if (k.KeyD) mx += 1;
    mx += IN.joy.x + IN.gpMove.x; my += IN.joy.y + IN.gpMove.y;
    const ml = Math.hypot(mx, my); if (ml > 1) { mx /= ml; my /= ml; }
    if (IN.take('crouch')) this.crouch = !this.crouch;
    if (this.crouch && IN.take('jump')) { this.crouch = false; }
    const wantSprint = (k.ShiftLeft || k.ShiftRight || IN.joy.sprint || IN.gpSprint) && my > 0.2 && !this.crouch;
    if (wantSprint && this.stamina > 0.02) { this.sprinting = true; this.stamina = Math.max(0, this.stamina - dt / 5.5); }
    else { this.sprinting = false; this.stamina = Math.min(1, this.stamina + dt / (wantSprint ? 9 : 3.2)); }
    // can we stand up?
    if (!this.crouch && this.ch > 0.01) { this.box(this.H, _mn2, _mx2); if (this.anyOverlap(L, _mn2, _mx2)) this.crouch = true; }
    this.ch = damp(this.ch, this.crouch ? 1 : 0, 10, dt);
    let speed = this.crouch ? 1.55 : this.sprinting ? 5.6 : 3.15;
    speed *= this.slow;
    this.basis();
    const wish = _w.set(0, 0, 0).addScaledVector(_fwd, my * speed).addScaledVector(_rgt, mx * speed);
    const up = this.up;
    let vUp = this.vel.dot(up);
    const vH = _vh.copy(this.vel).addScaledVector(up, -vUp);
    const accel = this.grounded ? 13 : 3.2;
    vH.lerp(wish, 1 - Math.exp(-accel * dt));
    vUp -= 15.5 * dt; if (vUp < -32) vUp = -32;
    if (IN.take('jump')) this.jumpBuf = 0.14;
    if (this.jumpBuf > 0) this.jumpBuf -= dt;
    let jumped = false;
    if (this.jumpBuf > 0 && (this.grounded || this.coyote > 0) && !this.crouch) { vUp = 5.0; this.jumpBuf = 0; this.coyote = 0; this.grounded = false; jumped = true; AU.noiseHit({ f: 1200, q: 1, dur: 0.06, gain: 0.05 }); }
    this.vel.copy(vH).addScaledVector(up, vUp);
    // carry on moving platform
    if (this.grounded && this.groundCol && this.groundCol.dv) this.pos.add(this.groundCol.dv);
    // integrate (sub-steps)
    const wasG = this.grounded; const preU = this.u();
    const steps = Math.ceil(this.vel.length() * dt / 0.25) || 1; const sd = dt / steps;
    const out = { canStep: wasG || this.coyote > 0, landed: null, head: false, hit: false, stepped: 0 };
    for (let s = 0; s < steps; s++) {
      for (const i of [0, 1, 2]) if (i !== this.ax) this.moveAxis(L, i, this.comp(this.vel, i) * sd, out);
      this.moveAxis(L, this.ax, this.comp(this.vel, this.ax) * sd, out);
    }
    let landed = out.landed;
    // snap down for stairs / slopes
    if (!landed && wasG && !jumped && this.vel.dot(up) <= 0.01) {
      const save = this.pos.clone(); const o2 = { canStep: false };
      this.moveAxis(L, this.ax, -this.sg * (this.stepH + 0.06), o2);
      if (o2.landed) landed = o2.landed; else this.pos.copy(save);
    }
    if (out.stepped) this.eyeOff.addScaledVector(up, -out.stepped);
    if (landed) {
      const fall = this.peakU - this.u();
      if (!this.grounded && fall > 0.6) { AU.land(fall); this.trauma = Math.min(1, this.trauma + Math.min(0.5, fall * 0.04)); if (fall > 7) GAME.shake(0.5); }
      this.grounded = true; this.coyote = 0.13; this.groundCol = landed; this.lastSurf = landed.surf || L.surf;
      const vu = this.vel.dot(up); if (vu < 0) this.vel.addScaledVector(up, -vu);
      this.peakU = this.u();
    } else {
      if (this.grounded) this.coyote = 0.13;
      this.grounded = false; this.groundCol = null; if (this.coyote > 0) this.coyote -= dt;
      this.peakU = Math.max(this.peakU, this.u());
    }
    if (out.head) { const vu = this.vel.dot(up); if (vu > 0) this.vel.addScaledVector(up, -vu); }
    // block velocity into walls
    for (const i of [0, 1, 2]) if (out['h' + i]) this.setComp(this.vel, i, 0);
    // footsteps & bob
    const hs = vH.length();
    if (this.grounded && hs > 0.4) {
      this.stepAcc += hs * dt; this.bob += hs * dt * 2.1; this.bobAmt = damp(this.bobAmt, Math.min(1, hs / 3), 8, dt);
      const stride = this.sprinting ? 0.95 : this.crouch ? 0.6 : 0.78;
      if (this.stepAcc > stride) { this.stepAcc = 0; AU.step(this.lastSurf, this.crouch ? 0.45 : this.sprinting ? 1.25 : 0.9); }
    } else this.bobAmt = damp(this.bobAmt, 0, 6, dt);
    // safe points
    this.safeT -= dt;
    if (this.grounded && this.safeT <= 0 && landed && !landed.dv && !landed.hazard && !landed.noSafe) {
      this.safeT = 0.35; this.safe.push({ p: this.pos.clone(), ax: this.ax, sg: this.sg, q: this.qGto.clone(), yaw: this.yaw }); if (this.safe.length > 24) this.safe.shift();
    }
    this.center.copy(this.pos).addScaledVector(up, this.height() * 0.5); // triggers and zones read this
    // fell into the void
    if (this.u() < L.killU || (L.killBox && !L.killBox.containsPoint(this.pos))) GAME.voidFall();
  },
  respawnSafe(back = 5) {
    const s = this.safe[Math.max(0, this.safe.length - 1 - back)];
    if (!s) return false;
    this.pos.copy(s.p); this.vel.set(0, 0, 0); this.qG.copy(s.q); this.qGto.copy(s.q); this.qGfrom.copy(s.q); this.gT = 1;
    this.ax = s.ax; this.sg = s.sg; this.up.copy(this.axisVec(s.ax, s.sg)); this.eyeOff.set(0, 0, 0); this.peakU = this.u();
    this.safe.length = Math.max(0, this.safe.length - back);
    return true;
  },
  camera(cam, dt) {
    if (this.gT < 1) this.gT = Math.min(1, this.gT + dt / 0.65);
    const q = this.curQG(); if (this.gT >= 1) this.qG.copy(this.qGto);
    this.eyeOff.multiplyScalar(Math.exp(-dt * 11));
    const eyeH = lerp(this.eye, this.eyeC, this.ch);
    const bobY = Math.sin(this.bob * 2) * 0.035 * this.bobAmt * (SET.calm ? 0.4 : 1), bobX = Math.cos(this.bob) * 0.025 * this.bobAmt * (SET.calm ? 0.4 : 1);
    this.basis();
    cam.position.copy(this.pos).addScaledVector(this.up, eyeH + bobY).addScaledVector(_rgt, bobX).add(this.eyeOff);
    // trauma shake
    this.trauma = Math.max(0, this.trauma - dt * 1.3);
    const sh = this.trauma * this.trauma * (SET.calm ? 0.35 : 1), tt = GAME.time * 31;
    const sy = noise1(tt * 0.37) * 0.035 * sh, sx = noise1(tt * 0.31 + 9) * 0.035 * sh;
    cam.quaternion.copy(q).multiply(_q4b.setFromAxisAngle(_Y, this.yaw + sx)).multiply(_q4c.setFromAxisAngle(_X, this.pitch + sy)).multiply(_q4d.setFromAxisAngle(_Z, this.roll + noise1(tt * 0.23 + 4) * 0.05 * sh));
    this.eyePos.copy(cam.position);
    this.center.copy(this.pos).addScaledVector(this.up, this.height() * 0.5);
    // lamp
    _v3a.set(0.22, -0.18, 0).applyQuaternion(cam.quaternion);
    this.lampPos.copy(cam.position).add(_v3a);
    this.lampDir.set(0, 0, -1).applyQuaternion(cam.quaternion);
  },
  forward(out) { return (out || new V3()).set(0, 0, -1).applyQuaternion(CAM.quaternion); }
};
const _cands = [], _qmn = [0, 0, 0], _qmx = [0, 0, 0], _mn = [0, 0, 0], _mx = [0, 0, 0], _mn2 = [0, 0, 0], _mx2 = [0, 0, 0];
const _fwd = new V3(), _rgt = new V3(), _w = new V3(), _vh = new V3(), _X = new V3(1, 0, 0), _Y = new V3(0, 1, 0), _Z = new V3(0, 0, 1);
const _q4a = new Q4(), _q4b = new Q4(), _q4c = new Q4(), _q4d = new Q4();
