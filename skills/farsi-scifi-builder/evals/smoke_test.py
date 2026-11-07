#!/usr/bin/env python3
"""Smoke test for farsi-scifi-builder: runs scripts/farsi_lint.py on the sample files.

Usage: python evals/smoke_test.py
Writes only to a temporary directory; exits non-zero if any check fails.
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
LINT = HERE.parent / "scripts" / "farsi_lint.py"
BAD = HERE / "files" / "sample_translationese.md"
CLEAN = HERE / "files" / "sample_clean.md"

failures = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (f"  ({detail})" if detail and not ok else ""))
    if not ok:
        failures.append(name)


def run(*args):
    return subprocess.run([sys.executable, "-B", str(LINT), *map(str, args)],
                          capture_output=True, text=True, encoding="utf-8")


def codes(report, kind):
    return {f["code"] for f in report["findings"][kind]}


with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)

    r = run("--help")
    check("--help exits 0", r.returncode == 0)

    r = run(BAD, "--json")
    check("lint flawed sample exits 0", r.returncode == 0, r.stderr)
    rep = json.loads(r.stdout)
    want_mech = {"arabic_yeh", "arabic_kaf", "arabic_digits", "straight_quotes", "latin_comma",
                 "zwnj_mi", "zwnj_plural", "ezafe_space"}
    got = codes(rep, "mechanical")
    check("mechanical issues detected", want_mech <= got, f"missing {want_mech - got}")
    want_style = {"tavasot", "gardid", "dar_hal", "mibashad", "betor", "qader", "mani",
                  "be_manzur", "anjam", "ke_quote"}
    got = codes(rep, "style")
    check("style signals detected", want_style <= got, f"missing {want_style - got}")
    check("pronoun density flagged", any(d["code"] == "pronoun_u" and d["high"] for d in rep["density"]))

    out = tmp / "fixed.md"
    before = BAD.read_bytes()
    r = run(BAD, "--fix", "-o", out)
    check("--fix exits 0", r.returncode == 0, r.stderr)
    check("input untouched", BAD.read_bytes() == before)
    fixed = out.read_text(encoding="utf-8")
    check("no Arabic ي/ك/digits left", not any(c in fixed for c in "يكى٠١٢٣٤٥٦٧٨٩"))
    check("half-spaces restored", all(w in fixed for w in ["می\u200cباشد", "نمی\u200cداد", "گزینه\u200cها", "جلسه\u200cی"]))
    check("guillemets used", "«باید تصمیمی گرفته شود»" in fixed)
    rep2 = json.loads(run(out, "--json").stdout)
    check("fixed copy has 0 mechanical issues", not rep2["findings"]["mechanical"],
          str(rep2["findings"]["mechanical"][:2]))

    rep3 = json.loads(run(CLEAN, "--json").stdout)
    n = sum(len(v) for v in rep3["findings"].values())
    check("clean sample has no findings", n == 0, str(rep3["findings"]))

    r = run(BAD, "--fix", "-o", BAD)
    check("refuses to overwrite input", r.returncode != 0 and BAD.read_bytes() == before)

    copy = tmp / "draft.md"
    shutil.copy(BAD, copy)
    run(copy, "--fix")
    check("default output goes next to input", (tmp / "draft.fixed.md").is_file())

    p = tmp / "digits.md"
    p.write_text("ساعت 3.5 بود.\n", encoding="utf-8")
    run(p, "--fix", "--persian-digits", "-o", tmp / "digits.out.md")
    check("--persian-digits converts", (tmp / "digits.out.md").read_text(encoding="utf-8").strip() == "ساعت ۳٫۵ بود.")

    # --- v1.1: nested quotes and pandoc attributes are left alone
    MARK = HERE / "files" / "sample_markup.md"
    rep4 = json.loads(run(MARK, "--json").stdout)
    check("markup sample: no mechanical findings", not rep4["findings"]["mechanical"], str(rep4["findings"]["mechanical"][:2]))
    out2 = tmp / "markup.fixed.md"
    run(MARK, "--fix", "-o", out2)
    check("--fix leaves markup unchanged", out2.read_text(encoding="utf-8") == MARK.read_text(encoding="utf-8"))

    # --- v1.1: ink_diff finds a mark added to one page
    INK = HERE.parent / "scripts" / "ink_diff.py"
    try:
        from reportlab.pdfgen import canvas
        def pdf(path, mark):
            c = canvas.Canvas(str(path), pagesize=(400, 225))
            for page in range(2):
                c.drawString(40, 180, "page %d" % (page + 1))
                if mark and page == 1:
                    c.setLineWidth(3); c.line(60, 100, 300, 120)
                c.showPage()
            c.save()
        pdf(tmp / "sent.pdf", False); pdf(tmp / "ann.pdf", True)
        r = subprocess.run([sys.executable, "-B", str(INK), str(tmp / "sent.pdf"), str(tmp / "ann.pdf"),
                            "-o", str(tmp / "ink"), "--json", "--dpi", "72", "--zoom-dpi", "144"],
                           capture_output=True, text=True)
        res = json.loads(r.stdout) if r.returncode == 0 else []
        check("ink_diff finds the mark on page 2 only", [x["page"] for x in res] == [2], r.stderr[-200:])
        check("ink_diff writes red page and zoom crop", bool(res) and Path(res[0]["red_page"]).is_file() and res[0]["zoom_crops"])
    except ImportError:
        print("SKIP ink_diff test (reportlab not installed)")

    # --- v1.1: reading-PDF builder at least parses its arguments
    PDFB = HERE.parent / "scripts" / "make_reading_pdf.py"
    r = subprocess.run([sys.executable, "-B", str(PDFB), "--help"], capture_output=True, text=True)
    check("make_reading_pdf --help exits 0", r.returncode == 0, r.stderr[-200:])

print(f"\n{'All checks passed' if not failures else str(len(failures)) + ' check(s) failed'}")
sys.exit(1 if failures else 0)
