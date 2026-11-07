/* ===================== world: geometry, colliders, levels, doors, pickups, build helpers =====================
   Levels are built from boxes. GeoAcc merges every box of a level into one mesh plus one set of boiling edge
   lines (two draw calls), and every solid box is also an axis-aligned collider in a spatial hash. */
let MAT = null;
function initMats() {
  MAT = {
    ink: makeInkMat(), inkDouble: makeInkMat({ side: THREE.DoubleSide }), line: makeLineMat(), lineW: makeLineMat({ tone: 1 }),
    glow: makeGlowMat(BLUE), glowWhite: makeGlowMat(new THREE.Color(1.0, 0.98, 0.9), { pulse: 0.3 }), glowWarm: makeGlowMat(new THREE.Color(1.0, 0.85, 0.55), { pulse: 0.5 }),
    portal: new THREE.ShaderMaterial({ uniforms: R.portalUniforms, vertexShader: PORTAL_VS, fragmentShader: PORTAL_FS, side: THREE.DoubleSide })
  };
}
const FACE_DEF = [ // n, u, v
  [[1, 0, 0], [0, 0, -1], [0, 1, 0]], [[-1, 0, 0], [0, 0, 1], [0, 1, 0]],
  [[0, 1, 0], [1, 0, 0], [0, 0, -1]], [[0, -1, 0], [1, 0, 0], [0, 0, 1]],
  [[0, 0, 1], [1, 0, 0], [0, 1, 0]], [[0, 0, -1], [-1, 0, 0], [0, 1, 0]]
];
const _bv = new V3(), _bn = new V3(), _nm3 = new THREE.Matrix3();
class GeoAcc {
  constructor() { this.P = []; this.N = []; this.T = []; this.A = []; this.I = []; this.L = []; this.S = []; this.vc = 0; }
  vert(x, y, z, nx, ny, nz, tone, pat) { this.P.push(x, y, z); this.N.push(nx, ny, nz); this.T.push(tone); this.A.push(pat); return this.vc++; }
  line(a, b, os = 0.04) {
    const dx = b.x - a.x, dy = b.y - a.y, dz = b.z - a.z, l = Math.sqrt(dx * dx + dy * dy + dz * dz) || 1;
    const e = Math.min(os, l * 0.08) / l;
    this.L.push(a.x - dx * e, a.y - dy * e, a.z - dz * e, b.x + dx * e, b.y + dy * e, b.z + dz * e);
    this.S.push(Math.random() * 100, Math.random() * 100);
  }
  // oriented box: m (Matrix4 or null), centre at local origin, half sizes hx,hy,hz
  boxM(m, hx, hy, hz, tone, pat, edges = true, faces = 63) {
    const hs = [hx, hy, hz];
    if (m) _nm3.getNormalMatrix(m);
    for (let f = 0; f < 6; f++) {
      if (!(faces & (1 << f))) continue;
      const [n, u, v] = FACE_DEF[f];
      const ax = n[0] ? 0 : n[1] ? 1 : 2, uax = u[0] ? 0 : u[1] ? 1 : 2, vax = v[0] ? 0 : v[1] ? 1 : 2;
      const cn = [n[0] * hs[ax], n[1] * hs[ax], n[2] * hs[ax]];
      const us = hs[uax], vs = hs[vax];
      _bn.set(n[0], n[1], n[2]); if (m) _bn.applyMatrix3(_nm3).normalize();
      const base = this.vc;
      for (const [su, sv] of [[-1, -1], [1, -1], [1, 1], [-1, 1]]) {
        _bv.set(cn[0] + u[0] * us * su + v[0] * vs * sv, cn[1] + u[1] * us * su + v[1] * vs * sv, cn[2] + u[2] * us * su + v[2] * vs * sv);
        if (m) _bv.applyMatrix4(m);
        this.vert(_bv.x, _bv.y, _bv.z, _bn.x, _bn.y, _bn.z, tone, pat);
      }
      this.I.push(base, base + 1, base + 2, base, base + 2, base + 3);
    }
    if (edges) {
      const c = []; for (let i = 0; i < 8; i++) { const p = new V3(i & 1 ? hx : -hx, i & 2 ? hy : -hy, i & 4 ? hz : -hz); if (m) p.applyMatrix4(m); c.push(p); }
      const E = [[0, 1], [2, 3], [4, 5], [6, 7], [0, 2], [1, 3], [4, 6], [5, 7], [0, 4], [1, 5], [2, 6], [3, 7]];
      for (const [a, b] of E) this.line(c[a], c[b]);
    }
  }
  box(x0, y0, z0, x1, y1, z1, tone, pat, edges = true, faces = 63) {
    _m4b.makeTranslation((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2);
    this.boxM(_m4b, Math.abs(x1 - x0) / 2, Math.abs(y1 - y0) / 2, Math.abs(z1 - z0) / 2, tone, pat, edges, faces);
  }
  geo(g, m, tone, pat, edgeAngle = 35) { // import a THREE geometry
    const gg = g.index ? g.toNonIndexed() : g;
    const p = gg.attributes.position, n = gg.attributes.normal; if (m) _nm3.getNormalMatrix(m);
    for (let i = 0; i < p.count; i++) {
      _bv.set(p.getX(i), p.getY(i), p.getZ(i)); if (m) _bv.applyMatrix4(m);
      _bn.set(n.getX(i), n.getY(i), n.getZ(i)); if (m) _bn.applyMatrix3(_nm3).normalize();
      const k = this.vert(_bv.x, _bv.y, _bv.z, _bn.x, _bn.y, _bn.z, tone, pat); this.I.push(k);
    }
    if (edgeAngle) {
      const eg = new THREE.EdgesGeometry(g, edgeAngle); const ep = eg.attributes.position;
      for (let i = 0; i < ep.count; i += 2) { const a = new V3(ep.getX(i), ep.getY(i), ep.getZ(i)), b = new V3(ep.getX(i + 1), ep.getY(i + 1), ep.getZ(i + 1)); if (m) { a.applyMatrix4(m); b.applyMatrix4(m); } this.line(a, b, 0.02); }
      eg.dispose();
    }
    if (gg !== g) gg.dispose();
  }
  cyl(x, y, z, r, h, seg, tone, pat, edges = true, m = null) {
    const g = new THREE.CylinderGeometry(r, r, h, seg, 1, false);
    const mm = new M4().makeTranslation(x, y + h / 2, z); if (m) mm.premultiply(m);
    this.geo(g, mm, tone, pat, edges ? 30 : 0); g.dispose();
  }
  empty() { return this.vc === 0 && this.L.length === 0; }
  build() {
    let mesh = null, lines = null;
    if (this.vc) {
      const g = new THREE.BufferGeometry();
      g.setAttribute('position', new THREE.Float32BufferAttribute(this.P, 3));
      g.setAttribute('normal', new THREE.Float32BufferAttribute(this.N, 3));
      g.setAttribute('aTone', new THREE.Float32BufferAttribute(this.T, 1));
      g.setAttribute('aPat', new THREE.Float32BufferAttribute(this.A, 1));
      g.setIndex(this.vc > 65535 ? new THREE.Uint32BufferAttribute(this.I, 1) : new THREE.Uint16BufferAttribute(this.I, 1));
      g.computeBoundingSphere(); g.computeBoundingBox(); mesh = g;
    }
    if (this.L.length) {
      const lg = new THREE.BufferGeometry();
      lg.setAttribute('position', new THREE.Float32BufferAttribute(this.L, 3));
      lg.setAttribute('aSeed', new THREE.Float32BufferAttribute(this.S, 1));
      lg.computeBoundingSphere(); lines = lg;
    }
    return { mesh, lines };
  }
}
// build a standalone object (dynamic) from an accumulator callback
function buildObj(fn, o = {}) {
  const a = new GeoAcc(); fn(a); const b = a.build(); const grp = new THREE.Group();
  if (b.mesh) { const m = new THREE.Mesh(b.mesh, o.mat || MAT.ink); m.renderOrder = 1; grp.add(m); grp.userData.mesh = m; }
  if (b.lines && !o.noLines) { const l = new THREE.LineSegments(b.lines, o.lineMat || MAT.line); l.renderOrder = 2; grp.add(l); grp.userData.lines = l; }
  return grp;
}

/* ---------- spatial hash of AABB colliders ---------- */
class SHash {
  constructor(c = 4) { this.c = c; this.m = new Map(); this.st = 1; }
  k(x, y, z) { return ((x + 600) * 1300 + (y + 600)) * 1300 + (z + 600); }
  insert(col) {
    const c = this.c;
    for (let x = Math.floor(col.min[0] / c); x <= Math.floor(col.max[0] / c); x++)
      for (let y = Math.floor(col.min[1] / c); y <= Math.floor(col.max[1] / c); y++)
        for (let z = Math.floor(col.min[2] / c); z <= Math.floor(col.max[2] / c); z++) {
          const k = this.k(x, y, z); let a = this.m.get(k); if (!a) { a = []; this.m.set(k, a); } a.push(col);
        }
  }
  query(mn, mx, out) {
    const c = this.c; this.st++;
    for (let x = Math.floor(mn[0] / c); x <= Math.floor(mx[0] / c); x++)
      for (let y = Math.floor(mn[1] / c); y <= Math.floor(mx[1] / c); y++)
        for (let z = Math.floor(mn[2] / c); z <= Math.floor(mx[2] / c); z++) {
          const a = this.m.get(this.k(x, y, z)); if (!a) continue;
          for (const col of a) if (col._s !== this.st) { col._s = this.st; if (col.on) out.push(col); }
        }
    return out;
  }
  ray(o, d, maxT) { // returns nearest t or Infinity
    const c = this.c; let x = Math.floor(o.x / c), y = Math.floor(o.y / c), z = Math.floor(o.z / c);
    const sx = d.x > 0 ? 1 : -1, sy = d.y > 0 ? 1 : -1, sz = d.z > 0 ? 1 : -1;
    const tdx = d.x !== 0 ? Math.abs(c / d.x) : Infinity, tdy = d.y !== 0 ? Math.abs(c / d.y) : Infinity, tdz = d.z !== 0 ? Math.abs(c / d.z) : Infinity;
    let tmx = d.x !== 0 ? ((x + (sx > 0 ? 1 : 0)) * c - o.x) / d.x : Infinity;
    let tmy = d.y !== 0 ? ((y + (sy > 0 ? 1 : 0)) * c - o.y) / d.y : Infinity;
    let tmz = d.z !== 0 ? ((z + (sz > 0 ? 1 : 0)) * c - o.z) / d.z : Infinity;
    this.st++; let best = Infinity, t = 0, guard = 0;
    while (t <= maxT && guard++ < 400) {
      const a = this.m.get(this.k(x, y, z));
      if (a) for (const col of a) {
        if (col._s === this.st || !col.on || col.noRay) continue; col._s = this.st;
        const h = rayBox(o, d, col.min, col.max); if (h < best) best = h;
      }
      const tn = Math.min(tmx, tmy, tmz);
      if (best <= tn) break;
      t = tn;
      if (tmx <= tmy && tmx <= tmz) { x += sx; tmx += tdx; } else if (tmy <= tmz) { y += sy; tmy += tdy; } else { z += sz; tmz += tdz; }
    }
    return best <= maxT ? best : Infinity;
  }
}
function rayBox(o, d, mn, mx) {
  let t0 = -Infinity, t1 = Infinity;
  for (let i = 0; i < 3; i++) {
    const oi = i === 0 ? o.x : i === 1 ? o.y : o.z, di = i === 0 ? d.x : i === 1 ? d.y : d.z;
    if (Math.abs(di) < 1e-9) { if (oi < mn[i] || oi > mx[i]) return Infinity; continue; }
    let a = (mn[i] - oi) / di, b = (mx[i] - oi) / di; if (a > b) { const t = a; a = b; b = t; }
    if (a > t0) t0 = a; if (b < t1) t1 = b; if (t0 > t1) return Infinity;
  }
  if (t1 < 0) return Infinity;
  return t0 >= 0 ? t0 : 0;
}

/* ---------- Level ---------- */
// env: sun direction and strength, ambient, fog (tone 1 = paper, 0 = ink), hatch density, ambient sound bed, mood (post effects)
const ENV_DEF = () => ({ sunDir: new V3(-0.45, 0.8, 0.35), sun: 0.75, amb: 0.48, fogTone: 1, fogDen: 0.012, hatch: 9, bgTone: null, lampMul: 1, upW: new V3(0, 1, 0),
  bed: { root: 55, fifth: 1.5, cut: 240, noise: 0.04, gain: 0.4 }, mood: { boil: 0.08, warp: 0, double: 0, wave: 0, swirl: 0, tendril: 0.15, chrom: 0 } });
class Level {
  constructor(idx, name) {
    this.idx = idx; this.name = name; this.scene = new THREE.Scene(); this.scene.matrixAutoUpdate = false;
    this.acc = { main: new GeoAcc() }; this.cur = 'main'; this.chunkObjs = {};
    this.cols = []; this.hash = new SHash(4); this.ents = []; this.doors = []; this.plights = []; this.dyn = [];
    this.triggers = []; this.pickups = []; this.inter = []; this.gravZones = [];
    this.bounds = new THREE.Box3(); this.env = ENV_DEF(); this.killU = -30; this.t = 0;
    this.portalHide = []; this.surf = 'stone';
    this.data = {};
  }
  get a() { return this.acc[this.cur]; }
  chunk(n) { if (!this.acc[n]) this.acc[n] = new GeoAcc(); this.cur = n; return this; }
  addCol(x0, y0, z0, x1, y1, z1, o = {}) {
    const c = { min: [Math.min(x0, x1), Math.min(y0, y1), Math.min(z0, z1)], max: [Math.max(x0, x1), Math.max(y0, y1), Math.max(z0, z1)], on: true, surf: o.surf || this.surf, chunk: this.cur, hazard: o.hazard || 0, noRay: !!o.noRay, tag: o.tag, _s: 0 };
    this.cols.push(c); return c;
  }
  // box by corners. o: tone, pat, solid(true), surf, edges, faces
  B(x0, y0, z0, x1, y1, z1, o = {}) {
    if (o.vis !== false) this.a.box(x0, y0, z0, x1, y1, z1, o.tone == null ? 0.85 : o.tone, o.pat || 0, o.edges !== false, o.faces == null ? 63 : o.faces);
    if (o.solid !== false) return this.addCol(x0, y0, z0, x1, y1, z1, o);
    return null;
  }
  // oriented decor box (non-colliding unless o.solid and axis-aligned)
  BM(m, hx, hy, hz, o = {}) { this.a.boxM(m, hx, hy, hz, o.tone == null ? 0.85 : o.tone, o.pat || 0, o.edges !== false); }
  cyl(x, y, z, r, h, o = {}) {
    this.a.cyl(x, y, z, r, h, o.seg || 10, o.tone == null ? 0.85 : o.tone, o.pat || 0, o.edges !== false, o.m || null);
    if (o.solid !== false && !o.m) this.addCol(x - r * 0.85, y, z - r * 0.85, x + r * 0.85, y + h, z + r * 0.85, o);
  }
  light(x, y, z, r, i, o = {}) { const pl = { pos: new V3(x, y, z), r, i, base: i, flick: 1, flicker: o.flicker || 0, phase: Math.random() * 10, on: true, kind: o.kind }; this.plights.push(pl); return pl; }
  add(obj) { this.scene.add(obj); return obj; }
  ent(e) { this.ents.push(e); return e; }
  trigger(x0, y0, z0, x1, y1, z1, fn, o = {}) { const t = { min: [Math.min(x0, x1), Math.min(y0, y1), Math.min(z0, z1)], max: [Math.max(x0, x1), Math.max(y0, y1), Math.max(z0, z1)], fn, once: o.once !== false, done: false, inside: false, exit: o.exit }; this.triggers.push(t); return t; }
  finalize() {
    for (const n in this.acc) {
      const b = this.acc[n].build(); const grp = new THREE.Group(); grp.name = 'chunk_' + n;
      if (b.mesh) { const m = new THREE.Mesh(b.mesh, MAT.ink); m.layers.enable(1); m.renderOrder = 1; grp.add(m); this.bounds.union(b.mesh.boundingBox); }
      if (b.lines) { const l = new THREE.LineSegments(b.lines, MAT.line); l.renderOrder = 2; grp.add(l); }
      this.scene.add(grp); this.chunkObjs[n] = grp;
    }
    for (const c of this.cols) this.hash.insert(c);
    if (this.bounds.isEmpty()) this.bounds.set(new V3(-10, -10, -10), new V3(10, 10, 10));
    this.acc = null;
  }
  ray(o, d, maxT) { return this.hash.ray(o, d, maxT); }
  dispose() {
    this.scene.traverse(o => {
      if (o.geometry) o.geometry.dispose();
      if (o.material && o.material.userData && o.material.userData.own) o.material.dispose();
    });
    if (this.shadowRT) this.shadowRT.dispose();
    for (const e of this.ents) if (e.dispose) e.dispose();
    this.disposed = true;
  }
}

/* ---------- frame helper: matrix from position/yaw/up ---------- */
function frameMatrix(x, y, z, yaw, upQ) {
  const m = new M4().makeRotationY(yaw);
  if (upQ) m.premultiply(new M4().makeRotationFromQuaternion(upQ));
  m.setPosition(x, y, z); return m;
}
function aabbOfBoxM(m, hx, hy, hz) {
  const mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9];
  for (let i = 0; i < 8; i++) { const p = new V3(i & 1 ? hx : -hx, i & 2 ? hy : -hy, i & 4 ? hz : -hz).applyMatrix4(m); const a = [p.x, p.y, p.z]; for (let k = 0; k < 3; k++) { if (a[k] < mn[k]) mn[k] = a[k]; if (a[k] > mx[k]) mx[k] = a[k]; } }
  return [mn, mx];
}

/* ---------- Door ---------- */
let DOOR_ID = 0;
class Door {
  constructor(L, o) {
    this.L = L; this.id = DOOR_ID++; this.kind = o.kind || 'plain'; this.w = o.w || 1.1; this.h = o.h || 2.25;
    this.locked = !!o.locked; this.real = !!o.real; this.onOpen = o.onOpen; this.onTry = o.onTry; this.lockMsg = o.lockMsg;
    this.F = frameMatrix(o.x, o.y, o.z, o.yaw || 0, o.upQ || null); this.Finv = this.F.clone().invert();
    this.pos = new V3().setFromMatrixPosition(this.F);
    this.upQ = o.upQ || null; this.fwd = new V3(0, 0, 1).transformDirection(this.F); this.upV = new V3(0, 1, 0).transformDirection(this.F);
    this.angle = o.startOpen ? (o.swingIn ? -1.6 : 1.6) : 0; this.target = this.angle; this.swingIn = !!o.swingIn; this.speed = 2.2;
    this.portal = null; this.auto = o.autoClose || 0; this.openT = 0; this.hidden = false;
    this.interactive = o.interactive !== false; this.prompt = o.prompt || 'Open';
    const w = this.w, h = this.h, ft = 0.13, fd = o.frameDepth || 0.34;
    // ---- frame (merged into the level mesh) ----
    const frameFn = a => {
      const t = o.frameTone == null ? 0.62 : o.frameTone;
      const mk = (cx, cy, cz, hx, hy, hz) => { const m = this.F.clone().multiply(new M4().makeTranslation(cx, cy, cz)); a.boxM(m, hx, hy, hz, t, 4, true); return m; };
      this._jambs = [mk(-w / 2 - ft / 2, h / 2 + 0.06, 0, ft / 2, h / 2 + 0.06, fd / 2), mk(w / 2 + ft / 2, h / 2 + 0.06, 0, ft / 2, h / 2 + 0.06, fd / 2), mk(0, h + ft / 2 + 0.06, 0, w / 2 + ft, ft / 2, fd / 2)];
      if (o.ornate) { mk(0, h + ft + 0.2, 0, w / 2 + ft + 0.08, 0.06, fd / 2 + 0.04); mk(0, h + ft + 0.36, 0, w / 2 + ft - 0.05, 0.1, fd / 2 - 0.02); }
    };
    frameFn(L.a);
    if (o.frameSolid !== false) for (const jm of this._jambs.slice(0, 2)) { const [mn, mx] = aabbOfBoxM(jm, ft / 2, h / 2 + 0.06, fd / 2); L.addCol(mn[0], mn[1], mn[2], mx[0], mx[1], mx[2]); }
    // ---- leaf ----
    this.pivot = new THREE.Group(); this.pivot.matrixAutoUpdate = false;
    this.base = new M4().copy(this.F).multiply(new M4().makeTranslation(-w / 2, 0, 0));
    const lt = o.leafTone == null ? 0.72 : o.leafTone;
    this.leaf = buildObj(a => {
      const lw = w - 0.03, lh = h - 0.02;
      a.box(0.01, 0.01, -0.035, lw, lh, 0.035, lt, 4, true);
      for (const s of [-1, 1]) {
        a.box(0.14, lh * 0.55, s * 0.035, lw - 0.14, lh - 0.16, s * 0.05, lt * 0.92, 0, true);
        a.box(0.14, 0.18, s * 0.035, lw - 0.14, lh * 0.5, s * 0.05, lt * 0.92, 0, true);
        a.box(lw - 0.16, h * 0.46, s * 0.05, lw - 0.08, h * 0.46 + 0.05, s * 0.11, 0.3, 0, true);
        if (o.window) a.box(lw * 0.3, lh * 0.66, s * 0.036, lw * 0.7, lh * 0.86, s * 0.052, 0.08, 0, true);
      }
    }, { mat: this.ownMat() });
    if (this.real) {
      const kh = new THREE.Mesh(new THREE.BoxGeometry(0.05, 0.1, 0.14), MAT.glow); kh.position.set(w - 0.15, h * 0.46 - 0.1, 0); this.leaf.add(kh);
      this.keyGlow = kh; this.markReal();
    }
    if (o.knocker) { this.leaf.add(buildObj(a => a.box(w * 0.42, h * 0.62, -0.09, w * 0.58, h * 0.66, 0.09, 0.2, 0, true))); }
    this.pivot.add(this.leaf); L.add(this.pivot);
    // ---- leaf collider (dynamic) ----
    const [lmn, lmx] = aabbOfBoxM(new M4().copy(this.F).multiply(new M4().makeTranslation(0, h / 2, 0)), w / 2, h / 2, 0.06);
    this.col = { min: lmn, max: lmx, on: true, surf: 'wood', _s: 0, door: this }; L.dyn.push(this.col);
    // ---- portal aperture (box beyond the plane) ----
    this.aperture = new THREE.Mesh(new THREE.BoxGeometry(w + 0.02, h + 0.02, 0.6), MAT.portal);
    // the portal box sits beyond the doorway as seen by the viewer: +z for exits, -z for entrances (seen from inside the room)
    this.aperture.matrixAutoUpdate = false; this.aperture.matrix.copy(this.F).multiply(new M4().makeTranslation(0, h / 2, this.kind === 'entrance' ? -0.31 : 0.31));
    this.aperture.matrixWorld.copy(this.aperture.matrix); // valid before the first render (frustum tests use it)
    this.aperture.matrixWorldNeedsUpdate = true; this.aperture.visible = false; this.aperture.renderOrder = 0; L.add(this.aperture);
    // local plane (for portal clipping when this door is a destination)
    this.plane = new THREE.Plane().setFromNormalAndCoplanarPoint(this.fwd.clone(), this.pos.clone());
    this.prevLocal = null;
    { const [bmn, bmx] = aabbOfBoxM(new M4().copy(this.F).multiply(new M4().makeTranslation(0, h / 2, -0.45)), w / 2 + 0.1, h / 2, 0.12); this.block = { min: bmn, max: bmx, on: false, _s: 0 }; L.dyn.push(this.block); }
    this.update(0);
    L.doors.push(this);
  }
  markReal() {
    if (this.leak) return;
    // a thin line of light in the gap under the leaf, and a soft blue pool on the floor in front of it
    const lk = new THREE.Mesh(new THREE.BoxGeometry(this.w - 0.12, 0.014, 0.035), MAT.glow); lk.matrixAutoUpdate = false;
    lk.matrix.copy(this.F).multiply(new M4().makeTranslation(0, 0.007, -0.055)); lk.matrixWorldNeedsUpdate = true; this.L.add(lk); this.leak = lk;
    this.spillMat = makeSpillMat(BLUE, 0.75);
    const pool = new THREE.Mesh(new THREE.PlaneGeometry(this.w + 1.3, 2.3), this.spillMat); pool.matrixAutoUpdate = false; pool.renderOrder = 2;
    pool.matrix.copy(this.F).multiply(new M4().makeTranslation(0, 0.014, -1.2)).multiply(new M4().makeRotationX(-Math.PI / 2)); pool.matrixWorldNeedsUpdate = true; this.L.add(pool); this.pool = pool;
    // a soft halo around the keyhole on both faces of the leaf, so the real door reads from across a room
    if (this.keyGlow) {
      const hm = makeSpillMat(BLUE, 0.6, 1), kp = this.keyGlow.position;
      for (const sd of [1, -1]) { const h = new THREE.Mesh(new THREE.PlaneGeometry(0.62, 0.62), hm); h.position.set(kp.x, kp.y, sd * 0.085); if (sd < 0) h.rotation.y = Math.PI; h.renderOrder = 2; this.leaf.add(h); }
    }
    const sp = new V3(0, 0.6, -1.3).applyMatrix4(this.F); this.spill = this.L.light(sp.x, sp.y, sp.z, 3.6, 0.32, { flicker: 0.04 });
  }
  ownMat() { if (!this._mat) { this._mat = makeInkMat(); this._mat.userData.own = true; } return this._mat; }
  local(p, out) { return (out || new V3()).copy(p).applyMatrix4(this.Finv); }
  get isOpen() { return Math.abs(this.angle) > 0.12; }
  interactPoint() { return _v3a.set(0, this.h * 0.46, 0).applyMatrix4(this.F); }
  canInteract() { return this.interactive && !this.hidden && Math.abs(this.target) < 0.01; }
  tryOpen() {
    if (this.locked) {
      AU.rattle(this.pos); if (this.onTry) this.onTry(this); else if (this.lockMsg) GAME.toast(this.lockMsg);
      this.shake = 0.35; return false;
    }
    this.open(); return true;
  }
  open(fast) {
    this.target = this.swingIn ? -1.62 : 1.62; this.speed = fast ? 6 : 1.9; AU.creak(this.pos, 1.1);
    this.openT = 0; if (this.onOpen) this.onOpen(this);
  }
  slamWhenClear() { this.slamPending = true; }
  close(slam) { this.slamPending = false; this.target = 0; this.speed = slam ? 9 : 2.2; this._slam = slam; if (!slam) AU.creak(this.pos, 0.9, 0.15); }
  update(dt) {
    const prev = this.angle;
    if (this.angle !== this.target) {
      const d = this.target - this.angle, s = this.speed * dt;
      this.angle = Math.abs(d) < s ? this.target : this.angle + Math.sign(d) * s;
      if (this.target === 0 && this.angle === 0 && prev !== 0 && this._slam) { AU.slam(this.pos, 0.55); GAME.shake(0.25); this._slam = false; if (this.onSlam) this.onSlam(this); }
    }
    let sh = 0; if (this.shake > 0) { this.shake -= dt; sh = Math.sin(this.shake * 90) * 0.02 * this.shake; }
    this.pivot.matrix.copy(this.base).multiply(_m4b.makeRotationY(this.angle + sh)); this.pivot.matrixWorldNeedsUpdate = true;
    this.col.on = Math.abs(this.angle) < 0.25 && !this.hidden;
    if (this.spillMat) { const o = 1 - Math.min(1, Math.abs(this.angle) / 0.9); this.spillMat.uniforms.uA.value = 0.5 * o; this.pool.visible = o > 0.01; this.leak.visible = o > 0.6; }
    if (this.slamPending) { this.slamT = (this.slamT || 0) + dt; const lz = this.local(PL.pos, _v3c).z; if (Math.abs(lz) > 0.95 || PL.pos.distanceTo(this.pos) > 2.6 || (this.slamT > 3 && Math.abs(lz) > 0.4)) { this.slamT = 0; this.close(true); } }
    if (this.auto && this.isOpen && this.target !== 0) { this.openT += dt; if (this.openT > this.auto) this.close(true); }
  }
}

/* ---------- pickups: 'key' (a blue octahedron, lit) or 'note' (a sheet of paper). o.onGet(p) runs on collect ---------- */
class Pickup {
  constructor(L, kind, x, y, z, o = {}) {
    this.L = L; this.kind = kind; this.pos = new V3(x, y, z); this.o = o; this.alive = true; this.t = Math.random() * 6;
    this.obj = new THREE.Group(); this.obj.position.copy(this.pos);
    if (kind === 'key') this.obj.add(new THREE.Mesh(new THREE.OctahedronGeometry(0.14, 0), MAT.glow));
    else this.obj.add(buildObj(a => { a.box(-0.15, -0.2, -0.004, 0.15, 0.2, 0.004, 1.2, PAT.PAPER, true); for (let i = 0; i < 6; i++) a.line(new V3(-0.11, 0.13 - i * 0.05, 0.006), new V3(0.1 - (i === 5 ? 0.08 : 0), 0.13 - i * 0.05, 0.006), 0); }));
    if (kind === 'key' && o.light !== false) this.pl = L.light(x, y + 0.1, z, 4.5, 0.55);
    L.add(this.obj); L.pickups.push(this);
  }
  update(dt) {
    if (!this.alive) return;
    this.t += dt; this.obj.position.copy(this.pos).addScaledVector(PL.up, Math.sin(this.t * 2) * 0.05);
    this.obj.rotation.y += dt * (this.kind === 'note' ? 0.6 : 1.2);
    if (PL.center.distanceTo(this.obj.position) < (this.o.r || 1.25)) this.collect();
  }
  collect() { this.alive = false; this.obj.visible = false; if (this.pl) this.pl.i = 0; AU.chime(0.14); if (this.o.onGet) this.o.onGet(this); GAME.onPickup(this); }
}

/* ---------- build helpers ---------- */
const DIRS = { '+x': [1, 0], '-x': [-1, 0], '+z': [0, 1], '-z': [0, -1] };
const yawOf = d => ({ '+z': 0, '+x': Math.PI / 2, '-z': Math.PI, '-x': -Math.PI / 2 })[d];
const faceYaw = doorYaw => doorYaw + Math.PI; // player yaw that looks along a door's walking direction
// wall spanning x0..x1 (thickness z0..z1) with rectangular holes [{a0,a1,b0,b1}] (x and y)
function wallX(L, x0, x1, z0, z1, y0, y1, holes = [], o = {}) {
  holes = holes.slice().sort((a, b) => a.a0 - b.a0); let cur = x0;
  for (const h of holes) {
    if (h.a0 > cur + 0.001) L.B(cur, y0, z0, h.a0, y1, z1, o);
    if (h.b1 < y1 - 0.001) L.B(h.a0, h.b1, z0, h.a1, y1, z1, o);
    if (h.b0 > y0 + 0.001) L.B(h.a0, y0, z0, h.a1, h.b0, z1, o);
    cur = h.a1;
  }
  if (cur < x1 - 0.001) L.B(cur, y0, z0, x1, y1, z1, o);
}
function wallZ(L, z0, z1, x0, x1, y0, y1, holes = [], o = {}) {
  holes = holes.slice().sort((a, b) => a.a0 - b.a0); let cur = z0;
  for (const h of holes) {
    if (h.a0 > cur + 0.001) L.B(x0, y0, cur, x1, y1, h.a0, o);
    if (h.b1 < y1 - 0.001) L.B(x0, h.b1, h.a0, x1, y1, h.a1, o);
    if (h.b0 > y0 + 0.001) L.B(x0, y0, h.a0, x1, h.b0, h.a1, o);
    cur = h.a1;
  }
  if (cur < z1 - 0.001) L.B(x0, y0, cur, x1, y1, z1, o);
}
const doorHole = (c, y0, w = 1.1, h = 2.25) => ({ a0: c - w / 2 - 0.13, a1: c + w / 2 + 0.13, b0: y0, b1: y0 + h + 0.19 });
// straight flight of stairs. Starts at (x,y,z): bottom of first step, centre of width. Returns end point.
function stairs(L, x, y, z, dir, n, o = {}) {
  const w = o.w || 1.8, rise = o.rise || 0.22, run = o.run || 0.34, tone = o.tone == null ? 0.88 : o.tone, pat = o.pat || 0;
  const [dx, dz] = DIRS[dir], skip = o.skip || [];
  const steps = [];
  for (let i = 0; i < n; i++) {
    if (skip.includes(i)) continue;
    const top = y + rise * (i + 1), bot = o.solid ? y : top - Math.max(o.thick || 0.24, rise + 0.03);
    const a0 = i * run, a1 = (i + 1) * run;
    let c;
    if (dx) c = [x + dx * a0, bot, z - w / 2, x + dx * a1, top, z + w / 2]; else c = [x - w / 2, bot, z + dz * a0, x + w / 2, top, z + dz * a1];
    if (o.collapse) steps.push(c); else L.B(Math.min(c[0], c[3]), c[1], Math.min(c[2], c[5]), Math.max(c[0], c[3]), c[4], Math.max(c[2], c[5]), { tone, pat, surf: o.surf });
  }
  const len = n * run, H = n * rise;
  // stringers (sloped side beams)
  if (o.stringers !== false && !o.solid) {
    const ang = Math.atan2(H, len), sl = Math.hypot(H, len);
    for (const s of [-1, 1]) {
      const cx = x + dx * len / 2 + (dz ? s * (w / 2 + 0.06) : 0), cz = z + dz * len / 2 + (dx ? s * (w / 2 + 0.06) : 0), cy = y + H / 2 - 0.12;
      const m = new M4().makeTranslation(cx, cy, cz);
      if (dx) m.multiply(new M4().makeRotationZ(dx * ang)); else m.multiply(new M4().makeRotationX(-dz * ang));
      L.BM(m, dx ? sl / 2 : 0.06, 0.2, dx ? 0.06 : sl / 2, { tone: o.stringerTone == null ? 0.62 : o.stringerTone });
    }
  }
  if (o.rails) for (const s of (o.railSides || [-1, 1])) stairRail(L, x, y, z, dir, n, rise, run, w, s, o);
  return { x: x + dx * len, y: y + H, z: z + dz * len, steps };
}
function stairRail(L, x, y, z, dir, n, rise, run, w, side, o = {}) {
  const [dx, dz] = DIRS[dir]; const off = w / 2 - 0.05;
  for (let i = 0; i < n; i += 2) {
    const a = (i + 0.5) * run, top = y + rise * (i + 1);
    const px = x + dx * a + (dz ? side * off : 0), pz = z + dz * a + (dx ? side * off : 0);
    L.B(px - 0.03, top, pz - 0.03, px + 0.03, top + 0.92, pz + 0.03, { tone: 1, pat: 13, solid: false });
  }
  const len = n * run, H = n * rise, ang = Math.atan2(H, len), sl = Math.hypot(H, len);
  const cx = x + dx * len / 2 + (dz ? side * off : 0), cz = z + dz * len / 2 + (dx ? side * off : 0);
  const m = new M4().makeTranslation(cx, y + H / 2 + 0.95, cz);
  if (dx) m.multiply(new M4().makeRotationZ(dx * ang)); else m.multiply(new M4().makeRotationX(-dz * ang));
  L.BM(m, dx ? sl / 2 : 0.05, 0.04, dx ? 0.05 : sl / 2, { tone: 0.55 });
  // invisible colliders per step to stop falls
  for (let i = 0; i < n; i++) {
    const a0 = i * run, a1 = (i + 1) * run, top = y + rise * (i + 1);
    const px = x + (dz ? side * off : 0), pz = z + (dx ? side * off : 0);
    if (dx) L.addCol(px + dx * a0, top, pz - 0.05, px + dx * a1, top + 1.0, pz + 0.05, { noRay: true });
    else L.addCol(px - 0.05, top, pz + dz * a0, px + 0.05, top + 1.0, pz + dz * a1, { noRay: true });
  }
}
// straight balustrade along a horizontal segment at height y
function rail(L, x0, z0, x1, z1, y, o = {}) {
  const len = Math.hypot(x1 - x0, z1 - z0), n = Math.max(1, Math.round(len / 0.42));
  for (let i = 0; i <= n; i++) { const t = i / n, px = lerp(x0, x1, t), pz = lerp(z0, z1, t); L.B(px - 0.035, y, pz - 0.035, px + 0.035, y + 0.92, pz + 0.035, { tone: 1, pat: 13, solid: false, edges: true }); }
  const t = 0.05;
  L.B(Math.min(x0, x1) - t, y + 0.9, Math.min(z0, z1) - t, Math.max(x0, x1) + t, y + 0.98, Math.max(z0, z1) + t, { tone: 0.6, solid: false });
  L.addCol(Math.min(x0, x1) - t, y, Math.min(z0, z1) - t, Math.max(x0, x1) + t, y + 1.0, Math.max(z0, z1) + t, { noRay: true });
}
function column(L, x, y, z, r, h, o = {}) {
  L.B(x - r * 1.35, y, z - r * 1.35, x + r * 1.35, y + 0.3, z + r * 1.35, { tone: o.tone || 0.8, solid: o.solid !== false });
  L.cyl(x, y + 0.3, z, r, h - 0.6, { seg: o.seg || 10, tone: o.tone || 0.85, solid: o.solid !== false });
  L.B(x - r * 1.35, y + h - 0.3, z - r * 1.35, x + r * 1.35, y + h, z + r * 1.35, { tone: o.tone || 0.8, solid: o.solid !== false });
}
// arch: axis 'x' spans along x (opening faces z). centre at (cx, y, cz)
function arch(L, cx, y, cz, axis, span, h, depth, o = {}) {
  const pw = o.pw || 0.5, tone = o.tone == null ? 0.82 : o.tone, pat = o.pat || 9, r = span / 2;
  const sx = axis === 'x';
  for (const s of [-1, 1]) {
    const px = sx ? cx + s * (r + pw / 2) : cx, pz = sx ? cz : cz + s * (r + pw / 2);
    L.B(px - (sx ? pw / 2 : depth / 2), y, pz - (sx ? depth / 2 : pw / 2), px + (sx ? pw / 2 : depth / 2), y + h, pz + (sx ? depth / 2 : pw / 2), { tone, pat, solid: o.solid !== false });
  }
  const N = o.n || 9;
  for (let i = 0; i < N; i++) {
    const a = Math.PI * (i + 0.5) / N; const rr = r + pw / 2;
    const ox = Math.cos(a) * rr, oy = Math.sin(a) * rr;
    const m = new M4().makeTranslation(sx ? cx + ox : cx, y + h + oy, sx ? cz : cz + ox);
    if (sx) m.multiply(new M4().makeRotationZ(a - Math.PI / 2)); else m.multiply(new M4().makeRotationX(-(a - Math.PI / 2)));
    const seg = Math.PI * rr / N * 0.52;
    L.BM(m, sx ? seg : depth / 2, pw / 2, sx ? depth / 2 : seg, { tone: tone * (i % 2 ? 0.95 : 1), pat: 0 });
  }
}
// local-frame builder for oriented decor (non-colliding)
function frameB(L, m) {
  return {
    box(x0, y0, z0, x1, y1, z1, o = {}) {
      const mm = m.clone().multiply(new M4().makeTranslation((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2));
      L.BM(mm, Math.abs(x1 - x0) / 2, Math.abs(y1 - y0) / 2, Math.abs(z1 - z0) / 2, o);
    }
  };
}
// a decorative Escher fragment in an arbitrary orientation
function decoChunk(L, m, kind, s = 1) {
  const f = frameB(L, m);
  if (kind === 'stairs' || kind === 'flight') {
    const n = 9; for (let i = 0; i < n; i++) f.box(-0.9 * s, i * 0.24 * s, i * 0.34 * s, 0.9 * s, (i + 1) * 0.24 * s, (i + 1) * 0.34 * s, { tone: 0.88 });
    f.box(-1.0 * s, 0, -1.6 * s, 1.0 * s, 0.24 * s, 0, { tone: 0.85, pat: 9 });
    f.box(-1.0 * s, n * 0.24 * s - 0.24 * s, n * 0.34 * s, 1.0 * s, n * 0.24 * s, n * 0.34 * s + 1.6 * s, { tone: 0.85, pat: 9 });
    for (let i = 0; i < n; i += 2) f.box(-0.95 * s, (i + 1) * 0.24 * s, (i + 0.4) * 0.34 * s, -0.9 * s, (i + 1) * 0.24 * s + 0.9 * s, (i + 0.6) * 0.34 * s, { tone: 0.7 });
  } else if (kind === 'arch') {
    f.box(-2.2 * s, 0, -0.4 * s, -1.6 * s, 3.4 * s, 0.4 * s, { pat: 9, tone: 0.82 }); f.box(1.6 * s, 0, -0.4 * s, 2.2 * s, 3.4 * s, 0.4 * s, { pat: 9, tone: 0.82 });
    for (let i = 0; i < 7; i++) { const a = Math.PI * (i + 0.5) / 7, rr = 1.9 * s; const mm = m.clone().multiply(new M4().makeTranslation(Math.cos(a) * rr, 3.4 * s + Math.sin(a) * rr, 0)).multiply(new M4().makeRotationZ(a - Math.PI / 2)); L.BM(mm, 0.45 * s, 0.3 * s, 0.4 * s, { tone: 0.8 }); }
    f.box(-2.4 * s, -0.4 * s, -0.6 * s, 2.4 * s, 0, 0.6 * s, { tone: 0.75, pat: 9 });
  } else if (kind === 'block') {
    f.box(-2 * s, -2 * s, -2 * s, 2 * s, 2 * s, 2 * s, { pat: 1, tone: 0.86 });
    f.box(-0.6 * s, -0.9 * s, 2 * s, 0.6 * s, 0.9 * s, 2.06 * s, { tone: 0.1 });
    f.box(-2.3 * s, 2 * s, -2.3 * s, 2.3 * s, 2.3 * s, 2.3 * s, { tone: 0.75 });
  } else if (kind === 'column') {
    f.box(-0.5 * s, 0, -0.5 * s, 0.5 * s, 0.3 * s, 0.5 * s, { tone: 0.8 });
    f.box(-0.32 * s, 0.3 * s, -0.32 * s, 0.32 * s, 7.4 * s, 0.32 * s, { tone: 0.88 });
    f.box(-0.5 * s, 7.4 * s, -0.5 * s, 0.5 * s, 7.7 * s, 0.5 * s, { tone: 0.8 });
  } else if (kind === 'room') {
    f.box(-3 * s, 0, -3 * s, 3 * s, 0.3 * s, 3 * s, { pat: 3, tone: 0.9 });
    f.box(-3 * s, 0.3 * s, 2.7 * s, 3 * s, 3.5 * s, 3 * s, { pat: 6, tone: 0.85 });
    f.box(-3 * s, 0.3 * s, -3 * s, -2.7 * s, 3.5 * s, 2.7 * s, { pat: 6, tone: 0.85 });
    f.box(-0.5 * s, 0.3 * s, 2.6 * s, 0.5 * s, 2.4 * s, 2.7 * s, { tone: 0.6, pat: 4 });
  }
}
function scatterDeco(L, n, rmin, rmax, ymin, ymax, kinds, seed, center = new V3()) {
  const r = mulberry32(seed);
  for (let i = 0; i < n; i++) {
    const a = r() * TAU, d = rmin + r() * (rmax - rmin), y = ymin + r() * (ymax - ymin);
    const m = new M4().makeTranslation(center.x + Math.cos(a) * d, y, center.z + Math.sin(a) * d);
    const ro = [0, Math.PI / 2, Math.PI, -Math.PI / 2];
    m.multiply(new M4().makeRotationY(r() * TAU)).multiply(new M4().makeRotationX(ro[Math.floor(r() * 4)] * (r() < 0.6 ? 1 : 0))).multiply(new M4().makeRotationZ(ro[Math.floor(r() * 4)] * (r() < 0.5 ? 1 : 0)));
    decoChunk(L, m, kinds[Math.floor(r() * kinds.length)], 0.8 + r() * 1.6);
  }
}
/* ---------- canvas textures ---------- */
function canvasTex(w, h, draw) {
  const c = document.createElement('canvas'); c.width = w; c.height = h; const g = c.getContext('2d');
  draw(g, w, h); const t = new THREE.CanvasTexture(c); t.minFilter = THREE.LinearMipmapLinearFilter; t.anisotropy = 4; t.userData = { c, g, draw }; return t;
}
const PAPER_HEX = '#E4E0D5', INK_HEX = '#171511';
function textPlane(L, x, y, z, nx, nz, w, h, draw, parent) {
  const tex = canvasTex(Math.round(w * 200), Math.round(h * 200), draw);
  const mat = new THREE.MeshBasicMaterial({ map: tex, transparent: true }); mat.userData.own = true;
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), mat);
  m.position.set(x + nx * 0.025, y, z + nz * 0.025); m.rotation.y = Math.atan2(nx, nz);
  (parent || L.scene).add(m); m.userData.tex = tex; return m;
}
function redrawText(m, draw) { const t = m.userData.tex; const c = t.userData.c; draw(t.userData.g, c.width, c.height); t.needsUpdate = true; }
function scrawl(text, size = 64, font = '"Special Elite"') {
  return (g, w, h) => {
    g.clearRect(0, 0, w, h); g.fillStyle = INK_HEX; g.textAlign = 'center'; g.textBaseline = 'middle';
    const lines = text.split('\n'); const fs = Math.min(size, h / (lines.length * 1.25));
    g.font = `${fs}px ${font}, "Courier New", monospace`;
    lines.forEach((ln, i) => {
      const y = h / 2 + (i - (lines.length - 1) / 2) * fs * 1.2;
      g.save(); g.translate(w / 2, y); g.rotate((Math.random() - 0.5) * 0.04); g.fillText(ln, 0, 0); g.restore();
      for (let k = 0; k < ln.length / 3; k++) { const x = w / 2 + (Math.random() - 0.5) * fs * ln.length * 0.5; g.fillRect(x, y + fs * 0.3, 2, Math.random() * fs * 0.9); }
    });
  };
}
/* ---------- interactables ---------- */
function interact(L, pos, prompt, fn, o = {}) {
  const it = { pos: pos.clone(), prompt, fn, on: true, r: o.r || 2.4, cos: o.cos || 0.9, when: o.when }; (L.inter || (L.inter = [])).push(it); return it;
}
/* ---------- simple point-light lamp visuals ---------- */
function lampVis(L, x, y, z, kind = 'bulb', parent) {
  let m;
  if (kind === 'candle') { const g = new THREE.Group(); g.add(buildObj(a => a.cyl(0, -0.25, 0, 0.035, 0.22, 8, 0.95, 0, true))); const f = new THREE.Mesh(new THREE.SphereGeometry(0.035, 8, 6), MAT.glowWarm); f.scale.y = 1.8; f.position.y = 0.03; g.add(f); m = g; }
  else if (kind === 'panel') m = new THREE.Mesh(new THREE.BoxGeometry(1.4, 0.05, 0.35), MAT.glowWhite);
  else if (kind === 'sconce') { const g = new THREE.Group(); g.add(buildObj(a => { a.box(-0.06, -0.12, -0.04, 0.06, 0.0, 0.04, 0.4, 0, true); })); const b = new THREE.Mesh(new THREE.SphereGeometry(0.08, 10, 8), MAT.glowWarm); b.position.y = 0.06; g.add(b); m = g; }
  else m = new THREE.Mesh(new THREE.SphereGeometry(0.1, 10, 8), MAT.glowWhite);
  m.position.set(x, y, z); (parent || L.scene).add(m); return m;
}

/* ---------- Escher rooms: every wall can be a floor ----------
   A face is a local frame on one side of a room: o = origin, X/Y/Z = its axes in world space, Y = that face's "up".
   fW(face, x, y, z) turns face coordinates into world coordinates, so you build on a wall exactly as on a floor.
   Gravity is always along a world axis (PL.ax 0/1/2, PL.sg ±1), so every collider stays an axis-aligned box. */
function face(o, X, Y, Z) { const ax = Y[0] ? 0 : Y[1] ? 1 : 2; return { o, X, Y, Z, ax, sg: Y[ax] > 0 ? 1 : -1 }; }
function fW(f, x, y, z) { return new V3(f.o[0] + f.X[0] * x + f.Y[0] * y + f.Z[0] * z, f.o[1] + f.X[1] * x + f.Y[1] * y + f.Z[1] * z, f.o[2] + f.X[2] * x + f.Y[2] * y + f.Z[2] * z); }
function fB(L, f, x0, y0, z0, x1, y1, z1, o) { const a = fW(f, x0, y0, z0), b = fW(f, x1, y1, z1); return L.B(Math.min(a.x, b.x), Math.min(a.y, b.y), Math.min(a.z, b.z), Math.max(a.x, b.x), Math.max(a.y, b.y), Math.max(a.z, b.z), o); }
function fStairs(L, f, x, y, z, n, rise, run, w, o = {}) { for (let i = 0; i < n; i++) fB(L, f, x - w / 2, y, z + i * run, x + w / 2, y + rise * (i + 1), z + (i + 1) * run, Object.assign({ tone: 0.88 }, o)); return { y: y + n * rise, z: z + n * run }; }
// rotation that stands a door (or anything built for +y up) on face f. Door yaw then turns it about the face's up.
function faceQ(f) { const m = new M4().makeBasis(new V3(...f.X), new V3(...f.Y), new V3(...f.Z)); return new Q4().setFromRotationMatrix(m); }
function onFace(f) { return PL.ax === f.ax && PL.sg === f.sg; }
// switch "down" to face f, keeping the eye where it was (the camera swings round smoothly over ~0.65 s)
function gravSwitch(f, feet, axisOverride) {
  const oldEye = CAM.position.clone();
  PL.setGravity(f.ax, f.sg, false, true, axisOverride);
  PL.pos.copy(feet); PL.vel.multiplyScalar(0.25);
  const eyeH = lerp(PL.eye, PL.eyeC, PL.ch);
  PL.eyeOff.copy(oldEye).sub(_v3a.copy(PL.pos).addScaledVector(PL.up, eyeH));
  PL.peakU = PL.u(); PL.grounded = false; PL.safe = [];
  AU.grav(); GAME.shake(0.18);
}
// a glowing half-ring that marks a gravity switch. Pair it with a zone: L.gravZones.push({ from, to, box, place })
function blueArch(L, center, rot, r = 1.35) {
  const g = new THREE.Mesh(new THREE.TorusGeometry(r, 0.09, 6, 22, Math.PI), MAT.glow);
  g.position.copy(center); g.quaternion.copy(rot); L.add(g);
  for (const s of [-1, 1]) { const p = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.09, 1.2, 6), MAT.glow); p.position.set(s * r, -0.6, 0); g.add(p); }
  return g;
}
/* ---------- doors every level needs ---------- */
// the door you came in by: locked behind you; you spawn 1.35 m in front of it, facing into the room
function stdEntrance(L, x, y, z, yaw, o = {}) {
  L.entrance = new Door(L, Object.assign({ x, y, z, yaw, kind: 'entrance', locked: true, swingIn: true, lockMsg: 'It will not open. There is no going back.' }, o));
  const f = new V3(Math.sin(yaw), 0, Math.cos(yaw)); if (o.upQ) f.applyQuaternion(o.upQ);
  L.spawn = { pos: new V3(x, y, z).addScaledVector(f, 1.35), yaw: faceYaw(yaw), q: o.upQ ? o.upQ.clone() : null };
}
// the real way on: blue keyhole, blue light under the leaf. Walking through it once it is open crosses into the next level.
function exitDoor(L, x, y, z, yaw, o = {}) { L.exitDoor = new Door(L, Object.assign({ x, y, z, yaw, kind: 'exit', real: true, ornate: true }, o)); return L.exitDoor; }
