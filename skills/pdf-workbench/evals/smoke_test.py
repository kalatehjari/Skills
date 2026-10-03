#!/usr/bin/env python3
"""Smoke test for pdf-workbench: runs every script against the sample files.

    python evals/smoke_test.py            # from the skill folder
Exits non-zero on the first failure. Uses a temporary folder for outputs.
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(os.path.dirname(HERE), "scripts")
FILES = os.path.join(HERE, "files")


def run(name, *args, expect=0):
    cmd = [sys.executable, os.path.join(SCRIPTS, name), *args]
    res = subprocess.run(cmd, capture_output=True, text=True)
    ok = res.returncode == expect
    print(("PASS " if ok else "FAIL ") + name + " " + " ".join(os.path.basename(a) for a in args))
    if not ok:
        print(res.stdout[-1500:], res.stderr[-1500:], sep="\n")
        sys.exit(1)
    return res


def main():
    paper, form, scan, flat = (os.path.join(FILES, f) for f in
                               ("sample_paper.pdf", "sample_form.pdf", "sample_scan.pdf", "sample_flat_form.pdf"))
    with tempfile.TemporaryDirectory() as t:
        j = lambda *p: os.path.join(t, *p)
        info = json.loads(run("pdf_inspect.py", paper, "--json").stdout)
        assert info["pages"] == 3 and info["dois_found"][0]["page"] == 1
        assert json.loads(run("pdf_inspect.py", scan, "--json").stdout)["scanned_pages"] == [1]
        out = run("pdf_text.py", paper, "--pages", "1", "--columns", "2", "--header", "125").stdout
        assert "cyclic loading" in out.splitlines()[1]
        run("pdf_tables.py", paper, "--format", "xlsx", "-o", j("t.xlsx"))
        assert "Table 1" in run("pdf_tables.py", paper, "--format", "md").stdout
        run("pdf_pages.py", "merge", paper, form, "-o", j("m.pdf"), "--bookmarks")
        run("pdf_pages.py", "extract", j("m.pdf"), "--pages", "2-4", "-o", j("e.pdf"))
        run("pdf_pages.py", "split", j("m.pdf"), "--ranges", "1-2,5;3-4", "-o", j("sp"))
        run("pdf_pages.py", "rotate", paper, "--angle", "90", "--pages", "2", "-o", j("r.pdf"))
        run("pdf_pages.py", "extract", paper, "--pages", "1", "-o", paper, expect=1)  # must refuse to overwrite
        fields = json.loads(run("pdf_forms.py", "list", form).stdout)
        assert {f["name"] for f in fields} >= {"applicant_name", "agree", "method", "soil", "notes"}
        with open(j("v.json"), "w") as fh:
            json.dump({"applicant_name": "Test", "agree": True, "method": "direct_shear", "soil": "sand", "notes": "x"}, fh)
        run("pdf_forms.py", "fill", form, j("v.json"), "-o", j("f.pdf"), "--flatten")
        assert "no fillable fields" in run("pdf_inspect.py", j("f.pdf")).stdout
        with open(j("bad.json"), "w") as fh:
            json.dump({"method": "vane"}, fh)
        run("pdf_forms.py", "fill", form, j("bad.json"), "-o", j("x.pdf"), expect=1)
        with open(j("spec.json"), "w") as fh:
            json.dump([{"page": 1, "x": 135, "y": 782, "text": "Test"}, {"page": 1, "x": 55, "y": 744, "type": "check", "size": 8, "center": True}], fh)
        run("pdf_overlay_text.py", flat, j("spec.json"), "-o", j("o.pdf"))
        run("pdf_render.py", j("o.pdf"), "--grid", "-o", j("png"))
        run("pdf_render.py", j("o.pdf"), "--dpi", "300", "--crop", "40,730,260,800", "-o", j("png"))
        run("pdf_images.py", paper, "-o", j("img"))
        try:
            run("pdf_ocr.py", scan, "-o", j("ocr.pdf"))
            assert json.loads(run("pdf_inspect.py", j("ocr.pdf"), "--json").stdout)["dois_found"], "OCR found no DOI"
        except SystemExit:
            print("(OCR step failed — is tesseract installed?)")
            raise
    print("All checks passed.")


if __name__ == "__main__":
    main()
