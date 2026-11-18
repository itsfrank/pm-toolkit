# Insights v2 performance report: September 2026

Owner: Insights engineering (Kai Lund, report author) | Status: reviewed by Infrastructure | Updated: 2026-09-30

This report summarises dashboard performance for Insights v2 over the four weeks to 2026-09-27, using real-user timings from the browser instrumentation and server-side traces. It covers all plans. Audience: Insights and Infrastructure teams, Product, Support Engineering.

## Method
- Load time is measured from navigation start to the last visible tile rendered.
- Only dashboards with at least 5 tiles are included, to avoid skewing from trivial pages.
- Sample: about 2.1 million dashboard loads from roughly 3,800 workspaces.
- Percentiles are computed per day and then averaged across the period.

## Headline results
- Insights v2 p95 dashboard load time is 2.8 seconds. The median stays 1.1 s.
- The slowest 5% of loads are dominated by dashboards with many tiles and cold caches.
- Cache hit rate on the filter-list endpoint rose after the change shipped in September.

## Breakdown by dashboard size
| Tiles | Share of loads | Notes |
|---|---|---|
| 5 to 10 | majority | Fast; mostly cached |
| 11 to 20 | substantial | Where most of the p95 tail starts |
| More than 20 | small | Slowest; benefits from lazy loading |

## Custom SQL tiles
Custom SQL tiles are about 40% slower in v2 than in v1. This is under investigation and the cause is unknown. Hypotheses we have not yet confirmed or ruled out: a different query planner path, extra result serialization, and cache keys that no longer match. Kai has opened an investigation ticket and Infrastructure has offered to help with traces. We do not yet have a fix or a date; please do not promise customers one.

## What improved
1. Filter list caching removed a slow query on first load.
2. Tile rendering is now parallel for tiles that do not depend on each other.
3. Chart library upgrade reduced client-side render time on large tables.

## What we are watching
- Memory use in the browser for dashboards with many tiles.
- Variation between regions, since latency to the nearest data centre matters.
- Tenants with unusually high numbers of dashboard filters.

## Recommendations
- Continue the investigation of custom SQL tiles with a clear owner and weekly update.
- Add a performance budget to the release checklist for dashboards.
- Publish a short guide for customers on speeding up heavy dashboards.
- Share this report with Support Engineering so they have the context for performance tickets.

## Next steps
| Action | Owner | Target |
|---|---|---|
| Trace comparison of v1 and v2 custom SQL | Kai Lund, Infrastructure | October |
| Customer guide on heavy dashboards | Docs | October |
| Budget in release checklist | Jonah Feld | next release |

## Appendix: instrumentation notes
Browser timings come from the standard performance API; ad blockers can reduce sample coverage slightly. Server traces are sampled at one in fifty requests. Results exclude embedded dashboards.

## Appendix: glossary and definitions
- Cold cache: the first load of a dashboard after a deployment or after cache expiry.
- Tile: a single chart or table on a dashboard.
- Real-user timing: measurements collected from customers' browsers, as opposed to synthetic tests.
- Heavy dashboard: a dashboard with more than 20 tiles or with several custom queries.

## Appendix: reviewers
Reviewed by Mei Arakawa (Infrastructure), Bea Santos (Insights EM) and Jonah Feld (Insights PM). Comments were incorporated on 2026-09-29. The raw data export is available from the Insights engineering folder on request.
