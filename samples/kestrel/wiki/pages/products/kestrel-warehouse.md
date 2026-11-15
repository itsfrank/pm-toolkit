---
type: product
status: reviewed
updated: 2026-09-10
aliases: [Warehouse, KW, event store]
sources: [S-0001, S-0002, S-0004]
---

# Kestrel Warehouse

Managed event storage and query engine behind every Kestrel product. [S-0001]

## Key facts
- Per-tenant retention: 13 months Enterprise, 6 months Growth, 3 months Starter. [S-0001]
- Production region AWS us-east-1. [S-0001]
- EU home region (eu-central-1) in beta under Project Fjord since 2026-09-01, new tenants
  only. [S-0004]
- Tenant home region is set at creation and cannot be changed in beta. [S-0004]

## People and ownership
- Infrastructure team: EM Tomas Lindqvist, staff engineer Mei Arakawa. [S-0002]

## Related
- [Project Fjord](../initiatives/project-fjord.md): EU region.
- [Kestrel Collect](kestrel-collect.md): writes events into Warehouse.

## Conflicts
- None recorded.

## Open questions
- How are existing US tenants migrated to the EU region? → Mei Arakawa.
