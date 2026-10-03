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
