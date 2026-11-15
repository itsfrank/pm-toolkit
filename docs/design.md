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

**6. Markdown only, local only.** No scripts, hooks, MCP servers or connectors. The whole
toolkit can be reviewed in under an hour, which matters at companies where installing
outside tools needs approval. Documents stay on the PM's machine, and the agent never sends
anything. Connectors can be added later, deliberately; see [security](security.md).

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
