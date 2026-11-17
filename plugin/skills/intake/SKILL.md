---
name: intake
description: Turn a broad or ambiguous product ask into a framing brief - interpretations, the underlying problem, assumptions, what done looks like, ranked questions, search terms and people to ask. Use when the user receives a new ask or request, or says "help me understand what they're asking for".
---

# Intake: frame the ask

Input: `work/<slug>/ask.md` (create it with the user if missing) plus the wiki.
Output: `work/<slug>/intake.md` and `work/<slug>/questions.md`.

## Steps
1. Read `ask.md`, `wiki/INDEX.md`, `wiki/glossary.md` and `wiki/pages/topics/about-me.md` if
   present. Skim wiki pages whose names or aliases obviously match the ask, and reports in
   `wiki/reports/INDEX.md` on related topics (overlap scans especially);
   `python3 tools/wiki.py find <the ask's key terms>` lists both. If read-only
   connectors are available, run a few searches for the ask's key terms to spot related
   work in flight; cite what you rely on after saving it (`wiki-ingest`), otherwise list it
   as leads to check. If
   `wiki/catalog/` has catalogs, run `python3 tools/wiki.py catalog-search` on the key terms
   and list relevant unread pages as leads with their links.
2. Write `intake.md` with the sections below. Keep it to two pages or less.
3. Write or extend `questions.md` grouped by who should answer, with a priority
   (**blocking** / important / nice), and an empty answer field.

## intake.md
```
# Intake: <short title>
## The ask (verbatim)
## Interpretations
2–4 plausible readings of what is being asked. Check each layer the ask could live at: our
own operations or internal tooling, a customer-facing product capability, the platform or
protocol level, and a compliance or standards obligation. Separate "we should do X" from
"our product should support, show or manage X for customers"; for a PM, the second is often
what's meant. Weight readings by what the PM's own product does (`about-me.md`, product
pages). For each reading: what it would mean to build, who it serves, rough size. Mark the one the evidence favors and why. Ask-as-solution check: if the
ask names a solution, state the problem it might be solving.
## Underlying problem hypotheses
Who hurts, how we know (cite or label), what happens if nothing is done.
## What "done" looks like for the requester
Deliverable expected (PRD, decision, estimate, answer), decision it feeds, deadline.
## Scope guesses
Likely in / likely out / unclear.
## Assumptions
Each with: why we believe it, how to check, what changes if it's wrong.
## Search terms
Synonyms, internal names, acronyms, adjacent concepts, standards and competitor terms to use
in `landscape-map`. Include terms from the glossary.
## People to ask first
Roles or names from wiki team pages, and what each probably knows.
## Questions for the requester now
The 3–5 cheapest clarifications that would most change the direction.
```

## Rules
- Don't research outside the workspace here; that's `landscape-map`.
- Every factual statement is cited `[S-NNNN]` or labeled `(inferred)`, `(assumption)`, `(unknown)`.
- Prefer questions that a single person can answer in one message.
