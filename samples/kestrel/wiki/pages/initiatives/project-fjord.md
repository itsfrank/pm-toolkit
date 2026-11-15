---
type: initiative
status: reviewed
updated: 2026-09-10
aliases: [Fjord, EU region, Warehouse EU region]
sources: [S-0004]
---

# Project Fjord

Infrastructure initiative to give Enterprise tenants an EU home region (AWS eu-central-1)
for Kestrel Warehouse storage and query compute. [S-0004]

## Key facts
- Status: beta since 2026-09-01 with 3 design-partner tenants; new tenants only. [S-0004]
- Target GA 2027-02-15: engineering target, not approved for external communication. [S-0004]
- Out of scope: Collect ingestion, Insights, Connect, support tooling; those owners must
  assess their own data paths. [S-0004]
- Estimated run-rate $520k/year for the region. [S-0004]
- Migration of existing US tenants: not designed. [S-0004]

## People and ownership
- Infrastructure team; design author Mei Arakawa; reviewers Tomas Lindqvist, Priya
  Natarajan. [S-0004]

## Related
- [Kestrel Warehouse](../products/kestrel-warehouse.md)
- [2024 decision: EU region not now](../decisions/2024-05-eu-region-not-now.md)
- [Regional access policies](govern-regional-access-policies.md): depends on Fjord metadata.

## Conflicts
- None recorded.

## Open questions
- Pricing for EU-homed tenants → Pricing & Packaging (Marco Bellini).
