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
