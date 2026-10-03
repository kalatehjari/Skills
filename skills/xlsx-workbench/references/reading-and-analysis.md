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
