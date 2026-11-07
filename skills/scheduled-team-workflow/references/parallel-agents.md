# Adding agents and Claude accounts

How to let several scheduled tasks, in one account or several, work the same job folder without doing the same work.

## Contents

1. When it's worth it
2. What each extra account needs
3. Prove it's the same folder
4. Steps
5. Schedules and claim windows
6. Runs already in progress
7. The kit config

## 1. When it's worth it

- Each Claude account has its own usage, so a second account roughly doubles the work done per hour. Two tasks in the same account also run in parallel, but they share that account's usage.
- **Costs:**
  - Continuity seams: a unit may be done before the one it follows exists.
  - Clashes: two agents may pick different words for the same new term.
  - More files: claims, status, log and messages.
- **Mitigations:**
  - PROTOCOL.md §6: re-read proposals before saving, and message the next agent about what you introduced.
  - Peer learning (`references/peer-learning.md`).
  - If continuity matters most, give each agent whole blocks (for example, whole chapters) by having TASK.md assign units by block.

## 2. What each extra account needs

1. **Access to the same files.** There are two ways to get it:
   - The other account's Claude connects to the same Dropbox account. This is the simplest, because paths are identical.
   - The folder is shared to the other account's Dropbox with edit rights. A shared folder usually appears at a different path there, for example `/had-e-momken` at its root. Its prompt then has to map the path and fall back to searching for the folder; the generated prompts do both.
2. **The skills the job uses,** either installed in that account or readable from Dropbox. If the skill folder isn't in a Dropbox both can see, share it too.
3. **Its own scheduled task,** with:
   - the same prompt, but its own agent letter;
   - a minute offset from the other agents;
   - automatic approval;
   - the notifications the user wants.
4. **The Dropbox connector,** connected in that account. The task's connector list should include Dropbox.

## 3. Prove it's the same folder

Two copies of a folder look the same, but agents in different copies can't see each other's claims and redo everything. Check before relying on the setup:

1. The setup message (`prompts/setup-<X>.md`) already makes the other account report its Dropbox email (who_am_i) and TASK.md's path and file id. With `dropbox_email` set in the config, it also stops without creating anything if the email differs. For a later re-check, use `prompts/verify-<X>.md`.
2. Run `who_am_i` here and compare:
   - **Same email:** same Dropbox account, so the same files. Done.
   - **Different email:** it must be a shared folder. Create a canary file in the job folder, `sync-check-<random code>.txt` with the code inside. Ask the other account to read it back, then delete it. If it can't find the file or the code differs, it's working in a copy: pause its task, share the folder properly, and fix its job folder path.
3. If the other account finds the folder at exactly the owner's path, that usually means it's connected to the same Dropbox account rather than a share. The email confirms it.

Two things to explain to the user:

- **Files show the same creator.** When accounts share one Dropbox, every agent's files show the same Dropbox user as creator. The other account may report that "something else created this file". That's the other agent's run, and the claim's `agent:` line and the log say which one.
- **A file id can confirm a specific file.** For example, the claim the first run created. If both accounts see the same id for it, they see the same file.

## 4. Steps

1. **Agree letters.** A is the owner's account (this one). B, C and so on are the others.
2. **Write the kit config** (start from `assets/job-kit.example.json`) and run `python scripts/make_job_kit.py job.json -o kit/`.
3. **Create the folders** in `kit/folders.txt` (parents first), then upload `PROTOCOL.md` and, with peer learning, `PEER.md`.
4. **Update this account's task** to `prompts/agent-A.md` with `update_trigger`. Don't recreate it.
5. **Give the user `prompts/setup-B.md`** to paste into account B. It:
   - checks the Dropbox email, the job folder and the skill folder;
   - creates B's task, or replaces the prompt of an existing one;
   - reports the approval setting and checks that Dropbox is among the task's connectors;
   - starts B's first run if approval is automatic.
6. **Verify** as in section 3, and tell the user the result in a sentence.
7. **Watch the first coordinated runs.** Claims in `claims/` carry an `agent:` line, `status/A.md` and `status/B.md` appear, and `log/` fills with events.

Without the script, write the same pieces by hand from `assets/templates/`. Keep every agent's prompt identical apart from its letter, its job folder path and its skill path.

## 5. Schedules and claim windows

- Offset the minutes (for example A at :35 and B at :30) so runs don't start at the same moment. Overlap is still safe, because the claims decide who does what.
- A run can last longer than an hour. Claims stay fresh for the claim window (3 hours by default), and the generated protocol also counts a holder as alive while its status file was updated in the last hour. Make the window longer than the longest run you expect, and lower the units per run if runs get close to it.

## 6. Runs already in progress

A run that started before the protocol existed follows the old rules. Its claim has no `agent:` line, and the protocol treats it like any other claim. There's nothing to fix. The next runs of every task pick up the protocol.

## 7. The kit config

`scripts/make_job_kit.py` reads a JSON file. Start from `assets/job-kit.example.json`. Keys:

| Key | Meaning | Default |
|---|---|---|
| `job_name` | the job in a phrase ("the Persian adaptation of …"); prompts start "Continue the job: …" | required |
| `task_name` | the task name in the first account | the job name, capitalised |
| `job_folder` | full Dropbox path of the job folder in the owner's Dropbox | required |
| `owner` | how files refer to the human ("the author", "the researcher") | "the owner" |
| `unit` | `{"singular": "chapter", "plural": "chapters"}` | unit / units |
| `units_per_run` | the cap per run | 1 |
| `stale_hours` | the claim window, used if TASK.md gives none | 3 |
| `done_file` | the end marker | DONE.md |
| `outputs_folder` | folder the units go to, created with the others (for example `coded`) | none |
| `proposals_folder` | where new terms and decisions go | additions |
| `version` | shown in the titles of PROTOCOL.md and PEER.md; bump it when you replace them | v1 |
| `self_pause` | prompts pause their own task once the done file exists | true |
| `dropbox_email` | the email the other accounts' Dropbox must show; the setup message stops if it differs | none |
| `timezone`, `timezone_label` | IANA zone for cron (`CRON_TZ=`), and the words used in text | none (UTC) |
| `skill` | `{"name": …, "dropbox_path": …}` for the skill the work uses and its Dropbox copy | none |
| `agents` | list of `{"id", "account", "minute", "task_name", "job_folder"}`; the first is this account. `job_folder`: `"same"` (same Dropbox), a path, or left out (unknown: placeholder plus search) | required |
| `peer_learning` | `{"enabled", "notes_language", "authority_files", "review_checks", "retro_words", "review_words", "digest_lessons", "digest_after"}` | off |
