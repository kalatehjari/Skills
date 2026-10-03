#!/usr/bin/env python3
"""Summarise a workbook before working on it.

Per sheet: used range, rows × cols, header row guess, formulas vs constants,
error values (cached), merged cells, Excel tables, data validation, conditional
formats, charts, images, freeze panes, hidden state. Workbook: defined names,
external links, macros, calculation settings.

Usage:
    python xlsx_inspect.py book.xlsx [--json] [--sheet NAME] [--preview 5]
Cached values are what Excel last saved; run xlsx_recalc.py for fresh results.
"""
import argparse
import json
import os
import re
import sys
import zipfile
from collections import Counter

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _xlsx_common import ERROR_VALUES, pick_sheets  # noqa: E402

from openpyxl import load_workbook  # noqa: E402
from openpyxl.utils import get_column_letter  # noqa: E402


def header_guess(ws, max_rows=10):
    """First row (within the top 10) where most non-empty cells are text and the next row has data."""
    best = None
    for r in range(ws.min_row, min(ws.max_row, ws.min_row + max_rows) + 1):
        vals = [c.value for c in ws[r] if c.value is not None]
        if len(vals) >= 2 and sum(isinstance(v, str) for v in vals) / len(vals) >= 0.8:
            best = r
            break
    return best


def inspect(path, sheet_spec, preview, list_formulas=False):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".xls":
        sys.exit("Legacy .xls: convert first — python xlsx_convert.py book.xls --to xlsx")
    wb_f = load_workbook(path, data_only=False, keep_vba=ext == ".xlsm")
    wb_v = load_workbook(path, data_only=True, read_only=False)
    info = {"file": path, "sheets": []}
    for ws in pick_sheets(wb_f, sheet_spec):
        wv = wb_v[ws.title]
        formulas = constants = 0
        errors = Counter()
        no_cache = 0
        fn = Counter()
        formula_cells = []
        for row in ws.iter_rows():
            for c in row:
                v = c.value
                if v is None:
                    continue
                if c.data_type == "f" or (isinstance(v, str) and v.startswith("=")):
                    formulas += 1
                    for name in re.findall(r"([A-Z][A-Z0-9.]*)\(", re.sub(r'"[^"]*"', "", str(v).upper())):
                        fn[name.replace("_XLFN.", "")] += 1
                    formula_cells.append((c.coordinate, str(v)))
                    cv = wv[c.coordinate].value
                    if cv is None:
                        no_cache += 1
                    elif isinstance(cv, str) and cv in ERROR_VALUES:
                        errors[cv] += 1
                else:
                    constants += 1
                    if isinstance(v, str) and v in ERROR_VALUES:
                        errors[v] += 1
        hdr = header_guess(ws)
        s = {
            "name": ws.title,
            "state": ws.sheet_state,
            "dimensions": ws.dimensions,
            "rows": ws.max_row, "cols": ws.max_column,
            "header_row": hdr,
            "headers": [str(c.value) for c in ws[hdr] if c.value is not None][:30] if hdr else [],
            "formulas": formulas, "constants": constants,
            "formulas_without_cached_value": no_cache,
            "cached_errors": dict(errors),
            "functions": dict(fn.most_common()),
            "formula_cells": formula_cells if list_formulas else formula_cells[:0],
            "merged_ranges": [str(r) for r in ws.merged_cells.ranges][:20],
            "tables": {name: (ref if isinstance(ref, str) else ref.ref) for name, ref in ws.tables.items()},
            "data_validations": len(ws.data_validations.dataValidation) if ws.data_validations else 0,
            "conditional_formats": len(list(ws.conditional_formatting)),
            "charts": len(getattr(ws, "_charts", [])),
            "images": len(getattr(ws, "_images", [])),
            "freeze_panes": ws.freeze_panes,
            "autofilter": ws.auto_filter.ref,
        }
        if preview:
            start = hdr or ws.min_row
            end = min(ws.max_row, start + preview)
            s["preview"] = [[_short(wv.cell(r, c).value) for c in range(1, min(ws.max_column, 12) + 1)]
                            for r in range(start, end + 1)]
            s["preview_note"] = (f"rows {start}–{end} of {ws.max_row}" + (f", columns A–L of {ws.max_column}" if ws.max_column > 12 else "")
                                 + ("" if end >= ws.max_row else " (use xlsx_read.py for all rows)"))
        info["sheets"].append(s)
    info["defined_names"] = {n: str(d.attr_text) for n, d in list(wb_f.defined_names.items())[:40]}
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
    info["external_links"] = len([n for n in names if n.startswith("xl/externalLinks/")])
    info["has_macros"] = any(n.endswith("vbaProject.bin") for n in names)
    info["pivot_tables"] = len([n for n in names if n.startswith("xl/pivotTables/")])
    calc = wb_f.calculation
    info["calculation"] = {"mode": calc.calcMode or "auto", "recalculate_on_open": bool(calc.fullCalcOnLoad)}
    return info


def _short(v):
    import datetime as dt
    if isinstance(v, dt.datetime):
        return v.date().isoformat() if (v.hour, v.minute, v.second) == (0, 0, 0) else v.isoformat(sep=" ")
    if isinstance(v, float):
        return round(v, 6)
    if isinstance(v, str) and len(v) > 40:
        return v[:37] + "…"
    return v if isinstance(v, (int, float, str, type(None))) else str(v)


def print_human(i):
    print(f"File: {i['file']}")
    for s in i["sheets"]:
        flag = "" if s["state"] == "visible" else f" [{s['state']}]"
        print(f"\nSheet '{s['name']}'{flag}: {s['dimensions']} ({s['rows']}×{s['cols']}), "
              f"{s['formulas']} formulas, {s['constants']} constants")
        if s["header_row"]:
            print(f"  Header row {s['header_row']}: {s['headers'][:12]}")
        if s["cached_errors"]:
            print(f"  Errors (cached): {s['cached_errors']}")
        if s["formulas_without_cached_value"]:
            print(f"  {s['formulas_without_cached_value']} formula(s) have no cached value (file written by a script) — run xlsx_recalc.py to see results")
        if s["functions"]:
            print(f"  Functions: {s['functions']}")
        extras = [f"{k.replace('_', ' ')}: {s[k]}" for k in ("tables", "merged_ranges", "freeze_panes", "autofilter") if s[k]]
        extras += [f"{k.replace('_', ' ')}: {s[k]}" for k in ("data_validations", "conditional_formats", "charts", "images") if s[k]]
        for e in extras:
            print("  " + e)
        if s.get("preview"):
            print(f"  Preview ({s['preview_note']}):")
        for row in s.get("preview", []):
            print("  | " + " | ".join("" if v is None else str(v) for v in row))
        if s["formula_cells"]:
            print("  Formulas:")
            for coord, f in s["formula_cells"]:
                print(f"    {coord}: {f}")
    if i["defined_names"]:
        print(f"\nDefined names: {i['defined_names']}")
    flags = [f"{i['external_links']} external link(s)" if i["external_links"] else "", "macros (VBA)" if i["has_macros"] else "",
             f"{i['pivot_tables']} pivot table(s)" if i["pivot_tables"] else ""]
    flags = [f for f in flags if f]
    if flags:
        print("Contains: " + ", ".join(flags))
    print(f"Calculation: {i['calculation']}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("xlsx")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--sheet")
    ap.add_argument("--preview", type=int, default=5, help="rows to preview per sheet (0 = none)")
    ap.add_argument("--formulas", action="store_true", help="list every formula cell with its address")
    a = ap.parse_args()
    info = inspect(a.xlsx, a.sheet, a.preview, a.formulas)
    if a.json:
        print(json.dumps(info, indent=2, ensure_ascii=False, default=str))
    else:
        print_human(info)


if __name__ == "__main__":
    main()
