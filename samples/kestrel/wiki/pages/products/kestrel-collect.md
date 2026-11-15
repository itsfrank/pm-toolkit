---
type: product
status: reviewed
updated: 2026-09-26
aliases: [Collect, KC, ingest, ingestion SDKs]
sources: [S-0001, S-0002, S-0005]
---

# Kestrel Collect

Event-ingestion SDKs (web, iOS, Android, server) and HTTP ingestion endpoints that feed
Kestrel Warehouse. [S-0001]

## Key facts
- SDKs for web, iOS, Android and server; HTTP API for direct ingestion. [S-0001]
- Ingest v3 pipeline (edge receivers, spool, router) rolled out to 100% of tenants on
  2026-09-20. [S-0005]
- Router forwards events to Warehouse writers based on tenant home region. [S-0005]
- Throughput target 400k events/s per cluster, p99 accept latency under 120 ms. [S-0005]

## People and ownership
- Ingestion team: EM Priya Natarajan, staff engineer Rafael Osei, PM Wen Liu. [S-0002]

## Related
- [Kestrel Warehouse](kestrel-warehouse.md): destination of all events.
- [Project Fjord](../initiatives/project-fjord.md): EU-homed tenants routed by Collect.

## Conflicts
- None recorded.

## Open questions
- SDK deprecation policy for v2-era SDK versions → Wen Liu.
