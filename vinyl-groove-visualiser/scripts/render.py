# Vinyl groove visualiser renderer.
# usage: python3 render.py <workdir> stills <t> [t...]          -> <workdir>/out/still_<t>.png
#        python3 render.py <workdir> video <f0> <f1> <out.mp4>  -> silent video segment of frames [f0, f1)
# <workdir> must contain analysis.npz (from analyze.py) and sections.json.
import numpy as np, sys, subprocess, math, json, os
from multiprocessing import Pool
from PIL import Image, ImageDraw

WD = sys.argv[1]
CFG = json.load(open(os.path.join(WD, 'sections.json')))
W, H = CFG.get('size', [1280, 720])
FPS = CFG.get('fps', 30)
A = np.load(os.path.join(WD, 'analysis.npz'))
RATE, DUR = float(A['rate']), float(A['dur'])
BEATS = A['beats']; SNARES = A['snares']
B = {k: A[k] for k in ['bassL', 'bassR', 'midL', 'midR', 'highL', 'highR', 'side', 'full']}
# smoothed loudness for groove width
k_ = np.ones(int(RATE * 0.12)) / int(RATE * 0.12)
B['fullS'] = np.convolve(B['full'], k_, 'same')
B['bass'] = (B['bassL'] + B['bassR']) / 2
B['high'] = (B['highL'] + B['highR']) / 2
NF = int(DUR * FPS)

def env(name, tau):
    arr = B[name]
    i = np.clip((np.asarray(tau) * RATE).astype(np.int64), 0, len(arr) - 1)
    return arr[i]

def smooth(x): x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)
def mix(a, b, k): return a + (b - a) * k

# kick strength at each beat = bass peak around it
BEAT_STR = np.array([env('bass', np.linspace(b - 0.04, b + 0.06, 12)).max() for b in BEATS])
BEAT_STR = np.clip((BEAT_STR - 0.25) / 0.6, 0, 1.3)

# ---------- palettes & sections ----------
P = {
    'indigo':  ((0.35, 0.75, 1.00), (0.60, 0.30, 1.00), (0.03, 0.03, 0.10)),
    'violet':  ((0.85, 0.45, 1.00), (1.00, 0.30, 0.60), (0.06, 0.02, 0.10)),
    'amber':   ((1.00, 0.55, 0.20), (1.00, 0.20, 0.35), (0.12, 0.04, 0.03)),
    'emerald': ((0.30, 1.00, 0.70), (0.20, 0.60, 1.00), (0.02, 0.08, 0.07)),
    'ice':     ((0.80, 0.90, 1.00), (0.50, 0.60, 1.00), (0.05, 0.05, 0.09)),
    'gold':    ((1.00, 0.80, 0.35), (1.00, 0.25, 0.80), (0.10, 0.04, 0.08)),
    'crimson': ((1.00, 0.30, 0.25), (1.00, 0.85, 0.80), (0.12, 0.02, 0.03)),
}
for k_, v_ in CFG.get('palettes', {}).items(): P[k_] = tuple(tuple(c) for c in v_)
# sections.json "sections": [[start, end, mode('rec'|'grv'), palette, speed, energy], ...]
SECT = [tuple(x) for x in CFG['sections']]
SECT[-1] = (SECT[-1][0], DUR + 1) + tuple(SECT[-1][2:])
def sect(t):
    for i, s in enumerate(SECT):
        if s[0] <= t < s[1]: return i, s
    return len(SECT) - 1, SECT[-1]

def palette(t):
    i, s = sect(t)
    cur = np.array(P[s[3]])
    if i > 0:
        prev = np.array(P[SECT[i - 1][3]])
        cur = mix(prev, cur, smooth((t - s[0]) / 0.6))
    return cur[0], cur[1], cur[2]

# distance travelled (for dust) with smoothed speed
TT = np.arange(0, DUR + 1, 1 / FPS)
SPD = np.array([sect(t)[1][4] or 4.0 for t in TT])
SPD = np.convolve(SPD, np.ones(15) / 15, 'same')
DIST = np.cumsum(SPD) / FPS
def speed(t): return SPD[min(len(SPD) - 1, int(t * FPS))]
def dist(t): return DIST[min(len(DIST) - 1, int(t * FPS))]

ys_, xs_ = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = (1 - 0.45 * (((xs_ - W / 2) / W) ** 2 + ((ys_ - H / 2) / H) ** 2) * 2)[..., None]

# ---------- label (no text) ----------
def make_label():
    S = 512
    im = Image.new('RGB', (S, S), (0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([0, 0, S - 1, S - 1], fill=(30, 26, 40))
    for rr, col, wd in [(230, (210, 170, 90), 3), (200, (210, 170, 90), 1), (120, (180, 60, 70), 30), (60, (210, 170, 90), 2)]:
        d.ellipse([S / 2 - rr, S / 2 - rr, S / 2 + rr, S / 2 + rr], outline=col, width=wd)
    for k in range(12):  # small geometric motif so rotation is readable
        a = k * math.pi / 6
        x, y = S / 2 + 165 * math.cos(a), S / 2 + 165 * math.sin(a)
        d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=(210, 170, 90) if k % 3 else (230, 90, 90))
    return np.asarray(im).astype(np.float32) / 255
LABEL = make_label()

# ---------- top-down record: the whole song is cut into the spiral ----------
R_LAB, R_IN, R_OUT = 0.33, 0.36, 0.97
REV = 1.8                                  # seconds per revolution
NR = (DUR / REV) / (R_OUT - R_IN)          # grooves per unit radius
TGT_A = -2.2

def rec_target(t):
    r = R_OUT - (t / REV) / NR
    return np.array([r * math.cos(TGT_A), r * math.sin(TGT_A)])

def record_frame(t, zoom):
    glow, side, fog = palette(t)
    s0 = H * 0.46
    scale = s0 * zoom
    T = rec_target(t)
    c = T + (np.zeros(2) - T) * (1 / zoom)
    X = (xs_ - W / 2) / scale + c[0]
    Y = (ys_ - H / 2) / scale + c[1]
    r = np.sqrt(X * X + Y * Y); th = np.arctan2(Y, X)
    rot = t * 2 * math.pi / REV
    phi = ((th - rot) % (2 * math.pi)) / (2 * math.pi)
    # spiral: groove index n -> time in song
    ring = (R_OUT - r) * NR
    tau = (np.floor(ring - phi) + phi) * REV
    wig = 0.22 * env('bass', tau) * np.sin(tau * 2 * math.pi * 7) + 0.08 * env('mid' + 'L', tau) * np.sin(tau * 2 * math.pi * 31)
    ph = ring - phi + wig
    px_per_cycle = scale / NR
    contrast = np.clip((px_per_cycle - 1.5) / 4, 0, 1)
    g = 0.5 + 0.5 * np.cos(2 * np.pi * ph)
    groove_shape = np.abs(((ph % 1) - 0.5) * 2)
    loud = env('fullS', tau)  # loud passages read as rougher, brighter bands
    sheen = np.exp(-(np.sin(th - 0.75) ** 2) / 0.03) + 0.7 * np.exp(-(np.sin(th + 2.0) ** 2) / 0.05)
    sheen = sheen * (0.35 + 0.65 * r) * (0.55 + 0.7 * loud)
    hue = (r * 3.0 + th * 0.15)
    rainbow = np.stack([0.5 + 0.5 * np.cos(2 * np.pi * (hue + k)) for k in (0, 0.33, 0.66)], -1)
    base = 0.018 + 0.03 * mix(0.5, g, contrast)[..., None]
    tint = mix(np.ones(3), glow, 0.5)
    col = base + sheen[..., None] * (0.22 + 0.25 * contrast * groove_shape)[..., None] * (0.55 + 0.45 * rainbow) * tint
    # beat glow on the groove currently under the needle
    bnow = env('bass', np.array([t]))[0]
    col += (glow * 0.25 * bnow) * np.exp(-((r - math.hypot(*T)) * scale / 40) ** 2)[..., None] * contrast[..., None]
    smooth_area = (r < R_IN) | (r > R_OUT)
    col = np.where(smooth_area[..., None], 0.02 + sheen[..., None] * 0.18 * np.array([1, 1, 1.05]), col)
    lab = r < R_LAB
    if lab.any():
        lx = (r * np.cos(th - rot)) / R_LAB; ly = (r * np.sin(th - rot)) / R_LAB
        li = np.clip(((lx + 1) / 2 * 511).astype(int), 0, 511); lj = np.clip(((ly + 1) / 2 * 511).astype(int), 0, 511)
        lc = LABEL[lj, li] * (0.85 + 0.15 * np.clip(sheen[..., None], 0, 1))
        col = np.where(lab[..., None], lc, col)
    col = np.where((r < 0.02)[..., None], 0.0, col)
    edge = smooth((1.0 - r) * scale / 1.5)
    bgv = 0.06 + 0.04 * np.exp(-((xs_ - W * 0.3) ** 2 + (ys_ - H * 0.2) ** 2) / (2 * (W * 0.5) ** 2))
    bg = bgv[..., None] * mix(np.array([0.55, 0.42, 0.36]), fog * 4, 0.4)
    col = bg + (col - bg) * edge[..., None]
    img = np.clip(col, 0, 1)
    if zoom < 6:
        im = Image.fromarray((img * 255).astype(np.uint8))
        d = ImageDraw.Draw(im, 'RGBA')
        def sp(p): return ((p[0] - c[0]) * scale + W / 2, (p[1] - c[1]) * scale + H / 2)
        rr = math.hypot(*T); na = TGT_A + 0.22
        head = np.array([rr * math.cos(na), rr * math.sin(na)])
        pivot = np.array([1.05, -1.05])
        a = max(0.0, 1 - zoom / 6)
        wdt = max(2, int(0.022 * scale))
        d.line([sp(pivot), sp(head + (pivot - head) * 0.18)], fill=(200, 200, 205, int(255 * a)), width=wdt)
        hp = sp(head); hs = 0.03 * scale
        d.polygon([(hp[0] - hs, hp[1] - hs * .4), (hp[0] + hs * .3, hp[1] - hs * .9), (hp[0] + hs, hp[1] + hs * .3), (hp[0] - hs * .2, hp[1] + hs * .8)], fill=(150, 150, 158, int(255 * a)))
        pp = sp(pivot); pr = 0.09 * scale
        d.ellipse([pp[0] - pr, pp[1] - pr, pp[0] + pr, pp[1] + pr], fill=(120, 120, 128, int(255 * a)))
        img = np.asarray(im).astype(np.float32) / 255
    return img

# ---------- inside the groove ----------
RIM = 0.9
FOV = 1.15
PX = (xs_ - W / 2) / (W / 2) * FOV
PY = -(ys_ - H / 2) / (W / 2) * FOV
rng = np.random.default_rng(3)
DUST = rng.uniform([-1.5, -0.8, 0], [1.5, 1.2, 60], (220, 3))
STARS = rng.uniform([-1.6, 0.05], [1.6, 0.9], (180, 2)); STAR_PH = rng.uniform(0, 1, 180)

def wig(ch, tau):
    # bass -> big slow swings, mids (voice/synth) -> ripples, highs -> fine fuzz; per stereo channel
    b = env('bass' + ch, tau); m = env('mid' + ch, tau); h = env('high' + ch, tau)
    ph = 1.7 if ch == 'R' else 0.0
    return (0.17 * b * np.sin(2 * np.pi * 3.0 * tau + ph)
            + 0.07 * m * np.sin(2 * np.pi * 11.0 * tau + 1.3 + ph)
            + 0.025 * h * np.sin(2 * np.pi * 47.0 * tau + ph))

def widthf(tau): return 0.85 + 0.35 * np.clip(env('fullS', tau), 0, 1.2)

def solve(a, b, cc):
    if abs(a) < 1e-9:
        z = -cc / np.where(np.abs(b) < 1e-9, 1e-9, b)
        return np.where(z > 0, z, np.inf)
    disc = b * b - 4 * a * cc
    sq = np.sqrt(np.maximum(disc, 0))
    z1 = (-b - sq) / (2 * a); z2 = (-b + sq) / (2 * a)
    lo = np.minimum(z1, z2); hi = np.maximum(z1, z2)
    z = np.where(lo > 1e-4, lo, np.where(hi > 1e-4, hi, np.inf))
    return np.where(disc >= 0, z, np.inf)

def hash2(a, b):
    v = np.sin(a * 127.1 + b * 311.7) * 43758.5453
    return v - np.floor(v)

def groove_frame(t):
    glow, side, fog = palette(t)
    i, s = sect(t)
    V = speed(t); en = s[5]
    kick = env('bass', np.array([t]))[0]
    past = BEATS[BEATS <= t + 1e-6]
    kick_now = math.exp(-(t - past[-1]) * 6) * BEAT_STR[len(past) - 1] if len(past) else 0
    sn = SNARES[SNARES <= t + 1e-6]
    snare_now = math.exp(-(t - sn[-1]) * 9) if len(sn) else 0
    sway = (0.08 + 0.08 * en) * math.sin(t * 1.3); bob = 0.06 * math.sin(t * 2.1) - 0.05 * kick_now
    roll = (0.04 + 0.06 * en) * math.sin(t * 0.7) + 0.015 * snare_now * math.sin(t * 40)
    pitch = 0.10 + 0.05 * math.sin(t * 0.9)
    cr, sr = math.cos(roll), math.sin(roll)
    dx = PX * cr - PY * sr
    dy = PX * sr + PY * cr - pitch
    curv = (0.004 + 0.006 * en) * math.sin(t * 0.23 + 1)
    tt = np.array([t])
    ox = ((wig('L', tt) + wig('R', tt)) / 2)[0] + sway; oy = bob
    sw0 = widthf(tt)[0]
    zr = solve(curv, -(dx - sw0 * dy), sw0 * (1 + oy)); zl = solve(curv, -(dx + sw0 * dy), -sw0 * (1 + oy))
    for _ in range(2):
        tr = t + np.minimum(zr, 80) / V; tl = t + np.minimum(zl, 80) / V
        sr_, sl_ = widthf(tr), widthf(tl)
        wr = wig('R', tr) - ox; wl = wig('L', tl) - ox
        zr = solve(curv, -(dx - sr_ * dy), wr + sr_ * (1 + oy))
        zl = solve(curv, -(dx + sl_ * dy), wl - sl_ * (1 + oy))
    right = zr < zl
    z = np.minimum(zr, zl)
    yh = dy * z + oy
    over = yh > RIM
    zland = np.where(dy > 1e-3, (RIM - oy) / np.maximum(dy, 1e-3), np.inf)
    hitland = over & np.isfinite(zland) & (zland < 120)
    z = np.where(over, zland, z)
    z = np.where(np.isfinite(z), z, 200)
    tau = t + z / V
    xs = dx * z
    ch_is_R = right
    # slopes for normals (numeric derivative of the wall offset)
    dwR = (wig('R', tau + 0.004) - wig('R', tau - 0.004)) / 0.008 / V
    dwL = (wig('L', tau + 0.004) - wig('L', tau - 0.004)) / 0.008 / V
    sw = widthf(tau)
    nr = np.stack([-np.ones_like(z), sw, 2 * curv * z + dwR], -1)
    nl = np.stack([np.ones_like(z), sw, -(2 * curv * z + dwL)], -1)
    n = np.where(right[..., None], nr, nl)
    n = np.where(hitland[..., None], np.array([0, 1.0, 0]), n)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    d = np.stack([dx, dy, np.ones_like(dx)], -1); d /= np.linalg.norm(d, axis=-1, keepdims=True)
    rf = d - 2 * (d * n).sum(-1, keepdims=True) * n
    ahead = np.exp(-((rf[..., 0] - curv * 20) ** 2 + (rf[..., 1] - 0.15) ** 2) / 0.05) * (1.2 + 1.8 * kick_now)
    sidel = np.exp(-((np.abs(rf[..., 0]) - 0.8) ** 2) / 0.04) * np.clip(rf[..., 1] + 0.3, 0, 1) * (0.6 + 1.2 * snare_now)
    fres = 0.04 + 0.96 * (1 - np.abs((d * n).sum(-1))) ** 4
    col = (ahead[..., None] * glow + 0.5 * sidel[..., None] * side) * (0.25 + fres[..., None])
    stri = 0.5 + 0.5 * np.sin(yh * 90 + xs * 13) * np.exp(-z / 6)
    col *= (0.75 + 0.35 * stri)[..., None]
    col += 0.012
    near = np.exp(-z / 30)[..., None]
    wall = (~hitland)[..., None]
    # MID band (voice / synths): two etched lanes along each wall glow with that channel's mids
    mid = np.where(right, env('midR', tau), env('midL', tau))
    lanes = np.exp(-((yh + 0.35) ** 2) / 0.0025) + 0.7 * np.exp(-((yh - 0.3) ** 2) / 0.0018)
    col += (lanes * np.clip(mid - 0.15, 0, 1.5) ** 1.5 * 1.3)[..., None] * side * near * wall
    # BASS: light rings that reach the camera exactly on each kick, size = kick strength
    pulse = np.zeros_like(z)
    for tb, st in zip(BEATS, BEAT_STR):
        dz = (tb - t) * V
        if -2 < dz < 70 and st > 0.05:
            pulse += st * np.exp(-((z - dz) ** 2) / (0.12 + 0.1 * st))
    col += pulse[..., None] * glow * 1.5 * wall
    # bass also makes the whole wall breathe
    col *= (0.8 + 0.5 * env('bass', tau))[..., None]
    # HIGHS (hats, shakers): glints scattered on the walls
    hi_ = env('high', tau)
    cell = hash2(np.floor(z * 30), np.floor(yh * 50) + right * 7.0)
    glint = (cell > 1 - 0.035 * np.clip(hi_, 0, 1.3)) * np.exp(-z / 10) * smooth((z - 2.5) / 2)
    col += (glint * 1.2)[..., None] * mix(np.ones(3), glow, 0.3) * wall
    # land: neighbouring grooves receding as stripes
    lx = (xs - curv * z * z) / 3.8
    ridge = np.exp(-(((lx % 1) - 0.5) ** 2) / 0.003)
    landcol = (0.03 + ridge[..., None] * 0.5 * glow * np.exp(-z / 25)[..., None] * (0.6 + 0.8 * kick_now)) * (0.6 + 0.4 * stri[..., None])
    col = np.where(hitland[..., None], landcol, col)
    sky = (over & ~hitland)
    skyc = fog * (0.6 + 1.5 * snare_now) + glow * 0.25 * np.exp(-(dx ** 2 + (dy - 0.3) ** 2) / 0.15)[..., None]
    col = np.where(sky[..., None], skyc, col)
    f = 1 - np.exp(-z / 22)
    vp = np.exp(-((dx - curv * 18) ** 2 + (dy + 0.05) ** 2) / 0.02)
    fogc = fog + glow * vp[..., None] * (0.4 + 0.8 * kick_now)
    col = col * (1 - f[..., None]) + fogc * f[..., None]
    # particles: dust motes (brighter with highs) + stars above the rim (twinkle with highs)
    hnow = env('high', tt)[0]
    dust = np.zeros((H, W), np.float32)
    D = dist(t)
    def splat(cx, cy, rad, a):
        if -20 < cx < W + 20 and -20 < cy < H + 20:
            x1, x2 = int(max(0, cx - 3 * rad)), int(min(W, cx + 3 * rad + 1))
            y1, y2 = int(max(0, cy - 3 * rad)), int(min(H, cy + 3 * rad + 1))
            if x2 > x1 and y2 > y1:
                gx = xs_[y1:y2, x1:x2] - cx; gy = ys_[y1:y2, x1:x2] - cy
                dust[y1:y2, x1:x2] += np.exp(-(gx * gx + gy * gy) / (2 * rad * rad)) * a
    def proj(x, y, zz):
        sx_, sy_ = x / zz, y / zz + pitch
        px = sx_ * cr + sy_ * sr; py = -sx_ * sr + sy_ * cr
        return px / FOV * (W / 2) + W / 2, -py / FOV * (W / 2) + H / 2
    for (x0, y0, z0) in DUST:
        zz = (z0 - D) % 60 + 0.4
        cx, cy = proj(x0 + 0.1 * math.sin(t + x0 * 5) - sway, y0 - oy, zz)
        splat(cx, cy, max(1.0, 9 / zz), min(1, 3 / zz) * (0.35 + 0.5 * hnow))
    img = col + dust[..., None] * (0.6 * glow + 0.4)
    starl = np.zeros((H, W), np.float32)
    dust[:] = 0
    for (sx, sy), p in zip(STARS, STAR_PH):
        cx = (sx * cr + (sy + pitch) * sr) / FOV * (W / 2) + W / 2
        cy = -(-sx * sr + (sy + pitch) * cr) / FOV * (W / 2) + H / 2
        tw = 0.3 + 0.7 * hnow * (0.5 + 0.5 * math.sin(t * 9 + p * 40))
        splat(cx, cy, 1.3, tw * 0.6)
    img = img + (dust * sky)[..., None] * mix(np.ones(3), side, 0.4)
    return np.clip(img, 0, 1)

def tonemap(img): return 1 - np.exp(-img * 2.0)

def rec_zoom(t, s, i):
    t0, t1 = s[0], s[1]
    L1 = math.log(1500)
    if i == 0:  # intro: full record -> dive
        k = (t - t0) / (t1 - t0)
        return math.exp(L1 * smooth(k) ** 1.6)
    if i == len(SECT) - 1:  # outro: pull out to the full record
        k = min(1, (t - t0) / 9.0)
        return math.exp(L1 * (1 - smooth(k)) ** 1.6)
    # mid-song breaks: pull out to a hovering view of the grooves, then dive again
    hold = math.log(18 if (t1 - t0) < 8 else 4)
    up = min(2.0, (t1 - t0) * 0.3); down = min(2.5, (t1 - t0) * 0.35)
    if t < t0 + up: return math.exp(mix(L1, hold, smooth((t - t0) / up)))
    if t > t1 - down: return math.exp(mix(hold, L1, smooth((t - (t1 - down)) / down) ** 1.6))
    return math.exp(hold + 0.25 * math.sin((t - t0) * 0.5))

def frame(n):
    t = n / FPS
    i, s = sect(t)
    if s[2] == 'rec':
        img = record_frame(t, rec_zoom(t, s, i))
        if i < len(SECT) - 1:
            img = mix(img, np.ones(3), smooth((t - (s[1] - 0.35)) / 0.35))
        if i > 0:
            img = mix(img, np.ones(3), 1 - smooth((t - s[0]) / 0.5))
    else:
        img = tonemap(groove_frame(t))
        prev_rec = i > 0 and SECT[i - 1][2] == 'rec'
        img = mix(img, np.ones(3), (1 - smooth((t - s[0]) / (0.45 if prev_rec else 0.3))) * (0.95 if prev_rec else 0.6))
        if i + 1 < len(SECT) and SECT[i + 1][2] == 'rec':
            img = mix(img, np.ones(3), smooth((t - (s[1] - 0.35)) / 0.35))
    img = img * VIG
    img = img * min(1, t / 1.0) * min(1, max(0, DUR - t) / 2.0)
    g = np.random.default_rng(n).normal(0, 0.012, (H, W, 1))
    return (np.clip(img + g, 0, 1) * 255).astype(np.uint8)

if __name__ == '__main__':
    os.makedirs(os.path.join(WD, 'out'), exist_ok=True)
    if sys.argv[2] == 'stills':
        for ts in sys.argv[3:]:
            Image.fromarray(frame(int(float(ts) * FPS))).save(os.path.join(WD, 'out', f'still_{ts}.png'))
    elif sys.argv[2] == 'info':
        print('frames', NF, 'fps', FPS, 'size', W, H)
    else:
        start, end, outp = int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
        end = min(end, NF)
        ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                               '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', outp], stdin=subprocess.PIPE)
        with Pool(2) as p:
            for k, fr in enumerate(p.imap(frame, range(start, end), chunksize=4)):
                ff.stdin.write(fr.tobytes())
                if k % 150 == 0: print(start + k, flush=True)
        ff.stdin.close(); ff.wait(); print('done', flush=True)
