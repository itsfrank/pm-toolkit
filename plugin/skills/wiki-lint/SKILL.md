---
name: wiki-lint
description: Health-check the PM wiki - uncited claims, stale pages, unresolved conflicts, orphan or unindexed pages, broken links, duplicate pages, missing glossary terms and long-open questions - and propose fixes. Use when the user asks to clean up, audit, lint or maintain the wiki, or periodically (suggest monthly).
---

# Wiki lint

Output: `work/YYYY-MM-DD-wiki-lint.md` (status uses its date to know when the last check
ran) and a short summary in chat. Fix only after the user approves; small mechanical fixes
(index lines, broken relative links) can be batched.

Start with `python3 tools/wiki.py lint` (add `--json` for every item). It covers the
mechanical checks: uncited candidates, dangling citations, broken links, index drift,
orphans, unused sources, raw files without cards, card fields to fill, stale pages, old
reports, sources due for a recheck and open notes. Read the flagged items before reporting
them: the uncited check is a heuristic. Index drift can be fixed with `lint --fix-index`. Then
do the judgment checks below by reading.

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
11. **Freshness:** sources due for a recheck; suggest `wiki-refresh`. Cards superseded by a
    newer version whose facts are still cited on pages.
12. **Reports:** reports missing the required header, and reports older than 60 days that
    pages or answers seem to rely on.
13. **People pages:** opinions or personal details that don't belong (see `wiki/README.md`).
14. **Open notes:** count of open and `needs-info` notes; suggest `wiki-notes`.
15. **Catalogs:** lines already carded but not ticked, ticks pointing at missing cards
    (both mechanical), and catalogued pages that recent work folders listed as unread
    leads more than once: suggest ingesting them.
16. **Unfinished runs:** `HANDOFF.md` files in `work/`; remind the PM how to continue each.

## Report format
Counts per check, then the top 10 fixes ranked by how much they would mislead a reader if
left alone.
