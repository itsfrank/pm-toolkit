# Wiki maintenance rules

The wiki turns scattered documents and conversations into cited, current pages that an
agent (and a person) can navigate quickly. It follows the "LLM wiki" pattern: raw sources
stay immutable, the agent writes and maintains the pages, and an index keeps reads small.

## Flow
1. **Save** the document into `raw/` (export, copy-paste into `.md`, PDF, transcript).
   Name it `YYYY-MM-DD-short-title.ext`. From a connector (Confluence, Jira, docs), save
   the content as markdown and record its URL, ID and version on the card.
2. **Card** it: create `sources/S-NNNN.md` from `sources/_TEMPLATE.md`
   (`python3 tools/wiki.py next-id` gives the number). Conversations with no document get a
   card too: write the notes into `raw/` first.
3. **File** facts into pages in `pages/`, each fact cited `[S-NNNN]`. Create a page from
   `pages/_TEMPLATE.md` only when no existing page fits.
4. **Index**: add or update the page's line in `INDEX.md`. Add new terms to `glossary.md`.
5. **Lint** periodically (`wiki-lint`): stale pages, uncited claims, conflicts, orphans.

## Citations
- `[S-0012]` cites a source card. Add a locator for long sources:
  `[S-0040 §3.2 p.212]`. Cite several as `[S-0012, S-0013]`.
- Cite the card, never a page or a report. A page link is navigation, not evidence.

## Page conventions
- One entity per page: a product, team, person, initiative, customer, competitor, topic or
  decision.
- File names are kebab-case: `pages/products/report-builder.md`.
- `status: draft` until the PM has read it; then `status: reviewed`.
- Keep `## Open questions` on every page. Unknowns are first-class.
- Conflicting facts go side by side under `## Conflicts` with dates and sources.
- Link related pages with relative links. Keep pages short; split when over ~150 lines.

## People pages
`pages/people/<first-last>.md` records work facts only: role, team, what they own, what to
ask them about, decisions they made or approved. Each fact is cited. No opinions about the
person, no personal details, no performance commentary.

## Reports
`reports/YYYY-MM-DD-slug.md` holds research the PM asked for: comparisons, overlap and
conflict scans, summaries of an area. Reports are lighter than pages:
- Required header: the question asked, date, sources read, and "as of" date.
- Cite facts as usual so the reader can click through. No template or status needed.
- A report is a snapshot. Never cite a report from a page; file durable facts into pages
  with `wiki-ingest`, keeping the original citations.
- Refreshing a report means a new dated file, or an update with a `Refreshed:` line.
- `reports/INDEX.md` is generated: `python3 tools/wiki.py reports-index`.

## Trust levels (on source cards)
- `authoritative`: written or confirmed by the owner (spec, design doc, release notes,
  the owning team in a meeting).
- `secondary`: accurate-looking but not owner-confirmed (wiki of another team, summary,
  another team's draft PRD).
- `marketing`: external-facing copy. Good for positioning, weak for capability truth.
- `hearsay`: "I heard that…", chat messages, ticket comments, unattributed notes. Needs
  confirmation.
- `pm-note`: something the PM stated (a note or correction). Treat as a lead from a
  knowledgeable person; ask for a source when the fact matters externally.

## Freshness
Sources that live elsewhere (a Confluence page, a ticket) can change after capture. Cards
record `origin_version`, `last_checked` and `recheck_days`. A source is due when
`last_checked + recheck_days` is in the past; `python3 tools/wiki.py due` lists them.
`wiki-refresh` checks due sources and re-ingests the ones that changed. Defaults:
draft PRDs and tickets 7 days, specs and design docs 30, released docs 90, static files
(PDF exports, transcripts) `never`.

## Notes
The PM annotates rendered pages in the viewer (`python3 tools/viewer/serve.py`). Notes land
in `notes.jsonl`, an append-only log; `wiki-notes` processes them. Never rewrite or delete
lines in `notes.jsonl`; record outcomes by appending status events.

## Answers library
`pages/answers/` holds external answers (RFP, security questionnaire, customer email) the PM
has approved. Reuse them for consistency; re-check the cited sources before reusing an
answer older than 90 days.
