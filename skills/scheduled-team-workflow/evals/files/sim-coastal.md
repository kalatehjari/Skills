# Simulated environment for this test

This is a dry run. Don't call the real Dropbox connector, the scheduled-task tools or any other tool that changes something outside your workspace. Treat this file as what those tools would return. Everything here is made up for the test.

## Dropbox (`who_am_i`)

- Signed in as: researcher@example.org (personal account)

## Folder tree (`list_folder /Research/Coastal Interviews`)

```
/Research/Coastal Interviews/
  codebook.md
  consent-notes.md
  raw/
    int-01_harbourmaster.txt
    int-02_fisher-a.txt
    int-03_fisher-b.txt
    int-04_council-planner.txt
    int-05_surf-club.txt
    int-06_iwi-representative.txt
    int-07_cafe-owner.txt
    int-08_retired-engineer.txt
    int-09_school-teacher.txt
    int-10_dune-volunteer.txt
    int-11_insurer.txt
    int-12_bach-owner.txt
    int-13_marine-scientist.txt
    int-14_ferry-crew.txt
```

There is no `coded/` folder and no TASK.md yet. Each raw transcript is 6–9 KB of automatic transcription: no speaker labels, timestamps every 30 seconds, frequent mishearings of place names.

## `codebook.md` (contents)

```
# Coastal adaptation codebook v3

Apply codes at the sentence level. A sentence can take more than one code.

| Code | Definition | Example |
|---|---|---|
| RISK-PERC | How the speaker describes coastal hazard risk (erosion, storm surge, flooding) | "The dunes are going faster than they told us" |
| TRUST-INST | Trust or distrust in council, government or science | "Council never comes back to us" |
| PLACE-ATT | Attachment to place, identity, history | "My grandfather built that wharf" |
| ADAPT-ACT | Actions taken or proposed (retreat, protection, insurance) | "We moved the caravan back twenty metres" |
| COST | Money, insurance, property values | "Premiums doubled after the 2023 storms" |
| EQUITY | Who wins or loses; fairness | "The baches will get the sea wall, not us" |

Mark uncertain codings with a trailing `?` (e.g. `RISK-PERC?`). Never invent quotes; anonymise names of private people as [P1], [P2] …
```

## `consent-notes.md` (contents)

```
All 14 participants consented to transcription and coding. Participant 6 asked that the name of their marae not appear in any output.
```

## Scheduled tasks in this account (`list_triggers`)

- none

## The user

- Time zone: Pacific/Auckland.
- Away most of the time; wants results in Dropbox, no notifications.
