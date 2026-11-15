---
name: coverage-review
description: Systematically find unknown unknowns and blind spots in an ask, plan or draft PRD - walk every coverage lens, apply discovery moves (assumption inversion, pre-mortem, lifecycle walk, boundary analysis, evidence audit), check past review lessons, and report what is covered, partial, missing or unverified. Use for "what am I missing?", "is this complete?", "blind spots", or as stage 4 of pre-prd.
---

# Coverage review

Goal: replace "I hope I covered everything" with an explicit, honest map of what is covered,
what isn't, and what to do about each gap. Use the strongest available model for this skill.

Input: the work folder (`intake.md`, `landscape.md`, any draft) or a document the user names.
Also read `wiki/lenses.md` and `wiki/review-log.md`.
Output: `work/<slug>/coverage.md`; new questions appended to `work/<slug>/questions.md`.

## Steps
1. **Lessons first.** Read `review-log.md`. List every past lesson relevant to this ask; these
   are the highest-priority checks because that kind of miss has happened before. Rank them
   by origin (`review` and `backfill` above `asked` and `org-checklist`, above
   `confirmed-sim`) and by how often they recur.
2. **Walk every lens** in `lenses.md`. For each, decide:
   - `covered`: answered, with a source. Cite it.
   - `partial`: some answer, but missing a piece or resting on weak sources.
   - `gap`: not addressed.
   - `n/a`: explain why in one line. Never mark n/a just because the answer is unknown.
3. **Discovery moves.** Run these and record anything new:
   - *Assumption inversion:* list what must be true for the plan to work; flip each.
   - *Pre-mortem:* a year later it failed. Give the three most plausible stories.
   - *Lifecycle walk:* trace a customer from evaluation → purchase → deploy → configure →
     use → upgrade → support → renew or churn → offboard; note each handoff.
   - *Boundary scan:* who and what sits just outside the scope: adjacent products, other
     deployment models, other regions, partners, internal users.
   - *Evidence audit:* for the 5–10 claims the plan rests on, how strong is the source?
   - *Perspectives:* how would sales, support, security, finance, legal, a competitor, and the
     most demanding customer each poke at it?
   - *Reference class:* what similar past effort (ours or others') can we learn from?
4. **Accuracy pass.** Check claims in the draft against cited sources. Flag mismatches,
   stale sources (older than ~6 months for fast-moving facts), and uncited claims.
5. Write `coverage.md` and append questions.

## coverage.md
```
# Coverage review: <title>
## Verdict
Counts by status. Overall confidence (high / medium / low) and the main reasons.
## Must fix before drafting or review
Ranked. Each: the gap, why it matters, the question, who to ask, blocking or not.
## Past lessons that apply
## Lens table
| # | Lens | Status | Finding | Source / question | Owner |
## Discovery moves
Findings per move, only the non-obvious ones.
## Accuracy issues
| Claim | Problem | Source | Fix |
## What would raise confidence
The three cheapest actions that would close the most important gaps.
```

## Rules
- Be specific: "Which plans include it? Pricing team owns SKUs [S-0031]" beats "consider pricing".
- Don't pad. A lens with nothing new gets one line.
- The goal is truth, not reassurance. If coverage is weak, say so with counts.
