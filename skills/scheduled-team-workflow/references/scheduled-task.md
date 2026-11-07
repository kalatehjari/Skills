# Creating the scheduled task

How to put a long job on a recurring Cowork scheduled task, with the checks that keep unattended runs from stalling or colliding.

## Contents

1. Before you create anything
2. The prompt
3. Settings
4. After creating
5. Changing, pausing and stopping

## 1. Before you create anything

- **Load the right tools.** Scheduled tasks are the `create_trigger`, `update_trigger`, `fire_trigger`, `list_triggers` and `delete_trigger` tools on the Claude Code Remote server. In Cowork they are often deferred, so load them with ToolSearch (for example `select:mcp__claude-code-remote__create_trigger`). Never use local cron tools such as CronCreate: whatever they schedule dies with the session.
- **Read TASK.md through the Dropbox connector** (`fetch`). That proves the path exists and that this account can reach it, and it tells you what the runs need: units per run, the done file, the skill. If there is no TASK.md, write one with the user from `assets/TASK-template.md` before creating the task. If there is one, it's the owner's file, so don't rewrite it unless asked.
- **List existing tasks** (`list_triggers`). If a task for this job already exists, update it instead of adding a second one, unless the user wants parallel agents (`references/parallel-agents.md`).
- **Ask only what's still open,** in one AskUserQuestion: what each run does (usually "follow TASK.md"), how often (hourly is the shortest interval), when (in the user's time zone), how results reach them (push, email, or just files in Dropbox) and how much per run. If the user answers with a full instruction of their own, build the prompt around it.

## 2. The prompt

Each firing starts a fresh session with nothing but this prompt, so it must stand on its own. Include every item below. Each one prevents a specific failure:

| Item | Why |
|---|---|
| The job in one line | the run knows what it's for |
| The full Dropbox path of TASK.md, and "follow it exactly" | one source of truth; fixing the instructions later is one file edit |
| "You have no memory of earlier runs; progress lives in the files" | stops the run hunting for context or redoing finished units |
| A cap per run ("at most 2 units") | the run finishes inside its time limit, and never saves half a unit |
| Where it may write, and "never overwrite or edit existing files" except named exceptions | matches what the connector can do, and protects the owner's files |
| Pre-approval for the actions it needs: creating files and folders in the job folder, deleting its own claims and stale claims | nobody is there to confirm, so a run that asks just stops |
| "Don't ask questions; write them to questions/ and carry on" | the run keeps going, and the owner gets the question in one place |
| The skill to use, with a Dropbox fallback path | another account may not have the skill installed |
| The stop condition: when the done file exists, stop at once, and pause this task with `list_triggers` and `update_trigger` (pre-approved, best effort) | the schedule doesn't stop itself; in the real setup, runs kept waking hourly with nothing to do until the user paused them |
| "If PAUSE.md exists in the job folder, stop at once without writing anything" | the owner can halt every agent, in every account, by creating one file |
| Multi-agent only: "YOU ARE AGENT X", the other agents, and "follow PROTOCOL.md too" | coordination rules live in one file all agents read |

Write it from `assets/templates/agent-prompt.md.tmpl` by hand, or generate it with `scripts/make_job_kit.py` (`prompts/agent-<X>.md`). A real single-agent prompt that worked:

```
Continue the Persian adaptation of my novel «حدِ ممکن».

Using the Dropbox connector, read the file /Novel/Farsi Novel/Had-e Momken/had-e-momken/TASK.md and follow it exactly. It holds all the instructions. You have no memory of earlier runs, and progress lives only in the files in that folder.

Rules for this run:
- Draft at most two units.
- Save everything to /Novel/Farsi Novel/Had-e Momken/had-e-momken (the job folder) and write nothing outside it. Never overwrite or edit existing files, except where TASK.md says so: you may delete your own claim files in claims/ and stale claims.
- I've pre-approved creating files in my Dropbox and deleting claim files, so don't stop to confirm these actions.
- Do not ask me any questions; no one is there to answer. Log any question that needs my decision in questions/uNN.md, as TASK.md describes, and carry on.
- Use the farsi-scifi-builder skill as TASK.md directs. If it isn't installed, use the copy in Dropbox at /Claude Products/Skills/skills/farsi-scifi-builder/.
- If every unit is already drafted and DONE.md exists, stop right away and do nothing else.
```

## 3. Settings

`create_trigger` parameters:

- **name:** short and human, such as "Had-e Momken Persian adaptation".
- **cron_expression:** for hourly runs, `0 * * * *`. The server anchors it to the minute you create it, which spreads load. To give several agents set minutes, write the minute with the time zone: `CRON_TZ=Pacific/Auckland 35 * * * *`. For a fixed daily time, move it a few minutes off :00 or :30, which are busy.
- **initiation:** `human_request`.
- **notifications:** what the user chose. `{}` turns them all off (results live only in Dropbox); `{"push": true}` or `{"email": true}` turn channels on.
- **requires_local_device:** `false`. Dropbox work goes through the connector in the cloud. Only set `true` if runs need the user's own computer.
- **permission_mode:** leave it unset. The result's `derived_state.permission_mode` says what the task got. `auto` means runs go ahead. Anything else means runs stop at the first action that needs approval, which for this workflow is the first file save. Tell the user to turn on "Automatically approve" in the task's settings, if their organisation allows it.
- **Connectors:** the result lists `mcp_connections`. Check that Dropbox is among them; otherwise runs can't reach the folder. Claude_Code_Remote is usually there too, which is what lets a run pause its own task at the end.
- **Usage:** every run draws on the same account's usage as the user's chats. A run that drafts two chapters takes about 15 to 20 minutes of model time, so hourly runs can use up a session limit and cut off the user's interactive work (that happened while this skill was being built). Mention it, and lower the units per run or the frequency if the user also needs the account for other work.

## 4. After creating

- Tell the user in plain words: the task's name, the schedule in their time zone, the first run (convert `next_run_at` from UTC), the approval setting, notifications, where results land, and how it ends (the done file, then pausing the task).
- Offer to start the first run now with `fire_trigger`. The run gets its own session, which the user can open from the task's run history. The next scheduled run won't collide with it: the claim stays fresh for the claim window (3 hours by default).
- Within a minute or two, `claims/` should show the run's claim. Outputs appear as units finish.
- Offer a check-in: `send_later` back into this session after the first run or two (for example 30 to 90 minutes). The check reads the first outputs against TASK.md and fixes the instructions before many runs repeat a mistake.

## 5. Changing, pausing and stopping

- **Change the prompt** with `update_trigger` and a new `prompt`. That keeps the task's history. Never delete and recreate a task just to change its prompt.
- **Prefer changing files over prompts.** A rule in TASK.md or PROTOCOL.md reaches every agent at its next run; a prompt change has to be made in every account separately.
- **Pause** with `update_trigger` and `enabled: false`. Delete a task only when the user asks.
- **Pause everything at once:** create `PAUSE.md` in the job folder. Every agent that follows the generated prompt stops at its next run without writing anything. Delete the file to resume.
- **Other accounts' tasks** can only be changed from those accounts. Give the user a short message to paste there.
