---
name: wiki-lint
description: Health-check the PM wiki - uncited claims, stale pages, unresolved conflicts, orphan or unindexed pages, broken links, duplicate pages, missing glossary terms and long-open questions - and propose fixes. Use when the user asks to clean up, audit, lint or maintain the wiki, or periodically (suggest monthly).
---

# Wiki lint

Output: a report in chat (or `work/YYYY-MM-DD-wiki-lint.md` if long). Fix only after the user
approves; small mechanical fixes (index lines, broken relative links) can be batched.

## Checks
1. **Uncited facts:** lines in `pages/` stating facts without `[S-NNNN]` or a label.
2. **Dangling citations:** `[S-NNNN]` with no matching source card.
3. **Staleness:** pages with `updated` older than 90 days, and facts resting only on
   sources older than 6 months, in areas that change fast (status, dates, owners, roadmap).
4. **Conflicts:** pages with entries under `## Conflicts`; propose who could resolve each.
5. **Index drift:** pages missing from `INDEX.md`, index lines pointing nowhere, wrong status.
6. **Orphans and duplicates:** pages with no inbound links; pages that look like the same
   entity under different names (suggest merging and adding aliases).
7. **Glossary gaps:** capitalized terms or acronyms used on 3+ pages but not in `glossary.md`.
8. **Open questions:** count by page; list the oldest.
9. **Unused sources:** cards whose `Filed into` is empty.
10. **Lens promotion:** review-log entries not yet reflected in `lenses.md`. Propose a lens
    probe for any `review` or `backfill` entry, and for any pattern seen two or more times
    across entries of any origin (`asked`, `confirmed-sim` included). A single
    `confirmed-sim` or `asked` entry stays in the log until it recurs.

## Report format
Counts per check, then the top 10 fixes ranked by how much they would mislead a reader if
left alone.
