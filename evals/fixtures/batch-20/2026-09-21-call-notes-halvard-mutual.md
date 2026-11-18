# Call notes: Halvard Mutual

From: Sam Whitlock | Date: 2026-09-21 | To: Customer Success, Govern product team

Call with Halvard Mutual, a long-standing Enterprise customer in insurance. Purpose: a check-in on how they use Insights and Collect, and an early look at what they want from Govern.

Attendees from Halvard: Katarina Voss (Head of Data Platform), Emil Strand (Security Engineering), Ruth Okonkwo-Hale (BI lead). From Kestrel: Sam Whitlock (PM), Ilse Mortensen (CSM), Aisha Karim for the last 15 minutes.

Housekeeping: the CSM joined late because her flight from Oslo was delayed, so Sam opened the call and covered the introductions.

## Current usage
- Insights: roughly 40 active dashboard authors, mostly in claims analytics. They are partway through moving to Insights v2 and are happy with the editor.
- Collect: server-side SDKs for their policy portal and a mobile SDK for their customer app.
- Warehouse: they run scheduled exports to an internal data lake.
- They asked about Usage Alerts and want to join the next beta wave. Sam noted the request.

## What they need from Govern
Emil explained that Halvard's security team reviews access to anything that touches customer data. Halvard wants a weekly export of the Govern audit log to their SIEM. They already ingest logs from other vendors that way and want one consistent pipeline. Format is flexible as long as each entry has a timestamp, actor, action and target. Emil asked whether delivery to cloud storage would be acceptable; Sam said he would check with the Govern team and respond in writing.

Other Govern comments:
- Role templates for analysts versus reviewers.
- A clear way to show an auditor who had access to a dashboard at a given point in time.
- They would like to see the beta docs before committing to a pilot.

## Commercial
Halvard's renewal date is 2027-06-30. Ilse said the account is healthy and that Katarina has budget sponsorship for the Govern pilot, subject to security review. No pricing was discussed. Sam reminded them that Govern is in beta and no commitments about timing or packaging were made.

## Feedback on support
Ruth was positive about response times but wants a named contact for migration questions. Ilse will arrange this.

## Action items
| Owner | Action | Due |
|---|---|---|
| Sam | Ask Govern team whether scheduled export to cloud storage is on the roadmap | next week |
| Sam | Send beta docs and a pilot outline | next week |
| Ilse | Introduce a named migration contact for Ruth | next week |
| Aisha | Share the Govern role-template draft | when reviewed |

## Follow-up
Katarina asked for a short note summarising the call, which Ilse will send. Next check-in is planned for the end of the quarter.

## Background notes for the wiki
- Halvard uses a single Enterprise contract covering four business units; the Govern pilot would start with the claims analytics unit.
- Their security team has a standard vendor questionnaire, last completed in the autumn of the previous year; a refreshed RFP questionnaire is already in the raw folder.
- Emil asked whether the audit log could carry a customer-defined tag for the business unit. Sam said this was a good idea to pass to the Govern team, with no commitment.
- Katarina mentioned an internal audit in the spring and wants documentation of access controls ready ahead of it.
- Ruth asked for a walkthrough of what changes for dashboards after the migration to v2; Jonah Feld's team has the migration guide.
