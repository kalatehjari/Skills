#!/usr/bin/env python3
"""Build a clean, formatted workbook from CSV/JSON data (one sheet per input).

Per sheet: typed values (numbers/dates parsed from text when the whole column
parses), bold shaded header, frozen header row, filter or Excel Table, sensible
number formats, column widths, optional title row and a live totals row
(=SUBTOTAL/SUM formulas, not pasted numbers).

Usage:
    python xlsx_from_data.py results.csv [more.csv|data.json ...] -o book.xlsx
        [--sheet-names "Lab,Field"] [--table] [--totals sum|average] [--total-cols "Load (kN)"]
        [--title "Lab results — Lot 12"]
        [--decimals 2] [--date-format yyyy-mm-dd]
JSON input: a list of objects (keys become headers) or {"columns": [...], "rows": [[...]]}.
Number parsing: "12,500.5" (comma thousands groups) -> 12500.5; "1,5" is NOT a number
here and stays text (decimal commas: convert the file first). The totals row sits
directly BELOW the table/filter range: add new data rows inside the range (Excel
Tables grow when you type in the row under them) so SUBTOTAL and charts include them.
"""
import argparse
import csv
import datetime as dt
import json
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _xlsx_common  # noqa: E402,F401

from openpyxl import Workbook  # noqa: E402
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side  # noqa: E402
from openpyxl.utils import get_column_letter  # noqa: E402
from openpyxl.worksheet.table import Table, TableStyleInfo  # noqa: E402

NUM = re.compile(r"^[+-]?(\d{1,3}(,\d{3})+|\d+)(\.\d+)?([eE][+-]?\d+)?$")
DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%d %b %Y", "%d %B %Y")


def load(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".json":
        with open(path, encoding="utf-8") as fh:
            d = json.load(fh)
        if isinstance(d, dict) and "rows" in d:
            return list(d.get("columns") or []), [list(r) for r in d["rows"]]
        if isinstance(d, list) and d and isinstance(d[0], dict):
            cols = []
            for row in d:
                for k in row:
                    if k not in cols:
                        cols.append(k)
            return cols, [[row.get(k) for k in cols] for row in d]
        sys.exit(f"{path}: expected a list of objects or {{columns, rows}}")
    with open(path, encoding="utf-8-sig", newline="") as fh:
        sample = fh.read(4096)
        fh.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        except csv.Error:
            dialect = csv.excel
        rows = list(csv.reader(fh, dialect))
    rows = [r for r in rows if any(x.strip() for x in r)]
    return rows[0], rows[1:]


def parse_col(values):
    """Convert a column of strings to numbers or dates if (almost) every non-empty value parses."""
    present = [v for v in values if v not in (None, "")]
    if not present or not all(isinstance(v, str) for v in present):
        return values, None
    if all(NUM.match(v.strip()) for v in present):
        out = []
        for v in values:
            if v in (None, ""):
                out.append(None)
                continue
            t = v.strip().replace(",", "")
            out.append(int(t) if re.fullmatch(r"[+-]?\d+", t) else float(t))
        return out, "number"
    for f in DATE_FORMATS:
        try:
            parsed = [dt.datetime.strptime(v.strip(), f) if v not in (None, "") else None for v in values]
            return parsed, "date"
        except ValueError:
            continue
    return values, None


def decimals_of(col):
    d = 0
    for v in col:
        if isinstance(v, float):
            s = repr(v)
            if "e" not in s and "." in s:
                d = max(d, len(s.split(".")[1].rstrip("0")))
    return min(d, 4)


def build_sheet(ws, header, rows, a, sheet_name):
    width = max(len(header), max((len(r) for r in rows), default=0))
    header = list(header) + [f"col{j + 1}" for j in range(len(header), width)]
    rows = [list(r) + [None] * (width - len(r)) for r in rows]
    cols = list(zip(*rows)) if rows else [[] for _ in header]
    kinds = []
    for j in range(width):
        parsed, kind = parse_col(list(cols[j]))
        if kind is None and any(isinstance(v, (int, float)) and not isinstance(v, bool) for v in cols[j]):
            kind = "number"
            parsed = list(cols[j])
        for i, v in enumerate(parsed):
            rows[i][j] = v
        kinds.append(kind)

    top = 1
    if a.title:
        ws.cell(1, 1, a.title).font = Font(bold=True, size=13)
        top = 3
    thin = Side(style="thin", color="A6A6A6")
    for j, h in enumerate(header, start=1):
        c = ws.cell(top, j, h)
        c.font = Font(bold=True)
        c.fill = PatternFill("solid", fgColor="DCE6F1")
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = Border(bottom=thin)
    for i, r in enumerate(rows, start=top + 1):
        for j, v in enumerate(r, start=1):
            ws.cell(i, j, v)
    last = top + len(rows)
    for j, kind in enumerate(kinds, start=1):
        letter = get_column_letter(j)
        col_vals = [r[j - 1] for r in rows]
        if kind == "number":
            d = a.decimals if a.decimals is not None else decimals_of(col_vals)
            fmt = "#,##0" + ("." + "0" * d if d else "") if any(isinstance(v, (int, float)) and abs(v) >= 10000 for v in col_vals if v is not None) else ("0" + ("." + "0" * d if d else ""))
            for i in range(top + 1, last + 1):
                ws.cell(i, j).number_format = fmt
        elif kind == "date":
            for i in range(top + 1, last + 1):
                ws.cell(i, j).number_format = a.date_format
        def shown(v):
            if isinstance(v, (dt.date, dt.datetime)):
                return len(a.date_format)
            if isinstance(v, float):
                return len(f"{v:,.{a.decimals if a.decimals is not None else 2}f}")
            return len(str(v))
        longest = max([len(str(header[j - 1]))] + [shown(v) for v in col_vals if v is not None])
        ws.column_dimensions[letter].width = min(max(8, longest + 2), 60)
    ws.freeze_panes = ws.cell(top + 1, 1)
    ref = f"A{top}:{get_column_letter(width)}{max(last, top + 1)}"
    if a.table:
        name = re.sub(r"\W", "_", sheet_name) or "Table1"
        if name[0].isdigit():
            name = "T_" + name
        t = Table(displayName=name, ref=ref)
        t.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
        ws.add_table(t)
    else:
        ws.auto_filter.ref = ref
    if a.totals and rows:
        tr = last + 1
        ws.cell(tr, 1, "Total" if a.totals == "sum" else "Mean").font = Font(bold=True)
        fn = 9 if a.totals == "sum" else 1  # SUBTOTAL 9 = SUM, 1 = AVERAGE; ignores rows hidden by a filter
        for j, kind in enumerate(kinds, start=1):
            if kind == "number" and j > 1 and (not a.total_cols or header[j - 1] in a.total_cols):
                letter = get_column_letter(j)
                c = ws.cell(tr, j, f"=SUBTOTAL({fn},{letter}{top + 1}:{letter}{last})")
                c.font = Font(bold=True)
                c.number_format = ws.cell(last, j).number_format
                c.border = Border(top=thin)
    return len(rows), width


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--sheet-names")
    ap.add_argument("--table", action="store_true", help="format as an Excel Table (structured, banded)")
    ap.add_argument("--totals", choices=["sum", "average"])
    ap.add_argument("--total-cols", help="comma list of column headers to total (default: every numeric column)")
    ap.add_argument("--title")
    ap.add_argument("--decimals", type=int)
    ap.add_argument("--date-format", default="yyyy-mm-dd")
    a = ap.parse_args()
    names = [n.strip() for n in a.sheet_names.split(",")] if a.sheet_names else []
    a.total_cols = [c.strip() for c in a.total_cols.split(",")] if a.total_cols else None
    wb = Workbook()
    wb.remove(wb.active)
    for k, path in enumerate(a.inputs):
        name = (names[k] if k < len(names) else os.path.splitext(os.path.basename(path))[0])[:31]
        name = re.sub(r"[\[\]:*?/\\]", "_", name)
        header, rows = load(path)
        ws = wb.create_sheet(name)
        n, w = build_sheet(ws, header, rows, a, name)
        print(f"  sheet '{name}': {n} rows × {w} columns", file=sys.stderr)
    wb.calculation.fullCalcOnLoad = True  # Excel computes formulas on open
    wb.save(a.output)
    print(f"Wrote {a.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
