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
| get a whole new area: an acquired company, another team's space | "Bring in everything about X." (add "with a budget of $20" to run it without stopping) | A survey of every page for you to approve, then the best pages filed, the rest catalogued, and a summary report |
| have a document or meeting notes | "Save this to the wiki." (paste, or give the file) | The document saved, a source card, and the facts filed into pages |
| got feedback, or were asked something you couldn't answer | "My reviewer said…" / "They asked me X and I didn't know." | A lesson the toolkit checks next time, and the wiki fixed |
| finished a draft | "Review this like my toughest reviewer would." | A list of what a demanding reviewer would catch |
| need customer-facing answers | "Answer this RFP / questionnaire / email." | Draft answers from approved sources only, with gaps marked |
| need a mockup | "Mock up a usage panel on the Insights overview." Share screenshots or saved pages of the product the first time. | One HTML file you can share, styled like the real product. Corrections you give are remembered for next time |
| have other work | "Prep me for my call with…", "Check this datasheet", "Compare us with…", "Gap analysis against…" | Call prep or debrief, a fact-check, a comparison, a gap table |

## Reading and notes
- Open the viewer: `/wiki open` opens it in your browser (it runs only on this computer).
  `/wiki close` stops it. Without Claude: open **PM Wiki** from Applications or Spotlight
  (ask Claude once to "add the wiki launcher"), and press **Quit** in the top bar to stop it.
- **Home** shows what is waiting on you and on Claude. You can answer Claude's questions
  there, drop in a document or paste text to save it, and leave requests for next time.
  None of that needs Claude running; Claude picks it up when you next work together.
- Search (the box at the top) finds words, their other forms and the names in the glossary,
  best matches first; the chips narrow results to pages, sources or originals.
  It doesn't understand meaning: if a search misses a page, tell Claude which word you
  tried and it adds it.
- Select any text and click **Note** to leave a comment. Claude processes notes when you
  say "go through my notes", and tells you when there are open ones.
- Click a citation like `[S-0012]` to see the source it came from.
- **Mockups** in the top bar lists design systems, product screens and mockups; they open
  in a new tab.

## Long jobs
Big jobs (bringing in an area, a migration) stop gracefully when their budget runs low: you
get a report of what's done and what isn't, and "continue the expand with a budget of $N"
picks up where it left off.

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

## Cost
- You pick the model. The workspace starts on the mid-size one (Sonnet), which is enough
  for most work. For a session that needs the strongest model, start Claude with
  `claude --model opus` or type `/model opus`; it costs two to three times as much. Nothing
  switches to it on its own.
- One task per conversation. Start a new one for a new task, and after a long break: say
  "continue work/<folder>" and it picks up from the files. Coming back to a long
  conversation makes Claude re-read all of it at full price.
- "What did I spend this week?" shows where the money went, by model and by conversation.

## Safety
- Nothing is sent anywhere. You copy drafts out yourself after reading them.
- If the workspace uses git, say "commit this" after work you want to keep. Anything
  committed can be shown or undone; uncommitted changes can't.
