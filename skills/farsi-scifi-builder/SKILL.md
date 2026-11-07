---
name: farsi-scifi-builder
description: Write, revise and worldbuild science fiction in Persian (Farsi) that reads like native literary prose, not translated English. Drafts scenes, chapters and stories with formal narration and natural colloquial dialogue; edits Persian manuscripts for translationese and orthography (نیم‌فاصله, ی/ک, « »); coins Persian SF terms; adapts the user's English drafts or whole novels into Persian (not word for word) and applies an author's handwritten PDF edits. Use this whenever the user wants Persian fiction with any speculative element (AI, robots, space, future Iran, dystopia/ویران‌شهر, climate or water futures, time travel, alternate history), asks to write or fix a فصل, صحنه or داستان, or talks about their رمان or داستان علمی‌تخیلی, even if they never say "sci-fi" or name this skill.
license: MIT
---

# Farsi SF builder

Paths in this file are relative to the skill folder.

Persian SF has two jobs at once. The speculative idea has to be clear and followed through, and the Persian has to sound written in Persian. Models usually manage the first and fail the second: the prose comes out as English wearing Persian words, with a pronoun on every verb, توسط passives, «یک» for every "a", and spaces where half-spaces belong. Iranian readers notice within a sentence. Most of this skill exists to prevent that.

## What do you need?

| Goal | Do this | Read |
|---|---|---|
| Draft a scene, chapter or story | Settle the book's choices, compose directly in Persian, revise, lint | `references/dialogue.md`, `references/translationese.md` |
| Edit or polish a Persian draft | Lint for mechanics, then revise translationese and rhythm by hand | `references/translationese.md`, `references/orthography.md` |
| Name a technology, place, people or concept | Use the established term if there is one, otherwise coin with Persian morphology | `references/terminology.md` |
| Find Iranian material to build a world from | Myth, old engineering, landscape, calendar, uncanny Persian prose | `references/wellsprings.md` |
| Turn the user's English draft into Persian | Rewrite each sentence in Persian shape; never transpose word order | `references/translationese.md` |
| Adapt a whole novel or manuscript into Persian | Settle depth and lens with the author, set up glossary and units, draft with an adaptation log | `references/adaptation.md` |
| Apply the author's handwritten edits on a PDF | `python scripts/ink_diff.py sent.pdf annotated.pdf`, read every mark, apply, return a clean copy with notes | `references/adaptation.md` |
| Give the author a reading copy | `python scripts/make_reading_pdf.py draft.md --title "…"` (16:9, two RTL columns; `--notes` appends notes) | `references/adaptation.md` |
| Keep a long project consistent | Start or update the style sheet (شیوه‌نامه) | `assets/style-sheet.md` |
| Check orthography mechanically | `python scripts/farsi_lint.py draft.md`, add `--fix` for a corrected copy | `references/orthography.md` |

## Working principles

### 1. Settle the book's choices first, then keep them

A Persian manuscript makes choices English never asks about: the register of the narration, the register and dialect of the dialogue, whether dialogue sits in « » or after a dash, whether ezafe after silent ه is written خانهٔ or خانه‌ی, Persian or Latin digits, and loanword or coinage for technology. Readers forgive any one of these choices but not switching between them.

If the project has a style sheet or earlier chapters, read them and match them before writing a word. If not, use these defaults and state them to the user in one line so they can override: formal-literary narration in past tense; Tehrani colloquial dialogue in « »; ezafe as ـه‌ی, which renders in every font; Persian digits; numbers in words inside narration. For anything longer than a single scene, offer to start `assets/style-sheet.md`.

### 2. Compose in Persian

Drafting in English and converting produces English syntax, however good the vocabulary. Think in Persian sentence shapes from the first line: verb last; subject dropped when the verb ending already carries it; indefinite ـی instead of «یک»; possession on the noun (دستش, not دست او); one idea per clause rather than English-style chains of که. If a sentence would make an Iranian reader pause to untangle it, recast it.

The same applies when translating the user's English SF. Translate the scene, not the sentences: keep events, images and voice, and rebuild every sentence in Persian order. `references/translationese.md` lists the calques that slip through.

### 3. Write the Persian a reader would write: plain, explicit, concrete

An author's first review of a translated chapter changes the same things again and again:

- **Everyday words.** Use the word an Iranian actually uses (چادرِ اکسیژن, not سرپوشِ تنفسی; مترو; دستگاهِ تصفیه) over coined, technical or literary ones.
- **Explicit logic.** Add the subject, object or connector that makes the logic obvious, and complete clipped lines.
- **Concrete images.** Turn English abstractions and metaphors into concrete Persian images.
- **Flow.** Let sentences flow, and keep fragments only where they carry tension.

Readers stumble over compression far more than over a plain extra word. `references/adaptation.md` (section 5) has the examples.

### 4. Revise for translationese every time, without over-correcting

Before delivering any Persian prose, read it once looking only for these, because they are the most common tells:

- pronouns the verb already marks (او رفت و او گفت → رفت و گفت)
- توسط passives (make the agent the subject)
- light-verb padding (انجام داد، صورت گرفت → the plain verb)
- «یک» as an English article (یک مرد پیر → پیرمردی)
- office verbs in fiction (می‌باشد، گردید، نمود → است، شد، کرد)
- adverb padding (به‌طور ناگهانی → ناگهان)
- English idioms in Persian words (معنی می‌دهد for "makes sense")
- direct quotes after که (گفت که «…» → گفت: «…»)

`scripts/farsi_lint.py` flags most of these as style signals. Treat them as pointers, not verdicts: sometimes «او» is needed to say who acts, and a bureaucrat character may well say می‌باشد.

Over-correction is the opposite failure. Stripping every «یک», «به‌عنوانِ» or «که», and squeezing sentences into elliptical Persian, reads as stiff or unclear; authors put those words back. Remove calques, but keep the small words that make a sentence clear: «یک» for a generic role or a count (از یک مادر) is natural Persian.

### 5. Make the central change touch ordinary life

Good SF follows one change (the novum) into its consequences: work, family, money, religion, language, bodies. Show those consequences through ordinary Iranian life (a queue, a water bill, a family gathering, a تعارف, the Nowruz table) rather than through explanation. Keep exposition inside action and let a character's ignorance or expertise carry it. Readers have plenty of translated SF about American and European futures; the future of their own streets is what Persian SF can give them that translations cannot.

### 6. Use Persian grammar as an SF tool

- **او has no gender.** An AI, alien, clone or narrator can stay ungendered without any awkwardness. Don't add gender the story doesn't need, and drop he/she when translating from English unless gender matters to the scene.
- **آن or او.** Calling a machine آن makes it a thing; the moment the narrator or a character switches to او is a story event. Choose deliberately, record it in the style sheet, and keep it until the story changes it.
- **تو, شما and تعارف.** Who uses تو with whom maps age, power and intimacy. A machine that takes تعارف literally, or performs it flawlessly, is characterization for free.
- **Register as voice.** An old system that speaks classical, Shahnameh-flavoured Persian against street colloquial; a character who insists on پارسی سره. Use archaic forms (همی، اندر، بُوَد) only in a voice, never to decorate narration.

`references/dialogue.md` has the colloquial conversions, honorifics and تعارف patterns.

### 7. Coin words the way Persian coins them

Coin only for things that don't exist yet: for anything ordinary, the established everyday word wins, because readers stumble over coinages for familiar objects. Check `references/terminology.md` before coining, since many SF terms are settled (فضاپیما، سیاه‌چاله، پهپاد، ویران‌شهر). For new things, build from Persian roots and productive affixes (ابر-، پسا-، پاد-، فرا-، -گاه، -یاب، -سنج، -زاد، -واره) so the reader can parse the word the first time. Let context define it; no footnotes, no glossary dumps. Check that the coinage doesn't already mean something else (خوابگاه is a dormitory).

Let the setting decide between loanword and coinage. Characters in near-future Tehran say موبایل and اینترنت; Farhangestan words such as رایانه in their mouths sound like a news anchor. A ship three centuries out from Earth will have grown its own words. Add every coinage to the style sheet.

### 8. Use Iranian material structurally, not as decoration

Myth, old engineering and landscape are rich SF sources: the var of Jamshid as a survival vault, qanats and the میرآب who divided their water, Attar's thirty birds as a collective mind. `references/wellsprings.md` collects them. Use them as load-bearing parts of the world, not as names and props sprinkled for colour. Write for Persian readers who already know these things, and surprise them by transforming the familiar rather than explaining it.

### 9. Deliver clean text

Persian ی and ک, half-spaces, Persian punctuation and digits, no Latin words inside Persian sentences unless they are part of the story world (a screen readout), since bidirectional text scrambles punctuation around them. For files: `dir="rtl" lang="fa"` and a Persian font (Vazirmatn) in HTML; right-to-left paragraphs and a complex-script font in Word. Give machine voices and screen text one consistent treatment, agreed with the author and recorded in the style sheet. One author's rule was an AI's speech in « », bold and centred, with its screen text in bold; the markup is in `references/adaptation.md`. Run the linter on anything longer than a few paragraphs. Details are in `references/orthography.md`.

## Drafting workflow

1. Read the style sheet, earlier chapters and any notes on characters or terms.
2. Ask only about what blocks the writing (point of view, length, where the scene sits). Otherwise assume, and say what you assumed.
3. Draft in Persian.
4. Revise: plain, explicit, concrete (principle 3), then the translationese pass (principle 4), then rhythm (vary sentence length; Persian prose carries long sentences joined by و well, but not stacked subordinate clauses), then consistency with the style sheet.
5. For anything longer than a scene, save to a file and run `python scripts/farsi_lint.py <file> --fix`. Read the report, apply judgment to the style signals, and deliver the corrected copy.
6. After the text, in the user's language, note in a line or two any new coinages and any style choices you made, so they can go into the style sheet. When adapting a longer work, deliver an adaptation log instead (see `references/adaptation.md`).

## Editing workflow

1. Run the linter on the user's text (save it to a file first if it was pasted).
2. Apply the mechanical fixes.
3. Revise translationese and rhythm by hand. Keep the author's voice, plot and deliberate choices; dialect, colloquial spelling and odd syntax may be intentional, so ask before "correcting" anything that looks chosen.
4. Return the edited text and a short summary of the kinds of change made, with one example of each, so the author can learn the pattern. Don't produce a line-by-line log unless asked.

## Review workflow (author's handwritten edits)

Run `scripts/ink_diff.py`, read every mark before applying any, and interpret ambiguous ones in the way that fits the scene. Then apply them all, re-run the checks, and return a clean reading copy with notes covering what changed, what you learned, your interpretations and open questions. Record the learning in the style sheet. Full procedure: `references/adaptation.md`, section 4.

## Language of replies

Talk to the user in the language they wrote in. The fiction itself is in Persian unless they ask otherwise.
