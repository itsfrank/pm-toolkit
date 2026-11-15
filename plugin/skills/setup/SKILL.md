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
2. Copy the template tree into the target **without overwriting existing files**. For every
   file that already exists, list it and leave it untouched.
3. If an `AGENTS.md` or `CLAUDE.md` already exists, don't replace it. Propose a short merge:
   append the template's sections the user lacks, then show the diff and wait for approval.
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
6. Suggest a first session:
   - Save 5–10 core documents into `wiki/raw/` and run `wiki-ingest` on them.
   - Seed the review log: save past feedback (comment exports, post-mortems) and a few
     draft-and-final pairs of approved PRDs, then run `review-feedback` in backfill mode.
   - Pick a live ask and run `pre-prd`.

## Upgrade
When a workspace exists, compare it with the template. Add missing folders and files. For
changed template files (`lenses.md`, `wiki/README.md`, `AGENTS.md`), show the differences and
let the user choose; never overwrite their customizations.

## Rules
- Don't install anything, add connectors, or change Claude Code settings.
- Report every file created, skipped or merged.
