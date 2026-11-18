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
3. **Raw details (don't skip):** build a term list from the capabilities compared (our
   products and features, regions, data types), the competitor's names, and their glossary
   aliases, and run `python3 tools/wiki.py raw-hits <terms...>`. It prints raw-file lines
   matching a term that no card or page mentions; limitations that weaken our position
   often sit only there. Read each reported line in context.
4. **Unread pages:** if `wiki/catalog/` has catalogs, run
   `python3 tools/wiki.py catalog-search <terms...>`. For the hits that bear on the
   comparison (up to about five), fetch each page (read-only connector, or its `file:`
   export), save it to `wiki/raw/` with a card, use it, and tick its line with
   `catalog-mark`. List the other relevant hits under `## Unread pages` with their links.
5. Write **Our position** from our own sources, including the raw details: state our limits
   as plainly as theirs. For a comparison, build a table per capability: us / them /
   evidence / as of / confidence.
6. Close with **what we don't know** and **where they're likely to attack us**. Then, in
   the comparison (or in your reply when you only updated a competitor page), add
   `## Raw details not in the wiki`: one line per file `raw-hits` reported, stating its new
   fact in your own words [S-NNNN]; never group files or write "used as cited". Then say
   where you used it, or why it doesn't bear on the comparison.

## Rules
- Save fetched connector pages with `wiki.py save-fetched`, and before you finish add catalog lines for the connector pages you saw and didn't rely on (`AGENTS.md`, Working style).
- No public mention means `unknown`, never "they don't have it".
- Flag cards older than 6 months as stale; don't use stale cards externally without rechecking.
- Customer-reported competitor claims are useful signals but `low` confidence until confirmed.
- Anything going external (battlecards, sales content) must be checked with `marketing-check`.
