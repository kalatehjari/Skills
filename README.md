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
| [scheduled-team-workflow](skills/scheduled-team-workflow) | Runs a long job from a Dropbox folder as recurring Cowork scheduled tasks, unit by unit. Scales to several agents or Claude accounts without double work (claim, status, log and message files) and adds peer learning (retros, reviews, digests). Includes a script that writes the protocol, prompts and setup messages | v1.0, smoke-tested; 3 evals run |
| [pen-and-ink-game-builder](skills/pen-and-ink-game-builder) | First-person 3D browser games drawn as living pen-and-ink etchings, in one offline HTML file: crosshatch renderer with boiling lines, doors that open straight onto the next level, Escher rooms where walls become floors, keyboard, touch and gamepad, synthesized sound. Starts from a playable three-level game; 8 tested scripts (new game, build, screenshots, robot playtest, trailer filming, offline soundtrack, finishing at -14 LUFS with a store GIF) | v1.0, smoke-tested; 3 evals run |
| [observer-multi-lens-reasoning](skills/observer-multi-lens-reasoning) | The Observer method for complex, ambiguous or high-stakes questions: five lenses (analytical, creative, critical, systems, pragmatic) each reason separately, then a higher-order observer compares them and gives one recommendation with a confidence score. Case study and self-improvement record: [kalatehjari/Observer](https://github.com/kalatehjari/Observer) | v1.0 |
| [farsi-scifi-builder](skills/farsi-scifi-builder) | Write, revise and worldbuild Persian (Farsi) science fiction that reads as native literary prose: formal narration, natural colloquial dialogue, coined SF terms, edits for translationese and orthography (نیم‌فاصله, ی/ک, « »), and adaptation of English drafts | v1.0, smoke-tested |
| [audiobook-narrator](skills/audiobook-narrator) | Chapter of fiction → speaker-tagged narration script, one Kokoro TTS voice per character, rendered chapter MP3 with exact punctuation pauses, or an in-browser narrator page | first release |
| [music-video-director](skills/music-video-director) | Story-driven, hand-drawn animated music video (16:9 by default) for your own song, starring a character designed from reference photos | first release |
| [cubism-animator](skills/cubism-animator) | Cubist / avant-garde animated films and music videos: the character drawn as planes of colour, lines and shapes, cut to the beats of your song | first release |
| [vinyl-groove-visualiser](skills/vinyl-groove-visualiser) | Music visualiser where the camera flies through the grooves of a spinning record carved by your song (stereo walls, bass waves, kick-synced light rings) | first release |

These are released under the MIT licence. Each skill folder has its own `LICENSE`.

## Third-party skills (`third-party/`)

These are open-source skills by others, included unmodified with their licences. See [third-party/README.md](third-party/README.md) for the sources and snapshot commits.

- **Anthropic (Apache-2.0):** skill-creator, web-artifacts-builder, webapp-testing, algorithmic-art, canvas-design, internal-comms, mcp-builder
- **Conor Bronsdon (MIT):** avoid-ai-writing
- **iart-ai (MIT):** 54 motion-graphics skills; get them from [iart-ai/motion-skills](https://github.com/iart-ai/motion-skills) (not mirrored here)

## Installing a skill

**Claude apps (claude.ai or desktop):** zip the skill folder so the zip contains `pdf-workbench/SKILL.md`. Then upload it under *Settings → Capabilities → Skills*. Ready-made zips are in `dist-console/` (original skills) and `dist/` (third-party).

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
dist-console/             installable zips of original skills (tools/package_md.py --zip)
dist-md/                  single-file .md builds of original skills (tools/package_md.py)
dist/                     installable zips of third-party skills (tools/package.py)
docs/conventions.md       naming and structure rules for new skills
```

## Adding a new skill

Follow [docs/conventions.md](docs/conventions.md). In short: use a kebab-case name, put a "when to use" description in the frontmatter, add tested scripts, include an `evals/` folder, and add a row to the table above.
