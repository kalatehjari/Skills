# ArenaSupreme templates

Copy these and fill in the `<…>` slots.

## 1. Lean agent definition

Save this as `.claude/agents/arena-lean.md`, wherever the host reads agent definitions. It takes effect from the next session.

Measured effect: the helper's entry context dropped from about 80k tokens to **17k**.

```markdown
---
name: arena-lean
description: Lean worker for arena jobs (read files, judge, write one report). File tools only, no connectors or browser.
tools: Read, Write, Edit, Bash, Grep, Glob
---
You are a careful analyst working on one bounded job. Use only the files named in your task.
- Read large texts in as few calls as possible (whole files, or one batched cat), never piece by piece.
- Issue independent reads in parallel in a single step.
- Do not re-read a file you already have; use grep for spot checks.
- Write your output early as a complete draft, then improve it in place.
- If the Write tool refuses a path, write the file with a quoted Bash heredoc.
- Finish with a short final message: the output path and the one-line result your task asks for.
```

## 2. `ARENA_STATE.json`

```json
{
  "run": "<task>, started <date time TZ>",
  "output_location": "<durable folder>",
  "user_rules": ["never delete", "duplicates get _#", "update the index after saving"],
  "usage_rule": "<e.g. pause at 10% left, resume after reset>",
  "budget": {"estimate_M": "<range>", "phase_start_utc": {}},
  "phases": {
    "preflight": {"status": "done"},
    "ground": {"status": "pending", "outputs": [], "cost_M": null},
    "frame": {"status": "pending", "outputs": ["ARENA_FRAME.md", "NUMBERS.md", "DIGEST_*.md"]},
    "fan_out": {"status": "pending", "candidates": {"1_<stance>": {"status": "pending"}, "2_<stance>": {"status": "pending"}}},
    "cross_judge": {"status": "pending"},
    "pick": {"status": "pending"},
    "graft": {"status": "pending"},
    "verify": {"status": "pending"},
    "deliver": {"status": "pending"}
  }
}
```

## 3. Evidence-reader brief (blind whole-text reader)

```markdown
# BRIEF: cold read of <the work>

You are one of several independent readers. Work only from this brief and the folder named in your task message. Read nothing else.

## How to read (lean)
- Read the whole text, in order, in at most <5> calls: one Bash `cat` per part.
- Keep no notes file. Score only after you have finished.
- Write your report in ONE call, then make at most one revision pass.

## Your stance
You are hard to impress. AI readers are systematically too kind: a 7 means good and publishable with work, and a 9 is rare. Every claim needs evidence from the text.

## Produce (one Markdown file, about 2,500–3,500 words)
1. Header: persona, start and finish time, and which parts you read.
2. Brief summary (150 words or fewer).
3. Scores, 1–10, on <dimensions>, using the rubric anchors. For each score give at least 3 pieces of evidence, including at least 1 weakness.
4. The three weakest scenes and the three strongest scenes.
5. The gate questions: <questions>.
6. A ranking against <comparison works>.
7. Five to eight recommendations, ordered by impact.
8. A verdict.

Final message: the report path, your scores and average on one line, and your rank.
```

## 4. Scene-judge brief (blind matched passages)

```markdown
# BRIEF: blind comparison of three drafts of one scene

Your folder holds SCENE.txt and version_X.md, version_Y.md and version_Z.md. The labels are random. Read only this brief and your folder.

1. In ONE Bash call, `cat` the brief and all four files.
2. Judge each draft as a scene in a published book.
   - Length is not a merit in itself.
   - Guard against position bias.
   - Be hard to impress.
3. Score each version 1–10 on: prose, emotion, clarity, restraint, job.
4. For each pair (X–Y, X–Z, Y–Z), name a winner with a margin from 1 to 3. No ties. Quote evidence, under 15 words per quote.
5. Write ONE file containing the pairs, the scores, a ranking, the best sentence and one sentence to cut per version, and a JSON block:
   {"set": "<name>", "pairs": [{"a": "X", "b": "Y", "winner": "?", "margin": 0}], "scores": {"X": {}}, "ranking": []}

Final message: the path and your ranking on one line.
```

Two judges per passage, each with a different random label order. Keep `KEY.json` (label → version) outside the judges' folders.

## 5. Candidate brief

```markdown
# Brief: <artifact>

## Task
<who it is for; the decision it serves; the house format to follow>

## Read exactly these, once
In ONE Bash call, `cat`: README.md, NUMBERS.md, DIGEST_part1.md … (each 40k characters or less).
For anything else, use at most two batched `grep -n` calls across <sources>. Read nothing else.

## Step budget (about 8–12 tool calls)
1. Read the grounding (1 call).
2. Make up to 2 grep calls.
3. Write the artifact in 2–3 sections, each its own quick call.
4. Run the checkers:
   python3 scripts/verify_quotes.py OUT.md --sources "<globs>"
   python3 scripts/check_numbers.py OUT.md --refs NUMBERS.md
   Fix what they flag, in at most 1 revision call.
5. Write RATIONALE.md (400 words or less): why this structure, which alternatives you rejected and why, and what in the evidence is ambiguous.

## Must contain
<sections>

## Rules
- Use only figures from NUMBERS.md, or recomputations you show.
- Quotations must be verbatim, with each source named.
- <user rules: sensitivity, naming, restore-first, …>

Final message: the output folder, your conclusion, the word count, and one sentence on your structure.
```

Give each candidate a one-paragraph stance: planner (built around the decision), reviewer (built around the evidence and its reliability) or designer (built around the reader's experience, and tightest).

## 6. Cross-judge brief

```markdown
You are the read-only cross-judge. STEP BUDGET: 3 tool calls.
Step 1: in ONE message, Read each candidate's OUT.md in parallel, plus one Bash `cat` of every RATIONALE.md, CHECKER_OUTPUT.md and NUMBERS.md.
Step 2: write JUDGE.md in ONE call.
Step 3: final message.

Rubric (score each criterion 1–10 per candidate): <R1…R6 with concrete tests>.

JUDGE.md must contain:
- the score table and totals;
- 2 strengths and 2 weaknesses per candidate, with section numbers;
- the recommended base and why;
- 1–3 grafts from each loser, with section numbers;
- any errors found;
- whether the candidates converge.

Be hard to impress, and separate substance from style.
Final message: the path, the recommended base, and the totals on one line.
```

## 7. `SYNTHESIS_NOTE.md`

```markdown
# Arena synthesis note: <task>
## Candidates: role · conclusion · checker result · words · status (and any dropouts)
## Cross-judge: score table, recommended base, errors found
## Pick: my score table · base · reason
## Grafts: <item> (from candidate n) …
## Rejections, and why: <item>: <reason> …
## Verification: quotes n/n verbatim · figures checked · manual checks · items removed as unverifiable · render checked
## Measured cost: phase · estimate · actual · why it differed
```
