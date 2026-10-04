# Skills

Agent Skills for Claude, developed and maintained by Roohollah Kalatehjari ([@kalatehjari](https://github.com/kalatehjari)) at GEOTECH-LAB, Auckland University of Technology.

A skill is a folder with a `SKILL.md` file. The file starts with YAML frontmatter, then gives instructions, and the folder can also hold scripts and reference files. Claude loads a skill when the task matches its description. See [agentskills.io](https://agentskills.io) for the format.

## Original skills (`skills/`)

| Skill | What it does | Status |
|---|---|---|
| [pdf-workbench](skills/pdf-workbench) | Read, extract (text, tables, figures, DOIs), edit, fill forms, OCR and create PDFs. Has 9 tested Python scripts and tips for research papers | v1.0, tested |
| [docx-workbench](skills/docx-workbench) | Create, fill (templates, mail merge), edit, review (tracked changes and comments), compare and convert Word documents. Reports come from Markdown with a cover page, TOC and page numbers. Has 10 tested scripts | v1.0, tested |
| [xlsx-workbench](skills/xlsx-workbench) | Read, build, check and edit Excel workbooks. Formulas that really calculate (LibreOffice recalc with cached values), audits for errors, overwritten formulas and suspicious data, formatted tables, native charts including depth profiles, diffs and conversions. Has 8 tested scripts | v1.0, tested |
| [pptx-workbench](skills/pptx-workbench) | Markdown outline to a clean 16:9 deck, or to one in your template, with native bullets, tables, editable charts, figures and speaker notes. Also QA checks (overflow, fonts, alt text, low-res or duplicate images, leftovers), contact-sheet renders, fill and replace, and slide reordering and merging. Has 7 tested scripts | v1.0, tested |
| [arena-supreme](skills/arena-supreme) | ArenaSupreme: a lean, budgeted, checkpointed arena. Runs 2–3 parallel candidates, cross-judges them on a different model, then picks a base, grafts the best of the others in and verifies by script. Includes the token-cost model, lean-helper and brief templates, and 5 tested scripts (quote and figure checks, digest builder, Bradley–Terry aggregation, usage meter). Install prompt: `Copy Me ArenaSupreme.txt` | v1.0, smoke-tested |

These are released under the MIT licence. Each skill folder has its own `LICENSE`.

## Third-party skills (`third-party/`)

These are open-source skills by others, included unmodified with their licences. See [third-party/README.md](third-party/README.md) for the sources and snapshot commits.

- **Anthropic (Apache-2.0):** skill-creator, web-artifacts-builder, webapp-testing, algorithmic-art, canvas-design, internal-comms, mcp-builder
- **Conor Bronsdon (MIT):** avoid-ai-writing

## Installing a skill

**Claude apps (claude.ai or desktop):** zip the skill folder so the zip contains `pdf-workbench/SKILL.md`. Then upload it under *Settings → Capabilities → Skills*. Ready-made zips are in `dist/`.

**Claude Code:** copy or symlink the folder into `~/.claude/skills/` (personal) or `.claude/skills/` (project):

```bash
git clone https://github.com/kalatehjari/Skills
ln -s "$PWD/Skills/skills/pdf-workbench" ~/.claude/skills/pdf-workbench
```

**API:** upload the folder with the Skills API. See the [Skills guide](https://docs.claude.com/en/api/skills-guide).

## Repository layout

```
skills/<name>/            original skills (MIT)
  SKILL.md                frontmatter + instructions (kept under ~500 lines)
  scripts/                standalone, tested helper scripts
  references/             detailed docs loaded only when needed
  evals/                  test prompts, sample files, smoke tests
  LICENSE
third-party/<author>/<name>/   unmodified upstream skills with their licences
dist/                     installable zips (rebuild with tools/package.py)
docs/conventions.md       naming and structure rules for new skills
```

## Adding a new skill

Follow [docs/conventions.md](docs/conventions.md). In short: use a kebab-case name, put a "when to use" description in the frontmatter, add tested scripts, include an `evals/` folder, and add a row to the table above.
