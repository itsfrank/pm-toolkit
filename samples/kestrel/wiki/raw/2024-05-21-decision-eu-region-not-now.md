# Decision record D-2024-07: EU hosting region, not now

Date: 2024-05-21. Decided by: VP Product (then: Raj Mehta) with VP Engineering and CFO.
Author: Platform PM. Status: Decided.

## Context
Four Enterprise prospects asked for EU data hosting in H1 2024. Two lost deals listed it as
a factor. Infrastructure estimated a second region.

## Options
1. Full EU region (storage, ingestion, dashboards). Estimated $1.4M/year run-rate plus
   3 engineers for 3 quarters.
2. EU storage only, ingestion stays in US. Rejected by Legal at the time as "not a residency
   story customers will accept".
3. Do nothing now; revisit.

## Decision
Option 3. Cost is not justified by four requests. We will not build an EU region in FY25.

## Revisit triggers
- 10 or more qualified Enterprise requests in two quarters, or
- a regulatory driver that blocks renewals, or
- run-rate cost of a second region falling below $600k/year.

## Consequences
Sales may not promise EU hosting. The approved RFP answer states data is hosted in the US.
