---
name: customer-call
description: Prepare for a customer or prospect call (account context, goals, non-leading questions, landmines) and debrief afterwards from notes or a transcript (verbatim quotes, observations vs. interpretations, requests, follow-ups), filing the evidence into the wiki. Use before or after customer calls, discovery interviews, QBRs or escalation meetings.
---

# Customer call

## Prep mode
Input: customer name, call purpose, attendees, any agenda.
Output: `work/YYYY-MM-DD-call-<customer>/prep.md`.

1. Read the customer page, related source cards, past debriefs, open requests, RFP answers
   and relevant product pages.
2. Write a one-page prep:
   - **Context:** who they are, what they use, history, open issues and commitments (cited).
   - **Goals:** what we want to learn or achieve; what they likely want.
   - **Questions:** 5–8 open, non-leading questions about past behavior ("Walk me through the
     last time…") before any about solutions. One follow-up per question.
   - **Hypotheses to test** and what answer would disprove each.
   - **Landmines:** roadmap items not approved for discussion, known sore points, competitor
     context, things not to promise.

## Debrief mode
Input: notes or transcript (save it into `wiki/raw/` first).
Output: `work/.../debrief.md`, a source card, and updates to the customer page.

1. Create the source card (`type: call-transcript` or `meeting-notes`, trust `authoritative`
   for what the customer said, the PM's interpretations kept separate).
2. Write the debrief:
   - **Verbatim quotes** with speaker role and timestamp/line. Only text that appears in the
     source; never paraphrase into quotation marks.
   - **Observations** (what they said or did) vs **interpretations** (what we think it means).
   - **Requests and pain points**, each with a quote reference and the speaker's priority.
   - **Surprises**: anything that contradicts the wiki or our assumptions.
   - **Follow-ups:** owner, due date, what was promised. Flag promises the PM shouldn't
     have made.
3. Offer to update the customer page and add requests to relevant initiative or topic pages.

## Rules
- One call is one data point. Don't generalize to "customers want" from a single debrief.
- Keep personal data minimal: roles over names unless names are needed for follow-up.
