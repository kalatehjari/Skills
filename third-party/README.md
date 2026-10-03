# Third-party skills

These skills were written by others and are included here, unmodified, under their open-source licences. Each folder keeps its original `LICENSE`/`LICENSE.txt` (and `NOTICE.md` where the upstream has one). Use, modify and redistribute them under those terms.

| Skill | Upstream | Licence | Snapshot |
|---|---|---|---|
| [skill-creator](anthropic/skill-creator) | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/skill-creator) | Apache-2.0 | `8a1541c` (2026-09-28) |
| [web-artifacts-builder](anthropic/web-artifacts-builder) | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/web-artifacts-builder) | Apache-2.0 | `8a1541c` |
| [webapp-testing](anthropic/webapp-testing) | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/webapp-testing) | Apache-2.0 | `8a1541c` |
| [algorithmic-art](anthropic/algorithmic-art) | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/algorithmic-art) | Apache-2.0 | `8a1541c` |
| [canvas-design](anthropic/canvas-design) | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/canvas-design) | Apache-2.0 (bundled fonts: SIL OFL, licences inside `canvas-fonts/`) | `8a1541c` |
| [internal-comms](anthropic/internal-comms) | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/internal-comms) | Apache-2.0 | `8a1541c` |
| [mcp-builder](anthropic/mcp-builder) | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/mcp-builder) | Apache-2.0 | `8a1541c` |
| [avoid-ai-writing](conorbronsdon/avoid-ai-writing) | [conorbronsdon/avoid-ai-writing](https://github.com/conorbronsdon/avoid-ai-writing) | MIT | `bdeb726` |

## Not included, on purpose

Anthropic's `docx`, `pdf`, `pptx` and `xlsx` skills are **source-available, not open source**. Their licence forbids copying, redistribution and derivative works, so they are not in this repository. The `*-workbench` skills in [`../skills`](../skills) are independent replacements, written from scratch under MIT.

## avoid-ai-writing: what's included

The canonical skill directory only: `SKILL.md`, `references/`, `scripts/`, `detector/`, `examples/`, plus `LICENSE`, `NOTICE.md` and the upstream `README.md`. The upstream repo's packaging for other platforms (ChatGPT/Codex plugin, Cursor rules, corpus, CI) is left out. Get it from the upstream repo if you need it.

## Updating a snapshot

```bash
git clone --depth 1 https://github.com/anthropics/skills /tmp/anthropic-skills
rsync -a --delete /tmp/anthropic-skills/skills/<name>/ third-party/anthropic/<name>/
# then update the commit hash in the table above
```
