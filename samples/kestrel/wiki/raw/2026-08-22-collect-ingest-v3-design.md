# Kestrel Collect ingest v3: architecture (design doc)

Owner: Ingestion team. Author: Rafael Osei. Approved by: Priya Natarajan (EM).
Created 2026-08-22. Status: Approved; rollout to 100% of tenants completed 2026-09-20.

## Overview
Ingest v3 replaces the v2 single-stage receivers with a three-stage pipeline:
1. **Edge receivers** accept SDK and HTTP API traffic at ingest.kestrel.example.
2. **Spool**: a durable queue that absorbs bursts and downstream outages.
3. **Router**: reads the tenant's home region and forwards batches to the right
   Kestrel Warehouse writers.

## Goals
- Sustain 400k events/second per cluster with p99 accept latency under 120 ms.
- Zero event loss during Warehouse maintenance windows (spool absorbs the backlog).
- Support Project Fjord EU-homed tenants via the router.

## SDK changes
- Web and mobile SDKs batch up to 50 events or 10 seconds, whichever comes first.
- Server SDKs gain retry with jitter. No customer-visible configuration changes.

## Rollout
Shadow traffic in July, 10% on 2026-08-30, 100% on 2026-09-20. No incidents.

## Limitations
1. All edge receivers and the spool run in AWS us-east-1 only. Events for EU-homed
   (Fjord) tenants are received in us-east-1 and buffered in the us-east-1 spool before
   the router forwards them to the EU Warehouse. Typical time in spool is under 5 minutes;
   during downstream incidents events can stay in the spool for up to 72 hours, then are
   purged after delivery.
2. Raw request logs (including client IP addresses) are kept for 14 days in us-east-1
   for abuse handling, for all tenants.
3. There is no EU edge receiver on the current roadmap. No estimate has been made.

## Monitoring
Spool depth and router lag dashboards; page on-call at 15 minutes of router lag.
