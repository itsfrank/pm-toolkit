# Retro: Insights migration tooling

Owner: Bea Santos (Insights EM, facilitator) | Status: final | Updated: 2026-10-05

Retrospective on the Insights v1-to-v2 migration assistant: what we built, what worked, what did not, and what we change next. Attendees: Bea Santos, Kai Lund, Jonah Feld, Owen Hale, Ilse Mortensen and two engineers from the migration squad.

## Where we are
The migration assistant now converts 91% of v1 dashboards unchanged, up from 85% in April. Custom SQL tiles still need rebuilding by hand. Conversion is measured on dashboards processed by the assistant across all migrating tenants, counting a dashboard as converted unchanged when no manual edits were needed after the run.

## What went well
- The conversion rate improved steadily with each release of the assistant.
- Dry-run mode let customers preview results before switching, which reduced surprises.
- Pairing a support engineer with an engineer during the busiest weeks shortened the loop from ticket to fix.
- Documentation of known limitations helped Support set expectations.

## What did not go well
- Early releases changed filter behaviour on some charts without a clear warning.
- Re-linking scheduled emails after migration was manual and easy to forget.
- Progress was hard to see for large tenants, since there was no bulk status view.
- Communication about date changes reached some customers late.

## Lessons
1. Show customers a dry-run result first, always.
2. Tell people what the tool cannot convert, early and in plain words.
3. Give large customers a status view, not just a tool.
4. Keep the support loop short: one engineer on rota per week with authority to ship small fixes.

## Actions
| Action | Owner | Due |
|---|---|---|
| Bulk status view for large tenants | Kai Lund | Q4 |
| Auto re-link scheduled emails | migration squad | Q4 |
| Warning for changed filter behaviour | migration squad | next assistant release |
| Plain-language limitations page | Docs, Owen Hale | October |
| Review date-change communication process | Jonah Feld, Ilse Mortensen | October |

## Appreciation
Thanks to the support engineers who triaged tickets late into the evening during the August peak, and to the customers who allowed us to run trial migrations on real dashboards.

## Notes on process
The retro ran for 90 minutes using a start, stop, continue format. Notes were taken by Kai Lund and reviewed by all attendees before filing.

## Appendix: how conversion is measured
Each assistant run produces a report listing every dashboard, every tile, and the result for each: converted, converted with warnings, or not converted. A dashboard counts as converted unchanged only if all its tiles are in the first category. Dashboards that customers delete or archive during migration are removed from the denominator. The reports are kept for 90 days and are available to Support Engineering for troubleshooting.

## Appendix: timeline of assistant releases
| Month | Change |
|---|---|
| April | First general release; relative date handling still limited |
| June | Filter mapping improvements |
| August | Dry-run mode and clearer warnings |
| September | Fix for relative date ranges and scheduled email links groundwork |

## Open question for the next retro
Whether to publish conversion statistics to customers. Product leans against it, because the figure depends on mix; Customer Success wants something to show anxious accounts. To be discussed with Aisha Karim.
