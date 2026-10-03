# Filling PDF forms

First, find out which kind of form you have:

```bash
python scripts/pdf_inspect.py form.pdf      # look at the "Form:" line
```

- **"N fields"** means a fillable (AcroForm) form. Go to section A.
- **"no fillable fields"** means a printed-style form with lines and boxes drawn on the page. Go to section B.
- **"[XFA present]"** means a dynamic form built in Adobe LiveCycle. See section C.

## A. Fillable forms

### 1. List the fields

```bash
python scripts/pdf_forms.py list form.pdf -o fields.json
```

Each entry includes `name`, `type`, `value`, `options`, `widgets` (page and rectangle), and, where the form has them, `tooltip`, `required`, `readonly` and `max_length`. For checkboxes and radio buttons, each widget also has a `state`, which is the option that box represents. Radio buttons often have no printed label of their own. Match each `state` to its position (`rect`) on the rendered page before you choose one. Field names are often cryptic, like `Text7` or `topmostSubform[0].Page1[0].f1_03[0]`. To work out which label each one belongs to, look at the field's `tooltip` and its rectangle position. If that isn't enough, render the page (`pdf_render.py`) and match the rectangle to the label next to it.

### 2. Write the values

Write a JSON file that maps the fully qualified name to a value. The names below are only an illustration. Always use the names that `list` prints for the actual form:

```json
{
  "applicant.name": "Roo Kalatehjari",
  "agree": true,
  "test_method": "direct_shear",
  "soil_type": "sand"
}
```

Each type takes a different kind of value:

| Type | Value |
|---|---|
| text | any string. Dates go in the format the form asks for |
| checkbox | `true` or `false`, or the exact on-state name from `options` |
| radio | exactly one of the `options` |
| choice (dropdown or list) | exactly one of the `options` |
| signature or pushbutton | can't be filled with a value. To sign, overlay an image of the signature (section B) |

A short name is accepted when it's unambiguous: `"name"` works if only one field ends in `.name`. Otherwise the script stops and lists the candidates.

### 3. Fill, check, deliver

```bash
python scripts/pdf_forms.py fill form.pdf values.json -o form_filled.pdf
python scripts/pdf_render.py form_filled.pdf --pages 1     # look at it
```

The script checks every value before it writes anything. Unknown names, invalid options and text over `max_length` are all reported together, and no output is produced. Fix the JSON and run it again. Use `--ignore-unknown` only when you deliberately skip fields.

`--flatten` (or the separate `flatten` subcommand) burns the values into the page. The fields disappear and the file looks the same in every viewer. Flatten when the user wants a final copy to send. Don't flatten when they still need to edit, sign or submit it through a portal.

- To confirm that flattening worked, run `pdf_inspect.py` on the output. It should say "Form: no fillable fields". Then render the pages.
- Text and dropdown fields can lose their shaded box or border when flattened, leaving the value as plain text. Ticks and radio dots keep their outlines. Mention this if it's visible.
- **Flattening alone doesn't make a file uneditable.** Any PDF editor can still change it. When the user asks for a copy that "nobody can edit", also add an owner password that restricts changes (editing-and-assembly.md §5). Tell them it's a deterrent, not a security measure, and that real tamper-evidence needs a digital signature.
- If a field already has a value, the script prints a note when it replaces it. Mention any replaced value that the user didn't ask to change.

### Why values sometimes "disappear"

Some viewers, notably macOS Preview and some browsers, show only a field's stored appearance, not its value. The fill script sets `NeedAppearances` so that viewers regenerate the appearance. If the user reports blank fields anyway, flattening fixes it (it generates appearance streams with pikepdf or qpdf). `pdf_render.py` turns on form drawing, so its PNG shows what a compliant viewer displays.

## B. Forms without fields (flat forms)

### 1. Find the coordinates

```bash
python scripts/pdf_render.py form.pdf --pages 1 --grid --grid-step 25
```

Open the PNG. The red labels across the top are x, and the blue labels down the left are y. Both are in points, with the origin at the bottom-left. Text sits on its baseline, so set y about 2–3 pt above the line the user writes on.

For better precision, ask pdfplumber where the labels are, then place values relative to them. A character's baseline is the last number of its `matrix`. Don't use `bottom`, because it includes the descender and is about 2–3 pt lower than the baseline:

```python
import pdfplumber
with pdfplumber.open("form.pdf") as pdf:
    p = pdf.pages[0]
    for w in p.extract_words():
        if w["text"].startswith(("Name", "Date", "Borehole")):
            first = next(c for c in p.chars if abs(c["x0"] - w["x0"]) < 0.5 and abs(c["top"] - w["top"]) < 0.5)
            print(w["text"], "x1=", round(w["x1"], 1), "baseline_y=", round(first["matrix"][5], 1))
```

Start a value about 5–10 pt after the label's `x1`, on the same baseline, or 1–2 pt higher if there's an underline to clear.

### 2. Write the spec and overlay it

```json
[
  {"page": 1, "x": 140, "y": 731, "text": "Roo Kalatehjari"},
  {"page": 1, "x": 140, "y": 706, "text": "03/10/2026"},
  {"page": 1, "x": 61,  "y": 652, "type": "check", "size": 9},
  {"page": 1, "x": 120, "y": 600, "text": "Free-text answer that needs wrapping…", "max_width": 380, "size": 9},
  {"page": 2, "x": 380, "y": 95,  "type": "image", "path": "signature.png", "width": 110}
]
```

```bash
python scripts/pdf_overlay_text.py form.pdf spec.json -o form_filled.pdf
python scripts/pdf_render.py form_filled.pdf --pages 1,2
```

Look at the render. Nudge x and y by a few points and run it again until every value sits cleanly on its line or in its box. Two rounds is normal.

- Text with characters outside Latin-1, such as macrons in Māori names or Persian, Chinese or Greek letters: the script falls back to DejaVu Sans when it's available. For scripts DejaVu doesn't cover, set `"font_file"` to a TTF that does (for example Noto Sans Arabic or Noto Sans CJK).
- Checkboxes: `"type": "check"` draws a tick and `"type": "cross"` draws an X. Their size is in points. By default x and y are the lower-left corner of the mark's square. Add `"center": true` and give the centre of the box instead, which is easier. For a box typed as `[ ]`, the centre is about halfway between the brackets and 3–4 pt above the baseline. Use a size about 1–2 pt smaller than the box.
- Drawn ticks are graphics, so text extraction still shows `[ ]`. If the recipient's system reads the text layer, use `{"text": "X"}` instead, or `"✔"` with a font that has that glyph.
- To check small marks, zoom in with `pdf_render.py out.pdf --pages 1 --dpi 300 --crop x0,y0,x1,y1`. At the default 110 dpi, a tick 1 pt off looks fine.
- Extracting text from an overlaid page can interleave your text with the underscores below it (`_R_o_o_`). That's expected, so judge placement from the render, not from extracted text.
- For a signature image, use a PNG with a transparent background. Only place a signature the user has provided and asked you to use.

## C. XFA forms

XFA forms store the layout in XML, and most libraries can't fill them. Options, best first:

1. Check whether the form also has AcroForm fields ("N fields" alongside XFA). If it does, fill those with `pdf_forms.py`. Many XFA forms carry both.
2. Ask the user to "Print to PDF" from Adobe Reader, which renders XFA, and send you the static copy. Then use section B.
3. Tell the user that the form needs Adobe Acrobat or Reader to fill reliably.

## Checklist before you hand the form over

- Every required field (`"required": true`) has a value.
- Dates, IDs and numbers match the format printed next to the field.
- You looked at the rendered page, not just the JSON.
- The output file name says it's filled (`*_filled.pdf`). The blank original is untouched.
