# Customizing

The toolkit gets better the more it reflects your organization. In order of payoff:

## 1. Seed the wiki
The first week matters most. Save and ingest:
- product overviews and docs for everything you own and its neighbors;
- the current roadmap and the list of initiatives in flight;
- org charts or team pages (who owns what);
- two or three PRDs your organization considers good;
- any internal glossary or code-name list.

After each meeting where you learned something durable, paste your notes and run `wiki-ingest`.

## 2. Seed the review log
Don't wait for reviews to accumulate. Save past comment threads, post-mortems, and draft and
final versions of a few approved PRDs (colleagues' work counts: it shows the organization's
bar), then run `review-feedback` in backfill mode. After meetings, log questions you couldn't
answer ("asked about X, didn't know"); it takes one line.

## 3. Tune the lenses
`wiki/lenses.md` is yours. Add probes your organization always asks about (a certification
you must keep, a platform every feature must support, a launch-review checklist). Mark lenses
that never apply. Lessons from `review-feedback` land here automatically.

## 4. Use your PRD template
Save your organization's template at `wiki/pages/topics/prd-template.md`. The `prd` skill
uses it when present and keeps its evidence rules.

## 5. Record reviewer preferences
`review-feedback` builds `wiki/pages/topics/review-preferences.md`: who wants what level
of detail, which sections are mandatory, and recurring questions. `critical-review` reads it.

## 6. Edit skills
Skills are plain markdown in `.claude/skills/` (copy mode); helper scripts are in `tools/`. Change steps, templates or tone
directly, or ask the agent to. Keep the evidence rules; most of the toolkit's value depends on them.

Your changes survive upgrades. The workspace's `pm-toolkit` git branch holds each release
exactly as shipped, and an upgrade merges the new release from it into your branch, so git
can tell your changes from the toolkit's. The agent records why it changed a skill or rule
in `LOCAL-CHANGES.md`; when a new release rewrote the same text, the upgrade re-applies that
intent to the new version. Plugin mode can't keep skill edits: use copy mode if you will
change skills.

To suggest an improvement upstream, ask the agent for a note on your `general` changes. It
drafts one without internal details; read it before you send it.

## Other domains
Nothing in the skills assumes an industry. For a regulated domain, add the regime to lens 9
and save the relevant standards into `wiki/raw/` so claims can cite them.
