---
name: pptx-workbench
description: Build, edit, review and convert PowerPoint decks (.pptx) with tested Python scripts — write the talk as a Markdown outline and get a clean 16:9 deck (or one in your own template) with native bullets, tables, editable charts, images, section dividers and speaker notes; then QA it for overflowing text, tiny fonts, missing alt text, low-res images and leftovers, and render a contact sheet to check it visually. Use this whenever the user wants slides or a presentation file: a conference talk, lecture, client briefing, thesis defence, lab meeting update; filling a .pptx template; extracting or summarising what's in a deck; replacing text across slides; reordering/deleting/merging slides; converting to PDF. Trigger on "slides", "deck", "PowerPoint", "pptx", "presentation" or an attached .pptx.
license: MIT (see LICENSE)
---

# PPTX Workbench

A toolkit for PowerPoint. The scripts do the mechanics, and the reference files hold the design guidance and recipes. Every script is a standalone Python CLI, so run it with `--help` to see the options.

Paths such as `scripts/pptx_build.py` are relative to this skill's folder, the directory that holds this SKILL.md, so prefix them with that folder's path when you run them. Always pass `-o` with a path in the user's folder, because outputs otherwise go next to the input. Never write into the skill folder.

## Setup

```bash
pip install python-pptx pillow pypdfium2      # pypdfium2: renders only
# LibreOffice (impress) is needed for PDF/PNG renders and contact sheets
```

## Pick the path

| Goal | Use | Details |
|---|---|---|
| A new deck from content you've drafted | write a Markdown outline → `scripts/pptx_build.py` | references/building-decks.md |
| A new deck in the user's corporate or university template | `pptx_build.py --template their.pptx` | references/building-decks.md |
| What makes slides good (structure, density, charts) | — | references/design-principles.md |
| What's in an existing deck | `scripts/pptx_inspect.py`, `scripts/pptx_text.py` | references/editing-decks.md |
| Change wording everywhere, fill `{{placeholders}}`, or replace placeholder text with bullets | `scripts/pptx_replace.py` (a `\n` in the replacement makes new paragraphs) | references/editing-decks.md |
| Delete, reorder, duplicate, hide or merge slides; set notes | `scripts/pptx_slides.py` | references/editing-decks.md |
| Check a deck before it's shown or sent | `scripts/pptx_check.py`, then `pptx_render.py --sheet` | references/design-principles.md |
| PDF, slide PNGs, one-page overview | `scripts/pptx_render.py --pdf / --png / --sheet` | — |

## Working principles

**Plan the story before the slides.** Decide the audience, the time and the 3–5 points you want people to remember. Then draft the outline: about one slide per minute for a talk, with one message per slide and a title that states it ("Both cases fall below the 1.5 target", not "Results"). design-principles.md has structures for common talk types.

**Write the outline in Markdown and let the builder lay it out.** `pptx_build.py` turns `##` headings, bullets, images, tables, chart blocks and `Notes:` lines into consistent slides. It uses native bullets and editable charts, keeps margins, and fits images by aspect ratio. Hand-placing shapes is slow and inconsistent, so do it only for one-off visuals.

**Put detail in speaker notes, not on the slide.** Aim for ≤ 6 bullets and ≤ 40 words per slide, with body text ≥ 18 pt. When the builder says it shrank text or that text overflows, split the slide rather than accept small type.

**Use real data and real figures.** Make charts from actual numbers with a `chart` block, so they stay editable. Use figures at 150 dpi or more. The builder and `pptx_check.py` warn about blurry images. Every chart needs axis titles with units.

**Always look at the deck, and read it critically.** Run `pptx_check.py deck.pptx`, then `pptx_render.py deck.pptx --sheet`. Open the contact-sheet PNG and look for overflow, overlaps, empty areas and inconsistent styling before you deliver. LibreOffice renders close to PowerPoint, but fonts can be substituted.

Then check the content. Do the numbers in the text match the charts and tables? Does each figure show what its caption claims? Are any figures placeholders or duplicates? Do the notes refer to slides or appendices that don't exist? The check can't judge any of this. design-principles.md has the checklist.

**Respect the user's template and decks.** Build with `--template` so the user's masters, fonts and colours apply. When editing their deck, change only what's asked, keep a copy, and confirm with `pptx_text.py` or `pptx_inspect.py` afterwards.

## Quick recipes

```bash
# Outline → deck (built-in clean design; themes: navy, teal, charcoal, forest, maroon; or --accent HEX)
python scripts/pptx_build.py talk.md -o talk.pptx --theme navy
python scripts/pptx_check.py talk.pptx
python scripts/pptx_render.py talk.pptx --sheet -o talk_overview.png     # look at it

# Same outline in the user's template
python scripts/pptx_build.py talk.md -o talk_uni.pptx --template university_template.pptx

# Summarise an existing deck / reuse its content
python scripts/pptx_text.py their_deck.pptx -o their_deck.md

# Fill a template deck's {{placeholders}}; replace wording everywhere including notes
python scripts/pptx_replace.py template.pptx -o client.pptx --fill client.json --strict
python scripts/pptx_replace.py deck.pptx -o deck_v2.pptx --find "Lot 12" --replace "Lot 14" --notes
python scripts/pptx_replace.py template.pptx -o t2.pptx --find "Lorem ipsum dolor" --replace $'Findings\nOptions\nRecommendation'   # 3 bullets

# Restructure
python scripts/pptx_slides.py reorder deck.pptx --order 1,2,5,3,4,6- -o deck_v2.pptx
python scripts/pptx_slides.py delete deck.pptx --slides 7-9 -o short.pptx

# Handout PDF
python scripts/pptx_render.py talk.pptx --pdf -o talk.pdf
```

## Delivering results

Give the slide count and the structure, for example "12 slides: title, 3 sections, summary". List anything the builder or check flagged that you left for the user, such as a low-resolution figure they should replace. Mention that speaker notes are included where you wrote them. Share the contact-sheet PNG so the user can see the deck without opening it.
