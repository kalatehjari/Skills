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
