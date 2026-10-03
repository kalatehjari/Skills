#!/usr/bin/env python3
"""Smoke test for docx-workbench: runs every script against the sample files.

    python evals/smoke_test.py
LibreOffice/pandoc steps are skipped (with a note) when those tools are missing.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(os.path.dirname(HERE), "scripts")
F = lambda n: os.path.join(HERE, "files", n)  # noqa: E731


def run(name, *args, expect=0):
    res = subprocess.run([sys.executable, os.path.join(SCRIPTS, name), *args], capture_output=True, text=True)
    ok = res.returncode == expect
    print(("PASS " if ok else "FAIL ") + name + " " + " ".join(os.path.basename(str(a)) for a in args))
    if not ok:
        print(res.stdout[-1500:], res.stderr[-1500:], sep="\n")
        sys.exit(1)
    return res


def main():
    with tempfile.TemporaryDirectory() as t:
        j = lambda *p: os.path.join(t, *p)  # noqa: E731
        info = json.loads(run("docx_inspect.py", F("sample_template.docx"), "--json").stdout)
        assert "client_name" in info["placeholders"] and info["outline"]
        run("docx_fill_template.py", F("sample_template.docx"), F("sample_data.json"), "-o", j("filled.docx"), "--strict")
        info = json.loads(run("docx_inspect.py", j("filled.docx"), "--json").stdout)
        assert not info["placeholders"] and info["tables_detail"][0]["rows"] == 4
        run("docx_fill_template.py", F("sample_template.docx"), F("sample_data.json"), "-o", F("sample_template.docx"), expect=1)
        run("docx_replace.py", F("sample_template.docx"), "-o", j("rep.docx"), "--find", "Lot 12", "--replace", "Lot 14")
        assert "Lot 14" in run("docx_replace.py", j("rep.docx"), "--find", "Lot 14", "--dry-run").stdout
        edits = [{"find": "Lot 12", "replace": "Lot 14", "comment": "check"}, {"find": "groundwater table", "comment": "when?", "occurrence": 1}]
        with open(j("edits.json"), "w") as fh:
            json.dump(edits, fh)
        run("docx_redline.py", F("sample_template.docx"), j("edits.json"), "-o", j("red.docx"), "--author", "Tester")
        info = json.loads(run("docx_inspect.py", j("red.docx"), "--json").stdout)
        assert info["tracked_changes"]["insertions"] == 1 and len(info["comments"]) == 2
        listing = run("docx_revisions.py", "list", j("red.docx")).stdout
        assert "'12' → '14'" in listing, listing  # word-level (minimal) redline
        assert "Lot 12" in run("docx_revisions.py", "list", F("sample_reviewed.docx")).stdout
        assert "groundwater" in run("docx_revisions.py", "comments", F("sample_reviewed.docx")).stdout
        run("docx_revisions.py", "accept", F("sample_reviewed.docx"), "-o", j("acc.docx"), "--stop-tracking")
        run("docx_revisions.py", "accept", F("sample_reviewed.docx"), "-o", j("clean.docx"), "--drop-comments")
        import zipfile
        assert not [n for n in zipfile.ZipFile(j("clean.docx")).namelist() if "comment" in n.lower()]
        run("docx_revisions.py", "reject", F("sample_reviewed.docx"), "-o", j("rej.docx"))
        assert json.loads(run("docx_inspect.py", j("acc.docx"), "--json").stdout)["tracked_changes"]["insertions"] == 0
        assert "Changed" in run("docx_compare.py", j("rej.docx"), j("acc.docx")).stdout
        if shutil.which("pandoc"):
            run("docx_make_reference.py", "-o", j("house.docx"), "--a4")
            run("docx_convert.py", F("sample_draft.md"), "--to", "docx", "--reference-doc", j("house.docx"), "-o", j("draft.docx"))
            run("docx_convert.py", j("filled.docx"), "--to", "md", "-o", j("filled.md"))
            run("docx_finish.py", j("draft.docx"), "-o", j("final.docx"), "--a4", "--cover", "--toc", "--page-numbers")
            info = json.loads(run("docx_inspect.py", j("final.docx"), "--json").stdout)
            assert info["fields"].get("TOC") == 1 and info["equations"] >= 1 and info["footnotes"] == 1
        else:
            print("(pandoc missing: skipped Markdown steps)")
        if shutil.which("soffice") or shutil.which("libreoffice"):
            run("docx_convert.py", j("filled.docx"), "--to", "pdf", "-o", j("filled.pdf"))
            run("docx_convert.py", j("red.docx"), "--to", "png", "--pages", "1", "-o", j("png"))
        else:
            print("(LibreOffice missing: skipped PDF/PNG steps)")
    print("All checks passed.")


if __name__ == "__main__":
    main()
