# Editing, templates and review

## Contents
1. Find and replace (silent edits)
2. Templates and mail merge
3. Suggesting edits as tracked changes, plus comments
4. Handling a reviewed document: list, accept, reject, comments
5. Comparing versions
6. Editing beyond text

## 1. Find and replace

```bash
python scripts/docx_replace.py in.docx --find "Lot 12" --dry-run                  # see each match in context
python scripts/docx_replace.py in.docx -o out.docx --find "Lot 12" --replace "Lot 14"
python scripts/docx_replace.py in.docx -o out.docx --map renames.json             # {"old": "new", ...} in order
python scripts/docx_replace.py in.docx -o out.docx --regex --find "(\d+) kPa" --replace "\1 kN/m²"
```

- Matches can span runs inside one paragraph. The replacement takes the formatting of the run where the match begins.
- Body, tables (including nested ones), headers and footers are all covered. Text boxes, footnotes and comments aren't. For those, see section 6.
- Do a `--dry-run` first whenever the find string is short or generic. Use `--whole-word` so that "BH1" doesn't also match "BH10".

## 2. Templates and mail merge

Template syntax:

| In the .docx | Data (JSON) | Result |
|---|---|---|
| `{{client_name}}` | `"client_name": "Auckland Council"` | text replaced, keeping the placeholder's formatting |
| `{{client.address}}` | `"client": {"address": "..."}` | dotted path |
| A table row containing `{{bh.id}}`, `{{bh.depth}}` | `"bh": [{"id": "BH1", "depth": "6.5"}, ...]` | the row is repeated once per item |
| `{{#}}` inside a repeated row | | the item number (1, 2, 3 …) |
| `{{logo}}` alone in its paragraph | `"logo": {"image": "logo.png", "width_cm": 4}` | the picture is placed there |

```bash
python scripts/docx_inspect.py template.docx            # the "Placeholders:" line lists what the template expects
python scripts/docx_fill_template.py template.docx data.json -o filled.docx --strict
```

- Numbers are inserted exactly as they appear in the JSON. Pass strings when you want specific formatting (`"6.50"`, `"1,250"`, `"3 October 2026"`).
- `--strict` stops with an error if any placeholder has no value. Without it, the script leaves the placeholder and warns, which suits drafts.
- **To make a template from an existing document**, replace the variable parts with placeholders using `docx_replace.py` (for example `--find "Auckland Council" --replace "{{client_name}}"`). The styles, logos and headers all stay as they were.

**Mail merge** (one document per row of a CSV):

```python
import csv, json, subprocess, os
os.makedirs("letters", exist_ok=True)
for i, row in enumerate(csv.DictReader(open("recipients.csv", encoding="utf-8-sig")), start=1):
    json.dump(row, open("_row.json", "w"))
    name = "".join(c for c in row["name"] if c.isalnum() or c in " -_").strip().replace(" ", "_")
    subprocess.run(["python", "scripts/docx_fill_template.py", "letter_template.docx", "_row.json",
                    "-o", f"letters/{i:03d}_{name}.docx", "--strict"], check=True)
```

To get PDFs, run `docx_convert.py --to pdf` on each output. To get one combined PDF, merge the PDFs afterwards (pdf-workbench `pdf_pages.py merge`).

## 3. Suggesting edits as tracked changes, plus comments

Use this whenever the text belongs to someone else: a student's thesis, a co-author's manuscript, or a contractor's report.

```json
[
  {"find": "Lot 12", "replace": "Lot 14", "comment": "Per the survey plan dated 12 Aug"},
  {"find": "very ", "replace": ""},
  {"find": "groundwater table", "comment": "State when it was measured", "occurrence": 1},
  {"find": "(\\d+) kPa", "replace": "\\1 kN/m²", "regex": true}
]
```

```bash
python scripts/docx_redline.py manuscript.docx edits.json -o manuscript_RK.docx --author "R. Kalatehjari" --initials RK
```

- An entry with `replace` creates a tracked deletion plus insertion. `"replace": ""` is a pure deletion. An entry with only `comment` adds a comment without changing anything.
- **Changes are word-level by default.** `"Lot 12" → "Lot 14"` appears as Lot ~~12~~ <u>14</u>, which is how reviewers mark up by hand. So you can give a whole phrase as `find` for context, and only the words that differ are marked. Set `"minimal": false` to strike and replace the whole match.
- `occurrence` limits the edit to the Nth match, counted through the whole document as it stands when that edit runs. The default is `"all"`. Edits run in file order, so a later edit sees the text left by earlier ones. Put comment-only entries before replacements that touch the same words. To get occurrence numbers, run `docx_replace.py --find "…" --dry-run`, which lists the matches as #1, #2 and so on.
- Make `find` strings specific, about 3–8 words, so they match exactly where you mean. Check them first with `docx_replace.py --dry-run`.
- `--track-future` turns on Word's Track Changes, so the author's own edits are tracked as well.
- When a match crosses a hyperlink, a field or an existing tracked change, it's skipped and reported. Put that suggestion in a comment instead.
- `--author` is the name Word shows on each change. Use the reviewer's name: the user's own name when it's their review, or the role they asked for ("Supervisor"). Tell them they can change it if they want.
- Comments don't appear in PDF or PNG renders. Check them with `docx_revisions.py comments out.docx`. Check tracked changes with `docx_revisions.py list` or a render, where changes show in colour.
- Comments can't go in headers or footers. Mention issues there, such as a wrong project name, in your reply.

**Writing good review comments.** Say what the problem is and why, then suggest a fix: "Units missing: give su in kPa", not "unclear". Group repeated issues. Comment once ("Applies throughout: use SI units") rather than 40 times. End with a summary for the author in your reply: the main issues, then the minor ones.

**Review checklist** (technical reports and theses). Check:
- the structure: every scope item has results, and the conclusions follow from them.
- that terms and abbreviations are defined at first use.
- that units, datums and standards are given.
- that each table and figure has a numbered caption, is cited in the text and is interpreted.
- that headings use styles (`docx_inspect.py` shows "manual bold" headings), and that the paper size is right for the audience.
- that references are complete.
- that no placeholders or leftover template text remain.
Things a tracked change or comment can't express (page size, heading styles, header text) go in your summary.

## 4. Handling a reviewed document

```bash
python scripts/docx_revisions.py list reviewed.docx                 # who changed what
python scripts/docx_revisions.py comments reviewed.docx --json      # comments + the text each refers to
python scripts/docx_revisions.py accept reviewed.docx -o clean.docx --stop-tracking
python scripts/docx_revisions.py accept reviewed.docx -o v2.docx --author "Supervisor"   # only one reviewer's changes
python scripts/docx_revisions.py reject reviewed.docx -o original.docx
```

- Accept and reject cover insertions and deletions, moves, inserted or deleted paragraph marks, table rows and formatting changes, in the body, headers, footers, footnotes and endnotes.
- Comments stay unless you add `--drop-comments`. That option removes the comment anchors **and** the comments part, so no comment text is left anywhere in the file. Use it for copies that go to clients or journals.
- When a comment was attached to text that has since been deleted, accepting the deletion leaves the comment without any text. `comments` then says "(anchor text no longer present)".
- `list` prints each change with its context. Pairs of deletion and insertion come out as `'old' → 'new'`, together with the heading they sit under and the paragraph as it reads once accepted. Use this to write the summary.
- Before accepting everything, give the user that summary. Accepting can't be undone in the output file, although the input stays unchanged.

**Responding to reviewers** (for example on a journal manuscript): pull the comments as JSON, draft a response table (comment, response, change made with its location), then make the agreed changes with `docx_redline.py`. That way the editor sees them tracked.

## 5. Comparing versions

```bash
python scripts/docx_compare.py v3.docx v4.docx -o changes.md
```

The output lists every changed, added and removed paragraph, with word-level `~~deleted~~ **inserted**` marks. If either file contains tracked changes, accept them first so you compare the final text. For a native Word redline, tell the user about Word's Review → Compare.

## 6. Editing beyond text

| Target | How |
|---|---|
| Text boxes and shapes | Their text is in `w:txbxContent` inside `w:drawing` or `mc:AlternateContent`. Iterate `doc.element.body.iter(qn("w:txbxContent"))`, wrap each `w:p` in `Paragraph(p, doc)`, and use `replace_in_paragraph` from `_docx_common.py` |
| Footnotes and endnotes | Separate parts (`word/footnotes.xml`) that python-docx doesn't expose. Use the XML approach in ooxml-notes.md |
| Fill or shading of table cells, borders | ooxml-notes.md, and the `shade()` helper in creating-documents.md §4 |
| Update fields (TOC, numbering) | Open in Word and press F9, or use `w:updateFields` (creating-documents.md §5). Converting with LibreOffice also refreshes the TOC in the PDF |
| Change a style everywhere (font, size) | Edit the style (`doc.styles["Normal"].font.name = …`), not each paragraph |
| Delete a paragraph | `p._p.getparent().remove(p._p)` |
| Insert a paragraph after another | `new = OxmlElement("w:p"); p._p.addnext(new); para = Paragraph(new, p._parent); para.add_run("text"); para.style = p.style` |
