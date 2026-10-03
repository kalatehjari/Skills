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
