# Wiki viewer

A local web page for reading the wiki and `work/` folders as rendered markdown, with
clickable citations and notes. Python 3 standard library and plain browser JavaScript; no
installs, no build step, no network access.

## Run
```
python3 tools/viewer/serve.py            # http://127.0.0.1:8765/
python3 tools/viewer/serve.py --open --port 8800
python3 tools/viewer/serve.py --open --detach   # keep running in the background
python3 tools/viewer/serve.py --stop            # stop this workspace's viewer
```
It listens on 127.0.0.1 only, serves only `.md` files inside the workspace, and writes only
one file: `wiki/notes.jsonl`. Stop it with Ctrl+C.

## Use
- The left panel lists files by folder, with a dot for page status (draft or reviewed).
  Filter by name, or search file contents (Enter).
- Citations like `[S-0012]` or `[S-0040 §3.2 p.212]` link to the source card. Hover for its
  title and trust level.
- "Highlight uncited" marks facts in curated pages with no citation or label.
- Select text and press **Note** to leave a note. Enter saves, Shift+Enter adds a line, Esc
  cancels. The notes panel lists the page's notes and their status. Agents process them with
  the `wiki-notes` skill.

## Notes schema
`wiki/notes.jsonl` is an append-only event log, one JSON object per line.

- note: `{"type":"note","id":"N-YYYYMMDD-HHMMSS-xxxx","created":ISO8601 local,"file":"wiki/pages/..md","quote":{"exact":str,"prefix":str<=60,"suffix":str<=60},"line":int|null,"commit":str|null,"file_sha256":str,"text":str}`
- status: `{"type":"status","id":<note id>,"status":"open|applied|rejected|needs-info","at":ISO8601,"by":str,"resolution":str}`

A note's current status is its last status event; with none, it is `open`. The viewer only
writes notes; agents write status events. `line`, `commit` and `file_sha256` describe the
file when the note was written. Pages change, so find the quote again by `exact` text plus
`prefix` and `suffix` rather than trusting `line`.
