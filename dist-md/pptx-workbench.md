---
name: pptx-workbench
description: "Build, edit, review and convert PowerPoint decks (.pptx) with tested Python scripts — write the talk as a Markdown outline and get a clean 16:9 deck (or one in your own template) with native bullets, tables, editable charts, images, section dividers and speaker notes; then QA it for overflowing text, tiny fonts, missing alt text, low-res images and leftovers, and render a contact sheet to check it visually. Use this whenever the user wants slides or a presentation file: a conference talk, lecture, client briefing, thesis defence, lab meeting update; filling a .pptx template; extracting or summarising what's in a deck; replacing text across slides; reordering/deleting/merging slides; converting to PDF. Trigger on \"slides\", \"deck\", \"PowerPoint\", \"pptx\", \"presentation\" or an attached .pptx."
license: MIT (see LICENSE)
---

**Single-file build.** This is the `pptx-workbench` skill packed into one file on 2026-11-05. The instructions below are its SKILL.md, unchanged. Its supporting files (3 reference files, 8 scripts and the licence) are embedded verbatim under "Bundled files" at the end, each with a SHA-256 checksum. You can read a reference there directly. Before you run a script or use an asset, unpack the files once:

```bash
python3 - "${CLAUDE_SKILL_DIR}/SKILL.md" "${TMPDIR:-/tmp}/pptx-workbench" <<'PY'
import hashlib, os, re, sys
src, out = sys.argv[1], sys.argv[2]
if not os.path.isfile(src):
    src = "/mnt/skills/user/pptx-workbench/SKILL.md"
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

The first argument is the path of this file. Claude Code and Cowork fill it in for you; elsewhere, use the path you read this file from (on claude.ai the command also tries `/mnt/skills/user/pptx-workbench/SKILL.md`). The command prints the folder it wrote to. From then on, use that folder wherever the instructions mean this skill's folder: paths such as `scripts/...`, `references/...`, `assets/...` and `<this-skill>/...` all point into it.

---


# PPTX Workbench

A toolkit for PowerPoint. The scripts do the mechanics, and the reference files hold the design guidance and recipes. Every script is a standalone Python CLI, so run it with `--help` to see the options.

Paths such as `scripts/pptx_build.py` are relative to this skill's folder, the directory that holds this SKILL.md, so prefix them with that folder's path when you run them. Always pass `-o` with a path in the user's folder, because outputs otherwise go next to the input. Never write into the skill folder.

## Setup

```bash
pip install python-pptx pillow pypdfium2      # pypdfium2: renders only
# LibreOffice (impress) is needed for PDF/PNG renders and contact sheets
```

## Pick the path

| Goal | Use | Details |
|---|---|---|
| A new deck from content you've drafted | write a Markdown outline → `scripts/pptx_build.py` | references/building-decks.md |
| A new deck in the user's corporate or university template | `pptx_build.py --template their.pptx` | references/building-decks.md |
| What makes slides good (structure, density, charts) | — | references/design-principles.md |
| What's in an existing deck | `scripts/pptx_inspect.py`, `scripts/pptx_text.py` | references/editing-decks.md |
| Change wording everywhere, fill `{{placeholders}}`, or replace placeholder text with bullets | `scripts/pptx_replace.py` (a `\n` in the replacement makes new paragraphs) | references/editing-decks.md |
| Delete, reorder, duplicate, hide or merge slides; set notes | `scripts/pptx_slides.py` | references/editing-decks.md |
| Check a deck before it's shown or sent | `scripts/pptx_check.py`, then `pptx_render.py --sheet` | references/design-principles.md |
| PDF, slide PNGs, one-page overview | `scripts/pptx_render.py --pdf / --png / --sheet` | — |

## Working principles

**Plan the story before the slides.** Decide the audience, the time and the 3–5 points you want people to remember. Then draft the outline: about one slide per minute for a talk, with one message per slide and a title that states it ("Both cases fall below the 1.5 target", not "Results"). design-principles.md has structures for common talk types.

**Write the outline in Markdown and let the builder lay it out.** `pptx_build.py` turns `##` headings, bullets, images, tables, chart blocks and `Notes:` lines into consistent slides. It uses native bullets and editable charts, keeps margins, and fits images by aspect ratio. Hand-placing shapes is slow and inconsistent, so do it only for one-off visuals.

**Put detail in speaker notes, not on the slide.** Aim for ≤ 6 bullets and ≤ 40 words per slide, with body text ≥ 18 pt. When the builder says it shrank text or that text overflows, split the slide rather than accept small type.

**Use real data and real figures.** Make charts from actual numbers with a `chart` block, so they stay editable. Use figures at 150 dpi or more. The builder and `pptx_check.py` warn about blurry images. Every chart needs axis titles with units.

**Always look at the deck, and read it critically.** Run `pptx_check.py deck.pptx`, then `pptx_render.py deck.pptx --sheet`. Open the contact-sheet PNG and look for overflow, overlaps, empty areas and inconsistent styling before you deliver. LibreOffice renders close to PowerPoint, but fonts can be substituted.

Then check the content. Do the numbers in the text match the charts and tables? Does each figure show what its caption claims? Are any figures placeholders or duplicates? Do the notes refer to slides or appendices that don't exist? The check can't judge any of this. design-principles.md has the checklist.

**Respect the user's template and decks.** Build with `--template` so the user's masters, fonts and colours apply. When editing their deck, change only what's asked, keep a copy, and confirm with `pptx_text.py` or `pptx_inspect.py` afterwards.

## Quick recipes

```bash
# Outline → deck (built-in clean design; themes: navy, teal, charcoal, forest, maroon; or --accent HEX)
python scripts/pptx_build.py talk.md -o talk.pptx --theme navy
python scripts/pptx_check.py talk.pptx
python scripts/pptx_render.py talk.pptx --sheet -o talk_overview.png     # look at it

# Same outline in the user's template
python scripts/pptx_build.py talk.md -o talk_uni.pptx --template university_template.pptx

# Summarise an existing deck / reuse its content
python scripts/pptx_text.py their_deck.pptx -o their_deck.md

# Fill a template deck's {{placeholders}}; replace wording everywhere including notes
python scripts/pptx_replace.py template.pptx -o client.pptx --fill client.json --strict
python scripts/pptx_replace.py deck.pptx -o deck_v2.pptx --find "Lot 12" --replace "Lot 14" --notes
python scripts/pptx_replace.py template.pptx -o t2.pptx --find "Lorem ipsum dolor" --replace $'Findings\nOptions\nRecommendation'   # 3 bullets

# Restructure
python scripts/pptx_slides.py reorder deck.pptx --order 1,2,5,3,4,6- -o deck_v2.pptx
python scripts/pptx_slides.py delete deck.pptx --slides 7-9 -o short.pptx

# Handout PDF
python scripts/pptx_render.py talk.pptx --pdf -o talk.pdf
```

## Delivering results

Give the slide count and the structure, for example "12 slides: title, 3 sections, summary". List anything the builder or check flagged that you left for the user, such as a low-resolution figure they should replace. Mention that speaker notes are included where you wrote them. Share the contact-sheet PNG so the user can see the deck without opening it.

---

## Bundled files

The skill's supporting files, verbatim. Unpack them with the command at the top, or read one here. Line is where each file starts in this document.

| File | Size | Line |
|---|---:|---:|
| `references/building-decks.md` | 7.4 KB | 135 |
| `references/design-principles.md` | 5.1 KB | 296 |
| `references/editing-decks.md` | 4.4 KB | 365 |
| `scripts/_pptx_common.py` | 5.5 KB | 448 |
| `scripts/pptx_build.py` | 37.5 KB | 623 |
| `scripts/pptx_check.py` | 10.1 KB | 1481 |
| `scripts/pptx_inspect.py` | 4.3 KB | 1685 |
| `scripts/pptx_render.py` | 3.4 KB | 1787 |
| `scripts/pptx_replace.py` | 4.5 KB | 1875 |
| `scripts/pptx_slides.py` | 6.1 KB | 1989 |
| `scripts/pptx_text.py` | 4.2 KB | 2144 |
| `LICENSE` | 1.1 KB | 2256 |

### `references/building-decks.md`

<!-- bundle-file: references/building-decks.md sha256=84a43401ac41c8b1708acab2348155e75188833bcf43740626b465050c6e1348 -->
````markdown
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
````

### `references/design-principles.md`

<!-- bundle-file: references/design-principles.md sha256=3907ee0b570e1b7f373a5aa8d6efde7d5798830cf6e1764c9a72cb6be1a344ee -->
````markdown
# Designing slides that work

## Structure first

| Talk | Slides | Shape |
|---|---|---|
| Conference talk (12–15 min) | 10–14 | Title → problem and why it matters → gap and aim → method (1–2) → key results (3–5) → implications → conclusions (3 bullets) → thanks and contact |
| Lab or research group update (10 min) | 6–8 | Last time → what I did → results (with honest problems) → next steps → questions or asks |
| Thesis defence (30–45 min) | 25–40 | Context → research questions → one section per chapter (aim, method, key result, contribution) → synthesis → limitations → future work |
| Client or stakeholder briefing | 8–12 | **Recommendation first** → site or situation → findings → options with cost and risk → recommendation and next steps |
| Lecture (50 min) | 25–35 | Learning outcomes → concept → worked example → check question (repeat) → summary |

A good rule of thumb is about one slide per minute, plus a title slide and a closing slide.

## One message per slide

- **The title is the message**, written as a sentence: "Factor of safety falls below 1.5 when the water table rises". "Results 2" tells the audience nothing.
- Use **≤ 6 bullets and ≤ 40 words** per slide, and keep bullets to 1 line where possible. Put the rest in speaker notes.
- When a slide needs a second message, make a second slide.
- Use parallel grammar for bullets: start each with a noun, or each with a verb.

## Make it readable from the back of the room

- Body text ≥ 18 pt (24 pt preferred), titles 28–36 pt, and nothing below 14 pt. Table text can go down to 14 pt if needed.
- Use high contrast: dark text on a light background, or the reverse. No text over busy photos.
- Use at most 2 fonts and 1 accent colour, plus grey. Use colour to point at things, not to decorate.
- Leave space around content. Crowded slides look harder than they are.

## Figures, tables and charts

- **Figures carry the evidence.** Make them large: they should fill the slide below the title. Use 150 dpi or more (300 for print). Re-export from the source with large fonts. Axis labels at 8 pt in a paper become unreadable on a slide.
- **Put units on every axis** ("Depth (m)"), and in table headers rather than in cells.
- **Highlight the point**: an accent colour on the key series, an annotation ("target 1.5"), or grey for everything else.
- **Simplify tables.** Show ≤ 6 rows and ≤ 5 columns on a slide, with a consistent number of decimals per column and numbers right-aligned. Put full tables in an appendix or handout.
- **Chart choice:** use bars to compare categories, lines for trends over time, scatter for relationships, and depth profiles with depth downwards. Avoid 3D, pie charts with more than 5 slices, and dual axes unless they're essential.
- Cite data and figure sources in small text under the figure, for example "(after Smith 2020)".

## Accessibility

- Every slide has a unique title in a real title placeholder. Screen readers, outline view and PowerPoint's accessibility checker rely on it, and `pptx_build.py` creates one. `pptx_check.py` reports `no-title` when a deck uses plain text boxes as titles.
- Every picture has alt text. The builder uses the caption, and `pptx_check.py` flags missing ones.
- Don't rely on colour alone. Use labels and line styles too, because about 1 in 12 men is colour-blind.
- Reading order follows creation order. The builder adds the title first.

## Before delivering: the QA loop

1. Run `python scripts/pptx_check.py deck.pptx` and fix everything except judgement calls.
2. Run `python scripts/pptx_render.py deck.pptx --sheet` and look at the PNG:
   - Is anything cut off, overlapping or too small?
   - Do all the slides look like one deck, with the same title position, fonts and colours?
   - Are images sharp, and are charts readable at thumbnail size? If you can read it in the contact sheet, the room can read it on screen.
3. Read the titles in order with `pptx_text.py`. They should tell the story on their own.
4. Do the content review that no script can do:
   - Numbers in the text match the charts and tables, for example "below the 1.5 target" when the chart shows two different targets.
   - Each figure shows what its caption says. Look for placeholder or duplicate pictures, which `pptx_check.py` flags as `duplicate`.
   - Claims match the evidence. If the notes say "BH2 is weaker" but the plot shows it plotting higher, ask.
   - Notes and slides don't refer to things that don't exist, such as appendices or slide numbers.
   - Every chart axis has a title with units (`chart-axes`). Checks and recommendations are stated.
5. Check the timing: count the slides against the time slot.

`pptx_check.py` defaults to 40 words and 6 bullets per slide (tables excluded). For reading decks or handouts, relax these with `--max-words 120 --max-bullets 10`. Footers and slide numbers are exempt from the font-size check.

`pptx_check.py` estimates text height from font size and box size. That's a heuristic, so the render is the final word. An `overlap` finding is fine when it's deliberate, such as a callout placed on a figure.
````

### `references/editing-decks.md`

<!-- bundle-file: references/editing-decks.md sha256=7541be7d35223935c8490609ce284f33d376c86f7b030c5b1806f30099beae1a -->
````markdown
# Reading and editing existing decks

## Read

```bash
python scripts/pptx_inspect.py deck.pptx              # per slide: layout, title, shape counts, words, notes, {{placeholders}}, hidden
python scripts/pptx_inspect.py deck.pptx --layouts    # the template's layouts and placeholders
python scripts/pptx_text.py deck.pptx -o deck.md      # titles, bullets, tables, chart data, alt text, notes
```

`pptx_text.py` orders shapes top to bottom and left to right. It skips footers and slide numbers, gives chart data as a table, and marks pictures with their alt text. Use its output to summarise a deck, turn it into a document, or rebuild it with `pptx_build.py`. For a rebuild, edit the Markdown and convert `## Slide n: Title` back to `## Title`.

## Replace text and fill templates

```bash
python scripts/pptx_replace.py deck.pptx --find "2025" --dry-run                  # where it occurs
python scripts/pptx_replace.py deck.pptx -o deck_v2.pptx --find "2025" --replace "2026" --notes
python scripts/pptx_replace.py deck.pptx -o deck_v2.pptx --map renames.json        # several at once
python scripts/pptx_replace.py template.pptx -o client.pptx --fill data.json --strict
```

- A `\n` in the replacement or fill value starts a new paragraph. Each new paragraph copies the original's bullet style and level, and the first run's formatting. Use this to turn template text such as "Lorem ipsum" into several bullets.
- Zero matches print as "0 match(es)". Check the spelling, or try `--ignore-case`.
- Matching works across runs inside a paragraph, and the formatting of the run where the match starts is kept. Text in groups and table cells is covered. Chart titles and labels aren't: edit those with python-pptx (`chart.chart_title.text_frame.text = …`) or rebuild the chart.
- The `--fill` placeholders look like `{{client}}` and `{{project.name}}`. With `--strict`, the script stops if a key is missing.
- One template per client or project: `pptx_inspect.py` lists the `{{placeholders}}` on each slide.

## Restructure

```bash
python scripts/pptx_slides.py delete deck.pptx --slides 4,9-11 -o out.pptx
python scripts/pptx_slides.py keep deck.pptx --slides 1-3,12 -o excerpt.pptx
python scripts/pptx_slides.py reorder deck.pptx --order 1,2,6,3,4,5,7- -o out.pptx
python scripts/pptx_slides.py duplicate deck.pptx --slides 5 -o out.pptx
python scripts/pptx_slides.py hide deck.pptx --slides 14-16 -o out.pptx       # backup slides
python scripts/pptx_slides.py notes deck.pptx --notes notes.json -o out.pptx  # {"3": "…", "4": "…"}
python scripts/pptx_slides.py merge a.pptx b.pptx -o combined.pptx
```

"Move X to be first" usually means first after the title slide. When the deck has a title slide, ask, or say which you did.

Limits:

- **duplicate** and **merge** copy text, shapes, pictures, tables and notes, but not charts. The script reports skipped charts. Rebuild them with a `chart` block, or copy the slide in PowerPoint.
- **merge** puts the second deck's slides on the first deck's Blank layout, so their master styling isn't carried over. Different slide sizes are reported. For decks from different templates, PowerPoint's Reuse Slides works better, so say so.

## Direct edits with python-pptx

```python
from pptx import Presentation
from pptx.util import Pt
prs = Presentation("deck.pptx")

# replace a placeholder's body with bullets (keeps the layout's bullet styling)
body = next(ph for ph in prs.slides[1].placeholders if ph.placeholder_format.idx == 1)
items = ["Findings", "Options", "Recommendation"]
body.text_frame.text = items[0]
for t in items[1:]:
    body.text_frame.add_paragraph().text = t

for slide in prs.slides:
    for shape in slide.shapes:
        if shape.has_text_frame:
            for p in shape.text_frame.paragraphs:
                for r in p.runs:
                    if r.font.size and r.font.size.pt < 14:
                        r.font.size = Pt(14)                       # lift tiny text
slide = prs.slides[2]
slide.notes_slide.notes_text_frame.text = "Key point: …"            # speaker notes
for s in prs.slides:                                               # alt text for every picture lacking it
    for shape in s.shapes:
        if shape.shape_type == 13 and not shape._element.nvPicPr.cNvPr.get("descr"):   # 13 = picture
            shape._element.nvPicPr.cNvPr.set("descr", shape.name)   # better: describe what it shows
prs.save("deck_v2.pptx")
```

Always save to a new file, then run `pptx_check.py` and `pptx_render.py --sheet` on the result.
````

### `scripts/_pptx_common.py`

<!-- bundle-file: scripts/_pptx_common.py sha256=4a6d0699c57a5bbb07bd92258b4b75ead9d6ebb8908261f5119ee71a73db0bcb -->
````python
"""Shared helpers for pptx-workbench scripts (imported from the same folder)."""
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True

try:
    from pptx import Presentation  # noqa: F401
    from pptx.enum.shapes import MSO_SHAPE_TYPE, PP_PLACEHOLDER  # noqa: F401
    from pptx.util import Emu, Pt  # noqa: F401
except ImportError:
    sys.exit("python-pptx is required: pip install python-pptx")

EMU_PER_PT = 12700
EMU_PER_IN = 914400


def iter_shapes(shapes):
    """All shapes, descending into groups."""
    for sh in shapes:
        if sh.shape_type == MSO_SHAPE_TYPE.GROUP:
            yield from iter_shapes(sh.shapes)
        else:
            yield sh


def iter_text_frames(slide, notes=False):
    """(shape, text_frame) for every text-bearing shape, table cell and (optionally) the notes."""
    for sh in iter_shapes(slide.shapes):
        if sh.has_text_frame:
            yield sh, sh.text_frame
        if getattr(sh, "has_table", False) and sh.has_table:
            for row in sh.table.rows:
                for cell in row.cells:
                    yield sh, cell.text_frame
    if notes and slide.has_notes_slide:
        yield None, slide.notes_slide.notes_text_frame


def replace_in_paragraph(p, regex, repl):
    """Run-aware replace inside one paragraph; keeps the formatting of the run where a match starts."""
    runs = list(p.runs)
    if not runs:
        return 0
    texts = [r.text for r in runs]
    full = "".join(texts)
    matches = [m for m in regex.finditer(full) if m.start() != m.end()]
    if not matches:
        return 0
    starts, pos = [], 0
    for t in texts:
        starts.append(pos)
        pos += len(t)

    def locate(off, end=False):
        for i in range(len(runs)):
            lo, hi = starts[i], starts[i] + len(texts[i])
            if (lo <= off < hi) or (end and lo < off <= hi):
                return i, off - lo
        return len(runs) - 1, len(texts[-1])

    for m in reversed(matches):
        new = repl(m) if callable(repl) else m.expand(repl)
        si, so = locate(m.start())
        ei, eo = locate(m.end(), end=True)
        if si == ei:
            texts[si] = texts[si][:so] + new + texts[si][eo:]
        else:
            texts[si] = texts[si][:so] + new
            for k in range(si + 1, ei):
                texts[k] = ""
            texts[ei] = texts[ei][eo:]
    for r, t in zip(runs, texts):
        if r.text != t:
            r.text = t
    if any("\n" in t or "\v" in t for t in texts):
        split_paragraph_lines(p)
    return len(matches)


def split_paragraph_lines(p):
    """Turn line breaks inside a paragraph's runs into separate paragraphs (e.g. one bullet each),
    copying the paragraph's properties and the first run's formatting."""
    import copy
    from pptx.oxml.ns import qn
    full = "".join(r.text for r in p.runs).replace("\v", "\n")
    lines = full.split("\n")
    p_el = p._p
    runs = list(p.runs)
    template_r = copy.deepcopy(runs[0]._r) if runs else None
    for r in runs[1:]:
        p_el.remove(r._r)
    if runs:
        runs[0].text = lines[0]
    anchor = p_el
    for line in lines[1:]:
        new_p = copy.deepcopy(p_el)
        for r in new_p.findall(qn("a:r")) + new_p.findall(qn("a:br")) + new_p.findall(qn("a:fld")):
            new_p.remove(r)
        if template_r is not None:
            r = copy.deepcopy(template_r)
            r.find(qn("a:t")).text = line
            end = new_p.find(qn("a:endParaRPr"))
            if end is not None:
                end.addprevious(r)
            else:
                new_p.append(r)
        anchor.addnext(new_p)
        anchor = new_p


def soffice():
    for name in ("soffice", "libreoffice", "/Applications/LibreOffice.app/Contents/MacOS/soffice"):
        found = shutil.which(name) or (name if os.path.exists(name) else None)
        if found:
            return found
    return None


def to_pdf(src, outdir):
    exe = soffice()
    if not exe:
        sys.exit("LibreOffice not found (apt install libreoffice-impress / brew install --cask libreoffice)")
    with tempfile.TemporaryDirectory() as profile:
        res = subprocess.run([exe, f"-env:UserInstallation=file://{profile}", "--headless", "--convert-to", "pdf",
                              "--outdir", outdir, src], capture_output=True, text=True, timeout=300)
    out = os.path.join(outdir, os.path.splitext(os.path.basename(src))[0] + ".pdf")
    if not os.path.exists(out):
        sys.exit(f"LibreOffice conversion failed: {res.stderr.strip() or res.stdout.strip()}")
    return out


def parse_slides(spec, n):
    """'1-3,7,10-' -> 0-based indices."""
    if not spec:
        return list(range(n))
    out = []
    for part in str(spec).split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            s, e = (int(a) if a else 1), (int(b) if b else n)
        else:
            s = e = int(part)
        if s < 1 or e > n or s > e:
            sys.exit(f"Slide range '{part}' is outside 1-{n}")
        out += [i for i in range(s - 1, e) if i not in out]
    return out


def slide_title(slide):
    try:
        if slide.shapes.title is not None and slide.shapes.title.text.strip():
            return slide.shapes.title.text.strip()
    except Exception:
        pass
    for sh in iter_shapes(slide.shapes):
        if sh.has_text_frame and sh.text_frame.text.strip():
            return sh.text_frame.text.strip().split("\n")[0][:80]
    return ""


PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z0-9_.\-]+)\s*\}\}")
````

### `scripts/pptx_build.py`

<!-- bundle-file: scripts/pptx_build.py sha256=a6d478cbcc9d6f57d87f78d07b3f8570d9ec36992d9153f017832efe71aa8d8c -->
````python
#!/usr/bin/env python3
"""Build a PowerPoint deck from a Markdown outline (or JSON), with a clean built-in
design or the layouts of your own template.

    python pptx_build.py talk.md -o talk.pptx [--template house.pptx] [--theme navy|teal|charcoal|forest]
                         [--accent 1F3864] [--font Calibri] [--ratio 16:9|4:3] [--no-numbers]

Outline format (one slide per heading; YAML-ish front matter optional):

    ---
    title: Slope stability at Lot 12
    subtitle: Site investigation findings
    author: R. Kalatehjari, GEOTECH-LAB
    date: 3 October 2026
    footer: Lot 12 retaining wall
    ---
    # Background                     <- "# " = section divider slide
    ## Site and geology              <- "## " = content slide title
    - Bullet                         <- bullets; indent 2+ spaces for sub-bullets
      - Sub-bullet
    Plain lines become paragraphs.
    Notes: what to say here          <- speaker notes (rest of the slide's lines)

    ## Results
    ![Effective stress paths](fig/paths.png)    <- image slide (alt text = caption)
    ![q–p′ paths of six CU tests, BH1 and BH2](fig/paths.png "Stress paths")  <- alt + shorter caption
    ![Site photo](photo.jpg "")                  <- alt text, no caption

    ## Strength parameters
    | Sample | c' (kPa) | phi' (deg) |          <- table slide
    |---|---|---|
    | BH1 | 5 | 32 |

    ## Factor of safety
    ```chart
    {"type": "bar", "categories": ["Static", "Seismic"], "series": {"FoS": [1.32, 1.08]},
     "y_title": "FoS", "number_format": "0.00", "colors": {"Target": "A6A6A6"}}
    ```                                          <- native, editable chart (bar|column|line|pie|scatter)

    ## Two views
    ::: left
    - text, image or table
    :::
    ::: right
    ![Plan](plan.png)
    :::                                          <- two-column slide

    ## Key message
    > Retaining wall needs 2 m deeper embedment.  <- title + big centred statement
    ##
    > Retaining wall needs 2 m deeper embedment.  <- empty "##": the statement alone (it becomes the slide title)

JSON input: {"meta": {...}, "slides": [{"type": "bullets", "title": "...", "bullets": ["a", ["sub"]], "notes": "..."}, ...]}
Text that would overflow is shrunk (down to --min-font) and reported; check with pptx_check.py.
"""
import argparse
import json
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _pptx_common  # noqa: E402,F401

from pptx import Presentation  # noqa: E402
from pptx.chart.data import CategoryChartData, XyChartData  # noqa: E402
from pptx.dml.color import RGBColor  # noqa: E402
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION  # noqa: E402
from pptx.enum.shapes import MSO_SHAPE, PP_PLACEHOLDER  # noqa: E402
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN  # noqa: E402
from pptx.util import Emu, Inches, Pt  # noqa: E402

THEMES = {"navy": "1F3864", "teal": "006D77", "charcoal": "333F48", "forest": "2E6B3F", "maroon": "7B1E3A"}
WARNINGS = []


# ----------------------------------------------------------------------------- parsing
def parse_markdown(text, base_dir):
    meta, slides = {}, []
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip().lower()] = v.strip().strip('"')
        text = text[m.end():]
    cur = None
    lines = text.splitlines()
    i = 0

    def new(kind, title):
        nonlocal cur
        cur = {"type": kind, "title": title, "blocks": [], "notes": ""}
        slides.append(cur)

    while i < len(lines):
        line = lines[i]
        if line.startswith("# "):
            new("section", line[2:].strip())
        elif line.startswith("## ") or line.strip() == "##":
            new("content", line[3:].strip())
        elif cur is None:
            if line.strip():
                new("content", "")
                continue
        elif re.match(r"^\s*(Notes|Note|Speaker notes):", line, re.I):
            cur["notes"] = "\n".join([line.split(":", 1)[1].strip()] + [l for l in lines[i + 1:] if not l.startswith("#")][:0])
            j = i + 1
            extra = []
            while j < len(lines) and not lines[j].startswith("#"):
                extra.append(lines[j])
                j += 1
            cur["notes"] = (cur["notes"] + "\n" + "\n".join(extra)).strip()
            i = j
            continue
        elif line.strip().startswith("```chart"):
            j = i + 1
            body = []
            while j < len(lines) and not lines[j].strip().startswith("```"):
                body.append(lines[j])
                j += 1
            try:
                cur["blocks"].append(("chart", json.loads("\n".join(body))))
            except json.JSONDecodeError as e:
                sys.exit(f"Chart block on slide '{cur['title']}' is not valid JSON: {e}")
            i = j + 1
            continue
        elif line.strip().startswith(":::") and line.strip()[3:].strip() in ("left", "right"):
            side = line.strip()[3:].strip()
            j = i + 1
            body = []
            while j < len(lines) and lines[j].strip() != ":::":
                body.append(lines[j])
                j += 1
            sub = parse_blocks(body, base_dir)
            cur["blocks"].append((side, sub))
            i = j + 1
            continue
        else:
            cur.setdefault("_raw", []).append(line)
            nxt = lines[i + 1] if i + 1 < len(lines) else "#"
            if nxt.startswith("#") or nxt.strip().startswith("```chart") or re.match(r"^\s*(Notes|Note|Speaker notes):", nxt, re.I) \
                    or (nxt.strip().startswith(":::") and nxt.strip()[3:].strip() in ("left", "right")):
                cur["blocks"].extend(parse_blocks(cur.pop("_raw"), base_dir))
        i += 1
    for s in slides:
        if "_raw" in s:
            s["blocks"].extend(parse_blocks(s.pop("_raw"), base_dir))
    return meta, slides


def parse_blocks(lines, base_dir):
    blocks, i = [], 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        img = re.match(r'^\s*!\[(.*?)\]\((\S+?)(?:\s+"(.*?)")?\)\s*$', line)
        if img:
            path = img.group(2).strip()
            path = path if os.path.isabs(path) else os.path.join(base_dir, path)
            alt = img.group(1).strip()
            caption = alt if img.group(3) is None else img.group(3).strip()  # ![alt](p "caption"); "" = no caption
            blocks.append(("image", {"path": path, "caption": caption, "alt": alt}))
            i += 1
            continue
        if line.strip().startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            blocks.append(("table", rows))
            continue
        if line.lstrip().startswith(">"):
            q = []
            while i < len(lines) and lines[i].lstrip().startswith(">"):
                q.append(lines[i].lstrip()[1:].strip())
                i += 1
            blocks.append(("quote", " ".join(q)))
            continue
        b = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", line)
        if b:
            items = []
            while i < len(lines):
                b = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", lines[i])
                if not b:
                    if lines[i].strip() and lines[i].startswith("  ") and items:
                        items[-1] = (items[-1][0], items[-1][1] + " " + lines[i].strip(), items[-1][2])
                        i += 1
                        continue
                    break
                level = min(len(b.group(1).replace("\t", "    ")) // 2, 4)
                items.append((level, b.group(3).strip(), b.group(2)[0].isdigit()))
                i += 1
            blocks.append(("bullets", items))
            continue
        para = [line.strip()]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^\s*([-*+]|\d+[.)])\s+|^\s*!\[|^\s*\||^\s*>", lines[i]):
            para.append(lines[i].strip())
            i += 1
        blocks.append(("para", " ".join(para)))
    return blocks


def from_json(d, base_dir):
    meta = d.get("meta", {})
    slides = []
    for s in d.get("slides", []):
        t = s.get("type", "bullets")
        kind = "section" if t == "section" else "content"
        blocks = []
        if s.get("bullets"):
            items = []

            def walk(xs, lvl):
                for x in xs:
                    if isinstance(x, list):
                        walk(x, lvl + 1)
                    else:
                        items.append((lvl, str(x), False))
            walk(s["bullets"], 0)
            blocks.append(("bullets", items))
        for k in ("text",):
            if s.get(k):
                blocks.append(("para", s[k]))
        if s.get("image"):
            p = s["image"] if os.path.isabs(s["image"]) else os.path.join(base_dir, s["image"])
            blocks.append(("image", {"path": p, "caption": s.get("caption", "")}))
        if s.get("table"):
            blocks.append(("table", s["table"]))
        if s.get("chart"):
            blocks.append(("chart", s["chart"]))
        if s.get("quote"):
            blocks.append(("quote", s["quote"]))
        slides.append({"type": kind, "title": s.get("title", ""), "blocks": blocks, "notes": s.get("notes", "")})
    return meta, slides


# ----------------------------------------------------------------------------- rendering helpers
def rgb(hexstr):
    return RGBColor.from_string(hexstr.upper())


def style_run(run, size=None, bold=None, color=None, font=None, italic=None):
    f = run.font
    if size:
        f.size = Pt(size)
    if bold is not None:
        f.bold = bold
    if italic is not None:
        f.italic = italic
    if color:
        f.color.rgb = rgb(color)
    if font:
        f.name = font


def add_rich(paragraph, text, size, color, font, bold=None):
    """**bold**, *italic* and `code` inline markup -> runs."""
    parts = re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)", text)
    for part in parts:
        if not part:
            continue
        r = paragraph.add_run()
        if part.startswith("**") and part.endswith("**"):
            r.text = part[2:-2]
            style_run(r, size, True, color, font)
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            r.text = part[1:-1]
            style_run(r, size, bold, color, font, italic=True)
        elif part.startswith("`") and part.endswith("`"):
            r.text = part[1:-1]
            style_run(r, size, bold, color, "Consolas")
        else:
            r.text = part
            style_run(r, size, bold, color, font)


def set_bullet(p, level, kind, color):
    """Real PowerPoint bullets (so they behave natively when edited): kind = bullet | num | none."""
    from pptx.oxml.ns import qn
    from lxml import etree
    pPr = p._p.get_or_add_pPr()
    step = 342900  # 0.375 in per level
    pPr.set("lvl", str(level))
    if kind == "none":
        pPr.set("marL", str(step * level))
        pPr.set("indent", "0")
    else:
        pPr.set("marL", str(step * (level + 1)))
        pPr.set("indent", str(-step))
    for tag in ("a:buClr", "a:buSzPct", "a:buFont", "a:buNone", "a:buChar", "a:buAutoNum"):
        for e in pPr.findall(qn(tag)):
            pPr.remove(e)
    anchor = next((c for c in pPr if c.tag in (qn("a:tabLst"), qn("a:defRPr"), qn("a:extLst"))), None)

    def put(el):
        if anchor is not None:
            anchor.addprevious(el)
        else:
            pPr.append(el)
        return el
    if kind == "none":
        put(etree.Element(qn("a:buNone")))
        return
    clr = put(etree.Element(qn("a:buClr")))
    etree.SubElement(clr, qn("a:srgbClr")).set("val", color)
    if kind == "num":
        put(etree.Element(qn("a:buAutoNum"))).set("type", "arabicPeriod")
    else:
        put(etree.Element(qn("a:buFont"))).set("typeface", "Arial")
        put(etree.Element(qn("a:buChar"))).set("char", "•" if level == 0 else "–")


def estimate_height_pt(items, size, width_pt):
    """Rough text height: average glyph ≈ 0.5 em, line height 1.2, paragraph gap 0.3 em."""
    h = 0.0
    for level, text, _ in items:
        s = size * (0.9 ** level)
        usable = max(width_pt - level * 24 - 18, 50)
        chars_per_line = max(usable / (s * 0.5), 8)
        lines = max(1, -(-len(text) // int(chars_per_line)))
        h += lines * s * 1.2 + s * 0.35
    return h


class Builder:
    def __init__(self, a, meta):
        self.a = a
        self.meta = meta
        self.template = a.template
        self.prs = Presentation(a.template) if a.template else Presentation()
        if a.template and not a.keep_template_slides:
            self.remove_all_slides()
        if not a.template:
            if a.ratio == "16:9":
                self.prs.slide_width, self.prs.slide_height = Inches(13.333), Inches(7.5)
            else:
                self.prs.slide_width, self.prs.slide_height = Inches(10), Inches(7.5)
        self.W, self.H = self.prs.slide_width, self.prs.slide_height
        self.accent = (a.accent or THEMES.get(a.theme, THEMES["navy"])).lstrip("#")
        self.font = a.font
        self.dark = "222222"
        self.grey = "7F7F7F"
        self.n = 0

    # -- template helpers
    def remove_all_slides(self):
        sldIdLst = self.prs.slides._sldIdLst
        for sldId in list(sldIdLst):
            self.prs.part.drop_rel(sldId.rId)
            sldIdLst.remove(sldId)

    def layout(self, want):
        """Pick a layout: in a template by placeholder pattern/name; otherwise Blank."""
        layouts = list(self.prs.slide_layouts)
        if not self.template:
            # real title placeholders (outline view, screen readers, accessibility checker),
            # repositioned and styled per slide
            name = "Title Slide" if want == "title" else "Title Only"
            return next((l for l in layouts if l.name == name), layouts[0])

        def types(l):
            return [ph.placeholder_format.type for ph in l.placeholders]
        names = {l.name.lower(): l for l in layouts}
        if want == "title":
            for l in layouts:
                if PP_PLACEHOLDER.CENTER_TITLE in types(l):
                    return l
        if want == "section":
            for key in ("section header", "section", "divider"):
                for n, l in names.items():
                    if key in n:
                        return l
        if want == "content":
            for key in ("title and content", "content"):
                for n, l in names.items():
                    if key in n:
                        return l
        if want == "title_only":
            for key in ("title only",):
                for n, l in names.items():
                    if key in n:
                        return l
        return layouts[min(1, len(layouts) - 1)]

    def content_box(self, slide=None):
        """(left, top, width, height) of the area below the title."""
        if self.template:
            lay = self.layout("content")
            for ph in lay.placeholders:
                if ph.placeholder_format.type in (PP_PLACEHOLDER.OBJECT, PP_PLACEHOLDER.BODY):
                    return ph.left, ph.top, ph.width, ph.height
        m = Inches(0.6)
        top = Inches(1.45)
        return m, top, self.W - 2 * m, self.H - top - Inches(0.7)

    # -- slide kinds
    def new_slide(self, kind):
        self.n += 1
        lay = self.layout({"title": "title", "section": "section"}.get(kind, "title_only" if kind == "visual" else "content"))
        s = self.prs.slides.add_slide(lay)
        return s

    def style_placeholder(self, ph, left, top, width, height, anchor=MSO_ANCHOR.BOTTOM):
        ph.left, ph.top, ph.width, ph.height = left, top, width, height
        tf = ph.text_frame
        tf.text = ""
        tf.word_wrap = True
        tf.auto_size = MSO_AUTO_SIZE.NONE
        tf.vertical_anchor = anchor
        tf.margin_left = tf.margin_right = 0
        return tf

    def set_title(self, slide, text, size=30):
        if self.template and slide.shapes.title is not None:
            slide.shapes.title.text = text
            return slide.shapes.title
        m = Inches(0.6)
        if slide.shapes.title is not None:
            tb = slide.shapes.title
            tf = self.style_placeholder(tb, m, Inches(0.35), self.W - 2 * m, Inches(0.9))
        else:
            tb = slide.shapes.add_textbox(m, Inches(0.35), self.W - 2 * m, Inches(0.9))
            tf = tb.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.BOTTOM
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT
        add_rich(p, text, size if len(text) < 60 else size - 6, self.accent, self.font, bold=True)
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, m, Inches(1.27), Inches(1.2), Pt(3))
        line.fill.solid()
        line.fill.fore_color.rgb = rgb(self.accent)
        line.line.fill.background()
        line.name = "Title rule"
        return tb

    def footer(self, slide):
        if self.template or self.a.no_numbers:
            return
        foot = self.meta.get("footer") or self.meta.get("title", "")
        tb = slide.shapes.add_textbox(Inches(0.6), self.H - Inches(0.5), self.W - Inches(2.2), Inches(0.35))
        tb.name = "Footer"
        tb.text_frame.word_wrap = True  # without wrapping, LibreOffice centres the text in the box
        p = tb.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT
        r = p.add_run()
        r.text = foot
        style_run(r, 10, False, self.grey, self.font)
        tb2 = slide.shapes.add_textbox(self.W - Inches(1.4), self.H - Inches(0.5), Inches(0.8), Inches(0.35))
        tb2.name = "Slide Number"
        tb2.text_frame.word_wrap = True
        p2 = tb2.text_frame.paragraphs[0]
        p2.alignment = PP_ALIGN.RIGHT
        r2 = p2.add_run()
        r2.text = str(self.n)
        style_run(r2, 10, False, self.grey, self.font)

    def title_slide(self):
        s = self.new_slide("title")
        title = self.meta.get("title", "Untitled")
        sub = " — ".join(x for x in (self.meta.get("subtitle"),) if x)
        byline = "  |  ".join(x for x in (self.meta.get("author"), self.meta.get("date")) if x)
        if self.template:
            if s.shapes.title is not None:
                s.shapes.title.text = title
            for ph in s.placeholders:
                if ph.placeholder_format.type == PP_PLACEHOLDER.SUBTITLE:
                    ph.text = "\n".join(x for x in (sub, byline) if x)
            return s
        bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, self.W, self.H)
        bg.fill.solid()
        bg.fill.fore_color.rgb = rgb(self.accent)
        bg.line.fill.background()
        bg.name = "Background"
        s.shapes._spTree.remove(bg._element)
        s.shapes._spTree.insert(2, bg._element)  # behind the placeholders
        tph = s.shapes.title
        tf = self.style_placeholder(tph, Inches(0.9), Inches(1.9), self.W - Inches(1.8), Inches(1.9))
        tf.paragraphs[0].alignment = PP_ALIGN.LEFT
        add_rich(tf.paragraphs[0], title, 40 if len(title) < 50 else 32, "FFFFFF", self.font, bold=True)
        sph = next((ph for ph in s.placeholders if ph.placeholder_format.type == PP_PLACEHOLDER.SUBTITLE), None)
        if sph is not None:
            if sub:
                stf = self.style_placeholder(sph, Inches(0.9), Inches(3.9), self.W - Inches(1.8), Inches(1.0), MSO_ANCHOR.TOP)
                stf.paragraphs[0].alignment = PP_ALIGN.LEFT
                add_rich(stf.paragraphs[0], sub, 22, "E6E6E6", self.font)
            else:
                sph._element.getparent().remove(sph._element)
        if byline:
            tb2 = s.shapes.add_textbox(Inches(0.9), self.H - Inches(1.6), self.W - Inches(1.8), Inches(0.6))
            tb2.text_frame.word_wrap = True
            tb2.text_frame.paragraphs[0].alignment = PP_ALIGN.LEFT
            add_rich(tb2.text_frame.paragraphs[0], byline, 16, "E6E6E6", self.font)
        return s

    def section_slide(self, spec):
        s = self.new_slide("section")
        if self.template:
            if s.shapes.title is not None:
                s.shapes.title.text = spec["title"]
            paras = [d for k, d in spec["blocks"] if k == "para"]
            for ph in list(s.placeholders):
                if ph.placeholder_format.type in (PP_PLACEHOLDER.BODY, PP_PLACEHOLDER.SUBTITLE, PP_PLACEHOLDER.OBJECT):
                    if paras:
                        ph.text = paras.pop(0)
                    else:
                        ph._element.getparent().remove(ph._element)  # no empty "Click to add text" boxes
            return s
        band = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.35), self.H)
        band.fill.solid()
        band.fill.fore_color.rgb = rgb(self.accent)
        band.line.fill.background()
        band.name = "Section band"
        tf = self.style_placeholder(s.shapes.title, Inches(1.0), Inches(2.4), self.W - Inches(2), Inches(1.4))
        tf.paragraphs[0].alignment = PP_ALIGN.LEFT
        add_rich(tf.paragraphs[0], spec["title"], 36, self.accent, self.font, bold=True)
        paras = [d for k, d in spec["blocks"] if k == "para"]
        if paras:
            tb = s.shapes.add_textbox(Inches(1.0), Inches(3.9), self.W - Inches(2), Inches(1.2))
            tb.name = "Section subtitle"
            tb.text_frame.word_wrap = True
            tb.text_frame.margin_left = 0
            for k, d in enumerate(paras):
                p = tb.text_frame.paragraphs[0] if k == 0 else tb.text_frame.add_paragraph()
                add_rich(p, d, 18, self.grey, self.font)
        return s

    def content_slide(self, spec):
        blocks = spec["blocks"]
        kinds = [k for k, _ in blocks]
        visual = any(k in ("image", "table", "chart", "left", "right", "quote") for k in kinds)
        s = self.new_slide("visual" if visual else "content")
        if not spec["title"] and kinds == ["quote"] and not self.template and s.shapes.title is not None:
            # statement slide: the statement itself is the slide title (accessible), big and centred
            text = blocks[0][1]
            tf = self.style_placeholder(s.shapes.title, Inches(1.2), Inches(1.5), self.W - Inches(2.4), self.H - Inches(3.2), MSO_ANCHOR.MIDDLE)
            tf.paragraphs[0].alignment = PP_ALIGN.CENTER
            add_rich(tf.paragraphs[0], text, 36 if len(text) < 90 else 28, self.accent, self.font, bold=True)
            if spec.get("notes"):
                s.notes_slide.notes_text_frame.text = spec["notes"]
            self.footer(s)
            return s
        if not spec["title"] and kinds == ["quote"] and self.template and s.shapes.title is not None:
            s.shapes.title.text = blocks[0][1]  # template: the statement becomes the (template-styled) title
            if spec.get("notes"):
                s.notes_slide.notes_text_frame.text = spec["notes"]
            return s
        if spec["title"]:
            self.set_title(s, spec["title"])
        elif s.shapes.title is not None:
            s.shapes.title._element.getparent().remove(s.shapes.title._element)
            WARNINGS.append(f"slide {self.n}: no title — slides without titles are hard to navigate")
        L, T, Wd, Ht = self.content_box(s)
        body_ph = None
        if self.template and not visual:
            body_ph = next((ph for ph in s.placeholders if ph.placeholder_format.type in (PP_PLACEHOLDER.OBJECT, PP_PLACEHOLDER.BODY)), None)
        if body_ph is not None:
            # text-only slide in a template: fill the layout's own body placeholder so the
            # template's fonts, sizes and bullet styles apply
            items = []
            for kind, data in blocks:
                items += data if kind == "bullets" else [(0, data, None)] if kind == "para" else []
            tf = body_ph.text_frame
            for k, (level, text, numbered) in enumerate(items):
                p = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
                p.level = min(level, 4)
                if numbered is None:
                    set_bullet(p, level, "none", self.grey)
                elif numbered:
                    set_bullet(p, level, "num", self.accent)
                add_rich(p, text, None, None, None)
            if estimate_height_pt(items, 24, body_ph.width / 12700) > body_ph.height / 12700:
                WARNINGS.append(f"slide {self.n} '{spec['title']}': text may overflow the template's body box — split the slide")
        elif "left" in kinds or "right" in kinds:
            gap = Inches(0.4)
            half = int((Wd - gap) / 2)
            for kind, data in blocks:
                if kind == "left":
                    self.place_blocks(s, data, L, T, half, Ht, spec)
                elif kind == "right":
                    self.place_blocks(s, data, L + half + gap, T, half, Ht, spec)
        else:
            self.place_blocks(s, blocks, L, T, Wd, Ht, spec)
        if self.template:
            # remove empty body placeholder when we placed our own content
            for ph in list(s.placeholders):
                if ph.placeholder_format.type in (PP_PLACEHOLDER.OBJECT, PP_PLACEHOLDER.BODY) and not ph.has_text_frame or \
                        (ph.placeholder_format.type in (PP_PLACEHOLDER.OBJECT, PP_PLACEHOLDER.BODY) and not ph.text_frame.text.strip()):
                    ph._element.getparent().remove(ph._element)
        if spec.get("notes"):
            s.notes_slide.notes_text_frame.text = spec["notes"]
        self.footer(s)
        return s

    def place_blocks(self, s, blocks, L, T, Wd, Ht, spec):
        text_items = []
        visuals = []
        for kind, data in blocks:
            if kind == "bullets":
                text_items += data
            elif kind == "para":
                text_items.append((0, data, None))
            elif kind in ("image", "table", "chart", "quote"):
                visuals.append((kind, data))
        top = T
        avail = Ht
        if text_items and visuals:
            # text above, visual below: give text what it needs (max 40 %)
            need = Emu(int(estimate_height_pt(text_items, 18, Wd / 12700) * 12700)) + Inches(0.1)
            th = min(need, int(Ht * 0.4))
            self.text_box(s, text_items, L, top, Wd, th, spec, base=18)
            top += th + Inches(0.1)
            avail = Ht - th - Inches(0.1)
        elif text_items:
            self.text_box(s, text_items, L, top, Wd, avail, spec, base=24 if self.W > Inches(11) else 22)
        if visuals:
            hv = int(avail / len(visuals))
            for kind, data in visuals:
                getattr(self, f"place_{kind}")(s, data, L, top, Wd, hv, spec)
                top += hv

    def text_box(self, s, items, L, T, Wd, Ht, spec, base=24):
        size = base
        width_pt = Wd / 12700
        while size > self.a.min_font and estimate_height_pt(items, size, width_pt) > Ht / 12700:
            size -= 1
        sparse = False
        if size == base:  # few short bullets: larger type, vertically centred, instead of a half-empty slide
            while size < base + 6 and estimate_height_pt(items, size + 1, width_pt) < 0.45 * Ht / 12700:
                size += 1
            sparse = estimate_height_pt(items, size, width_pt) < 0.45 * Ht / 12700
        if estimate_height_pt(items, size, width_pt) > Ht / 12700:
            WARNINGS.append(f"slide {self.n} '{spec['title']}': text likely overflows even at {size} pt — split the slide")
        elif size < base:
            WARNINGS.append(f"slide {self.n} '{spec['title']}': text shrunk to {size} pt to fit")
        tb = s.shapes.add_textbox(L, T, Wd, Ht)
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = 0
        if sparse:
            tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        first = True
        for level, text, numbered in items:
            p = tf.paragraphs[0] if first else tf.add_paragraph()
            p.alignment = PP_ALIGN.LEFT
            first = False
            sz = round(size * (0.9 ** level))
            p.space_after = Pt(sz * 0.35)
            kind = "none" if numbered is None else ("num" if numbered else "bullet")
            set_bullet(p, level, kind, self.accent if level == 0 else self.grey)
            add_rich(p, text, sz, self.dark, self.font)
        tb.name = "Body"
        return tb

    def place_image(self, s, data, L, T, Wd, Ht, spec):
        from PIL import Image as PILImage
        if not os.path.exists(data["path"]):
            WARNINGS.append(f"slide {self.n}: image not found: {data['path']}")
            return
        cap_h = Inches(0.4) if data.get("caption") else 0
        with PILImage.open(data["path"]) as im:
            iw, ih = im.size
            dpi = im.info.get("dpi", (96, 96))[0] or 96
        box_w, box_h = Wd, Ht - cap_h
        scale = min(box_w / iw, box_h / ih)
        w, h = int(iw * scale), int(ih * scale)
        x = L + int((box_w - w) / 2)
        pic = s.shapes.add_picture(data["path"], x, T, w, h)
        pic.name = data.get("caption") or os.path.basename(data["path"])
        # alt text (accessibility): stored as the descr attribute
        pic._element.nvPicPr.cNvPr.set("descr", data.get("alt") or data.get("caption") or os.path.basename(data["path"]))
        shown_in = w / 914400
        if iw / max(shown_in, 0.01) < 100:
            WARNINGS.append(f"slide {self.n}: image {os.path.basename(data['path'])} is only ~{iw / shown_in:.0f} px/inch at this size — may look blurry")
        if data.get("caption"):
            tb = s.shapes.add_textbox(L, T + h + Inches(0.05), Wd, cap_h)
            tb.name = "Caption"
            tb.text_frame.word_wrap = True
            p = tb.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER
            add_rich(p, data["caption"], 14, self.grey, self.font, bold=None)
            tb.text_frame.word_wrap = True

    def place_table(self, s, rows, L, T, Wd, Ht, spec):
        if not rows:
            return
        nr, nc = len(rows), max(len(r) for r in rows)
        size = 18 if nr <= 6 else 14 if nr <= 10 else 11
        row_h = Pt(size * 2.0)
        h = min(Ht, row_h * nr)
        lens = [max(len(str(r[j])) if j < len(r) else 0 for r in rows) + 3 for j in range(nc)]
        natural = int(sum(lens) * size * 0.62 * 12700)  # rough width the content needs
        tw = max(min(Wd, natural), int(Wd * 0.45))
        L = L + int((Wd - tw) / 2)  # centre narrower tables
        Wd = tw
        gt = s.shapes.add_table(nr, nc, L, T, Wd, h)
        tbl = gt.table
        for j in range(nc):
            tbl.columns[j].width = int(Wd * lens[j] / sum(lens))
        for i, r in enumerate(rows):
            for j in range(nc):
                cell = tbl.cell(i, j)
                cell.text = ""
                p = cell.text_frame.paragraphs[0]
                txt = str(r[j]) if j < len(r) else ""
                numeric = bool(re.fullmatch(r"[-+]?[\d.,]+%?", txt)) and i > 0
                p.alignment = PP_ALIGN.RIGHT if numeric else PP_ALIGN.LEFT
                add_rich(p, txt, size, "FFFFFF" if i == 0 else self.dark, self.font, bold=(i == 0) or None)
                cell.fill.solid()
                cell.fill.fore_color.rgb = rgb(self.accent) if i == 0 else (rgb("F2F2F2") if i % 2 == 0 else rgb("FFFFFF"))
                cell.margin_left = cell.margin_right = Pt(6)
        if row_h * nr > Ht:
            WARNINGS.append(f"slide {self.n} '{spec['title']}': table with {nr} rows may not fit — consider splitting")

    def place_chart(self, s, c, L, T, Wd, Ht, spec):
        kind = c.get("type", "column")
        if kind == "scatter":
            cd = XyChartData()
            for name, pts in c["series"].items():
                ser = cd.add_series(name)
                for x, y in pts:
                    ser.add_data_point(x, y)
            ct = XL_CHART_TYPE.XY_SCATTER_LINES if c.get("lines") else XL_CHART_TYPE.XY_SCATTER
        else:
            cd = CategoryChartData()
            cd.categories = c["categories"]
            for name, vals in c["series"].items():
                cd.add_series(name, vals)
            ct = {"bar": XL_CHART_TYPE.COLUMN_CLUSTERED, "column": XL_CHART_TYPE.COLUMN_CLUSTERED,
                  "barh": XL_CHART_TYPE.BAR_CLUSTERED, "line": XL_CHART_TYPE.LINE_MARKERS,
                  "pie": XL_CHART_TYPE.PIE, "stacked": XL_CHART_TYPE.COLUMN_STACKED}[kind]
        gf = s.shapes.add_chart(ct, L, T, Wd, Ht, cd)
        ch = gf.chart
        ch.font.size = Pt(14)
        ch.font.name = self.font
        multi = len(c["series"]) > 1 or kind == "pie"
        ch.has_legend = multi
        if multi:
            ch.legend.position = XL_LEGEND_POSITION.BOTTOM
            ch.legend.include_in_layout = False
        if c.get("title"):
            ch.has_title = True
            ch.chart_title.text_frame.text = c["title"]
        else:
            ch.has_title = False
        if kind != "pie":
            if c.get("x_title"):
                ch.category_axis.has_title = True
                ch.category_axis.axis_title.text_frame.text = c["x_title"]
            if c.get("y_title"):
                ch.value_axis.has_title = True
                ch.value_axis.axis_title.text_frame.text = c["y_title"]
            if c.get("number_format"):
                ch.value_axis.tick_labels.number_format = c["number_format"]
                ch.value_axis.tick_labels.number_format_is_linked = False
            ch.value_axis.has_major_gridlines = True
            ch.value_axis.major_gridlines.format.line.color.rgb = rgb("D9D9D9")
            if c.get("y_reverse"):
                from pptx.enum.chart import XL_AXIS_CROSSES
                from pptx.oxml.ns import qn
                scaling = ch.value_axis._element.find(qn("c:scaling"))
                orient = scaling.find(qn("c:orientation"))
                orient.set("val", "maxMin")
                ch.value_axis.crosses = XL_AXIS_CROSSES.MAXIMUM  # keeps the x axis at the bottom
            if c.get("data_labels") and kind != "scatter":
                plot = ch.plots[0]
                plot.has_data_labels = True
                if c.get("number_format"):
                    plot.data_labels.number_format = c["number_format"]
                    plot.data_labels.number_format_is_linked = False
        palette = [self.accent, "C55A11", "70AD47", "7F7F7F", "FFC000", "5B9BD5"]
        custom = {k: v.lstrip("#") for k, v in (c.get("colors") or {}).items()}
        if ch.has_legend:
            ch.legend.font.size = Pt(14)
        if kind != "pie":
            for ax in (ch.category_axis, ch.value_axis):
                ax.tick_labels.font.size = Pt(14)
            if c.get("y_min") is not None:
                ch.value_axis.minimum_scale = c["y_min"]
            if c.get("y_max") is not None:
                ch.value_axis.maximum_scale = c["y_max"]
        if kind not in ("pie",):
            for k, ser in enumerate(ch.series):
                col = rgb(custom.get(ser.name, palette[k % len(palette)]))
                if kind in ("line", "scatter"):
                    ser.format.line.color.rgb = col
                    try:
                        ser.marker.format.fill.solid()
                        ser.marker.format.fill.fore_color.rgb = col
                    except Exception:
                        pass
                else:
                    ser.format.fill.solid()
                    ser.format.fill.fore_color.rgb = col

    def place_quote(self, s, text, L, T, Wd, Ht, spec):
        tb = s.shapes.add_textbox(L + Inches(0.5), T, Wd - Inches(1.0), Ht)
        tb.name = "Statement"
        tf = tb.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        add_rich(p, text, 32 if len(text) < 90 else 26, self.accent, self.font, bold=True)

    def build(self, slides):
        if self.meta.get("title"):
            self.title_slide()
        for spec in slides:
            if spec["type"] == "section":
                self.section_slide(spec)
            else:
                self.content_slide(spec)
        self.prs.core_properties.title = self.meta.get("title", "")
        if self.meta.get("author"):
            self.prs.core_properties.author = self.meta["author"]
        return self.prs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("outline", help=".md or .json")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--template", help=".pptx/.potx whose layouts, fonts and colours to use")
    ap.add_argument("--keep-template-slides", action="store_true")
    ap.add_argument("--theme", default="navy", choices=sorted(THEMES))
    ap.add_argument("--accent", help="hex colour overriding the theme, e.g. 1F3864")
    ap.add_argument("--font", default="Calibri")
    ap.add_argument("--ratio", default="16:9", choices=["16:9", "4:3"])
    ap.add_argument("--min-font", type=int, default=14, help="never shrink body text below this")
    ap.add_argument("--no-numbers", action="store_true", help="no footer/slide numbers")
    a = ap.parse_args()
    base = os.path.dirname(os.path.abspath(a.outline))
    with open(a.outline, encoding="utf-8") as fh:
        raw = fh.read()
    meta, slides = (from_json(json.loads(raw), base) if a.outline.lower().endswith(".json") else parse_markdown(raw, base))
    prs = Builder(a, meta).build(slides)
    prs.save(a.output)
    print(f"Wrote {a.output}: {len(prs.slides)} slides", file=sys.stderr)
    for w in WARNINGS:
        print("  ! " + w, file=sys.stderr)
    print("Check: python pptx_render.py " + a.output + " --sheet   (contact sheet of all slides)", file=sys.stderr)


if __name__ == "__main__":
    main()
````

### `scripts/pptx_check.py`

<!-- bundle-file: scripts/pptx_check.py sha256=388a60117347da6ad6f7b3cc4338cbd9bdbfe86927a2e3b05da3bd10c35c93b8 -->
````python
#!/usr/bin/env python3
"""Quality check a deck before it is shown or sent.

Flags, per slide:
  overflow     text likely too long for its box (estimate from font size & box size)
  small-font   text below --min-font pt (default 14; 18+ recommended for body text in talks)
  dense        more than --max-words words (default 40, tables excluded) or --max-bullets (6) bullets
  off-slide    shapes partly outside the slide
  overlap      text boxes overlapping other text/pictures/tables
  empty        empty placeholders ("Click to add text" shows in edit view, may print)
  no-title     slide without a real title placeholder (outline view, screen readers and
               PowerPoint's accessibility checker use it; a text box that looks like a title is not enough)
  chart-axes   chart without axis titles
  duplicate    the same picture on several slides (often a placeholder figure never replaced)
  alt-text     pictures without alternative text
  low-res      pictures shown at < 120 px per inch
  leftover     {{placeholders}}, "Lorem ipsum", "TODO", "TBC", "XX" left in text
  fonts        more than 3 font families used

Usage:
    python pptx_check.py deck.pptx [--json] [--min-font 14] [--max-words 40] [--max-bullets 6]
Defaults follow references/design-principles.md (talk slides). For reading decks / handouts
use e.g. --max-words 120 --max-bullets 10.
"""
import argparse
import io
import json
import os
import re
import sys
from collections import Counter

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pptx_common import iter_shapes, slide_title  # noqa: E402,F401

from pptx import Presentation  # noqa: E402
from pptx.enum.shapes import MSO_SHAPE_TYPE, PP_PLACEHOLDER  # noqa: E402

LEFTOVER = re.compile(r"\{\{[^}]+\}\}|lorem ipsum|\bTODO\b|\bTBC\b|\bTBD\b|\bXX+\b|click to (add|edit)", re.I)


def font_size_pt(run, para, shape):
    for src in (run.font.size, getattr(para.font, "size", None)):
        if src:
            return src.pt
    return 18.0  # typical inherited body size when not set explicitly


def text_height_estimate(tf, width_pt, shape):
    h = 0.0
    for p in tf.paragraphs:
        text = "".join(r.text for r in p.runs)
        size = max([font_size_pt(r, p, shape) for r in p.runs] or [18.0])
        usable = max(width_pt - 14 - p.level * 20, 30)
        cpl = max(usable / (size * 0.5), 6)
        lines = max(1, -(-len(text) // int(cpl))) + text.count("\n")
        h += lines * size * 1.2 + size * 0.3
    return h


def boxes_overlap(a, b):
    ax0, ay0, ax1, ay1 = a.left, a.top, a.left + a.width, a.top + a.height
    bx0, by0, bx1, by1 = b.left, b.top, b.left + b.width, b.top + b.height
    ix = min(ax1, bx1) - max(ax0, bx0)
    iy = min(ay1, by1) - max(ay0, by0)
    if ix <= 0 or iy <= 0:
        return 0
    return ix * iy / max(1, min(a.width * a.height, b.width * b.height))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--min-font", type=float, default=14)
    ap.add_argument("--max-words", type=int, default=40)
    ap.add_argument("--max-bullets", type=int, default=6)
    a = ap.parse_args()
    prs = Presentation(a.deck)
    W, H = prs.slide_width, prs.slide_height
    findings = []
    families = Counter()
    pics = {}

    def add(i, check, msg):
        findings.append({"slide": i, "check": check, "note": msg})

    for i, s in enumerate(prs.slides, start=1):
        shapes = [sh for sh in iter_shapes(s.shapes) if sh.width is not None and sh.left is not None]
        words, bullets = 0, 0
        tph = s.shapes.title
        if tph is None:
            add(i, "no-title", "no title placeholder" + (f" (visible heading '{slide_title(s)[:40]}' is a plain text box)" if slide_title(s) else ""))
        elif not tph.text_frame.text.strip():
            add(i, "no-title", "title placeholder is empty")
        for sh in shapes:
            if sh.left < -12700 or sh.top < -12700 or sh.left + sh.width > W + 12700 or sh.top + sh.height > H + 12700:
                add(i, "off-slide", f"'{sh.name}' extends beyond the slide edge")
            if sh.is_placeholder and sh.has_text_frame and not sh.text_frame.text.strip() \
                    and sh.placeholder_format.type not in (PP_PLACEHOLDER.DATE, PP_PLACEHOLDER.FOOTER, PP_PLACEHOLDER.SLIDE_NUMBER):
                add(i, "empty", f"empty placeholder '{sh.name}' — delete it or fill it")
            if sh.has_text_frame and sh.text_frame.text.strip():
                tf = sh.text_frame
                is_footer = sh.top > H * 0.88 and sh.height < H * 0.08
                if not is_footer:
                    words += len(tf.text.split())
                    if sh.name not in ("Title",) and not (sh.is_placeholder and sh.placeholder_format.type in (PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE)):
                        bullets += sum(1 for p in tf.paragraphs if "".join(r.text for r in p.runs).strip())
                need = text_height_estimate(tf, sh.width / 12700, sh)
                if need > sh.height / 12700 * 1.1 and not is_footer:
                    add(i, "overflow", f"'{sh.name}': text needs ≈{need:.0f} pt, box is {sh.height / 12700:.0f} pt high")
                for p in tf.paragraphs:
                    for r in p.runs:
                        if r.font.name:
                            families[r.font.name] += 1
                        if r.text.strip() and r.font.size and r.font.size.pt < a.min_font and not is_footer:
                            add(i, "small-font", f"'{r.text.strip()[:30]}' at {r.font.size.pt:g} pt")
                            break
                m = LEFTOVER.search(tf.text)
                if m:
                    add(i, "leftover", f"'{m.group(0)}' in '{sh.name}'")
            if getattr(sh, "has_chart", False) and sh.has_chart:
                ch = sh.chart
                try:
                    if ch.chart_type is not None and "PIE" not in str(ch.chart_type) and "DOUGHNUT" not in str(ch.chart_type):
                        missing = [n for n, ax in (("x", ch.category_axis), ("y", ch.value_axis)) if not ax.has_title]
                        if missing:
                            add(i, "chart-axes", f"chart '{sh.name}' has no {' or '.join(missing)} axis title (give units)")
                except Exception:
                    pass
            if sh.shape_type == MSO_SHAPE_TYPE.PICTURE:
                try:
                    import hashlib
                    pics.setdefault(hashlib.md5(sh.image.blob).hexdigest(), []).append(i)
                except Exception:
                    pass
            if getattr(sh, "has_table", False) and sh.has_table:
                if len(sh.table.rows) > 8:
                    add(i, "dense", f"table with {len(sh.table.rows)} rows — keep ≤ 8 on a slide, move the rest to a handout")
                for row in sh.table.rows:
                    for cell in row.cells:
                        m = LEFTOVER.search(cell.text)
                        if m:
                            add(i, "leftover", f"'{m.group(0)}' in a table cell")
            if sh.shape_type == MSO_SHAPE_TYPE.PICTURE:
                descr = sh._element.nvPicPr.cNvPr.get("descr")
                if not descr:
                    add(i, "alt-text", f"picture '{sh.name}' has no alt text")
                try:
                    from PIL import Image
                    with Image.open(io.BytesIO(sh.image.blob)) as im:
                        px = im.size[0]
                    ppi = px / (sh.width / 914400)
                    if ppi < 120:
                        add(i, "low-res", f"picture '{sh.name}' shown at ≈{ppi:.0f} px/inch (blurry when projected/printed)")
                except Exception:
                    pass
        chrome = lambda sh: sh.name in ("Footer", "Slide Number") or (sh.is_placeholder and sh.placeholder_format.type in (PP_PLACEHOLDER.FOOTER, PP_PLACEHOLDER.SLIDE_NUMBER, PP_PLACEHOLDER.DATE))  # noqa: E731
        texty = [sh for sh in shapes if sh.has_text_frame and sh.text_frame.text.strip() and not chrome(sh)]
        solid = [sh for sh in shapes if sh.shape_type == MSO_SHAPE_TYPE.PICTURE or getattr(sh, "has_table", False) and sh.has_table
                 or getattr(sh, "has_chart", False) and sh.has_chart or sh.has_text_frame and sh.text_frame.text.strip()]
        for t in texty:
            for o in solid:
                if o is t or o.shape_id == t.shape_id:
                    continue
                if boxes_overlap(t, o) > 0.15:
                    add(i, "overlap", f"'{t.name}' overlaps '{o.name}'")
        if words > a.max_words:
            add(i, "dense", f"{words} words (aim for ≤ {a.max_words}); split the slide or move detail to notes")
        if bullets > a.max_bullets:
            add(i, "dense", f"{bullets} bullet lines (aim for ≤ {a.max_bullets})")
    for digest, where in pics.items():
        if len(set(where)) > 1:
            findings.append({"slide": where[0], "check": "duplicate",
                             "note": f"same picture on slides {sorted(set(where))} — intended, or a placeholder figure?"})
    if len(families) > 3:
        findings.append({"slide": 0, "check": "fonts", "note": f"{len(families)} font families: {dict(families)}"})
    # de-duplicate overlap pairs
    seen, uniq = set(), []
    for f in findings:
        key = (f["slide"], f["check"], frozenset(re.findall(r"'([^']+)'", f["note"])) if f["check"] == "overlap" else f["note"])
        if key not in seen:
            seen.add(key)
            uniq.append(f)
    findings = uniq
    summary = Counter(f["check"] for f in findings)
    if a.json:
        print(json.dumps({"summary": summary, "findings": findings}, indent=2, ensure_ascii=False))
        return
    print(f"Checked {len(prs.slides)} slides: " + (", ".join(f"{v} {k}" for k, v in summary.items()) or "no issues found"))
    for f in sorted(findings, key=lambda f: (f["slide"], f["check"])):
        print(f"  slide {f['slide']:>2}  {f['check']:<10} {f['note']}")
    print("Estimates are heuristic — confirm visually: python pptx_render.py DECK --sheet", file=sys.stderr)


if __name__ == "__main__":
    main()
````

### `scripts/pptx_inspect.py`

<!-- bundle-file: scripts/pptx_inspect.py sha256=a0b8e29a6c1e9ab5a674715eff9da4781b5e892f93a5e62cd6b91c42b1f9ca95 -->
````python
#!/usr/bin/env python3
"""Summarise a deck: size, layouts available, and per slide its layout, title,
shapes (text/picture/table/chart/group/media), word count, notes, and
{{placeholders}}. Use before editing or reusing a deck or template.

Usage:
    python pptx_inspect.py deck.pptx [--json] [--layouts]
--layouts lists every slide layout with its placeholders (for building from a template).
"""
import argparse
import json
import os
import sys
from collections import Counter

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pptx_common import PLACEHOLDER, iter_shapes, iter_text_frames, slide_title  # noqa: E402

from pptx import Presentation  # noqa: E402
from pptx.enum.shapes import MSO_SHAPE_TYPE  # noqa: E402


def kind(sh):
    if getattr(sh, "has_chart", False) and sh.has_chart:
        return "chart"
    if getattr(sh, "has_table", False) and sh.has_table:
        return "table"
    if sh.shape_type == MSO_SHAPE_TYPE.PICTURE or (sh.is_placeholder and hasattr(sh, "image")):
        return "picture"
    if sh.shape_type in (MSO_SHAPE_TYPE.MEDIA,):
        return "media"
    if sh.has_text_frame and sh.text_frame.text.strip():
        return "text"
    return "shape"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--layouts", action="store_true")
    a = ap.parse_args()
    prs = Presentation(a.deck)
    W, H = prs.slide_width, prs.slide_height
    info = {"file": a.deck, "slides": len(prs.slides), "size_in": [round(W / 914400, 2), round(H / 914400, 2)],
            "aspect": "16:9" if abs(W / H - 16 / 9) < 0.02 else "4:3" if abs(W / H - 4 / 3) < 0.02 else f"{W / H:.2f}:1"}
    info["layouts"] = [{"name": l.name, "placeholders": [f"{ph.placeholder_format.idx}:{ph.placeholder_format.type.name if ph.placeholder_format.type else '?'}" for ph in l.placeholders]}
                       for l in prs.slide_layouts]
    fonts = Counter()
    slides = []
    for i, s in enumerate(prs.slides, start=1):
        kinds = Counter(kind(sh) for sh in iter_shapes(s.shapes))
        words, phs = 0, Counter()
        for _, tf in iter_text_frames(s):
            words += len(tf.text.split())
            for m in PLACEHOLDER.finditer(tf.text):
                phs[m.group(1)] += 1
            for p in tf.paragraphs:
                for r in p.runs:
                    if r.font.name:
                        fonts[r.font.name] += 1
        empty_ph = [ph.name for ph in s.placeholders if ph.has_text_frame and not ph.text_frame.text.strip()]
        notes = s.notes_slide.notes_text_frame.text.strip() if s.has_notes_slide else ""
        slides.append({"slide": i, "layout": s.slide_layout.name, "title": slide_title(s), "shapes": dict(kinds),
                       "words": words, "empty_placeholders": empty_ph, "notes": notes[:200],
                       "placeholders": dict(phs), "hidden": s._element.get("show") == "0"})
    info["slides_detail"] = slides
    info["fonts_used"] = dict(fonts.most_common(8))
    if a.json:
        print(json.dumps(info, indent=2, ensure_ascii=False))
        return
    print(f"File: {a.deck}\n{info['slides']} slides, {info['size_in'][0]}×{info['size_in'][1]} in ({info['aspect']})")
    if info["fonts_used"]:
        print(f"Fonts set on runs: {info['fonts_used']} (others inherit the theme)")
    for sl in slides:
        shapes = ", ".join(f"{v} {k}" for k, v in sl["shapes"].items())
        flags = []
        if sl["empty_placeholders"]:
            flags.append(f"empty placeholders: {sl['empty_placeholders']}")
        if sl["placeholders"]:
            flags.append("{{" + "}}, {{".join(sl["placeholders"]) + "}}")
        if sl["hidden"]:
            flags.append("HIDDEN")
        print(f"\n{sl['slide']:>3}. [{sl['layout']}] {sl['title'] or '(no title)'}")
        print(f"     {shapes or 'empty'}; {sl['words']} words" + (f"; notes: {sl['notes'][:80]!r}" if sl["notes"] else ""))
        if flags:
            print("     " + "; ".join(flags))
    if a.layouts:
        print("\nLayouts:")
        for k, l in enumerate(info["layouts"]):
            print(f"  {k}: {l['name']}  [{', '.join(l['placeholders'])}]")


if __name__ == "__main__":
    main()
````

### `scripts/pptx_render.py`

<!-- bundle-file: scripts/pptx_render.py sha256=77cc1b5a7f939d67397ec860e77c4d7f2e3d544b1946069b6bbe1e8a3bc3f472 -->
````python
#!/usr/bin/env python3
"""Render a deck to PDF, per-slide PNGs, or a single contact sheet for review.

    python pptx_render.py deck.pptx --sheet [-o deck_sheet.png] [--cols 4]   # all slides on one image
    python pptx_render.py deck.pptx --png [--slides 2-5] [--dpi 110] [-o renders/]
    python pptx_render.py deck.pptx --pdf [-o deck.pdf]

Uses LibreOffice (close to PowerPoint; fonts may be substituted). Outputs go next
to the deck unless -o is given. Look at the result before delivering a deck.
"""
import argparse
import os
import shutil
import sys
import tempfile

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pptx_common import parse_slides, to_pdf  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--sheet", action="store_true", help="one contact-sheet PNG of all (or --slides) slides")
    g.add_argument("--png", action="store_true")
    g.add_argument("--pdf", action="store_true")
    ap.add_argument("-o", "--output", help="--sheet: PNG file; --pdf: PDF file; --png: output FOLDER")
    ap.add_argument("--slides")
    ap.add_argument("--dpi", type=int, default=110)
    ap.add_argument("--cols", type=int, default=4)
    a = ap.parse_args()
    src = os.path.abspath(a.deck)
    if not os.path.exists(src):
        sys.exit(f"Not found: {a.deck}")
    here, base = os.path.dirname(src), os.path.splitext(os.path.basename(src))[0]

    with tempfile.TemporaryDirectory() as tmp:
        pdf = to_pdf(src, tmp)
        if a.pdf:
            out = a.output or os.path.join(here, base + ".pdf")
            shutil.move(pdf, out)
            print(f"Wrote {out}", file=sys.stderr)
            return
        try:
            import pypdfium2 as pdfium
            from PIL import Image, ImageDraw
        except ImportError:
            sys.exit("pip install pypdfium2 pillow")
        doc = pdfium.PdfDocument(pdf)
        idx = parse_slides(a.slides, len(doc))
        if a.png:
            out_dir = a.output or os.path.join(here, "renders")
            os.makedirs(out_dir, exist_ok=True)
            for i in idx:
                fn = os.path.join(out_dir, f"{base}_s{i + 1:02d}.png")
                doc[i].render(scale=a.dpi / 72).to_pil().save(fn)
                print(fn)
        else:
            thumbs = [doc[i].render(scale=60 / 72).to_pil().convert("RGB") for i in idx]
            tw, th = thumbs[0].size
            cols = min(a.cols, len(thumbs))
            rows = -(-len(thumbs) // cols)
            pad, label = 12, 22
            sheet = Image.new("RGB", (cols * (tw + pad) + pad, rows * (th + pad + label) + pad), "white")
            d = ImageDraw.Draw(sheet)
            for k, (i, im) in enumerate(zip(idx, thumbs)):
                x = pad + (k % cols) * (tw + pad)
                y = pad + (k // cols) * (th + pad + label)
                sheet.paste(im, (x, y + label))
                d.rectangle([x - 1, y + label - 1, x + tw, y + label + th], outline=(180, 180, 180))
                d.text((x, y + 4), f"Slide {i + 1}", fill=(60, 60, 60))
            out = a.output or os.path.join(here, base + "_sheet.png")
            sheet.save(out)
            print(out)
        print(f"{len(doc)} slide(s) in the deck", file=sys.stderr)
        doc.close()


if __name__ == "__main__":
    main()
````

### `scripts/pptx_replace.py`

<!-- bundle-file: scripts/pptx_replace.py sha256=fcc01547679d9b890a77e7cc26e88eba1f84af809e1f96977b0f8fb5f95b6c2e -->
````python
#!/usr/bin/env python3
"""Find/replace text across a deck, or fill {{placeholders}} from JSON, keeping formatting.

    python pptx_replace.py deck.pptx -o new.pptx --find "Lot 12" --replace "Lot 14"
    python pptx_replace.py deck.pptx -o new.pptx --map renames.json           # {"old": "new", ...}
    python pptx_replace.py template.pptx -o filled.pptx --fill data.json       # {{client}}, {{date}} ...
    python pptx_replace.py deck.pptx --find "draft" --dry-run                   # list matches per slide
Options: --regex  --ignore-case  --notes (also speaker notes)  --strict (fill: fail on missing keys)
Covers text boxes, placeholders, grouped shapes and table cells. Text inside charts is not changed.
A "\n" in a replacement (or a fill value) starts a new paragraph — e.g. one bullet per line:
    --find "Lorem ipsum dolor" --replace $'Findings\nOptions\nRecommendation'
(each new paragraph copies the original paragraph's bullet/level and the first run's formatting).
"""
import argparse
import json
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pptx_common import PLACEHOLDER, iter_text_frames, replace_in_paragraph  # noqa: E402

from pptx import Presentation  # noqa: E402


def lookup(data, path):
    cur = data
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck")
    ap.add_argument("-o", "--output")
    ap.add_argument("--find")
    ap.add_argument("--replace", default="")
    ap.add_argument("--map")
    ap.add_argument("--fill")
    ap.add_argument("--regex", action="store_true")
    ap.add_argument("--ignore-case", action="store_true")
    ap.add_argument("--notes", action="store_true")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if not a.dry_run and not a.output:
        sys.exit("Give -o OUTPUT (or --dry-run)")
    if a.output and os.path.abspath(a.output) == os.path.abspath(a.deck):
        sys.exit("Refusing to overwrite the input; choose a different -o")
    prs = Presentation(a.deck)
    flags = re.I if a.ignore_case else 0

    jobs = []
    if a.map:
        with open(a.map, encoding="utf-8") as fh:
            jobs += [(re.compile(k if a.regex else re.escape(k), flags), v, k) for k, v in json.load(fh).items()]
    if a.find is not None:
        repl = a.replace if a.regex else a.replace.replace("\\", "\\\\")
        jobs.append((re.compile(a.find if a.regex else re.escape(a.find), flags), repl, a.find))
    data = None
    if a.fill:
        with open(a.fill, encoding="utf-8") as fh:
            data = json.load(fh)
    if not jobs and data is None:
        sys.exit("Give --find, --map or --fill")

    missing = set()
    totals = {}
    for i, slide in enumerate(prs.slides, start=1):
        for _, tf in iter_text_frames(slide, notes=a.notes):
            for p in tf.paragraphs:
                text = "".join(r.text for r in p.runs)
                for rx, repl, label in jobs:
                    if a.dry_run:
                        for m in rx.finditer(text):
                            print(f"  slide {i}: …{text[max(0, m.start() - 30):m.end() + 30]}…")
                            totals[label] = totals.get(label, 0) + 1
                    else:
                        totals[label] = totals.get(label, 0) + replace_in_paragraph(p, rx, repl)
                if data is not None and not a.dry_run:
                    def fill(m):
                        v = lookup(data, m.group(1))
                        if v is None:
                            missing.add(m.group(1))
                            return m.group(0)
                        return str(v)
                    totals["{{…}}"] = totals.get("{{…}}", 0) + replace_in_paragraph(p, PLACEHOLDER, fill)
    labels = [lab for _, _, lab in jobs] + (["{{…}}"] if data is not None else [])
    for label in labels:
        n = totals.get(label, 0)
        print(f"{label!r}: {n} {'match(es)' if a.dry_run else 'replacement(s)'}", file=sys.stderr)
    if missing:
        msg = f"No value for: {sorted(missing)}"
        if a.strict:
            sys.exit(msg)
        print("Warning: " + msg + " (left in place)", file=sys.stderr)
    if not a.dry_run:
        prs.save(a.output)
        print(f"Wrote {a.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
````

### `scripts/pptx_slides.py`

<!-- bundle-file: scripts/pptx_slides.py sha256=fc1a02057cfe9fdaf50fb8ff12587f0b83e72a53f570272ed4e87d81f45a4013 -->
````python
#!/usr/bin/env python3
"""Slide-level operations on a deck (input is never modified).

  delete    deck.pptx --slides 3,7-9 -o out.pptx
  keep      deck.pptx --slides 1-5,12 -o out.pptx          (delete everything else)
  reorder   deck.pptx --order 1,3,2,4- -o out.pptx         (every slide must appear once)
  duplicate deck.pptx --slides 4 -o out.pptx               (copy placed right after the original)
  hide      deck.pptx --slides 9-10 -o out.pptx            (hidden in slide show; --unhide to reverse)
  notes     deck.pptx --notes notes.json -o out.pptx       ({"3": "Speaker notes for slide 3", ...})
  merge     a.pptx b.pptx -o out.pptx                      (b's slides appended using a's layouts —
                                                          text, pictures, tables; charts not copied)
"""
import argparse
import copy
import json
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pptx_common import parse_slides  # noqa: E402

from pptx import Presentation  # noqa: E402
from pptx.opc.constants import RELATIONSHIP_TYPE as RT  # noqa: E402


def sld_ids(prs):
    return prs.slides._sldIdLst


def delete(prs, idxs):
    lst = sld_ids(prs)
    items = list(lst)
    for i in sorted(idxs, reverse=True):
        el = items[i]
        prs.part.drop_rel(el.rId)
        lst.remove(el)


def copy_slide(prs, src_slide, dest_prs=None, layout=None):
    """Copy shapes (and picture/media relationships) of src_slide into a new slide."""
    dest_prs = dest_prs or prs
    layout = layout or (src_slide.slide_layout if dest_prs is prs else dest_prs.slide_layouts[6 if len(dest_prs.slide_layouts) > 6 else -1])
    new = dest_prs.slides.add_slide(layout)
    for ph in list(new.placeholders):
        ph._element.getparent().remove(ph._element)
    skipped = 0
    for sh in src_slide.shapes:
        el = copy.deepcopy(sh._element)
        # re-link images/media
        for blip in el.xpath(".//a:blip"):
            rid = blip.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed")
            if rid and rid in src_slide.part.rels:
                part = src_slide.part.rels[rid].target_part
                blip.set("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed",
                         new.part.relate_to(part, RT.IMAGE))
        if el.xpath(".//c:chart") if hasattr(el, "xpath") else False:
            skipped += 1
            continue
        new.shapes._spTree.insert_element_before(el, "p:extLst")
    if src_slide.has_notes_slide and src_slide.notes_slide.notes_text_frame.text:
        new.notes_slide.notes_text_frame.text = src_slide.notes_slide.notes_text_frame.text
    return new, skipped


def move(prs, from_idx, to_idx):
    lst = sld_ids(prs)
    el = list(lst)[from_idx]
    lst.remove(el)
    lst.insert(to_idx, el)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["delete", "keep", "reorder", "duplicate", "hide", "notes", "merge"])
    ap.add_argument("decks", nargs="+")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--slides")
    ap.add_argument("--order")
    ap.add_argument("--notes")
    ap.add_argument("--unhide", action="store_true")
    a = ap.parse_args()
    if any(os.path.abspath(a.output) == os.path.abspath(d) for d in a.decks):
        sys.exit("Refusing to overwrite an input; choose a different -o")
    prs = Presentation(a.decks[0])
    n = len(prs.slides)
    msg = ""
    if a.cmd == "delete":
        idx = parse_slides(a.slides, n)
        delete(prs, idx)
        msg = f"deleted {len(idx)} slide(s)"
    elif a.cmd == "keep":
        keep = set(parse_slides(a.slides, n))
        delete(prs, [i for i in range(n) if i not in keep])
        msg = f"kept {len(keep)} slide(s)"
    elif a.cmd == "reorder":
        order = []
        for part in a.order.split(","):
            order += parse_slides(part, n)
        if sorted(order) != list(range(n)):
            sys.exit(f"--order must list every slide 1-{n} exactly once (got {[o + 1 for o in order]})")
        lst = sld_ids(prs)
        items = list(lst)
        for el in items:
            lst.remove(el)
        for i in order:
            lst.append(items[i])
        msg = "reordered"
    elif a.cmd == "duplicate":
        idx = parse_slides(a.slides, n)
        for k, i in enumerate(sorted(idx, reverse=True)):
            _, skipped = copy_slide(prs, prs.slides[i])
            move(prs, len(prs.slides) - 1, i + 1)
            if skipped:
                print(f"  slide {i + 1}: {skipped} chart(s) not copied (re-create with pptx_build or in PowerPoint)", file=sys.stderr)
        msg = f"duplicated {len(idx)} slide(s)"
    elif a.cmd == "hide":
        for i in parse_slides(a.slides, n):
            el = prs.slides[i]._element
            if a.unhide:
                el.attrib.pop("show", None)
            else:
                el.set("show", "0")
        msg = ("unhid" if a.unhide else "hid") + " slide(s)"
    elif a.cmd == "notes":
        with open(a.notes, encoding="utf-8") as fh:
            notes = json.load(fh)
        for k, text in notes.items():
            i = int(k) - 1
            if not 0 <= i < n:
                sys.exit(f"Slide {k} does not exist (1-{n})")
            prs.slides[i].notes_slide.notes_text_frame.text = text
        msg = f"set notes on {len(notes)} slide(s)"
    elif a.cmd == "merge":
        total_skipped = 0
        for other in a.decks[1:]:
            src = Presentation(other)
            if (src.slide_width, src.slide_height) != (prs.slide_width, prs.slide_height):
                print(f"  ! {other} has a different slide size; shapes keep their absolute positions", file=sys.stderr)
            for s in src.slides:
                _, skipped = copy_slide(src, s, dest_prs=prs)
                total_skipped += skipped
        msg = f"merged {len(a.decks) - 1} deck(s)" + (f"; {total_skipped} chart(s) not copied" if total_skipped else "")
    prs.save(a.output)
    print(f"Wrote {a.output}: {msg}; now {len(prs.slides)} slides", file=sys.stderr)


if __name__ == "__main__":
    main()
````

### `scripts/pptx_text.py`

<!-- bundle-file: scripts/pptx_text.py sha256=92bfb1712622e3502e0191587a5ac6f3167568cd0f72653e32e661633ee2abd0 -->
````python
#!/usr/bin/env python3
"""Extract a deck's content as Markdown: slide titles, bullet hierarchy, tables,
chart data, picture alt text and speaker notes — for summarising, reviewing or
rebuilding a deck.

Usage:
    python pptx_text.py deck.pptx [-o deck.md] [--slides 2-6] [--no-notes]
"""
import argparse
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pptx_common import iter_shapes, parse_slides, slide_title  # noqa: E402

from pptx import Presentation  # noqa: E402
from pptx.enum.shapes import MSO_SHAPE_TYPE  # noqa: E402


def is_chrome(sh):
    """Footers, slide numbers and dates: repeated on every slide, not content."""
    from pptx.enum.shapes import PP_PLACEHOLDER
    if sh.is_placeholder and sh.placeholder_format.type in (PP_PLACEHOLDER.FOOTER, PP_PLACEHOLDER.SLIDE_NUMBER, PP_PLACEHOLDER.DATE):
        return True
    return sh.name in ("Footer", "Slide Number")


def shape_md(sh, title_text):
    out = []
    if getattr(sh, "has_table", False) and sh.has_table:
        rows = [[c.text.replace("\n", " ").replace("|", "\\|") for c in r.cells] for r in sh.table.rows]
        if rows:
            out.append("| " + " | ".join(rows[0]) + " |")
            out.append("|" + "---|" * len(rows[0]))
            out += ["| " + " | ".join(r) + " |" for r in rows[1:]]
        return out
    if getattr(sh, "has_chart", False) and sh.has_chart:
        ch = sh.chart
        out.append(f"*[Chart: {ch.chart_type}".split(" (")[0] + "]*")
        try:
            cats = list(ch.plots[0].categories)
            out.append("| Series | " + " | ".join(str(c) for c in cats) + " |")
            out.append("|" + "---|" * (len(cats) + 1))
            for s in ch.series:
                out.append(f"| {s.name} | " + " | ".join(f"{v:g}" if isinstance(v, (int, float)) else str(v) for v in s.values) + " |")
        except Exception:
            pass
        return out
    if sh.shape_type == MSO_SHAPE_TYPE.PICTURE:
        alt = sh._element.nvPicPr.cNvPr.get("descr") or sh.name
        out.append(f"*[Picture: {alt}]*")
        return out
    if sh.has_text_frame:
        counters = {}
        for p in sh.text_frame.paragraphs:
            t = "".join(r.text for r in p.runs).strip()
            if not t or t == title_text:
                continue
            pPr = p._p.pPr
            numbered = pPr is not None and pPr.find("{http://schemas.openxmlformats.org/drawingml/2006/main}buAutoNum") is not None
            plain = pPr is not None and pPr.find("{http://schemas.openxmlformats.org/drawingml/2006/main}buNone") is not None
            if numbered:
                counters[p.level] = counters.get(p.level, 0) + 1
                for deeper in [k for k in counters if k > p.level]:
                    del counters[deeper]
            marker = f"{counters[p.level]}. " if numbered else ("" if plain or len(sh.text_frame.paragraphs) == 1 else "- ")
            out.append("  " * p.level + marker + t)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck")
    ap.add_argument("-o", "--output")
    ap.add_argument("--slides")
    ap.add_argument("--no-notes", action="store_true")
    a = ap.parse_args()
    prs = Presentation(a.deck)
    lines = []
    for i in parse_slides(a.slides, len(prs.slides)):
        s = prs.slides[i]
        title = slide_title(s)
        lines.append(f"## Slide {i + 1}: {title}")
        lines.append("")
        shapes = sorted(iter_shapes(s.shapes), key=lambda x: (x.top or 0, x.left or 0))
        shapes = [x for x in shapes if not is_chrome(x)]
        for sh in shapes:
            md = shape_md(sh, title)
            if md:
                lines += md + [""]
        if not a.no_notes and s.has_notes_slide:
            notes = s.notes_slide.notes_text_frame.text.strip()
            if notes:
                lines += ["> **Notes:** " + notes.replace("\n", " "), ""]
    text = "\n".join(lines).rstrip() + "\n"
    if a.output:
        with open(a.output, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"Wrote {a.output}", file=sys.stderr)
    else:
        sys.stdout.write(text)


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
