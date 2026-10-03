#!/usr/bin/env python3
"""Page-level PDF operations with pypdf. Inputs are never modified.

Subcommands (page numbers are 1-based; specs like 1-3,7,10-):
  merge   a.pdf b.pdf ... -o out.pdf [--bookmarks]
  split   in.pdf --out-dir dir [--every N | --ranges "1-3,4-9,10-"]
          (no option = one file per page; use ';' between files if a file
          needs several ranges: --ranges "1-2,5;3-4")
  extract in.pdf --pages SPEC -o out.pdf        keep only these pages
  delete  in.pdf --pages SPEC -o out.pdf        drop these pages
  rotate  in.pdf --angle 90 [--pages SPEC] -o out.pdf   (90/180/270, clockwise)
  reorder in.pdf --order "3,1,2,4-" -o out.pdf  (use --reverse to flip order)

For encrypted inputs put --password before the subcommand:
  python pdf_pages.py --password PW extract in.pdf --pages 1 -o out.pdf
"""
import argparse
import os
import sys

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    sys.exit("pypdf is required: pip install pypdf")


def parse_pages(spec, n, allow_dupes=False):
    out = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            start, end = (int(a) if a else 1), (int(b) if b else n)
        else:
            start = end = int(part)
        if start < 1 or end > n or start > end:
            sys.exit(f"Page range '{part}' is outside 1-{n}")
        for i in range(start - 1, end):
            if allow_dupes or i not in out:
                out.append(i)
    return out


def open_reader(path, password):
    r = PdfReader(path)
    if r.is_encrypted and not r.decrypt(password or ""):
        sys.exit(f"{path} is encrypted; pass --password")
    return r


def write(writer, out, src_reader=None):
    if os.path.abspath(out) in INPUTS:
        sys.exit("Refusing to overwrite an input file; choose a different -o")
    if src_reader is not None and src_reader.metadata:
        try:
            writer.add_metadata({k: v for k, v in src_reader.metadata.items() if isinstance(k, str)})
        except Exception:
            pass
    with open(out, "wb") as fh:
        writer.write(fh)
    print(f"Wrote {out} ({len(writer.pages)} pages)", file=sys.stderr)


def subset(reader, idxs):
    w = PdfWriter()
    for i in idxs:
        w.add_page(reader.pages[i])
    return w


def cmd_merge(a):
    w = PdfWriter()
    for path in a.inputs:
        r = open_reader(path, a.password)
        start = len(w.pages)
        w.append(r, import_outline=True)
        if a.bookmarks:
            w.add_outline_item(os.path.splitext(os.path.basename(path))[0], start)
        print(f"  + {path}: {len(r.pages)} pages", file=sys.stderr)
    write(w, a.output)


def cmd_split(a):
    r = open_reader(a.input, a.password)
    n = len(r.pages)
    a.out_dir = a.out_dir or os.path.join(os.path.dirname(os.path.abspath(a.input)), "split")
    os.makedirs(a.out_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(a.input))[0]
    if a.every:
        groups = [list(range(s, min(s + a.every, n))) for s in range(0, n, a.every)]
    elif a.ranges:
        # "1-3,4-9" -> two files; use ';' between files when a file needs several ranges: "1-3,7;4-6"
        sep = ";" if ";" in a.ranges else ","
        groups = [parse_pages(part, n) for part in a.ranges.split(sep) if part.strip()]
    else:
        groups = [[i] for i in range(n)]
    for g in groups:
        contiguous = g == list(range(g[0], g[0] + len(g)))
        if len(g) == 1:
            label = f"p{g[0] + 1:03d}"
        elif contiguous:
            label = f"p{g[0] + 1:03d}-{g[-1] + 1:03d}"
        else:
            label = "p" + "_".join(str(i + 1) for i in g)[:60]
        write(subset(r, g), os.path.join(a.out_dir, f"{base}_{label}.pdf"), r)


def cmd_extract(a):
    r = open_reader(a.input, a.password)
    write(subset(r, parse_pages(a.pages, len(r.pages))), a.output, r)


def cmd_delete(a):
    r = open_reader(a.input, a.password)
    drop = set(parse_pages(a.pages, len(r.pages)))
    keep = [i for i in range(len(r.pages)) if i not in drop]
    if not keep:
        sys.exit("That would delete every page")
    write(subset(r, keep), a.output, r)


def cmd_rotate(a):
    if a.angle % 90:
        sys.exit("--angle must be a multiple of 90")
    r = open_reader(a.input, a.password)
    targets = set(parse_pages(a.pages, len(r.pages))) if a.pages else set(range(len(r.pages)))
    w = PdfWriter()
    for i, p in enumerate(r.pages):
        page = w.add_page(p)
        if i in targets:
            page.rotate(a.angle)
    write(w, a.output, r)


def cmd_reorder(a):
    r = open_reader(a.input, a.password)
    n = len(r.pages)
    order = parse_pages(a.order, n, allow_dupes=True) if a.order else list(range(n))
    if a.reverse:
        order = order[::-1]
    write(subset(r, order), a.output, r)


INPUTS = set()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--password")
    sub = ap.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("merge"); m.add_argument("inputs", nargs="+"); m.add_argument("-o", "--output", required=True)
    m.add_argument("--bookmarks", action="store_true", help="add one bookmark per input file"); m.set_defaults(fn=cmd_merge)
    s = sub.add_parser("split"); s.add_argument("input"); s.add_argument("-o", "--out-dir", help="default: split/ next to the input")
    g = s.add_mutually_exclusive_group(); g.add_argument("--every", type=int); g.add_argument("--ranges"); s.set_defaults(fn=cmd_split)
    e = sub.add_parser("extract"); e.add_argument("input"); e.add_argument("--pages", required=True); e.add_argument("-o", "--output", required=True); e.set_defaults(fn=cmd_extract)
    d = sub.add_parser("delete"); d.add_argument("input"); d.add_argument("--pages", required=True); d.add_argument("-o", "--output", required=True); d.set_defaults(fn=cmd_delete)
    ro = sub.add_parser("rotate"); ro.add_argument("input"); ro.add_argument("--angle", type=int, default=90); ro.add_argument("--pages")
    ro.add_argument("-o", "--output", required=True); ro.set_defaults(fn=cmd_rotate)
    rr = sub.add_parser("reorder"); rr.add_argument("input"); rr.add_argument("--order"); rr.add_argument("--reverse", action="store_true")
    rr.add_argument("-o", "--output", required=True); rr.set_defaults(fn=cmd_reorder)

    a = ap.parse_args()
    for attr in ("inputs", "input"):
        v = getattr(a, attr, None)
        if v:
            INPUTS.update(os.path.abspath(x) for x in (v if isinstance(v, list) else [v]))
    a.fn(a)


if __name__ == "__main__":
    main()
