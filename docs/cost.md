# Cost

What the toolkit does about cost, and the measurements behind it. The toolkit changes how
the agent works only where a saving was measured without losing quality. Three ingest
changes passed that test; the rest is a default, a report and advice.

## What ships
- **The PM picks the model.** The workspace template has `.claude/settings.json` with
  `"model": "sonnet"`, so a session starts on the standard model whatever the user's global
  default is. `claude --model opus` or `/model opus` puts a session on the strong model.
  Every skill runs on the session's model; none switches it or asks for a stronger one.
- **`python3 tools/wiki.py spend --days 7`** (or "what did I spend this week?") reads the
  workspace's Claude Code session logs and prints tokens and estimated dollars per model,
  then the costliest sessions with their size, largest context and the skills they ran.
  Prices come from `tools/prices.json`. Session logs are an unofficial format and
  undercount; treat the totals as a guide to where the money went.
- **`python3 tools/wiki.py find <terms>`** searches pages, reports, cards and raw files in
  one call and ranks files by how many of the terms they match. Skills mention it as an
  option; nothing forbids reading more.
- **The cheatsheet's cost advice**: one task per conversation, and a new conversation after
  a long break.
- **`python3 tools/wiki.py save-fetched <page id> <raw file>`** saves a connector page the
  agent already fetched, copied from the session log, so the model doesn't retype it. The
  shared rules (`AGENTS.md`, Working style) and the connector skills point to it.
- **Catalog lines for pages seen but not used.** During any task, connector pages the agent
  fetched or saw in search results and didn't rely on get one catalog line each (link, id,
  date, one-line summary), so a later task finds them with `catalog-search` instead of
  searching again. What is never catalogued is listed once in `wiki/README.md`, Catalogs.
- **Batch filing in one session.** `wiki-ingest` files up to about 20 documents in one
  session, and larger batches in fresh sessions of about 20, never a session or subagent
  per file.

## Where the money goes
Measured on eval runs (Claude Code's reported per-model usage and cost, November 2026):

- **Model.** Per token, the strong model costs twice the standard one, and the standard one
  twenty times the fast one. A whole session on the strong model cost 2.5 to 3 times a
  standard one, because the strong model also reads and writes more.
- **New text entering the context** is about half of a typical run: every file read,
  command output and system prompt is written to the cache once, at twice the input price.
- **Output** is about a third. **Re-reading the cached context** on each step is the rest.
- A session's fixed context is about 37,000 tokens; the toolkit's own always-on text is a
  tenth of that. At the wiki sizes tested, the fixed context and the agent's own tool calls
  outweigh the sources it reads.
- A cached conversation expires after a pause. Coming back to a long conversation pays for
  all of it again as new text, which is why the cheatsheet says to start a new conversation
  after a break and continue from the work folder. No eval measures this; in real use it
  may be the larger share.

## Ingest
Measured on fictional cases on the sample (November 2026), standard model unless named;
3 runs per arm, 6 for the deciding ones. At 3 runs a cost difference under about 15% is
noise.

| Change | Case | Cost per run | Quality |
|---|---|---|---|
| `save-fetched` | file five connector pages of about 10,000 characters | $1.07 → $0.76 (−29%) | critical items 6/6 both; 21.7 and 21.2 of 24 facts filed; raw copies exact in both |
| `save-fetched` | landscape task, pages under 1,000 characters | $0.89 → $0.85 | raw copies exact 33/33, against 21/41 when the model retyped them |
| catalog lines | landscape task with a connector | $0.89 → $0.92 | pages read or seen and then lost: 15 → 6 per task; HR, personal and template pages left out |
| catalog line present | a later question about a catalogued page | $0.21 → $0.15 | same answer; one connector call instead of 3–5 |
| one session | file 20 documents (39 graded items) | $1.51 ($0.075 a document) | 35/36 judged items, all mechanical ones |
| one session per document | same | $7.03 | same; each session reads the wiki again |
| strong model, one session | same | $3.24 | same facts; filed small talk once |
| fast model, one session | same | $0.59 | lost 4 minor items |

- A document filed on its own costs $0.22–0.32. Most of that is reading and judgement:
  which pages, which qualifiers, which conflicts. Copying connector pages is the one
  mechanical part that grows with the document, so it is the one a script pays for.
- Retyping a page puts it in the context twice (the fetch and the copy) and costs output
  tokens, the most expensive kind. Retyped copies also changed: curly quotes, dropped code
  blocks, moved headers.

## Standard session or strong session
Whole sessions on each model. Two runs per case; the sample is fictional, the other cases
come from larger private packs. Runs are few, so a difference of one or two items is noise.

| Cases | Standard session | Strong session |
|---|---|---|
| PRD on the sample | critical 1.00, $0.59 | critical 0.98, $1.45 |
| three reviews (two on the sample, one private) | critical 37/40, all items 45/50, $1.73 | critical 37/40, all items 47/50, $5.19 |
| seven private retrieval and mapping cases | critical 83/84, all items 96/108, $3.47 | critical 84/84, all items 106/112, $9.21 |

- On critical items the two are level.
- On minor items the strong model found more in the three mapping cases (88% against 75%)
  and nothing more elsewhere (RFP answers, claim checks, question answering, reviews).
- So the standard model is the default, and a PM who wants the most complete map can start
  that session on the strong model. The cases are near their ceiling on the standard model,
  so they can't show where the strong model helps reasoning; that needs harder cases.

## Tested and not adopted
Each of these was built and measured, and left out because it restricts the agent without
a measured saving.

- **Pinning the two reviews to the strong model**, in their own context. It takes the
  choice from the PM, and the reviews scored the same on the standard model.
- **Running the reviews in their own context.** The reviewer isn't steered by the
  conversation, but it also loses what the PM said there. No cost or quality effect showed.
- **The fast model for bulk filing.** Filing single documents on it was reliable (22 runs,
  every planted fact found, a small slip in 3). Filing 20 documents in one session cost 61%
  less and lost 4 minor items of 32; one fast-model session per document with a standard
  reconcile cost 29% less but passed the injection warning on in only 1 of 3 runs. In
  synthesis it invented a quote, owner or date in 3 of 4 runs. It stays the PM's choice.
- **A fast-model subagent that copies connector pages.** Copies were exact and it cost 36%
  less on large pages, but the standard session filed about 2 fewer facts of 24.
  `save-fetched` does the copy with no model at all.
- **Ingest helper commands**: one call that lists the next ID, earlier versions and the
  pages a document mentions (`prep`), commands that write card frontmatter (`card`,
  `card-fill`), and one that adds catalog lines from JSON (`catalog-add`). None changed
  cost beyond noise (−7% to +16%), and commands that take long text through the shell trip
  Claude Code's safety check, so agents fell back to doing the work by hand.
- **Filing what a task discovers**: in the task itself (+24%, all facts filed; not adopted
  because the catalog line is cheaper and keeps the task short), as draft cards only
  (missed a fact), or through fast-model subagents per page (filed less).
- **Delegating the reading to cheaper subagents** in a strong session, with every quote
  checked against its file by a script. It cost 50% more with standard-model gatherers
  (the strong model took in as much as before, and the gatherers' reading came on top) and
  lost items with fast-model gatherers. Standard-model gatherers did give the most
  complete maps.
- **Rules that limit reading and replies** ("search, then read; never read a whole
  folder", "draft the PRD from the work folder", "summarize in a few lines"). Scores held,
  and cost did not fall measurably (down 1.5% over 18 cases).

## Not tried
- Lower reasoning effort on mechanical skills (`effort:` in frontmatter).
- Re-reviews that check only the changed sections.
- Earlier compaction, or a "where I left off" note that makes a new conversation cheap.
