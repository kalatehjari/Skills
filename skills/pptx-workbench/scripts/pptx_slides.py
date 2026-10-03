#!/usr/bin/env python3
"""Slide-level operations on a deck (input is never modified).

  delete    deck.pptx --slides 3,7-9 -o out.pptx
  keep      deck.pptx --slides 1-5,12 -o out.pptx          (delete everything else)
  reorder   deck.pptx --order 1,3,2,4- -o out.pptx         (every slide must appear once)
  duplicate deck.pptx --slides 4 -o out.pptx               (copy placed right after the original)
  hide      deck.pptx --slides 9-10 -o out.pptx            (hidden in slide show; --unhide to reverse)
  notes     deck.pptx --notes notes.json -o out.pptx       ({"3": "Speaker notes for slide 3", ...})
  merge     a.pptx b.pptx -o out.pptx                      (b's slides appended using a's layouts —
                                                          text, pictures, tables; charts not copied)
"""
import argparse
import copy
import json
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pptx_common import parse_slides  # noqa: E402

from pptx import Presentation  # noqa: E402
from pptx.opc.constants import RELATIONSHIP_TYPE as RT  # noqa: E402


def sld_ids(prs):
    return prs.slides._sldIdLst


def delete(prs, idxs):
    lst = sld_ids(prs)
    items = list(lst)
    for i in sorted(idxs, reverse=True):
        el = items[i]
        prs.part.drop_rel(el.rId)
        lst.remove(el)


def copy_slide(prs, src_slide, dest_prs=None, layout=None):
    """Copy shapes (and picture/media relationships) of src_slide into a new slide."""
    dest_prs = dest_prs or prs
    layout = layout or (src_slide.slide_layout if dest_prs is prs else dest_prs.slide_layouts[6 if len(dest_prs.slide_layouts) > 6 else -1])
    new = dest_prs.slides.add_slide(layout)
    for ph in list(new.placeholders):
        ph._element.getparent().remove(ph._element)
    skipped = 0
    for sh in src_slide.shapes:
        el = copy.deepcopy(sh._element)
        # re-link images/media
        for blip in el.xpath(".//a:blip"):
            rid = blip.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed")
            if rid and rid in src_slide.part.rels:
                part = src_slide.part.rels[rid].target_part
                blip.set("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed",
                         new.part.relate_to(part, RT.IMAGE))
        if el.xpath(".//c:chart") if hasattr(el, "xpath") else False:
            skipped += 1
            continue
        new.shapes._spTree.insert_element_before(el, "p:extLst")
    if src_slide.has_notes_slide and src_slide.notes_slide.notes_text_frame.text:
        new.notes_slide.notes_text_frame.text = src_slide.notes_slide.notes_text_frame.text
    return new, skipped


def move(prs, from_idx, to_idx):
    lst = sld_ids(prs)
    el = list(lst)[from_idx]
    lst.remove(el)
    lst.insert(to_idx, el)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["delete", "keep", "reorder", "duplicate", "hide", "notes", "merge"])
    ap.add_argument("decks", nargs="+")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--slides")
    ap.add_argument("--order")
    ap.add_argument("--notes")
    ap.add_argument("--unhide", action="store_true")
    a = ap.parse_args()
    if any(os.path.abspath(a.output) == os.path.abspath(d) for d in a.decks):
        sys.exit("Refusing to overwrite an input; choose a different -o")
    prs = Presentation(a.decks[0])
    n = len(prs.slides)
    msg = ""
    if a.cmd == "delete":
        idx = parse_slides(a.slides, n)
        delete(prs, idx)
        msg = f"deleted {len(idx)} slide(s)"
    elif a.cmd == "keep":
        keep = set(parse_slides(a.slides, n))
        delete(prs, [i for i in range(n) if i not in keep])
        msg = f"kept {len(keep)} slide(s)"
    elif a.cmd == "reorder":
        order = []
        for part in a.order.split(","):
            order += parse_slides(part, n)
        if sorted(order) != list(range(n)):
            sys.exit(f"--order must list every slide 1-{n} exactly once (got {[o + 1 for o in order]})")
        lst = sld_ids(prs)
        items = list(lst)
        for el in items:
            lst.remove(el)
        for i in order:
            lst.append(items[i])
        msg = "reordered"
    elif a.cmd == "duplicate":
        idx = parse_slides(a.slides, n)
        for k, i in enumerate(sorted(idx, reverse=True)):
            _, skipped = copy_slide(prs, prs.slides[i])
            move(prs, len(prs.slides) - 1, i + 1)
            if skipped:
                print(f"  slide {i + 1}: {skipped} chart(s) not copied (re-create with pptx_build or in PowerPoint)", file=sys.stderr)
        msg = f"duplicated {len(idx)} slide(s)"
    elif a.cmd == "hide":
        for i in parse_slides(a.slides, n):
            el = prs.slides[i]._element
            if a.unhide:
                el.attrib.pop("show", None)
            else:
                el.set("show", "0")
        msg = ("unhid" if a.unhide else "hid") + " slide(s)"
    elif a.cmd == "notes":
        with open(a.notes, encoding="utf-8") as fh:
            notes = json.load(fh)
        for k, text in notes.items():
            i = int(k) - 1
            if not 0 <= i < n:
                sys.exit(f"Slide {k} does not exist (1-{n})")
            prs.slides[i].notes_slide.notes_text_frame.text = text
        msg = f"set notes on {len(notes)} slide(s)"
    elif a.cmd == "merge":
        total_skipped = 0
        for other in a.decks[1:]:
            src = Presentation(other)
            if (src.slide_width, src.slide_height) != (prs.slide_width, prs.slide_height):
                print(f"  ! {other} has a different slide size; shapes keep their absolute positions", file=sys.stderr)
            for s in src.slides:
                _, skipped = copy_slide(src, s, dest_prs=prs)
                total_skipped += skipped
        msg = f"merged {len(a.decks) - 1} deck(s)" + (f"; {total_skipped} chart(s) not copied" if total_skipped else "")
    prs.save(a.output)
    print(f"Wrote {a.output}: {msg}; now {len(prs.slides)} slides", file=sys.stderr)


if __name__ == "__main__":
    main()
