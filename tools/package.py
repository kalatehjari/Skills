#!/usr/bin/env python3
"""Build installable zips in dist/ for every skill (original and third-party).

    python tools/package.py            # all skills
    python tools/package.py pdf-workbench

Each zip contains <name>/SKILL.md and the rest of the folder, without evals/,
caches or OS clutter, ready to upload in Claude's Settings → Capabilities → Skills.
"""
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {"evals", "__pycache__", ".git", "node_modules"}
SKIP_FILES = {".DS_Store", "Thumbs.db"}


def skill_dirs():
    for base in ("skills", "third-party"):
        for dirpath, dirnames, filenames in os.walk(os.path.join(ROOT, base)):
            if "SKILL.md" in filenames:
                dirnames[:] = []  # don't descend into a skill
                yield dirpath


def check(path):
    with open(os.path.join(path, "SKILL.md"), encoding="utf-8") as fh:
        head = fh.read(4000)
    m = re.match(r"---\n(.*?)\n---", head, re.S)
    if not m or "name:" not in m.group(1) or "description:" not in m.group(1):
        sys.exit(f"{path}/SKILL.md: frontmatter needs name and description")
    name = re.search(r"^name:\s*(\S+)", m.group(1), re.M).group(1)
    if name != os.path.basename(path):
        print(f"warning: {path}: folder name differs from name: {name}", file=sys.stderr)


def build(path):
    name = os.path.basename(path)
    out = os.path.join(ROOT, "dist", f"{name}.zip")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for dirpath, dirnames, filenames in os.walk(path):
            dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
            for f in sorted(filenames):
                if f in SKIP_FILES or f.endswith(".pyc"):
                    continue
                full = os.path.join(dirpath, f)
                z.write(full, os.path.join(name, os.path.relpath(full, path)))
    print(f"{out}  ({os.path.getsize(out) // 1024} KB)")


def main():
    os.makedirs(os.path.join(ROOT, "dist"), exist_ok=True)
    wanted = set(sys.argv[1:])
    for d in skill_dirs():
        if not wanted or os.path.basename(d) in wanted:
            check(d)
            build(d)


if __name__ == "__main__":
    main()
