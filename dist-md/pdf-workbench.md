---
name: pdf-workbench
description: Read, extract from, edit, fill, OCR and create PDF files with tested Python scripts. Use this whenever a task involves a .pdf file in any way — pulling text, tables, figures or DOIs out of papers and reports; merging, splitting, rotating, reordering or deleting pages; filling or flattening forms (fillable or not); making scanned PDFs searchable; adding stamps, watermarks or passwords; or generating a new PDF from data, Markdown or HTML. Trigger even when the user doesn't say "PDF" but mentions a scanned document, a journal article, a lab report, a datasheet or a form they need filled.
license: MIT (see LICENSE)
---

**Single-file build.** This is the `pdf-workbench` skill packed into one file on 2026-11-05. The instructions below are its SKILL.md, unchanged. Its supporting files (5 reference files, 9 scripts and the licence) are embedded verbatim under "Bundled files" at the end, each with a SHA-256 checksum. You can read a reference there directly. Before you run a script or use an asset, unpack the files once:

```bash
python3 - "${CLAUDE_SKILL_DIR}/SKILL.md" "${TMPDIR:-/tmp}/pdf-workbench" <<'PY'
import hashlib, os, re, sys
src, out = sys.argv[1], sys.argv[2]
if not os.path.isfile(src):
    src = "/mnt/skills/user/pdf-workbench/SKILL.md"
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

The first argument is the path of this file. Claude Code and Cowork fill it in for you; elsewhere, use the path you read this file from (on claude.ai the command also tries `/mnt/skills/user/pdf-workbench/SKILL.md`). The command prints the folder it wrote to. From then on, use that folder wherever the instructions mean this skill's folder: paths such as `scripts/...`, `references/...`, `assets/...` and `<this-skill>/...` all point into it.

---


# PDF Workbench

A practical toolkit for working with PDFs. The bundled scripts cover the jobs that come up most often, and the reference files explain the rest. Every script is a standalone Python CLI. Run it with `--help` to see its options.

The `scripts/` and `references/` paths below are relative to this skill's folder, the directory that contains this SKILL.md. Call scripts by their full path (for example `python /path/to/pdf-workbench/scripts/pdf_inspect.py`), or `cd` into the skill folder first. Keep your outputs in the user's working folder, not in the skill folder.

## Setup

Most environments already have these. Install anything missing before you start:

```bash
pip install pypdf pdfplumber pypdfium2 reportlab pikepdf openpyxl pytesseract
# system tools that some paths use (optional): qpdf, poppler-utils (pdftotext/pdftoppm), tesseract-ocr, ocrmypdf
```

In this skill, page numbers are **1-based** everywhere, the way a person counts them. Page specs look like `1-3,7,10-`. Here `10-` means page 10 to the last page.

## Always start by inspecting

Before you choose an approach, find out what kind of PDF you have. The right method depends on whether there is a text layer, whether the file is encrypted, and whether it has form fields.

```bash
python scripts/pdf_inspect.py input.pdf          # human-readable summary
python scripts/pdf_inspect.py input.pdf --json   # for programmatic use
```

The summary reports the page count, page sizes, metadata, encryption, the amount of text on each page, form fields, images, bookmarks and any DOIs it finds, with the page each DOI appears on. "Likely-scanned" pages have almost no text but do have an image. OCR those before you extract text. "Sparse" pages, such as blank forms and divider pages, have little text and no image, and don't need OCR.

## Pick the path

| Goal | Use | Details |
|---|---|---|
| Get the text (keeping reading order or layout) | `scripts/pdf_text.py` | references/reading-and-extraction.md |
| Get tables as CSV or Excel | `scripts/pdf_tables.py` | references/reading-and-extraction.md |
| Get embedded figures or images | `scripts/pdf_images.py` | references/reading-and-extraction.md |
| Search a scan, or extract text from one | `scripts/pdf_ocr.py`, then the text tools | references/reading-and-extraction.md |
| Merge, split, extract, delete, rotate or reorder pages | `scripts/pdf_pages.py` | references/editing-and-assembly.md |
| Watermark, stamp, encrypt, decrypt, compress or repair | snippets and commands | references/editing-and-assembly.md |
| List, fill or flatten fillable form fields | `scripts/pdf_forms.py` | references/forms.md |
| Stop recipients from editing a file you send | flatten, then restrict with an owner password | references/forms.md, references/editing-and-assembly.md §5 |
| Write onto a form or page that has no fields | `scripts/pdf_render.py --grid`, then `scripts/pdf_overlay_text.py` | references/forms.md |
| See what a page looks like (to check your work) | `scripts/pdf_render.py` | — |
| Create a new PDF (report, table, certificate, Markdown or HTML to PDF) | reportlab or pandoc | references/creating-pdfs.md |
| Journal articles: title, abstract, references, DOIs, figure captions | the text tools plus the patterns in the reference | references/research-papers.md |

Only read the reference file you need. Each one is self-contained.

## Working principles

**Never overwrite the input.** Write results to a new file, such as `report_merged.pdf` or `form_filled.pdf`. The user may need the original, and a failed write can't destroy it if you never touch it.

**Check your output visually when it matters.** Text extraction can look fine and still be wrong: columns can interleave, ligatures can break and form values can render invisibly. After you fill a form, overlay text or rebuild a document, render the affected pages with `pdf_render.py` and look at the PNG before you report success. This catches most mistakes that would otherwise reach the user.

**Choose the lightest tool that works.** Use pypdf for page-level structure: merging, splitting, rotating, forms and metadata. Use pdfplumber when position matters: tables, columns and word coordinates. Use pypdfium2 for rendering. Use qpdf or pikepdf for repair, linearisation and decryption. Use OCR only when there is no text layer, because it is slow and makes mistakes.

**Coordinates are in PDF points and start at the bottom-left.** One point is 1/72 inch, and A4 is 595 × 842 pt. pdfplumber reports `top` from the top edge, so convert with `y = page_height - top`. `pdf_render.py --grid` draws a point grid over the page so you can read positions straight off the image. `pdf_render.py --crop x0,y0,x1,y1 --dpi 300` zooms in on a small area.

**Use the right flag for each output.** Scripts that write one file take `-o FILE`. `pdf_render.py`, `pdf_images.py` and `pdf_pages.py split` write a folder, and also take `-o` (or `--out-dir`). `pdf_tables.py` takes `-o FILE` for xlsx, md and json output, and `--out-dir` for CSV output.

**Report what you couldn't do.** If a page has no text layer and OCR isn't available, the PDF is encrypted with an unknown password, or a table didn't parse cleanly, say so plainly and suggest the next step. Don't silently return partial results.

## Quick recipes

```bash
# Text from pages 1–5, keeping the visual layout (good for reports with columns of numbers)
python scripts/pdf_text.py paper.pdf --pages 1-5 --layout -o paper.txt

# All tables in a datasheet to one Excel workbook (one sheet per table)
python scripts/pdf_tables.py datasheet.pdf --format xlsx -o tables.xlsx

# Merge three files, then keep only pages 2–4 of the result
python scripts/pdf_pages.py merge a.pdf b.pdf c.pdf -o merged.pdf
python scripts/pdf_pages.py extract merged.pdf --pages 2-4 -o excerpt.pdf

# Two-column article: read the title block at full width, then the columns
python scripts/pdf_text.py paper.pdf --pages 1 --columns 2 --header 180

# Fill a fillable form from JSON, then flatten it (fields become plain page content)
python scripts/pdf_forms.py list form.pdf -o fields.json
python scripts/pdf_forms.py fill form.pdf values.json -o filled.pdf --flatten

# Make a scanned report searchable
python scripts/pdf_ocr.py scan.pdf -o scan_searchable.pdf --lang eng
```

## Delivering results

Name output files after what they contain. When you extract data, say how many pages, tables or fields you processed and point out anything that needs a human check. Examples are a table that spans pages, a low-confidence OCR page or a form field the script couldn't match.

---

## Bundled files

The skill's supporting files, verbatim. Unpack them with the command at the top, or read one here. Line is where each file starts in this document.

| File | Size | Line |
|---|---:|---:|
| `references/creating-pdfs.md` | 7.0 KB | 154 |
| `references/editing-and-assembly.md` | 7.6 KB | 294 |
| `references/forms.md` | 8.0 KB | 482 |
| `references/reading-and-extraction.md` | 7.5 KB | 619 |
| `references/research-papers.md` | 6.0 KB | 758 |
| `scripts/pdf_forms.py` | 10.2 KB | 857 |
| `scripts/pdf_images.py` | 3.1 KB | 1131 |
| `scripts/pdf_inspect.py` | 7.8 KB | 1223 |
| `scripts/pdf_ocr.py` | 6.0 KB | 1436 |
| `scripts/pdf_overlay_text.py` | 7.3 KB | 1575 |
| `scripts/pdf_pages.py` | 6.5 KB | 1775 |
| `scripts/pdf_render.py` | 5.8 KB | 1955 |
| `scripts/pdf_tables.py` | 8.5 KB | 2119 |
| `scripts/pdf_text.py` | 6.2 KB | 2332 |
| `LICENSE` | 1.1 KB | 2499 |

### `references/creating-pdfs.md`

<!-- bundle-file: references/creating-pdfs.md sha256=960b867c14f4a1524742df95697d8d984d24aa6d6bd1f52135aa2fea8d595cb5 -->
````markdown
# Creating new PDFs

Pick the route by what the content looks like:

| Content | Route |
|---|---|
| Structured report: headings, paragraphs, tables, figures | **reportlab platypus** (section 1) |
| Exact positioning: certificates, labels, letterhead, sample tags | **reportlab canvas** (section 2) |
| Content that already exists as Markdown or text | **pandoc** (section 3) |
| Content that already exists as HTML/CSS | **weasyprint** or a headless browser (section 4) |
| Equation-heavy academic text | **LaTeX** via pandoc or `pdflatex` (section 3) |
| One page per row of data (mail merge) | canvas in a loop, or fill one template (section 5) |

Whichever route you take, render page 1 (`scripts/pdf_render.py out.pdf --pages 1`) and check it before you deliver.

## 1. reportlab platypus: flowing documents

```python
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                Image, PageBreak, KeepTogether)

styles = getSampleStyleSheet()
body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=10, leading=13, spaceAfter=6)

def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(A4[0] - 20*mm, 12*mm, f"Page {doc.page}")
    canvas.restoreState()

doc = SimpleDocTemplate("lab_report.pdf", pagesize=A4, title="Triaxial Test Report",
                        author="GEOTECH-LAB", leftMargin=20*mm, rightMargin=20*mm,
                        topMargin=20*mm, bottomMargin=20*mm)
story = [
    Paragraph("Triaxial Test Report", styles["Title"]),
    Paragraph("Project: Lot 12 Retaining Wall &nbsp;·&nbsp; Date: 3 October 2026", body),
    Spacer(1, 6*mm),
    Paragraph("1 Results", styles["Heading2"]),
]
data = [["Sample", "Depth (m)", "c′ (kPa)", "φ′ (°)"],
        ["BH1-S1", "1.5", "12.3", "31.5"],
        ["BH1-S2", "3.0", "8.7", "33.0"]]
t = Table(data, colWidths=[35*mm, 30*mm, 30*mm, 30*mm], repeatRows=1)
t.setStyle(TableStyle([
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eef5")),
    ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.black),
    ("LINEBELOW", (0, -1), (-1, -1), 0.8, colors.black),
    ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
    ("FONTSIZE", (0, 0), (-1, -1), 9),
]))
story += [t, Spacer(1, 4*mm),
          KeepTogether([Image("stress_path.png", width=140*mm, height=90*mm),
                        Paragraph("Figure 1. Effective stress paths.", body)])]
doc.build(story, onFirstPage=footer, onLaterPages=footer)
```

Notes:
- **Characters like φ′, σ′ and γ.** The built-in fonts (Helvetica, Times, Courier) only cover Latin-1. Characters outside it can come out as boxes or in the wrong glyph, or they can't be copied as text. Register a TTF and use it in your styles:
  ```python
  from reportlab.pdfbase import pdfmetrics
  from reportlab.pdfbase.ttfonts import TTFont
  pdfmetrics.registerFont(TTFont("DejaVu", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
  pdfmetrics.registerFont(TTFont("DejaVu-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
  body.fontName = "DejaVu"
  ```
- Paragraph text is mini-HTML. Use `<b>`, `<i>`, `<sub>`, `<super>`, `<font color="#c00">` and `<br/>`, and escape `&`, `<` and `>`.
- `repeatRows=1` repeats the header row when a table breaks across pages. `KeepTogether` keeps a figure with its caption.
- For figures from matplotlib, save them as PNG at 200–300 dpi. Or save them as PDF or SVG and embed with `svglib` to keep them as vector graphics.

## 2. reportlab canvas: exact positioning

```python
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas

c = canvas.Canvas("certificate.pdf", pagesize=landscape(A4))
W, H = landscape(A4)
c.setLineWidth(3); c.rect(30, 30, W - 60, H - 60)
c.setFont("Times-Bold", 34); c.drawCentredString(W / 2, H - 150, "Certificate of Completion")
c.setFont("Times-Roman", 18); c.drawCentredString(W / 2, H - 210, "awarded to")
c.setFont("Times-BoldItalic", 28); c.drawCentredString(W / 2, H - 260, "Jane Smith")
c.drawImage("logo.png", 50, H - 120, width=80, preserveAspectRatio=True, mask="auto")
c.showPage()          # end page; repeat drawing for more pages
c.save()
```

The origin is the bottom-left and units are points (`from reportlab.lib.units import mm, cm` for metric). Text is drawn on its baseline.

## 3. pandoc: from Markdown or text

```bash
pandoc notes.md -o notes.pdf                                   # uses LaTeX (pdflatex) if installed
pandoc notes.md -o notes.pdf --pdf-engine=xelatex -V mainfont="DejaVu Serif" -V geometry:margin=2cm
pandoc notes.md -o notes.pdf --pdf-engine=weasyprint --css style.css   # no LaTeX needed
pandoc paper.md --citeproc --bibliography refs.bib --csl apa.csl -o paper.pdf
```

Use xelatex or lualatex whenever the text has non-Latin scripts or Unicode symbols. pdflatex fails on them. Check which engines are installed with `which pdflatex xelatex weasyprint wkhtmltopdf`. If none are, use section 1.

## 4. HTML and CSS to PDF

```python
from weasyprint import HTML, CSS
HTML("report.html").write_pdf("report.pdf",
    stylesheets=[CSS(string="@page { size: A4; margin: 18mm } body { font-family: 'DejaVu Sans'; }")])
```

WeasyPrint supports `@page` rules, page counters (`content: counter(page)`), and `break-before` and `break-inside`. If a page relies on JavaScript, as dashboards and charts often do, print it with headless Chromium instead (Playwright: `page.pdf(path="out.pdf", format="A4", print_background=True)`).

## 5. One page per record (mail merge)

There are two good options.

- **Draw each record** with the canvas (section 2), calling `c.showPage()` after each record. Write either one file per record or a single combined file.
- **Fill a template.** If the user has a fillable form, call `pdf_forms.py fill` once per row with a generated values file. For a flat design, use `pdf_overlay_text.py`. Then merge the results with `pdf_pages.py merge` if they want one file.

```python
import csv, json, subprocess
for i, row in enumerate(csv.DictReader(open("samples.csv")), start=1):
    json.dump({"sample_id": row["id"], "depth": row["depth"]}, open("v.json", "w"))
    subprocess.run(["python", "scripts/pdf_forms.py", "fill", "label_template.pdf", "v.json",
                    "-o", f"labels/label_{i:03d}.pdf", "--flatten"], check=True)
```

## Accessibility and archiving

- Always set a title and author (`SimpleDocTemplate(title=..., author=...)`, or `add_metadata` in pypdf).
- If the user needs PDF/A for archiving, convert with Ghostscript (`gs -dPDFA=2 -dPDFACompatibilityPolicy=1 -sDEVICE=pdfwrite -sColorConversionStrategy=RGB -o out_pdfa.pdf in.pdf`), or with `ocrmypdf --output-type pdfa`. Then validate the result with veraPDF if it's available.
- Fully tagged, accessible PDFs (PDF/UA) are beyond reportlab. Tell the user that when it matters, and suggest exporting from Word or LibreOffice with tagging enabled.
````

### `references/editing-and-assembly.md`

<!-- bundle-file: references/editing-and-assembly.md sha256=0617b7375a5aebdab80ae69c8f3e60a132bf057521ab19809f03ef0af055d281 -->
````markdown
# Editing and assembling PDFs

Page operations such as merge, split, extract, delete, rotate and reorder are covered by `scripts/pdf_pages.py`. This file has tested snippets for everything else. Write to a new file every time, never over the input.

## Contents
1. Watermarks and stamps
2. Page numbers and running footers
3. Metadata, bookmarks, attachments
4. Crop, resize, n-up
5. Encrypt and decrypt
6. Compress and repair
7. Redaction (do it properly)

## 1. Watermarks and stamps

To put a one-off mark on a few pages, use `scripts/pdf_overlay_text.py` with `opacity` and `rotate`.

To put the same stamp on every page, build it once and merge it:

```python
import io
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

reader = PdfReader("report.pdf")
w0, h0 = float(reader.pages[0].mediabox.width), float(reader.pages[0].mediabox.height)
buf = io.BytesIO()
c = canvas.Canvas(buf, pagesize=(w0, h0))
c.setFillColorRGB(0.8, 0, 0); c.setFillAlpha(0.15)          # colour first, then alpha
c.setFont("Helvetica-Bold", 72)
c.translate(w0 / 2, h0 / 2); c.rotate(35); c.drawCentredString(0, 0, "CONFIDENTIAL")
c.save()
stamp = PdfReader(io.BytesIO(buf.getvalue())).pages[0]

writer = PdfWriter(clone_from=reader)
for page in writer.pages:
    page.merge_page(stamp, over=True)   # over=False puts it underneath the content
writer.write("report_watermarked.pdf")
```

When the pages vary in size, build one stamp per size, or scale each one with `stamp.scale_to(w, h)` on a copy.

To use an existing logo or letterhead PDF as the stamp, read its first page and merge it the same way.

## 2. Page numbers and running footers

```python
import io
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

reader = PdfReader("in.pdf")
writer = PdfWriter(clone_from=reader)
n = len(writer.pages)
for i, page in enumerate(writer.pages, start=1):
    w, h = float(page.mediabox.width), float(page.mediabox.height)
    buf = io.BytesIO(); c = canvas.Canvas(buf, pagesize=(w, h))
    c.setFont("Helvetica", 9); c.drawCentredString(w / 2, 20, f"Page {i} of {n}")
    c.drawString(40, 20, "Geotechnical Investigation Report — Draft")
    c.save()
    page.merge_page(PdfReader(io.BytesIO(buf.getvalue())).pages[0])
writer.write("in_numbered.pdf")
```

Skip the cover page with `if i == 1: continue`. To number from the second page, use `i - 1`.

## 3. Metadata, bookmarks, attachments

```python
from pypdf import PdfReader, PdfWriter
writer = PdfWriter(clone_from=PdfReader("in.pdf"))
writer.add_metadata({"/Title": "Site Investigation – Lot 12", "/Author": "R. Kalatehjari", "/Subject": "Geotech report"})

# bookmarks (0-based page index); nest by passing parent
ch1 = writer.add_outline_item("1 Introduction", 0)
writer.add_outline_item("1.1 Scope", 1, parent=ch1)

# attach a data file (e.g. the raw CSV behind a figure)
with open("raw_data.csv", "rb") as fh:
    writer.add_attachment("raw_data.csv", fh.read())
writer.write("out.pdf")
```

To read attachments, use `PdfReader("x.pdf").attachments`, a dict of name to a list of bytes.

## 4. Crop, resize, n-up

```python
from pypdf import PdfReader, PdfWriter, PaperSize, Transformation
from pypdf.generic import RectangleObject

r = PdfReader("in.pdf"); w = PdfWriter()
for p in r.pages:
    # crop: what viewers show and print (points, origin bottom-left)
    p.cropbox = RectangleObject((36, 36, float(p.mediabox.width) - 36, float(p.mediabox.height) - 36))
    w.add_page(p)
w.write("cropped.pdf")

# resize everything to A4, scaling the content to fit
r = PdfReader("in.pdf"); w = PdfWriter()
for p in r.pages:
    p.scale_to(PaperSize.A4.width, PaperSize.A4.height)
    w.add_page(p)
w.write("a4.pdf")

# 2-up (two pages side by side on landscape A4)
r = PdfReader("in.pdf"); w = PdfWriter()
W, H = PaperSize.A4.height, PaperSize.A4.width
for i in range(0, len(r.pages), 2):
    sheet = w.add_blank_page(W, H)
    for slot, j in enumerate((i, i + 1)):
        if j >= len(r.pages):
            break
        src = r.pages[j]
        s = min((W / 2) / float(src.mediabox.width), H / float(src.mediabox.height))
        sheet.merge_transformed_page(src, Transformation().scale(s).translate(slot * W / 2, 0))
w.write("2up.pdf")
```

## 5. Encrypt and decrypt

```python
from pypdf import PdfReader, PdfWriter
w = PdfWriter(clone_from=PdfReader("in.pdf"))
w.encrypt(user_password="open-me", owner_password="admin-only", algorithm="AES-256")
w.write("locked.pdf")

r = PdfReader("locked.pdf"); r.decrypt("open-me")
PdfWriter(clone_from=r).write("unlocked.pdf")
```

**Restrict editing without a password to open.** Use this for "send it so nobody can change it". The file opens normally, but a compliant viewer won't let anyone edit it, fill it, annotate it or move its pages. Printing and copying text are still allowed:

```python
import secrets
from pypdf import PdfReader, PdfWriter
from pypdf.constants import UserAccessPermissions as P
w = PdfWriter(clone_from=PdfReader("form_filled_flat.pdf"))
allowed = P.PRINT | P.PRINT_TO_REPRESENTATION | P.EXTRACT | P.EXTRACT_TEXT_AND_GRAPHICS
w.encrypt(user_password="", owner_password=secrets.token_urlsafe(16), algorithm="AES-256", permissions_flag=allowed)
w.write("form_final.pdf")
```

Explain the limits to the user. Permission flags are honoured by mainstream viewers, but a determined person with other tools can remove them. Real tamper-evidence needs a digital signature (a certificate-based signature made in Acrobat or a similar signing service). Give the owner password to the user if they might need to edit the file later, or say that it was random and discarded.

AES needs the `cryptography` package (`pip install cryptography`). You can also use the CLI: `qpdf --encrypt open-me admin-only 256 -- in.pdf locked.pdf` or `qpdf --decrypt --password=open-me locked.pdf unlocked.pdf`.

Only remove a password when the user owns the document or has the right to unlock it. If they don't know the password, say that you can't open the file. Don't attempt to crack it.

## 6. Compress and repair

Try these in order, lightest first, and report the size before and after:

```bash
# 1) lossless: recompress streams and pack objects (often 10–40% on generated PDFs)
python -c "import pikepdf; pikepdf.open('in.pdf').save('small.pdf', compress_streams=True, object_stream_mode=pikepdf.ObjectStreamMode.generate)"
#    or: qpdf --compress-streams=y --object-streams=generate in.pdf small.pdf

# 2) lossy: downsample images (big wins on scans and photo-heavy reports)
gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.6 -dPDFSETTINGS=/ebook -dNOPAUSE -dBATCH -dQUIET -sOutputFile=small.pdf in.pdf
#    /screen ≈ 72 dpi (smallest), /ebook ≈ 150 dpi (good default), /printer ≈ 300 dpi
```

Ghostscript rewrites the whole file. Form fields can be lost, and text may be re-encoded. Check the result with `pdf_inspect.py` and `pdf_render.py`. Never use it on forms that still need filling.

Repair a damaged file ("xref table broken", "EOF marker not found"):

```bash
qpdf in.pdf repaired.pdf            # qpdf reconstructs the cross-reference table
python -c "import pikepdf; pikepdf.open('in.pdf').save('repaired.pdf')"
```

## 7. Redaction (do it properly)

Drawing a black box over text does **not** remove it. The text can still be selected and extracted. Real redaction has to remove the content:

1. Rasterise the affected pages (`pdf_render.py --dpi 200`).
2. Paint the boxes onto the PNG with PIL.
3. Rebuild those pages from the images. For example, `img.save("page.pdf", resolution=200)`, then put the page back in with `pdf_pages.py`.
4. Check with `pdf_text.py` that the redacted strings are gone.

Tell the user that redacted pages become images, so their text is no longer selectable. They can OCR the pages afterwards if they need search.
````

### `references/forms.md`

<!-- bundle-file: references/forms.md sha256=1ab1bff390b38bb561a04ee683356221fc863cd629f38aec36d49e6fed9a07fe -->
````markdown
# Filling PDF forms

First, find out which kind of form you have:

```bash
python scripts/pdf_inspect.py form.pdf      # look at the "Form:" line
```

- **"N fields"** means a fillable (AcroForm) form. Go to section A.
- **"no fillable fields"** means a printed-style form with lines and boxes drawn on the page. Go to section B.
- **"[XFA present]"** means a dynamic form built in Adobe LiveCycle. See section C.

## A. Fillable forms

### 1. List the fields

```bash
python scripts/pdf_forms.py list form.pdf -o fields.json
```

Each entry includes `name`, `type`, `value`, `options`, `widgets` (page and rectangle), and, where the form has them, `tooltip`, `required`, `readonly` and `max_length`. For checkboxes and radio buttons, each widget also has a `state`, which is the option that box represents. Radio buttons often have no printed label of their own. Match each `state` to its position (`rect`) on the rendered page before you choose one. Field names are often cryptic, like `Text7` or `topmostSubform[0].Page1[0].f1_03[0]`. To work out which label each one belongs to, look at the field's `tooltip` and its rectangle position. If that isn't enough, render the page (`pdf_render.py`) and match the rectangle to the label next to it.

### 2. Write the values

Write a JSON file that maps the fully qualified name to a value. The names below are only an illustration. Always use the names that `list` prints for the actual form:

```json
{
  "applicant.name": "Roo Kalatehjari",
  "agree": true,
  "test_method": "direct_shear",
  "soil_type": "sand"
}
```

Each type takes a different kind of value:

| Type | Value |
|---|---|
| text | any string. Dates go in the format the form asks for |
| checkbox | `true` or `false`, or the exact on-state name from `options` |
| radio | exactly one of the `options` |
| choice (dropdown or list) | exactly one of the `options` |
| signature or pushbutton | can't be filled with a value. To sign, overlay an image of the signature (section B) |

A short name is accepted when it's unambiguous: `"name"` works if only one field ends in `.name`. Otherwise the script stops and lists the candidates.

### 3. Fill, check, deliver

```bash
python scripts/pdf_forms.py fill form.pdf values.json -o form_filled.pdf
python scripts/pdf_render.py form_filled.pdf --pages 1     # look at it
```

The script checks every value before it writes anything. Unknown names, invalid options and text over `max_length` are all reported together, and no output is produced. Fix the JSON and run it again. Use `--ignore-unknown` only when you deliberately skip fields.

`--flatten` (or the separate `flatten` subcommand) burns the values into the page. The fields disappear and the file looks the same in every viewer. Flatten when the user wants a final copy to send. Don't flatten when they still need to edit, sign or submit it through a portal.

- To confirm that flattening worked, run `pdf_inspect.py` on the output. It should say "Form: no fillable fields". Then render the pages.
- Text and dropdown fields can lose their shaded box or border when flattened, leaving the value as plain text. Ticks and radio dots keep their outlines. Mention this if it's visible.
- **Flattening alone doesn't make a file uneditable.** Any PDF editor can still change it. When the user asks for a copy that "nobody can edit", also add an owner password that restricts changes (editing-and-assembly.md §5). Tell them it's a deterrent, not a security measure, and that real tamper-evidence needs a digital signature.
- If a field already has a value, the script prints a note when it replaces it. Mention any replaced value that the user didn't ask to change.

### Why values sometimes "disappear"

Some viewers, notably macOS Preview and some browsers, show only a field's stored appearance, not its value. The fill script sets `NeedAppearances` so that viewers regenerate the appearance. If the user reports blank fields anyway, flattening fixes it (it generates appearance streams with pikepdf or qpdf). `pdf_render.py` turns on form drawing, so its PNG shows what a compliant viewer displays.

## B. Forms without fields (flat forms)

### 1. Find the coordinates

```bash
python scripts/pdf_render.py form.pdf --pages 1 --grid --grid-step 25
```

Open the PNG. The red labels across the top are x, and the blue labels down the left are y. Both are in points, with the origin at the bottom-left. Text sits on its baseline, so set y about 2–3 pt above the line the user writes on.

For better precision, ask pdfplumber where the labels are, then place values relative to them. A character's baseline is the last number of its `matrix`. Don't use `bottom`, because it includes the descender and is about 2–3 pt lower than the baseline:

```python
import pdfplumber
with pdfplumber.open("form.pdf") as pdf:
    p = pdf.pages[0]
    for w in p.extract_words():
        if w["text"].startswith(("Name", "Date", "Borehole")):
            first = next(c for c in p.chars if abs(c["x0"] - w["x0"]) < 0.5 and abs(c["top"] - w["top"]) < 0.5)
            print(w["text"], "x1=", round(w["x1"], 1), "baseline_y=", round(first["matrix"][5], 1))
```

Start a value about 5–10 pt after the label's `x1`, on the same baseline, or 1–2 pt higher if there's an underline to clear.

### 2. Write the spec and overlay it

```json
[
  {"page": 1, "x": 140, "y": 731, "text": "Roo Kalatehjari"},
  {"page": 1, "x": 140, "y": 706, "text": "03/10/2026"},
  {"page": 1, "x": 61,  "y": 652, "type": "check", "size": 9},
  {"page": 1, "x": 120, "y": 600, "text": "Free-text answer that needs wrapping…", "max_width": 380, "size": 9},
  {"page": 2, "x": 380, "y": 95,  "type": "image", "path": "signature.png", "width": 110}
]
```

```bash
python scripts/pdf_overlay_text.py form.pdf spec.json -o form_filled.pdf
python scripts/pdf_render.py form_filled.pdf --pages 1,2
```

Look at the render. Nudge x and y by a few points and run it again until every value sits cleanly on its line or in its box. Two rounds is normal.

- Text with characters outside Latin-1, such as macrons in Māori names or Persian, Chinese or Greek letters: the script falls back to DejaVu Sans when it's available. For scripts DejaVu doesn't cover, set `"font_file"` to a TTF that does (for example Noto Sans Arabic or Noto Sans CJK).
- Checkboxes: `"type": "check"` draws a tick and `"type": "cross"` draws an X. Their size is in points. By default x and y are the lower-left corner of the mark's square. Add `"center": true` and give the centre of the box instead, which is easier. For a box typed as `[ ]`, the centre is about halfway between the brackets and 3–4 pt above the baseline. Use a size about 1–2 pt smaller than the box.
- Drawn ticks are graphics, so text extraction still shows `[ ]`. If the recipient's system reads the text layer, use `{"text": "X"}` instead, or `"✔"` with a font that has that glyph.
- To check small marks, zoom in with `pdf_render.py out.pdf --pages 1 --dpi 300 --crop x0,y0,x1,y1`. At the default 110 dpi, a tick 1 pt off looks fine.
- Extracting text from an overlaid page can interleave your text with the underscores below it (`_R_o_o_`). That's expected, so judge placement from the render, not from extracted text.
- For a signature image, use a PNG with a transparent background. Only place a signature the user has provided and asked you to use.

## C. XFA forms

XFA forms store the layout in XML, and most libraries can't fill them. Options, best first:

1. Check whether the form also has AcroForm fields ("N fields" alongside XFA). If it does, fill those with `pdf_forms.py`. Many XFA forms carry both.
2. Ask the user to "Print to PDF" from Adobe Reader, which renders XFA, and send you the static copy. Then use section B.
3. Tell the user that the form needs Adobe Acrobat or Reader to fill reliably.

## Checklist before you hand the form over

- Every required field (`"required": true`) has a value.
- Dates, IDs and numbers match the format printed next to the field.
- You looked at the rendered page, not just the JSON.
- The output file name says it's filled (`*_filled.pdf`). The blank original is untouched.
````

### `references/reading-and-extraction.md`

<!-- bundle-file: references/reading-and-extraction.md sha256=11f291fd91786d65eb73cecd9753ce9af1f400c793e22a6bff3d8f899572137a -->
````markdown
# Reading and extracting content

## Contents
1. Choosing a text engine
2. Multi-column layouts
3. Tables
4. Words with coordinates (for custom parsing)
5. Images and figures
6. Scanned PDFs and OCR
7. Common problems

## 1. Choosing a text engine

`scripts/pdf_text.py` wraps three engines. Pick one based on the kind of document:

| Document | Engine and options | Why |
|---|---|---|
| Ordinary prose: letters, reports, articles | `--engine plumber` (default) | Good reading order and handles most fonts |
| Columns of numbers, test certificates, logs | `--layout` (plumber) or `--engine pdftotext --layout` | Keeps columns aligned with spaces, so values stay on their row |
| Very large files where speed matters | `--engine pypdf` | Pure Python with no rendering, so it's fast |
| Two-column journal pages | `--columns 2` | See section 2 |

Every engine prints `=== Page N ===` markers so you can cite pages. Use `--no-markers` to get continuous text.

In Python:

```python
import pdfplumber
with pdfplumber.open("in.pdf") as pdf:
    text = "\n".join((p.extract_text() or "") for p in pdf.pages)
```

## 2. Multi-column layouts

By default, extraction reads straight across the page, so the lines of side-by-side columns get interleaved. `--columns 2` crops each page into equal vertical strips and reads them left to right.

A full-width block at the top of the page, such as the title, authors and DOI on page 1, would be cut in half by the column split. `--header PT` reads the top PT points at full width first, and splits only the area below it into columns. To find PT, render the page with `pdf_render.py --grid`. PT is the page height minus the y value where the columns begin, typically 150–250 on a journal's first page.

```bash
python scripts/pdf_text.py paper.pdf --pages 1 --columns 2 --header 190 -o p1.txt   # title block + abstract columns
python scripts/pdf_text.py paper.pdf --pages 2- --columns 2 -o body.txt              # body pages
```

If the gutter isn't centred, crop by hand:

```python
with pdfplumber.open("paper.pdf") as pdf:
    p = pdf.pages[3]
    left  = p.crop((0, 0, 300, p.height)).extract_text()
    right = p.crop((300, 0, p.width, p.height)).extract_text()
```

To find the gutter, render the page (`pdf_render.py --grid`) and read off the x position.

## 3. Tables

`scripts/pdf_tables.py` uses pdfplumber's table finder.

- `--strategy lines` (default) uses the ruling lines in the PDF. It's the most reliable choice for bordered tables.
- `--strategy text` infers columns from how the text lines up. Use it for borderless tables, the "booktabs" style common in journals. Check the result, because merged headers or wrapped cells can shift columns.
- `--format xlsx` writes one sheet per table. Values that are clearly numbers (12, -3.5, 1,234.5) are stored as numbers. Anything ambiguous stays text, including decimal commas, `12 ± 3` and `5%`.
- A table that continues over a page break comes out as two tables. Join them yourself after checking that the header row repeats.

If neither strategy works, extract words with coordinates (section 4) and group them into rows by their `top` value. camelot (`camelot.read_pdf(path, flavor="lattice"|"stream")`) is a second opinion if it's installed.

Always compare the row and column counts with what the page shows. Say in your answer which tables you checked.

## 4. Words with coordinates

When you need to parse a fixed layout yourself, such as a lab certificate where the value sits to the right of a label:

```python
import pdfplumber
with pdfplumber.open("cert.pdf") as pdf:
    page = pdf.pages[0]
    words = page.extract_words(keep_blank_chars=False, use_text_flow=True)
    # each word: {'text', 'x0', 'x1', 'top', 'bottom', ...}; 'top' is measured from the TOP edge
    label = next(w for w in words if w["text"].startswith("Moisture"))
    same_row = [w for w in words if abs(w["top"] - label["top"]) < 3 and w["x0"] > label["x1"]]
    value = " ".join(w["text"] for w in sorted(same_row, key=lambda w: w["x0"]))
```

You can also search regions: `page.within_bbox((x0, top, x1, bottom)).extract_text()`.

pdfplumber measures `top` from the top edge, while reportlab and pypdf measure y from the bottom. Convert with `y = page.height - top`.

## 5. Images and figures

`scripts/pdf_images.py` saves embedded raster images such as photos, scanned figures and logos, keeping their original format.

Most charts made with matplotlib, Excel, MATLAB or Origin are vector graphics, not embedded images, so `pdf_images.py` won't find them. To capture one, render the page at high DPI and crop it:

```bash
python scripts/pdf_render.py paper.pdf --pages 5 --dpi 300 --out-dir figs
```

```python
from PIL import Image
im = Image.open("figs/paper_p005.png")
scale = 300 / 72                      # pixels per point
x0, top, x1, bottom = 60, 90, 540, 400  # region in points, top measured from the top edge (pdfplumber style)
im.crop((int(x0*scale), int(top*scale), int(x1*scale), int(bottom*scale))).save("figure3.png")
```

To find figure boundaries, look at `page.images`, `page.rects` and `page.curves` in pdfplumber. Or find the caption ("Figure 3") with `extract_words` and take the region above it.

## 6. Scanned PDFs and OCR

`pdf_inspect.py` flags pages with fewer than about 25 characters as likely scans. Then:

```bash
python scripts/pdf_ocr.py scan.pdf -o scan_ocr.pdf --lang eng --sidecar scan.txt
python scripts/pdf_text.py scan_ocr.pdf
```

- If the `ocrmypdf` CLI is installed, the script uses it: original images are kept, pages are deskewed and auto-rotated. Otherwise it falls back to tesseract. In that case, pages that already have text are copied unchanged and only scanned pages are rasterised and rebuilt.
- To get more languages, combine codes like `--lang eng+deu`. Install the language packs too (for example `tesseract-ocr-deu`).
- OCR makes mistakes with subscripts, Greek letters (φ′, σ′, γ), units and tables. Tell the user which values came from OCR and should be checked, especially numbers.
- When a single value matters, such as a DOI, ID, date or test result, check it against the image. Render a zoomed crop (`pdf_render.py scan.pdf --dpi 300 --crop x0,y0,x1,y1`) and read it yourself. OCR often confuses 0/O, 1/l/I and 5/S.
- On multi-column scans, the `--sidecar` text from tesseract usually has the right reading order. Prefer it over running `pdf_text.py` on the OCR output, or use `--columns` and `--header` on the OCR output.
- Without `ocrmypdf`, the fallback rebuilds scanned pages as JPEG images, so expect the file to be somewhat larger than the scan. It reports sizes before and after. If quality matters more than size, use `--lossless`.
- For low-quality scans, a higher `--dpi` (400) helps small print. Above about 400 it rarely helps and is slow.

## 7. Common problems

| Symptom | Likely cause | What to do |
|---|---|---|
| Words run together ("thetriaxialtest") | Spacing is drawn with positioning, not space characters | Try `--engine pdftotext`, or use plumber's `extract_text(x_tolerance=1.5)` |
| `ﬁ`/`ﬂ` ligatures or odd symbols | The font has no ToUnicode map | Post-process with `unicodedata.normalize("NFKC", text)`. If the text is still garbled, OCR the page |
| Text is (cid:123) or gibberish | The font encoding can't be decoded | OCR the page (`pdf_ocr.py --force`) |
| Columns are interleaved | Multi-column layout | `--columns 2` or manual crops |
| Empty text, but the page shows text | A scan, or text drawn as vector outlines | OCR |
| Error about the password | Encrypted | `--password`, or `qpdf --decrypt --password=PW in.pdf out.pdf` |
````

### `references/research-papers.md`

<!-- bundle-file: references/research-papers.md sha256=8d417e1f48bd71ce741cca204f63b23ad0dfa554313aa028f70cd60c0b16fda0 -->
````markdown
# Journal articles, theses and technical reports

Tasks that come up often with academic PDFs: pull out the bibliographic details, read the abstract and sections, extract data tables and figures, build a reference list, or compare several papers.

## Contents
1. Bibliographic details (title, authors, DOI, year)
2. Sections: abstract, methods, conclusions
3. Reference lists
4. Tables and figures with their captions
5. Working across many papers
6. Accuracy rules

## 1. Bibliographic details

```bash
python scripts/pdf_inspect.py paper.pdf --json   # metadata + "dois_found"
```

Metadata is often empty or wrong. Publishers frequently leave a production filename in `/Title`. Use this order of precedence:

1. **DOI.** The first DOI on page 1 is usually the article's own. Later DOIs belong to cited works.
2. **Title.** This is usually the text in the largest font on page 1:
   ```python
   import pdfplumber
   from collections import defaultdict
   with pdfplumber.open("paper.pdf") as pdf:
       p = pdf.pages[0]
       lines = defaultdict(list)
       for ch in p.chars:
           lines[(round(ch["top"]), round(ch["size"], 1))].append(ch)
       biggest = max(size for (_, size) in lines)
       title = " ".join("".join(c["text"] for c in sorted(chs, key=lambda c: c["x0"]))
                        for (top, size), chs in sorted(lines.items()) if size >= biggest - 0.5)
   ```
3. **Authors, journal, year.** Read these from the page-1 header text. Don't guess from the filename.

When the session has web access, resolve the DOI to get authoritative metadata. Use `https://doi.org/<DOI>` with the header `Accept: application/vnd.citationstyles.csl+json`, or the Crossref API. Report any mismatch with what the PDF shows.

## 2. Sections

Extract the text first. Use `--columns 2` on the body pages of two-column journals (see reading-and-extraction.md, section 2). Then split it on heading patterns:

```python
import re
text = open("body.txt", encoding="utf-8").read()
heads = re.compile(r"^\s*(?:\d+(?:\.\d+)*\.?\s+)?(Abstract|Introduction|Background|Methods?|Methodology|"
                   r"Materials and methods|Results|Discussion|Conclusions?|References|Bibliography|"
                   r"Acknowledg(?:e)?ments)\s*$", re.I | re.M)
marks = [(m.start(), m.group(1).title()) for m in heads.finditer(text)]
sections = {name: text[s:(marks[i + 1][0] if i + 1 < len(marks) else len(text))].strip()
            for i, (s, name) in enumerate(marks)}
```

Headings vary by journal ("2. Experimental programme", "Concluding remarks"). If the pattern misses some, list the candidate heading lines before you split. These are short lines in Title Case or with a section number, often bold, which you can check with `page.chars[i]["fontname"]`.

The abstract often has no heading. In that case, take the paragraph between the author block and "Keywords" or "1. Introduction".

On two-column journals, the abstract is usually on page 1, under a full-width title block. Read that page with `--columns 2 --header PT` so the title stays whole and the columns don't interleave. When the abstract itself is full width, which is common, use no `--columns` on page 1 at all. Render page 1 to see which layout you're dealing with.

If the request is ambiguous ("without the other column mixed in" could mean de-interleaved, or one column only), give the most likely reading and say how you read it.

## 3. Reference lists

1. Isolate the text after the last "References" or "Bibliography" heading.
2. Split it into entries:
   - Numbered styles start lines with `[12]` or `12.`. Split on `^\s*\[?\d+[\].]\s`.
   - Author–year styles (Harvard or APA) start each entry with `Surname, X.` or `Surname X`. Split where a new line starts with a capitalised surname followed by initials, and the line before ended with a full stop or a DOI.
3. Re-join hyphenated line breaks (`consoli-\ndation` becomes `consolidation`), but keep real hyphens in compounds ("stress-strain").
4. Pull out DOIs with `10\.\d{4,9}/\S+`, and strip trailing `.,;)`.

Return the result in the format the user wants (a list, BibTeX, RIS or a CSV table). Mark any entries you couldn't parse cleanly rather than quietly dropping them.

## 4. Tables and figures with their captions

- **Tables.** `python scripts/pdf_tables.py paper.pdf --pages N --strategy text`. Journal tables are usually borderless, so use the text strategy. The script finds "Table N …" captions above or below each table. It reports them on screen and in the md and json output. In xlsx output they go on an `Index` sheet. It also lists any cell where a comma was read as a thousands separator ("2,000.5" became 2000.5). Check those against the column's scale, because a decimal comma or a typo is often more likely.
- **Figures.** Embedded photos and micrographs come out with `pdf_images.py`. Plotted charts are vector graphics, so render and crop them instead (reading-and-extraction.md, section 5). Captions sit below the figure.
- **Values read off a chart are estimates.** If the user wants data digitised from a plot, say it's approximate. Give the axis calibration you used and the estimated precision.

## 5. Working across many papers

For literature reviews and comparison tables:

1. Run `pdf_inspect.py --json` on every file first. Note which are scans (they need OCR) and which are encrypted.
2. Extract each paper to its own `.txt` file, with page markers kept for citation.
3. Build the comparison as a table: one row per paper, with columns such as material, test type, sample size, key parameters, main finding, and page reference.
4. Cite page numbers for every extracted claim ("p. 7"), so the user can check them.

## 6. Accuracy rules

- Quote numbers exactly as printed, with units. Keep the paper's symbols (φ′, c′, σ′v, e₀) and note any normalisation you made.
- Never fill gaps from memory. If a value isn't in the PDF, say so.
- Separate what the paper reports from your interpretation.
- OCR'd pages, interleaved columns and tables split across pages are the usual sources of error. Say which of these affected the extraction.
````

### `scripts/pdf_forms.py`

<!-- bundle-file: scripts/pdf_forms.py sha256=b23c4ee60c9dd022e025295a3872d45456b15a6373cb7f35be43f959ed642d9d -->
````python
#!/usr/bin/env python3
"""Work with fillable (AcroForm) PDF forms.

Subcommands:
  list    form.pdf [-o fields.json]
          Every field: name, type, current value, allowed options, page, rect, tooltip.
  fill    form.pdf values.json -o filled.pdf [--flatten] [--ignore-unknown]
          values.json maps field name -> value:
            text      "any string"
            checkbox  true / false   (or the exact on-state name from `list`)
            radio     one of the options listed by `list`
            choice    one of the options listed by `list`
  flatten filled.pdf -o flat.pdf
          Burn field appearances into page content so the fields disappear.
          This stops casual changes in a viewer but is NOT tamper-proof. To also
          restrict editing, add an owner password (see references/editing-and-assembly.md).
          Flattened text fields may lose their coloured box/border; check the render.

For forms WITHOUT fields, use pdf_render.py --grid + pdf_overlay_text.py instead.
"""
import argparse
import json
import shutil
import subprocess
import sys

try:
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import NameObject
except ImportError:
    sys.exit("pypdf is required: pip install pypdf")

TYPE_NAMES = {"/Tx": "text", "/Btn": "button", "/Ch": "choice", "/Sig": "signature"}


def inherited(obj, key):
    while obj is not None:
        if key in obj:
            return obj[key]
        obj = obj.get("/Parent")
        obj = obj.get_object() if obj is not None else None
    return None


def full_name(obj):
    parts = []
    while obj is not None:
        if "/T" in obj:
            parts.append(str(obj["/T"]))
        obj = obj.get("/Parent")
        obj = obj.get_object() if obj is not None else None
    return ".".join(reversed(parts))


def classify(widget):
    ft = inherited(widget, "/FT")
    kind = TYPE_NAMES.get(str(ft), str(ft))
    if kind == "button":
        flags = int(inherited(widget, "/Ff") or 0)
        if flags & (1 << 16):
            kind = "pushbutton"
        elif flags & (1 << 15):
            kind = "radio"
        else:
            kind = "checkbox"
    return kind


def on_states(widget):
    ap = widget.get("/AP")
    if not ap:
        return []
    normal = ap.get_object().get("/N")
    if normal is None or not hasattr(normal.get_object(), "keys"):
        return []
    return [str(k).lstrip("/") for k in normal.get_object().keys() if str(k) != "/Off"]


def collect(reader):
    fields = {}
    for pno, page in enumerate(reader.pages, start=1):
        for ref in page.get("/Annots", []) or []:
            w = ref.get_object()
            if w.get("/Subtype") != "/Widget":
                continue
            name = full_name(w)
            if not name:
                continue
            kind = classify(w)
            f = fields.setdefault(name, {"name": name, "type": kind, "value": None, "options": [], "widgets": []})
            v = inherited(w, "/V")
            if v is not None:
                f["value"] = str(v).lstrip("/") if kind in ("checkbox", "radio") else str(v)
            if kind in ("checkbox", "radio"):
                for s in on_states(w):
                    if s not in f["options"]:
                        f["options"].append(s)
            elif kind == "choice":
                opts = inherited(w, "/Opt") or []
                f["options"] = [str(o[1] if isinstance(o, list) else o) for o in opts]
            tu = inherited(w, "/TU")
            if tu:
                f["tooltip"] = str(tu)
            ff = int(inherited(w, "/Ff") or 0)
            if ff & 1:
                f["readonly"] = True
            if ff & 2:
                f["required"] = True
            if kind == "text" and inherited(w, "/MaxLen"):
                f["max_length"] = int(inherited(w, "/MaxLen"))
            wd = {"page": pno, "rect": [round(float(x), 1) for x in w.get("/Rect", [])]}
            if kind in ("checkbox", "radio"):
                states = on_states(w)
                if states:
                    wd["state"] = states[0]  # which option this particular box/button represents
            f["widgets"].append(wd)
    return list(fields.values())


def cmd_list(a):
    r = PdfReader(a.pdf)
    if r.is_encrypted:
        r.decrypt(a.password or "")
    fields = collect(r)
    if not fields:
        print("No fillable fields. Use pdf_render.py --grid and pdf_overlay_text.py for flat forms.", file=sys.stderr)
        sys.exit(1)
    text = json.dumps(fields, indent=2, ensure_ascii=False)
    if a.output:
        with open(a.output, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"Wrote {len(fields)} field(s) to {a.output}", file=sys.stderr)
    else:
        print(text)


def normalise(field, value):
    """Turn a user value into what pypdf expects; return (value, error)."""
    kind, opts = field["type"], field["options"]
    if kind == "checkbox":
        if isinstance(value, bool) or str(value).lower() in ("true", "false", "yes", "no", "on", "off", "1", "0"):
            truthy = value if isinstance(value, bool) else str(value).lower() in ("true", "yes", "on", "1")
            if not truthy:
                return "/Off", None
            return "/" + (opts[0] if opts else "Yes"), None
        if str(value).lstrip("/") in opts:
            return "/" + str(value).lstrip("/"), None
        return None, f"checkbox accepts true/false or {opts}"
    if kind == "radio":
        v = str(value).lstrip("/")
        if v not in opts:
            return None, f"radio options are {opts}"
        return "/" + v, None
    if kind == "choice":
        v = str(value)
        if opts and v not in opts:
            return None, f"choice options are {opts}"
        return v, None
    if kind in ("pushbutton", "signature"):
        return None, f"{kind} fields can't be filled with a value"
    v = str(value)
    if field.get("max_length") and len(v) > field["max_length"]:
        return None, f"longer than max_length {field['max_length']}"
    return v, None


def flatten_file(src, dst):
    try:
        import pikepdf
        with pikepdf.open(src) as pdf:
            pdf.generate_appearance_streams()
            pdf.flatten_annotations("all")
            if "/AcroForm" in pdf.Root:
                del pdf.Root["/AcroForm"]
            pdf.save(dst)
        return "pikepdf"
    except ImportError:
        pass
    if shutil.which("qpdf"):
        subprocess.run(["qpdf", src, "--generate-appearances", "--flatten-annotations=all", dst], check=True)
        return "qpdf"
    sys.exit("Flattening needs pikepdf (pip install pikepdf) or the qpdf CLI")


def cmd_fill(a):
    r = PdfReader(a.pdf)
    if r.is_encrypted:
        r.decrypt(a.password or "")
    fields = {f["name"]: f for f in collect(r)}
    with open(a.values, encoding="utf-8") as fh:
        wanted = json.load(fh)

    errors, unknown, by_page = [], [], {}
    for name, value in wanted.items():
        f = fields.get(name)
        if f is None:
            # allow the short (last-segment) name when it is unambiguous
            matches = [k for k in fields if k.split(".")[-1] == name]
            if len(matches) == 1:
                f = fields[matches[0]]
            elif matches:
                errors.append(f"'{name}' is ambiguous — use one of {matches}")
                continue
            else:
                unknown.append(name)
                continue
        val, err = normalise(f, value)
        if err:
            errors.append(f"{f['name']}: {err} (got {value!r})")
            continue
        current = f.get("value")
        if current not in (None, "", "Off") and str(val).lstrip("/") != current:
            print(f"Note: {f['name']} was pre-filled with {current!r}; replacing it", file=sys.stderr)
        for wd in f["widgets"]:
            # fully qualified name avoids clashes like applicant.name vs spouse.name
            by_page.setdefault(wd["page"], {})[f["name"]] = val
        if f.get("readonly"):
            print(f"Note: {f['name']} is read-only in the form; value set anyway", file=sys.stderr)

    if unknown and not a.ignore_unknown:
        errors.append(f"unknown field name(s): {unknown} — run `list` to see valid names")
    if errors:
        sys.exit("Not filled:\n  " + "\n  ".join(errors))

    w = PdfWriter(clone_from=r)
    for pno, vals in by_page.items():
        w.update_page_form_field_values(w.pages[pno - 1], vals, auto_regenerate=False)
    w.set_need_appearances_writer(True)

    out_unflat = a.output if not a.flatten else a.output + ".tmp.pdf"
    with open(out_unflat, "wb") as fh:
        w.write(fh)
    if a.flatten:
        engine = flatten_file(out_unflat, a.output)
        import os
        os.remove(out_unflat)
        print(f"Flattened with {engine}", file=sys.stderr)

    # verify by reading back
    check = {f["name"]: f["value"] for f in collect(PdfReader(a.output))} if not a.flatten else None
    filled = sum(len(v) for v in by_page.values())
    print(f"Wrote {a.output}: {len(wanted) - len(unknown)} field(s) set" + (f", skipped unknown {unknown}" if unknown else ""), file=sys.stderr)
    if check is not None:
        mismatched = [n for n, v in wanted.items() if n in check and isinstance(v, str) and fields[n]["type"] == "text" and check[n] != v]
        if mismatched:
            print(f"Warning: read-back mismatch for {mismatched}", file=sys.stderr)
    print("Render a page with pdf_render.py to confirm the values are visible.", file=sys.stderr)


def cmd_flatten(a):
    engine = flatten_file(a.pdf, a.output)
    print(f"Wrote {a.output} (flattened with {engine})", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--password")
    sub = ap.add_subparsers(dest="cmd", required=True)
    l = sub.add_parser("list"); l.add_argument("pdf"); l.add_argument("-o", "--output"); l.set_defaults(fn=cmd_list)
    f = sub.add_parser("fill"); f.add_argument("pdf"); f.add_argument("values"); f.add_argument("-o", "--output", required=True)
    f.add_argument("--flatten", action="store_true"); f.add_argument("--ignore-unknown", action="store_true"); f.set_defaults(fn=cmd_fill)
    fl = sub.add_parser("flatten"); fl.add_argument("pdf"); fl.add_argument("-o", "--output", required=True); fl.set_defaults(fn=cmd_flatten)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
````

### `scripts/pdf_images.py`

<!-- bundle-file: scripts/pdf_images.py sha256=999f56ba0c325774108f6fc35a3335cd6e90f9452bef5b1f536d664d5b849955 -->
````python
#!/usr/bin/env python3
"""Extract embedded images (figures, photos, logos) from a PDF.

Saves each image in its native format where possible (JPEG stays JPEG),
skipping tiny decorations below --min-size pixels on either side.

Note: vector figures (most plots made in matplotlib/Excel/MATLAB and saved as
PDF) are NOT embedded images. To capture those, render the page region:
    python pdf_render.py paper.pdf --pages 4 --dpi 200   # then crop the PNG

Usage:
    python pdf_images.py in.pdf [--pages 2-6] [--out-dir images] [--min-size 64]
"""
import argparse
import os
import sys

try:
    from pypdf import PdfReader
except ImportError:
    sys.exit("pypdf is required: pip install pypdf")


def parse_pages(spec, n):
    if not spec:
        return list(range(n))
    out = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            start, end = (int(a) if a else 1), (int(b) if b else n)
        else:
            start = end = int(part)
        if start < 1 or end > n or start > end:
            sys.exit(f"Page range '{part}' is outside 1-{n}")
        out += [i for i in range(start - 1, end) if i not in out]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("--pages")
    ap.add_argument("-o", "--out-dir", help="default: images/ next to the PDF")
    ap.add_argument("--min-size", type=int, default=64)
    ap.add_argument("--password")
    a = ap.parse_args()

    r = PdfReader(a.pdf)
    if r.is_encrypted and not r.decrypt(a.password or ""):
        sys.exit("PDF is encrypted; pass --password")
    a.out_dir = a.out_dir or os.path.join(os.path.dirname(os.path.abspath(a.pdf)), "images")
    os.makedirs(a.out_dir, exist_ok=True)
    saved, skipped, failed = 0, 0, 0
    for i in parse_pages(a.pages, len(r.pages)):
        try:
            images = r.pages[i].images
        except Exception as exc:
            print(f"page {i + 1}: could not list images ({exc})", file=sys.stderr)
            continue
        for k, im in enumerate(images, start=1):
            try:
                pil = im.image
                if pil is not None and min(pil.size) < a.min_size:
                    skipped += 1
                    continue
                ext = os.path.splitext(im.name)[1].lower() or ".png"
                fn = os.path.join(a.out_dir, f"p{i + 1:03d}_img{k}{ext}")
                with open(fn, "wb") as fh:
                    fh.write(im.data)
                size = f"{pil.size[0]}×{pil.size[1]}" if pil is not None else "?"
                print(f"{fn}  {size}")
                saved += 1
            except Exception as exc:
                failed += 1
                print(f"page {i + 1} image {k}: {exc}", file=sys.stderr)
    print(f"Saved {saved}, skipped {skipped} small, failed {failed}", file=sys.stderr)
    if saved == 0:
        print("No raster images found — figures may be vector graphics; render the page instead.", file=sys.stderr)


if __name__ == "__main__":
    main()
````

### `scripts/pdf_inspect.py`

<!-- bundle-file: scripts/pdf_inspect.py sha256=166d1ff6f1962413a2f2298341a2b5fdcd5858eed9b401b1c2af31b4b5086963 -->
````python
#!/usr/bin/env python3
"""Summarise a PDF so you can choose how to process it.

Reports page count, page sizes, metadata, encryption, text per page (to spot
scans), form fields, images, bookmarks, attachments and DOIs found in the text.

Usage:
    python pdf_inspect.py input.pdf [--json] [--password PW] [--max-pages N]
"""
import argparse
import json
import re
import sys

try:
    from pypdf import PdfReader
except ImportError:
    sys.exit("pypdf is required: pip install pypdf")

DOI_RE = re.compile(r"\b10\.\d{4,9}/[^\s\"<>]+", re.IGNORECASE)
SCAN_THRESHOLD = 25  # pages with fewer extractable characters than this are flagged


def page_size_label(w, h):
    sizes = {"A4": (595, 842), "Letter": (612, 792), "A3": (842, 1191), "Legal": (612, 1008), "A5": (420, 595)}
    for name, (sw, sh) in sizes.items():
        if abs(w - sw) < 3 and abs(h - sh) < 3:
            return f"{name} portrait"
        if abs(w - sh) < 3 and abs(h - sw) < 3:
            return f"{name} landscape"
    return "custom"


def count_images(page):
    try:
        return len(page.images)
    except Exception:
        return None


def walk_outline(outline, reader, depth=0, out=None):
    out = [] if out is None else out
    for item in outline:
        if isinstance(item, list):
            walk_outline(item, reader, depth + 1, out)
        else:
            try:
                pg = reader.get_destination_page_number(item) + 1
            except Exception:
                pg = None
            out.append({"title": str(item.title), "page": pg, "level": depth})
    return out


def inspect(path, password=None, max_pages=None):
    reader = PdfReader(path)
    info = {"file": path, "encrypted": reader.is_encrypted, "decrypted": None}
    if reader.is_encrypted:
        try:
            ok = reader.decrypt(password or "")
            info["decrypted"] = bool(ok)
        except Exception as exc:  # missing crypto backend, etc.
            info["decrypted"] = False
            info["decrypt_error"] = str(exc)
        if not info["decrypted"]:
            info["note"] = "Encrypted and could not be opened. Supply --password, or try: qpdf --decrypt in.pdf out.pdf"
            return info

    n = len(reader.pages)
    info["pages"] = n
    meta = reader.metadata or {}
    info["metadata"] = {k.lstrip("/"): str(v) for k, v in meta.items()} if meta else {}

    pages = []
    dois = []
    limit = n if not max_pages else min(n, max_pages)
    for i in range(limit):
        p = reader.pages[i]
        w, h = float(p.mediabox.width), float(p.mediabox.height)
        rot = int(p.get("/Rotate", 0) or 0)
        try:
            text = p.extract_text() or ""
        except Exception:
            text = ""
        chars = len(text.strip())
        dois.extend((m.group(0).rstrip(".,;)]"), i + 1) for m in DOI_RE.finditer(text))
        n_img = count_images(p)
        pages.append({
            "page": i + 1,
            "width_pt": round(w, 1),
            "height_pt": round(h, 1),
            "size": page_size_label(w, h),
            "rotation": rot,
            "text_chars": chars,
            # little text + at least one image = probably a scan; little text and no image = just a sparse page
            "likely_scanned": chars < SCAN_THRESHOLD and bool(n_img),
            "sparse_text": chars < SCAN_THRESHOLD,
            "images": n_img,
            "annotations": len(p.get("/Annots", []) or []),
        })
    info["pages_detail"] = pages
    if limit < n:
        info["pages_detail_truncated_at"] = limit

    fields = reader.get_fields() or {}
    info["form"] = {
        "has_acroform": "/AcroForm" in reader.trailer["/Root"],
        "field_count": len(fields),
        "field_types": sorted({str(v.get("/FT", "?")) for v in fields.values()}),
        "has_xfa": bool(reader.trailer["/Root"].get("/AcroForm", {}).get("/XFA")) if "/AcroForm" in reader.trailer["/Root"] else False,
    }
    try:
        info["bookmarks"] = walk_outline(reader.outline, reader)
    except Exception:
        info["bookmarks"] = []
    try:
        info["attachments"] = list((reader.attachments or {}).keys())
    except Exception:
        info["attachments"] = []
    seen, out = set(), []
    for d, pg in dois:
        if d.lower() not in seen:
            seen.add(d.lower())
            out.append({"doi": d, "page": pg})
    info["dois_found"] = out[:50]  # in page order; on articles the first one on page 1 is usually the article's own

    scanned = [p["page"] for p in pages if p["likely_scanned"]]
    info["scanned_pages"] = scanned
    if scanned and len(scanned) == len(pages):
        info["advice"] = "No text layer found. OCR it first: python pdf_ocr.py in.pdf -o out.pdf"
    elif scanned:
        info["advice"] = f"{len(scanned)} page(s) look scanned (little text, has an image); OCR them if you need their text."
    return info


def compress_ranges(nums):
    if not nums:
        return "none"
    out, start, prev = [], nums[0], nums[0]
    for x in nums[1:]:
        if x == prev + 1:
            prev = x
            continue
        out.append(f"{start}-{prev}" if start != prev else str(start))
        start = prev = x
    out.append(f"{start}-{prev}" if start != prev else str(start))
    return ",".join(out)


def print_human(info):
    print(f"File: {info['file']}")
    if info.get("note"):
        print(f"Encrypted: yes — {info['note']}")
        return
    print(f"Pages: {info['pages']}" + ("  (encrypted, opened)" if info["encrypted"] else ""))
    sizes = {}
    for p in info["pages_detail"]:
        key = f"{p['size']} ({p['width_pt']}×{p['height_pt']} pt)" + (f", rotated {p['rotation']}°" if p["rotation"] else "")
        sizes.setdefault(key, []).append(p["page"])
    print("Page sizes:")
    for k, v in sizes.items():
        print(f"  {k}: pages {compress_ranges(v)}")
    md = info.get("metadata") or {}
    if md:
        print("Metadata:")
        for k in ("Title", "Author", "Subject", "Creator", "Producer", "CreationDate", "ModDate"):
            if k in md:
                print(f"  {k}: {md[k]}")
    total_chars = sum(p["text_chars"] for p in info["pages_detail"])
    sparse = [p["page"] for p in info["pages_detail"] if p["sparse_text"] and not p["likely_scanned"]]
    print(f"Text layer: {total_chars} characters in total; likely-scanned pages: {compress_ranges(info['scanned_pages'])}"
          + (f"; sparse (little text, no images) pages: {compress_ranges(sparse)}" if sparse else ""))
    imgs = [p["images"] for p in info["pages_detail"] if p["images"] is not None]
    if imgs:
        print(f"Embedded images: {sum(imgs)}")
    f = info["form"]
    if f["field_count"]:
        print(f"Form: {f['field_count']} fields, types {', '.join(f['field_types'])}" + ("  [XFA present]" if f["has_xfa"] else ""))
    else:
        print("Form: no fillable fields")
    if info["bookmarks"]:
        print(f"Bookmarks: {len(info['bookmarks'])} (first: {info['bookmarks'][0]['title']!r})")
    if info["attachments"]:
        print(f"Attachments: {', '.join(info['attachments'])}")
    if info["dois_found"]:
        shown = [f"{d['doi']} (p{d['page']})" for d in info["dois_found"][:5]]
        print(f"DOIs found: {', '.join(shown)}" + (f" … +{len(info['dois_found']) - 5} more" if len(info["dois_found"]) > 5 else ""))
    if info.get("advice"):
        print(f"Advice: {info['advice']}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("--json", action="store_true", help="print JSON instead of a summary")
    ap.add_argument("--password", help="password for encrypted files")
    ap.add_argument("--max-pages", type=int, help="only analyse the first N pages (for very large files)")
    a = ap.parse_args()
    info = inspect(a.pdf, a.password, a.max_pages)
    if a.json:
        print(json.dumps(info, indent=2, ensure_ascii=False))
    else:
        print_human(info)


if __name__ == "__main__":
    main()
````

### `scripts/pdf_ocr.py`

<!-- bundle-file: scripts/pdf_ocr.py sha256=eef45c9877533be64cdb6391f27c50a0334db5e4331d5c02df88ac08b1ce0055 -->
````python
#!/usr/bin/env python3
"""Make scanned PDFs searchable (add an invisible OCR text layer).

Engine choice (automatic):
  1. ocrmypdf CLI, if installed — best quality, keeps original images, deskews.
  2. Fallback: pypdfium2 + tesseract (pytesseract). Pages that already have a
     text layer are copied untouched; scanned pages are rasterised at --dpi and
     rebuilt as image+text pages at the original page size. Rebuilt pages are
     stored as JPEG (--jpeg-quality, default 80; greyscale when the page has no
     colour) to keep the file small; --lossless keeps PNG (much larger files).

For multi-column scans, the --sidecar text (straight from tesseract) usually
has better reading order than extracting from the OCR'd PDF afterwards.

Usage:
    python pdf_ocr.py scan.pdf -o searchable.pdf [--lang eng] [--dpi 300]
                      [--force] [--sidecar text.txt] [--engine auto|ocrmypdf|tesseract]

--lang takes tesseract codes, joined with '+', e.g. eng+deu. List installed
languages with: tesseract --list-langs
"""
import argparse
import io
import os
import shutil
import subprocess
import sys
import tempfile

TEXT_MIN = 25


def run_ocrmypdf(a):
    cmd = ["ocrmypdf", "-l", a.lang, "--output-type", "pdf", "--rotate-pages", "--deskew"]
    cmd.append("--force-ocr" if a.force else "--skip-text")
    if a.sidecar:
        cmd += ["--sidecar", a.sidecar]
    res = subprocess.run(cmd + [a.input, a.output], capture_output=True, text=True)
    if res.returncode not in (0, 6):  # 6 = already has text (with --skip-text that's fine)
        sys.exit(f"ocrmypdf failed ({res.returncode}): {res.stderr.strip()[-800:]}")
    print(f"Wrote {a.output} (ocrmypdf)", file=sys.stderr)


def is_grey(img, tol=12):
    """True if an RGB image has (almost) no colour — sample pixels to stay fast."""
    small = img.resize((min(200, img.width), min(200, img.height)))
    return all(max(p) - min(p) <= tol for p in small.getdata())


def run_tesseract(a):
    try:
        import pypdfium2 as pdfium
        import pytesseract
        from pypdf import PdfReader, PdfWriter
    except ImportError as e:
        sys.exit(f"Fallback OCR needs pypdfium2, pytesseract, pypdf ({e.name} missing) and the tesseract binary")
    if not shutil.which("tesseract"):
        sys.exit("tesseract binary not found (apt install tesseract-ocr / brew install tesseract)")

    reader = PdfReader(a.input)
    doc = pdfium.PdfDocument(a.input)
    writer = PdfWriter()
    sidecar, done, kept = [], 0, 0
    with tempfile.TemporaryDirectory() as tmp:
        for i, page in enumerate(reader.pages):
            existing = (page.extract_text() or "").strip()
            if len(existing) >= TEXT_MIN and not a.force:
                writer.add_page(page)
                sidecar.append(existing)
                kept += 1
                continue
            w_pt, h_pt = float(page.mediabox.width), float(page.mediabox.height)
            img = doc[i].render(scale=a.dpi / 72).to_pil().convert("RGB")
            if is_grey(img):
                img = img.convert("L")
            if a.lossless:
                png = os.path.join(tmp, f"p{i}.png")
                img.save(png, dpi=(a.dpi, a.dpi))
            else:  # tesseract embeds JPEG input as-is, which keeps output size close to the scan's
                png = os.path.join(tmp, f"p{i}.jpg")
                img.save(png, dpi=(a.dpi, a.dpi), quality=a.jpeg_quality, optimize=True)
            pdf_bytes = pytesseract.image_to_pdf_or_hocr(png, extension="pdf", lang=a.lang, config=f"--dpi {a.dpi}")
            new_page = PdfReader(io.BytesIO(pdf_bytes)).pages[0]
            nw, nh = float(new_page.mediabox.width), float(new_page.mediabox.height)
            if abs(nw - w_pt) > 1 or abs(nh - h_pt) > 1:
                new_page.scale_to(w_pt, h_pt)
            writer.add_page(new_page)
            if a.sidecar:
                sidecar.append(pytesseract.image_to_string(png, lang=a.lang, config=f"--dpi {a.dpi}"))
            done += 1
            print(f"  OCR page {i + 1}/{len(reader.pages)}", file=sys.stderr)
    if reader.metadata:
        writer.add_metadata({k: v for k, v in reader.metadata.items() if isinstance(k, str)})
    with open(a.output, "wb") as fh:
        writer.write(fh)
    if a.sidecar:
        with open(a.sidecar, "w", encoding="utf-8") as fh:
            fh.write("\n\f".join(sidecar))
    msg = f"Wrote {a.output}: OCR'd {done} page(s)"
    if kept:
        msg += f", copied {kept} page(s) unchanged because they already had text"
    print(msg + " (tesseract fallback; install ocrmypdf for better results)", file=sys.stderr)
    try:
        print(f"Size: {os.path.getsize(a.input):,} → {os.path.getsize(a.output):,} bytes", file=sys.stderr)
    except OSError:
        pass


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--lang", default="eng")
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--force", action="store_true", help="OCR every page, even ones with text")
    ap.add_argument("--sidecar", help="also write recognised text to this file")
    ap.add_argument("--engine", choices=["auto", "ocrmypdf", "tesseract"], default="auto")
    ap.add_argument("--jpeg-quality", type=int, default=80, help="tesseract fallback: JPEG quality for rebuilt pages")
    ap.add_argument("--lossless", action="store_true", help="tesseract fallback: store rebuilt pages as PNG")
    a = ap.parse_args()
    if os.path.abspath(a.input) == os.path.abspath(a.output):
        sys.exit("Refusing to overwrite the input; choose a different -o")
    if a.engine == "ocrmypdf" or (a.engine == "auto" and shutil.which("ocrmypdf")):
        if not shutil.which("ocrmypdf"):
            sys.exit("ocrmypdf not installed (pip install ocrmypdf, plus tesseract and ghostscript)")
        run_ocrmypdf(a)
    else:
        run_tesseract(a)
    print("Verify: python pdf_text.py " + a.output + " --pages 1", file=sys.stderr)


if __name__ == "__main__":
    main()
````

### `scripts/pdf_overlay_text.py`

<!-- bundle-file: scripts/pdf_overlay_text.py sha256=9c4a34f79f28389f9cf9e3eeb1779eedb66395ad110d252aa46640b842ab1583 -->
````python
#!/usr/bin/env python3
"""Place text, tick marks or images onto existing PDF pages — for forms with
no fillable fields, stamping, annotating figures, adding signatures.

Coordinates are PDF points from the page's BOTTOM-LEFT corner. Find them with:
    python pdf_render.py form.pdf --pages 1 --grid

Spec file (JSON list):
[
  {"page": 1, "x": 120, "y": 705, "text": "Jane Smith"},
  {"page": 1, "x": 120, "y": 680, "text": "Long answer that wraps", "max_width": 300, "size": 9},
  {"page": 1, "x": 430, "y": 612, "type": "check"},
  {"page": 2, "x": 400, "y": 90, "type": "image", "path": "signature.png", "width": 120},
  {"page": 1, "x": 297, "y": 40, "text": "DRAFT", "size": 40, "align": "center",
   "color": "#cc0000", "opacity": 0.3, "rotate": 0}
]
Optional keys: size (default 10), font (Helvetica, Helvetica-Bold, Times-Roman,
Courier…), font_file (a .ttf for non-Latin text), color ("#RRGGBB"),
align (left|center|right), max_width (wrap), leading, opacity, rotate.

Text: x,y is the start of the BASELINE (left end for align=left).
check / cross: x,y is the LOWER-LEFT corner of a size×size square; add
"center": true to give the square's centre instead — easiest for tick boxes.
image: x,y is the lower-left corner.

Usage:
    python pdf_overlay_text.py in.pdf spec.json -o out.pdf
"""
import argparse
import io
import json
import os
import sys

try:
    from pypdf import PdfReader, PdfWriter
    from reportlab.lib.colors import HexColor
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas
except ImportError as e:
    sys.exit(f"Missing dependency ({e.name}): pip install pypdf reportlab")

FALLBACK_TTF = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "C:/Windows/Fonts/arial.ttf",
]
_registered = {}


def font_for(item):
    if item.get("font_file"):
        path = item["font_file"]
    else:
        name = item.get("font", "Helvetica")
        try:
            item.get("text", "").encode("latin-1")
            return name
        except UnicodeEncodeError:
            path = next((p for p in FALLBACK_TTF if os.path.exists(p)), None)
            if not path:
                sys.exit("Text has non-Latin characters; pass \"font_file\" pointing to a .ttf that covers them")
    if path not in _registered:
        fname = "F" + str(len(_registered))
        pdfmetrics.registerFont(TTFont(fname, path))
        _registered[path] = fname
    return _registered[path]


def wrap(text, font, size, max_width):
    lines = []
    for para in text.split("\n"):
        words, cur = para.split(), ""
        for w in words:
            trial = (cur + " " + w).strip()
            if pdfmetrics.stringWidth(trial, font, size) <= max_width or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def draw_item(c, item):
    kind = item.get("type", "text")
    x, y = float(item["x"]), float(item["y"])
    c.saveState()
    color = HexColor(item.get("color", "#000000"))
    c.setFillColor(color)
    c.setStrokeColor(color)
    if "opacity" in item:  # after the colour: setting a colour resets alpha in reportlab
        c.setFillAlpha(float(item["opacity"]))
        c.setStrokeAlpha(float(item["opacity"]))
    if item.get("rotate"):
        c.translate(x, y)
        c.rotate(float(item["rotate"]))
        x, y = 0, 0
    if kind in ("check", "cross") and item.get("center"):
        half = float(item.get("size", 10)) / 2
        x, y = x - half, y - half
    if kind == "check":
        s = float(item.get("size", 10))
        c.setLineWidth(max(1, s / 7))
        p = c.beginPath()
        p.moveTo(x, y + s * 0.5); p.lineTo(x + s * 0.35, y + s * 0.1); p.lineTo(x + s, y + s * 0.9)
        c.drawPath(p, stroke=1, fill=0)
    elif kind == "cross":
        s = float(item.get("size", 10))
        c.setLineWidth(max(1, s / 8))
        c.line(x, y, x + s, y + s); c.line(x, y + s, x + s, y)
    elif kind == "image":
        from reportlab.lib.utils import ImageReader
        img = ImageReader(item["path"])
        iw, ih = img.getSize()
        w = float(item.get("width", iw))
        h = float(item.get("height", w * ih / iw))
        c.drawImage(img, x, y, width=w, height=h, mask="auto")
    else:
        font = font_for(item)
        size = float(item.get("size", 10))
        c.setFont(font, size)
        text = str(item["text"])
        lines = wrap(text, font, size, float(item["max_width"])) if item.get("max_width") else text.split("\n")
        leading = float(item.get("leading", size * 1.2))
        align = item.get("align", "left")
        for n, line in enumerate(lines):
            ly = y - n * leading
            if align == "center":
                c.drawCentredString(x, ly, line)
            elif align == "right":
                c.drawRightString(x, ly, line)
            else:
                c.drawString(x, ly, line)
    c.restoreState()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("spec")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--password")
    a = ap.parse_args()
    if os.path.abspath(a.output) == os.path.abspath(a.pdf):
        sys.exit("Refusing to overwrite the input; choose a different -o")

    with open(a.spec, encoding="utf-8") as fh:
        items = json.load(fh)
    reader = PdfReader(a.pdf)
    if reader.is_encrypted and not reader.decrypt(a.password or ""):
        sys.exit("PDF is encrypted; pass --password")
    n = len(reader.pages)

    by_page = {}
    for it in items:
        p = int(it.get("page", 1))
        if not 1 <= p <= n:
            sys.exit(f"Item {it} refers to page {p}, but the PDF has {n} pages")
        by_page.setdefault(p, []).append(it)

    writer = PdfWriter(clone_from=reader)
    for p, its in by_page.items():
        page = writer.pages[p - 1]
        box = page.mediabox
        w, h = float(box.width), float(box.height)
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=(w, h))
        for it in its:
            draw_item(c, it)
        c.save()
        overlay = PdfReader(io.BytesIO(buf.getvalue())).pages[0]
        if float(box.left) or float(box.bottom):
            from pypdf import Transformation
            page.merge_transformed_page(overlay, Transformation().translate(float(box.left), float(box.bottom)))
        else:
            page.merge_page(overlay)
        rot = int(page.get("/Rotate", 0) or 0)
        if rot:
            print(f"Note: page {p} has /Rotate {rot}; coordinates are in the unrotated page space. Check the render.", file=sys.stderr)

    with open(a.output, "wb") as fh:
        writer.write(fh)
    print(f"Wrote {a.output}: {len(items)} item(s) on page(s) {sorted(by_page)}", file=sys.stderr)
    render = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdf_render.py")
    print(f"Check placement: python {render} {a.output} --pages {','.join(map(str, sorted(by_page)))}", file=sys.stderr)
    print("(Extracted text of overlaid pages can look jumbled; judge placement from the render.)", file=sys.stderr)


if __name__ == "__main__":
    main()
````

### `scripts/pdf_pages.py`

<!-- bundle-file: scripts/pdf_pages.py sha256=f656591bebe476dcecc4662dab5466b95d58f84e02b552e2997778c0bc41340a -->
````python
#!/usr/bin/env python3
"""Page-level PDF operations with pypdf. Inputs are never modified.

Subcommands (page numbers are 1-based; specs like 1-3,7,10-):
  merge   a.pdf b.pdf ... -o out.pdf [--bookmarks]
  split   in.pdf --out-dir dir [--every N | --ranges "1-3,4-9,10-"]
          (no option = one file per page; use ';' between files if a file
          needs several ranges: --ranges "1-2,5;3-4")
  extract in.pdf --pages SPEC -o out.pdf        keep only these pages
  delete  in.pdf --pages SPEC -o out.pdf        drop these pages
  rotate  in.pdf --angle 90 [--pages SPEC] -o out.pdf   (90/180/270, clockwise)
  reorder in.pdf --order "3,1,2,4-" -o out.pdf  (use --reverse to flip order)

For encrypted inputs put --password before the subcommand:
  python pdf_pages.py --password PW extract in.pdf --pages 1 -o out.pdf
"""
import argparse
import os
import sys

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    sys.exit("pypdf is required: pip install pypdf")


def parse_pages(spec, n, allow_dupes=False):
    out = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            start, end = (int(a) if a else 1), (int(b) if b else n)
        else:
            start = end = int(part)
        if start < 1 or end > n or start > end:
            sys.exit(f"Page range '{part}' is outside 1-{n}")
        for i in range(start - 1, end):
            if allow_dupes or i not in out:
                out.append(i)
    return out


def open_reader(path, password):
    r = PdfReader(path)
    if r.is_encrypted and not r.decrypt(password or ""):
        sys.exit(f"{path} is encrypted; pass --password")
    return r


def write(writer, out, src_reader=None):
    if os.path.abspath(out) in INPUTS:
        sys.exit("Refusing to overwrite an input file; choose a different -o")
    if src_reader is not None and src_reader.metadata:
        try:
            writer.add_metadata({k: v for k, v in src_reader.metadata.items() if isinstance(k, str)})
        except Exception:
            pass
    with open(out, "wb") as fh:
        writer.write(fh)
    print(f"Wrote {out} ({len(writer.pages)} pages)", file=sys.stderr)


def subset(reader, idxs):
    w = PdfWriter()
    for i in idxs:
        w.add_page(reader.pages[i])
    return w


def cmd_merge(a):
    w = PdfWriter()
    for path in a.inputs:
        r = open_reader(path, a.password)
        start = len(w.pages)
        w.append(r, import_outline=True)
        if a.bookmarks:
            w.add_outline_item(os.path.splitext(os.path.basename(path))[0], start)
        print(f"  + {path}: {len(r.pages)} pages", file=sys.stderr)
    write(w, a.output)


def cmd_split(a):
    r = open_reader(a.input, a.password)
    n = len(r.pages)
    a.out_dir = a.out_dir or os.path.join(os.path.dirname(os.path.abspath(a.input)), "split")
    os.makedirs(a.out_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(a.input))[0]
    if a.every:
        groups = [list(range(s, min(s + a.every, n))) for s in range(0, n, a.every)]
    elif a.ranges:
        # "1-3,4-9" -> two files; use ';' between files when a file needs several ranges: "1-3,7;4-6"
        sep = ";" if ";" in a.ranges else ","
        groups = [parse_pages(part, n) for part in a.ranges.split(sep) if part.strip()]
    else:
        groups = [[i] for i in range(n)]
    for g in groups:
        contiguous = g == list(range(g[0], g[0] + len(g)))
        if len(g) == 1:
            label = f"p{g[0] + 1:03d}"
        elif contiguous:
            label = f"p{g[0] + 1:03d}-{g[-1] + 1:03d}"
        else:
            label = "p" + "_".join(str(i + 1) for i in g)[:60]
        write(subset(r, g), os.path.join(a.out_dir, f"{base}_{label}.pdf"), r)


def cmd_extract(a):
    r = open_reader(a.input, a.password)
    write(subset(r, parse_pages(a.pages, len(r.pages))), a.output, r)


def cmd_delete(a):
    r = open_reader(a.input, a.password)
    drop = set(parse_pages(a.pages, len(r.pages)))
    keep = [i for i in range(len(r.pages)) if i not in drop]
    if not keep:
        sys.exit("That would delete every page")
    write(subset(r, keep), a.output, r)


def cmd_rotate(a):
    if a.angle % 90:
        sys.exit("--angle must be a multiple of 90")
    r = open_reader(a.input, a.password)
    targets = set(parse_pages(a.pages, len(r.pages))) if a.pages else set(range(len(r.pages)))
    w = PdfWriter()
    for i, p in enumerate(r.pages):
        page = w.add_page(p)
        if i in targets:
            page.rotate(a.angle)
    write(w, a.output, r)


def cmd_reorder(a):
    r = open_reader(a.input, a.password)
    n = len(r.pages)
    order = parse_pages(a.order, n, allow_dupes=True) if a.order else list(range(n))
    if a.reverse:
        order = order[::-1]
    write(subset(r, order), a.output, r)


INPUTS = set()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--password")
    sub = ap.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("merge"); m.add_argument("inputs", nargs="+"); m.add_argument("-o", "--output", required=True)
    m.add_argument("--bookmarks", action="store_true", help="add one bookmark per input file"); m.set_defaults(fn=cmd_merge)
    s = sub.add_parser("split"); s.add_argument("input"); s.add_argument("-o", "--out-dir", help="default: split/ next to the input")
    g = s.add_mutually_exclusive_group(); g.add_argument("--every", type=int); g.add_argument("--ranges"); s.set_defaults(fn=cmd_split)
    e = sub.add_parser("extract"); e.add_argument("input"); e.add_argument("--pages", required=True); e.add_argument("-o", "--output", required=True); e.set_defaults(fn=cmd_extract)
    d = sub.add_parser("delete"); d.add_argument("input"); d.add_argument("--pages", required=True); d.add_argument("-o", "--output", required=True); d.set_defaults(fn=cmd_delete)
    ro = sub.add_parser("rotate"); ro.add_argument("input"); ro.add_argument("--angle", type=int, default=90); ro.add_argument("--pages")
    ro.add_argument("-o", "--output", required=True); ro.set_defaults(fn=cmd_rotate)
    rr = sub.add_parser("reorder"); rr.add_argument("input"); rr.add_argument("--order"); rr.add_argument("--reverse", action="store_true")
    rr.add_argument("-o", "--output", required=True); rr.set_defaults(fn=cmd_reorder)

    a = ap.parse_args()
    for attr in ("inputs", "input"):
        v = getattr(a, attr, None)
        if v:
            INPUTS.update(os.path.abspath(x) for x in (v if isinstance(v, list) else [v]))
    a.fn(a)


if __name__ == "__main__":
    main()
````

### `scripts/pdf_render.py`

<!-- bundle-file: scripts/pdf_render.py sha256=e8b469c0e402e489f906f24fb52af54e336dc8e7103eca453f9baac1440190a7 -->
````python
#!/usr/bin/env python3
"""Render PDF pages to PNG — to check output visually or to locate coordinates.

--grid overlays a labelled grid in PDF points with the origin at the
BOTTOM-LEFT (the coordinate system pdf_overlay_text.py and reportlab use),
so you can read x/y positions for text placement straight off the image.

--crop x0,y0,x1,y1 (PDF points, bottom-left origin) saves only that region —
use it with a higher --dpi (300-400) to inspect small marks such as ticks.

Usage:
    python pdf_render.py in.pdf [--pages 1,3] [--dpi 110] [-o/--out-dir renders]
                         [--grid] [--grid-step 50] [--crop 40,700,300,800]   (default -o: renders/ next to the PDF)
                         [--password PW]
Prints the paths of the PNGs written.
"""
import argparse
import os
import shutil
import subprocess
import sys


def parse_pages(spec, n):
    if not spec:
        return list(range(n))
    out = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            start, end = (int(a) if a else 1), (int(b) if b else n)
        else:
            start = end = int(part)
        if start < 1 or end > n or start > end:
            sys.exit(f"Page range '{part}' is outside 1-{n}")
        out += [i for i in range(start - 1, end) if i not in out]
    return out


def render_pdfium(path, idxs, dpi, password):
    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(path, password=password)
    try:
        doc.init_forms()  # without this, form-field values are not drawn
    except Exception:
        pass
    out = []
    for i in idxs:
        page = doc[i]
        w_pt, h_pt = page.get_size()
        img = page.render(scale=dpi / 72).to_pil()
        out.append((i, img, w_pt, h_pt))
    return out


def render_poppler(path, idxs, dpi, password, tmpdir):
    from PIL import Image
    from pypdf import PdfReader
    r = PdfReader(path)
    if r.is_encrypted:
        r.decrypt(password or "")
    out = []
    for i in idxs:
        prefix = os.path.join(tmpdir, f"_r{i + 1}")
        cmd = ["pdftoppm", "-png", "-r", str(dpi), "-f", str(i + 1), "-l", str(i + 1), "-singlefile"]
        if password:
            cmd += ["-upw", password]
        subprocess.run(cmd + [path, prefix], check=True)
        img = Image.open(prefix + ".png").copy()
        os.remove(prefix + ".png")
        box = r.pages[i].cropbox
        out.append((i, img, float(box.width), float(box.height)))
    return out


def draw_grid(img, w_pt, h_pt, step):
    from PIL import ImageDraw, ImageFont
    img = img.convert("RGB")
    d = ImageDraw.Draw(img, "RGBA")
    sx, sy = img.width / w_pt, img.height / h_pt
    fs = max(10, int(9 * sx))
    try:
        font = ImageFont.load_default(size=fs)
    except TypeError:
        font = ImageFont.load_default()
    x = 0
    while x <= w_pt:
        px = x * sx
        major = x % (step * 2) == 0
        d.line([(px, 0), (px, img.height)], fill=(255, 0, 0, 110 if major else 55), width=1)
        if major:
            d.text((px + 2, 2), str(int(x)), fill=(200, 0, 0, 255), font=font)
        x += step
    y = 0
    while y <= h_pt:
        py = img.height - y * sy  # origin bottom-left
        major = y % (step * 2) == 0
        d.line([(0, py), (img.width, py)], fill=(0, 0, 255, 110 if major else 55), width=1)
        if major:
            d.text((2, max(0, py - fs - 2)), str(int(y)), fill=(0, 0, 200, 255), font=font)
        y += step
    return img


def main():
    class Fmt(argparse.RawDescriptionHelpFormatter, argparse.ArgumentDefaultsHelpFormatter):
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=Fmt)
    ap.add_argument("pdf")
    ap.add_argument("--pages", help="page spec, 1-based (default: all)")
    ap.add_argument("--dpi", type=int, default=110, help="render resolution")
    ap.add_argument("-o", "--out-dir", help="folder for the PNGs (default: renders/ next to the PDF)")
    ap.add_argument("--crop", help="x0,y0,x1,y1 in points (bottom-left origin); save only this region")
    ap.add_argument("--grid", action="store_true")
    ap.add_argument("--grid-step", type=int, default=50, help="grid spacing in points (labels every 2 steps)")
    ap.add_argument("--password")
    a = ap.parse_args()

    a.out_dir = a.out_dir or os.path.join(os.path.dirname(os.path.abspath(a.pdf)), "renders")
    os.makedirs(a.out_dir, exist_ok=True)
    try:
        import pypdfium2 as pdfium
        n = len(pdfium.PdfDocument(a.pdf, password=a.password))
        pages = render_pdfium(a.pdf, parse_pages(a.pages, n), a.dpi, a.password)
    except ImportError:
        if not shutil.which("pdftoppm"):
            sys.exit("Need pypdfium2 (pip install pypdfium2) or poppler's pdftoppm")
        from pypdf import PdfReader
        n = len(PdfReader(a.pdf).pages)
        pages = render_poppler(a.pdf, parse_pages(a.pages, n), a.dpi, a.password, a.out_dir)

    base = os.path.splitext(os.path.basename(a.pdf))[0]
    crop = None
    if a.crop:
        try:
            crop = [float(v) for v in a.crop.split(",")]
            assert len(crop) == 4 and crop[0] < crop[2] and crop[1] < crop[3]
        except (ValueError, AssertionError):
            sys.exit("--crop needs x0,y0,x1,y1 with x0<x1 and y0<y1 (points, bottom-left origin)")
    for i, img, w_pt, h_pt in pages:
        if a.grid:
            img = draw_grid(img, w_pt, h_pt, a.grid_step)
        suffix = "_grid" if a.grid else ""
        if crop:
            sx, sy = img.width / w_pt, img.height / h_pt
            x0, y0, x1, y1 = crop
            img = img.crop((int(x0 * sx), int(img.height - y1 * sy), int(x1 * sx), int(img.height - y0 * sy)))
            suffix += "_crop"
        fn = os.path.join(a.out_dir, f"{base}_p{i + 1:03d}{suffix}.png")
        img.save(fn)
        print(f"{fn}  (page {i + 1}: {w_pt:.0f}×{h_pt:.0f} pt)")


if __name__ == "__main__":
    main()
````

### `scripts/pdf_tables.py`

<!-- bundle-file: scripts/pdf_tables.py sha256=1cccd223aa031c62f3faa0f08f7e16d40c0566b3be5ab6f0265b88af5167c616 -->
````python
#!/usr/bin/env python3
"""Extract tables from a PDF with pdfplumber.

Output formats:
  csv   one CSV per table in --out-dir (default: ./tables)
  xlsx  one workbook (-o), one sheet per table, named p<page>_t<n>, plus an
        'Index' sheet with page and caption ("Table 3. ...") for each
  md    Markdown tables to stdout (or -o) — handy for a quick look
  json  list of {page, index, bbox, rows} to stdout (or -o)

Strategies:
  lines (default)  uses ruling lines drawn in the PDF — best for bordered tables
  text             infers columns from text alignment — for borderless tables

Usage:
    python pdf_tables.py in.pdf [--pages 3-5] [--format csv|xlsx|md|json]
                         [-o out] [--out-dir dir] [--strategy lines|text]
                         [--min-rows 2] [--password PW]
"""
import argparse
import csv
import json
import os
import re
import sys

try:
    import pdfplumber
except ImportError:
    sys.exit("pdfplumber is required: pip install pdfplumber")


def parse_pages(spec, n):
    if not spec:
        return list(range(n))
    out = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            start, end = (int(a) if a else 1), (int(b) if b else n)
        else:
            start = end = int(part)
        if start < 1 or end > n or start > end:
            sys.exit(f"Page range '{part}' is outside 1-{n}")
        out += [i for i in range(start - 1, end) if i not in out]
    return out


def clean(cell):
    if cell is None:
        return ""
    return " ".join(str(cell).split())


def extract(path, pages, strategy, min_rows, password):
    settings = {"vertical_strategy": strategy, "horizontal_strategy": strategy}
    if strategy == "text":
        settings.update({"snap_tolerance": 3, "join_tolerance": 3, "intersection_tolerance": 5})
    found = []
    with pdfplumber.open(path, password=password or None) as pdf:
        for i in parse_pages(pages, len(pdf.pages)):
            page = pdf.pages[i]
            for t_idx, table in enumerate(page.find_tables(table_settings=settings), start=1):
                rows = [[clean(c) for c in row] for row in table.extract()]
                rows = [r for r in rows if any(r)]
                if len(rows) < min_rows:
                    continue
                width = max(len(r) for r in rows)
                rows = [r + [""] * (width - len(r)) for r in rows]
                # drop columns that are empty in every row
                keep = [c for c in range(width) if any(r[c] for r in rows)]
                rows = [[r[c] for c in keep] for r in rows]
                found.append({"page": i + 1, "index": t_idx, "bbox": [round(v, 1) for v in table.bbox],
                              "caption": find_caption(page, table.bbox), "rows": rows})
    return found


CAPTION_RE = re.compile(r"^(Table|Tab\.|TABLE)\s*[A-Z]?\d+", re.I)


def find_caption(page, bbox, reach=60):
    """Return the 'Table N ...' line just above (or failing that, below) a table, else ''."""
    x0, top, x1, bottom = bbox
    words = page.extract_words(keep_blank_chars=True, use_text_flow=True)
    lines = {}
    for w in words:
        lines.setdefault(round(w["top"]), []).append(w)
    candidates = []
    for t, ws in lines.items():
        text = " ".join(w["text"] for w in sorted(ws, key=lambda w: w["x0"])).strip()
        if not CAPTION_RE.match(text):
            continue
        b = max(w["bottom"] for w in ws)
        if 0 <= top - b <= reach:
            candidates.append((top - b, text))
        elif 0 <= t - bottom <= reach:
            candidates.append((t - bottom + reach, text))  # below: lower priority
    return min(candidates)[1] if candidates else ""


def to_markdown(t):
    rows = t["rows"]
    esc = lambda s: s.replace("|", "\\|")
    head = "| " + " | ".join(esc(c) for c in rows[0]) + " |"
    sep = "| " + " | ".join("---" for _ in rows[0]) + " |"
    body = ["| " + " | ".join(esc(c) for c in r) + " |" for r in rows[1:]]
    cap = f" — {t['caption']}" if t.get("caption") else ""
    return f"**Page {t['page']}, table {t['index']}**{cap} ({len(rows)} rows × {len(rows[0])} cols)\n\n" + "\n".join([head, sep] + body)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("--pages")
    ap.add_argument("--format", choices=["csv", "xlsx", "md", "json"], default="csv")
    ap.add_argument("-o", "--output", help="output file (xlsx/md/json)")
    ap.add_argument("--out-dir", help="directory for CSV files (default: tables/ next to the PDF)")
    ap.add_argument("--strategy", choices=["lines", "text"], default="lines")
    ap.add_argument("--min-rows", type=int, default=2)
    ap.add_argument("--password")
    a = ap.parse_args()

    tables = extract(a.pdf, a.pages, a.strategy, a.min_rows, a.password)
    if not tables:
        hint = " Try --strategy text for borderless tables." if a.strategy == "lines" else ""
        print(f"No tables found.{hint} If the page is a scan, OCR it first.", file=sys.stderr)
        sys.exit(1)

    if a.format == "csv":
        a.out_dir = a.out_dir or os.path.join(os.path.dirname(os.path.abspath(a.pdf)), "tables")
        os.makedirs(a.out_dir, exist_ok=True)
        for t in tables:
            fn = os.path.join(a.out_dir, f"page{t['page']:03d}_table{t['index']}.csv")
            with open(fn, "w", newline="", encoding="utf-8") as fh:
                csv.writer(fh).writerows(t["rows"])
        print(f"Wrote {len(tables)} CSV file(s) to {a.out_dir}/", file=sys.stderr)
    elif a.format == "xlsx":
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font
        except ImportError:
            sys.exit("openpyxl is required for xlsx: pip install openpyxl")
        out = a.output or os.path.splitext(os.path.abspath(a.pdf))[0] + "_tables.xlsx"
        wb = Workbook()
        idx = wb.active
        idx.title = "Index"
        idx.append(["Sheet", "Page", "Caption", "Rows", "Cols"])
        for t in tables:
            name = f"p{t['page']}_t{t['index']}"[:31]
            idx.append([name, t["page"], t.get("caption", ""), len(t["rows"]), len(t["rows"][0])])
            ws = wb.create_sheet(name)
            for r_i, r in enumerate(t["rows"], start=1):
                vals = [_num(c) for c in r]
                for c_i, (raw, v) in enumerate(zip(r, vals), start=1):
                    if isinstance(v, (int, float)) and "," in raw:
                        THOUSANDS_SEEN.append(f"{name}!{ws.cell(row=r_i, column=c_i).column_letter}{r_i}: '{raw}' -> {v}")
                ws.append(vals)
            for cell in ws[1]:
                cell.font = Font(bold=True)
            for col in ws.columns:
                ws.column_dimensions[col[0].column_letter].width = min(60, max(8, max(len(str(c.value or "")) for c in col) + 2))
        for cell in idx[1]:
            cell.font = Font(bold=True)
        idx.column_dimensions["C"].width = 60
        wb.save(out)
        print(f"Wrote {len(tables)} table(s) to {out} (sheet 'Index' lists pages and captions)", file=sys.stderr)
        if THOUSANDS_SEEN:
            print("Check: these cells had a comma read as a thousands separator:", file=sys.stderr)
            for line in THOUSANDS_SEEN[:20]:
                print("  " + line, file=sys.stderr)
    else:
        text = "\n\n".join(to_markdown(t) for t in tables) if a.format == "md" else json.dumps(tables, indent=2, ensure_ascii=False)
        if a.output:
            with open(a.output, "w", encoding="utf-8") as fh:
                fh.write(text + "\n")
            print(f"Wrote {len(tables)} table(s) to {a.output}", file=sys.stderr)
        else:
            print(text)

    for t in tables:
        cap = f"  [{t['caption'][:60]}]" if t.get("caption") else ""
        print(f"  page {t['page']} table {t['index']}: {len(t['rows'])}×{len(t['rows'][0])}{cap}", file=sys.stderr)


THOUSANDS_SEEN = []
_PLAIN = re.compile(r"^-?\d+(\.\d+)?$")
_THOUSANDS = re.compile(r"^-?\d{1,3}(,\d{3})+(\.\d+)?$")


def _num(s):
    """Store numeric-looking cells as numbers so Excel can compute with them.

    Only unambiguous forms are converted: 12, -3.5, 1,234.5. Anything else
    (e.g. '1,5' decimal comma, '12 ± 3', '5%') stays text so nothing is silently altered.
    """
    t = s.replace("−", "-").strip()
    if _PLAIN.match(t) or _THOUSANDS.match(t):
        t = t.replace(",", "")
        return float(t) if "." in t else int(t)
    return s


if __name__ == "__main__":
    main()
````

### `scripts/pdf_text.py`

<!-- bundle-file: scripts/pdf_text.py sha256=b57bc372a622af2597dad62d932584ae87edcd848bc10a5332cadd98dfc3b75c -->
````python
#!/usr/bin/env python3
"""Extract text from a PDF, page by page.

Engines:
  plumber   (default) pdfplumber, good reading order, supports --layout and --columns
  pypdf     fast, no extra dependencies beyond pypdf
  pdftotext poppler's CLI, excellent --layout fidelity if installed

Usage:
    python pdf_text.py in.pdf [-o out.txt] [--pages 1-3,7] [--layout]
                       [--columns 2] [--engine plumber|pypdf|pdftotext]
                       [--no-markers] [--password PW]

--columns N splits each page into N equal-width vertical strips and reads them
left to right — use it for two-column journal articles where the default
reading order interleaves lines from both columns.

--header PT (with --columns) first reads the top PT points of each page at full
width (title, authors, DOI line), then splits only the area below into columns.
Typical first pages need 120-250 pt; find the value with pdf_render.py --grid
(header height = page height - y where the columns start).
"""
import argparse
import shutil
import subprocess
import sys


def parse_pages(spec, n):
    """'1-3,7,10-' -> [0,1,2,6,9..n-1] (0-based, in order given, no duplicates)."""
    if not spec:
        return list(range(n))
    out = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            start = int(a) if a else 1
            end = int(b) if b else n
        else:
            start = end = int(part)
        if start < 1 or end > n or start > end:
            sys.exit(f"Page range '{part}' is outside 1-{n}")
        for i in range(start - 1, end):
            if i not in out:
                out.append(i)
    return out


def extract_plumber(path, idxs, layout, columns, password, header=0.0):
    import pdfplumber
    texts = []
    with pdfplumber.open(path, password=password or None) as pdf:
        for i in idxs:
            page = pdf.pages[i]
            if columns and columns > 1:
                w = page.width
                top = min(max(header or 0.0, 0.0), page.height)
                parts = []
                if top:
                    head = page.crop((0, 0, w, top), relative=False, strict=False)
                    parts.append(head.extract_text(layout=layout) or "")
                for c in range(columns):
                    crop = page.crop((w * c / columns, top, w * (c + 1) / columns, page.height), relative=False, strict=False)
                    parts.append(crop.extract_text(layout=layout) or "")
                texts.append("\n\n".join(p.strip("\n") for p in parts))
            else:
                texts.append(page.extract_text(layout=layout) or "")
    return texts


def extract_pypdf(path, idxs, layout, password):
    from pypdf import PdfReader
    r = PdfReader(path)
    if r.is_encrypted:
        r.decrypt(password or "")
    out = []
    for i in idxs:
        try:
            out.append(r.pages[i].extract_text(extraction_mode="layout" if layout else "plain") or "")
        except TypeError:  # very old pypdf
            out.append(r.pages[i].extract_text() or "")
    return out


def extract_pdftotext(path, idxs, layout, password):
    if not shutil.which("pdftotext"):
        sys.exit("pdftotext not found (install poppler-utils) — use --engine plumber instead")
    out = []
    for i in idxs:
        cmd = ["pdftotext", "-f", str(i + 1), "-l", str(i + 1), "-enc", "UTF-8"]
        if layout:
            cmd.append("-layout")
        if password:
            cmd += ["-upw", password]
        cmd += [path, "-"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            sys.exit(f"pdftotext failed: {res.stderr.strip()}")
        out.append(res.stdout.rstrip("\f"))
    return out


def page_count(path, password):
    from pypdf import PdfReader
    r = PdfReader(path)
    if r.is_encrypted:
        if not r.decrypt(password or ""):
            sys.exit("PDF is encrypted; pass --password")
    return len(r.pages)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("-o", "--output", help="write to this file instead of stdout")
    ap.add_argument("--pages", help="page spec, 1-based, e.g. 1-3,7,10-")
    ap.add_argument("--layout", action="store_true", help="preserve horizontal layout (tables of numbers, forms)")
    ap.add_argument("--columns", type=int, default=0, help="read N equal-width columns left→right (plumber engine)")
    ap.add_argument("--header", type=float, default=0.0, help="with --columns: read the top PT points full-width first")
    ap.add_argument("--engine", choices=["plumber", "pypdf", "pdftotext"], default="plumber")
    ap.add_argument("--no-markers", action="store_true", help="omit '=== Page N ===' separators")
    ap.add_argument("--password")
    a = ap.parse_args()

    n = page_count(a.pdf, a.password)
    idxs = parse_pages(a.pages, n)
    if a.columns and a.engine != "plumber":
        sys.exit("--columns works only with --engine plumber")

    if a.engine == "plumber":
        try:
            texts = extract_plumber(a.pdf, idxs, a.layout, a.columns, a.password, a.header)
        except ImportError:
            print("pdfplumber not installed; falling back to pypdf", file=sys.stderr)
            texts = extract_pypdf(a.pdf, idxs, a.layout, a.password)
    elif a.engine == "pypdf":
        texts = extract_pypdf(a.pdf, idxs, a.layout, a.password)
    else:
        texts = extract_pdftotext(a.pdf, idxs, a.layout, a.password)

    empty = [i + 1 for i, t in zip(idxs, texts) if len(t.strip()) < 25]
    chunks = []
    for i, t in zip(idxs, texts):
        chunks.append(t if a.no_markers else f"=== Page {i + 1} ===\n{t}")
    result = "\n\n".join(chunks).rstrip() + "\n"

    if a.output:
        with open(a.output, "w", encoding="utf-8") as fh:
            fh.write(result)
        print(f"Wrote {len(idxs)} page(s), {len(result)} characters to {a.output}", file=sys.stderr)
    else:
        sys.stdout.write(result)
    if empty:
        print(f"Warning: little or no text on page(s) {empty} — likely scanned or image-only; consider pdf_ocr.py", file=sys.stderr)


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
