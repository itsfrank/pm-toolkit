Source: https://wiki.kestrel.example/spaces/ING/pages/40117/Collect+SDK+limits (version 7)

# Collect SDK limits

Owner: Ingestion team (Priya Natarajan). Last updated 2026-09-28.

## Per-tenant limits
- Ingestion is capped at 20,000 events per second per tenant. Bursts up to 2x for 60 seconds.
- Maximum event payload: 64 KB. Larger events are rejected with HTTP 413.
- Batch requests: up to 500 events per request.

## Regions
All SDK traffic is received in us-east-1. EU-homed tenants are routed onward after receipt.
