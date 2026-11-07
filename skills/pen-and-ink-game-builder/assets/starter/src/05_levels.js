/* ===================== levels: LEVELS[i] = { name, sub, build(L), onStart?(L, viaPortal), update?(L, dt), titleView?(t) } =====================
   Units are metres, y is up, the player is 1.72 m tall and walks 3.15 m/s. Every level needs an entrance
   (stdEntrance: where you appear) and, unless it is the last, an exitDoor (the way on). Walking through an open
   exit door crosses straight into the next level, which GAME builds in the background while you play. */
const LEVELS = [];

/* ---------- an example enemy: patrols a loop, sees in a cone, catches you if it watches too long ---------- */
class Blot {
  constructor(L, path, o = {}) {
    this.L = L; this.path = path.map(p => new V3(...p)); this.speed = o.speed || 1.1; this.range = o.range || 7.5;
    this.obj = new THREE.Group();
    this.obj.add(buildObj(a => { const g = new THREE.IcosahedronGeometry(0.5, 1); a.geo(g, null, 0.2, PAT.MONSTER, 25); g.dispose(); }));
    const white = makeGlowMat(new THREE.Color(0.93, 0.91, 0.85), { pulse: 0 }), dark = makeGlowMat(INK, { pulse: 0 });
    white.userData.own = dark.userData.own = true;
    const eye = new THREE.Mesh(new THREE.CircleGeometry(0.2, 18), white); eye.position.z = 0.49; this.obj.add(eye);
    this.pupil = new THREE.Mesh(new THREE.CircleGeometry(0.08, 12), dark); this.pupil.position.z = 0.5; this.obj.add(this.pupil);
    L.add(this.obj); this.reset();
  }
  reset() { this.seg = 0; this.pos = this.path[0].clone(); this.look = this.path[1].clone().sub(this.pos).normalize(); this.sus = 0; this.t = 0; this.warned = false;
    this.obj.position.copy(this.pos); this.obj.lookAt(_v3c.copy(this.pos).add(this.look)); } // placed even while off
  update(dt) {
    if (this.off) return;
    this.t += dt;
    const P = this.path, tgt = P[(this.seg + 1) % P.length], d = _v3a.copy(tgt).sub(this.pos), dist = d.length();
    if (this.sus < 0.35) { // it stops to stare once it has noticed you
      if (dist < this.speed * dt) { this.pos.copy(tgt); this.seg = (this.seg + 1) % P.length; } else this.pos.addScaledVector(d, this.speed * dt / dist);
    }
    const toP = _v3b.copy(PL.center).sub(this.pos), pd = toP.length(); toP.divideScalar(pd || 1);
    const want = this.sus > 0.2 ? toP : dist > 0.01 ? d.divideScalar(dist) : this.look;
    this.look.lerp(want, 1 - Math.exp(-dt * 3)).normalize();
    // a cone, a range (shorter while you crouch) and a clear line of sight
    const range = this.range * (PL.crouch ? 0.55 : 1);
    const sees = pd < range && this.look.dot(toP) > 0.72 && GAME.los(this.pos, PL.center, 0.3);
    this.sus = clamp(this.sus + (sees ? dt * (1.9 - pd / range) : -dt * 0.4), 0, 1);
    GAME.threat = Math.max(GAME.threat, this.sus);
    if (sees && this.sus > 0.25 && !this.warned) { this.warned = true; AU.tone({ f: 330, fEnd: 170, dur: 0.7, gain: 0.14, type: 'triangle', rev: 0.5 }); }
    if (this.sus < 0.05) this.warned = false;
    if (this.sus >= 1) { this.sus = 0; GAME.caught(this); }
    this.obj.position.copy(this.pos); this.obj.position.y += Math.sin(this.t * 2.1) * 0.12;
    this.obj.lookAt(_v3c.copy(this.obj.position).add(this.look));
    this.pupil.scale.setScalar(1 + this.sus * 0.8);
  }
}

/* ---------------- I. THE STAIR HALL: move, climb, jump a gap for the key, open the locked door ---------------- */
LEVELS[1] = {
  name: 'The Stair Hall', sub: 'find the blue key',
  titleView: t => ({ pos: [Math.sin(t * 0.05) * 19, 11 + Math.sin(t * 0.08) * 2, 1.5 + Math.cos(t * 0.05) * 19], look: [0, 2.5, 1.5] }),
  build(L) {
    const E = L.env; E.sunDir.set(-0.5, 0.8, 0.32); E.sun = 0.8; E.amb = 0.5; E.fogDen = 0.009; E.hatch = 8.5; L.killU = -20; L.surf = 'stone';
    E.bed = { root: 55, fifth: 1.5, cut: 260, noise: 0.05, noiseF: 600, gain: 0.42 };
    const WALL = { pat: PAT.BRICK, tone: 0.86 }, SLAB = { pat: PAT.ASHLAR, tone: 0.9 };
    L.B(-6.5, -0.5, -7.25, 6.5, 0, 10.25, { pat: PAT.CHECKER, tone: 0.92 });                  // floor
    wallX(L, -6.5, 6.5, -7.25, -6.75, 0, 8, [doorHole(0, 0)], WALL);                          // south wall, with the entrance
    stdEntrance(L, 0, 0, -7, 0);
    L.B(-7, -0.5, -7.25, -6.5, 8, 10.25, WALL); L.B(6.5, -0.5, -7.25, 7, 8, 10.25, WALL);      // west, east
    const st = stairs(L, -4.8, 0, -1.5, '+z', 14, { w: 2, rise: 0.22, run: 0.34, rails: true, railSides: [1] });
    wallX(L, -6.5, 6.5, 9.75, 10.25, 0, 8, [doorHole(-3.5, st.y)], WALL);                     // north wall, the exit is up on the gallery
    // two galleries with a gap between them; the key is across the gap
    L.B(-6.5, st.y - 0.5, st.z, -0.8, st.y, 9.75, SLAB);
    L.B(0.8, st.y - 0.5, st.z, 6.5, st.y, 9.75, SLAB);
    rail(L, -6.45, st.z + 0.05, -5.85, st.z + 0.05, st.y); rail(L, -3.75, st.z + 0.05, -0.85, st.z + 0.05, st.y); rail(L, 0.85, st.z + 0.05, 6.45, st.z + 0.05, st.y);
    for (const x of [-1.2, 1.2]) column(L, x, 0, st.z + 0.4, 0.28, st.y - 0.5);
    for (const z of [-4, 0.5]) arch(L, 6.3, 0, z, 'z', 2.2, 2.6, 0.4, { solid: false });
    exitDoor(L, -3.5, st.y, 10.0, 0, { locked: true, lockMsg: 'Locked. Something blue opens it.' });
    new Pickup(L, 'key', 4.6, st.y + 0.95, 7.2, { onGet: () => { L.exitDoor.locked = false; GAME.toast('The blue key. Somewhere, a lock gives.', 3); GAME.pulse = 0.6; } });
    L.B(2, 0, -4, 3, 0.75, -3, { pat: PAT.WOOD, tone: 0.6 });
    new Pickup(L, 'note', 2.5, 1.1, -3.5, { text: 'Every door here opens one way. Blue means real.' });
    L.trigger(-2.6, st.y, st.z, -0.8, st.y + 3, 9.75, () => GAME.hint('jump'));
    textPlane(L, -3.5, 6.3, 9.75, 0, -1, 2.6, 0.7, scrawl('THE WAY ON', 90));
    lampVis(L, 0, 6.2, 1.5, 'bulb'); L.light(0, 6.2, 1.5, 12, 0.3, { flicker: 0.05 });
    scatterDeco(L, 9, 15, 28, 4, 20, ['stairs', 'arch', 'column', 'block'], 7, new V3(0, 0, 1.5));
  }
};

/* ---------------- II. THE TURNED ROOM: slip past the watcher, walk through the arch, the north wall becomes the floor ---------------- */
const FLOOR2 = face([0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]);
const NORTH2 = face([0, 0, 6], [1, 0, 0], [0, 0, -1], [0, 1, 0]); // y = height off the wall, z runs up the wall
LEVELS[2] = {
  name: 'The Turned Room', sub: 'down is a suggestion',
  build(L) {
    const E = L.env; E.sun = 0; E.amb = 0.64; E.fogDen = 0.012; E.hatch = 9; L.killU = -1e9; L.surf = 'wood';
    E.bed = { root: 52, fifth: 1.414, cut: 240, gain: 0.4 }; E.mood.boil = 0.12; E.mood.tendril = 0.22;
    L.B(-6.5, -0.5, -6.5, 6.5, 0, 6.5, { pat: PAT.BLOCKS, tone: 0.95 });                     // floor
    L.B(-6.5, 12, -6.5, 6.5, 12.5, 6.5, { pat: PAT.WOOD, tone: 0.86 });                      // ceiling
    wallX(L, -6.5, 6.5, -6.5, -6, 0, 12, [doorHole(0, 0)], { pat: PAT.BRICK, tone: 0.86 });  // south, with the entrance
    stdEntrance(L, 0, 0, -6.25, 0);
    L.B(-6.5, 0, 6, 6.5, 12, 6.5, { pat: PAT.ASHLAR, tone: 0.9 });                           // north: you will walk on it
    L.B(-6.5, 0, -6, -6, 12, 6, { pat: PAT.DAMASK, tone: 0.9 }); L.B(6, 0, -6, 6.5, 12, 6, { pat: PAT.DAMASK, tone: 0.9 });
    // the floor: furniture to hide behind, and a watcher
    L.B(-4.6, 0, -2.4, -2.6, 0.95, -1.4, { pat: PAT.WOOD, tone: 0.6 }); L.B(2.4, 0, 0.6, 3.6, 1.4, 1.6, { pat: PAT.BOOKS, tone: 0.8 });
    L.ent(new Blot(L, [[-4, 1.4, -0.4], [4, 1.4, -0.4], [4, 1.4, 3.0], [-4, 1.4, 3.0]], { speed: 1.2 }));
    L.trigger(-6, 0, -4.4, 6, 3, -3.2, () => GAME.hint('crouch'));
    // the arch: walk through it and the north wall is the floor
    blueArch(L, new V3(0, 1.2, 4.7), new Q4());
    L.gravZones.push({ from: FLOOR2, to: NORTH2, box: [-1.3, 0, 4.4, 1.3, 2.6, 5.1], place: p => new V3(clamp(p.x, -1, 1), 1.0, 6) });
    L.trigger(-3, 0, 2.6, 3, 3, 4.3, () => GAME.hint('arch'));
    // on the north wall, built in that wall's own coordinates
    const N = NORTH2, DW = { pat: PAT.BRICK, tone: 0.86 };
    fB(L, N, -6, 0, 7.75, -0.68, 5, 8.25, DW); fB(L, N, 0.68, 0, 7.75, 6, 5, 8.25, DW); fB(L, N, -0.68, 2.44, 7.75, 0.68, 5, 8.25, DW);
    exitDoor(L, ...fW(N, 0, 0, 8).toArray(), 0, { upQ: faceQ(N) });
    fB(L, N, -2, 0, 2.2, 2, 0.04, 7.4, { pat: PAT.CARPET, tone: 0.5, solid: false });
    fB(L, N, -5.8, 0, 3.5, -5.1, 2.6, 7.2, { pat: PAT.BOOKS, tone: 0.85 });
    fB(L, N, 3, 0, 3.2, 4.6, 0.8, 4.4, { pat: PAT.WOOD, tone: 0.6 });
    const lp = fW(N, 0, 4.2, 5); lampVis(L, lp.x, lp.y, lp.z, 'bulb'); L.light(lp.x, lp.y, lp.z, 9, 0.3);
    // a third floor nobody uses: the ceiling, and stairs lying on the west wall
    L.B(-1, 11.2, -1, 1, 12, 1, { pat: PAT.WOOD, tone: 0.6, solid: false });
    decoChunk(L, new M4().makeTranslation(-6, 4.5, -2).multiply(new M4().makeRotationZ(-Math.PI / 2)), 'stairs', 0.9);
    lampVis(L, 0, 9, -1, 'bulb'); L.light(0, 9, -1, 14, 0.35);
  }
};

/* ---------------- III. THE MARGIN: the end. A door standing alone on blank paper ---------------- */
LEVELS[3] = {
  name: 'The Margin', sub: 'where the drawing stops',
  build(L) {
    const E = L.env; E.sunDir.set(0.3, 0.9, -0.2); E.sun = 0.45; E.amb = 0.85; E.fogDen = 0.035; E.hatch = 7; L.killU = -20;
    E.bed = { root: 65.4, fifth: 1.5, cut: 520, gain: 0.25 }; E.mood.boil = 0.03; E.mood.tendril = 0;
    L.B(-40, -0.5, -40, 40, 0, 40, { pat: PAT.PAPER, tone: 1, edges: false });
    stdEntrance(L, 0, 0, 0, 0);
    const tex = canvasTex(1024, 256, scrawl('YOU WALKED OUT\nOF THE DRAWING', 96));
    const m = new THREE.Mesh(new THREE.PlaneGeometry(8, 2), new THREE.MeshBasicMaterial({ map: tex, transparent: true }));
    m.material.userData.own = true; m.rotation.set(-Math.PI / 2, 0, Math.PI); // lie flat, reading away from the door
    m.position.set(0, 0.02, 7.5); L.add(m);
    scatterDeco(L, 6, 12, 30, 2, 14, ['stairs', 'arch', 'column'], 3);
  },
  update(L) {
    if (L.t > 3 && !L.data.thanks) { L.data.thanks = 1; GAME.toast('Thank you for playing.', 4); }
    if (L.t > 8 && !L.data.out) { L.data.out = 1; GAME.fadeTo(1, 2.5); }
    if (L.t > 11) GAME.toTitle();
  }
};
