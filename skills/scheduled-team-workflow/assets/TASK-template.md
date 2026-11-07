# Scheduled task: <job name>

<!-- How to use this template: replace every <…> with the job's details, agreed with the owner, and delete what doesn't apply. Keep the numbered steps. Scheduled runs and the coordination protocol depend on them (claims in step 3, saving only finished units in step 7, the done file in step 9). Delete this comment. -->

You are one run of a recurring scheduled task. You have no memory of earlier runs: everything you need is in this Dropbox folder, and progress is recorded only by the files in it. Follow these instructions exactly. Do not ask anyone anything during the run; there is no one to answer. Write questions to files instead (step 7).

**JOB** = `<Dropbox path of this folder>` (Dropbox, via the Dropbox connector). All paths below are relative to JOB.

## What the job is

<Two to five sentences: what the job produces, the quality bar, and which approved example (if any) is the model for voice, format and layout. Say to read the example before doing any work.>

- **Units:** listed in `reference/units.json` (id, input file, output file name). The input for a unit is `source/<file>`, and its output uses <the same file name> in `<outputs folder>/`.
- **Skill:** use the **<skill name>** skill. Read its SKILL.md, then <the references that matter most>. If the skill is not installed, read the same files from `<Dropbox path of the skill folder>`.

## Each run, in order

### 1. Load the job
If `PAUSE.md` exists in JOB, stop at once without writing anything: the owner has paused the job. If `DONE.md` exists, the job is finished: stop.

Otherwise, read these files:
- <reference files with the owner's decisions: style sheet, glossary, codebook, background>
- every file in `additions/` and `questions/` (decisions and proposals so far)

Then list the files in `<outputs folder>/` and `claims/`.

### 2. Pick the unit
The next unit is the lowest-numbered unit that has no output in `<outputs folder>/` and no fresh claim in `claims/` (less than <3> hours old).
- **No unit left:** if every unit has an output, create `DONE.md` (step 9) and stop. If the only units left have fresh claims, another run is working on them: stop without creating `DONE.md`.
- **Stale claim:** a claim older than <3> hours with no output is stale. Delete it and claim the unit yourself.

### 3. Claim it
Create `claims/<unit id>.claim` containing the current UTC time. The connector cannot create a file that already exists. If creation fails because another run claimed the unit first, go back to step 2 and pick the next one.

Right after the claim succeeds, list `<outputs folder>/` again. If the unit's output now exists, another run finished it meanwhile: delete your claim and go back to step 2.

### 4. Prepare
Read the unit's input in full. <Context to read for continuity: the previous unit's input and output, or at least its end.> If you have code execution, copy <the checking scripts and data> into your workspace so you can run the checks in step 6.

### 5. Do the work
<How to do one unit, as rules in priority order, each with its reason. Include the output's header line, its format and layout, names and terms (from the glossary, exactly), and how to mark and log anything added or interpreted.>

### 6. Check
- <Automated check 1: command, and what must pass>
- <Automated check 2>
- **Without code execution:** do the same checks by reading, against <reference>.

### 7. Save, without overwriting anything
Create these files with the Dropbox connector:
- **`<outputs folder>/<output file name>`:** the finished output. Create it only when the unit is complete.
- **`<outputs folder>/<name>.log.md`:** the unit's notes: additions and why, cuts and significant changes, interpretations of anything ambiguous, new terms, check results.
- **`additions/<unit id>.json`:** only if you chose new terms or decisions that later runs must reuse: `[{"term": "...", "choice": "...", "note": "..."}]`.
- **`questions/<unit id>.md`:** only if a decision needs the owner. For each question: the passage, the choice you made, and the alternatives. Never stop to wait for an answer.

Then delete `claims/<unit id>.claim`.

### 8. Continue or stop
Do at most **<N> units per run**. If you have done fewer and have room left, go back to step 2. Otherwise stop. If a run is cut off before step 7, its claim goes stale and a later run redoes the unit. Never save a partial output.

<Optional assembly rule, for example: when every unit of a chapter exists, create `<outputs folder>/chNN_full.md` by joining them in order.>

### 9. When everything is done
Create `DONE.md`, a short summary:
- units done;
- assembled files;
- the number of open questions, with links to the files;
- new terms or decisions waiting for approval;
- anything the owner should read first.

## Never
- Edit or delete anything in `source/` or `reference/`, the approved example, or any existing output.
- <Job-specific never-rules, for example: skip a unit, summarise instead of doing the work, translate word for word.>
- Ask questions during the run (write them in `questions/`).
- Write outside JOB.
