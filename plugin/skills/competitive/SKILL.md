---
name: competitive
description: Build and maintain dated, sourced competitor claim cards and comparisons from saved public material (docs, datasheets, release notes, analyst notes), keeping scope, confidence and staleness explicit. Use for competitor analysis, battlecards, "how does X compare", or checking a competitive claim.
---

# Competitive intelligence

Input: a competitor, a topic, or a claim; competitor material saved in `wiki/raw/`.
Output: updates to `wiki/pages/competitors/<name>.md`; for a comparison,
`work/YYYY-MM-DD-compete-<topic>/comparison.md`.

## Claim cards
Every competitive claim on a competitor page is a card:
```
### <Claim in one sentence>
- **Scope:** product, version/edition, deployment model, plan, region.
- **Evidence:** [S-NNNN] (type: docs | release-notes | datasheet | analyst | customer-said | hearsay)
- **As of:** date of the source; date checked.
- **Confidence:** high (their own current docs) | medium | low (hearsay, old, indirect).
- **Our position:** how we compare, cited to our own sources.
```

## Steps
1. Card new sources with `wiki-ingest` rules first. Competitor marketing is `marketing`,
   their technical docs are `secondary` for us.
2. Extract claims into cards. Update existing cards instead of adding duplicates; keep
   superseded versions under `## History` with dates.
3. For a comparison, build a table per capability: us / them / evidence / as of / confidence.
4. Close with **what we don't know** and **where they're likely to attack us**.

## Rules
- No public mention means `unknown`, never "they don't have it".
- Flag cards older than 6 months as stale; don't use stale cards externally without rechecking.
- Customer-reported competitor claims are useful signals but `low` confidence until confirmed.
- Anything going external (battlecards, sales content) must be checked with `marketing-check`.
