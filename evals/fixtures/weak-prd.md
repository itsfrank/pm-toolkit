# PRD: EU Data Residency for Enterprise
Status: draft | Owner: Sam Whitlock | Updated: 2026-10-20 | Decision needed: approve for build, VP Product, 2026-11-15

## Summary
Enterprise customers want their data in the EU. Kestrel already offers full EU data
residency today through the Frankfurt region, so this PRD is about packaging it, making it
self-serve and telling the market.

## Problem
Enterprise customers keep asking about EU data residency. Brightwater Retail said "We can't
renew in March without a clear answer on EU data residency." [S-0010]

## Goals and non-goals
- Goal: every Enterprise tenant can choose the EU region at signup.
- Goal: launch "Kestrel EU" in January 2027.
- Non-goal: changes to ingestion; Collect already supports EU tenants.

## Context
Full EU residency is available today [S-0007]. Project Fjord delivers the EU Warehouse
region [S-0004]. Collect already has an EU endpoint [S-0012].

## Requirements
| ID | Requirement | Priority | Rationale | Acceptance criteria |
|---|---|---|---|---|
| R1 | Region picker at tenant creation | must | customer asks | EU selectable |
| R2 | EU residency badge in Insights | should | marketing | badge visible |
| R3 | Residency add-on SKU at 18% of platform fee | must | pricing memo | SKU live |
| R4 | Migrate existing tenants to EU | could | Brightwater | tenant moved |

## Options considered
Only the proposal; the status quo is not viable.

## Cross-functional impact
- Security and privacy: covered by Fjord.
- Support: n/a, no change.
- Pricing: residency add-on as in the pricing memo.

## Success metrics
- 30 EU tenants by end of FY27.

## Rollout
GA on 2027-01-12, all Enterprise customers.

## Risks and open questions
- None blocking.

## Sources
S-0004, S-0007, S-0010, S-0012
