# Decision D-2026-21: Warehouse cold storage tier

Owner: Mei Arakawa (Infrastructure) | Status: approved | Updated: 2026-10-03

## Decision
Decision D-2026-21, approved 2026-10-03: a cold storage tier for events older than 13 months, enabled from 2027-01-01 for the Team plan first; Enterprise later, no date.

## Context
Warehouse storage cost is dominated by older events that are rarely queried. Most queries touch the most recent months. A cold tier stores older events on cheaper storage, with slower access, so we can keep them for longer without costs growing in step.

## Options considered
| Option | Description | Outcome |
|---|---|---|
| 1 | Keep all events on the standard tier | Rejected: cost grows linearly with retention |
| 2 | Delete older events sooner | Rejected: conflicts with customer retention expectations |
| 3 | Add a cold tier for older events | Chosen |
| 4 | Offer export-only for older events | Rejected: poor customer experience |

## Consequences
- Queries over older events may be slower, and the user should see a notice when a query reads cold data.
- Support will need a macro explaining the notice.
- Pricing and Packaging will review whether the tier changes any plan limits; Marco Bellini has the action.
- Docs need a page explaining how cold data behaves.
- Infrastructure will add monitoring for cold reads and for the migration job that moves events between tiers.

## Rollout approach
1. Build and test the tiering job in staging.
2. Run a dry run on internal tenants.
3. Enable the tier according to the decision above, with a staged ramp and a rollback plan.
4. Announce to affected customers ahead of enablement, using wording agreed with Customer Success.

## Risks
- Slow queries might surprise customers who run long-range analytics. Mitigation: clear in-product messaging.
- Migration job load could affect normal queries. Mitigation: run during low-traffic windows with rate limits.
- Cost savings may be lower than modelled if cold reads are more frequent than expected. Mitigation: review after the first month.

## Decision meeting
Attendees: Mei Arakawa, Tomas Lindqvist, Marco Bellini, Aisha Karim, Owen Hale and a Finance representative. The decision was unanimous. A follow-up review is planned after the first month of operation.

## Related pages
- Kestrel Warehouse product page.
- Warehouse query limits FAQ.
- Enterprise plan repackaging initiative.

## Open follow-ups
| Item | Owner | Notes |
|---|---|---|
| Customer announcement draft | Customer Success | Needs Product review |
| In-product cold-read notice wording | Docs and Design | Short, plain language |
| Support macro | Owen Hale | After the wording is agreed |
| Cost model refresh | Finance with Infrastructure | After first month of operation |

## Background reading
The cold tier idea first came up in the Infrastructure planning offsite, where the team looked at storage growth by plan and by event age. The data showed a long tail of events that were almost never read after their first quarter. The team then prototyped a tiering job and measured retrieval times on sample tenants, which informed the notice and the rollout plan above.
