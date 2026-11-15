# Bootstrap: instructions for the agent installing pm-toolkit

You are a coding agent (Claude Code or similar). The user downloaded this repository, most
likely as a zip, and wants a PM workspace set up. Follow these steps exactly. Setup is copying files; don't
run scripts from this repository during setup. The workspace gets small helper scripts in
`tools/` (Python standard library only) that the skills use later.

## 0. Before anything
- Tell the user to confirm their employer allows using an outside open-source toolkit and
  AI assistance on work documents. You can't verify this; just make sure they've considered it.
- Ask where the workspace should live (an empty folder, e.g. `~/pm-workspace`). Internal
  documents will go there, so it should not be inside a synced public repo.
- If the folder already holds a knowledge base (markdown notes, copied documents, an
  index, agent instructions) that wasn't built with pm-toolkit, follow
  `$KIT/plugin/MIGRATION.md` instead of the steps below. It runs without stopping for
  questions and works on a git branch the user reviews.
- Note the unzipped toolkit's root folder (call it `$KIT`) and the version in
  `$KIT/plugin/.claude-plugin/plugin.json`.

## 1. Choose an install mode (ask the user; recommend A)
**A. Copy into the workspace (recommended).** Skills become ordinary project files the user
can read, edit and review. No plugin system needed.

**B. Claude Code plugin.** Keeps the skills updatable as a unit:
`claude plugin marketplace add $KIT` then `claude plugin install pm-toolkit@pm-toolkit`
(or `/plugin` inside Claude Code). Skills are then namespaced, e.g. `pm-toolkit:pre-prd`.

## 2. Install
**Mode A**
1. Create `<workspace>/.claude/skills/`.
2. Copy every folder in `$KIT/plugin/skills/` there, including `setup` (it runs later
   upgrades).
3. Perform the setup yourself by following `$KIT/plugin/skills/setup/SKILL.md`, using
   `$KIT/plugin/workspace/` as the template directory.

**Mode B**
1. Install the plugin as above.
2. Open Claude Code in the workspace and run the `setup` skill.

Both modes: write `<workspace>/.pm-toolkit-version` containing the version number and today's
date. Don't copy `samples/`, `evals/`, `docs/` or `scripts/` into the workspace.

## 3. Verify
- List the installed skills and the workspace tree for the user.
- Confirm `AGENTS.md` and `CLAUDE.md` exist in the workspace root and `CLAUDE.md` imports
  `AGENTS.md`.
- Optional practice run: copy `$KIT/samples/kestrel` to a scratch folder, open Claude Code
  there and run `pre-prd` on `work/2026-10-05-eu-data-residency/`. It's a fictional company;
  it shows what good output looks like before real documents are involved.

## 4. First real session (suggest to the user)
1. Save 5–10 core documents into `wiki/raw/`: product overviews, the current roadmap,
   team/org notes, a recent PRD the org considers good, any glossary.
2. Run `wiki-ingest` on them.
3. Bring a live ask and run `pre-prd`.

## Upgrading
Unzip the new version alongside the old one. Mode A: compare `$KIT/plugin/skills/` with
`.claude/skills/`, show the user the differences per skill, and update only those they approve
(they may have customized skills). Then follow the Upgrade section of `setup/SKILL.md`. Mode B:
update the plugin, then run `setup` to upgrade the workspace. Both: rewrite `.pm-toolkit-version`.
Never overwrite `wiki/` content.
