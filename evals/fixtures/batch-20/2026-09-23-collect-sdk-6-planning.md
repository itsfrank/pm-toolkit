# Collect SDK 6.0 planning

Owner: Ingestion team (Rafael Osei, staff engineer; PM Wen Liu) | Status: planning draft | Updated: 2026-09-23

This document scopes the next major version of the Kestrel Collect SDKs. It is a planning document for the Ingestion team and its partners, not a public announcement.

## Why a major version
The 5.x line has accumulated deprecations, and several fixes need breaking changes: the batching API, the retry defaults and the way consent flags are passed. The ingest v3 pipeline also gives us a chance to simplify client behaviour, since the server now handles dedupe.

## Scope
| Area | Change | Notes |
|---|---|---|
| Batching | Single configuration object replaces three flags | Migration helper provided |
| Retries | Exponential backoff by default | Configurable ceiling |
| Consent | Consent state passed per event | Matches Govern's data model |
| Offline spool | Size limit enforced by default | Prevents unbounded disk use on mobile |
| Typing | Full type definitions in the JavaScript and Python SDKs | Removes the separate types package |
| Runtime support | Raise the minimum supported runtimes | See below |

## Runtime support
Collect SDK 6.0 drops support for Python 3.8. The Python SDK will continue to support the newer Python versions that are still maintained upstream at release time. The JavaScript SDK will drop the oldest Node line as well; Tomas will confirm the exact version once we have usage data.

Data on who is affected: we are running a query on SDK version and runtime headers from the last 30 days to find tenants still on the oldest runtimes. Customer Success will receive the list before any communication.

## Timeline
- Design review for the breaking changes: this month.
- Migration guide draft: alongside the beta.
- SDK 6.0 beta targeted for January 2027. This is an engineering target, not a customer commitment, and nothing should be announced externally until the beta plan is signed off.
- GA: to be decided after the beta feedback.

## Dependencies
- Ingest v3 pipeline rollout (Ingestion team).
- Govern consent model alignment (Govern team; Lukas Brenner is the contact).
- Docs: a new SDK reference site section (Docs team).
- Partner SDK wrappers: a heads-up to partner engineering through the partner newsletter once dates firm up.

## Risks
1. The migration helper might not cover custom transports. We will survey the top accounts that use them.
2. Mobile SDK parity: the iOS and Android SDKs share design but not code, so changes land at different speeds.
3. Documentation lag: the previous major release had stale docs for weeks. We will treat docs as part of the definition of done.

## Open questions
- Should the SDK ship a compatibility shim for the old consent flags for one minor version?
- Do we publish a long-term-support branch for 5.x, and for how long?
- Who owns the migration support rota during the beta?

## Attendees of the planning session
Rafael Osei, Wen Liu, Anja Petrov, Mei Arakawa (for infrastructure input) and Aisha Karim (for Govern consent alignment).

## Communication plan (draft)
- Internal heads-up to Support Engineering and Customer Success once the design review closes.
- A short engineering blog post when the beta opens, written by Anja Petrov.
- A changelog entry per pre-release.
- Office hours for partners who maintain wrapper libraries, run by Wen Zhao.
