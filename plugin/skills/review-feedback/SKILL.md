---
name: review-feedback
description: Turn feedback into lessons the toolkit checks automatically next time - log real reviewer comments, backfill lessons from past comment threads, draft-vs-final document versions, post-mortems and escalations, or quickly capture a question the user couldn't answer. Files revealed facts into the wiki and recurring misses into coverage lens probes. Use when the user pastes or describes feedback, says "I got dinged for missing X", "they asked me Y and I didn't know", or wants to mine old reviews.
---

# Review feedback

This is how the toolkit learns what your organization cares about. Every miss a reviewer
catches, and every question you couldn't answer, should be impossible to repeat.

## Origins
Every review-log entry has an origin. `coverage-review` weighs them in this order:
| Origin | From | Weight |
|---|---|---|
| `review` | real feedback on your artifact | high |
| `backfill` | past comments, draft-vs-final diffs, post-mortems, escalations (yours or others') | high |
| `asked` | a question you were asked and couldn't answer | medium |
| `org-checklist` | the organization's review checklists or templates (seeded by `setup`) | medium |
| `confirmed-sim` | a `critical-review` finding you accepted as a real miss | low |

## Mode 1: feedback on an artifact (`review`)
1. Save the feedback verbatim to `work/<slug>/feedback.md` if it isn't saved yet.
2. Split it into items and classify each:
   - **missed fact**: something true we didn't include (product, team, initiative, history).
   - **wrong fact**: something we stated incorrectly.
   - **missing angle**: a consideration not covered (a lens-level gap).
   - **preference**: style, format or emphasis the reviewer wants.
   - **disagreement**: a judgment call; record it, don't treat it as fact.
3. Diagnose why each miss happened: not in wiki / in wiki but not surfaced / wrong or stale
   source / no lens for it / lens skipped.
4. Apply fixes (below), log entries, and revise the artifact if the user wants.

## Mode 2: backfill from history (`backfill`)
For material saved in `wiki/raw/`: exported comment threads, post-mortems and retros,
escalation or launch-blocker tickets, and especially **draft and final versions of the same
document** (yours or colleagues'). What was added or changed between draft and approval is a
record of what reviewers demanded.
1. Card each input with `wiki-ingest` rules if it has no source card.
2. For version pairs, compare section by section. List additions, removals and changed
   claims. Ignore wording edits, reordering, and normal progress such as an open question
   that got answered or a date that moved; those are not lessons unless a reviewer comment
   shows they were forced by review.
3. Turn each substantive change or comment into a candidate lesson: what the earlier version
   lacked, which lens it belongs to, and the source. Don't guess who asked for a change unless
   the source says; use "reviewers (inferred from final version)".
4. Compare with existing review-log entries. If a change is the fix for feedback already
   logged (same artifact, same review), annotate that entry (`Resolved in: [S-NNNN]`). If it
   is an independent recurrence (a different artifact or review), append
   `Seen again: <date> [S-NNNN]` to the existing entry. Never create a duplicate.
5. Show the candidate list to the user, apply the fixes they approve, and log entries.

## Mode 3: quick capture (`asked`)
The user says something like "asked about X in the roadmap review, didn't know". Log it in
one step: the question, who asked (role), the context, the answer if found later. Search the
wiki: if the answer was there, diagnose "in wiki but not surfaced"; if not, add the question
to the relevant page's `## Open questions` and suggest who might know.

## Applying fixes
- Facts → `wiki-ingest` (source card for the reviewer's statement: trust `authoritative` if
  they own the area, otherwise `hearsay` until confirmed).
- Missing angle → add a probe under the right lens in `wiki/lenses.md`, tagged
  `[RL YYYY-MM-DD]`. Create a new lens if none fits. For `confirmed-sim` and single `asked`
  entries, add the probe only after the pattern recurs (see `wiki-lint`).
- Preference → `wiki/pages/topics/review-preferences.md` (who prefers what format, level of
  detail, must-have sections). `prd` and `critical-review` read it.

## Log entry format (`wiki/review-log.md`)
```
## YYYY-MM-DD: short title
- **Origin:** review | backfill | asked | org-checklist | confirmed-sim
- **Artifact:** work/... or the source document
- **Reviewer role:** role, not name, unless the user prefers names
- **What was missed or wrong:**
- **Lens:** number and name
- **Why it was missed:** not in wiki / not surfaced / wrong source / no lens / lens skipped
- **The fact, with source:** [S-NNNN] or "from reviewer, to confirm"
- **Fix applied:** wiki page updated / lens probe added / preference recorded / pending
```

## Rules
- Keep tone neutral: what was missed and why, not who was upset.
- Never invent feedback, reviewers or reasons. Inferred items are labeled `(inferred)`.
