---
name: prd
description: Draft or revise a PRD from a discovery work folder (intake, landscape, coverage, answered questions), with every claim traceable to a source and open questions explicit. Use when the user asks to write, draft, update or restructure a PRD or product spec.
---

# PRD

Input: `work/<slug>/` (ask, intake, landscape, coverage, questions) and the wiki. If there's no
discovery yet, say so and offer `pre-prd`; draft anyway only if the user insists, with gaps
labeled. If the organization has its own PRD template (check `wiki/pages/topics/` and ask),
use its structure and keep these rules.
Output: `work/<slug>/prd.md`. On revision, keep a short changelog at the bottom.

## Template
```
# <Title>
Status: draft | Owner: <PM> | Updated: <date> | Decision needed: <what, by whom, by when>

## Summary
Five lines: problem, who, proposal, why now, the main open risk.
## Problem
Evidence (cited). Who is affected: user / buyer / operator. Current workaround. Cost of
inaction.
## Goals and non-goals
## Context
What exists today and what's in flight (from landscape.md), and how this fits. Owners.
## Requirements
| ID | Requirement | Priority (must/should/could) | Rationale and evidence | Acceptance criteria |
Cover failure and degraded behavior, not only the happy path.
## Options considered
Status quo, a smaller option, the proposal, and the main alternative. Tradeoffs. Effort
estimates are `(assumption)` until engineering confirms.
## Cross-functional impact
Security, privacy, compliance, data, compatibility and migration, packaging and pricing,
go-to-market, support, docs: one line each, or "n/a: reason".
## Success metrics
Outcome metric (definition, baseline, target), leading signals, guardrails, instrumentation.
## Rollout
Phases, beta, flags, rollback, dependencies with owners and dates.
## Risks and open questions
| Question / risk | Owner | Blocking? | Status |
## Sources
S-ids used, with titles.
```

## Rules
- Requirements describe behavior and outcomes, not implementation, unless a constraint is real
  and sourced.
- Every factual claim is cited or labeled. Coverage gaps from `coverage.md` that are still open
  appear in the risks table, never silently dropped.
- No roadmap dates or customer commitments unless a source shows they're approved.
- After drafting, suggest `critical-review`.
