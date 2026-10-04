#!/usr/bin/env python3
"""Smoke test for arena-supreme: runs every script against the sample files.

    python evals/smoke_test.py            # from the skill folder
Exits non-zero on the first failure. Uses a temporary folder for outputs.
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(os.path.dirname(HERE), "scripts")
FILES = os.path.join(HERE, "files")


def run(name, *args, expect=0, want=None):
    res = subprocess.run([sys.executable, "-B", os.path.join(SCRIPTS, name), *args], capture_output=True, text=True)
    ok = res.returncode == expect and (want is None or want in res.stdout + res.stderr)
    print(("PASS " if ok else "FAIL ") + name + " " + " ".join(os.path.basename(a) for a in args))
    if not ok:
        print(res.stdout[-1500:], res.stderr[-1500:], sep="\n")
        sys.exit(1)
    return res


def main():
    f = lambda n: os.path.join(FILES, n)
    tmp = tempfile.mkdtemp()
    try:
        run("verify_quotes.py", f("report_good.md"), "--sources", f("source_review.md"), want="NOT FOUND: 0")
        run("verify_quotes.py", f("report_bad.md"), "--sources", f("source_review.md"), expect=1, want="NOT FOUND: 1")
        run("check_numbers.py", f("report_good.md"), "--refs", f("NUMBERS.md"), want="not in reference files: 0")
        run("check_numbers.py", f("report_bad.md"), "--refs", f("NUMBERS.md"), want="7.12")
        run("build_digest.py", f("source_review.md"), "-o", os.path.join(tmp, "DG"), "--tables", "|", want="wrote 1 part")
        digest = open(os.path.join(tmp, "DG_part1.md"), encoding="utf-8").read()
        assert "It states the thesis at a lectern." in digest and "Not ready for submission." in digest, "digest content"
        print("PASS digest content is verbatim")
        run("bt_aggregate.py", "--key", f("KEY.json"), f("judges/P1a_JUDGE.md"), f("judges/P1b_JUDGE.md"), want="margin-weighted")
        run("usage_meter.py", "--help", want="usage")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("ALL PASS")


if __name__ == "__main__":
    main()
