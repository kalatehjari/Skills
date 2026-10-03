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
