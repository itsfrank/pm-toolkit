---
type: product
status: reviewed
updated: 2026-05-04
aliases: [Insights, dashboards, Insights Classic (v1), KI2 (v2)]
sources: [S-0001, S-0002, S-0013]
---

# Kestrel Insights

Dashboards, funnels and retention charts on top of Kestrel Warehouse. [S-0001]

## Key facts
- Insights v2 GA on 2026-04-20; median dashboard load 1.1 s vs 3.4 s in v1. [S-0013]
- v1 deprecated: read-only from 2026-12-01, removed 2027-03-31. [S-0013]
- Migration assistant converts about 85% of v1 dashboards unchanged; custom SQL tiles must
  be rebuilt by hand. [S-0013]

## People and ownership
- Insights team: PM Jonah Feld, EM Bea Santos. [S-0002]

## Related
- [Kestrel Warehouse](kestrel-warehouse.md): v2 queries Warehouse directly.

## Conflicts
- None recorded.

## Open questions
- How many Enterprise tenants are still on v1? → Jonah Feld.
