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
