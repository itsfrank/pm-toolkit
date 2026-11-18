# PRD: Usage Alerts (v1.1, approved)

Owner: Sam Whitlock, PM | Status: approved in product review 2026-09-18 | Updated: 2026-09-18 | Supersedes: v1.0 (2026-07-08)

## Summary
Let workspace users define threshold alerts on event volumes and metrics in Kestrel
Insights and be notified by email or webhook when a threshold is crossed.

## Changes from v1.0
Two changes, both driven by beta feedback and the Enterprise packaging discussion. Everything else in v1.0 is unchanged.
- Faster notifications for Enterprise workspaces (see Goals).
- Higher alert limit for the Team plan (see Packaging).

## Problem
Customers learn about tracking breakages and traffic spikes days later, when someone opens a
dashboard. Support sees 30–40 tickets a month that begin with "our numbers dropped last week
and nobody noticed".

## Goals
- Users can create threshold alerts on any Insights v2 chart.
- Notifications by email and webhook within 10 minutes of the threshold being crossed. For Enterprise workspaces only, notifications arrive within 2 minutes of the threshold being crossed; Free and Team stay at 10 minutes.

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
Team plan alerts per workspace are raised from 25 to 50.

| Plan | Alerts per workspace |
|---|---|
| Free | 3 |
| Team | 50 |
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

## Review notes (2026-09-18 product review)
Attendees: Sam Whitlock, Jonah Feld, Bea Santos, Marco Bellini, Mei Arakawa. The review approved the two changes above. Mei confirmed that evaluation cadence for the faster path needs a separate scheduler queue, which Infrastructure will size before rollout; the cost estimate above is carried over from v1.0 and will be refreshed once that sizing is done. Marco noted that the packaging table should be mirrored in the pricing page copy after launch communications are agreed.
