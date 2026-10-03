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
