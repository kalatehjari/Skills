// THE SCORE — Tan Be Tan (Rosha). The song is the user's own track; this file locks the picture to its real beats.
(function () {
  const node = typeof require !== 'undefined';
  const U = node ? require('./engine/util') : globalThis.U;
  const MU = node ? require('./engine/music') : globalThis.MUSIC;
  const A = node ? require('./beats.js') : globalThis.ANALYSIS;
  const { m, makeClock } = MU;

  const FPS = 30;
  const FORMAT = U.pickFormat('16:9');
  const [W, H] = U.formatSize(FORMAT);
  const SAFE = U.safeArea(W, H);
  const WIDE = true;
  const clock = makeClock({ beats: A.beats, downbeat: A.downbeat, beatsPerBar: A.meter });
  const { T, BEAT } = clock;
  const DURATION = 293.08;

  // ---------- story sections, in bars of the real song ----------
  const S = {
    cold:    [0, T(10)],        // black, ink drop, title. Night hallway, she waits.
    hook:    [T(10), T(18)],    // instrumental hook: the drummer's shadow under the door, she opens it -> desert
    verse1:  [T(18), T(34)],    // the desert of no-love
    bridge1: [T(34), T(50)],    // he arrives: strings, plans, dagger, face to face
    chorus1: [T(50), T(66)],    // the siege: hands, marionette, body-to-body duel
    solo:    [T(66), T(79)],    // storm: she tears the strings, runs through the rain
    build1:  [T(79), T(83)],    // he beats the war drum
    verse3:  [T(83), T(99)],    // she stands; meets her own self; peace
    bridge2: [T(99), T(115)],   // desert again, but green grows where she walks
    chorus2: [T(115), T(131)],  // the hands return; she disarms him
    build2:  [T(131), T(137)],  // the drum cracks
    outro:   [T(137), T(153)],  // she walks to the door of light; he drums alone, small
    end:     [T(153), DURATION],
  };
  const sec = (t) => { for (const k in S) if (t >= S[k][0] && t < S[k][1]) return k; return 'end'; };

  // ---------- lyrics: each line = 4 bars, from the section's first downbeat ----------
  const LY = {
    v1: [['من خالی از مهر توام', 'I am emptied of your love'],
         ['صحرای بی‌آب و علف', 'a desert without water, without grass'],
         ['یک ریگزار رو به موت', 'a field of sand, turned toward death'],
         ['در جنگ با تو، بی‌هدف', 'at war with you, without aim']],
    b1: [['تو در پی نیرنگ و دام', 'you, chasing tricks and snares'],
         ['خنجر به دست از روبرو', 'dagger in hand, face to face'],
         ['در فکر ویران کردنی', 'thinking only of ruin'],
         ['با نقشه‌ها در پیش رو', 'with your plans laid out ahead']],
    c:  [['نایی ندارم در صدا', 'no breath left in my voice'],
         ['تابی ندارم در بدن', 'no strength left in my body'],
         ['محو تماشای توام', 'lost, only watching you'],
         ['در جنگ با من، تن به تن', 'at war with me, body to body']],
    v3: [['تو هی بزن بر طبل جنگ', 'go on, keep beating the drum of war'],
         ['دیگر چه می‌خواهی ز من', 'what more could you want from me'],
         ['من صلح کردم با خودم', 'I have made peace with myself'],
         ['بر جان من آتش نزن', 'do not set fire to my soul']],
  };
  const subtitles = [];
  const place = (key, bar0) => LY[key].forEach(([fa, en], i) => subtitles.push({ t: T(bar0 + i * 4) + 0.15, end: T(bar0 + i * 4 + 4) - 0.45, fa, en, key }));
  place('v1', 18); place('b1', 34); place('c', 50); place('v3', 83); place('v1', 99); place('c', 115); place('v3', 137);

  // ---------- drum hits the picture plays (the drummer's strikes, shockwaves) ----------
  const beatsIn = (t0, t1) => A.beats.filter((b) => b >= t0 - 1e-3 && b < t1 - 1e-3);
  const strikes = [...beatsIn(T(79), T(83)), ...beatsIn(T(131), T(137))];
  const v3strikes = beatsIn(T(83), T(99)).filter((b, i) => i % 2 === 0); // half-time strikes under verse 3

  const ev = {
    title: 0.8,
    doorOpen: T(17),
    he: T(34),
    hands: T(50),
    duel: T(62),
    snap: T(66),          // she tears the strings: first solo downbeat
    drum1: T(79),
    stand: T(83),
    mirror: T(91),        // "I have made peace with myself"
    fire: T(95),
    bloom: T(99),
    disarm: T(127),
    crack: T(137) - BEAT, // last strike tears the drum skin
    door: T(149),
    end: T(153),
  };

  const markers = {
    title: ev.title, he: ev.he,
    hands: { t: ev.hands, sync: 'v' }, snap: { t: ev.snap, sync: 'v' }, drum1: { t: ev.drum1, sync: 'v' },
    stand: { t: ev.stand, sync: 'v' }, mirror: ev.mirror, fire: ev.fire, bloom: ev.bloom,
    chorus2: { t: T(115), sync: 'v' }, disarm: ev.disarm, crack: ev.crack, outro: T(137), door: ev.door, end: ev.end,
  };

  const SCORE = { FPS, FORMAT, W, H, SAFE, WIDE, DURATION, clock, T, BEAT, S, sec, m, ev, markers, subtitles, strikes, v3strikes, beats: A.beats, STYLE: 'paper' };
  if (node) module.exports = SCORE; else globalThis.SCORE = SCORE;
})();
