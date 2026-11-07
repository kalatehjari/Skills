# Simulated environment for this test

This is a dry run. Don't call the real Dropbox connector, the scheduled-task tools or any other tool that changes something outside your workspace. Treat this file as what those tools would return. Everything here is made up for the test.

## Dropbox (`who_am_i`)

- Signed in as: owner@example.org (personal account). The second account's Claude is connected to the same Dropbox account (checked last week: same email, same file ids).

## Folder tree (`list_folder /Lab Manual/fa-translation`)

```
/Lab Manual/fa-translation/
  TASK.md
  PROTOCOL.md
  README.md
  reference/   units.json, glossary.md, style.md
  source/      ch01.md … ch12.md
  scripts/     check_numbers.py
  drafts/      ch01 … ch07 (.md and .log.md); each log starts "Done by: A (…)" or "Done by: B (…)" from ch06 on
  claims/      ch08.claim (agent: B, claimed 2026-10-14T01:40:12Z)
  additions/   ch02.json  ch04.json  ch06.json
  questions/   ch03.md  ch06.md
  status/      A.md (idle, last_finished ch07)  B.md (working, ch08)
  log/         20261013T222010Z_A_start_-.md
               20261013T222031Z_A_claim_ch06.md
               20261013T224012Z_B_start_-.md
               20261013T224040Z_B_claim_ch07.md
               20261014T005502Z_A_saved_ch06.md
               20261014T005530Z_A_end_-.md
               20261014T012433Z_B_saved_ch07.md
               20261014T012450Z_B_end_-.md
               20261014T014003Z_B_start_-.md
               20261014T014012Z_B_claim_ch08.md
  messages/    20261014T005420Z_A-to-B.md   ("in ch06 I used «نمونه‌ی دست‌نخورده» for 'undisturbed sample'; please keep it")
               20261014T005420Z_A-to-B.md.read-B
```

## `TASK.md` (contents)

```markdown
# Scheduled task: Persian translation of the Soil Mechanics Lab Manual

You are one run of a recurring scheduled task. You have no memory of earlier runs: everything you need is in this Dropbox folder, and progress is recorded only by the files in it. Follow these instructions exactly. Do not ask anyone anything during the run; write questions to files instead (step 7).

**JOB** = `/Lab Manual/fa-translation`. All paths below are relative to JOB.

## What the job is

Translate the twelve chapters of the undergraduate soil mechanics lab manual into clear Persian technical prose. Keep every procedure step, value, unit and safety warning. Tables stay tables. The owner approved `drafts/ch01.md`; it is the model for register and layout.

- **Units:** listed in `reference/units.json` (ch01–ch12). The English for chapter NN is `source/chNN.md`; the draft is `drafts/chNN.md`.
- **Skill:** use the **persian-technical-style** skill. If it is not installed, read the same files from `/Skills/persian-technical-style/` in Dropbox.

## Each run, in order

1. **Load the job.** Read `reference/glossary.md`, `reference/style.md`, and every file in `additions/` and `questions/`. List `drafts/` and `claims/`.
2. **Pick the chapter:** the lowest-numbered chapter with no draft and no fresh claim (less than 3 hours old). None left: create `DONE.md` (step 9) if missing, then stop. A claim older than 3 hours with no draft is stale: delete it and claim the chapter.
3. **Claim it:** create `claims/chNN.claim` containing the current UTC time. If creation fails because the file exists, pick the next chapter.
4. **Prepare:** read the chapter's English in full, and the end of the previous chapter's draft.
5. **Translate** following the style guide and the glossary exactly.
6. **Check:** run `scripts/check_numbers.py` (every number and unit must match the source); check glossary terms.
7. **Save without overwriting:** create `drafts/chNN.md` (only when complete), `drafts/chNN.log.md` (notes, new terms, check results), `additions/chNN.json` (new terms), `questions/chNN.md` (decisions for the owner). Then delete the claim.
8. **Continue or stop:** at most **1 chapter per run**. Never save a partial draft.
9. **When everything is drafted:** create `DONE.md` with a short summary.

## Never
- Edit or delete anything in `source/` or `reference/`, the approved `drafts/ch01.md`, or any existing draft.
- Skip a chapter or summarise instead of translating.
- Ask questions during the run.
- Write outside JOB.
```

## `PROTOCOL.md` (contents)

```markdown
# Coordination protocol for parallel runs

Job: the Persian translation of the soil mechanics lab manual

Two scheduled tasks work on this job at the same time, from the same Dropbox folder:

| Agent | Account | Runs |
|---|---|---|
| **A** | owner's Claude account | hourly at :20 Auckland time |
| **B** | second Claude account | hourly at :40 Auckland time |

Your task prompt tells you which agent you are. Follow this file together with TASK.md. None of this changes how to do the work itself. Where TASK.md and this file differ on coordination (claims, logging, status), this file wins.

## Why it's built from many small files

The Dropbox connector can create files but cannot edit a file in place, and creating a file that already exists fails. So:

- a **claim file** is the lock, because only one agent can create it;
- each agent has its **own status file**, and no one else writes to it;
- the **log** is one new file per event, and its files are never changed;
- **messages** are one new file each.

Never try to keep a single shared file up to date by editing it.

## 0. Run ID and times

At the start of the run, take the current UTC time and make your run ID: `<agent>-<yyyymmddThhmmZ>`, for example `A-20261010T1135Z`. Use UTC everywhere. In file names, write times as `yyyymmddThhmmssZ` (no colons).

## 1. Read the board (with TASK.md's first step)

In addition to what TASK.md asks you to read first:

1. List `claims/`, and read every claim file in it.
2. Read the other agents' status files in `status/`.
3. List `log/` and read the latest ~10 entries.
4. List `messages/`. Read every message addressed to you or to everyone (`…_<from>-to-<you>.md`, `…_<from>-to-all.md`) that has no matching `<message name>.read-<you>` file. Act on it (for example, reuse a term it names), then create that `.read-<you>` file containing your run ID.

Then write a `start` log event (step 4).

## 2. Picking and claiming a chapter

Pick the chapter exactly as TASK.md says. Then create its claim file (the name TASK.md gives, such as `claims/<chapter id>.claim`) with this content:

```
agent: A
run: A-20261010T1135Z
chapter: <id>
claimed_utc: 2026-10-10T11:35:12Z
```

- If creation fails because the file exists, another agent got there first. Go back to TASK.md and pick the next chapter.
- A claim with no `agent:` line was made before this protocol existed. Treat it like any other claim.
- **Fresh or stale:** a claim is stale only when both are true: it is older than the window (TASK.md's window if it gives one, otherwise 3 hours; use `claimed_utc` if present, otherwise the file's modified time), and its holder's status file has not been updated in the last hour. A recent status update means the holder is still working, however old the claim is.
- **Reclaiming a stale claim:** read it first, write a `stale` log event naming the previous holder and run, then delete it and create your own.
- **Never delete a fresh claim**, and never delete someone else's claim unless it is stale.

As soon as your claim succeeds, write a `claim` log event (step 4) and update your status (step 3).

**Attribution:** begin the notes or log file that TASK.md asks you to write for each chapter with the line `Done by: <agent> (<run ID>)`. If TASK.md asks for no such file, put that line in your `saved` log event. Other agents use it to know whose work they are looking at.

## 3. Your status file: `status/<agent>.md`

Only you write your own status file; never touch another agent's. To update it, delete your file, then create it again (if it doesn't exist, just create it). Content:

```
agent: A
run: A-20261010T1135Z
state: working | idle | done
chapter: <id>        (or - when idle)
updated_utc: 2026-10-10T11:36:02Z
last_finished: <id> at 2026-10-10T11:20:44Z
note: one short line
```

Update it right after claiming a chapter, right after saving one, and at the end of the run (`idle`, or `done` if nothing is left). If a chapter takes long, also refresh it between major steps, at least once an hour: that is how other agents can tell you're still working (step 2).

## 4. The log: `log/`

For each event, create one new file named `<yyyymmddThhmmssZ>_<agent>_<event>_<chapter id or ->.md`, for example `log/20261010T113512Z_A_claim_u03.md`. Content: your run ID plus one or two lines (what happened, file names). Never edit or delete a log file.

| Event | When |
|---|---|
| `start` | start of run, after reading the board |
| `claim` | you claimed a chapter |
| `stale` | you reclaimed a stale claim (name the old holder) |
| `saved` | output and notes saved, claim deleted |
| `question` | you wrote a question for the owner in `questions/` |
| `proposal` | you proposed a new term or decision for approval |
| `message` | you sent a message to another agent |
| `error` | something failed and you couldn't finish a chapter (say what) |
| `end` | end of run (chapters finished this run) |

## 5. Messages between agents: `messages/`

Messages are for coordination that can't wait. Create `messages/<yyyymmddThhmmssZ>_<from>-to-<to>.md`, where `<to>` is an agent letter or `all`, for example `messages/20261010T114210Z_A-to-B.md`. Use it for:

- a term or decision another agent should follow, especially if you saw it choose differently for the same thing;
- a continuity point (for example: "in u05 I named the café X; keep it in u06").

Messages are never for the owner. Anything that needs the owner's decision goes to `questions/`, as TASK.md says.

## 6. Shared decisions and continuity

- **Just before saving,** list the folder where TASK.md keeps new terms or decisions (such as `additions/`) again. If another agent chose something since you started that covers part of your work, use its choice.
- If your chapter follows one another agent hasn't finished yet (for example, the previous part of the same chapter), work from the source, say so in your notes, and send that agent a short message listing the names, terms and recurring details you introduced, so the seam can be checked.

## 7. End of run (with TASK.md's last steps)

After saving each chapter: delete your claim, write a `saved` event, update your status.

When you stop working:

1. Write an `end` event and set your status to `idle` (or `done`).

**DONE.md:** only one agent can create it, because creating fails if it already exists. If it already exists, write your `end` event, set your status to `done`, and stop.
```

## Scheduled tasks in this account (`list_triggers`)

- **Lab manual Persian translation** (agent A): id `trig_LAB01`, cron `CRON_TZ=Pacific/Auckland 20 * * * *`, enabled, permission_mode auto, notifications off, cloud only. Next run 2026-10-14T02:20:00Z. Prompt:

```
Continue the job: the Persian translation of the soil mechanics lab manual.

YOU ARE AGENT A. Another scheduled task, agent B (second Claude account), works on this job at the same time from the same Dropbox folder.

JOB FOLDER: /Lab Manual/fa-translation

Using the Dropbox connector, read these files in the job folder and follow them exactly:
1. TASK.md: the job, and how to do it.
2. PROTOCOL.md: how the agents coordinate through claims/, status/, log/ and messages/ so no two agents do the same work. Where the two differ on coordination, PROTOCOL.md wins.

You have no memory of earlier runs. Progress lives only in the files in the job folder.

Rules for this run:
- Do at most 1 chapter.
- Save everything inside the job folder and write nothing outside it. Never overwrite or edit existing files, except as TASK.md and PROTOCOL.md allow: delete and re-create your own status/A.md, delete your own claim files, and delete stale claims after logging them.
- Creating files and folders in the job folder, and those deletions, are pre-approved, so don't stop to confirm them.
- Don't ask any questions; no one is there to answer. Write any question that needs the owner's decision to questions/, as TASK.md describes, and carry on.
- Use the persian-technical-style skill as TASK.md directs. If it isn't installed in this account, read its files from /Skills/persian-technical-style/ in Dropbox.
- If all the work is done and DONE.md exists, write your end log event, set status/A.md to done, and stop.
```

## The second account (agent B)

- Its scheduled task runs hourly at :40 Auckland time with the same prompt, except "YOU ARE AGENT B" and status/B.md. Next run 2026-10-14T02:40:00Z.
- You can't change that task from here; the user can paste messages into that account.

## The user

- Time zone: Pacific/Auckland. It's 2026-10-14T01:55Z now.
