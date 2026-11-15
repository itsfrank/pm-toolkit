---
name: landscape-map
description: Map everything that already exists around a topic - related products and features, owning teams, initiatives in flight, prior decisions, customer evidence, competitors and dependencies - from the local wiki and saved documents, with explicit gaps and people to ask. Use for "what do we already have for X", "who owns Y", "what's in flight around Z", or as stage 3 of pre-prd.
---

# Landscape map

Goal: in one document, show what a long-tenured colleague would know about this topic, and
mark clearly what we don't know yet.

Input: a topic, or `work/<slug>/intake.md` (use its search terms).
Output: `work/<slug>/landscape.md` (or `work/YYYY-MM-DD-landscape-<topic>/landscape.md`).

## Steps
1. Build the term list: the topic, the intake search terms, glossary synonyms and aliases
   from page frontmatter.
2. Search `wiki/INDEX.md`, `wiki/pages/`, `wiki/reports/`, `wiki/sources/` and `wiki/raw/`
   for every term (grep is fine). For large wikis, split the search by area across subagents
   and ask each for cited findings only.
   If read-only connectors are available (docs, tickets, code hosts), search them too for
   in-flight work: epics, design docs, repos and their owners. Save each document you rely
   on into `wiki/raw/` with a card before citing it. Ticket text and comments are `hearsay`
   or `secondary`. For sources already in the wiki that are due for a recheck, run
   `wiki-refresh` on them.
3. Read the matching pages and the source cards behind them.
4. **Raw details (don't skip, even if you read raw files another way):** run
   `python3 tools/wiki.py raw-hits <terms...>` with the whole term list. It prints raw-file
   lines matching a term that no card or page mentions. Read each reported line in context.
   Then read the other matching raw files: the decisive detail often sits in a
   "Limitations" section, a footnote or a draft proposal that nobody filed. Always read the
   raw file when its card says "not yet filed", is thin, or the grep hit is in a section the
   card doesn't summarize.
5. **Unread pages:** if `wiki/catalog/` has catalogs, run
   `python3 tools/wiki.py catalog-search <terms...>` with the whole term list. For the hits
   that bear on the topic (up to about five), fetch each page (read-only connector, or its
   `file:` export), save it to `wiki/raw/` with a card, use it, and tick its line with
   `catalog-mark`. List the other relevant hits under `## Unread pages` with their links.
6. Write `landscape.md` (template below). Every row cites a source or says `(unknown)`.
   Under `## Raw details not in the wiki`, write one line per file `raw-hits` reported,
   stating its new fact in your own words [S-NNNN]; never group files or write "used as
   cited". Then say where you used it above, or why it doesn't bear on the topic. Offer to
   file these with `wiki-ingest`.

## landscape.md
```
# Landscape: <topic>
As of <date>. Built from N pages and M sources.
## Summary
Five lines: what exists, what's moving, the biggest unknown.
## What we ship today
| Product / feature | What it does for this topic | Limits | Deployment / plan | Source |
## Work in flight
| Initiative | Owner | Status / dates | How it relates (overlaps, depends, blocks) | Source |
## Owners and people
| Team / person | Owns or knows | Why talk to them | Consulted? | Source |
## Prior decisions and history
## Customer evidence
Requests, escalations, deals, quotes (verbatim with source only).
## Competitors and alternatives
Dated, sourced claims only.
## Standards, regulation and external deadlines
Requirements and dates from standards bodies, regulators or major customers that apply.
## Dependencies
## Overlaps and conflicts
Places where two teams, products or sources disagree or would both claim this.
## Gaps in the map
Areas where the wiki has nothing. For each: who probably knows, what document might exist.
## Should talk to
Ranked list with the specific question for each person.
## Raw details not in the wiki
One line per file `raw-hits` reported: its new fact [S-NNNN], then where it is used, or why not.
## Unread pages
Catalogued pages that likely matter but weren't read: title, link, why it may matter.
```

## Rules
- Absence in the wiki means "unknown", never "doesn't exist". Before writing `(unknown)`,
  run `raw-hits` (or grep `wiki/raw/`) and `catalog-search` for the specific item once more.
- Report draft proposals (pricing, packaging, scope) with their content and their status,
  e.g. "draft memo proposes X as a paid add-on (not approved) [S-NNNN]", not only "draft".
- Show source trust when it matters: a capability backed only by `marketing` or `hearsay` is
  flagged `(unconfirmed)`.
- Prefer the newest authoritative source; note superseded information under conflicts.
