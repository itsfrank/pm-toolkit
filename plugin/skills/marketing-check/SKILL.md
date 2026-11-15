---
name: marketing-check
description: Review marketing or sales material (web copy, datasheets, decks, blog drafts, battlecards, launch messaging) against what the product actually does, flagging overclaims, unsupported superlatives, stale or roadmap claims, scope mismatches and risky competitor statements, with suggested fixes. Use when the user asks to review, fact-check or draft marketing or sales content.
---

# Marketing check

Input: the draft (saved or pasted) and its audience and channel.
Output: `work/YYYY-MM-DD-mktg-<slug>/review.md` and, if asked, a revised draft.

## Steps
1. Split the draft into individual claims (capability, performance number, comparison,
   customer reference, compliance statement, availability date).
2. Check each against product pages, source cards and approved answers. Assign:
   - `ok`: supported by an authoritative source, in the stated scope.
   - `narrow`: true only for some products, plans, deployment models or versions. Say which.
   - `unsupported`: no source. Ask the owner or cut.
   - `wrong`: contradicted by a source.
   - `roadmap`: describes unreleased work. Needs explicit approval.
   - `risky`: legal or reputational risk (absolute claims like "only", "first", "100%",
     unsourced competitor comparisons, customer names without approval, compliance
     certifications not held).
3. Write the review as a table of claims with status, source and suggested rewrite, then
   the top issues in priority order.
4. If writing new copy, use only `ok` claims and phrase `narrow` claims with their scope.

## Rules
- Positioning and tone are the marketer's call; focus on truth, scope and risk.
- Never strengthen a claim beyond its source.
