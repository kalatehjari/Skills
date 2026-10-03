#!/usr/bin/env python3
"""Summarise a PDF so you can choose how to process it.

Reports page count, page sizes, metadata, encryption, text per page (to spot
scans), form fields, images, bookmarks, attachments and DOIs found in the text.

Usage:
    python pdf_inspect.py input.pdf [--json] [--password PW] [--max-pages N]
"""
import argparse
import json
import re
import sys

try:
    from pypdf import PdfReader
except ImportError:
    sys.exit("pypdf is required: pip install pypdf")

DOI_RE = re.compile(r"\b10\.\d{4,9}/[^\s\"<>]+", re.IGNORECASE)
SCAN_THRESHOLD = 25  # pages with fewer extractable characters than this are flagged


def page_size_label(w, h):
    sizes = {"A4": (595, 842), "Letter": (612, 792), "A3": (842, 1191), "Legal": (612, 1008), "A5": (420, 595)}
    for name, (sw, sh) in sizes.items():
        if abs(w - sw) < 3 and abs(h - sh) < 3:
            return f"{name} portrait"
        if abs(w - sh) < 3 and abs(h - sw) < 3:
            return f"{name} landscape"
    return "custom"


def count_images(page):
    try:
        return len(page.images)
    except Exception:
        return None


def walk_outline(outline, reader, depth=0, out=None):
    out = [] if out is None else out
    for item in outline:
        if isinstance(item, list):
            walk_outline(item, reader, depth + 1, out)
        else:
            try:
                pg = reader.get_destination_page_number(item) + 1
            except Exception:
                pg = None
            out.append({"title": str(item.title), "page": pg, "level": depth})
    return out


def inspect(path, password=None, max_pages=None):
    reader = PdfReader(path)
    info = {"file": path, "encrypted": reader.is_encrypted, "decrypted": None}
    if reader.is_encrypted:
        try:
            ok = reader.decrypt(password or "")
            info["decrypted"] = bool(ok)
        except Exception as exc:  # missing crypto backend, etc.
            info["decrypted"] = False
            info["decrypt_error"] = str(exc)
        if not info["decrypted"]:
            info["note"] = "Encrypted and could not be opened. Supply --password, or try: qpdf --decrypt in.pdf out.pdf"
            return info

    n = len(reader.pages)
    info["pages"] = n
    meta = reader.metadata or {}
    info["metadata"] = {k.lstrip("/"): str(v) for k, v in meta.items()} if meta else {}

    pages = []
    dois = []
    limit = n if not max_pages else min(n, max_pages)
    for i in range(limit):
        p = reader.pages[i]
        w, h = float(p.mediabox.width), float(p.mediabox.height)
        rot = int(p.get("/Rotate", 0) or 0)
        try:
            text = p.extract_text() or ""
        except Exception:
            text = ""
        chars = len(text.strip())
        dois.extend((m.group(0).rstrip(".,;)]"), i + 1) for m in DOI_RE.finditer(text))
        n_img = count_images(p)
        pages.append({
            "page": i + 1,
            "width_pt": round(w, 1),
            "height_pt": round(h, 1),
            "size": page_size_label(w, h),
            "rotation": rot,
            "text_chars": chars,
            # little text + at least one image = probably a scan; little text and no image = just a sparse page
            "likely_scanned": chars < SCAN_THRESHOLD and bool(n_img),
            "sparse_text": chars < SCAN_THRESHOLD,
            "images": n_img,
            "annotations": len(p.get("/Annots", []) or []),
        })
    info["pages_detail"] = pages
    if limit < n:
        info["pages_detail_truncated_at"] = limit

    fields = reader.get_fields() or {}
    info["form"] = {
        "has_acroform": "/AcroForm" in reader.trailer["/Root"],
        "field_count": len(fields),
        "field_types": sorted({str(v.get("/FT", "?")) for v in fields.values()}),
        "has_xfa": bool(reader.trailer["/Root"].get("/AcroForm", {}).get("/XFA")) if "/AcroForm" in reader.trailer["/Root"] else False,
    }
    try:
        info["bookmarks"] = walk_outline(reader.outline, reader)
    except Exception:
        info["bookmarks"] = []
    try:
        info["attachments"] = list((reader.attachments or {}).keys())
    except Exception:
        info["attachments"] = []
    seen, out = set(), []
    for d, pg in dois:
        if d.lower() not in seen:
            seen.add(d.lower())
            out.append({"doi": d, "page": pg})
    info["dois_found"] = out[:50]  # in page order; on articles the first one on page 1 is usually the article's own

    scanned = [p["page"] for p in pages if p["likely_scanned"]]
    info["scanned_pages"] = scanned
    if scanned and len(scanned) == len(pages):
        info["advice"] = "No text layer found. OCR it first: python pdf_ocr.py in.pdf -o out.pdf"
    elif scanned:
        info["advice"] = f"{len(scanned)} page(s) look scanned (little text, has an image); OCR them if you need their text."
    return info


def compress_ranges(nums):
    if not nums:
        return "none"
    out, start, prev = [], nums[0], nums[0]
    for x in nums[1:]:
        if x == prev + 1:
            prev = x
            continue
        out.append(f"{start}-{prev}" if start != prev else str(start))
        start = prev = x
    out.append(f"{start}-{prev}" if start != prev else str(start))
    return ",".join(out)


def print_human(info):
    print(f"File: {info['file']}")
    if info.get("note"):
        print(f"Encrypted: yes — {info['note']}")
        return
    print(f"Pages: {info['pages']}" + ("  (encrypted, opened)" if info["encrypted"] else ""))
    sizes = {}
    for p in info["pages_detail"]:
        key = f"{p['size']} ({p['width_pt']}×{p['height_pt']} pt)" + (f", rotated {p['rotation']}°" if p["rotation"] else "")
        sizes.setdefault(key, []).append(p["page"])
    print("Page sizes:")
    for k, v in sizes.items():
        print(f"  {k}: pages {compress_ranges(v)}")
    md = info.get("metadata") or {}
    if md:
        print("Metadata:")
        for k in ("Title", "Author", "Subject", "Creator", "Producer", "CreationDate", "ModDate"):
            if k in md:
                print(f"  {k}: {md[k]}")
    total_chars = sum(p["text_chars"] for p in info["pages_detail"])
    sparse = [p["page"] for p in info["pages_detail"] if p["sparse_text"] and not p["likely_scanned"]]
    print(f"Text layer: {total_chars} characters in total; likely-scanned pages: {compress_ranges(info['scanned_pages'])}"
          + (f"; sparse (little text, no images) pages: {compress_ranges(sparse)}" if sparse else ""))
    imgs = [p["images"] for p in info["pages_detail"] if p["images"] is not None]
    if imgs:
        print(f"Embedded images: {sum(imgs)}")
    f = info["form"]
    if f["field_count"]:
        print(f"Form: {f['field_count']} fields, types {', '.join(f['field_types'])}" + ("  [XFA present]" if f["has_xfa"] else ""))
    else:
        print("Form: no fillable fields")
    if info["bookmarks"]:
        print(f"Bookmarks: {len(info['bookmarks'])} (first: {info['bookmarks'][0]['title']!r})")
    if info["attachments"]:
        print(f"Attachments: {', '.join(info['attachments'])}")
    if info["dois_found"]:
        shown = [f"{d['doi']} (p{d['page']})" for d in info["dois_found"][:5]]
        print(f"DOIs found: {', '.join(shown)}" + (f" … +{len(info['dois_found']) - 5} more" if len(info["dois_found"]) > 5 else ""))
    if info.get("advice"):
        print(f"Advice: {info['advice']}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("--json", action="store_true", help="print JSON instead of a summary")
    ap.add_argument("--password", help="password for encrypted files")
    ap.add_argument("--max-pages", type=int, help="only analyse the first N pages (for very large files)")
    a = ap.parse_args()
    info = inspect(a.pdf, a.password, a.max_pages)
    if a.json:
        print(json.dumps(info, indent=2, ensure_ascii=False))
    else:
        print_human(info)


if __name__ == "__main__":
    main()
