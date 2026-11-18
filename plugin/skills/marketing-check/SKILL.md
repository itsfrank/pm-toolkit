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
2. **Raw details (don't skip):** build a term list from the claims' subjects (products,
   features, regions, data types, certifications) and their glossary aliases, and run
   `python3 tools/wiki.py raw-hits <terms...>`. It prints raw-file lines matching a term
   that no card or page mentions; limitations that contradict a claim often sit only there.
   Read each reported line in context.
3. **Unread pages:** if `wiki/catalog/` has catalogs, run
   `python3 tools/wiki.py catalog-search <terms...>`. For the hits that bear on a claim (up
   to about five), fetch each page (read-only connector, or its `file:` export), save it to
   `wiki/raw/` with a card, use it, and tick its line with `catalog-mark`. List the other
   relevant hits under `## Unread pages` with their links.
4. Check each claim against product pages, source cards, the raw details and approved
   answers. Assign:
   - `ok`: supported by an authoritative source, in the stated scope.
   - `narrow`: true only for some products, plans, deployment models or versions. Say which.
   - `unsupported`: no source. Ask the owner or cut.
   - `wrong`: contradicted by a source.
   - `roadmap`: describes unreleased work. Needs explicit approval.
   - `risky`: legal or reputational risk (absolute claims like "only", "first", "100%",
     unsourced competitor comparisons, customer names without approval, compliance
     certifications not held).
5. Write the review as a table of claims with status, source and suggested rewrite, then
   the top issues in priority order. Under `## Raw details not in the wiki`, write one line
   per file `raw-hits` reported, stating its new fact in your own words [S-NNNN]; never
   group files or write "used as cited". Then say which claim it affects, or why none.
6. If writing new copy, use only `ok` claims and phrase `narrow` claims with their scope.

## Rules
- Save fetched connector pages with `wiki.py save-fetched`, and before you finish add catalog lines for the connector pages you saw and didn't rely on (`AGENTS.md`, Working style).
- Positioning and tone are the marketer's call; focus on truth, scope and risk.
- Never strengthen a claim beyond its source.
