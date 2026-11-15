# pm-toolkit

Claude Code skills and a cited, local wiki for product managers. It focuses on the slowest
and riskiest part of the job: getting from a vague ask ("we need X") to a PRD you're
confident is complete and accurate.

- **Markdown only.** No scripts, hooks, MCP servers or connectors are needed to use it.
  Everything is readable in a few minutes, which makes it easy to review and approve.
- **Local first.** Your documents stay in your workspace. The agent never sends anything
  anywhere.
- **Evidence-based.** Every claim is cited to a source card or labeled as inferred,
  assumption or unknown.
- **It learns your organization.** Misses that reviewers catch become new checks, so the
  same gap doesn't come up twice.

## What it does

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
| `wiki-ingest` / `wiki-lint` | Grow and maintain the wiki. |
| `setup` | Create or upgrade the workspace. |

## How it works

```
wiki/raw/        saved documents (immutable)      ──┐
wiki/sources/    one card per source: trust, date   ├─►  wiki/pages/  cited, curated pages
wiki/lenses.md   coverage checklist (editable)      │    wiki/INDEX.md one line per page
wiki/review-log  lessons from real reviews  ────────┘
work/<ask>/      ask → intake → landscape → coverage → prd → critical review
```

The wiki follows the "LLM wiki" pattern: the agent writes and maintains pages from raw
sources, and an index keeps each task's reads small. See [docs/design.md](docs/design.md)
for the reasoning and [docs/research.md](docs/research.md) for the sources behind it.

## Install

Download the repository (or a release zip), open Claude Code in the folder where you want
your workspace, and say:

> Read `<path-to-pm-toolkit>/BOOTSTRAP.md` and set up my PM workspace.

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
| `plugin/` | The toolkit: `skills/`, the `workspace/` template, plugin manifest |
| `samples/` | Fictional example workspace (optional) |
| `evals/` | Regression cases for the skills, run against `samples/` |
| `docs/` | Design rationale, research, security, customization |
| `scripts/` | Maintainer checks (not needed to use the toolkit) |

## Customizing

Most of the value comes from tuning it to your organization: lenses, the PRD template and
review preferences. See [docs/customizing.md](docs/customizing.md).

## License

MIT. See [LICENSE](LICENSE).
