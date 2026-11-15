---
name: pre-prd
description: Guide a broad or vague product ask (e.g. "we need X", "how are we handling Y?") all the way to a reviewed PRD - intake, landscape map, coverage review, questions for people, draft, critical review. Use when the user has a new ask, request or initiative and wants to get to a PRD, or asks "where do I start?".
---

# Pre-PRD pipeline

Most of the effort before a PRD goes into finding out what already exists, who is involved
and what nobody has said yet. This skill runs that discovery as stages with checkpoints. Each
stage writes a file into the work folder, so work can pause for days while the PM talks to
people and pick up where it stopped.

## Stages
| # | Stage | Skill | Output | Checkpoint |
|---|---|---|---|---|
| 1 | Capture the ask | (here) | `ask.md` | PM confirms the ask is captured verbatim |
| 2 | Frame it | `intake` | `intake.md`, `questions.md` | PM answers or sends the requester questions |
| 3 | Map what exists | `landscape-map` | `landscape.md` | PM corrects the map, saves missing docs |
| 4 | Find the gaps | `coverage-review` | `coverage.md`, `questions.md` | PM gets answers from people |
| 5 | Draft | `prd` | `prd.md` | PM edits |
| 6 | Pressure-test | `critical-review` | `review-N.md` | PM decides what to fix |
| 7 | Learn | `review-feedback` | `review-log.md`, `lenses.md` | after the real review |

## How to run
1. Find or create `work/YYYY-MM-DD-slug/`. If it exists, read every file in it, report which
   stage it's at and what's open in `questions.md`, then continue from there.
2. For stage 1, write `ask.md`: the ask verbatim, who asked, their role, date, channel,
   any deadline, and links to related threads or documents the PM has.
3. Run each stage's skill. Stop at each checkpoint: summarize in five lines or fewer, list
   what the PM needs to do or find out, and wait.
4. Loop back when new information arrives. New documents → `wiki-ingest`, then refresh
   `landscape.md`. New answers → update `questions.md` and re-run the affected lenses.
5. Don't move to stage 5 while any question marked **blocking** is open, unless the PM
   explicitly chooses to draft with labeled assumptions.

## Readiness check before drafting
State plainly, with counts:
- Lenses covered with sources / partial / gaps / not applicable.
- Blocking questions open.
- Key claims resting only on `hearsay` or `marketing` sources.
- People in `landscape.md` "should talk to" who haven't been consulted.

Close the check with a one-line recommendation: draft now, or first do the specific things listed.
