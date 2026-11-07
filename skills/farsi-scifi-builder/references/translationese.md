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
