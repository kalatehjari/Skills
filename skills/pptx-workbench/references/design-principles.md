# Designing slides that work

## Structure first

| Talk | Slides | Shape |
|---|---|---|
| Conference talk (12–15 min) | 10–14 | Title → problem and why it matters → gap and aim → method (1–2) → key results (3–5) → implications → conclusions (3 bullets) → thanks and contact |
| Lab or research group update (10 min) | 6–8 | Last time → what I did → results (with honest problems) → next steps → questions or asks |
| Thesis defence (30–45 min) | 25–40 | Context → research questions → one section per chapter (aim, method, key result, contribution) → synthesis → limitations → future work |
| Client or stakeholder briefing | 8–12 | **Recommendation first** → site or situation → findings → options with cost and risk → recommendation and next steps |
| Lecture (50 min) | 25–35 | Learning outcomes → concept → worked example → check question (repeat) → summary |

A good rule of thumb is about one slide per minute, plus a title slide and a closing slide.

## One message per slide

- **The title is the message**, written as a sentence: "Factor of safety falls below 1.5 when the water table rises". "Results 2" tells the audience nothing.
- Use **≤ 6 bullets and ≤ 40 words** per slide, and keep bullets to 1 line where possible. Put the rest in speaker notes.
- When a slide needs a second message, make a second slide.
- Use parallel grammar for bullets: start each with a noun, or each with a verb.

## Make it readable from the back of the room

- Body text ≥ 18 pt (24 pt preferred), titles 28–36 pt, and nothing below 14 pt. Table text can go down to 14 pt if needed.
- Use high contrast: dark text on a light background, or the reverse. No text over busy photos.
- Use at most 2 fonts and 1 accent colour, plus grey. Use colour to point at things, not to decorate.
- Leave space around content. Crowded slides look harder than they are.

## Figures, tables and charts

- **Figures carry the evidence.** Make them large: they should fill the slide below the title. Use 150 dpi or more (300 for print). Re-export from the source with large fonts. Axis labels at 8 pt in a paper become unreadable on a slide.
- **Put units on every axis** ("Depth (m)"), and in table headers rather than in cells.
- **Highlight the point**: an accent colour on the key series, an annotation ("target 1.5"), or grey for everything else.
- **Simplify tables.** Show ≤ 6 rows and ≤ 5 columns on a slide, with a consistent number of decimals per column and numbers right-aligned. Put full tables in an appendix or handout.
- **Chart choice:** use bars to compare categories, lines for trends over time, scatter for relationships, and depth profiles with depth downwards. Avoid 3D, pie charts with more than 5 slices, and dual axes unless they're essential.
- Cite data and figure sources in small text under the figure, for example "(after Smith 2020)".

## Accessibility

- Every slide has a unique title in a real title placeholder. Screen readers, outline view and PowerPoint's accessibility checker rely on it, and `pptx_build.py` creates one. `pptx_check.py` reports `no-title` when a deck uses plain text boxes as titles.
- Every picture has alt text. The builder uses the caption, and `pptx_check.py` flags missing ones.
- Don't rely on colour alone. Use labels and line styles too, because about 1 in 12 men is colour-blind.
- Reading order follows creation order. The builder adds the title first.

## Before delivering: the QA loop

1. Run `python scripts/pptx_check.py deck.pptx` and fix everything except judgement calls.
2. Run `python scripts/pptx_render.py deck.pptx --sheet` and look at the PNG:
   - Is anything cut off, overlapping or too small?
   - Do all the slides look like one deck, with the same title position, fonts and colours?
   - Are images sharp, and are charts readable at thumbnail size? If you can read it in the contact sheet, the room can read it on screen.
3. Read the titles in order with `pptx_text.py`. They should tell the story on their own.
4. Do the content review that no script can do:
   - Numbers in the text match the charts and tables, for example "below the 1.5 target" when the chart shows two different targets.
   - Each figure shows what its caption says. Look for placeholder or duplicate pictures, which `pptx_check.py` flags as `duplicate`.
   - Claims match the evidence. If the notes say "BH2 is weaker" but the plot shows it plotting higher, ask.
   - Notes and slides don't refer to things that don't exist, such as appendices or slide numbers.
   - Every chart axis has a title with units (`chart-axes`). Checks and recommendations are stated.
5. Check the timing: count the slides against the time slot.

`pptx_check.py` defaults to 40 words and 6 bullets per slide (tables excluded). For reading decks or handouts, relax these with `--max-words 120 --max-bullets 10`. Footers and slide numbers are exempt from the font-size check.

`pptx_check.py` estimates text height from font size and box size. That's a heuristic, so the render is the final word. An `overlap` finding is fine when it's deliberate, such as a callout placed on a figure.
