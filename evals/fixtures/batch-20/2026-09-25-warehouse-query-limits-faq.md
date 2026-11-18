# Warehouse query limits: frequently asked questions

Owner: Infrastructure team (Mei Arakawa) | Status: reviewed | Updated: 2026-09-25

This FAQ explains the limits that apply when running queries against Kestrel Warehouse. It is for Support Engineering, Customer Success and Solutions staff answering customer questions. Limits may be adjusted by Infrastructure as the platform changes; check this page before quoting anything.

## Why do limits exist?
Warehouse is a shared multi-tenant system. Limits protect each tenant from noisy neighbours and keep response times predictable. They are not meant to block normal analytics use.

## What is the query timeout?
Query timeout is 120 seconds on the Team plan and 600 seconds on Enterprise. A query that runs longer is cancelled and the caller receives a timeout error with the query ID. The Free plan has a shorter timeout, listed on the pricing page.

## How many queries can run at once?
At most 25 concurrent queries per tenant. Additional queries wait in a queue for a short period, then fail with a "capacity" error. Queue time does not count toward the timeout.

## Summary table
| Topic | Team | Enterprise |
|---|---|---|
| Timeout | see above | see above |
| Result size limit | 1 GB per query | 5 GB per query |
| Retention of query history | 30 days | 90 days |
| Priority queueing | no | yes |

(The timeout and concurrency numbers are in the answers above and apply as written.)

## A customer's queries are timing out. What should I check?
1. Is the query scanning a wide time range? Suggest filtering on event date.
2. Is it joining several large tables? Suggest pre-aggregating.
3. Is the tenant running many dashboards that refresh at the same time? Suggest staggering refresh schedules.
4. Is the query hitting data that has been moved to slower storage? The Infrastructure team can look at this.
5. If none of these apply, open a ticket with the query ID and the time of the failure.

## Can limits be raised for one customer?
Not through Support Engineering. Requests go to Infrastructure with the account name, the business reason and the query pattern. Raising limits is rare and is reviewed case by case.

## Does Kestrel Query (KQ) behave differently from the SQL we show in the docs?
The docs show the supported SQL subset. Unsupported syntax gives a clear parse error. Report unclear errors to Infrastructure so we can improve the messages.

## Related pages
- Warehouse product page in the wiki.
- Insights v2 performance report (for dashboard load questions).
- The status page, for incidents.

## Contact
Questions about this page: Mei Arakawa or the Infrastructure channel.

## Wording guidance for customer replies
Keep replies short and factual. Suggested pattern: state the limit that applies to the customer's plan, explain what happened to their query, and offer one concrete next step. Avoid promising that a limit will change. If a customer compares our limits with a competitor, do not quote competitor numbers unless they come from a public source, and note that comparisons depend on workload.

## Change log for this page
- 2026-09-25: reviewed by Infrastructure; added troubleshooting checklist and wording guidance.
- Earlier versions are in the wiki history.
