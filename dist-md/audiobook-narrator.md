---
name: audiobook-narrator
description: Turn a chapter of the user's fiction (Possible Enough or any English novel) into a multi-voice audiobook with Kokoro TTS - write a speaker-tagged narration script, cast a voice per character, and render a chapter MP3 with exact punctuation pauses, or hand over the in-browser PE Narrator page. Use for "narrate this chapter", "make an audiobook", "multi-voice reading", "narration script", or any Kokoro/TTS audiobook request.
---

**Single-file build.** This is the `audiobook-narrator` skill packed into one file on 2026-11-07. The instructions below are its SKILL.md, unchanged. Its supporting files (3 reference files, 1 asset, 3 scripts and the licence) are embedded verbatim under "Bundled files" at the end, each with a SHA-256 checksum. You can read a reference there directly. Before you run a script or use an asset, unpack the files once:

```bash
python3 - "${CLAUDE_SKILL_DIR}/SKILL.md" "${TMPDIR:-/tmp}/audiobook-narrator" <<'PY'
import hashlib, os, re, sys
src, out = sys.argv[1], sys.argv[2]
if not os.path.isfile(src):
    src = "/mnt/skills/user/audiobook-narrator/SKILL.md"
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

The first argument is the path of this file. Claude Code and Cowork fill it in for you; elsewhere, use the path you read this file from (on claude.ai the command also tries `/mnt/skills/user/audiobook-narrator/SKILL.md`). The command prints the folder it wrote to. From then on, use that folder wherever the instructions mean this skill's folder: paths such as `scripts/...`, `references/...`, `assets/...` and `<this-skill>/...` all point into it.

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

---

## Bundled files

The skill's supporting files, verbatim. Unpack them with the command at the top, or read one here. Line is where each file starts in this document.

| File | Size | Line |
|---|---:|---:|
| `references/mac-setup.md` | 1.0 KB | 132 |
| `references/pe-cast.md` | 1.9 KB | 152 |
| `references/script-format.md` | 1.9 KB | 194 |
| `assets/PE_Narrator.html` | 29.8 KB | 232 |
| `scripts/narrate.py` | 28.1 KB | 811 |
| `scripts/narrate_cast.py` | 11.0 KB | 1416 |
| `scripts/setup_env.sh` | 0.9 KB | 1679 |
| `LICENSE` | 1.1 KB | 1701 |

### `references/mac-setup.md`

<!-- bundle-file: references/mac-setup.md sha256=517a049c29b8e72c74d9e8019cd45e322608d73f7902f23a71d5010da6ff3e2f -->
````markdown
# Running the Python narrator on a Mac

1. Install Python 3.10+ from python.org, and ffmpeg (Homebrew from brew.sh, then `brew install ffmpeg`).
2. `pip3 install sherpa-onnx soundfile scipy numpy`
3. Put `narrate.py`, `narrate_cast.py` and the script in one folder, with a `models` folder inside it.
4. Download and unpack into `models` (about 450 MB; double-click a .tar.bz2 to unpack):
   - https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/kokoro-multi-lang-v1_0.tar.bz2
   - https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8.tar.bz2
5. `cd` into the folder and run
   `python3 narrate_cast.py PE_v8_Ch01_narration_script.txt "Possible Enough v8 - Chapter 01.mp3"`

Or simply `bash setup_env.sh` from the scripts folder, which does steps 2 and 4.

The browser alternative needs no installation: double-click `PE_Narrator.html` in Chrome or Safari (internet needed the first time to download the model).
````

### `references/pe-cast.md`

<!-- bundle-file: references/pe-cast.md sha256=dc0ce10524b768f22373523f86a371c2b06c285a22b2b5f53feb0d700ce0eefe -->
````markdown
# Possible Enough - cast so far (from Chapter One, v8.0)

Keep each voice fixed for the whole book; add characters as they appear.

| Speaker | Who | Voice brief | Kokoro voice | Speed | Loudness |
|---|---|---|---|---|---|
| NARRATOR | Third person, close on Leila | Calm, intimate, unhurried; neutral or light NZ/British | af_heart | 0.95 | 1.0 |
| LEILA | Leila Vale, 45, climate scientist, Mara's mother | Warm but controlled; a scientist hiding fear | bf_emma | 1.00 | 1.0 |
| MARA | Mara, 8, under the oxygen hood | Small, clear, matter-of-fact, never cute | af_sky | 1.05 | 1.0 |
| AMRITA | Respiratory nurse | Brisk, friendly, teasing | af_nicole | 1.00 | 1.0 |
| NIA | Dr Nia Okafor, systems scientist | Measured, precise, no contractions | bf_isabella | 0.98 | 1.0 |
| ORISON | The AI's voice | Even, neutral, unhurried; never robotic or menacing | am_michael | 0.90 | 1.0 |
| SCREEN | Display, record and summons text | Flat read-out, quieter | af_heart | 0.90 | 0.8 |
| ENGINEER | Senior engineers (minor) | Any distinct adult voice | am_adam | 1.00 | 1.0 |

Still to cast (later chapters): Elias Venn, Tom Arden, Celia Park, Jonah Reyes, Elena Reyes, Sofia Ren, Arun Patel, Maya Chen, Tara Nome, Hana and Dev Nome, Amina Kaur, Kelechi Okafor, the older Elias, and a HAND voice for handwriting if wanted. v8 retired Marianne Tait, Caleb Rangi, Owen Hale and Isla Raman.

## Pronunciation

| Word | Say |
|---|---|
| Leila | LAY-lah |
| Mara | MAH-rah |
| Amrita | um-REE-tah |
| Nia Okafor | NEE-ah oh-KAH-for |
| Elias Venn | eh-LYE-us VEN |
| Orison | OR-ih-zun (an old word for prayer; not "horizon") |
| Noah | NO-ah |
| Auckland | AWK-lund |
| Vale | VAIL |

## Open decisions from Chapter One (ask the author)

1. The garbled line before "YOU." - currently an interference effect with no words.
2. Who says "YOU." - currently SCREEN; ORISON is the alternative.
3. Whether to keep plain dialogue tags ("she said") or drop them for a more dramatised feel.
````

### `references/script-format.md`

<!-- bundle-file: references/script-format.md sha256=d303d21bbb884990d7ccce9042da4ea3ca987aa32db50fcad436d9e452b7c65b -->
````markdown
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
````

### `assets/PE_Narrator.html`

<!-- bundle-file: assets/PE_Narrator.html sha256=84606783bfc31861bccca4d49fa54b11578feb554ab2e378fc6c48be2faf35e3 -->
````html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PE Narrator</title>
<style>
:root{
  --bg:#f6f5f2; --panel:#ffffff; --ink:#1d1d1f; --muted:#6b6b70; --line:#e3e1dc;
  --accent:#2f5d8a; --accent-ink:#ffffff; --ok:#2e7d4f; --warn:#a15c00; --bad:#b3261e;
  --chip:#eef2f7; --sel:#fff6d6;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --bg:#151618; --panel:#1e2023; --ink:#ececec; --muted:#9a9aa0; --line:#2e3135;
    --accent:#7fb0e0; --accent-ink:#0d1520; --ok:#6cc391; --warn:#e0a85a; --bad:#ef8a83;
    --chip:#25303b; --sel:#3a3420;
  }
}
:root[data-theme="dark"]{
  --bg:#151618; --panel:#1e2023; --ink:#ececec; --muted:#9a9aa0; --line:#2e3135;
  --accent:#7fb0e0; --accent-ink:#0d1520; --ok:#6cc391; --warn:#e0a85a; --bad:#ef8a83;
  --chip:#25303b; --sel:#3a3420;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
header{padding:20px 16px 8px;max-width:1100px;margin:auto}
header h1{margin:0;font-size:22px}
header p{margin:4px 0 0;color:var(--muted)}
main{max-width:1100px;margin:auto;padding:8px 16px 40px;display:grid;gap:14px}
section{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
section h2{margin:0 0 10px;font-size:16px;display:flex;align-items:center;gap:8px}
.step{display:inline-grid;place-items:center;width:22px;height:22px;border-radius:50%;background:var(--accent);color:var(--accent-ink);font-size:12px;font-weight:700}
.row{display:flex;flex-wrap:wrap;gap:10px;align-items:center}
button{font:inherit;border:1px solid var(--line);background:var(--panel);color:var(--ink);border-radius:8px;padding:7px 12px;cursor:pointer}
button.primary{background:var(--accent);color:var(--accent-ink);border-color:var(--accent);font-weight:600}
button:disabled{opacity:.45;cursor:default}
button.icon{padding:3px 8px;font-size:13px}
select,input[type=number],input[type=text]{font:inherit;border:1px solid var(--line);background:var(--panel);color:var(--ink);border-radius:8px;padding:6px 8px}
textarea{width:100%;min-height:120px;font:13px/1.4 ui-monospace,Menlo,monospace;border:1px solid var(--line);background:var(--panel);color:var(--ink);border-radius:8px;padding:8px}
.muted{color:var(--muted)}
.bar{height:8px;background:var(--line);border-radius:4px;overflow:hidden;flex:1;min-width:120px}
.bar>div{height:100%;width:0;background:var(--accent);transition:width .2s}
table{width:100%;border-collapse:collapse}
th,td{text-align:left;padding:6px 6px;border-bottom:1px solid var(--line);vertical-align:middle}
th{font-size:12px;color:var(--muted);font-weight:600}
.cast input[type=number]{width:72px}
.lines{max-height:440px;overflow:auto;border:1px solid var(--line);border-radius:8px}
.ln{display:grid;grid-template-columns:44px 92px 1fr auto;gap:8px;padding:6px 8px;border-bottom:1px solid var(--line);align-items:start}
.ln:last-child{border-bottom:0}
.ln.cur{background:var(--sel)}
.ln .n{color:var(--muted);font-size:12px;padding-top:2px}
.ln .who{font-size:12px;font-weight:700;padding:2px 6px;border-radius:6px;background:var(--chip);justify-self:start}
.ln .txt{white-space:pre-wrap;word-break:break-word}
.ln .txt[contenteditable=true]{outline:1px dashed var(--accent);border-radius:4px;padding:0 2px}
.ln.dir .txt{color:var(--muted);font-style:italic}
.st{font-size:12px;white-space:nowrap}
.st.done{color:var(--ok)} .st.err{color:var(--bad)} .st.work{color:var(--warn)}
.tools{display:flex;gap:4px}
audio{width:100%;margin-top:8px}
.note{font-size:13px;color:var(--muted);margin-top:6px}
.pill{font-size:12px;padding:2px 8px;border-radius:999px;background:var(--chip)}
@media (max-width:640px){.ln{grid-template-columns:34px 1fr auto}.ln .who{grid-column:2}.ln .txt{grid-column:1/-1}}
</style>
</head>
<body>
<header>
  <h1>PE Narrator</h1>
  <p>Multi-voice audiobook narration with Kokoro, running entirely in this browser. Nothing is uploaded.</p>
</header>
<main>

<section>
  <h2><span class="step">1</span> Load the voices</h2>
  <div class="row">
    <label>Engine
      <select id="device">
        <option value="auto">Automatic (GPU if available)</option>
        <option value="webgpu">GPU (WebGPU, faster)</option>
        <option value="wasm">CPU (WASM, slower, works everywhere)</option>
      </select>
    </label>
    <button class="primary" id="loadBtn">Load Kokoro</button>
    <div class="bar"><div id="loadBar"></div></div>
    <span id="loadMsg" class="muted">Not loaded</span>
  </div>
  <div class="note">The first load downloads the Kokoro model (about 90–330 MB) and keeps it in the browser's cache, so later loads are quick. Use Chrome or Safari on your Mac.</div>
</section>

<section>
  <h2><span class="step">2</span> Open a narration script</h2>
  <div class="row">
    <input type="file" id="file" accept=".txt,text/plain">
    <span class="muted">or paste it below, then</span>
    <button id="parseBtn">Read script</button>
    <span id="scriptMsg" class="pill">No script</span>
  </div>
  <textarea id="scriptText" placeholder="NARRATOR: Mara had drawn the birds too large.
MARA: They're closer,
NARRATOR: Mara said.
[PAUSE 1s]"></textarea>
  <div class="note">Format: <code>SPEAKER: text</code> per line; <code>[PAUSE 1.5s]</code>, <code>[SCENE BREAK — PAUSE 2.5s]</code>, <code>[SFX: soft interface tone]</code>, <code>[SFX: digital interference, 1.5s]</code>. Notes in [brackets] inside a line are not spoken ("slow", "quiet" and "soft" change the delivery). Anything above a line of ===== is ignored.</div>
</section>

<section>
  <h2><span class="step">3</span> Cast the voices</h2>
  <table class="cast"><thead><tr><th>Speaker</th><th>Voice</th><th>Speed</th><th>Loudness</th><th>Lines</th><th></th></tr></thead>
  <tbody id="castBody"><tr><td colspan="6" class="muted">Read a script to see its speakers.</td></tr></tbody></table>
  <div class="row" style="margin-top:8px">
    <label><input type="checkbox" id="exact" checked> Exact punctuation pauses (as in narrate.py)</label>
    <button id="resetCast">Reset to the PE cast</button>
  </div>
  <div class="note">Exact pauses: each line is spoken in pieces cut at punctuation, with 0.5 s after . ? ! and :, 0.75 s after , ; — and 0.25 s after …. Untick it to let Kokoro phrase whole lines itself (more natural flow, less exact timing).</div>
</section>

<section>
  <h2><span class="step">4</span> Record</h2>
  <div class="row">
    <button class="primary" id="goBtn" disabled>Record all</button>
    <button id="stopBtn" disabled>Stop</button>
    <button id="buildBtn" disabled>Build audiobook</button>
    <div class="bar"><div id="recBar"></div></div>
    <span id="recMsg" class="muted"></span>
  </div>
  <div class="note">Recorded lines are kept while this page is open, so Stop and Record all carry on where they stopped. ▶ plays a line, ↻ records a new take, ✎ edits the words (then ↻). Listen for any garbled word and give it a new take.</div>
  <div class="lines" id="lines" style="margin-top:10px"></div>
</section>

<section>
  <h2><span class="step">5</span> Listen and save</h2>
  <div class="row">
    <input type="text" id="outName" value="Possible Enough v8 - Chapter 01" style="flex:1;min-width:220px">
    <button id="mp3Btn" disabled>Save MP3</button>
    <button id="wavBtn" disabled>Save WAV</button>
    <span id="outMsg" class="muted"></span>
  </div>
  <audio id="player" controls></audio>
</section>

</main>

<script src="https://cdnjs.cloudflare.com/ajax/libs/lamejs/1.2.1/lame.min.js"></script>
<script>
"use strict";
// ------------------------------------------------------------------ settings
const SR = 24000;
const VOICES = ("af_heart af_alloy af_aoede af_bella af_jessica af_kore af_nicole af_nova af_river af_sarah af_sky " +
  "am_adam am_echo am_eric am_fenrir am_liam am_michael am_onyx am_puck am_santa " +
  "bf_alice bf_emma bf_isabella bf_lily bm_daniel bm_fable bm_george bm_lewis").split(" ");
const PE_CAST = {
  NARRATOR: ["af_heart", 0.95, 1.0], LEILA: ["bf_emma", 1.0, 1.0], MARA: ["af_sky", 1.05, 1.0],
  AMRITA: ["af_nicole", 1.0, 1.0], NIA: ["bf_isabella", 0.98, 1.0], ORISON: ["am_michael", 0.9, 1.0],
  SCREEN: ["af_heart", 0.9, 0.8], ENGINEER: ["am_adam", 1.0, 1.0],
};
const RULES = { full: 0.5, mid: 0.75, colon: 0.5, quote: 0.5, ellipsis: 0.25 };
const GAP = { comma: 0.75, tag: 0.5, para: 0.7 };
const CARRIER = "And then I heard it said,";
const MATH = { "+": "plus", "=": "equals", "×": "times", "÷": "divided by", "−": "minus" };
const MOCK = new URLSearchParams(location.search).has("mock");   // for testing the page without the model

// ------------------------------------------------------------------ small helpers
const $ = (id) => document.getElementById(id);
const store = {
  get(k, d) { try { const v = localStorage.getItem("pe-narrator:" + k); return v ? JSON.parse(v) : d; } catch { return d; } },
  set(k, v) { try { localStorage.setItem("pe-narrator:" + k, JSON.stringify(v)); } catch {} },
};
function esc(s) { return s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }
function concat(parts) {
  let n = 0; for (const p of parts) n += p.length;
  const out = new Float32Array(n); let o = 0;
  for (const p of parts) { out.set(p, o); o += p.length; }
  return out;
}
const silence = (s) => new Float32Array(Math.max(0, Math.round(s * SR)));

// ------------------------------------------------------------------ the voices (Kokoro, loaded on this page)
// A background worker would be smoother, but browsers block workers in pages opened as files,
// so the model runs on the page itself; the page pauses briefly between pieces to stay responsive.
const KOKORO_URL = "https://cdn.jsdelivr.net/npm/kokoro-js@1.2.1/dist/kokoro.web.js";
const MODEL_ID = "onnx-community/Kokoro-82M-v1.0-ONNX";
let tts = null, ready = false;

function resample(x, sr) {
  if (sr === SR) return x;
  const r = sr / SR, n = Math.floor(x.length / r), y = new Float32Array(n);
  for (let i = 0; i < n; i++) { const t = i * r, k = Math.floor(t), f = t - k; y[i] = (x[k] || 0) * (1 - f) + (x[k + 1] || 0) * f; }
  return y;
}

async function synth(text, voice, speed) {
  if (MOCK) {   // a tone whose length follows the text, so the page can be tested without the model
    const n = Math.round((0.06 * text.length + 0.2) * SR / speed), y = new Float32Array(n + Math.round(0.1 * SR));
    for (let i = 0; i < n; i++) y[i + 1200] = 0.3 * Math.sin(i / 8) * (/,\s/.test(text) && Math.abs(i - n * 0.6) < 2400 ? 0 : 1);
    await new Promise((r) => setTimeout(r, 5));
    return y;
  }
  await new Promise((r) => setTimeout(r, 0));   // let the page update between pieces
  const a = await tts.generate(text, { voice, speed });
  return resample(new Float32Array(a.audio), a.sampling_rate);
}

async function loadModel(choice) {
  const { KokoroTTS } = await import(KOKORO_URL);
  const progress = (p) => {
    if (p && p.status === "progress" && p.total) {
      $("loadBar").style.width = Math.round(100 * p.loaded / p.total) + "%";
      $("loadMsg").textContent = "Downloading " + (p.file || "") + " " + Math.round(100 * p.loaded / p.total) + "%";
    }
  };
  let device = choice === "auto" ? ("gpu" in navigator ? "webgpu" : "wasm") : choice;
  try {
    tts = await KokoroTTS.from_pretrained(MODEL_ID, { dtype: device === "webgpu" ? "fp32" : "q8", device, progress_callback: progress });
    if (device === "webgpu") await tts.generate("Ready.", { voice: "af_heart" });   // make sure the GPU really works
  } catch (err) {
    if (device !== "webgpu") throw err;
    $("loadMsg").textContent = "GPU not available here; using the CPU instead…";
    device = "wasm";
    tts = await KokoroTTS.from_pretrained(MODEL_ID, { dtype: "q8", device, progress_callback: progress });
  }
  return device;
}

$("loadBtn").onclick = async () => {
  if (MOCK) { ready = true; $("loadMsg").textContent = "Ready (test mode)"; $("loadBtn").disabled = true; refreshButtons(); return; }
  $("loadBtn").disabled = true; $("loadMsg").textContent = "Starting…";
  store.set("device", $("device").value);
  try {
    const device = await loadModel($("device").value);
    ready = true; $("loadBar").style.width = "100%";
    $("loadMsg").textContent = "Ready (" + (device === "webgpu" ? "GPU" : "CPU") + ")";
    refreshButtons();
  } catch (err) {
    console.error(err);
    $("loadMsg").textContent = "Could not load Kokoro: " + (err && err.message ? err.message : err);
    $("loadBtn").disabled = false;
  }
};
$("device").value = store.get("device", "auto");

// ------------------------------------------------------------------ script parsing (same rules as narrate_cast.py)
function parseScript(text) {
  const k = text.indexOf("=====");
  if (k >= 0) text = text.slice(text.indexOf("\n", k) + 1);
  const items = [];
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.trim();
    if (!line) continue;
    if (line.startsWith("[")) {
      const inner = line.replace(/^\[|\]$/g, "");
      if (/^SFX/i.test(inner)) { items.push({ kind: "sfx", desc: inner.split(":").slice(1).join(":").trim() || inner }); continue; }
      const m = inner.match(/PAUSE\s+([\d.]+)\s*s/i);
      if (m) items.push({ kind: "pause", secs: parseFloat(m[1]), label: inner });
      continue;
    }
    const m = line.match(/^([A-Z][A-Z ]*[A-Z]|[A-Z]):\s*(.*)$/);
    if (!m) continue;
    const dirs = [...m[2].matchAll(/\[([^\]]*)\]/g)].map((x) => x[1]).join(" ").toLowerCase();
    const body = m[2].replace(/\s*\[[^\]]*\]\s*/g, " ").trim();
    if (body) items.push({ kind: "say", who: m[1], text: body, dirs });
  }
  // the silence before each line
  const out = []; let pend = 0, prev = null;
  for (const it of items) {
    if (it.kind === "pause") { pend = Math.max(pend, it.secs); out.push({ ...it, shown: true }); continue; }
    if (it.kind === "sfx") { out.push({ ...it, gap: pend }); pend = 0; prev = null; continue; }
    let gap = GAP.para;
    if (prev) {
      if (/[,;]\s*$/.test(prev.text)) gap = GAP.comma;
      else if (it.who === "NARRATOR" && /^[a-z]/.test(it.text)) gap = GAP.tag;
    } else if (out.length && out[out.length - 1].kind === "sfx") gap = 0;
    const first = !out.some((o) => o.kind === "say" || o.kind === "sfx");
    out.push({ ...it, gap: Math.max(first ? 0 : gap, pend) });
    pend = 0; prev = it;
  }
  return { lines: out, tail: Math.max(pend, 1) };
}

// ------------------------------------------------------------------ pause rules inside a line (port of narrate.py)
function speakable(t) {
  return t.replace(/\S+/g, (w) => (w.length > 1 && /^[A-Z'’.,;:!?-]+$/.test(w) && /[A-Z]{2}/.test(w) ? w.toLowerCase() : w))
          .replace(/\s([+=×÷−])\s/g, (m, op) => " " + MATH[op] + " ");
}
function chunks(text) {   // [{text, pause}] ; the pause comes after the chunk
  const out = []; let buf = "";
  const push = (mark, pause) => { const t = (buf + mark).trim(); if (t.replace(/[.,;:!?…]/g, "").trim()) out.push({ text: t, pause }); else if (out.length) out[out.length - 1].pause = Math.max(out[out.length - 1].pause, pause); buf = ""; };
  for (let i = 0; i < text.length; i++) {
    const c = text[i], prevD = /\d/.test(text[i - 1] || ""), nextD = /\d/.test(text[i + 1] || "");
    if (text.startsWith("...", i)) { push("...", RULES.ellipsis); i += 2; }
    else if (c === "…") push("...", RULES.ellipsis);
    else if (".?!".includes(c) && !(c === "." && prevD && nextD)) push(c, RULES.full);
    else if (c === "," && prevD && nextD) buf += c;
    else if (",;".includes(c)) push(c, RULES.mid);
    else if ("—–()".includes(c)) push("", RULES.mid);
    else if (c === ":") push(":", RULES.colon);
    else if ("“”\"".includes(c)) push("", RULES.quote);
    else buf += c;
  }
  push("", 0);
  if (out.length) out[out.length - 1].pause = 0;
  return out;
}
const wordCount = (t) => (t.match(/[A-Za-z0-9’']+/g) || []).length;

// ------------------------------------------------------------------ audio clean-up
function trim(x) {
  let mx = 0; for (let i = 0; i < x.length; i++) mx = Math.max(mx, Math.abs(x[i]));
  const th = Math.max(1e-4, 0.005 * mx);
  let a = 0, b = x.length - 1;
  while (a < x.length && Math.abs(x[a]) <= th) a++;
  while (b > a && Math.abs(x[b]) <= th) b--;
  if (a >= b) return new Float32Array(0);
  const s = Math.max(0, a - Math.round(0.015 * SR)), e = Math.min(x.length, b + Math.round(0.045 * SR));
  const y = x.slice(s, e), f = Math.min(Math.round(0.005 * SR), y.length >> 1);
  for (let i = 0; i < f; i++) { y[i] *= i / f; y[y.length - 1 - i] *= i / f; }
  return y;
}
function cutAfterCarrier(y) {   // keep only what follows the last real pause (the comma after the carrier)
  const fr = Math.round(0.01 * SR), n = Math.floor(y.length / fr), rms = new Float32Array(n);
  let mx = 0;
  for (let k = 0; k < n; k++) { let s = 0; for (let i = k * fr; i < (k + 1) * fr; i++) s += y[i] * y[i]; rms[k] = Math.sqrt(s / fr); mx = Math.max(mx, rms[k]); }
  const th = 0.06 * mx; let best = -1, run = 0;
  for (let k = 0; k < n; k++) {
    if (rms[k] < th) run++;
    else { if (run >= 8 && k - run > 10) best = k; run = 0; }
  }
  if (best < 0) return null;
  return trim(y.slice(Math.max(0, best * fr - Math.round(0.02 * SR))));
}

async function sayChunk(text, voice, speed) {
  if (wordCount(text) === 1) {   // Kokoro garbles a word said on its own: say it after a carrier, then cut
    const y = await synth(CARRIER + " " + text, voice, speed);
    const cut = cutAfterCarrier(trim(y));
    if (cut && cut.length > 0.12 * SR) return cut;
  }
  return trim(await synth(text, voice, speed));
}

async function recordLine(line, cast) {
  const [voice, speed0] = cast[line.who] || cast.NARRATOR || PE_CAST.NARRATOR;
  const speed = speed0 * (/slow/.test(line.dirs) ? 0.9 : 1);
  const text = speakable(line.text);
  if (!$("exact").checked) {
    if (wordCount(text) === 1) return sayChunk(text, voice, speed);
    return trim(await synth(text, voice, speed));
  }
  const parts = [];
  for (const c of chunks(text)) {
    parts.push(await sayChunk(c.text, voice, speed));
    if (c.pause) parts.push(silence(c.pause));
  }
  return concat(parts);
}

// ------------------------------------------------------------------ sound effects
function sfx(desc) {
  const d = desc.toLowerCase();
  if (/tone|chime/.test(d)) {
    const n = Math.round(0.9 * SR), y = new Float32Array(n);
    for (let i = 0; i < n; i++) { const t = i / SR; y[i] = 0.12 * (Math.sin(2 * Math.PI * 880 * t) + 0.35 * Math.sin(2 * Math.PI * 1320 * t)) * Math.exp(-4.5 * t) * Math.min(1, i / 240); }
    return y;
  }
  if (/interference|glitch|static/.test(d)) {
    const m = d.match(/([\d.]+)\s*s/), n = Math.round((m ? parseFloat(m[1]) : 1.5) * SR), y = new Float32Array(n);
    let seed = 13; const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
    let pos = 0, prevN = 0;
    while (pos < n) {
      const burst = Math.round((0.03 + 0.11 * rnd()) * SR), on = rnd() < 0.7, g = 0.4 + 0.6 * rnd();
      for (let i = pos; i < Math.min(n, pos + burst); i++) {
        const noise = (rnd() * 2 - 1); prevN = 0.8 * prevN + 0.2 * noise;
        const buzz = Math.sin(2 * Math.PI * 120 * i / SR) > 0 ? 0.3 : -0.3;
        y[i] = on ? 0.18 * g * (prevN * 1.5 + buzz) : 0;
      }
      pos += burst + Math.round(0.06 * rnd() * SR);
    }
    const f = Math.round(0.02 * SR); for (let i = 0; i < f; i++) { y[i] *= i / f; y[n - 1 - i] *= i / f; }
    return y;
  }
  return silence(1);
}

// ------------------------------------------------------------------ state and UI
let script = null;      // {lines, tail}
let cast = {};
const takes = new Map(); // line index -> Float32Array
let running = false, stopAsked = false, built = null;

function castFor(speakers) {
  const saved = store.get("cast", {});
  const c = {};
  for (const s of speakers) c[s] = saved[s] || PE_CAST[s] || PE_CAST.NARRATOR;
  return c;
}
function renderCast() {
  const body = $("castBody");
  const speakers = Object.keys(cast);
  if (!speakers.length) { body.innerHTML = '<tr><td colspan="6" class="muted">Read a script to see its speakers.</td></tr>'; return; }
  const count = (s) => script.lines.filter((l) => l.kind === "say" && l.who === s).length;
  body.innerHTML = speakers.map((s) => `<tr data-s="${esc(s)}">
    <td><b>${esc(s)}</b>${PE_CAST[s] ? "" : ' <span class="muted">(new)</span>'}</td>
    <td><select class="v">${VOICES.map((v) => `<option ${v === cast[s][0] ? "selected" : ""}>${v}</option>`).join("")}</select></td>
    <td><input class="sp" type="number" min="0.5" max="2" step="0.05" value="${cast[s][1]}"></td>
    <td><input class="ld" type="number" min="0.2" max="1.5" step="0.05" value="${cast[s][2]}"></td>
    <td class="muted">${count(s)}</td>
    <td><button class="icon pv" title="Hear this voice">▶ Try</button></td></tr>`).join("");
  body.querySelectorAll("tr").forEach((tr) => {
    const s = tr.dataset.s;
    const upd = () => {
      const nv = [tr.querySelector(".v").value, parseFloat(tr.querySelector(".sp").value) || 1, parseFloat(tr.querySelector(".ld").value) || 1];
      const changedVoice = nv[0] !== cast[s][0] || nv[1] !== cast[s][1];
      cast[s] = nv; store.set("cast", { ...store.get("cast", {}), [s]: nv });
      if (changedVoice) script.lines.forEach((l, i) => { if (l.who === s) { takes.delete(i); setStatus(i, ""); } });
      built = null; refreshButtons();
    };
    tr.querySelectorAll("select,input").forEach((el) => (el.onchange = upd));
    tr.querySelector(".pv").onclick = async () => {
      if (!ready) return alert("Load Kokoro first (step 1).");
      const line = script.lines.find((l) => l.kind === "say" && l.who === s && wordCount(l.text) > 4) || script.lines.find((l) => l.who === s);
      play(scaled(await recordLine(line, cast), cast[s][2]));
    };
  });
}
function renderLines() {
  const box = $("lines");
  box.innerHTML = script.lines.map((l, i) => {
    if (l.kind === "say") return `<div class="ln" id="ln${i}"><span class="n">${i + 1}</span><span class="who">${esc(l.who)}</span>
      <span class="txt">${esc(l.text)}${l.dirs ? ` <span class="muted">[${esc(l.dirs)}]</span>` : ""}</span>
      <span class="tools"><span class="st" id="st${i}"></span><button class="icon" data-a="play" data-i="${i}" title="Play">▶</button><button class="icon" data-a="redo" data-i="${i}" title="New take">↻</button><button class="icon" data-a="edit" data-i="${i}" title="Edit words">✎</button></span></div>`;
    const label = l.kind === "sfx" ? "Sound: " + l.desc : l.label;
    return `<div class="ln dir" id="ln${i}"><span class="n">${i + 1}</span><span class="who">${l.kind === "sfx" ? "SFX" : "PAUSE"}</span><span class="txt">${esc(label)}</span><span class="tools"><span class="st" id="st${i}"></span></span></div>`;
  }).join("");
  box.onclick = async (e) => {
    const b = e.target.closest("button"); if (!b) return;
    const i = +b.dataset.i, line = script.lines[i];
    if (b.dataset.a === "play") {
      if (!takes.has(i)) { if (!ready) return alert("Load Kokoro first (step 1)."); await recordOne(i); }
      play(scaled(takes.get(i), (cast[line.who] || [0, 0, 1])[2]));
    } else if (b.dataset.a === "redo") {
      if (!ready) return alert("Load Kokoro first (step 1).");
      takes.delete(i); built = null; await recordOne(i);
      play(scaled(takes.get(i), (cast[line.who] || [0, 0, 1])[2]));
    } else if (b.dataset.a === "edit") {
      const t = document.querySelector(`#ln${i} .txt`);
      if (t.isContentEditable) { line.text = t.textContent.replace(/\s*\[[^\]]*\]\s*$/, "").trim(); t.contentEditable = false; takes.delete(i); setStatus(i, "edited"); built = null; refreshButtons(); }
      else { t.textContent = line.text; t.contentEditable = true; t.focus(); b.title = "Done editing"; }
    }
  };
}
function setStatus(i, s, cls) { const el = $("st" + i); if (el) { el.textContent = s; el.className = "st " + (cls || ""); } }
function refreshButtons() {
  const has = !!script;
  $("goBtn").disabled = !(has && ready) || running;
  $("stopBtn").disabled = !running;
  const says = has ? script.lines.filter((l) => l.kind === "say").length : 0;
  const done = has ? script.lines.filter((l, i) => l.kind === "say" && takes.has(i)).length : 0;
  $("buildBtn").disabled = !(has && done === says && says > 0) || running;
  $("mp3Btn").disabled = $("wavBtn").disabled = !built;
  if (has) { $("recBar").style.width = (says ? Math.round(100 * done / says) : 0) + "%"; if (!running) $("recMsg").textContent = `${done} of ${says} lines recorded`; }
}
function scaled(y, g) { if (g === 1) return y; const z = new Float32Array(y.length); for (let i = 0; i < y.length; i++) z[i] = y[i] * g; return z; }

async function recordOne(i) {
  const line = script.lines[i];
  document.querySelectorAll(".ln.cur").forEach((n) => n.classList.remove("cur"));
  const row = $("ln" + i); if (row) { row.classList.add("cur"); row.scrollIntoView({ block: "nearest" }); }
  setStatus(i, "recording…", "work");
  try { takes.set(i, await recordLine(line, cast)); setStatus(i, "✓", "done"); }
  catch (err) { setStatus(i, "failed", "err"); console.error(err); throw err; }
  finally { refreshButtons(); }
}

$("goBtn").onclick = async () => {
  running = true; stopAsked = false; refreshButtons();
  const t0 = performance.now(); let n = 0;
  try {
    for (let i = 0; i < script.lines.length && !stopAsked; i++) {
      const l = script.lines[i];
      if (l.kind !== "say" || takes.has(i)) continue;
      await recordOne(i); n++;
      const says = script.lines.filter((x) => x.kind === "say").length, done = script.lines.filter((x, k) => x.kind === "say" && takes.has(k)).length;
      const per = (performance.now() - t0) / n / 1000, left = Math.round(per * (says - done) / 60);
      $("recMsg").textContent = `${done} of ${says} lines · about ${left} min left`;
    }
  } catch (err) { $("recMsg").textContent = "Stopped: " + err.message; }
  running = false; refreshButtons();
  if (!stopAsked && !$("buildBtn").disabled) build();
};
$("stopBtn").onclick = () => { stopAsked = true; $("recMsg").textContent = "Stopping after this line…"; };
$("buildBtn").onclick = build;

function build() {
  const parts = [];
  script.lines.forEach((l, i) => {
    if (l.kind === "sfx") { parts.push(silence(l.gap), sfx(l.desc)); return; }
    if (l.kind !== "say") return;
    const g = (cast[l.who] || [0, 0, 1])[2] * (/quiet|soft/.test(l.dirs) ? 0.8 : 1);
    parts.push(silence(l.gap), scaled(takes.get(i), g));
  });
  parts.push(silence(script.tail));
  let y = concat(parts), mx = 0;
  for (let i = 0; i < y.length; i++) mx = Math.max(mx, Math.abs(y[i]));
  if (mx > 0) { const k = 0.89 / mx; for (let i = 0; i < y.length; i++) y[i] *= k; }
  built = y;
  const url = URL.createObjectURL(wavBlob(y));
  $("player").src = url;
  $("outMsg").textContent = `${(y.length / SR / 60).toFixed(1)} minutes`;
  refreshButtons();
}

let playing = null;
function play(y) {
  if (playing) { try { playing.stop(); } catch {} }
  const ctx = play.ctx || (play.ctx = new AudioContext({ sampleRate: SR }));
  const b = ctx.createBuffer(1, y.length, SR); b.copyToChannel(y, 0);
  const s = ctx.createBufferSource(); s.buffer = b; s.connect(ctx.destination); s.start(); playing = s;
}

// ------------------------------------------------------------------ files
function wavBlob(y) {
  const buf = new ArrayBuffer(44 + y.length * 2), v = new DataView(buf);
  const w = (o, s) => { for (let i = 0; i < s.length; i++) v.setUint8(o + i, s.charCodeAt(i)); };
  w(0, "RIFF"); v.setUint32(4, 36 + y.length * 2, true); w(8, "WAVE"); w(12, "fmt ");
  v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true); v.setUint32(24, SR, true);
  v.setUint32(28, SR * 2, true); v.setUint16(32, 2, true); v.setUint16(34, 16, true); w(36, "data"); v.setUint32(40, y.length * 2, true);
  for (let i = 0; i < y.length; i++) v.setInt16(44 + i * 2, Math.max(-1, Math.min(1, y[i])) * 32767, true);
  return new Blob([buf], { type: "audio/wav" });
}
function mp3Blob(y) {
  const enc = new lamejs.Mp3Encoder(1, SR, 128), pcm = new Int16Array(y.length), out = [];
  for (let i = 0; i < y.length; i++) pcm[i] = Math.max(-1, Math.min(1, y[i])) * 32767;
  for (let i = 0; i < pcm.length; i += 1152) { const d = enc.encodeBuffer(pcm.subarray(i, i + 1152)); if (d.length) out.push(new Uint8Array(d)); }
  const end = enc.flush(); if (end.length) out.push(new Uint8Array(end));
  return new Blob(out, { type: "audio/mpeg" });
}
function download(blob, name) {
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = name;
  document.body.appendChild(a); a.click(); a.remove();
}
$("wavBtn").onclick = () => download(wavBlob(built), $("outName").value.trim() + ".wav");
$("mp3Btn").onclick = () => {
  if (typeof lamejs === "undefined") { $("outMsg").textContent = "MP3 encoder didn't load (no internet?); saving WAV instead."; return $("wavBtn").onclick(); }
  $("outMsg").textContent = "Encoding MP3…";
  setTimeout(() => { download(mp3Blob(built), $("outName").value.trim() + ".mp3"); $("outMsg").textContent = `${(built.length / SR / 60).toFixed(1)} minutes · MP3 saved`; }, 30);
};

function loadScript(text) {
  script = parseScript(text);
  takes.clear(); built = null;
  const speakers = [...new Set(script.lines.filter((l) => l.kind === "say").map((l) => l.who))];
  cast = castFor(speakers);
  const says = script.lines.filter((l) => l.kind === "say").length;
  $("scriptMsg").textContent = says ? `${says} spoken lines · ${speakers.length} speakers` : "No spoken lines found";
  renderCast(); renderLines(); refreshButtons();
}
$("file").onchange = async (e) => {
  const f = e.target.files[0]; if (!f) return;
  const text = await f.text(); $("scriptText").value = text; loadScript(text);
  const m = f.name.match(/Ch(\d+)/i); if (m) $("outName").value = "Possible Enough v8 - Chapter " + m[1].padStart(2, "0");
};
$("parseBtn").onclick = () => loadScript($("scriptText").value);
$("resetCast").onclick = () => {
  if (!script) return;
  store.set("cast", {});
  const before = { ...cast };
  cast = castFor(Object.keys(cast));
  for (const s of Object.keys(cast)) if (before[s][0] !== cast[s][0] || before[s][1] !== cast[s][1]) script.lines.forEach((l, i) => { if (l.who === s) takes.delete(i); });
  renderCast(); renderLines(); refreshButtons();
};
// for tests
window.__pe = { parseScript, chunks, speakable, wordCount };
</script>
</body>
</html>
````

### `scripts/narrate.py`

<!-- bundle-file: scripts/narrate.py sha256=20ba45e5172609022ab3ffbb8a438ba3482ae02914c2584d3fa3e5835c82b1fc -->
````python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rule-based audiobook narrator: Kokoro v1.0 voices on sherpa-onnx, with exact, rule-driven pauses.

Pause rules. Where marks or breaks meet (a comma before a closing quote, a full stop at the end of a paragraph,
two unreadable characters in a row), only the longest of their pauses is used; pauses never add up.
  *                         not spoken; 1.0 s each
  .  ?  !                   0.5 s (end of sentence)
  ,  ;  —  –  ( )  [ ]      0.75 s (mid-sentence punctuation); hyphens inside words are not pauses
  :                         0.5 s before what follows
  “ ” " ‘ (as quote)        0.5 s each, opening and closing
  …  or ...                 0.25 s
  new paragraph (new line)  0.7 s before it
  hanging line              0.25 s before and 0.25 s after, instead of the paragraph pause.
                            A hanging line is a line on its own with no lower-case letters (e.g. ME + MUM OUTSIDE),
                            or a short line of up to 3 words that doesn't end a sentence.
  maths operators           + − × ÷ = ≠ ≈ < > ≤ ≥ ± ^ are spoken ("plus", "equals" …) with 0.25 s before and after.
                            A hyphen counts as minus only with spaces and numbers on both sides (5 - 3) or straight
                            before a number (-5); * keeps its own rule, and / is not treated as division.
                            Decimal points and thousands commas inside numbers (3.5, 1,000) are not pauses.
  unreadable characters     (e.g. ▒) not spoken; 0.25 s each. A word containing one is spelled letter by letter:
                            letters between unreadable marks are said together in one breath, 0.15 s separates a
                            letter group from the next, and 0.3 s separates spelled words.

Kokoro garbles a word said entirely on its own (a lone "Us.", "You.", "plus" or a single letter). So a maths
expression is said in one breath and cut at its operators, and a one-word line is said in one breath with a
neighbouring line and cut out; the exact rule pauses then go back in. A speech recogniser checks each take.

Usage: python3 narrate.py input.txt output.mp3 --voice bm_lewis
"""
import argparse, json, os, re, subprocess, tempfile, unicodedata
import numpy as np
import sherpa_onnx
import soundfile as sf

RULES = dict(star=1.0, full=0.5, mid=0.75, colon=0.5, quote=0.5, ellipsis=0.25, unread=0.25,
             para=0.7, hang=0.25, math=0.25, letter_gap=0.15, spelled_word_gap=0.30, tail=1.0)

KOKORO_V1_SPEAKERS = ("af_alloy af_aoede af_bella af_heart af_jessica af_kore af_nicole af_nova af_river af_sarah "
                      "af_sky am_adam am_echo am_eric am_fenrir am_liam am_michael am_onyx am_puck am_santa "
                      "bf_alice bf_emma bf_isabella bf_lily bm_daniel bm_fable bm_george bm_lewis").split()

MID = set(",;—–()[]{}")
END = set(".?!")
DQUOTE = set("“”\"«»„‟")
SYMBOL_WORDS = {"&": "and", "%": "percent", "@": "at"}
MATH_OPS = {"+": "plus", "−": "minus", "×": "times", "÷": "divided by", "=": "equals", "≠": "does not equal",
            "≈": "is approximately", "<": "is less than", ">": "is greater than", "≤": "is less than or equal to",
            "≥": "is greater than or equal to", "±": "plus or minus", "^": "to the power of"}
LETTERS = dict(A="ay", B="bee", C="see", D="dee", E="ee", F="ef", G="gee", H="aitch", I="eye", J="jay", K="kay",
               L="el", M="em", N="en", O="oh", P="pee", Q="cue", R="ar", S="ess", T="tee", U="you", V="vee",
               W="double you", X="ex", Y="why", Z="zed")
DIGITS = "zero one two three four five six seven eight nine".split()
# words a recogniser writes for letter names ("why" for Y)
LETTER_SOUNDS = {"why": "y", "oh": "o", "owe": "o", "are": "r", "you": "u", "see": "c", "sea": "c", "bee": "b",
                 "be": "b", "tea": "t", "tee": "t", "pea": "p", "pee": "p", "eye": "i", "queue": "q", "cue": "q",
                 "ex": "x", "en": "n", "em": "m", "el": "l", "ell": "l", "es": "s", "ess": "s", "jay": "j",
                 "kay": "k", "dee": "d", "gee": "g", "vee": "v", "zed": "z", "aitch": "h", "ay": "a"}


NUMBER = re.compile(r"\d+(?:,\d{3})*(?:\.\d+)?")


def is_unreadable(c):
    if c in "'’-/" or c in SYMBOL_WORDS or c in MATH_OPS:
        return False
    return unicodedata.category(c)[0] not in "LN"


def is_hanging(line):
    letters = [c for c in line if c.isalpha()]
    if letters and not any(c.islower() for c in letters):
        return True
    return len(line.split()) <= 3 and line[-1] not in ".?!:”\"…"


def _neighbour(line, i, step):
    j = i + step
    while 0 <= j < len(line) and line[j] == " ":
        j += step
    return line[j] if 0 <= j < len(line) else ""


def is_minus(line, i):
    """A hyphen is a minus sign with spaces and numbers on both sides (5 - 3), or straight before a number
    when it starts a term (-5, = -5). Anything else stays a hyphen or a dash."""
    before, after = _neighbour(line, i, -1), _neighbour(line, i, 1)
    spaced = (i == 0 or line[i - 1] == " ") and (i + 1 == len(line) or line[i + 1] == " ")
    if spaced and before.isdigit() and after.isdigit():
        return True
    starts_term = i == 0 or line[i - 1] == " " or line[i - 1] in MATH_OPS or line[i - 1] in "(["
    return starts_term and i + 1 < len(line) and line[i + 1].isdigit() and not before.isdigit()


def tokens(line):
    stop = MID | END | DQUOTE | set(MATH_OPS) | {":", "…", "*", "‘"}
    i, out = 0, []
    while i < len(line):
        c = line[i]
        if c.isspace():
            i += 1
        elif c in MATH_OPS:
            out.append(("op", c)); i += 1
        elif c == "-" and is_minus(line, i):
            out.append(("op", "−")); i += 1
        elif c.isdigit():  # a number: keep its decimal point and thousands commas
            m = re.match(r"\d+(?:,\d{3})*(?:\.\d+)?", line[i:])
            j = i + m.end()
            while j < len(line) and not line[j].isspace() and line[j] not in stop and not line.startswith("...", j):
                j += 1  # attached letters or symbols (3rd, 10-20, 5%)
            out.append(("word", line[i:j])); i = j
        elif line.startswith("...", i):
            out.append(("ellipsis", "…")); i += 3
        elif c in stop:
            kind = {"…": "ellipsis", "*": "star", ":": "colon", "‘": "quote"}.get(c)
            kind = kind or ("quote" if c in DQUOTE else "end" if c in END else "mid")
            out.append((kind, c)); i += 1
        elif c == "-" and (i == 0 or line[i - 1].isspace()) and (i + 1 == len(line) or line[i + 1].isspace()):
            out.append(("mid", c)); i += 1  # a spaced hyphen works like a dash
        else:
            j = i
            while j < len(line) and not line[j].isspace() and line[j] not in stop and not line.startswith("...", j):
                j += 1
            out.append(("word", line[i:j])); i = j
    return out


def speakable(word):
    if word in SYMBOL_WORDS:
        return SYMBOL_WORDS[word]
    w = word.replace("’", "'")  # numbers such as 3.5 and 1,000 are read correctly by the voice as they are
    w = re.sub(r"(?<=[A-Za-z])/(?=[A-Za-z])", " ", w)  # and/or -> and or
    if len(w) > 1 and w.isupper():
        w = w.lower()  # ALL-CAPS words are read as words, not as letters
    return w


def spell(word):
    """Events for a word that contains unreadable characters. Letters between unreadable marks are spelled
    together in one breath (Kokoro garbles letters said entirely on their own); each unreadable mark adds 0.25 s."""
    ev, run, pending, why = [], [], 0.0, []

    def say_run():
        nonlocal pending, why
        if not run:
            return
        if ev and ev[-1][0] == "speak":
            pending = max(pending, RULES["letter_gap"]); why.append("letter gap")
        if pending:
            ev.append(("pause", round(pending, 3), " | ".join(why))); pending, why = 0.0, []
        names = [LETTERS[c.upper()] if c.upper() in "AI" else (DIGITS[int(c)] if c.isdigit() else c.lower())
                 for c in run]
        ev.append(("speak", ", ".join(names) + ".", "letters " + "".join(run).upper()))
        run.clear()

    for ch in word:
        if ch in "'’-":
            continue
        if ch.isdigit() or ch.upper() in LETTERS:
            run.append(ch)
        else:  # unreadable: silent, 0.25 s
            say_run()
            pending = max(pending, RULES["unread"]); why.append(f"unreadable {ch}")
    say_run()
    if pending:
        ev.append(("pause", round(pending, 3), " | ".join(why)))
    return ev


def line_events(line, hanging):
    ev, buf = [], []
    prev_spelled = False

    def flush(mark=""):
        if buf:
            ev.append(("speak", " ".join(buf) + mark, "text")); buf.clear()

    for kind, v in tokens(line):
        if kind == "word":
            core = NUMBER.sub("", v)  # decimal points and thousands commas in numbers are readable
            if any(is_unreadable(c) for c in core) and any(c.isalnum() for c in v):
                flush()
                if prev_spelled:
                    ev.append(("pause", RULES["spelled_word_gap"], "space between spelled words"))
                ev += spell(v); prev_spelled = True
            elif all(is_unreadable(c) for c in v):
                flush(); ev.append(("pause", RULES["unread"], f"unreadable {v}"))
            else:
                buf.append(speakable(v)); prev_spelled = False
            continue
        prev_spelled = False
        if kind == "end":
            flush(v); ev.append(("pause", RULES["full"], f"'{v}'"))
        elif kind == "mid":
            flush(v if v in ",;" else ""); ev.append(("pause", RULES["mid"], f"'{v}'"))
        elif kind == "colon":
            flush(":"); ev.append(("pause", RULES["colon"], "':'"))
        elif kind == "quote":
            flush(); ev.append(("pause", RULES["quote"], f"'{v}'"))
        elif kind == "ellipsis":
            flush("..."); ev.append(("pause", RULES["ellipsis"], "'…'"))
        elif kind == "star":
            flush(); ev.append(("pause", RULES["star"], "'*'"))
        elif kind == "op":
            flush()
            ev.append(("pause", RULES["math"], f"before '{v}'"))
            ev.append(("speak", MATH_OPS[v], "op"))
            ev.append(("pause", RULES["math"], f"after '{v}'"))
    flush("." if hanging else "")  # a caption gets a falling tone; no extra pause
    return ev


def text_events(text):
    ev = []
    for raw in text.replace("\r\n", "\n").split("\n"):
        line = raw.strip()
        if not line:
            continue
        hanging = is_hanging(line)
        ev.append(("pause", RULES["hang"] if hanging else RULES["para"],
                   "hanging line (before)" if hanging else "new paragraph"))
        ev += line_events(line, hanging)
        if hanging:
            ev.append(("pause", RULES["hang"], "hanging line (after)"))
    ev.append(("pause", RULES["tail"], "end of recording"))
    merged = []
    for e in ev:  # pauses that meet: the longest one wins
        if e[0] == "pause" and merged and merged[-1][0] == "pause":
            merged[-1] = ("pause", max(merged[-1][1], e[1]), merged[-1][2] + " | " + e[2])
        else:
            merged.append(e)
    return merged


def make_tts(model_dir, voice):
    accent = "gb" if voice.startswith("b") else "us"
    d = model_dir
    cfg = sherpa_onnx.OfflineTtsConfig(
        model=sherpa_onnx.OfflineTtsModelConfig(
            kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(
                model=f"{d}/model.onnx", voices=f"{d}/voices.bin", tokens=f"{d}/tokens.txt",
                data_dir=f"{d}/espeak-ng-data", lexicon=f"{d}/lexicon-{accent}-en.txt,{d}/lexicon-zh.txt",
                lang="en-us" if accent == "us" else "en"),
            num_threads=2, provider="cpu"),
        max_num_sentences=1)
    return sherpa_onnx.OfflineTts(cfg), KOKORO_V1_SPEAKERS.index(voice)


def trim(x, sr):
    """Cut the model's own leading/trailing silence; return audio and the quiet margins kept."""
    a = np.abs(x)
    idx = np.where(a > max(1e-4, 0.005 * a.max()))[0]
    if not len(idx):
        return x[:0], 0.0, 0.0
    s, e = max(0, idx[0] - int(0.015 * sr)), min(len(x), idx[-1] + int(0.045 * sr))
    y = x[s:e].astype(np.float32).copy()
    f = min(int(0.005 * sr), len(y) // 2)
    if f:
        r = np.linspace(0, 1, f, dtype=np.float32)
        y[:f] *= r; y[-f:] *= r[::-1]
    return y, (idx[0] - s) / sr, (e - idx[-1]) / sr


PARAKEET = "/home/claude/tts/models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8"


class Checker:
    """Speech recogniser used to check takes (a garbled short line, a whole maths expression) and to time words."""

    def __init__(self, model_dir=PARAKEET):
        self.rec = sherpa_onnx.OfflineRecognizer.from_transducer(
            encoder=f"{model_dir}/encoder.int8.onnx", decoder=f"{model_dir}/decoder.int8.onnx",
            joiner=f"{model_dir}/joiner.int8.onnx", tokens=f"{model_dir}/tokens.txt", num_threads=2,
            model_type="nemo_transducer")

    def _run(self, audio, rate):
        st = self.rec.create_stream(); st.accept_waveform(rate, audio); self.rec.decode_stream(st)
        return st.result

    def __call__(self, y, sr):
        """What the recogniser hears, at full rate and at 16 kHz (a take must survive both)."""
        from math import gcd
        from scipy.signal import resample_poly
        pad = np.zeros(int(0.3 * sr), np.float32)
        x = np.concatenate([pad, y, pad])
        g = gcd(16000, sr)
        return [words_of(self._run(a, r).text) for a, r in
                ((x, sr), (resample_poly(x, 16000 // g, sr // g).astype(np.float32), 16000))]

    def word_starts(self, y, sr):
        """[(normalised word, start time in seconds)] for everything the recogniser hears in y."""
        pad = 0.3
        r = self._run(np.concatenate([np.zeros(int(pad * sr), np.float32), y, np.zeros(int(pad * sr), np.float32)]), sr)
        raw = []
        for tok, ts in zip(r.tokens, r.timestamps):
            if tok.startswith(" ") or not raw:
                raw.append([tok.strip(), ts - pad])
            else:
                raw[-1][0] += tok
        out = []
        for w, t in raw:
            w = w.strip(".,!?;:\"“”'’")
            for ww in words_of(MATH_OPS.get(w, w)):
                out.append((ww, t))
        return out


def make_checker(model_dir=PARAKEET):
    return Checker(model_dir) if os.path.isdir(model_dir) else None


def cut_points(y, sr, pieces, checker):
    """Sample positions where each piece after the first begins: found from the recogniser's word timings,
    then moved to the quietest moment just before that word."""
    seq = checker.word_starts(y, sr)
    starts, pos = [], 0
    for text, _ in pieces:
        want = words_of(text)
        if not want:
            return None
        j = next((j for j in range(pos, min(pos + 3, len(seq)))
                  if want[0] in (seq[j][0], LETTER_SOUNDS.get(seq[j][0]))), None)
        if j is None:
            return None
        starts.append(seq[j][1]); pos = j + len(want)
    fr = int(0.01 * sr)
    env = np.array([np.sqrt(np.mean(y[i:i + fr] ** 2)) for i in range(0, len(y) - fr, fr)])
    cuts, prev = [], 0
    for t0 in starts[1:]:
        lo, hi = max(prev + 8, int((t0 - 0.30) * 100)), min(len(env) - 1, int((t0 + 0.04) * 100))
        if hi <= lo:
            return None
        k = lo + int(np.argmin(env[lo:hi + 1]))
        cuts.append(k * fr + fr // 2); prev = k
    return cuts


def render_group(pieces, tts, sid, speed, checker, tries=4):
    """A maths expression is said in one breath, with commas around its operators, then cut at the operators so the
    rule pauses can go in. Words said alone (a bare "plus") come out garbled in Kokoro; in one breath they don't."""
    parts = []
    for k, (text, _) in enumerate(pieces):
        last = k == len(pieces) - 1
        parts.append(text if last or text.endswith((",", ";", ":")) else text.rstrip(".!?…") + ",")
    say = " ".join(parts)
    want = words_of(" ".join(t for t, _ in pieces))
    for n in range(1, tries + 1):
        a = tts.generate(say, sid=sid, speed=speed)
        sr = a.sample_rate
        y, _, _ = trim(np.asarray(a.samples, np.float32), sr)
        if max(word_errors(want, h) for h in checker(y, sr)) > 0:
            continue
        cuts = cut_points(y, sr, pieces, checker)
        if cuts is None:
            continue
        clips = [trim(s, sr) for s in np.split(y, cuts)]
        if all(len(c[0]) >= int(0.08 * sr) for c in clips):
            return clips, sr, n
    return None


CONTRACTIONS = {"theyre": "they are", "isnt": "is not", "im": "i am", "dont": "do not", "cant": "can not",
                "cannot": "can not", "wont": "will not", "its": "it is", "youre": "you are", "were": "we are",
                "didnt": "did not", "wasnt": "was not", "hes": "he is", "shes": "she is", "thats": "that is"}
SAME_SOUND = {"layla": "leila", "laila": "leila", "lela": "leila", "uz": "us"}  # spelling choices, not misreadings


ONES = ("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
        "seventeen eighteen nineteen").split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def int_words(n):
    if n < 20:
        return ONES[n]
    if n < 100:
        return TENS[n // 10] + ("" if n % 10 == 0 else " " + ONES[n % 10])
    for size, name in ((10 ** 9, "billion"), (10 ** 6, "million"), (1000, "thousand"), (100, "hundred")):
        if n >= size:
            rest = n % size
            return int_words(n // size) + " " + name + ("" if rest == 0 else " " + int_words(rest))


def number_words(m):
    whole, _, frac = m.group(0).replace(",", "").partition(".")
    out = int_words(int(whole)) if len(whole) < 13 else " ".join(ONES[int(d)] for d in whole)
    return " " + out + ("" if not frac else " point " + " ".join(ONES[int(d)] for d in frac)) + " "


def words_of(t):
    t = re.sub(r"\d+(?:,\d{3})*(?:\.\d+)?", number_words, t)
    t = t.lower().replace("’", "'").replace("-", " ").replace(" and ", " ")
    t = re.sub(r"[^a-z0-9' ]", " ", t).replace("'", "")
    out = []
    for w in t.split():
        out += CONTRACTIONS.get(w, SAME_SOUND.get(w, w)).split()
    return out


def word_errors(ref, hyp):
    D = np.arange(len(hyp) + 1)
    for i in range(1, len(ref) + 1):
        prev, D[0] = D.copy(), i
        for j in range(1, len(hyp) + 1):
            D[j] = min(prev[j] + 1, D[j - 1] + 1, prev[j - 1] + (ref[i - 1] != hyp[j - 1]))
    return int(D[-1])


def is_op_pause(e):
    return e[0] == "pause" and ("before '" in e[2] or "after '" in e[2])


def carrier_for(i, events):
    """A neighbouring chunk to say a one-word chunk with. Letters lean on the bigger of the neighbouring letter
    groups of the same spelled line; words lean on the nearest earlier line of three words or more (else the next)."""
    e = events[i]
    if e[2].startswith("letters"):
        options = [k for k in (i + 2, i - 2) if 0 <= k < len(events) and events[k][0] == "speak"
                   and events[k][2].startswith("letters") and events[(i + k) // 2][0] == "pause"]
        return max(options, key=lambda k: len(events[k][2]), default=None)
    for rng in (range(i - 1, -1, -1), range(i + 1, len(events))):
        for k in rng:
            if events[k][0] == "speak" and events[k][2] == "text" and len(events[k][1].split()) >= 3:
                return k
    return None


def render_with_carrier(i, events, tts, sid, speed, checker, tries=4):
    """Kokoro garbles a word said entirely on its own ("Us.", "You.", a single letter). Say it in one breath with a
    neighbouring chunk, cut it out at the boundary, and keep only the word; the rule pauses go back around it."""
    k = carrier_for(i, events)
    if k is None:
        return None
    word, carrier = events[i][1], events[k][1]
    if k < i:
        pieces = [(carrier.rstrip(".!?…,;:") + ",", False), (word, False)]
    else:
        pieces = [(word.rstrip(".!?…,;:") + ",", False), (carrier, False)]
    say = " ".join(p for p, _ in pieces)
    want = words_of(say)
    letters = events[i][2].startswith("letters")
    for n in range(1, tries + 1):
        a = tts.generate(say, sid=sid, speed=speed)
        sr = a.sample_rate
        y, _, _ = trim(np.asarray(a.samples, np.float32), sr)
        heard = checker(y, sr)
        if letters:
            ok = all("".join(LETTER_SOUNDS.get(w, w) for w in h) == "".join(want) for h in heard)
        else:
            ok = max(word_errors(want, h) for h in heard) <= (1 if len(want) > 4 else 0)
        if not ok:
            continue
        cuts = cut_points(y, sr, pieces, checker)
        if cuts is None:
            continue
        clips = [trim(s, sr) for s in np.split(y, cuts)]
        piece = clips[1] if k < i else clips[0]
        if len(piece[0]) >= int(0.12 * sr):
            return piece, sr, n, carrier
    return None


def render(events, tts, sid, speed=1.0, checker=None):
    """Synthesise every chunk. With a checker:
    - a maths expression (chunks joined only by operator pauses) is said in one breath and cut at the operators;
    - a one-word chunk is said in one breath with a neighbouring chunk and cut out;
    - any other chunk the recogniser doesn't hear word for word gets retakes, and the clearest take is kept."""
    clips, retakes, sr = [None] * len(events), [], tts.sample_rate
    i = 0
    while checker and i < len(events):  # 1) maths expressions
        if events[i][0] == "speak":
            group, j = [i], i
            while j + 2 < len(events) and is_op_pause(events[j + 1]) and events[j + 2][0] == "speak":
                group.append(j + 2); j += 2
            if len(group) > 1 and any(events[g][2] == "op" for g in group):
                got = render_group([(events[g][1], events[g][2] == "op") for g in group], tts, sid, speed, checker)
                if got:
                    pieces, sr, n = got
                    for g, (y, lead, tail) in zip(group, pieces):
                        clips[g] = (events[g], y, lead, tail)
                    retakes.append((" ".join(events[g][1] for g in group), "one breath, cut at the operators",
                                    speed, 0, n))
                    i = j + 1
                    continue
        i += 1
    for i, e in enumerate(events):  # 2) one-word chunks
        if checker and e[0] == "speak" and clips[i] is None and len(e[1].split()) == 1:
            got = render_with_carrier(i, events, tts, sid, speed, checker)
            if got:
                (y, lead, tail), sr, n, carrier = got
                clips[i] = (e, y, lead, tail)
                retakes.append((e[1], "said with a neighbour", speed, 0, n, carrier))
    for i, e in enumerate(events):  # 3) everything else, on its own
        if clips[i] is None:
            if e[0] != "speak":
                clips[i] = (e, None, 0.0, 0.0)
            else:
                clips[i], sr = best_take(e, tts, sid, speed, checker, retakes)
    return assemble(clips, sr, retakes, speed)


def best_take(e, tts, sid, speed, checker, retakes):
    """One chunk on its own, with retakes when the recogniser doesn't hear it word for word."""
    if True:
        takes = [(e[1], speed)]
        if checker and e[2].startswith("letters"):
            takes += [(e[1], speed)] * 3
        elif checker and e[2] in ("text", "op"):
            base = e[1].rstrip(".!?…,;:")
            if len(e[1].split()) <= 2:  # very short lines: also try a comma ending (intonation only)
                takes += [(base + ",", speed), (base + ".", speed), (e[1], speed), (base + ",", speed),
                          (base + ".", speed)]
            else:  # each take differs a little; change the pace only as a last resort
                takes += [(e[1], speed), (e[1], speed), (e[1], speed * 0.95), (e[1], speed * 1.05)]
        best = None
        for k, (t, sp) in enumerate(takes):
            a = tts.generate(t, sid=sid, speed=sp)
            y, lead, tail = trim(np.asarray(a.samples, np.float32), a.sample_rate)
            sr = a.sample_rate
            if len(takes) == 1:
                best = (0, y, lead, tail, t, sp); break
            heard = checker(y, sr)
            if e[2].startswith("letters"):  # e.g. "t, h." may come back as "th": compare the letters only
                want = e[2].split(" ", 1)[1].lower()
                err = max(int("".join(LETTER_SOUNDS.get(w, w) for w in h) != want) for h in heard)
            else:
                err = max(word_errors(words_of(e[1]), h) for h in heard)
            if best is None or err < best[0]:
                best = (err, y, lead, tail, t, sp, " | ".join(" ".join(h) for h in heard))
            if err == 0:
                break
        if k > 0:
            retakes.append((e[1], best[4], best[5], best[0], k + 1))
        return (e, best[1], best[2], best[3]), sr


def assemble(clips, sr, retakes, speed):
    """Lay the clips end to end with the exact pauses between them."""
    out, timeline, t = [], [], 0.0
    for k, (e, y, lead, tail) in enumerate(clips):
        if e[0] == "pause":
            prev_tail = clips[k - 1][3] if k > 0 else 0.0
            next_lead = clips[k + 1][2] if k + 1 < len(clips) else 0.0
            n = max(0.0, e[1] - prev_tail - next_lead)  # quiet margins already count towards the pause
            out.append(np.zeros(int(round(n * sr)), np.float32))
            timeline.append(dict(type="pause", seconds=e[1], why=e[2], start=round(t - prev_tail, 3)))
            t += n
        else:
            out.append(y)
            timeline.append(dict(type="speech", text=e[1], start=round(t + lead, 3),
                                 end=round(t + len(y) / sr - tail, 3)))
            t += len(y) / sr
    for orig, used, sp, err, n, *extra in retakes:
        if used == "one breath, cut at the operators":
            print(f"  maths {orig[:48]!r}: said in one breath and cut at the operators (take {n})")
            continue
        if used == "said with a neighbour":
            print(f"  one-word {orig!r}: said in one breath with {extra[0][:40]!r} and cut out (take {n})")
            continue
        note = "" if used == orig and abs(sp - speed) < 1e-6 else f" as {used!r} at speed {sp:.2f}"
        print(f"  {n} takes of {orig[:48]!r}: kept the clearest{note}; {err} word(s) still unclear")
    return np.concatenate(out), sr, timeline


def export_mp3(x, sr, mp3, wav_out=None, lufs=-20.0, tp=-3.0):
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "in.wav")
        sf.write(src, x, sr, subtype="FLOAT")
        ln = f"loudnorm=I={lufs}:TP={tp}:LRA=11"
        r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", src, "-af", ln + ":print_format=json",
                            "-f", "null", "-"], capture_output=True, text=True)
        m = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S).group(0))
        ln2 = (f"{ln}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
               f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
        af = f"{ln2},aresample=44100"
        subprocess.run(["ffmpeg", "-hide_banner", "-y", "-i", src, "-af", af, "-ac", "1", "-c:a", "libmp3lame",
                        "-b:a", "192k", "-id3v2_version", "3", mp3], check=True, capture_output=True)
        if wav_out:
            subprocess.run(["ffmpeg", "-hide_banner", "-y", "-i", src, "-af", af, "-ac", "1", "-c:a",
                            "pcm_s16le", wav_out], check=True, capture_output=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("text"); ap.add_argument("mp3")
    ap.add_argument("--voice", default="bm_lewis", choices=KOKORO_V1_SPEAKERS)
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--model-dir", default="/home/claude/tts/models/kokoro-multi-lang-v1_0")
    ap.add_argument("--wav", default=None, help="also save a 44.1 kHz WAV")
    ap.add_argument("--plan", default=None, help="save the speech/pause timeline as JSON")
    a = ap.parse_args()
    events = text_events(open(a.text, encoding="utf-8").read())
    tts, sid = make_tts(a.model_dir, a.voice)
    audio, sr, timeline = render(events, tts, sid, a.speed, checker=make_checker())
    export_mp3(audio, sr, a.mp3, a.wav)
    if a.plan:
        json.dump(timeline, open(a.plan, "w"), ensure_ascii=False, indent=1)
    print(f"{a.mp3}: {len(audio) / sr:.1f} s, {sum(e[0] == 'speak' for e in events)} spoken chunks, "
          f"{sum(e[0] == 'pause' for e in events)} pauses")
````

### `scripts/narrate_cast.py`

<!-- bundle-file: scripts/narrate_cast.py sha256=92025e9474f51e64030abfb1c9b3adc57292b2c3a5d9cf0c0e6676b3f6a0e11c -->
````python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Multi-voice audiobook narrator for the Possible Enough narration scripts.

Reads a script such as PE_v8_Ch01_narration_script.txt, where every line is

    SPEAKER: text            spoken in that speaker's voice
    [PAUSE 1.5s]             silence (also [SCENE BREAK — PAUSE 2.5s], [END … PAUSE 3s])
    [SFX: …]                 a small sound effect: "tone" (soft chime), "interference" (digital glitch)

Text in [brackets] inside a spoken line is a direction, not spoken. Directions that mention
"slow" read the line a little slower; "quiet" or "soft" read it a little quieter.

Every line goes through narrate.py (Kokoro v1.0 on sherpa-onnx, with its exact pause rules and the speech
recogniser that checks each take). Pauses between lines follow the same rules:
    after a comma (a line that stops mid-sentence, e.g. "Those are very big birds,")   0.75 s
    before a dialogue tag ("she said.")                                                0.5 s
    otherwise, a new paragraph                                                          0.7 s
An explicit [PAUSE] replaces the gap if it is longer (pauses never add up).

A one-word line ("Us.", "No.", "You.") is said in one breath after a short carrier phrase in the same voice,
then cut out, because Kokoro garbles a word said entirely on its own.

Every finished line is cached in work/cache, so a run that stops carries on where it left off, and changing one
voice or one line only re-records the lines that change.

Usage:
    python3 narrate_cast.py PE_v8_Ch01_narration_script.txt "Possible Enough 01.mp3"
    python3 narrate_cast.py script.txt out.mp3 --cast MARA=af_bella,ORISON=bm_george
    python3 narrate_cast.py script.txt sample.mp3 --sample 40      (only the first 40 lines)
"""
import argparse, hashlib, os, re, sys, time
from pathlib import Path
import numpy as np

import narrate as N

HERE = Path(__file__).resolve().parent

# ------------------------------------------------------------------ the cast (change freely)
# speaker: (Kokoro voice, speed, loudness)
CAST = {
    "NARRATOR": ("af_heart",    0.95, 1.00),
    "LEILA":    ("bf_emma",     1.00, 1.00),
    "MARA":     ("af_sky",      1.05, 1.00),
    "AMRITA":   ("af_nicole",   1.00, 1.00),
    "NIA":      ("bf_isabella", 0.98, 1.00),
    "ORISON":   ("am_michael",  0.90, 1.00),
    "SCREEN":   ("af_heart",    0.90, 0.80),
    "ENGINEER": ("am_adam",     1.00, 1.00),
}
DEFAULT_VOICE = ("af_heart", 1.0, 1.0)   # any speaker not listed above
CARRIER = "And then I heard it said"     # said before a one-word line, then cut away
GAP_COMMA, GAP_TAG, GAP_PARA = 0.75, 0.5, 0.7
CACHE_VERSION = "1"
# -------------------------------------------------------------------------------------------

LINE = re.compile(r"^([A-Z][A-Z ]*[A-Z]|[A-Z]):\s*(.*)$")
PAUSE = re.compile(r"PAUSE\s+([\d.]+)\s*s", re.I)


def parse(path):
    """The script as a list of ('say', speaker, text, direction) / ('pause', seconds) / ('sfx', description)."""
    text = Path(path).read_text(encoding="utf-8")
    if "=====" in text:  # the header above the ===== line is notes for people
        text = text[text.index("=====") :].split("\n", 1)[1]
    items = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("["):
            inner = line.strip("[]")
            if inner.upper().startswith("SFX"):
                items.append(("sfx", inner.split(":", 1)[-1].strip()))
                continue
            m = PAUSE.search(inner)
            if m:
                items.append(("pause", float(m.group(1))))
            continue
        m = LINE.match(line)
        if not m:
            print(f"  (skipped a line I can't read: {line[:60]!r})")
            continue
        speaker, body = m.group(1), m.group(2)
        direction = " ".join(re.findall(r"\[([^\]]*)\]", body)).lower()
        body = re.sub(r"\s*\[[^\]]*\]\s*", " ", body).strip()
        if body:
            items.append(("say", speaker, body, direction))
    return items


def plan(items):
    """Work out the silence before every spoken line."""
    out, pending, prev = [], 0.0, None
    for it in items:
        if it[0] == "pause":
            pending = max(pending, it[1])
            continue
        if it[0] == "sfx":
            out.append(("sfx", it[1], pending)); pending, prev = 0.0, None
            continue
        _, speaker, body, direction = it
        gap = GAP_PARA
        if prev is not None:
            if prev[2].rstrip().endswith((",", ";")):
                gap = GAP_COMMA
            elif speaker == "NARRATOR" and body[:1].islower():
                gap = GAP_TAG
        elif out and out[-1][0] == "sfx":
            gap = 0.0
        out.append(("say", speaker, body, direction, max(gap if out else 0.0, pending)))
        pending, prev = 0.0, it
    return out, pending


class Voices:
    """One Kokoro engine per accent (American / British), shared by every voice of that accent."""

    def __init__(self, model_dir):
        self.model_dir, self.engines = model_dir, {}

    def get(self, voice):
        accent = "gb" if voice.startswith("b") else "us"
        if accent not in self.engines:
            self.engines[accent] = N.make_tts(self.model_dir, voice)[0]
        return self.engines[accent], N.KOKORO_V1_SPEAKERS.index(voice)


def one_word(body):
    return len(N.words_of(body)) == 1


def record(body, voice, speed, voices, checker):
    """Synthesise one line with narrate.py's rules; returns float32 audio at the model's rate."""
    tts, sid = voices.get(voice)
    ev = N.text_events(body)
    while ev and ev[0][0] == "pause":   # the gaps between lines are set by plan(), not here
        ev.pop(0)
    while ev and ev[-1][0] == "pause":
        ev.pop()
    if checker and one_word(body):
        ev = [("speak", CARRIER + ".", "text"), ("pause", 0.5, "carrier")] + ev
        audio, sr, timeline = N.render(ev, tts, sid, speed, checker)
        speech = [t for t in timeline if t["type"] == "speech"]
        if len(speech) >= 2:
            cut = max(0, int((speech[1]["start"] - 0.03) * sr))
            return audio[cut:], sr
        return audio, sr
    audio, sr, _ = N.render(ev, tts, sid, speed, checker)
    return audio, sr


def sfx(description, sr):
    """Small synthesised effects, kept quiet under the voices."""
    d = description.lower()
    rng = np.random.default_rng(13)
    if "tone" in d or "chime" in d:
        t = np.arange(int(0.9 * sr)) / sr
        y = (np.sin(2 * np.pi * 880 * t) + 0.35 * np.sin(2 * np.pi * 1320 * t)) * np.exp(-4.5 * t)
        y[: int(0.01 * sr)] *= np.linspace(0, 1, int(0.01 * sr))
        return (0.12 * y).astype(np.float32)
    if "interference" in d or "glitch" in d or "static" in d:
        m = re.search(r"([\d.]+)\s*s", d)
        length = float(m.group(1)) if m else 1.5
        n = int(length * sr)
        noise = rng.standard_normal(n)
        k = np.ones(6) / 6                      # soften the hiss a little
        noise = np.convolve(noise, k, mode="same")
        gate = np.zeros(n)
        pos = 0
        while pos < n:                           # stuttering bursts, like a signal breaking up
            burst = int(rng.uniform(0.03, 0.14) * sr)
            if rng.random() < 0.7:
                gate[pos:pos + burst] = rng.uniform(0.4, 1.0)
            pos += burst + int(rng.uniform(0.0, 0.06) * sr)
        t = np.arange(n) / sr
        buzz = 0.3 * np.sign(np.sin(2 * np.pi * 120 * t))
        y = (noise * 0.6 + buzz) * gate
        fade = int(0.02 * sr)
        y[:fade] *= np.linspace(0, 1, fade); y[-fade:] *= np.linspace(1, 0, fade)
        return (0.08 * y / (np.abs(y).max() + 1e-9) * 3).astype(np.float32)
    return np.zeros(int(1.0 * sr), np.float32)  # unknown effect: a second of silence, to be added by hand


def main():
    ap = argparse.ArgumentParser(description="Narrate a Possible Enough script with a cast of Kokoro voices.")
    ap.add_argument("script")
    ap.add_argument("mp3")
    ap.add_argument("--cast", default="", help="changes to the cast, e.g. MARA=af_bella,ORISON=bm_george:0.9")
    ap.add_argument("--sample", type=int, default=0, help="only the first N lines")
    ap.add_argument("--model-dir", default=str(HERE / "models" / "kokoro-multi-lang-v1_0"))
    ap.add_argument("--checker-dir", default=str(HERE / "models" / "sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8"))
    ap.add_argument("--no-check", action="store_true", help="skip the recogniser (faster, less careful)")
    ap.add_argument("--wav", default=None, help="also save a WAV")
    a = ap.parse_args()

    cast = dict(CAST)
    for item in filter(None, a.cast.split(",")):
        who, _, spec = item.partition("=")
        voice, _, speed = spec.partition(":")
        old = cast.get(who.strip().upper(), DEFAULT_VOICE)
        cast[who.strip().upper()] = (voice.strip(), float(speed) if speed else old[1], old[2])
    for who, (voice, _, _) in cast.items():
        if voice not in N.KOKORO_V1_SPEAKERS:
            raise SystemExit(f"{who}: there is no Kokoro voice called {voice!r}. Choose from: "
                             + ", ".join(N.KOKORO_V1_SPEAKERS))

    items = parse(a.script)
    lines, tail = plan(items)
    if a.sample:
        lines = lines[: a.sample]
    speakers = sorted({l[1] for l in lines if l[0] == "say"})
    print(f"{len(lines)} lines; voices: " + ", ".join(f"{s}={cast.get(s, DEFAULT_VOICE)[0]}" for s in speakers))
    unknown = [s for s in speakers if s not in cast]
    if unknown:
        print("  not in the cast, so read by the default voice: " + ", ".join(unknown))

    voices = Voices(a.model_dir)
    checker = None if a.no_check else N.make_checker(a.checker_dir)
    if checker is None and not a.no_check:
        print("  (no speech recogniser found, so takes are not checked)")
    cache = HERE / "work" / "cache"
    cache.mkdir(parents=True, exist_ok=True)

    sr = 24000
    parts, started = [], time.time()
    for n, l in enumerate(lines, 1):
        if l[0] == "sfx":
            parts.append(np.zeros(int(round(l[2] * sr)), np.float32))
            parts.append(sfx(l[1], sr))
            continue
        _, speaker, body, direction, gap = l
        voice, speed, gain = cast.get(speaker, DEFAULT_VOICE)
        if "slow" in direction:
            speed *= 0.9
        if "quiet" in direction or "soft" in direction:
            gain *= 0.8
        key = hashlib.sha256(f"{CACHE_VERSION}|{voice}|{speed:.3f}|{bool(checker)}|{body}".encode()).hexdigest()[:20]
        path = cache / f"{key}.npy"
        if path.exists():
            y = np.load(path)
        else:
            print(f"[{n}/{len(lines)}] {speaker}: {body[:60]}", flush=True)
            y, sr = record(body, voice, speed, voices, checker)
            np.save(path, y.astype(np.float32))
        parts.append(np.zeros(int(round(gap * sr)), np.float32))
        parts.append((y * gain).astype(np.float32))
    parts.append(np.zeros(int(round(max(tail, 1.0) * sr)), np.float32))
    audio = np.concatenate(parts)
    N.export_mp3(audio, sr, a.mp3, a.wav)
    mins = (time.time() - started) / 60
    print(f"{a.mp3}: {len(audio) / sr / 60:.1f} minutes of audio, made in {mins:.1f} min")


if __name__ == "__main__":
    sys.exit(main())
````

### `scripts/setup_env.sh`

<!-- bundle-file: scripts/setup_env.sh sha256=06d37552fd694fe057e1cfa843c61a9e2295c1418990281159893f2686429445 -->
````bash
#!/usr/bin/env bash
# Install what narrate.py / narrate_cast.py need and download the two models into ./models.
set -e
cd "$(dirname "$0")"
pip install --break-system-packages -q sherpa-onnx soundfile scipy numpy 2>/dev/null || pip3 install -q sherpa-onnx soundfile scipy numpy
command -v ffmpeg >/dev/null || echo "ffmpeg is missing: install it (apt-get install ffmpeg, or brew install ffmpeg on a Mac)"
mkdir -p models && cd models
if [ ! -d kokoro-multi-lang-v1_0 ]; then
  curl -sSL -o kokoro.tar.bz2 https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/kokoro-multi-lang-v1_0.tar.bz2
  tar xjf kokoro.tar.bz2 && rm kokoro.tar.bz2
fi
if [ ! -d sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8 ]; then
  curl -sSL -o p.tar.bz2 https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8.tar.bz2
  tar xjf p.tar.bz2 && rm p.tar.bz2
fi
echo "Ready: $(pwd)"
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
