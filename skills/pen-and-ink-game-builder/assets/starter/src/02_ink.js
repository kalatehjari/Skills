/* ===================== ink renderer: crosshatch shaders, boiling lines, portals, baked shadows, post =====================
   Everything is drawn by four materials sharing the uniforms in U: INK (faces, hatched by light), LINE (boiling
   edges), GLOW (the one colour, BLUE, for things that are real), SPILL (soft light pools). POST adds paper and mood. */
const _v3a = new THREE.Vector3(), _v3b = new THREE.Vector3(), _v3c = new THREE.Vector3();
const V3 = THREE.Vector3, Q4 = THREE.Quaternion, M4 = THREE.Matrix4;
const PAPER = new THREE.Color('#E4E0D5'), INK = new THREE.Color('#171511'), BLUE = new THREE.Color('#5C64FF');
// surface patterns drawn by INK_FS (the aPat vertex attribute). Pass { pat: PAT.BRICK } to L.B() and friends.
const PAT = { NONE: 0, BRICK: 1, BLOCKS: 2, CHECKER: 3, WOOD: 4, BOOKS: 5, DAMASK: 6, TILES: 7, HEDGE: 8, ASHLAR: 9, BOARDS: 10,
  GRASS: 11, MONSTER: 12, PAPER: 13, PLASTER: 14, CARPET: 15, DIAL: 16, ROCK: 17 };

// shared global uniforms (objects shared by reference between all ink materials)
const U = {
  uTime: { value: 0 }, uWarp: { value: 0 }, uBoil: { value: 0 }, uBoilRate: { value: 8 }, uHatch: { value: 9 },
  uPaper: { value: new V3(PAPER.r, PAPER.g, PAPER.b) }, uInk: { value: new V3(INK.r, INK.g, INK.b) },
  uSunDir: { value: new V3(0.4, 0.8, 0.3).normalize() }, uSun: { value: 0.8 }, uAmb: { value: 0.45 },
  uFogTone: { value: 1 }, uFogDen: { value: 0.02 }, uCamPos: { value: new V3() },
  uLampPos: { value: new V3() }, uLampDir: { value: new V3(0, 0, -1) }, uLamp: { value: 0 }, uLampRange: { value: 14 },
  uPL: { value: Array.from({ length: 8 }, () => new THREE.Vector4(0, -999, 0, 1)) }, uPLi: { value: new Array(8).fill(0) },
  uShadowMap: { value: null }, uShadowMat: { value: new M4() }, uShadowOn: { value: 0 }, uShadowTexel: { value: 1 / 2048 },
  uCalm: { value: 0 }, uLod: { value: 1 }, uUpW: { value: new V3(0, 1, 0) }, uPatScale: { value: 1 }
};
const GLSL_COMMON = `
float h21(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float h11(float p){ return fract(sin(p * 91.345 + 7.13) * 43758.5453); }
vec3 warpP(vec3 p){ return p + uWarp * 0.11 * vec3(sin(p.y*0.6+uTime*1.3+p.z*0.21), sin(p.z*0.5+uTime*1.1+p.x*0.33), sin(p.x*0.55+uTime*0.9+p.y*0.27)); }
`;
const INK_VS = `
attribute float aTone; attribute float aPat;
uniform float uTime; uniform float uWarp;
varying vec3 vWP; varying vec3 vN; varying float vTone; varying float vPat;
#include <clipping_planes_pars_vertex>
${GLSL_COMMON}
void main(){
  vec4 wp = modelMatrix * vec4(position, 1.0);
  wp.xyz = warpP(wp.xyz);
  vWP = wp.xyz;
  vN = normalize(mat3(modelMatrix) * normal);
  vTone = aTone; vPat = aPat;
  vec4 mvPosition = viewMatrix * wp;
  gl_Position = projectionMatrix * mvPosition;
  #include <clipping_planes_vertex>
}`;
const INK_FS = `
precision highp float;
#include <packing>
uniform float uTime, uWarp, uBoil, uBoilRate, uHatch, uSun, uAmb, uFogTone, uFogDen, uLamp, uLampRange, uShadowOn, uShadowTexel, uCalm, uLod;
uniform float uFade, uToneMul, uFlash, uInvert, uMinTone, uPatScale;
uniform vec3 uPaper, uInk, uSunDir, uCamPos, uLampPos, uLampDir, uUpW;
uniform vec4 uPL[8]; uniform float uPLi[8];
uniform sampler2D uShadowMap; uniform mat4 uShadowMat;
varying vec3 vWP; varying vec3 vN; varying float vTone; varying float vPat;
#include <clipping_planes_pars_fragment>
${GLSL_COMMON}
float vnoise(vec2 p){ vec2 i=floor(p), f=fract(p); vec2 u=f*f*(3.0-2.0*f);
  return mix(mix(h21(i),h21(i+vec2(1.0,0.0)),u.x), mix(h21(i+vec2(0.0,1.0)),h21(i+vec2(1.0,1.0)),u.x), u.y); }
float sat1(float x){ return clamp(x, 0.0, 1.0); }
float hline(vec2 p, vec2 dp, vec2 dir, float freq, float w, float ph){
  if(w <= 0.0005) return 0.0;
  vec2 perp = vec2(-dir.y, dir.x);
  float along = dot(p, perp) * freq;
  float x = dot(p, dir) * freq + ph + 0.05*sin(along*0.29 + ph*3.1) + 0.025*sin(along*1.17 + ph);
  float fw = (abs(dir.x)*dp.x + abs(dir.y)*dp.y) * freq + 1e-4;
  float d = abs(fract(x) - 0.5);
  float l = 1.0 - smoothstep(w - fw, w + fw, d);
  return mix(l, sat1(2.0*w), smoothstep(0.3, 0.75, fw));
}
float gridLine(float x, float fw, float w){
  float d = abs(fract(x + 0.5) - 0.5);
  float l = 1.0 - smoothstep(w - fw, w + fw, d);
  return mix(l, sat1(2.0*w), smoothstep(0.3, 0.7, fw));
}
float hatchInk(vec2 p, vec2 dp, float t, float freq, float ph, float a0){
  float c1 = clamp((0.97 - t) * 1.05, 0.0, 0.6);
  float c2 = clamp((0.47 - t) * 1.3, 0.0, 0.5);
  float c3 = clamp((0.26 - t) * 1.6, 0.0, 0.45);
  float c4 = clamp((0.13 - t) * 2.5, 0.0, 0.4);
  float ink = hline(p, dp, vec2(cos(a0), sin(a0)), freq, c1*0.5, ph);
  ink = max(ink, hline(p, dp, vec2(cos(a0 - 1.45), sin(a0 - 1.45)), freq * 1.07, c2*0.5, ph + 1.7));
  ink = max(ink, hline(p, dp, vec2(cos(a0 + 0.62), sin(a0 + 0.62)), freq * 1.16, c3*0.5, ph + 3.1));
  ink = max(ink, hline(p, dp, vec2(cos(a0 - 0.75), sin(a0 - 0.75)), freq * 1.3, c4*0.5, ph + 4.3));
  return max(ink, smoothstep(0.05, 0.015, t));
}
float shadowF(vec3 N){
  if(uShadowOn < 0.5) return 1.0;
  vec4 sc = uShadowMat * vec4(vWP + N * 0.06, 1.0);
  vec3 c = sc.xyz / sc.w * 0.5 + 0.5;
  if(c.x < 0.0 || c.x > 1.0 || c.y < 0.0 || c.y > 1.0 || c.z > 1.0) return 1.0;
  float s = 0.0; float b = 0.0015; float o = uShadowTexel;
  s += step(c.z - b, unpackRGBAToDepth(texture2D(uShadowMap, c.xy + vec2(-o, -o))));
  s += step(c.z - b, unpackRGBAToDepth(texture2D(uShadowMap, c.xy + vec2( o, -o))));
  s += step(c.z - b, unpackRGBAToDepth(texture2D(uShadowMap, c.xy + vec2(-o,  o))));
  s += step(c.z - b, unpackRGBAToDepth(texture2D(uShadowMap, c.xy + vec2( o,  o))));
  return s * 0.25;
}
void main(){
  #include <clipping_planes_fragment>
  vec3 N = normalize(vN);
  // dissolve: uFade 0..1 eats the surface away in noise (things appearing / vanishing)
  if(uFade > 0.001){
    float n = vnoise(vWP.xy * 3.1 + vWP.z * 1.7) * 0.6 + vnoise(vWP.zx * 9.0) * 0.4;
    if(n < uFade) discard;
  }
  vec3 an = abs(N);
  vec2 p; float a0;
  if(an.x > an.y && an.x > an.z) { p = vWP.zy; a0 = 1.05; } else if(an.y > an.z) { p = vWP.xz; a0 = 0.785; } else { p = vWP.xy; a0 = 0.5; }
  vec2 dp = fwidth(p);
  float pid = floor(vPat + 0.5);
  float tone = vTone * uToneMul;
  float pink = 0.0;
  vec2 p0 = p; vec2 dp0 = dp;
  // ---------- patterns ----------
  if(pid > 0.5){
    p = p * uPatScale; dp = dp * uPatScale;
    if(pid < 1.5){ // brick
      vec2 b = p / vec2(0.5, 0.25); float row = floor(b.y); b.x += mod(row, 2.0) * 0.5;
      pink = max(gridLine(b.y, dp.y / 0.25, 0.05), gridLine(b.x, dp.x / 0.5, 0.03)) * 0.9;
      tone *= 0.9 + 0.12 * h21(floor(b));
    } else if(pid < 2.5){ // tumbling blocks (rhombille)
      vec2 q = p / 0.42;
      vec2 s = vec2(1.0, 1.7320508);
      vec4 hC = floor(vec4(q, q - vec2(0.5, 0.8660254)) / s.xyxy) + 0.5;
      vec2 h1 = q - hC.xy * s; vec2 h2 = q - (hC.zw * s + vec2(0.5, 0.8660254));
      vec2 lc = dot(h1, h1) < dot(h2, h2) ? h1 : h2;
      float a = atan(lc.y, lc.x);
      float face = (a > 0.5236 && a < 2.618) ? 0.0 : ((a >= 2.618 || a < -1.5708) ? 1.0 : 2.0);
      tone *= face < 0.5 ? 1.0 : (face < 1.5 ? 0.5 : 0.2);
      float fwq = length(dp) / 0.42 + 1e-4;
      vec2 u1 = vec2(0.8660254, 0.5), u2 = vec2(-0.8660254, 0.5), u3 = vec2(0.0, -1.0);
      float sp = 9.0;
      if(dot(lc, u1) > 0.0) sp = min(sp, abs(lc.x * u1.y - lc.y * u1.x));
      if(dot(lc, u2) > 0.0) sp = min(sp, abs(lc.x * u2.y - lc.y * u2.x));
      if(dot(lc, u3) > 0.0) sp = min(sp, abs(lc.x * u3.y - lc.y * u3.x));
      float hd = max(abs(lc.x), dot(abs(lc), vec2(0.5, 0.8660254)));
      float e = min(sp, abs(hd - 0.5));
      pink = (1.0 - smoothstep(0.025 - fwq, 0.025 + fwq, e)) * (1.0 - smoothstep(0.35, 0.8, fwq));
    } else if(pid < 3.5){ // checker floor
      vec2 c = floor(p / 0.6);
      float ch = mod(c.x + c.y, 2.0);
      if(uInvert > 0.5) ch = 1.0 - ch;
      tone *= ch > 0.5 ? 0.38 : 1.0;
      pink = max(gridLine(p.x / 0.6, dp.x / 0.6, 0.015), gridLine(p.y / 0.6, dp.y / 0.6, 0.015)) * 0.8;
    } else if(pid < 4.5){ // wood planks
      float row = floor(p.y / 0.18);
      pink = gridLine(p.y / 0.18, dp.y / 0.18, 0.035) * 0.85;
      pink = max(pink, gridLine((p.x + h11(row) * 5.0) / 2.2, dp.x / 2.2, 0.006) * 0.8);
      tone *= 0.86 + 0.14 * h11(row * 3.7);
      pink = max(pink, hline(p, dp, vec2(0.0, 1.0), 26.0, 0.04 * h11(row), row) * 0.35);
    } else if(pid < 5.5){ // books
      float row = floor(p.y / 0.45);
      float sx = p.x / 0.075 + h11(row) * 13.0;
      float sid = floor(sx);
      float ht = 0.62 + 0.3 * h21(vec2(sid, row));
      float fy = fract(p.y / 0.45);
      tone *= (0.3 + 0.7 * h21(vec2(sid * 1.3, row + 2.0)));
      if(fy > ht) tone *= 0.15;
      pink = max(gridLine(p.y / 0.45, dp.y / 0.45, 0.05), gridLine(sx, dp.x / 0.075, 0.05) * step(fy, ht)) * 0.9;
      pink = max(pink, (1.0 - smoothstep(0.0, 0.02, abs(fy - ht * 0.8))) * 0.5 * step(0.5, h21(vec2(sid, row * 7.0))));
    } else if(pid < 6.5){ // damask wallpaper
      vec2 l = fract(p / 0.5) - 0.5; vec2 cl = floor(p / 0.5);
      float fq = length(dp) / 0.5 + 1e-4;
      float dmd = abs(abs(l.x) + abs(l.y) - 0.34);
      float ci = abs(length(l) - 0.09);
      float st = abs(l.x);
      pink = max(1.0 - smoothstep(0.012 - fq, 0.012 + fq, dmd), 1.0 - smoothstep(0.01 - fq, 0.01 + fq, ci)) * (1.0 - smoothstep(0.3, 0.7, fq));
      pink = max(pink, (1.0 - smoothstep(0.004, 0.004 + fq, st)) * 0.5 * (1.0 - smoothstep(0.3, 0.7, fq)));
      tone *= 0.93;
    } else if(pid < 7.5){ // small tiles
      pink = max(gridLine(p.x / 0.3, dp.x / 0.3, 0.02), gridLine(p.y / 0.3, dp.y / 0.3, 0.02)) * 0.75;
      tone *= 0.95 + 0.05 * h21(floor(p / 0.3));
    } else if(pid < 8.5){ // hedge
      float n = vnoise(p * 5.0) * 0.6 + vnoise(p * 13.0) * 0.4;
      tone *= 0.38 + 0.55 * n;
      pink = smoothstep(0.66, 0.74, 1.0 - n) * 0.7;
    } else if(pid < 9.5){ // ashlar stone
      vec2 b = p / vec2(1.2, 0.6); float row = floor(b.y); b.x += mod(row, 2.0) * 0.37;
      pink = max(gridLine(b.y, dp.y / 0.6, 0.025), gridLine(b.x, dp.x / 1.2, 0.012)) * 0.85;
      tone *= 0.88 + 0.12 * h21(floor(b)) - 0.08 * vnoise(p * 4.0);
    } else if(pid < 10.5){ // wainscot boards
      pink = gridLine(p.x / 0.24, dp.x / 0.24, 0.03) * 0.8;
      tone *= 0.8 + 0.08 * h11(floor(p.x / 0.24));
    } else if(pid < 11.5){ // grass / earth stipple
      tone *= 0.72 + 0.28 * vnoise(p * 0.7);
      vec2 cc = floor(p * 9.0); vec2 lc2 = fract(p * 9.0) - 0.5;
      float on = step(0.55, h21(cc));
      float fq = length(dp) * 9.0 + 1e-4;
      pink = on * (1.0 - smoothstep(0.07 - fq, 0.07 + fq, length(lc2 + (vec2(h21(cc + 3.0), h21(cc + 7.0)) - 0.5) * 0.5))) * (1.0 - smoothstep(0.3, 0.7, fq));
    } else if(pid < 12.5){ // monster ink: black with paper scribbles
      tone = 0.03;
      float bp = floor(uTime * 10.0);
      float sc = hline(p, dp, normalize(vec2(0.8, 0.6 + 0.3 * sin(bp))), 22.0, 0.05, bp * 1.7);
      sc = max(sc, hline(p, dp, normalize(vec2(-0.5, 0.86)), 15.0, 0.035, bp * 2.3));
      pink = -sc;
    } else if(pid < 13.5){ // plain paper (signs)
      tone = 1.25;
    } else if(pid < 14.5){ // plaster with cracks
      tone *= 0.9 + 0.1 * vnoise(p * 1.5);
      float cr = abs(vnoise(p * 1.1 + 3.0) - 0.5);
      pink = (1.0 - smoothstep(0.006, 0.006 + length(dp) * 1.1 + 0.004, cr)) * 0.55;
    } else if(pid < 15.5){ // carpet runner
      float e = abs(fract(p.x / 1.6) - 0.5);
      pink = (1.0 - smoothstep(0.42, 0.43, e)) * 0.0 + gridLine(p.x / 1.6 + 0.5, dp.x / 1.6, 0.012) * 0.8;
      tone *= 0.55 + 0.1 * vnoise(p * 8.0);
    } else if(pid < 16.5){ // clock face / dial ticks (radial in plane)
      float ang = atan(p.y, p.x); float r = length(p);
      tone = 0.95;
      pink = (1.0 - smoothstep(0.0, 0.02, abs(fract(ang / 0.5236 + 0.5) - 0.5) * r)) * step(0.8, fract(r));
    } else { // void rock
      tone *= 0.55 + 0.45 * vnoise(p * 1.7);
      pink = smoothstep(0.7, 0.75, vnoise(p * 3.0 + 9.0)) * 0.6;
    }
    p = p0; dp = dp0;
  }
  // ---------- lighting ----------
  float sh = shadowF(N);
  float hemi = uAmb * (0.72 + 0.28 * dot(N, uUpW));
  float sun = max(dot(N, uSunDir), 0.0) * uSun * sh;
  vec3 Ld = uLampPos - vWP; float dl = length(Ld) + 1e-4; vec3 Ln = Ld / dl;
  float att = sat1(1.0 - dl / uLampRange); att *= att;
  float cone = smoothstep(0.8, 0.95, dot(-Ln, uLampDir));
  float lamp = uLamp * att * (0.18 + 0.82 * cone) * (0.35 + 0.65 * max(dot(N, Ln), 0.0)) * 1.6;
  float pl = 0.0;
  for(int i = 0; i < 8; i++){
    vec3 d = uPL[i].xyz - vWP; float dd = length(d) + 1e-4;
    float a = sat1(1.0 - dd / uPL[i].w); a *= a;
    pl += uPLi[i] * a * (0.3 + 0.7 * max(dot(N, d / dd), 0.0));
  }
  float light = hemi + sun + lamp + pl;
  float t = max(tone * light, uMinTone);
  // fog
  float dist = length(vWP - uCamPos);
  float fd = dist * uFogDen;
  float fog = 1.0 - exp(-fd * fd);
  t = mix(t, uFogTone, fog);
  t = clamp(t, 0.0, 1.3);
  // ---------- hatching ----------
  float boil = uBoil * (1.0 - uCalm * 0.7);
  float bs = floor(uTime * uBoilRate) * step(0.002, boil);
  float ph = boil * h11(bs) * 6.2831;
  vec2 hp = p + boil * 0.025 * (vec2(h11(bs + 1.0), h11(bs + 2.0)) - 0.5);
  float px = max(max(min(dp.x, dp.y), length(dp) * 0.45), 1e-5) * uHatch;
  float l = clamp(log2(0.19 / px), 0.0, 3.5) * uLod;
  float lf = floor(l); float fr = l - lf;
  float f1 = uHatch * exp2(lf);
  float ink = hatchInk(hp, dp, t, f1, ph, a0);
  if(fr > 0.02){ ink = mix(ink, hatchInk(hp, dp, t, f1 * 2.0, ph, a0), fr); }
  if(pink < 0.0) ink = min(ink, 1.0 + pink * 0.9 * (1.0 - fog));
  else ink = max(ink, pink * (1.0 - fog) * smoothstep(0.02, 0.25, t + 0.2));
  vec3 col = mix(uPaper, uInk, ink);
  col = mix(col, uPaper * 1.06, uFlash);
  gl_FragColor = vec4(col, 1.0);
}`;
function makeInkMat(o = {}) {
  const u = Object.assign({}, U, {
    uFade: { value: o.fade || 0 }, uToneMul: { value: o.toneMul == null ? 1 : o.toneMul }, uFlash: { value: 0 },
    uInvert: { value: 0 }, uMinTone: { value: o.minTone || 0 }
  });
  const m = new THREE.ShaderMaterial({
    uniforms: u, vertexShader: INK_VS, fragmentShader: INK_FS, clipping: true,
    extensions: { derivatives: true }, side: o.side || THREE.FrontSide,
    polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1
  });
  return m;
}
const LINE_VS = `
attribute float aSeed;
uniform float uTime; uniform float uWarp; uniform float uBoil; uniform float uBoilRate; uniform float uCalm;
varying vec3 vWP;
#include <clipping_planes_pars_vertex>
${GLSL_COMMON}
void main(){
  vec4 wp = modelMatrix * vec4(position, 1.0);
  wp.xyz = warpP(wp.xyz);
  float b = uBoil * (1.0 - uCalm * 0.7);
  float st = floor(uTime * uBoilRate) * step(0.002, b);
  vec3 j = vec3(h11(aSeed * 12.99 + st * 7.23), h11(aSeed * 39.35 + st * 1.13), h11(aSeed * 73.16 + st * 5.22)) - 0.5;
  wp.xyz += j * (0.01 + b * 0.06);
  vWP = wp.xyz;
  vec4 mvPosition = viewMatrix * wp;
  gl_Position = projectionMatrix * mvPosition;
  #include <clipping_planes_vertex>
}`;
const LINE_FS = `
precision highp float;
uniform vec3 uInk; uniform vec3 uPaper; uniform vec3 uCamPos; uniform float uFogDen; uniform float uFogTone; uniform float uLineTone; uniform float uFade;
varying vec3 vWP;
#include <clipping_planes_pars_fragment>
void main(){
  #include <clipping_planes_fragment>
  if(uFade > 0.5) discard;
  float d = length(vWP - uCamPos); float fd = d * uFogDen; float f = 1.0 - exp(-fd * fd);
  vec3 c = mix(mix(uInk, uPaper, uLineTone), mix(uInk, uPaper, uFogTone), f);
  gl_FragColor = vec4(c, 1.0);
}`;
function makeLineMat(o = {}) {
  const u = Object.assign({}, U, { uLineTone: { value: o.tone || 0 }, uFade: { value: 0 } });
  return new THREE.ShaderMaterial({ uniforms: u, vertexShader: LINE_VS, fragmentShader: LINE_FS, clipping: true, depthWrite: false });
}
const GLOW_VS = `
uniform float uTime; uniform float uWarp;
varying vec3 vWP; varying vec3 vN;
#include <clipping_planes_pars_vertex>
${GLSL_COMMON}
void main(){
  vec4 wp = modelMatrix * vec4(position, 1.0);
  vWP = wp.xyz; vN = normalize(mat3(modelMatrix) * normal);
  vec4 mvPosition = viewMatrix * wp;
  gl_Position = projectionMatrix * mvPosition;
  #include <clipping_planes_vertex>
}`;
const GLOW_FS = `
precision highp float;
uniform vec3 uColor; uniform float uTime; uniform float uPulse; uniform vec3 uCamPos; uniform float uFogDen; uniform float uFogTone; uniform vec3 uInk; uniform vec3 uPaper; uniform float uFade; uniform float uAlpha; uniform float uFogMul;
varying vec3 vWP; varying vec3 vN;
#include <clipping_planes_pars_fragment>
void main(){
  #include <clipping_planes_fragment>
  if(uFade > 0.5) discard;
  vec3 V = normalize(uCamPos - vWP);
  float fr = pow(1.0 - clamp(abs(dot(normalize(vN), V)), 0.0, 1.0), 2.0);
  vec3 c = uColor * (0.9 + 0.25 * sin(uTime * 4.0) * uPulse) + vec3(0.35) * fr;
  float d = length(vWP - uCamPos); float fd = d * uFogDen * 0.6 * uFogMul; float f = 1.0 - exp(-fd * fd);
  c = mix(c, mix(uInk, uPaper, uFogTone), f);
  gl_FragColor = vec4(c, uAlpha);
}`;
function makeGlowMat(color = BLUE, o = {}) {
  const u = Object.assign({}, U, { uColor: { value: new V3(color.r, color.g, color.b) }, uPulse: { value: o.pulse == null ? 1 : o.pulse }, uFade: { value: 0 }, uAlpha: { value: o.alpha == null ? 1 : o.alpha }, uFogMul: { value: o.fog === false ? 0 : 1 } });
  return new THREE.ShaderMaterial({ uniforms: u, vertexShader: GLOW_VS, fragmentShader: GLOW_FS, clipping: true, transparent: !!o.alpha, depthWrite: !o.alpha, side: o.side || THREE.FrontSide, blending: o.add ? THREE.AdditiveBlending : THREE.NormalBlending });
}
// soft light pool spilling from under a real door (alpha falls off away from the door and to the sides)
const SPILL_VS = `
uniform float uTime; uniform float uWarp;
varying vec2 vUv;
#include <clipping_planes_pars_vertex>
${GLSL_COMMON}
void main(){
  vUv = uv;
  vec4 wp = modelMatrix * vec4(position, 1.0);
  wp.xyz = warpP(wp.xyz);
  vec4 mvPosition = viewMatrix * wp;
  gl_Position = projectionMatrix * mvPosition;
  #include <clipping_planes_vertex>
}`;
const SPILL_FS = `
precision highp float;
uniform vec3 uColor; uniform float uTime; uniform float uA; uniform float uRadial;
varying vec2 vUv;
#include <clipping_planes_pars_fragment>
void main(){
  #include <clipping_planes_fragment>
  float fx = 1.0 - smoothstep(0.1, 0.5, abs(vUv.x - 0.5));
  float fz = pow(1.0 - vUv.y, 1.7);
  float fr = pow(1.0 - clamp(length(vUv - 0.5) * 2.0, 0.0, 1.0), 2.2);
  float a = uA * mix(fx * fz, fr, uRadial) * (0.78 + 0.22 * sin(uTime * 1.7));
  if(a < 0.004) discard;
  gl_FragColor = vec4(uColor, a);
}`;
function makeSpillMat(color = BLUE, a = 0.5, radial = 0) {
  const u = Object.assign({}, U, { uColor: { value: new V3(color.r, color.g, color.b) }, uA: { value: a }, uRadial: { value: radial } });
  return new THREE.ShaderMaterial({ uniforms: u, vertexShader: SPILL_VS, fragmentShader: SPILL_FS, clipping: true, transparent: true, depthWrite: false });
}
const PORTAL_FS = `
precision highp float; uniform sampler2D tPortal; uniform vec2 uRes;
void main(){ gl_FragColor = texture2D(tPortal, gl_FragCoord.xy / uRes); }`;
const PORTAL_VS = `void main(){ gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`;

/* ---------- post (final) pass ---------- */
const POST_FS = `
precision highp float;
uniform sampler2D tScene; uniform vec2 uRes; uniform float uTime;
uniform float uDouble, uSwirl, uWave, uTendril, uTunnel, uInvert, uFlash, uFlashTone, uFade, uGrain, uWarm, uRed, uCalm, uChrom;
uniform vec3 uPaper, uInk;
varying vec2 vUv;
float h21(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vn(vec2 p){ vec2 i=floor(p), f=fract(p); vec2 u=f*f*(3.0-2.0*f); return mix(mix(h21(i),h21(i+vec2(1.,0.)),u.x), mix(h21(i+vec2(0.,1.)),h21(i+vec2(1.,1.)),u.x), u.y); }
void main(){
  vec2 uv = vUv;
  vec2 c = uv - 0.5; c.x *= uRes.x / uRes.y;
  float r = length(c);
  float sw = uSwirl * (1.0 - uCalm);
  if(sw > 0.001){ float a = sw * sin(uTime * 0.6) * smoothstep(0.75, 0.0, r); float ca = cos(a), sa = sin(a); vec2 cc = uv - 0.5; uv = 0.5 + vec2(ca * cc.x - sa * cc.y, sa * cc.x + ca * cc.y); }
  float wv = uWave * (1.0 - uCalm);
  if(wv > 0.001) uv += wv * vec2(sin(uv.y * 13.0 + uTime * 2.1), cos(uv.x * 11.0 + uTime * 1.7)) * 0.0045;
  vec3 col = texture2D(tScene, uv).rgb;
  if(uChrom > 0.001){ col.r = texture2D(tScene, uv + vec2(uChrom * 0.004, 0.0)).r; col.b = texture2D(tScene, uv - vec2(uChrom * 0.004, 0.0)).b; }
  if(uDouble > 0.001){
    vec2 o = vec2(sin(uTime * 0.83), cos(uTime * 0.61)) * 0.011 * uDouble * (1.0 - uCalm * 0.7);
    vec3 c2 = texture2D(tScene, uv + o).rgb;
    col = mix(col, min(col, c2), 0.75 * clamp(uDouble, 0.0, 1.0));
  }
  // paper grain & fibres
  vec2 gp = gl_FragCoord.xy;
  float g = h21(floor(gp * 0.5)) * 0.5 + vn(gp * 0.035) * 0.35 + vn(gp * vec2(0.004, 0.02)) * 0.15;
  col *= 1.0 - uGrain * (g - 0.5) * 0.16;
  // ink tendrils / vignette
  float n = vn(uv * 5.0 + vec2(uTime * 0.05, -uTime * 0.04)) * 0.65 + vn(uv * 17.0 - uTime * 0.1) * 0.35;
  float edge = r * (1.0 + uTunnel * 0.9) + (n - 0.5) * 0.35 * uTendril;
  float v = smoothstep(0.98 - uTendril * 0.32, 0.58 - uTendril * 0.3, edge);
  col = mix(uInk, col, mix(1.0, v, clamp(0.35 + uTendril, 0.0, 1.0)));
  if(uRed > 0.001) col = mix(col, col * vec3(1.25, 0.7, 0.62), uRed);
  if(uWarm > 0.001){
    float lum = dot(col, vec3(0.333));
    vec3 warm = mix(vec3(0.16, 0.07, 0.04), vec3(1.0, 0.72, 0.42), lum);
    col = mix(col, warm, uWarm);
  }
  col = mix(col, uPaper + uInk - col, uInvert);
  col = mix(col, mix(uInk, uPaper * 1.05, uFlashTone), uFlash);
  col = mix(col, uInk * 0.5, uFade);
  gl_FragColor = vec4(col, 1.0);
}`;
const POST = {
  tScene: { value: null }, uRes: { value: new THREE.Vector2(1, 1) }, uTime: U.uTime,
  uDouble: { value: 0 }, uSwirl: { value: 0 }, uWave: { value: 0 }, uTendril: { value: 0 }, uTunnel: { value: 0 }, uInvert: { value: 0 },
  uFlash: { value: 0 }, uFlashTone: { value: 1 }, uFade: { value: 1 }, uGrain: { value: 1 }, uWarm: { value: 0 },
  uRed: { value: 0 }, uCalm: U.uCalm, uChrom: { value: 0 },
  uPaper: U.uPaper, uInk: U.uInk
};

const R = {
  renderer: null, mainRT: null, portalRT: null, w: 1, h: 1, pr: 1, q: null,
  pcam: new THREE.PerspectiveCamera(70, 1, 0.05, 900),
  init(canvas) {
    let r;
    try { r = new THREE.WebGLRenderer({ canvas, antialias: false, alpha: false, stencil: false, powerPreference: 'high-performance', preserveDrawingBuffer: false }); }
    catch (e) { throw new Error('WebGL is not available on this device/browser.'); }
    r.autoClear = false; r.outputEncoding = THREE.LinearEncoding; r.sortObjects = true;
    this.renderer = r; this.isGL2 = r.capabilities.isWebGL2;
    this.postCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
    this.postMat = new THREE.ShaderMaterial({ uniforms: POST, vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }', fragmentShader: POST_FS, depthTest: false, depthWrite: false });
    this.postScene = new THREE.Scene();
    const tri = new THREE.BufferGeometry(); tri.setAttribute('position', new THREE.Float32BufferAttribute([-1, -1, 0, 3, -1, 0, -1, 3, 0], 3)); tri.setAttribute('uv', new THREE.Float32BufferAttribute([0, 0, 2, 0, 0, 2], 2));
    const quad = new THREE.Mesh(tri, this.postMat); quad.frustumCulled = false; this.postScene.add(quad);
    this.depthMat = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking });
    this.shadowCam = new THREE.OrthographicCamera(-10, 10, 10, -10, 0.1, 100); this.shadowCam.layers.set(1);
    this.portalUniforms = { tPortal: { value: null }, uRes: POST.uRes };
    this.applyQuality();
  },
  qualityPreset() {
    const dpr = window.devicePixelRatio || 1;
    const q = SET.quality;
    if (q === 0) return { pr: Math.min(dpr, 1.5) * (IS_TOUCH ? 0.62 : 0.75), samples: 0, shadow: 1024, lod: 0, portalScale: 0.6 };
    if (q === 1) return { pr: Math.min(dpr, IS_TOUCH ? 1.25 : 1.5), samples: this.isGL2 ? 2 : 0, shadow: 2048, lod: 1, portalScale: 1 };
    return { pr: Math.min(dpr, 2), samples: this.isGL2 ? 4 : 0, shadow: 2048, lod: 1, portalScale: 1 };
  },
  applyQuality() {
    this.q = this.qualityPreset(); U.uLod.value = 1; this.resize(true);
  },
  resize(force) {
    const w = window.innerWidth, h = window.innerHeight;
    if (!force && w === this.cw && h === this.ch) return;
    this.cw = w; this.ch = h;
    const pr = this.q.pr; this.renderer.setPixelRatio(pr); this.renderer.setSize(w, h, false);
    const W = Math.max(2, Math.floor(w * pr)), H = Math.max(2, Math.floor(h * pr));
    this.w = W; this.h = H; POST.uRes.value.set(W, H);
    if (this.mainRT) this.mainRT.dispose(); if (this.portalRT) this.portalRT.dispose();
    const opt = { minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter, depthBuffer: true, stencilBuffer: false };
    this.mainRT = new THREE.WebGLRenderTarget(W, H, opt); if (this.q.samples) this.mainRT.samples = this.q.samples;
    const ps = this.q.portalScale;
    this.portalRT = new THREE.WebGLRenderTarget(Math.max(2, Math.floor(W * ps)), Math.max(2, Math.floor(H * ps)), opt); if (this.q.samples) this.portalRT.samples = this.q.samples;
    POST.tScene.value = this.mainRT.texture; this.portalUniforms.tPortal.value = this.portalRT.texture;
    if (window.CAM) { CAM.aspect = w / h; CAM.updateProjectionMatrix(); }
  },
  bakeShadow(level) {
    const env = level.env; if (!env.sun || env.noShadow) { level.shadowRT = null; return; }
    const size = this.q.shadow;
    const rt = new THREE.WebGLRenderTarget(size, size, { minFilter: THREE.NearestFilter, magFilter: THREE.NearestFilter, depthBuffer: true, stencilBuffer: false });
    const bb = level.bounds; const c = bb.getCenter(new V3()); const rad = bb.getSize(new V3()).length() * 0.5 + 2;
    const cam = this.shadowCam; const sd = env.sunDir.clone().normalize();
    cam.position.copy(c).addScaledVector(sd, rad + 10); cam.up.set(Math.abs(sd.y) > 0.95 ? 1 : 0, Math.abs(sd.y) > 0.95 ? 0 : 1, 0); cam.lookAt(c);
    cam.updateMatrixWorld();
    // fit to bounds in light space
    const inv = cam.matrixWorldInverse; const pts = [];
    for (let i = 0; i < 8; i++) pts.push(new V3(i & 1 ? bb.max.x : bb.min.x, i & 2 ? bb.max.y : bb.min.y, i & 4 ? bb.max.z : bb.min.z).applyMatrix4(inv));
    let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9, z0 = 1e9, z1 = -1e9;
    for (const p of pts) { x0 = Math.min(x0, p.x); x1 = Math.max(x1, p.x); y0 = Math.min(y0, p.y); y1 = Math.max(y1, p.y); z0 = Math.min(z0, p.z); z1 = Math.max(z1, p.z); }
    cam.left = x0 - 1; cam.right = x1 + 1; cam.bottom = y0 - 1; cam.top = y1 + 1; cam.near = Math.max(0.1, -z1 - 2); cam.far = -z0 + 2;
    cam.updateProjectionMatrix();
    const r = this.renderer; const ov = level.scene.overrideMaterial; level.scene.overrideMaterial = this.depthMat;
    const oldClear = r.getClearColor(new THREE.Color()), oldA = r.getClearAlpha();
    r.setRenderTarget(rt); r.setClearColor(0xffffff, 1); r.clear(); r.render(level.scene, cam);
    r.setRenderTarget(null); r.setClearColor(oldClear, oldA);
    level.scene.overrideMaterial = ov;
    level.shadowRT = rt; level.shadowMat = new M4().multiplyMatrices(cam.projectionMatrix, cam.matrixWorldInverse); level.shadowTexel = 1 / size;
  },
  applyEnv(level, M) { // M: optional matrix mapping current coords → this level coords (for the lamp)
    const e = level.env;
    U.uSunDir.value.copy(e.sunDir).normalize(); U.uSun.value = e.sun; U.uAmb.value = e.amb * (e.ambMul == null ? 1 : e.ambMul);
    U.uFogTone.value = e.fogTone; U.uFogDen.value = e.fogDen * (e.fogMul == null ? 1 : e.fogMul); U.uHatch.value = e.hatch || 9;
    U.uUpW.value.copy(e.upW || _up0); U.uPatScale.value = e.patScale || 1;
    if (level.shadowRT) { U.uShadowMap.value = level.shadowRT.texture; U.uShadowMat.value.copy(level.shadowMat); U.uShadowOn.value = 1; U.uShadowTexel.value = level.shadowTexel; }
    else { U.uShadowOn.value = 0; U.uShadowMap.value = null; }
    const L = level.plights;
    for (let i = 0; i < 8; i++) {
      const pl = L[i];
      if (pl && pl.i > 0.001) { U.uPL.value[i].set(pl.pos.x, pl.pos.y, pl.pos.z, pl.r); U.uPLi.value[i] = pl.i * (pl.flick == null ? 1 : pl.flick); }
      else { U.uPL.value[i].set(0, -9999, 0, 1); U.uPLi.value[i] = 0; }
    }
    U.uLampPos.value.copy(PL.lampPos); U.uLampDir.value.copy(PL.lampDir);
    if (M) { U.uLampPos.value.applyMatrix4(M); U.uLampDir.value.transformDirection(M); }
    U.uLamp.value = PL.lampI * (e.lampMul == null ? 1 : e.lampMul); U.uLampRange.value = PL.lampRange;
  },
  clearColor(env) { const t = env.bgTone == null ? env.fogTone : env.bgTone; return _cc.copy(INK).lerp(PAPER, t); },
  render(level, cam, portal) {
    const r = this.renderer;
    // ---- portal pass ----
    if (portal) {
      const tl = portal.level;
      this.pcam.projectionMatrix.copy(cam.projectionMatrix); this.pcam.projectionMatrixInverse.copy(cam.projectionMatrixInverse);
      _m4a.multiplyMatrices(portal.M, cam.matrixWorld);
      _m4a.decompose(this.pcam.position, this.pcam.quaternion, this.pcam.scale);
      this.pcam.updateMatrixWorld(true);
      this.applyEnv(tl, portal.M);
      U.uCamPos.value.copy(this.pcam.position);
      r.clippingPlanes = [portal.plane];
      const hidden = [];
      for (const d of tl.doors) { if (d.aperture && d.aperture.visible !== false) { d.aperture.visible = false; hidden.push(d.aperture); } }
      if (!tl._apScan || tl._apScan !== tl.scene.children.length) { tl._apScan = tl.scene.children.length; tl._aps = tl.scene.children.filter(o => o.material === MAT.portal); }
      for (const o of tl._aps) if (o.visible !== false) { o.visible = false; hidden.push(o); }
      if (portal.hideLeaf) { hidden.push(portal.hideLeaf); portal.hideLeaf.visible = false; }
      for (const o of (tl.portalHide || [])) if (o.visible) { o.visible = false; hidden.push(o); }
      r.setRenderTarget(this.portalRT); r.setClearColor(this.clearColor(tl.env), 1); r.clear(); r.render(tl.scene, this.pcam);
      for (const o of hidden) o.visible = true;
      r.clippingPlanes = [];
    }
    // ---- main pass ----
    this.applyEnv(level, null);
    U.uCamPos.value.copy(cam.position);
    r.setRenderTarget(this.mainRT); r.setClearColor(this.clearColor(level.env), 1); r.clear(); r.render(level.scene, cam);
    // ---- post ----
    r.setRenderTarget(null); r.clear(); r.render(this.postScene, this.postCam);
  }
};
const _cc = new THREE.Color(), _m4a = new M4(), _m4b = new M4(), _up0 = new V3(0, 1, 0);
