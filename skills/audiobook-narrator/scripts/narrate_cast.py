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
