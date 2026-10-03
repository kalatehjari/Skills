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
