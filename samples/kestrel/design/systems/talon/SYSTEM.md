---
title: Talon
updated: 2026-09-28
---
# Talon

Kestrel's design system: calm and dense. A dark navy sidebar, light grey canvas, white cards
with thin borders and almost no shadow, one teal accent used sparingly.

## Layout
- Fixed sidebar (220 px), 56 px header with breadcrumbs above the page title, content on a
  12-column grid with 16 px gaps and 24 px page padding.
- Spacing scale 4 / 8 / 12 / 16 / 24.

## Type
- Inter, falling back to the system sans. 14 px body, 13 px tables and controls, 22 px page
  titles and KPI values. Weights 400 and 600 only.

## Color usage
- Teal accent (`--color-accent`) only for the primary action, the active nav item and the
  active tab. Never for chart series or decoration.
- Status colors only inside `.status`.

## Components
See `kit.html`. Card, KPI card, table (numbers right-aligned), status, tabs, buttons
(one primary per view), sidebar, header.

## Icons
- 16 px outline icons, 1.5 px stroke, `currentColor`.

## Do and don't
- Do keep one primary button per view, top right of the card or page.
- Don't use filled colored backgrounds for status.

## Corrections
- 2026-09-14: Status is a colored dot and sentence-case text (`.status`), never a filled or
  uppercase pill. Was: filled uppercase pills. (PM correction)
- 2026-09-28: Table headers are sentence case on a light grey band, never uppercase.
  Was: uppercase headers. (PM correction)

## References
- refs/2026-09-10-insights-overview.png: Kestrel Insights overview dashboard, shipped v2,
  captured 2026-09-10.
