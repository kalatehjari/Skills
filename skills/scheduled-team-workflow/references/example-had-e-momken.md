# Worked example: two accounts adapting a novel

This is the real setup the skill was taken from, in October 2026. An author's English novel was adapted into Persian («حدِ ممکن») unit by unit by two Claude accounts, using the farsi-scifi-builder skill.

## The job folder

```
/Novel/Farsi Novel/Had-e Momken/had-e-momken/
  TASK.md          the instructions every run follows (written before the schedule)
  PROTOCOL.md      coordination rules (added when the second account joined; v2 links PEER.md)
  PEER.md          peer-learning rules
  README.md
  source/          the English, one file per unit (read-only)
  reference/       style-sheet.md, glossary.md (+ .json), story-bible.md, units.json (read-only)
  drafts/          u01_ch01.md is the author-approved model; runs add uNN_*.md and .log.md
  scripts/         check_motifs.py and other checks
  claims/          one claim file per unit being drafted
  additions/       new terms proposed per unit, reused by later runs
  questions/       decisions waiting for the author
  status/          A.md and B.md, one per agent
  log/             one file per event
  messages/        agent-to-agent notes
  peer/retro/, peer/review/, peer/digest/
```

## How it was set up, step by step

1. **Explain, then ask.** Claude explained in a few bullets how scheduled tasks work, then asked four questions: what to do, how often, when, and how results should arrive. The author answered with a full instruction (read TASK.md, draft at most two units, save to the folder, log questions in `questions/`), "hourly", "24/7" and "save to Dropbox".
2. **Verify first.** Claude read TASK.md through the Dropbox connector and checked there were no existing scheduled tasks.
3. **Create the task.** `create_trigger` with `0 * * * *` (the server anchored it to :35), notifications `{}`, in the cloud, approval left to the server. It got automatic approval.
4. **First run now.** `fire_trigger` started it at once. It claimed unit 02.
5. **A second account.** The author asked whether another account could help. Claude explained what that account needs: the same files, the skill or its Dropbox copy, its own task with an offset minute, and automatic approval. It gave the exact prompt, with placeholders for the folder and skill paths.
6. **Verify the second account.** Its Claude found the folder at exactly the owner's path and suspected it might be the owner's account. Claude checked the folder from its own side: an ordinary, unshared folder, so only the same Dropbox account could see it. Claude then asked the other account for its who_am_i email and the file id of `claims/u02.claim`. Both matched. The other account noticed the claim was written "by something else" three minutes before its task existed: that was the first run started in step 4.
7. **Coordination protocol.** The author asked for a communication protocol so the two never double-work. Claude created `status/`, `log/` and `messages/`, uploaded PROTOCOL.md (claims with agent lines, per-agent status, event log, messages), and updated its own task's prompt to "YOU ARE AGENT A … follow TASK.md and PROTOCOL.md". It gave the author the agent-B prompt to paste into the other account, which replaced its prompt and kept its :30 schedule.
8. **Peer learning.** The author asked for peer-to-peer communication so the agents encourage each other and share lessons and challenges. Claude created `peer/retro/`, `peer/review/` and `peer/digest/`, and uploaded PEER.md. It then replaced PROTOCOL.md with v2, which links PEER.md, by deleting and recreating it 40 minutes before the next runs. Neither account's prompt had to change.

## How it went

| UTC, 10 Oct 2026 | What happened |
|---|---|
| 10:36 | the first run (A, started by hand) claims unit 02 |
| 10:51 | PROTOCOL.md v2 with peer learning goes live |
| 11:34 | B's first coordinated run claims unit 04 |
| 14:54 | first digest (v01), written by B |
| 17:53 | B claims unit 24 just after A saved it; B notices, logs an `error` and releases it |
| 18:04 | B saves unit 25, assembles the last chapter and creates DONE.md |
| 18:35–20:36 | three more rounds of runs find DONE.md and stop; B still writes a short retro each time |
| 20:43 | the task in the owner's account is paused |

- Units 02–25 (24 units) were drafted in about 7.5 hours. Each run did two units in 10 to 20 minutes.
- No unit was drafted twice. All 16 chapter files were assembled.
- The agents also wrote 15 retros (4 of them empty, after DONE.md), 10 peer reviews, 3 digests and 10 messages, each with a read receipt, plus 25 question files and 24 term files.
- The digests held real craft lessons (everyday words, keeping recurring lines verbatim, reading the peer's previous draft before a seam unit). They also held process lessons: "claim first, then read the board", and the fact that Dropbox downloads were blocked (403), so checks were rebuilt from fetched text.
- DONE.md was a clear briefing: what to read first, open questions by file, terms waiting for approval, and a pointer to the newest digest.

## What was learned

- The connector's create-only behaviour is a feature: claim files make a safe lock, but nothing can be edited in place. Every design decision follows from that.
- Asking the other account for its email and a file id settled "is this the same Dropbox?" in one exchange.
- Putting new behaviour behind the file all prompts already read (PROTOCOL.md) saved a second round of pasting prompts into the other account.
- The manual first run was the right call: it showed the setup working before the schedule took over, and its claim kept the next scheduled run off the same unit.
- Tell the user up front that the schedule keeps firing after DONE.md appears. The generated prompts now pause their own task at that point, and runs that find DONE.md write no retro.
- After a successful claim, check the claim is really yours: re-list the outputs (the unit 24 race).
- Scheduled runs share the account's usage with the user's chats. The hourly runs in the owner's account were busy while the owner was also building this skill, and the session limit ran out.

## The final prompts

Agent A's prompt is what `scripts/make_job_kit.py assets/job-kit.example.json` generates as `prompts/agent-A.md`. Agent B's prompt is the same with "AGENT B" and `status/B.md`, and its folder and skill paths are identical because both accounts use the same Dropbox.
