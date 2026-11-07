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
