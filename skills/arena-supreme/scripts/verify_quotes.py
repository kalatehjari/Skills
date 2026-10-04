#!/usr/bin/env python3
"""ArenaSupreme: check that every quotation in a report appears verbatim in the sources.
Usage: python3 verify_quotes.py REPORT.md --sources "dir/**/*.md" "texts/*.txt" [--min-words 3]
Quotes are text inside “…” or "…". Ellipses and [brackets] split a quote into fragments, and
each fragment of at least --min-words words is checked. Curly/straight quotes, dashes, markdown
emphasis and whitespace are normalised. Exit code 1 if anything is not found."""
import argparse, glob, re, sys, unicodedata
ap = argparse.ArgumentParser()
ap.add_argument("report"); ap.add_argument("--sources", nargs="+", required=True)
ap.add_argument("--min-words", type=int, default=3)
a = ap.parse_args()
def norm(s):
    s = unicodedata.normalize("NFKC", s)
    for x, y in (("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'), ("—", "-"), ("–", "-")):
        s = s.replace(x, y)
    s = re.sub(r"[*_`>|]", "", s)
    return re.sub(r"\s+", " ", s).lower().strip()
files = sorted({f for g in a.sources for f in glob.glob(g, recursive=True)})
if not files: sys.exit("no source files matched")
corpus = norm(" ".join(open(f, encoding="utf-8", errors="ignore").read() for f in files))
text = open(a.report, encoding="utf-8").read()
ok, miss = 0, []
for c, s in re.findall(r'“([^”]{3,400})”|"([^"\n]{3,400})"', text):
    q = c or s
    frags = [f.strip(" .,;:!?") for f in re.split(r"…|\.\.\.|\[[^\]]*\]", q)]
    frags = [f for f in frags if len(f.split()) >= a.min_words]
    if not frags: continue
    bad = [f for f in frags if norm(f) not in corpus]
    if bad: miss.append((q, bad[0]))
    else: ok += 1
print(f"sources: {len(files)} files | quotations checked: {ok + len(miss)} | verbatim: {ok} | NOT FOUND: {len(miss)}")
for q, b in miss: print(" -", q[:140], "| missing:", b[:80])
sys.exit(1 if miss else 0)
