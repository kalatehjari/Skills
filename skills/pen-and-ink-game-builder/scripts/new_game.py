#!/usr/bin/env python3
"""Start a new pen-and-ink game from the starter kit: a playable three-level game you then reshape.

  python3 new_game.py "The Quiet Stair"                    -> ./the-quiet-stair/ (src, vendor, dist/the-quiet-stair.html)
  python3 new_game.py "The Quiet Stair" --dir games/stair  -> games/stair/
  python3 new_game.py "X" --vendor-from other-game/vendor  -> offline: copy three.js and fonts instead of downloading

Refuses to write into a folder that already has files in it, so it never overwrites anyone's work.
"""
import sys
sys.dont_write_bytecode = True
import argparse, json, os, re, shutil, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
STARTER = os.path.join(HERE, '..', 'assets', 'starter', 'src')


def slugify(t):
    return re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-') or 'ink-game'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('title', help='the game title, shown on the title screen and the browser tab')
    ap.add_argument('--dir', help='where to create the game (default: ./<slug>)')
    ap.add_argument('--slug', help='file and save-key name (default: from the title)')
    ap.add_argument('--vendor-from', help='copy vendor files from this folder instead of downloading')
    ap.add_argument('--no-deps', action='store_true', help='do not fetch three.js and the fonts (and do not build)')
    a = ap.parse_args()
    slug = a.slug or slugify(a.title)
    game = a.dir or slug
    if os.path.exists(game) and os.listdir(game):
        raise SystemExit(f'{game} already exists and is not empty; pick another --dir')
    os.makedirs(os.path.join(game, 'src'), exist_ok=True)
    esc = a.title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    for f in sorted(os.listdir(STARTER)):
        s = open(os.path.join(STARTER, f), encoding='utf-8').read()
        s = s.replace('{{TITLE}}', esc if f.endswith('.html') else a.title).replace('{{SLUG}}', slug.replace('-', '_'))
        open(os.path.join(game, 'src', f), 'w', encoding='utf-8').write(s)
    json.dump({'title': a.title, 'slug': slug, 'three': '0.147.0'}, open(os.path.join(game, 'game.json'), 'w'), indent=2)
    print(f'created {game}/src ({len(os.listdir(STARTER))} files)', file=sys.stderr)
    if a.no_deps:
        print('next: python3 scripts/get_deps.py %s && python3 scripts/build_html.py %s' % (game, game), file=sys.stderr)
        return
    dep = [sys.executable, os.path.join(HERE, 'get_deps.py'), game] + (['--from', a.vendor_from] if a.vendor_from else [])
    if subprocess.run(dep).returncode:
        raise SystemExit('could not fetch three.js/fonts; retry get_deps.py, or pass --vendor-from')
    if subprocess.run([sys.executable, os.path.join(HERE, 'build_html.py'), game]).returncode:
        raise SystemExit('build failed')
    print(f'play: open {os.path.join(game, "dist", slug + ".html")} in a browser', file=sys.stderr)


if __name__ == '__main__':
    main()
