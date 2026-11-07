---
name: xlsx-workbench
description: "Read, build, check and edit Excel workbooks (.xlsx/.xlsm/.xls/.csv) with tested Python scripts — formulas that actually calculate, error and consistency audits, formatted tables, native charts, sheet-to-CSV/JSON, workbook diffs, PDF/PNG renders. Use this whenever a task involves a spreadsheet: analysing data someone sent in Excel, turning CSV/JSON results into a tidy workbook, building a calculation sheet or model, checking a spreadsheet for #REF!/#DIV/0!/overwritten formulas, adding a chart, comparing two versions, or converting .xls/.ods. Trigger even for \"my spreadsheet\", \"the Excel file\", \"lab data in xlsx\", \"make a table I can filter\" or any attached .xlsx/.csv."
license: MIT (see LICENSE)
---

**Single-file build.** This is the `xlsx-workbench` skill packed into one file on 2026-11-05. The instructions below are its SKILL.md, unchanged. Its supporting files (4 reference files, 9 scripts and the licence) are embedded verbatim under "Bundled files" at the end, each with a SHA-256 checksum. You can read a reference there directly. Before you run a script or use an asset, unpack the files once:

```bash
python3 - "${CLAUDE_SKILL_DIR}/SKILL.md" "${TMPDIR:-/tmp}/xlsx-workbench" <<'PY'
import hashlib, os, re, sys
src, out = sys.argv[1], sys.argv[2]
if not os.path.isfile(src):
    src = "/mnt/skills/user/xlsx-workbench/SKILL.md"
text = open(src, encoding="utf-8", newline="").read()
rx = r"^<!-- bundle-file: (\S+) sha256=([0-9a-f]{64}) -->\n(`{3,})[^\n]*\n(.*?)^\3$"
n = 0
for path, sha, _, body in re.findall(rx, text, re.M | re.S):
    if path.startswith("/") or ".." in path.split("/"):
        continue
    data = next((b for b in (body, body[:-1]) if hashlib.sha256(b.encode()).hexdigest() == sha), None)
    if data is None:
        data = body
        print("warning: " + path + " was edited after packing (checksum differs)")
    dest = os.path.join(out, path)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8", newline="") as f:
        f.write(data)
    if data.startswith("#!"):
        os.chmod(dest, 0o755)
    n += 1
print(n, "files unpacked to", os.path.abspath(out))
PY
```

The first argument is the path of this file. Claude Code and Cowork fill it in for you; elsewhere, use the path you read this file from (on claude.ai the command also tries `/mnt/skills/user/xlsx-workbench/SKILL.md`). The command prints the folder it wrote to. From then on, use that folder wherever the instructions mean this skill's folder: paths such as `scripts/...`, `references/...`, `assets/...` and `<this-skill>/...` all point into it.

---


# XLSX Workbench

A toolkit for spreadsheets. The scripts cover the common jobs, and the reference files hold the detailed recipes. Every script is a standalone Python CLI, so run it with `--help` to see the options.

Paths are relative to this skill's folder, the directory that holds this SKILL.md. Call scripts by their full path. Always pass `-o` (or `--write`) with a path in the user's folder. Where `-o` is optional, the output goes next to the input. Never write into the skill folder.

## Setup

```bash
pip install openpyxl lxml pandas pypdfium2   # pandas: analysis only; pypdfium2: PNG renders only
# LibreOffice is needed for: recalculating formulas, .xls/.ods conversion, PDF/PNG renders
```

## Start by inspecting

```bash
python scripts/xlsx_inspect.py book.xlsx            # sheets, header rows, formulas, errors, tables, charts, names, macros
```

Inspecting shows which row holds the headers, whether the values are formulas or typed numbers, and whether there are cached errors, hidden sheets, external links, macros or pivot tables you must not break. "Formulas without cached value" means the file was written by a script. Its numbers don't exist until something calculates them, so run `xlsx_recalc.py`.

## Pick the path

| Goal | Use | Details |
|---|---|---|
| Look at the data, or get it into CSV/JSON/Markdown | `scripts/xlsx_read.py --format md\|csv\|json\|describe` | references/reading-and-analysis.md |
| Add a summary of live statistics (mean, SD …) | openpyxl formulas | references/reading-and-analysis.md |
| Analyse with pandas and write results back | pandas + openpyxl recipes | references/reading-and-analysis.md |
| Turn CSV/JSON into a tidy formatted workbook | `scripts/xlsx_from_data.py` | references/building-workbooks.md |
| Build a calculation sheet or model with live formulas | openpyxl recipes, then `xlsx_recalc.py` | references/building-workbooks.md, references/formulas-and-checking.md |
| See what the formulas actually return | `scripts/xlsx_recalc.py --cells …` | references/formulas-and-checking.md |
| Find errors, overwritten formulas, broken references, suspicious values | `scripts/xlsx_audit.py` | references/formulas-and-checking.md |
| Deliver a file whose formula results show in previews | `scripts/xlsx_recalc.py in.xlsx --write out.xlsx` | references/formulas-and-checking.md |
| Add a native chart (scatter, line, bar, depth profile) | `scripts/xlsx_add_chart.py` | references/charts.md |
| What changed between two versions | `scripts/xlsx_diff.py` | — |
| .xls/.ods to .xlsx, sheets to CSV, PDF or PNG | `scripts/xlsx_convert.py` | — |

## Working principles

**Formulas, not pasted numbers.** If a value depends on other cells (totals, averages, PI = LL − PL, factors of safety), write the formula (`=D4-E4`) rather than a number you computed in Python. The user can then change an input and trust the result. Put inputs and assumptions in clearly labelled cells, and point formulas at them instead of embedding constants (`=B2*$H$1`, not `=B2*1.15`).

**openpyxl writes formulas but never calculates them.** After building or editing formulas, run `xlsx_recalc.py` to get real results and catch `#DIV/0!`, `#REF!` and `#NAME?` before the user does. Then run `xlsx_audit.py` on anything that matters. Report the numbers from the recalculated values, never from your own side calculation.

To deliver the file, run `xlsx_recalc.py work.xlsx --write final.xlsx`. It stores the computed results as cached values inside your file and keeps every Excel feature: table styles, charts and validation. Previews, email attachments and pandas then show numbers instead of blank cells. Excel still recalculates when the file is opened.

**Check the numbers make sense as well as that they calculate.** The audit catches mechanical faults, and it flags zeros among non-zero data and statistical outliers as `suspicious`. Only you and the user can judge physical plausibility, for example a plastic limit of 0, a PI above the A-line limit, or w > LL in a stiff clay. Look at the values, not just the formulas, and raise implausible inputs. Don't silently "fix" them.

**Fix clear slips; list judgement calls.** Restore an overwritten formula or remove a no-op like `+0`, and report both. Leave suspicious inputs and design choices for the user to decide. Never change someone's data values without asking.

**Keep the user's workbook intact.** Edit with openpyxl by loading the file, changing what's needed and saving under a new name. Don't rebuild the workbook from extracted data, because formatting, formulas, validation and charts would be lost. Load `.xlsm` files with `keep_vba=True`. openpyxl drops some features it can't read, such as pivot caches, slicers and some chart formatting. If `xlsx_inspect.py` shows pivot tables or anything unusual, tell the user what might not survive. For a heavily featured file, prefer making a separate output file over editing theirs.

**Choose cached or recalculated values deliberately.** `data_only=True` gives the values Excel last saved. These can be missing (the file was written by a script) or stale (an input was edited without recalculating). When values matter, use `xlsx_read.py --recalc` or `xlsx_recalc.py`.

**Make it readable.** Use one header row, units in the headers ("Depth (m)"), a frozen header row, filters or an Excel Table, and consistent number formats (the same decimals within a column). Keep inputs visually distinct from calculated cells. `xlsx_from_data.py` applies these defaults.

**Check visually when layout matters.** `xlsx_convert.py book.xlsx --to png --fit` renders every sheet, including its charts, one page wide.

## Quick recipes

```bash
# What's in it, in numbers?
python scripts/xlsx_read.py lab.xlsx --sheet Lab --format describe --recalc

# CSV results → formatted workbook with a live totals row
python scripts/xlsx_from_data.py results.csv -o results.xlsx --table --totals sum --total-cols "Volume (m3)" --title "Earthworks — Lot 12"

# Check a model before sending it
python scripts/xlsx_recalc.py model.xlsx --cells "Summary!B2:B10"
python scripts/xlsx_audit.py model.xlsx

# Depth profile chart: two parameters against depth, depth increasing downwards
python scripts/xlsx_add_chart.py lab.xlsx -o lab_chart.xlsx --sheet Lab --type scatter \
    --x "C4:C40,D4:D40" --y "B3:B40,B3:B40" --series-names "w (%),LL (%)" --y-reverse \
    --title "Moisture content and LL" --x-title "w, LL (%)" --y-title "Depth (m)"

# Final copy for sending: results cached so previews show numbers
python scripts/xlsx_recalc.py lab_chart.xlsx --write lab_final.xlsx

# Versions, conversions, visual check
python scripts/xlsx_diff.py v1.xlsx v2.xlsx --values
python scripts/xlsx_convert.py old.xls --to xlsx
python scripts/xlsx_convert.py book.xlsx --to png --fit -o renders
```

## Delivering results

Say what you built or changed, which sheets were affected, and how you checked it: "recalculated, 0 errors; audit flagged F7 as a typed value inside a formula column". Quote key results with their cell reference so the user can find them. When you leave something for the user to decide, such as a suspicious value or an inconsistent formula, list it rather than fixing it silently.

---

## Bundled files

The skill's supporting files, verbatim. Unpack them with the command at the top, or read one here. Line is where each file starts in this document.

| File | Size | Line |
|---|---:|---:|
| `references/building-workbooks.md` | 6.9 KB | 152 |
| `references/charts.md` | 4.3 KB | 298 |
| `references/formulas-and-checking.md` | 7.2 KB | 377 |
| `references/reading-and-analysis.md` | 4.6 KB | 486 |
| `scripts/_xlsx_common.py` | 6.7 KB | 573 |
| `scripts/xlsx_add_chart.py` | 7.7 KB | 730 |
| `scripts/xlsx_audit.py` | 10.9 KB | 896 |
| `scripts/xlsx_convert.py` | 4.4 KB | 1119 |
| `scripts/xlsx_diff.py` | 4.1 KB | 1227 |
| `scripts/xlsx_from_data.py` | 8.7 KB | 1329 |
| `scripts/xlsx_inspect.py` | 7.9 KB | 1539 |
| `scripts/xlsx_read.py` | 6.9 KB | 1722 |
| `scripts/xlsx_recalc.py` | 5.0 KB | 1887 |
| `LICENSE` | 1.1 KB | 2005 |

### `references/building-workbooks.md`

<!-- bundle-file: references/building-workbooks.md sha256=cd1d1097a38b1d0fd070b8dfa0a7d10838881f9d79d8d3054bbb19dde3507c20 -->
````markdown
# Building and formatting workbooks

## Contents
1. Quick route: data → formatted workbook
2. Layout of a calculation sheet
3. Styling and number formats
4. Conditional formatting and data validation
5. Print setup, protection, hyperlinks, notes
6. Editing an existing workbook safely

## 1. Quick route

```bash
python scripts/xlsx_from_data.py results.csv field.json -o lot12.xlsx --sheet-names "Lab,Field" \
    --table --totals sum --total-cols "Volume (m3)" --title "Lot 12 — test results"
```

You get typed values, a shaded and frozen header, an Excel Table (or a filter), number formats with consistent decimals per column, column widths, and a live `SUBTOTAL` totals row. Then add charts with `xlsx_add_chart.py`, or formulas with openpyxl.

## 2. Layout of a calculation sheet

For engineering calculations and models, a reviewer should be able to follow the logic:

```
A: label            B: value     C: unit   D: source / note
Inputs (blue font, light-yellow fill)
  Unit weight γ      18.5         kN/m³     Lab report 12/08
  Cohesion c′        5            kPa       Triaxial BH1
  Friction angle φ′  32           °         Triaxial BH1
Calculations (black font)
  tan φ′             =TAN(RADIANS(B5))
  …
Results (bold, boxed)
  Factor of safety   =…           –         ≥ 1.5 required
```

- Inputs go in one place and are referenced absolutely or by name. There are no constants inside formulas.
- Units go in their own column, and each source is noted.
- A colour convention, explained in a one-line note at the top: blue = input, black = formula, green = link to another sheet.
- Checks are cells that say OK or CHECK, for example `=IF(B20>=1.5,"OK","CHECK")`.

```python
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
INPUT = dict(font=Font(color="1F4E9E"), fill=PatternFill("solid", fgColor="FFF9DB"))
RESULT = dict(font=Font(bold=True), border=Border(*(Side(style="thin"),) * 4))

def style(cell, spec):
    for k, v in spec.items():
        setattr(cell, k, v)

ws["A1"] = "Infinite slope — Lot 12"; ws["A1"].font = Font(bold=True, size=14)
ws["A2"] = "Blue = input, black = calculated."; ws["A2"].font = Font(italic=True, color="808080")
rows = [("Unit weight γ", 18.5, "kN/m³"), ("Cohesion c′", 5, "kPa"), ("Friction angle φ′", 32, "°"),
        ("Slope angle β", 25, "°"), ("Depth z", 2.0, "m")]
for i, (label, val, unit) in enumerate(rows, start=4):
    ws.cell(i, 1, label); style(ws.cell(i, 2, val), INPUT); ws.cell(i, 3, unit)
ws["A10"] = "Factor of safety"
ws["B10"] = "=(B5+B4*B8*COS(RADIANS(B7))^2*TAN(RADIANS(B6)))/(B4*B8*SIN(RADIANS(B7))*COS(RADIANS(B7)))"
style(ws["B10"], RESULT); ws["B10"].number_format = "0.00"
ws["C10"] = '=IF(B10>=1.5,"OK","CHECK")'
ws.column_dimensions["A"].width = 22
```

## 3. Styling and number formats

| Data | `number_format` |
|---|---|
| Fixed decimals | `"0.00"`; thousands separator: `"#,##0.0"` |
| Percent stored as a fraction (0.32) | `"0.0%"`. If it's stored as 32, use `"0.0"` and put "(%)" in the header |
| Scientific (permeability 1.2e-7) | `"0.00E+00"` |
| Dates | `"yyyy-mm-dd"` (unambiguous) or `"d mmm yyyy"` |
| Units shown in the cell | `'0.0" kPa"'`, but keep units in headers where possible |
| Negative numbers in red | `"0.00;[Red]-0.00"` |

```python
from openpyxl.utils import get_column_letter
ws.freeze_panes = "A2"                            # keep the header visible
ws.auto_filter.ref = ws.dimensions                # or add an Excel Table (see xlsx_from_data.py)
for col in ws.iter_cols(min_row=1, max_row=ws.max_row):
    width = max(len(str(c.value)) if c.value is not None else 0 for c in col)
    ws.column_dimensions[get_column_letter(col[0].column)].width = min(max(8, width + 2), 60)
ws["A1"].alignment = Alignment(wrap_text=True, vertical="top")
ws.merge_cells("A1:F1")                           # titles only — merged cells break sorting and filtering
```

## 4. Conditional formatting and data validation

```python
from openpyxl.formatting.rule import CellIsRule, ColorScaleRule, DataBarRule, FormulaRule
from openpyxl.worksheet.datavalidation import DataValidation

red = PatternFill("solid", fgColor="F8CBAD")
ws.conditional_formatting.add("B4:B50", CellIsRule(operator="lessThan", formula=["1.5"], fill=red))   # FoS < 1.5
ws.conditional_formatting.add("C4:C50", ColorScaleRule(start_type="min", start_color="63BE7B",
                                                       mid_type="percentile", mid_value=50, mid_color="FFEB84",
                                                       end_type="max", end_color="F8696B"))
ws.conditional_formatting.add("D4:D50", DataBarRule(start_type="min", end_type="max", color="5B9BD5"))
ws.conditional_formatting.add("A4:F50", FormulaRule(formula=['$F4="CHECK"'], fill=red))  # whole row

dv = DataValidation(type="list", formula1='"Clay,Silt,Sand,Gravel"', allow_blank=True)
dv.error, dv.errorTitle = "Pick a soil type from the list", "Invalid entry"
ws.add_data_validation(dv); dv.add("E4:E200")
num = DataValidation(type="decimal", operator="between", formula1="0", formula2="100")
ws.add_data_validation(num); num.add("C4:C200")
```

## 5. Print setup, protection, hyperlinks, notes

```python
ws.page_setup.orientation = "landscape"
ws.page_setup.paperSize = ws.PAPERSIZE_A4
ws.sheet_properties.pageSetUpPr.fitToPage = True
ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 0   # one page wide, as many tall as needed
ws.print_title_rows = "1:3"                                  # repeat header rows on each page
ws.oddFooter.center.text = "Page &P of &N"

from openpyxl.comments import Comment
ws["B5"].comment = Comment("From triaxial test BH1-S2, 12 Aug 2026", "RK")
ws["D4"].hyperlink = "https://doi.org/10.1680/jgeot.19.P.123"; ws["D4"].style = "Hyperlink"

ws.protection.sheet = True                                   # lock formulas, leave inputs editable:
from openpyxl.styles import Protection
for r in range(4, 9):
    ws.cell(r, 2).protection = Protection(locked=False)
```

Sheet protection without a password stops accidental edits, not determined ones. Tell the user that.

## 6. Editing an existing workbook safely

```python
from openpyxl import load_workbook
wb = load_workbook("their_model.xlsx", keep_vba=False)       # keep_vba=True and save as .xlsm for macro files
ws = wb["Calc"]
ws.insert_rows(10)                                           # ⚠ openpyxl does NOT update formulas that refer below
```

- `insert_rows`, `delete_rows` and `move_range` don't adjust formulas, defined names or chart ranges. Prefer appending at the end. If you must insert, run `xlsx_audit.py` and `xlsx_recalc.py` afterwards and fix the references by hand. Use `ws.move_range("A10:F20", rows=1, translate=True)` to translate formulas inside the moved block.
- Copying a sheet within a workbook: `wb.copy_worksheet(ws)` copies values, styles and formulas, but not charts or images.
- Save under a new name, then run `xlsx_diff.py original.xlsx new.xlsx` to confirm you changed only what you intended.
````

### `references/charts.md`

<!-- bundle-file: references/charts.md sha256=3baa20ec41c86fb971166cce84f0a1faf1f35719f5651250874013ed094a8815 -->
````markdown
# Charts in Excel

Native charts, made with `xlsx_add_chart.py` or openpyxl, stay linked to the cells, so they update when the data changes and the user can restyle them in Excel. Use a matplotlib picture only when Excel can't draw the chart, for example contour plots or complex annotations. Then insert it as an image with `ws.add_image(openpyxl.drawing.image.Image("fig.png"), "H2")`, and say that it's static.

## Choosing the type

| Data | Chart |
|---|---|
| Numeric x: depth, time as numbers, stress, strain | **scatter**. A "line" chart treats x as evenly spaced categories |
| Categories: samples, boreholes, months as labels | **bar** (`bar` = vertical columns, `barh` = horizontal) |
| Trend over evenly spaced periods | line |
| Parts of a whole, ≤ 6 parts | pie (use sparingly) |
| Profiles against depth | scatter with **depth on Y** and `--y-reverse`, so depth increases downward. Give one x range per parameter |

```bash
# Depth profile: w and LL against depth (depth in column B), depth downwards, markers only.
# --x: one range per parameter (no header); --y: the depth range repeated (header row
# included, as for every --y); --series-names: legend names (otherwise every series
# would be called "Depth (m)", the header of the y range). Default size is portrait 12×15 cm.
python scripts/xlsx_add_chart.py lab.xlsx -o lab_chart.xlsx --sheet Lab --type scatter \
  --x "C4:C40,D4:D40" --y "B3:B40,B3:B40" --series-names "w (%),LL (%)" --y-reverse --marker-only \
  --title "Moisture content and liquid limit" --x-title "w, LL (%)" --y-title "Depth (m)"

# Several series against one x (headers in the first row of each y range)
python scripts/xlsx_add_chart.py tests.xlsx -o tests_chart.xlsx --type scatter \
  --x "A2:A50" --y "B1:B50,C1:C50,D1:D50" --title "Stress–strain" --x-title "Axial strain (%)" --y-title "q (kPa)"

# Bar chart on its own sheet; keep any totals row OUT of the ranges; whole-number axis labels
python scripts/xlsx_add_chart.py summary.xlsx -o summary_chart.xlsx --type bar --x A2:A6 --y C1:C6 \
  --target-sheet Charts --y-format "#,##0"
```

## openpyxl details

```python
from openpyxl import load_workbook
from openpyxl.chart import ScatterChart, Reference, Series
from openpyxl.chart.trendline import Trendline

wb = load_workbook("tests.xlsx"); ws = wb.active
ch = ScatterChart(); ch.title = "q vs strain"; ch.style = 10
ch.x_axis.title, ch.y_axis.title = "Axial strain (%)", "q (kPa)"
ch.x_axis.delete = ch.y_axis.delete = False          # openpyxl ≥3.1 hides axes unless told otherwise
x = Reference(ws, min_col=1, min_row=2, max_row=50)
y = Reference(ws, min_col=2, min_row=1, max_row=50)  # includes the header → series name
s = Series(y, x, title_from_data=True)
s.marker.symbol = "circle"; s.marker.size = 5
s.trendline = Trendline(trendlineType="linear", dispEq=True, dispRSqr=True)
ch.series.append(s)
ch.x_axis.scaling.min, ch.x_axis.scaling.max = 0, 15  # fixed axis limits
ch.width, ch.height = 18, 10                          # cm
ws.add_chart(ch, "F2")

# Secondary axis: build a second chart and combine
from openpyxl.chart import LineChart
c2 = LineChart(); c2.add_data(Reference(ws, min_col=3, min_row=1, max_row=50), titles_from_data=True)
c2.y_axis.axId = 200; c2.y_axis.title = "Pore pressure (kPa)"; c2.y_axis.crosses = "max"
bar_or_line = LineChart(); bar_or_line.add_data(Reference(ws, min_col=2, min_row=1, max_row=50), titles_from_data=True)
bar_or_line.x_axis.delete = bar_or_line.y_axis.delete = False
bar_or_line += c2                                     # combined chart with two y axes
ws.add_chart(bar_or_line, "F24")
wb.save("tests_chart.xlsx")
```

## Check the chart

```bash
python scripts/xlsx_convert.py tests_chart.xlsx --to png --fit -o renders
```

Look at the PNG. Check that the axes have titles with units, the series are named, the scale makes sense (start at zero for bars), and depth runs downward on profiles. LibreOffice's rendering is close to Excel's but not identical in fonts and colours, and it doesn't show Excel Table banding.

For depth profiles built directly in openpyxl, set `ch.y_axis.scaling.orientation = "maxMin"` and `ch.x_axis.crosses = "max"`, which keeps the x axis at the bottom. Also give markers an explicit `graphicalProperties.solidFill`, or LibreOffice draws them invisible. Name each series with `s.tx = SeriesLabel(v="w (%)")` (from `openpyxl.chart.series`).
````

### `references/formulas-and-checking.md`

<!-- bundle-file: references/formulas-and-checking.md sha256=82db040a8a39f03e0fa45b9811c933c4e7246da15694194828b37e648b3cfb1f -->
````markdown
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
````

### `references/reading-and-analysis.md`

<!-- bundle-file: references/reading-and-analysis.md sha256=583cb149282bd82f69b3a6d7e66edfb4182923e1343d01ba1202b76282cfda37 -->
````markdown
# Reading data and analysing it

## Quick looks

```bash
python scripts/xlsx_inspect.py data.xlsx                       # where things are
python scripts/xlsx_read.py data.xlsx --sheet Lab --format describe --recalc   # per-column stats
python scripts/xlsx_read.py data.xlsx --sheet Lab --format md | head -40       # eyeball rows
python scripts/xlsx_read.py data.xlsx --sheet Lab --range A3:F200 --header-row 1 --format csv -o lab.csv
```

`xlsx_read.py` finds the header row and skips title rows above it. It fills merged cells down and across, and repeated header names get `_2`, `_3`. It stops at the first blank row and prints a note if non-empty rows follow, which are often a Mean or Total row or a second table. Use `--all-rows` or `--range` to include them. `describe` reports count, missing, min, max, mean, median and sample SD per numeric column.

## pandas

```python
import pandas as pd
df = pd.read_excel("data.xlsx", sheet_name="Lab", header=2)          # header=2 → the 3rd row is the header
df = df.dropna(how="all").dropna(axis=1, how="all")                    # blank rows/cols
df.columns = [str(c).strip() for c in df.columns]
df["w (%)"] = pd.to_numeric(df["w (%)"], errors="coerce")              # text numbers → numbers (bad → NaN)
all_sheets = pd.read_excel("data.xlsx", sheet_name=None)               # dict of DataFrames
```

- `read_excel` reads cached values. For files written by scripts, or with stale results, make a recalculated copy first (`xlsx_recalc.py --write tmp.xlsx`) and read that.
- Dates stored as text stay text. Use `pd.to_datetime(df["Date"], dayfirst=True)` for NZ, UK and AU formats.
- Excel stores numbers as floats, so 0.1 + 0.2 issues show up. Round only for display.
- For very large files, use `openpyxl.load_workbook(path, read_only=True, data_only=True)` and iterate `ws.iter_rows(values_only=True)`.

## Writing analysis results back

Keep the user's sheets untouched and add new sheets:

```python
from openpyxl import load_workbook
from openpyxl.utils.dataframe import dataframe_to_rows
summary = df.groupby(df["Sample"].str[:3]).agg(n=("LL (%)", "size"), LL_mean=("LL (%)", "mean")).reset_index()

wb = load_workbook("data.xlsx")
ws = wb.create_sheet("Summary")
for row in dataframe_to_rows(summary, index=False, header=True):
    ws.append(row)
wb.save("data_with_summary.xlsx")
```

**A live summary-statistics sheet** recalculates when the data changes:

```python
from openpyxl import load_workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter
wb = load_workbook("profile.xlsx"); data = wb["Profile"]; n_last = data.max_row
ss = wb.create_sheet("Summary")
cols = [c for c in range(1, data.max_column + 1)]
ss.append(["Statistic"] + [data.cell(1, c).value for c in cols])
for label, fn in [("n", "COUNT"), ("Min", "MIN"), ("Max", "MAX"), ("Mean", "AVERAGE"),
                  ("Median", "MEDIAN"), ("Std dev (sample)", "STDEV")]:
    ss.append([label] + [f"=ROUND({fn}(Profile!{get_column_letter(c)}2:{get_column_letter(c)}{n_last}),3)" if fn != "COUNT"
                         else f"=COUNT(Profile!{get_column_letter(c)}2:{get_column_letter(c)}{n_last})" for c in cols])
for cell in ss[1]:
    cell.font = Font(bold=True)
wb.save("profile_summary.xlsx")     # then: xlsx_recalc.py profile_summary.xlsx --write profile_final.xlsx
```

Use `STDEV`, `VAR` and `PERCENTILE`, which work everywhere. The newer `STDEV.S` and `PERCENTILE.INC` must be written by openpyxl as `_xlfn.STDEV.S(...)`, or Excel shows `#NAME?`.

When the result should stay live, write formulas (`=AVERAGEIFS(Lab!D:D,Lab!A:A,"BH1*")`) instead of pandas numbers. Pasted numbers become stale as soon as the data changes. Use pasted values for one-off statistics, and say they're static.

To write several DataFrames to a new workbook in one go, use `with pd.ExcelWriter("out.xlsx", engine="openpyxl") as xw: df.to_excel(xw, "Data", index=False)`. Then apply the formatting from building-workbooks.md, or simply use `xlsx_from_data.py` on CSV exports.

## Cleaning checklist

Before analysing, check for:

- Header rows repeated mid-sheet (pasted blocks) and total rows mixed in with the data. Drop them.
- Numbers stored as text, which `xlsx_audit.py` flags as `text-number`. Also look for units typed into cells ("12 kPa"), which need splitting into value and unit.
- Merged cells used for grouping, such as a borehole ID merged down several rows. `xlsx_read.py` fills them down.
- Hidden rows, columns and sheets (inspect shows the sheet state). Ask whether hidden data should count.
- Mixed units in one column, and inconsistent sample IDs ("BH1-S1" vs "BH1 S1").

Report what you cleaned and how many rows each step affected.
````

### `scripts/_xlsx_common.py`

<!-- bundle-file: scripts/_xlsx_common.py sha256=c37b6ded11155253c131e254eed46eeb8b42c817dbb512f4f40a54670ad5965f -->
````python
"""Shared helpers for xlsx-workbench scripts (imported from the same folder)."""
import os
import shutil
import subprocess
import sys
import tempfile
import warnings

sys.dont_write_bytecode = True
# openpyxl warns about extensions it drops on read (e.g. in LibreOffice-written copies); not useful here
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

try:
    import openpyxl  # noqa: F401
except ImportError:
    sys.exit("openpyxl is required: pip install openpyxl")

ERROR_VALUES = ("#DIV/0!", "#N/A", "#NAME?", "#NULL!", "#NUM!", "#REF!", "#VALUE!", "#SPILL!", "#CALC!", "#GETTING_DATA")

# A LibreOffice profile setting that forces formulas to be recalculated when a file is
# opened. Without it LibreOffice keeps whatever values Excel cached — possibly stale.
_RECALC_XCU = """<?xml version="1.0" encoding="UTF-8"?>
<oor:items xmlns:oor="http://openoffice.org/2001/registry" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<item oor:path="/org.openoffice.Office.Calc/Formula/Load"><prop oor:name="OOXMLRecalcMode" oor:op="fuse"><value>0</value></prop></item>
<item oor:path="/org.openoffice.Office.Calc/Formula/Load"><prop oor:name="ODFRecalcMode" oor:op="fuse"><value>0</value></prop></item>
</oor:items>
"""


def soffice():
    for name in ("soffice", "libreoffice", "/Applications/LibreOffice.app/Contents/MacOS/soffice"):
        found = shutil.which(name) or (name if os.path.exists(name) else None)
        if found:
            return found
    return None


def lo_convert(src, fmt, outdir, recalc=True, timeout=300):
    """Convert with LibreOffice (headless, private profile). Returns the output path."""
    exe = soffice()
    if not exe:
        sys.exit("LibreOffice not found (apt install libreoffice-calc / brew install --cask libreoffice)")
    os.makedirs(outdir, exist_ok=True)
    with tempfile.TemporaryDirectory() as profile:
        if recalc:
            os.makedirs(os.path.join(profile, "user"), exist_ok=True)
            with open(os.path.join(profile, "user", "registrymodifications.xcu"), "w") as fh:
                fh.write(_RECALC_XCU)
        cmd = [exe, f"-env:UserInstallation=file://{profile}", "--headless", "--convert-to", fmt, "--outdir", outdir, src]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    out = os.path.join(outdir, os.path.splitext(os.path.basename(src))[0] + "." + fmt.split(":")[0])
    if not os.path.exists(out):
        sys.exit(f"LibreOffice conversion failed: {res.stderr.strip() or res.stdout.strip()}")
    return out


def recalculated_copy(path, tmpdir):
    """Path to a copy of the workbook with every formula recalculated by LibreOffice."""
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    fmt = "xlsx" if ext in ("xlsx", "xlsm", "xls", "ods", "csv") else ext
    return lo_convert(os.path.abspath(path), fmt, tmpdir, recalc=True)


def pick_sheets(wb, spec):
    """spec: None (all), 'Name', '2' (1-based index), or comma list."""
    if not spec:
        return list(wb.worksheets)
    out = []
    for part in str(spec).split(","):
        part = part.strip()
        if part.isdigit() and part not in wb.sheetnames:
            out.append(wb.worksheets[int(part) - 1])
        elif part in wb.sheetnames:
            out.append(wb[part])
        else:
            sys.exit(f"No sheet '{part}'. Sheets: {wb.sheetnames}")
    return out


def default_out(src, suffix, ext=None):
    """Output path next to the input: report.xlsx -> report_<suffix>.<ext>."""
    base, e = os.path.splitext(os.path.abspath(src))
    return f"{base}_{suffix}{'.' + ext if ext else e}"


def inject_cached_values(original, recalculated, out):
    """Write `out` = `original` byte-for-byte, except that every formula cell gets the
    value LibreOffice computed (from `recalculated`) as its cached <v>. All Excel
    features of the original (table styles, charts, validation, VBA parts) are kept,
    and viewers that don't calculate (previews, pandas, data_only=True) see numbers.
    Returns the number of cells updated."""
    import datetime as dt
    import posixpath
    import zipfile
    from lxml import etree
    from openpyxl import load_workbook
    from openpyxl.utils.datetime import to_excel

    NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
          "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
          "pr": "http://schemas.openxmlformats.org/package/2006/relationships"}
    M = "{%s}" % NS["m"]
    vals = load_workbook(recalculated, data_only=True)
    zin = zipfile.ZipFile(original)
    wbx = etree.fromstring(zin.read("xl/workbook.xml"))
    rels = etree.fromstring(zin.read("xl/_rels/workbook.xml.rels"))
    target = {r.get("Id"): r.get("Target") for r in rels.findall("pr:Relationship", NS)}
    sheet_xml = {}
    for sh in wbx.findall("m:sheets/m:sheet", NS):
        t = target.get(sh.get("{%s}id" % NS["r"]))
        if t:
            path = t.lstrip("/") if t.startswith("/") else posixpath.normpath(posixpath.join("xl", t))
            sheet_xml[path] = sh.get("name")
    changed = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            name = sheet_xml.get(item.filename)
            if name and name in vals.sheetnames:
                ws = vals[name]
                root = etree.fromstring(data)
                for c in root.iter(M + "c"):
                    if c.find(M + "f") is None:
                        continue
                    v = ws[c.get("r")].value
                    old = c.find(M + "v")
                    if old is not None:
                        c.remove(old)
                    for attr in ("t",):
                        if attr in c.attrib:
                            del c.attrib[attr]
                    if v is None:
                        continue
                    ve = etree.SubElement(c, M + "v")
                    if isinstance(v, bool):
                        c.set("t", "b")
                        ve.text = "1" if v else "0"
                    elif isinstance(v, (int, float)):
                        ve.text = repr(float(v)) if isinstance(v, float) else str(v)
                    elif isinstance(v, (dt.datetime, dt.date)):
                        ve.text = repr(float(to_excel(v)))
                    elif isinstance(v, str) and v in ERROR_VALUES:
                        c.set("t", "e")
                        ve.text = v
                    else:
                        c.set("t", "str")
                        ve.text = str(v)
                    changed += 1
                data = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
            zout.writestr(item, data)
    return changed
````

### `scripts/xlsx_add_chart.py`

<!-- bundle-file: scripts/xlsx_add_chart.py sha256=092d7e3501fe53dc7433937d478bd79294051e10d59b4e188215e8b0fc1d5d6e -->
````python
#!/usr/bin/env python3
"""Add a native Excel chart (editable in Excel, updates when data changes).

    python xlsx_add_chart.py book.xlsx -o book_chart.xlsx --sheet Lab --type scatter \
        --x "B4:B20" --y "C3:C20,D3:D20" --title "Moisture vs depth" \
        --x-title "Depth (m)" --y-title "Moisture (%)" [--anchor H3] [--target-sheet Charts]
        [--y-reverse] [--size 18x10] [--style 10] [--no-legend] [--marker-only]

--y ranges INCLUDE the header cell (first row = series name); --x excludes it.
--x may be a comma list paired one-to-one with --y (scatter): each series gets its own x.
--series-names "w (%),LL (%)" overrides the names taken from the --y headers.

Depth profile with two parameters (depth down the page, one series per parameter):
    --type scatter --x "B2:B13,C2:C13" --y "A1:A13,A1:A13" --series-names "w (%),LL (%)" \
    --y-reverse --x-title "Water content / LL (%)" --y-title "Depth (m)"
Types: line, scatter (numeric x — use for depth/time/measurements), bar (vertical
columns), barh (horizontal bars), area, pie.
--y-reverse flips the y axis (depth increasing downward, as on borehole logs).
For profiles with depth on the vertical axis, plot depth as Y with --y-reverse.
"""
import argparse
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _xlsx_common  # noqa: E402,F401

from openpyxl import load_workbook  # noqa: E402
from openpyxl.chart import AreaChart, BarChart, LineChart, PieChart, Reference, ScatterChart, Series  # noqa: E402
from openpyxl.chart.series import SeriesLabel  # noqa: E402
from openpyxl.chart.shapes import GraphicalProperties  # noqa: E402
from openpyxl.utils.cell import range_boundaries  # noqa: E402


def ref(ws, rng):
    c1, r1, c2, r2 = range_boundaries(rng)
    return Reference(ws, min_col=c1, min_row=r1, max_col=c2, max_row=r2)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("xlsx")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--sheet", help="sheet holding the data (default: first)")
    ap.add_argument("--type", choices=["line", "scatter", "bar", "barh", "area", "pie"], default="line")
    ap.add_argument("--x", required=True, help="category / x values, without header, e.g. A4:A20")
    ap.add_argument("--y", required=True, help="comma list of series ranges WITH header, e.g. C3:C20,D3:D20")
    ap.add_argument("--title")
    ap.add_argument("--x-title")
    ap.add_argument("--y-title")
    ap.add_argument("--anchor", help="top-left cell for the chart (default: two columns right of the data)")
    ap.add_argument("--target-sheet", help="put the chart on this sheet (created if missing)")
    ap.add_argument("--size", help="width x height in cm (default 16x9; 12x15 with --y-reverse)")
    ap.add_argument("--style", type=int, default=10)
    ap.add_argument("--y-reverse", action="store_true")
    ap.add_argument("--no-legend", action="store_true")
    ap.add_argument("--marker-only", action="store_true", help="scatter/line: markers without lines")
    ap.add_argument("--series-names", help="comma list of series names (default: header cell of each --y range)")
    ap.add_argument("--x-format", help="number format for the x axis, e.g. 0.0")
    ap.add_argument("--y-format", help="number format for the y axis, e.g. #,##0")
    a = ap.parse_args()
    if os.path.abspath(a.output) == os.path.abspath(a.xlsx):
        sys.exit("Refusing to overwrite the input; choose a different -o")

    keep_vba = a.xlsx.lower().endswith(".xlsm")
    wb = load_workbook(a.xlsx, keep_vba=keep_vba)
    ws = wb[a.sheet] if a.sheet else wb.worksheets[0]
    xranges = [r.strip() for r in a.x.split(",") if r.strip()]
    yranges = [r.strip() for r in a.y.split(",") if r.strip()]
    for xr in xranges:
        c1, r1, c2, r2 = range_boundaries(xr)
        if c1 != c2 and r1 != r2:
            sys.exit(f"--x range {xr} spans several columns and rows; give one column (or a comma list)")
    if len(xranges) not in (1, len(yranges)):
        sys.exit("--x must be one range, or one range per --y range")
    if len(xranges) > 1 and a.type != "scatter":
        sys.exit("Per-series x ranges only work with --type scatter")
    names = [n.strip() for n in a.series_names.split(",")] if a.series_names else []
    palette = ["4472C4", "C0504D", "9BBB59", "8064A2", "F79646", "4BACC6", "7F7F7F", "1F3864"]

    def style_series(s, k):
        color = palette[k % len(palette)]
        s.marker.symbol = ["circle", "square", "triangle", "diamond", "x", "star"][k % 6]
        s.marker.size = 6
        # explicit marker colours: without them LibreOffice draws invisible markers
        s.marker.graphicalProperties = GraphicalProperties(solidFill=color)
        s.marker.graphicalProperties.line.solidFill = color
        if a.marker_only:
            s.graphicalProperties.line.noFill = True
        else:
            s.graphicalProperties.line.solidFill = color
            s.graphicalProperties.line.width = 19050  # 1.5 pt

    if a.type == "scatter":
        ch = ScatterChart()
        ch.scatterStyle = "lineMarker"
        for k, yr in enumerate(yranges):
            xref = ref(ws, xranges[k] if len(xranges) > 1 else xranges[0])
            s = Series(ref(ws, yr), xref, title_from_data=True)
            s.smooth = False
            style_series(s, k)
            ch.series.append(s)
    else:
        xref = ref(ws, xranges[0])
        ch = {"line": LineChart, "bar": BarChart, "barh": BarChart, "area": AreaChart, "pie": PieChart}[a.type]()
        if a.type == "barh":
            ch.type = "bar"
        elif a.type == "bar":
            ch.type = "col"
        for yr in yranges:
            ch.add_data(ref(ws, yr), titles_from_data=True)
        ch.set_categories(xref)
        if a.type == "line":
            for k, s in enumerate(ch.series):
                style_series(s, k)
    for k, s in enumerate(ch.series):
        if k < len(names) and names[k]:
            s.tx = SeriesLabel(v=names[k])
    if a.title:
        ch.title = a.title
    if a.type != "pie":
        if a.x_title:
            ch.x_axis.title = a.x_title
        if a.y_title:
            ch.y_axis.title = a.y_title
        # openpyxl ≥3.1 hides axes unless told otherwise
        ch.x_axis.delete = False
        ch.y_axis.delete = False
        if a.y_reverse:
            ch.y_axis.scaling.orientation = "maxMin"
            if a.type == "scatter":
                ch.x_axis.crosses = "max"  # keep the x axis at the bottom; on a reversed y it would jump to the top
        if a.x_format:
            ch.x_axis.number_format = a.x_format
            ch.x_axis.numFmt.sourceLinked = False if ch.x_axis.numFmt is not None else None
        if a.y_format:
            ch.y_axis.number_format = a.y_format
            ch.y_axis.numFmt.sourceLinked = False if ch.y_axis.numFmt is not None else None
    ch.style = a.style
    size = a.size or ("12x15" if a.y_reverse else "16x9")
    w, h = (float(v) for v in size.lower().split("x"))
    ch.width, ch.height = w, h
    if a.no_legend:
        ch.legend = None

    target = ws
    if a.target_sheet:
        target = wb[a.target_sheet] if a.target_sheet in wb.sheetnames else wb.create_sheet(a.target_sheet)
    anchor = a.anchor or (f"{chr(ord('A') + min(ws.max_column + 1, 24))}2" if target is ws else "A1")
    target.add_chart(ch, anchor)
    wb.save(a.output)
    print(f"Wrote {a.output}: {a.type} chart with {len(yranges)} series "
          f"({', '.join(str(s.tx.v) if s.tx is not None and s.tx.v else (s.tx.strRef.f if s.tx is not None and s.tx.strRef is not None else '?') for s in ch.series)}) "
          f"at {target.title}!{anchor}", file=sys.stderr)
    print("Check it renders: python xlsx_convert.py " + a.output + " --to png", file=sys.stderr)


if __name__ == "__main__":
    main()
````

### `scripts/xlsx_audit.py`

<!-- bundle-file: scripts/xlsx_audit.py sha256=fe6d2f106a88c2b45d5278cd9d5dacd691e584cf2d50a795d963cd3ccb4233c4 -->
````python
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
````

### `scripts/xlsx_convert.py`

<!-- bundle-file: scripts/xlsx_convert.py sha256=1bc6208d4a21c47637b2ed9348142ad2ac286df98f8447c935b8ad3edcaf08de -->
````python
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
````

### `scripts/xlsx_diff.py`

<!-- bundle-file: scripts/xlsx_diff.py sha256=760638eba949d4244c1e4009bdf7c4de88e46579209863e4c4cb6bd2a4c1e6af -->
````python
#!/usr/bin/env python3
"""Cell-by-cell comparison of two workbooks (or two sheets).

Reports, per sheet: added/removed sheets, changed formulas, changed values
(constants, and formula results if --values), and rows/columns added at the end.

Usage:
    python xlsx_diff.py old.xlsx new.xlsx [--sheet NAME] [--values] [--tolerance 1e-9] [--json] [-o diff.md]
--values also compares cached formula results (run both through xlsx_recalc.py --write first
if they were saved by scripts).
"""
import argparse
import json
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _xlsx_common  # noqa: E402,F401

from openpyxl import load_workbook  # noqa: E402
from openpyxl.utils import get_column_letter  # noqa: E402


def same(a, b, tol):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return math.isclose(a, b, rel_tol=tol, abs_tol=tol)
    return a == b


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("old")
    ap.add_argument("new")
    ap.add_argument("--sheet")
    ap.add_argument("--values", action="store_true")
    ap.add_argument("--tolerance", type=float, default=1e-9)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("-o", "--output")
    a = ap.parse_args()

    fo, fn = load_workbook(a.old), load_workbook(a.new)
    vo = load_workbook(a.old, data_only=True) if a.values else None
    vn = load_workbook(a.new, data_only=True) if a.values else None
    sheets_o, sheets_n = fo.sheetnames, fn.sheetnames
    result = {"added_sheets": [s for s in sheets_n if s not in sheets_o],
              "removed_sheets": [s for s in sheets_o if s not in sheets_n], "sheets": {}}
    common = [s for s in sheets_o if s in sheets_n and (not a.sheet or s == a.sheet)]
    for s in common:
        wo, wn = fo[s], fn[s]
        changes = []
        rows = max(wo.max_row, wn.max_row)
        cols = max(wo.max_column, wn.max_column)
        for r in range(1, rows + 1):
            for c in range(1, cols + 1):
                x, y = wo.cell(r, c).value, wn.cell(r, c).value
                coord = f"{get_column_letter(c)}{r}"
                if not same(x, y, a.tolerance):
                    kind = "formula" if any(isinstance(v, str) and v.startswith("=") for v in (x, y)) else "value"
                    changes.append({"cell": coord, "kind": kind, "old": x, "new": y})
                elif a.values and isinstance(x, str) and x.startswith("="):
                    rx, ry = vo[s].cell(r, c).value, vn[s].cell(r, c).value
                    if not same(rx, ry, a.tolerance):
                        changes.append({"cell": coord, "kind": "result", "old": rx, "new": ry, "formula": x})
        result["sheets"][s] = {"size_old": f"{wo.max_row}×{wo.max_column}", "size_new": f"{wn.max_row}×{wn.max_column}",
                               "changes": changes}

    if a.json:
        text = json.dumps(result, indent=2, default=str, ensure_ascii=False)
    else:
        lines = [f"# {os.path.basename(a.old)} → {os.path.basename(a.new)}", ""]
        if result["added_sheets"]:
            lines.append(f"Added sheets: {result['added_sheets']}")
        if result["removed_sheets"]:
            lines.append(f"Removed sheets: {result['removed_sheets']}")
        for s, d in result["sheets"].items():
            ch = d["changes"]
            size = "" if d["size_old"] == d["size_new"] else f" (size {d['size_old']} → {d['size_new']})"
            lines.append(f"\n## {s}: {len(ch)} change(s){size}")
            for c in ch[:500]:
                extra = f"   [{c['formula']}]" if c.get("formula") else ""
                lines.append(f"- {c['cell']} ({c['kind']}): {c['old']!r} → {c['new']!r}{extra}")
            if len(ch) > 500:
                lines.append(f"- … {len(ch) - 500} more")
        text = "\n".join(lines)
    if a.output:
        with open(a.output, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
        print(f"Wrote {a.output}", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
````

### `scripts/xlsx_from_data.py`

<!-- bundle-file: scripts/xlsx_from_data.py sha256=d26857d2494f14fff0ef9a029f030af45c03b987e3e212e4107f985256d301d9 -->
````python
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
````

### `scripts/xlsx_inspect.py`

<!-- bundle-file: scripts/xlsx_inspect.py sha256=ce8eb2bb67fbab42fb82444b1f9a75d24b20d7e871a6be5fc5f6b532c82b366d -->
````python
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
````

### `scripts/xlsx_read.py`

<!-- bundle-file: scripts/xlsx_read.py sha256=88224100c998285075cfb92c96babfb0168a647781f292085fcb6503e78ed0a0 -->
````python
#!/usr/bin/env python3
"""Read a sheet (or range) into CSV, JSON, Markdown or a quick summary.

Detects the header row (or use --header-row N; 0 = no header), skips title rows
above it, stops at the first fully blank row unless --all-rows, and fills merged
header cells. Values are the cached results of formulas (what Excel last showed);
add --recalc to compute fresh values with LibreOffice first, or --formulas to get
the formulas themselves.

Usage:
    python xlsx_read.py book.xlsx [--sheet NAME|N] [--range A3:F20] [--header-row 3]
                        [--format csv|json|md|describe] [-o out] [--recalc] [--formulas] [--all-rows]
"describe" prints per-column type, count, min/max/mean/median/sample stdev for
numbers — a fast way to understand a dataset before analysing it.
Formats: csv, json, md (Markdown table, the default), describe.
"""
import argparse
import csv
import datetime as dt
import io
import json
import os
import statistics
import sys
import tempfile

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _xlsx_common import pick_sheets, recalculated_copy  # noqa: E402

from openpyxl import load_workbook  # noqa: E402


def guess_header(rows):
    for i, r in enumerate(rows[:10]):
        vals = [v for v in r if v not in (None, "")]
        if len({str(v) for v in vals}) >= 2 and sum(isinstance(v, str) for v in vals) / len(vals) >= 0.8:
            return i
    return 0


def fmt(v):
    if isinstance(v, dt.datetime):
        return v.date().isoformat() if (v.hour, v.minute, v.second) == (0, 0, 0) else v.isoformat(sep=" ")
    if isinstance(v, (dt.date, dt.time)):
        return v.isoformat()
    return v


def describe(header, data):
    out = []
    for j, name in enumerate(header):
        col = [r[j] for r in data if j < len(r) and r[j] not in (None, "")]
        nums = [v for v in col if isinstance(v, (int, float)) and not isinstance(v, bool)]
        line = {"column": name, "non_empty": len(col), "missing": len(data) - len(col)}
        if nums and len(nums) >= 0.8 * len(col):
            r = lambda x: round(x, 4)  # noqa: E731
            line.update(type="number", min=r(min(nums)), max=r(max(nums)), mean=r(statistics.fmean(nums)),
                        median=r(statistics.median(nums)))
            if len(nums) > 1:
                line["stdev_sample"] = r(statistics.stdev(nums))
        elif col and all(isinstance(v, (dt.date, dt.datetime)) for v in col):
            line.update(type="date", min=fmt(min(col)), max=fmt(max(col)))
        else:
            distinct = sorted({str(v) for v in col})
            line.update(type="text", distinct=len(distinct), examples=distinct[:5])
        out.append(line)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("xlsx")
    ap.add_argument("--sheet")
    ap.add_argument("--range")
    ap.add_argument("--header-row", type=int, help="1-based row number of the header within the sheet/range; 0 = none")
    ap.add_argument("--format", choices=["csv", "json", "md", "describe"], default="md")
    ap.add_argument("-o", "--output")
    ap.add_argument("--recalc", action="store_true")
    ap.add_argument("--formulas", action="store_true")
    ap.add_argument("--all-rows", action="store_true", help="don't stop at the first blank row")
    a = ap.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        path = recalculated_copy(a.xlsx, tmp) if a.recalc else a.xlsx
        wb = load_workbook(path, data_only=not a.formulas)
        ws = pick_sheets(wb, a.sheet)[0]
        merged = {}
        for mr in ws.merged_cells.ranges:  # fill merged blocks with their top-left value
            v = ws.cell(mr.min_row, mr.min_col).value
            for r in range(mr.min_row, mr.max_row + 1):
                for c in range(mr.min_col, mr.max_col + 1):
                    merged[(r, c)] = v
        grid = ws[a.range] if a.range else list(ws.iter_rows())
        raw = [[c.value for c in r] for r in grid]
        rows = [[merged.get((c.row, c.column), c.value) for c in r] for r in grid]

    if a.header_row is None:
        h = guess_header(raw)  # on raw cells, so a merged title row isn't mistaken for a header
    else:
        h = a.header_row - 1 if a.header_row > 0 else None
    if h is not None:
        header, seen = [], {}
        for j, v in enumerate(rows[h]):
            name = str(v).strip() if v is not None else f"col{j + 1}"
            seen[name] = seen.get(name, 0) + 1
            header.append(name if seen[name] == 1 else f"{name}_{seen[name]}")  # merged group headers repeat
        body = rows[h + 1:]
    else:
        header = [f"col{j + 1}" for j in range(max(len(r) for r in rows))]
        body = rows
    data, cut_at = [], None
    for k, r in enumerate(body):
        if all(v in (None, "") for v in r):
            if a.all_rows:
                continue
            if data:
                cut_at = k
                break
            continue
        data.append(r)
    if cut_at is not None:
        rest = [r for r in body[cut_at:] if any(v not in (None, "") for v in r)]
        if rest:
            first_row = (h + 2 if h is not None else 1) + cut_at
            print(f"Note: stopped at the blank row {first_row}; {len(rest)} non-empty row(s) below it were not read "
                  f"(often totals/means or a second table). Use --all-rows or --range to include them.", file=sys.stderr)
    # drop trailing columns that are empty everywhere
    width = max([j + 1 for j, n in enumerate(header) if not n.startswith("col")] +
                [max((j + 1 for j, v in enumerate(r) if v not in (None, "")), default=0) for r in data] + [1])
    header = header[:width]
    data = [[fmt(v) for v in r[:width]] for r in data]

    if a.format == "describe":
        text = json.dumps(describe(header, data), indent=2, default=str, ensure_ascii=False) + "\n"
        text = f"Sheet '{ws.title}': {len(data)} data rows, header row {h + 1 if h is not None else '-'}\n" + text
    elif a.format == "json":
        text = json.dumps([dict(zip(header, r)) for r in data], indent=2, default=str, ensure_ascii=False) + "\n"
    elif a.format == "csv":
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(header)
        w.writerows(data)
        text = buf.getvalue()
    else:
        esc = lambda v: "" if v is None else str(v).replace("|", "\\|").replace("\n", " ")  # noqa: E731
        lines = ["| " + " | ".join(esc(x) for x in header) + " |", "|" + "---|" * len(header)]
        lines += ["| " + " | ".join(esc(x) for x in r) + " |" for r in data]
        text = "\n".join(lines) + "\n"
    if a.output:
        with open(a.output, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        print(f"Wrote {a.output}: {len(data)} rows × {len(header)} columns from '{ws.title}'", file=sys.stderr)
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
````

### `scripts/xlsx_recalc.py`

<!-- bundle-file: scripts/xlsx_recalc.py sha256=8b5945a106ae96f747170eeb77e122a9f9edadd5581b625831230bd5c578bc1b -->
````python
#!/usr/bin/env python3
"""Recalculate every formula with LibreOffice and report the results.

openpyxl writes formulas but cannot calculate them, and files saved by scripts
have no cached values; files from Excel may have stale ones. This script makes
a recalculated copy (LibreOffice, forced recalc-on-load), then reports:
  - formula errors (#DIV/0!, #REF!, #NAME?, #N/A, #VALUE! ...) with cell and formula
  - optionally the values of chosen cells (--cells "Summary!B5,Lab!F10")
The input file is not modified.
--write OUT   saves a copy of the ORIGINAL file with the computed results stored as
              cached values: every Excel feature is kept (table styles, charts,
              validation), and previews / pandas / data_only readers see numbers.
              This is the copy to hand to people.
--write-lo OUT saves LibreOffice's own re-saved workbook instead (may lose Excel-only
              features — see references/formulas-and-checking.md).

Usage:
    python xlsx_recalc.py model.xlsx [--cells "Sheet!A1,Sheet!B2:B5"] [--json]
                          [--write model_recalc.xlsx] [--fail-on-error]
"""
import argparse
import json
import os
import shutil
import sys
import tempfile

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _xlsx_common import ERROR_VALUES, inject_cached_values, recalculated_copy  # noqa: E402

from openpyxl import load_workbook  # noqa: E402


def cell_refs(spec, wb):
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        sheet, _, rng = part.rpartition("!")
        sheet = sheet.strip("'") or wb.sheetnames[0]
        ws = wb[sheet]
        cells = ws[rng]
        if not isinstance(cells, tuple):
            yield sheet, cells
        else:
            for row in cells if isinstance(cells[0], tuple) else (cells,):
                for c in row:
                    yield sheet, c


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("xlsx")
    ap.add_argument("--cells", action="append", help="cells/ranges to print, e.g. 'Summary!B2:C5,Lab!F10' (repeatable)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--write", help="save the original with computed values cached (keeps all features)")
    ap.add_argument("--write-lo", help="save LibreOffice's re-saved workbook")
    ap.add_argument("--fail-on-error", action="store_true", help="exit 1 if any formula errors")
    a = ap.parse_args()
    for w in (a.write, a.write_lo):
        if w and os.path.abspath(w) == os.path.abspath(a.xlsx):
            sys.exit("Refusing to overwrite the input; choose a different output path")
    if a.write and os.path.splitext(a.xlsx)[1].lower() not in (".xlsx", ".xlsm"):
        sys.exit("--write needs an .xlsx/.xlsm input; use --write-lo for other formats")

    with tempfile.TemporaryDirectory() as tmp:
        rc = recalculated_copy(a.xlsx, tmp)
        wf = load_workbook(a.xlsx, data_only=False)
        wv = load_workbook(rc, data_only=True)
        errors, n_formulas = [], 0
        for ws in wf.worksheets:
            if ws.title not in wv.sheetnames:
                continue
            vs = wv[ws.title]
            for row in ws.iter_rows():
                for c in row:
                    if c.data_type == "f" or (isinstance(c.value, str) and str(c.value).startswith("=")):
                        n_formulas += 1
                        v = vs[c.coordinate].value
                        if isinstance(v, str) and v in ERROR_VALUES:
                            errors.append({"cell": f"{ws.title}!{c.coordinate}", "error": v, "formula": str(c.value)})
        values = []
        if a.cells:
            for sheet, c in cell_refs(",".join(a.cells), wv):
                f = wf[sheet][c.coordinate].value
                values.append({"cell": f"{sheet}!{c.coordinate}", "value": c.value,
                               "formula": str(f) if isinstance(f, str) and f.startswith("=") else None})
        if a.write:
            n_cached = inject_cached_values(a.xlsx, rc, a.write)
        if a.write_lo:
            shutil.copy(rc, a.write_lo)

    if a.json:
        print(json.dumps({"formulas": n_formulas, "errors": errors, "values": values}, indent=2, default=str, ensure_ascii=False))
    else:
        print(f"{n_formulas} formula(s) recalculated; {len(errors)} error(s)")
        for e in errors:
            print(f"  {e['cell']}: {e['error']}   {e['formula']}")
        for v in values:
            val = round(v["value"], 6) if isinstance(v["value"], float) else v["value"]
            print(f"  {v['cell']} = {val!r}" + (f"   ({v['formula']})" if v["formula"] else ""))
        if a.write:
            print(f"Wrote {a.write} ({n_cached} cached value(s) stored; original formatting and features kept)")
        if a.write_lo:
            print(f"Wrote {a.write_lo} (LibreOffice re-save)")
    if errors and a.fail_on_error:
        sys.exit(1)


if __name__ == "__main__":
    main()
````

### `LICENSE`

<!-- bundle-file: LICENSE sha256=af7f621414b904053616a4ae3e0dacd5a1a9be9d2d90f558266627c2e8680859 -->
````text
MIT License

Copyright (c) 2026 Roohollah Kalatehjari

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
````
