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
