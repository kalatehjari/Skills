#!/usr/bin/env python3
"""Find and replace text in a .docx while keeping formatting.

Word often splits one visible word across several runs (spell-check marks,
revisions, partial bold). A naive run-by-run replace misses those; this script
matches across runs inside each paragraph and keeps the formatting of the run
where each match starts. Covers body text, tables (incl. nested), headers and
footers. Text inside text boxes, footnotes and comments is not touched.

Usage:
    python docx_replace.py in.docx -o out.docx --find "Lot 12" --replace "Lot 14"
    python docx_replace.py in.docx -o out.docx --map replacements.json   # {"old": "new", ...}
    python docx_replace.py in.docx --find "colour" --dry-run              # just count/show matches
Options: --regex  --ignore-case  --whole-word  --no-headers
For tracked (redlined) edits instead of silent replacement, use docx_redline.py.
"""
import argparse
import json
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _docx_common import compile_pattern, iter_paragraphs, replace_in_paragraph  # noqa: E402

import docx  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("docx")
    ap.add_argument("-o", "--output")
    ap.add_argument("--find")
    ap.add_argument("--replace", default="")
    ap.add_argument("--map", help="JSON file mapping find -> replace (applied in order)")
    ap.add_argument("--regex", action="store_true", help="treat find strings as regular expressions (\\1 in replace works)")
    ap.add_argument("--ignore-case", action="store_true")
    ap.add_argument("--whole-word", action="store_true")
    ap.add_argument("--no-headers", action="store_true", help="skip headers and footers")
    ap.add_argument("--dry-run", action="store_true", help="report matches without writing")
    a = ap.parse_args()

    pairs = []
    if a.map:
        with open(a.map, encoding="utf-8") as fh:
            pairs = list(json.load(fh).items())
    if a.find is not None:
        pairs.append((a.find, a.replace))
    if not pairs:
        sys.exit("Give --find/--replace or --map")
    if not a.dry_run and not a.output:
        sys.exit("Give -o OUTPUT (or --dry-run)")
    if a.output and os.path.abspath(a.output) == os.path.abspath(a.docx):
        sys.exit("Refusing to overwrite the input; choose a different -o")

    d = docx.Document(a.docx)
    total = 0
    for find, repl in pairs:
        rx = compile_pattern(find, a.regex, a.ignore_case, a.whole_word)
        n = 0
        for p in iter_paragraphs(d, headers=not a.no_headers):
            if a.dry_run:
                for m in rx.finditer(p.text):
                    n += 1
                    s = max(0, m.start() - 30)
                    print(f"  #{n}: …{p.text[s:m.end() + 30]}…")
            else:
                n += replace_in_paragraph(p, rx, repl if a.regex else repl.replace("\\", "\\\\"))
        label = f"{find!r}: {n} match(es)" if a.dry_run else f"{find!r} -> {repl!r}: {n} replacement(s)"
        print(label, file=sys.stderr)
        total += n
    if a.dry_run:
        return
    d.save(a.output)
    print(f"Wrote {a.output} ({total} replacement(s))", file=sys.stderr)
    if total == 0:
        print("Nothing matched. Check spelling, try --ignore-case, or the text may sit in a text box/footnote.", file=sys.stderr)


if __name__ == "__main__":
    main()
