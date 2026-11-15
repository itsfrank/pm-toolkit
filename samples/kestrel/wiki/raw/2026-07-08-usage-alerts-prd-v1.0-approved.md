# PRD: Usage Alerts (v1.0, approved)

Owner: Sam Whitlock, PM | Status: approved in product review 2026-07-08 | Updated: 2026-07-08

## Summary
Let workspace users define threshold alerts on event volumes and metrics in Kestrel
Insights and be notified by email or webhook when a threshold is crossed.

## Problem
Customers learn about tracking breakages and traffic spikes days later, when someone opens a
dashboard. Support sees 30–40 tickets a month that begin with "our numbers dropped last week
and nobody noticed".

## Goals
- Users can create threshold alerts on any Insights v2 chart.
- Notifications by email and webhook within 10 minutes of the threshold being crossed.

## Non-goals
- Anomaly detection (later).
- Alerts on Insights v1 charts.

## Requirements
| ID | Requirement | Priority |
|---|---|---|
| R1 | Create an alert from any Insights v2 chart: metric, threshold, window | must |
| R2 | Email and webhook notifications, including a sample of up to 5 matching events | must |
| R3 | Mute, edit and delete alerts | must |
| R4 | Alert history page per alert | should |
| R5 | Only workspace Admins and Editors can create or edit alerts; Viewers can subscribe. Uses Govern roles where Govern is enabled | must |
| R6 | Alert history kept 13 months, then deleted; all alerts and history deleted within 30 days of workspace deletion | must |

## Packaging
| Plan | Alerts per workspace |
|---|---|
| Free | 3 |
| Team | 25 |
| Enterprise | unlimited |

## Internal tools
Event samples in alert payloads are visible in Lookout's event inspector. Lookout redacts
sample payloads by default for alert records; support staff need the customer's
case-linked consent to unredact. Support Engineering signed off 2026-07-02.

## Cost
Alert evaluation adds an estimated 4% to Insights query compute at GA volumes
(Infrastructure estimate, 2026-06-30).

## Success metrics
- Primary: share of fired alerts acknowledged (opened or muted) within 24 hours. Baseline:
  none (new feature). Target: 60% by end of beta.
- Guardrail: alert notification emails marked as spam below 0.5%.
- Tracking only: alerts created per week.

## Rollout
Beta to 20 Team and Enterprise workspaces in July, GA in Q3.

## Open questions
- Webhook retry policy: decided, 3 retries with exponential backoff.
