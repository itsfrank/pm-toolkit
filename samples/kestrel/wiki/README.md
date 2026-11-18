# Wiki maintenance rules

The wiki turns scattered documents and conversations into cited, current pages that an
agent (and a person) can navigate quickly. It follows the "LLM wiki" pattern: raw sources
stay immutable, the agent writes and maintains the pages, and an index keeps reads small.

## Flow
1. **Save** the document into `raw/` (export, copy-paste into `.md`, PDF, transcript).
   Name it `YYYY-MM-DD-short-title.ext`. From a connector (Confluence, Jira, docs), save
   the content as markdown and record its URL, ID and version on the card. Next to a PDF,
   save its text as `raw/<same-name>/part-NN.md` with a `<!-- p.N -->` line where each page
   starts (one card for the whole), so search hits carry a `p.N` locator. On macOS,
   `python3 tools/wiki.py pdf-text raw/<file>.pdf` does this and writes `contents.md` from
   the PDF's bookmarks; elsewhere, read the PDF and write the parts.
2. **Card** it: create `sources/S-NNNN.md` from `sources/_TEMPLATE.md`
   (`python3 tools/wiki.py next-id` gives the number). Conversations with no document get a
   card too: write the notes into `raw/` first.
3. **File** facts into pages in `pages/`, each fact cited `[S-NNNN]`. Create a page from
   `pages/_TEMPLATE.md` only when no existing page fits.
4. **Index**: add or update the page's line in `INDEX.md`. Add new terms to `glossary.md`,
   and search words (below).
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
  with `wiki-ingest`, keeping the original citations, then set `promoted: yes`.
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

## Catalogs
`catalog/<space>.md` lists every page of a space or collection `wiki-expand` surveyed, one
line per page, so agents can find what the wiki hasn't read yet:
```
- [ ] [Billing architecture](https://…/pages/7104) · id: 7104 · path: WREN > Engineering · labels: billing · modified: 2026-09-02 · Summary of the page
- [x] [Product overview](https://…/pages/7101) · id: 7101 · path: WREN > Home · modified: 2026-09-20 · card: S-0031
```
- `[ ]` not ingested, `[x]` ingested (`card:` names the card). `file:` points to a local
  export when the page came from one.
- A catalog line is a lead, not a source: never cite it. Fetch the page, save it to `raw/`,
  card it, cite the card, then `python3 tools/wiki.py catalog-mark <id> S-NNNN`.
- Top-ranked pages get a one-line summary; the long tail may have title, path and labels
  only.
- Tasks add lines too: connector pages an agent saw but didn't rely on (`AGENTS.md`,
  Working style).
- Never catalogue personal spaces, templates (page or document templates), HR and
  people-management pages, or pages with personal data. Lines added during tasks also leave
  out pages unrelated to product work (social posts, admin notices). Old meeting notes,
  retros and archived pages are fine.
- `watch.md` lists the spaces `wiki-refresh` checks for new or removed pages.

## Long runs and handoffs
Any long or budgeted run (expanding an area, a migration, a large batch ingest or report)
works in its folder under `work/` and follows these rules:
- **Budget:** in dollars, tokens, or pages. Record the start time (UTC) and budget in the
  run's `LOG.md`. Batches run as `claude -p ... --output-format json` append their result
  to the run's `ledger.jsonl`; `python3 tools/wiki.py spend --ledger <it>` totals it exactly.
  Within one session, `spend --session-id <id> --since <start>` gives an estimate (it
  undercounts). At about 80% of the budget, start no new batches; let running ones finish.
- **Wrap up gracefully** when the budget runs low, a limit is hit, or context runs short:
  leave every file consistent (no half-filed page; finish or revert a cut-off batch),
  update indexes, commit if the workspace uses git, then write the report with a
  `## Not completed` section and `HANDOFF.md`. Going slightly over budget to finish the
  wrap-up is fine; say by how much.
- **`HANDOFF.md`** is for the next agent. Use these sections, all of them:
  ```
  # Handoff: <run>
  Restart: "Continue work/<folder>/ with a budget of $N"   ← one line the PM can paste
  ## Request
  The original request, scope, budget and what was spent.
  ## Done
  Source IDs and page IDs or files processed, cards created, pages built, so none is redone.
  ## Next steps
  Numbered, in order, starting with the next item to process; flag items that matter most
  (for example a page with a known conflict).
  ## Decisions made
  Choices already taken (exclusions, rankings, trust levels), so they aren't relitigated.
  ## Open questions
  ```
- **Resume:** a skill that finds `HANDOFF.md` in its folder continues from it instead of
  starting over, and appends to `LOG.md`.

## Search words
The viewer's search uses no model: it matches words, their stems and glossary synonyms,
nothing else. So when a page is created or changed, add the everyday words someone would
type to find it that its text doesn't use: a page that says "customers leaving" gets
`churn`. Put them in the page's `aliases`. When the word is another name for a glossary
term, put it in that term's "Also called" instead, so every search for either finds both.
Three to six words a page; no words the page already uses.

## Notes
The PM annotates rendered pages in the viewer (`python3 tools/viewer/serve.py`). Notes land
in `notes.jsonl`, an append-only log; `wiki-notes` processes them. Never rewrite or delete
lines in `notes.jsonl`; record outcomes by appending status events. A note with no `file`
is a request the PM typed on the viewer's Home page.

## Documents added in the viewer
The PM can drop a file or paste text on the viewer's Home page. The viewer saves it as a new
file in `raw/` and drafts its card (`type` and `trust` left to choose). Such a document is
searchable but not yet in any page: `wiki.py status` lists these cards, and `wiki-ingest`
finishes them.

## Answers library
`pages/answers/` holds external answers (RFP, security questionnaire, customer email) the PM
has approved. Reuse them for consistency; re-check the cited sources before reusing an
answer older than 90 days.
