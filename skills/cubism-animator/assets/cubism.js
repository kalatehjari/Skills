// CUBISM.JS — a cubist / avant-garde animation library for canvas films (Cubism-Animator skill).
// Planes, facets, Delaunay discs, Kandinsky bursts, a plane-built heroine (face + figure), the wedge antagonist,
// claw hands, red lines, a Constructivist lyric strip. Load after engine/video/boot.js; everything lands on globalThis.CUBE.
(function () {
  const U = globalThis.U, G = globalThis.G, Studio = globalThis.Studio, S = globalThis.SCORE;
  const { T } = S;
  const { clamp, lerp } = U;
  const E = U.ease;
  const W = G.W, H = G.H;
  const BEATS = S.beats;
  const INK = '#141012', RED = '#C8261E', CREAM = '#F1E6CF';
  // identity signs of the heroine (set once from the user's reference photos): hair, eye, lips, tee
  const LOOK = { hair: INK, iris: '#C98A2B', lips: null, tee: null };
  const setLook = (o) => Object.assign(LOOK, o || {});
  const h = (...a) => U.hash(...a);
  const sm = (x) => x * x * (3 - 2 * x);
  const prog = (t, a, b) => clamp((t - a) / (b - a));
  const lastBeat = (t) => { if (t < BEATS[0]) return -1; let lo = 0, hi = BEATS.length - 1; while (lo < hi) { const m = (lo + hi + 1) >> 1; if (BEATS[m] <= t) lo = m; else hi = m - 1; } return lo; };
  const sinceBeat = (t) => { const i = lastBeat(t); return i < 0 ? 9 : t - BEATS[i]; };
  const kick = (t, d = 7) => Math.exp(-sinceBeat(t) * d);
  const B = (b, beat = 0) => T(b, beat);

  // ---------------- palettes ----------------
  const PAL = {
    night:  { bg: ['#1B1F3A', '#2A2F52', '#3B3A5E', '#151729', '#4A4F7A'], L: '#D9CDB4', M: '#9A8FB0', D: '#4B4770', A: '#C9A44A', W: '#E8DFCB', R: RED },
    desert: { bg: ['#D7A65E', '#C98A45', '#E8C98F', '#B87436', '#EAD9B0', '#9C5E2E'], L: '#F0D9A8', M: '#D49A55', D: '#8E5126', A: '#5E7FA3', W: '#F4E8CF', R: RED },
    blood:  { bg: ['#C8261E', '#8E1712', '#1A0A08', '#E5D8BE', '#4A0D0A'], L: '#EAD9BC', M: '#D25A3E', D: '#6E1410', A: '#E8B04A', W: '#F1E6CF', R: '#E0362A' },
    storm:  { bg: ['#1E3B4A', '#2E5A66', '#14262F', '#6F8E92', '#0E1A20', '#3E6E7A'], L: '#C9D6D2', M: '#6F9AA0', D: '#24424C', A: '#E3C36A', W: '#E4EBE6', R: '#B33A2E' },
    ember:  { bg: ['#E06A2A', '#B8381C', '#F2A43A', '#5A1E3A', '#2A0E1E', '#F6CF6A'], L: '#F6DDB0', M: '#E58A4A', D: '#7A2A3A', A: '#3A6EA5', W: '#F8EBD2', R: '#C8261E' },
    dawn:   { bg: ['#E7B8C2', '#B9A5D6', '#F2D49A', '#9CCBB0', '#F6E6D4', '#7C9BD0'], L: '#F7E6D2', M: '#E2A7A0', D: '#7A6AA8', A: '#5FA57A', W: '#FBF3E6', R: '#D0453E' },
    gold:   { bg: ['#E3B054', '#C98D3A', '#F2D99A', '#6E8B5A', '#3E5A4A', '#F7EBCB'], L: '#F6E2B6', M: '#D8A055', D: '#5E6E44', A: '#3E6EA5', W: '#FBF1DA', R: '#C8261E' },
    white:  { bg: ['#F4EEE2', '#ECE4D4', '#F8F4EA', '#E2D9C6'], L: '#F7F1E4', M: '#E0D4BE', D: '#B7A88E', A: '#C8261E', W: '#FBF8F1', R: RED },
  };

  // ---------------- drawing primitives ----------------
  function pathOf(ctx, pts) { ctx.beginPath(); pts.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y))); ctx.closePath(); }
  function bbox(pts) { let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9; for (const [x, y] of pts) { x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); } return [x0, y0, x1, y1]; }
  function texture(ctx, pts, tex) {
    const [x0, y0, x1, y1] = bbox(pts);
    ctx.save(); pathOf(ctx, pts); ctx.clip();
    if (tex.kind === 'hatch') {
      ctx.strokeStyle = tex.color || 'rgba(20,16,18,0.28)'; ctx.lineWidth = tex.lw || 2;
      const a = tex.angle ?? 0.8, gap = tex.gap || 11, cx = (x0 + x1) / 2, cy = (y0 + y1) / 2, R = Math.hypot(x1 - x0, y1 - y0);
      ctx.translate(cx, cy); ctx.rotate(a); ctx.beginPath();
      for (let k = -R; k <= R; k += gap) { ctx.moveTo(-R, k); ctx.lineTo(R, k); }
      ctx.stroke();
    } else if (tex.kind === 'dots') {
      ctx.fillStyle = tex.color || 'rgba(20,16,18,0.3)'; const gap = tex.gap || 12, r = tex.r || 2.2;
      for (let y = y0; y <= y1; y += gap) for (let x = x0 + ((y / gap) % 2) * gap / 2; x <= x1; x += gap) { ctx.beginPath(); ctx.arc(x, y, r, 0, 6.29); ctx.fill(); }
    } else if (tex.kind === 'grad') {
      const g = ctx.createLinearGradient(x0, y0, x1, y1); g.addColorStop(0, 'rgba(255,255,255,0.22)'); g.addColorStop(1, 'rgba(0,0,0,0.28)');
      ctx.fillStyle = g; ctx.fillRect(x0, y0, x1 - x0, y1 - y0);
    }
    ctx.restore();
  }
  function plane(ctx, pts, fill, o = {}) {
    pathOf(ctx, pts);
    if (fill) { ctx.globalAlpha = o.alpha ?? 1; ctx.fillStyle = fill; ctx.fill(); ctx.globalAlpha = 1; }
    if (o.tex) texture(ctx, pts, o.tex);
    if (o.lw !== 0) { pathOf(ctx, pts); ctx.lineWidth = o.lw || 3.5; ctx.strokeStyle = o.stroke || INK; ctx.lineJoin = 'miter'; ctx.globalAlpha = o.strokeAlpha ?? 1; ctx.stroke(); ctx.globalAlpha = 1; }
  }
  function line(ctx, a, b, lw = 4, col = INK) { ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.lineWidth = lw; ctx.strokeStyle = col; ctx.lineCap = 'butt'; ctx.stroke(); }
  function circle(ctx, x, y, r, fill, o = {}) { ctx.beginPath(); ctx.arc(x, y, Math.max(0.1, r), 0, Math.PI * 2); if (fill) { ctx.globalAlpha = o.alpha ?? 1; ctx.fillStyle = fill; ctx.fill(); ctx.globalAlpha = 1; } if (o.lw) { ctx.lineWidth = o.lw; ctx.strokeStyle = o.stroke || INK; ctx.stroke(); } }
  const texFor = (i, seed, col) => { const r = h(i, seed); return r < 0.32 ? { kind: 'hatch', angle: (h(i, seed + 1) - 0.5) * 2.4, gap: 9 + 8 * h(i, seed + 2), color: col } : r < 0.5 ? { kind: 'dots', gap: 11 + 6 * h(i, seed + 3), color: col } : r < 0.75 ? { kind: 'grad' } : null; };

  // ---------------- backgrounds: analytic facets ----------------
  function facets(ctx, t, pal, seed, o = {}) {
    const cols = PAL[pal].bg, nx = o.nx || 6, ny = o.ny || 4, drift = o.drift ?? 22, M = 240;
    ctx.fillStyle = cols[0]; ctx.fillRect(-W, -H, W * 3, H * 3);
    const P = [];
    for (let j = 0; j <= ny; j++) for (let i = 0; i <= nx; i++) {
      const edge = i === 0 || j === 0 || i === nx || j === ny;
      const bx = -M + (i / nx) * (W + 2 * M), by = -M + (j / ny) * (H + 2 * M);
      const jx = edge ? 0 : (h(i, j, seed) - 0.5) * (W / nx) * 0.8, jy = edge ? 0 : (h(j, i, seed + 1) - 0.5) * (H / ny) * 0.8;
      P.push([bx + jx + drift * U.noise1(t * 0.12 + i * 1.7 + j, seed), by + jy + drift * U.noise1(t * 0.1 + j * 2.3 + i, seed + 3)]);
    }
    const at = (i, j) => P[j * (nx + 1) + i];
    let k = 0;
    for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) {
      const a = at(i, j), b = at(i + 1, j), c = at(i + 1, j + 1), d = at(i, j + 1);
      const tris = h(i, j, seed + 5) < 0.5 ? [[a, b, c], [a, c, d]] : [[a, b, d], [b, c, d]];
      for (const tri of tris) {
        k++;
        const col = cols[Math.floor(h(k, seed + 7) * cols.length)];
        plane(ctx, tri, col, { alpha: o.alpha ?? 0.92, lw: 1.6, strokeAlpha: 0.45, tex: (o.tex ?? true) ? texFor(k, seed, 'rgba(20,16,18,0.16)') : null });
      }
    }
    // a few Kandinsky lines across the field
    for (let q = 0; q < (o.lines ?? 4); q++) {
      const a = [h(q, seed, 1) * W, -50], b = [h(q, seed, 2) * W, H + 50];
      line(ctx, a, b, 2 + 4 * h(q, seed, 3), 'rgba(20,16,18,0.55)');
    }
  }
  // Delaunay disc: concentric rings in quartered colour segments
  function disc(ctx, x, y, R, n, cols, rot = 0, o = {}) {
    for (let k = 0; k < n; k++) {
      const r0 = R * (1 - k / n), r1 = R * (1 - (k + 1) / n);
      for (let q = 0; q < 4; q++) {
        const a0 = rot + q * Math.PI / 2 + (o.split ? (h(k, q, 9) - 0.5) * o.split : 0), a1 = a0 + Math.PI / 2;
        const off = o.burst ? o.burst * (60 + 220 * h(k, q, 3)) : 0, am = (a0 + a1) / 2;
        const ox = x + Math.cos(am) * off, oy = y + Math.sin(am) * off;
        ctx.beginPath(); ctx.arc(ox, oy, r0, a0, a1); ctx.arc(ox, oy, Math.max(0, r1), a1, a0, true); ctx.closePath();
        ctx.globalAlpha = o.alpha ?? 1; ctx.fillStyle = cols[(k + q) % cols.length]; ctx.fill(); ctx.globalAlpha = 1;
        ctx.lineWidth = o.lw ?? 2.5; ctx.strokeStyle = INK; ctx.stroke();
      }
    }
  }
  // Kandinsky burst: circles, triangles, bars flying from a point
  function burst(ctx, t, t0, x, y, n, cols, seed, dur = 3) {
    const u = clamp((t - t0) / dur); if (u <= 0 || u >= 1) return;
    for (let k = 0; k < n; k++) {
      const a = h(k, seed) * Math.PI * 2, d = E.outCubic(u) * (200 + 1100 * h(k, seed + 1)), px = x + Math.cos(a) * d, py = y + Math.sin(a) * d * 0.75;
      const s = (10 + 50 * h(k, seed + 2)) * (1 - u * 0.4), col = cols[k % cols.length], typ = k % 3;
      ctx.save(); ctx.translate(px, py); ctx.rotate(u * 6 * (h(k, seed + 4) - 0.5) + a);
      if (typ === 0) circle(ctx, 0, 0, s, col, { lw: 2.5 });
      else if (typ === 1) plane(ctx, [[0, -s], [s * 0.9, s * 0.7], [-s * 0.9, s * 0.7]], col, { lw: 2.5 });
      else plane(ctx, [[-s * 2, -4], [s * 2, -4], [s * 2, 4], [-s * 2, 4]], INK, { lw: 0 });
      ctx.restore();
    }
  }

  // ---------------- HER: the cubist face ----------------
  // groups move together when the face splits apart
  const FACE = [
    { g: 0, pts: [[-240, -250], [60, -330], [250, -210], [262, 110], [180, 210], [-210, 200], [-272, 40]], role: 'K' },               // hair mass
    { g: 1, pts: [[-400, 400], [400, 400], [480, 640], [-480, 640]], role: 'W', tex: { kind: 'hatch', angle: -0.4, gap: 14, color: 'rgba(20,16,18,0.12)' } }, // shoulders (white tee)
    { g: 1, pts: [[30, 400], [400, 400], [480, 640], [140, 640]], role: 'M', alpha: 0.55 },                                           // shoulder shadow plane
    { g: 2, pts: [[-72, 170], [64, 170], [84, 420], [-92, 420]], role: 'M', tex: { kind: 'grad' } },                                   // neck
    { g: 3, pts: [[-6, -222], [150, -168], [176, -24], [236, 46], [166, 72], [170, 138], [96, 212], [6, 222]], role: 'D', tex: { kind: 'hatch', angle: 1.1, gap: 10, color: 'rgba(20,16,18,0.2)' } }, // profile plane (right)
    { g: 4, pts: [[-162, -176], [-6, -222], [6, 222], [-62, 204], [-150, 96], [-176, -36]], role: 'L' },                              // frontal plane (left)
    { g: 4, pts: [[-150, 40], [-36, 64], [-104, 172]], role: 'M', alpha: 0.75 },                                                      // cheek facet
    { g: 5, pts: [[-122, -176], [104, -204], [44, -96], [-104, -104]], role: 'W', tex: { kind: 'dots', gap: 12, color: 'rgba(20,16,18,0.18)' } }, // forehead
    { g: 4, pts: [[-4, -50], [-4, 96], [-46, 96]], role: 'M' },                                                                       // nose shadow
  ];
  const FRINGE = { g: 6, pts: [[-214, -244], [86, -296], [140, -204], [26, -132], [-58, -96], [-178, -78], [-222, -150]] };
  function almond(cx, cy, w, hgt, open) { const p = []; for (let k = 0; k <= 10; k++) { const u = k / 10; p.push([cx - w + 2 * w * u, cy - Math.sin(Math.PI * u) * hgt * open]); } for (let k = 9; k >= 1; k--) { const u = k / 10; p.push([cx - w + 2 * w * u, cy + Math.sin(Math.PI * u) * hgt * 0.75 * open]); } return p; }
  function eyeFront(ctx, cx, cy, s, open, pal) {
    if (open < 0.08) { line(ctx, [cx - 50 * s, cy], [cx + 52 * s, cy - 6 * s], 6 * s); return; }
    const pts = almond(cx, cy, 52 * s, 26 * s, open);
    plane(ctx, pts, '#F6EFE2', { lw: 4.5 * s });
    ctx.save(); pathOf(ctx, pts); ctx.clip();
    circle(ctx, cx, cy, 19 * s, LOOK.iris); circle(ctx, cx, cy, 8 * s, INK); plane(ctx, [[cx - 19 * s, cy - 19 * s], [cx + 19 * s, cy - 19 * s], [cx, cy]], 'rgba(20,16,18,0.25)', { lw: 0 });
    ctx.restore();
    line(ctx, [cx + 50 * s, cy - 2 * s], [cx + 72 * s, cy - 18 * s], 5 * s);
  }
  function eyeProfile(ctx, cx, cy, s, open) {
    if (open < 0.08) { line(ctx, [cx - 32 * s, cy], [cx + 30 * s, cy + 2 * s], 5 * s); return; }
    const pts = [[cx - 34 * s, cy - 18 * s * open], [cx + 32 * s, cy], [cx - 34 * s, cy + 14 * s * open]];
    plane(ctx, pts, '#F6EFE2', { lw: 4 * s });
    circle(ctx, cx + 10 * s, cy - 1, 9 * s * Math.min(1, open), LOOK.iris); circle(ctx, cx + 12 * s, cy - 1, 4 * s, INK);
  }
  // o: { s, split 0..1, snap 0..1, palette, eyes 0..1, mouth 0..1, tears 0..1, extraEyes 0..1, half: 'both'|'dark'|'light', rot, seed, smile }
  function face(ctx, x, y, t, o = {}) {
    const pal = PAL[o.pal || 'desert'], s = o.s || 1, split = o.split || 0, seed = o.seed || 3;
    const bi = lastBeat(t), snap = (o.snap || 0) * (0.35 + 0.65 * kick(t, 5));
    const role = (r) => (r === 'K' ? LOOK.hair : r === 'W' && LOOK.tee ? LOOK.tee : pal[r]);
    const tf = (g) => {
      const a = h(g, seed) * Math.PI * 2, d = split * (90 + 300 * h(g, seed + 1)), r = split * (h(g, seed + 2) - 0.5) * 1.0;
      const sx = snap * (h(g, bi, seed + 4) - 0.5) * 120, sy = snap * (h(g, bi, seed + 5) - 0.5) * 90;
      return { dx: Math.cos(a) * d + sx, dy: Math.sin(a) * d * 0.8 + sy, r: r + snap * (h(g, bi, seed + 6) - 0.5) * 0.25 };
    };
    const inGroup = (g, fn) => { const q = tf(g); ctx.save(); ctx.translate(q.dx, q.dy); ctx.rotate(q.r); fn(); ctx.restore(); };
    ctx.save(); ctx.translate(x, y); ctx.rotate(o.rot || 0); ctx.scale(s, s);
    const half = o.half || 'both';
    if (half !== 'both') { ctx.beginPath(); if (half === 'dark') ctx.rect(-2000, -2000, 2000, 4000); else ctx.rect(0, -2000, 2000, 4000); ctx.clip(); }
    FACE.forEach((p, i) => inGroup(p.g, () => plane(ctx, p.pts, role(p.role), { alpha: p.alpha, tex: p.tex, lw: 3.5 })));
    // features ride on their planes
    inGroup(4, () => {
      eyeFront(ctx, -84, -36, 1, o.eyes ?? 1, pal);
      plane(ctx, [[-150, -96], [-40, -108], [-30, -92], [-146, -78]], INK, { lw: 0 });                    // brow
      if (o.tears) { plane(ctx, [[-92, -6], [-80, -6], [-74, -6 + 220 * o.tears], [-90, -6 + 220 * o.tears]], '#3B6FA8', { lw: 2 }); }
    });
    inGroup(3, () => {
      eyeProfile(ctx, 104, -44, 1, o.eyes ?? 1);
      plane(ctx, [[60, -102], [150, -96], [156, -82], [64, -86]], INK, { lw: 0 });
    });
    // lips: two red planes, the mouth opens by separating them
    inGroup(7, () => {
      const m = (o.mouth || 0) * 34, sl = o.smile ? 8 : 0;
      plane(ctx, [[-44, 140 - sl], [-8, 124], [8, 128], [46, 138 - sl], [6, 148]], LOOK.lips || pal.R, { lw: 3 });
      if (m > 4) plane(ctx, [[-36, 148], [36, 148], [24, 150 + m], [-24, 150 + m]], INK, { lw: 0 });
      plane(ctx, [[-36, 152 + m], [38, 150 + m], [4, 182 + m]], LOOK.lips || pal.R, { lw: 3, tex: { kind: 'grad' } });
    });
    inGroup(6, () => plane(ctx, FRINGE.pts, LOOK.hair, { lw: 3.5 }));
    // simultaneity: extra eyes appear on the shards (the gaze multiplies under pressure)
    if (o.extraEyes > 0) {
      const spots = [[-300, 470, 3, 0.9], [210, -150, 5, 0.7], [-200, -40, 0, 0.6], [300, 520, 1, 0.8], [40, 300, 2, 0.6]];
      spots.forEach(([ex, ey, g, sc], k) => { if (k / spots.length < o.extraEyes) inGroup(g, () => (k % 2 ? eyeProfile(ctx, ex, ey, sc, 1) : eyeFront(ctx, ex, ey, sc, 1, pal))); });
    }
    // papier-collé scrap on the shoulder: the title in newsprint
    if (o.collage !== false) inGroup(1, () => {
      const pts = [[-360, 470], [-150, 452], [-140, 560], [-352, 578]];
      plane(ctx, pts, '#EFE7D2', { lw: 2.5, tex: { kind: 'dots', gap: 9, r: 1.4, color: 'rgba(20,16,18,0.2)' } });
      ctx.save(); ctx.translate(-250, 525); ctx.rotate(-0.08); ctx.fillStyle = INK; ctx.textAlign = 'center'; ctx.direction = 'rtl'; ctx.font = '500 44px Vazir'; ctx.fillText('تن به تن', 0, 0); ctx.restore();
    });
    ctx.restore();
  }

  // ---------------- HER: the figure in planes ----------------
  const add = (a, b) => [a[0] + b[0], a[1] + b[1]], P = (L, a) => [L * Math.sin(a), L * Math.cos(a)];
  function poses(o) {
    const ph = (o.phase || 0) * Math.PI * 2, sw = Math.sin(ph);
    switch (o.pose) {
      case 'walk': return { hip: -392, lean: 0.06, legF: [0.42 * sw, 0.42 * sw - 0.5 * Math.max(0, Math.cos(ph + 0.3))], legB: [-0.42 * sw, -0.42 * sw - 0.5 * Math.max(0, -Math.cos(ph + 0.3))], armF: [-0.3 * sw, -0.3 * sw + 0.3], armB: [0.3 * sw, 0.3 * sw + 0.3], head: 0.02 };
      case 'run': return { hip: -370, lean: 0.3, legF: [0.85 * sw + 0.15, 0.85 * sw - 1.3 * Math.max(0, Math.cos(ph + 0.4))], legB: [-0.85 * sw + 0.15, -0.85 * sw - 1.3 * Math.max(0, -Math.cos(ph + 0.4))], armF: [-0.8 * sw, -0.8 * sw + 1.4], armB: [0.8 * sw, 0.8 * sw + 1.4], head: 0 };
      case 'kneel': return { hip: -230, lean: 0.15, legF: [1.45, 0.05], legB: [0.15, -1.52], armF: [0.3, 0.5], armB: [0.1, 0.4], head: 0.35 };
      case 'hug': return { hip: -60, lean: 0.35, legF: [2.35, -0.2], legB: [2.2, -0.25], armF: [0.95, 2.05], armB: [0.85, 1.95], head: 0.4 };
      case 'open': return { hip: -392, lean: -0.05, legF: [0.18, 0.05], legB: [-0.18, -0.05], armF: [2.1, 2.3], armB: [-2.1, -2.3], head: -0.3 };
      default: return { hip: -392, lean: 0, legF: [0.05, 0.02], legB: [-0.05, -0.02], armF: [0.1, 0.12], armB: [-0.08, 0.04], head: 0 };
    }
  }
  function seg(ctx, a, b, w0, w1, fill, lw = 3) {
    const ang = Math.atan2(b[1] - a[1], b[0] - a[0]) + Math.PI / 2, c = Math.cos(ang), s = Math.sin(ang);
    plane(ctx, [[a[0] + c * w0, a[1] + s * w0], [b[0] + c * w1, b[1] + s * w1], [b[0] - c * w1, b[1] - s * w1], [a[0] - c * w0, a[1] - s * w0]], fill, { lw });
  }
  // o: { s, dir, pose, phase, j, pal, mono (single colour), split }
  function figure(ctx, x, y, t, o = {}) {
    const pal = PAL[o.pal || 'desert'], p = Object.assign(poses(o), o.j || {}), s = o.s || 1;
    const mono = o.mono, cL = mono || pal.L, cM = mono || pal.M, cD = mono || pal.D, cK = mono || INK, cW = mono || pal.W, lw = mono ? 0 : 3;
    const sp = o.split || 0, jit = (k) => [sp * (h(k, 11) - 0.5) * 160, sp * (h(k, 12) - 0.5) * 120];
    ctx.save(); ctx.translate(x, y); ctx.scale(s * (o.dir || 1), s);
    const hip = [0, p.hip], sh = add(hip, P(250, Math.PI - p.lean)), neck = add(sh, P(40, Math.PI - p.lean));
    const leg = (lg, dx) => { const a = add(hip, [dx, 0]); const k = add(a, P(195, lg[0])); return [a, k, add(k, P(190, lg[1]))]; };
    const arm = (ar, dx) => { const a = add(sh, [dx, 0]); const e = add(a, P(140, ar[0])); return [a, e, add(e, P(130, ar[1]))]; };
    const lB = leg(p.legB, -12), lF = leg(p.legF, 12), aB = arm(p.armB, -14), aF = arm(p.armF, 14);
    const piece = (k, fn) => { const [dx, dy] = jit(k); ctx.save(); ctx.translate(dx, dy); fn(); ctx.restore(); };
    piece(1, () => { seg(ctx, aB[0], aB[1], 20, 14, cD, lw); seg(ctx, aB[1], aB[2], 14, 10, cD, lw); });
    piece(2, () => { seg(ctx, lB[0], lB[1], 40, 24, cK, lw); seg(ctx, lB[1], lB[2], 24, 14, cK, lw); });
    piece(3, () => { seg(ctx, lF[0], lF[1], 42, 26, mono || '#2A2228', lw); seg(ctx, lF[1], lF[2], 26, 15, mono || '#2A2228', lw); });
    // torso: two planes, light and shadow (simultaneous front and side)
    const n = [Math.cos(p.lean), Math.sin(p.lean)], at = (b, f) => [b[0] + n[0] * f, b[1] + n[1] * f];
    piece(4, () => { plane(ctx, [at(sh, -70), at(sh, 0), at(hip, 0), at(hip, -56)], cW, { lw, tex: mono ? null : { kind: 'hatch', angle: 0.5, gap: 12, color: 'rgba(20,16,18,0.12)' } }); });
    piece(5, () => { plane(ctx, [at(sh, 0), at(sh, 62), at(hip, 52), at(hip, 0)], cM, { lw }); });
    piece(6, () => { seg(ctx, aF[0], aF[1], 20, 14, cL, lw); seg(ctx, aF[1], aF[2], 14, 10, cL, lw); });
    // head: bob as a black trapezoid, face as a sharp profile wedge, one red lip, one amber eye
    piece(7, () => {
      const hc = add(neck, P(95, Math.PI - p.lean - p.head));
      ctx.save(); ctx.translate(hc[0], hc[1]); ctx.rotate(p.lean * 0.6 + p.head);
      plane(ctx, [[-70, -80], [40, -96], [70, -40], [72, 20], [10, 30], [-80, 40]], mono || LOOK.hair, { lw });
      plane(ctx, [[10, -30], [64, -38], [78, 10], [96, 26], [74, 40], [76, 70], [20, 80], [6, 30]], mono || pal.L, { lw });
      if (!mono) { plane(ctx, [[30, -6], [58, 2], [30, 10]], '#F6EFE2', { lw: 2 }); circle(ctx, 50, 2, 4, LOOK.iris); plane(ctx, [[68, 48], [82, 50], [70, 58]], pal.R, { lw: 0 }); }
      plane(ctx, [[-60, -96], [56, -100], [50, -44], [0, -36]], cK, { lw: 0 });
      ctx.restore();
      return hc;
    });
    ctx.restore();
    const Wt = (q) => [x + q[0] * s * (o.dir || 1), y + q[1] * s];
    return { head: Wt(add(neck, P(95, Math.PI - p.lean - p.head))), wF: Wt(aF[2]), wB: Wt(aB[2]), hip: Wt(hip) };
  }

  // ---------------- HIM: the wedge ----------------
  // o: { s, arm (angle), dagger, eye glow, broken }
  function wedge(ctx, x, y, t, o = {}) {
    const s = o.s || 1;
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s); ctx.rotate(o.rot || 0);
    const br = o.broken || 0;
    plane(ctx, [[-160 - br * 40, 0], [160, 0], [10 + br * 60, -720 + br * 200]], INK, { lw: 3 });
    plane(ctx, [[10 + br * 60, -720 + br * 200], [160, 0], [90, 0], [40, -520 + br * 160]], '#3A2C2A', { lw: 0, alpha: 0.9 });
    const ey = -560 + br * 180;
    circle(ctx, 30, ey, 26, `rgba(200,38,30,${o.eye ?? 1})`, { lw: 3 });
    if (o.arm !== undefined) {
      const sh = [60, -480 + br * 150], hand = add(sh, P(380, o.arm));
      seg(ctx, sh, hand, 22, 10, INK, 2);
      if (o.dagger) { const d = add(hand, P(240, o.arm)); plane(ctx, [add(hand, P(14, o.arm + 1.57)), d, add(hand, P(14, o.arm - 1.57))], '#ECE7DC', { lw: 3 }); }
      if (o.stick) { line(ctx, hand, add(hand, P(160, o.arm + 0.6)), 8, '#7A4A22'); }
    }
    ctx.restore();
  }
  // a hand of planes reaching from (fx,fy) to (hx,hy)
  function claw(ctx, fx, fy, hx, hy, col, grip = 0.4) {
    seg(ctx, [fx, fy], [hx, hy], 38, 26, INK, 3);
    const a = Math.atan2(hy - fy, hx - fx);
    ctx.save(); ctx.translate(hx, hy); ctx.rotate(a);
    plane(ctx, [[-10, -38], [56, -34], [64, 34], [-10, 38]], col, { lw: 3, tex: { kind: 'hatch', angle: 0.6, gap: 10, color: 'rgba(20,16,18,0.2)' } });
    for (let k = 0; k < 4; k++) { const y0 = -30 + k * 20, ang = (k - 1.5) * 0.12 + grip * (k < 2 ? -0.5 : 0.5) * 0.6; plane(ctx, [[56, y0 - 7], [56 + Math.cos(ang) * 110, y0 + Math.sin(ang) * 110], [56, y0 + 7]], col, { lw: 2.5 }); }
    plane(ctx, [[10, -36], [60, -90], [30, -30]], col, { lw: 2.5 });
    ctx.restore();
  }
  function redLines(ctx, from, pts, lw = 3) { ctx.strokeStyle = RED; ctx.lineWidth = lw; for (let i = 0; i < pts.length; i++) { const f = from[i % from.length]; ctx.beginPath(); ctx.moveTo(f[0], f[1]); ctx.lineTo(pts[i][0], pts[i][1]); ctx.stroke(); } }
  function flash(ctx, a, col = '255,248,236') { if (a > 0.01) { ctx.fillStyle = `rgba(${col},${a})`; ctx.fillRect(0, 0, W, H); } }

  // ---------------- lyrics: a Constructivist paper strip ----------------
  function lyrics(ctx, t) {
    for (const sb of S.subtitles) {
      if (t < sb.t - 0.2 || t > sb.end + 0.2) continue;
      const a = Math.min(sm(clamp((t - sb.t + 0.2) / 0.45)), sm(clamp((sb.end + 0.2 - t) / 0.4)));
      if (a <= 0) continue;
      const big = sb.key === 'c';
      ctx.save(); ctx.globalAlpha = a;
      ctx.font = `500 ${big ? 54 : 48}px Vazir`; ctx.direction = 'rtl'; const w1 = ctx.measureText(sb.fa).width;
      ctx.font = 'italic 500 30px Cormorant'; ctx.direction = 'ltr'; const w2 = ctx.measureText(sb.en).width;
      const w = Math.max(w1, w2) + 90, slide = (1 - a) * 40;
      ctx.translate(W / 2 + slide, H - 104); ctx.rotate(-0.014);
      plane(ctx, [[-w / 2, -64], [w / 2, -64], [w / 2, 56], [-w / 2, 56]], CREAM, { lw: 3 });
      plane(ctx, [[-w / 2, -64], [-w / 2 + 18, -64], [-w / 2 + 18, 56], [-w / 2, 56]], big ? RED : INK, { lw: 0 });
      ctx.fillStyle = INK; ctx.textAlign = 'center';
      ctx.direction = 'rtl'; ctx.font = `500 ${big ? 54 : 48}px Vazir`; ctx.fillText(sb.fa, 6, -8);
      ctx.direction = 'ltr'; ctx.font = 'italic 500 30px Cormorant'; ctx.fillStyle = '#3A302A'; ctx.fillText(sb.en, 6, 36);
      ctx.restore();
    }
  }

  function sand(ctx, t, n, col = 'rgba(120,70,30,0.55)') { ctx.fillStyle = col; for (let k = 0; k < n; k++) { const x = (h(k, 1) * W * 1.2 + t * (200 + 300 * h(k, 2))) % (W * 1.2) - W * 0.1, y = h(k, 3) * H; ctx.fillRect(x, y, 3 + 9 * h(k, 4), 2); } }
  function stormLines(ctx, t, n, a = 0.6) { ctx.strokeStyle = `rgba(228,235,230,${a})`; ctx.lineWidth = 2; for (let k = 0; k < n; k++) { const sp = 1500 + 900 * h(k, 2), x = (h(k, 1) * (W + 600) + t * 400) % (W + 600) - 300, y = ((h(k, 3) * (H + 600) + t * sp) % (H + 600)) - 300, L = 60 + 140 * h(k, 4); ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x - L * 0.45, y - L); ctx.stroke(); } }
  // a siege: the face under pressure, claw hands landing one per beat from t0 (8 hands)
  const HANDS = [[-140, 60, 620, 230], [2060, 40, 1300, 220], [-160, 640, 600, 520], [2080, 660, 1320, 520], [-140, 1180, 520, 880], [2060, 1200, 1400, 880], [960, -300, 960, 90], [-200, 380, 560, 380]];
  function hands(ctx, t, t0, o = {}) {
    const bi0 = lastBeat(t0);
    HANDS.forEach(([fx, fy, hx, hy], i) => {
      const ta = BEATS[bi0 + i] ?? t0; const a = E.outBack(clamp((t - ta) / 0.2), 1.6) * (1 - (o.dissolve || 0));
      if (a <= 0) return;
      claw(ctx, fx, fy, lerp(fx, hx, a), lerp(fy, hy, a), i % 2 ? (o.c1 || '#D25A3E') : (o.c2 || '#EAD9BC'), 0.4 + 0.2 * Math.sin(t * 6 + i));
    });
  }
  globalThis.CUBE = { PAL, INK, RED, CREAM, LOOK, setLook, h, sm, prog, lastBeat, sinceBeat, kick, B,
    pathOf, plane, texture, line, circle, facets, disc, burst, almond, eyeFront, eyeProfile, face, figure, seg, wedge, claw, hands, HANDS,
    redLines, flash, lyrics, sand, stormLines };
})();
