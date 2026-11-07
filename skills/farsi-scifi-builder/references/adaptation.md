# Adapting a novel into Persian, and working with the author's review

How to turn an existing (usually English) novel into Persian that reads as if it had been written in Persian, and how to run the review cycle with its author. Learned on a real manuscript; the examples come from the author's handwritten edits to the first chapter.

Contents: 1 Adaptation, not translation · 2 Set up before drafting · 3 Drafting a unit · 4 The review cycle · 5 What authors fix: calibration · 6 Page conventions

## 1. Adaptation, not translation

- **Keep the meaning; rebuild the wording.** Every plot beat, every fact and nearly all dialogue survive. The narration is rebuilt sentence by sentence in Persian order and Persian imagery, not transposed.
- **Decide the depth with the author first.** The options are a close adaptation (same world, native prose), a full move into an Iranian setting (which rewrites the plot's skeleton and invites a political reading), or the same world seen through a Persian lens (for example, an Iranian-born character whose inner life carries the Persian).
- **Keep the Persian lens implicit.** It works through a character's inner life and relationships, not through the plot or explanations. Authors cut lines that announce it (for example «به فارسی»).
- **Bridging is allowed and expected.** Where the original jumps (an arrival with no wait, an object with no setup), add the smallest beat that lets a Persian reader follow, and mark it.

## 2. Set up before drafting

- **Style sheet.** Fill in `assets/style-sheet.md`: registers, dialogue punctuation, ezafe, digits, calendar, pronouns for machines, and an "author preferences" section that grows after each review.
- **Glossary as data.** Keep names, terms, titles and recurring lines (the motif register) in one JSON file, and render a readable table from it. Every recurring line gets one approved Persian form, reused verbatim.
- **Work units.** Split the source into scene-aligned units of about 3,000 words, and keep them in a manifest with a status field.
- **Story bible.** Record characters, ages over time, the timeline, rules of the world, and open questions. Fill gaps from the text before asking the author; then ask only for what the text cannot answer.

## 3. Drafting a unit

1. Read the style sheet, the glossary and the last scene of the previous unit.
2. Draft scene by scene in Persian, from the meaning of the English.
3. Revise (see section 5 and `translationese.md`), then lint with `scripts/farsi_lint.py --fix`.
4. Check that every recurring line appears verbatim.
5. Deliver the text with an **adaptation log**: what was added (marked ⟦+ … ⟧ in the draft), cut or changed, new terms, and the check results.

## 4. The review cycle

1. **Reading copy.** Run `scripts/make_reading_pdf.py draft.md --title "…"` to get a 16:9 two-column PDF. Machine text uses its styles, and proposed additions are highlighted.
2. **Author marks it up by hand** and sends the PDF back. Handwriting is usually flattened into the page, so it is invisible in the text layer and is not stored as annotations.
3. **Find the ink.** Run `scripts/ink_diff.py sent.pdf annotated.pdf`. It writes each marked page with the ink in red, plus close-up crops. Read the red pages first and the crops wherever a mark is small. Check any edit that seems to add new text against the source: it may be the author bridging a gap, not something the draft dropped.
4. **Read every mark before applying any.** List them page by page. Watch for:
   - moves (boxed text with an arrow);
   - global rules written in a margin ("Rule, overruling all comments: …");
   - judgments ("Bad translation");
   - edits that change who acts in a sentence.
5. **Interpret openly.** Where a mark is ambiguous, choose the reading that fits the scene, apply it, and list it in the notes. An edited proposed addition counts as approved; a struck one as rejected.
6. **Clean copy plus notes.** Apply every edit to the source, re-run the checks, and rebuild the PDF with `--notes`. The notes cover:
   - what changed;
   - what you learned about the author's taste;
   - how you will write from now on;
   - where you interpreted marks;
   - open questions (consequences of edits, terms that now conflict).
7. **Record the learning** in the style sheet's author-preferences section and in the glossary before drafting the next unit. Ask the open questions one at a time if the author prefers.

## 5. What authors fix: calibration

One full review of the first chapter showed what this author changes. Treat these as the defaults until a later review says otherwise.

- **The word people actually use.** «چادرِ اکسیژن», not «سرپوشِ تنفسی». The same goes for «دستگاهِ تصفیه» over «سامانه», «مترو» over «قطار», «بدن» over «تن», «دید» over «تماشا کرد», «حرکت کرد» over «جنبید» and «دیشب» over «شب». Coined, technical or literary words lose to everyday ones.
- **Explicit beats compressed.** Authors add the small words that make the logic obvious: «پرنده **زیاد** دیده بود»، «**حسِ** پیروزی»، «طبقه‌ی **بیمارانِ** تنفسی»، «به **نیا** نزدیک‌تر شد». They also restore antecedents («همین **روحیه‌ی قویِ مارا**») and complete clipped lines («ولی خودِ پرنده یادت نیست»).
- **Clarity beats purity.** «یک» for a generic role or a count (از یک مادر، یک اتاق), «به‌عنوانِ» and «تا وقتی که» all come back if you strip them. Remove calques, not clarifying words.
- **Concrete images instead of English abstractions.**
  - "The first absence her body reached for" → «اولین کسی که بی‌اختیار دنبالش می‌گشت».
  - "A piece of debris" → «یک کیسه‌ی پلاستیکِ زباله‌ی بازمانده از سال‌های قبل».
  - "Her skin tightened" → «قلبش به تپش افتاد».
- **Natural verbs.** «لب‌هایش را به هم فشرد» rather than «لب‌هایش به هم فشرده شد». Passive is fine where Persian uses it: «روی شیشه نمایش داده می‌شد».
- **Flow over fragments.** «…در کار بود و فردا و پس‌فردا». Keep fragments only where they carry tension.
- **Dialogue that sounds alive and a little dry.** «حوصله‌سربر» rather than «کسل‌کننده». A wry literal answer («که تفسیرش کنیم») over a formal one.
- **Wordplay is rebuilt, not mimicked.** A child's writing quirk tied to English capitals became a child who drops a word: «من مامان بیرون».

## 6. Page conventions

- **Markup.** Machine text and handwriting use pandoc custom styles: `::: {custom-style=Screen}` blocks, `[text]{custom-style=ScreenChar}` inline, `Hand` for handwriting, and a style ending in `Voice` for a machine's speech. Write attributes without quotes; the linter leaves `{…}` alone.
- **Machine voices** get a consistent treatment set by the author. In the first book, the AI's speech is in « », bold and centred, and its screen text is bold.
- **Nested quotes** use “ ” inside « ».
- **Word export.** pandoc with `-M dir=rtl -M lang=fa` keeps every paragraph right-to-left and carries the custom styles into Word.
