# pm-toolkit

Claude Code skills and a cited, local wiki for product managers. It focuses on the slowest
and riskiest part of the job: getting from a vague ask ("we need X") to a PRD you're
confident is complete and accurate.

- **Easy to review.** Skills are markdown; a few helper scripts and a local viewer use only
  the Python standard library and plain browser JavaScript. No installs, hooks, MCP servers
  or connectors are needed, which makes it easy to review and approve.
- **Local first.** Your documents stay in your workspace. The agent never sends anything
  anywhere.
- **Evidence-based.** Every claim is cited to a source card or labeled as inferred,
  assumption or unknown.
- **It learns your organization.** Misses that reviewers catch become new checks, so the
  same gap doesn't come up twice.

## What it does

You don't need to remember any of this. Talk in plain language, or start with `/wiki` to
be sure the toolkit handles it: `/wiki` alone shows what needs your attention, and
`/wiki cheatsheet` shows a one-page guide to what you can ask. The skills behind it:

| Skill | Use it when |
|---|---|
| `pre-prd` | You got a broad ask and need to get to a PRD. Runs the stages below with checkpoints. |
| `intake` | You need to frame an ask: interpretations, assumptions, questions, who to ask. |
| `landscape-map` | "What do we already have, who owns it, what's in flight?" |
| `coverage-review` | "What am I missing?" Walks the coverage lenses and discovery moves, and applies past lessons. |
| `critical-review` | Before review: a demanding senior stakeholder tears the draft apart. |
| `prd` | Draft or revise a PRD with traceable claims and explicit open questions. |
| `review-feedback` | You got real feedback. Log it, fix the wiki, add a lens probe. |
| `rfp-response` | RFPs, RFIs and security questionnaires answered from approved sources only. |
| `gap-analysis` | Requirements versus current capabilities: meets, partial, gap or unknown. |
| `customer-call` | Prep before and debrief after customer calls; files the evidence. |
| `competitive` | Dated, scoped and sourced competitor claim cards and comparisons. |
| `marketing-check` | Fact-check marketing and sales copy against what the product does. |
| `ui-mockup` | Mockups as one shareable HTML file that looks like your real product. Learns the design system from screenshots and saved pages, and remembers your corrections. |
| `report` | Research a question and write a cited, dated report you can read later. |
| `wiki-ingest` / `wiki-lint` | Grow and maintain the wiki. |
| `wiki-expand` | Bring in a whole area (an acquired company, another team's space): survey, ingest the best pages within a budget, catalog the rest. |
| `wiki-notes` | Process the notes you left on pages in the viewer. |
| `wiki-refresh` | Check saved sources against their originals (read-only connector) and re-ingest changes. |
| `setup` | Create or upgrade the workspace. |
| `wiki` | The front door: `/wiki <anything>` routes to the right skill; only runs when you type it. |

## How it works

```
wiki/raw/        saved documents (immutable)      ──┐
wiki/sources/    one card per source: trust, date   ├─►  wiki/pages/  cited, curated pages
wiki/lenses.md   coverage checklist (editable)      │    wiki/INDEX.md one line per page
wiki/review-log  lessons from real reviews  ────────┘
wiki/reports/    research you asked for (dated snapshots)
wiki/notes.jsonl your notes from the viewer, processed by wiki-notes
wiki/catalog/    one line per page of surveyed spaces, read or not
work/<ask>/      ask → intake → landscape → coverage → prd → critical review
design/          design systems, product screens and mockups (ui-mockup)
tools/           wiki.py (IDs, cards, lint, freshness, notes), design.py and the viewer
```

To read the wiki in a browser and leave notes on any line, say `/wiki open` (or run
`python3 tools/viewer/serve.py --open` in your workspace). It listens on this machine only.

The wiki follows the "LLM wiki" pattern: the agent writes and maintains pages from raw
sources, and an index keeps each task's reads small. See [docs/design.md](docs/design.md)
for the reasoning and [docs/research.md](docs/research.md) for the sources behind it.

## Install

Download the repository (or a release zip), open Claude Code in the folder where you want
your workspace, and say:

> Read `<path-to-pm-toolkit>/BOOTSTRAP.md` and set up my PM workspace.

Already have a wiki or notes folder that agents built? Say instead:

> Read `<path-to-pm-toolkit>/plugin/MIGRATION.md` and migrate my knowledge base.

It brings an existing knowledge base under the toolkit's conventions on a git branch,
without deleting anything, and logs its questions for you instead of stopping.

[BOOTSTRAP.md](BOOTSTRAP.md) is written for the agent. It offers two modes: copying the
skills into your workspace (recommended) or installing them as a Claude Code plugin.

Before using it at work, read [docs/security.md](docs/security.md) and check your
employer's policy on AI tools and outside software.

## Try it on the sample company

[samples/kestrel](samples/kestrel/) is a fictional analytics company with a partly built
wiki, planted conflicts and missing facts, and a live ask about EU data residency. Copy it
somewhere and run `pre-prd` to see the full pipeline. `samples/` is independent of the
toolkit and can be deleted.

## Repository layout

| Path | What |
|---|---|
| `plugin/` | The toolkit: `skills/`, the `workspace/` template (with `tools/`), `MIGRATION.md`, plugin manifest |
| `samples/` | Fictional example workspace (optional) |
| `evals/` | Regression cases for the skills, run against `samples/` |
| `docs/` | Design rationale, research, security, customization |
| `scripts/` | Maintainer checks (not needed to use the toolkit) |

## Customizing

Most of the value comes from tuning it to your organization: lenses, the PRD template and
review preferences. See [docs/customizing.md](docs/customizing.md).

## License

MIT. See [LICENSE](LICENSE).
