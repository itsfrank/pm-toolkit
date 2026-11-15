# PRD: Usage Alerts (v0.3, draft for review)

Owner: Sam Whitlock, PM | Status: draft | Updated: 2026-05-20

## Summary
Let workspace users define alerts on event volumes and metrics in Kestrel Insights and get
notified by email or webhook when a threshold is crossed.

## Problem
Customers find out about tracking breakages and traffic spikes days later, when someone
opens a dashboard. Support sees 30–40 tickets a month that start with "our numbers dropped
last week and nobody noticed".

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
| R2 | Email and webhook notifications, including a sample of matching events | must |
| R3 | Mute, edit and delete alerts | must |
| R4 | Alert history page per alert | should |

## Success metrics
- Number of alerts created per week.

## Rollout
Beta to 20 Team and Enterprise workspaces in July, GA in Q3.

## Open questions
- Webhook retry policy.
