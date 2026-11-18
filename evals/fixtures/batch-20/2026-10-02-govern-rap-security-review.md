# Govern RAP security review

Owner: Priya Raman (Security) | Status: review in progress | Updated: 2026-10-02

RAP is the regional access policies capability in Kestrel Govern, which lets customers restrict access by location. This review summarises the security assessment carried out before wider release. Audience: Govern team, Security, Product.

## Scope
- Policy evaluation logic and its enforcement points.
- Admin API and the admin UI.
- Audit logging of policy decisions.
- Handling of IP geolocation data.

Out of scope: the rest of Govern, which has its own review.

## Method
An external penetration testing firm ran a black-box test over two weeks, followed by a grey-box session with source access for the policy engine. The internal Security team reviewed threat models and configuration. Testing used a staging environment with realistic policies.

## Results
The RAP penetration test found 2 medium-severity findings, fixes due 2026-10-31. No high-severity or critical findings were reported.

| Finding | Severity | Summary | Owner |
|---|---|---|---|
| F-1 | Medium | A policy change was not recorded with the acting user in one admin API path | Govern team |
| F-2 | Medium | Rate limiting missing on a policy preview endpoint | Govern team |
| Informational | Low | Several hardening suggestions for headers and error messages | Backlog |

Details of the fixes are tracked in the security ticket; Lukas Brenner is following progress for the Govern team.

## Beta status
RAP private beta has 6 tenants. All are Enterprise accounts selected by the Govern team and Customer Success. Beta tenants use RAP with test groups first; production restriction is opt-in. We do not plan to widen the beta until the fixes are verified.

## Positive observations
- Policy decisions fail closed when location data is unavailable.
- Admin actions are logged with consistent fields.
- The testers noted clear separation between policy evaluation and policy storage.

## Recommendations
1. Fix F-1 and F-2 and retest the affected paths.
2. Add automated tests for audit logging on every admin path.
3. Document the geolocation data sources and their limits in the admin guide.
4. Schedule a short follow-up test when the fixes are complete.

## Dependencies
- Retest capacity from the external firm: booking in progress.
- Docs updates from Ines Duarte.
- Customer communications: none until the retest is done.

## Sign-off
Security will sign off for wider beta once the retest confirms the fixes. The review will be updated as results come in.

## Appendix: threat model summary
The threat model considered four actors: a customer admin acting in error, a malicious insider with admin rights, an external attacker with a stolen low-privilege session, and a user trying to bypass location rules with network tools such as proxies. Controls reviewed included policy precedence rules, session binding, audit completeness and safe defaults. The proxy-evasion scenario is partly mitigated by design, since location rules are one layer among others, and customers are advised in the admin guide to combine them with role-based controls.

## Appendix: attendees at the readout
Priya Raman, Lukas Brenner, Aisha Karim, Tomas Lindqvist and a representative of the external testing firm. The readout lasted one hour and included a live demonstration of the two medium findings in the staging environment.
