# Proposal: new data platform glossary terms

Owner: Infrastructure and Ingestion teams (proposed by Mei Arakawa) | Status: proposal for review | Updated: 2026-10-03

Several internal channels use shorthand that new joiners and Customer Success staff keep asking about. This proposal lists the terms to add to the wiki glossary, with a short definition for each, and asks for review before they are added. Existing glossary entries are not changed.

## Why now
Over the last quarter, people from Support, Sales and Product asked in chat what a few abbreviations meant. Writing them down once saves repeated questions and reduces mistakes when someone quotes engineering notes to a customer.

## Proposed terms
| Term | Definition | Used by |
|---|---|---|
| KQ | "KQ" means Kestrel Query, the Warehouse query engine | Infrastructure, Support Engineering |
| hot path | "hot path" means Collect's real-time delivery path (as opposed to the spool) | Ingestion, Collect SDK team |
| spool | The Collect buffer where events wait when real-time delivery is unavailable | Ingestion, mobile SDK teams |
| tenant | A customer account that owns one or more workspaces | everyone |

Notes on the entries:
- The spool entry is included for context, because the hot path definition refers to it.
- The tenant entry is listed only so the proposed terms read as a set; reviewers may drop it if the glossary already covers it.

## Usage guidance
- Use the full name on first mention in customer-facing material. The abbreviations are for internal writing.
- When a customer uses the same abbreviation for something else, ask what they mean before answering.
- Do not use these terms in marketing copy without review from the product marketing team.

## Review process
1. Reviewers add comments in the proposal for a week.
2. Mei merges the agreed terms into the glossary page.
3. The wiki index is updated if a new page is needed.
4. Anything disputed goes to the next Infrastructure and Ingestion sync.

## Reviewers
Rafael Osei (Ingestion), Owen Hale (Support Engineering), Marco Bellini (Pricing & Packaging) and Ines Duarte (Docs). Ines asked that definitions be written in plain language so they can be reused in help-centre articles.

## Other candidates for later
Terms raised during preparation but not yet defined: "fan-out", "late arrivals" and "backfill window". They need owners to write definitions, so they are not part of this proposal.

## Timeline
Reviews close one week after circulation. The glossary update follows within the week after that, with no other dependencies.

## Examples of the confusion this solves
- A support engineer wrote "the issue is in the hot path" in a ticket note, and the Customer Success manager read it as a priority label rather than a technical area.
- A solutions engineer told a customer that "KQ limits" apply, and the customer asked whether KQ was a separate product they needed to buy.
- A new Ingestion hire spent a morning searching for the spool design doc because nobody had defined the word.

## Format
Each accepted term gets one glossary line: the term, a one-sentence definition, the owning team and a link to a longer page when one exists. No term gets more than three lines.
