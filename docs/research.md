# Research behind the toolkit design

This page condenses the public research that shaped `pm-toolkit`. Each section states a
finding, cites the public source, and says what the toolkit does because of it.

How to read the evidence: most sources are vendor documentation, practitioner frameworks
or a small number of experiments. None of them shows in a controlled way that an
LLM-assisted PM workflow produces better product decisions. The toolkit is a set of
reasonable defaults to test on your own work. It is not a proven method.

## 1. Agent workflows: skills, subagents, instruction files, review gates

### Start with bounded workflows, not an autonomous PM

Anthropic separates *workflows*, which follow predefined steps, from *agents*, which choose
their own process and tools. It recommends the simplest solution that works and points to
the latency and cost of autonomy. Prompt chaining with checks between steps (outline,
check, draft) suits PM documents well
([Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)).

**Design implication:** each skill runs a fixed sequence with explicit gates, for example
inventory sources, extract claims, draft, then verify. A skill does not decide on its own
what to research or publish.

### Use each mechanism for its own job

- **Instruction files (`CLAUDE.md`, `AGENTS.md`)** hold persistent guidance written by
  people. Keep them short and specific; the docs suggest under about 200 lines per file.
  They are context, not enforced configuration
  ([Memory](https://code.claude.com/docs/en/memory)).
- **Skills** package a repeatable procedure. The body loads only when the skill is used, so
  long procedures belong in skills, not in always-loaded instructions
  ([Skills](https://code.claude.com/docs/en/skills)). Anthropic's skills repository shows the
  self-contained `SKILL.md` folder structure
  ([anthropics/skills](https://github.com/anthropics/skills)).
- **Subagents** run in their own context with their own prompt and tool access. They keep
  bulky exploration out of the main conversation, but they still use up shared usage limits
  ([Subagents](https://code.claude.com/docs/en/sub-agents)).
- **Permissions** are enforced by the runtime. Deny rules win over ask, and ask wins over
  allow. Prompt text and skills do not change what the agent is allowed to do
  ([Permissions](https://code.claude.com/docs/en/permissions)).

**Design implication:** `CLAUDE.md` / `AGENTS.md` hold only boundaries, citation rules and
output locations. Procedures live in skills. Read-only reviewer subagents (citation
checker, red-team critic) are added only where separate context helps. The toolkit never
treats a written rule as a security control.

### More agents are not automatically better

Anthropic's multi-agent research write-up reports coordination failures and much higher
token use, and says the architecture fits only some tasks
([Multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)).

**Design implication:** use a subagent only when it isolates context or adds an independent
review. Do not add one just to have more agents.

### Public PM skills are prior art, not validated colleagues

Public PM skill repositories contain useful patterns: clarifying questions before drafting,
explicit inputs, phase outputs, decision gates, and assumptions kept apart from facts
([Dean Peters, discovery-process skill](https://github.com/deanpeters/Product-Manager-Skills/blob/main/skills/discovery-process/SKILL.md);
[usage guide](https://github.com/deanpeters/Product-Manager-Skills/blob/main/docs/Using%20PM%20Skills%20with%20Claude%20Code.md);
[phuryn create-prd skill](https://github.com/phuryn/pm-skills/blob/main/pm-execution/skills/create-prd/SKILL.md)).
Some of these skills also allow open-ended web research or automatic file writes. No
outcome studies were found.

**Design implication:** borrow the patterns, then tighten the boundaries: set a source
budget, require an explicit output path, and check that a decision owner is named. Read a
skill's instructions, scripts and hooks before adopting it. Do not follow next steps that a
skill suggests without checking them first.

### Task contracts and compact handoffs

Every bounded task should state its goal, allowed inputs and excluded data, allowed tools,
output file, claim/source schema, source or time budget, stop conditions and reviewer.

Run one task per session where practical. At each checkpoint, keep a short handoff: verified
facts with source IDs, decisions a human actually made, open questions, and the next action.

**Design implication:** skills begin from a task contract and end with a handoff block. The
toolkit does not keep whole chat transcripts as memory.

## 2. Pre-PRD discovery and unknown-unknowns methods

### An agent proposes candidate gaps; humans decide what matters

A model cannot reveal a true unknown unknown on request. It can propose *candidate* gaps by
reframing the question, testing assumptions, tracing boundaries and adding perspectives.
Once a gap is named, it becomes a known question, not a verified risk. Expertise, customer
observation and targeted tests decide whether it matters.

Use four working categories (proposed, not a validated taxonomy):

1. **Known fact:** supported by a source, within a stated scope.
2. **Known unknown:** the question is clear but the answer is missing or disputed.
3. **Unexamined assumption:** the plan depends on it, but no one has said so.
4. **Unknown unknown:** not yet considered at all.

Also design for **known to someone else**: the answer exists, but you have not found the
person or the page yet.

### Think independently before reading AI output

The experimental evidence is mixed and depends on the task. One study found that AI help
improved individual creativity on simple tasks but hurt it on complex tasks, consistent with
fixation ([Humanities & Social Sciences Communications](https://www.nature.com/articles/s41599-025-05867-9)).
In another experiment (n=75), individuals supported by GPT-3.5 did not perform better on
their own, but the combined human and AI output scored higher on collective brainstorming
measures ([Business & Information Systems Engineering](https://link.springer.com/article/10.1007/s12599-025-00974-y)).
Evidence note: only abstracts and introductions were reviewed, and neither study looks at
PM work.

**Design implication:** discovery skills ask for your own two or three concerns *before*
showing the model's list. Judge results by how many questions changed a decision, not by
how many risks were generated.

### Methods the toolkit uses

- **Premortem.** Assume the plan failed, then build distinct causal paths to that failure.
  Gary Klein describes it as a way to bring out plausible failure reasons and make
  knowledgeable dissent easier ([HBR, Performing a project premortem](https://hbr.org/2007/09/performing-a-project-premortem)).
  Output: scenario → causal chain → earliest warning sign → assumption → next test. An
  imagined failure is a prompt for investigation, not a forecast.
- **Assumption mapping / inversion.** For each proposed behavior, ask what must be true
  about users, data, systems, incentives, authority and timing, then ask "what if it is
  false?" Sort assumptions into four queues: value, usability, feasibility and viability
  ([SVPG, Four big risks](https://www.svpg.com/four-big-risks/)). The agent must not answer
  feasibility or legal questions on behalf of the people responsible for them.
- **Lifecycle and handoff walk.** Walk through learn → evaluate → procure → deploy →
  configure → operate → troubleshoot → upgrade → retire. At each stage, note the actor,
  inputs, dependencies, authority, failure and recovery. Pay most attention to handoffs.
- **Boundary and negative-space analysis.** List the adjacent systems, trust boundaries,
  identities, data flows and dependencies owned by others. An empty cell in a coverage
  matrix means no evidence was supplied. It does not mean the capability is missing.
- **Perspective lenses.** Run through evaluator, buyer, implementer, administrator, operator,
  support, partner, security, legal and accessibility roles. Simulated personas produce
  questions, not testimony.
- **Opposing explanations.** For any signal, list at least two other explanations and the
  evidence that would tell them apart. Always compare against a do-nothing or learn-first
  option.
- **Red-team and surprise log.** For consequential changes, ask someone who did not write
  the plan to challenge it. A model critique adds a perspective but does not replace an
  independent expert. After each review, log what was missed and add a check only after a
  human has reviewed it.

**Design implication:** the unknown-unknowns skill runs an evidence pass, a premortem and a
boundary/lifecycle pass, then a human picks at most five items by consequence and decision
relevance. The skill gives no invented probabilities. Severe, irreversible harms are flagged
even when they cannot be quantified. Stop growing the checklist once it produces repeated
noise.

### Strategy and PRD framing

- Strategy means choosing problems and what *not* to do. A polished feature list is not a
  strategy ([SVPG, Product strategy](https://www.svpg.com/product-strategy-overview)).
- A customer-first PR/FAQ tests value before building. The quote and launch date in it must
  be clearly marked as fictional
  ([Working Backwards, PR/FAQ](https://workingbackwards.com/concepts/working-backwards-pr-faq-process/)).
- RICE helps judgment but does not decide the roadmap. Dependencies and table-stakes work
  can override the scores, and confidence bands describe how well-supported an estimate is,
  not the probability of success
  ([Intercom, RICE](https://www.intercom.com/blog/rice-simple-prioritization-for-product-managers/)).

**Design implication:** a PRD is an evidence-and-decision packet. "Baseline unknown",
"owner unassigned" and "estimate pending" are valid entries, and the agent never fills them
with plausible numbers or names. If inputs are missing, prioritization returns "unrankable
pending evidence" and a sensitivity analysis. Decisions go in an append-only log.

## 3. Evidence and traceability

### Do not use AI to replace discovery with real people

Teresa Torres separates learning from real past behavior from producing plausible artifacts
about imaginary customers. Synthetic interviews can be used to rehearse a method. They
cannot establish what customers need
([Product Talk, generative AI and discovery](https://www.producttalk.org/generative-ai-discovery)).
This applies equally to persona "digital twins" built from existing data: their answers are
retrieval or inference, not new participants
([Dovetail AI overview](https://docs.dovetail.com/help/dovetail-ai/overview)).

**Design implication:** the toolkit has no synthetic-validation path. Anything model-generated
about customers is labeled `synthetic` at both the document and the claim level and can
never support a demand claim.

### Synthesize one interview before synthesizing across interviews

Torres warns against dumping transcripts together and asking for generic themes. AI
synthesis cannot repair missing context or a shallow story. Build a snapshot for each
interview first: context, timeline, goal, workaround, outcome and opportunities
([Customer interview analysis](https://www.producttalk.org/customer-interview-analysis-ai)).
Keep learning interviews, sales calls, support conversations and solution tests separate
([Customer interviews](https://www.producttalk.org/customer-interviews)). JTBD switch
interviews reconstruct an actual change decision: what pushed the customer, what pulled
them, and what friction slowed them
([Bob Moesta, JTBD case studies](https://businessofsoftware.org/talks/live-jobs-to-be-done-case-studies/)).

**Design implication:** the customer-call skill extracts verbatim spans with speaker labels
and stable anchors, keeps fact, interpretation and proposed solution in separate fields, and
marks missing context as unknown. Only snapshots a human has reviewed go into
cross-interview synthesis, and both supporting and contradicting evidence are kept.

### A citation is a testable dependency, not a trust badge

Dovetail's engineering write-up reports citations that failed in follow-up turns and in
outbound messages. A citation can exist without supporting the claim
([Dovetail, the work you don't see](http://dovetail.com/blog/the-work-you-dont-see)).
Evidence note: this is a vendor self-report with no published error rates.

**Design implication:** every load-bearing claim carries a source ID, URL or path, a short
supporting passage and the access date. Reviewers check that the passage actually supports
the claim, not just that the link opens. Also check that citations still resolve after a
follow-up question or an export.

### Counting rules

Mention counts describe the sample, not how common something is in the market. Several
tickets from one account are not independent demand signals. The absence of a complaint
validates nothing. Two summaries of the same source do not corroborate each other. Never
invent confidence percentages, respondent counts or hours saved.

## 4. LLM wiki / knowledge base design

### Raw sources → wiki pages → index

Karpathy's LLM Wiki idea describes an agent that incrementally maintains an interlinked
Markdown wiki over immutable raw sources, guided by a schema. Sources are ingested one at a
time with a human involved, and answers carry citations
([Karpathy, LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)).
Evidence note: this is a practitioner pattern, not a measured result.

**Design implication:** the toolkit wiki has three layers: `raw/` (read-only sources with
provenance), wiki pages derived from claims, and an index for navigation. Instructions, decisions and session handoffs live outside the content layers, so an ingested
document cannot rewrite agent rules.

### Provenance on every page

For each raw source, record the URL or path, publisher, publication date (if verified),
access date, extraction limits and reuse constraints. Each claim records the exact passage,
source version, scope (product, version, mode), evidence class, reviewer and links to any
contradicting or superseding claims. Generated summaries are derived artifacts and never
count as new corroboration. Keep "last checked" separate from the publication date, and never
set an access date to today without actually retrieving the source.

### Editorial workflow, not "let the model remember everything"

The loop is source → claim → proposed page diff → human review → index → refresh. The agent
proposes a diff and lists the claims it changed. Before marking a page reviewed, a
human checks that the passage supports the claim, the scope and freshness fit this use,
conflicting evidence is shown, and fact, interpretation and proposal can be told apart.

A newer source is not automatically more authoritative. Do not overwrite a statement that is
still true for an older version.

### Linting and maintenance

Run a weekly lint for broken links, orphan pages, unresolved conflicts and stale claims.
Re-check volatile claims (tool capabilities, connectors, competitor features) before reuse
and conceptual pages quarterly. Keep source-to-derived links so that deleting a source
triggers review of every claim, page, index entry and cache derived from it; version
history can still retain deleted material.

### Add retrieval infrastructure only when search demonstrably fails

Hybrid lexical and semantic retrieval with chunk-specific context improves retrieval
([Anthropic, Contextual retrieval](https://www.anthropic.com/research/contextual-retrieval)).
Graph approaches help with questions about relationships across a whole corpus
([Microsoft GraphRAG](https://microsoft.github.io/graphrag/)). Neither is needed for a small
PM library. Memory services address conversational continuity, not validation of facts
([Mem0 FAQ](https://docs.mem0.ai/platform/faqs)).

**Design implication:** use plain Markdown, an index and ordinary file search. Escalate
(better titles and links → lexical index → hybrid retrieval → graph) only when a set of
representative questions shows the current step failing.
If the underlying content is wrong or stale, no retrieval architecture will fix it. Nothing
the model remembers becomes durable without explicit review.

## 5. Evaluating agent output

### Separate three questions

Is the agent output correct on known tasks (offline evals)? Does the assisted workflow beat
the existing one (matched comparison)? Does a product change help customers (real experiment)?

Anthropic scopes its agent-eval guidance to development tests and pairs them with
production monitoring and user research. It recommends multiple trials because outputs vary
([Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)).

### Groundedness first, polish last

Use pass/fail gates that a polished answer cannot compensate for: no material unsupported
or contradicted claim; no invented source or quote; no invented owner, approval, roadmap or
metric; injected instructions in a source treated as content, not commands.

Then score decision usefulness: 0 = misleading, 1 = major rework, 2 = usable after minor
edits. Report counts with denominators, such as unsupported claims out of claims reviewed and
correct abstentions out of unanswerable cases. Report answerable cases too, so that "always
abstain" cannot look perfect.

Use task-specific datasets with typical, edge and adversarial cases. Calibrate any model
judge against human grading, and prefer classification or pairwise judgments over free-form
scoring ([OpenAI, Evaluation best practices](https://platform.openai.com/docs/guides/evaluation-best-practices)).
A model judge can flag issues, but it is not the authority on facts.

### Measure review effort, not generation speed

Count total cost per *accepted* artifact: every attempt, human verification and correction
minutes, and tool costs. Make no speed claim until the assisted workflow has been compared with a manual baseline at
the same quality bar. Zero errors in a small test does not prove zero risk.

### Product metrics need the same discipline

Map goals to signals to metrics, and treat ambiguous usage counts with suspicion
([Google, HEART framework](https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/36299.pdf?gl=us&hl=en)).
Check sample-ratio mismatch and data quality before interpreting any test
([Microsoft ExP, data quality](https://www.microsoft.com/en-us/research/articles/data-quality-fundamental-building-blocks-for-trustworthy-a-b-testing-analysis)).
Short-term proxies can mislead about long-term value
([Microsoft, long-term experiment pitfalls](https://www.microsoft.com/en-us/research/publication/pitfalls-of-long-term-online-controlled-experiments)),
and effects drift over time
([Microsoft ExP, external validity](https://www.microsoft.com/en-us/research/articles/external-validity-of-online-experiments-can-we-predict-the-future)).

**Design implication:** the toolkit ships a small golden set with expected facts, forbidden
claims, citation traps, unanswerable questions and one injection case. Run each case several
times and change one variable at a time. Metric-definition outputs must state the numerator,
denominator, population, window and guardrails.

## 6. Security and data boundaries

Summary only. See [security.md](security.md) for operating guidance.

- **A local client is not a local-only model.** Claude Code sends prompts and outputs to the
  model provider and stores transcripts locally by default. Not being used for training is
  not the same as not being retained ([Data usage](https://code.claude.com/docs/en/data-usage)).
- **Prompt injection through retrieved content is a core risk.** RAG does not fully prevent
  it. Mitigations are segregating external content, least privilege, human approval for
  consequential actions and adversarial testing
  ([OWASP LLM01](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)).
- **Connectors are delegated authority.** MCP risks include tool poisoning, changed tool
  definitions, confused deputies, over-scoped tokens and supply-chain compromise. Tool
  annotations are hints, not enforcement
  ([OWASP MCP security](https://cheatsheetseries.owasp.org/cheatsheets/MCP_Security_Cheat_Sheet.html)).
  Read-only tools can still leak data through their query arguments. Claude Code warns that
  external content can carry injected instructions ([MCP](https://code.claude.com/docs/en/mcp)).
- **Constrain authority, not just language.** Permission rules are enforced; prompts are not.
  An approved shell command runs with the user's authority unless it is sandboxed
  ([Security](https://code.claude.com/docs/en/security)). Use least privilege, isolated
  memory and action-specific approvals
  ([OWASP AI agent security](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html)).
  Keep an accountable record of scope, tests and incidents
  ([NIST AI 600-1](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf)).

**Design implication:** the toolkit is markdown-only, needs no connectors, MCP servers or
hooks, and produces drafts only. Saved documents are treated as untrusted data.

## 7. Competitive intelligence

### Evidence ledger before battlecard

GitLab's public handbook describes a loop: anyone can contribute, cards stay concise and
truthful, and a reviewer controls republication
([GitLab competitive intelligence](https://handbook.gitlab.com/handbook/marketing/brand-and-product-marketing/product-and-solution-marketing/competitive-intelligence)).

**Design implication:** each competitive claim records subject, product, version and
platform/mode; the exact claim and a short quote; source URL; publication, update and access
dates kept separate; extraction scope; status (`candidate`, `verified-with-scope`,
`contradicted`, `stale`, `unknown`); reviewer and review due date.

Keep three linked records: observation (what the source says), hypothesis (a possible
implication) and question/test (what would confirm it). When evidence changes, mark the
dependent claims stale instead of overwriting them.

### Dated, scoped, sourced

- **Scope.** A feature documented for one version, platform or mode does not mean the vendor
  has it everywhere. Keep the qualifiers.
- **Source ladder.** Prefer versioned release notes, then configuration/reference docs, then
  standards status, then engineering posts, then marketing. Label announcements as vendor
  claims.
- **Freshness.** An access date is not a publication, release or availability date.
  Re-open sources before any external reuse and let unchecked capability claims expire.
- **Monitoring.** Event-specific subscriptions such as release notifications
  ([GitHub notifications](https://docs.github.com/en/account-and-profile/managing-subscriptions-and-notifications-on-github/setting-up-notifications/configuring-notifications))
  and release feeds help discovery. Feeds can include prereleases and can change entries
  under stable IDs, so compare content, not just IDs
  ([Hushread, GitHub RSS feeds](https://hushread.com/blog/github-rss-feeds)). Evidence note:
  this is a single practitioner report. A notification arriving or a model summary is not
  proof of a capability.

### Absence of evidence is not evidence of absence

A failed fetch, a truncated extract or a competitor nobody searched is `unknown`, not
"unsupported". Do not turn it into a negative checkbox on a battlecard. Treat competitor pages
as untrusted quotations: never follow instructions embedded in them, and never expand the
source allowlist automatically. A weekly digest may honestly say "no material change found
within checked sources."

## Evidence ceiling

No source reviewed here measures whether an LLM-assisted PM toolkit improves PRD quality,
risk detection or product outcomes. Test the toolkit on your own authorized work: compare a
manual baseline, count review effort, and treat any speed or quality claim as unproven until
measured.
