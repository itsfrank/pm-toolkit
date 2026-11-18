# Insights weekly status, week of 2026-09-14

From: Jonah Feld | Date: 2026-09-14 | To: Product and Engineering leads, Customer Success, Support Engineering

Hi all, here is the weekly Insights status. Short version: v2 adoption keeps climbing, the migration backlog is the main risk, and I am changing one date because of it.

## Headlines
- Insights v1 goes read-only on 2027-01-15. This moves from the previously announced 2026-12-01 because of the migration backlog. The removal date of 2027-03-31 is unchanged.
- Dashboard share-links for v2 shipped to all plans on Tuesday with no incidents.
- The migration assistant ships a small fix this week for charts that use relative date ranges.
- Customer Success: please do not tell customers a new removal date; only the read-only date has changed. A customer note goes out on Thursday through the usual lifecycle email.

## Migration numbers
The backlog is mostly large Enterprise tenants with many shared dashboards. Bea's team is staffing a second migration squad from the Insights pod for October.

| Item | Status |
|---|---|
| Tenants fully migrated (all plans) | tracked in the migration board, updated Fridays |
| Enterprise tenants still on Insights v1 | 312 as of 2026-09-11 |
| Migration assistant runs this week | 1,904 dashboards processed |
| Open migration support tickets | 61, down from 74 last week |

Of the Enterprise tenants still on v1, a large share have already started a trial migration but have not switched their default workspace. Customer Success will reach out to those first, since they are the closest to done.

## Delivered this week
- v2 chart editor: keyboard shortcuts for duplicate and move tile.
- Fixed a timezone bug where weekly buckets started on Sunday for workspaces set to Monday week start.
- Performance: cached dashboard filter lists, which removed a slow query on the first load of large dashboards.
- Docs: new "Moving from v1 to v2" walkthrough with screenshots.

## In progress
1. Folder permissions for v2 dashboards (design review on Wednesday).
2. Scheduled email reports: backend work is done, UI polish remains.
3. Usage Alerts integration: Sam Whitlock's team needs the chart-level threshold hook; we agreed on the interface last week.
4. Tile-level comments (spike only, no commitment).

## Risks
- Migration backlog, described above. The mitigation is the second squad plus more targeted outreach.
- Two customer-facing docs still mention the old v1 date. Docs owner has the list and will fix them by Friday.
- Staffing: one engineer is out for two weeks in October. We have covered the on-call rota.

## Asks
- Support Engineering: share the top five migration questions from tickets so we can add them to the walkthrough.
- Customer Success: send me the list of accounts that asked for a date extension; I want to see whether they cluster in a single segment.
- Sales: please hold off on promising bespoke migration help until we agree what the help desk offers.

## Next week
- Folder permissions decision.
- Second migration squad kickoff.
- Review the metrics for the share-links launch.

Questions to me directly or in the Insights channel. Thanks, everyone, for the quick turnaround on the date change discussion last week.

Jonah

## Appendix: share-links launch detail
Share-links let a dashboard owner generate a read-only link that respects workspace roles. Early numbers from the first three days:
- Links created: 410, across 96 workspaces.
- Support tickets mentioning share-links: 3, all about expired links.
- Open design question: whether links should expire by default. Product leans towards 30-day expiry with a visible banner, to be decided in the next design review.
