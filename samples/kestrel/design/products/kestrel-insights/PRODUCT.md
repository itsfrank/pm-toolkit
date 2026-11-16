---
title: Kestrel Insights
system: talon
updated: 2026-09-28
---
# Kestrel Insights

## Shell
- Sidebar, in order: Overview, Dashboards, Funnels, Retention, Data, Settings. Brand text
  "Kestrel" at the top.
- Header: breadcrumbs "Workspace name / Section", page title, actions on the right (date
  range selector, then one primary button).

## Screens
- screens/overview.html: the Overview dashboard. Faithful to the ref: KPI row, events
  chart, top events table, recent activity.

## Vocabulary
- "workspace", never "account" or "tenant". "Events", "event volume". Dates as "Oct 3, 2026".
- Event names are snake_case in monospace: `checkout_completed`.

## Data
- Workspace names like "Northwind Demo"; event volumes in the tens of thousands to millions,
  formatted with thousands separators (1,284,330).

## Corrections
- 2026-09-28: The date range selector sits left of the primary button, never in the
  sidebar. Was: sidebar filter. (PM correction)

## References
- refs/2026-09-10-insights-overview.png: Overview dashboard, captured 2026-09-10.
