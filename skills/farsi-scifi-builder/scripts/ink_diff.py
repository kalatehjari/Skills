#!/usr/bin/env python3
"""Find an author's handwritten marks in a PDF by comparing it with the PDF you sent.

Handwriting added on a tablet is often flattened into the page as vector strokes, so it
never shows up as annotations or in the text layer. Rendering both PDFs and diffing the
pixels finds every mark. For each page with ink, this writes the annotated page with the
ink coloured red, plus close-up crops of each marked region, and prints a summary.

Examples:
  python ink_diff.py sent.pdf annotated.pdf               # outputs to annotated_ink/
  python ink_diff.py sent.pdf annotated.pdf -o marks --dpi 200 --zoom-dpi 320

Then view the red pages first, and the zoom crops wherever a mark is small or unclear.
Needs poppler's pdftoppm and Pillow. Inputs are never modified.
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageChops


def render(pdf, dpi, outdir, prefix, first=None, last=None):
    cmd = ["pdftoppm", "-png", "-r", str(dpi)]
    if first:
        cmd += ["-f", str(first), "-l", str(last or first)]
    subprocess.run(cmd + [str(pdf), str(outdir / prefix)], check=True)
    return sorted(outdir.glob(prefix + "-*.png"))


def ink_mask(a, b, threshold):
    if a.size != b.size:
        b = b.resize(a.size)
    return ImageChops.difference(a.convert("L"), b.convert("L")).point(lambda v: 255 if v > threshold else 0)


def regions(mask, gap):
    """Group ink into horizontal bands (rows of handwriting), returning boxes."""
    w, h = mask.size
    rows = [any(mask.getpixel((x, y)) for x in range(0, w, 3)) for y in range(h)]
    bands, start, quiet = [], None, 0
    for y, on in enumerate(rows):
        if on:
            start = y if start is None else start
            quiet = 0
        elif start is not None:
            quiet += 1
            if quiet > gap:
                bands.append((start, y - quiet))
                start, quiet = None, 0
    if start is not None:
        bands.append((start, h - 1))
    boxes = []
    for y0, y1 in bands:
        box = mask.crop((0, y0, w, y1 + 1)).getbbox()
        if box:
            boxes.append((box[0], y0 + box[1], box[2], y0 + box[3]))
    return boxes


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sent", help="the PDF you gave the author")
    ap.add_argument("annotated", help="the PDF the author sent back")
    ap.add_argument("-o", "--outdir", help="output folder (default: <annotated>_ink next to it)")
    ap.add_argument("--dpi", type=int, default=150, help="resolution of the red-ink pages (default 150)")
    ap.add_argument("--zoom-dpi", type=int, default=300, help="resolution of the close-up crops (default 300)")
    ap.add_argument("--threshold", type=int, default=50, help="grey-level difference counted as ink (default 50)")
    ap.add_argument("--json", action="store_true", help="print the summary as JSON")
    a = ap.parse_args()

    sent, ann = Path(a.sent), Path(a.annotated)
    for f in (sent, ann):
        if not f.is_file():
            sys.exit(f"error: {f} is not a file")
    if not shutil.which("pdftoppm"):
        sys.exit("error: pdftoppm (poppler) is required")
    out = Path(a.outdir) if a.outdir else ann.with_name(ann.stem + "_ink")
    out.mkdir(parents=True, exist_ok=True)

    summary = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        pages_a = render(ann, a.dpi, tmp, "a")
        pages_s = render(sent, a.dpi, tmp, "s")
        if len(pages_a) != len(pages_s):
            print(f"warning: page counts differ ({len(pages_s)} sent, {len(pages_a)} annotated); comparing in order",
                  file=sys.stderr)
        scale = a.zoom_dpi / a.dpi
        for i, (pa, ps) in enumerate(zip(pages_a, pages_s), 1):
            A, S = Image.open(pa).convert("RGB"), Image.open(ps).convert("RGB")
            mask = ink_mask(A, S, a.threshold)
            if not mask.getbbox():
                continue
            ink_px = sum(1 for v in mask.getdata() if v)
            red = Image.composite(Image.new("RGB", A.size, (215, 20, 20)), A, mask)
            red_path = out / f"page-{i:03d}-ink.png"
            red.save(red_path)
            boxes = regions(mask, gap=int(a.dpi * 0.12))
            zoom = render(ann, a.zoom_dpi, tmp, f"z{i}", first=i)[0]
            Z = Image.open(zoom)
            crops = []
            for k, (x0, y0, x1, y1) in enumerate(boxes, 1):
                pad = int(a.dpi * 0.25)
                box = (max(0, int((x0 - pad) * scale)), max(0, int((y0 - pad) * scale)),
                       min(Z.width, int((x1 + pad) * scale)), min(Z.height, int((y1 + pad) * scale)))
                cp = out / f"page-{i:03d}-zoom-{k:02d}.png"
                Z.crop(box).save(cp)
                crops.append(str(cp))
            summary.append({"page": i, "ink_pixels": ink_px, "regions": len(boxes),
                            "red_page": str(red_path), "zoom_crops": crops})

    if a.json:
        print(json.dumps(summary, indent=1))
    else:
        for s in summary:
            print(f"page {s['page']:>3}: {s['regions']} marked region(s), {s['ink_pixels']} ink px -> {s['red_page']}")
    print(f"{len(summary)} page(s) with ink; outputs in {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
