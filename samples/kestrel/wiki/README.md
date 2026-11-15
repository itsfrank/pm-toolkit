# Wiki maintenance rules

The wiki turns scattered documents and conversations into cited, current pages that an
agent (and a person) can navigate quickly. It follows the "LLM wiki" pattern: raw sources
stay immutable, the agent writes and maintains the pages, and an index keeps reads small.

## Flow
1. **Save** the document into `raw/` (export, copy-paste into `.md`, PDF, transcript).
   Name it `YYYY-MM-DD-short-title.ext`.
2. **Card** it: create `sources/S-NNNN.md` from `sources/_TEMPLATE.md` (next free number).
   Conversations with no document get a card too: write the notes into `raw/` first.
3. **File** facts into pages in `pages/`, each fact cited `[S-NNNN]`. Create a page from
   `pages/_TEMPLATE.md` only when no existing page fits.
4. **Index**: add or update the page's line in `INDEX.md`. Add new terms to `glossary.md`.
5. **Lint** periodically (`wiki-lint`): stale pages, uncited claims, conflicts, orphans.

## Page conventions
- One entity per page: a product, team, initiative, customer, competitor, topic or decision.
- File names are kebab-case: `pages/products/report-builder.md`.
- `status: draft` until the PM has read it; then `status: reviewed`.
- Keep `## Open questions` on every page. Unknowns are first-class.
- Conflicting facts go side by side under `## Conflicts` with dates and sources.
- Link related pages with relative links. Keep pages short; split when over ~150 lines.

## Trust levels (on source cards)
- `authoritative`: written or confirmed by the owner (spec, design doc, release notes,
  the owning team in a meeting).
- `secondary`: accurate-looking but not owner-confirmed (wiki of another team, summary).
- `marketing`: external-facing copy. Good for positioning, weak for capability truth.
- `hearsay`: "I heard that…", chat messages, unattributed notes. Needs confirmation.

## Answers library
`pages/answers/` holds external answers (RFP, security questionnaire, customer email) the PM
has approved. Reuse them for consistency; re-check the cited sources before reusing an
answer older than 90 days.
