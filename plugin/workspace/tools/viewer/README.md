# Wiki viewer

A local web page for reading the wiki and `work/` folders as rendered markdown, with
clickable citations, search and notes, and a Home page for the days the PM works without an
assistant. Python 3 standard library and plain browser JavaScript; no installs, no build
step, no network access, no model.

## Run
```
python3 tools/viewer/serve.py            # http://127.0.0.1:8765/
python3 tools/viewer/serve.py --open --port 8800
python3 tools/viewer/serve.py --open --detach   # keep running in the background
python3 tools/viewer/serve.py --stop            # stop this workspace's viewer
python3 tools/viewer/serve.py --install-app     # macOS: add "PM Wiki" to ~/Applications
```
It listens on 127.0.0.1 only, serves only `.md` files inside the workspace, saved originals
from `wiki/raw/` and `design/`, and mockups from `design/` (in a sandbox with no network or
viewer access; their local stylesheets are inlined when served). Stop it with Ctrl+C, or
**Quit** in the top bar.

What it writes, and nothing else:
- `wiki/notes.jsonl`: notes, requests and answers, appended.
- New files in `wiki/raw/` for documents the PM adds on Home, each with a draft card in
  `wiki/sources/`. A name that exists gets `-2`, `-3`; no file is ever overwritten.

It answers only requests addressed to `127.0.0.1` or `localhost`, and accepts a write only
with a header its own page sends, so another site open in the browser cannot read the wiki
or post into it.

## Launcher (macOS)
`--install-app` writes `~/Applications/PM Wiki.app`: a folder holding a short shell script
that runs `serve.py --open --detach` for this workspace. Spotlight and Launchpad find it, so
the wiki opens without a terminal. `--app-name` picks another name (one app per workspace),
`--app-dir` another folder. It replaces only a launcher it wrote before. Moving the app to
the Trash removes it; run the command again if the workspace folder moves.

## Use
- **Home** lists what is waiting on the PM (with a box to answer), what is waiting for the
  assistant, sources to recheck, pages with conflicts or unsourced facts, and recent work:
  the same checks `wiki.py status`, `due` and `lint` print. The PM can drop files or paste
  text to save a document, and leave requests for the next session.
- The left panel lists files by folder, with a dot for page status (draft or reviewed).
  Filter by name.
- The search box in the top bar (`/` jumps to it) opens a results page as you type: one
  card per file with its best three matching lines, the rest behind "Show all", and chips
  to narrow to pages, sources, originals or work. Arrow keys walk the results; a result
  opens at its line with the matched words marked; Back returns to the results.
- Search (`search.py`) covers the markdown files and the text originals in `wiki/raw/`,
  best matches first. It uses SQLite's full-text index, which ships with Python: every word
  must match as typed, as a prefix, in another form (pricing, priced) or as a glossary
  synonym. With no result it retries with the closest known spelling, then with any of the
  words. The index is kept in memory and rebuilt when files change. It doesn't match by
  meaning; `wiki/README.md` (Search words) is how pages get the words people search for.
- Citations like `[S-0012]` or `[S-0040 §3.2 p.212]` link to the source card. Hover for its
  title and trust level.
- "Highlight uncited" marks facts in curated pages with no citation or label.
- Select text and press **Note** to leave a note. Enter saves, Shift+Enter adds a line, Esc
  cancels. The notes panel lists the page's notes and their status. Agents process them with
  the `wiki-notes` skill.

## Notes schema
`wiki/notes.jsonl` is an append-only event log, one JSON object per line.

- note: `{"type":"note","id":"N-YYYYMMDD-HHMMSS-xxxx","created":ISO8601 local,"file":"wiki/pages/..md","quote":{"exact":str,"prefix":str<=60,"suffix":str<=60},"line":int|null,"commit":str|null,"file_sha256":str,"text":str}`
- request (from Home): `{"type":"note","id":...,"created":...,"kind":"request","file":"","text":str}`
- answer to a note waiting on the PM: `{"type":"note","id":...,"parent":<note id>,"created":...,"text":str}`; it reopens the note
- status: `{"type":"status","id":<note id>,"status":"open|applied|rejected|needs-info","at":ISO8601,"by":str,"resolution":str}`

A note's current status is its last status event; with none, it is `open`. The viewer only
writes notes, requests and answers; agents write status events. `line`, `commit` and `file_sha256` describe the
file when the note was written. Pages change, so find the quote again by `exact` text plus
`prefix` and `suffix` rather than trusting `line`.
