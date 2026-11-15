# Project Fjord: Kestrel Warehouse EU region (design doc)

Owner: Infrastructure team. Author: Mei Arakawa. Reviewers: Tomas Lindqvist, Priya Natarajan.
Created 2026-07-14, last updated 2026-09-03. Status: Approved design; region in beta.

## Goal
Let Enterprise tenants choose an EU home region for Kestrel Warehouse storage and query
compute. Region: AWS eu-central-1.

## Scope
- In scope: Warehouse storage, query engine, tenant metadata for EU-homed tenants.
- Out of scope: Kestrel Collect ingestion (Ingestion team), Kestrel Insights, Kestrel
  Connect, support tooling. Owners of those must assess their own data paths.

## Status and dates
- Beta started 2026-09-01 with 3 design-partner tenants (new tenants only; no migration).
- Migration of existing US tenants: not designed yet.
- Target GA: 2027-02-15. Engineering target only; not approved for external communication.

## Cost
Shared control plane keeps the run-rate at an estimated $520k/year for the region
(compare $1.4M/year in the 2024 estimate, D-2024-07).

## Design notes
- Each EU tenant's Warehouse data is written and queried only in eu-central-1.
- Ingestion path: unchanged. Collect routes EU tenant events to the EU Warehouse writers.
- Tenant home region is set at tenant creation and cannot be changed in beta.

## Backup and disaster recovery
Not covered in this document.

## Open issues
- Migration tooling for existing tenants (owner: Infrastructure, unscheduled).
- Pricing of EU-homed tenants (owner: Pricing & Packaging).
