#!/usr/bin/env python3
"""Render a marked-up draft unit as a 16:9 reading PDF (two RTL columns, Persian page numbers).

Usage: python make_reading_pdf.py drafts/u01_ch01.md [-o out.pdf] --title "نام کتاب" [--notes notes.md]

Markup understood: # part / ## chapter headings; # alone = scene break; ::: {custom-style=Screen} (screen
text), Hand (handwriting), any style ending in Voice (a machine voice: centred, bold); [text]{custom-style=...}
inline; ⟦+ … ⟧ proposed additions (highlighted, with a legend on the title page).
--notes appends an English Markdown file (headings, bullets, **bold**) after the chapter, left to right.
Needs Playwright with Chromium. Static Noto Naskh Arabic and Vazirmatn (SIL OFL) are downloaded once into
--fonts-dir; static builds matter, because Chromium embeds variable fonts as Type 3 and loses the text layer.
Without -o the PDF is written next to the input as <name>.pdf. The input is never modified.
"""
import argparse, html, re, sys
from pathlib import Path

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("draft"); ap.add_argument("-o", "--output"); ap.add_argument("--title", default="پیش‌نویس")
ap.add_argument("--label", default="پیش‌نویس · برای خواندن و بازبینی")
ap.add_argument("--notes", help="optional English Markdown file appended after the chapter, left-to-right")
ap.add_argument("--fonts-dir", default=str(Path.home() / ".cache" / "farsi-scifi-builder" / "fonts"),
                help="where the fonts live or are downloaded to")
A = ap.parse_args()
SRC = Path(A.draft)
OUT = Path(A.output) if A.output else SRC.with_suffix(".pdf")
if OUT.resolve() == SRC.resolve(): sys.exit("error: refusing to overwrite the input")
src = SRC.read_text(encoding="utf-8")
src = re.sub(r"<!--.*?-->", "", src, flags=re.S)
FONTS = Path(A.fonts_dir).expanduser()
FONT_URLS = {
    "NotoNaskhArabic-Regular.ttf": "https://raw.githubusercontent.com/notofonts/notofonts.github.io/main/fonts/NotoNaskhArabic/hinted/ttf/NotoNaskhArabic-Regular.ttf",
    "NotoNaskhArabic-Bold.ttf": "https://raw.githubusercontent.com/notofonts/notofonts.github.io/main/fonts/NotoNaskhArabic/hinted/ttf/NotoNaskhArabic-Bold.ttf",
    "Vazirmatn-Regular.ttf": "https://raw.githubusercontent.com/rastikerdar/vazirmatn/master/fonts/ttf/Vazirmatn-Regular.ttf",
    "Vazirmatn-Bold.ttf": "https://raw.githubusercontent.com/rastikerdar/vazirmatn/master/fonts/ttf/Vazirmatn-Bold.ttf",
}
FONTS.mkdir(parents=True, exist_ok=True)
for _name, _url in FONT_URLS.items():
    if not (FONTS / _name).is_file():
        import urllib.request
        try:
            urllib.request.urlretrieve(_url, FONTS / _name)
        except Exception as e:
            sys.exit(f"error: could not download {_name} ({e}); put the four static fonts in {FONTS}")
part = next((l[2:].strip() for l in src.splitlines() if l.startswith("# ")), "")
chap = next((l[3:].strip() for l in src.splitlines() if l.startswith("## ")), "")

def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"\[([^\]]+)\]\{custom-style=ScreenChar\}", r'<span class="scr">\1</span>', t)
    t = re.sub(r"⟦\+\s*(.*?)\s*⟧", r'<mark class="add">\1</mark>', t, flags=re.S)
    return t

blocks = [b.strip() for b in re.split(r"\n\s*\n", src) if b.strip()]
body = []
for b in blocks:
    if b.startswith("# "):
        continue  # part title goes on the title page
    if b.startswith("## "):
        continue  # chapter title goes on the title page
    m = re.match(r"::: \{custom-style=(\w+)\}\n(.*?)\n:::", b, re.S)
    if m:
        cls = "orison" if m.group(1).endswith("Voice") else {"Screen": "screen", "Hand": "hand"}.get(m.group(1), "screen")
        body.append(f'<p class="{cls}">{inline(m.group(2))}</p>')
    elif b == "#":
        body.append('<p class="brk">⁂</p>')
    else:
        body.append(f"<p>{inline(b)}</p>")

NOTES = ""
LEGEND = ('<br><span style="background:#f6e3b4;padding:0 4px;border-radius:2px">زمینه‌ی کهربایی</span> = افزوده‌ی پیشنهادی، در انتظارِ تأیید' if "⟦+" in src else "")
if A.notes:
    def nin(t):
        t = html.escape(t, quote=False)
        t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
        return re.sub(r"([\u0600-\u06FF\u200c«»“”][\u0600-\u06FF\u200c«»“”\s.،؛؟:0-9۰-۹\-]*[\u0600-\u06FF\u200c«»“”.؟])", r"<bdi>\1</bdi>", t)
    out, inlist = [], False
    for line in Path(A.notes).read_text(encoding="utf-8").splitlines():
        s_ = line.strip()
        if s_.startswith("- "):
            if not inlist: out.append("<ul>"); inlist = True
            out.append(f"<li>{nin(s_[2:])}</li>"); continue
        if inlist: out.append("</ul>"); inlist = False
        if not s_: continue
        if s_.startswith("## "): out.append(f"<h2>{nin(s_[3:])}</h2>")
        elif s_.startswith("# "): out.append(f"<h1>{nin(s_[2:])}</h1>")
        else: out.append(f"<p>{nin(s_)}</p>")
    if inlist: out.append("</ul>")
    NOTES = '<section class="notes" dir="ltr" lang="en">' + "\n".join(out) + "</section>"

page = f"""<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8">
<style>
@font-face {{ font-family: Naskh; src: url("file://{FONTS}/NotoNaskhArabic-Regular.ttf"); font-weight: 400; }}
@font-face {{ font-family: Naskh; src: url("file://{FONTS}/NotoNaskhArabic-Bold.ttf"); font-weight: 700; }}
@font-face {{ font-family: Vazir; src: url("file://{FONTS}/Vazirmatn-Regular.ttf"); font-weight: 400; }}
@font-face {{ font-family: Vazir; src: url("file://{FONTS}/Vazirmatn-Bold.ttf"); font-weight: 700; }}
@page {{ size: 254mm 142.875mm; margin: 13mm 16mm 15mm 16mm;
  @bottom-center {{ content: counter(page, persian); font-family: Vazir; font-size: 8pt; color: #9a948a; }} }}
@page :first {{ @bottom-center {{ content: none; }} }}
html {{ background: #ffffff; }}
body {{ margin: 0; font-family: Naskh, serif; font-size: 12.3pt; line-height: 1.95; color: #23211d;
  text-align: justify; text-justify: inter-word; }}
.title {{ height: 114mm; display: flex; flex-direction: column; justify-content: center; align-items: center;
  text-align: center; break-after: page; }}
.title .book {{ font-family: Naskh; font-weight: 700; font-size: 34pt; line-height: 1.4; margin: 0; }}
.title .rule {{ width: 22mm; border-top: 1px solid #b9ae9a; margin: 5mm 0; }}
.title .part {{ font-family: Vazir; font-size: 10.5pt; letter-spacing: 0; color: #7b7466; margin: 0; }}
.title .chap {{ font-family: Naskh; font-size: 19pt; margin: 1.5mm 0 0; }}
.title .meta {{ font-family: Vazir; font-size: 8.5pt; color: #9a948a; margin-top: 9mm; line-height: 1.9; }}
.cols {{ column-count: 2; column-gap: 15mm; column-rule: 0.4pt solid #e2dbcd; column-fill: auto; height: auto; }}
p {{ margin: 0 0 0.55em; orphans: 2; widows: 2; }}
p.screen {{ font-family: Vazir; font-weight: 700; font-size: 10.8pt; letter-spacing: 0;
  text-align: center; color: #1f3a4d; margin: 0.6em 0 0.8em; break-inside: avoid; }}
.scr {{ font-family: Vazir; font-weight: 700; font-size: 0.88em; color: #1f3a4d; }}
p.orison {{ font-family: Vazir; font-weight: 700; font-size: 11pt; text-align: center; color: #1f3a4d; margin: 0.5em 0 0.8em; break-inside: avoid; }}
section.notes {{ break-before: page; direction: ltr; text-align: left; font-family: Vazir, sans-serif; font-size: 9.6pt; line-height: 1.6; column-count: 2; column-gap: 12mm; }}
section.notes h1 {{ font-size: 14pt; margin: 0 0 3mm; column-span: all; }}
section.notes h2 {{ font-size: 11pt; margin: 4mm 0 1.5mm; break-after: avoid; }}
section.notes p, section.notes li {{ margin: 0 0 1.6mm; text-align: left; }}
section.notes ul {{ margin: 0 0 2mm; padding-left: 5mm; }}
section.notes bdi {{ font-family: Naskh, Vazir; }}
p.hand {{ font-family: Naskh; font-weight: 700; font-size: 17pt; text-align: center; color: #2c4f8c;
  margin: 0.4em 0 0.7em; word-spacing: 0.35em; }}
p.brk {{ text-align: center; color: #a89d88; margin: 0.4em 0 0.7em; }}
mark.add {{ background: #f6e3b4; padding: 0 2px; border-radius: 2px; color: inherit; }}
.note {{ font-family: Vazir; font-size: 8pt; color: #8a8374; }}
</style></head><body>
<section class="title">
  <p class="book">{html.escape(A.title)}</p>
  <div class="rule"></div>
  <p class="part">{html.escape(part)}</p>
  <p class="chap">{html.escape(chap)}</p>
  <p class="meta">{html.escape(A.label)}
  {LEGEND}</p>
</section>
<div class="cols">
{chr(10).join(body)}
</div>
{NOTES}
</body></html>"""
TMP = OUT.with_suffix(".tmp.html"); TMP.write_text(page, encoding="utf-8")

from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page()
    pg.goto(f"file://{TMP.resolve()}")
    pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(300)
    pg.pdf(path=str(OUT), prefer_css_page_size=True, print_background=True)
    b.close()
TMP.unlink(); print(f"wrote {OUT}", file=sys.stderr)
