// Trailer director for a pen-and-ink game (works as-is with the starter's three levels; copy it and rewrite the shots).
// film_shots.py evaluates this inside the game's own scope (promo build), so GAME, PL, POST, LEVELS... are all here.
// A shot = { name, n (frames at 30 fps), prep() (set the scene once), frame(i) (pose, then draw()) }.
// Rules that keep shots repeatable: seed Math.random in prep, freeze or script the player, never wait on real time.
(() => {
  const FPS = 30, dt = 1 / FPS;
  const ease = t => t * t * (3 - 2 * t), mix = (a, b, t) => a + (b - a) * t, k01 = (i, a, b) => clamp((i - a) / (b - a), 0, 1);
  const PAPER_C = '#E4E0D5', INK_C = '#171511', TITLE = document.title;
  const css = document.createElement('style');
  css.textContent = '#ui,#loading{display:none!important}' +
    '#trText{position:fixed;left:0;right:0;bottom:11%;text-align:center;z-index:999;pointer-events:none;opacity:0;padding:0 9%;font:italic 5.2vh/1.25 "IM Fell English",Georgia,serif;color:' + INK_C + '}' +
    '#trCard{position:fixed;inset:0;z-index:998;display:flex;flex-direction:column;align-items:center;justify-content:center;opacity:0;pointer-events:none;' +
    'background:radial-gradient(ellipse 62% 58% at 50% 50%,rgba(228,224,213,.97) 0%,rgba(228,224,213,.9) 46%,rgba(228,224,213,0) 100%)}' +
    '#trCard h1{font:16.5vh/.9 "IM Fell English SC",Georgia,serif;margin:0 0 .3em;color:' + INK_C + '}' +
    '#trCard .c1{font:italic 4.3vh/1.2 "IM Fell English",Georgia,serif;color:' + INK_C + '}' +
    '#trCard .c2{font:3.3vh/1.5 "Special Elite","Courier New",monospace;color:' + INK_C + ';margin-top:.4em}';
  document.head.appendChild(css);
  const txt = document.createElement('div'); txt.id = 'trText'; document.body.appendChild(txt);
  const card = document.createElement('div'); card.id = 'trCard';
  card.innerHTML = `<h1>${TITLE}</h1><div class="c1">Play free in your browser</div><div class="c2">yourname.itch.io/your-game</div>`; // EDIT the card text
  document.body.appendChild(card);
  const cardEls = [...card.children];
  // a line of text, fading in over 0.4 s from frame a and out by frame b; paper halo so it reads over ink
  function say(s, o) { if (txt._s !== s) { txt.textContent = s; txt._s = s; } txt.style.opacity = (o || 0).toFixed(3); txt.style.textShadow = `0 0 6px ${PAPER_C},0 0 16px ${PAPER_C},0 0 30px ${PAPER_C}`; }
  function beat(i, a, b, s) { const t = i / FPS; say(s, clamp(Math.min((t - a / FPS) / 0.4, (b / FPS - t) / 0.4), 0, 1)); }
  const keepFov = SET.fov;
  function prep(level, seed, o = {}) { // level 0 = the title view
    Math.random = mulberry32(seed);
    SET.fov = o.fov || keepFov;
    if (level === 0) GAME.titleLevel(); else GAME.newRun(level);
    UI.show(null); UI.hud(false); GAME.toast = () => { }; GAME.hint = () => { }; GAME.caught = () => { };
    GAME.fadeT = null; POST.uFade.value = 0; CAM.fov = SET.fov; CAM.updateProjectionMatrix();
    for (const k in IN.keys) IN.keys[k] = false;
    PL.frozen = true; card.style.opacity = 0; say('', 0);
    for (let i = 0; i < (o.warm || 0); i++) GAME.update(dt); // e.g. warm: 30 lets the next level build behind the exit door
  }
  function place(x, y, z, yaw, pitch) { PL.pos.set(x, y, z); PL.vel.set(0, 0, 0); PL.yaw = yaw; PL.pitch = pitch || 0; }
  function draw(o = {}) {
    GAME.update(dt);
    if (o.post) o.post();
    GAME.fadeT = null; POST.uFade.value = o.fade || 0;
    if (o.flash != null) { POST.uFlash.value = o.flash; POST.uFlashTone.value = o.flashTone == null ? 1 : o.flashTone; }
    if (!window.__tr.noRender) GAME.render();
  }
  const quiet = () => { for (const e of GAME.L.ents) e.off = true; };
  const S = [];
  // 1. the title view, a line types itself out
  S.push({ name: 's01-title', n: 90, prep() { prep(0, 11); GAME.titleT = 30; },
    frame(i) { const line = 'Somewhere in the drawing there is a door.'; const k = Math.floor(k01(i, 8, 60) * line.length);
      say(line.slice(0, k), i < 8 ? 0 : clamp((89 - i) / 10, 0, 1)); draw({ fade: clamp(1 - i / 20, 0, 1) }); } });
  // 2. walking into the stair hall
  S.push({ name: 's02-hall', n: 75, prep() { prep(1, 12); place(0, 0, -5.4, Math.PI, 0.1); PL.frozen = false; IN.keys.KeyW = true; },
    frame(i) { PL.pitch = mix(0.1, 0.32, ease(i / 74)); beat(i, 6, 72, 'The walls draw themselves.'); draw(); } });
  // 3. the exit door opens onto the next level
  S.push({ name: 's03-door', n: 78, prep() { prep(1, 13, { warm: 30 }); place(-3.5, 3.08, 6.2, Math.PI, 0.02); },
    frame(i) { PL.pos.z = mix(6.2, 8.9, ease(i / 77)); if (i === 24) { const d = GAME.L.exitDoor; d.locked = false; GAME.linkNext(); d.open(); }
      beat(i, 2, 34, 'Blue is real.'); draw(); } });
  // 4. through the blue arch: down turns into the wall
  S.push({ name: 's04-turn', n: 70, prep() { prep(2, 14); quiet(); place(0, 0, 2.6, Math.PI, 0.18); PL.frozen = false; IN.keys.KeyW = true; },
    frame(i) { quiet(); if (i >= 40) PL.pitch = mix(0.18, 0.05, k01(i, 40, 69)); draw(); } });
  // 5. the title card over the title view
  S.push({ name: 's05-card', n: 120, prep() { prep(0, 15); GAME.titleT = 99; },
    frame(i) { say('', 0); card.style.opacity = 1; cardEls.forEach((e, k) => e.style.opacity = ease(k01(i, k * 10, k * 10 + 14)).toFixed(3));
      draw({ fade: clamp(1 - i / 10, 0, 1) }); } });
  window.__tr = {
    S, FPS, noRender: false,
    names() { return S.map(s => s.name + ':' + s.n); },
    prep(k) { txt.style.opacity = 0; txt._s = null; S[k].prep.call(S[k]); },
    frame(k, i) { S[k].frame.call(S[k], i); },
    // per-frame facts render_audio.py turns into sound timings (footsteps from pos, flips from up)
    info() { return JSON.stringify({ idx: GAME.idx, pos: PL.pos.toArray().map(v => +v.toFixed(2)), up: PL.up.toArray().map(v => Math.round(v)), gr: PL.grounded ? 1 : 0, state: GAME.state }); }
  };
})();
