# Song analysis for the vinyl groove visualiser.
# usage: python3 analyze.py <song.(mp3|wav)> <workdir>
# writes <workdir>/analysis.npz (band envelopes per stereo channel, beats, snares, section bounds),
#        <workdir>/structure.png (look at it!), <workdir>/sections.json (a suggested edit list).
import sys, os, json
import numpy as np, librosa
from scipy.signal import butter, sosfiltfilt
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt

song, wd = sys.argv[1], sys.argv[2]
os.makedirs(wd, exist_ok=True)
SR = 22050
y, _ = librosa.load(song, sr=SR, mono=False)
if y.ndim == 1: y = np.vstack([y, y])
L, R = y[0], y[1]
m = (L + R) / 2
dur = len(m) / SR
tempo, beats = librosa.beat.beat_track(y=m, sr=SR, units='time', tightness=200)
print('tempo', np.round(tempo, 1), 'beats', len(beats), 'dur', round(dur, 1))

RATE = 200
hop = SR // RATE
def band(x, lo, hi):
    if lo is None: sos = butter(4, hi, 'low', fs=SR, output='sos')
    elif hi is None: sos = butter(4, lo, 'high', fs=SR, output='sos')
    else: sos = butter(4, [lo, hi], 'band', fs=SR, output='sos')
    return sosfiltfilt(sos, x)
def envf(x):
    n = len(x) // hop
    return np.sqrt((x[: n * hop] ** 2).reshape(n, hop).mean(1))
bands = {}
for name, lo, hi in [('bass', None, 150), ('mid', 300, 3000), ('high', 5000, None)]:
    for ch, sig in (('L', L), ('R', R)):
        bands[name + ch] = envf(band(sig, lo, hi))
bands['side'] = envf(L - R); bands['full'] = envf(m)
for k in bands:
    bands[k] = bands[k] / max(1e-9, np.percentile(bands[k], 99.5))

def onsets(x, lo, hi, delta):
    oenv = librosa.onset.onset_strength(y=band(x, lo, hi), sr=SR, hop_length=512)
    return librosa.onset.onset_detect(onset_envelope=oenv, sr=SR, hop_length=512, units='time', delta=delta)
snares = onsets(m, 1500, 5000, 0.3)

# section boundaries from timbre + harmony novelty
mf = librosa.feature.mfcc(y=m, sr=SR, hop_length=2048, n_mfcc=13)
ch = librosa.feature.chroma_cqt(y=m, sr=SR, hop_length=2048)
feat = np.vstack([librosa.util.normalize(mf, axis=1), ch])
k = int(np.clip(dur / 26, 4, 16))
bt = librosa.frames_to_time(librosa.segment.agglomerative(feat, k), sr=SR, hop_length=2048)
bt = sorted(set([0.0] + [round(float(b), 1) for b in bt if b > 2 and b < dur - 2]))
# merge slivers shorter than 4 s into the previous section
merged = [bt[0]]
for b in bt[1:]:
    if b - merged[-1] >= 4: merged.append(b)
if dur - merged[-1] < 4 and len(merged) > 1: merged.pop()
bt = merged
print('section bounds', bt)
np.savez(os.path.join(wd, 'analysis.npz'), rate=RATE, dur=dur, beats=beats, snares=snares, bounds=bt, **bands)

# suggested sections: quiet stretches -> 'rec' (hover over the record), loud -> 'grv' (inside the groove)
edges = bt + [dur]
fullS = np.convolve(bands['full'], np.ones(RATE) / RATE, 'same')
energies = [float(fullS[int(a * RATE):max(int(a * RATE) + 1, int(b * RATE))].mean()) for a, b in zip(edges[:-1], edges[1:])]
hi_e, lo_e = max(energies), min(energies)
pal_cycle = ['indigo', 'violet', 'amber', 'emerald', 'gold', 'crimson']
sections, pi = [], 0
for j, (a, b) in enumerate(zip(edges[:-1], edges[1:])):
    e = (energies[j] - lo_e) / max(1e-6, hi_e - lo_e)
    if j == 0 or j == len(energies) - 1: mode = 'rec'                  # intro dive / outro pull-out
    elif e < 0.35 and (b - a) > 4: mode = 'rec'                         # breakdowns
    else: mode = 'grv'
    pal = 'ice' if (mode == 'rec' and 0 < j < len(energies) - 1) else pal_cycle[pi % len(pal_cycle)]
    if mode == 'grv': pi += 1
    sections.append([round(a, 1), round(b, 1), mode, pal, round(5 + 6 * e, 1) if mode == 'grv' else 0, round(e, 2) if mode == 'grv' else 0])
json.dump({'size': [1280, 720], 'fps': 30, 'sections': sections}, open(os.path.join(wd, 'sections.json'), 'w'), indent=1)
for s in sections: print(s)

fig, ax = plt.subplots(5, 1, figsize=(22, 12), sharex=True)
tt = np.arange(len(bands['bassL'])) / RATE
for a, key in zip(ax, ['bassL', 'midL', 'highL', 'side', 'full']):
    a.plot(tt, bands[key], lw=0.4); a.set_ylabel(key)
    for b in bt: a.axvline(b, color='r')
ax[-1].set_xticks(np.arange(0, dur, 10))
plt.tight_layout(); plt.savefig(os.path.join(wd, 'structure.png'), dpi=60)
