#!/usr/bin/env python3
"""Convert spreadsheets, and render sheets to PNG for a visual check.

  python xlsx_convert.py old.xls --to xlsx              # .xls / .ods / .csv -> .xlsx (LibreOffice)
  python xlsx_convert.py book.xlsx --to csv [--sheet Lab]   # one CSV per sheet (or just --sheet)
  python xlsx_convert.py book.xlsx --to pdf             # LibreOffice; uses each sheet's print setup
  python xlsx_convert.py book.xlsx --to png [--dpi 110] # via PDF; one PNG per page
  add --fit to pdf/png: each sheet scaled to one page wide, landscape (no charts cut in half)
  python xlsx_convert.py book.xlsx --to ods|html

Outputs go next to the input unless -o is given (file, or folder for csv/png).
Formulas are recalculated during LibreOffice conversions. CSV export writes
values (recalculated), never formulas.
"""
import argparse
import csv
import datetime as dt
import os
import sys
import tempfile

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _xlsx_common import lo_convert, pick_sheets, recalculated_copy, soffice  # noqa: E402

from openpyxl import load_workbook  # noqa: E402


def to_csv(src, sheet_spec, out_dir, recalc):
    with tempfile.TemporaryDirectory() as tmp:
        path = recalculated_copy(src, tmp) if recalc and soffice() else src
        wb = load_workbook(path, data_only=True, read_only=True)
        os.makedirs(out_dir, exist_ok=True)
        base = os.path.splitext(os.path.basename(src))[0]
        for ws in pick_sheets(wb, sheet_spec):
            fn = os.path.join(out_dir, f"{base}_{ws.title}.csv".replace("/", "_"))
            with open(fn, "w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)
                for row in ws.iter_rows(values_only=True):
                    w.writerow(["" if v is None else (v.isoformat() if isinstance(v, (dt.date, dt.datetime)) else v) for v in row])
            print(fn)


def fitted_copy(src, tmp):
    """Copy with every sheet set to print 1 page wide, landscape (the input is untouched)."""
    wb = load_workbook(src, keep_vba=src.lower().endswith(".xlsm"))
    for ws in wb.worksheets:
        ws.page_setup.orientation = "landscape"
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
    out = os.path.join(tmp, "fit_" + os.path.basename(src))
    wb.save(out)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("--to", required=True, choices=["xlsx", "csv", "pdf", "png", "ods", "html"])
    ap.add_argument("-o", "--output")
    ap.add_argument("--sheet", help="csv: only these sheets")
    ap.add_argument("--dpi", type=int, default=110)
    ap.add_argument("--no-recalc", action="store_true", help="csv: use cached values as saved")
    ap.add_argument("--fit", action="store_true", help="pdf/png: fit each sheet to one page wide, landscape")
    a = ap.parse_args()
    src = os.path.abspath(a.input)
    if not os.path.exists(src):
        sys.exit(f"Input not found: {a.input}")
    here = os.path.dirname(src)
    base = os.path.splitext(os.path.basename(src))[0]

    if a.to == "csv":
        to_csv(src, a.sheet, a.output or here, not a.no_recalc)
        return
    if a.to == "png":
        try:
            import pypdfium2 as pdfium
        except ImportError:
            sys.exit("pip install pypdfium2 to render PNGs")
        out_dir = a.output or os.path.join(here, "renders")
        os.makedirs(out_dir, exist_ok=True)
        with tempfile.TemporaryDirectory() as tmp:
            pdf = lo_convert(fitted_copy(src, tmp) if a.fit else src, "pdf", tmp)
            doc = pdfium.PdfDocument(pdf)
            for i in range(len(doc)):
                fn = os.path.join(out_dir, f"{base}_p{i + 1:03d}.png")
                doc[i].render(scale=a.dpi / 72).to_pil().save(fn)
                print(fn)
            doc.close()
        return
    with tempfile.TemporaryDirectory() as tmp:
        out = lo_convert(fitted_copy(src, tmp) if (a.fit and a.to == "pdf") else src, a.to, tmp)
        dest = a.output or os.path.join(here, f"{base}.{a.to}")
        if os.path.abspath(dest) == src:
            sys.exit("Refusing to overwrite the input; give -o")
        __import__("shutil").move(out, dest)
    print(f"Wrote {dest}", file=sys.stderr)


if __name__ == "__main__":
    main()
