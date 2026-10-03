#!/usr/bin/env python3
"""Build a PowerPoint deck from a Markdown outline (or JSON), with a clean built-in
design or the layouts of your own template.

    python pptx_build.py talk.md -o talk.pptx [--template house.pptx] [--theme navy|teal|charcoal|forest]
                         [--accent 1F3864] [--font Calibri] [--ratio 16:9|4:3] [--no-numbers]

Outline format (one slide per heading; YAML-ish front matter optional):

    ---
    title: Slope stability at Lot 12
    subtitle: Site investigation findings
    author: R. Kalatehjari, GEOTECH-LAB
    date: 3 October 2026
    footer: Lot 12 retaining wall
    ---
    # Background                     <- "# " = section divider slide
    ## Site and geology              <- "## " = content slide title
    - Bullet                         <- bullets; indent 2+ spaces for sub-bullets
      - Sub-bullet
    Plain lines become paragraphs.
    Notes: what to say here          <- speaker notes (rest of the slide's lines)

    ## Results
    ![Effective stress paths](fig/paths.png)    <- image slide (alt text = caption)
    ![q–p′ paths of six CU tests, BH1 and BH2](fig/paths.png "Stress paths")  <- alt + shorter caption
    ![Site photo](photo.jpg "")                  <- alt text, no caption

    ## Strength parameters
    | Sample | c' (kPa) | phi' (deg) |          <- table slide
    |---|---|---|
    | BH1 | 5 | 32 |

    ## Factor of safety
    ```chart
    {"type": "bar", "categories": ["Static", "Seismic"], "series": {"FoS": [1.32, 1.08]},
     "y_title": "FoS", "number_format": "0.00", "colors": {"Target": "A6A6A6"}}
    ```                                          <- native, editable chart (bar|column|line|pie|scatter)

    ## Two views
    ::: left
    - text, image or table
    :::
    ::: right
    ![Plan](plan.png)
    :::                                          <- two-column slide

    ## Key message
    > Retaining wall needs 2 m deeper embedment.  <- title + big centred statement
    ##
    > Retaining wall needs 2 m deeper embedment.  <- empty "##": the statement alone (it becomes the slide title)

JSON input: {"meta": {...}, "slides": [{"type": "bullets", "title": "...", "bullets": ["a", ["sub"]], "notes": "..."}, ...]}
Text that would overflow is shrunk (down to --min-font) and reported; check with pptx_check.py.
"""
import argparse
import json
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _pptx_common  # noqa: E402,F401

from pptx import Presentation  # noqa: E402
from pptx.chart.data import CategoryChartData, XyChartData  # noqa: E402
from pptx.dml.color import RGBColor  # noqa: E402
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION  # noqa: E402
from pptx.enum.shapes import MSO_SHAPE, PP_PLACEHOLDER  # noqa: E402
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN  # noqa: E402
from pptx.util import Emu, Inches, Pt  # noqa: E402

THEMES = {"navy": "1F3864", "teal": "006D77", "charcoal": "333F48", "forest": "2E6B3F", "maroon": "7B1E3A"}
WARNINGS = []


# ----------------------------------------------------------------------------- parsing
def parse_markdown(text, base_dir):
    meta, slides = {}, []
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip().lower()] = v.strip().strip('"')
        text = text[m.end():]
    cur = None
    lines = text.splitlines()
    i = 0

    def new(kind, title):
        nonlocal cur
        cur = {"type": kind, "title": title, "blocks": [], "notes": ""}
        slides.append(cur)

    while i < len(lines):
        line = lines[i]
        if line.startswith("# "):
            new("section", line[2:].strip())
        elif line.startswith("## ") or line.strip() == "##":
            new("content", line[3:].strip())
        elif cur is None:
            if line.strip():
                new("content", "")
                continue
        elif re.match(r"^\s*(Notes|Note|Speaker notes):", line, re.I):
            cur["notes"] = "\n".join([line.split(":", 1)[1].strip()] + [l for l in lines[i + 1:] if not l.startswith("#")][:0])
            j = i + 1
            extra = []
            while j < len(lines) and not lines[j].startswith("#"):
                extra.append(lines[j])
                j += 1
            cur["notes"] = (cur["notes"] + "\n" + "\n".join(extra)).strip()
            i = j
            continue
        elif line.strip().startswith("```chart"):
            j = i + 1
            body = []
            while j < len(lines) and not lines[j].strip().startswith("```"):
                body.append(lines[j])
                j += 1
            try:
                cur["blocks"].append(("chart", json.loads("\n".join(body))))
            except json.JSONDecodeError as e:
                sys.exit(f"Chart block on slide '{cur['title']}' is not valid JSON: {e}")
            i = j + 1
            continue
        elif line.strip().startswith(":::") and line.strip()[3:].strip() in ("left", "right"):
            side = line.strip()[3:].strip()
            j = i + 1
            body = []
            while j < len(lines) and lines[j].strip() != ":::":
                body.append(lines[j])
                j += 1
            sub = parse_blocks(body, base_dir)
            cur["blocks"].append((side, sub))
            i = j + 1
            continue
        else:
            cur.setdefault("_raw", []).append(line)
            nxt = lines[i + 1] if i + 1 < len(lines) else "#"
            if nxt.startswith("#") or nxt.strip().startswith("```chart") or re.match(r"^\s*(Notes|Note|Speaker notes):", nxt, re.I) \
                    or (nxt.strip().startswith(":::") and nxt.strip()[3:].strip() in ("left", "right")):
                cur["blocks"].extend(parse_blocks(cur.pop("_raw"), base_dir))
        i += 1
    for s in slides:
        if "_raw" in s:
            s["blocks"].extend(parse_blocks(s.pop("_raw"), base_dir))
    return meta, slides


def parse_blocks(lines, base_dir):
    blocks, i = [], 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        img = re.match(r'^\s*!\[(.*?)\]\((\S+?)(?:\s+"(.*?)")?\)\s*$', line)
        if img:
            path = img.group(2).strip()
            path = path if os.path.isabs(path) else os.path.join(base_dir, path)
            alt = img.group(1).strip()
            caption = alt if img.group(3) is None else img.group(3).strip()  # ![alt](p "caption"); "" = no caption
            blocks.append(("image", {"path": path, "caption": caption, "alt": alt}))
            i += 1
            continue
        if line.strip().startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            blocks.append(("table", rows))
            continue
        if line.lstrip().startswith(">"):
            q = []
            while i < len(lines) and lines[i].lstrip().startswith(">"):
                q.append(lines[i].lstrip()[1:].strip())
                i += 1
            blocks.append(("quote", " ".join(q)))
            continue
        b = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", line)
        if b:
            items = []
            while i < len(lines):
                b = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", lines[i])
                if not b:
                    if lines[i].strip() and lines[i].startswith("  ") and items:
                        items[-1] = (items[-1][0], items[-1][1] + " " + lines[i].strip(), items[-1][2])
                        i += 1
                        continue
                    break
                level = min(len(b.group(1).replace("\t", "    ")) // 2, 4)
                items.append((level, b.group(3).strip(), b.group(2)[0].isdigit()))
                i += 1
            blocks.append(("bullets", items))
            continue
        para = [line.strip()]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^\s*([-*+]|\d+[.)])\s+|^\s*!\[|^\s*\||^\s*>", lines[i]):
            para.append(lines[i].strip())
            i += 1
        blocks.append(("para", " ".join(para)))
    return blocks


def from_json(d, base_dir):
    meta = d.get("meta", {})
    slides = []
    for s in d.get("slides", []):
        t = s.get("type", "bullets")
        kind = "section" if t == "section" else "content"
        blocks = []
        if s.get("bullets"):
            items = []

            def walk(xs, lvl):
                for x in xs:
                    if isinstance(x, list):
                        walk(x, lvl + 1)
                    else:
                        items.append((lvl, str(x), False))
            walk(s["bullets"], 0)
            blocks.append(("bullets", items))
        for k in ("text",):
            if s.get(k):
                blocks.append(("para", s[k]))
        if s.get("image"):
            p = s["image"] if os.path.isabs(s["image"]) else os.path.join(base_dir, s["image"])
            blocks.append(("image", {"path": p, "caption": s.get("caption", "")}))
        if s.get("table"):
            blocks.append(("table", s["table"]))
        if s.get("chart"):
            blocks.append(("chart", s["chart"]))
        if s.get("quote"):
            blocks.append(("quote", s["quote"]))
        slides.append({"type": kind, "title": s.get("title", ""), "blocks": blocks, "notes": s.get("notes", "")})
    return meta, slides


# ----------------------------------------------------------------------------- rendering helpers
def rgb(hexstr):
    return RGBColor.from_string(hexstr.upper())


def style_run(run, size=None, bold=None, color=None, font=None, italic=None):
    f = run.font
    if size:
        f.size = Pt(size)
    if bold is not None:
        f.bold = bold
    if italic is not None:
        f.italic = italic
    if color:
        f.color.rgb = rgb(color)
    if font:
        f.name = font


def add_rich(paragraph, text, size, color, font, bold=None):
    """**bold**, *italic* and `code` inline markup -> runs."""
    parts = re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)", text)
    for part in parts:
        if not part:
            continue
        r = paragraph.add_run()
        if part.startswith("**") and part.endswith("**"):
            r.text = part[2:-2]
            style_run(r, size, True, color, font)
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            r.text = part[1:-1]
            style_run(r, size, bold, color, font, italic=True)
        elif part.startswith("`") and part.endswith("`"):
            r.text = part[1:-1]
            style_run(r, size, bold, color, "Consolas")
        else:
            r.text = part
            style_run(r, size, bold, color, font)


def set_bullet(p, level, kind, color):
    """Real PowerPoint bullets (so they behave natively when edited): kind = bullet | num | none."""
    from pptx.oxml.ns import qn
    from lxml import etree
    pPr = p._p.get_or_add_pPr()
    step = 342900  # 0.375 in per level
    pPr.set("lvl", str(level))
    if kind == "none":
        pPr.set("marL", str(step * level))
        pPr.set("indent", "0")
    else:
        pPr.set("marL", str(step * (level + 1)))
        pPr.set("indent", str(-step))
    for tag in ("a:buClr", "a:buSzPct", "a:buFont", "a:buNone", "a:buChar", "a:buAutoNum"):
        for e in pPr.findall(qn(tag)):
            pPr.remove(e)
    anchor = next((c for c in pPr if c.tag in (qn("a:tabLst"), qn("a:defRPr"), qn("a:extLst"))), None)

    def put(el):
        if anchor is not None:
            anchor.addprevious(el)
        else:
            pPr.append(el)
        return el
    if kind == "none":
        put(etree.Element(qn("a:buNone")))
        return
    clr = put(etree.Element(qn("a:buClr")))
    etree.SubElement(clr, qn("a:srgbClr")).set("val", color)
    if kind == "num":
        put(etree.Element(qn("a:buAutoNum"))).set("type", "arabicPeriod")
    else:
        put(etree.Element(qn("a:buFont"))).set("typeface", "Arial")
        put(etree.Element(qn("a:buChar"))).set("char", "•" if level == 0 else "–")


def estimate_height_pt(items, size, width_pt):
    """Rough text height: average glyph ≈ 0.5 em, line height 1.2, paragraph gap 0.3 em."""
    h = 0.0
    for level, text, _ in items:
        s = size * (0.9 ** level)
        usable = max(width_pt - level * 24 - 18, 50)
        chars_per_line = max(usable / (s * 0.5), 8)
        lines = max(1, -(-len(text) // int(chars_per_line)))
        h += lines * s * 1.2 + s * 0.35
    return h


class Builder:
    def __init__(self, a, meta):
        self.a = a
        self.meta = meta
        self.template = a.template
        self.prs = Presentation(a.template) if a.template else Presentation()
        if a.template and not a.keep_template_slides:
            self.remove_all_slides()
        if not a.template:
            if a.ratio == "16:9":
                self.prs.slide_width, self.prs.slide_height = Inches(13.333), Inches(7.5)
            else:
                self.prs.slide_width, self.prs.slide_height = Inches(10), Inches(7.5)
        self.W, self.H = self.prs.slide_width, self.prs.slide_height
        self.accent = (a.accent or THEMES.get(a.theme, THEMES["navy"])).lstrip("#")
        self.font = a.font
        self.dark = "222222"
        self.grey = "7F7F7F"
        self.n = 0

    # -- template helpers
    def remove_all_slides(self):
        sldIdLst = self.prs.slides._sldIdLst
        for sldId in list(sldIdLst):
            self.prs.part.drop_rel(sldId.rId)
            sldIdLst.remove(sldId)

    def layout(self, want):
        """Pick a layout: in a template by placeholder pattern/name; otherwise Blank."""
        layouts = list(self.prs.slide_layouts)
        if not self.template:
            # real title placeholders (outline view, screen readers, accessibility checker),
            # repositioned and styled per slide
            name = "Title Slide" if want == "title" else "Title Only"
            return next((l for l in layouts if l.name == name), layouts[0])

        def types(l):
            return [ph.placeholder_format.type for ph in l.placeholders]
        names = {l.name.lower(): l for l in layouts}
        if want == "title":
            for l in layouts:
                if PP_PLACEHOLDER.CENTER_TITLE in types(l):
                    return l
        if want == "section":
            for key in ("section header", "section", "divider"):
                for n, l in names.items():
                    if key in n:
                        return l
        if want == "content":
            for key in ("title and content", "content"):
                for n, l in names.items():
                    if key in n:
                        return l
        if want == "title_only":
            for key in ("title only",):
                for n, l in names.items():
                    if key in n:
                        return l
        return layouts[min(1, len(layouts) - 1)]

    def content_box(self, slide=None):
        """(left, top, width, height) of the area below the title."""
        if self.template:
            lay = self.layout("content")
            for ph in lay.placeholders:
                if ph.placeholder_format.type in (PP_PLACEHOLDER.OBJECT, PP_PLACEHOLDER.BODY):
                    return ph.left, ph.top, ph.width, ph.height
        m = Inches(0.6)
        top = Inches(1.45)
        return m, top, self.W - 2 * m, self.H - top - Inches(0.7)

    # -- slide kinds
    def new_slide(self, kind):
        self.n += 1
        lay = self.layout({"title": "title", "section": "section"}.get(kind, "title_only" if kind == "visual" else "content"))
        s = self.prs.slides.add_slide(lay)
        return s

    def style_placeholder(self, ph, left, top, width, height, anchor=MSO_ANCHOR.BOTTOM):
        ph.left, ph.top, ph.width, ph.height = left, top, width, height
        tf = ph.text_frame
        tf.text = ""
        tf.word_wrap = True
        tf.auto_size = MSO_AUTO_SIZE.NONE
        tf.vertical_anchor = anchor
        tf.margin_left = tf.margin_right = 0
        return tf

    def set_title(self, slide, text, size=30):
        if self.template and slide.shapes.title is not None:
            slide.shapes.title.text = text
            return slide.shapes.title
        m = Inches(0.6)
        if slide.shapes.title is not None:
            tb = slide.shapes.title
            tf = self.style_placeholder(tb, m, Inches(0.35), self.W - 2 * m, Inches(0.9))
        else:
            tb = slide.shapes.add_textbox(m, Inches(0.35), self.W - 2 * m, Inches(0.9))
            tf = tb.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.BOTTOM
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT
        add_rich(p, text, size if len(text) < 60 else size - 6, self.accent, self.font, bold=True)
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, m, Inches(1.27), Inches(1.2), Pt(3))
        line.fill.solid()
        line.fill.fore_color.rgb = rgb(self.accent)
        line.line.fill.background()
        line.name = "Title rule"
        return tb

    def footer(self, slide):
        if self.template or self.a.no_numbers:
            return
        foot = self.meta.get("footer") or self.meta.get("title", "")
        tb = slide.shapes.add_textbox(Inches(0.6), self.H - Inches(0.5), self.W - Inches(2.2), Inches(0.35))
        tb.name = "Footer"
        tb.text_frame.word_wrap = True  # without wrapping, LibreOffice centres the text in the box
        p = tb.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT
        r = p.add_run()
        r.text = foot
        style_run(r, 10, False, self.grey, self.font)
        tb2 = slide.shapes.add_textbox(self.W - Inches(1.4), self.H - Inches(0.5), Inches(0.8), Inches(0.35))
        tb2.name = "Slide Number"
        tb2.text_frame.word_wrap = True
        p2 = tb2.text_frame.paragraphs[0]
        p2.alignment = PP_ALIGN.RIGHT
        r2 = p2.add_run()
        r2.text = str(self.n)
        style_run(r2, 10, False, self.grey, self.font)

    def title_slide(self):
        s = self.new_slide("title")
        title = self.meta.get("title", "Untitled")
        sub = " — ".join(x for x in (self.meta.get("subtitle"),) if x)
        byline = "  |  ".join(x for x in (self.meta.get("author"), self.meta.get("date")) if x)
        if self.template:
            if s.shapes.title is not None:
                s.shapes.title.text = title
            for ph in s.placeholders:
                if ph.placeholder_format.type == PP_PLACEHOLDER.SUBTITLE:
                    ph.text = "\n".join(x for x in (sub, byline) if x)
            return s
        bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, self.W, self.H)
        bg.fill.solid()
        bg.fill.fore_color.rgb = rgb(self.accent)
        bg.line.fill.background()
        bg.name = "Background"
        s.shapes._spTree.remove(bg._element)
        s.shapes._spTree.insert(2, bg._element)  # behind the placeholders
        tph = s.shapes.title
        tf = self.style_placeholder(tph, Inches(0.9), Inches(1.9), self.W - Inches(1.8), Inches(1.9))
        tf.paragraphs[0].alignment = PP_ALIGN.LEFT
        add_rich(tf.paragraphs[0], title, 40 if len(title) < 50 else 32, "FFFFFF", self.font, bold=True)
        sph = next((ph for ph in s.placeholders if ph.placeholder_format.type == PP_PLACEHOLDER.SUBTITLE), None)
        if sph is not None:
            if sub:
                stf = self.style_placeholder(sph, Inches(0.9), Inches(3.9), self.W - Inches(1.8), Inches(1.0), MSO_ANCHOR.TOP)
                stf.paragraphs[0].alignment = PP_ALIGN.LEFT
                add_rich(stf.paragraphs[0], sub, 22, "E6E6E6", self.font)
            else:
                sph._element.getparent().remove(sph._element)
        if byline:
            tb2 = s.shapes.add_textbox(Inches(0.9), self.H - Inches(1.6), self.W - Inches(1.8), Inches(0.6))
            tb2.text_frame.word_wrap = True
            tb2.text_frame.paragraphs[0].alignment = PP_ALIGN.LEFT
            add_rich(tb2.text_frame.paragraphs[0], byline, 16, "E6E6E6", self.font)
        return s

    def section_slide(self, spec):
        s = self.new_slide("section")
        if self.template:
            if s.shapes.title is not None:
                s.shapes.title.text = spec["title"]
            paras = [d for k, d in spec["blocks"] if k == "para"]
            for ph in list(s.placeholders):
                if ph.placeholder_format.type in (PP_PLACEHOLDER.BODY, PP_PLACEHOLDER.SUBTITLE, PP_PLACEHOLDER.OBJECT):
                    if paras:
                        ph.text = paras.pop(0)
                    else:
                        ph._element.getparent().remove(ph._element)  # no empty "Click to add text" boxes
            return s
        band = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.35), self.H)
        band.fill.solid()
        band.fill.fore_color.rgb = rgb(self.accent)
        band.line.fill.background()
        band.name = "Section band"
        tf = self.style_placeholder(s.shapes.title, Inches(1.0), Inches(2.4), self.W - Inches(2), Inches(1.4))
        tf.paragraphs[0].alignment = PP_ALIGN.LEFT
        add_rich(tf.paragraphs[0], spec["title"], 36, self.accent, self.font, bold=True)
        paras = [d for k, d in spec["blocks"] if k == "para"]
        if paras:
            tb = s.shapes.add_textbox(Inches(1.0), Inches(3.9), self.W - Inches(2), Inches(1.2))
            tb.name = "Section subtitle"
            tb.text_frame.word_wrap = True
            tb.text_frame.margin_left = 0
            for k, d in enumerate(paras):
                p = tb.text_frame.paragraphs[0] if k == 0 else tb.text_frame.add_paragraph()
                add_rich(p, d, 18, self.grey, self.font)
        return s

    def content_slide(self, spec):
        blocks = spec["blocks"]
        kinds = [k for k, _ in blocks]
        visual = any(k in ("image", "table", "chart", "left", "right", "quote") for k in kinds)
        s = self.new_slide("visual" if visual else "content")
        if not spec["title"] and kinds == ["quote"] and not self.template and s.shapes.title is not None:
            # statement slide: the statement itself is the slide title (accessible), big and centred
            text = blocks[0][1]
            tf = self.style_placeholder(s.shapes.title, Inches(1.2), Inches(1.5), self.W - Inches(2.4), self.H - Inches(3.2), MSO_ANCHOR.MIDDLE)
            tf.paragraphs[0].alignment = PP_ALIGN.CENTER
            add_rich(tf.paragraphs[0], text, 36 if len(text) < 90 else 28, self.accent, self.font, bold=True)
            if spec.get("notes"):
                s.notes_slide.notes_text_frame.text = spec["notes"]
            self.footer(s)
            return s
        if not spec["title"] and kinds == ["quote"] and self.template and s.shapes.title is not None:
            s.shapes.title.text = blocks[0][1]  # template: the statement becomes the (template-styled) title
            if spec.get("notes"):
                s.notes_slide.notes_text_frame.text = spec["notes"]
            return s
        if spec["title"]:
            self.set_title(s, spec["title"])
        elif s.shapes.title is not None:
            s.shapes.title._element.getparent().remove(s.shapes.title._element)
            WARNINGS.append(f"slide {self.n}: no title — slides without titles are hard to navigate")
        L, T, Wd, Ht = self.content_box(s)
        body_ph = None
        if self.template and not visual:
            body_ph = next((ph for ph in s.placeholders if ph.placeholder_format.type in (PP_PLACEHOLDER.OBJECT, PP_PLACEHOLDER.BODY)), None)
        if body_ph is not None:
            # text-only slide in a template: fill the layout's own body placeholder so the
            # template's fonts, sizes and bullet styles apply
            items = []
            for kind, data in blocks:
                items += data if kind == "bullets" else [(0, data, None)] if kind == "para" else []
            tf = body_ph.text_frame
            for k, (level, text, numbered) in enumerate(items):
                p = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
                p.level = min(level, 4)
                if numbered is None:
                    set_bullet(p, level, "none", self.grey)
                elif numbered:
                    set_bullet(p, level, "num", self.accent)
                add_rich(p, text, None, None, None)
            if estimate_height_pt(items, 24, body_ph.width / 12700) > body_ph.height / 12700:
                WARNINGS.append(f"slide {self.n} '{spec['title']}': text may overflow the template's body box — split the slide")
        elif "left" in kinds or "right" in kinds:
            gap = Inches(0.4)
            half = int((Wd - gap) / 2)
            for kind, data in blocks:
                if kind == "left":
                    self.place_blocks(s, data, L, T, half, Ht, spec)
                elif kind == "right":
                    self.place_blocks(s, data, L + half + gap, T, half, Ht, spec)
        else:
            self.place_blocks(s, blocks, L, T, Wd, Ht, spec)
        if self.template:
            # remove empty body placeholder when we placed our own content
            for ph in list(s.placeholders):
                if ph.placeholder_format.type in (PP_PLACEHOLDER.OBJECT, PP_PLACEHOLDER.BODY) and not ph.has_text_frame or \
                        (ph.placeholder_format.type in (PP_PLACEHOLDER.OBJECT, PP_PLACEHOLDER.BODY) and not ph.text_frame.text.strip()):
                    ph._element.getparent().remove(ph._element)
        if spec.get("notes"):
            s.notes_slide.notes_text_frame.text = spec["notes"]
        self.footer(s)
        return s

    def place_blocks(self, s, blocks, L, T, Wd, Ht, spec):
        text_items = []
        visuals = []
        for kind, data in blocks:
            if kind == "bullets":
                text_items += data
            elif kind == "para":
                text_items.append((0, data, None))
            elif kind in ("image", "table", "chart", "quote"):
                visuals.append((kind, data))
        top = T
        avail = Ht
        if text_items and visuals:
            # text above, visual below: give text what it needs (max 40 %)
            need = Emu(int(estimate_height_pt(text_items, 18, Wd / 12700) * 12700)) + Inches(0.1)
            th = min(need, int(Ht * 0.4))
            self.text_box(s, text_items, L, top, Wd, th, spec, base=18)
            top += th + Inches(0.1)
            avail = Ht - th - Inches(0.1)
        elif text_items:
            self.text_box(s, text_items, L, top, Wd, avail, spec, base=24 if self.W > Inches(11) else 22)
        if visuals:
            hv = int(avail / len(visuals))
            for kind, data in visuals:
                getattr(self, f"place_{kind}")(s, data, L, top, Wd, hv, spec)
                top += hv

    def text_box(self, s, items, L, T, Wd, Ht, spec, base=24):
        size = base
        width_pt = Wd / 12700
        while size > self.a.min_font and estimate_height_pt(items, size, width_pt) > Ht / 12700:
            size -= 1
        sparse = False
        if size == base:  # few short bullets: larger type, vertically centred, instead of a half-empty slide
            while size < base + 6 and estimate_height_pt(items, size + 1, width_pt) < 0.45 * Ht / 12700:
                size += 1
            sparse = estimate_height_pt(items, size, width_pt) < 0.45 * Ht / 12700
        if estimate_height_pt(items, size, width_pt) > Ht / 12700:
            WARNINGS.append(f"slide {self.n} '{spec['title']}': text likely overflows even at {size} pt — split the slide")
        elif size < base:
            WARNINGS.append(f"slide {self.n} '{spec['title']}': text shrunk to {size} pt to fit")
        tb = s.shapes.add_textbox(L, T, Wd, Ht)
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = 0
        if sparse:
            tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        first = True
        for level, text, numbered in items:
            p = tf.paragraphs[0] if first else tf.add_paragraph()
            p.alignment = PP_ALIGN.LEFT
            first = False
            sz = round(size * (0.9 ** level))
            p.space_after = Pt(sz * 0.35)
            kind = "none" if numbered is None else ("num" if numbered else "bullet")
            set_bullet(p, level, kind, self.accent if level == 0 else self.grey)
            add_rich(p, text, sz, self.dark, self.font)
        tb.name = "Body"
        return tb

    def place_image(self, s, data, L, T, Wd, Ht, spec):
        from PIL import Image as PILImage
        if not os.path.exists(data["path"]):
            WARNINGS.append(f"slide {self.n}: image not found: {data['path']}")
            return
        cap_h = Inches(0.4) if data.get("caption") else 0
        with PILImage.open(data["path"]) as im:
            iw, ih = im.size
            dpi = im.info.get("dpi", (96, 96))[0] or 96
        box_w, box_h = Wd, Ht - cap_h
        scale = min(box_w / iw, box_h / ih)
        w, h = int(iw * scale), int(ih * scale)
        x = L + int((box_w - w) / 2)
        pic = s.shapes.add_picture(data["path"], x, T, w, h)
        pic.name = data.get("caption") or os.path.basename(data["path"])
        # alt text (accessibility): stored as the descr attribute
        pic._element.nvPicPr.cNvPr.set("descr", data.get("alt") or data.get("caption") or os.path.basename(data["path"]))
        shown_in = w / 914400
        if iw / max(shown_in, 0.01) < 100:
            WARNINGS.append(f"slide {self.n}: image {os.path.basename(data['path'])} is only ~{iw / shown_in:.0f} px/inch at this size — may look blurry")
        if data.get("caption"):
            tb = s.shapes.add_textbox(L, T + h + Inches(0.05), Wd, cap_h)
            tb.name = "Caption"
            tb.text_frame.word_wrap = True
            p = tb.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER
            add_rich(p, data["caption"], 14, self.grey, self.font, bold=None)
            tb.text_frame.word_wrap = True

    def place_table(self, s, rows, L, T, Wd, Ht, spec):
        if not rows:
            return
        nr, nc = len(rows), max(len(r) for r in rows)
        size = 18 if nr <= 6 else 14 if nr <= 10 else 11
        row_h = Pt(size * 2.0)
        h = min(Ht, row_h * nr)
        lens = [max(len(str(r[j])) if j < len(r) else 0 for r in rows) + 3 for j in range(nc)]
        natural = int(sum(lens) * size * 0.62 * 12700)  # rough width the content needs
        tw = max(min(Wd, natural), int(Wd * 0.45))
        L = L + int((Wd - tw) / 2)  # centre narrower tables
        Wd = tw
        gt = s.shapes.add_table(nr, nc, L, T, Wd, h)
        tbl = gt.table
        for j in range(nc):
            tbl.columns[j].width = int(Wd * lens[j] / sum(lens))
        for i, r in enumerate(rows):
            for j in range(nc):
                cell = tbl.cell(i, j)
                cell.text = ""
                p = cell.text_frame.paragraphs[0]
                txt = str(r[j]) if j < len(r) else ""
                numeric = bool(re.fullmatch(r"[-+]?[\d.,]+%?", txt)) and i > 0
                p.alignment = PP_ALIGN.RIGHT if numeric else PP_ALIGN.LEFT
                add_rich(p, txt, size, "FFFFFF" if i == 0 else self.dark, self.font, bold=(i == 0) or None)
                cell.fill.solid()
                cell.fill.fore_color.rgb = rgb(self.accent) if i == 0 else (rgb("F2F2F2") if i % 2 == 0 else rgb("FFFFFF"))
                cell.margin_left = cell.margin_right = Pt(6)
        if row_h * nr > Ht:
            WARNINGS.append(f"slide {self.n} '{spec['title']}': table with {nr} rows may not fit — consider splitting")

    def place_chart(self, s, c, L, T, Wd, Ht, spec):
        kind = c.get("type", "column")
        if kind == "scatter":
            cd = XyChartData()
            for name, pts in c["series"].items():
                ser = cd.add_series(name)
                for x, y in pts:
                    ser.add_data_point(x, y)
            ct = XL_CHART_TYPE.XY_SCATTER_LINES if c.get("lines") else XL_CHART_TYPE.XY_SCATTER
        else:
            cd = CategoryChartData()
            cd.categories = c["categories"]
            for name, vals in c["series"].items():
                cd.add_series(name, vals)
            ct = {"bar": XL_CHART_TYPE.COLUMN_CLUSTERED, "column": XL_CHART_TYPE.COLUMN_CLUSTERED,
                  "barh": XL_CHART_TYPE.BAR_CLUSTERED, "line": XL_CHART_TYPE.LINE_MARKERS,
                  "pie": XL_CHART_TYPE.PIE, "stacked": XL_CHART_TYPE.COLUMN_STACKED}[kind]
        gf = s.shapes.add_chart(ct, L, T, Wd, Ht, cd)
        ch = gf.chart
        ch.font.size = Pt(14)
        ch.font.name = self.font
        multi = len(c["series"]) > 1 or kind == "pie"
        ch.has_legend = multi
        if multi:
            ch.legend.position = XL_LEGEND_POSITION.BOTTOM
            ch.legend.include_in_layout = False
        if c.get("title"):
            ch.has_title = True
            ch.chart_title.text_frame.text = c["title"]
        else:
            ch.has_title = False
        if kind != "pie":
            if c.get("x_title"):
                ch.category_axis.has_title = True
                ch.category_axis.axis_title.text_frame.text = c["x_title"]
            if c.get("y_title"):
                ch.value_axis.has_title = True
                ch.value_axis.axis_title.text_frame.text = c["y_title"]
            if c.get("number_format"):
                ch.value_axis.tick_labels.number_format = c["number_format"]
                ch.value_axis.tick_labels.number_format_is_linked = False
            ch.value_axis.has_major_gridlines = True
            ch.value_axis.major_gridlines.format.line.color.rgb = rgb("D9D9D9")
            if c.get("y_reverse"):
                from pptx.enum.chart import XL_AXIS_CROSSES
                from pptx.oxml.ns import qn
                scaling = ch.value_axis._element.find(qn("c:scaling"))
                orient = scaling.find(qn("c:orientation"))
                orient.set("val", "maxMin")
                ch.value_axis.crosses = XL_AXIS_CROSSES.MAXIMUM  # keeps the x axis at the bottom
            if c.get("data_labels") and kind != "scatter":
                plot = ch.plots[0]
                plot.has_data_labels = True
                if c.get("number_format"):
                    plot.data_labels.number_format = c["number_format"]
                    plot.data_labels.number_format_is_linked = False
        palette = [self.accent, "C55A11", "70AD47", "7F7F7F", "FFC000", "5B9BD5"]
        custom = {k: v.lstrip("#") for k, v in (c.get("colors") or {}).items()}
        if ch.has_legend:
            ch.legend.font.size = Pt(14)
        if kind != "pie":
            for ax in (ch.category_axis, ch.value_axis):
                ax.tick_labels.font.size = Pt(14)
            if c.get("y_min") is not None:
                ch.value_axis.minimum_scale = c["y_min"]
            if c.get("y_max") is not None:
                ch.value_axis.maximum_scale = c["y_max"]
        if kind not in ("pie",):
            for k, ser in enumerate(ch.series):
                col = rgb(custom.get(ser.name, palette[k % len(palette)]))
                if kind in ("line", "scatter"):
                    ser.format.line.color.rgb = col
                    try:
                        ser.marker.format.fill.solid()
                        ser.marker.format.fill.fore_color.rgb = col
                    except Exception:
                        pass
                else:
                    ser.format.fill.solid()
                    ser.format.fill.fore_color.rgb = col

    def place_quote(self, s, text, L, T, Wd, Ht, spec):
        tb = s.shapes.add_textbox(L + Inches(0.5), T, Wd - Inches(1.0), Ht)
        tb.name = "Statement"
        tf = tb.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        add_rich(p, text, 32 if len(text) < 90 else 26, self.accent, self.font, bold=True)

    def build(self, slides):
        if self.meta.get("title"):
            self.title_slide()
        for spec in slides:
            if spec["type"] == "section":
                self.section_slide(spec)
            else:
                self.content_slide(spec)
        self.prs.core_properties.title = self.meta.get("title", "")
        if self.meta.get("author"):
            self.prs.core_properties.author = self.meta["author"]
        return self.prs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("outline", help=".md or .json")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--template", help=".pptx/.potx whose layouts, fonts and colours to use")
    ap.add_argument("--keep-template-slides", action="store_true")
    ap.add_argument("--theme", default="navy", choices=sorted(THEMES))
    ap.add_argument("--accent", help="hex colour overriding the theme, e.g. 1F3864")
    ap.add_argument("--font", default="Calibri")
    ap.add_argument("--ratio", default="16:9", choices=["16:9", "4:3"])
    ap.add_argument("--min-font", type=int, default=14, help="never shrink body text below this")
    ap.add_argument("--no-numbers", action="store_true", help="no footer/slide numbers")
    a = ap.parse_args()
    base = os.path.dirname(os.path.abspath(a.outline))
    with open(a.outline, encoding="utf-8") as fh:
        raw = fh.read()
    meta, slides = (from_json(json.loads(raw), base) if a.outline.lower().endswith(".json") else parse_markdown(raw, base))
    prs = Builder(a, meta).build(slides)
    prs.save(a.output)
    print(f"Wrote {a.output}: {len(prs.slides)} slides", file=sys.stderr)
    for w in WARNINGS:
        print("  ! " + w, file=sys.stderr)
    print("Check: python pptx_render.py " + a.output + " --sheet   (contact sheet of all slides)", file=sys.stderr)


if __name__ == "__main__":
    main()
