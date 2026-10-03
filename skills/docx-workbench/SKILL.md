---
name: docx-workbench
description: Create, read, edit, review and convert Word documents (.docx) with tested Python scripts. Use this whenever a task involves a Word file — writing a report, letter, thesis chapter or manual; filling a template with {{placeholders}} or mail-merging from data; find-and-replace that keeps formatting; suggesting edits as tracked changes or adding comments; accepting/rejecting tracked changes or summarising reviewer comments; comparing two versions; converting between .docx, PDF, Markdown, .doc and .odt. Trigger even when the user just says "Word doc", "track changes", "redline", "my manuscript" or attaches a .docx.
license: MIT (see LICENSE)
---

# DOCX Workbench

A toolkit for Word documents. The scripts cover the common jobs, and each reference file goes deeper on one area. Every script is a standalone Python CLI, so run it with `--help` to see the options.

Paths below are relative to this skill's folder, the directory that holds this SKILL.md. Call scripts by their full path. Outputs go next to the input file unless you pass `-o`. Always give `-o` with a path in the user's folder, and never write into the skill folder.

## Setup

```bash
pip install python-docx lxml pypdfium2      # python-docx ≥ 1.2 is needed for comments
# optional system tools: pandoc (Markdown/equations/footnotes), LibreOffice (PDF/PNG/.doc conversion,
# TOC page numbers); install libreoffice-math too if you want equations to appear in renders
```

## Start by inspecting

```bash
python scripts/docx_inspect.py report.docx           # outline, styles, tables, sections, revisions, comments, placeholders
```

The output tells you:

- whether the document uses real heading styles. If it doesn't, the headings are manual bold text, and a table of contents won't pick them up.
- whether it already has tracked changes or comments. Don't silently discard someone else's review.
- what page setup it uses.
- which `{{placeholders}}` it expects.

## Pick the path

| Goal | Use | Details |
|---|---|---|
| Read the content, or turn it into Markdown | `scripts/docx_convert.py in.docx --to md` | references/reading-and-converting.md |
| Write a new document from content you've drafted | Markdown → `docx_convert.py --to docx --reference-doc house.docx` | references/creating-documents.md |
| Build a document that needs precise layout (cover page, landscape tables, fields) | python-docx recipes | references/creating-documents.md |
| A consistent house style for generated documents | `scripts/docx_make_reference.py` | references/creating-documents.md |
| Cover page, table of contents with page numbers, "Page X of Y", A4 | `scripts/docx_finish.py` | references/creating-documents.md |
| Fill a template, one per record (mail merge) | `scripts/docx_fill_template.py` | references/editing-and-review.md |
| Change wording but keep formatting | `scripts/docx_replace.py` | references/editing-and-review.md |
| Suggest edits the author can accept or reject, and add comments | `scripts/docx_redline.py` | references/editing-and-review.md |
| List, accept or reject tracked changes, or read the comments | `scripts/docx_revisions.py` | references/editing-and-review.md |
| See what changed between two versions | `scripts/docx_compare.py` | references/editing-and-review.md |
| Convert to PDF or PNG, or from .doc/.odt/.rtf | `scripts/docx_convert.py` | references/reading-and-converting.md |
| Something none of these cover (text boxes, footnotes XML, numbering) | edit the XML directly | references/ooxml-notes.md |

## Working principles

**Leave the original untouched.** Write `report_v2.docx`, `report_reviewed.docx` and so on. The scripts refuse to overwrite their input.

**Use styles, not direct formatting.** Headings should use the Heading 1–3 styles, body text Normal, and captions Caption. Then the table of contents, navigation pane, numbering and any later restyling all work. When editing a user's document, reuse its styles. Don't invent new ones.

**Edit through the scripts, not by retyping paragraphs.** Word splits text into "runs" in places you can't see, so a placeholder like `{{client_name}}` may sit across three runs. The replace, fill and redline scripts match across run boundaries and keep the formatting. Rebuilding a paragraph from `p.text` loses bold, italics, links and comments.

**Use review mode when someone else owns the text.** If the user asks you to "suggest", "review", "edit my manuscript" or "mark up", use `docx_redline.py` so every change is a tracked change they can accept or reject. Use `docx_replace.py` only when they want the change made outright, for example "update the client name everywhere".

**Check the result.** Re-run `docx_inspect.py` on the output. It reports the placeholders left, revisions, comments, equations, footnotes and the paper size. Then render pages with `docx_convert.py out.docx --to png -o renders` and look at them.

LibreOffice renders a close approximation of Word, so small differences in line breaks are normal. Comments don't appear in renders, so check them with `docx_revisions.py comments`. Equations only appear if libreoffice-math is installed. Otherwise confirm them with `docx_inspect.py` ("Also contains: N equations").

## Quick recipes

```bash
# Report from Markdown in a house style (headings, tables, equations, footnotes, citations all supported by pandoc)
python scripts/docx_make_reference.py -o house.docx --font "Calibri" --heading-color 1F3864 --a4    # 1F3864 = dark blue
python scripts/docx_convert.py report.md --to docx --reference-doc house.docx -o body.docx
python scripts/docx_finish.py body.docx -o report.docx --a4 --cover --toc --page-numbers --report-no GL-2026-014

# Fill a template; rows containing {{bh.*}} repeat once per item of the "bh" list
python scripts/docx_fill_template.py template.docx data.json -o filled.docx --strict

# Tracked-change review with comments (author = the person the review is from)
python scripts/docx_redline.py draft.docx edits.json -o draft_reviewed.docx --author "R. Kalatehjari"

# Summarise reviewer comments and changes, then make a clean copy to send out
python scripts/docx_revisions.py comments paper_reviewed.docx
python scripts/docx_revisions.py list paper_reviewed.docx           # each change in context: 'old' → 'new', under which heading
python scripts/docx_revisions.py accept paper_reviewed.docx -o paper_clean.docx --stop-tracking --drop-comments

# What changed between versions?
python scripts/docx_compare.py thesis_v3.docx thesis_v4.docx -o changes.md

# PDF and a quick visual check
python scripts/docx_convert.py report.docx --to pdf -o report.pdf
python scripts/docx_convert.py report.docx --to png --pages 1-2 -o renders
```

## Delivering results

Say what you changed, with counts: placeholders filled, replacements made, tracked changes added, comments added. A "clean copy" means no tracked changes and no comments, so use `--drop-comments`, which deletes the comment text from the file too. If a comment is still unresolved, ask before you drop it, or deliver one copy with comments and one without. Mention it if the paper size doesn't suit the user, for example US Letter for someone in New Zealand. Point out anything you left alone, such as an unfilled placeholder, text inside a text box, or a match that crossed a hyperlink. For reviews, give a short summary of the main suggestions. The author shouldn't have to open every comment to see the main points.
