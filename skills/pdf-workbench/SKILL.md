---
name: pdf-workbench
description: Read, extract from, edit, fill, OCR and create PDF files with tested Python scripts. Use this whenever a task involves a .pdf file in any way — pulling text, tables, figures or DOIs out of papers and reports; merging, splitting, rotating, reordering or deleting pages; filling or flattening forms (fillable or not); making scanned PDFs searchable; adding stamps, watermarks or passwords; or generating a new PDF from data, Markdown or HTML. Trigger even when the user doesn't say "PDF" but mentions a scanned document, a journal article, a lab report, a datasheet or a form they need filled.
license: MIT (see LICENSE)
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
