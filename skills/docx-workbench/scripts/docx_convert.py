#!/usr/bin/env python3
"""Convert Word documents, and render pages to PNG for a visual check.

  python docx_convert.py report.docx --to pdf            # LibreOffice
  python docx_convert.py report.docx --to png [--pages 1-2] [--dpi 110]
  python docx_convert.py old.doc --to docx               # legacy .doc / .rtf / .odt -> .docx
  python docx_convert.py notes.md --to docx [--reference-doc house.docx]   # pandoc
  python docx_convert.py report.docx --to md|html|txt|odt
  python docx_convert.py notes.md --to pdf [--reference-doc house.docx]  # via .docx
  python docx_convert.py report.pdf --to png                            # render an existing PDF

-o sets the output file (or folder for png). Without -o, output goes NEXT TO THE
INPUT file (png: a "renders" folder next to it). Rendering uses LibreOffice, so
fonts and pagination can differ slightly from Word — good enough to catch
layout mistakes, not a pixel-exact proof.
"""
import argparse
import glob
import os
import shutil
import subprocess
import sys
import tempfile


def soffice():
    for name in ("soffice", "libreoffice", "/Applications/LibreOffice.app/Contents/MacOS/soffice"):
        if shutil.which(name) or os.path.exists(name):
            return shutil.which(name) or name
    sys.exit("LibreOffice not found (apt install libreoffice-writer / brew install --cask libreoffice)")


def lo_convert(src, fmt, outdir):
    os.makedirs(outdir, exist_ok=True)
    with tempfile.TemporaryDirectory() as profile:  # private profile avoids clashes with a running LibreOffice
        cmd = [soffice(), f"-env:UserInstallation=file://{profile}", "--headless", "--convert-to", fmt, "--outdir", outdir, src]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
    base = os.path.splitext(os.path.basename(src))[0]
    ext = fmt.split(":")[0]
    out = os.path.join(outdir, f"{base}.{ext}")
    if not os.path.exists(out):
        sys.exit(f"LibreOffice conversion failed: {res.stderr.strip() or res.stdout.strip()}")
    return out


def basic_markdown(path):
    """Fallback .docx -> Markdown without pandoc: headings, lists, tables, bold/italic."""
    import re
    import docx
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    d = docx.Document(path)
    lines = []
    for block in d.element.body.iterchildren():
        tag = block.tag.split("}")[1]
        if tag == "p":
            p = Paragraph(block, d)
            style = p.style.name if p.style is not None else ""
            text = "".join(
                (f"**{r.text}**" if r.bold and r.text.strip() else f"*{r.text}*" if r.italic and r.text.strip() else r.text)
                for r in p.runs) or p.text
            if not text.strip():
                continue
            m = re.match(r"Heading (\d)", style)
            if style == "Title":
                lines.append(f"# {p.text}")
            elif m:
                lines.append("#" * (int(m.group(1)) + (1 if any(l.startswith('# ') for l in lines[:1]) else 0)) + " " + p.text)
            elif "List Number" in style:
                lines.append(f"1. {text}")
            elif "List" in style or block.find(".//{*}numPr") is not None:
                lines.append(f"- {text}")
            else:
                lines.append(text)
            lines.append("")
        elif tag == "tbl":
            t = Table(block, d)
            rows = [[c.text.replace("\n", " ").replace("|", "\\|") for c in r.cells] for r in t.rows]
            if rows:
                lines.append("| " + " | ".join(rows[0]) + " |")
                lines.append("|" + "---|" * len(rows[0]))
                lines += ["| " + " | ".join(r) + " |" for r in rows[1:]]
                lines.append("")
    return "\n".join(lines)


def parse_pages(spec, n):
    if not spec:
        return list(range(n))
    out = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-", 1)
            out += list(range((int(a) if a else 1) - 1, int(b) if b else n))
        elif part.strip():
            out.append(int(part) - 1)
    return [i for i in out if 0 <= i < n]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("--to", required=True, choices=["pdf", "png", "docx", "odt", "html", "txt", "md"])
    ap.add_argument("-o", "--output", help="output file (png: output folder)")
    ap.add_argument("--pages", help="png only: page spec, 1-based")
    ap.add_argument("--dpi", type=int, default=110)
    ap.add_argument("--reference-doc", help="md->docx: a .docx whose styles to use")
    a = ap.parse_args()

    src = os.path.abspath(a.input)
    if not os.path.exists(src):
        sys.exit(f"Input not found: {a.input}")
    base, ext = os.path.splitext(os.path.basename(src))
    ext = ext.lower()

    src_dir = os.path.dirname(src)
    is_markdown = ext in (".md", ".markdown")

    if a.to == "md" or (is_markdown and a.to == "docx"):
        out = os.path.abspath(a.output or os.path.join(src_dir, f"{base}.{'md' if a.to == 'md' else 'docx'}"))
        if not shutil.which("pandoc"):
            if a.to == "md" and ext == ".docx":
                with open(out, "w", encoding="utf-8") as fh:
                    fh.write(basic_markdown(src))
                print(f"Wrote {out} (basic converter: pandoc not installed — no images/equations/footnotes)", file=sys.stderr)
                return
            sys.exit("pandoc not found (https://pandoc.org/installing.html)")
        cmd = ["pandoc", src, "-o", out]
        cwd = None
        if a.to == "md":
            # -s keeps the Title as YAML front matter; images go to <name>_media/ next to the .md,
            # referenced with RELATIVE paths (pandoc runs inside the output folder)
            cwd = os.path.dirname(out)
            cmd = ["pandoc", src, "-o", os.path.basename(out), "-s", "-t", "gfm", "--wrap=none",
                   "--track-changes=accept", f"--extract-media={os.path.splitext(os.path.basename(out))[0]}_media"]
        if a.reference_doc:
            cmd += ["--reference-doc", os.path.abspath(a.reference_doc)]
        if is_markdown:
            cmd += ["--resource-path", src_dir]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
        if res.returncode != 0:
            sys.exit(f"pandoc failed: {res.stderr.strip()}")
        print(f"Wrote {out}", file=sys.stderr)
        return

    if is_markdown and a.to in ("pdf", "png", "odt", "html", "txt"):
        # Markdown -> .docx (pandoc) -> target (LibreOffice), keeping the reference-doc styling
        with tempfile.TemporaryDirectory() as tmp:
            mid = os.path.join(tmp, f"{base}.docx")
            cmd = ["pandoc", src, "-o", mid, "--resource-path", src_dir]
            if a.reference_doc:
                cmd += ["--reference-doc", os.path.abspath(a.reference_doc)]
            if not shutil.which("pandoc") or subprocess.run(cmd).returncode != 0:
                sys.exit("pandoc is needed to convert Markdown")
            sys.argv = [sys.argv[0], mid, "--to", a.to, "-o", a.output or (os.path.join(src_dir, "renders") if a.to == "png" else os.path.join(src_dir, f"{base}.{a.to}"))]
            if a.pages:
                sys.argv += ["--pages", a.pages]
            return main()

    if a.to == "png":
        outdir = a.output or os.path.join(src_dir, "renders")
        with tempfile.TemporaryDirectory() as tmp:
            pdf = lo_convert(src, "pdf", tmp) if ext != ".pdf" else src
            try:
                import pypdfium2 as pdfium
            except ImportError:
                sys.exit("pip install pypdfium2 to render PNGs")
            os.makedirs(outdir, exist_ok=True)
            doc = pdfium.PdfDocument(pdf)
            for i in parse_pages(a.pages, len(doc)):
                fn = os.path.join(outdir, f"{base}_p{i + 1:03d}.png")
                doc[i].render(scale=a.dpi / 72).to_pil().save(fn)
                print(fn)
            print(f"{len(doc)} page(s) in total", file=sys.stderr)
            doc.close()
        return

    fmt = {"txt": "txt:Text (encoded):UTF8", "html": "html:XHTML Writer File:UTF8"}.get(a.to, a.to)
    if a.output:
        with tempfile.TemporaryDirectory() as tmp:
            out = lo_convert(src, fmt, tmp)
            shutil.move(out, a.output)
            out = a.output
    else:
        out = lo_convert(src, fmt, src_dir)
    print(f"Wrote {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
