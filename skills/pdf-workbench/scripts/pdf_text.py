#!/usr/bin/env python3
"""Extract text from a PDF, page by page.

Engines:
  plumber   (default) pdfplumber, good reading order, supports --layout and --columns
  pypdf     fast, no extra dependencies beyond pypdf
  pdftotext poppler's CLI, excellent --layout fidelity if installed

Usage:
    python pdf_text.py in.pdf [-o out.txt] [--pages 1-3,7] [--layout]
                       [--columns 2] [--engine plumber|pypdf|pdftotext]
                       [--no-markers] [--password PW]

--columns N splits each page into N equal-width vertical strips and reads them
left to right — use it for two-column journal articles where the default
reading order interleaves lines from both columns.

--header PT (with --columns) first reads the top PT points of each page at full
width (title, authors, DOI line), then splits only the area below into columns.
Typical first pages need 120-250 pt; find the value with pdf_render.py --grid
(header height = page height - y where the columns start).
"""
import argparse
import shutil
import subprocess
import sys


def parse_pages(spec, n):
    """'1-3,7,10-' -> [0,1,2,6,9..n-1] (0-based, in order given, no duplicates)."""
    if not spec:
        return list(range(n))
    out = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            start = int(a) if a else 1
            end = int(b) if b else n
        else:
            start = end = int(part)
        if start < 1 or end > n or start > end:
            sys.exit(f"Page range '{part}' is outside 1-{n}")
        for i in range(start - 1, end):
            if i not in out:
                out.append(i)
    return out


def extract_plumber(path, idxs, layout, columns, password, header=0.0):
    import pdfplumber
    texts = []
    with pdfplumber.open(path, password=password or None) as pdf:
        for i in idxs:
            page = pdf.pages[i]
            if columns and columns > 1:
                w = page.width
                top = min(max(header or 0.0, 0.0), page.height)
                parts = []
                if top:
                    head = page.crop((0, 0, w, top), relative=False, strict=False)
                    parts.append(head.extract_text(layout=layout) or "")
                for c in range(columns):
                    crop = page.crop((w * c / columns, top, w * (c + 1) / columns, page.height), relative=False, strict=False)
                    parts.append(crop.extract_text(layout=layout) or "")
                texts.append("\n\n".join(p.strip("\n") for p in parts))
            else:
                texts.append(page.extract_text(layout=layout) or "")
    return texts


def extract_pypdf(path, idxs, layout, password):
    from pypdf import PdfReader
    r = PdfReader(path)
    if r.is_encrypted:
        r.decrypt(password or "")
    out = []
    for i in idxs:
        try:
            out.append(r.pages[i].extract_text(extraction_mode="layout" if layout else "plain") or "")
        except TypeError:  # very old pypdf
            out.append(r.pages[i].extract_text() or "")
    return out


def extract_pdftotext(path, idxs, layout, password):
    if not shutil.which("pdftotext"):
        sys.exit("pdftotext not found (install poppler-utils) — use --engine plumber instead")
    out = []
    for i in idxs:
        cmd = ["pdftotext", "-f", str(i + 1), "-l", str(i + 1), "-enc", "UTF-8"]
        if layout:
            cmd.append("-layout")
        if password:
            cmd += ["-upw", password]
        cmd += [path, "-"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            sys.exit(f"pdftotext failed: {res.stderr.strip()}")
        out.append(res.stdout.rstrip("\f"))
    return out


def page_count(path, password):
    from pypdf import PdfReader
    r = PdfReader(path)
    if r.is_encrypted:
        if not r.decrypt(password or ""):
            sys.exit("PDF is encrypted; pass --password")
    return len(r.pages)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("-o", "--output", help="write to this file instead of stdout")
    ap.add_argument("--pages", help="page spec, 1-based, e.g. 1-3,7,10-")
    ap.add_argument("--layout", action="store_true", help="preserve horizontal layout (tables of numbers, forms)")
    ap.add_argument("--columns", type=int, default=0, help="read N equal-width columns left→right (plumber engine)")
    ap.add_argument("--header", type=float, default=0.0, help="with --columns: read the top PT points full-width first")
    ap.add_argument("--engine", choices=["plumber", "pypdf", "pdftotext"], default="plumber")
    ap.add_argument("--no-markers", action="store_true", help="omit '=== Page N ===' separators")
    ap.add_argument("--password")
    a = ap.parse_args()

    n = page_count(a.pdf, a.password)
    idxs = parse_pages(a.pages, n)
    if a.columns and a.engine != "plumber":
        sys.exit("--columns works only with --engine plumber")

    if a.engine == "plumber":
        try:
            texts = extract_plumber(a.pdf, idxs, a.layout, a.columns, a.password, a.header)
        except ImportError:
            print("pdfplumber not installed; falling back to pypdf", file=sys.stderr)
            texts = extract_pypdf(a.pdf, idxs, a.layout, a.password)
    elif a.engine == "pypdf":
        texts = extract_pypdf(a.pdf, idxs, a.layout, a.password)
    else:
        texts = extract_pdftotext(a.pdf, idxs, a.layout, a.password)

    empty = [i + 1 for i, t in zip(idxs, texts) if len(t.strip()) < 25]
    chunks = []
    for i, t in zip(idxs, texts):
        chunks.append(t if a.no_markers else f"=== Page {i + 1} ===\n{t}")
    result = "\n\n".join(chunks).rstrip() + "\n"

    if a.output:
        with open(a.output, "w", encoding="utf-8") as fh:
            fh.write(result)
        print(f"Wrote {len(idxs)} page(s), {len(result)} characters to {a.output}", file=sys.stderr)
    else:
        sys.stdout.write(result)
    if empty:
        print(f"Warning: little or no text on page(s) {empty} — likely scanned or image-only; consider pdf_ocr.py", file=sys.stderr)


if __name__ == "__main__":
    main()
