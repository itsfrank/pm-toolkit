---
name: report
description: Research a question across the wiki, saved sources and read-only connectors, and write a cited, dated report into wiki/reports/ for the PM to read in the viewer - comparisons, overlap and conflict scans across in-flight PRDs, summaries of an area, "what do we know about X". Use when the PM asks for research, a comparison, a summary or a report they will want to read or come back to, or asks to refresh an earlier report.
---

# Report

Output: `wiki/reports/YYYY-MM-DD-<slug>.md`, then `python3 tools/wiki.py reports-index`.

Hand off when another skill fits better: what exists and who owns it → `landscape-map`;
requirements against capabilities → `gap-analysis`; competitors → `competitive`. Still save
the result as a report if the PM wants to read it later.

## Steps
1. Restate the question in one line. If it is ambiguous, pick the likeliest reading, say so
   in the report, and continue; don't stop to ask unless the PM is waiting on you.
2. Check `wiki/reports/INDEX.md` for an earlier report on the same question. If one exists,
   read it and build on it; refreshing means a new dated file that links to the old one.
3. Gather evidence (`python3 tools/wiki.py find <the question's terms>` lists matching
   pages, cards and raw files): `wiki/INDEX.md` and the matching pages, the source cards behind them, and
   the raw files for decisive detail. If read-only connectors are available and the question
   is about current state (in-flight work, owners, status), search them too, and save
   anything you rely on into `wiki/raw/` with a card (`wiki-ingest` rules). Search the
   catalogs too (`python3 tools/wiki.py catalog-search <terms>`): fetch and card the unread
   pages that answer the question, tick their lines with `catalog-mark`, and list the rest
   in the report's unknowns as links.
4. Write the report. Cite every fact `[S-NNNN]` or label it. Separate what sources say from
   your analysis. Show conflicts with dates and trust levels.
5. Rebuild the index and reply with a five-line summary and the report path.
6. Offer to file durable facts you found into pages with `wiki-ingest`. Don't cite the report
   from pages.

## Report header
```
---
title: <short title>
question: <the question, as asked>
as_of: YYYY-MM-DD
sources: [S-NNNN, ...]
refreshes:          # earlier report this replaces, if any
promoted: no        # yes once its durable facts are filed into pages
---
# <Title>
**Question:** <as asked>. **As of:** <date>. **Sources read:** <count, and connectors searched>.
## Summary
```
After the summary, use whatever structure fits the question: a table for comparisons, one
section per conflict or overlap, a timeline. End with `## Unknowns and who to ask`.

## Overlap and conflict scans
For "where do these plans clash": one entry per clash with the documents involved (cited),
what clashes, the owners, the status (`open`, `raised`, `resolved`) and what would settle
it. Two accurate sources whose plans clash are an overlap, not a source conflict.

## Rules
- A report is a snapshot. Say what it doesn't cover.
- Never send or post a report; the PM shares it.
