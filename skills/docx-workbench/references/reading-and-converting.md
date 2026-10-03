# Reading and converting Word documents

## Reading content

| Need | Command |
|---|---|
| Structure at a glance | `python scripts/docx_inspect.py in.docx` (`--json` for scripts) |
| Full text with headings, lists, tables, images and equations | `python scripts/docx_convert.py in.docx --to md -o in.md` |
| Plain text only | `python scripts/docx_convert.py in.docx --to txt` |
| Reviewer comments, with the text they refer to | `python scripts/docx_revisions.py comments in.docx` |
| Tracked changes | `python scripts/docx_revisions.py list in.docx` |

Notes on the Markdown export (pandoc):

- The Title style becomes YAML front matter (`title:`), and headings become `#` levels.
- Images are written to `<name>_media/`, next to the `.md` file.
- Equations come out as LaTeX (`$\phi' = 32^\circ$`). This is the best way to read them, because LibreOffice renders don't show Word equations.
- Tracked changes are **accepted** in the export (`--track-changes=accept`). If you need to see the proposed edits themselves, read them with `docx_revisions.py list`.
- Text boxes, shapes and SmartArt are often missing. If `docx_inspect.py` shows few words but the rendered page is full, look in text boxes (ooxml-notes.md).
- Without pandoc, the script falls back to a basic converter. It handles headings, lists, tables, bold and italic, but not images, equations or footnotes.

To read with python-docx in body order, paragraphs and tables interleaved:

```python
import docx
from docx.table import Table
from docx.text.paragraph import Paragraph
d = docx.Document("in.docx")
for block in d.element.body.iterchildren():
    tag = block.tag.rsplit("}", 1)[1]
    if tag == "p":
        p = Paragraph(block, d); print(p.style.name, "|", p.text)
    elif tag == "tbl":
        t = Table(block, d); print([[c.text for c in r.cells] for r in t.rows])
```

`d.paragraphs` alone skips everything inside tables, so use the loop above, or `iter_paragraphs()` from `scripts/_docx_common.py`.

## Converting

Without `-o`, the output is written next to the input (`report.pdf`, `report.md` + `report_media/`, `renders/`). Pass `-o` to choose a location.

```bash
python scripts/docx_convert.py report.docx --to pdf              # LibreOffice, ~2 s per document
python scripts/docx_convert.py report.docx --to png --pages 1-3 -o renders   # visual check
python scripts/docx_convert.py legacy.doc --to docx              # .doc / .rtf / .odt → .docx
python scripts/docx_convert.py notes.md --to docx --reference-doc house.docx
python scripts/docx_convert.py notes.md --to pdf --reference-doc house.docx   # via .docx, keeps the styling
python scripts/docx_convert.py report.pdf --to png               # render an existing PDF without re-converting
python scripts/docx_convert.py report.docx --to html|odt|txt|md
```

- **PDF fidelity.** LibreOffice is close to Word, but fonts that aren't installed get substituted, so line breaks and page counts can shift. When the exact look matters, such as a thesis submission, tell the user to export the final PDF from Word. Use the LibreOffice PDF for checking and drafts.
- **Legacy .doc files.** Convert them to .docx first. python-docx can't open .doc.
- **Batch.** Loop in the shell. Each call starts LibreOffice with a private profile, so calls never clash with a copy the user has open:
  ```bash
  for f in *.docx; do python scripts/docx_convert.py "$f" --to pdf; done
  ```
- **PDF to Word.** That conversion is lossy. Use a dedicated PDF skill (pdf-workbench) to extract the text and tables, then rebuild the document with this skill.
