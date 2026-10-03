# Journal articles, theses and technical reports

Tasks that come up often with academic PDFs: pull out the bibliographic details, read the abstract and sections, extract data tables and figures, build a reference list, or compare several papers.

## Contents
1. Bibliographic details (title, authors, DOI, year)
2. Sections: abstract, methods, conclusions
3. Reference lists
4. Tables and figures with their captions
5. Working across many papers
6. Accuracy rules

## 1. Bibliographic details

```bash
python scripts/pdf_inspect.py paper.pdf --json   # metadata + "dois_found"
```

Metadata is often empty or wrong. Publishers frequently leave a production filename in `/Title`. Use this order of precedence:

1. **DOI.** The first DOI on page 1 is usually the article's own. Later DOIs belong to cited works.
2. **Title.** This is usually the text in the largest font on page 1:
   ```python
   import pdfplumber
   from collections import defaultdict
   with pdfplumber.open("paper.pdf") as pdf:
       p = pdf.pages[0]
       lines = defaultdict(list)
       for ch in p.chars:
           lines[(round(ch["top"]), round(ch["size"], 1))].append(ch)
       biggest = max(size for (_, size) in lines)
       title = " ".join("".join(c["text"] for c in sorted(chs, key=lambda c: c["x0"]))
                        for (top, size), chs in sorted(lines.items()) if size >= biggest - 0.5)
   ```
3. **Authors, journal, year.** Read these from the page-1 header text. Don't guess from the filename.

When the session has web access, resolve the DOI to get authoritative metadata. Use `https://doi.org/<DOI>` with the header `Accept: application/vnd.citationstyles.csl+json`, or the Crossref API. Report any mismatch with what the PDF shows.

## 2. Sections

Extract the text first. Use `--columns 2` on the body pages of two-column journals (see reading-and-extraction.md, section 2). Then split it on heading patterns:

```python
import re
text = open("body.txt", encoding="utf-8").read()
heads = re.compile(r"^\s*(?:\d+(?:\.\d+)*\.?\s+)?(Abstract|Introduction|Background|Methods?|Methodology|"
                   r"Materials and methods|Results|Discussion|Conclusions?|References|Bibliography|"
                   r"Acknowledg(?:e)?ments)\s*$", re.I | re.M)
marks = [(m.start(), m.group(1).title()) for m in heads.finditer(text)]
sections = {name: text[s:(marks[i + 1][0] if i + 1 < len(marks) else len(text))].strip()
            for i, (s, name) in enumerate(marks)}
```

Headings vary by journal ("2. Experimental programme", "Concluding remarks"). If the pattern misses some, list the candidate heading lines before you split. These are short lines in Title Case or with a section number, often bold, which you can check with `page.chars[i]["fontname"]`.

The abstract often has no heading. In that case, take the paragraph between the author block and "Keywords" or "1. Introduction".

On two-column journals, the abstract is usually on page 1, under a full-width title block. Read that page with `--columns 2 --header PT` so the title stays whole and the columns don't interleave. When the abstract itself is full width, which is common, use no `--columns` on page 1 at all. Render page 1 to see which layout you're dealing with.

If the request is ambiguous ("without the other column mixed in" could mean de-interleaved, or one column only), give the most likely reading and say how you read it.

## 3. Reference lists

1. Isolate the text after the last "References" or "Bibliography" heading.
2. Split it into entries:
   - Numbered styles start lines with `[12]` or `12.`. Split on `^\s*\[?\d+[\].]\s`.
   - Author–year styles (Harvard or APA) start each entry with `Surname, X.` or `Surname X`. Split where a new line starts with a capitalised surname followed by initials, and the line before ended with a full stop or a DOI.
3. Re-join hyphenated line breaks (`consoli-\ndation` becomes `consolidation`), but keep real hyphens in compounds ("stress-strain").
4. Pull out DOIs with `10\.\d{4,9}/\S+`, and strip trailing `.,;)`.

Return the result in the format the user wants (a list, BibTeX, RIS or a CSV table). Mark any entries you couldn't parse cleanly rather than quietly dropping them.

## 4. Tables and figures with their captions

- **Tables.** `python scripts/pdf_tables.py paper.pdf --pages N --strategy text`. Journal tables are usually borderless, so use the text strategy. The script finds "Table N …" captions above or below each table. It reports them on screen and in the md and json output. In xlsx output they go on an `Index` sheet. It also lists any cell where a comma was read as a thousands separator ("2,000.5" became 2000.5). Check those against the column's scale, because a decimal comma or a typo is often more likely.
- **Figures.** Embedded photos and micrographs come out with `pdf_images.py`. Plotted charts are vector graphics, so render and crop them instead (reading-and-extraction.md, section 5). Captions sit below the figure.
- **Values read off a chart are estimates.** If the user wants data digitised from a plot, say it's approximate. Give the axis calibration you used and the estimated precision.

## 5. Working across many papers

For literature reviews and comparison tables:

1. Run `pdf_inspect.py --json` on every file first. Note which are scans (they need OCR) and which are encrypted.
2. Extract each paper to its own `.txt` file, with page markers kept for citation.
3. Build the comparison as a table: one row per paper, with columns such as material, test type, sample size, key parameters, main finding, and page reference.
4. Cite page numbers for every extracted claim ("p. 7"), so the user can check them.

## 6. Accuracy rules

- Quote numbers exactly as printed, with units. Keep the paper's symbols (φ′, c′, σ′v, e₀) and note any normalisation you made.
- Never fill gaps from memory. If a value isn't in the PDF, say so.
- Separate what the paper reports from your interpretation.
- OCR'd pages, interleaved columns and tables split across pages are the usual sources of error. Say which of these affected the extraction.
