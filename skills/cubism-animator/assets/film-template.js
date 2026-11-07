// FILM — shots for this piece. Draws with the CUBE library (cubism.js). Every frame is a pure function of t.
(function () {
  const U = globalThis.U, G = globalThis.G, Studio = globalThis.Studio, S = globalThis.SCORE;
  const { clamp, lerp } = U; const E = U.ease; const W = G.W, H = G.H;
  const { PAL, INK, RED, CREAM, h, sm, prog, lastBeat, sinceBeat, kick, B, plane, line, circle, facets, disc, burst, face, figure, wedge, claw, hands, redLines, flash, lyrics, sand, stormLines } = globalThis.CUBE;
  // globalThis.CUBE.setLook({ hair: '#141012', iris: '#C98A2B', lips: '#C8261E', tee: '#F1E6CF' }); // from the reference photos

  const shots = [];
  const shot = (b0, b1, fn, tr = 'cut', d = 0) => shots.push({ t0: B(b0), t1: B(b1), fn, tr, d });
  const shotT = (t0, t1, fn, tr = 'cut', d = 0) => shots.push({ t0, t1, fn, tr, d });

  // ---- EXAMPLE SHOTS (replace with the treatment). Arc: whole -> splitting -> shattered -> rupture -> reassembled ----
  shotT(0, B(4), (ctx, t, u) => {                       // the point and the line
    ctx.fillStyle = CREAM; ctx.fillRect(0, 0, W, H);
    circle(ctx, W * 0.62, H * 0.45, 30 + 180 * E.outBack(prog(t, 0.5, 1.5), 1.4), RED, { lw: 4 });
    line(ctx, [W * 0.1, H * 0.8], [lerp(W * 0.1, W * 0.9, E.inOutCubic(prog(t, 1, 3))), lerp(H * 0.8, H * 0.2, E.inOutCubic(prog(t, 1, 3)))], 10);
  });
  shot(4, 8, (ctx, t, u) => {                           // emptiness: planes drift apart
    facets(ctx, t, 'desert', 11, { lines: 2 });
    face(ctx, W / 2, 470, t, { pal: 'desert', s: 0.85, split: lerp(0.05, 0.5, sm(u)), eyes: 0.6 });
  }, 'fade', 0.8);
  shot(8, 12, (ctx, t, u) => {                          // pressure: shatter on every beat, hands, many eyes
    facets(ctx, t, 'blood', 12, { lines: 3 });
    face(ctx, W / 2, 470, t, { pal: 'blood', s: 0.82, split: 0.18 + 0.2 * kick(t, 5), snap: 1, eyes: 1.15, mouth: 0.8, tears: 0.8, extraEyes: 1 });
    hands(ctx, t, B(8));
  }, 'flash');
  shot(12, 16, (ctx, t, u) => {                         // rupture: Kandinsky burst on the downbeat
    facets(ctx, t, 'storm', 13, { lines: 6 });
    burst(ctx, t, B(12), W / 2, H / 2, 90, [RED, INK, '#E3C36A', '#C9D6D2', CREAM], 7, 4);
    figure(ctx, W / 2, 980, t, { pal: 'storm', pose: 'run', phase: t * 1.5, s: 0.7 });
    stormLines(ctx, t, 140, 0.5); flash(ctx, Math.exp(-(t - B(12)) * 5) * 0.9);
  });
  shot(16, 20, (ctx, t, u) => {                         // peace: two halves become one face
    ctx.fillStyle = '#2A0E1E'; ctx.fillRect(0, 0, W, H);
    const m = E.inOutCubic(prog(t, B(16), B(18, 2)));
    face(ctx, W / 2 - lerp(520, 0, m), 470, t, { pal: 'night', s: 0.85, half: 'dark', collage: false });
    face(ctx, W / 2 + lerp(520, 0, m), 470, t, { pal: 'ember', s: 0.85, half: 'light', collage: false });
  }, 'fade', 0.6);

  // ---------------- compositor ----------------
  shots.sort((a, b) => a.t0 - b.t0);
  let off = null;
  function drawShot(ctx, sh, t) { ctx.save(); sh.fn(ctx, t, clamp((t - sh.t0) / (sh.t1 - sh.t0))); ctx.restore(); }
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
