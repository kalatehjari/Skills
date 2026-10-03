# Creating Word documents

## Contents
1. Choose a route
2. Markdown + pandoc (most reports)
3. python-docx essentials
4. Tables that look professional
5. Figures and captions with automatic numbers
6. Table of contents, page numbers and other fields
7. Sections: landscape pages, different first page, columns
8. A report skeleton

## 1. Choose a route

| Situation | Route |
|---|---|
| Mostly prose, headings, lists, simple tables, equations, footnotes, citations | **pandoc**: write Markdown, convert with a reference doc (section 2) |
| Exact layout: cover page, landscape appendix, shaded tables, fields, letterhead | **python-docx** (sections 3–7) |
| The organisation has its own Word template | Fill its `{{placeholders}}` (editing-and-review.md), or open it with python-docx and append to it, so its styles, headers and logos carry over |

The two routes combine well. Generate the body with pandoc, then finish it with `scripts/docx_finish.py`, which adds a cover page, a pre-filled table of contents, "Page X of Y" and A4. Use python-docx (sections 3–7) for anything more custom.

```bash
python scripts/docx_convert.py report.md --to docx --reference-doc house.docx -o body.docx
python scripts/docx_finish.py body.docx -o report.docx --a4 --cover --toc --page-numbers \
    --report-no GL-2026-014 --header-text "Slope Stability – Lot 12"
```

`docx_finish.py` takes the cover's title, author and date from the Markdown YAML front matter, or from `--title`, `--author` and `--date`. The cover has no header or footer but counts as page 1. TOC entries and their page numbers are filled in by rendering the document once with LibreOffice, so the contents are correct when the file opens. Word can still refresh them with right-click → Update Field.

## 2. Markdown + pandoc

```bash
python scripts/docx_make_reference.py -o house.docx --font "Calibri" --size 11 --heading-color 1F4E79 --a4
python scripts/docx_convert.py report.md --to docx --reference-doc house.docx -o report.docx
```

Pandoc converts these Markdown features into native Word features:

- `# Heading` becomes Heading 1, and so on.
- `$\sigma'_v = \gamma z$` becomes an editable Word equation.
- `[^1]` footnotes become real Word footnotes.
- Pipe tables, `![Caption](fig.png){width=12cm}`, and the title, author and date from YAML front matter all come across.
- `--citeproc --bibliography refs.bib --csl apa.csl` produces formatted citations. Add these by calling pandoc directly.

Word cross-references and live figure numbering aren't created this way. If you need them, add the SEQ fields afterwards (section 5).

The colour default `1F3864` is a dark navy blue, `1F4E79` is a medium blue, and `2F5496` is Word's default heading blue.

## 3. python-docx essentials

```python
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.section import WD_ORIENT
import datetime as dt

doc = Document()                      # or Document("house.docx") to inherit styles/headers
doc.core_properties.title = "Geotechnical Investigation Report"
doc.core_properties.author = "R. Kalatehjari"
doc.core_properties.created = dt.datetime.now()   # the blank template carries a 2013 date otherwise

sec = doc.sections[0]                 # A4 with 2.5 cm margins
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
    setattr(sec, side, Cm(2.5))

normal = doc.styles["Normal"]
normal.font.name, normal.font.size = "Calibri", Pt(11)
normal.paragraph_format.space_after = Pt(6)

doc.add_heading("1 Introduction", level=1)
p = doc.add_paragraph("Undrained shear strength ")
p.add_run("s").italic = True
r = p.add_run("u"); r.font.subscript = True
p.add_run(" was measured with a hand vane.")
doc.add_paragraph("First point", style="List Bullet")
doc.add_paragraph("Step one", style="List Number")
doc.add_page_break()
doc.save("out.docx")
```

Notes:

- Headings and lists rely on the template's built-in styles, which the default template and pandoc's reference doc both have. For automatic heading numbers ("1.2.3"), use a template whose Heading styles already carry multilevel numbering. Defining numbering from scratch in XML is fiddly (see ooxml-notes.md).
- To set a font for every script, so that Greek letters and symbols use the same face, also set `rFonts` for eastAsia and cs. `scripts/docx_make_reference.py` shows how in `set_font()`.
- `doc.add_paragraph(text)` keeps tabs (`\t`). A `\n` inside a run becomes a line break, not a new paragraph.

## 4. Tables that look professional

```python
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def shade(cell, hex_fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), hex_fill)
    tcPr.append(shd)

def repeat_header(row):
    trPr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader"); el.set(qn("w:val"), "true"); trPr.append(el)

data = [("BH1", 1.5, 12.3, 31.5), ("BH1", 3.0, 8.7, 33.0)]
cap = doc.add_paragraph("Table 1. Strength parameters", style="Caption")   # captions go ABOVE tables
t = doc.add_table(rows=1, cols=4)
t.style = "Table Grid"                      # or a style defined in your template
t.alignment = WD_TABLE_ALIGNMENT.CENTER
for cell, h in zip(t.rows[0].cells, ["Sample", "Depth (m)", "c′ (kPa)", "φ′ (°)"]):
    cell.text = h
    cell.paragraphs[0].runs[0].bold = True
    shade(cell, "D9E2F3")
repeat_header(t.rows[0])
for row in data:
    cells = t.add_row().cells
    for i, v in enumerate(row):
        cells[i].text = f"{v:.1f}" if isinstance(v, float) else str(v)
        if i:                                   # numbers right-aligned
            cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
widths = [Cm(3), Cm(3), Cm(3), Cm(3)]
for row in t.rows:                              # Word honours cell widths, not column widths
    for cell, w in zip(row.cells, widths):
        cell.width = w
```

- To merge cells, use `a = t.cell(0, 0); b = t.cell(0, 1); a.merge(b)`.
- To stop a row splitting across pages, add `w:cantSplit` to `trPr`, the same way `repeat_header` adds its element.
- Format numbers once, consistently (`f"{v:.1f}"`), and give the units in the header rather than in every cell.

## 5. Figures and captions with automatic numbers

Word numbers captions with a `SEQ` field. Insert the field and Word renumbers when the document is updated. Press F9, or let Word do it when printing. `add_field()` lives in `scripts/_docx_common.py`:

```python
import sys; sys.path.insert(0, "scripts")            # path to this skill's scripts folder
from _docx_common import add_field, set_setting      # add_field(paragraph, instr, placeholder)

doc.add_picture("stress_path.png", width=Cm(14))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
cap = doc.add_paragraph("Figure ", style="Caption")      # captions go BELOW figures
add_field(cap, r"SEQ Figure \* ARABIC", "1")
cap.add_run(". Effective stress paths for BH1 samples.")
```

Use the right placeholder number when you generate the document, so it reads correctly even before the fields update. To make Word update fields when the document opens, use `set_setting(doc, "updateFields", "true")`, which puts the element in its required schema position. Word then asks the reader "This document contains fields that may refer to other files…". It's usually nicer to pre-fill the values, as `docx_finish.py` does for the TOC.

## 6. Table of contents, page numbers and other fields

```python
toc = doc.add_paragraph()
add_field(toc, r'TOC \o "1-3" \h \z \u', "Right-click → Update field to build the table of contents.")

footer_p = doc.sections[0].footer.paragraphs[0]
footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
footer_p.add_run("Page ")
add_field(footer_p, "PAGE", "1")
footer_p.add_run(" of ")
add_field(footer_p, "NUMPAGES", "1")
```

- A bare TOC field like this shows only its placeholder text until Word updates it, and LibreOffice conversion doesn't fill it in either. Use `scripts/docx_finish.py --toc` instead to get a TOC whose entries and page numbers are filled in already.
- Don't style the "Contents" title as Heading 1, or it will list itself. `docx_finish.py` uses the TOC Heading style.
- For a date that updates itself, use `add_field(p, r'DATE \@ "d MMMM yyyy"', "…")`. Usually a fixed date is better in a report.

## 7. Sections: landscape pages, different first page, columns

```python
from docx.enum.section import WD_SECTION
first = doc.sections[0]
first.different_first_page_header_footer = True       # no header on the cover page — set this BEFORE adding sections
W, H = first.page_width, first.page_height            # keep sizes as values: Section objects for the
                                                      # last section move along when you add a section
new = doc.add_section(WD_SECTION.NEW_PAGE)            # e.g. for a wide appendix table
new.orientation = WD_ORIENT.LANDSCAPE
new.page_width, new.page_height = H, W                # swap — orientation alone doesn't
# ... add the wide content ...
back = doc.add_section(WD_SECTION.NEW_PAGE)
back.orientation = WD_ORIENT.PORTRAIT
back.page_width, back.page_height = W, H

cols = new._sectPr.find(qn("w:cols"))                 # templates usually have one already — edit it,
if cols is None:                                       # never append a second (schema order matters)
    cols = OxmlElement("w:cols")
    later = new._sectPr.find(qn("w:docGrid"))
    (later.addprevious if later is not None else new._sectPr.append)(cols)
cols.set(qn("w:num"), "2"); cols.set(qn("w:space"), "708")   # two text columns in that section
```

A new section inherits the previous section's header and footer (`is_linked_to_previous = True`). To give it its own header, set `new.header.is_linked_to_previous = False` and then write to it.

**Pitfall:** `doc.add_section()` turns the current last section into an earlier one, and the new section takes over the document's final section properties. A `Section` object you saved earlier for the last section then refers to the new section. Read `doc.sections[i]` again after adding sections, and keep page sizes as plain values.

## 8. A report skeleton

A good default for technical reports:

1. **Cover page:** title, client or project, report number, date and author. Use a different first page with no header.
2. **Document control table:** revision, date, author, reviewer.
3. **Table of contents** (TOC field), then a page break.
4. **Numbered sections** with Heading 1–3, an executive summary first and the conclusions last.
5. **Tables** with captions above and **figures** with captions below, both numbered by SEQ fields.
6. **References** in one consistent style, using pandoc citeproc or written by hand.
7. **Appendices** in their own sections. Use landscape where tables are wide.
8. **Footer** with "Page X of Y", and a header with the short title.

Afterwards, run `docx_inspect.py` to check the outline and sections, then `docx_convert.py --to png --pages 1-3` to look at the cover, the TOC and the first page of content.
