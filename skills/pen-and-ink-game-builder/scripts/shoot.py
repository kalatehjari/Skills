#!/usr/bin/env python3
"""Screenshot a built pen-and-ink game headlessly, and fail loudly on any JavaScript error.

  python3 shoot.py dist/my-game.html                      -> dist/shots/title.jpg, level-1.jpg, level-2.jpg ...
  python3 shoot.py dist/my-game.html --shots shots.json   -> your own camera positions
  python3 shoot.py dist/my-game.html --size 1920x1080 --png

shots.json is a list of {"name", "level", "pos": [x,y,z], "yaw", "pitch", "steps", "js"}; every key but name is
optional. "level": 0 is the title screen. "js" runs inside the page after placing the player (window.__game is there).
The game runs in software WebGL (SwiftShader), frame by frame through window.__game.step(), so shots are repeatable.
Exit status 1 if the page threw, logged an error, or the game caught one (window.__game.ERRS).
"""
import sys
sys.dont_write_bytecode = True
import argparse, json, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
from _pen_ink_common import open_game

def default_shots(pg):
    n = pg.evaluate('() => window.__game.LEVELS.length - 1')
    return [{'name': 'title', 'level': 0, 'steps': 75}] + [{'name': f'level-{i}', 'level': i, 'steps': 45} for i in range(1, n + 1)]


def take(pg, s):
    lvl = s.get('level', 1)
    if lvl == 0:
        pg.evaluate('() => window.__game.GAME.titleLevel()')
    else:
        pg.evaluate(f'() => window.__game.play({lvl})')
        # skip the fade-in a level start plays, so short shots are not dark
        pg.evaluate("() => { const g = window.__game; g.UI.show(null); g.GAME.fadeTo(0, 0); g.GAME.toast = () => {}; g.GAME.hint = () => {}; g.GAME.caught = () => {}; document.getElementById('toast').classList.remove('show'); for (const k in g.IN.keys) g.IN.keys[k] = false; }")
    if 'pos' in s:
        x, y, z = s['pos']
        pg.evaluate(f'() => window.__game.tp({x}, {y}, {z})')
    if 'yaw' in s or 'pitch' in s:
        pg.evaluate(f"() => window.__game.look({s.get('yaw', 0)}, {s.get('pitch', 0)})")
    if s.get('js'):
        pg.evaluate('code => (0, eval)(code)', s['js'])
    return pg.evaluate(f"() => window.__game.step({int(s.get('steps', 45))})")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('html', help='the built game (dist/<slug>.html)')
    ap.add_argument('--shots', help='JSON list of shots (default: title + every level at its spawn)')
    ap.add_argument('--out', help='folder for the images (default: <game>/shots/)')
    ap.add_argument('--size', default='1280x720')
    ap.add_argument('--quality', type=int, default=1, help='0 low (phone), 1 medium, 2 high')
    ap.add_argument('--png', action='store_true', help='PNG instead of JPEG (q92)')
    a = ap.parse_args()
    w, h = map(int, a.size.lower().split('x'))
    d = os.path.dirname(os.path.abspath(a.html))
    out = a.out or os.path.join(os.path.dirname(d) if os.path.basename(d) == 'dist' else d, 'shots')  # never inside dist/, the folder you ship
    os.makedirs(out, exist_ok=True)
    t0 = time.time(); report = []
    with sync_playwright() as p:
        b, pg, errs = open_game(p, a.html, w, h, a.quality)
        shots = json.load(open(a.shots)) if a.shots else default_shots(pg)
        for s in shots:
            st = take(pg, s)
            fn = os.path.join(out, s['name'] + ('.png' if a.png else '.jpg'))
            pg.screenshot(path=fn, type='png' if a.png else 'jpeg', **({} if a.png else {'quality': 92}))
            errs += [f'game: {e}' for e in st.get('errs', []) if f'game: {e}' not in errs]
            report.append({'name': s['name'], 'file': fn, 'state': st})
            print(f"{s['name']:>16}  level {st.get('idx')}  {st.get('state')}  pos {st.get('pos')}  up {st.get('up')}", file=sys.stderr)
        b.close()
    json.dump(report, open(os.path.join(out, 'shots.json'), 'w'), indent=1)
    print(f'{len(report)} shot(s) in {out}  ({time.time() - t0:.0f}s)', file=sys.stderr)
    if errs:
        print('ERRORS:\n  ' + '\n  '.join(dict.fromkeys(errs)), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
