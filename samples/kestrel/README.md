# Kestrel Analytics: fictional demo workspace

This is a pre-populated pm-toolkit workspace for a **fictional** company, Kestrel Analytics,
a B2B product-analytics SaaS vendor. Every company, customer, competitor, person, document,
number and date in it is invented for demonstration and testing. Nothing here describes a
real organization.

It has the same layout as `plugin/workspace/`:

- `wiki/raw/`: 20 saved source documents (design docs, runbook, decks, call notes, chat
  export, RFP, marketing draft, draft and approved versions of a past PRD).
- `wiki/sources/`: source cards S-0001 to S-0020.
- `wiki/pages/`: a partly filled wiki (products, teams, initiatives, a decision, a customer,
  a competitor, an approved answer). Some important facts are only in `raw/` and have not
  been filed yet, as in a real wiki.
- `wiki/INDEX.md`, `glossary.md`, `lenses.md`, `review-log.md`: index, aliases, coverage
  checklist and one past review lesson (the Usage Alerts PRD pair in `raw/` is
  there to try `review-feedback` backfill mode).
- `work/2026-10-05-eu-data-residency/ask.md`: a live ask from the VP Product.

The scenario's "today" is early October 2026. The helper scripts and viewer follow
`PM_TODAY` when it is set, so pin it to keep source freshness consistent:
`PM_TODAY=2026-10-06 python3 tools/viewer/serve.py --open`. On that date one source,
S-0014 (a competitor web page last checked in 2025), is due for a recheck.

## Try it
1. Copy this folder somewhere outside the repo, e.g. `cp -R samples/kestrel ~/kestrel-demo`.
2. Copy the agent instructions in: `cp plugin/workspace/AGENTS.md plugin/workspace/CLAUDE.md ~/kestrel-demo/`.
3. Make the pm-toolkit skills available (install the plugin as described in the repo README).
4. Open Claude Code in `~/kestrel-demo` and run:
   `pre-prd on work/2026-10-05-eu-data-residency/`
5. Go stage by stage. Compare what it finds with what a careful PM should find: things
   scattered across design docs, a runbook, a draft memo and a chat thread, plus sources
   that disagree.

Other things to try: answer the RFP in `wiki/raw/2026-10-02-halvard-mutual-rfp-questionnaire.md`
with `rfp-response`, check the launch blog draft with `marketing-check`, or run `wiki-lint`.
