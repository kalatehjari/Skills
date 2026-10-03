# Conventions for skills in this repository

These rules keep the collection consistent so every skill installs, triggers and behaves the same way.

## Naming

- The folder name and the `name:` field match, and use lowercase kebab-case (`pdf-workbench`, `borehole-log-parser`).
- Name the skill after what it works on, plus a suffix for the kind of skill:
  - `-workbench` for a general toolkit for one file type (pdf, docx, xlsx, pptx).
  - `-builder` when it produces one kind of artefact (`report-builder`).
  - `-review` or `-check` for auditing or QA workflows.
  - `-workflow` for a repeatable multi-step procedure taken from real work.
- Don't put `claude` or `anthropic` in a name, and don't reuse the name of a built-in skill (`pdf`, `docx`, `xlsx`, `pptx`), so they don't clash.

## Folder layout

```
<name>/
├── SKILL.md          required
├── LICENSE           MIT for original skills
├── scripts/          standalone CLIs: argparse, --help, never overwrite inputs
├── references/       one topic per file, each self-contained, table of contents if >100 lines
├── assets/           templates, fonts, images used in outputs (optional)
└── evals/
    ├── evals.json    3–5 realistic prompts with expected outputs
    ├── files/        small sample inputs for the prompts
    └── smoke_test.py runs every script on the samples; must pass before release
```

## SKILL.md

- Frontmatter has `name`, a `description` and `license`.
  - The description says what the skill does **and** when to use it. Include the phrases users actually type, and make it slightly "pushy" so the skill triggers reliably.
- The body is under about 200 lines. Start with a short decision table (goal, tool, reference), followed by the working principles and their reasons. Keep detail in `references/`.
- Paths are relative to the skill folder. Say so near the top.
- Explain *why* a rule matters instead of writing ALWAYS or NEVER in capitals.

## Scripts

- Every script runs on its own. The one exception is a single `_<skill>_common.py` helper in the same folder, imported via the script's own directory, for logic several scripts need. Dependency errors give a clear `pip install …` hint.
- Scripts set `sys.dont_write_bytecode = True` before importing a helper, so `__pycache__` never appears inside the skill folder.
- Without `-o`, outputs go next to the input file. They never go to the current directory, which might be the skill folder.
- Results go to a new file (`-o`). A script refuses to overwrite its input.
- Page, row and slide numbers are 1-based in every interface.
- Scripts print a short summary to stderr, and data to stdout or a file.

## Quality bar before release

1. `python evals/smoke_test.py` passes.
2. At least 3 eval prompts have been run by a fresh agent using only the skill, and the problems it found have been fixed.
3. Reference snippets have been executed, not just written.
4. A row has been added to the README table, and the zip in `dist/` rebuilt.

## Third-party skills

- Include only skills under an open licence (MIT, Apache-2.0, BSD and similar). Keep their licence and notice files, don't modify them, and record the upstream commit in `third-party/README.md`.
- Source-available skills (for example, Anthropic's docx, pdf, pptx and xlsx) can't be copied or adapted. Write an independent replacement instead, without looking at their text.

## Turning a conversation into a skill

When a workflow in a chat turns out to be useful and repeatable:

1. Write down the trigger: what the user asked for, the inputs and the output format.
2. Pull out the steps that actually worked, and the corrections the user made along the way.
3. Turn any code that had to be written more than once into a script.
4. Name it using the rules above, scaffold the folder, write the evals, and test it.
5. Save it to the Dropbox `Skills` folder and push it to `kalatehjari/Skills`.
