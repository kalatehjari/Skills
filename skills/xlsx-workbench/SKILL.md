---
name: xlsx-workbench
description: Read, build, check and edit Excel workbooks (.xlsx/.xlsm/.xls/.csv) with tested Python scripts — formulas that actually calculate, error and consistency audits, formatted tables, native charts, sheet-to-CSV/JSON, workbook diffs, PDF/PNG renders. Use this whenever a task involves a spreadsheet: analysing data someone sent in Excel, turning CSV/JSON results into a tidy workbook, building a calculation sheet or model, checking a spreadsheet for #REF!/#DIV/0!/overwritten formulas, adding a chart, comparing two versions, or converting .xls/.ods. Trigger even for "my spreadsheet", "the Excel file", "lab data in xlsx", "make a table I can filter" or any attached .xlsx/.csv.
license: MIT (see LICENSE)
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
