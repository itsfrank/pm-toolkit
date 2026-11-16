# Instructions for agents developing pm-toolkit

This repository is the toolkit's source. It is not a PM workspace; don't ingest real
documents here.

## Layout
- `plugin/skills/<name>/SKILL.md`: the skills. Frontmatter `name` equals the folder name;
  `description` says what it does and when to use it, under 1024 chars.
- `plugin/workspace/`: template copied into a user's workspace by `setup`/BOOTSTRAP. Its
  `AGENTS.md` holds the shared evidence and safety rules that every skill relies on.
  `plugin/workspace/tools/` holds the helper scripts (`wiki.py`) and the viewer.
- `plugin/MIGRATION.md`: agent instructions for adopting an existing knowledge base.
- `samples/kestrel/`: a fictional example workspace. `evals/`: cases graded against it.
- `docs/`: design rationale, research, security, customizing.

## Rules for changes
- Skills are markdown. Code is welcome where it makes work deterministic or cheaper, with
  limits: Python 3.8+ standard library only, browser code as plain JS/CSS with no build step
  and no external loads, no network installs, no hooks, no required MCP servers. Shared
  scripts live in `plugin/workspace/tools/`. Keep code short enough to review in one sitting;
  users must be able to review the whole toolkit by reading it.
- Skills must not depend on a connector being present. Connector steps are optional and
  read-only.
- Keep skills directive and short. Put rationale in `docs/`, not in skill text.
- Shared conventions (citations, labels, trust levels, folders) are defined once in
  `plugin/workspace/AGENTS.md`, `plugin/workspace/wiki/README.md` and
  `plugin/workspace/design/README.md`. Change them there
  and update the skills that depend on them.
- Samples and evals use only fictional companies, people and products.
- A skill behavior change should come with an eval case or an updated one in `evals/cases.json`.
- Run `python3 scripts/validate.py` and `python3 scripts/check_leaks.py` before committing.
