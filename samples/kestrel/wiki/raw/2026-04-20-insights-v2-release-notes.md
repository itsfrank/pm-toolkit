# Release notes: Kestrel Insights v2 (GA)

Published: 2026-04-20. Owner: Insights team (Jonah Feld). Audience: customers (external).

## New in v2
- Rebuilt dashboard engine: median dashboard load 1.1 s (v1: 3.4 s).
- Shared dashboards with view-only links for Enterprise.
- Funnels with up to 20 steps.

## Insights v1 deprecation
- v1 is deprecated as of this release.
- 2026-12-01: v1 becomes read-only.
- 2027-03-31: v1 is removed. Dashboards not migrated by then are archived for 90 days.
- A migration assistant converts v1 dashboards; about 85% convert without changes.

## Architecture changes
- Query result caching: v1 stores cached query results in a shared cache cluster in
  us-east-1 for all tenants. v2 caches results in the tenant's Warehouse region.
- v2 queries run against Kestrel Warehouse directly; no separate v1 aggregation store.

## Known issues
- Custom SQL tiles from v1 must be rebuilt by hand.
