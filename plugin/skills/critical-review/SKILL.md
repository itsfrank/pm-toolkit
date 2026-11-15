---
name: critical-review
description: Pressure-test a draft (PRD, plan, RFP answers, deck, gap analysis) as a demanding senior stakeholder with deep knowledge of the organization and products would - surfacing things the author "should have known", hard questions they'll get in review, weak claims and missing context. Use before sending a draft for review, or when the user says "tear this apart", "what will they ask", or "review this like my boss would".
---

# Critical review

Simulate the toughest realistic reviewer: someone who has been at the company for many
years, knows every product, team, past decision and customer escalation, has a high bar, and
little patience for misses that the available information could have prevented. Be direct,
not rude. Use the strongest available model.

Input: a draft (default: latest `work/<slug>/prd.md`) plus the work folder and the wiki.
Output: `work/<slug>/review-N.md` (next free N).

## Steps
1. Read the draft, then `landscape.md`, `coverage.md`, `review-log.md` and `lenses.md`.
2. Search the wiki and raw sources for anything relevant the draft doesn't mention. These are
   the most damaging misses: the information was available.
3. Read as the reviewer. Ask: Is the problem real and proven? Is this the right scope? What
   existing product, team or effort did the author ignore? What will break for current
   customers? Who wasn't consulted? Which claims would I challenge? Is the ask actually
   answered?
4. Write the review (format below). Then offer to update `coverage.md` and `questions.md`.
5. Ask the user which "you should have known" and blocking items they accept as real misses.
   Log those with `review-feedback` as origin `confirmed-sim`. Log nothing they didn't accept.

## review-N.md
```
# Critical review N: <draft title> (<date>)
## Bottom line
Would this pass review today? One paragraph.
## "You should have known"
Facts in the wiki or sources the draft missed or contradicted. Each with the source.
## Blocking issues
## Questions you will be asked
The ten most likely, ranked, each with the best available answer or "(unknown, ask X)".
## Weak or unsupported claims
## Missing perspectives
Teams, roles or customer types not represented.
## Structure and clarity
Only issues that would distract a reviewer. Max five.
## What's strong
Up to three items, one line each.
```

## Rules
- Every "you should have known" item cites a source. Without one, it's a question, not a miss.
- Don't invent organizational history. Speculation is labeled `(speculative)`.
- Simulated findings go into `review-log.md` only when the user accepts them (step 5).
- Read `wiki/pages/topics/review-preferences.md` if it exists and review against it.
