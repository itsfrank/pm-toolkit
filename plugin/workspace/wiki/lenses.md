# Coverage lenses

The checklist `coverage-review` walks for every ask. Each lens has probe questions. Edit
freely: add org-specific probes, mark lenses that never apply, and add the lessons from
`review-log.md` under the lens they belong to (tag them `[RL YYYY-MM-DD]`).

## 1. Problem and evidence
- What problem, for whom, observed where? Which evidence is direct vs. second-hand?
- Who asked, and what do they think "done" looks like? Is the ask a solution in disguise?
- What happens if we do nothing? Why now?

## 2. Users, buyers, operators
- Who uses it, who buys it, who deploys and runs it, who approves it? Are they different?
- Which segments, sizes, industries, regions differ in needs?

## 3. Existing products and overlap
- What do we already ship that touches this, fully or partly? Any internal duplicate?
- Which product, team or platform is the natural home? Who else will think they own it?

## 4. Work in flight
- Which initiatives, betas, re-architectures or migrations are in progress nearby?
- Is anyone already building a piece of this, or about to change something it depends on?

## 5. Prior decisions and history
- Was this proposed, tried, or rejected before? Why? What changed since?
- Are there standing decisions (architecture, pricing, platform) that constrain it?

## 6. Dependencies and interfaces
- Which teams, services, APIs, data or vendors does it depend on? Their roadmap and capacity?
- What depends on it? Who must change something for this to work?

## 7. Architecture and technical constraints
- Deployment models (SaaS, self-managed, hybrid, regions, versions) and which are in scope?
- Scale, performance, availability, latency targets? Limits of the current platform?

## 8. Security and privacy
- New data collected or exposed? Authentication, authorization, audit, secrets handling?
- Abuse cases: how could an attacker or a careless admin misuse it?

## 9. Compliance, regulation, certification
- Which regimes apply (privacy law, sector rules, government certifications)?
- Does it change an existing certification scope or a public compliance statement?

## 10. Data lifecycle
- Where is data stored, processed, replicated, backed up, and for how long? Residency?
- Import, export, deletion, retention, and what happens on downgrade or churn?

## 11. Compatibility, migration, deprecation
- Upgrade path for existing customers and configurations? Breaking changes? Rollback?
- Does it replace or deprecate something? Announced timelines and contractual notice?

## 12. Packaging, pricing, licensing
- Which plan, SKU or license includes it? Cost to serve? Does it cannibalize something?
- Third-party or open-source licensing implications?

## 13. Go-to-market
- How will sales, partners and marketing describe it? Existing claims that become wrong?
- Commitments already made to customers (deals, RFPs, escalations, roadmap promises)?

## 14. Support and operations
- Who supports it, with what runbooks, tooling and SLAs? New on-call or escalation paths?
- Observability: how do we know it works for a given customer?

## 15. Docs, enablement, UX
- Docs, training, field enablement, UI copy, accessibility, localization?

## 16. Success metrics
- Outcome metric with definition, baseline and target? Leading signals? Guardrails?
- Is the telemetry in place, and allowed?

## 17. Competition and alternatives
- How do competitors and the customer's do-it-yourself alternative handle this (dated, sourced)?
- Where is parity enough and where must we differentiate?

## 18. Rollout and risk
- Phasing, beta customers, feature flags, kill switch, rollback plan?
- Pre-mortem: it's a year later and this failed. What happened?

## 19. Organization and decision
- Who decides? Who must approve, who must be consulted, who would be surprised?
- Who has context we lack (long-tenured engineers, field, support), and have we asked them?
