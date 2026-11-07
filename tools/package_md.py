#!/usr/bin/env python3
"""Build installable skills: single-file .md in dist-md/, or zips in dist-console/.

    python3 tools/package_md.py                  # dist-md/<name>.md for every skill in skills/
    python3 tools/package_md.py --zip            # dist-console/<name>.zip for every skill
    python3 tools/package_md.py pdf-workbench    # one or more, by name
    python3 tools/package_md.py --out /tmp/md    # write somewhere else

Each <name>.md is the skill's SKILL.md (frontmatter and instructions as they
are) plus every runtime file in its folder (references/, scripts/, assets/,
LICENSE), embedded verbatim with a SHA-256 checksum. A note at the top gives
Claude one command that unpacks those files byte for byte, so the single .md
works like the whole folder.

Each <name>.zip (--zip) holds one top-level <name>/ folder with SKILL.md and
the same supporting files as separate files. That is the layout the Claude
Console, the Skills API and claude.ai expect when you upload a skill. Its
timestamps are set to the build date, so unchanged skills rebuild the same.

Left out of both, because a skill doesn't need them at run time: evals/,
development notes (README.md, PROGRESS.md), history folders (case-studies/,
self-improvement/, reports/, versions/), caches and OS clutter. Binary files
go into zips but can't be embedded in a .md.

A frontmatter value that YAML would reject (an unquoted description
containing ": ", for example) is re-quoted; the text itself is unchanged.
After building, every output is checked against the source files: each .md
is unpacked with its embedded command, each zip is reopened and compared
(--no-verify skips this).
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIP_LIMIT = 30 * 1024 * 1024  # Skills API: total uncompressed upload size
DEV_DIRS = {"evals", "case-studies", "self-improvement", "reports", "versions"}  # top level only
DEV_FILES = {"SKILL.md", "README.md", "PROGRESS.md"}  # top level only
SKIP_DIRS = {"__pycache__", "node_modules"}
SKIP_FILES = {"Thumbs.db"}
GROUPS = ("references", "assets", "scripts")
ALLOWED_KEYS = {"name", "description", "license", "allowed-tools", "metadata", "compatibility"}
LANG = {".py": "python", ".sh": "bash", ".js": "javascript", ".mjs": "javascript",
        ".md": "markdown", ".json": "json", ".html": "html", ".css": "css",
        ".yaml": "yaml", ".yml": "yaml", ".csv": "csv", ".txt": "text", ".tmpl": "text"}
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---[ \t]*\n", re.S)

# The unpacker Claude runs. It reads this .md from disk, so text shown in the
# conversation can differ (placeholders filled in) without affecting the files.
UNPACK = r'''import hashlib, os, re, sys
src, out = sys.argv[1], sys.argv[2]
if not os.path.isfile(src):
    src = "/mnt/skills/user/{name}/SKILL.md"
text = open(src, encoding="utf-8", newline="").read()
rx = r"^<!-- bundle-file: (\S+) sha256=([0-9a-f]{{64}}) -->\n(`{{3,}})[^\n]*\n(.*?)^\3$"
n = 0
for path, sha, _, body in re.findall(rx, text, re.M | re.S):
    if path.startswith("/") or ".." in path.split("/"):
        continue
    data = next((b for b in (body, body[:-1]) if hashlib.sha256(b.encode()).hexdigest() == sha), None)
    if data is None:
        data = body
        print("warning: " + path + " was edited after packing (checksum differs)")
    dest = os.path.join(out, path)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8", newline="") as f:
        f.write(data)
    if data.startswith("#!"):
        os.chmod(dest, 0o755)
    n += 1
print(n, "files unpacked to", os.path.abspath(out))'''

NOTE = '''**Single-file build.** This is the `{name}` skill packed into one file on {today}. The instructions below are its SKILL.md, unchanged. Its supporting files ({contents}) are embedded verbatim under "Bundled files" at the end, each with a SHA-256 checksum. You can read a reference there directly. Before you run a script or use an asset, unpack the files once:

```bash
python3 - "${{CLAUDE_SKILL_DIR}}/SKILL.md" "${{TMPDIR:-/tmp}}/{name}" <<'PY'
{unpack}
PY
```

The first argument is the path of this file. Claude Code and Cowork fill it in for you; elsewhere, use the path you read this file from (on claude.ai the command also tries `/mnt/skills/user/{name}/SKILL.md`). The command prints the folder it wrote to. From then on, use that folder wherever the instructions mean this skill's folder: paths such as `scripts/...`, `references/...`, `assets/...` and `<this-skill>/...` all point into it.

---

'''

NOTE_NO_FILES = '''*Single-file build of `{name}`, packed on {today}. This skill has no supporting files{licence}.*

'''


def warn(msg):
    print(f"warning: {msg}", file=sys.stderr)


def skill_dirs(root, wanted):
    base = os.path.join(root, "skills")
    found = sorted(d for d in os.listdir(base) if os.path.isfile(os.path.join(base, d, "SKILL.md")))
    missing = sorted(set(wanted) - set(found))
    if missing:
        sys.exit(f"no skill folder with a SKILL.md for: {', '.join(missing)}")
    return [os.path.join(base, d) for d in found if not wanted or d in wanted]


def plain_value_problem(value):
    """Why YAML would misread this unquoted one-line value, or None if it's fine."""
    v = value.strip()
    if not v or v[0] in "'\"|>[{":
        return None  # quoted, block or flow value: left to the YAML check
    if v[0] in "&*!%@`#," or (v[0] in "-?:" and (len(v) == 1 or v[1] in " \t")):
        return f"starts with {v[0]!r}"
    if ": " in v or "\t:" in v or v.endswith(":"):
        return "contains ': '"
    if " #" in v or "\t#" in v:
        return "contains ' #'"
    return None


def fix_frontmatter(block):
    """Re-quote top-level one-line values that YAML would reject. Returns (block, notes)."""
    lines = block.split("\n")
    notes = []
    for i, line in enumerate(lines):
        m = re.match(r"([A-Za-z][\w-]*):[ \t]+(\S.*)$", line)
        continued = i + 1 < len(lines) and lines[i + 1][:1] in (" ", "\t")
        if not m or continued:
            continue
        why = plain_value_problem(m.group(2))
        if why:
            lines[i] = f"{m.group(1)}: {json.dumps(m.group(2).strip(), ensure_ascii=False)}"
            notes.append(f"quoted {m.group(1)} ({why})")
    return "\n".join(lines), notes


def check_frontmatter(block, name, where):
    try:
        import yaml
    except ImportError:
        yaml = None
    if yaml:
        try:
            data = yaml.safe_load(block)
        except yaml.YAMLError as e:
            sys.exit(f"{where}: frontmatter is not valid YAML: {e}")
        if not isinstance(data, dict):
            sys.exit(f"{where}: frontmatter is not a mapping")
    else:
        warn("PyYAML not installed, so the frontmatter is only checked roughly")
        data = {k: v.strip().strip("'\"") for k, v in re.findall(r"^([A-Za-z][\w-]*):(.*)$", block, re.M)}
    desc = data.get("description")
    if data.get("name") != name:
        sys.exit(f"{where}: name is {data.get('name')!r}, but the folder is {name!r}")
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) or len(name) > 64:
        sys.exit(f"{where}: name must be lowercase kebab-case, up to 64 characters")
    if not isinstance(desc, str) or not desc.strip():
        sys.exit(f"{where}: description is missing")
    if len(desc) > 1024:
        sys.exit(f"{where}: description is {len(desc)} characters (limit 1024)")
    if "<" in desc or ">" in desc:
        warn(f"{where}: description contains < or >, which some uploaders reject")
    extra = set(data) - ALLOWED_KEYS
    if extra:
        warn(f"{where}: frontmatter keys {sorted(extra)} are not in the Agent Skills spec")


def collect(skill_dir):
    """Runtime files of a skill, as /-separated relative paths, references first."""
    files = []
    for dirpath, dirnames, filenames in os.walk(skill_dir):
        rel_dir = os.path.relpath(dirpath, skill_dir)
        top = rel_dir == "."
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")
                             and not (top and d in DEV_DIRS))
        for f in filenames:
            if f.startswith(".") or f in SKIP_FILES or f.endswith(".pyc") or (top and f in DEV_FILES):
                continue
            files.append(f if top else os.path.join(rel_dir, f).replace(os.sep, "/"))

    def order(path):
        head = path.split("/")[0]
        return (GROUPS.index(head) if head in GROUPS else len(GROUPS), path)
    return sorted(files, key=order)


def describe(paths):
    counts = {}
    for p in paths:
        head = p.split("/")[0] if "/" in p else p
        counts[head] = counts.get(head, 0) + 1
    words = {"references": ("reference file", "reference files"), "assets": ("asset", "assets"),
             "scripts": ("script", "scripts")}
    parts = []
    for head, n in counts.items():
        if head in words:
            parts.append(f"{n} {words[head][n != 1]}")
        elif head == "LICENSE":
            parts.append("the licence")
        else:
            parts.append(f"`{head}`" if n == 1 else f"{n} files in `{head}/`")
    return parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " and " + parts[-1]


def fence_for(text):
    longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
    return "`" * max(4, longest + 1)


def read_skill(skill_dir):
    """Read and check SKILL.md. Returns (name, text with repairs applied, frontmatter, body, notes)."""
    name = os.path.basename(skill_dir)
    where = f"skills/{name}/SKILL.md"
    with open(os.path.join(skill_dir, "SKILL.md"), encoding="utf-8", newline="") as fh:
        text = fh.read().lstrip("﻿")
    if "\r" in text:
        sys.exit(f"{where}: has Windows line endings; convert it to LF first")
    m = FRONTMATTER.match(text)
    if not m:
        sys.exit(f"{where}: must start with a --- frontmatter --- block")
    block, notes = fix_frontmatter(m.group(1))
    check_frontmatter(block, name, where)
    body = text[m.end():]
    if notes:
        text = text[:m.start(1)] + block + text[m.end(1):]
    return name, text, block, body, notes


def build(skill_dir, out_dir, today):
    name, _, block, body, notes = read_skill(skill_dir)
    if not body.endswith("\n"):
        body += "\n"

    entries, skipped = [], []
    for rel in collect(skill_dir):
        with open(os.path.join(skill_dir, rel), "rb") as fh:
            raw = fh.read()
        try:
            data = raw.decode("utf-8")
        except UnicodeDecodeError:
            skipped.append(rel)
            continue
        if re.search(r"\s", rel):
            sys.exit(f"skills/{name}/{rel}: file names with spaces can't be bundled")
        entries.append((rel, data, hashlib.sha256(raw).hexdigest(), len(raw)))
    for rel in skipped:
        warn(f"skills/{name}/{rel}: binary file left out of the .md")

    runtime = [e[0] for e in entries if e[0] != "LICENSE"]
    if runtime:
        head = NOTE.format(name=name, today=today, contents=describe([e[0] for e in entries]),
                           unpack=UNPACK.format(name=name))
    else:
        head = NOTE_NO_FILES.format(name=name, today=today,
                                    licence="; its licence is at the end" if entries else "")

    parts = ["---\n", block, "\n---\n\n", head, body]
    if runtime:
        parts.append("\n---\n\n## Bundled files\n\n")
        parts.append("The skill's supporting files, verbatim. Unpack them with the command at the top, "
                     "or read one here. Line is where each file starts in this document.\n\n")
        parts.append("| File | Size | Line |\n|---|---:|---:|\n")
        parts += [f"| `{rel}` | {size / 1024:.1f} KB | @@LINE{i}@@ |\n" for i, (rel, _, _, size) in enumerate(entries)]
        if skipped:
            parts.append("\nNot embedded (binary): " + ", ".join(f"`{s}`" for s in skipped) + "\n")
    elif entries:
        parts.append("\n---\n\n## Licence\n")
    if entries:
        for rel, data, sha, _ in entries:
            fence = fence_for(data)
            lang = LANG.get(os.path.splitext(rel)[1], "text")
            parts.append(f"\n### `{rel}`\n\n<!-- bundle-file: {rel} sha256={sha} -->\n{fence}{lang}\n")
            parts.append(data if data.endswith("\n") or not data else data + "\n")
            parts.append(f"{fence}\n")
    doc = "".join(parts)

    lines = doc.split("\n")
    for i, (rel, _, sha, _) in enumerate(entries):
        marker = f"<!-- bundle-file: {rel} sha256={sha} -->"
        line_no = lines.index(marker) - 1  # the ### heading sits two lines above (1-based: -2 + 1)
        doc = doc.replace(f"@@LINE{i}@@", str(line_no), 1)

    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"{name}.md")
    with open(out, "w", encoding="utf-8", newline="") as fh:
        fh.write(doc)
    return out, entries, notes, body


def verify(md_path, skill_dir, entries, body):
    """Unpack with the embedded command and compare every file with its source."""
    name = os.path.basename(skill_dir)
    with open(md_path, encoding="utf-8", newline="") as fh:
        doc = fh.read()
    problems = []
    if body not in doc:
        problems.append("SKILL.md body not found verbatim")
    code = UNPACK.format(name=name)
    if any(e[0] != "LICENSE" for e in entries) and f"<<'PY'\n{code}\nPY\n" not in doc:
        problems.append("unpack command in the note differs from the template")
    with tempfile.TemporaryDirectory() as tmp:
        run = subprocess.run([sys.executable, "-I", "-", md_path, tmp], input=code,
                             capture_output=True, text=True)
        if run.returncode or "warning" in run.stdout:
            problems.append(f"unpacker failed: {run.stdout.strip()} {run.stderr.strip()}")
        got = sorted(os.path.relpath(os.path.join(dp, f), tmp).replace(os.sep, "/")
                     for dp, _, fs in os.walk(tmp) for f in fs)
        want = sorted(e[0] for e in entries)
        if got != want:
            problems.append(f"unpacked {got} but expected {want}")
        for rel, _, _, _ in entries:
            src, dst = os.path.join(skill_dir, rel), os.path.join(tmp, rel)
            if os.path.isfile(dst):
                with open(src, "rb") as a, open(dst, "rb") as b:
                    if a.read() != b.read():
                        problems.append(f"{rel} differs after unpacking")
    return problems


def build_zip(skill_dir, out_dir, today):
    """<name>.zip with a single <name>/ folder: SKILL.md plus the supporting files."""
    name, text, _, _, notes = read_skill(skill_dir)
    members = [("SKILL.md", text.encode("utf-8"))]
    for rel in collect(skill_dir):
        with open(os.path.join(skill_dir, rel), "rb") as fh:
            members.append((rel, fh.read()))
    size = sum(len(data) for _, data in members)
    if size > ZIP_LIMIT:
        sys.exit(f"skills/{name}: {size / 2**20:.1f} MB uncompressed, over the 30 MB upload limit")
    stamp = tuple(int(x) for x in today.split("-")) + (0, 0, 0)
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"{name}.zip")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for rel, data in members:
            info = zipfile.ZipInfo(f"{name}/{rel}", date_time=stamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3  # Unix, so the permission bits below are kept
            info.external_attr = (0o100755 if data.startswith(b"#!") else 0o100644) << 16
            z.writestr(info, data)
    return out, members, notes


def verify_zip(zip_path, skill_dir, members):
    """Reopen the zip and check its layout, its SKILL.md and every file in it."""
    name = os.path.basename(skill_dir)
    problems = []
    with zipfile.ZipFile(zip_path) as z:
        if z.testzip() is not None:
            problems.append("a file in the zip fails its CRC check")
        names = z.namelist()
        if sorted(names) != sorted(f"{name}/{rel}" for rel, _ in members):
            problems.append("the zip's file list differs from the skill folder")
        if {n.split("/", 1)[0] for n in names} != {name}:
            problems.append(f"the top level is not a single {name}/ folder")
        for rel, data in members:
            if f"{name}/{rel}" in names and z.read(f"{name}/{rel}") != data:
                problems.append(f"{rel} differs")
        packed = z.read(f"{name}/SKILL.md").decode("utf-8")
    with open(os.path.join(skill_dir, "SKILL.md"), encoding="utf-8", newline="") as fh:
        original = fh.read().lstrip("﻿")
    a, b = FRONTMATTER.match(original), FRONTMATTER.match(packed)
    if not b or original[a.end():] != packed[b.end():]:
        problems.append("the SKILL.md instructions changed")
    else:
        check_frontmatter(b.group(1), name, f"{name}.zip: {name}/SKILL.md")
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__.split("\n\n", 2)[2])
    ap.add_argument("names", nargs="*", help="skill names (default: every skill in skills/)")
    ap.add_argument("--root", default=ROOT, help="library root (default: the folder above tools/)")
    ap.add_argument("--zip", action="store_true",
                    help="build <name>.zip (a <name>/ folder with SKILL.md and its files) for the "
                         "Claude Console, the Skills API or claude.ai, in <root>/dist-console")
    ap.add_argument("--out", help="output folder (default: <root>/dist-md, or <root>/dist-console with --zip)")
    ap.add_argument("--no-verify", action="store_true", help="skip the check against the source files")
    args = ap.parse_args()
    out_dir = args.out or os.path.join(args.root, "dist-console" if args.zip else "dist-md")
    today = datetime.date.today().isoformat()
    failed = 0
    for skill_dir in skill_dirs(args.root, args.names):
        if args.zip:
            out, members, notes = build_zip(skill_dir, out_dir, today)
            problems = [] if args.no_verify else verify_zip(out, skill_dir, members)
            count = f"{len(members)} files"
        else:
            out, entries, notes, body = build(skill_dir, out_dir, today)
            problems = [] if args.no_verify else verify(out, skill_dir, entries, body)
            count = f"{len(entries)} files bundled"
        status = "FAILED: " + "; ".join(problems) if problems else ("ok" if not args.no_verify else "built")
        extra = f" ({'; '.join(notes)})" if notes else ""
        print(f"{out}  {os.path.getsize(out) // 1024} KB, {count}, {status}{extra}", file=sys.stderr)
        failed += bool(problems)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
