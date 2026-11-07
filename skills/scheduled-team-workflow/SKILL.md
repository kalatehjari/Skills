---
name: scheduled-team-workflow
description: Run a long job that won't fit in one session (adapting or translating a book unit by unit, working through a folder of transcripts, papers, data or documents) as a recurring Cowork scheduled task that works from a Dropbox folder with no memory between runs. Scale it to several agents or Claude accounts working in parallel without double work, using claim, status, log and message files in Dropbox. Have the agents learn from each other through retros, peer reviews and a shared lesson digest. Use this whenever the user wants Claude to keep working on something every hour or overnight, "continue the job" on a schedule, add another account or agent to share the work, set up a coordination or communication protocol between agents, stop agents duplicating work, find out why two agents did the same unit, or have agents give each other feedback, even if they never say "scheduled task", "protocol" or "Dropbox".
license: MIT
---

# Scheduled team workflow

Paths in this file are relative to the skill folder. If only this SKILL.md was installed, read the other files from Dropbox at `/Claude Products/Skills/skills/scheduled-team-workflow/`.

Some jobs are too big for one session, like adapting a novel or coding sixty interviews. Run them as a Cowork scheduled task. Each run is a fresh session: it reads the job's instructions and progress from files in a Dropbox folder, does a bounded amount of work, saves it as new files and stops. All state lives in those files, so more agents (including agents in other Claude accounts) can work the same folder at once. They coordinate through files the Dropbox connector can safely create.

## What do you need?

| Goal | Do this | Read or use |
|---|---|---|
| Put a long job on a schedule | Check the folder and TASK.md, create the task with a standalone prompt, start the first run | `references/scheduled-task.md` |
| Write TASK.md for a new job | Fill the template with the user: units, inputs, outputs, checks, never-rules | `assets/TASK-template.md` |
| Add another agent or Claude account | Prove both see the same files, give the other account its prompt, offset the schedules | `references/parallel-agents.md` |
| Stop agents doing the same work | Install PROTOCOL.md: claims, status, log, messages | `references/coordination.md`, `scripts/make_job_kit.py` |
| Have agents learn from each other | Install PEER.md: retros, peer reviews, digest | `references/peer-learning.md` |
| Change the rules while tasks run | Replace the file every prompt already points to, between runs | `references/coordination.md` (changing the rules) |
| Fix double work, stalled runs or silence | Read claims/, status/, log/ and the run history | `references/troubleshooting.md` |
| See a complete real setup | Two accounts adapting a novel into Persian | `references/example-had-e-momken.md` |

## Working principles

### 1. Every run starts from zero, so the folder is the memory

A scheduled run is a new session. It can't see this conversation or earlier runs. Everything it needs lives in the job folder: `TASK.md` says what to do and how, reference files hold the owner's decisions, and progress is simply which output files exist. Keep the task prompt short and point it at `TASK.md`. Then a fix to the instructions is one file edit, not a prompt change in every account. A run that dies midway loses only its own unit.

### 2. Bound every run

Cap the work per run, for example one or two units for heavy work like drafting a chapter, so a run finishes inside its time limit. Save a unit only when it is complete. Unit boundaries are the only save points, so a cut-off run leaves nothing half-done for the next run to trip over.

Scheduled runs use the same account's usage as the user's own chats. Heavy hourly runs can use up a session limit and cut off the user's interactive work. Say so when you set one up, and size the cap with it in mind. A second account brings its own usage.

### 3. Unattended means no questions and no waiting

Nobody is there to answer. Runs write questions to `questions/`, state the choice they made, and carry on. The prompt pre-approves the exact actions runs need, such as creating files in the job folder and deleting their own claims. Check the approval setting the task got: if it isn't automatic, runs stall at the first file save, so tell the user how to switch it.

### 4. Create new files; never edit shared ones

The Dropbox connector can create a file but not edit it, and creating a file that already exists fails. Build on that instead of fighting it:

- outputs are new files, and existing ones are never overwritten;
- a claim file is a lock, because only one agent's create can succeed;
- each agent replaces only its own status file (delete, then create);
- logs, messages and peer notes are one new file per event.

Don't design a single shared file that several agents keep updating. Updates get lost, and the connector can't edit in place anyway.

### 5. Verify instead of assuming

- Before creating a task, read `TASK.md` through the connector: that proves the path and the access.
- List the existing scheduled tasks so you don't create a duplicate.
- When another account joins, prove both see the same files, through the same Dropbox email or a canary file read back.
- After the first run starts, look for its claim or output.

Two copies of a folder look identical, but agents in different copies can't see each other's claims and will redo everything.

### 6. Keep the owner in charge

Agents can share habits and feedback, but terms, style and content decisions belong to the owner. They go to `questions/` or a proposals folder for approval. The owner's reference files outrank anything one agent tells another.

### 7. Plan the end

A done file (`DONE.md`) stops the work, but the schedule keeps firing: in the real setup, both agents kept waking every hour to find nothing to do until the user paused them. So:

- Have each prompt pause its own task once `DONE.md` exists. The generated prompts do this, with `list_triggers` and `update_trigger`.
- Tell the user to check that every task is paused when `DONE.md` appears.
- Tell the user that creating `PAUSE.md` in the job folder stops every agent at once, in every account. That's the quickest way to halt a team.

## Workflow

1. **Job folder.** Find it and read `TASK.md`. If there is none, write one with the user from `assets/TASK-template.md`, and create the folders it names (`source/`, `reference/`, an outputs folder, `claims/`, `questions/`, `additions/`). If `TASK.md` exists, it's the owner's file: don't rewrite it unless asked.
2. **Scheduled task.** Ask only what's still open: how often, when, how results should reach the user, how much per run. Write the prompt from `assets/templates/agent-prompt.md.tmpl` or generate it (step 4). Then create the task. For settings and checks, see `references/scheduled-task.md`.
3. **First run.** Offer to start it now. The claim it creates keeps the next scheduled run off the same unit.
4. **More agents (optional).** Follow `references/parallel-agents.md`. Write a job config (start from `assets/job-kit.example.json`) and run `python scripts/make_job_kit.py job.json -o kit/`. It writes `PROTOCOL.md`, `PEER.md`, each agent's prompt, a setup message and a verification prompt for each other account, and the folder list, all consistent with each other. Then:
   - upload `PROTOCOL.md` (and `PEER.md`);
   - create the folders in `kit/folders.txt`;
   - update this account's task prompt;
   - give the user the setup message for each other account.
5. **Verify.** The setup message makes the other account report its Dropbox email and the TASK.md path and file id. Compare them with your own, and use a canary file if the emails differ. Confirm the first coordinated runs write claims, status files and log entries. Offer a check-in with `send_later` after the first runs, so problems surface while the user is away.
6. **Peer learning (optional).** Install `PEER.md` and its folders. The generated `PROTOCOL.md` already points to it, so no prompt changes are needed. If the live `PROTOCOL.md` doesn't mention PEER.md, replace it with one that does (step 7).
7. **Changing the rules later.** Edit `PROTOCOL.md` or `PEER.md`, not the prompts. Replace the file (delete, then create straight away) when no run is about to start. Then add an owner log event saying what changed, so runs don't mistake the switch-over for errors. See `references/coordination.md`.
8. **Finish.** When `DONE.md` exists, pause the tasks: `update_trigger` with `enabled: false` in this account, and a one-line message for the user to paste into each other account.

## Talking to the user

- Call them scheduled tasks, never triggers, routines or cron jobs.
- After creating or changing a task, cover in a sentence or two: its name, the schedule in the user's time zone, when the first run is, the approval setting it got, where results land and how it ends.
- Write `TASK.md`, `PROTOCOL.md` and prompts in English unless the user writes them in another language, and talk to the user in their own language.
- Results the user should read are `status/<agent>.md` (what each agent is doing), `questions/` (what needs them) and the newest file in `peer/digest/` (what the agents have learned).
- Tell the user how to stop everything: create `PAUSE.md` in the job folder (and delete it to resume), or pause each task.
