#!/usr/bin/env python3
"""ArenaSupreme: aggregate blind pairwise judgements.
Usage: python3 bt_aggregate.py --key KEY.json judges/*_JUDGE.md
KEY.json: {"<set>": {"X": "<version>", "Y": "...", "Z": "..."}}. The set name is the judge file name
up to the first "_". Each judge file holds a ```json block with "pairs": [{"a","b","winner","margin"}].
Prints the decoded rankings, the win matrix, margin sums, and Bradley–Terry ratings (Elo-style scale,
1500 centre, 0.5 pseudo-win prior), plain and margin-weighted."""
import argparse, collections, json, math, os, re
ap = argparse.ArgumentParser(); ap.add_argument("files", nargs="+"); ap.add_argument("--key", required=True)
a = ap.parse_args(); key = json.load(open(a.key))
W, M = collections.Counter(), collections.Counter(); vers = set()
for f in sorted(a.files):
    s = os.path.basename(f).split("_")[0]; k = key[s]; vers |= set(k.values())
    d = json.loads(re.search(r"```json\s*(\{.*?\})\s*```", open(f).read(), re.S).group(1))
    row = []
    for p in d["pairs"]:
        x, y, w = k[p["a"]], k[p["b"]], k[p["winner"]]; l = x if w == y else y
        W[(w, l)] += 1; M[(w, l)] += p["margin"]; row.append(f"{w}>{l}({p['margin']})")
    print(s, " > ".join(k[r] for r in d.get("ranking", [])), "|", "; ".join(row))
vers = sorted(vers)
def bt(C, prior=0.5):
    C = collections.Counter(C)
    for i in vers:
        for j in vers:
            if i != j: C[(i, j)] += prior
    p = {v: 1.0 for v in vers}
    for _ in range(2000):
        new = {i: sum(C[(i, j)] for j in vers if j != i) / sum((C[(i, j)] + C[(j, i)]) / (p[i] + p[j]) for j in vers if j != i) for i in vers}
        g = math.exp(sum(math.log(x) for x in new.values()) / len(vers)); p = {k: v / g for k, v in new.items()}
    return p
print("\nwins:", {f"{w}>{l}": n for (w, l), n in W.items()}, "\nmargin sums:", {f"{w}>{l}": n for (w, l), n in M.items()})
for lab, C in (("plain", W), ("margin-weighted", M)):
    p = bt(C); print(lab, {v: round(1500 + 400 * math.log10(p[v])) for v in vers},
                     {f"P({i}>{j})": round(p[i] / (p[i] + p[j]), 2) for i in vers for j in vers if i < j})
