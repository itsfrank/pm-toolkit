# Govern GA readiness review

From: Aisha Karim (notes) | Date: 2026-09-16 | To: Govern team, Infrastructure, Support Engineering, Security

Attendees: Aisha Karim (PM), Lukas Brenner (EM), Mei Arakawa (Infrastructure), Priya Raman (Security), Tomas Lindqvist, Owen Hale (Support Engineering), Ines Duarte (Docs). Apologies: Marco Bellini.

Purpose: walk the Govern readiness checklist section by section, find the blockers, and agree who does what. Kestrel Govern is still in beta; nothing here changes the public status.

## 1. Timeline
Lukas presented the current plan. The Govern GA target is 2027-02-01. This is an engineering target, not a committed date, and it is not for customers. Sales and Customer Success should keep telling customers that Govern is in beta with no GA date.

Aisha asked that the team revisit the target after the RAP security review lands, since any findings could push things around.

## 2. Checklist ownership
The checklist has 34 items grouped into security, operations, docs, support and commercial readiness. Lukas Brenner owns the GA readiness checklist and will report status in the Thursday engineering sync. Item owners remain with the individual teams; Lukas only tracks.

## 3. Audit log
Retention was the main product discussion.
- Audit log retention for Govern is 400 days on the Enterprise plan and 90 days on the Team plan.
- Export formats: JSON lines and CSV are in; a scheduled export is a candidate for after GA.
- Owen asked whether support staff access to audit entries is itself logged; Priya confirmed yes, via the Lookout integration.

## 4. Operations
| Area | Status | Owner |
|---|---|---|
| On-call runbook | draft written | Mei Arakawa |
| Load test at 5x beta volume | scheduled for early October | Infrastructure |
| Backup and restore drill | not started | Infrastructure |
| Alerting on audit pipeline lag | in review | Govern team |

Mei flagged that the restore drill depends on a test environment that is shared with Warehouse. She will book it once the Fjord testing window closes.

## 5. Docs and support
Ines has the admin guide at roughly 70% complete. The role-model explainer needs diagrams. Owen wants a support playbook with the standard questions: why can a user not see a dashboard, how to read an access decision, how to recover from a locked-out admin. Owen will draft it and Aisha will review.

## 6. Commercial
Pricing for Govern is not set and is being discussed in the packaging work. Nothing from this meeting should be quoted to customers.

## Action items
- Lukas: publish the checklist as a shared page by next Wednesday.
- Mei: share the load-test plan.
- Priya: confirm the penetration test schedule.
- Ines: send the docs outline to the group.
- Owen: first draft of the support playbook.
- Aisha: update the Govern product page after review.

## Next meeting
Two weeks from today, same time. Agenda: checklist status, load test results, docs progress.

## Appendix: open questions parked for later
- Whether delegated admin (a customer admin managing a sub-group) is needed at GA or can follow. Aisha will gather customer input from the beta tenants.
- Naming of the role templates in the admin UI. Ines suggested plain names over internal ones; Tomas will propose a list.
- Whether the beta status banner in the app should link to the docs page or the status page. Owen prefers the docs page.
- Translation of the admin guide: out of scope for now.
