# Design

## The problem
PMs are rarely blocked on writing a PRD. They're blocked on what comes before it: working out
what the ask really means, what already exists, who owns the pieces, what's in flight nearby,
what was decided before, and which considerations nobody has mentioned. That knowledge sits
in scattered documents and in long-tenured colleagues' heads. Anyone new to a product area,
team or company pays this cost on every ask, and still can't be sure they've covered
everything.

The toolkit treats that discovery as the main job, and the PRD as its output.

## Principles

**1. Stages with checkpoints.** `pre-prd` breaks discovery into intake → landscape →
coverage → draft → critical review. Each stage writes a file and stops for the PM, because
most answers come from people, not documents. Work can pause for days and resume from the
work folder.

**2. Coverage made explicit.** `coverage-review` walks a fixed set of lenses (security,
compliance, data, migration, packaging, go-to-market, support…) and structured discovery
moves (assumption inversion, pre-mortem, lifecycle walk, boundary scan, evidence audit). The
output is a count of covered, partial, gap and n/a lenses, not reassurance. Checklists and
pre-mortems are among the better-supported methods for surfacing missed risks; see
[research](research.md).

**3. The organization's memory becomes a file.** The wiki captures what a veteran knows:
products and their limits, owners, initiatives, past decisions, code names. Each ask adds
to it, so each ask costs less than the one before.

**4. Learn from misses.** Real reviewer feedback goes into `review-log.md`. Missed
considerations become new lens probes, and missed facts get filed into the wiki. Over time
the lenses turn into a model of what the PM's reviewers care about. `critical-review`
simulates a demanding senior reviewer, so misses surface before the real review.

**5. Evidence over fluency.** Every factual claim carries a source ID or a label (`inferred`,
`assumption`, `unknown`). Source cards record trust, so a sales deck can't quietly outrank a
design doc. Conflicts are shown side by side rather than resolved silently. "Not found" is
`unknown`, never "doesn't exist". These rules matter most for external outputs (RFPs,
marketing, gap analyses), where overclaiming is costly.

**6. Reviewable, local only.** Skills are markdown. Where code makes work deterministic or
cheaper (next IDs, card drafts, index rebuilds, mechanical lint checks, note anchoring) it
lives in `tools/` and uses only the Python standard library, so it runs on locked-down
laptops where package installs are blocked. The viewer is plain browser JavaScript served
from localhost. No hooks or MCP servers are required, and the whole toolkit can be reviewed
in about an hour, which matters at companies where installing outside tools needs
approval. Documents stay on the PM's machine, and the agent never sends anything.
Connectors are optional and used read-only; see [security](security.md).

**7. Budget-aware.** Reading, filing and mapping run fine on a mid-tier model. Coverage,
critical review and final PRD passes benefit from the strongest model, and the skills say so.

## Why a wiki and not RAG
For one PM's working set (hundreds of documents, not millions), a curated, cited,
index-first markdown wiki is cheaper and more transparent than a vector store. The agent
can read the index, open a handful of pages and follow citations to source cards. Search
(grep) covers raw files. Add retrieval only when that stops working.

## What stays human
Deciding what to build, approving external answers, making roadmap commitments, judging
trade-offs, and talking to people. The toolkit prepares and checks; it doesn't decide.

## Reading, notes and reports
PMs read the wiki more than they edit it, and many don't want to read raw markdown in a
terminal. The viewer renders pages, makes citations clickable through to source cards, and
lets the PM select any text and leave a note. Notes go to an append-only log rather than
into the page: the PM never has to think about format, and the agent decides whether a note
is a correction, a question, a lesson for the review log or a request. Each note stores the
quoted text with some context and the commit it was written against, because pages change
before notes are processed; `tools/wiki.py notes` finds the quote again.

Reports are the other half of reading. PMs ask for comparisons and scans ("where do the
in-flight PRDs conflict?") that they want to come back to. Holding them to page rules would
make them slow to write, so they get a light header (question, date, sources) and stay
snapshots. They never become evidence for pages: durable facts move into pages with their
original citations, which keeps the wiki from citing its own summaries.

## One front door
A PM shouldn't have to learn eighteen skill names. Most requests arrive in plain language
and Claude matches them to a skill by its description. `/wiki` is the explicit fallback: a
short router that only runs when typed, so it never adds a hop to ordinary requests. With no
argument it shows what needs attention; `/wiki cheatsheet` shows the workspace's
`CHEATSHEET.md`, which the viewer also uses as its home page. Upkeep (notes, rechecks, lint)
is offered by the agent at the start of a session instead of being something the PM must
remember. Skills stay separate behind the router because each run then loads only the text
it needs, and each skill can be evaluated on its own.

## Freshness
Sources pulled from a live system (a Confluence page, a ticket) go stale silently. A global
age rule ("re-check anything older than two days") fires on every source forever and costs
a model call each time. Instead, each card records the original's version, when it was last
checked, and how often it is worth checking for its type: weekly for draft PRDs, never for a
PDF export. Detection is a metadata comparison a small model can do in the background,
without blocking the answer. Writing changes back into the wiki goes through normal ingest on
the default model, because a new version can contradict pages, reports and approved answers,
and that needs judgment.

## Expanding into a new area
When a company acquires another, or two teams' spaces merge, thousands of pages arrive at
once. Ingesting all of them would cost a lot and bury the useful ones under meeting notes.
`wiki-expand` surveys everything in scope cheaply, ingests the highest-value pages within a
budget, and catalogs the rest: one searchable line per page with its link. The catalog is
what makes selective ingest safe. Before an agent writes "unknown", it searches the catalogs
and fetches the page that probably holds the answer, so the long tail is one step away
rather than invisible. Catalog lines are never cited; only the fetched, carded page is.

Surveys stop for the PM's approval unless a budget was given up front. Budgets can be in
dollars because `claude -p --output-format json` reports each run's `total_cost_usd` and
per-model usage, subagents included; runs append those results to a ledger and
`tools/wiki.py spend --ledger` sums it. Session logs are an unofficial format and
undercount, so `spend --session-id` reads them only for mid-run estimates, priced from
`tools/prices.json` if the PM filled it in. Prices are not written into skills because they
change, and family-wide prices can't be exact.

## Graceful wind-down
A run that stops at its budget mid-edit leaves half-filed pages and no trail. Long runs
instead stop starting new work at about 80% of the budget, finish what's in flight, leave
every file consistent, and write a `HANDOFF.md` for the next agent: what's done, what's
next, decisions already made. Running slightly over to finish cleanly is better than
leaving the wiki inconsistent. The same applies when a run hits a usage limit or runs out of
context, so the rule lives in the shared conventions, not in one skill.

## Migration
Many PMs start with an ad-hoc wiki before they find a toolkit. Re-ingesting from scratch
throws away the pages they value. `MIGRATION.md` classifies files by role rather than
location, moves instead of deletes, adds citations where they can be traced and labels the
rest, and runs on a git branch. It never stops for questions: migrations are long and often
run unattended, so it takes the conservative choice and logs a question for the PM instead.
