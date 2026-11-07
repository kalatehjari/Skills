# Narration script format

A plain UTF-8 text file. Everything above a line of `=====` is notes for people and is ignored by both renderers.

| Line | Meaning |
|---|---|
| `SPEAKER: text` | Spoken by that speaker. Speaker names are capitals (`NARRATOR`, `LEILA`, `SCREEN`, `ENGINEER`). |
| `[PAUSE 1.5s]` | Silence before the next line (the longest pending pause wins; pauses never add up). |
| `[SCENE BREAK — PAUSE 2.5s]` | A scene break; any bracketed line containing `PAUSE Ns` sets a pause. |
| `[END OF CHAPTER ONE — PAUSE 3s]` | Silence at the end. |
| `[SFX: a single soft interface tone]` | Soft chime (keywords: tone, chime). |
| `[SFX: a short burst of digital interference, about 1.5s …]` | Stuttering digital noise (keywords: interference, glitch, static; length from "N s"). Other effects become 1 s of silence. |
| `[…]` inside a spoken line | Direction, not spoken. "slow" → speed × 0.9; "quiet"/"soft" → volume × 0.8. |
| Blank lines, other `[…]` lines | Ignored. |

## Gaps between lines (both renderers)

- 0.75 s after a line that ends with `,` or `;` (the sentence continues in the next line).
- 0.5 s before a NARRATOR line that starts lower-case (a dialogue tag: "she said.").
- 0.7 s otherwise (a new paragraph).
- No gap straight after a sound effect unless a `[PAUSE]` asks for one.

## Inside a line (exact-pause mode, as narrate.py)

0.5 s after `. ? !` and `:`, 0.75 s after `, ;` and dashes or brackets, 0.25 s after `…`, 0.5 s at quotation marks. Decimal points and thousands commas inside numbers are not pauses. ALL-CAPS words are read as words. A one-word piece is said after a carrier phrase and cut out, because Kokoro garbles a word said alone.

## Writing tips

- One speaker per line; split dialogue from tags.
- Spell numbers and dates the way a narrator says them; list every such change in the casting sheet.
- Hyphenate letter abbreviations (`A-Q-I`), never separate them with commas.
- Display text in normal case under `SCREEN:`.
