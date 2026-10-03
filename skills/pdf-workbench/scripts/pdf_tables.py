#!/usr/bin/env python3
"""Extract tables from a PDF with pdfplumber.

Output formats:
  csv   one CSV per table in --out-dir (default: ./tables)
  xlsx  one workbook (-o), one sheet per table, named p<page>_t<n>, plus an
        'Index' sheet with page and caption ("Table 3. ...") for each
  md    Markdown tables to stdout (or -o) — handy for a quick look
  json  list of {page, index, bbox, rows} to stdout (or -o)

Strategies:
  lines (default)  uses ruling lines drawn in the PDF — best for bordered tables
  text             infers columns from text alignment — for borderless tables

Usage:
    python pdf_tables.py in.pdf [--pages 3-5] [--format csv|xlsx|md|json]
                         [-o out] [--out-dir dir] [--strategy lines|text]
                         [--min-rows 2] [--password PW]
"""
import argparse
import csv
import json
import os
import re
import sys

try:
    import pdfplumber
except ImportError:
    sys.exit("pdfplumber is required: pip install pdfplumber")


def parse_pages(spec, n):
    if not spec:
        return list(range(n))
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
        out += [i for i in range(start - 1, end) if i not in out]
    return out


def clean(cell):
    if cell is None:
        return ""
    return " ".join(str(cell).split())


def extract(path, pages, strategy, min_rows, password):
    settings = {"vertical_strategy": strategy, "horizontal_strategy": strategy}
    if strategy == "text":
        settings.update({"snap_tolerance": 3, "join_tolerance": 3, "intersection_tolerance": 5})
    found = []
    with pdfplumber.open(path, password=password or None) as pdf:
        for i in parse_pages(pages, len(pdf.pages)):
            page = pdf.pages[i]
            for t_idx, table in enumerate(page.find_tables(table_settings=settings), start=1):
                rows = [[clean(c) for c in row] for row in table.extract()]
                rows = [r for r in rows if any(r)]
                if len(rows) < min_rows:
                    continue
                width = max(len(r) for r in rows)
                rows = [r + [""] * (width - len(r)) for r in rows]
                # drop columns that are empty in every row
                keep = [c for c in range(width) if any(r[c] for r in rows)]
                rows = [[r[c] for c in keep] for r in rows]
                found.append({"page": i + 1, "index": t_idx, "bbox": [round(v, 1) for v in table.bbox],
                              "caption": find_caption(page, table.bbox), "rows": rows})
    return found


CAPTION_RE = re.compile(r"^(Table|Tab\.|TABLE)\s*[A-Z]?\d+", re.I)


def find_caption(page, bbox, reach=60):
    """Return the 'Table N ...' line just above (or failing that, below) a table, else ''."""
    x0, top, x1, bottom = bbox
    words = page.extract_words(keep_blank_chars=True, use_text_flow=True)
    lines = {}
    for w in words:
        lines.setdefault(round(w["top"]), []).append(w)
    candidates = []
    for t, ws in lines.items():
        text = " ".join(w["text"] for w in sorted(ws, key=lambda w: w["x0"])).strip()
        if not CAPTION_RE.match(text):
            continue
        b = max(w["bottom"] for w in ws)
        if 0 <= top - b <= reach:
            candidates.append((top - b, text))
        elif 0 <= t - bottom <= reach:
            candidates.append((t - bottom + reach, text))  # below: lower priority
    return min(candidates)[1] if candidates else ""


def to_markdown(t):
    rows = t["rows"]
    esc = lambda s: s.replace("|", "\\|")
    head = "| " + " | ".join(esc(c) for c in rows[0]) + " |"
    sep = "| " + " | ".join("---" for _ in rows[0]) + " |"
    body = ["| " + " | ".join(esc(c) for c in r) + " |" for r in rows[1:]]
    cap = f" — {t['caption']}" if t.get("caption") else ""
    return f"**Page {t['page']}, table {t['index']}**{cap} ({len(rows)} rows × {len(rows[0])} cols)\n\n" + "\n".join([head, sep] + body)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("--pages")
    ap.add_argument("--format", choices=["csv", "xlsx", "md", "json"], default="csv")
    ap.add_argument("-o", "--output", help="output file (xlsx/md/json)")
    ap.add_argument("--out-dir", help="directory for CSV files (default: tables/ next to the PDF)")
    ap.add_argument("--strategy", choices=["lines", "text"], default="lines")
    ap.add_argument("--min-rows", type=int, default=2)
    ap.add_argument("--password")
    a = ap.parse_args()

    tables = extract(a.pdf, a.pages, a.strategy, a.min_rows, a.password)
    if not tables:
        hint = " Try --strategy text for borderless tables." if a.strategy == "lines" else ""
        print(f"No tables found.{hint} If the page is a scan, OCR it first.", file=sys.stderr)
        sys.exit(1)

    if a.format == "csv":
        a.out_dir = a.out_dir or os.path.join(os.path.dirname(os.path.abspath(a.pdf)), "tables")
        os.makedirs(a.out_dir, exist_ok=True)
        for t in tables:
            fn = os.path.join(a.out_dir, f"page{t['page']:03d}_table{t['index']}.csv")
            with open(fn, "w", newline="", encoding="utf-8") as fh:
                csv.writer(fh).writerows(t["rows"])
        print(f"Wrote {len(tables)} CSV file(s) to {a.out_dir}/", file=sys.stderr)
    elif a.format == "xlsx":
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font
        except ImportError:
            sys.exit("openpyxl is required for xlsx: pip install openpyxl")
        out = a.output or os.path.splitext(os.path.abspath(a.pdf))[0] + "_tables.xlsx"
        wb = Workbook()
        idx = wb.active
        idx.title = "Index"
        idx.append(["Sheet", "Page", "Caption", "Rows", "Cols"])
        for t in tables:
            name = f"p{t['page']}_t{t['index']}"[:31]
            idx.append([name, t["page"], t.get("caption", ""), len(t["rows"]), len(t["rows"][0])])
            ws = wb.create_sheet(name)
            for r_i, r in enumerate(t["rows"], start=1):
                vals = [_num(c) for c in r]
                for c_i, (raw, v) in enumerate(zip(r, vals), start=1):
                    if isinstance(v, (int, float)) and "," in raw:
                        THOUSANDS_SEEN.append(f"{name}!{ws.cell(row=r_i, column=c_i).column_letter}{r_i}: '{raw}' -> {v}")
                ws.append(vals)
            for cell in ws[1]:
                cell.font = Font(bold=True)
            for col in ws.columns:
                ws.column_dimensions[col[0].column_letter].width = min(60, max(8, max(len(str(c.value or "")) for c in col) + 2))
        for cell in idx[1]:
            cell.font = Font(bold=True)
        idx.column_dimensions["C"].width = 60
        wb.save(out)
        print(f"Wrote {len(tables)} table(s) to {out} (sheet 'Index' lists pages and captions)", file=sys.stderr)
        if THOUSANDS_SEEN:
            print("Check: these cells had a comma read as a thousands separator:", file=sys.stderr)
            for line in THOUSANDS_SEEN[:20]:
                print("  " + line, file=sys.stderr)
    else:
        text = "\n\n".join(to_markdown(t) for t in tables) if a.format == "md" else json.dumps(tables, indent=2, ensure_ascii=False)
        if a.output:
            with open(a.output, "w", encoding="utf-8") as fh:
                fh.write(text + "\n")
            print(f"Wrote {len(tables)} table(s) to {a.output}", file=sys.stderr)
        else:
            print(text)

    for t in tables:
        cap = f"  [{t['caption'][:60]}]" if t.get("caption") else ""
        print(f"  page {t['page']} table {t['index']}: {len(t['rows'])}×{len(t['rows'][0])}{cap}", file=sys.stderr)


THOUSANDS_SEEN = []
_PLAIN = re.compile(r"^-?\d+(\.\d+)?$")
_THOUSANDS = re.compile(r"^-?\d{1,3}(,\d{3})+(\.\d+)?$")


def _num(s):
    """Store numeric-looking cells as numbers so Excel can compute with them.

    Only unambiguous forms are converted: 12, -3.5, 1,234.5. Anything else
    (e.g. '1,5' decimal comma, '12 ± 3', '5%') stays text so nothing is silently altered.
    """
    t = s.replace("−", "-").strip()
    if _PLAIN.match(t) or _THOUSANDS.match(t):
        t = t.replace(",", "")
        return float(t) if "." in t else int(t)
    return s


if __name__ == "__main__":
    main()
