# Formulas, recalculation and checking

## Contents
1. Writing formulas with openpyxl
2. Recalculating: why and how
3. The audit checks and what to do about each
4. Formula patterns that hold up
5. LibreOffice fidelity notes

## 1. Writing formulas with openpyxl

```python
from openpyxl import load_workbook
wb = load_workbook("lab.xlsx")
ws = wb["Lab"]
for r in range(4, ws.max_row + 1):
    if ws[f"D{r}"].value is not None:
        ws[f"F{r}"] = f"=D{r}-E{r}"                  # PI = LL − PL
ws["F10"] = "=AVERAGE(F4:F8)"
ws["H1"] = "Load factor"; ws["I1"] = 1.15         # an input cell…
ws["G4"] = "=C4*$I$1"                             # …referenced absolutely, not typed into the formula
wb.calculation.fullCalcOnLoad = True              # Excel recalculates everything when the file opens
wb.save("lab_v2.xlsx")
```

- Write formulas in English with comma separators (`=IF(A1>0,1,0)`), whatever the user's Excel locale. Files store them that way, and Excel displays them in the user's locale.
- Use only functions that exist in the user's Excel version. `XLOOKUP`, `FILTER`, `UNIQUE`, `LET` and `LAMBDA` need Excel 365 or 2021+. For older versions, and for LibreOffice recalculation, prefer `INDEX/MATCH`, `SUMIFS` and `COUNTIFS`. If LibreOffice reports `#NAME?` for a newer function, that's the reason.
- Dynamic-array formulas need `ws["A1"] = ArrayFormula("A1:A10", "=…")` in openpyxl, or they spill only in Excel 365. Avoid them unless the user is on 365.
- Text in formulas uses double quotes: `'=COUNTIFS(A:A,"BH1*")'`.

## 2. Recalculating: why and how

openpyxl saves formulas without results. Excel calculates them when the file opens (with `fullCalcOnLoad`). But you, previews, `pandas.read_excel` and `data_only=True` all see **nothing**, or stale numbers from the last Excel save.

```bash
python scripts/xlsx_recalc.py model.xlsx                               # count formulas, list every error
python scripts/xlsx_recalc.py model.xlsx --cells "Summary!B2:C6"       # print results you will report
python scripts/xlsx_recalc.py model.xlsx --write model_final.xlsx      # your file + cached results (keeps all features)
python scripts/xlsx_recalc.py model.xlsx --write-lo model_lo.xlsx      # LibreOffice's own re-save (section 5)
python scripts/xlsx_read.py model.xlsx --recalc --format csv           # read fresh values as data
```

The script makes LibreOffice recalculate every formula on load. By default LibreOffice would keep Excel's cached values. The input is never modified.

`--write` copies your file byte for byte and inserts only the computed `<v>` values into formula cells. It's the right file to deliver: previews, pandas and `data_only=True` see numbers, and nothing Excel-specific is lost. Excel recalculates on open anyway. `--write-lo` saves LibreOffice's own re-save, which you should rarely need (see section 5).

## 3. The audit checks and what to do about each

```bash
python scripts/xlsx_audit.py model.xlsx [--sheet Calc] [--json]
```

| Check | Typical cause | Action |
|---|---|---|
| `errors` | division by an empty or zero cell, a lookup key missing, deleted rows (`#REF!`), unsupported function (`#NAME?`) | Fix the cause. Wrap a formula in `IFERROR` only when an error is an expected state, and say so |
| `inconsistent` | one formula in a column differs from its neighbours, often a one-off edit or a reference that drifted | Show the user the expected pattern. Fix it if it's clearly a slip; ask if it might be deliberate |
| `hardcoded` | a number typed over a formula ("just for now") | Restore the formula, or move the override into a labelled input cell |
| `blank-ref` | the formula points at an empty cell: a shifted reference, or a missing input | Check whether the reference should be elsewhere or the input is missing |
| `text-number` | a value imported as text, `'29.9`; SUM and AVERAGE silently ignore it | Convert it: `ws["C7"] = float(ws["C7"].value)` |
| `suspicious` | a 0 among clearly non-zero values (a missing value typed as 0), or a value more than 3 SD from its column mean | Ask the user. Never change the data. Point out which averages and totals include it |
| `magic-number` | constants inside formulas (`*1.15`, `/9.81`). SUBTOTAL and AGGREGATE function codes are ignored | Fine for physical constants if they're labelled. Otherwise move them to input cells |

When reporting, give the most serious issues first, which are errors and overwritten formulas, then each with its cell reference and what you'd change. Don't fix things silently in someone else's model.

**Plausibility review.** Do this after the audit, and use your own domain knowledge. Mechanical checks pass a perfectly calculated wrong number, so look at the values themselves:
- Look for impossible or unlikely values. In lab and engineering data that means negative thicknesses, percentages over 100 where they can't occur, a plastic limit of 0 (usually "non-plastic" or missing), PI larger than LL, densities or unit weights outside normal ranges, and factors of safety below 1 on a "stable" slope.
- Check units: a column of depths in mm among m values, or kPa mixed with MPa.
- Look for missing data entered as 0, which `suspicious` flags. Also look for blanks treated as zero by AVERAGE, and repeated copy-paste values.
- Check what summary rows actually include, such as means that take in a flagged row or totals that miss new rows.
- Ask about anything that matters before changing it, and say which results it affects.

## 4. Formula patterns that hold up

| Need | Robust formula |
|---|---|
| Lookup (any version) | `=INDEX(Data!C:C, MATCH(A2, Data!A:A, 0))` |
| Lookup with a default | `=IFERROR(INDEX(…,MATCH(…,0)), "not found")` |
| Conditional sum/count/mean | `=SUMIFS(D:D, A:A, "BH1*", B:B, ">=2")`, `COUNTIFS`, `AVERAGEIFS` |
| Totals that respect filters | `=SUBTOTAL(9, D4:D200)` for sum, `1` for average |
| Safe division | `=IF(E4=0, "", D4/E4)` |
| Rounding for display only | Keep full precision and set `number_format = "0.00"`. Use `ROUND()` only when the rounded value feeds later steps by rule (for example design values) |
| Interpolation (linear) | `=FORECAST.LINEAR(x, known_ys, known_xs)` for a fit, or `=y1+(x-x1)*(y2-y1)/(x2-x1)` between two points |
| Unit conversion | Separate columns with the unit in the header. Don't convert inside other formulas |
| Excel Table references | `=SUM(Piezo[Reading])` works in Excel. LibreOffice may not evaluate structured references in xlsx files, so use plain ranges if you need `xlsx_recalc.py` |

Use named inputs for clarity:

```python
from openpyxl.workbook.defined_name import DefinedName
wb.defined_names["LoadFactor"] = DefinedName("LoadFactor", attr_text="Inputs!$B$2")
ws["G4"] = "=C4*LoadFactor"
```

## 5. LibreOffice fidelity notes

A file saved by LibreOffice (`xlsx_recalc.py --write-lo`, `xlsx_convert.py --to xlsx`) can lose or alter:

- VBA macros. Never round-trip an `.xlsm` through LibreOffice.
- Pivot table caches, slicers and timelines.
- Excel Table styles (banding), some chart styling, sparklines, newer conditional-format icon sets, and data-validation input messages.
- Excel 365 dynamic-array and LAMBDA formulas.

Use LibreOffice output to **check** values or to **convert** legacy formats. When the file you hand back must keep the Excel features above, make your edits with openpyxl on the original instead.
