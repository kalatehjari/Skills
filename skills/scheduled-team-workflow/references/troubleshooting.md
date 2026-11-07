# Troubleshooting

Symptoms, the usual causes, and fixes. Diagnose from the files first (`claims/`, `status/`, `log/`, outputs), then from each task's run history. Don't delete or overwrite anyone's output while diagnosing. When two versions of a unit exist, the owner picks which one to keep.

## Two agents did the same unit

Read the unit's log events in time order, then match the case below.

**1. A claim was reclaimed while its holder was still working.** The log shows a `stale` event by one agent, naming the other agent's claim, followed by `saved` events from both.

- Cause: the run took longer than the claim window, and nothing showed the holder was alive.
- Fix:
  - Lengthen the window in TASK.md or PROTOCOL.md (for example to 6 hours).
  - Lower the units per run.
  - Use a PROTOCOL.md that treats a claim as alive while its holder's status file was updated within the hour, and has holders refresh their status during long units. The generated PROTOCOL.md does both.

**2. Agents are working in different copies of the folder.** Each folder's log shows only one agent, but both produced the unit.

- Cause: one account's Dropbox has a copy, not the shared folder, or its prompt's search fallback found an old copy.
- Fix: verify (`references/parallel-agents.md` §3), pause the task that uses the copy, and fix its job folder path.

**3. Different claim names.** One agent claims `u05.claim`, another `ch05.claim`.

- Cause: different TASK.md versions, or an old prompt that names its own claim scheme.
- Fix: one TASK.md, read from the shared folder by every agent; prompts that don't restate the claim rules.

**4. An agent ignores the protocol.** Its claims have no `agent:` line long after the protocol went live, and no status or log files appear for it.

- Cause: its prompt was never updated to "follow PROTOCOL.md".
- Fix: give the user the setup message for that account again.

**5. A claim was made for a unit that was already done.** The log shows a `claim` just after another agent's `saved` event for the same unit.

- Cause: the agent listed the folder, the other agent saved and deleted its claim, and then the create succeeded. Nothing is lost if saves never overwrite, but the run wastes time, or saves a second version under another name.
- Fix: the claim check in the generated PROTOCOL.md: read the claim back and re-list the outputs right after claiming. In the real setup, agent B caught this itself on unit 24 and logged it as an error.

**6. A claim was deleted while fresh.** There's a `stale` event with a claim time inside the window.

- Cause: clock or format confusion.
- Fix: make sure claims carry `claimed_utc` in UTC, and that the protocol says to use it.

## Runs do nothing, or stop early

- **Approval isn't automatic.** Runs stop at the first file save and wait. Check the task's approval setting, and tell the user to turn on "Automatically approve".
- **No Dropbox connector in that account,** or it's signed in to a different Dropbox. The run's session shows connector errors, or "file not found" for TASK.md.
- **Wrong job folder path** after sharing. Use the path mapping and search fallback in the generated prompts.
- **The done file exists.** Runs stop by design.
- **A run hit its time limit before saving.** Its claim goes stale and a later run redoes the unit. If this keeps happening, lower the units per run.

## DONE.md appeared while a unit was still being worked on

- Cause: TASK.md's "no unit left: create DONE.md" fired because the last units were claimed by another agent, not finished.
- Fix: the done guard in the generated PROTOCOL.md: create DONE.md only when every unit has its output. If DONE.md came too early, the owner can delete it; the agents still holding claims carry on.

## The user's chats hit a usage limit

Scheduled runs share the account's usage with the user's own chats, so a busy schedule can exhaust a session limit (this happened while building this skill). Lower the units per run or the frequency, move some agents to another account, or pause the tasks while the user needs the account.

## Scripts in Dropbox can't be downloaded

Download links can return 403 in scheduled runs. Have runs read the script's text with `fetch` and write it into their workspace, or do the check by reading. The real agents did this and said so in DONE.md.

## Claims pile up

Several stale claims with no outputs means runs keep being cut off. Lower the units per run, and check the run sessions for errors. Stale claims are reclaimed automatically after the window, so they do no harm, only delay.

## A question flood

If many questions arrive, the instructions probably leave a recurring decision open. Answer by updating the reference files (glossary, style sheet, codebook). Every run reads them, so the questions stop. Replying to an individual question file doesn't teach future runs anything unless TASK.md says to read answers.

## Runs keep firing after the job is done

A schedule doesn't stop itself. The generated prompts have each run pause its own task once DONE.md exists. If a task is still on, pause it with `update_trigger` and `enabled: false` in this account, and give the user a one-line message for each other account. Creating `PAUSE.md` in the job folder stops every agent at once in the meantime.

## "Something else created this file"

When accounts share one Dropbox, every agent's files show the same creator. Tell agents apart by the claim's `agent:` line, the log file names and the `Done by:` line in each unit's notes.

## The connector refuses to change a file

It can't edit files in place. Delete the file and create it again, and only for files a single agent owns. Never do this to an output or a reference file unless the owner asked for that change.
