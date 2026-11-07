---
name: docx-workbench
description: Create, read, edit, review and convert Word documents (.docx) with tested Python scripts. Use this whenever a task involves a Word file — writing a report, letter, thesis chapter or manual; filling a template with {{placeholders}} or mail-merging from data; find-and-replace that keeps formatting; suggesting edits as tracked changes or adding comments; accepting/rejecting tracked changes or summarising reviewer comments; comparing two versions; converting between .docx, PDF, Markdown, .doc and .odt. Trigger even when the user just says "Word doc", "track changes", "redline", "my manuscript" or attaches a .docx.
license: MIT (see LICENSE)
---

**Single-file build.** This is the `docx-workbench` skill packed into one file on 2026-11-05. The instructions below are its SKILL.md, unchanged. Its supporting files (4 reference files, 10 scripts and the licence) are embedded verbatim under "Bundled files" at the end, each with a SHA-256 checksum. You can read a reference there directly. Before you run a script or use an asset, unpack the files once:

```bash
python3 - "${CLAUDE_SKILL_DIR}/SKILL.md" "${TMPDIR:-/tmp}/docx-workbench" <<'PY'
import hashlib, os, re, sys
src, out = sys.argv[1], sys.argv[2]
if not os.path.isfile(src):
    src = "/mnt/skills/user/docx-workbench/SKILL.md"
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

The first argument is the path of this file. Claude Code and Cowork fill it in for you; elsewhere, use the path you read this file from (on claude.ai the command also tries `/mnt/skills/user/docx-workbench/SKILL.md`). The command prints the folder it wrote to. From then on, use that folder wherever the instructions mean this skill's folder: paths such as `scripts/...`, `references/...`, `assets/...` and `<this-skill>/...` all point into it.

---


# DOCX Workbench

A toolkit for Word documents. The scripts cover the common jobs, and each reference file goes deeper on one area. Every script is a standalone Python CLI, so run it with `--help` to see the options.

Paths below are relative to this skill's folder, the directory that holds this SKILL.md. Call scripts by their full path. Outputs go next to the input file unless you pass `-o`. Always give `-o` with a path in the user's folder, and never write into the skill folder.

## Setup

```bash
pip install python-docx lxml pypdfium2      # python-docx ≥ 1.2 is needed for comments
# optional system tools: pandoc (Markdown/equations/footnotes), LibreOffice (PDF/PNG/.doc conversion,
# TOC page numbers); install libreoffice-math too if you want equations to appear in renders
```

## Start by inspecting

```bash
python scripts/docx_inspect.py report.docx           # outline, styles, tables, sections, revisions, comments, placeholders
```

The output tells you:

- whether the document uses real heading styles. If it doesn't, the headings are manual bold text, and a table of contents won't pick them up.
- whether it already has tracked changes or comments. Don't silently discard someone else's review.
- what page setup it uses.
- which `{{placeholders}}` it expects.

## Pick the path

| Goal | Use | Details |
|---|---|---|
| Read the content, or turn it into Markdown | `scripts/docx_convert.py in.docx --to md` | references/reading-and-converting.md |
| Write a new document from content you've drafted | Markdown → `docx_convert.py --to docx --reference-doc house.docx` | references/creating-documents.md |
| Build a document that needs precise layout (cover page, landscape tables, fields) | python-docx recipes | references/creating-documents.md |
| A consistent house style for generated documents | `scripts/docx_make_reference.py` | references/creating-documents.md |
| Cover page, table of contents with page numbers, "Page X of Y", A4 | `scripts/docx_finish.py` | references/creating-documents.md |
| Fill a template, one per record (mail merge) | `scripts/docx_fill_template.py` | references/editing-and-review.md |
| Change wording but keep formatting | `scripts/docx_replace.py` | references/editing-and-review.md |
| Suggest edits the author can accept or reject, and add comments | `scripts/docx_redline.py` | references/editing-and-review.md |
| List, accept or reject tracked changes, or read the comments | `scripts/docx_revisions.py` | references/editing-and-review.md |
| See what changed between two versions | `scripts/docx_compare.py` | references/editing-and-review.md |
| Convert to PDF or PNG, or from .doc/.odt/.rtf | `scripts/docx_convert.py` | references/reading-and-converting.md |
| Something none of these cover (text boxes, footnotes XML, numbering) | edit the XML directly | references/ooxml-notes.md |

## Working principles

**Leave the original untouched.** Write `report_v2.docx`, `report_reviewed.docx` and so on. The scripts refuse to overwrite their input.

**Use styles, not direct formatting.** Headings should use the Heading 1–3 styles, body text Normal, and captions Caption. Then the table of contents, navigation pane, numbering and any later restyling all work. When editing a user's document, reuse its styles. Don't invent new ones.

**Edit through the scripts, not by retyping paragraphs.** Word splits text into "runs" in places you can't see, so a placeholder like `{{client_name}}` may sit across three runs. The replace, fill and redline scripts match across run boundaries and keep the formatting. Rebuilding a paragraph from `p.text` loses bold, italics, links and comments.

**Use review mode when someone else owns the text.** If the user asks you to "suggest", "review", "edit my manuscript" or "mark up", use `docx_redline.py` so every change is a tracked change they can accept or reject. Use `docx_replace.py` only when they want the change made outright, for example "update the client name everywhere".

**Check the result.** Re-run `docx_inspect.py` on the output. It reports the placeholders left, revisions, comments, equations, footnotes and the paper size. Then render pages with `docx_convert.py out.docx --to png -o renders` and look at them.

LibreOffice renders a close approximation of Word, so small differences in line breaks are normal. Comments don't appear in renders, so check them with `docx_revisions.py comments`. Equations only appear if libreoffice-math is installed. Otherwise confirm them with `docx_inspect.py` ("Also contains: N equations").

## Quick recipes

```bash
# Report from Markdown in a house style (headings, tables, equations, footnotes, citations all supported by pandoc)
python scripts/docx_make_reference.py -o house.docx --font "Calibri" --heading-color 1F3864 --a4    # 1F3864 = dark blue
python scripts/docx_convert.py report.md --to docx --reference-doc house.docx -o body.docx
python scripts/docx_finish.py body.docx -o report.docx --a4 --cover --toc --page-numbers --report-no GL-2026-014

# Fill a template; rows containing {{bh.*}} repeat once per item of the "bh" list
python scripts/docx_fill_template.py template.docx data.json -o filled.docx --strict

# Tracked-change review with comments (author = the person the review is from)
python scripts/docx_redline.py draft.docx edits.json -o draft_reviewed.docx --author "R. Kalatehjari"

# Summarise reviewer comments and changes, then make a clean copy to send out
python scripts/docx_revisions.py comments paper_reviewed.docx
python scripts/docx_revisions.py list paper_reviewed.docx           # each change in context: 'old' → 'new', under which heading
python scripts/docx_revisions.py accept paper_reviewed.docx -o paper_clean.docx --stop-tracking --drop-comments

# What changed between versions?
python scripts/docx_compare.py thesis_v3.docx thesis_v4.docx -o changes.md

# PDF and a quick visual check
python scripts/docx_convert.py report.docx --to pdf -o report.pdf
python scripts/docx_convert.py report.docx --to png --pages 1-2 -o renders
```

## Delivering results

Say what you changed, with counts: placeholders filled, replacements made, tracked changes added, comments added. A "clean copy" means no tracked changes and no comments, so use `--drop-comments`, which deletes the comment text from the file too. If a comment is still unresolved, ask before you drop it, or deliver one copy with comments and one without. Mention it if the paper size doesn't suit the user, for example US Letter for someone in New Zealand. Point out anything you left alone, such as an unfilled placeholder, text inside a text box, or a match that crossed a hyperlink. For reviews, give a short summary of the main suggestions. The author shouldn't have to open every comment to see the main points.

---

## Bundled files

The skill's supporting files, verbatim. Unpack them with the command at the top, or read one here. Line is where each file starts in this document.

| File | Size | Line |
|---|---:|---:|
| `references/creating-documents.md` | 11.0 KB | 154 |
| `references/editing-and-review.md` | 9.5 KB | 368 |
| `references/ooxml-notes.md` | 4.3 KB | 508 |
| `references/reading-and-converting.md` | 3.5 KB | 601 |
| `scripts/_docx_common.py` | 9.0 KB | 666 |
| `scripts/docx_compare.py` | 3.9 KB | 909 |
| `scripts/docx_convert.py` | 8.3 KB | 1022 |
| `scripts/docx_fill_template.py` | 5.8 KB | 1218 |
| `scripts/docx_finish.py` | 12.7 KB | 1393 |
| `scripts/docx_inspect.py` | 7.5 KB | 1711 |
| `scripts/docx_make_reference.py` | 5.5 KB | 1877 |
| `scripts/docx_redline.py` | 11.5 KB | 2008 |
| `scripts/docx_replace.py` | 3.4 KB | 2323 |
| `scripts/docx_revisions.py` | 12.7 KB | 2410 |
| `LICENSE` | 1.1 KB | 2735 |

### `references/creating-documents.md`

<!-- bundle-file: references/creating-documents.md sha256=5e513078f6d1d474494004722c3bffeae85eb648bde2bef67bada4bcaa8a969c -->
````markdown
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
````

### `references/editing-and-review.md`

<!-- bundle-file: references/editing-and-review.md sha256=70da2f6488f0edad42d54b8c7560c164dbe9d8bb0004f8b49d28a98286bd0b08 -->
````markdown
# Editing, templates and review

## Contents
1. Find and replace (silent edits)
2. Templates and mail merge
3. Suggesting edits as tracked changes, plus comments
4. Handling a reviewed document: list, accept, reject, comments
5. Comparing versions
6. Editing beyond text

## 1. Find and replace

```bash
python scripts/docx_replace.py in.docx --find "Lot 12" --dry-run                  # see each match in context
python scripts/docx_replace.py in.docx -o out.docx --find "Lot 12" --replace "Lot 14"
python scripts/docx_replace.py in.docx -o out.docx --map renames.json             # {"old": "new", ...} in order
python scripts/docx_replace.py in.docx -o out.docx --regex --find "(\d+) kPa" --replace "\1 kN/m²"
```

- Matches can span runs inside one paragraph. The replacement takes the formatting of the run where the match begins.
- Body, tables (including nested ones), headers and footers are all covered. Text boxes, footnotes and comments aren't. For those, see section 6.
- Do a `--dry-run` first whenever the find string is short or generic. Use `--whole-word` so that "BH1" doesn't also match "BH10".

## 2. Templates and mail merge

Template syntax:

| In the .docx | Data (JSON) | Result |
|---|---|---|
| `{{client_name}}` | `"client_name": "Auckland Council"` | text replaced, keeping the placeholder's formatting |
| `{{client.address}}` | `"client": {"address": "..."}` | dotted path |
| A table row containing `{{bh.id}}`, `{{bh.depth}}` | `"bh": [{"id": "BH1", "depth": "6.5"}, ...]` | the row is repeated once per item |
| `{{#}}` inside a repeated row | | the item number (1, 2, 3 …) |
| `{{logo}}` alone in its paragraph | `"logo": {"image": "logo.png", "width_cm": 4}` | the picture is placed there |

```bash
python scripts/docx_inspect.py template.docx            # the "Placeholders:" line lists what the template expects
python scripts/docx_fill_template.py template.docx data.json -o filled.docx --strict
```

- Numbers are inserted exactly as they appear in the JSON. Pass strings when you want specific formatting (`"6.50"`, `"1,250"`, `"3 October 2026"`).
- `--strict` stops with an error if any placeholder has no value. Without it, the script leaves the placeholder and warns, which suits drafts.
- **To make a template from an existing document**, replace the variable parts with placeholders using `docx_replace.py` (for example `--find "Auckland Council" --replace "{{client_name}}"`). The styles, logos and headers all stay as they were.

**Mail merge** (one document per row of a CSV):

```python
import csv, json, subprocess, os
os.makedirs("letters", exist_ok=True)
for i, row in enumerate(csv.DictReader(open("recipients.csv", encoding="utf-8-sig")), start=1):
    json.dump(row, open("_row.json", "w"))
    name = "".join(c for c in row["name"] if c.isalnum() or c in " -_").strip().replace(" ", "_")
    subprocess.run(["python", "scripts/docx_fill_template.py", "letter_template.docx", "_row.json",
                    "-o", f"letters/{i:03d}_{name}.docx", "--strict"], check=True)
```

To get PDFs, run `docx_convert.py --to pdf` on each output. To get one combined PDF, merge the PDFs afterwards (pdf-workbench `pdf_pages.py merge`).

## 3. Suggesting edits as tracked changes, plus comments

Use this whenever the text belongs to someone else: a student's thesis, a co-author's manuscript, or a contractor's report.

```json
[
  {"find": "Lot 12", "replace": "Lot 14", "comment": "Per the survey plan dated 12 Aug"},
  {"find": "very ", "replace": ""},
  {"find": "groundwater table", "comment": "State when it was measured", "occurrence": 1},
  {"find": "(\\d+) kPa", "replace": "\\1 kN/m²", "regex": true}
]
```

```bash
python scripts/docx_redline.py manuscript.docx edits.json -o manuscript_RK.docx --author "R. Kalatehjari" --initials RK
```

- An entry with `replace` creates a tracked deletion plus insertion. `"replace": ""` is a pure deletion. An entry with only `comment` adds a comment without changing anything.
- **Changes are word-level by default.** `"Lot 12" → "Lot 14"` appears as Lot ~~12~~ <u>14</u>, which is how reviewers mark up by hand. So you can give a whole phrase as `find` for context, and only the words that differ are marked. Set `"minimal": false` to strike and replace the whole match.
- `occurrence` limits the edit to the Nth match, counted through the whole document as it stands when that edit runs. The default is `"all"`. Edits run in file order, so a later edit sees the text left by earlier ones. Put comment-only entries before replacements that touch the same words. To get occurrence numbers, run `docx_replace.py --find "…" --dry-run`, which lists the matches as #1, #2 and so on.
- Make `find` strings specific, about 3–8 words, so they match exactly where you mean. Check them first with `docx_replace.py --dry-run`.
- `--track-future` turns on Word's Track Changes, so the author's own edits are tracked as well.
- When a match crosses a hyperlink, a field or an existing tracked change, it's skipped and reported. Put that suggestion in a comment instead.
- `--author` is the name Word shows on each change. Use the reviewer's name: the user's own name when it's their review, or the role they asked for ("Supervisor"). Tell them they can change it if they want.
- Comments don't appear in PDF or PNG renders. Check them with `docx_revisions.py comments out.docx`. Check tracked changes with `docx_revisions.py list` or a render, where changes show in colour.
- Comments can't go in headers or footers. Mention issues there, such as a wrong project name, in your reply.

**Writing good review comments.** Say what the problem is and why, then suggest a fix: "Units missing: give su in kPa", not "unclear". Group repeated issues. Comment once ("Applies throughout: use SI units") rather than 40 times. End with a summary for the author in your reply: the main issues, then the minor ones.

**Review checklist** (technical reports and theses). Check:
- the structure: every scope item has results, and the conclusions follow from them.
- that terms and abbreviations are defined at first use.
- that units, datums and standards are given.
- that each table and figure has a numbered caption, is cited in the text and is interpreted.
- that headings use styles (`docx_inspect.py` shows "manual bold" headings), and that the paper size is right for the audience.
- that references are complete.
- that no placeholders or leftover template text remain.
Things a tracked change or comment can't express (page size, heading styles, header text) go in your summary.

## 4. Handling a reviewed document

```bash
python scripts/docx_revisions.py list reviewed.docx                 # who changed what
python scripts/docx_revisions.py comments reviewed.docx --json      # comments + the text each refers to
python scripts/docx_revisions.py accept reviewed.docx -o clean.docx --stop-tracking
python scripts/docx_revisions.py accept reviewed.docx -o v2.docx --author "Supervisor"   # only one reviewer's changes
python scripts/docx_revisions.py reject reviewed.docx -o original.docx
```

- Accept and reject cover insertions and deletions, moves, inserted or deleted paragraph marks, table rows and formatting changes, in the body, headers, footers, footnotes and endnotes.
- Comments stay unless you add `--drop-comments`. That option removes the comment anchors **and** the comments part, so no comment text is left anywhere in the file. Use it for copies that go to clients or journals.
- When a comment was attached to text that has since been deleted, accepting the deletion leaves the comment without any text. `comments` then says "(anchor text no longer present)".
- `list` prints each change with its context. Pairs of deletion and insertion come out as `'old' → 'new'`, together with the heading they sit under and the paragraph as it reads once accepted. Use this to write the summary.
- Before accepting everything, give the user that summary. Accepting can't be undone in the output file, although the input stays unchanged.

**Responding to reviewers** (for example on a journal manuscript): pull the comments as JSON, draft a response table (comment, response, change made with its location), then make the agreed changes with `docx_redline.py`. That way the editor sees them tracked.

## 5. Comparing versions

```bash
python scripts/docx_compare.py v3.docx v4.docx -o changes.md
```

The output lists every changed, added and removed paragraph, with word-level `~~deleted~~ **inserted**` marks. If either file contains tracked changes, accept them first so you compare the final text. For a native Word redline, tell the user about Word's Review → Compare.

## 6. Editing beyond text

| Target | How |
|---|---|
| Text boxes and shapes | Their text is in `w:txbxContent` inside `w:drawing` or `mc:AlternateContent`. Iterate `doc.element.body.iter(qn("w:txbxContent"))`, wrap each `w:p` in `Paragraph(p, doc)`, and use `replace_in_paragraph` from `_docx_common.py` |
| Footnotes and endnotes | Separate parts (`word/footnotes.xml`) that python-docx doesn't expose. Use the XML approach in ooxml-notes.md |
| Fill or shading of table cells, borders | ooxml-notes.md, and the `shade()` helper in creating-documents.md §4 |
| Update fields (TOC, numbering) | Open in Word and press F9, or use `w:updateFields` (creating-documents.md §5). Converting with LibreOffice also refreshes the TOC in the PDF |
| Change a style everywhere (font, size) | Edit the style (`doc.styles["Normal"].font.name = …`), not each paragraph |
| Delete a paragraph | `p._p.getparent().remove(p._p)` |
| Insert a paragraph after another | `new = OxmlElement("w:p"); p._p.addnext(new); para = Paragraph(new, p._parent); para.add_run("text"); para.style = p.style` |
````

### `references/ooxml-notes.md`

<!-- bundle-file: references/ooxml-notes.md sha256=098114f43d8917f01aa5dde38c3c6a2f0c4ebf42da944ba680b4471ad925535a -->
````markdown
# Working with the underlying XML (OOXML)

Use this when python-docx and the scripts don't reach what you need. A .docx is a ZIP archive of XML parts.

## Map of a .docx

| Part | Holds |
|---|---|
| `word/document.xml` | the body: `w:body` → `w:p` (paragraphs), `w:tbl` (tables), and the final `w:sectPr` |
| `word/styles.xml` | paragraph, character and table styles |
| `word/numbering.xml` | list and heading numbering (`w:abstractNum` + `w:num`) |
| `word/header1.xml`, `footer1.xml` … | headers and footers, linked from each `w:sectPr` |
| `word/footnotes.xml`, `endnotes.xml` | notes. The body has `w:footnoteReference w:id="n"` |
| `word/comments.xml` | comment text. The body has `w:commentRangeStart/End` and `w:commentReference` |
| `word/settings.xml` | `w:trackRevisions`, `w:updateFields`, compatibility settings |
| `word/media/*` | images, referenced through relationships (`r:embed`) |
| `docProps/core.xml` | title, author, created and modified dates |

The text model is: paragraph `w:p` contains properties `w:pPr` (style, numbering, spacing) and runs `w:r`. Each run contains properties `w:rPr` (bold, italic, font, size) and content: `w:t` for text, `w:tab`, `w:br`, `w:drawing`, `w:fldChar` and so on. Tracked changes wrap runs in `w:ins` or `w:del`. Deleted text sits in `w:delText`.

## Safe editing pattern

```python
import zipfile, shutil
from lxml import etree
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}

src, dst = "in.docx", "out.docx"
with zipfile.ZipFile(src) as zin:
    xml = etree.fromstring(zin.read("word/footnotes.xml"))
    for t in xml.iterfind(".//w:t", NS):
        if t.text and "Lot 12" in t.text:
            t.text = t.text.replace("Lot 12", "Lot 14")
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/footnotes.xml":
                data = etree.tostring(xml, xml_declaration=True, encoding="UTF-8", standalone=True)
            zout.writestr(item, data)
```

Rules that prevent corrupt files:

- Copy every other part byte for byte, in the original order. `[Content_Types].xml` must stay.
- Keep `xml:space="preserve"` on any `w:t` whose text starts or ends with a space.
- Element order inside `w:pPr`, `w:rPr` and `w:sectPr` is fixed by the schema. Insert new children in the right place. For example, in `w:rPr` the font (`w:rFonts`) comes before `w:b`, which comes before `w:sz`. If you're unsure, look at a Word-made document.
- IDs (`w:id` on revisions, comments and bookmarks) must be unique within their kind.
- After editing, open the file with python-docx and convert it with `docx_convert.py --to pdf`. If either fails, the XML is broken.

Inside python-docx you can reach the same XML: `doc.element` (body), `paragraph._p`, `run._r`, `table._tbl`, `section._sectPr`, and `doc.part.package.iter_parts()` for other parts. Parts that python-docx doesn't model, such as footnotes, appear as generic parts. Read them with `etree.fromstring(part.blob)` and write them back with `part._blob = etree.tostring(...)`. `docx_revisions.py` does this.

## Recipes

**Bold a label in every table's first column:**

```python
for t in doc.tables:
    for row in t.rows:
        for r in row.cells[0].paragraphs[0].runs:
            r.bold = True
```

**Find text in text boxes:**

```python
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph
for box in doc.element.body.iter(qn("w:txbxContent")):
    for p_el in box.iter(qn("w:p")):
        print(Paragraph(p_el, doc).text)
```

**Turn on line numbering** (useful for manuscripts under review):

```python
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
ln = OxmlElement("w:lnNumType"); ln.set(qn("w:countBy"), "1"); ln.set(qn("w:restart"), "continuous")
sectPr = doc.sections[0]._sectPr
pgMar = sectPr.find(qn("w:pgMar"))
(pgMar.addnext if pgMar is not None else sectPr.append)(ln)  # must come after w:pgMar
```

**Double line spacing everywhere** (common for manuscripts): `doc.styles["Normal"].paragraph_format.line_spacing = 2.0`.

**Numbered headings.** Reuse a template whose Heading styles already link to a multilevel list. That's far more reliable than building `w:abstractNum` by hand. To check whether a style is numbered, look for `w:numPr` in `doc.styles["Heading 1"].element.pPr`.
````

### `references/reading-and-converting.md`

<!-- bundle-file: references/reading-and-converting.md sha256=6099cb24485684031df6aee88b8a4975a726de30cc4b4d5f055661517382aa90 -->
````markdown
# Reading and converting Word documents

## Reading content

| Need | Command |
|---|---|
| Structure at a glance | `python scripts/docx_inspect.py in.docx` (`--json` for scripts) |
| Full text with headings, lists, tables, images and equations | `python scripts/docx_convert.py in.docx --to md -o in.md` |
| Plain text only | `python scripts/docx_convert.py in.docx --to txt` |
| Reviewer comments, with the text they refer to | `python scripts/docx_revisions.py comments in.docx` |
| Tracked changes | `python scripts/docx_revisions.py list in.docx` |

Notes on the Markdown export (pandoc):

- The Title style becomes YAML front matter (`title:`), and headings become `#` levels.
- Images are written to `<name>_media/`, next to the `.md` file.
- Equations come out as LaTeX (`$\phi' = 32^\circ$`). This is the best way to read them, because LibreOffice renders don't show Word equations.
- Tracked changes are **accepted** in the export (`--track-changes=accept`). If you need to see the proposed edits themselves, read them with `docx_revisions.py list`.
- Text boxes, shapes and SmartArt are often missing. If `docx_inspect.py` shows few words but the rendered page is full, look in text boxes (ooxml-notes.md).
- Without pandoc, the script falls back to a basic converter. It handles headings, lists, tables, bold and italic, but not images, equations or footnotes.

To read with python-docx in body order, paragraphs and tables interleaved:

```python
import docx
from docx.table import Table
from docx.text.paragraph import Paragraph
d = docx.Document("in.docx")
for block in d.element.body.iterchildren():
    tag = block.tag.rsplit("}", 1)[1]
    if tag == "p":
        p = Paragraph(block, d); print(p.style.name, "|", p.text)
    elif tag == "tbl":
        t = Table(block, d); print([[c.text for c in r.cells] for r in t.rows])
```

`d.paragraphs` alone skips everything inside tables, so use the loop above, or `iter_paragraphs()` from `scripts/_docx_common.py`.

## Converting

Without `-o`, the output is written next to the input (`report.pdf`, `report.md` + `report_media/`, `renders/`). Pass `-o` to choose a location.

```bash
python scripts/docx_convert.py report.docx --to pdf              # LibreOffice, ~2 s per document
python scripts/docx_convert.py report.docx --to png --pages 1-3 -o renders   # visual check
python scripts/docx_convert.py legacy.doc --to docx              # .doc / .rtf / .odt → .docx
python scripts/docx_convert.py notes.md --to docx --reference-doc house.docx
python scripts/docx_convert.py notes.md --to pdf --reference-doc house.docx   # via .docx, keeps the styling
python scripts/docx_convert.py report.pdf --to png               # render an existing PDF without re-converting
python scripts/docx_convert.py report.docx --to html|odt|txt|md
```

- **PDF fidelity.** LibreOffice is close to Word, but fonts that aren't installed get substituted, so line breaks and page counts can shift. When the exact look matters, such as a thesis submission, tell the user to export the final PDF from Word. Use the LibreOffice PDF for checking and drafts.
- **Legacy .doc files.** Convert them to .docx first. python-docx can't open .doc.
- **Batch.** Loop in the shell. Each call starts LibreOffice with a private profile, so calls never clash with a copy the user has open:
  ```bash
  for f in *.docx; do python scripts/docx_convert.py "$f" --to pdf; done
  ```
- **PDF to Word.** That conversion is lossy. Use a dedicated PDF skill (pdf-workbench) to extract the text and tables, then rebuild the document with this skill.
````

### `scripts/_docx_common.py`

<!-- bundle-file: scripts/_docx_common.py sha256=7ef40d1786ae5e7dbc18c90bf6d1b02a5aef702466d5b3bc988a0451e8c2db10 -->
````python
"""Shared helpers for the docx-workbench scripts (imported from the same folder).

- iter_paragraphs(doc): every paragraph in body, tables (incl. nested), headers, footers
- replace_in_paragraph(p, regex, repl): run-aware replace that survives Word splitting
  text such as "{{client_name}}" across several runs
"""
import re
import sys

sys.dont_write_bytecode = True  # keep the skill folder free of __pycache__

try:
    import docx  # noqa: F401
    from docx.text.paragraph import Paragraph
    from docx.text.run import Run
    from docx.oxml.ns import qn
except ImportError:
    sys.exit("python-docx is required: pip install python-docx")


def _walk(container, seen):
    for p in container.paragraphs:
        yield p
    for table in container.tables:
        for row in table.rows:
            for cell in row.cells:
                tc = cell._tc
                if tc in seen:  # merged cells repeat in row.cells; keep the element itself so identity is stable
                    continue
                seen.add(tc)
                yield from _walk(cell, seen)


def iter_paragraphs(doc, headers=True):
    seen = set()
    yield from _walk(doc, seen)
    if not headers:
        return
    parts = set()
    for s in doc.sections:
        for hf in (s.header, s.first_page_header, s.even_page_header,
                   s.footer, s.first_page_footer, s.even_page_footer):
            if hf.is_linked_to_previous:
                continue
            key = id(hf.part)
            if key in parts:
                continue
            parts.add(key)
            yield from _walk(hf, seen)


def text_runs(p):
    """Runs that carry the paragraph's visible text, in order (includes runs inside hyperlinks)."""
    runs = []
    for child in p._p.iterchildren():
        if child.tag == qn("w:r"):
            runs.append(Run(child, p))
        elif child.tag in (qn("w:hyperlink"), qn("w:ins"), qn("w:smartTag"), qn("w:fldSimple")):
            for r in child.iterchildren(qn("w:r")):
                runs.append(Run(r, p))
    return runs


def replace_in_paragraph(p, regex, repl):
    """Replace regex matches across run boundaries. `repl` is a str or a function(match)->str.

    The replacement inherits the formatting of the run where the match starts.
    Returns the number of replacements made.
    """
    runs = text_runs(p)
    if not runs:
        return 0
    texts = [r.text for r in runs]
    full = "".join(texts)
    matches = list(regex.finditer(full))
    if not matches:
        return 0
    # starting offset of each run
    starts, pos = [], 0
    for t in texts:
        starts.append(pos)
        pos += len(t)

    def locate(offset, end=False):
        for i in range(len(runs)):
            lo, hi = starts[i], starts[i] + len(texts[i])
            if (lo <= offset < hi) or (end and lo < offset <= hi):
                return i, offset - lo
        return len(runs) - 1, len(texts[-1])

    for m in reversed(matches):
        s, e = m.span()
        if s == e:
            continue
        new = repl(m) if callable(repl) else m.expand(repl)
        si, so = locate(s)
        ei, eo = locate(e, end=True)
        if si == ei:
            t = texts[si]
            texts[si] = t[:so] + new + t[eo:]
        else:
            texts[si] = texts[si][:so] + new
            for k in range(si + 1, ei):
                texts[k] = ""
            texts[ei] = texts[ei][eo:]
    for r, t in zip(runs, texts):
        if r.text != t:
            r.text = t
    return len([m for m in matches if m.start() != m.end()])


def compile_pattern(find, regex=False, ignore_case=False, whole_word=False):
    pat = find if regex else re.escape(find)
    if whole_word:
        pat = r"\b" + pat + r"\b"
    return re.compile(pat, re.IGNORECASE if ignore_case else 0)


# Order of children in word/settings.xml (CT_Settings). Word rejects out-of-order elements,
# so new settings must be inserted before the first element that the schema puts after them.
SETTINGS_ORDER = """writeProtection view zoom removePersonalInformation removeDateAndTime
doNotDisplayPageBoundaries displayBackgroundShape printPostScriptOverText printFractionalCharacterWidth
printFormsData embedTrueTypeFonts embedSystemFonts saveSubsetFonts saveFormsData mirrorMargins
alignBordersAndEdges bordersDoNotSurroundHeader bordersDoNotSurroundFooter gutterAtTop hideSpellingErrors
hideGrammaticalErrors activeWritingStyle proofState formsDesign attachedTemplate linkStyles
stylePaneFormatFilter stylePaneSortMethod documentType mailMerge revisionView trackRevisions
doNotTrackMoves doNotTrackFormatting documentProtection autoFormatOverride styleLockTheme styleLockQFSet
defaultTabStop autoHyphenation consecutiveHyphenLimit hyphenationZone doNotHyphenateCaps showEnvelope
summaryLength clickAndTypeStyle defaultTableStyle evenAndOddHeaders bookFoldRevPrinting bookFoldPrinting
bookFoldPrintingSheets drawingGridHorizontalSpacing drawingGridVerticalSpacing
displayHorizontalDrawingGridEvery displayVerticalDrawingGridEvery doNotUseMarginsForDrawingGridOrigin
drawingGridHorizontalOrigin drawingGridVerticalOrigin doNotShadeFormData noPunctuationKerning
characterSpacingControl printTwoOnOne strictFirstAndLastChars noLineBreaksAfter noLineBreaksBefore
savePreviewPicture doNotValidateAgainstSchema saveInvalidXml ignoreMixedContent alwaysShowPlaceholderText
doNotDemarcateInvalidXml saveXmlDataOnly useXSLTWhenSaving saveThroughXslt showXMLTags
alwaysMergeEmptyNamespace updateFields hdrShapeDefaults footnotePr endnotePr compat docVars rsids mathPr
attachedSchema themeFontLang clrSchemeMapping doNotIncludeSubdocsInStats doNotAutoCompressPictures
forceUpgrade captions readModeInkLockDown smartTagType schemaLibrary shapeDefaults doNotEmbedSmartTags
decimalSymbol listSeparator""".split()


def set_setting(doc, name, val=None):
    """Add (or update) a w:<name> element in settings.xml at its schema position."""
    from docx.oxml import OxmlElement
    settings = doc.settings.element
    el = settings.find(qn(f"w:{name}"))
    if el is None:
        el = OxmlElement(f"w:{name}")
        later = set(SETTINGS_ORDER[SETTINGS_ORDER.index(name) + 1:])
        anchor = next((c for c in settings if c.tag.split("}")[-1] in later), None)
        if anchor is not None:
            anchor.addprevious(el)
        else:
            settings.append(el)
    if val is not None:
        el.set(qn("w:val"), val)
    return el


def add_field(paragraph, instr, placeholder="1"):
    """Append a complex field (PAGE, NUMPAGES, SEQ Figure, TOC, PAGEREF ...) to a paragraph.
    `placeholder` is the cached result shown until Word updates fields."""
    from docx.oxml import OxmlElement

    def fld(kind):
        r = paragraph.add_run()
        el = OxmlElement("w:fldChar")
        el.set(qn("w:fldCharType"), kind)
        r._r.append(el)
        return r
    fld("begin")
    r = paragraph.add_run()
    it = OxmlElement("w:instrText")
    it.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    it.text = f" {instr} "
    r._r.append(it)
    fld("separate")
    res = paragraph.add_run(placeholder)
    fld("end")
    return res


def ensure_paragraph_style(doc, style_id, name, based_on="Normal", font_size=None, bold=None,
                           color=None, space_before=None, space_after=None, tab_right_twips=None, indent_twips=None):
    """Create a paragraph style with an explicit Word styleId (e.g. 'TOC1', 'Footer') if missing."""
    from docx.oxml import OxmlElement
    styles_el = doc.styles.element
    for st in styles_el.iterchildren(qn("w:style")):
        if st.get(qn("w:styleId")) == style_id:
            return st
    st = OxmlElement("w:style")
    st.set(qn("w:type"), "paragraph")
    st.set(qn("w:styleId"), style_id)
    for tag, val in (("w:name", name), ("w:basedOn", based_on), ("w:uiPriority", "39")):
        e = OxmlElement(tag)
        e.set(qn("w:val"), val)
        st.append(e)
    st.append(OxmlElement("w:unhideWhenUsed"))
    ppr = OxmlElement("w:pPr")
    if tab_right_twips:
        tabs = OxmlElement("w:tabs")
        tab = OxmlElement("w:tab")
        tab.set(qn("w:val"), "right")
        tab.set(qn("w:leader"), "dot")
        tab.set(qn("w:pos"), str(int(tab_right_twips)))
        tabs.append(tab)
        ppr.append(tabs)
    if space_before is not None or space_after is not None:
        sp = OxmlElement("w:spacing")
        if space_before is not None:
            sp.set(qn("w:before"), str(int(space_before * 20)))
        if space_after is not None:
            sp.set(qn("w:after"), str(int(space_after * 20)))
        ppr.append(sp)
    if indent_twips:
        ind = OxmlElement("w:ind")
        ind.set(qn("w:left"), str(int(indent_twips)))
        ppr.append(ind)
    st.append(ppr)
    rpr = OxmlElement("w:rPr")
    if bold:
        rpr.append(OxmlElement("w:b"))
    if color:
        c = OxmlElement("w:color")
        c.set(qn("w:val"), color)
        rpr.append(c)
    if font_size:
        sz = OxmlElement("w:sz")
        sz.set(qn("w:val"), str(int(font_size * 2)))
        rpr.append(sz)
    st.append(rpr)
    styles_el.append(st)
    return st


def set_style_id(paragraph, style_id):
    paragraph._p.get_or_add_pPr().get_or_add_pStyle().val = style_id
````

### `scripts/docx_compare.py`

<!-- bundle-file: scripts/docx_compare.py sha256=9dbe028e9f62682ac9c70b492b1f581d3a8a8e4236bfd3f5ab287a4e87848432 -->
````python
#!/usr/bin/env python3
"""Compare two versions of a Word document and report what changed.

Aligns paragraphs (body + table cells, in order), then shows word-level
differences inside changed paragraphs. Output is Markdown:
  ~~deleted words~~  **inserted words**   and whole added/removed paragraphs.

Usage:
    python docx_compare.py v1.docx v2.docx [-o changes.md] [--context 0]
Files that contain tracked changes: accept them first (docx_revisions.py accept)
so you compare final text. For a Word-native redline, use Word: Review → Compare.
"""
import argparse
import difflib
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _docx_common import iter_paragraphs  # noqa: E402

import docx  # noqa: E402


def paragraphs(path):
    d = docx.Document(path)
    out = []
    for p in iter_paragraphs(d, headers=False):
        t = p.text.strip()
        if t:
            out.append(t)
    return out


def word_diff(a, b):
    ta, tb = re.findall(r"\S+|\s+", a), re.findall(r"\S+|\s+", b)
    sm = difflib.SequenceMatcher(None, ta, tb, autojunk=False)
    out = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            out.append("".join(ta[i1:i2]))
        if op in ("delete", "replace"):
            seg = "".join(ta[i1:i2]).strip()
            if seg:
                out.append(f"~~{seg}~~ ")
        if op in ("insert", "replace"):
            seg = "".join(tb[j1:j2]).strip()
            if seg:
                out.append(f"**{seg}** ")
    return re.sub(r" {2,}", " ", "".join(out)).strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("old")
    ap.add_argument("new")
    ap.add_argument("-o", "--output")
    ap.add_argument("--context", type=int, default=0, help="unchanged paragraphs to show around changes")
    a = ap.parse_args()

    A, B = paragraphs(a.old), paragraphs(a.new)
    sm = difflib.SequenceMatcher(None, A, B, autojunk=False)
    lines = [f"# Changes: `{os.path.basename(a.old)}` → `{os.path.basename(a.new)}`", ""]
    stats = {"changed": 0, "added": 0, "removed": 0}
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            if a.context:
                for t in A[i1:i2][:a.context]:
                    lines += [f"> {t[:200]}", ""]
            continue
        if op == "replace":
            # pair paragraphs up by similarity; leftovers count as added/removed
            pa, pb = A[i1:i2], B[j1:j2]
            for k in range(max(len(pa), len(pb))):
                if k < len(pa) and k < len(pb) and difflib.SequenceMatcher(None, pa[k], pb[k]).ratio() > 0.4:
                    lines += [f"- **Changed** (¶{i1 + k + 1}): {word_diff(pa[k], pb[k])}", ""]
                    stats["changed"] += 1
                else:
                    if k < len(pa):
                        lines += [f"- **Removed** (¶{i1 + k + 1}): ~~{pa[k]}~~", ""]
                        stats["removed"] += 1
                    if k < len(pb):
                        lines += [f"- **Added** (new ¶{j1 + k + 1}): {pb[k]}", ""]
                        stats["added"] += 1
        elif op == "delete":
            for k, t in enumerate(A[i1:i2]):
                lines += [f"- **Removed** (¶{i1 + k + 1}): ~~{t}~~", ""]
                stats["removed"] += 1
        elif op == "insert":
            for k, t in enumerate(B[j1:j2]):
                lines += [f"- **Added** (new ¶{j1 + k + 1}): {t}", ""]
                stats["added"] += 1
    summary = f"{stats['changed']} changed, {stats['added']} added, {stats['removed']} removed paragraph(s)"
    lines.insert(1, "")
    lines.insert(2, summary)
    text = "\n".join(lines).rstrip() + "\n"
    if a.output:
        with open(a.output, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"Wrote {a.output}: {summary}", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
````

### `scripts/docx_convert.py`

<!-- bundle-file: scripts/docx_convert.py sha256=94e14c4ed64bdf07227ced329fe5a446bf7cd16cac59a95d778cb60487f5dfa7 -->
````python
#!/usr/bin/env python3
"""Convert Word documents, and render pages to PNG for a visual check.

  python docx_convert.py report.docx --to pdf            # LibreOffice
  python docx_convert.py report.docx --to png [--pages 1-2] [--dpi 110]
  python docx_convert.py old.doc --to docx               # legacy .doc / .rtf / .odt -> .docx
  python docx_convert.py notes.md --to docx [--reference-doc house.docx]   # pandoc
  python docx_convert.py report.docx --to md|html|txt|odt
  python docx_convert.py notes.md --to pdf [--reference-doc house.docx]  # via .docx
  python docx_convert.py report.pdf --to png                            # render an existing PDF

-o sets the output file (or folder for png). Without -o, output goes NEXT TO THE
INPUT file (png: a "renders" folder next to it). Rendering uses LibreOffice, so
fonts and pagination can differ slightly from Word — good enough to catch
layout mistakes, not a pixel-exact proof.
"""
import argparse
import glob
import os
import shutil
import subprocess
import sys
import tempfile


def soffice():
    for name in ("soffice", "libreoffice", "/Applications/LibreOffice.app/Contents/MacOS/soffice"):
        if shutil.which(name) or os.path.exists(name):
            return shutil.which(name) or name
    sys.exit("LibreOffice not found (apt install libreoffice-writer / brew install --cask libreoffice)")


def lo_convert(src, fmt, outdir):
    os.makedirs(outdir, exist_ok=True)
    with tempfile.TemporaryDirectory() as profile:  # private profile avoids clashes with a running LibreOffice
        cmd = [soffice(), f"-env:UserInstallation=file://{profile}", "--headless", "--convert-to", fmt, "--outdir", outdir, src]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
    base = os.path.splitext(os.path.basename(src))[0]
    ext = fmt.split(":")[0]
    out = os.path.join(outdir, f"{base}.{ext}")
    if not os.path.exists(out):
        sys.exit(f"LibreOffice conversion failed: {res.stderr.strip() or res.stdout.strip()}")
    return out


def basic_markdown(path):
    """Fallback .docx -> Markdown without pandoc: headings, lists, tables, bold/italic."""
    import re
    import docx
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    d = docx.Document(path)
    lines = []
    for block in d.element.body.iterchildren():
        tag = block.tag.split("}")[1]
        if tag == "p":
            p = Paragraph(block, d)
            style = p.style.name if p.style is not None else ""
            text = "".join(
                (f"**{r.text}**" if r.bold and r.text.strip() else f"*{r.text}*" if r.italic and r.text.strip() else r.text)
                for r in p.runs) or p.text
            if not text.strip():
                continue
            m = re.match(r"Heading (\d)", style)
            if style == "Title":
                lines.append(f"# {p.text}")
            elif m:
                lines.append("#" * (int(m.group(1)) + (1 if any(l.startswith('# ') for l in lines[:1]) else 0)) + " " + p.text)
            elif "List Number" in style:
                lines.append(f"1. {text}")
            elif "List" in style or block.find(".//{*}numPr") is not None:
                lines.append(f"- {text}")
            else:
                lines.append(text)
            lines.append("")
        elif tag == "tbl":
            t = Table(block, d)
            rows = [[c.text.replace("\n", " ").replace("|", "\\|") for c in r.cells] for r in t.rows]
            if rows:
                lines.append("| " + " | ".join(rows[0]) + " |")
                lines.append("|" + "---|" * len(rows[0]))
                lines += ["| " + " | ".join(r) + " |" for r in rows[1:]]
                lines.append("")
    return "\n".join(lines)


def parse_pages(spec, n):
    if not spec:
        return list(range(n))
    out = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-", 1)
            out += list(range((int(a) if a else 1) - 1, int(b) if b else n))
        elif part.strip():
            out.append(int(part) - 1)
    return [i for i in out if 0 <= i < n]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("--to", required=True, choices=["pdf", "png", "docx", "odt", "html", "txt", "md"])
    ap.add_argument("-o", "--output", help="output file (png: output folder)")
    ap.add_argument("--pages", help="png only: page spec, 1-based")
    ap.add_argument("--dpi", type=int, default=110)
    ap.add_argument("--reference-doc", help="md->docx: a .docx whose styles to use")
    a = ap.parse_args()

    src = os.path.abspath(a.input)
    if not os.path.exists(src):
        sys.exit(f"Input not found: {a.input}")
    base, ext = os.path.splitext(os.path.basename(src))
    ext = ext.lower()

    src_dir = os.path.dirname(src)
    is_markdown = ext in (".md", ".markdown")

    if a.to == "md" or (is_markdown and a.to == "docx"):
        out = os.path.abspath(a.output or os.path.join(src_dir, f"{base}.{'md' if a.to == 'md' else 'docx'}"))
        if not shutil.which("pandoc"):
            if a.to == "md" and ext == ".docx":
                with open(out, "w", encoding="utf-8") as fh:
                    fh.write(basic_markdown(src))
                print(f"Wrote {out} (basic converter: pandoc not installed — no images/equations/footnotes)", file=sys.stderr)
                return
            sys.exit("pandoc not found (https://pandoc.org/installing.html)")
        cmd = ["pandoc", src, "-o", out]
        cwd = None
        if a.to == "md":
            # -s keeps the Title as YAML front matter; images go to <name>_media/ next to the .md,
            # referenced with RELATIVE paths (pandoc runs inside the output folder)
            cwd = os.path.dirname(out)
            cmd = ["pandoc", src, "-o", os.path.basename(out), "-s", "-t", "gfm", "--wrap=none",
                   "--track-changes=accept", f"--extract-media={os.path.splitext(os.path.basename(out))[0]}_media"]
        if a.reference_doc:
            cmd += ["--reference-doc", os.path.abspath(a.reference_doc)]
        if is_markdown:
            cmd += ["--resource-path", src_dir]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
        if res.returncode != 0:
            sys.exit(f"pandoc failed: {res.stderr.strip()}")
        print(f"Wrote {out}", file=sys.stderr)
        return

    if is_markdown and a.to in ("pdf", "png", "odt", "html", "txt"):
        # Markdown -> .docx (pandoc) -> target (LibreOffice), keeping the reference-doc styling
        with tempfile.TemporaryDirectory() as tmp:
            mid = os.path.join(tmp, f"{base}.docx")
            cmd = ["pandoc", src, "-o", mid, "--resource-path", src_dir]
            if a.reference_doc:
                cmd += ["--reference-doc", os.path.abspath(a.reference_doc)]
            if not shutil.which("pandoc") or subprocess.run(cmd).returncode != 0:
                sys.exit("pandoc is needed to convert Markdown")
            sys.argv = [sys.argv[0], mid, "--to", a.to, "-o", a.output or (os.path.join(src_dir, "renders") if a.to == "png" else os.path.join(src_dir, f"{base}.{a.to}"))]
            if a.pages:
                sys.argv += ["--pages", a.pages]
            return main()

    if a.to == "png":
        outdir = a.output or os.path.join(src_dir, "renders")
        with tempfile.TemporaryDirectory() as tmp:
            pdf = lo_convert(src, "pdf", tmp) if ext != ".pdf" else src
            try:
                import pypdfium2 as pdfium
            except ImportError:
                sys.exit("pip install pypdfium2 to render PNGs")
            os.makedirs(outdir, exist_ok=True)
            doc = pdfium.PdfDocument(pdf)
            for i in parse_pages(a.pages, len(doc)):
                fn = os.path.join(outdir, f"{base}_p{i + 1:03d}.png")
                doc[i].render(scale=a.dpi / 72).to_pil().save(fn)
                print(fn)
            print(f"{len(doc)} page(s) in total", file=sys.stderr)
            doc.close()
        return

    fmt = {"txt": "txt:Text (encoded):UTF8", "html": "html:XHTML Writer File:UTF8"}.get(a.to, a.to)
    if a.output:
        with tempfile.TemporaryDirectory() as tmp:
            out = lo_convert(src, fmt, tmp)
            shutil.move(out, a.output)
            out = a.output
    else:
        out = lo_convert(src, fmt, src_dir)
    print(f"Wrote {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
````

### `scripts/docx_fill_template.py`

<!-- bundle-file: scripts/docx_fill_template.py sha256=551f0c167294d549933eaa93890bfd2790997694d8e133b9f42f7df83fb20acd -->
````python
#!/usr/bin/env python3
"""Fill a Word template that contains {{placeholders}} from a JSON file.

Template rules
  {{name}}            replaced by data["name"] (works even if Word split it across runs)
  {{client.address}}  dotted paths reach into nested objects
  Table rows          a row containing {{items.<field>}} is repeated once per entry
                      of the list data["items"]; the original row is the pattern.
  Images              a value like {"image": "logo.png", "width_cm": 4} replaces the
                      placeholder with that picture (put it alone in its paragraph)
Placeholders work in body, tables, headers and footers.

Usage:
    python docx_fill_template.py template.docx data.json -o filled.docx [--strict]
--strict fails if any placeholder has no value (default: leave it and warn).
Batch: call once per record (see references/editing-and-review.md).
"""
import argparse
import copy
import json
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _docx_common import iter_paragraphs, replace_in_paragraph, text_runs  # noqa: E402

import docx  # noqa: E402
from docx.shared import Cm  # noqa: E402

PH = re.compile(r"\{\{\s*([A-Za-z0-9_.\-]+)\s*\}\}")
MISSING = object()


def lookup(data, path):
    cur = data
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif isinstance(cur, list) and part.isdigit() and int(part) < len(cur):
            cur = cur[int(part)]
        else:
            return MISSING
    return cur


def fmt(v):
    if isinstance(v, bool):
        return "Yes" if v else "No"
    if v is None:
        return ""
    return str(v)  # numbers keep their JSON form (8.0 stays "8.0"); pass strings for custom formatting


def expand_table_rows(doc, data):
    """Repeat rows that reference a list (e.g. {{bh.depth}} with data['bh'] = [...])."""
    count = 0
    for table in iter_tables(doc):
        for row in list(table.rows):
            keys = {m.group(1).split(".")[0] for c in row.cells for m in PH.finditer(c.text)}
            lists = [k for k in keys if isinstance(data.get(k), list)]
            if not lists:
                continue
            key = lists[0]
            items = data[key]
            tr = row._tr
            anchor = tr
            for idx, item in enumerate(items):
                new_tr = copy.deepcopy(tr)
                anchor.addnext(new_tr)
                anchor = new_tr
                new_row = docx.table._Row(new_tr, table)
                local = {**data, key: item}
                seen = set()
                for cell in new_row.cells:
                    if cell._tc in seen:
                        continue
                    seen.add(cell._tc)
                    for p in cell.paragraphs:
                        CELLS[0] += replace_in_paragraph(p, PH, lambda m: render(m, local, idx))
            tr.getparent().remove(tr)
            count += len(items)
    return count


def iter_tables(doc):
    def walk(container):
        for t in container.tables:
            yield t
            for row in t.rows:
                for cell in row.cells:
                    yield from walk(cell)
    yield from walk(doc)
    for s in doc.sections:
        for hf in (s.header, s.footer):
            if not hf.is_linked_to_previous:
                yield from walk(hf)


UNFILLED = []
CELLS = [0]


def render(m, data, idx=None):
    key = m.group(1)
    if key in ("#", "index") and idx is not None:
        return str(idx + 1)
    v = lookup(data, key)
    if v is MISSING:
        UNFILLED.append(key)
        return m.group(0)
    if isinstance(v, dict) and "image" in v:
        return m.group(0)  # images are handled separately
    return fmt(v)


def place_images(doc, data, base_dir):
    n = 0
    for p in iter_paragraphs(doc):
        for m in list(PH.finditer(p.text)):
            v = lookup(data, m.group(1))
            if isinstance(v, dict) and "image" in v:
                path = v["image"] if os.path.isabs(v["image"]) else os.path.join(base_dir, v["image"])
                if not os.path.exists(path):
                    sys.exit(f"Image not found for {{{{{m.group(1)}}}}}: {path}")
                replace_in_paragraph(p, re.compile(re.escape(m.group(0))), "")
                runs = text_runs(p)
                run = runs[0] if runs else p.add_run()
                kw = {}
                if "width_cm" in v:
                    kw["width"] = Cm(float(v["width_cm"]))
                if "height_cm" in v:
                    kw["height"] = Cm(float(v["height_cm"]))
                run.add_picture(path, **kw)
                n += 1
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("template")
    ap.add_argument("data")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()
    if os.path.abspath(a.output) == os.path.abspath(a.template):
        sys.exit("Refusing to overwrite the template; choose a different -o")
    with open(a.data, encoding="utf-8") as fh:
        data = json.load(fh)

    d = docx.Document(a.template)
    rows = expand_table_rows(d, data)
    imgs = place_images(d, data, os.path.dirname(os.path.abspath(a.data)))
    n = 0
    for p in iter_paragraphs(d):
        n += replace_in_paragraph(p, PH, lambda m: render(m, data))
    missing = sorted(set(UNFILLED))
    if missing and a.strict:
        sys.exit(f"No value for: {missing}")
    d.save(a.output)
    print(f"Wrote {a.output}: {n} placeholder(s) filled in text/headers, {rows} table row(s) generated "
          f"({CELLS[0]} cell placeholder(s)), {imgs} image(s) placed", file=sys.stderr)
    if missing:
        print(f"Warning: left unfilled (no data): {missing}", file=sys.stderr)


if __name__ == "__main__":
    main()
````

### `scripts/docx_finish.py`

<!-- bundle-file: scripts/docx_finish.py sha256=13085db14e0d98386e0ae9454d4a8541ae8b95a66c9f5edb4423ba01ff3dee8c -->
````python
#!/usr/bin/env python3
"""Add the finishing parts of a report to an existing .docx (typically pandoc output):
cover page, table of contents with real page numbers, page-number footer,
running header, paper size and margins.

    python docx_finish.py body.docx -o report.docx --a4 --cover --toc --page-numbers \
        [--title "..."] [--subtitle "..."] [--author "..."] [--date "3 October 2026"] [--report-no "GL-2026-014"] \
        [--header-text "Slope Stability – Lot 12"] [--toc-levels 3] [--margins-cm 2.5]

Cover: uses --title/--author/--date, else the document's Title/Author/Date paragraphs
       (pandoc puts YAML front matter there), else core properties. The cover gets
       no header/footer and counts as page 1.
TOC:   a real Word TOC field ("Contents"), pre-filled with entries and page numbers
       (found by rendering with LibreOffice), so it is correct on opening; Word can
       still refresh it (right-click → Update Field).
"""
import argparse
import datetime as dt
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _docx_common import add_field, ensure_paragraph_style, set_style_id  # noqa: E402

import docx  # noqa: E402
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK  # noqa: E402
from docx.oxml import OxmlElement  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402
from docx.shared import Cm, Pt  # noqa: E402
from docx.text.paragraph import Paragraph  # noqa: E402


def style_id(p):
    ps = p._p.find(f"{qn('w:pPr')}/{qn('w:pStyle')}")
    return ps.get(qn("w:val")) if ps is not None else ""


def heading_level(p):
    sid = style_id(p).lower().replace(" ", "")
    m = re.match(r"heading(\d)$", sid)
    if m:
        return int(m.group(1))
    name = (p.style.name if p.style is not None else "").lower()
    m = re.match(r"heading (\d)$", name)
    return int(m.group(1)) if m else None


def new_paragraph_before(anchor_p, text="", style=None):
    el = OxmlElement("w:p")
    anchor_p._p.addprevious(el)
    p = Paragraph(el, anchor_p._parent)
    if style:
        set_style_id(p, style)
    if text:
        p.add_run(text)
    return p


def text_width_twips(section):
    return int((section.page_width - section.left_margin - section.right_margin) / 635)  # EMU -> twips


def build_cover(doc, a):
    body_ps = doc.paragraphs
    meta = {}
    used = []
    for p in body_ps[:6]:
        sid = style_id(p)
        if sid in ("Title", "Subtitle", "Author", "Date", "Abstract") and p.text.strip():
            meta[sid] = p.text.strip()
            used.append(p)
        elif p.text.strip():
            break
    cp = doc.core_properties
    title = a.title or meta.get("Title") or cp.title or "Report"
    subtitle = a.subtitle or meta.get("Subtitle")
    author = a.author or meta.get("Author") or cp.author
    date = a.date or meta.get("Date") or dt.date.today().strftime("%-d %B %Y")
    for p in used:  # rebuild the cover from scratch for consistent spacing
        p._p.getparent().remove(p._p)
    first = doc.paragraphs[0]
    tp = new_paragraph_before(first, title, "Title")
    tp.paragraph_format.space_before = Pt(160)
    tp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if subtitle:
        sp = new_paragraph_before(first, subtitle, "Subtitle")
        sp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    gap = new_paragraph_before(first)
    gap.paragraph_format.space_before = Pt(60)
    for line in filter(None, [author, a.report_no and f"Report {a.report_no}", date]):
        lp = new_paragraph_before(first, line)
        lp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    brk = new_paragraph_before(first)
    brk.add_run().add_break(WD_BREAK.PAGE)
    if not cp.title:
        cp.title = title
    if author and not cp.author:
        cp.author = author
    return title


def add_bookmark(p, name, bid):
    start = OxmlElement("w:bookmarkStart")
    start.set(qn("w:id"), str(bid))
    start.set(qn("w:name"), name)
    end = OxmlElement("w:bookmarkEnd")
    end.set(qn("w:id"), str(bid))
    ppr = p._p.find(qn("w:pPr"))
    if ppr is not None:
        ppr.addnext(start)
    else:
        p._p.insert(0, start)
    p._p.append(end)


def build_toc(doc, a, after_cover):
    sec = doc.sections[0]
    tw = text_width_twips(sec)
    ensure_paragraph_style(doc, "TOCHeading", "TOC Heading", based_on="Heading1" if any(s.style_id == "Heading1" for s in doc.styles) else "Normal",
                           font_size=16, bold=True, space_after=12)
    for lvl in range(1, 4):
        ensure_paragraph_style(doc, f"TOC{lvl}", f"toc {lvl}", tab_right_twips=tw, indent_twips=(lvl - 1) * 220,
                               space_after=3 if lvl > 1 else 4, bold=(lvl == 1))
    heads = [(p, heading_level(p)) for p in doc.paragraphs]
    heads = [(p, lvl) for p, lvl in heads if lvl and lvl <= a.toc_levels and p.text.strip()]
    if not heads:
        print("No Heading-styled paragraphs found; TOC skipped", file=sys.stderr)
        return []
    entries = []
    for i, (p, lvl) in enumerate(heads):
        name = f"_Toc{900000 + i}"
        add_bookmark(p, name, 900000 + i)
        entries.append((p.text.strip(), lvl, name))

    # insertion point: first paragraph after the cover (or the start of the document)
    anchor = doc.paragraphs[after_cover] if after_cover < len(doc.paragraphs) else doc.paragraphs[-1]
    hp = new_paragraph_before(anchor, "Contents", "TOCHeading")
    toc_ps = []
    for k, (text, lvl, name) in enumerate(entries):
        ep = new_paragraph_before(anchor, style=f"TOC{lvl}")
        if k == 0:
            add_field_begin(ep, rf'TOC \o "1-{a.toc_levels}" \h \z \u')
        r = ep.add_run(text)
        ep.add_run("\t")
        add_field(ep, f"PAGEREF {name} \\h", "#")
        toc_ps.append(ep)
    end_r = toc_ps[-1].add_run()
    fc = OxmlElement("w:fldChar")
    fc.set(qn("w:fldCharType"), "end")
    end_r._r.append(fc)
    brk = new_paragraph_before(anchor)
    brk.add_run().add_break(WD_BREAK.PAGE)
    del r, hp
    return entries


def add_field_begin(p, instr):
    for kind, text in (("begin", None), (None, instr), ("separate", None)):
        r = p.add_run()
        if kind:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), kind)
        else:
            el = OxmlElement("w:instrText")
            el.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
            el.text = f" {text} "
        r._r.append(el)


def fill_toc_numbers(path, entries):
    """Render with LibreOffice, find each heading's page, write numbers into the cached PAGEREF results."""
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        print("LibreOffice not found: TOC page numbers left as '#'; Word fills them on Update Field", file=sys.stderr)
        return False
    try:
        import pypdfium2 as pdfium
    except ImportError:
        print("pypdfium2 missing: TOC page numbers left as '#'", file=sys.stderr)
        return False
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([soffice, f"-env:UserInstallation=file://{tmp}/p", "--headless", "--convert-to", "pdf", "--outdir", tmp, path],
                       capture_output=True, timeout=240)
        pdf = os.path.join(tmp, os.path.splitext(os.path.basename(path))[0] + ".pdf")
        if not os.path.exists(pdf):
            print("LibreOffice render failed: TOC numbers left as '#'", file=sys.stderr)
            return False
        doc = pdfium.PdfDocument(pdf)
        norm = lambda s: re.sub(r"\s+", " ", s).strip().lower()  # noqa: E731
        pages = [norm(doc[i].get_textpage().get_text_range()) for i in range(len(doc))]
        doc.close()
    # skip pages up to and including the TOC itself (it repeats every heading)
    toc_page = next((i for i, t in enumerate(pages) if "contents" in t[:200]), 0)
    found, start = {}, toc_page + 1
    for text, lvl, name in entries:
        key = norm(text)[:60]
        for i in range(start, len(pages)):
            if key in pages[i]:
                found[name] = i + 1
                start = i
                break
    d = docx.Document(path)
    for p in d.paragraphs:
        instr = "".join(t.text or "" for t in p._p.iter(qn("w:instrText")))
        m = re.search(r"PAGEREF (_Toc\d+)", instr)
        if not m or m.group(1) not in found:
            continue
        # cached result = text runs between 'separate' and 'end' of the PAGEREF field
        state = None
        for r in p._p.iter(qn("w:r")):
            fc = r.find(qn("w:fldChar"))
            it = r.find(qn("w:instrText"))
            if it is not None and "PAGEREF" in (it.text or ""):
                state = "instr"
            elif fc is not None and fc.get(qn("w:fldCharType")) == "separate" and state == "instr":
                state = "result"
            elif fc is not None and fc.get(qn("w:fldCharType")) == "end" and state == "result":
                break
            elif state == "result":
                t = r.find(qn("w:t"))
                if t is not None:
                    t.text = str(found[m.group(1)])
                    state = "done"
    d.save(path)
    missing = [t for t, _, n in entries if n not in found]
    if missing:
        print(f"Could not locate page for: {missing} (left as '#')", file=sys.stderr)
    return True


def add_page_numbers(doc, a):
    ensure_paragraph_style(doc, "Footer", "footer")
    ensure_paragraph_style(doc, "Header", "header")
    sec = doc.sections[0]
    fp = sec.footer.paragraphs[0] if sec.footer.paragraphs else sec.footer.add_paragraph()
    for r in list(fp.runs):
        r._r.getparent().remove(r._r)
    set_style_id(fp, "Footer")
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    parts = re.split(r"(\{PAGE\}|\{NUMPAGES\})", a.page_format)
    for part in parts:
        if part == "{PAGE}":
            add_field(fp, "PAGE", "1")
        elif part == "{NUMPAGES}":
            add_field(fp, "NUMPAGES", "1")
        elif part:
            fp.add_run(part)
    if a.header_text:
        hp = sec.header.paragraphs[0] if sec.header.paragraphs else sec.header.add_paragraph()
        hp.text = a.header_text
        set_style_id(hp, "Header")
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("docx")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--a4", action="store_true")
    ap.add_argument("--letter", action="store_true")
    ap.add_argument("--margins-cm", type=float)
    ap.add_argument("--cover", action="store_true")
    ap.add_argument("--title"); ap.add_argument("--subtitle"); ap.add_argument("--author")
    ap.add_argument("--date"); ap.add_argument("--report-no")
    ap.add_argument("--toc", action="store_true")
    ap.add_argument("--toc-levels", type=int, default=3)
    ap.add_argument("--page-numbers", action="store_true")
    ap.add_argument("--page-format", default="Page {PAGE} of {NUMPAGES}")
    ap.add_argument("--header-text")
    a = ap.parse_args()
    if os.path.abspath(a.output) == os.path.abspath(a.docx):
        sys.exit("Refusing to overwrite the input; choose a different -o")

    doc = docx.Document(a.docx)
    for s in doc.sections:
        if a.a4 or a.letter:
            w, h = (Cm(21.0), Cm(29.7)) if a.a4 else (Cm(21.59), Cm(27.94))
            landscape = s.page_width and s.page_height and s.page_width > s.page_height
            s.page_width, s.page_height = (h, w) if landscape else (w, h)
        if a.margins_cm is not None:
            s.left_margin = s.right_margin = s.top_margin = s.bottom_margin = Cm(a.margins_cm)

    after_cover = 0
    if a.cover:
        build_cover(doc, a)
        after_cover = next(i for i, p in enumerate(doc.paragraphs) if p._p.find(f".//{qn('w:br')}[@{qn('w:type')}='page']") is not None) + 1
        s0 = doc.sections[0]
        s0.different_first_page_header_footer = True
        for hf in (s0.first_page_header, s0.first_page_footer):  # explicit empty cover header/footer
            hf.is_linked_to_previous = False
            for para in hf.paragraphs:
                for r in list(para.runs):
                    r._r.getparent().remove(r._r)
    if a.page_numbers or a.header_text:
        add_page_numbers(doc, a)
    entries = build_toc(doc, a, after_cover) if a.toc else []
    doc.save(a.output)
    if entries:
        fill_toc_numbers(a.output, entries)
    done = [x for x, on in (("cover", a.cover), (f"TOC ({len(entries)} entries)", a.toc), ("page numbers", a.page_numbers),
                            ("header", bool(a.header_text)), ("A4" if a.a4 else "Letter", a.a4 or a.letter)) if on]
    print(f"Wrote {a.output}: " + ", ".join(done), file=sys.stderr)
    print("Check: python docx_convert.py " + a.output + " --to png --pages 1-3", file=sys.stderr)


if __name__ == "__main__":
    main()
````

### `scripts/docx_inspect.py`

<!-- bundle-file: scripts/docx_inspect.py sha256=0f0dd52dba156541d5e27663baf5e0158f1f876c606564ce7f15093f48728523 -->
````python
#!/usr/bin/env python3
"""Summarise a .docx before working on it.

Reports: core properties, word/paragraph counts, heading outline, styles in use,
tables (size + first row), images, sections (page size, orientation, margins),
headers/footers, comments, tracked changes, fields (TOC, page numbers, SEQ),
and {{placeholders}} found anywhere in the document.

Usage:
    python docx_inspect.py report.docx [--json] [--outline-depth 3]
"""
import argparse
import json
import os
import re
import sys
from collections import Counter

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _docx_common import iter_paragraphs  # noqa: E402

import docx  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402

EMU_PER_CM = 360000
PLACEHOLDER = re.compile(r"\{\{\s*([^{}]+?)\s*\}\}")


def heading_level(p):
    name = (p.style.name if p.style is not None else "") or ""
    if name == "Title":
        return 0
    m = re.match(r"Heading (\d)", name)
    if m:
        return int(m.group(1))
    lvl = p._p.find(f"{qn('w:pPr')}/{qn('w:outlineLvl')}")
    if lvl is not None:
        return int(lvl.get(qn("w:val"))) + 1
    return None


def inspect(path, depth):
    d = docx.Document(path)
    body = d.element.body
    info = {"file": path}
    cp = d.core_properties
    info["properties"] = {k: str(getattr(cp, k)) for k in ("title", "author", "subject", "keywords", "last_modified_by", "created", "modified", "revision") if getattr(cp, k)}

    paras = list(d.paragraphs)
    words = sum(len(p.text.split()) for p in iter_paragraphs(d, headers=False))
    info["counts"] = {"paragraphs_body": len(paras), "words_incl_tables": words, "tables": len(d.tables),
                      "inline_images": len(d.inline_shapes), "sections": len(d.sections)}

    outline = []
    for p in paras:
        lvl = heading_level(p)
        if lvl is not None and lvl <= depth and p.text.strip():
            outline.append({"level": lvl, "text": p.text.strip()[:120]})
    info["outline"] = outline
    info["styles_used"] = dict(Counter(p.style.name for p in iter_paragraphs(d) if p.style is not None).most_common(15))

    info["tables_detail"] = []
    for i, t in enumerate(d.tables, start=1):
        first = [c.text.strip()[:25] for c in t.rows[0].cells] if t.rows else []
        info["tables_detail"].append({"index": i, "rows": len(t.rows), "cols": len(t.columns), "style": t.style.name if t.style else None, "first_row": first})

    secs = []
    for i, s in enumerate(d.sections, start=1):
        secs.append({
            "section": i,
            "page_cm": [round(s.page_width / EMU_PER_CM, 1), round(s.page_height / EMU_PER_CM, 1)] if s.page_width else None,
            "orientation": "landscape" if s.orientation == 1 else "portrait",
            "margins_cm": [round(m / EMU_PER_CM, 2) if m is not None else None for m in (s.top_margin, s.right_margin, s.bottom_margin, s.left_margin)],
            "header": None if s.header.is_linked_to_previous else " | ".join(p.text for p in s.header.paragraphs if p.text)[:100],
            "footer": None if s.footer.is_linked_to_previous else " | ".join(p.text for p in s.footer.paragraphs if p.text)[:100],
            "different_first_page": bool(s.different_first_page_header_footer),
        })
    info["sections_detail"] = secs

    ins = body.findall(f".//{qn('w:ins')}")
    dels = body.findall(f".//{qn('w:del')}")
    authors = Counter(e.get(qn("w:author")) for e in ins + dels)
    info["tracked_changes"] = {"insertions": len(ins), "deletions": len(dels),
                               "format_changes": len(body.findall(f".//{qn('w:rPrChange')}")) + len(body.findall(f".//{qn('w:pPrChange')}")),
                               "authors": dict(authors)}
    try:
        comments = list(d.comments)
        info["comments"] = [{"author": c.author, "text": c.text[:120]} for c in comments][:50]
    except Exception:
        info["comments"] = [] if not body.findall(f".//{qn('w:commentReference')}") else ["(present; python-docx too old to read)"]

    instr = [e.text or "" for e in body.iter(qn("w:instrText"))] + [e.get(qn("w:instr")) or "" for e in body.iter(qn("w:fldSimple"))]
    kinds = Counter((s.strip().split() or ["?"])[0].upper() for s in instr if s.strip())
    info["fields"] = dict(kinds)
    M = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"
    info["equations"] = len(body.findall(f".//{M}oMath"))
    info["footnotes"] = len(body.findall(f".//{qn('w:footnoteReference')}"))
    info["endnotes"] = len(body.findall(f".//{qn('w:endnoteReference')}"))
    info["text_boxes"] = len(body.findall(f".//{qn('w:txbxContent')}"))

    found = Counter()
    for p in iter_paragraphs(d):
        for m in PLACEHOLDER.finditer(p.text):
            found[m.group(1)] += 1
    info["placeholders"] = dict(found)
    return info


def print_human(i):
    print(f"File: {i['file']}")
    if i["properties"]:
        print("Properties: " + "; ".join(f"{k}={v}" for k, v in i["properties"].items()))
    c = i["counts"]
    print(f"Content: {c['words_incl_tables']} words, {c['paragraphs_body']} body paragraphs, {c['tables']} tables, {c['inline_images']} images, {c['sections']} section(s)")
    if i["outline"]:
        print("Outline:")
        for h in i["outline"]:
            print("  " + "  " * max(h["level"] - 1, 0) + ("[T] " if h["level"] == 0 else f"H{h['level']} ") + h["text"])
    else:
        print("Outline: no heading styles used (headings may be manual bold text)")
    print("Styles: " + ", ".join(f"{k}×{v}" for k, v in i["styles_used"].items()))
    for t in i["tables_detail"]:
        print(f"Table {t['index']}: {t['rows']}×{t['cols']} ({t['style']}) first row: {t['first_row']}")
    for s in i["sections_detail"]:
        size = s["page_cm"] or [0, 0]
        paper = "A4" if sorted(size) == [21.0, 29.7] else "US Letter" if sorted(size) == [21.6, 27.9] else "custom"
        print(f"Section {s['section']}: {paper} {s['page_cm']} cm {s['orientation']}, margins T/R/B/L {s['margins_cm']} cm"
              + (f"; header '{s['header']}'" if s["header"] else "") + (f"; footer '{s['footer']}'" if s["footer"] else ""))
    tc = i["tracked_changes"]
    if tc["insertions"] or tc["deletions"] or tc["format_changes"]:
        print(f"Tracked changes: {tc['insertions']} insertions, {tc['deletions']} deletions, {tc['format_changes']} formatting; authors {tc['authors']}")
    else:
        print("Tracked changes: none")
    print(f"Comments: {len(i['comments'])}")
    if i["fields"]:
        print("Fields: " + ", ".join(f"{k}×{v}" for k, v in i["fields"].items()))
    extras = [f"{i[k]} {k.replace('_', ' ')}" for k in ("equations", "footnotes", "endnotes", "text_boxes") if i.get(k)]
    if extras:
        print("Also contains: " + ", ".join(extras) + (" (text-box text is not covered by replace/fill)" if i.get("text_boxes") else ""))
    if i["placeholders"]:
        print("Placeholders: " + ", ".join(f"{{{{{k}}}}}" + (f"×{v}" if v > 1 else "") for k, v in i["placeholders"].items()))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("docx")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--outline-depth", type=int, default=3)
    a = ap.parse_args()
    if a.docx.lower().endswith(".doc"):
        sys.exit("Legacy .doc: convert first — python docx_convert.py file.doc --to docx")
    info = inspect(a.docx, a.outline_depth)
    print(json.dumps(info, indent=2, ensure_ascii=False, default=str) if a.json else "", end="")
    if not a.json:
        print_human(info)


if __name__ == "__main__":
    main()
````

### `scripts/docx_make_reference.py`

<!-- bundle-file: scripts/docx_make_reference.py sha256=39e7efdd763ff5dc54f526fe7cbaa2728ffb801b9727b2835cd2db459836616a -->
````python
#!/usr/bin/env python3
"""Create a styles template ("reference doc") so Markdown -> Word conversions
come out in a consistent house style.

    python docx_make_reference.py -o house.docx --font "Calibri" --size 11 \\
        --heading-font "Calibri Light" --heading-color 1F4E79 --margins-cm 2.5 --a4
    python docx_convert.py notes.md --to docx --reference-doc house.docx

Starts from pandoc's default reference.docx (so every style pandoc uses exists),
or from --base your_template.docx to keep an existing look and only adjust it.
"""
import argparse
import os
import subprocess
import sys
import tempfile

try:
    import docx
    import docx.opc.exceptions
    from docx.enum.text import WD_LINE_SPACING  # noqa: F401
    from docx.oxml.ns import qn
    from docx.shared import Cm, Pt, RGBColor
except ImportError:
    sys.exit("python-docx is required: pip install python-docx")


def set_font(style, name=None, size=None, color=None, bold=None):
    f = style.font
    if name:
        f.name = name
        rpr = style.element.get_or_add_rPr()
        rfonts = rpr.find(qn("w:rFonts"))
        if rfonts is None:
            rfonts = rpr.makeelement(qn("w:rFonts"), {})
            rpr.append(rfonts)
        for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
            rfonts.set(qn(attr), name)
        for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
            if rfonts.get(qn(attr)) is not None:
                del rfonts.attrib[qn(attr)]
    if size:
        f.size = Pt(size)
    if color:
        f.color.rgb = RGBColor.from_string(color.upper())
    if bold is not None:
        f.bold = bold


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--base", help="start from this .docx instead of pandoc's default")
    ap.add_argument("--font", default="Calibri")
    ap.add_argument("--size", type=float, default=11)
    ap.add_argument("--heading-font")
    ap.add_argument("--heading-color", default="1F3864", help="hex RRGGBB (default 1F3864 = dark blue)")
    ap.add_argument("--line-spacing", type=float, default=1.15)
    ap.add_argument("--space-after", type=float, default=6, help="points after body paragraphs")
    ap.add_argument("--margins-cm", type=float, default=2.5)
    ap.add_argument("--a4", action="store_true", help="A4 paper (default keeps the base's size)")
    a = ap.parse_args()

    if a.base:
        d = docx.Document(a.base)
    else:
        with tempfile.TemporaryDirectory() as t:
            ref = os.path.join(t, "reference.docx")
            try:
                subprocess.run(["pandoc", "-o", ref, "--print-default-data-file", "reference.docx"], check=True)
                d = docx.Document(ref)
            except (FileNotFoundError, subprocess.CalledProcessError, docx.opc.exceptions.PackageNotFoundError):
                print("pandoc not available; starting from python-docx's default template", file=sys.stderr)
                d = docx.Document()

    # look styles up by displayed name (pandoc's template capitalises built-in names,
    # which python-docx's styles[...] lookup does not expect)
    by_name = {st.name: st for st in d.styles}
    hfont = a.heading_font or a.font
    for name in ("Normal", "Body Text", "First Paragraph", "Compact", "Block Text"):
        if name in by_name:
            st = by_name[name]
            set_font(st, a.font, a.size if name != "Compact" else None)
            pf = st.paragraph_format
            pf.line_spacing = a.line_spacing
            pf.space_after = Pt(a.space_after)
    sizes = {"Title": a.size * 2.2, "Subtitle": a.size * 1.4, "Heading 1": a.size * 1.6, "Heading 2": a.size * 1.3,
             "Heading 3": a.size * 1.15, "Heading 4": a.size}
    for name, sz in sizes.items():
        if name in by_name:
            set_font(by_name[name], hfont, round(sz), a.heading_color, bold=name.startswith("Heading"))
    for name in ("Caption", "Image Caption", "Table Caption"):
        if name in by_name:
            set_font(by_name[name], a.font, a.size - 1, "404040")
            by_name[name].font.italic = True

    # document defaults: anything without an explicit font (Author, Date, footnotes...) uses these
    rpr_default = d.styles.element.find(f"{qn('w:docDefaults')}/{qn('w:rPrDefault')}/{qn('w:rPr')}")
    if rpr_default is not None:
        rf = rpr_default.find(qn("w:rFonts"))
        if rf is None:
            rf = rpr_default.makeelement(qn("w:rFonts"), {})
            rpr_default.insert(0, rf)
        for attr in list(rf.attrib):
            del rf.attrib[attr]
        for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
            rf.set(qn(attr), a.font)
    for name, size, color in (("Author", a.size + 1, None), ("Date", a.size, None), ("Abstract", a.size - 1, None),
                              ("Footnote Text", a.size - 2, None), ("Block Text", a.size, None),
                              ("TOC Heading", round(a.size * 1.45), a.heading_color)):
        if name in by_name:
            set_font(by_name[name], hfont if name == "TOC Heading" else a.font, size, color,
                     bold=True if name == "TOC Heading" else None)

    for s in d.sections:
        if a.a4:
            s.page_width, s.page_height = Cm(21.0), Cm(29.7)
        s.left_margin = s.right_margin = s.top_margin = s.bottom_margin = Cm(a.margins_cm)

    d.save(a.output)
    print(f"Wrote {a.output}. Use: python docx_convert.py in.md --to docx --reference-doc {a.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
````

### `scripts/docx_redline.py`

<!-- bundle-file: scripts/docx_redline.py sha256=71ad0e87da95ddfd29f3bbb90d71ef0c1e9cb93573f3b7f665db53b515c41d93 -->
````python
#!/usr/bin/env python3
"""Make edits to a .docx as TRACKED CHANGES (redline) and/or add COMMENTS,
so the author can review and accept/reject them in Word.

Edits file (JSON list), applied in order:
[
  {"find": "Lot 12", "replace": "Lot 14", "comment": "Lot number per survey plan"},
  {"find": "very ", "replace": ""},                        # tracked deletion
  {"find": "groundwater table", "comment": "Give the date measured"},  # comment only
  {"find": "(\\\\d+) kPa", "replace": "\\\\1 kN/m²", "regex": true, "occurrence": 1}
]
Keys: find (required), replace (omit for comment-only), comment, regex (bool),
ignore_case (bool), occurrence ("all" default, or N = only the Nth match, counted in
the document as it is when that edit runs), minimal (default true: only the words
that differ are marked, so "Lot 12"->"Lot 14" shows as Lot ~~12~~ 14; false marks
the whole match). Edits run in file order; a later edit sees earlier ones applied.

Usage:
    python docx_redline.py in.docx edits.json -o in_reviewed.docx --author "R. Kalatehjari"
                           [--initials RK] [--track-future]
--track-future switches on Word's Track Changes so later manual edits are tracked too.
Scope: body paragraphs and table cells (Word does not allow comments in headers/footers).
A match must lie in plain text runs of one paragraph; matches crossing hyperlinks,
fields or existing tracked changes are skipped and reported.
"""
import argparse
import copy
import datetime as dt
import json
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _docx_common import set_setting  # noqa: E402

import docx  # noqa: E402
from docx.oxml import OxmlElement  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402
from docx.text.run import Run  # noqa: E402

TEXT_CHILDREN = {qn(t) for t in ("w:rPr", "w:t", "w:tab", "w:br", "w:cr", "w:noBreakHyphen", "w:softHyphen", "w:lastRenderedPageBreak")}
TRANSPARENT = {qn(t) for t in ("w:proofErr", "w:bookmarkStart", "w:bookmarkEnd", "w:permStart", "w:permEnd")}


class Ids:
    def __init__(self, root):
        vals = [int(v) for v in (e.get(qn("w:id")) for e in root.iter()) if v and v.lstrip("-").isdigit()]
        self.n = max(vals + [0]) + 1000

    def next(self):
        self.n += 1
        return str(self.n)


def plain(r):
    return all(c.tag in TEXT_CHILDREN for c in r)


def segments(p_el):
    """Lists of consecutive direct w:r children (transparent markup allowed between them)."""
    seg, out = [], []
    for c in p_el.iterchildren():
        if c.tag == qn("w:r"):
            seg.append(c)
        elif c.tag in TRANSPARENT:
            continue
        else:
            if seg:
                out.append(seg)
            seg = []
    if seg:
        out.append(seg)
    return out


def split_run(r_el, k, para):
    """Split run at character k; returns the new right-hand run element."""
    run = Run(r_el, para)
    t = run.text
    right = copy.deepcopy(r_el)
    run.text = t[:k]
    Run(right, para).text = t[k:]
    r_el.addnext(right)
    return right


def isolate(seg, s, e, para):
    """Split runs so [s,e) is covered exactly by whole runs; return those run elements."""
    pos, out = 0, []
    i = 0
    runs = list(seg)
    while i < len(runs):
        r = runs[i]
        t = Run(r, para).text
        lo, hi = pos, pos + len(t)
        if hi <= s or lo >= e or not t:
            pos = hi
            i += 1
            continue
        if not plain(r):
            return None
        if lo < s:  # cut off the left part
            right = split_run(r, s - lo, para)
            runs.insert(i + 1, right)
            pos = s
            i += 1
            continue
        if hi > e:  # cut off the right part
            split_run(r, e - lo, para)
            out.append(r)
            break
        out.append(r)
        pos = hi
        i += 1
    return out


def mark(tag, ids, author, date):
    el = OxmlElement(tag)
    el.set(qn("w:id"), ids.next())
    el.set(qn("w:author"), author)
    el.set(qn("w:date"), date)
    return el


def apply_edit(doc, para, runs, edit, ids, author, initials, date):
    has_replace = "replace" in edit
    first = runs[0]
    new_run = None
    if has_replace:
        template = copy.deepcopy(first)
        d_el = mark("w:del", ids, author, date)
        first.addprevious(d_el)
        for r in runs:
            d_el.append(r)
            for t in r.iter(qn("w:t")):
                t.tag = qn("w:delText")
        anchor_after = d_el
        if edit["replace"]:
            i_el = mark("w:ins", ids, author, date)
            Run(template, para).text = edit["replace"]
            i_el.append(template)
            d_el.addnext(i_el)
            anchor_after = i_el
            new_run = template
        start_el, end_el = d_el, anchor_after
    else:
        start_el, end_el = runs[0], runs[-1]

    if edit.get("comment"):
        target = [new_run] if new_run is not None else (list(runs) if not has_replace else [])
        apply_comment(doc, para, target, start_el, end_el, edit["comment"], author, initials)


def apply_comment(doc, para, target_els, start_el, end_el, text, author, initials):
    """Add a comment and place its range around start_el..end_el at paragraph level."""
    tmp = None
    if not target_els:  # pure deletion: anchor on a temporary empty run after the deletion
        tmp = OxmlElement("w:r")
        end_el.addnext(tmp)
        target_els = [tmp]
    c = doc.add_comment([Run(r, para) for r in target_els], text=text, author=author, initials=initials)
    cid = str(c.comment_id)
    p_el = para._p
    rs = p_el.find(f".//{qn('w:commentRangeStart')}[@{qn('w:id')}='{cid}']")
    re_ = p_el.find(f".//{qn('w:commentRangeEnd')}[@{qn('w:id')}='{cid}']")
    ref = None
    for r in p_el.iter(qn("w:r")):
        cr = r.find(qn("w:commentReference"))
        if cr is not None and cr.get(qn("w:id")) == cid:
            ref = r
    if rs is not None and re_ is not None and ref is not None:
        start_el.addprevious(rs)
        end_el.addnext(re_)
        re_.addnext(ref)
    if tmp is not None and tmp.getparent() is not None and len(tmp) == 0:
        tmp.getparent().remove(tmp)


def body_paragraphs(doc):
    def walk(container, seen):
        for p in container.paragraphs:
            yield p
        for t in container.tables:
            for row in t.rows:
                for cell in row.cells:
                    if cell._tc in seen:
                        continue
                    seen.add(cell._tc)
                    yield from walk(cell, seen)
    yield from walk(doc, set())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("docx")
    ap.add_argument("edits")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--author", default="Reviewer")
    ap.add_argument("--initials", default="")
    ap.add_argument("--track-future", action="store_true")
    a = ap.parse_args()
    if os.path.abspath(a.output) == os.path.abspath(a.docx):
        sys.exit("Refusing to overwrite the input; choose a different -o")
    with open(a.edits, encoding="utf-8") as fh:
        edits = json.load(fh)
    doc = docx.Document(a.docx)
    ids = Ids(doc.element)
    date = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    initials = a.initials or "".join(w[0] for w in a.author.replace(".", " ").split() if w)[:3]

    report = []
    for edit in edits:
        if "find" not in edit:
            sys.exit(f"Edit without 'find': {edit}")
        rx = re.compile(edit["find"] if edit.get("regex") else re.escape(edit["find"]), re.I if edit.get("ignore_case") else 0)
        want = edit.get("occurrence", "all")
        seen_n, done, skipped = 0, 0, 0
        for para in body_paragraphs(doc):
            for seg in segments(para._p):
                text = "".join(Run(r, para).text for r in seg)
                ms = list(rx.finditer(text))
                # process right-to-left so earlier offsets stay valid
                todo = []
                for m in ms:
                    seen_n += 1
                    if want == "all" or seen_n == int(want):
                        todo.append(m)
                for m in reversed(todo):
                    cur = segments_containing(para, seg)
                    e2 = dict(edit)
                    s, e = m.start(), m.end()
                    if "replace" in e2:
                        if edit.get("regex"):
                            e2["replace"] = m.expand(edit["replace"])
                        if edit.get("minimal", True):
                            s, e, e2["replace"] = trim_common(m.group(0), e2["replace"], s, e)
                            if s == e and not e2["replace"]:
                                continue  # replacement identical to the text
                            if s == e:  # pure insertion: anchor on the next character
                                e2["insert_at"] = True
                    if e2.pop("insert_at", False):
                        runs = isolate(cur, s, s + 1, para) if s < len(text) else isolate(cur, s - 1, s, para)
                        if not runs:
                            skipped += 1
                            continue
                        insert_only(para, runs[0], e2, ids, a.author, date, before=s < len(text), doc=doc, initials=initials)
                        done += 1
                        continue
                    runs = isolate(cur, s, e, para)
                    if not runs:
                        skipped += 1
                        continue
                    apply_edit(doc, para, runs, e2, ids, a.author, initials, date)
                    done += 1
        report.append((edit["find"], done, skipped))

    if a.track_future:
        set_setting(doc, "trackRevisions")
    doc.save(a.output)
    for find, done, skipped in report:
        print(f"{find!r}: {done} change(s)" + (f", {skipped} skipped (match crosses a hyperlink/field/revision)" if skipped else ""), file=sys.stderr)
    print(f"Wrote {a.output}. Open in Word → Review to accept/reject. Author: {a.author}", file=sys.stderr)
    if not any(d for _, d, _ in report):
        print("No edits applied — check the find strings against docx_inspect / docx_to_markdown output.", file=sys.stderr)


TOKEN = re.compile(r"\w+|\s+|[^\w\s]")


def trim_common(old, new, s, e):
    """Shrink a replacement to the differing middle, on word boundaries.
    Returns (new_start, new_end, new_replacement)."""
    a, b = TOKEN.findall(old), TOKEN.findall(new)
    i = 0
    while i < min(len(a), len(b)) and a[i] == b[i]:
        i += 1
    j = 0
    while j < min(len(a), len(b)) - i and a[len(a) - 1 - j] == b[len(b) - 1 - j]:
        j += 1
    pre = "".join(a[:i])
    suf = "".join(a[len(a) - j:]) if j else ""
    mid_new = "".join(b[i:len(b) - j]) if j else "".join(b[i:])
    return s + len(pre), e - len(suf), mid_new


def insert_only(para, anchor_run, edit, ids, author, date, before, doc, initials):
    """Tracked insertion with no deletion, placed before/after a 1-character anchor run."""
    template = copy.deepcopy(anchor_run)
    i_el = mark("w:ins", ids, author, date)
    Run(template, para).text = edit["replace"]
    i_el.append(template)
    (anchor_run.addprevious if before else anchor_run.addnext)(i_el)
    if edit.get("comment"):
        apply_comment(doc, para, [template], i_el, i_el, edit["comment"], author, initials)


def segments_containing(para, seg):
    """After earlier splits, recompute the live segment that contains the original first run."""
    for s in segments(para._p):
        if seg[0] in s:
            return s
    return seg


if __name__ == "__main__":
    main()
````

### `scripts/docx_replace.py`

<!-- bundle-file: scripts/docx_replace.py sha256=f3e15d0b719cb04f2edbb4fcc8f69a3d8e77ca94900e2644cfb8846a2b2184e1 -->
````python
#!/usr/bin/env python3
"""Find and replace text in a .docx while keeping formatting.

Word often splits one visible word across several runs (spell-check marks,
revisions, partial bold). A naive run-by-run replace misses those; this script
matches across runs inside each paragraph and keeps the formatting of the run
where each match starts. Covers body text, tables (incl. nested), headers and
footers. Text inside text boxes, footnotes and comments is not touched.

Usage:
    python docx_replace.py in.docx -o out.docx --find "Lot 12" --replace "Lot 14"
    python docx_replace.py in.docx -o out.docx --map replacements.json   # {"old": "new", ...}
    python docx_replace.py in.docx --find "colour" --dry-run              # just count/show matches
Options: --regex  --ignore-case  --whole-word  --no-headers
For tracked (redlined) edits instead of silent replacement, use docx_redline.py.
"""
import argparse
import json
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _docx_common import compile_pattern, iter_paragraphs, replace_in_paragraph  # noqa: E402

import docx  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("docx")
    ap.add_argument("-o", "--output")
    ap.add_argument("--find")
    ap.add_argument("--replace", default="")
    ap.add_argument("--map", help="JSON file mapping find -> replace (applied in order)")
    ap.add_argument("--regex", action="store_true", help="treat find strings as regular expressions (\\1 in replace works)")
    ap.add_argument("--ignore-case", action="store_true")
    ap.add_argument("--whole-word", action="store_true")
    ap.add_argument("--no-headers", action="store_true", help="skip headers and footers")
    ap.add_argument("--dry-run", action="store_true", help="report matches without writing")
    a = ap.parse_args()

    pairs = []
    if a.map:
        with open(a.map, encoding="utf-8") as fh:
            pairs = list(json.load(fh).items())
    if a.find is not None:
        pairs.append((a.find, a.replace))
    if not pairs:
        sys.exit("Give --find/--replace or --map")
    if not a.dry_run and not a.output:
        sys.exit("Give -o OUTPUT (or --dry-run)")
    if a.output and os.path.abspath(a.output) == os.path.abspath(a.docx):
        sys.exit("Refusing to overwrite the input; choose a different -o")

    d = docx.Document(a.docx)
    total = 0
    for find, repl in pairs:
        rx = compile_pattern(find, a.regex, a.ignore_case, a.whole_word)
        n = 0
        for p in iter_paragraphs(d, headers=not a.no_headers):
            if a.dry_run:
                for m in rx.finditer(p.text):
                    n += 1
                    s = max(0, m.start() - 30)
                    print(f"  #{n}: …{p.text[s:m.end() + 30]}…")
            else:
                n += replace_in_paragraph(p, rx, repl if a.regex else repl.replace("\\", "\\\\"))
        label = f"{find!r}: {n} match(es)" if a.dry_run else f"{find!r} -> {repl!r}: {n} replacement(s)"
        print(label, file=sys.stderr)
        total += n
    if a.dry_run:
        return
    d.save(a.output)
    print(f"Wrote {a.output} ({total} replacement(s))", file=sys.stderr)
    if total == 0:
        print("Nothing matched. Check spelling, try --ignore-case, or the text may sit in a text box/footnote.", file=sys.stderr)


if __name__ == "__main__":
    main()
````

### `scripts/docx_revisions.py`

<!-- bundle-file: scripts/docx_revisions.py sha256=06b98e247083b9ad3ba241a38e6d5fa46e0d5e5a69ba758e10403858faf0a9d8 -->
````python
#!/usr/bin/env python3
"""List, accept or reject tracked changes; list comments with the text they refer to.

Subcommands:
  list      in.docx [--json]          every insertion/deletion: type, author, date, text
  comments  in.docx [--json]          every comment: author, date, comment text, anchored text
  accept    in.docx -o out.docx [--author NAME]   accept all (or only NAME's) changes
  reject    in.docx -o out.docx [--author NAME]   reject all (or only NAME's) changes

Handles run insertions/deletions, moves, inserted/deleted paragraph marks,
inserted/deleted table rows and formatting changes, in the body, headers,
footers, footnotes and endnotes. Comments are kept unless you add --drop-comments,
which deletes them completely (anchors, comment text and the comments part).
Options for accept/reject: -o OUT  --author NAME  --drop-comments  --stop-tracking
"""
import argparse
import json
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _docx_common  # noqa: E402,F401

import docx  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402
from lxml import etree  # noqa: E402

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
STORY_TYPES = ("document.main", "header", "footer", "footnotes", "endnotes")


def story_roots(doc):
    """(part, root_element, is_blob) for every story part that can hold revisions."""
    out = []
    for part in doc.part.package.iter_parts():
        ct = part.content_type or ""
        if "wordprocessingml" not in ct or not any(s in ct for s in STORY_TYPES):
            continue
        if hasattr(part, "_element"):
            out.append((part, part._element, False))
        else:
            out.append((part, etree.fromstring(part.blob), True))
    return out


def text_of(el):
    return "".join(t.text or "" for t in el.iter(qn("w:t"), qn("w:delText"), qn("w:instrText")))


def unwrap(el):
    parent = el.getparent()
    idx = parent.index(el)
    for child in list(el):
        parent.insert(idx, child)
        idx += 1
    parent.remove(el)


def remove(el):
    el.getparent().remove(el)


def merge_with_next(p):
    """Remove p's paragraph mark: append the next paragraph's content to p, delete the next one."""
    nxt = p.getnext()
    while nxt is not None and nxt.tag != qn("w:p"):
        nxt = nxt.getnext()
    if nxt is None:
        return
    for child in list(nxt):
        if child.tag != qn("w:pPr"):
            p.append(child)
    remove(nxt)


def by(author, el):
    return author is None or el.get(qn("w:author")) == author


def resolve(root, mode, author):
    """mode = 'accept' or 'reject'. Returns number of revisions resolved."""
    n = 0
    keep_tag, drop_tag = ("w:ins", "w:del") if mode == "accept" else ("w:del", "w:ins")
    keep_move, drop_move = ("w:moveTo", "w:moveFrom") if mode == "accept" else ("w:moveFrom", "w:moveTo")

    # table rows inserted/deleted (marker lives in w:trPr)
    for mk in list(root.iter(qn("w:ins"), qn("w:del"))):
        par = mk.getparent()
        if par is not None and par.tag == qn("w:trPr") and by(author, mk):
            row = par.getparent()
            if mk.tag == qn(drop_tag):
                remove(row)
            else:
                remove(mk)
            n += 1

    # paragraph marks inserted/deleted (marker lives in w:pPr/w:rPr)
    for mk in list(root.iter(qn("w:ins"), qn("w:del"))):
        par = mk.getparent()
        if par is None or par.tag != qn("w:rPr") or par.getparent() is None or par.getparent().tag != qn("w:pPr"):
            continue
        if not by(author, mk):
            continue
        p = par.getparent().getparent()
        remove(mk)
        if mk.tag == qn(drop_tag):
            merge_with_next(p)
        n += 1

    # run-level content
    for el in list(root.iter(qn(drop_tag), qn(drop_move))):
        if el.getparent() is not None and by(author, el) and el.getparent().tag not in (qn("w:rPr"), qn("w:trPr")):
            remove(el)
            n += 1
    for el in list(root.iter(qn(keep_tag), qn(keep_move))):
        if el.getparent() is not None and by(author, el) and el.getparent().tag not in (qn("w:rPr"), qn("w:trPr")):
            for t in el.iter(qn("w:delText")):
                t.tag = qn("w:t")
            for t in el.iter(qn("w:delInstrText")):
                t.tag = qn("w:instrText")
            unwrap(el)
            n += 1
    for tag in ("w:moveFromRangeStart", "w:moveFromRangeEnd", "w:moveToRangeStart", "w:moveToRangeEnd"):
        for el in list(root.iter(qn(tag))):
            remove(el)

    # formatting changes
    for tag in ("w:rPrChange", "w:pPrChange", "w:sectPrChange", "w:tblPrChange", "w:trPrChange", "w:tcPrChange", "w:tblGridChange", "w:numberingChange"):
        for ch in list(root.iter(qn(tag))):
            if not by(author, ch):
                continue
            if mode == "reject":
                owner = ch.getparent()  # e.g. w:rPr; the change holds the OLD properties
                old = ch.find(f"{{{W}}}{owner.tag.split('}')[1]}")
                for child in list(owner):
                    if child is not ch:
                        owner.remove(child)
                if old is not None:
                    for child in list(old):
                        owner.append(child)
            remove(ch)
            n += 1
    return n


def para_text(p, accepted=True):
    """Paragraph text as it would read with revisions accepted (or rejected)."""
    out = []
    for node in p.iter(qn("w:t"), qn("w:delText"), qn("w:tab")):
        anc = node.getparent()
        in_del = in_ins = False
        while anc is not None and anc is not p:
            if anc.tag in (qn("w:del"), qn("w:moveFrom")):
                in_del = True
            if anc.tag in (qn("w:ins"), qn("w:moveTo")):
                in_ins = True
            anc = anc.getparent()
        if (accepted and in_del) or (not accepted and in_ins):
            continue
        out.append("\t" if node.tag == qn("w:tab") else (node.text or ""))
    return "".join(out)


def style_of(p):
    ps = p.find(f"{qn('w:pPr')}/{qn('w:pStyle')}")
    return ps.get(qn("w:val")) if ps is not None else ""


def cmd_list(a):
    doc = docx.Document(a.docx)
    rows = []
    for part, root, _ in story_roots(doc):
        where = os.path.basename(str(part.partname))
        heading, pno = "", 0
        for p in root.iter(qn("w:p")):
            pno += 1
            st = style_of(p).lower()
            if st.startswith("heading") or st == "title":
                heading = para_text(p)[:60]
            context = para_text(p)
            changes = []
            for el in p.iter(qn("w:ins"), qn("w:del"), qn("w:moveFrom"), qn("w:moveTo"), qn("w:rPrChange"), qn("w:pPrChange")):
                par = el.getparent()
                kind = el.tag.split("}")[1]
                if kind in ("rPrChange", "pPrChange"):
                    kind = "format"
                elif par is not None and par.tag == qn("w:rPr") and par.getparent() is not None and par.getparent().tag == qn("w:pPr"):
                    kind += "-paragraph-mark"
                elif par is not None and par.tag in (qn("w:rPr"), qn("w:trPr")):
                    continue
                changes.append({"el": el, "type": kind, "author": el.get(qn("w:author")), "date": (el.get(qn("w:date")) or "")[:10],
                                "text": text_of(el) if kind != "format" else ""})
            i = 0
            while i < len(changes):
                c = changes[i]
                nxt = changes[i + 1] if i + 1 < len(changes) else None
                row = {"part": where, "paragraph": pno, "heading": heading, "author": c["author"], "date": c["date"]}
                if (c["type"] == "del" and nxt and nxt["type"] == "ins" and nxt["author"] == c["author"]
                        and c["el"].getnext() is nxt["el"]):
                    row.update(type="replace", old=c["text"], new=nxt["text"])
                    i += 2
                else:
                    row.update(type=c["type"], text=c["text"])
                    i += 1
                row["context"] = context[:160]
                rows.append(row)
    if a.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return
    if not rows:
        print("No tracked changes.")
    for r in rows:
        what = f"{r['old']!r} → {r['new']!r}" if r["type"] == "replace" else repr(r.get("text", ""))
        loc = f"¶{r['paragraph']}" + (f" under '{r['heading']}'" if r["heading"] else "") + (f" [{r['part']}]" if r["part"] != "document.xml" else "")
        print(f"[{r['type']}] {what}  — {r['author']} {r['date']}, {loc}\n    reads (accepted): {r['context']!r}")
    print(f"{len(rows)} change(s)", file=sys.stderr)


def cmd_comments(a):
    doc = docx.Document(a.docx)
    anchors = {}
    body = doc.element.body
    active = {}  # comment id -> [visible text, deleted text]
    for node in body.iter():
        if node.tag == qn("w:commentRangeStart"):
            active[node.get(qn("w:id"))] = [[], []]
        elif node.tag == qn("w:commentRangeEnd"):
            cid = node.get(qn("w:id"))
            if cid in active:
                vis, dele = active.pop(cid)
                vis_t, del_t = "".join(vis), "".join(dele)
                anchors[cid] = vis_t + (f" [deleted: {del_t}]" if del_t else "")
        elif node.tag == qn("w:t"):
            for v in active.values():
                v[0].append(node.text or "")
        elif node.tag == qn("w:delText"):
            for v in active.values():
                v[1].append(node.text or "")
    out = []
    try:
        for c in doc.comments:
            out.append({"id": c.comment_id, "author": c.author, "initials": c.initials,
                        "date": str(getattr(c, "timestamp", "") or ""), "comment": c.text,
                        "anchored_text": anchors.get(str(c.comment_id), "")})
    except AttributeError:
        sys.exit("Reading comments needs python-docx >= 1.2: pip install -U python-docx")
    if a.json:
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return
    if not out:
        print("No comments.")
    for c in out:
        on = c["anchored_text"][:150] or "(anchor text no longer present — e.g. the commented text was deleted)"
        print(f"#{c['id']} {c['author']}: {c['comment']}\n    on: {on!r}")


COMMENT_RELS = ("/comments", "/commentsExtended", "/commentsIds", "/commentsExtensible", "/people")


def drop_comments(doc):
    """Remove comment anchors from the body AND the comment parts themselves,
    so no comment text remains anywhere in the saved file."""
    for tag in ("w:commentRangeStart", "w:commentRangeEnd"):
        for el in list(doc.element.body.iter(qn(tag))):
            remove(el)
    for r in list(doc.element.body.iter(qn("w:r"))):
        if r.find(qn("w:commentReference")) is not None:
            remove(r)
    rels = doc.part.rels
    for rid in [rid for rid, rel in rels.items() if rel.reltype.endswith(COMMENT_RELS)]:
        rels.pop(rid)  # parts no longer referenced are not written on save


def cmd_resolve(a, mode):
    if os.path.abspath(a.output) == os.path.abspath(a.docx):
        sys.exit("Refusing to overwrite the input; choose a different -o")
    doc = docx.Document(a.docx)
    total = 0
    for part, root, is_blob in story_roots(doc):
        n = resolve(root, mode, a.author)
        total += n
        if is_blob and n:
            part._blob = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    if a.drop_comments:
        drop_comments(doc)
    settings = doc.settings.element
    tr = settings.find(qn("w:trackRevisions"))
    if tr is not None and a.stop_tracking:
        settings.remove(tr)
    doc.save(a.output)
    print(f"Wrote {a.output}: {mode}ed {total} revision(s)" + (f" by {a.author}" if a.author else ""), file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("list", "comments"):
        s = sub.add_parser(name)
        s.add_argument("docx")
        s.add_argument("--json", action="store_true")
    for name in ("accept", "reject"):
        s = sub.add_parser(name)
        s.add_argument("docx")
        s.add_argument("-o", "--output", required=True)
        s.add_argument("--author", help="only resolve changes by this author")
        s.add_argument("--drop-comments", action="store_true", help="also delete all comments (anchors and comment text) — use for a clean copy to send out")
        s.add_argument("--stop-tracking", action="store_true", help="switch off Track Changes in the output")
    a = ap.parse_args()
    if a.cmd == "list":
        cmd_list(a)
    elif a.cmd == "comments":
        cmd_comments(a)
    else:
        cmd_resolve(a, a.cmd)


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
