#!/usr/bin/env python3
"""Compare two versions of a Word document and report what changed.

Aligns paragraphs (body + table cells, in order), then shows word-level
differences inside changed paragraphs. Output is Markdown:
  ~~deleted words~~  **inserted words**   and whole added/removed paragraphs.

Usage:
    python docx_compare.py v1.docx v2.docx [-o changes.md] [--context 0]
Files that contain tracked changes: accept them first (docx_revisions.py accept)
so you compare final text. For a Word-native redline, use Word: Review → Compare.
"""
import argparse
import difflib
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _docx_common import iter_paragraphs  # noqa: E402

import docx  # noqa: E402


def paragraphs(path):
    d = docx.Document(path)
    out = []
    for p in iter_paragraphs(d, headers=False):
        t = p.text.strip()
        if t:
            out.append(t)
    return out


def word_diff(a, b):
    ta, tb = re.findall(r"\S+|\s+", a), re.findall(r"\S+|\s+", b)
    sm = difflib.SequenceMatcher(None, ta, tb, autojunk=False)
    out = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            out.append("".join(ta[i1:i2]))
        if op in ("delete", "replace"):
            seg = "".join(ta[i1:i2]).strip()
            if seg:
                out.append(f"~~{seg}~~ ")
        if op in ("insert", "replace"):
            seg = "".join(tb[j1:j2]).strip()
            if seg:
                out.append(f"**{seg}** ")
    return re.sub(r" {2,}", " ", "".join(out)).strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("old")
    ap.add_argument("new")
    ap.add_argument("-o", "--output")
    ap.add_argument("--context", type=int, default=0, help="unchanged paragraphs to show around changes")
    a = ap.parse_args()

    A, B = paragraphs(a.old), paragraphs(a.new)
    sm = difflib.SequenceMatcher(None, A, B, autojunk=False)
    lines = [f"# Changes: `{os.path.basename(a.old)}` → `{os.path.basename(a.new)}`", ""]
    stats = {"changed": 0, "added": 0, "removed": 0}
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            if a.context:
                for t in A[i1:i2][:a.context]:
                    lines += [f"> {t[:200]}", ""]
            continue
        if op == "replace":
            # pair paragraphs up by similarity; leftovers count as added/removed
            pa, pb = A[i1:i2], B[j1:j2]
            for k in range(max(len(pa), len(pb))):
                if k < len(pa) and k < len(pb) and difflib.SequenceMatcher(None, pa[k], pb[k]).ratio() > 0.4:
                    lines += [f"- **Changed** (¶{i1 + k + 1}): {word_diff(pa[k], pb[k])}", ""]
                    stats["changed"] += 1
                else:
                    if k < len(pa):
                        lines += [f"- **Removed** (¶{i1 + k + 1}): ~~{pa[k]}~~", ""]
                        stats["removed"] += 1
                    if k < len(pb):
                        lines += [f"- **Added** (new ¶{j1 + k + 1}): {pb[k]}", ""]
                        stats["added"] += 1
        elif op == "delete":
            for k, t in enumerate(A[i1:i2]):
                lines += [f"- **Removed** (¶{i1 + k + 1}): ~~{t}~~", ""]
                stats["removed"] += 1
        elif op == "insert":
            for k, t in enumerate(B[j1:j2]):
                lines += [f"- **Added** (new ¶{j1 + k + 1}): {t}", ""]
                stats["added"] += 1
    summary = f"{stats['changed']} changed, {stats['added']} added, {stats['removed']} removed paragraph(s)"
    lines.insert(1, "")
    lines.insert(2, summary)
    text = "\n".join(lines).rstrip() + "\n"
    if a.output:
        with open(a.output, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"Wrote {a.output}: {summary}", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
