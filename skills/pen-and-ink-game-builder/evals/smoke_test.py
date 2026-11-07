#!/usr/bin/env python3
"""Smoke test for pen-and-ink-game-builder: runs every script on a fresh game and checks the results.

  python3 evals/smoke_test.py            (2 to 4 minutes; downloads three.js and fonts from the npm registry)
  PEN_INK_VENDOR=/path/to/vendor python3 evals/smoke_test.py      (offline: copy them from an existing game)

Needs python3 with playwright (+ Chromium), numpy, ffmpeg/ffprobe, and node (for the build's syntax check).
Works in a temporary folder; nothing is written inside the skill.
"""
import sys
sys.dont_write_bytecode = True
import json, os, re, subprocess, tempfile, time

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = os.path.join(SKILL, 'scripts')
FILES = os.path.join(SKILL, 'evals', 'files')
ok, bad = [], []


def check(name, cond, detail=''):
    (ok if cond else bad).append(name + ('' if cond else f'  <- {detail}'))
    print(('PASS ' if cond else 'FAIL ') + name + ('' if cond else f'  ({detail})'), file=sys.stderr, flush=True)
    return cond


def run(args, timeout=900):
    r = subprocess.run([sys.executable] + args, capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout + r.stderr


def main():
    t0 = time.time()
    tmp = tempfile.mkdtemp(prefix='ink-smoke-')
    game = os.path.join(tmp, 'smoke-test')
    # 1. every script answers --help
    for f in sorted(os.listdir(S)):
        if f.endswith('.py') and not f.startswith('_'):
            rc, out = run([os.path.join(S, f), '--help'], 60)
            check(f'{f} --help', rc == 0 and 'usage' in out.lower(), out[-300:])
    # 2. a new game builds
    vend = os.environ.get('PEN_INK_VENDOR')
    rc, out = run([os.path.join(S, 'new_game.py'), 'Smoke Test', '--dir', game] + (['--vendor-from', vend] if vend else []))
    html = os.path.join(game, 'dist', 'smoke-test.html')
    if not check('new_game.py builds a playable file', rc == 0 and os.path.exists(html), out[-600:]):
        return finish(t0)
    s = open(html, encoding='utf-8').read()
    check('placeholders filled, fonts and three.js inlined', '{{' not in s and 'smoke_test_' in s and '@font-face' in s and 'REVISION' in s and len(s) > 900_000)
    check('new_game.py refuses a non-empty folder', run([os.path.join(S, 'new_game.py'), 'X', '--dir', game, '--no-deps'])[0] != 0)
    # 3. add the worked example level from the references, link it after level II, rebuild
    lv = os.path.join(game, 'src', '05_levels.js')
    src = open(lv, encoding='utf-8').read()
    src2 = src.replace("name: 'The Turned Room', sub: 'down is a suggestion',", "name: 'The Turned Room', sub: 'down is a suggestion', next: 4,")
    open(lv, 'w', encoding='utf-8').write(src2 + '\n' + open(os.path.join(FILES, 'extra_level.js'), encoding='utf-8').read())
    rc, out = run([os.path.join(S, 'build_html.py'), game])
    check('build_html.py rebuilds with an added level', rc == 0 and src2 != src, out[-400:])
    bad_js = os.path.join(tmp, 'broken'); os.makedirs(bad_js)
    subprocess.run(['cp', '-r', os.path.join(game, 'src'), os.path.join(game, 'vendor'), os.path.join(game, 'game.json'), bad_js])
    with open(os.path.join(bad_js, 'src', '05_levels.js'), 'a') as f: f.write('\nLEVELS[9] = { build(L) { ');
    check('build_html.py rejects a syntax error', run([os.path.join(S, 'build_html.py'), bad_js])[0] != 0)
    # 4. the robot walks every exit and tries every gravity zone
    rc, out = run([os.path.join(S, 'playtest.py'), html])
    check('playtest.py passes on 4 levels', rc == 0 and 'level 4 (The Well)' in out and out.count('crossed in') == 3 and 'zone [1, 1]->[2, -1] ok' in out, out[-800:])
    # 5. screenshots
    shots = os.path.join(tmp, 'views')
    rc, out = run([os.path.join(S, 'shoot.py'), html, '--shots', os.path.join(FILES, 'views.json'), '--out', shots, '--size', '640x360'])
    imgs = [f for f in os.listdir(shots) if f.endswith('.jpg')] if os.path.isdir(shots) else []
    check('shoot.py takes 4 views without errors', rc == 0 and len(imgs) == 4, out[-600:])
    st = json.load(open(os.path.join(shots, 'shots.json'))) if rc == 0 else []
    check('the wall view stands on the north wall', any(r['name'] == 'turned-wall' and r['state']['up'] == [0, 0, -1] for r in st))
    # 6. trailer: stills, shots, sound, finish
    promo = os.path.join(tmp, 'promo'); os.makedirs(promo)
    d = os.path.join(promo, 'director.js'); c = os.path.join(promo, 'cues.js')
    subprocess.run(['cp', os.path.join(SKILL, 'assets', 'promo', 'director_template.js'), d])
    subprocess.run(['cp', os.path.join(SKILL, 'assets', 'promo', 'cues_template.js'), c])
    rc, out = run([os.path.join(S, 'film_shots.py'), html, d, '--stills', '--size', '320x180'])
    check('film_shots.py --stills', rc == 0 and len([f for f in os.listdir(os.path.join(promo, 'shots')) if f.endswith('.jpg')]) == 15, out[-600:])
    rc, out = run([os.path.join(S, 'film_shots.py'), html, d, '--size', '320x180'], 1500)
    mp4 = [f for f in os.listdir(os.path.join(promo, 'shots')) if f.endswith('.mp4') and 'part' not in f]
    check('film_shots.py films 5 shots', rc == 0 and len(mp4) == 5, out[-600:])
    edit = os.path.join(FILES, 'edit.json')
    rc, out = run([os.path.join(S, 'render_audio.py'), html, c, '--shots', os.path.join(promo, 'shots'), '--edit', edit])
    check('render_audio.py mixes the cue sheet', rc == 0 and os.path.exists(os.path.join(promo, 'mix.wav')), out[-600:])
    rc, out = run([os.path.join(S, 'finish_trailer.py'), os.path.join(promo, 'shots'), '--edit', edit, '--audio', os.path.join(promo, 'mix.wav'),
                   '--gif', 's03-door:0.8:1.6', '--thumb', 's03-door:40'])
    tr = os.path.join(promo, 'trailer-180p.mp4')
    check('finish_trailer.py writes trailer, GIF and thumbnail', rc == 0 and os.path.exists(tr) and os.path.exists(os.path.join(promo, 's03-door.gif'))
          and os.path.getsize(os.path.join(promo, 's03-door.gif')) < 3e6 and os.path.exists(os.path.join(promo, 's03-door-frame40.jpg')), out[-600:])
    if os.path.exists(tr):
        p = subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_frames', '-of', 'csv=p=0', tr], capture_output=True, text=True)
        check('trailer has every frame of the edit (463)', p.stdout.strip().split(',')[0] == '463', p.stdout)
        e = subprocess.run(['ffmpeg', '-hide_banner', '-i', tr, '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
        m = re.findall(r'I:\s+(-?[\d.]+) LUFS', e)
        check('trailer loudness is -14 LUFS (+-1.5)', bool(m) and abs(float(m[-1]) + 14) <= 1.5, m[-1:] if m else e[-300:])
    # 7. hygiene of the skill folder itself
    sk = open(os.path.join(SKILL, 'SKILL.md'), encoding='utf-8').read()
    fm = sk.split('---')[1]
    name = re.search(r'^name:\s*(\S+)', fm, re.M); desc = re.search(r'^description:\s*(.+)$', fm, re.M)
    check('SKILL.md frontmatter: name = folder, description <= 1024, MIT', bool(name) and name.group(1) == os.path.basename(SKILL)
          and bool(desc) and len(desc.group(1)) <= 1024 and 'license: MIT' in fm)
    refs = sorted(os.listdir(os.path.join(SKILL, 'references')))
    check('every reference is named in SKILL.md', all(f'references/{r}' in sk for r in refs), [r for r in refs if f'references/{r}' not in sk])
    check('SKILL.md body under ~200 lines', len(sk.split('---', 2)[2].splitlines()) <= 210)
    words = [bytes.fromhex(h).decode() for h in ('636f6d65646f776e', '68616c6c6f72616e', '646f6f726d616e', '726f6f78706572696d65')]  # names from the private game
    hits = []
    for root, _, fs in os.walk(SKILL):
        for f in fs:
            p = os.path.join(root, f)
            if p.endswith(('.py', '.js', '.md', '.html', '.json')):
                t = open(p, encoding='utf-8', errors='ignore').read().lower()
                hits += [f'{os.path.relpath(p, SKILL)}: {w}' for w in words if w in t]
    check('no private game content in the skill', not hits, hits[:5])
    check('no __pycache__ inside the skill', not any('__pycache__' in r for r, _, _ in os.walk(SKILL)))
    finish(t0, tmp)


def finish(t0, tmp=None):
    print(f'\n{len(ok)} passed, {len(bad)} failed in {time.time() - t0:.0f}s' + (f'  (work folder {tmp})' if tmp else ''), file=sys.stderr)
    for b in bad: print('  FAILED: ' + b, file=sys.stderr)
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
