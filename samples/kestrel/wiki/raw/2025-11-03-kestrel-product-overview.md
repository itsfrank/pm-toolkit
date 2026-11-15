# Kestrel Analytics: product overview (internal)

Owner: Product Operations (Gwen Talbot). Last updated 2025-11-03.
Audience: new hires and partner teams.

Kestrel Analytics sells a B2B product-analytics platform as multi-tenant SaaS. All plans
(Starter, Growth, Enterprise) run on a public cloud provider. Production runs in
AWS us-east-1. There is no customer-selectable hosting region today.

## Products
| Product | What it does | Owning team |
|---|---|---|
| Kestrel Collect | Event-ingestion SDKs (web, iOS, Android, server) and HTTP ingestion endpoints | Ingestion |
| Kestrel Warehouse ("KW") | Managed event storage and query engine; per-tenant retention settings | Infrastructure |
| Kestrel Insights | Dashboards, funnels, retention charts. Insights v2 is in development to replace v1 | Insights |
| Kestrel Govern | Role-based access control, audit log, compliance reports. New; in beta | Govern |
| Kestrel Connect | Integrations: scheduled exports to customer buckets, reverse-sync to CRMs, webhooks | Connect |

## Plans
- Starter and Growth: self-serve, monthly or annual.
- Enterprise: annual contracts, SSO, audit log, 13-month default retention, named CSM.
- Pricing and plan structure are owned by the Pricing & Packaging team.

## Facts people often ask about
- Default data retention: 13 months (Enterprise), 6 months (Growth), 3 months (Starter).
- Tenants: about 1,900 paying tenants, about 140 on Enterprise (as of 2025-10).
- Status page and uptime SLA: Enterprise 99.9% monthly.
