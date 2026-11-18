# Support escalations: Q3 review

From: Support Engineering (Owen Hale, review author) | Date: 2026-09-26 | To: Product leads, Engineering managers, Customer Success

This review summarises Tier 2 escalations handled by Support Engineering in the third quarter, with themes, patterns and requests for Product and Engineering. Figures are from the ticketing system; categories are assigned by the engineer who closes the escalation.

## Summary
- Tier 2 volume was steady across the quarter, with a small peak in the second half of August after the dashboard cache change.
- 38% of Tier 2 escalations in Q3 were about Insights v1 migration.
- Median time to first engineering response improved compared with Q2, mainly because of the new triage rota.
- Collect SDK questions fell, helped by the docs refresh.

## Themes
| Theme | Share of escalations | Comment |
|---|---|---|
| Insights v1 migration | see summary | Mostly dashboards not converting cleanly, tiles with custom SQL, and permissions questions |
| Warehouse query limits | smaller | Timeouts on wide queries; the new FAQ should help |
| Collect SDK and ingestion | smaller | Mobile spool and consent flag confusion |
| Billing and plans | smaller | Plan limits and seat counts |
| Lookout and access | smaller | Customer consent for unredaction |
| Other | remainder | One-off issues |

## Insights v1 migration in detail
Typical escalation patterns:
1. A customer's dashboard converts but filters behave differently.
2. Scheduled emails stop after migration because the recipient list was tied to the old dashboard ID.
3. Customers ask whether they can stay on v1 longer. Support answers with the published lifecycle dates and escalates to Customer Success for extension requests.
4. Large tenants ask for help with bulk migration.

To handle the load, Support Engineering and the Insights team set up a migration help desk. The migration help desk closes four weeks after v1 goes read-only on 2027-01-15. After it closes, migration questions return to the normal support path.

## Requests to Product and Engineering
- A bulk-migration status view for large tenants, so Support can see which dashboards still need work.
- A clearer message in the product when a tile cannot be converted.
- Documentation of how scheduled emails are re-linked after migration.
- A named contact for each large tenant during the migration window.

## What went well
- The triage rota reduced duplicated escalations.
- Runbooks for Lookout access were updated and used correctly in the audit sample we reviewed.
- Handover notes between shifts improved; fewer tickets bounced between engineers.

## What to improve
- Tagging discipline: some escalations were tagged "other" and had to be recoded.
- Fewer escalations should need engineering for known issues; we will add known-issue macros.
- Response templates for migration questions need updating after each assistant release.

## Q4 plan
- Add a migration dashboard for Support with filters by tenant and plan.
- Run a monthly review with the Insights team.
- Share the top ten known issues with Customer Success every two weeks.

Attendees at the review: Owen Hale, Rafael Costa, Mei Arakawa, Jonah Feld, Ilse Mortensen.
