#!/usr/bin/env python3
"""ArenaSupreme: list figures in a report that do not appear in the reference files.
Usage: python3 check_numbers.py REPORT.md --refs NUMBERS.md metrics/*.txt
Flags decimals, signed changes, ranges like 8–4 and thousands like 81,198. Each flagged figure
must be a recomputation shown in the text, a section reference or a target; otherwise fix it."""
import argparse, glob, re
ap = argparse.ArgumentParser(); ap.add_argument("report"); ap.add_argument("--refs", nargs="+", required=True)
a = ap.parse_args()
files = sorted({f for g in a.refs for f in glob.glob(g, recursive=True)})
ref = " ".join(open(f, encoding="utf-8", errors="ignore").read() for f in files).replace("−", "-")
refnum = ref.replace(",", "")
t = open(a.report, encoding="utf-8").read().replace("−", "-")
nums = set(re.findall(r"[+-]?\d+\.\d+|\b\d+[–-]\d+\b|\b\d{1,3}(?:,\d{3})+\b", t))
def known(n):
    m = n.lstrip("+")
    return n in ref or m in ref or n.replace("–", "-") in ref or m.replace(",", "") in refnum
unk = sorted(n for n in nums if not known(n))
print(f"figures found: {len(nums)} | not in reference files: {len(unk)}")
print(" ".join(unk))
