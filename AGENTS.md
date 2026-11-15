# Instructions for agents developing pm-toolkit

This repository is the toolkit's source. It is not a PM workspace; don't ingest real
documents here.

## Layout
- `plugin/skills/<name>/SKILL.md`: the skills. Frontmatter `name` equals the folder name;
  `description` says what it does and when to use it, under 1024 chars.
- `plugin/workspace/`: template copied into a user's workspace by `setup`/BOOTSTRAP. Its
  `AGENTS.md` holds the shared evidence and safety rules that every skill relies on.
- `samples/kestrel/`: a fictional example workspace. `evals/`: cases graded against it.
- `docs/`: design rationale, research, security, customizing.

## Rules for changes
- Skills are markdown only: no scripts, hooks or MCP dependencies. Users must be able to
  review the whole toolkit by reading it.
- Keep skills directive and short. Put rationale in `docs/`, not in skill text.
- Shared conventions (citations, labels, trust levels, folders) are defined once in
  `plugin/workspace/AGENTS.md` and `plugin/workspace/wiki/README.md`. Change them there
  and update the skills that depend on them.
- Samples and evals use only fictional companies, people and products.
- A skill behavior change should come with an eval case or an updated one in `evals/cases.json`.
- Run `python3 scripts/validate.py` and `python3 scripts/check_leaks.py` before committing.
