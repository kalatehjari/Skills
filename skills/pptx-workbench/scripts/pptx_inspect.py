#!/usr/bin/env python3
"""Summarise a deck: size, layouts available, and per slide its layout, title,
shapes (text/picture/table/chart/group/media), word count, notes, and
{{placeholders}}. Use before editing or reusing a deck or template.

Usage:
    python pptx_inspect.py deck.pptx [--json] [--layouts]
--layouts lists every slide layout with its placeholders (for building from a template).
"""
import argparse
import json
import os
import sys
from collections import Counter

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pptx_common import PLACEHOLDER, iter_shapes, iter_text_frames, slide_title  # noqa: E402

from pptx import Presentation  # noqa: E402
from pptx.enum.shapes import MSO_SHAPE_TYPE  # noqa: E402


def kind(sh):
    if getattr(sh, "has_chart", False) and sh.has_chart:
        return "chart"
    if getattr(sh, "has_table", False) and sh.has_table:
        return "table"
    if sh.shape_type == MSO_SHAPE_TYPE.PICTURE or (sh.is_placeholder and hasattr(sh, "image")):
        return "picture"
    if sh.shape_type in (MSO_SHAPE_TYPE.MEDIA,):
        return "media"
    if sh.has_text_frame and sh.text_frame.text.strip():
        return "text"
    return "shape"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--layouts", action="store_true")
    a = ap.parse_args()
    prs = Presentation(a.deck)
    W, H = prs.slide_width, prs.slide_height
    info = {"file": a.deck, "slides": len(prs.slides), "size_in": [round(W / 914400, 2), round(H / 914400, 2)],
            "aspect": "16:9" if abs(W / H - 16 / 9) < 0.02 else "4:3" if abs(W / H - 4 / 3) < 0.02 else f"{W / H:.2f}:1"}
    info["layouts"] = [{"name": l.name, "placeholders": [f"{ph.placeholder_format.idx}:{ph.placeholder_format.type.name if ph.placeholder_format.type else '?'}" for ph in l.placeholders]}
                       for l in prs.slide_layouts]
    fonts = Counter()
    slides = []
    for i, s in enumerate(prs.slides, start=1):
        kinds = Counter(kind(sh) for sh in iter_shapes(s.shapes))
        words, phs = 0, Counter()
        for _, tf in iter_text_frames(s):
            words += len(tf.text.split())
            for m in PLACEHOLDER.finditer(tf.text):
                phs[m.group(1)] += 1
            for p in tf.paragraphs:
                for r in p.runs:
                    if r.font.name:
                        fonts[r.font.name] += 1
        empty_ph = [ph.name for ph in s.placeholders if ph.has_text_frame and not ph.text_frame.text.strip()]
        notes = s.notes_slide.notes_text_frame.text.strip() if s.has_notes_slide else ""
        slides.append({"slide": i, "layout": s.slide_layout.name, "title": slide_title(s), "shapes": dict(kinds),
                       "words": words, "empty_placeholders": empty_ph, "notes": notes[:200],
                       "placeholders": dict(phs), "hidden": s._element.get("show") == "0"})
    info["slides_detail"] = slides
    info["fonts_used"] = dict(fonts.most_common(8))
    if a.json:
        print(json.dumps(info, indent=2, ensure_ascii=False))
        return
    print(f"File: {a.deck}\n{info['slides']} slides, {info['size_in'][0]}×{info['size_in'][1]} in ({info['aspect']})")
    if info["fonts_used"]:
        print(f"Fonts set on runs: {info['fonts_used']} (others inherit the theme)")
    for sl in slides:
        shapes = ", ".join(f"{v} {k}" for k, v in sl["shapes"].items())
        flags = []
        if sl["empty_placeholders"]:
            flags.append(f"empty placeholders: {sl['empty_placeholders']}")
        if sl["placeholders"]:
            flags.append("{{" + "}}, {{".join(sl["placeholders"]) + "}}")
        if sl["hidden"]:
            flags.append("HIDDEN")
        print(f"\n{sl['slide']:>3}. [{sl['layout']}] {sl['title'] or '(no title)'}")
        print(f"     {shapes or 'empty'}; {sl['words']} words" + (f"; notes: {sl['notes'][:80]!r}" if sl["notes"] else ""))
        if flags:
            print("     " + "; ".join(flags))
    if a.layouts:
        print("\nLayouts:")
        for k, l in enumerate(info["layouts"]):
            print(f"  {k}: {l['name']}  [{', '.join(l['placeholders'])}]")


if __name__ == "__main__":
    main()
