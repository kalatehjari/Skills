"""Usage: python3 song_info.py <song.mp3> <out_dir>
Prints title/artist/duration and any embedded lyrics (ID3 'lyrics' tags, common for Suno exports),
and writes <out_dir>/structure.png: a mel spectrogram (5 rows x 60 s, 2 s grid) plus a self-similarity
matrix. Read both images to find where sections start and which sections repeat (chorus = off-diagonal
stripes). Speech-recognition models are usually unreachable in this sandbox, so this is how lyrics get placed."""
import sys, json, subprocess, os
import numpy as np
song, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
tags = json.loads(subprocess.run(['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration:format_tags', '-of', 'json', song], capture_output=True, text=True).stdout)['format']
print('duration', tags.get('duration'))
for k, v in tags.get('tags', {}).items(): print(f'--- {k} ---\n{v}')
import librosa, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
y, sr = librosa.load(song, sr=22050, mono=True)
M = librosa.power_to_db(librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmax=8000), ref=np.max)
t = librosa.frames_to_time(np.arange(M.shape[1]), sr=sr); L = 60; rows = int(np.ceil(t[-1] / L))
fig, axs = plt.subplots(rows, 1, figsize=(24, 3.6 * rows))
for k, ax in enumerate(np.atleast_1d(axs)):
    m = (t >= k * L) & (t < (k + 1) * L)
    ax.imshow(M[:, m], origin='lower', aspect='auto', extent=[k * L, min((k + 1) * L, t[-1]), 0, 128], cmap='magma')
    ax.set_xticks(np.arange(k * L, (k + 1) * L + 1, 2)); ax.grid(axis='x', alpha=.3)
plt.tight_layout(); plt.savefig(f'{out}/structure.png', dpi=60); plt.close()
C = librosa.feature.chroma_cqt(y=y, sr=sr); F = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
X = np.vstack([librosa.util.normalize(C), librosa.util.normalize(F)]); hop = int(0.5 * sr / 512); n = X.shape[1] // hop
Xd = np.stack([X[:, i * hop:(i + 1) * hop].mean(1) for i in range(n)], 1)
R = librosa.segment.recurrence_matrix(Xd, mode='affinity', width=4, sym=True)
plt.figure(figsize=(12, 12)); plt.imshow(R, cmap='gray_r', extent=[0, n / 2, n / 2, 0]); plt.xticks(np.arange(0, n / 2, 10)); plt.yticks(np.arange(0, n / 2, 10)); plt.grid(alpha=.3)
plt.savefig(f'{out}/similarity.png', dpi=70)
print('wrote', f'{out}/structure.png', f'{out}/similarity.png')
