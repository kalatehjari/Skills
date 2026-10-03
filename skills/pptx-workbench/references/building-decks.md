# Building decks with pptx_build.py

## Contents
1. Outline syntax (full reference)
2. Charts
3. Templates
4. JSON input
5. When to go beyond the builder (python-pptx recipes)

## 1. Outline syntax

```markdown
---
title: Slope stability at Lot 12          # → title slide (omit the front matter for no title slide)
subtitle: Site investigation findings
author: R. Kalatehjari, GEOTECH-LAB
date: 3 October 2026
footer: Lot 12 retaining wall — client briefing   # bottom-left of every content slide
---

# Background                               ← section divider (a following plain line becomes its subtitle)

## Site and geology                        ← content slide; the title should state the message
- Residual soils over weathered greywacke  ← bullet
  - Silty clay to 3 m                      ← sub-bullet (indent 2 spaces per level)
- Groundwater at **2.5 m** bgl             ← **bold**, *italic*, `code`
1. Numbered item                           ← numbered list
A plain line is an unbulleted paragraph.
Notes: Speaker notes — everything from here to the next heading.

## Effective stress paths
![Stress paths, BH1 samples (CU triaxial)](figures/paths.png)   ← image, fitted, centred; alt text = caption
![q–p′ stress paths of six CU tests on BH1 and BH2](figures/paths.png "Stress paths")   ← long alt text, short caption
![Site photo looking north](photo.jpg "")                     ← alt text only, no caption

## Strength parameters
| Sample | c′ (kPa) | φ′ (°) |                ← table; header row styled, numbers right-aligned
|---|---|---|
| BH1-S1 | 12.3 | 31.5 |

## Two options
::: left
- Option A: deeper embedment
:::
::: right
![Section](figures/section.png)
:::                                        ← two columns; each side takes text, an image or a table

## Recommendation
> Increase wall embedment by 2 m and add drainage.   ← title on top + large centred statement

##
> Questions?                                 ← empty "##": the statement alone (it becomes the slide's title)
```

Every slide gets a real title placeholder, even in the built-in design. PowerPoint's outline view, slide navigation, screen readers and the accessibility checker all rely on it. Don't add titles as plain text boxes.

The layout rules:

- When a slide has text plus one visual (image, table or chart), the text goes above and takes up to 40% of the height. The visual fills the rest.
- Body text starts at 24 pt (22 pt on 4:3). It shrinks to fit, down to `--min-font` (default 14), and every shrink or likely overflow is reported. Treat a report as a sign that the slide needs splitting. Short lists grow up to 30 pt and are centred vertically, so a slide with three bullets doesn't look half-empty.
- Image paths are relative to the outline file. Images keep their aspect ratio. Use PNG at 150–300 dpi for figures, and keep the original files so the user can update them.
- Slide numbers and the footer are added to content slides. Use `--no-numbers` to switch them off.

## 2. Charts

A fenced block with the language `chart` holds JSON:

```chart
{"type": "column", "categories": ["Static", "Seismic"],
 "series": {"FoS": [1.32, 1.08], "Target": [1.5, 1.2]},
 "y_title": "Factor of safety", "number_format": "0.00", "data_labels": true}
```

| Key | Meaning |
|---|---|
| `type` | `column` (= `bar`), `barh`, `line`, `pie`, `stacked`, `scatter` |
| `categories` | x labels (not for scatter) |
| `series` | `{"name": [values…]}`. For scatter: `{"name": [[x, y], …]}`, with `"lines": true` to connect the points |
| `x_title`, `y_title`, `title` | axis and chart titles. Always give units |
| `number_format` | value axis and data labels, e.g. `"0.0"`, `"#,##0"`, `"0%"` |
| `data_labels` | show values on bars and points |
| `y_reverse` | reverse the value axis, e.g. for depth. The x axis stays at the bottom |
| `y_min`, `y_max` | fixed value-axis limits (bars should start at 0) |
| `colors` | `{"series name": "A6A6A6"}`. Grey out reference series ("Target", "Previous") so the main series stands out |

Charts are native PowerPoint charts. The user can click Edit Data in PowerPoint and change the numbers. For figures from analysis software, such as plots from PLAXIS or Python, use an image instead.

Value against target: plot both as series and grey out the target with `"colors": {"Target": "BFBFBF"}`. Put the comparison in the slide title, for example "Both cases fall short of the target FoS".

## 3. Templates

```bash
python scripts/pptx_inspect.py corporate.pptx --layouts      # see the layouts and their placeholders
python scripts/pptx_build.py talk.md -o talk.pptx --template corporate.pptx
```

- The builder picks layouts by name and placeholder type: Title Slide (title slide), "Section Header" (sections), "Title and Content" (text slides) and "Title Only" (slides with a visual). Text-only slides fill the template's body placeholder, so the template's own bullet styles apply.
- Any slides already in the template are removed unless you pass `--keep-template-slides`.
- When the layouts have unusual names and the result looks wrong, check `--layouts`. Fall back to the built-in design and set `--accent` to the brand colour, then tell the user.
- `.potx` files work as templates too.

## 4. JSON input

Use JSON when slides come from data, for example one slide per borehole:

```json
{"meta": {"title": "Borehole summaries", "footer": "Lot 12"},
 "slides": [
   {"type": "section", "title": "Boreholes"},
   {"title": "BH1: residual clay over greywacke", "bullets": ["Depth 8 m", ["Water at 2.5 m"]], "notes": "…"},
   {"title": "BH1 log", "image": "logs/bh1.png", "caption": "BH1 log"},
   {"title": "Summary", "table": [["BH", "Depth"], ["BH1", "8.0"]]},
   {"title": "Depths", "chart": {"type": "column", "categories": ["BH1", "BH2"], "series": {"Depth (m)": [8, 6.5]}}}
 ]}
```

## 5. Beyond the builder: python-pptx recipes

Open the built deck and adjust it:

```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

prs = Presentation("talk.pptx")
s = prs.slides[5]

# callout box pointing at a feature on a figure
box = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.5), Inches(2), Inches(3.5), Inches(0.9))
box.fill.solid(); box.fill.fore_color.rgb = RGBColor(0xFF, 0xF2, 0xCC); box.line.color.rgb = RGBColor(0xC5, 0x5A, 0x11)
box.text_frame.text = "Peak strength at ~4 % strain"
box.text_frame.paragraphs[0].runs[0].font.size = Pt(16)

# arrow
arrow = s.shapes.add_connector(1, Inches(8.5), Inches(2.45), Inches(7.2), Inches(3.4))   # 1 = straight
arrow.line.width = Pt(2); arrow.line.color.rgb = RGBColor(0xC5, 0x5A, 0x11)
arrow.line._get_or_add_ln().append(arrow.line._get_or_add_ln().makeelement(
    "{http://schemas.openxmlformats.org/drawingml/2006/main}tailEnd", {"type": "triangle"}))

# hyperlink on text
run = box.text_frame.paragraphs[0].runs[0]
run.hyperlink.address = "https://doi.org/10.1680/jgeot.19.P.123"

# video or audio (poster image optional)
# s.shapes.add_movie("clip.mp4", Inches(1), Inches(1.5), Inches(6), Inches(3.4), poster_frame_image="poster.png")

prs.save("talk_v2.pptx")
```

- Positions are in EMU (`Inches()`, `Pt()`, `Emu()`). The slide is `prs.slide_width` × `prs.slide_height`. A 16:9 slide is 13.333 × 7.5 in.
- To change chart data afterwards: `chart.replace_data(CategoryChartData(...))`.
- Slide transitions and animations aren't exposed by python-pptx. Say that they're best added in PowerPoint, and don't hand-edit timing XML.
