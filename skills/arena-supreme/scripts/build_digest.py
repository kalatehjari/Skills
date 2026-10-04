#!/usr/bin/env python3
"""ArenaSupreme: build a verbatim digest of chosen sections from many Markdown reports.
Usage: python3 build_digest.py -o out/DIGEST --keys "weakest:3,strongest:3,questions:4,recommend:1,verdict:6" \
          --tables "|" reports/*.md [--max-chars 40000]
For each file, copies the '## ' sections whose titles contain a key (case-insensitive), trimmed to N
sentences per paragraph or bullet (the number after the colon). '--tables' keeps table rows that contain
a score (a number cell). Output is split into DIGEST_part1.md, part2 … of at most --max-chars each,
so every part shows in one tool call. Everything is copied verbatim (only shortened), so it can be quoted.
Without -o, the parts are written next to the first input file, never to the current directory."""
import argparse, os, re
ap = argparse.ArgumentParser(description="Verbatim evidence digest builder (ArenaSupreme)"); ap.add_argument("files", nargs="+"); ap.add_argument("-o", "--out", default=None, help="output prefix (default: <dir of first input>/DIGEST)")
ap.add_argument("--keys", default="weakest:3,strongest:3,question:4,recommend:1,verdict:6")
ap.add_argument("--tables", default=""); ap.add_argument("--max-chars", type=int, default=40000)
a = ap.parse_args()
if not a.out: a.out = os.path.join(os.path.dirname(os.path.abspath(a.files[0])), "DIGEST")
keys = [(k.split(":")[0].lower(), int(k.split(":")[1]) if ":" in k else 3) for k in a.keys.split(",")]
SPLIT = re.compile(r'(?<=[a-z0-9)”"’][.!?])\s+(?=[A-Z*“"])')
def first(s, n):
    m = re.match(r"^((?:[-*]|\d+\.)\s+)", s); lead = m.group(1) if m else ""
    return lead + " ".join(SPLIT.split(s[len(lead):])[:n])
def trim(body, n):
    out = []
    for para in re.split(r"\n\s*\n", body):
        para = para.strip()
        if not para or para.startswith("|"): continue
        lines = para.split("\n")
        if len(lines) > 1 and all(re.match(r"^\s*(?:[-*]|\d+\.)\s", l) for l in lines): out += [first(l.strip(), n) for l in lines]
        else: out.append(first(" ".join(l.strip() for l in lines), n))
    return "\n".join(out)
chunks = []
for f in a.files:
    t = open(f, encoding="utf-8").read(); parts = re.split(r"(?m)^## ", t)
    block = [f"\n## Source: {os.path.basename(f)}\n"]
    if a.tables:
        rows = [l for l in t.split("\n") if l.startswith("|") and re.search(r"\|\s*\**\d+(\.\d+)?\**\s*\|", l)]
        if rows: block += ["**Score rows:**", *rows, ""]
    for p in parts[1:]:
        title, _, body = p.partition("\n")
        for k, n in keys:
            if k in title.lower(): block += [f"**{title.strip()}:**", trim(body, n), ""]; break
    chunks.append("\n".join(block))
part, size, n = [], 0, 1
def flush(part, n):
    open(f"{a.out}_part{n}.md", "w", encoding="utf-8").write("# Evidence digest (verbatim extracts, trimmed)\n" + "\n".join(part))
for c in chunks:
    if part and size + len(c) > a.max_chars: flush(part, n); n += 1; part, size = [], 0
    part.append(c); size += len(c)
if part: flush(part, n)
import sys; print(f"wrote {n} part(s): {a.out}_part1..{n}.md", file=sys.stderr)
