---
name: farsi-scifi-builder
description: Write, revise and worldbuild science fiction in Persian (Farsi) that reads like native literary prose, not translated English. Drafts scenes, chapters and stories with formal narration and natural colloquial dialogue; edits Persian manuscripts for translationese and orthography (نیم‌فاصله, ی/ک, « »); coins Persian SF terms; adapts the user's English drafts or whole novels into Persian (not word for word) and applies an author's handwritten PDF edits. Use this whenever the user wants Persian fiction with any speculative element (AI, robots, space, future Iran, dystopia/ویران‌شهر, climate or water futures, time travel, alternate history), asks to write or fix a فصل, صحنه or داستان, or talks about their رمان or داستان علمی‌تخیلی, even if they never say "sci-fi" or name this skill.
license: MIT
---

**Single-file build.** This is the `farsi-scifi-builder` skill packed into one file on 2026-11-05. The instructions below are its SKILL.md, unchanged. Its supporting files (6 reference files, 1 asset, 3 scripts and the licence) are embedded verbatim under "Bundled files" at the end, each with a SHA-256 checksum. You can read a reference there directly. Before you run a script or use an asset, unpack the files once:

```bash
python3 - "${CLAUDE_SKILL_DIR}/SKILL.md" "${TMPDIR:-/tmp}/farsi-scifi-builder" <<'PY'
import hashlib, os, re, sys
src, out = sys.argv[1], sys.argv[2]
if not os.path.isfile(src):
    src = "/mnt/skills/user/farsi-scifi-builder/SKILL.md"
text = open(src, encoding="utf-8", newline="").read()
rx = r"^<!-- bundle-file: (\S+) sha256=([0-9a-f]{64}) -->\n(`{3,})[^\n]*\n(.*?)^\3$"
n = 0
for path, sha, _, body in re.findall(rx, text, re.M | re.S):
    if path.startswith("/") or ".." in path.split("/"):
        continue
    data = next((b for b in (body, body[:-1]) if hashlib.sha256(b.encode()).hexdigest() == sha), None)
    if data is None:
        data = body
        print("warning: " + path + " was edited after packing (checksum differs)")
    dest = os.path.join(out, path)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8", newline="") as f:
        f.write(data)
    if data.startswith("#!"):
        os.chmod(dest, 0o755)
    n += 1
print(n, "files unpacked to", os.path.abspath(out))
PY
```

The first argument is the path of this file. Claude Code and Cowork fill it in for you; elsewhere, use the path you read this file from (on claude.ai the command also tries `/mnt/skills/user/farsi-scifi-builder/SKILL.md`). The command prints the folder it wrote to. From then on, use that folder wherever the instructions mean this skill's folder: paths such as `scripts/...`, `references/...`, `assets/...` and `<this-skill>/...` all point into it.

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

---

## Bundled files

The skill's supporting files, verbatim. Unpack them with the command at the top, or read one here. Line is where each file starts in this document.

| File | Size | Line |
|---|---:|---:|
| `references/adaptation.md` | 7.2 KB | 175 |
| `references/dialogue.md` | 6.1 KB | 250 |
| `references/orthography.md` | 5.2 KB | 339 |
| `references/terminology.md` | 7.3 KB | 440 |
| `references/translationese.md` | 7.0 KB | 555 |
| `references/wellsprings.md` | 6.2 KB | 654 |
| `assets/style-sheet.md` | 2.2 KB | 720 |
| `scripts/farsi_lint.py` | 14.1 KB | 776 |
| `scripts/ink_diff.py` | 5.3 KB | 1064 |
| `scripts/make_reading_pdf.py` | 8.7 KB | 1197 |
| `LICENSE` | 1.1 KB | 1353 |

### `references/adaptation.md`

<!-- bundle-file: references/adaptation.md sha256=bde7a7fb013623e62018b66dbf5a084bc7a90e186106f7a0a162fe4cf3ebcc2c -->
````markdown
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
````

### `references/dialogue.md`

<!-- bundle-file: references/dialogue.md sha256=7f2a261f533442ce84415ea8316e95039ad09c8fbf26c94f6fa6894d15fe1eb3 -->
````markdown
# Registers and dialogue

How Persian characters sound: the gap between written and spoken Persian, forms of address, تعارف, and register as a characterization tool.

Contents: 1 Narration registers · 2 Tehrani colloquial forms · 3 Writing colloquial readably · 4 Other varieties · 5 Address and respect · 6 تعارف · 7 Classical and pure-Persian voices · 8 Dialogue craft

## 1. Narration registers

Spoken and written Persian differ more than spoken and written English. Most novels narrate in the written standard (کتابی) and write dialogue as it is spoken. Some first-person narrators narrate in colloquial too, which gives intimacy and loses some range. A middle path is standard narration that lets a colloquial word or clitic in now and then (بازش کرده بودند). Choose for the whole book.

## 2. Tehrani colloquial forms

Tehrani colloquial is the default for spoken dialogue unless the book says otherwise.

| Written | Spoken |
|---|---|
| است | ـه (خوبه)، after a vowel ـست (کجاست) |
| هستم، هستی، هستیم، هستید، هستند | ـم، ـی، ـیم، ـین، ـن (خوبم، خوبی، خوبیم، خوبین، خوبن) |
| می‌خواهم، می‌خواهد | می‌خوام، می‌خواد |
| می‌روم، بروم، برود | می‌رم، برم، بره |
| می‌گویم، بگو | می‌گم، بگو |
| می‌دانم، می‌توانم | می‌دونم، می‌تونم |
| می‌آیم، آمد | میام، اومد |
| می‌شود | می‌شه |
| بگذار، بگذارم | بذار، بذارم |
| -ید (2nd plural) | -ین (می‌رین، بیاین) |
| -ند (3rd plural) | -ن (می‌رن، رفتن) |
| آن، آن‌ها، این‌ها | اون، اونا، اینا |
| را | رو; after a consonant often ـو (کتابو) |
| به او، با او، از او، برای او | بهش، باهاش، ازش، براش |
| چه، چه‌طور | چی، چطور / چجوری |
| اکنون، بسیار، زیرا، اما، سپس | الان، خیلی، چون، ولی، بعد |
| خانه، نان، جان، تهران | خونه، نون، جون، تهرون |
| رفته است، شده است | رفته، شده |

The ān → un shift is a habit of particular words, not a rule: خونه and نون shift, while many words, especially learned and technical ones (انسان، کهکشان), keep ān.

Prepositions often drop in speech: رفتم خونه (not به خانه رفتم).

## 3. Writing colloquial readably

- Write what is said, but keep words recognizable. A light hand reads better than full phonetic spelling.
- Keep half-spaces in colloquial too: می‌رم، نمی‌دونم، کوره‌ش.
- Keep each character's forms consistent from chapter to chapter. Record unusual ones in the style sheet.
- A character can switch register within a scene: formal with an official, colloquial a line later with family. That switch is information for the reader.

## 4. Other varieties

Persian has many regional and national varieties: Isfahani, Shirazi, Mashhadi and other city accents; Persian spoken by Azeri, Kurdish, Gilaki, Lori, Arab and Baluch Iranians; Dari in Afghanistan; Tajik in Central Asia. Render one only if the details are known. Otherwise signal it with a few marked words, a rhythm, and a line of narration, and ask the user whether they want more. Never play a variety for laughs it hasn't earned in the story.

## 5. Address and respect

- **تو / شما.** شما is the default with strangers, elders and superiors; تو with family, close friends, children and inferiors. A switch from شما to تو marks new intimacy or an insult.
- **Plural for respect.** Respected people take plural verbs and ایشان: آقای دکتر تشریف آوردند.
- **Titles.** آقا / خانم + name; جناب، استاد، دکتر، مهندس; حاج‌آقا / حاج‌خانم for older religious respectability; مش (from مشهدی) for an older working man in older or rural settings.
- **Kin terms for strangers.** In Tehran people call strangers عمو، خاله، داداش، آبجی، پدرجان، مادر. This gives instant texture and social position.
- **Thanks and apologies.** دستت درد نکنه، ممنون، مرسی، قربونت برم; ببخشید، شرمنده‌م، عذر می‌خوام: each with its own warmth and class.

## 6. تعارف

Ritual politeness: offers made to be refused at first, refusals made to be overruled, compliments returned with self-deprecation. Typical moves:

- «بفرمایید.» / «نه، شما بفرمایید.» at a door or a table
- «قابل نداره.» when asked a price; the buyer insists on paying
- «زحمت کشیدید.» / «خواهش می‌کنم، کاری نکردم.»
- «چاکرم»، «مخلصیم»، «نوکرتم» among men, often half-joking

For SF, تعارف is a gift. A machine that takes it literally, one that performs it perfectly and so seems colder, an alien that has to learn when "no" means "insist": each is characterization without exposition.

## 7. Classical and pure-Persian voices

- **Classical register** for an ancient system, a ritual text or an old scholar: همی + verb (همی رفت), اندر for در, بُوَد for است/باشد, مرا for به من, nouns before the verb in poetic order, vocabulary from the Shahnameh or Saadi.
- **Qajar-style officialese** for a bureaucracy: Arabic-heavy vocabulary, long honorific chains, می‌باشد and گردید on purpose.
- **پارسی سره** (pure Persian, avoiding Arabic loanwords) for an ideological or nationalist character, or a culture that purged its language.

Use these in voices. In narration they turn into costume.

## 8. Dialogue craft

- «گفت» is as invisible as "said". Vary it rarely (پرسید، جواب داد، زیر لب گفت) and avoid adverb tags such as «با عصبانیت گفت»; show the anger.
- Mark interruption with a dash and trailing off with …
- Let silences and gestures carry beats between lines.
- Exposition in dialogue only when one character truly doesn't know what the other knows.
````

### `references/orthography.md`

<!-- bundle-file: references/orthography.md sha256=bdd57d4ee410a4caace3e456f50422ece2fbfd8a10ec963e3394938b1c20fbd6 -->
````markdown
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
````

### `references/terminology.md`

<!-- bundle-file: references/terminology.md sha256=0fa63ce624d5ccb23855e534186b8af691d81bff96c368d4722fbc1354aee836 -->
````markdown
# SF terminology: established words and how to coin new ones

Contents: 1 Choosing a term · 2 Established vocabulary · 3 Coining with Persian morphology · 4 Names for people, machines and aliens · 5 Recording terms

## 1. Choosing a term

Work down this list and stop at the first that fits the setting:

1. **An established Persian term** that readers already know (section 2).
2. **A widely used loanword**, when the setting is near-future or present-day Iran. People say موبایل, لپ‌تاپ, اینترنت and اپ. Putting Farhangestan coinages such as رایانه or رایانامه in their mouths makes them sound like a news anchor, which is fine if they are one.
3. **A transparent coinage** from Persian roots (section 3), when the thing doesn't exist yet or the world is far from ours. Coinages tell the reader that history has happened.
4. **A loanword or alien word**, when the thing comes from outside the culture and the story wants it to feel foreign.

Different speakers can use different terms for the same thing. Engineers, officials, street speakers and the old all have their own vocabulary, and that difference is worldbuilding.

## 2. Established vocabulary

| English | Persian | Note |
|---|---|---|
| spaceship | فضاپیما؛ سفینه | فضاپیما is standard; سفینه is more literary and popular |
| space station | ایستگاه فضایی | |
| astronaut | فضانورد | |
| spacesuit | لباس فضایی | |
| orbit | مدار | |
| gravity | گرانش؛ جاذبه | گرانش technical, جاذبه everyday |
| weightlessness | بی‌وزنی | |
| light-year | سال نوری | |
| galaxy; Milky Way | کهکشان؛ کهکشان راه شیری | |
| planet; moon | سیاره؛ ماه، قمر | |
| exoplanet | سیاره‌ی فراخورشیدی | |
| asteroid; comet | سیارک؛ دنباله‌دار | |
| black hole; wormhole | سیاه‌چاله؛ کرم‌چاله | |
| supernova | ابرنواختر | |
| atmosphere | جو؛ اتمسفر | |
| extraterrestrial | فرازمینی؛ موجود فضایی؛ بیگانه | |
| satellite | ماهواره | |
| rocket; launch; launch pad | موشک؛ پرتاب؛ سکوی پرتاب | |
| drone | پهپاد | |
| robot; humanoid robot | ربات؛ ربات انسان‌نما | |
| cyborg; android | سایبورگ؛ اندروید | no settled Persian word |
| artificial intelligence | هوش مصنوعی | |
| computer | کامپیوتر؛ رایانه | رایانه is formal |
| supercomputer | ابررایانه | |
| software; hardware | نرم‌افزار؛ سخت‌افزار | |
| network; internet | شبکه؛ اینترنت | |
| virtual reality | واقعیت مجازی | |
| simulation; cloning | شبیه‌سازی | used for both; context decides |
| algorithm | الگوریتم | |
| quantum; entanglement | کوانتومی؛ درهم‌تنیدگی | |
| singularity | تکینگی | |
| nanotechnology | فناوری نانو؛ نانوفناوری | |
| gene; genome; mutation | ژن؛ ژنوم؛ جهش | جهش‌یافته = mutant |
| genetic engineering | مهندسی ژنتیک | |
| fusion; fission | همجوشی؛ شکافت | |
| antimatter | پادماده | |
| reactor; laser; hologram | رآکتور؛ لیزر؛ هولوگرام | |
| time travel; time machine | سفر در زمان؛ ماشین زمان | |
| parallel universe; multiverse | جهان موازی؛ چندجهانی | |
| utopia; dystopia | آرمان‌شهر؛ ویران‌شهر | |
| posthuman; transhumanism | پساانسان؛ فراانسان‌گرایی | |
| pandemic | همه‌گیری؛ پاندمی | |
| climate change | تغییر اقلیم | |
| drought; rationing | خشکسالی؛ جیره‌بندی، سهمیه‌بندی | |
| desalination plant | آب‌شیرین‌کن | |
| science fiction | علمی‌تخیلی | |

If a term isn't here and you aren't sure it is established, say so to the user rather than presenting a guess as standard usage.

## 3. Coining with Persian morphology

Persian builds new words from old parts very productively. A coinage built this way can be parsed on first reading, which is what lets context define it without a footnote.

| Element | Meaning | Established examples | Invented examples |
|---|---|---|---|
| ابر- | super- | ابررایانه، ابرنواختر | ابرذهن (overmind) |
| فرا- | trans-, beyond | فرازمینی، فراصوت | فرانوری (faster than light) |
| پسا- | post- | پساانسان | پساآب (the era after water) |
| پاد- | anti- | پادماده، پادتن | پادحافظه (anti-memory) |
| ریز- | micro- | ریزپردازنده، ریزتراشه | ریزماشین |
| دور- | far, tele- | دوربین، دورنگار | دوررسانی (teleportation) |
| هم- | co-, same | همجوشی، همزاد | هم‌ذهن (mind-linked) |
| -گاه | place | فرودگاه، پایگاه | پرشگاه (jump point) |
| -خانه | house of | رصدخانه، کارخانه | خواب‌خانه (sleeper hall) |
| -یاب | finder | مکان‌یاب | ذهن‌یاب |
| -سنج | meter | دماسنج، دروغ‌سنج | اندوه‌سنج (grief meter) |
| -نگار | recorder | لرزه‌نگار | خواب‌نگار (dream recorder) |
| -واره | -like, quasi- | ماهواره (literally "moon-like") | آدم‌واره (android) |
| -نما | resembling | انسان‌نما | زمین‌نما |
| -زی | living in | آبزی، خشکی‌زی | فضازی (space-dwelling) |
| -زاد | born of | آدمیزاد، همزاد | ماشین‌زاد، راه‌زاد (born on the voyage) |

Checks for any coinage:

- **Parse it cold.** Would a reader with no context guess roughly what it means?
- **Collisions.** Does the word already exist with another meaning? خوابگاه is a dormitory; هوابند already means airtight.
- **Say it aloud.** Persian avoids initial consonant clusters and some awkward joins.
- **Arabic roots are Persian too.** Prefer Persian roots for a native feel, but don't purge Arabic-origin words unless the story world has done so.
- **Reuse is a coinage too.** An old word with a new job (یخدان for a cryo-pod, میرآب for a water-allocation AI) often lands harder than a new one, because it brings its history.

## 4. Names for people, machines and aliens

- **Human names** should fit generation and class. Grandparents, parents and children in the same family often have names from different eras and naming fashions.
- **Machine names** can be role titles (میرآب، دیده‌بان، ناخدا), codes in a bureaucratic world (سامانه‌ی ۷۲), or mythic names for systems with prestige.
- **Alien names** sound alien when they break Persian patterns: letter combinations Persian avoids, unusual final sounds. Remember that Persian speakers add a vowel before initial clusters (اِسپانیا), so the narration's rendering of an alien name shows how humans hear it.
- Give an invented name diacritics on its first appearance so readers know how to say it.

## 5. Recording terms

Every coinage and every non-obvious term choice goes in the style sheet glossary (`assets/style-sheet.md`): the term, its meaning, the chapter where it first appears, who uses it, and any variant forms. A term used two ways in two chapters reads as a mistake, even if it was meant as drift.
````

### `references/translationese.md`

<!-- bundle-file: references/translationese.md sha256=777121c669dacb753e1183ed3d39ee5326d54150b0d127ae1df7723104dbd58f -->
````markdown
# Translationese and machine-prose tells in Persian

Persian written by a model, or translated in a hurry, carries English structure under Persian words. Abolhassan Najafi's «غلط ننویسیم» is the classic catalogue of these calques. This file covers the ones that turn up most in fiction, with a natural alternative for each. The alternatives are examples, not the only fix.

Contents: 1 Grammar calques · 2 Vocabulary and idiom calques · 3 Machine-prose habits · 4 Translating from English · 5 Revision passes · 6 Over-correction

## 1. Grammar calques

| Pattern | Stiff | Natural |
|---|---|---|
| Pronoun the verb already marks | او در را باز کرد و او بیرون رفت. | در را باز کرد و بیرون رفت. |
| Possessive pronoun after the noun | دست او را گرفت. | دستش را گرفت. |
| توسط passive | دروازه توسط نگهبان‌ها بسته شد. | نگهبان‌ها دروازه را بستند. / دروازه را بستند. |
| «یک» as the English article | او یک مرد پیر بود. | پیرمردی بود. / مرد پیری بود. (but «یک» for a generic role or a count is natural: از یک مادر انتظار می‌رود، یک اتاق) |
| Demonstrative for English "the" | این مرد به این صفحه نگاه کرد. | مرد به صفحه نگاه کرد. |
| در حال + verbal noun | در حال دویدن بود. | داشت می‌دوید. |
| قادر بودن for "could" | قادر به دیدن نبود. | نمی‌توانست ببیند. |
| Direct quote after که | گفت که «می‌آیم.» | گفت: «می‌آیم.» / گفت که می‌آید. |
| Stacked relative clauses | مردی که در ایستگاهی که آب نداشت کار می‌کرد که… | Split into two or three sentences. |
| Verb in the middle | رفت به سمت در با عجله. | با عجله به طرف در رفت. |

Persian has no definite article: a bare noun is already "the" when context makes it known. Persian also drops subjects freely, because the verb ending says who acts. Adding او or این everywhere is the single most common tell.

Verb-medial order does exist in literary Persian, for rhythm or emphasis. Use it on purpose, not by default.

## 2. Vocabulary and idiom calques

| Stiff | Natural | Note |
|---|---|---|
| بررسی‌ای انجام داد | بررسی کرد | light-verb padding |
| تلاش صورت گرفت | کوشیدند / تلاش کردند | say who did it |
| می‌باشد | است | office register |
| گردید | شد | office register |
| نمود | کرد | office register |
| به‌طور ناگهانی، به‌صورت آرام | ناگهان، آرام / آهسته | adverb padding |
| به منظور فرار | برای فرار / تا فرار کند | |
| در رابطه با | درباره‌ی | |
| از طریق | با / از | |
| تبدیل به ماشین شده بود | ماشین شده بود | |
| شروع به گریه کردن کرد | زد زیر گریه / گریه‌اش گرفت | more vivid |
| معنی می‌دهد ("makes sense") | جور درمی‌آید / عقل قبول می‌کند | idiom calque |
| زمان را کشتن ("kill time") | وقت گذراندن | idiom calque |
| در یک قایق بودن ("same boat") | سرنوشتمان یکی است | idiom calque |
| روی میز بودن ("on the table") | مطرح بودن | idiom calque |

Office verbs (می‌باشد، گردید، نمود) are fine in a character's mouth when that character is a bureaucrat or a system speaking officialese. That can even be the point.

## 3. Machine-prose habits

These are not calques but habits of generated prose, in Persian as in English:

- Naming the emotion right after showing it: قلبش از ترس می‌کوبید؛ ترسیده بود. Cut the second half.
- Stock atmosphere: «سکوتی سنگین»، «نوری کم‌جان»، «هوایی سرد و سنگین» in every scene. Find the specific detail of this place instead.
- Triplets everywhere: three adjectives, three clauses, three examples. Vary.
- Essay connectors at the start of sentences: همچنین، علاوه بر این، در نتیجه، با این حال. They make fiction sound like a report.
- «نه تنها… بلکه…» more than once a chapter.
- Ending a scene on a moral or a summary of what it meant. End on an image or an action.
- Every character speaking the same polished standard Persian. Give each one their own register and words (see `dialogue.md`).

## 4. Translating from English

- Translate the scene, not the sentences. Keep events, images, voice and pacing; rebuild every sentence in Persian order.
- Drop he/she/his/her unless gender matters. Persian is gender-neutral by default; adding مرد or زن to keep English clarity often over-specifies.
- Expect the Persian to be a little shorter: pronouns and articles disappear.
- Replace English idioms with Persian ones that carry the same feeling, or with plain speech, never word for word.
- Re-punctuate from scratch. English comma placement and semicolon habits don't transfer.
- Names of English-language brands, places and people are transliterated, not left in Latin.

## 5. Revision passes

Read the draft three times, each time for one thing only:

1. **Who acts.** Remove pronouns the verb marks; turn passives into actions with an agent.
2. **Verbs.** Replace padded and office verbs with plain ones; replace در حال and قادر بودن.
3. **Sound.** Read for rhythm as if aloud. Break stacked clauses; vary sentence length; check that each speaker sounds like themselves.

Then run `scripts/farsi_lint.py`. Its style signals and pronoun density point to the most likely spots, but the decision in each case is yours.

## 6. Over-correction

Translationese has an opposite failure: Persian scrubbed so hard it turns compressed, abstract or unnatural. Authors reverse these edits.

| Over-corrected | What the author wrote | What went wrong |
|---|---|---|
| جوابی که از مادر انتظار می‌رود | جوابی که از **یک** مادر انتظار می‌رود | stripped a natural «یک» |
| نقشه‌ها را هشدار بخواند | نقشه‌ها را **به‌عنوانِ** هشدار بخواند | dropped the word that carries the logic |
| روزگاری همین مایه‌ی دلگرمی بود | زمانی **همین روحیه‌ی قویِ مارا** مایه‌ی دلگرمی بود | lost antecedent |
| ولی خودِ پرنده رو نه. | ولی خودِ پرنده **یادت نیست**. | elliptical line |
| سرپوشِ تنفسی | چادرِ اکسیژن | coinage where an everyday word exists |
| سماجتِ نرم و ماشینی | عادتِ ملال‌آور و مصنوعی | English metaphor kept literally |
| امشب خداحافظیِ دیگری در کار بود. فردا. پس‌فردا. | …در کار بود و فردا و پس‌فردا. | English fragment rhythm |

The test: could a reader pause, even briefly, to work out who did what or what a word means? If so, add the plain word.
````

### `references/wellsprings.md`

<!-- bundle-file: references/wellsprings.md sha256=c9d71d3d1bf7d1975098534f6c4ae1fe0483f45435ffa02d795d55c6e62b7ecd -->
````markdown
# Iranian material for speculative worlds

Myth, old engineering, landscape and ritual that SF can build on. The SF move is not to mention these things but to ask what happens if one becomes literal, technological, or starts to fail. Persian readers already know most of this, so explaining it is wasted; transforming it is the point.

Contents: 1 Epic and myth · 2 Mystical and wonder literature · 3 Old engineering · 4 Landscape · 5 Time and ritual · 6 Prose models for the uncanny · 7 Pitfalls

## 1. Epic and myth

- **ور جمکرد (the var of Jamshid, Vendidad).** Warned of a killing winter, Jamshid builds an enclosure and gathers the seeds of the best people, animals, plants and fires to outlast it. A seed vault, a bunker colony or a generation ship, with built-in questions: who chose the "best", and who was left outside?
- **جام جهان‌نما.** The world-revealing cup in which Kay Khosrow finds the lost Bizhan, later called جام جم. Total surveillance, a planetary network, a search engine that sees too much.
- **The flying throne of Kay Kavus.** Eagles chained to a throne, straining toward meat on spears above them, carry the king skyward until they tire and he crashes. Hubris, propulsion, and the first failed launch.
- **Tahmuras and the divs.** The defeated divs buy their lives by teaching him writing. Knowledge bought from an enemy intelligence, and the price of it.
- **Zahhak.** Two serpents grow from his shoulders and must be fed human brains every day, and the young are taken to feed them. Parasitic technology; a state that consumes its youth; finally chained inside Damavand.
- **The Simorgh.** Raises the abandoned Zal, leaves a feather to burn when help is needed, and instructs the first surgical birth for Rostam. An older intelligence with a summoning protocol and medicine beyond human knowledge.
- **پل چینود.** The bridge every soul crosses after death, wide for the righteous and blade-thin for the wicked. A border, a checkpoint, an algorithm of judgment.
- **فرشکرد.** The final renovation of the world at the end of time. A singularity, a terraforming, a reset.

## 2. Mystical and wonder literature

- **Attar's منطق‌الطیر.** Thirty birds (سی مرغ), led by the hoopoe through seven valleys, reach the Simorgh and find they are it. A collective mind, emergence, a quest for an AI god that ends in a mirror.
- **هزار و یک شب.** The Ebony Horse, a mechanical flying horse built by a sage; the City of Brass with its automata and dead perfect city. Machines, hubris and ruined advanced civilizations.
- **عجایب‌المخلوقات (Zakariya Qazvini).** A medieval catalogue of the wonders of creation, from stars to strange peoples. A ready-made form for an in-world encyclopedia or a xenobiologist's notes.
- **Khayyam** was a mathematician and astronomer who worked on the Jalali calendar reform as well as a poet. His quatrains' cosmic doubt is a tonal key for SF about deep time.

## 3. Old engineering

- **قنات.** Underground channels that bring groundwater to the surface by gravity, dug and maintained by مقنی‌ها. Their vocabulary is a ready-made technical language: مادرچاه (mother well), میله (shaft), کوره (tunnel), مظهر (outlet), لای‌روبی (dredging). The **میرآب** divided water rights between users. Water futures, underground cities, a caste of diggers.
- **بادگیر.** Windcatchers (Yazd is famous for them) cool buildings without power. Climate futures, low-energy architecture.
- **یخچال / یخدان.** Domed ice houses that kept winter ice through the desert summer. Cryo-storage, archives, cold sleep.
- **آب‌انبار.** Covered cisterns. Rationing, reserves, sacred water.
- **کاروانسرا.** Fortified waystations a day's travel apart on trade routes. Stations on space lanes, outposts on a terraformed planet.
- **کبوترخانه.** Isfahan's pigeon towers, built to collect guano for the fields. Engineered ecology, designed symbiosis.

## 4. Landscape

- **Dasht-e Lut**, where satellites have measured some of the hottest land-surface temperatures on Earth; **Dasht-e Kavir**'s salt flats. Mars analogues, places where humans can't live without technology.
- **Lake Urmia**, which shrank dramatically in recent decades. Climate grief close to home; handle with the seriousness it has for readers.
- **Damavand**, the volcano where Zahhak lies chained. The Alborz, the Caspian forests, the Persian Gulf islands, the qanat towns on the desert edge.
- **Tehran's everyday**: highways, apartment blocks, smog days, power cuts, water pressure on the top floor. The future grows from these.

## 5. Time and ritual

- **The Solar Hijri calendar** begins the year at the spring equinox. On a world with a different year, or a ship with no seasons, when is Nowruz, and who decides?
- **Yalda**, the longest night; **Chaharshanbe Suri**, jumping over fires; **Sizdah Bedar**, leaving the house for nature on the thirteenth day; the **haft-sin** table. Rituals that a colony would keep, distort or argue about.
- **Muharram** and other religious observances are part of many readers' lives. If they appear, write them from inside, with the respect real readers will expect.

## 6. Prose models for the uncanny

Not SF, but these show how Persian prose makes the strange sound ordinary, which is most of what SF prose needs:

- Sadegh Hedayat, «بوف کور»: claustrophobic, looping interior dread.
- Gholam-Hossein Saedi, «عزاداران بیل»: a village where the impossible happens and everyone adjusts to it.
- Shahrnush Parsipur, «زنان بدون مردان»: transformation told in a flat, plain voice.

## 7. Pitfalls

- **Self-orientalizing.** Carpets, nightingales, saffron, rosewater and minarets as colour turn the future into a tourist brochure. Use the specific and the ordinary.
- **Explaining the familiar.** Persian readers don't need the Simorgh explained. Explain only what the story changed.
- **Famous names carry echoes.** A character named مش‌حسن will make many readers think of Saedi's villager who becomes his cow; a رستم or a سهراب brings an epic with him. Use echoes on purpose or avoid them.
- **Myth as a key to the plot.** If the reader knows the myth, they know the ending. Change something that matters.
````

### `assets/style-sheet.md`

<!-- bundle-file: assets/style-sheet.md sha256=73a5d9dfff463728c7998be604ca144394d3fcac36d29c47f1b5920bc8a5b317 -->
````markdown
# شیوه‌نامه‌ی [نام اثر]

این فایل را کنار دست‌نوشته نگه دارید و هر بار که تصمیم تازه‌ای گرفته شد، به‌روزش کنید. هر فصل تازه پیش از نوشتن با این فایل مقایسه می‌شود.

## زبان و خط

- لحن روایت: رسمی‌ادبی / ادبیِ نرم با گاه‌گاه واژه‌ی محاوره / محاوره (روایت اول‌شخص)
- زاویه‌ی دید و زمان روایت: اول‌شخص / سوم‌شخص محدود / دانای کل؛ گذشته / حال
- لحن گفت‌وگو: محاوره‌ی تهرانی / رسمی / گویش‌های دیگر (کدام شخصیت‌ها؟)
- نشانه‌گذاری گفت‌وگو: «» / خط تیره
- کسره‌ی اضافه پس از «ه»: خانهٔ / خانه‌ی
- اعداد: ارقام فارسی؛ در روایت به حروف تا عدد …
- تقویم جهان داستان:
- ضمیر برای ماشین‌ها و هوش‌های غیرانسانی: آن / او — کجا و چرا عوض می‌شود؟
- نوشتنِ صدای ماشین و متنِ صفحه: (مثلاً گفتارِ هوش مصنوعی در « »، سیاه و وسط‌چین؛ متنِ صفحه سیاه)
- واژه‌ی بیگانه یا واژه‌ی ساخته‌شده: سیاست کلی

## ترجیح‌های نویسنده

(پس از هر بازبینیِ نویسنده تکمیل می‌شود و بر قاعده‌های دیگرِ این فایل مقدم است.)

- 

## واژه‌نامه

| واژه | معنا | نخستین‌بار (فصل) | چه کسی به کار می‌برد | صورت‌های دیگر / یادداشت |
|---|---|---|---|---|
| | | | | |

## شخصیت‌ها

| نام (با اعراب در نخستین ذکر) | نقش | با چه کسی «تو»، با چه کسی «شما» | لحن، گویش، تکیه‌کلام |
|---|---|---|---|
| | | | |

## مکان‌ها و فناوری‌ها

| نام | چیست | قاعده‌ها و محدودیت‌ها | نخستین‌بار (فصل) |
|---|---|---|---|
| | | | |

## خط زمانی

| سال (به تقویم داستان) | رویداد |
|---|---|
| | |

## تصمیم‌های باز

- 
````

### `scripts/farsi_lint.py`

<!-- bundle-file: scripts/farsi_lint.py sha256=8c6b7bf1452d225beca0c662816858d5b1c38c94b2daf1da114f638e29327ff7 -->
````python
#!/usr/bin/env python3
"""Check Persian (Farsi) prose for orthography slips and translationese signals.

Three kinds of finding:
  mechanical  safe to fix automatically (--fix): Arabic ي/ك, Arabic-Indic digits,
              Latin ? , ; and straight or stray curly quotes in Persian text (nested
              “ ” inside « » is left alone, as are pandoc {…} attributes), punctuation spacing,
              spaces where a half-space (ZWNJ) belongs after می/نمی, before ها/های,
              and before a detached ezafe ی.
  review      probably wrong but ambiguous, never auto-fixed: suffixes after silent ه
              (خسته ام), تر/ترین spacing, ة, tatweel, Latin digits or Latin words
              inside Persian lines.
  style       translationese signals (توسط, می‌باشد, به‌طور, قادر بود, ...) and pronoun
              density. These are prompts for judgment, not errors.

Examples:
  python farsi_lint.py chapter3.md                 # report only
  python farsi_lint.py chapter3.md --fix           # writes chapter3.fixed.md next to it
  python farsi_lint.py chapter3.md --fix -o out.md --persian-digits
  python farsi_lint.py chapter3.md --json

Line numbers are 1-based. The report goes to stdout, a one-line summary to stderr.
The input file is never modified.
"""

import argparse
import json
import re
import sys
from pathlib import Path

LETTERS = "ءآأؤإئابةتثجحخدذرزسشصضطظعغفقكلمنهوىيپچژکگیۀ"
L = "[" + LETTERS + "]"
NOT_WORD_AFTER = "(?![" + LETTERS + "\u200c])"
NOT_WORD_BEFORE = "(?<![" + LETTERS + "\u200c])"
ZWNJ = "\u200c"

ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
LATIN_DIGITS = "0123456789"

# Words that can follow a standalone «می»/«نمی» which is NOT the verb prefix
# (e.g. «نمی از اشک», «جام می و ...»). Prefix + these is left alone.
MI_STOP = "از|به|در|با|بر|که|و|را|تا|این|آن|هم|یا|نه|چون|اگر|ولی|اما"
PLURAL = "ها|های|هایی|هایم|هایت|هایش|هایمان|هایتان|هایشان"

# (code, description, pattern, replacement) — applied in this order by --fix.
MECHANICAL = [
    ("arabic_yeh", "Arabic ي/ى → Persian ی", re.compile("[يى]"), "ی"),
    ("arabic_kaf", "Arabic ك → Persian ک", re.compile("ك"), "ک"),
    ("arabic_digits", "Arabic-Indic digits → Persian digits",
     re.compile("[" + ARABIC_DIGITS + "]"),
     lambda m: PERSIAN_DIGITS[ARABIC_DIGITS.index(m.group(0))]),
    ("zwnj_double", "doubled half-space collapsed", re.compile("\u200c{2,}"), ZWNJ),
    ("zwnj_space", "half-space next to a space removed", re.compile(" \u200c+|\u200c+ "), " "),
    ("zwnj_edge", "half-space at line edge or before punctuation removed",
     re.compile("^\u200c+|\u200c+$|\u200c+(?=[،؛؟.!:»])"), ""),
    ("straight_quotes", "straight quotes around Persian → « »",
     re.compile('"([^"\n]*?' + L + '[^"\n]*?)"'), r"«\1»"),
    ("curly_quotes", "curly “ ” around Persian outside « » → « » (nested “ ” inside « » is correct)",
     re.compile("\u201c([^\u201c\u201d\n]*?" + L + "[^\u201c\u201d\n]*?)\u201d"),
     lambda m: m.group(0) if inside_guillemets(m.string, m.start()) else "«" + m.group(1) + "»"),
    ("latin_question", "Latin ? after Persian → ؟",
     re.compile("(?<=[" + LETTERS + "\u200c»]) *\\?"), "؟"),
    ("latin_comma", "Latin , in Persian → ،",
     re.compile("(?<=[" + LETTERS + "\u200c»]) *,(?= *[" + LETTERS + "«])"), "،"),
    ("latin_semicolon", "Latin ; in Persian → ؛",
     re.compile("(?<=[" + LETTERS + "\u200c»]) *;(?= *[" + LETTERS + "«])"), "؛"),
    ("zwnj_mi", "space after می/نمی prefix → half-space (می‌روم)",
     re.compile(NOT_WORD_BEFORE + "(ن?می) (?!(?:" + MI_STOP + ")" + NOT_WORD_AFTER + ")(?=" + L + ")"),
     "\\1" + ZWNJ),
    ("zwnj_plural", "space before ها/های → half-space (کتاب‌ها)",
     re.compile("(?<=" + L + ") (" + PLURAL + ")" + NOT_WORD_AFTER),
     ZWNJ + "\\1"),
    ("ezafe_space", "detached ezafe «ه ی» → «ه‌ی»",
     re.compile("(?<=ه) ی" + NOT_WORD_AFTER), ZWNJ + "ی"),
    ("space_before_punct", "space before punctuation removed",
     re.compile("(?<=[" + LETTERS + "\u200c»]) +([،؛؟!:.»])"), "\\1"),
    ("space_inside_guillemets", "space just inside « » removed",
     re.compile("« +| +»"), lambda m: m.group(0).strip()),
    ("space_after_punct", "missing space after punctuation added",
     re.compile("([،؛؟]|(?<=" + L + ")[.!:])(?=[" + LETTERS + "«])"), "\\1 "),
    ("double_space", "repeated spaces inside a line collapsed",
     re.compile("(?<=\\S) {2,}(?=\\S)"), " "),
]

REVIEW = [
    ("zwnj_he_suffix", "suffix after silent ه probably needs a half-space (خسته‌ام، خانه‌ای)",
     re.compile("(?<=" + L + ")ه (ام|ای|ات|اش|ایم|اید|اند)" + NOT_WORD_AFTER)),
    ("zwnj_tar", "تر/ترین after a space: comparative (بزرگ‌تر) or the word «تر» (wet)?",
     re.compile("(?<=" + L + ") (تر|ترین)" + NOT_WORD_AFTER)),
    ("teh_marbuta", "ة in Persian text: usually ه or ت (رحمت)", re.compile("ة")),
    ("tatweel", "tatweel ـ stretching: remove unless deliberate", re.compile("\u0640")),
    ("latin_digits", "Latin digits in a Persian line (--persian-digits converts them)",
     re.compile("(?<![A-Za-z])[0-9]+(?![A-Za-z])")),
    ("latin_words", "Latin words inside a Persian line: bidi may scramble punctuation",
     re.compile("[A-Za-z]{2,}")),
]

# Codes reported once per line: a line with many Latin words needs one look, not twenty.
ONCE_PER_LINE = {"latin_digits", "latin_words"}

STYLE = [
    ("tavasot", "«توسط» passive reads as translated: make the agent the subject",
     re.compile(NOT_WORD_BEFORE + "توسط" + NOT_WORD_AFTER)),
    ("mibashad", "office register: use است / هستند",
     re.compile("می[\u200c ]?باش(?:د|ند|م|ی|یم|ید)" + NOT_WORD_AFTER)),
    ("gardid", "office register: use شد (ignore if it means 'wandered')",
     re.compile(NOT_WORD_BEFORE + "گردید(?:ند)?" + NOT_WORD_AFTER)),
    ("nemud", "office register: use کرد (ignore if it is the noun «نمود»)",
     re.compile(NOT_WORD_BEFORE + "نمود(?:ند|م)?" + NOT_WORD_AFTER)),
    ("anjam", "light-verb padding: «بررسی کرد», not «بررسی انجام داد»",
     re.compile("انجام[\u200c ]?(?:داد|دادند|دادیم|می[\u200c ]?دهد|می[\u200c ]?دهند|شد|شود|گرفت)" + NOT_WORD_AFTER)),
    ("surat", "light-verb padding «صورت گرفت»: say who did what",
     re.compile("صورت[\u200c ]?(?:گرفت|گرفتند|می[\u200c ]?گیرد|پذیرفت)" + NOT_WORD_AFTER)),
    ("betor", "adverb padding: «به‌طور ناگهانی» → «ناگهان»",
     re.compile(NOT_WORD_BEFORE + "به[\u200c ]?(?:طور|صورت)[\u200c ]")),
    ("dar_hal", "«در حال …» progressive: «داشت می‌…» is more native in narration",
     re.compile(NOT_WORD_BEFORE + "در[\u200c ]?حال[\u200c ](?!حاضر)")),
    ("qader", "«قادر بود» → «می‌توانست»",
     re.compile(NOT_WORD_BEFORE + "قادر[\u200c ]?(?:به|بود|است|نبود|نیست|بودند|نبودند)" + NOT_WORD_AFTER)),
    ("mani", "calque of 'makes sense': try «جور درمی‌آید» / «عقل قبول می‌کند»",
     re.compile(NOT_WORD_BEFORE + "معن[یا][\u200c ]?(?:ن?می[\u200c ]?(?:دهد|ده|داد)|داد|نداد|ن?میده)" + NOT_WORD_AFTER)),
    ("be_manzur", "«به منظور» → «برای» / «تا»",
     re.compile(NOT_WORD_BEFORE + "به[\u200c ]?منظور" + NOT_WORD_AFTER)),
    ("dar_rabete", "«در رابطه با» → «درباره‌ی»",
     re.compile(NOT_WORD_BEFORE + "در[\u200c ]?رابطه[\u200c ]?با" + NOT_WORD_AFTER)),
    ("ke_quote", "direct quote after «که»: write «گفت: «…»» or drop the quotes",
     re.compile(NOT_WORD_BEFORE + "که[ :]*[«\"\u201c]")),
    ("tabdil", "«تبدیل به … شد» is often just «… شد»",
     re.compile(NOT_WORD_BEFORE + "تبدیل[\u200c ]?(?:به|شد|شده)" + NOT_WORD_AFTER)),
]

DENSITY = [
    ("pronoun_u", "او", 10.0,
     "Persian drops subjects the verb already marks; check each «او»"),
    ("indef_yek", "یک", 8.0,
     "check only mechanical 'a' calques (مردی، نه یک مرد); «یک» for a generic role or a count is fine (از یک مادر، یک اتاق)"),
]


ATTR = re.compile(r"\{[^{}\n]*\}")


def inside_guillemets(line, pos):
    """True if pos sits inside an open « … » on this line (nested quotes are allowed there)."""
    before = line[:pos]
    return before.count("«") > before.count("»")


def mask_attrs(line):
    """Hide pandoc attribute blocks like {custom-style="Screen"} so no rule touches them."""
    saved = ATTR.findall(line)
    return ATTR.sub("\x00", line), saved


def unmask_attrs(line, saved):
    it = iter(saved)
    return re.sub("\x00", lambda m: next(it), line)


def has_persian(line):
    return re.search(L, line) is not None


def snippet(line, start, end, width=18):
    a, b = max(0, start - width), min(len(line), end + width)
    return ("…" if a > 0 else "") + line[a:b].strip() + ("…" if b < len(line) else "")


def scan(text):
    lines = text.split("\n")
    found = {"mechanical": [], "review": [], "style": []}
    for i, line in enumerate(lines, 1):
        if not has_persian(line):
            continue
        line, _saved = mask_attrs(line)
        for code, desc, rx, _ in MECHANICAL:
            for m in rx.finditer(line):
                if code == "curly_quotes" and inside_guillemets(line, m.start()):
                    continue
                found["mechanical"].append({"line": i, "code": code, "message": desc,
                                            "context": snippet(line, m.start(), m.end())})
        for code, desc, rx in REVIEW:
            for m in rx.finditer(line):
                found["review"].append({"line": i, "code": code, "message": desc,
                                        "context": snippet(line, m.start(), m.end())})
                if code in ONCE_PER_LINE:
                    break
        for code, desc, rx in STYLE:
            for m in rx.finditer(line):
                found["style"].append({"line": i, "code": code, "message": desc,
                                       "context": snippet(line, m.start(), m.end())})
    words = len(re.findall("[" + LETTERS + "\u064B-\u0655\u200c]+", text))
    density = []
    for code, word, limit, advice in DENSITY:
        n = len(re.findall(NOT_WORD_BEFORE + word + NOT_WORD_AFTER, text))
        per_k = round(1000.0 * n / words, 1) if words else 0.0
        density.append({"code": code, "word": word, "count": n, "per_1000": per_k,
                        "high": per_k > limit, "advice": advice})
    return {"words": words, "findings": found, "density": density}


def fix(text, persian_digits=False):
    out = []
    for line in text.split("\n"):
        if has_persian(line):
            line, saved = mask_attrs(line)
            for _, _, rx, rep in MECHANICAL:
                line = rx.sub(rep, line)
            line = unmask_attrs(line, saved)
            if persian_digits:
                line = re.sub("(?<=[0-9])\\.(?=[0-9])", "٫", line)
                line = re.sub("(?<![A-Za-z])[0-9]+(?![A-Za-z])",
                              lambda m: m.group(0).translate(str.maketrans(LATIN_DIGITS, PERSIAN_DIGITS)),
                              line)
        out.append(line)
    return "\n".join(out)


def print_report(path, result, fixed_to):
    f = result["findings"]
    print(f"{path} — {result['words']} Persian words")
    titles = {"mechanical": "Mechanical (fixed by --fix)",
              "review": "Needs review (not auto-fixed)",
              "style": "Style signals (judgment calls, not errors)"}
    for kind in ("mechanical", "review", "style"):
        print(f"\n{titles[kind]}: {len(f[kind])}")
        for item in f[kind]:
            print(f"  L{item['line']:<4} {item['code']:<22} {item['message']}")
            print(f"        {item['context']}")
    print("\nDensity per 1000 Persian words:")
    for d in result["density"]:
        flag = "  HIGH — " + d["advice"] if d["high"] else ""
        print(f"  {d['word']}: {d['count']} ({d['per_1000']}){flag}")
    if fixed_to:
        print(f"\nCorrected copy: {fixed_to}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="Persian text file (.md, .txt, ...)")
    ap.add_argument("--fix", action="store_true",
                    help="write a corrected copy (mechanical fixes only)")
    ap.add_argument("-o", "--output",
                    help="path for the corrected copy (default: <input>.fixed<ext> next to the input)")
    ap.add_argument("--persian-digits", action="store_true",
                    help="with --fix, also convert Latin digits in Persian lines to Persian digits")
    ap.add_argument("--json", action="store_true", help="print the report as JSON")
    args = ap.parse_args()

    src = Path(args.input)
    if not src.is_file():
        sys.exit(f"error: {src} is not a file")
    text = src.read_text(encoding="utf-8")
    result = scan(text)

    fixed_to = None
    if args.fix:
        dst = Path(args.output) if args.output else src.with_name(src.stem + ".fixed" + src.suffix)
        if dst.resolve() == src.resolve():
            sys.exit("error: refusing to overwrite the input file; choose another -o path")
        dst.write_text(fix(text, args.persian_digits), encoding="utf-8")
        fixed_to = str(dst)

    if args.json:
        result["file"] = str(src)
        result["fixed_to"] = fixed_to
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_report(src, result, fixed_to)

    f = result["findings"]
    high = sum(1 for d in result["density"] if d["high"])
    print(f"{src.name}: {len(f['mechanical'])} mechanical, {len(f['review'])} to review, "
          f"{len(f['style'])} style signals, {high} high-density flags"
          + (f"; wrote {fixed_to}" if fixed_to else ""), file=sys.stderr)


if __name__ == "__main__":
    main()
````

### `scripts/ink_diff.py`

<!-- bundle-file: scripts/ink_diff.py sha256=5a28b070122e5094e43a5fd0bc6a47f82222d4e50a407e2996084ec16d86598d -->
````python
#!/usr/bin/env python3
"""Find an author's handwritten marks in a PDF by comparing it with the PDF you sent.

Handwriting added on a tablet is often flattened into the page as vector strokes, so it
never shows up as annotations or in the text layer. Rendering both PDFs and diffing the
pixels finds every mark. For each page with ink, this writes the annotated page with the
ink coloured red, plus close-up crops of each marked region, and prints a summary.

Examples:
  python ink_diff.py sent.pdf annotated.pdf               # outputs to annotated_ink/
  python ink_diff.py sent.pdf annotated.pdf -o marks --dpi 200 --zoom-dpi 320

Then view the red pages first, and the zoom crops wherever a mark is small or unclear.
Needs poppler's pdftoppm and Pillow. Inputs are never modified.
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageChops


def render(pdf, dpi, outdir, prefix, first=None, last=None):
    cmd = ["pdftoppm", "-png", "-r", str(dpi)]
    if first:
        cmd += ["-f", str(first), "-l", str(last or first)]
    subprocess.run(cmd + [str(pdf), str(outdir / prefix)], check=True)
    return sorted(outdir.glob(prefix + "-*.png"))


def ink_mask(a, b, threshold):
    if a.size != b.size:
        b = b.resize(a.size)
    return ImageChops.difference(a.convert("L"), b.convert("L")).point(lambda v: 255 if v > threshold else 0)


def regions(mask, gap):
    """Group ink into horizontal bands (rows of handwriting), returning boxes."""
    w, h = mask.size
    rows = [any(mask.getpixel((x, y)) for x in range(0, w, 3)) for y in range(h)]
    bands, start, quiet = [], None, 0
    for y, on in enumerate(rows):
        if on:
            start = y if start is None else start
            quiet = 0
        elif start is not None:
            quiet += 1
            if quiet > gap:
                bands.append((start, y - quiet))
                start, quiet = None, 0
    if start is not None:
        bands.append((start, h - 1))
    boxes = []
    for y0, y1 in bands:
        box = mask.crop((0, y0, w, y1 + 1)).getbbox()
        if box:
            boxes.append((box[0], y0 + box[1], box[2], y0 + box[3]))
    return boxes


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sent", help="the PDF you gave the author")
    ap.add_argument("annotated", help="the PDF the author sent back")
    ap.add_argument("-o", "--outdir", help="output folder (default: <annotated>_ink next to it)")
    ap.add_argument("--dpi", type=int, default=150, help="resolution of the red-ink pages (default 150)")
    ap.add_argument("--zoom-dpi", type=int, default=300, help="resolution of the close-up crops (default 300)")
    ap.add_argument("--threshold", type=int, default=50, help="grey-level difference counted as ink (default 50)")
    ap.add_argument("--json", action="store_true", help="print the summary as JSON")
    a = ap.parse_args()

    sent, ann = Path(a.sent), Path(a.annotated)
    for f in (sent, ann):
        if not f.is_file():
            sys.exit(f"error: {f} is not a file")
    if not shutil.which("pdftoppm"):
        sys.exit("error: pdftoppm (poppler) is required")
    out = Path(a.outdir) if a.outdir else ann.with_name(ann.stem + "_ink")
    out.mkdir(parents=True, exist_ok=True)

    summary = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        pages_a = render(ann, a.dpi, tmp, "a")
        pages_s = render(sent, a.dpi, tmp, "s")
        if len(pages_a) != len(pages_s):
            print(f"warning: page counts differ ({len(pages_s)} sent, {len(pages_a)} annotated); comparing in order",
                  file=sys.stderr)
        scale = a.zoom_dpi / a.dpi
        for i, (pa, ps) in enumerate(zip(pages_a, pages_s), 1):
            A, S = Image.open(pa).convert("RGB"), Image.open(ps).convert("RGB")
            mask = ink_mask(A, S, a.threshold)
            if not mask.getbbox():
                continue
            ink_px = sum(1 for v in mask.getdata() if v)
            red = Image.composite(Image.new("RGB", A.size, (215, 20, 20)), A, mask)
            red_path = out / f"page-{i:03d}-ink.png"
            red.save(red_path)
            boxes = regions(mask, gap=int(a.dpi * 0.12))
            zoom = render(ann, a.zoom_dpi, tmp, f"z{i}", first=i)[0]
            Z = Image.open(zoom)
            crops = []
            for k, (x0, y0, x1, y1) in enumerate(boxes, 1):
                pad = int(a.dpi * 0.25)
                box = (max(0, int((x0 - pad) * scale)), max(0, int((y0 - pad) * scale)),
                       min(Z.width, int((x1 + pad) * scale)), min(Z.height, int((y1 + pad) * scale)))
                cp = out / f"page-{i:03d}-zoom-{k:02d}.png"
                Z.crop(box).save(cp)
                crops.append(str(cp))
            summary.append({"page": i, "ink_pixels": ink_px, "regions": len(boxes),
                            "red_page": str(red_path), "zoom_crops": crops})

    if a.json:
        print(json.dumps(summary, indent=1))
    else:
        for s in summary:
            print(f"page {s['page']:>3}: {s['regions']} marked region(s), {s['ink_pixels']} ink px -> {s['red_page']}")
    print(f"{len(summary)} page(s) with ink; outputs in {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
````

### `scripts/make_reading_pdf.py`

<!-- bundle-file: scripts/make_reading_pdf.py sha256=cd351b9f1565a2914dd03cab576dc97a0c73b7dd783435b7d682f249a826c7a4 -->
````python
#!/usr/bin/env python3
"""Render a marked-up draft unit as a 16:9 reading PDF (two RTL columns, Persian page numbers).

Usage: python make_reading_pdf.py drafts/u01_ch01.md [-o out.pdf] --title "نام کتاب" [--notes notes.md]

Markup understood: # part / ## chapter headings; # alone = scene break; ::: {custom-style=Screen} (screen
text), Hand (handwriting), any style ending in Voice (a machine voice: centred, bold); [text]{custom-style=...}
inline; ⟦+ … ⟧ proposed additions (highlighted, with a legend on the title page).
--notes appends an English Markdown file (headings, bullets, **bold**) after the chapter, left to right.
Needs Playwright with Chromium. Static Noto Naskh Arabic and Vazirmatn (SIL OFL) are downloaded once into
--fonts-dir; static builds matter, because Chromium embeds variable fonts as Type 3 and loses the text layer.
Without -o the PDF is written next to the input as <name>.pdf. The input is never modified.
"""
import argparse, html, re, sys
from pathlib import Path

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("draft"); ap.add_argument("-o", "--output"); ap.add_argument("--title", default="پیش‌نویس")
ap.add_argument("--label", default="پیش‌نویس · برای خواندن و بازبینی")
ap.add_argument("--notes", help="optional English Markdown file appended after the chapter, left-to-right")
ap.add_argument("--fonts-dir", default=str(Path.home() / ".cache" / "farsi-scifi-builder" / "fonts"),
                help="where the fonts live or are downloaded to")
A = ap.parse_args()
SRC = Path(A.draft)
OUT = Path(A.output) if A.output else SRC.with_suffix(".pdf")
if OUT.resolve() == SRC.resolve(): sys.exit("error: refusing to overwrite the input")
src = SRC.read_text(encoding="utf-8")
src = re.sub(r"<!--.*?-->", "", src, flags=re.S)
FONTS = Path(A.fonts_dir).expanduser()
FONT_URLS = {
    "NotoNaskhArabic-Regular.ttf": "https://raw.githubusercontent.com/notofonts/notofonts.github.io/main/fonts/NotoNaskhArabic/hinted/ttf/NotoNaskhArabic-Regular.ttf",
    "NotoNaskhArabic-Bold.ttf": "https://raw.githubusercontent.com/notofonts/notofonts.github.io/main/fonts/NotoNaskhArabic/hinted/ttf/NotoNaskhArabic-Bold.ttf",
    "Vazirmatn-Regular.ttf": "https://raw.githubusercontent.com/rastikerdar/vazirmatn/master/fonts/ttf/Vazirmatn-Regular.ttf",
    "Vazirmatn-Bold.ttf": "https://raw.githubusercontent.com/rastikerdar/vazirmatn/master/fonts/ttf/Vazirmatn-Bold.ttf",
}
FONTS.mkdir(parents=True, exist_ok=True)
for _name, _url in FONT_URLS.items():
    if not (FONTS / _name).is_file():
        import urllib.request
        try:
            urllib.request.urlretrieve(_url, FONTS / _name)
        except Exception as e:
            sys.exit(f"error: could not download {_name} ({e}); put the four static fonts in {FONTS}")
part = next((l[2:].strip() for l in src.splitlines() if l.startswith("# ")), "")
chap = next((l[3:].strip() for l in src.splitlines() if l.startswith("## ")), "")

def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"\[([^\]]+)\]\{custom-style=ScreenChar\}", r'<span class="scr">\1</span>', t)
    t = re.sub(r"⟦\+\s*(.*?)\s*⟧", r'<mark class="add">\1</mark>', t, flags=re.S)
    return t

blocks = [b.strip() for b in re.split(r"\n\s*\n", src) if b.strip()]
body = []
for b in blocks:
    if b.startswith("# "):
        continue  # part title goes on the title page
    if b.startswith("## "):
        continue  # chapter title goes on the title page
    m = re.match(r"::: \{custom-style=(\w+)\}\n(.*?)\n:::", b, re.S)
    if m:
        cls = "orison" if m.group(1).endswith("Voice") else {"Screen": "screen", "Hand": "hand"}.get(m.group(1), "screen")
        body.append(f'<p class="{cls}">{inline(m.group(2))}</p>')
    elif b == "#":
        body.append('<p class="brk">⁂</p>')
    else:
        body.append(f"<p>{inline(b)}</p>")

NOTES = ""
LEGEND = ('<br><span style="background:#f6e3b4;padding:0 4px;border-radius:2px">زمینه‌ی کهربایی</span> = افزوده‌ی پیشنهادی، در انتظارِ تأیید' if "⟦+" in src else "")
if A.notes:
    def nin(t):
        t = html.escape(t, quote=False)
        t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
        return re.sub(r"([\u0600-\u06FF\u200c«»“”][\u0600-\u06FF\u200c«»“”\s.،؛؟:0-9۰-۹\-]*[\u0600-\u06FF\u200c«»“”.؟])", r"<bdi>\1</bdi>", t)
    out, inlist = [], False
    for line in Path(A.notes).read_text(encoding="utf-8").splitlines():
        s_ = line.strip()
        if s_.startswith("- "):
            if not inlist: out.append("<ul>"); inlist = True
            out.append(f"<li>{nin(s_[2:])}</li>"); continue
        if inlist: out.append("</ul>"); inlist = False
        if not s_: continue
        if s_.startswith("## "): out.append(f"<h2>{nin(s_[3:])}</h2>")
        elif s_.startswith("# "): out.append(f"<h1>{nin(s_[2:])}</h1>")
        else: out.append(f"<p>{nin(s_)}</p>")
    if inlist: out.append("</ul>")
    NOTES = '<section class="notes" dir="ltr" lang="en">' + "\n".join(out) + "</section>"

page = f"""<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8">
<style>
@font-face {{ font-family: Naskh; src: url("file://{FONTS}/NotoNaskhArabic-Regular.ttf"); font-weight: 400; }}
@font-face {{ font-family: Naskh; src: url("file://{FONTS}/NotoNaskhArabic-Bold.ttf"); font-weight: 700; }}
@font-face {{ font-family: Vazir; src: url("file://{FONTS}/Vazirmatn-Regular.ttf"); font-weight: 400; }}
@font-face {{ font-family: Vazir; src: url("file://{FONTS}/Vazirmatn-Bold.ttf"); font-weight: 700; }}
@page {{ size: 254mm 142.875mm; margin: 13mm 16mm 15mm 16mm;
  @bottom-center {{ content: counter(page, persian); font-family: Vazir; font-size: 8pt; color: #9a948a; }} }}
@page :first {{ @bottom-center {{ content: none; }} }}
html {{ background: #ffffff; }}
body {{ margin: 0; font-family: Naskh, serif; font-size: 12.3pt; line-height: 1.95; color: #23211d;
  text-align: justify; text-justify: inter-word; }}
.title {{ height: 114mm; display: flex; flex-direction: column; justify-content: center; align-items: center;
  text-align: center; break-after: page; }}
.title .book {{ font-family: Naskh; font-weight: 700; font-size: 34pt; line-height: 1.4; margin: 0; }}
.title .rule {{ width: 22mm; border-top: 1px solid #b9ae9a; margin: 5mm 0; }}
.title .part {{ font-family: Vazir; font-size: 10.5pt; letter-spacing: 0; color: #7b7466; margin: 0; }}
.title .chap {{ font-family: Naskh; font-size: 19pt; margin: 1.5mm 0 0; }}
.title .meta {{ font-family: Vazir; font-size: 8.5pt; color: #9a948a; margin-top: 9mm; line-height: 1.9; }}
.cols {{ column-count: 2; column-gap: 15mm; column-rule: 0.4pt solid #e2dbcd; column-fill: auto; height: auto; }}
p {{ margin: 0 0 0.55em; orphans: 2; widows: 2; }}
p.screen {{ font-family: Vazir; font-weight: 700; font-size: 10.8pt; letter-spacing: 0;
  text-align: center; color: #1f3a4d; margin: 0.6em 0 0.8em; break-inside: avoid; }}
.scr {{ font-family: Vazir; font-weight: 700; font-size: 0.88em; color: #1f3a4d; }}
p.orison {{ font-family: Vazir; font-weight: 700; font-size: 11pt; text-align: center; color: #1f3a4d; margin: 0.5em 0 0.8em; break-inside: avoid; }}
section.notes {{ break-before: page; direction: ltr; text-align: left; font-family: Vazir, sans-serif; font-size: 9.6pt; line-height: 1.6; column-count: 2; column-gap: 12mm; }}
section.notes h1 {{ font-size: 14pt; margin: 0 0 3mm; column-span: all; }}
section.notes h2 {{ font-size: 11pt; margin: 4mm 0 1.5mm; break-after: avoid; }}
section.notes p, section.notes li {{ margin: 0 0 1.6mm; text-align: left; }}
section.notes ul {{ margin: 0 0 2mm; padding-left: 5mm; }}
section.notes bdi {{ font-family: Naskh, Vazir; }}
p.hand {{ font-family: Naskh; font-weight: 700; font-size: 17pt; text-align: center; color: #2c4f8c;
  margin: 0.4em 0 0.7em; word-spacing: 0.35em; }}
p.brk {{ text-align: center; color: #a89d88; margin: 0.4em 0 0.7em; }}
mark.add {{ background: #f6e3b4; padding: 0 2px; border-radius: 2px; color: inherit; }}
.note {{ font-family: Vazir; font-size: 8pt; color: #8a8374; }}
</style></head><body>
<section class="title">
  <p class="book">{html.escape(A.title)}</p>
  <div class="rule"></div>
  <p class="part">{html.escape(part)}</p>
  <p class="chap">{html.escape(chap)}</p>
  <p class="meta">{html.escape(A.label)}
  {LEGEND}</p>
</section>
<div class="cols">
{chr(10).join(body)}
</div>
{NOTES}
</body></html>"""
TMP = OUT.with_suffix(".tmp.html"); TMP.write_text(page, encoding="utf-8")

from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page()
    pg.goto(f"file://{TMP.resolve()}")
    pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(300)
    pg.pdf(path=str(OUT), prefer_css_page_size=True, print_background=True)
    b.close()
TMP.unlink(); print(f"wrote {OUT}", file=sys.stderr)
````

### `LICENSE`

<!-- bundle-file: LICENSE sha256=af7f621414b904053616a4ae3e0dacd5a1a9be9d2d90f558266627c2e8680859 -->
````text
MIT License

Copyright (c) 2026 Roohollah Kalatehjari

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
````
