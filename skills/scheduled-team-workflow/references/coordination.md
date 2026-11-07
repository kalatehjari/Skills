# Coordination through Dropbox files

Why PROTOCOL.md is built the way it is, and how to change it safely while tasks are running.

## Contents

1. Connector facts that shape the design
2. The building blocks
3. Why not one shared status file
4. Changing the rules while tasks run
5. What to show the user

## 1. Connector facts that shape the design

- `create_file` creates a new text file and fails if the path already exists. That failure is what makes a claim file a lock.
- There's no edit or overwrite in place. To "update" a file, delete it and create it again. The two steps aren't atomic, so use this only for files that a single agent owns, such as its own status file.
- `delete` moves files to Dropbox's Deleted files, so it's recoverable. It can return `in_progress`; poll `check_job_status` until it completes before creating the replacement.
- Parent folders must already exist. Create each level with `create_folder` first.
- `fetch` reads text files up to 5 MiB.
- In a personal Dropbox, display paths work. In team or shared spaces, prefer the `id:` or `ns:` paths that the tools return.
- Many writes in quick succession can fail with `too_many_write_operations`. Wait briefly and retry that one write.
- In scheduled runs, Dropbox download links can be blocked (HTTP 403), as happened in the real setup. `fetch` still returns the text of a file, scripts included, so have runs fetch a script's text and write it into their workspace instead of downloading it. Check each upload by comparing the size `create_file` reports with the local size.

## 2. The building blocks

| Block | File | Rule | Why |
|---|---|---|---|
| Claim | `claims/<unit>.claim` with agent, run, unit, time | create to claim; if create fails, pick another unit | only one create can succeed |
| Claim check | the claim file, and the outputs folder | right after a successful claim, read the claim back and re-list the outputs; if the output appeared, release the claim | another agent can finish the unit and delete its claim between your listing and your create; this happened in the real setup (unit 24) |
| Freshness | the claim's time plus the holder's status file | stale only if older than the window and the holder's status hasn't changed for an hour | a long run isn't mistaken for a dead one |
| Stale reclaim | the claim and a `stale` log event | read it, log it, read it again, delete it only if unchanged, then claim | nothing disappears silently, and a claim renewed in the meantime isn't deleted |
| Status | `status/<agent>.md` | only its owner replaces it, after a claim, after a save, at the end, and hourly during long units | shows what each agent is doing, and that it's alive |
| Log | `log/<time>_<agent>_<event>_<unit>.md` | one new file per event, never edited | a history nobody can overwrite |
| Messages | `messages/<time>_<from>-to-<to or all>.md` | read receipts are files: `<name>.read-<agent>` | coordination that can't wait for the owner |
| Shared decisions | proposals folder (for example `additions/`) | re-list it just before saving, and reuse other agents' choices | stops term clashes |
| Attribution | `Done by: <agent> (<run>)` in each unit's notes | — | peer reviews and the owner know whose work it is |
| Done file | `DONE.md` | created once, and only when every unit has its output; never while the last units are merely claimed | exactly one summary, and none while an agent is still on the last unit |
| Pause switch | `PAUSE.md` | if it exists, every run stops at once without writing | one file halts the whole team, in every account |
| After the end | — | a run that finds `DONE.md` writes only an `end` event, sets its status to done, pauses its own task if it can, and stops | no empty retros every hour until someone notices |

## 3. Why not one shared status file

It seems simpler, but it fails three ways:

- Two agents read it, both change it, and the second write erases the first.
- The connector can't edit a file in place anyway.
- While a shared file is being replaced (deleted, then created), it doesn't exist, and another agent reading at that moment sees nothing.

Separate files per agent and per event avoid all three.

## 4. Changing the rules while tasks run

- **Keep one entry point.** Every prompt says "follow TASK.md and PROTOCOL.md". New behaviour goes into PROTOCOL.md, or into a file it links to (like PEER.md). Then no account's prompt has to change, which matters because other accounts' tasks can only be changed from those accounts.
- **Replace the file at a quiet moment.** Delete it, wait for the delete to complete, then create the new version straight away. Runs read the files when they start, so avoid the minutes around each task's start time. Check `next_run_at` for this account's tasks (`list_triggers`), and use the agreed minutes for the other accounts.
- **Version the title** (for example "v2"), so a run's notes can say which rules it followed.
- **Stay compatible with files the old rules made.** For example, treat claims without an `agent:` line as normal claims. Runs already in progress keep the rules they read at their start.
- **Adding something new** (status, log, messages, peer notes): create its folders before the new PROTOCOL.md goes live, so the first run under the new rules doesn't fail on a missing folder.
- **Leave a note for the agents.** Write an owner log event, `log/<time>_owner_setup_-.md`, saying what changed and that runs already in progress follow the old rules. Then nobody mistakes the switch-over (a missing retro, a claim without an agent line) for an error.

## 5. What to show the user

- `status/<agent>.md`: what each agent is doing right now.
- `log/`: the history, file by file.
- `questions/`: what needs them. They answer by updating the reference files (glossary, style sheet), which every run reads, rather than by replying to an agent.
- `peer/digest/` (newest version): what the agents have learned, if peer learning is on.
