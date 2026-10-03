#!/usr/bin/env python3
"""Work with fillable (AcroForm) PDF forms.

Subcommands:
  list    form.pdf [-o fields.json]
          Every field: name, type, current value, allowed options, page, rect, tooltip.
  fill    form.pdf values.json -o filled.pdf [--flatten] [--ignore-unknown]
          values.json maps field name -> value:
            text      "any string"
            checkbox  true / false   (or the exact on-state name from `list`)
            radio     one of the options listed by `list`
            choice    one of the options listed by `list`
  flatten filled.pdf -o flat.pdf
          Burn field appearances into page content so the fields disappear.
          This stops casual changes in a viewer but is NOT tamper-proof. To also
          restrict editing, add an owner password (see references/editing-and-assembly.md).
          Flattened text fields may lose their coloured box/border; check the render.

For forms WITHOUT fields, use pdf_render.py --grid + pdf_overlay_text.py instead.
"""
import argparse
import json
import shutil
import subprocess
import sys

try:
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import NameObject
except ImportError:
    sys.exit("pypdf is required: pip install pypdf")

TYPE_NAMES = {"/Tx": "text", "/Btn": "button", "/Ch": "choice", "/Sig": "signature"}


def inherited(obj, key):
    while obj is not None:
        if key in obj:
            return obj[key]
        obj = obj.get("/Parent")
        obj = obj.get_object() if obj is not None else None
    return None


def full_name(obj):
    parts = []
    while obj is not None:
        if "/T" in obj:
            parts.append(str(obj["/T"]))
        obj = obj.get("/Parent")
        obj = obj.get_object() if obj is not None else None
    return ".".join(reversed(parts))


def classify(widget):
    ft = inherited(widget, "/FT")
    kind = TYPE_NAMES.get(str(ft), str(ft))
    if kind == "button":
        flags = int(inherited(widget, "/Ff") or 0)
        if flags & (1 << 16):
            kind = "pushbutton"
        elif flags & (1 << 15):
            kind = "radio"
        else:
            kind = "checkbox"
    return kind


def on_states(widget):
    ap = widget.get("/AP")
    if not ap:
        return []
    normal = ap.get_object().get("/N")
    if normal is None or not hasattr(normal.get_object(), "keys"):
        return []
    return [str(k).lstrip("/") for k in normal.get_object().keys() if str(k) != "/Off"]


def collect(reader):
    fields = {}
    for pno, page in enumerate(reader.pages, start=1):
        for ref in page.get("/Annots", []) or []:
            w = ref.get_object()
            if w.get("/Subtype") != "/Widget":
                continue
            name = full_name(w)
            if not name:
                continue
            kind = classify(w)
            f = fields.setdefault(name, {"name": name, "type": kind, "value": None, "options": [], "widgets": []})
            v = inherited(w, "/V")
            if v is not None:
                f["value"] = str(v).lstrip("/") if kind in ("checkbox", "radio") else str(v)
            if kind in ("checkbox", "radio"):
                for s in on_states(w):
                    if s not in f["options"]:
                        f["options"].append(s)
            elif kind == "choice":
                opts = inherited(w, "/Opt") or []
                f["options"] = [str(o[1] if isinstance(o, list) else o) for o in opts]
            tu = inherited(w, "/TU")
            if tu:
                f["tooltip"] = str(tu)
            ff = int(inherited(w, "/Ff") or 0)
            if ff & 1:
                f["readonly"] = True
            if ff & 2:
                f["required"] = True
            if kind == "text" and inherited(w, "/MaxLen"):
                f["max_length"] = int(inherited(w, "/MaxLen"))
            wd = {"page": pno, "rect": [round(float(x), 1) for x in w.get("/Rect", [])]}
            if kind in ("checkbox", "radio"):
                states = on_states(w)
                if states:
                    wd["state"] = states[0]  # which option this particular box/button represents
            f["widgets"].append(wd)
    return list(fields.values())


def cmd_list(a):
    r = PdfReader(a.pdf)
    if r.is_encrypted:
        r.decrypt(a.password or "")
    fields = collect(r)
    if not fields:
        print("No fillable fields. Use pdf_render.py --grid and pdf_overlay_text.py for flat forms.", file=sys.stderr)
        sys.exit(1)
    text = json.dumps(fields, indent=2, ensure_ascii=False)
    if a.output:
        with open(a.output, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"Wrote {len(fields)} field(s) to {a.output}", file=sys.stderr)
    else:
        print(text)


def normalise(field, value):
    """Turn a user value into what pypdf expects; return (value, error)."""
    kind, opts = field["type"], field["options"]
    if kind == "checkbox":
        if isinstance(value, bool) or str(value).lower() in ("true", "false", "yes", "no", "on", "off", "1", "0"):
            truthy = value if isinstance(value, bool) else str(value).lower() in ("true", "yes", "on", "1")
            if not truthy:
                return "/Off", None
            return "/" + (opts[0] if opts else "Yes"), None
        if str(value).lstrip("/") in opts:
            return "/" + str(value).lstrip("/"), None
        return None, f"checkbox accepts true/false or {opts}"
    if kind == "radio":
        v = str(value).lstrip("/")
        if v not in opts:
            return None, f"radio options are {opts}"
        return "/" + v, None
    if kind == "choice":
        v = str(value)
        if opts and v not in opts:
            return None, f"choice options are {opts}"
        return v, None
    if kind in ("pushbutton", "signature"):
        return None, f"{kind} fields can't be filled with a value"
    v = str(value)
    if field.get("max_length") and len(v) > field["max_length"]:
        return None, f"longer than max_length {field['max_length']}"
    return v, None


def flatten_file(src, dst):
    try:
        import pikepdf
        with pikepdf.open(src) as pdf:
            pdf.generate_appearance_streams()
            pdf.flatten_annotations("all")
            if "/AcroForm" in pdf.Root:
                del pdf.Root["/AcroForm"]
            pdf.save(dst)
        return "pikepdf"
    except ImportError:
        pass
    if shutil.which("qpdf"):
        subprocess.run(["qpdf", src, "--generate-appearances", "--flatten-annotations=all", dst], check=True)
        return "qpdf"
    sys.exit("Flattening needs pikepdf (pip install pikepdf) or the qpdf CLI")


def cmd_fill(a):
    r = PdfReader(a.pdf)
    if r.is_encrypted:
        r.decrypt(a.password or "")
    fields = {f["name"]: f for f in collect(r)}
    with open(a.values, encoding="utf-8") as fh:
        wanted = json.load(fh)

    errors, unknown, by_page = [], [], {}
    for name, value in wanted.items():
        f = fields.get(name)
        if f is None:
            # allow the short (last-segment) name when it is unambiguous
            matches = [k for k in fields if k.split(".")[-1] == name]
            if len(matches) == 1:
                f = fields[matches[0]]
            elif matches:
                errors.append(f"'{name}' is ambiguous — use one of {matches}")
                continue
            else:
                unknown.append(name)
                continue
        val, err = normalise(f, value)
        if err:
            errors.append(f"{f['name']}: {err} (got {value!r})")
            continue
        current = f.get("value")
        if current not in (None, "", "Off") and str(val).lstrip("/") != current:
            print(f"Note: {f['name']} was pre-filled with {current!r}; replacing it", file=sys.stderr)
        for wd in f["widgets"]:
            # fully qualified name avoids clashes like applicant.name vs spouse.name
            by_page.setdefault(wd["page"], {})[f["name"]] = val
        if f.get("readonly"):
            print(f"Note: {f['name']} is read-only in the form; value set anyway", file=sys.stderr)

    if unknown and not a.ignore_unknown:
        errors.append(f"unknown field name(s): {unknown} — run `list` to see valid names")
    if errors:
        sys.exit("Not filled:\n  " + "\n  ".join(errors))

    w = PdfWriter(clone_from=r)
    for pno, vals in by_page.items():
        w.update_page_form_field_values(w.pages[pno - 1], vals, auto_regenerate=False)
    w.set_need_appearances_writer(True)

    out_unflat = a.output if not a.flatten else a.output + ".tmp.pdf"
    with open(out_unflat, "wb") as fh:
        w.write(fh)
    if a.flatten:
        engine = flatten_file(out_unflat, a.output)
        import os
        os.remove(out_unflat)
        print(f"Flattened with {engine}", file=sys.stderr)

    # verify by reading back
    check = {f["name"]: f["value"] for f in collect(PdfReader(a.output))} if not a.flatten else None
    filled = sum(len(v) for v in by_page.values())
    print(f"Wrote {a.output}: {len(wanted) - len(unknown)} field(s) set" + (f", skipped unknown {unknown}" if unknown else ""), file=sys.stderr)
    if check is not None:
        mismatched = [n for n, v in wanted.items() if n in check and isinstance(v, str) and fields[n]["type"] == "text" and check[n] != v]
        if mismatched:
            print(f"Warning: read-back mismatch for {mismatched}", file=sys.stderr)
    print("Render a page with pdf_render.py to confirm the values are visible.", file=sys.stderr)


def cmd_flatten(a):
    engine = flatten_file(a.pdf, a.output)
    print(f"Wrote {a.output} (flattened with {engine})", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--password")
    sub = ap.add_subparsers(dest="cmd", required=True)
    l = sub.add_parser("list"); l.add_argument("pdf"); l.add_argument("-o", "--output"); l.set_defaults(fn=cmd_list)
    f = sub.add_parser("fill"); f.add_argument("pdf"); f.add_argument("values"); f.add_argument("-o", "--output", required=True)
    f.add_argument("--flatten", action="store_true"); f.add_argument("--ignore-unknown", action="store_true"); f.set_defaults(fn=cmd_fill)
    fl = sub.add_parser("flatten"); fl.add_argument("pdf"); fl.add_argument("-o", "--output", required=True); fl.set_defaults(fn=cmd_flatten)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
