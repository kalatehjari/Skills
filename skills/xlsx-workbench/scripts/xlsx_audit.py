#!/usr/bin/env python3
"""Audit a spreadsheet for the mistakes that most often corrupt results.

Checks
  errors        formula results that are errors (#DIV/0!, #REF!, #N/A ...) — after a
                LibreOffice recalculation (use --no-recalc to trust cached values)
  inconsistent  a formula that differs from its neighbours in the same column/row block
                (e.g. =D8-E8+0 among =Dn-En), after normalising relative references
  hardcoded     a typed number sitting inside a block of formulas (an overwritten formula)
  blank-ref     a formula that points at an empty cell (often a shifted reference)
  text-number   numbers stored as text in a numeric column (ignored by SUM/AVERAGE)
  magic-number  literal constants inside formulas (=B2*1.15) — listed for review
  suspicious    data-level red flags in numeric columns: a 0 among clearly non-zero values
                (often a missing value typed as 0) and outliers more than 3 standard
                deviations from the column mean (needs ≥ 8 values). Mechanical checks
                can't judge physical plausibility — review flagged values with the user.

Usage:
    python xlsx_audit.py model.xlsx [--sheet NAME] [--json] [--no-recalc] [--only errors,inconsistent]
Exit code 0 always (it's a report); use --fail-on errors,inconsistent in pipelines.
"""
import argparse
import json
import os
import re
import sys
import tempfile
from collections import Counter

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _xlsx_common import ERROR_VALUES, pick_sheets, recalculated_copy, soffice  # noqa: E402

from openpyxl import load_workbook  # noqa: E402
from openpyxl.formula.translate import Translator  # noqa: E402
from openpyxl.utils import get_column_letter  # noqa: E402

REF = re.compile(r"(?<![A-Za-z_!'\":$])(\$?[A-Z]{1,3}\$?\d+)(?![\d(:A-Za-z!])")  # single cells, not range ends
NUM_LIT = re.compile(r"(?<![A-Za-z_$\d.:])(\d+\.?\d*(?:[eE][+-]?\d+)?)(?![\d(:A-Za-z!])")
BENIGN = {"0", "1", "2", "10", "12", "24", "60", "100", "1000", "365", "0.5"}


def is_formula(c):
    return c.data_type == "f" or (isinstance(c.value, str) and c.value.startswith("="))


def norm(formula, origin, dest):
    try:
        return Translator(formula, origin=origin).translate_formula(dest)
    except Exception:
        return formula


def blocks(cells):
    """Split a list of cells (one column or row) into runs of consecutive non-empty cells."""
    run = []
    for c in cells:
        if c.value is None:
            if run:
                yield run
            run = []
        else:
            run.append(c)
    if run:
        yield run


def audit_lines(lines, findings, seen):
    for run in blocks(lines):
        f_cells = [c for c in run if is_formula(c)]
        if len(f_cells) < 3:
            continue
        ref0 = f_cells[0].coordinate
        pats = {c.coordinate: norm(str(c.value), c.coordinate, ref0) for c in f_cells}
        common, count = Counter(pats.values()).most_common(1)[0]
        if count < max(3, 0.6 * len(f_cells)):
            continue
        sample = next(c for c in f_cells if pats[c.coordinate] == common)
        for c in f_cells:
            if pats[c.coordinate] != common and c.coordinate not in seen:
                expected = norm(str(sample.value), sample.coordinate, c.coordinate)
                findings.append({"check": "inconsistent", "cell": c.coordinate, "formula": str(c.value),
                                 "note": f"neighbours use the pattern {expected}"})
                seen.add(c.coordinate)
        for c in run:
            if not is_formula(c) and isinstance(c.value, (int, float)) and c.coordinate not in seen:
                expected = norm(str(sample.value), sample.coordinate, c.coordinate)
                findings.append({"check": "hardcoded", "cell": c.coordinate, "value": c.value,
                                 "note": f"typed value inside a block of formulas; expected something like {expected}"})
                seen.add(c.coordinate)


def suspicious_values(ws, vs):
    """Zeros among clearly non-zero numbers, and |z| > 3 outliers, per column block (header excluded)."""
    import statistics
    out = []
    src = vs if vs is not None else ws
    for col in src.iter_cols(min_row=src.min_row, max_row=src.max_row):
        for run in blocks(list(col)):
            nums = [c for c in run if isinstance(c.value, (int, float)) and not isinstance(c.value, bool)]
            if len(nums) < 4:
                continue
            values = [c.value for c in nums]
            nonzero = [v for v in values if v != 0]
            if nonzero and len(nonzero) < len(values) and all(v > 0 for v in nonzero) \
                    and min(nonzero) > 0.2 * statistics.fmean(nonzero):
                for c in nums:
                    if c.value == 0:
                        out.append({"check": "suspicious", "cell": c.coordinate, "value": 0,
                                    "note": f"0 among values {min(nonzero):g}–{max(nonzero):g}; missing data typed as 0? "
                                            "it also affects averages/totals that include it"})
            if len(values) >= 8:
                mu, sd = statistics.fmean(values), statistics.pstdev(values)
                if sd > 0:
                    for c in nums:
                        z = (c.value - mu) / sd
                        if abs(z) > 3:
                            out.append({"check": "suspicious", "cell": c.coordinate, "value": c.value,
                                        "note": f"outlier: {z:+.1f} SD from the column mean {mu:.4g}"})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("xlsx")
    ap.add_argument("--sheet")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-recalc", action="store_true")
    ap.add_argument("--only", help="comma list of checks to run")
    ap.add_argument("--fail-on", help="comma list of checks that make the exit code 1")
    a = ap.parse_args()
    only = set(a.only.split(",")) if a.only else None

    wf = load_workbook(a.xlsx, data_only=False)
    with tempfile.TemporaryDirectory() as tmp:
        recalc_note = ""
        if not a.no_recalc and soffice():
            wv = load_workbook(recalculated_copy(a.xlsx, tmp), data_only=True)
            recalc_note = "values recalculated with LibreOffice"
        else:
            wv = load_workbook(a.xlsx, data_only=True)
            recalc_note = "using cached values (not recalculated)"

        report = []
        for ws in pick_sheets(wf, a.sheet):
            vs = wv[ws.title] if ws.title in wv.sheetnames else None
            findings, seen = [], set()
            want = lambda k: only is None or k in only  # noqa: E731
            if want("inconsistent") or want("hardcoded"):
                for col in ws.iter_cols(min_row=ws.min_row, max_row=ws.max_row):
                    audit_lines(list(col), findings, seen)
                for row in ws.iter_rows():
                    audit_lines(list(row), findings, seen)
                if only:
                    findings = [f for f in findings if f["check"] in only]
            for row in ws.iter_rows():
                for c in row:
                    if is_formula(c):
                        f = str(c.value)
                        if want("errors") and vs is not None:
                            v = vs[c.coordinate].value
                            if isinstance(v, str) and v in ERROR_VALUES:
                                findings.append({"check": "errors", "cell": c.coordinate, "formula": f, "value": v})
                        if want("blank-ref"):
                            body = re.sub(r'"[^"]*"', "", f)
                            for m in REF.finditer(body):
                                start = m.start()
                                if start > 0 and body[start - 1] == "!":
                                    continue  # other-sheet ref; skipped for simplicity
                                ref = m.group(1).replace("$", "")
                                try:
                                    target = ws[ref]
                                except Exception:
                                    continue
                                if target.value is None:
                                    findings.append({"check": "blank-ref", "cell": c.coordinate, "formula": f,
                                                     "note": f"{ref} is empty"})
                        if want("magic-number"):
                            body = re.sub(r'"[^"]*"', "", f)
                            body = re.sub(r"(?i)\b(SUBTOTAL|AGGREGATE)\(\s*\d+\s*,(\s*\d+\s*,)?", r"\1(", body)  # function codes
                            lits = [x for x in NUM_LIT.findall(body) if x not in BENIGN]
                            if lits:
                                findings.append({"check": "magic-number", "cell": c.coordinate, "formula": f,
                                                 "note": "literal(s) " + ", ".join(lits) + " — consider an input cell"})
                    elif want("text-number") and isinstance(c.value, str):
                        t = c.value.strip().replace(",", "")
                        if re.fullmatch(r"-?\d+(\.\d+)?", t):
                            col = [x.value for x in ws[get_column_letter(c.column)] if x.row != c.row]
                            nums = sum(isinstance(x, (int, float)) for x in col)
                            if nums >= 2:
                                findings.append({"check": "text-number", "cell": c.coordinate, "value": c.value,
                                                 "note": "number stored as text in a numeric column"})
            if want("suspicious"):
                findings += suspicious_values(ws, vs)
            order = ["errors", "inconsistent", "hardcoded", "blank-ref", "text-number", "suspicious", "magic-number"]
            findings.sort(key=lambda f: (order.index(f["check"]), f["cell"]))
            report.append({"sheet": ws.title, "findings": findings})

    total = Counter(f["check"] for s in report for f in s["findings"])
    if a.json:
        print(json.dumps({"note": recalc_note, "summary": dict(total), "sheets": report}, indent=2, default=str, ensure_ascii=False))
    else:
        print(f"Audit of {os.path.basename(a.xlsx)} ({recalc_note}): " + (", ".join(f"{v} {k}" for k, v in total.items()) or "no issues found"))
        for s in report:
            if not s["findings"]:
                continue
            print(f"\n[{s['sheet']}]")
            for f in s["findings"]:
                detail = f.get("formula") or f.get("value")
                extra = f" → {f['value']}" if f["check"] == "errors" else ""
                print(f"  {f['check']:<13} {f['cell']:<7} {detail}{extra}" + (f"   ({f['note']})" if f.get("note") else ""))
    if a.fail_on and any(total.get(k) for k in a.fail_on.split(",")):
        sys.exit(1)


if __name__ == "__main__":
    main()
