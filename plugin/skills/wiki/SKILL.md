---
name: wiki
description: Front door to the PM toolkit. Routes a plain-language request to the right skill, shows what needs attention, shows the cheatsheet, or opens the wiki viewer in the browser. Runs only when the user types /wiki.
disable-model-invocation: true
argument-hint: "[what you need] | cheatsheet | open | close"
---

# /wiki

Request: $ARGUMENTS

## 1. Empty request: status
Run `python3 tools/wiki.py status`. Reply in a few lines: open notes, notes waiting on the
PM, sources due for a recheck, whether a wiki check is due, recent asks (and their next
stage) and reports, catalog coverage, and unfinished runs (`HANDOFF.md` under `work/`).
Offer the one or two most useful next actions. End with: "Say
`/wiki cheatsheet` for what you can ask."

## 2. `cheatsheet` (or `help`, `?`)
Show `wiki/CHEATSHEET.md` as it is. If it is missing, show the routing table below in plain
words. End with a single line of counts from `python3 tools/wiki.py status` (for example
"Now: 5 open notes, 1 source to recheck."). Nothing else after it.

## 3. `open` (or `viewer`)
Run `python3 tools/viewer/serve.py --open --detach`. It opens the default browser and keeps
running after this session ends. If a viewer for this workspace is already running, it only
opens the browser. Reply with the URL it printed and that `/wiki close` stops it.

## 4. `close`
Run `python3 tools/viewer/serve.py --stop` and say what it printed.

## 5. Anything else: route
Pick the skill below that fits and follow it with the request. Start your final reply with
"Used `<skill>`." on its own line, so the PM can see the routing and redirect. If two fit, take the first match in this order. Don't ask which one; the
PM can redirect.

| Request is about | Skill |
|---|---|
| a new ask that should end in a PRD | `pre-prd` |
| framing an ask only ("what are they really asking?") | `intake` |
| what exists, who owns it, what's in flight | `landscape-map` |
| what's missing from a plan or draft | `coverage-review` |
| writing or revising a PRD | `prd` |
| pressure-testing a draft | `critical-review` |
| feedback received, or a question they couldn't answer | `review-feedback` |
| RFP, RFI, security questionnaire, customer question | `rfp-response` |
| requirements against current capabilities | `gap-analysis` |
| a customer call, before or after | `customer-call` |
| competitors | `competitive` |
| marketing or sales copy | `marketing-check` |
| research, a comparison, a summary or a report to read later | `report` |
| saving a document, notes or a fact | `wiki-ingest` |
| their notes from the viewer | `wiki-notes` |
| bringing in a whole area: an acquired company, another team's space, "continue the expand" | `wiki-expand` |
| whether sources are current, syncing | `wiki-refresh` |
| cleaning up or checking the wiki | `wiki-lint` |
| setting up or upgrading the workspace | `setup` |

If nothing fits, answer the request directly under the workspace rules.
