---
name: setup
description: Set up or upgrade a pm-toolkit workspace (wiki, lenses, review log, work folders, AGENTS.md) in the current directory. Use when the user asks to set up, initialize, install or upgrade the PM workspace or wiki.
---

# Set up a PM workspace

The workspace template lives next to this skill at `../../workspace/` (relative to this
skill's base directory). If you can't find it, ask the user where they unpacked pm-toolkit.

## Steps
1. Confirm the target directory with the user (default: current directory). Show what it
   contains. Refuse to proceed into a non-empty directory without explicit confirmation.
   If it already holds a knowledge base that wasn't built with pm-toolkit (markdown notes,
   copied documents, an index, agent instructions), stop here and follow `../../MIGRATION.md`
   (relative to this skill's base directory) instead.
2. Copy the template tree into the target **without overwriting existing files**, including
   `tools/` (helper scripts and the viewer). For every file that already exists, list it and
   leave it untouched. The workspace must be a git repository: if it isn't, `git init` and
   tell the user why (every change can be reviewed and rolled back, and upgrades keep their
   own changes).
3. If an `AGENTS.md` or `CLAUDE.md` already exists, don't replace it. Propose a short merge:
   append the template's sections the user lacks, then show the diff and wait for approval.
   In every case, then write the version (from `<kit>/plugin/.claude-plugin/plugin.json`)
   and today's date to `.pm-toolkit-version`, commit everything, and record this release as
   the toolkit baseline (see "Toolkit branch" below):
   `python3 tools/wiki.py toolkit-branch <kit> --baseline`, where `<kit>` is the unzipped
   toolkit folder that holds `plugin/`. Add `--no-skills` in plugin mode.
4. Ask three questions and record the answers in `wiki/pages/topics/about-me.md`
   (create from `wiki/pages/_TEMPLATE.md`, type `topic`):
   - Your role, product area and the products you're responsible for.
   - Teams you work with most and the main decision-makers.
   - Which documents you can save locally to seed the wiki (specs, decks, roadmaps, notes).
5. Ask whether the organization has review checklists (launch readiness, design review,
   security or privacy review questionnaires, a PRD template). If the user saves them into
   `wiki/raw/`, card them and add their items as probes under the matching lenses in
   `wiki/lenses.md`, tagged `[org-checklist]`, with one `org-checklist` review-log entry per
   checklist.
6. Check `python3 --version` (3.8 or newer). Show the user how to open the viewer: `/wiki open`
   (or `python3 tools/viewer/serve.py --open`). It only listens on this machine, and writes
   only `wiki/notes.jsonl`. If Python is missing, the skills still work; the scripts' checks are
   then done by reading.
7. Suggest a first session:
   - Save 5–10 core documents into `wiki/raw/` and run `wiki-ingest` on them.
   - Seed the review log: save past feedback (comment exports, post-mortems) and a few
     draft-and-final pairs of approved PRDs, then run `review-feedback` in backfill mode.
   - Pick a live ask and run `pre-prd`.

## Toolkit branch
The `pm-toolkit` git branch holds each toolkit release exactly as shipped: skills under
`.claude/skills/` (copy mode), and the template files (`AGENTS.md`, `CLAUDE.md`, `tools/`,
`wiki/` template files such as `lenses.md`). Nothing else is ever committed to it, and only
`tools/wiki.py toolkit-branch` writes it. The user's branch (usually `main`) holds their
changes on top. Merging a new release from `pm-toolkit` therefore keeps the user's changes
and brings in the toolkit's, and git can tell the two apart.

## Upgrade
`$NEW` is the unzipped new release. Use its `setup` skill and its `tools/wiki.py`, not the
installed ones. Don't copy files over the workspace.
1. Note the current branch. If the working tree has changes, commit them on that branch as
   "pre-upgrade snapshot" (never the unzipped release) and tell the user.
2. If there is no `pm-toolkit` branch (installed before 0.3.0): if the user still has the
   release named in `.pm-toolkit-version`, run
   `python3 $NEW/plugin/workspace/tools/wiki.py toolkit-branch <old release> --baseline`, then
   go on. If not, compare the workspace with `$NEW` file by file one last time, show the
   differences and let the user choose; never overwrite their customizations. Commit, then
   run `toolkit-branch $NEW --baseline` and skip steps 3 and 4.
3. `python3 $NEW/plugin/workspace/tools/wiki.py toolkit-branch $NEW` (add `--no-skills` in
   plugin mode), then `git merge pm-toolkit` on the user's branch.
4. Resolve conflicts. Read `LOCAL-CHANGES.md` for the intent of the user's changes: keep the
   toolkit's new version and re-apply that intent to it. When unsure, keep the user's
   version and tell the user what the toolkit changed there. Remove `LOCAL-CHANGES.md`
   entries the new release already covers (say which).
5. Write the new version and today's date to `.pm-toolkit-version`, commit, and report: what
   the release changed (its `CHANGELOG.md`), which of the user's changes were kept, merged
   or retired, and any conflict you resolved.

## Rules
- Don't install anything, add connectors, or change Claude Code settings. The scripts in
  `tools/` use only the Python standard library.
- Report every file created, skipped or merged.
