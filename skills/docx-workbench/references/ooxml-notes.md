# Working with the underlying XML (OOXML)

Use this when python-docx and the scripts don't reach what you need. A .docx is a ZIP archive of XML parts.

## Map of a .docx

| Part | Holds |
|---|---|
| `word/document.xml` | the body: `w:body` → `w:p` (paragraphs), `w:tbl` (tables), and the final `w:sectPr` |
| `word/styles.xml` | paragraph, character and table styles |
| `word/numbering.xml` | list and heading numbering (`w:abstractNum` + `w:num`) |
| `word/header1.xml`, `footer1.xml` … | headers and footers, linked from each `w:sectPr` |
| `word/footnotes.xml`, `endnotes.xml` | notes. The body has `w:footnoteReference w:id="n"` |
| `word/comments.xml` | comment text. The body has `w:commentRangeStart/End` and `w:commentReference` |
| `word/settings.xml` | `w:trackRevisions`, `w:updateFields`, compatibility settings |
| `word/media/*` | images, referenced through relationships (`r:embed`) |
| `docProps/core.xml` | title, author, created and modified dates |

The text model is: paragraph `w:p` contains properties `w:pPr` (style, numbering, spacing) and runs `w:r`. Each run contains properties `w:rPr` (bold, italic, font, size) and content: `w:t` for text, `w:tab`, `w:br`, `w:drawing`, `w:fldChar` and so on. Tracked changes wrap runs in `w:ins` or `w:del`. Deleted text sits in `w:delText`.

## Safe editing pattern

```python
import zipfile, shutil
from lxml import etree
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}

src, dst = "in.docx", "out.docx"
with zipfile.ZipFile(src) as zin:
    xml = etree.fromstring(zin.read("word/footnotes.xml"))
    for t in xml.iterfind(".//w:t", NS):
        if t.text and "Lot 12" in t.text:
            t.text = t.text.replace("Lot 12", "Lot 14")
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/footnotes.xml":
                data = etree.tostring(xml, xml_declaration=True, encoding="UTF-8", standalone=True)
            zout.writestr(item, data)
```

Rules that prevent corrupt files:

- Copy every other part byte for byte, in the original order. `[Content_Types].xml` must stay.
- Keep `xml:space="preserve"` on any `w:t` whose text starts or ends with a space.
- Element order inside `w:pPr`, `w:rPr` and `w:sectPr` is fixed by the schema. Insert new children in the right place. For example, in `w:rPr` the font (`w:rFonts`) comes before `w:b`, which comes before `w:sz`. If you're unsure, look at a Word-made document.
- IDs (`w:id` on revisions, comments and bookmarks) must be unique within their kind.
- After editing, open the file with python-docx and convert it with `docx_convert.py --to pdf`. If either fails, the XML is broken.

Inside python-docx you can reach the same XML: `doc.element` (body), `paragraph._p`, `run._r`, `table._tbl`, `section._sectPr`, and `doc.part.package.iter_parts()` for other parts. Parts that python-docx doesn't model, such as footnotes, appear as generic parts. Read them with `etree.fromstring(part.blob)` and write them back with `part._blob = etree.tostring(...)`. `docx_revisions.py` does this.

## Recipes

**Bold a label in every table's first column:**

```python
for t in doc.tables:
    for row in t.rows:
        for r in row.cells[0].paragraphs[0].runs:
            r.bold = True
```

**Find text in text boxes:**

```python
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph
for box in doc.element.body.iter(qn("w:txbxContent")):
    for p_el in box.iter(qn("w:p")):
        print(Paragraph(p_el, doc).text)
```

**Turn on line numbering** (useful for manuscripts under review):

```python
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
ln = OxmlElement("w:lnNumType"); ln.set(qn("w:countBy"), "1"); ln.set(qn("w:restart"), "continuous")
sectPr = doc.sections[0]._sectPr
pgMar = sectPr.find(qn("w:pgMar"))
(pgMar.addnext if pgMar is not None else sectPr.append)(ln)  # must come after w:pgMar
```

**Double line spacing everywhere** (common for manuscripts): `doc.styles["Normal"].paragraph_format.line_spacing = 2.0`.

**Numbered headings.** Reuse a template whose Heading styles already link to a multilevel list. That's far more reliable than building `w:abstractNum` by hand. To check whether a style is numbered, look for `w:numPr` in `doc.styles["Heading 1"].element.pPr`.
