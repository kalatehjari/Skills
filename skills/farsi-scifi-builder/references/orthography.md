# Persian orthography for fiction

What clean Persian text looks like on the page, and why each rule matters. `scripts/farsi_lint.py` checks most of it.

Contents: 1 Characters · 2 Half-space · 3 Ezafe after silent ه · 4 Punctuation · 5 Dialogue layout · 6 Numbers and dates · 7 Diacritics · 8 Mixed scripts · 9 Files and fonts

## 1. Characters

| Use | Not | Code points |
|---|---|---|
| ی | ي ى | U+06CC, not U+064A or U+0649 |
| ک | ك | U+06A9, not U+0643 |
| ۰۱۲۳۴۵۶۷۸۹ | ٠١٢٣٤٥٦٧٨٩ | U+06F0–06F9, not U+0660–0669 |

The Arabic forms look almost identical but break search, sorting and spell-check. They usually arrive in text pasted from Arabic sources or typed on an Arabic keyboard layout.

- ة (tā marbūṭa) belongs to Arabic. In Persian write ه or ت (رحمت), except inside quoted Arabic.
- Tatweel (ـ) doesn't belong in prose. Stretching a word for a shout is a deliberate effect; use it rarely if at all.

## 2. Half-space (نیم‌فاصله, ZWNJ U+200C)

The half-space keeps the parts of one word together without joining the letters. A full space instead breaks line-wrapping (می at the end of one line, روم at the start of the next) and search. Writing the parts joined (میروم) is common in casual typing but not in edited prose.

Use a half-space:

- after the verb prefixes می‌ and نمی‌: می‌روم، نمی‌دانست
- before plural ها/های: ستاره‌ها، کهکشان‌های دور (after a non-joining letter such as ر the result looks the same with or without it: دیوارها)
- before تر/ترین: بزرگ‌تر، سردترین
- before suffixes after silent ه: خسته‌ام، خانه‌ای، نامه‌اش، رفته‌اند
- after the prefix بی‌: بی‌صدا، بی‌نهایت (a few fused words are written joined: بیچاره، بیهوده)
- before the ezafe ی after silent ه, if the book uses that spelling: خانه‌ی (see section 3)
- in compounds that would otherwise join into an unreadable block: سیاه‌چاله، کرم‌چاله، پیش‌بینی، هم‌زمان

## 3. Ezafe after silent ه

Two spellings are current: خانهٔ (hamza above, which the Farhangestan's spelling guide prefers) and خانه‌ی (half-space and ی, which renders reliably in every font and on every keyboard). Either is correct. Choose one per book and record it in the style sheet. After ا and و the ezafe is written ی: دریای خزر، آهوی کوهی.

## 4. Punctuation

| Mark | Use |
|---|---|
| ، | comma (U+060C) |
| ؛ | semicolon (U+061B) |
| ؟ | question mark (U+061F) |
| « » | quotation marks |
| . ! : | as in English |
| … | ellipsis, one character, sparingly |
| — | dash, for interruption or (in some books) dialogue |

No space before ، ؛ ؟ . ! : or », one space after. No space just inside « ».

Persian uses fewer commas than English. Don't put one before every و, and don't copy English comma rhythm into Persian sentences.

## 5. Dialogue layout

Two conventions are common. Choose one per book.

Guillemets:

> گفت: «فردا آب نمی‌آید.»
>
> «فردا آب نمی‌آید.» این را بی‌آن‌که سر بلند کند گفت.

Dash, one speaker per paragraph:

> — فردا آب نمی‌آید.

Final punctuation of the quoted sentence goes inside the closing ». A direct quote never follows که: write گفت: «می‌آیم.» or, as indirect speech, گفت که می‌آید.

Start a new paragraph for each new speaker. Let most lines go untagged once the speakers are clear.

## 6. Numbers and dates

- In narration, write numbers in words up to about a hundred and for round figures: سی سال، هزار نفر، میله‌ی هفدهم.
- Use digits for dates, clock times, readouts, codes and serial numbers, and always Persian digits: ساعت ۶، سال ۱۴۶۰.
- Decimal separator ٫ (U+066B): ۳٫۵.
- Iranian settings date by the Solar Hijri calendar (1404 SH ≈ 2025). If the story world uses another calendar, decide it and record it in the style sheet.

## 7. Diacritics (اعراب)

Leave them out in general; Persian readers don't need them. Add them in two cases:

- to remove a real ambiguity in context: کُشت / کِشت، مُرد / مَرد
- on the first appearance of an invented name or term, to fix its pronunciation, then drop them

## 8. Mixed scripts

Avoid Latin words inside Persian sentences. Right-to-left text with embedded left-to-right runs reorders punctuation and numbers unpredictably. Transliterate instead (ناسا، الگوریتم). When Latin text is part of the story world, such as code on a screen, put it on its own line or block. In HTML, isolate any unavoidable inline Latin with `<bdi>` or `<span dir="ltr">`.

## 9. Files and fonts

- Markdown: fine as a working format. Viewers may need RTL turned on.
- HTML: `<html lang="fa" dir="rtl">` and a Persian font such as Vazirmatn (open source, on Google Fonts), with a fallback: `font-family: Vazirmatn, Tahoma, sans-serif;`.
- Word: set paragraphs right-to-left and set the complex-script font, not only the Latin one. In python-docx this means adding `w:bidi` to paragraph properties and `w:rtl` plus a `w:cs` font to runs.
- Plain text: UTF-8, always.
