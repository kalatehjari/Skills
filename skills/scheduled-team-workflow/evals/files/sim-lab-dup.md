# Simulated environment for this test

This is a dry run. Don't call the real Dropbox connector, the scheduled-task tools or any other tool that changes something outside your workspace. Treat this file as what those tools would return. Everything here is made up for the test.

## Dropbox (`who_am_i`)

- Signed in as: owner@example.org. Both accounts' Claude use this same Dropbox (verified).

## Folder tree (relevant parts)

```
/Lab Manual/fa-translation/
  TASK.md  PROTOCOL.md  (PROTOCOL.md v1: claims, status, log, messages; a claim is stale when older than 3 hours)
  drafts/  ch05.md  ch05.log.md        (log starts "Done by: A (A-20261015T0120Z)")
           ch05.alt-B.md  ch05.alt-B.log.md   (log starts "Done by: B (B-20261015T0440Z)")
  questions/ ch05_duplicate_B.md   ("drafts/ch05.md already existed when I tried to save; saved mine as ch05.alt-B.md")
  status/  A.md (idle; updated 2026-10-15T04:52:30Z)  B.md (idle; updated 2026-10-15T05:41:02Z)
  log/     20261015T012004Z_A_start_-.md
           20261015T012031Z_A_claim_ch05.md
           20261015T044005Z_B_start_-.md
           20261015T044019Z_B_stale_ch05.md      ("claim ch05 by A, claimed 01:20:31Z, older than 3 h, no draft; reclaimed")
           20261015T044022Z_B_claim_ch05.md
           20261015T045230Z_A_saved_ch05.md
           20261015T045241Z_A_end_-.md
           20261015T054055Z_B_saved_ch05.md      ("create drafts/ch05.md failed: exists; saved as ch05.alt-B.md")
           20261015T054102Z_B_end_-.md
```

`status/A.md` was last updated at 01:20:40Z (after claiming) and then at 04:52:30Z (after saving). A's run lasted from 01:20Z to 04:53Z: chapter 5 is the longest chapter (14 tables).

## Scheduled tasks in this account

- Agent A: cron `CRON_TZ=Pacific/Auckland 20 * * * *`, at most 1 chapter per run. Agent B (other account): :40, same prompt with AGENT B.

## The user

- Time zone: Pacific/Auckland.
