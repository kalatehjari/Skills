#!/usr/bin/env python3
"""Render a deck to PDF, per-slide PNGs, or a single contact sheet for review.

    python pptx_render.py deck.pptx --sheet [-o deck_sheet.png] [--cols 4]   # all slides on one image
    python pptx_render.py deck.pptx --png [--slides 2-5] [--dpi 110] [-o renders/]
    python pptx_render.py deck.pptx --pdf [-o deck.pdf]

Uses LibreOffice (close to PowerPoint; fonts may be substituted). Outputs go next
to the deck unless -o is given. Look at the result before delivering a deck.
"""
import argparse
import os
import shutil
import sys
import tempfile

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pptx_common import parse_slides, to_pdf  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--sheet", action="store_true", help="one contact-sheet PNG of all (or --slides) slides")
    g.add_argument("--png", action="store_true")
    g.add_argument("--pdf", action="store_true")
    ap.add_argument("-o", "--output", help="--sheet: PNG file; --pdf: PDF file; --png: output FOLDER")
    ap.add_argument("--slides")
    ap.add_argument("--dpi", type=int, default=110)
    ap.add_argument("--cols", type=int, default=4)
    a = ap.parse_args()
    src = os.path.abspath(a.deck)
    if not os.path.exists(src):
        sys.exit(f"Not found: {a.deck}")
    here, base = os.path.dirname(src), os.path.splitext(os.path.basename(src))[0]

    with tempfile.TemporaryDirectory() as tmp:
        pdf = to_pdf(src, tmp)
        if a.pdf:
            out = a.output or os.path.join(here, base + ".pdf")
            shutil.move(pdf, out)
            print(f"Wrote {out}", file=sys.stderr)
            return
        try:
            import pypdfium2 as pdfium
            from PIL import Image, ImageDraw
        except ImportError:
            sys.exit("pip install pypdfium2 pillow")
        doc = pdfium.PdfDocument(pdf)
        idx = parse_slides(a.slides, len(doc))
        if a.png:
            out_dir = a.output or os.path.join(here, "renders")
            os.makedirs(out_dir, exist_ok=True)
            for i in idx:
                fn = os.path.join(out_dir, f"{base}_s{i + 1:02d}.png")
                doc[i].render(scale=a.dpi / 72).to_pil().save(fn)
                print(fn)
        else:
            thumbs = [doc[i].render(scale=60 / 72).to_pil().convert("RGB") for i in idx]
            tw, th = thumbs[0].size
            cols = min(a.cols, len(thumbs))
            rows = -(-len(thumbs) // cols)
            pad, label = 12, 22
            sheet = Image.new("RGB", (cols * (tw + pad) + pad, rows * (th + pad + label) + pad), "white")
            d = ImageDraw.Draw(sheet)
            for k, (i, im) in enumerate(zip(idx, thumbs)):
                x = pad + (k % cols) * (tw + pad)
                y = pad + (k // cols) * (th + pad + label)
                sheet.paste(im, (x, y + label))
                d.rectangle([x - 1, y + label - 1, x + tw, y + label + th], outline=(180, 180, 180))
                d.text((x, y + 4), f"Slide {i + 1}", fill=(60, 60, 60))
            out = a.output or os.path.join(here, base + "_sheet.png")
            sheet.save(out)
            print(out)
        print(f"{len(doc)} slide(s) in the deck", file=sys.stderr)
        doc.close()


if __name__ == "__main__":
    main()
