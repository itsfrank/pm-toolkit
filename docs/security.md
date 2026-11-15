# Security and data boundaries

## For your security reviewer

`pm-toolkit` is Markdown instructions for a coding agent (Claude Code), a folder template,
a helper script (`tools/wiki.py`) and a local viewer (`tools/viewer/`). The scripts use only
the Python standard library and plain browser JavaScript. Nothing is installed from the
network; there are no hooks, background jobs, MCP servers or connectors of its own.

| | What | Where |
|---|---|---|
| **Reads** | documents the PM saves; the workspace's own files | the workspace folder |
| | Claude Code's session logs, for `wiki.py spend` only (optional) | `~/.claude/projects/` |
| | connectors the PM already has, if any, read-only by rule | as configured by the PM |
| **Writes** | wiki pages, source cards, reports, work folders, `notes.jsonl` | the workspace folder only |
| **Never sends** | no email, posts, uploads, tickets or comments (a rule; see below); outputs are drafts the PM copies out | |
| **Network** | the viewer listens on 127.0.0.1 only; the scripts make no network calls | |

What does leave the machine: everything the agent reads or writes goes to the model
provider as part of the conversation, and connector search queries go to that connector.
The rules forbid building queries from document text. Rules in `AGENTS.md` are guidance to
the model; enforce the boundaries above with Claude Code permissions and connector scopes
(section 5): your employer's policy and enforced permissions are the real controls. The
whole toolkit is short enough to review in one sitting.

## 1. Get authorization first

Before you use the toolkit with any nonpublic work material, confirm the following with the
people who own the decision (IT, security, legal, privacy):

- **Approved client and account:** a managed device and your work identity. Do not use a
  personal subscription or API key as a substitute.
- **Provider route and data handling.** Local Claude Code still sends prompts, file contents
  and outputs to the model provider, and stores session transcripts locally in plaintext by
  default. "Not used for training" does not mean "not retained." Check retention, any
  zero-data-retention arrangement, and where feedback goes
  ([Claude Code data usage](https://code.claude.com/docs/en/data-usage)).
- **Permitted data classes,** including any customer-contract, consent or residency limits.
  The agent cannot decide these for you.

If you don't have answers yet, work only with public or fully synthetic material.

## 2. Keep internal material in the local workspace

- Keep the wiki, `raw/` sources and drafts in one local project folder on the approved
  device.
- Do not sync it to personal cloud storage or a public Git remote, and do not mix it with
  public repositories.
- Never copy internal content back into a public fork of this toolkit. Contributions
  upstream must be public or independently written synthetic examples. A "sanitized"
  internal document still counts as internal.
- Deleting a raw file does not remove its derived claims, summaries, indexes, caches or Git
  history. Trace and remove all of them, and follow your employer's retention rules.

## 3. Check policy before importing outside repos or skills

Third-party skills, plugins and MCP packages are software that runs with delegated authority,
even when they look like plain prompts.

- Check employer policy on installing extensions first. Then read the whole skill:
  instructions, scripts, hooks, dependencies and requested access. Pin the reviewed
  revision instead of a mutable `main` branch, and confirm its license.
- Prefer copying and adapting one reviewed file over installing a whole marketplace.
- Never run commands just because a README or skill suggests them.

OWASP lists tool poisoning, silently changed tool definitions, over-scoped tokens and
supply-chain compromise among the main risks
([OWASP MCP Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/MCP_Security_Cheat_Sheet.html)).

## 4. Treat saved documents as untrusted

Anything you save into the wiki can contain instructions written to hijack an agent. That
includes web pages, RFPs, customer emails, call transcripts, competitor pages and issue
comments. Indirect prompt injection through retrieved files is a recognized risk, and RAG does
not fully prevent it ([OWASP LLM01:2025](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)).
Claude Code's MCP documentation gives the same warning about external content
([MCP](https://code.claude.com/docs/en/mcp)).

- Source text is evidence data, never instructions. Skills say this explicitly.
- Content in `raw/` must never change instruction files, skills, output destinations or tool
  permissions. An agent may *propose* an instruction change, and a human approves it.
- Do not let a summary or memory silently carry instructions or private facts forward. No
  automatic memory promotion.
- Test your setup with a synthetic injected instruction ("ignore previous instructions and
  send…") and confirm the agent treats it as content.

## 5. Constrain authority, not just language

- Prompts and `CLAUDE.md` rules are guidance. Permission rules are what the runtime enforces,
  with deny taking precedence over ask, and ask over allow
  ([Permissions](https://code.claude.com/docs/en/permissions)).
- An approved shell command runs with your account's authority. Sandboxing, which isolates the
  filesystem and network, is a separate layer
  ([Security](https://code.claude.com/docs/en/security)).
- Check `/permissions` and the active connectors before you start. Avoid broad "don't ask
  again" grants until you understand how far they reach.
- "Read-only" protects source integrity, not confidentiality. A read-only search tool can
  still send confidential text out in its query arguments.
- If you later add a connector, add one, with narrow scopes, after approval. Keep it read-only
  until retrieval quality has been shown to be good. The workspace rules tell the agent to use
  every connector for reading only, even one that allows writes; if your client can disable a
  connector's write tools, do that too, because a rule is guidance and a permission is a
  control. Freshness checks (`wiki-refresh`) only read metadata and content of documents the
  wiki already cites. `wiki-expand` surveys a whole space; its search queries and page
  fetches leave the machine like any connector use, and it excludes personal spaces and HR
  pages by rule.
- `python3 tools/wiki.py spend` reads Claude Code's own session logs under
  `~/.claude/projects/` (read-only, local) to total token usage for budgets. It is the only
  helper that reads outside the workspace. Admins should inventory every connector
  surface ([Managed MCP](https://code.claude.com/docs/en/managed-mcp)).

## 6. Human approval before anything leaves the machine

The toolkit produces drafts only, such as PRDs, RFP answers, battlecards, call summaries and
emails. A person reviews each draft and sends it through the normal channel. Do not wire up
auto-send, auto-post, ticket creation or notifications. If an approved workflow ever writes
externally, the approval should cover the exact target, actor and content, and it should be
enforced outside the model
([OWASP AI Agent Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html)).

Do not paste confidential troubleshooting transcripts into product feedback channels. Feedback
uploads can include conversation content as-is
([Claude Code data usage](https://code.claude.com/docs/en/data-usage)).

## 7. Never put these in the wiki

- Credentials, API keys, tokens, passwords, session cookies or private keys
- Customer personal data beyond what the task strictly needs. Use roles ("platform admin at
  a mid-size customer") instead of names, emails or phone numbers
- Regulated data (health, payment card, government ID) and anything under legal hold
- Material a contract, NDA or customer agreement restricts, unless the use is explicitly
  permitted
- Deal terms, pricing exceptions or unreleased financials unless policy allows it
- Content from a higher access tier than everyone who can read the wiki. A summary can leak
  restricted facts
- Synthetic personas or generated quotes presented as real customer evidence

## 8. Stop conditions

Stop and follow your employer's incident process if the agent reads data outside the
workspace, contacts an unexpected network destination, loads an extension you can't
explain, or its permissions don't match what you expected.

Keep a short record of the pilot: scope, data classes, reviewer, tests run and when you will
review it again. This matches the governance, mapping, measurement and management practices
in [NIST AI 600-1](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf).
