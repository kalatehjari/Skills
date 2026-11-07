#!/usr/bin/env python3
"""Fetch the pinned third-party files a pen-and-ink game embeds into its single HTML file.

  three.js r147 (MIT)              -> <game>/vendor/three.min.js
  IM Fell English + SC (OFL-1.1)   -> <game>/vendor/fonts/*.woff2
  Special Elite (Apache-2.0)       -> <game>/vendor/fonts/*.woff2      (+ every licence file next to them)

Each npm tarball is checked against its registry sha512 integrity before anything is extracted.
Files that already exist are kept (use --force to fetch again). Offline? Use --from DIR: a folder that already
holds three.min.js and the four .woff2 files (for example another game's vendor folder).

  python3 get_deps.py path/to/my-game
  python3 get_deps.py path/to/my-game --from ../other-game/vendor
"""
import sys
sys.dont_write_bytecode = True
import argparse, base64, hashlib, io, os, shutil, tarfile, urllib.request

REG = 'https://registry.npmjs.org'
# (package, version, sha512 integrity, {path in tarball: path under vendor/})
PKGS = [
    ('three', '0.147.0', 'sha512-LPTOslYQXFkmvceQjFTNnVVli2LaVF6C99Pv34fJypp8NbQLbTlu3KinZ0zURghS5zEehK+VQyvWuPZ/Sm8fzw==',
     {'package/build/three.min.js': 'three.min.js', 'package/LICENSE': 'LICENSE-three.txt'}),
    ('@fontsource/im-fell-english', '5.3.0', 'sha512-FcgdWfY9WeUM2gQkfmwhn4Ed9LVtlll8LSSZvHfbsUrnHK5tHHnGg6BgwAfHogp52adU3eE89J/3B52qV3b+Vw==',
     {'package/files/im-fell-english-latin-400-normal.woff2': 'fonts/im-fell-english-latin-400-normal.woff2',
      'package/files/im-fell-english-latin-400-italic.woff2': 'fonts/im-fell-english-latin-400-italic.woff2',
      'package/LICENSE': 'fonts/OFL-IM-Fell-English.txt'}),
    ('@fontsource/im-fell-english-sc', '5.3.0', 'sha512-jKnCJ22tgVwxWVs1YQ/GCWmP60ulVq49IJZ7c0wgv0MXHe8T8LPbl0sOteYLOkCURW5+ZKwFiLNU2h/l9fHgrg==',
     {'package/files/im-fell-english-sc-latin-400-normal.woff2': 'fonts/im-fell-english-sc-latin-400-normal.woff2',
      'package/LICENSE': 'fonts/OFL-IM-Fell-English-SC.txt'}),
    ('@fontsource/special-elite', '5.3.0', 'sha512-fOQ9XU8m4KnqzcLibAXCxTsKzbxePNDjPqVss5GSMcPVCY1TuCv+Wq8gm1ebqIR6XS1rhMbQ7ECP9ocKVEEpTA==',
     {'package/files/special-elite-latin-400-normal.woff2': 'fonts/special-elite-latin-400-normal.woff2',
      'package/LICENSE': 'fonts/LICENSE-Special-Elite.txt'}),
]
REQUIRED = [dst for _, _, _, files in PKGS for dst in files.values() if not dst.endswith('.txt')]


def tarball_url(name, ver):
    base = name.split('/')[-1]
    return f'{REG}/{name}/-/{base}-{ver}.tgz'


def fetch(name, ver, integrity):
    data = urllib.request.urlopen(tarball_url(name, ver), timeout=60).read()
    got = 'sha512-' + base64.b64encode(hashlib.sha512(data).digest()).decode()
    if got != integrity:
        raise SystemExit(f'integrity mismatch for {name}@{ver}: expected {integrity}, got {got}')
    return data


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('game_dir', help='the game folder (vendor/ is created inside it)')
    ap.add_argument('--from', dest='src', help='copy from this folder instead of downloading (offline)')
    ap.add_argument('--force', action='store_true', help='fetch again even if the files exist')
    a = ap.parse_args()
    vendor = os.path.join(a.game_dir, 'vendor')
    os.makedirs(os.path.join(vendor, 'fonts'), exist_ok=True)
    done = []
    if a.src:
        for dst in REQUIRED + [d for _, _, _, f in PKGS for d in f.values() if d.endswith('.txt')]:
            cand = [os.path.join(a.src, dst), os.path.join(a.src, os.path.basename(dst))]
            src = next((c for c in cand if os.path.exists(c)), None)
            out = os.path.join(vendor, dst)
            if src and (a.force or not os.path.exists(out)) and os.path.abspath(src) != os.path.abspath(out):
                shutil.copyfile(src, out); done.append(dst)
    else:
        for name, ver, integ, files in PKGS:
            if not a.force and all(os.path.exists(os.path.join(vendor, d)) for d in files.values()):
                continue
            tf = tarfile.open(fileobj=io.BytesIO(fetch(name, ver, integ)), mode='r:gz')
            for member, dst in files.items():
                out = os.path.join(vendor, dst)
                with tf.extractfile(member) as f, open(out, 'wb') as o:
                    o.write(f.read())
                done.append(dst)
    missing = [d for d in REQUIRED if not os.path.exists(os.path.join(vendor, d))]
    print(f'vendor: {vendor}  fetched {len(done)} file(s)', file=sys.stderr)
    if missing:
        print('missing: ' + ', '.join(missing), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
