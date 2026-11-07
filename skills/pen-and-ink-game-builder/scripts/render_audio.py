#!/usr/bin/env python3
"""Render a trailer soundtrack offline from the game's own synthesizer, timed to the filmed shots.

  python3 render_audio.py dist/my-game.html promo/cues.js --shots promo/shots   -> promo/mix.wav (48 kHz stereo)
  python3 render_audio.py dist/my-game.html promo/cues.js --shots promo/shots --edit promo/edit.json

The cue sheet (start from assets/promo/cues_template.js) defines window.__cues(E) -> sections; inside a section's
play(a), times are seconds from that section's t0. E gives every shot's start time on the trailer timeline and the
per-frame logs film_shots.py wrote, so footsteps and gravity flips land on the picture (__snd.steps / __snd.flips).
The timeline is shots.json order with no gaps, or edit.json: {"timeline": ["s01", {"black": 14}, "s02", ...]}
(the same file finish_trailer.py reads, so sound and picture agree). Peak is normalised to -1 dBFS; loudness is
set later by finish_trailer.py.
"""
import sys
sys.dont_write_bytecode = True
import argparse, base64, json, math, os, wave
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
from _pen_ink_common import GL_ARGS, promo_copy

HERE = os.path.dirname(os.path.abspath(__file__))
FPS, SR = 30, 48000


def timeline(shots_dir, edit=None):
    """[(kind, name_or_frames, start_seconds, frames)] for every item on the trailer timeline."""
    meta = {s['name']: s['frames'] for s in json.load(open(os.path.join(shots_dir, 'shots.json')))}
    items = json.load(open(edit))['timeline'] if edit else list(meta)
    out, f = [], 0
    for it in items:
        if isinstance(it, dict):
            out.append(('black', None, f / FPS, int(it['black']))); f += int(it['black'])
        else:
            if it not in meta: raise SystemExit(f'{it} is not in {shots_dir}/shots.json')
            out.append(('shot', it, f / FPS, meta[it])); f += meta[it]
    return out, f / FPS


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('html'); ap.add_argument('cues')
    ap.add_argument('--shots', required=True, help='the folder film_shots.py wrote (shots.json + <shot>.json logs)')
    ap.add_argument('--edit', help='edit.json with the timeline (default: every shot, in order, no gaps)')
    ap.add_argument('-o', '--out', help='output WAV (default: mix.wav next to the cue sheet)')
    a = ap.parse_args()
    tl, total = timeline(a.shots, a.edit)
    E = {'fps': FPS, 'total': total, 'start': {}, 'frames': {}, 'logs': {}}
    for kind, name, t, n in tl:
        if kind == 'shot':
            E['start'][name] = round(t, 4); E['frames'][name] = n
            lp = os.path.join(a.shots, f'{name}.json')
            E['logs'][name] = json.load(open(lp)) if os.path.exists(lp) else []
    out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.cues)), 'mix.wav')
    mix = np.zeros((int(math.ceil(total * SR)) + SR, 2), np.float32)
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, args=GL_ARGS + ['--autoplay-policy=no-user-gesture-required'])
        pg = b.new_page(viewport={'width': 640, 'height': 360}); pg.set_default_timeout(600000)
        pg.on('pageerror', lambda e: print('PAGE ERROR', e, file=sys.stderr))
        pg.add_init_script('window.requestAnimationFrame = () => 0;')
        pg.goto('file://' + os.path.abspath(promo_copy(a.html)))
        pg.wait_for_function('window.__ev && window.__game', polling=200, timeout=60000)
        for js in (os.path.join(HERE, '..', 'assets', 'promo', 'offline_audio.js'), a.cues):
            pg.evaluate('s => __ev(s)', open(js, encoding='utf-8').read())
        meta = pg.evaluate('E => __cues(E).map(s => ({ t0: s.t0, dur: s.dur, cut: s.cut, fade: s.fade || 0, gain: s.gain || 1 }))', E)
        for k, s in enumerate(meta):
            b64 = pg.evaluate('async ([E, k]) => { const s = __cues(E)[k]; return await __snd.render(s.dur, s.play); }', [E, k])
            x = np.frombuffer(base64.b64decode(b64), np.float32).reshape(-1, 2).copy() * s['gain']
            if s.get('cut') is not None:
                x = x[:max(0, int(round((s['cut'] - s['t0']) * SR)))]
            fn = int(s['fade'] * SR)
            if fn and len(x) >= fn: x[-fn:] *= np.linspace(1, 0, fn, dtype=np.float32)[:, None]
            i0 = int(round(s['t0'] * SR)); x = x[:max(0, len(mix) - i0)]; mix[i0:i0 + len(x)] += x
            print(f"section {k}: t0 {s['t0']:.2f}s  {len(x) / SR:.2f}s  peak {float(np.abs(x).max()) if len(x) else 0:.3f}", file=sys.stderr)
        b.close()
    mix = mix[:int(round(total * SR))]
    pk = float(np.abs(mix).max()); mix *= 0.89 / max(pk, 1e-6)
    with wave.open(out, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(mix, -1, 1) * 32767).astype('<i2').tobytes())
    print(f'wrote {out}  {len(mix) / SR:.2f}s (timeline {total:.2f}s)', file=sys.stderr)


if __name__ == '__main__':
    main()
