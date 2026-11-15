# Review log

Lessons from misses, so the same gap is never missed twice. Each entry has an origin:
`review` (real feedback), `backfill` (past comments, draft-vs-final diffs, post-mortems),
`asked` (a question we couldn't answer), `org-checklist` (the org's own checklists) or
`confirmed-sim` (a simulated-review finding the PM accepted). Recurring patterns become
probes in `lenses.md`. Logged with the `review-feedback` skill; format in its SKILL.md.

## 2026-06-12: Usage Alerts PRD missed impact on Support tooling
- **Origin:** review
- **Artifact:** work/2026-05-18-usage-alerts/prd.md (archived, not in this sample)
- **Reviewer role:** Support Engineering lead; VP Product
- **What was missed or wrong:** The PRD did not consider the Lookout support console, which
  picks up customer event samples. Support tooling was out of scope by omission. The VP
  Product noted this was the second time a PRD touching customer data skipped internal tools.
- **Lens:** 14 Support and operations
- **Why it was missed:** lens missing (lens 14 had no probe about internal tools handling
  customer data); Support Engineering not consulted.
- **The fact, with source:** Support tooling must be in scope for anything that touches
  customer data; every such PRD needs a section on internal tools that copy or display
  that data. [S-0015]
- **Fix applied:** lens added (lenses.md section 14, tagged [RL 2026-06-12]).
