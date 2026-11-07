#!/usr/bin/env python3
"""Build a pen-and-ink game into ONE self-contained HTML file (three.js, fonts and all code inlined; no network needed).

  python3 build_html.py path/to/my-game              -> path/to/my-game/dist/<slug>.html
  python3 build_html.py path/to/my-game --promo      -> dist/<slug>-promo.html (adds window.__ev for trailer tools)

Order: src/00_head.html, then every src/*.js in name order, wrapped in one function scope (so nothing leaks onto
window except what the code puts there on purpose). The JS is syntax-checked with `node --check` when node exists,
which catches a missing bracket before a browser ever loads the page.
"""
import sys
sys.dont_write_bytecode = True
import argparse, base64, json, os, shutil, subprocess, tempfile

FONTS = [('IM Fell English', 'normal', 'im-fell-english-latin-400-normal.woff2'),
         ('IM Fell English', 'italic', 'im-fell-english-latin-400-italic.woff2'),
         ('IM Fell English SC', 'normal', 'im-fell-english-sc-latin-400-normal.woff2'),
         ('Special Elite', 'normal', 'special-elite-latin-400-normal.woff2')]
END = '\n})();\n</script>\n</body>\n</html>\n'   # film_shots.py looks for this exact ending to add its hook


def slug_of(game):
    p = os.path.join(game, 'game.json')
    if os.path.exists(p):
        return json.load(open(p)).get('slug') or os.path.basename(os.path.abspath(game))
    return os.path.basename(os.path.abspath(game))


def build(game, out=None, promo=False, check=True):
    src = os.path.join(game, 'src')
    head = open(os.path.join(src, '00_head.html'), encoding='utf-8').read()
    warn = []
    css = ''
    for fam, sty, fn in FONTS:
        p = os.path.join(game, 'vendor', 'fonts', fn)
        if os.path.exists(p):
            css += '@font-face{font-family:"%s";font-style:%s;font-weight:400;font-display:swap;src:url(data:font/woff2;base64,%s) format("woff2")}\n' % (
                fam, sty, base64.b64encode(open(p, 'rb').read()).decode())
        else:
            warn.append(f'font missing ({fn}): the page falls back to Georgia/Courier. Run get_deps.py.')
    head = head.replace('<!--FONTS-->', '<style id="fonts">\n' + css + '</style>')
    tp = os.path.join(game, 'vendor', 'three.min.js')
    if not os.path.exists(tp):
        raise SystemExit(f'{tp} is missing. Run: python3 scripts/get_deps.py {game}')
    three = open(tp, encoding='utf-8').read()
    js = ''
    for f in sorted(os.listdir(src)):
        if f.endswith('.js'):
            js += f'\n/* ---- {f} ---- */\n' + open(os.path.join(src, f), encoding='utf-8').read()
    if check and shutil.which('node'):
        with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t:
            t.write('(function(){\n' + js + '\n})();\n'); tmp = t.name
        r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)
        os.unlink(tmp)
        if r.returncode:
            msg = r.stderr.strip().replace(tmp, '<game js>')
            raise SystemExit('syntax error in the game code (line numbers count from the first src/*.js file, +1):\n' + msg)
    hook = '\nwindow.__ev = s => eval(s); // promo build only: lets trailer scripts run inside the game scope' if promo else ''
    html = head + '<script>\n' + three + '\n</script>\n<script>\n(function(){\n' + js + hook + END
    slug = slug_of(game)
    out = out or os.path.join(game, 'dist', f'{slug}-promo.html' if promo else f'{slug}.html')
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    open(out, 'w', encoding='utf-8').write(html)
    return out, len(html.encode('utf-8')), warn


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('game_dir')
    ap.add_argument('-o', '--out', help='output file (default: <game>/dist/<slug>.html)')
    ap.add_argument('--promo', action='store_true', help='add the window.__ev hook used by film_shots.py and render_audio.py')
    ap.add_argument('--no-check', action='store_true', help='skip the node syntax check')
    a = ap.parse_args()
    out, size, warn = build(a.game_dir, a.out, a.promo, not a.no_check)
    for w in warn:
        print('warning: ' + w, file=sys.stderr)
    print(f'built {out}  {size / 1e6:.2f} MB', file=sys.stderr)


if __name__ == '__main__':
    main()
