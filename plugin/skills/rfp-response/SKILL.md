---
name: rfp-response
description: Draft answers to a customer RFP, RFI, security questionnaire or requirements list using only cited workspace sources and the approved answers library, with honest statuses (yes / partial / no / roadmap / unknown) and SME flags. Use when the user has a questionnaire, RFP, RFI or customer requirements document to answer.
---

# RFP / RFI response

Input: the questionnaire saved in `wiki/raw/` (or the work folder), deadline, customer name,
and any instructions (word limits, format).
Output: `work/YYYY-MM-DD-rfp-<customer>/answers.md` and, if useful, `answers.csv` with the same
columns for pasting into the customer's spreadsheet.

## Steps
1. Parse every question into a row, keeping the customer's numbering and wording exactly.
2. For each question, search `wiki/pages/answers/` first (approved answers), then product
   pages and source cards. Prefer sources with `external_ok: yes`.
3. Draft the answer and assign a status:
   - `yes`: supported today, cited to an authoritative source.
   - `partial`: supported with limits, conditions, or only some deployment models or plans.
     State the limits.
   - `no`: not supported, per an authoritative source. Offer a workaround if one is sourced.
   - `roadmap`: planned. **Needs PM and owner approval before sending.** Never give dates
     unless a source marks them approved for external use.
   - `unknown`: no source. Name the SME to ask.
4. Flag answers that reuse an approved answer older than 90 days, or that conflict with
   another answer in the same response.
5. Write the summary at the top: counts by status, the SME question list grouped by person,
   and the items needing approval.

## answers.md row format
```
### <Q-number>: <question verbatim>
**Status:** yes | partial | no | roadmap | unknown
**Answer:** customer-ready text, within limits, no internal names.
**Sources:** [S-NNNN], answers/<file>
**Internal notes:** caveats, SME to confirm, approval needed. (Strip before sending.)
```

## Rules
- Customer-ready text never overstates. "Partial" with honest limits beats a "yes" that sales
  must walk back.
- No internal code names, unreleased details or other customers' names in answer text.
- After the PM approves final answers, offer to save reusable ones to `wiki/pages/answers/`
  with their sources and approval date.
