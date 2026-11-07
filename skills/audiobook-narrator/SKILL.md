---
name: audiobook-narrator
description: Turn a chapter of the user's fiction (Possible Enough or any English novel) into a multi-voice audiobook with Kokoro TTS - write a speaker-tagged narration script, cast a voice per character, and render a chapter MP3 with exact punctuation pauses, or hand over the in-browser PE Narrator page. Use for "narrate this chapter", "make an audiobook", "multi-voice reading", "narration script", or any Kokoro/TTS audiobook request.
---

# Audiobook narrator (multi-voice, Kokoro)

Three stages, each usable on its own:

1. **Script** - turn a chapter into a speaker-tagged narration script plus a casting sheet.
2. **Render in the cloud** - run `scripts/narrate_cast.py` here and deliver the chapter MP3.
3. **Render on the user's Mac** - give them `assets/PE_Narrator.html` (runs Kokoro in the browser) or the Python scripts with `references/mac-setup.md`.

The user's existing audiobook work uses Kokoro voices; their auditions picked **Kokoro Heart (af_heart)** as the best narrator.

## 1. Write the narration script

Get the chapter text first (for PE, the newest `PE_v*_em.docx` in `/Novel/POSSIBLE ENOUGH/…/PE_v*_OUTPUT_em/`; Dropbox `fetch` of a docx returns its text, saved to a tool-results file when large - cut the chapter out by its `CHAPTER …` heading). Read the whole chapter before writing.

Format (full spec in `references/script-format.md`):

```
NARRATOR: Mara had drawn the birds too large. …
LEILA: Those are very big birds,
NARRATOR: she said.
[PAUSE 1s]
[SCENE BREAK — PAUSE 2.5s]
[SFX: a single soft interface tone]
SCREEN: Exterior exposure: prohibited.
MARA: [quiet, almost to herself] That's different.
```

Rules that matter:
- **Split dialogue from its tag.** The character says the quoted words; the NARRATOR says "she said." A line that stops mid-sentence ends with its comma ("Those are very big birds,") so the renderer uses the comma pause before the tag.
- **Never change the author's words.** Only spoken forms change, and every change is listed in the casting sheet: numbers and dates in words ("the seventeenth of September, twenty sixty-four"), "Dr" → "Doctor", "%" → "per cent", "+" → "plus". Write letter abbreviations hyphenated ("A-Q-I"), never with commas ("A, Q, I" makes one-letter chunks and long pauses).
- **Capitals are display text**, not shouting: give screen, record and handwriting text to a SCREEN (or HAND) speaker in normal case. TTS spells out all-caps words.
- **Unreadable text** (garbled characters such as ▒) can't be spoken: use an `[SFX: … interference …]` line and flag it as an open decision for the author.
- Inline `[directions]` are not spoken. The renderer acts on "slow" (speed × 0.9) and "quiet"/"soft" (volume × 0.8); others are notes for a human.
- Part/chapter titles are spoken by the narrator at the start.
- **Verify** the script against the source with a word-level diff (strip tags and directions, compare token sequences with `difflib`); the only differences allowed are the listed spoken forms.

Also write a **casting sheet** (`PE_v8_ChNN_casting_and_pronunciation.md`): speakers with a one-line voice brief and Kokoro voice, a pronunciation table for names, the spoken-form table, and open decisions for the author. The PE cast so far is in `references/pe-cast.md`; keep each character's voice fixed across the book and add new characters as they appear.

Save both files to Dropbox `/Novel/Audio Auditions/PE v8.0 English narration/` (the user allows Dropbox uploads without asking; batch them).

## 2. Render in the cloud (recommended - the recogniser checks every take)

```bash
bash scripts/setup_env.sh            # sherpa-onnx, soundfile, scipy, ffmpeg check, Kokoro v1.0 + Parakeet models into ./models
python3 scripts/narrate_cast.py PE_v8_Ch01_narration_script.txt "Possible Enough v8 - Chapter 01.mp3"
```

- Models come from GitHub releases (k2-fsa/sherpa-onnx); Hugging Face and jsDelivr may be blocked in the sandbox, GitHub is not.
- `narrate_cast.py` imports `narrate.py` (the user's rule-based narrator: exact punctuation pauses, one-word lines said with a neighbour and cut out, maths operators, unreadable characters, Parakeet recogniser retakes). Keep both in the same folder and the models in `./models` (or pass `--model-dir` / `--checker-dir`).
- Cast lives at the top of `narrate_cast.py`; override per run with `--cast MARA=af_bella,ORISON=bm_george:0.9`. `--sample 40` renders the first 40 lines; `--no-check` skips the recogniser.
- Between-line gaps follow narrate.py's rules: 0.75 s after a line ending in a comma, 0.5 s before a lower-case narrator tag, 0.7 s new paragraph; an explicit `[PAUSE]` wins if longer.
- Every line is cached in `work/cache` (keyed by voice, speed and text): reruns resume, and changing one voice re-records only its lines.
- Chapter One (264 lines, 24.5 min of audio) took about 30 min. Run it in the background (`nohup … > run.log 2>&1 &`) and poll; tool calls time out at 10 min. "Creating a resampler" lines in the log are normal.
- "N takes … still unclear" usually means the recogniser writes the words differently (2064 vs "twenty sixty-four", "percent"), not that the audio is wrong. Spot-check the opening and ending by transcribing with the Parakeet checker.
- Deliver the MP3 with SendUserFile (Dropbox's create_file can't take binary).

## 3. Render on the user's Mac

- **`assets/PE_Narrator.html`** - a single page: load Kokoro (kokoro-js 1.2.1 from jsDelivr, model `onnx-community/Kokoro-82M-v1.0-ONNX`, WebGPU fp32 or WASM q8), open a script, cast voices with ▶ Try, record line by line with ▶ / ↻ new take / ✎ edit, save MP3 (lamejs) or WAV. Same script format and gap rules; no recogniser, so the user listens and retakes garbled lines. `?mock=1` tests the page without the model.
  - Keep Kokoro on the page itself: **a module Worker fails on file:// pages** (Chrome reports a bare "worker error"); dynamic `import()` from the page works.
  - The sandbox can't reach jsDelivr or Hugging Face, so test UI changes with `?mock=1` in Playwright (`executablePath: '/opt/pw-browsers/chromium'`) and, for the import path, serve `kokoro-js` from `npm pack` on a local server with `Access-Control-Allow-Origin: *`.
- **Python on the Mac** - `references/mac-setup.md`.

## Files

| Path | What |
|---|---|
| `scripts/narrate.py` | The user's single-voice rule-based narrator (Kokoro v1.0 on sherpa-onnx + Parakeet checker). Unchanged. |
| `scripts/narrate_cast.py` | Multi-voice renderer for narration scripts, built on narrate.py. |
| `scripts/setup_env.sh` | Installs packages and downloads both models into `./models`. |
| `assets/PE_Narrator.html` | In-browser narrator with UI. |
| `references/script-format.md` | Full script format. |
| `references/pe-cast.md` | PE cast, voice briefs and pronunciations so far. |
| `references/mac-setup.md` | Running the Python version on a Mac. |
