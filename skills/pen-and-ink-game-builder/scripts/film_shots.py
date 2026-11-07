#!/usr/bin/env python3
"""Film trailer shots from inside the game: one MP4 per shot, rendered frame by frame (no dropped frames, ever).

  python3 film_shots.py dist/my-game.html promo/director.js                 -> promo/shots/<shot>.mp4 + <shot>.json
  python3 film_shots.py dist/my-game.html promo/director.js --stills        -> first/middle/last frame of each shot as JPEG
  python3 film_shots.py dist/my-game.html promo/director.js --only s03-door,s04-turn --size 1280x720

The director file defines window.__tr (start from assets/promo/director_template.js). It runs inside the game's
scope through window.__ev, which a promo build has; if the html lacks it, a <slug>-promo.html copy with the hook is
written next to it. Frames are JPEG q92 screenshots piped into ffmpeg (libx264 crf 18, 30 fps, yuv420p); each shot is
written to a .part.mp4 first and renamed only when ffmpeg succeeds, so a half-rendered shot never looks finished.
<shot>.json holds per-frame player facts (position, up, grounded) for render_audio.py to time footsteps and flips.
Rendering is software WebGL: expect roughly 1-4 frames per second at 1080p.
"""
import sys
sys.dont_write_bytecode = True
import argparse, json, os, subprocess, time
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pen_ink_common import GL_ARGS, promo_copy

ENC = ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', '30', '-video_track_timescale', '15360']


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('html'); ap.add_argument('director')
    ap.add_argument('--out', help='folder for the shot files (default: shots/ next to the director file)')
    ap.add_argument('--size', default='1920x1080')
    ap.add_argument('--only', help='comma-separated shot names to (re)render')
    ap.add_argument('--stills', action='store_true', help='only save first/middle/last frames as JPEG (fast check)')
    a = ap.parse_args()
    W, H = map(int, a.size.lower().split('x'))
    out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.director)), 'shots')
    os.makedirs(out, exist_ok=True)
    page = promo_copy(a.html)
    only = set(a.only.split(',')) if a.only else None
    T0 = time.time()
    log = lambda *m: print('%7.1fs' % (time.time() - T0), *m, file=sys.stderr, flush=True)
    errs = []
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, args=GL_ARGS)
        pg = b.new_page(viewport={'width': W, 'height': H}); pg.set_default_timeout(600000)
        pg.on('pageerror', lambda e: errs.append(str(e)) or log('PAGE ERROR', e))
        pg.on('console', lambda m: m.type == 'error' and (errs.append(m.text) or log('CONSOLE', m.text[:300])))
        pg.add_init_script('window.requestAnimationFrame = () => 0;')
        pg.goto('file://' + os.path.abspath(page))
        pg.wait_for_function('window.__ev && window.__game', polling=200, timeout=60000)
        pg.wait_for_timeout(1500)  # fonts and the loading cover
        pg.evaluate('s => __ev(s)', open(a.director, encoding='utf-8').read())
        names = pg.evaluate('__tr.names()')
        timeline, start = [], 0.0
        for si, nm in enumerate(names):
            name, n = nm.rsplit(':', 1); n = int(n)
            timeline.append({'name': name, 'frames': n, 'start': round(start, 3)}); start += n / 30
            if only and name not in only:
                continue
            pg.evaluate(f'__tr.prep({si})')
            if a.stills:
                keep = {0, n // 2, n - 1}
                for i in range(n):
                    pg.evaluate(f'__tr.noRender = {str(i not in keep).lower()}; __tr.frame({si},{i})')
                    if i in keep:
                        pg.screenshot(path=os.path.join(out, f'{name}-{i:03d}.jpg'), type='jpeg', quality=90)
                pg.evaluate('__tr.noRender = false')
                log(name, 'stills'); continue
            part, final = os.path.join(out, f'{name}.part.mp4'), os.path.join(out, f'{name}.mp4')
            ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'image2pipe', '-framerate', '30', '-c:v', 'mjpeg', '-i', '-'] + ENC + [part], stdin=subprocess.PIPE)
            info = []
            for i in range(n):
                pg.evaluate(f'__tr.frame({si},{i})')
                ff.stdin.write(pg.screenshot(type='jpeg', quality=92))
                info.append(json.loads(pg.evaluate('__tr.info()')))
                if i % 30 == 0: log('  ', name, f'{i}/{n}')
            ff.stdin.close(); rc = ff.wait()
            if rc == 0: os.replace(part, final)
            json.dump(info, open(os.path.join(out, f'{name}.json'), 'w'))
            log(name, f'{n} frames', 'ok' if rc == 0 else f'ffmpeg failed ({rc})')
        b.close()
    json.dump(timeline, open(os.path.join(out, 'shots.json'), 'w'), indent=1)
    log(f'shots in {out}; order and lengths in shots.json')
    if errs:
        print('ERRORS during filming:\n  ' + '\n  '.join(dict.fromkeys(errs)), file=sys.stderr); sys.exit(1)


if __name__ == '__main__':
    main()
