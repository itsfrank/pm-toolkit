---
name: gap-analysis
description: Compare a set of requirements (from a customer, RFP, standard, regulation, market segment or competitor) against current product capabilities, producing a cited meets / partial / gap / unknown matrix with workarounds and themes. Use for "gap analysis", "how do we stack up against X requirements", "what are we missing for segment Y".
---

# Gap analysis

Input: the requirements source (a saved doc, a list from the user, a standard or a competitor
page in `wiki/raw/`) and the scope: which products, versions, deployment models and plans.
Output: `work/YYYY-MM-DD-gaps-<topic>/gaps.md`.

## Steps
1. Confirm scope with the user if unspecified. Deployment model and plan often change answers.
2. Normalize the requirements into atomic rows, each with an ID and the source wording.
   Split compound requirements ("A and B").
   Record each requirement's deadline or milestone dates, cited to the standard, regulation
   or customer document that sets them, and list them in a timeline in the summary.
3. For each row, search product pages and source cards (`python3 tools/wiki.py find`
   searches both), then the catalogs
   (`python3 tools/wiki.py catalog-search`) for unread pages that may settle it. Assign:
   - `meets`: authoritative source shows it, in scope.
   - `partial`: some of it, or with conditions. Say what's missing.
   - `gap`: authoritative source shows it's not supported.
   - `unknown`: no source either way. Never convert unknown into gap.
     Use `partial` only when a source shows part of it; if nothing does, it is `unknown`.
4. Note workarounds (cited), in-flight work that would close the gap (from initiative pages,
   with status), and how competitors handle it if sourced and dated.
5. Group the gaps into themes and rank by impact (how many requirements, how important to the
   requester, deal or segment size if known).

## gaps.md
```
# Gap analysis: <requirements source> vs <products, scope>
As of <date>.
## Summary
Counts by status. Top 3 themes. Biggest unknowns.
## Matrix
| ID | Requirement | Deadline | Status | Evidence | Workaround | In flight | Notes |
## Themes
Per theme: the gaps, impact, options (build, partner, document workaround, accept).
## Unknowns to resolve
| ID | Question | Who knows |
```

## Rules
- Be precise about scope: "meets (SaaS, Enterprise plan)" not just "meets".
- Marketing sources alone can't establish `meets`; mark `partial (unconfirmed)` and ask.
