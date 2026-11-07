// TAN BE TAN — the cubist cut. A woman as planes, lines and colour; the antagonist as a black wedge;
// the war drum as a Delaunay disc. Same story arc and beat-lock as the narrative film, told as painting.
(function () {
  const U = globalThis.U, G = globalThis.G, Studio = globalThis.Studio, S = globalThis.SCORE;
  const { T } = S;
  const { clamp, lerp } = U;
  const E = U.ease;
  const W = G.W, H = G.H;
  const BEATS = S.beats;
  const INK = '#141012', RED = '#C8261E', CREAM = '#F1E6CF';
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
    circle(ctx, cx, cy, 19 * s, '#C98A2B'); circle(ctx, cx, cy, 8 * s, INK); plane(ctx, [[cx - 19 * s, cy - 19 * s], [cx + 19 * s, cy - 19 * s], [cx, cy]], 'rgba(20,16,18,0.25)', { lw: 0 });
    ctx.restore();
    line(ctx, [cx + 50 * s, cy - 2 * s], [cx + 72 * s, cy - 18 * s], 5 * s);
  }
  function eyeProfile(ctx, cx, cy, s, open) {
    if (open < 0.08) { line(ctx, [cx - 32 * s, cy], [cx + 30 * s, cy + 2 * s], 5 * s); return; }
    const pts = [[cx - 34 * s, cy - 18 * s * open], [cx + 32 * s, cy], [cx - 34 * s, cy + 14 * s * open]];
    plane(ctx, pts, '#F6EFE2', { lw: 4 * s });
    circle(ctx, cx + 10 * s, cy - 1, 9 * s * Math.min(1, open), '#C98A2B'); circle(ctx, cx + 12 * s, cy - 1, 4 * s, INK);
  }
  // o: { s, split 0..1, snap 0..1, palette, eyes 0..1, mouth 0..1, tears 0..1, extraEyes 0..1, half: 'both'|'dark'|'light', rot, seed, smile }
  function face(ctx, x, y, t, o = {}) {
    const pal = PAL[o.pal || 'desert'], s = o.s || 1, split = o.split || 0, seed = o.seed || 3;
    const bi = lastBeat(t), snap = (o.snap || 0) * (0.35 + 0.65 * kick(t, 5));
    const role = (r) => (r === 'K' ? INK : pal[r]);
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
      plane(ctx, [[-44, 140 - sl], [-8, 124], [8, 128], [46, 138 - sl], [6, 148]], pal.R, { lw: 3 });
      if (m > 4) plane(ctx, [[-36, 148], [36, 148], [24, 150 + m], [-24, 150 + m]], INK, { lw: 0 });
      plane(ctx, [[-36, 152 + m], [38, 150 + m], [4, 182 + m]], pal.R, { lw: 3, tex: { kind: 'grad' } });
    });
    inGroup(6, () => plane(ctx, FRINGE.pts, INK, { lw: 3.5 }));
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
      plane(ctx, [[-70, -80], [40, -96], [70, -40], [72, 20], [10, 30], [-80, 40]], cK, { lw });
      plane(ctx, [[10, -30], [64, -38], [78, 10], [96, 26], [74, 40], [76, 70], [20, 80], [6, 30]], mono || pal.L, { lw });
      if (!mono) { plane(ctx, [[30, -6], [58, 2], [30, 10]], '#F6EFE2', { lw: 2 }); circle(ctx, 50, 2, 4, '#C98A2B'); plane(ctx, [[68, 48], [82, 50], [70, 58]], pal.R, { lw: 0 }); }
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

  // =====================================================================
  // SHOTS
  // =====================================================================
  const shots = [];
  const shot = (b0, b1, fn, tr = 'cut', d = 0) => shots.push({ t0: B(b0), t1: B(b1), fn, tr, d });
  const shotT = (t0, t1, fn, tr = 'cut', d = 0) => shots.push({ t0, t1, fn, tr, d });

  // ---- 0-4: the point and the line (title) ----
  shotT(0, B(4), (ctx, t) => {
    ctx.fillStyle = CREAM; ctx.fillRect(0, 0, W, H);
    const t0 = B(0);
    const r = 14 + 210 * E.outBack(prog(t, t0, t0 + 0.8), 1.4);
    if (t > t0 - 1.2) circle(ctx, W / 2 + 230, H / 2 - 40, t < t0 ? 14 : r, RED, { lw: 4 });
    const ln = E.inOutCubic(prog(t, t0 + 0.6, t0 + 2.2));
    if (ln > 0) line(ctx, [W * 0.08, H * 0.82], [lerp(W * 0.08, W * 0.92, ln), lerp(H * 0.82, H * 0.18, ln)], 10);
    plane(ctx, [[W * 0.18, H * 0.25], [W * 0.18 + 26, H * 0.25], [W * 0.18 + 26, H * 0.25 + 400 * prog(t, t0 + 1, t0 + 2)], [W * 0.18, H * 0.25 + 400 * prog(t, t0 + 1, t0 + 2)]], INK, { lw: 0 });
    const ta = sm(prog(t, t0 + 1.4, t0 + 2.8)) * (1 - sm(prog(t, B(3, 2), B(4))));
    ctx.save(); ctx.globalAlpha = ta; ctx.fillStyle = INK; ctx.textAlign = 'left';
    ctx.direction = 'rtl'; ctx.font = '700 190px Vazir'; ctx.fillText('تن به تن', W * 0.62, H * 0.56);
    ctx.direction = 'ltr'; ctx.font = 'italic 500 44px Cormorant'; ctx.fillText('tan be tan — body to body', W * 0.24, H * 0.66);
    ctx.font = '500 30px Vazir'; ctx.fillText('ROSHA', W * 0.24, H * 0.72);
    ctx.restore();
    if (t >= B(3, 2)) flash(ctx, sm(prog(t, B(3, 2), B(4))) * 0.0);
  });
  // ---- 4-10: night. folded inward, the lit rectangle ----
  shot(4, 10, (ctx, t, u) => {
    facets(ctx, t, 'night', 21, { lines: 3 });
    const glow = 0.6 + 0.4 * kick(t, 2);
    plane(ctx, [[1500, 180], [1640, 180], [1640, 760], [1500, 760]], `rgba(242,214,150,${glow})`, { lw: 4 });
    plane(ctx, [[1500, 760], [1640, 760], [1900, 1100], [1240, 1100]], `rgba(242,214,150,${0.25 * glow})`, { lw: 0 });
    const look = sm(prog(t, B(8), B(9)));
    face(ctx, 760, 470, t, { pal: 'night', s: 0.92, split: lerp(0.12, 0.05, u), eyes: lerp(0.05, 0.9, look), rot: lerp(-0.12, 0.02, look) });
  }, 'fade', 1.6);
  // ---- 10-18: the pulse behind the door; the walk into the light ----
  shot(10, 14, (ctx, t, u) => {
    facets(ctx, t, 'night', 22, { lines: 5 });
    const k = kick(t, 6);
    plane(ctx, [[1420, 140], [1660, 140], [1660, 800], [1420, 800]], `rgb(${200 + 55 * k},${40 + 30 * (1 - k)},${30})`, { lw: 5 });
    disc(ctx, 1540, 470, 80 + 40 * k, 4, [RED, INK, '#E8B04A', CREAM], t * 0.5);
    face(ctx, 700, 470, t, { pal: 'night', s: 0.9, split: 0.08, snap: 0.25, eyes: 1.1, mouth: 0.25 });
  });
  shot(14, 17, (ctx, t, u) => {
    facets(ctx, t, 'night', 23, { lines: 2 });
    plane(ctx, [[1480, 160], [1700, 160], [1700, 860], [1480, 860]], RED, { lw: 5 });
    figure(ctx, lerp(300, 1300, u), 920, t, { pal: 'night', pose: 'walk', phase: (t - B(14)) * 0.9, s: 0.95 });
  });
  shot(17, 18, (ctx, t, u) => {
    ctx.fillStyle = '#1B1F3A'; ctx.fillRect(0, 0, W, H);
    const o = E.inCubic(u), x0 = lerp(860, -40, o), x1 = lerp(1060, W + 40, o), y0 = lerp(200, -40, o), y1 = lerp(880, H + 40, o);
    plane(ctx, [[x0, y0], [x1, y0], [x1, y1], [x0, y1]], CREAM, { lw: 5 });
    figure(ctx, 960, 900, t, { pal: 'night', pose: 'stand', s: 0.9, mono: INK });
  });

  // ---- 18-34: the desert of no-love: the planes drift apart, sand fills the gaps ----
  function sand(ctx, t, n, col = 'rgba(120,70,30,0.55)') { ctx.fillStyle = col; for (let k = 0; k < n; k++) { const x = (h(k, 1) * W * 1.2 + t * (200 + 300 * h(k, 2))) % (W * 1.2) - W * 0.1, y = h(k, 3) * H; ctx.fillRect(x, y, 3 + 9 * h(k, 4), 2); } }
  shot(18, 22, (ctx, t, u) => {
    facets(ctx, t, 'desert', 31, { ny: 3, lines: 2 });
    disc(ctx, W * 0.7, H * 0.32, 190, 6, ['#F4E8CF', '#E8C98F', '#D9B580', '#F0D9A8'], t * 0.05);
    line(ctx, [0, H * 0.7], [W, H * 0.66], 6);
    figure(ctx, lerp(1450, 500, u), H * 0.68, t, { pal: 'desert', pose: 'walk', phase: (t - B(18)) * 0.8, s: 0.32, dir: -1 });
    sand(ctx, t, 120);
    flash(ctx, 1 - sm(prog(t, B(18), B(18) + 1.2)));
  });
  shot(22, 30, (ctx, t, u) => {
    facets(ctx, t, 'desert', 32, { lines: 3 });
    const sp = lerp(0.1, 0.55, sm(u));
    face(ctx, W / 2, 460, t, { pal: 'desert', s: 0.85, split: sp, eyes: lerp(0.8, 0.25, u), rot: Math.sin(t * 0.3) * 0.04 });
    // sand pours out through the gaps
    for (let k = 0; k < 160; k++) { const life = (t * 0.5 + h(k, 7)) % 1, x = W / 2 + (h(k, 8) - 0.5) * 500 * sp * 2, y = 400 + life * 700; ctx.fillStyle = `rgba(150,90,40,${0.8 * (1 - life)})`; ctx.fillRect(x + life * 80, y, 4, 4); }
    sand(ctx, t, 80);
  }, 'fade', 0.8);
  shot(30, 34, (ctx, t, u) => {
    facets(ctx, t, 'desert', 33, { ny: 3, lines: 0, tex: false, alpha: 0.85 });
    // a field of black verticals: spears as pure lines
    for (let k = 0; k < 40; k++) { const x = h(k, 1) * W, d = h(k, 2), y = lerp(H * 0.6, H * 1.02, d), L = lerp(80, 360, d), a = (h(k, 3) - 0.5) * 0.5; line(ctx, [x, y], [x + Math.sin(a) * L, y - Math.cos(a) * L], lerp(3, 9, d)); if (h(k, 4) > 0.6) plane(ctx, [[x + Math.sin(a) * L, y - Math.cos(a) * L], [x + Math.sin(a) * L + 60 * d, y - Math.cos(a) * L + 14], [x + Math.sin(a) * L, y - Math.cos(a) * L + 30 * d]], RED, { lw: 2 }); }
    figure(ctx, W / 2, H * 0.84, t, { pal: 'desert', pose: 'kneel', s: lerp(0.62, 0.42, u) });
  }, 'fade', 0.8);

  // ---- 34-50: the wedge arrives; the plans are drawn ----
  shot(34, 38, (ctx, t, u) => {
    facets(ctx, t, 'blood', 41, { lines: 2, alpha: 0.75 });
    const enter = E.outCubic(prog(t, B(34), B(36)));
    wedge(ctx, lerp(-400, 640, enter), 1000, t, { s: 1.15, eye: sm(prog(t, B(36), B(37))) });
    // a red wedge cuts the field (Beat the Whites with the Red Wedge)
    const c = E.inOutCubic(prog(t, B(36), B(38)));
    plane(ctx, [[-200, 300], [lerp(-200, 1500, c), 560], [-200, 820]], RED, { lw: 4 });
    face(ctx, 1480, 470, t, { pal: 'desert', s: 0.62, split: 0.3, eyes: 1.1, rot: 0.06 });
  });
  shot(38, 42, (ctx, t, u) => {
    ctx.fillStyle = CREAM; ctx.fillRect(0, 0, W, H);
    plane(ctx, [[0, 0], [W / 2, 0], [W / 2, H], [0, H]], '#E5D8BE', { lw: 0, tex: { kind: 'dots', gap: 14, color: 'rgba(20,16,18,0.1)' } });
    plane(ctx, [[W / 2, 0], [W, 0], [W, H], [W / 2, H]], INK, { lw: 0 });
    face(ctx, 620, 500, t, { pal: 'desert', s: 0.95, split: 0.08, eyes: 1, half: 'light', rot: 0.04 });
    wedge(ctx, 1380, 1080, t, { s: 1.1, arm: -1.57 - 0.05, dagger: true, eye: 1 });
    const gx = W / 2, gl = kick(t, 6);
    plane(ctx, [[gx - 16, 900], [gx, lerp(900, 160, E.outCubic(prog(t, B(38), B(39))))], [gx + 16, 900]], `rgb(${236},${231 - 40 * gl},${220 - 60 * gl})`, { lw: 3 });
  });
  shot(42, 46, (ctx, t, u) => {
    facets(ctx, t, 'blood', 43, { lines: 1, alpha: 0.7 });
    // the puppet: her figure hangs from a black bar held by the wedge
    const bar = [[W / 2 - 330, 110 + 40 * Math.sin(t * 2)], [W / 2 + 330, 110 - 40 * Math.sin(t * 2)]];
    line(ctx, bar[0], bar[1], 22);
    wedge(ctx, W / 2 + 560, 1080, t, { s: 1.0, arm: -2.6, eye: 1 });
    const bi = lastBeat(t);
    const f = figure(ctx, W / 2 - 40, 960 - 50 * kick(t, 6), t, { pal: 'blood', pose: 'custom', j: { hip: -392, lean: (h(bi, 1) - 0.5) * 0.4, legF: [0.2 + h(bi, 2) * 0.5, -0.2], legB: [-0.2, -0.4 * h(bi, 3)], armF: [1.4 + h(bi, 4) * 1.2, 1.8 + h(bi, 5)], armB: [-1.4 - h(bi, 6), -1.8 - h(bi, 7)], head: 0.4 }, s: 0.8 });
    redLines(ctx, bar, [f.wF, f.wB, f.head, f.hip], 3);
  }, 'fade', 0.5);
  shot(46, 50, (ctx, t, u) => {
    ctx.fillStyle = CREAM; ctx.fillRect(0, 0, W, H);
    ctx.strokeStyle = 'rgba(20,16,18,0.18)'; ctx.lineWidth = 1.5; for (let x = 0; x < W; x += 80) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); } for (let y = 0; y < H; y += 80) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
    const n = lastBeat(t) - lastBeat(B(46)) + 1, tgt = [W / 2, 470];
    for (let k = 0; k < Math.min(16, n); k++) { const a = h(k, 5) * Math.PI * 2, d = 900; const p = clamp((t - BEATS[lastBeat(B(46)) + k]) / 0.3); line(ctx, [tgt[0] + Math.cos(a) * d, tgt[1] + Math.sin(a) * d], [lerp(tgt[0] + Math.cos(a) * d, tgt[0] + Math.cos(a) * 150, p), lerp(tgt[1] + Math.sin(a) * d, tgt[1] + Math.sin(a) * 150, p)], 5, RED); }
    face(ctx, tgt[0], tgt[1], t, { pal: 'desert', s: 0.6, split: 0.05 + 0.02 * n, eyes: 1.1, collage: false });
    flash(ctx, sm(prog(t, B(49, 2), B(50) - 0.02)) * 0.95, '200,38,30');
  });

  // ---- 50-66: the siege — the face shatters on every beat; hands of planes; many eyes ----
  const HANDS = [[-140, 60, 620, 230], [2060, 40, 1300, 220], [-160, 640, 600, 520], [2080, 660, 1320, 520], [-140, 1180, 520, 880], [2060, 1200, 1400, 880], [960, -300, 960, 90], [-200, 380, 560, 380]];
  function siege(ctx, t, t0, o = {}) {
    facets(ctx, t, 'blood', 51 + (o.seedShift || 0), { lines: 3 });
    const bi0 = lastBeat(t0);
    face(ctx, W / 2, 470, t, { pal: 'blood', s: 0.82, split: o.split ?? (0.18 + 0.2 * kick(t, 5)), snap: o.snap ?? 1, eyes: o.eyes ?? 1.15, mouth: o.mouth ?? 0.8, tears: o.tears ?? 0.8, extraEyes: o.extra ?? 1 });
    HANDS.forEach(([fx, fy, hx, hy], i) => {
      const ta = BEATS[bi0 + i] ?? t0; let a = E.outBack(clamp((t - ta) / 0.2), 1.6) * (1 - (o.dissolve || 0));
      if (a <= 0) return;
      claw(ctx, fx, fy, lerp(fx, hx, a), lerp(fy, hy, a), i % 2 ? '#D25A3E' : '#EAD9BC', 0.4 + 0.2 * Math.sin(t * 6 + i));
    });
  }
  shot(50, 54, (ctx, t) => siege(ctx, t, B(50)), 'flash');
  shot(54, 58, (ctx, t, u) => {
    facets(ctx, t, 'blood', 55, { lines: 0 });
    disc(ctx, W / 2, 430, 360, 6, ['#EAD9BC', '#E8B04A', '#D25A3E', CREAM], t * 0.2);
    const bi = lastBeat(t), jk = E.outCubic(clamp(sinceBeat(t) / 0.15));
    const pz = (i) => ({ armF: [1.0 + h(i, 1) * 1.8, 1.3 + h(i, 2) * 1.6], armB: [-1.0 - h(i, 3) * 1.8, -1.3 - h(i, 4) * 1.4], legF: [0.1 + h(i, 5) * 0.7, -0.1 - h(i, 6) * 0.6], legB: [-0.1 - h(i, 7) * 0.4, -0.3], lean: (h(i, 8) - 0.5) * 0.5, head: 0.3 + h(i, 9) * 0.6 });
    const p0 = pz(bi - 1), p1 = pz(bi), j = { hip: -392 };
    for (const k in p1) j[k] = Array.isArray(p1[k]) ? p1[k].map((v, q) => lerp(p0[k][q], v, jk)) : lerp(p0[k], p1[k], jk);
    const f = figure(ctx, W / 2, 1000 - 60 * kick(t, 6), t, { pal: 'blood', pose: 'custom', j, s: 0.9, split: 0.15 * kick(t, 6) });
    const bar = [[W / 2 - 300, 40], [W / 2 + 300, 40]]; line(ctx, bar[0], bar[1], 24);
    redLines(ctx, [bar[0], bar[1], [W / 2, 40]], [f.wB, f.wF, f.head, f.hip], 3.5);
  });
  shot(58, 62, (ctx, t, u) => {
    // the gaze: one huge frontal eye, the wedge reflected in its iris, framed by shards
    facets(ctx, t, 'blood', 59, { lines: 4, nx: 8, ny: 5 });
    const cx = W / 2, cy = H / 2 - 40, s = lerp(5.6, 6.2, u);
    eyeFront(ctx, cx, cy, s, 1, PAL.blood);
    plane(ctx, [[cx - 10, cy + 40], [cx + 18, cy - 70], [cx + 46, cy + 40]], INK, { lw: 0 });
    circle(ctx, cx + 18, cy - 40, 6, RED);
    if (u > 0.1) plane(ctx, [[cx - 210, cy + 150], [cx - 196, cy + 150], [cx - 190, cy + 150 + 400 * u], [cx - 206, cy + 150 + 400 * u]], '#3B6FA8', { lw: 3 });
  });
  const DUEL = [[1.6, 1.6, 0.5], [2.6, 2.8, -0.45], [0.4, 0.6, 0.2], [1.9, 2.3, 0.4], [1.5, 1.5, 0.15], [2.3, 2.6, -0.3]];
  function duel(ctx, t, t0, o = {}) {
    facets(ctx, t, 'blood', 63, { lines: 2 });
    disc(ctx, W / 2, H * 0.5, 300, 5, [RED, INK, '#E8B04A', CREAM], t * 0.3, { alpha: 0.9 });
    const i = lastBeat(t) - lastBeat(t0), d = DUEL[((i % 6) + 6) % 6], orbit = Math.sin((t - t0) * 0.8) * 120;
    const pinned = o.disarm !== undefined && t >= o.disarm;
    wedge(ctx, W / 2 + 230 + orbit, 1000, t, { s: 0.8, arm: pinned ? -0.2 : -1.6 - (i % 3) * 0.4, dagger: !pinned, eye: 1, rot: pinned ? 0.12 : 0 });
    figure(ctx, W / 2 - 200 + orbit + (i % 2) * 60, 1000, t, { pal: 'blood', pose: 'custom', j: { hip: -380, lean: d[2], armF: [d[0], d[1]], armB: [d[0] - 0.3, d[1] - 0.2], legF: [0.6, 0.1], legB: [-0.5, -0.4], head: 0 }, s: 0.75 });
    flash(ctx, Math.exp(-sinceBeat(t) * 14) * 0.45, '255,90,60');
    if (o.disarm !== undefined) { const u2 = clamp((t - o.disarm) / 0.9); if (u2 > 0) { ctx.save(); ctx.translate(lerp(W / 2 + 300, W / 2 + 720, u2), lerp(500, 980, u2) - 300 * Math.sin(Math.PI * u2)); ctx.rotate(u2 < 1 ? u2 * 14 : 2.9); plane(ctx, [[-12, 0], [0, -220], [12, 0]], '#ECE7DC', { lw: 3 }); ctx.restore(); } }
  }
  shot(62, 66, (ctx, t) => duel(ctx, t, B(62)));

  // ---- 66-79: rupture. the lines snap; a Kandinsky explosion; storm of diagonals ----
  function stormLines(ctx, t, n, a = 0.6) { ctx.strokeStyle = `rgba(228,235,230,${a})`; ctx.lineWidth = 2; for (let k = 0; k < n; k++) { const sp = 1500 + 900 * h(k, 2), x = (h(k, 1) * (W + 600) + t * 400) % (W + 600) - 300, y = ((h(k, 3) * (H + 600) + t * sp) % (H + 600)) - 300, L = 60 + 140 * h(k, 4); ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x - L * 0.45, y - L); ctx.stroke(); } }
  shot(66, 71, (ctx, t, u) => {
    facets(ctx, t, 'storm', 67, { lines: 6 });
    const t0 = B(66);
    burst(ctx, t, t0, W / 2, H / 2, 90, [RED, INK, '#E3C36A', '#C9D6D2', '#3E6E7A', CREAM], 7, 4.5);
    figure(ctx, W / 2, 980, t, { pal: 'storm', pose: t < t0 + 0.4 ? 'open' : 'run', phase: (t - t0) * 1.5, s: 0.7, split: Math.exp(-(t - t0) * 2) * 0.8 });
    for (let k = 0; k < 14; k++) { const a = h(k, 3) * Math.PI * 2, d = (t - t0) * 600 * (0.4 + h(k, 4)); const x = W / 2 + Math.cos(a) * d, y = 400 + Math.sin(a) * d * 0.6 + 300 * (t - t0) ** 2; line(ctx, [x, y], [x + Math.cos(a + 1) * 70, y + Math.sin(a + 1) * 70], 4, RED); }
    stormLines(ctx, t, 140, 0.5);
    flash(ctx, Math.exp(-(t - t0) * 5) * 0.95, '235,245,255');
  });
  shot(71, 75, (ctx, t, u) => {
    facets(ctx, t, 'storm', 72, { lines: 3 });
    face(ctx, W / 2, 480, t, { pal: 'storm', s: 0.86, split: lerp(0.4, 0.22, u), eyes: lerp(0, 0.85, sm(prog(t, B(74), B(75)))), rot: -0.05 + Math.sin(t * 0.5) * 0.03, tears: 0.5 });
    stormLines(ctx, t, 200, 0.55);
  }, 'fade', 0.4);
  shot(75, 79, (ctx, t, u) => {
    facets(ctx, t, 'storm', 76, { lines: 7 });
    const op = sm(prog(t, B(75), B(77)));
    figure(ctx, W / 2, 1000, t, { pal: 'storm', pose: 'custom', j: { hip: -392, lean: -0.05, armF: [lerp(0.1, 2.2, op), lerp(0.1, 2.4, op)], armB: [lerp(-0.1, -2.2, op), lerp(0.0, -2.4, op)], legF: [0.18, 0.05], legB: [-0.18, -0.05], head: -0.35 }, s: 0.8 });
    if (lastBeat(t) % 4 === 0) flash(ctx, 0.3 * kick(t, 6), '235,245,255');
    stormLines(ctx, t, 220, 0.55);
  });

  // ---- 79-83 / 131-137: the drum = a Delaunay disc, one composition per beat ----
  function drumBeat(ctx, t, i, crack = 0) {
    const k = kick(t, 9), pals = ['blood', 'ember', 'night'];
    facets(ctx, t, pals[i % 3], 80 + (i % 5), { lines: 5, drift: 0 });
    const v = i % 3;
    if (v === 0) disc(ctx, W / 2, H / 2, 420 + 50 * k, 7, [RED, INK, '#E8B04A', CREAM, '#3A6EA5'], i * 0.4, { split: crack * 0.6, burst: crack * 0.5 });
    else if (v === 1) { wedge(ctx, W * 0.42, 1060, t, { s: 1.2, arm: sinceBeat(t) < 0.07 ? -0.8 : -2.4, stick: true, eye: 1 }); disc(ctx, W * 0.66, H * 0.62, 230 + 30 * k, 5, [RED, INK, CREAM, '#E8B04A'], i, { split: crack * 0.6 }); }
    else face(ctx, W / 2, 480, t, { pal: 'blood', s: 0.85, split: 0.35 * k + 0.1, eyes: 0, mouth: 0.3, snap: 1 });
    for (let q = 0; q < 3; q++) { const r = (1 - k) * 1100 + q * 90; ctx.strokeStyle = `rgba(20,16,18,${0.6 * k})`; ctx.lineWidth = 8; ctx.beginPath(); ctx.arc(W / 2, H / 2, r, 0, 6.29); ctx.stroke(); }
    flash(ctx, 0.6 * Math.exp(-sinceBeat(t) * 16));
  }
  shot(79, 83, (ctx, t) => drumBeat(ctx, t, lastBeat(t) - lastBeat(B(79))));

  // ---- 83-99: she stops breaking. the planes come home. ----
  shot(83, 87, (ctx, t, u) => {
    facets(ctx, t, 'ember', 84, { lines: 2 });
    const last = S.v3strikes.filter((s0) => s0 <= t).pop() ?? -9, since = t - last;
    wedge(ctx, 360, 1000, t, { s: 0.55, arm: since < 0.1 ? -0.8 : -2.4, stick: true, eye: 1 });
    disc(ctx, 520, 860, 110, 4, [RED, INK, '#F6CF6A', CREAM], t, {});
    for (const s0 of S.v3strikes) { const a = t - s0; if (a < 0 || a > 2) continue; ctx.strokeStyle = `rgba(20,16,18,${0.7 * (1 - a / 2)})`; ctx.lineWidth = 6; ctx.beginPath(); ctx.arc(520, 860, a * 900, -1.2, 1.2); ctx.stroke(); }
    face(ctx, 1350, 480, t, { pal: 'ember', s: 0.7, split: lerp(0.3, 0.06, sm(u)), eyes: 0.9, rot: 0.02 });
  }, 'flash');
  shot(87, 91, (ctx, t, u) => {
    facets(ctx, t, 'ember', 88, { lines: 1 });
    face(ctx, W / 2, 430, t, { pal: 'ember', s: 0.78, split: 0.03, eyes: 0.85 });
    const up = E.outCubic(prog(t, B(88), B(89, 2)));
    for (const sd of [-1, 1]) { ctx.save(); ctx.translate(W / 2 + sd * 360, lerp(1300, 940, up)); ctx.scale(sd, 1); plane(ctx, [[-70, 120], [70, 120], [80, -40], [40, -170], [-10, -180], [-60, -60]], PAL.ember.L, { lw: 3.5, tex: { kind: 'hatch', angle: 0.7, gap: 10, color: 'rgba(20,16,18,0.15)' } }); ctx.restore(); }
  }, 'fade', 0.5);
  shot(91, 95, (ctx, t, u) => {
    // the mirror: the dark half and the light half slide together into one face
    ctx.fillStyle = '#2A0E1E'; ctx.fillRect(0, 0, W, H);
    plane(ctx, [[W / 2, 0], [W, 0], [W, H], [W / 2, H]], '#F6CF6A', { lw: 0, alpha: lerp(0.2, 1, sm(u)) });
    const meet = E.inOutCubic(prog(t, B(91), B(93, 2)));
    face(ctx, W / 2 - lerp(520, 0, meet), 470, t, { pal: 'night', s: 0.85, half: 'dark', eyes: 0.9, collage: false });
    face(ctx, W / 2 + lerp(520, 0, meet), 470, t, { pal: 'ember', s: 0.85, half: 'light', eyes: 0.9, collage: false });
    for (let k = 0; k < 16; k++) { const y = ((t - B(91)) * (100 + 80 * h(k, 2)) + h(k, 1) * 600) % (H + 200) - 100, x = h(k, 3) * W; line(ctx, [x, y], [x + 20, y + 80], 3, `rgba(200,38,30,${1 - meet * 0.8})`); }
    flash(ctx, t > B(94) ? 0.6 * Math.exp(-(t - B(94)) * 3) : 0);
  }, 'fade', 0.6);
  shot(95, 99, (ctx, t, u) => {
    facets(ctx, t, 'ember', 96, { lines: 0, alpha: 0.6 });
    // fire as triangles that bend away from her
    for (let k = 0; k < 30; k++) { const x = (k / 29) * W, hg = 300 + 280 * Math.abs(U.noise1(t * 1.3 + k, 4)), bend = (x < W / 2 ? -1 : 1) * 200 * clamp(1 - Math.abs(x - W / 2) / 700); plane(ctx, [[x - 60, H + 10], [x + bend + 10 * Math.sin(t * 7 + k), H - hg], [x + 60, H + 10]], k % 3 ? '#E06A2A' : (k % 2 ? '#F2A43A' : RED), { lw: 2.5, alpha: 0.9 }); }
    face(ctx, W / 2, 450, t, { pal: 'ember', s: 0.82, split: 0, eyes: lerp(0, 0.95, sm(prog(t, B(97), B(98)))) });
    circle(ctx, W / 2, 450, 520, null, { lw: 6, stroke: 'rgba(58,110,165,0.9)' });
  }, 'fade', 0.5);

  // ---- 99-115: the same world, blooming (Orphism) ----
  shot(99, 103, (ctx, t, u) => {
    facets(ctx, t, 'dawn', 100, { ny: 3, lines: 1 });
    line(ctx, [0, H * 0.68], [W, H * 0.64], 5);
    const x = lerp(300, 1600, u);
    for (let k = 0; k < 24; k++) { const fx = 300 + k * 56; if (fx > x - 30) break; const g = clamp((x - fx) / 260); disc(ctx, fx, H * 0.68 - 0.04 * (fx / W) * H - 10, 34 * g, 3, ['#E7B8C2', '#9CCBB0', '#F2D49A', '#B9A5D6'], k); }
    figure(ctx, x, H * 0.66 - 0.04 * (x / W) * H, t, { pal: 'dawn', pose: 'walk', phase: (t - B(99)) * 0.8, s: 0.34 });
  }, 'fade', 1.0);
  shot(103, 111, (ctx, t, u) => {
    facets(ctx, t, 'dawn', 104, { lines: 2 });
    for (let k = 0; k < 7; k++) disc(ctx, h(k, 1) * W, h(k, 2) * H, (50 + 110 * h(k, 3)) * E.outBack(prog(t, B(103) + k * 0.9, B(104) + k * 0.9)), 4, ['#E7B8C2', '#9CCBB0', '#F2D49A', '#B9A5D6', '#7C9BD0'], t * 0.2 + k);
    face(ctx, W / 2, 470, t, { pal: 'dawn', s: 0.86, split: 0, eyes: 0.8, smile: true, rot: Math.sin(t * 0.4) * 0.03 });
    for (let k = 0; k < 10; k++) { const g = E.outBack(prog(t, B(105) + k * 0.6, B(106) + k * 0.6)); const x = 200 + k * 170; plane(ctx, [[x, H], [x + 30, H - 220 * g], [x + 60, H]], '#5FA57A', { lw: 3 }); }
  }, 'fade', 0.7);
  shot(111, 115, (ctx, t, u) => {
    facets(ctx, t, 'dawn', 112, { ny: 3, lines: 0, tex: false, alpha: 0.85 });
    for (let k = 0; k < 40; k++) { const x = h(k, 1) * W, d = h(k, 2), y = lerp(H * 0.6, H * 1.02, d), L = lerp(80, 360, d), a = (h(k, 3) - 0.5) * 0.5, tx = x + Math.sin(a) * L, ty = y - Math.cos(a) * L; line(ctx, [x, y], [tx, ty], lerp(3, 9, d)); const g = clamp((t - B(111) - h(k, 5) * 4) / 1); if (g > 0) disc(ctx, tx, ty, 26 * g * lerp(0.6, 1.2, d), 3, ['#E7B8C2', '#F2D49A', '#9CCBB0'], k); }
    figure(ctx, lerp(700, 1200, u), H * 0.86, t, { pal: 'dawn', pose: 'walk', phase: (t - B(111)) * 0.8, s: 0.42 });
    flash(ctx, sm(prog(t, B(114), B(115))) * 0.85, '200,38,30');
  }, 'fade', 0.6);

  // ---- 115-131: the siege returns and cannot break her ----
  shot(115, 119, (ctx, t, u) => {
    const dis = sm(prog(t, B(117, 1), B(119)));
    siege(ctx, t, B(115), { split: 0.02, snap: 0, eyes: lerp(0, 1, sm(prog(t, B(117), B(117, 2)))), mouth: 0, tears: 0, extra: 0, dissolve: dis, seedShift: 64 });
    if (dis > 0) for (let k = 0; k < 220; k++) { const hd = HANDS[k % 8], x = lerp(hd[2], hd[0], h(k, 1)) + dis * (300 + 700 * h(k, 2)) * (hd[0] < W / 2 ? -1 : 1), y = lerp(hd[3], hd[1], h(k, 1)) - dis * 200 * h(k, 3); const col = ['#E7B8C2', '#9CCBB0', '#F2D49A', '#B9A5D6'][k % 4]; plane(ctx, [[x, y], [x + 14, y + 4], [x + 4, y + 16]], col, { lw: 1.5, alpha: 1 - dis * 0.6 }); }
  }, 'flash');
  shot(119, 123, (ctx, t, u) => {
    facets(ctx, t, 'blood', 120, { lines: 2, alpha: 0.8 });
    const pull = E.inOutCubic(prog(t, B(120), B(122)));
    wedge(ctx, W / 2 + 380, lerp(1000, 1250, pull), t, { s: lerp(1.0, 0.8, pull), arm: -2.6, eye: 1, rot: lerp(0, 0.6, pull) });
    const f = figure(ctx, W / 2 - 260, 1000, t, { pal: 'dawn', pose: 'custom', j: { hip: -392, lean: lerp(0, -0.3, pull), armF: [lerp(2.6, 1.9, pull), lerp(2.6, 1.6, pull)], armB: [lerp(2.4, 1.7, pull), lerp(2.5, 1.5, pull)], legF: [0.35, 0.1], legB: [-0.35, -0.3], head: -0.15 }, s: 0.8 });
    redLines(ctx, [[W / 2 + 380 + 60, lerp(520, 900, pull)]], [f.wF, f.wB], 4);
  });
  shot(123, 127, (ctx, t, u) => {
    facets(ctx, t, 'dawn', 124, { lines: 3, nx: 8, ny: 5 });
    const cx = W / 2, cy = H / 2 - 40, s = lerp(6.2, 5.6, u);
    eyeFront(ctx, cx, cy, s, 1, PAL.dawn);
    plane(ctx, [[cx + 4, cy + 60], [cx + 20, cy - 40], [cx + 36, cy + 60]], '#5FA57A', { lw: 2 });
    circle(ctx, cx + 20, cy - 50, 12, '#E7B8C2', { lw: 2 });
  });
  shot(127, 131, (ctx, t) => duel(ctx, t, B(127), { disarm: B(128) }));
  shot(131, 137, (ctx, t) => {
    const i = lastBeat(t) - lastBeat(B(131)), crack = clamp((t - B(131)) / (B(137) - B(131)));
    if (t >= B(136, 3)) { facets(ctx, t, 'night', 137, { lines: 0 }); disc(ctx, W / 2, H / 2, 470, 7, [RED, INK, '#E8B04A', CREAM, '#3A6EA5'], 0, { split: 1.2, burst: 1 + (t - B(136, 3)) * 2 }); flash(ctx, 0.9 * Math.exp(-(t - B(136, 3)) * 6)); return; }
    drumBeat(ctx, t, i, crack * 0.5);
  });

  // ---- 137-157: the walk to the white rectangle; the face becomes pure colour ----
  shot(137, 141, (ctx, t, u) => {
    facets(ctx, t, 'gold', 138, { ny: 3, lines: 1 });
    line(ctx, [0, H * 0.7], [W, H * 0.68], 5);
    wedge(ctx, 360, H * 0.72, t, { s: 0.3, broken: 1, eye: 0.3 });
    disc(ctx, 470, H * 0.7, 46, 3, [RED, INK, CREAM], 0, { split: 1.2, burst: 0.4 });
    figure(ctx, lerp(1050, 1460, u), lerp(H * 0.7, H * 0.98, u), t, { pal: 'gold', pose: 'walk', phase: (t - B(137)) * 0.8, s: lerp(0.32, 0.7, u) });
  }, 'fade', 1.0);
  shot(141, 145, (ctx, t, u) => {
    facets(ctx, t, 'gold', 142, { lines: 1, drift: 40 });
    face(ctx, W / 2, 470, t, { pal: 'gold', s: 0.86, split: lerp(0, 0.7, sm(u)) * 0.6, eyes: 0.8, smile: true, rot: lerp(0, -0.05, u) });
  }, 'fade', 0.6);
  shot(145, 149, (ctx, t, u) => {
    facets(ctx, t, 'white', 146, { lines: 1, alpha: 0.9 });
    plane(ctx, [[1180, 160], [1460, 160], [1460, 820], [1180, 820]], '#FFFDF6', { lw: 4 });
    line(ctx, [0, 820], [W, 820], 4);
    figure(ctx, lerp(300, 1080, E.outQuad(u)), 820, t, { pal: 'gold', pose: u < 0.96 ? 'walk' : 'stand', phase: (t - B(145)) * 0.8, s: 0.6 });
  }, 'fade', 0.8);
  shot(149, 153, (ctx, t, u) => {
    facets(ctx, t, 'white', 150, { lines: 0, alpha: 0.6 });
    const o = E.inOutCubic(prog(t, B(150), B(152))), x0 = lerp(820, -40, o), x1 = lerp(1100, W + 40, o), y0 = lerp(160, -40, o), y1 = lerp(860, H + 40, o);
    plane(ctx, [[x0, y0], [x1, y0], [x1, y1], [x0, y1]], '#FFFDF6', { lw: 4 });
    const step = E.inOutCubic(prog(t, B(151), B(152, 2)));
    figure(ctx, lerp(760, 960, step), 860, t, { pal: 'gold', pose: step > 0 && step < 1 ? 'walk' : 'stand', phase: (t - B(151)) * 0.8, s: lerp(0.62, 0.4, step), mono: step > 0.6 ? '#E9E1D0' : null });
  });
  shotT(B(153), S.DURATION + 1, (ctx, t) => {
    ctx.fillStyle = '#FBF8F1'; ctx.fillRect(0, 0, W, H);
    const u = prog(t, B(153), B(155));
    circle(ctx, W * 0.72, H * 0.42, 150 * E.outBack(u), RED, { lw: 4 });
    line(ctx, [W * 0.1, H * 0.78], [lerp(W * 0.1, W * 0.9, E.inOutCubic(u)), H * 0.78], 8);
    const ta = sm(prog(t, B(154), B(155))) * (1 - sm(prog(t, S.DURATION - 2.2, S.DURATION - 0.6)));
    ctx.save(); ctx.globalAlpha = ta; ctx.fillStyle = INK; ctx.textAlign = 'left';
    ctx.textAlign = 'right'; ctx.direction = 'rtl'; ctx.font = '700 96px Vazir'; ctx.fillText('من صلح کردم با خودم', W * 0.6, H * 0.44); ctx.textAlign = 'left';
    ctx.direction = 'ltr'; ctx.font = 'italic 500 42px Cormorant'; ctx.fillText('I have made peace with myself', W * 0.14, H * 0.54);
    ctx.font = '500 26px Vazir'; ctx.globalAlpha = ta * 0.75; ctx.fillText('ROSHA  —  TAN BE TAN  ·  تن به تن', W * 0.14, H * 0.6);
    ctx.restore();
  });

  // ---------------- compositor ----------------
  shots.sort((a, b) => a.t0 - b.t0);
  let off = null;
  function drawShot(ctx, sh, t) { ctx.save(); sh.fn(ctx, t, clamp((t - sh.t0) / (sh.t1 - sh.t0))); ctx.restore(); }
  globalThis.CUBIST = { face, figure, wedge, disc, facets, claw, PAL };
  Studio.film({
    async init() {
      await Studio.loadFont('Vazir', 'assets/Vazirmatn-Light.ttf', 300);
      await Studio.loadFont('Vazir', 'assets/Vazirmatn-Medium.ttf', 500);
      await Studio.loadFont('Vazir', 'assets/Vazirmatn-Bold.ttf', 700);
      await Studio.loadFont('Cormorant', 'assets/CormorantItalic.ttf', 500);
      off = G.makeCanvas(W, H);
    },
    draw(ctx, t) {
      let i = 0; for (let k = 0; k < shots.length; k++) if (shots[k].t0 <= t + 1e-6) i = k;
      const sh = shots[i]; drawShot(ctx, sh, t);
      const since = t - sh.t0;
      if (sh.tr === 'fade' && i > 0 && since < sh.d) {
        const oc = off.getContext('2d'); oc.setTransform(1, 0, 0, 1, 0, 0); oc.clearRect(0, 0, W, H);
        drawShot(oc, shots[i - 1], t);
        ctx.save(); ctx.globalAlpha = 1 - sm(since / sh.d); ctx.drawImage(off, 0, 0); ctx.restore();
      } else if (sh.tr === 'flash' && since < 0.3) flash(ctx, 0.85 * (1 - since / 0.3) ** 2);
      lyrics(ctx, t);
    },
    post: { paper: 0.55, vignette: 0.25, grain: 0.06 },
    fadeOut: 1.2,
  });
})();
