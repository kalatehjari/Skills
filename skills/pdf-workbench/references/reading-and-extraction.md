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
