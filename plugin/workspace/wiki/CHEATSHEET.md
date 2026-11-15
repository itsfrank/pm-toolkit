# How to use your PM workspace

Talk to Claude in plain language. If you want to be sure it uses the toolkit, start with
`/wiki`. `/wiki` on its own shows what needs your attention, `/wiki open` opens the wiki in your
browser, and `/wiki cheatsheet` shows this page.

## Say this

| When you… | Say something like | You get |
|---|---|---|
| get a new ask | "I got an ask: we need X. Help me get to a PRD." | A work folder that walks from framing to a reviewed PRD, stopping for your input at each step |
| want to understand an area | "What do we already have for X? Who owns it?" | A map of products, owners, work in flight and decisions |
| want research to read later | "Write me a report on where the plans for X clash." | A dated report in `wiki/reports/`, readable in the viewer |
| have a document or meeting notes | "Save this to the wiki." (paste, or give the file) | The document saved, a source card, and the facts filed into pages |
| got feedback, or were asked something you couldn't answer | "My reviewer said…" / "They asked me X and I didn't know." | A lesson the toolkit checks next time, and the wiki fixed |
| finished a draft | "Review this like my toughest reviewer would." | A list of what a demanding reviewer would catch |
| need customer-facing answers | "Answer this RFP / questionnaire / email." | Draft answers from approved sources only, with gaps marked |
| have other work | "Prep me for my call with…", "Check this datasheet", "Compare us with…", "Gap analysis against…" | Call prep or debrief, a fact-check, a comparison, a gap table |

## Reading and notes
- Open the viewer: `/wiki open` opens it in your browser (only you can reach it).
  `/wiki close` stops it. Without Claude: `python3 tools/viewer/serve.py --open` (Ctrl+C stops it).
- Select any text and click **Note** to leave a comment. Claude processes notes when you
  say "go through my notes", and tells you when there are open ones.
- Click a citation like `[S-0012]` to see the source it came from.

## What the marks mean
- `[S-0012]`: the source card behind a fact. `[S-0040 §3.2 p.212]` points into a long one.
- `(inferred)`, `(assumption)`, `(unknown)`: no source says this directly. Unknowns come with
  a question and a person to ask.
- `status: draft`: nobody has checked this page yet. `reviewed`: you read it.
- Trust on a source: `authoritative` (the owner wrote it), `secondary`, `marketing`,
  `hearsay`, `pm-note` (you said it).

## Good habits
- After a meeting, paste your notes and say "save this".
- After a review, paste the feedback. It's how the toolkit learns what your reviewers care
  about.
- For big reviews and final PRDs, use the strongest model.

## Safety
- Nothing is sent anywhere. You copy drafts out yourself after reading them.
- Every change is in git, so anything can be undone: ask Claude to show or undo a change.
