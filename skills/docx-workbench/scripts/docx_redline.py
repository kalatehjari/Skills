#!/usr/bin/env python3
"""Make edits to a .docx as TRACKED CHANGES (redline) and/or add COMMENTS,
so the author can review and accept/reject them in Word.

Edits file (JSON list), applied in order:
[
  {"find": "Lot 12", "replace": "Lot 14", "comment": "Lot number per survey plan"},
  {"find": "very ", "replace": ""},                        # tracked deletion
  {"find": "groundwater table", "comment": "Give the date measured"},  # comment only
  {"find": "(\\\\d+) kPa", "replace": "\\\\1 kN/m²", "regex": true, "occurrence": 1}
]
Keys: find (required), replace (omit for comment-only), comment, regex (bool),
ignore_case (bool), occurrence ("all" default, or N = only the Nth match, counted in
the document as it is when that edit runs), minimal (default true: only the words
that differ are marked, so "Lot 12"->"Lot 14" shows as Lot ~~12~~ 14; false marks
the whole match). Edits run in file order; a later edit sees earlier ones applied.

Usage:
    python docx_redline.py in.docx edits.json -o in_reviewed.docx --author "R. Kalatehjari"
                           [--initials RK] [--track-future]
--track-future switches on Word's Track Changes so later manual edits are tracked too.
Scope: body paragraphs and table cells (Word does not allow comments in headers/footers).
A match must lie in plain text runs of one paragraph; matches crossing hyperlinks,
fields or existing tracked changes are skipped and reported.
"""
import argparse
import copy
import datetime as dt
import json
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _docx_common import set_setting  # noqa: E402

import docx  # noqa: E402
from docx.oxml import OxmlElement  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402
from docx.text.run import Run  # noqa: E402

TEXT_CHILDREN = {qn(t) for t in ("w:rPr", "w:t", "w:tab", "w:br", "w:cr", "w:noBreakHyphen", "w:softHyphen", "w:lastRenderedPageBreak")}
TRANSPARENT = {qn(t) for t in ("w:proofErr", "w:bookmarkStart", "w:bookmarkEnd", "w:permStart", "w:permEnd")}


class Ids:
    def __init__(self, root):
        vals = [int(v) for v in (e.get(qn("w:id")) for e in root.iter()) if v and v.lstrip("-").isdigit()]
        self.n = max(vals + [0]) + 1000

    def next(self):
        self.n += 1
        return str(self.n)


def plain(r):
    return all(c.tag in TEXT_CHILDREN for c in r)


def segments(p_el):
    """Lists of consecutive direct w:r children (transparent markup allowed between them)."""
    seg, out = [], []
    for c in p_el.iterchildren():
        if c.tag == qn("w:r"):
            seg.append(c)
        elif c.tag in TRANSPARENT:
            continue
        else:
            if seg:
                out.append(seg)
            seg = []
    if seg:
        out.append(seg)
    return out


def split_run(r_el, k, para):
    """Split run at character k; returns the new right-hand run element."""
    run = Run(r_el, para)
    t = run.text
    right = copy.deepcopy(r_el)
    run.text = t[:k]
    Run(right, para).text = t[k:]
    r_el.addnext(right)
    return right


def isolate(seg, s, e, para):
    """Split runs so [s,e) is covered exactly by whole runs; return those run elements."""
    pos, out = 0, []
    i = 0
    runs = list(seg)
    while i < len(runs):
        r = runs[i]
        t = Run(r, para).text
        lo, hi = pos, pos + len(t)
        if hi <= s or lo >= e or not t:
            pos = hi
            i += 1
            continue
        if not plain(r):
            return None
        if lo < s:  # cut off the left part
            right = split_run(r, s - lo, para)
            runs.insert(i + 1, right)
            pos = s
            i += 1
            continue
        if hi > e:  # cut off the right part
            split_run(r, e - lo, para)
            out.append(r)
            break
        out.append(r)
        pos = hi
        i += 1
    return out


def mark(tag, ids, author, date):
    el = OxmlElement(tag)
    el.set(qn("w:id"), ids.next())
    el.set(qn("w:author"), author)
    el.set(qn("w:date"), date)
    return el


def apply_edit(doc, para, runs, edit, ids, author, initials, date):
    has_replace = "replace" in edit
    first = runs[0]
    new_run = None
    if has_replace:
        template = copy.deepcopy(first)
        d_el = mark("w:del", ids, author, date)
        first.addprevious(d_el)
        for r in runs:
            d_el.append(r)
            for t in r.iter(qn("w:t")):
                t.tag = qn("w:delText")
        anchor_after = d_el
        if edit["replace"]:
            i_el = mark("w:ins", ids, author, date)
            Run(template, para).text = edit["replace"]
            i_el.append(template)
            d_el.addnext(i_el)
            anchor_after = i_el
            new_run = template
        start_el, end_el = d_el, anchor_after
    else:
        start_el, end_el = runs[0], runs[-1]

    if edit.get("comment"):
        target = [new_run] if new_run is not None else (list(runs) if not has_replace else [])
        apply_comment(doc, para, target, start_el, end_el, edit["comment"], author, initials)


def apply_comment(doc, para, target_els, start_el, end_el, text, author, initials):
    """Add a comment and place its range around start_el..end_el at paragraph level."""
    tmp = None
    if not target_els:  # pure deletion: anchor on a temporary empty run after the deletion
        tmp = OxmlElement("w:r")
        end_el.addnext(tmp)
        target_els = [tmp]
    c = doc.add_comment([Run(r, para) for r in target_els], text=text, author=author, initials=initials)
    cid = str(c.comment_id)
    p_el = para._p
    rs = p_el.find(f".//{qn('w:commentRangeStart')}[@{qn('w:id')}='{cid}']")
    re_ = p_el.find(f".//{qn('w:commentRangeEnd')}[@{qn('w:id')}='{cid}']")
    ref = None
    for r in p_el.iter(qn("w:r")):
        cr = r.find(qn("w:commentReference"))
        if cr is not None and cr.get(qn("w:id")) == cid:
            ref = r
    if rs is not None and re_ is not None and ref is not None:
        start_el.addprevious(rs)
        end_el.addnext(re_)
        re_.addnext(ref)
    if tmp is not None and tmp.getparent() is not None and len(tmp) == 0:
        tmp.getparent().remove(tmp)


def body_paragraphs(doc):
    def walk(container, seen):
        for p in container.paragraphs:
            yield p
        for t in container.tables:
            for row in t.rows:
                for cell in row.cells:
                    if cell._tc in seen:
                        continue
                    seen.add(cell._tc)
                    yield from walk(cell, seen)
    yield from walk(doc, set())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("docx")
    ap.add_argument("edits")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--author", default="Reviewer")
    ap.add_argument("--initials", default="")
    ap.add_argument("--track-future", action="store_true")
    a = ap.parse_args()
    if os.path.abspath(a.output) == os.path.abspath(a.docx):
        sys.exit("Refusing to overwrite the input; choose a different -o")
    with open(a.edits, encoding="utf-8") as fh:
        edits = json.load(fh)
    doc = docx.Document(a.docx)
    ids = Ids(doc.element)
    date = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    initials = a.initials or "".join(w[0] for w in a.author.replace(".", " ").split() if w)[:3]

    report = []
    for edit in edits:
        if "find" not in edit:
            sys.exit(f"Edit without 'find': {edit}")
        rx = re.compile(edit["find"] if edit.get("regex") else re.escape(edit["find"]), re.I if edit.get("ignore_case") else 0)
        want = edit.get("occurrence", "all")
        seen_n, done, skipped = 0, 0, 0
        for para in body_paragraphs(doc):
            for seg in segments(para._p):
                text = "".join(Run(r, para).text for r in seg)
                ms = list(rx.finditer(text))
                # process right-to-left so earlier offsets stay valid
                todo = []
                for m in ms:
                    seen_n += 1
                    if want == "all" or seen_n == int(want):
                        todo.append(m)
                for m in reversed(todo):
                    cur = segments_containing(para, seg)
                    e2 = dict(edit)
                    s, e = m.start(), m.end()
                    if "replace" in e2:
                        if edit.get("regex"):
                            e2["replace"] = m.expand(edit["replace"])
                        if edit.get("minimal", True):
                            s, e, e2["replace"] = trim_common(m.group(0), e2["replace"], s, e)
                            if s == e and not e2["replace"]:
                                continue  # replacement identical to the text
                            if s == e:  # pure insertion: anchor on the next character
                                e2["insert_at"] = True
                    if e2.pop("insert_at", False):
                        runs = isolate(cur, s, s + 1, para) if s < len(text) else isolate(cur, s - 1, s, para)
                        if not runs:
                            skipped += 1
                            continue
                        insert_only(para, runs[0], e2, ids, a.author, date, before=s < len(text), doc=doc, initials=initials)
                        done += 1
                        continue
                    runs = isolate(cur, s, e, para)
                    if not runs:
                        skipped += 1
                        continue
                    apply_edit(doc, para, runs, e2, ids, a.author, initials, date)
                    done += 1
        report.append((edit["find"], done, skipped))

    if a.track_future:
        set_setting(doc, "trackRevisions")
    doc.save(a.output)
    for find, done, skipped in report:
        print(f"{find!r}: {done} change(s)" + (f", {skipped} skipped (match crosses a hyperlink/field/revision)" if skipped else ""), file=sys.stderr)
    print(f"Wrote {a.output}. Open in Word → Review to accept/reject. Author: {a.author}", file=sys.stderr)
    if not any(d for _, d, _ in report):
        print("No edits applied — check the find strings against docx_inspect / docx_to_markdown output.", file=sys.stderr)


TOKEN = re.compile(r"\w+|\s+|[^\w\s]")


def trim_common(old, new, s, e):
    """Shrink a replacement to the differing middle, on word boundaries.
    Returns (new_start, new_end, new_replacement)."""
    a, b = TOKEN.findall(old), TOKEN.findall(new)
    i = 0
    while i < min(len(a), len(b)) and a[i] == b[i]:
        i += 1
    j = 0
    while j < min(len(a), len(b)) - i and a[len(a) - 1 - j] == b[len(b) - 1 - j]:
        j += 1
    pre = "".join(a[:i])
    suf = "".join(a[len(a) - j:]) if j else ""
    mid_new = "".join(b[i:len(b) - j]) if j else "".join(b[i:])
    return s + len(pre), e - len(suf), mid_new


def insert_only(para, anchor_run, edit, ids, author, date, before, doc, initials):
    """Tracked insertion with no deletion, placed before/after a 1-character anchor run."""
    template = copy.deepcopy(anchor_run)
    i_el = mark("w:ins", ids, author, date)
    Run(template, para).text = edit["replace"]
    i_el.append(template)
    (anchor_run.addprevious if before else anchor_run.addnext)(i_el)
    if edit.get("comment"):
        apply_comment(doc, para, [template], i_el, i_el, edit["comment"], author, initials)


def segments_containing(para, seg):
    """After earlier splits, recompute the live segment that contains the original first run."""
    for s in segments(para._p):
        if seg[0] in s:
            return s
    return seg


if __name__ == "__main__":
    main()
