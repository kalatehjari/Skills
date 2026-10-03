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
