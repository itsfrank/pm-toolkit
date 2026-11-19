#!/usr/bin/env python3
"""Mechanical helpers for a pm-toolkit wiki: IDs, source cards, freshness, notes, lint.
Standard library only (Python 3.8+). Run from the workspace root or pass --root.

  python3 tools/wiki.py status [--json] [--today YYYY-MM-DD]
  python3 tools/wiki.py next-id
  python3 tools/wiki.py cards-from-raw [--dry-run] [FILE ...]
  python3 tools/wiki.py due [--today YYYY-MM-DD]
  python3 tools/wiki.py pdf-text FILE.pdf [--pages-per-part N]
  python3 tools/wiki.py find TERM [TERM ...] [--limit N]
  python3 tools/wiki.py raw-hits TERM [TERM ...] [--all] [--files N]
  python3 tools/wiki.py catalog-search TERM [TERM ...] [--all] [--limit N]
  python3 tools/wiki.py catalog-mark ID_OR_URL S-NNNN
  python3 tools/wiki.py save-fetched PAGE_ID wiki/raw/YYYY-MM-DD-title.md [--url URL]
  python3 tools/wiki.py spend [--days N] [--ledger FILE] [--session-id ID [--since ISO_TIME]] [--json]
  python3 tools/wiki.py notes [--all] [--json]
  python3 tools/wiki.py note-status ID STATUS --resolution TEXT [--by NAME]
  python3 tools/wiki.py note-reply ID TEXT
  python3 tools/wiki.py lint [--json] [--today YYYY-MM-DD] [--fix-index]
  python3 tools/wiki.py reports-index
  python3 KIT/plugin/workspace/tools/wiki.py toolkit-branch KIT [--baseline] [--no-skills]

Dates default to today; set PM_TODAY=YYYY-MM-DD to pin them (the sample and evals do).

The viewer (tools/viewer/serve.py) reuses these functions for its Home page and saved documents.
Read-only except: cards-from-raw writes new cards, pdf-text writes a PDF's text parts,
note-status and note-reply append to notes.jsonl, reports-index rewrites wiki/reports/INDEX.md,
catalog-mark edits one catalog line, save-fetched writes one new raw file, lint --fix-index edits wiki/INDEX.md, toolkit-branch
commits to the git branch `pm-toolkit` (and, with --baseline, records a merge on the current branch).
spend --session-id and --days, and save-fetched, read Claude Code session logs under
~/.claude/projects/ (read-only).
"""
import argparse
import datetime
import difflib
import json
import os
import pathlib
import re
import secrets
import shutil
import subprocess
import sys
import tempfile

VERSION = "0.7.0"  # the toolkit release these tools came with; keep equal to plugin.json
CITE = re.compile(r"\[(S-\d{4}[^\]]*)\]")
SID = re.compile(r"S-\d{4}")
LABELS = ("(inferred)", "(assumption)", "(unknown)")
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
URL = re.compile(r"https?://[^\s)>\]]+")
STATUSES = ("open", "applied", "rejected", "needs-info")
# Catalog line: - [ ] [Title](url) · id: 123 · path: A > B · labels: x, y · modified: 2026-01-02 · file: exports/a.md · Summary
CATALOG_LINE = re.compile(r"^- \[( |x)\] \[(.+?)\]\((\S+?)\)(.*)$")
# Page sections whose bullets need no citation.
UNCITED_OK = ("related", "open questions")
BRANCH = "pm-toolkit"  # holds toolkit releases exactly as shipped; see setup, Upgrade


def today_arg(value):
    """--today, else the PM_TODAY environment variable (for samples and evals), else today."""
    value = value or os.environ.get("PM_TODAY")
    return datetime.date.fromisoformat(value) if value else datetime.date.today()


def read(path):
    return path.read_text(encoding="utf-8", errors="replace")


def frontmatter(text):
    """Parse the simple `key: value` frontmatter the templates use."""
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}, text
    fields = {}
    for line in m.group(1).splitlines():
        kv = re.match(r"^(\w[\w-]*):\s*(.*)$", line)
        if not kv:
            continue
        value = re.sub(r"\s{2,}#.*$", "", kv.group(2)).strip()
        if len(value) > 1 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if value.startswith("[") and value.endswith("]"):
            value = [v.strip() for v in value[1:-1].split(",") if v.strip()]
        fields[kv.group(1)] = value
    return fields, text[m.end():]


def parse_date(value):
    try:
        return datetime.date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


class Wiki:
    def __init__(self, root):
        self.root = pathlib.Path(root).resolve()
        self.wiki = self.root / "wiki"
        if not self.wiki.is_dir():
            sys.exit(f"no wiki/ folder under {self.root}; run from the workspace root or pass --root")

    def rel(self, path):
        return path.relative_to(self.root).as_posix()

    def cards(self):
        out = {}
        for path in sorted((self.wiki / "sources").glob("S-*.md")):
            fields, body = frontmatter(read(path))
            out[path.stem] = (path, fields, body)
        return out

    def pages(self):
        return sorted(p for p in (self.wiki / "pages").rglob("*.md") if p.name != "_TEMPLATE.md")

    def reports(self):
        return sorted(p for p in (self.wiki / "reports").glob("*.md") if p.name != "INDEX.md")

    def raw_files(self):
        return sorted(p for p in (self.wiki / "raw").rglob("*")
                      if p.is_file() and not p.name.startswith("."))

    def origin(self, raw):
        """A raw file's card origin: the PDF for its text parts (raw/<name>/ next to <name>.pdf)."""
        pdf = raw.parent.with_suffix(".pdf")
        return self.rel(pdf if pdf.is_file() else raw).replace("wiki/", "", 1)

    def notes(self):
        """Fold the append-only notes log into {id: note with current status}."""
        path = self.wiki / "notes.jsonl"
        notes = {}
        if not path.exists():
            return notes
        for n, line in enumerate(read(path).splitlines(), 1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except ValueError:
                print(f"notes.jsonl:{n}: not valid JSON, skipped", file=sys.stderr)
                continue
            if event.get("type") == "note" and event.get("parent") in notes:  # a reply reopens its note
                parent = notes[event["parent"]]
                parent["status"] = "open"
                parent["replies"].append(event.get("text", ""))
            elif event.get("type") == "note":
                notes[event["id"]] = dict(event, status="open", history=[], replies=[])
            elif event.get("type") == "status" and event.get("id") in notes:
                notes[event["id"]]["status"] = event.get("status", "open")
                notes[event["id"]]["history"].append(event)
        return notes


def next_id(wiki):
    nums = [int(k[2:]) for k in wiki.cards()]
    return f"S-{(max(nums) + 1) if nums else 1:04d}"


def cmd_next_id(wiki, args):
    print(next_id(wiki))


def guess_card(wiki, raw):
    """Draft card fields from a raw file's name and first lines."""
    text = read(raw) if raw.suffix.lower() in (".md", ".txt", ".html", ".csv") else ""
    head = text[:4000]
    fields, body = frontmatter(head)
    title = fields.get("title") or next(
        (l.lstrip("# ").strip() for l in body.splitlines() if l.startswith("# ")), None)
    if not title:
        title = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", raw.stem).replace("-", " ").capitalize()
    first = next((l for l in body.splitlines() if l.strip()), "")  # connector saves put the URL here
    url = fields.get("source") or fields.get("url") or next(iter(URL.findall(first)), "")
    m = re.match(r"(\d{4}-\d{2}-\d{2})", raw.name)
    captured = m.group(1) if m else datetime.date.fromtimestamp(raw.stat().st_mtime).isoformat()
    page_id = re.search(r"pageId=(\d+)|/pages/(\d+)", url or "")
    origin_id = next((g for g in page_id.groups() if g), "") if page_id else ""
    recheck = "never" if raw.suffix.lower() == ".pdf" or not url else "30"
    return {"title": title, "origin": wiki.rel(raw).replace("wiki/", "", 1), "origin_url": url,
            "origin_id": origin_id, "captured": captured, "recheck_days": recheck}


def cards_from_raw(wiki, files=None, dry_run=False):
    """Draft a card for each raw file that has none. Returns [(id, fields)]."""
    cards = wiki.cards()
    carded = {str(f.get("origin", "")) for _, f, _ in cards.values()}
    raws = [pathlib.Path(p).resolve() for p in files] if files else wiki.raw_files()
    nums = [int(k[2:]) for k in cards] or [0]
    n = max(nums)
    template = read(wiki.wiki / "sources" / "_TEMPLATE.md")
    made = []
    for raw in raws:
        fields = guess_card(wiki, raw)
        if fields["origin"] in carded or wiki.origin(raw) != fields["origin"]:
            continue
        n += 1
        sid = f"S-{n:04d}"
        text = template.replace("id: S-NNNN", f"id: {sid}")
        for key, value in fields.items():
            text = re.sub(rf"^{key}:.*$", f"{key}: {value}".rstrip(), text, count=1, flags=re.M)
        text = re.sub(r"^last_checked:.*$", f"last_checked: {fields['captured']}" if fields["origin_url"]
                      else "last_checked:", text, count=1, flags=re.M)
        made.append((sid, fields))
        if not dry_run:
            (wiki.wiki / "sources" / f"{sid}.md").write_text(text, encoding="utf-8")
    return made


def cmd_cards_from_raw(wiki, args):
    for sid, fields in cards_from_raw(wiki, args.files, args.dry_run):
        print(f"{sid}  {fields['origin']}  {fields['origin_url'] or '(no origin url)'}")
    if not args.dry_run:
        print("Fill in type, trust, summary, key facts and caveats on each new card.")


def due(wiki, today):
    """Cards whose origin should be compared again. Superseded cards are skipped."""
    out = []
    cards = wiki.cards()
    replaced = {str(f.get("supersedes", "")).strip() for _, f, _ in cards.values()}
    for sid, (path, f, _) in cards.items():
        days = str(f.get("recheck_days", "")).strip()
        if f.get("superseded_by") or sid in replaced:
            continue
        if not (f.get("origin_url") or f.get("origin_id")) or days in ("", "never"):
            continue
        last = parse_date(f.get("last_checked") or f.get("captured") or "")
        if not days.isdigit():
            out.append((sid, f, "recheck_days is not a number"))
        elif last is None:
            out.append((sid, f, "never checked"))
        elif last + datetime.timedelta(days=int(days)) < today:
            out.append((sid, f, f"last checked {last}, every {days} days"))
    return out


def cmd_due(wiki, args):
    rows = due(wiki, today_arg(args.today))
    for sid, f, why in rows:
        print(f"{sid}  {f.get('title', '')}  [{why}]  {f.get('origin_url') or f.get('origin_id')}")
    print(f"{len(rows)} source(s) due for a recheck")


def aliases(wiki, terms):
    """Expand terms with glossary synonyms (Term and 'Also called' columns)."""
    out = {t.lower() for t in terms}
    path = wiki.wiki / "glossary.md"
    if not path.exists():
        return sorted(out)
    for line in read(path).splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or cells[0] in ("Term", "") or set(cells[0]) <= set("-: "):
            continue
        names = {cells[0].lower()} | {a.strip().lower() for a in cells[2].split(",") if a.strip()}
        if names & out:
            out |= names
    return sorted(out)


def catalog_entries(wiki):
    """Every line of every wiki/catalog/*.md, parsed into fields."""
    out = []
    for path in sorted((wiki.wiki / "catalog").glob("*.md")):
        if path.name == "README.md":
            continue
        for n, line in enumerate(read(path).splitlines(), 1):
            m = CATALOG_LINE.match(line.strip())
            if not m:
                continue
            fields, summary = {}, []
            for part in (x.strip() for x in m.group(4).split(" · ") if x.strip()):
                kv = re.match(r"^(id|path|labels|modified|file|space|card):\s*(.*)$", part)
                if kv:
                    fields[kv.group(1)] = kv.group(2)
                else:
                    summary.append(part.lstrip("→ ").strip())
            card = re.search(r"S-\d{4}", fields.pop("card", ""))
            out.append(dict(fields, catalog=wiki.rel(path), line=n, done=m.group(1) == "x",
                            title=m.group(2), url=m.group(3), summary=" ".join(summary),
                            card=card.group(0) if card else None))
    return out


def catalog_search(wiki, terms, show_all=False):
    terms = aliases(wiki, terms)
    rows = []
    for e in catalog_entries(wiki):
        if e["done"] and not show_all:
            continue
        hay = {"title": e["title"].lower(), "path": e.get("path", "").lower(),
               "labels": e.get("labels", "").lower(), "summary": e["summary"].lower()}
        weight = {"title": 3, "labels": 2, "path": 1, "summary": 1}
        score = sum(w for t in terms for k, w in weight.items() if t in hay[k])
        if score:
            rows.append((score, e))
    rows.sort(key=lambda r: r[1].get("modified", ""), reverse=True)  # ties: newest first
    rows.sort(key=lambda r: -r[0])
    return terms, rows


def cmd_catalog_search(wiki, args):
    terms, rows = catalog_search(wiki, args.terms, args.all)
    print(f"terms: {', '.join(terms)}")
    for score, e in rows[:args.limit]:
        where = e.get("file") or e["url"]
        state = f"ingested as {e['card']}" if e["done"] else "not ingested"
        print(f"[{score}] {e['title']}  ({state}; modified {e.get('modified', '?')})\n"
              f"    {e.get('path', '')}\n    {where}" + (f"\n    {e['summary'][:160]}" if e["summary"] else ""))
    print(f"{len(rows)} catalog page(s) match" + ("" if args.all else " (not yet ingested; --all for every page)"))


def cmd_catalog_mark(wiki, args):
    """Tick the catalog line for a page and point it at its new card."""
    key = args.page.strip()
    hits = [e for e in catalog_entries(wiki) if key in (e.get("id"), e["url"], e.get("file"))]
    if not hits:
        sys.exit(f"no catalog line with id, url or file {key}")
    for e in hits:
        path = wiki.root / e["catalog"]
        lines = read(path).splitlines()
        line = lines[e["line"] - 1].replace("- [ ]", "- [x]", 1)
        if args.card not in line:
            line += f" · card: {args.card}"
        lines[e["line"] - 1] = line
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"{e['catalog']}:{e['line']}  {e['title']} -> {args.card}")


def session_folder(wiki):
    """Where Claude Code keeps this workspace's session logs."""
    base = pathlib.Path(os.environ.get("CLAUDE_CONFIG_DIR", pathlib.Path.home() / ".claude"))
    return base / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(wiki.root))


def fetched_page(wiki, page_id, logs=None):
    """The text of a connector page an agent in this workspace already fetched, read from the
    session logs (main sessions and subagents). The latest fetch of that page wins.
    A result too large for the log names the file it was saved to; that file is read instead.
    Returns (tool name, text, characters the notice reported or None) or None."""
    folder = pathlib.Path(logs) if logs else session_folder(wiki)
    files = sorted(list(folder.glob("*.jsonl")) + list(folder.glob("*/subagents/*.jsonl")),
                   key=lambda p: p.stat().st_mtime)
    found = None
    for log in files:
        uses = {}
        for line in read(log).splitlines():
            try:
                content = (json.loads(line).get("message") or {}).get("content")
            except (ValueError, AttributeError):
                continue
            for b in content if isinstance(content, list) else []:
                if b.get("type") == "tool_use" and str(b.get("name", "")).startswith("mcp__"):
                    uses[b.get("id")] = b
                elif b.get("type") == "tool_result" and b.get("tool_use_id") in uses and not b.get("is_error"):
                    use = uses[b["tool_use_id"]]
                    if str(page_id) not in [str(v) for v in (use.get("input") or {}).values()]:
                        continue
                    c = b.get("content")
                    text = c if isinstance(c, str) else "".join(
                        x.get("text", "") for x in (c or []) if isinstance(x, dict))
                    found = (use.get("name"),) + spilled_result(text)
    return found


def spilled_result(text):
    """Follow a notice that a large result was saved to a file, in either wording:
    `<persisted-output> ... Full output saved to: PATH` or
    `Error: result (N characters) exceeds maximum allowed tokens. Output has been saved to PATH`.
    Returns (text, characters reported or None); the notice itself when the file is gone."""
    head = text[:2000]
    if not (text.startswith("<persisted-output>") or "exceeds maximum" in head):
        return text, None
    size = re.search(r"\(([\d,]+) characters\)", head)
    size = int(size.group(1).replace(",", "")) if size else None
    path = re.search(r"saved to:? (\S+)", head)
    path = pathlib.Path(path.group(1).rstrip(".,;:)")) if path else None
    return (read(path) if path and path.is_file() else text), size


def cmd_save_fetched(wiki, args):
    """Save a fetched connector page to raw/ exactly as the connector returned it."""
    dest = (wiki.root / args.dest).resolve()
    if wiki.wiki / "raw" not in dest.parents:
        sys.exit("the destination must be under wiki/raw/")
    if dest.exists():
        sys.exit(f"{args.dest} exists; raw files are never edited")
    got = fetched_page(wiki, args.page_id, args.logs)
    if not got:
        sys.exit(f"no fetch of page {args.page_id} in this workspace's session logs; save the copy by hand")
    tool, text, size = got
    if text.lstrip().startswith(("Error:", "<persisted-output>")):
        sys.exit(f"the fetch of page {args.page_id} is an error or a notice that the result was too large, not the page: "
                 "fetch it again or save the copy by hand")
    if size and len(text) < size * 0.9:
        sys.exit(f"the fetch of page {args.page_id} reported {size} characters and only {len(text)} were found: "
                 "fetch it again or save the copy by hand")
    url, body = args.url or "", text
    try:
        data = json.loads(text)
    except ValueError:
        data = None
    if isinstance(data, dict):  # a JSON result: keep the page text, take the URL from its fields
        meta = data.get("page") if isinstance(data.get("page"), dict) else data
        body = next((data[k] for k in ("body", "content", "text", "markdown") if isinstance(data.get(k), str)), text)
        url = url or str(meta.get("url") or "")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text((f"{url}\n\n" if url else "") + body.strip("\n") + "\n", encoding="utf-8")
    print(f"saved {wiki.rel(dest)}: {len(body)} characters of page {args.page_id} from {tool}"
          + ("" if url else " (no URL found: pass --url)"))


def ledger_spend(path):
    """Sum a run's ledger: JSON lines, each the result of `claude -p --output-format json`
    (total_cost_usd, and per-model modelUsage including subagents). Exact, not estimated."""
    runs, usd, models = 0, 0.0, {}
    for n, line in enumerate(read(pathlib.Path(path)).splitlines(), 1):
        try:
            r = json.loads(line) if line.strip() else None
        except ValueError:
            r = None
            print(f"{path}:{n}: not a JSON result, skipped", file=sys.stderr)
        if not isinstance(r, dict) or "total_cost_usd" not in r:
            continue
        runs += 1
        usd += r.get("total_cost_usd") or 0
        for model, u in (r.get("modelUsage") or {}).items():
            row = models.setdefault(model, {})
            for k, v in u.items():
                if isinstance(v, (int, float)):
                    row[k] = row.get(k, 0) + v
    return {"source": "ledger", "file": str(path), "runs": runs, "usd": round(usd, 4), "models": models}


def session_logs(session_id=None, session=None):
    """Claude Code's log for one session, located by its id (or path), plus its subagents' logs.
    Never guesses the newest log: several sessions can share a workspace."""
    if session:
        main = pathlib.Path(session)
    else:
        base = pathlib.Path(os.environ.get("CLAUDE_CONFIG_DIR", pathlib.Path.home() / ".claude"))
        found = sorted((base / "projects").glob(f"*/{session_id}.jsonl"))
        if not found:
            sys.exit(f"no Claude Code session log {session_id}.jsonl under {base / 'projects'}")
        main = found[0]
    return [main] + sorted((main.parent / main.stem / "subagents").glob("*.jsonl"))


USAGE_KEYS = ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")


def log_usage(files, since=None):
    """Messages with token usage in session logs, each counted once: {id: (model, usage, record)}.
    Also returns the skills the session invoked."""
    usage, skills = {}, []
    for path in files:
        for line in read(path).splitlines():
            try:
                e = json.loads(line)
            except ValueError:
                continue
            m = e.get("message") if isinstance(e, dict) else None
            if not isinstance(m, dict) or not m.get("usage") or (since and e.get("timestamp", "") < since):
                continue
            usage[m.get("id") or e.get("uuid")] = (m.get("model", "unknown"), m["usage"], e)
            for block in m.get("content") if isinstance(m.get("content"), list) else []:
                if block.get("type") == "tool_use" and block.get("name") == "Skill":
                    name = str((block.get("input") or {}).get("skill", "")).split(":")[-1]
                    if name and name not in skills:
                        skills.append(name)
    return usage, skills


def price_models(usage, prices_path):
    """Tokens per model, priced from prices.json where it has the model.
    Returns (models, usd of the priced ones, names of the unpriced ones)."""
    price_keys = dict(zip(USAGE_KEYS, ("input", "output", "cache_write", "cache_read")))
    prices = json.loads(read(prices_path)).get("models", {}) if prices_path.exists() else {}
    models = {}
    for model, u, _ in usage.values():
        if model == "<synthetic>":
            continue
        row = models.setdefault(model, dict.fromkeys(USAGE_KEYS, 0))
        for k in USAGE_KEYS:
            row[k] += u.get(k) or 0
    total, unpriced = 0.0, []
    for model, row in models.items():
        rate = next((v for k, v in prices.items() if model.startswith(k)), None)
        if rate and all(isinstance(rate.get(price_keys[k]), (int, float)) for k in USAGE_KEYS):
            row["usd"] = round(sum(row[k] * rate[price_keys[k]] for k in USAGE_KEYS) / 1e6, 4)
            total += row["usd"]
        else:
            unpriced.append(model)
    return models, round(total, 2), unpriced


def log_spend(prices_path, session_id=None, session=None, since=None):
    """Estimate from session logs: tokens per model since a time, each message counted once.
    The log format is unofficial and undercounts, so this is for mid-run checks only.
    Priced from prices.json if it is filled in; otherwise budget in tokens."""
    files = session_logs(session_id, session)
    usage, _ = log_usage(files, since)
    models, usd, unpriced = price_models(usage, prices_path)
    usd = usd if models and not unpriced else None
    return {"source": "estimate", "file": str(files[0]), "subagent_logs": len(files) - 1, "since": since,
            "messages": len(usage), "models": models, "usd": usd}


def recent_spend(wiki, days, today, logs=None):
    """Every Claude Code session of this workspace in the last N days: tokens per model, and per
    session its size, largest context and the skills it ran. Shows where the money goes."""
    folder = pathlib.Path(logs) if logs else session_folder(wiki)
    since = (today - datetime.timedelta(days=days - 1)).isoformat()
    prices_path = wiki.root / "tools" / "prices.json"
    everything, sessions = {}, []
    for main in sorted(folder.glob("*.jsonl")):
        files = [main] + sorted((main.parent / main.stem / "subagents").glob("*.jsonl"))
        usage, skills = log_usage(files, since)
        if not usage:
            continue
        everything.update(usage)
        models, usd, _ = price_models(usage, prices_path)
        tokens = {k: sum(row[k] for row in models.values()) for k in USAGE_KEYS}
        sessions.append({
            "session": main.stem, "day": min(e.get("timestamp", "") for _, _, e in usage.values())[:10],
            "messages": len(usage), "skills": skills, "usd": usd, "tokens": tokens,
            "models": sorted({m.replace("claude-", "") for m in models}),
            "peak_context": max(sum(u.get(k) or 0 for k in USAGE_KEYS if k != "output_tokens")
                                for _, u, _ in usage.values())})
    models, usd, unpriced = price_models(everything, prices_path)
    sessions.sort(key=lambda s: (s["usd"], s["tokens"]["output_tokens"]), reverse=True)
    return {"source": "recent", "folder": str(folder), "days": days, "since": since, "messages": len(everything),
            "models": models, "usd": usd, "unpriced": unpriced, "sessions": sessions}


def cmd_spend(wiki, args):
    if not (args.ledger or args.session_id or args.session or args.days):
        sys.exit("spend needs --days N (this workspace's recent sessions), --ledger FILE (exact) "
                 "or --session-id ID (estimate); it never guesses a session")
    parts = []
    if args.days:
        parts.append(recent_spend(wiki, args.days, today_arg(args.today), args.logs))
    if args.ledger:
        parts.append(ledger_spend(args.ledger))
    if args.session_id or args.session:
        parts.append(log_spend(wiki.root / "tools" / "prices.json", args.session_id, args.session, args.since))
    if args.json:
        print(json.dumps(parts, indent=2))
        return
    for s in parts:
        if s["source"] == "ledger":
            print(f"ledger {s['file']}: {s['runs']} run(s), ${s['usd']:.2f}")
        elif s["source"] == "recent":
            print(f"last {s['days']} day(s) (since {s['since']}): {len(s['sessions'])} session(s), "
                  f"{s['messages']} messages, from {s['folder']}")
        else:
            print(f"estimate from session log {s['file']} (+{s['subagent_logs']} subagent logs), "
                  f"{s['messages']} messages" + (f" since {s['since']}" if s["since"] else ""))
        for model, row in s["models"].items():
            cost = row.get("costUSD", row.get("usd"))
            tokens = ", ".join(f"{k} {v:,}" for k, v in row.items() if k.lower().endswith("tokens"))
            print(f"  {model}: {tokens}" + (f"  = ${cost:.2f}" if cost is not None else ""))
        for row in s.get("sessions", [])[:args.top]:
            t = row["tokens"]
            print(f"  {row['day']} {row['session'][:8]}  ${row['usd']:.2f}  {row['messages']} msgs, "
                  f"output {t['output_tokens']:,}, largest context "
                  f"{row['peak_context']:,}  [{', '.join(row['models'])}]  {', '.join(row['skills']) or 'no skill'}")
    usd = [s["usd"] for s in parts]
    estimate = any(s["source"] != "ledger" for s in parts)
    unpriced = sorted({m for s in parts for m in s.get("unpriced", [])})
    if None in usd:
        print("total: unpriced estimate; budget in tokens (or fill in tools/prices.json)")
    elif unpriced:
        print(f"total: ${sum(usd):.2f} (estimate), not counting {', '.join(unpriced)}: no price in tools/prices.json")
    else:
        print(f"total: ${sum(usd):.2f}" + (" (estimate: session logs undercount)" if estimate else ""))


TOKEN = re.compile(r"[a-z0-9][a-z0-9.\-]*[a-z0-9]")
TEXT = (".md", ".txt", ".csv", ".html", ".eml")
PAGE = re.compile(r"^<!-- p\.(\d+) -->$")  # page marker in text parts of a PDF
# Long words that are common in any document and carry no specific detail.
STOP = set("""additional approximately available because business customers currently different
everything following generally important including information otherwise possible probably
question questions received processed something sometimes therefore together whatever
whenever estimated unchanged downstream""".split())


def distinctive(token):
    """Words that carry a specific detail: codes and numbers (us-east-1, 72, v3) or long
    technical words. Short and common words are ignored."""
    return any(c.isdigit() for c in token) or "-" in token or (len(token) >= 8 and token not in STOP)


def term_pattern(term):
    """Substring match, but whole words for short terms (so 'eu' doesn't match 'neutral')."""
    t = re.escape(term)
    return re.compile(rf"(?<![a-z0-9]){t}(?![a-z0-9])" if len(term) < 4 else t)


def raw_hits(wiki, terms, show_all=False, per_file=8):
    """Lines in raw files that match a term (or its glossary synonyms) and say something the
    file's card and the pages citing it never mention: the term itself, or a distinctive word
    (a region code, a number, a long technical word). Files are ranked by how many of the
    terms they match. Returns (rows, skipped non-text files)."""
    groups = {t: [(a, term_pattern(a)) for a in aliases(wiki, [t])] for t in {t.lower() for t in terms if len(t) >= 2}}
    by_origin = {str(f.get("origin", "")): (sid, read(path).lower()) for sid, (path, f, _) in wiki.cards().items()}
    page_text = {p: read(p).lower() for p in wiki.pages()}
    out, skipped = [], 0
    for raw in wiki.raw_files():
        if raw.suffix.lower() not in TEXT:
            skipped += 1
            continue
        sid, card = by_origin.get(wiki.origin(raw), (None, ""))
        summaries = card + "".join(t for t in page_text.values() if sid and sid.lower() in t)
        known = set(TOKEN.findall(summaries))
        hits, found, page = [], set(), None
        for n, line in enumerate(read(raw).splitlines(), 1):
            low = line.lower()
            marker = PAGE.match(low.strip())
            page = int(marker.group(1)) if marker else page
            matched = {g: [a for a, rx in alts if rx.search(low)] for g, alts in groups.items()}
            matched = {g: a for g, a in matched.items() if a}
            if not matched:
                continue
            names = sorted({a for a in sum(matched.values(), [])})
            new = [a for a in names if not term_pattern(a).search(summaries)]
            new += sorted({w for w in TOKEN.findall(low) if distinctive(w) and w not in known} - set(new))
            if new or show_all:
                hits.append((n, page, new or names, line.strip()))
                found |= set(matched)
        if hits:
            hits.sort(key=lambda h: -len(h[2]))
            out.append((wiki.rel(raw), sid, sorted(hits[:per_file]), len(hits), len(found)))
    out.sort(key=lambda r: (-r[4], r[0]))
    return out, skipped


def term_groups(wiki, terms):
    """Each term with its glossary synonyms, as (name, pattern) alternatives."""
    return {t: [(a, term_pattern(a)) for a in aliases(wiki, [t])] for t in {t.lower() for t in terms if len(t) >= 2}}


def find(wiki, terms):
    """One search over pages, reports, cards and raw files for terms and their synonyms.
    Per file: how many of the terms it matches, how many lines, and its best lines.
    Returns {section: [(path, label, terms matched, lines matched, [(line no, text)])]}."""
    groups = term_groups(wiki, terms)
    cards = wiki.cards()
    by_origin = {str(f.get("origin", "")): sid for sid, (_, f, _) in cards.items()}

    def scan(path, skip=None):
        lines, matched = [], set()
        for n, line in enumerate(read(path).splitlines(), 1):
            low = line.lower()
            got = {g for g, alts in groups.items() if any(rx.search(low) for _, rx in alts)}
            matched |= got
            if got and not PAGE.match(low.strip()) and not (skip and skip.match(low)):
                lines.append((len(got), n, line.strip()))
        best = sorted(sorted(lines, key=lambda l: -l[0])[:3], key=lambda l: l[1])
        return len(matched), len(lines), [(n, text) for _, n, text in best]

    def title(path):
        return frontmatter(read(path))[0].get("title", "")

    out = {"pages": [], "reports": [], "cards": [], "raw": []}
    for section, paths in (("pages", wiki.pages()), ("reports", wiki.reports())):
        for path in paths:
            matched, count, best = scan(path)
            if matched:
                out[section].append((wiki.rel(path), title(path), matched, count, best))
    for sid, (path, f, _) in cards.items():
        matched, count, best = scan(path, re.compile(r"(id|title|origin\w*):"))
        if matched:
            label = ", ".join(str(x) for x in (f.get("title"), f.get("trust"), f.get("published") or f.get("captured")) if x)
            label += f"; superseded by {f['superseded_by']}" if f.get("superseded_by") else ""
            out["cards"].append((sid, label, matched, count, best))
    for raw in wiki.raw_files():
        if raw.suffix.lower() in TEXT:
            matched, count, best = scan(raw)
            if matched:
                out["raw"].append((wiki.rel(raw), by_origin.get(wiki.origin(raw), "no card"), matched, count, best))
    for rows in out.values():
        rows.sort(key=lambda r: (-r[2], -r[3], r[0]))
    return sorted(a for alts in groups.values() for a, _ in alts), out


def cmd_find(wiki, args):
    terms, out = find(wiki, args.terms)
    print(f"terms: {', '.join(sorted(set(terms)))}")
    for section, rows in out.items():
        print(f"\n## {section}: {len(rows)} match")
        for name, label, matched, count, best in rows[:args.limit]:
            print(f"{name}  [{label}]  ({matched} of the terms, {count} lines)" if label
                  else f"{name}  ({matched} of the terms, {count} lines)")
            for n, text in best if section != "raw" else best[:1]:
                print(f"  {n}: {text[:args.width]}")
        if len(rows) > args.limit:
            print(f"+{len(rows) - args.limit} more: " + ", ".join(r[0] for r in rows[args.limit:args.limit + 40]))
    unread = catalog_search(wiki, args.terms)[1] if (wiki.wiki / "catalog").is_dir() else []
    print(f"\n## catalog: {len(unread)} unread page(s) match" + (" (catalog-search lists them)" if unread else ""))
    print("Next: read the files that matter; `raw-hits` with the same terms shows raw details no card or page has.")


def cmd_raw_hits(wiki, args):
    rows, skipped = raw_hits(wiki, args.terms, args.all)
    for path, sid, hits, total, matched in rows[:args.files]:
        print(f"{path}  [{sid or 'no card'}]  ({matched} of the terms)")
        for n, page, why, line in hits:
            print(f"  {n}{f' p.{page}' if page else ''}: (new: {', '.join(why[:6])}) {line[:160]}")
        if total > len(hits):
            print(f"  ... {total - len(hits)} more lines")
    if len(rows) > args.files:
        print(f"+{len(rows) - args.files} more files: " + ", ".join(r[0] for r in rows[args.files:]))
    print(f"{len(rows)} raw file(s) with details not in their card or pages"
          + (" (or matching, with --all)" if args.all else ""))
    if skipped:
        print(f"{skipped} non-text raw file(s) not searched (PDFs: search their text parts)")


def anchor(wiki, note):
    """Find where a note's quote is now. Returns (line or None, how)."""
    if not note.get("file"):
        return None, "request"  # from the viewer's Home page: no page, no quote
    path = wiki.root / note["file"]
    if not path.is_file():
        return None, "file missing"
    lines = read(path).splitlines()
    quote = note.get("quote") or {}
    exact = " ".join(str(quote.get("exact", "")).split())
    if not exact:
        return note.get("line"), "no quote"
    flat = [" ".join(l.split()) for l in lines]
    hits = [i + 1 for i, l in enumerate(flat) if exact in l]
    if not hits:  # quotes can span lines; try a window of three
        hits = [i + 1 for i in range(len(flat)) if exact in " ".join(flat[i:i + 3])]
    if hits:
        best = min(hits, key=lambda h: abs(h - (note.get("line") or h)))
        return best, "exact" if best == note.get("line") else "moved"
    ratios = [(difflib.SequenceMatcher(None, exact, l).ratio(), i + 1) for i, l in enumerate(flat) if l]
    score, line = max(ratios, default=(0, None))
    return (line, f"fuzzy {score:.2f}") if score >= 0.6 else (None, "lost")


def cmd_notes(wiki, args):
    rows = []
    for note in wiki.notes().values():
        if note["status"] != "open" and not args.all:
            continue
        line, how = anchor(wiki, note)
        rows.append(dict(id=note["id"], status=note["status"], file=note.get("file"),
                         line_then=note.get("line"), line_now=line, anchor=how,
                         quote=(note.get("quote") or {}).get("exact", ""), text=note.get("text", ""),
                         created=note.get("created"), commit=note.get("commit"), replies=note["replies"]))
    if args.json:
        print(json.dumps(rows, indent=2))
        return
    for r in rows:
        where = f"{r['file']}:{r['line_now'] or '?'} ({r['anchor']})" if r["file"] else "request (no page)"
        print(f"{r['id']}  [{r['status']}]  {where}\n"
              f"    quote: {r['quote'][:100]!r}\n    note:  {r['text'][:200]!r}"
              + "".join(f"\n    reply: {t[:200]!r}" for t in r["replies"]))
    print(f"{len(rows)} note(s)")


# PDFKit through JavaScript for Automation: ships with macOS, nothing to install.
PDF_JS = r"""
ObjC.import("PDFKit");
function run(argv) {
  var d = $.PDFDocument.alloc.initWithURL($.NSURL.fileURLWithPath(argv[0]));
  if (d.isNil()) return JSON.stringify({error: "cannot open " + argv[0]});
  var pages = [], outline = [];
  for (var i = 0; i < d.pageCount; i++) {
    var s = d.pageAtIndex(i).string;
    pages.push(s.isNil() ? "" : s.js);
  }
  function walk(o, level) {
    for (var i = 0; i < o.numberOfChildren; i++) {
      var c = o.childAtIndex(i), dest = c.destination;
      outline.push([level, c.label.isNil() ? "" : c.label.js.trim(), dest.isNil() ? null : Number(d.indexForPage(dest.page)) + 1]);
      walk(c, level + 1);
    }
  }
  if (!d.outlineRoot.isNil()) walk(d.outlineRoot, 0);
  return JSON.stringify({pages: pages, outline: outline});
}
"""


def pdf_extract(path):
    """{"pages": [text, ...], "outline": [[level, title, page], ...]} via macOS PDFKit."""
    import subprocess
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as js:
        js.write(PDF_JS)
    try:
        out = subprocess.run(["osascript", "-l", "JavaScript", js.name, str(path.resolve())],
                             capture_output=True, text=True, stdin=subprocess.DEVNULL)
    except FileNotFoundError:
        sys.exit("pdf-text needs macOS (osascript). Elsewhere, read the PDF and save its parts by hand.")
    finally:
        os.unlink(js.name)
    data = json.loads(out.stdout or '{"error": "%s"}' % out.stderr.strip().replace('"', "'"))
    if "error" in data:
        sys.exit(f"pdf-text: {data['error']}")
    return data


def pdf_parts(npages, outline, size):
    """Page ranges of at most `size` pages, cut at chapter starts where possible."""
    starts = sorted({p for level, _, p in outline if level == 0 and p and p > 1})
    parts, first = [], 1
    while first <= npages:
        last = min(first + size - 1, npages)
        cut = [p - 1 for p in starts if first + size // 3 <= p - 1 < last]
        last = cut[-1] if cut and last < npages else last
        parts.append((first, last))
        first = last + 1
    return parts


def cmd_pdf_text(wiki, args):
    pdf = pathlib.Path(args.file).resolve()
    data = pdf_extract(pdf)
    pages, outline = data["pages"], data["outline"]
    out = pdf.with_suffix("")
    if out.exists() and any(out.iterdir()):
        sys.exit(f"{wiki.rel(out)}/ already has files; raw files are never overwritten")
    out.mkdir(parents=True, exist_ok=True)
    ranges = pdf_parts(len(pages), outline, args.pages_per_part)
    part_of = {}
    for n, (first, last) in enumerate(ranges, 1):
        lines = [f"# {pdf.name}, part {n} of {len(ranges)}: pages {first}-{last}", ""]
        for p in range(first, last + 1):
            part_of[p] = n
            body = pages[p - 1].rstrip().splitlines()
            if body and body[-1].strip() == str(p):  # the printed page number
                body.pop()
            lines += [f"<!-- p.{p} -->", *body, ""]
        (out / f"part-{n:02d}.md").write_text("\n".join(lines), encoding="utf-8")
    contents = [f"# {pdf.name}: contents", "",
                f"From the PDF's bookmarks. {len(pages)} pages in {len(ranges)} parts.", ""]
    contents += [f"{'  ' * level}- {title} p.{page} (part-{part_of.get(page, 0):02d})"
                 for level, title, page in outline if page]
    (out / "contents.md").write_text("\n".join(contents) + "\n", encoding="utf-8")
    print(f"{len(pages)} pages -> {len(ranges)} parts and contents.md in {wiki.rel(out)}/")
    if not outline:
        print("No bookmarks: write the card's ## Contents from the headings in the parts.")
    empty = [str(i + 1) for i, t in enumerate(pages) if not t.strip()]
    if len(empty) > len(pages) // 10:
        print(f"{len(empty)} pages have no text (scanned images?): read those pages from the PDF.")


def note_reply(wiki, note_id, text):
    """Record the PM's answer to a note; the note is open again for wiki-notes."""
    now = datetime.datetime.now()
    event = {"type": "note", "id": "N-" + now.strftime("%Y%m%d-%H%M%S-") + secrets.token_hex(2),
             "parent": note_id, "created": now.isoformat(timespec="seconds"), "text": text}
    with open(wiki.wiki / "notes.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event


def cmd_note_reply(wiki, args):
    if args.id not in wiki.notes():
        sys.exit(f"unknown note id {args.id}")
    note_reply(wiki, args.id, args.text)
    print(f"{args.id} -> open (reply recorded)")


def cmd_note_status(wiki, args):
    if args.id not in wiki.notes():
        sys.exit(f"unknown note id {args.id}")
    event = {"type": "status", "id": args.id, "status": args.status,
             "at": datetime.datetime.now().isoformat(timespec="seconds"),
             "by": args.by, "resolution": args.resolution}
    with open(wiki.wiki / "notes.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    print(f"{args.id} -> {args.status}")


def uncited_lines(text):
    """Fact-like bullets and paragraphs in a page body with neither a citation nor a label.
    Wrapped lines belong to the bullet or paragraph they continue."""
    _, body = frontmatter(text)
    section, units, fence = "", [], False
    offset = text.count("\n", 0, len(text) - len(body))
    for n, line in enumerate(body.splitlines(), offset + 1):
        s = line.strip()
        if s.startswith("```"):
            fence = not fence
        if fence or not s or s.startswith(("#", "|---", "<!--")):
            if s.startswith("## "):
                section = s[3:].strip().lower()
            if units:
                units[-1][2] = True  # close the current unit
            continue
        starts = re.match(r"([-*+]|\d+\.)\s", s) or s.startswith("|")
        if units and not starts and not units[-1][2]:
            units[-1][1] += " " + s
        else:
            units.append([n, s, False, section])
    out = []
    for n, s, _, sec in units:
        if sec in UNCITED_OK or re.fullmatch(r"[-*]\s*none( recorded)?\.?", s, re.I):
            continue
        if re.fullmatch(r"[-*]?\s*\[[^\]]+\]\([^)]+\)(:.*)?", s) and not re.search(r"\d", s):
            continue  # a bare link line
        if CITE.search(s) or any(label in s for label in LABELS):
            continue
        out.append((n, s))
    return out


def lint(wiki, today):
    cards = wiki.cards()
    pages = wiki.pages()
    report = {}

    def add(check, item):
        report.setdefault(check, []).append(item)

    cited = set()
    inbound = {p: 0 for p in pages}
    for path in pages + wiki.reports() + [wiki.wiki / "INDEX.md"]:
        if not path.exists():
            continue
        text = read(path)
        for group in CITE.findall(text):
            for sid in SID.findall(group):
                cited.add(sid)
                if sid not in cards:
                    add("dangling citations", f"{wiki.rel(path)}: {sid}")
        scan = re.sub(r"`[^`\n]*`", "", re.sub(r"```.*?```", "", text, flags=re.S))
        for target in LINK.findall(scan):
            if re.match(r"^[a-z]+:", target) or target.startswith("#"):
                continue
            dest = (path.parent / target.split("#")[0]).resolve()
            if not dest.exists():
                add("broken links", f"{wiki.rel(path)}: {target}")
            elif dest in inbound and dest != path and path.name != "INDEX.md":
                inbound[dest] += 1
        if path in inbound:
            fields, _ = frontmatter(text)
            for n, s in uncited_lines(text):
                add("uncited lines", f"{wiki.rel(path)}:{n}: {s[:90]}")
            for key in ("type", "status", "updated"):
                if not fields.get(key):
                    add("frontmatter", f"{wiki.rel(path)}: missing {key}")
            updated = parse_date(fields.get("updated", ""))
            if updated and (today - updated).days > 90:
                add("stale pages", f"{wiki.rel(path)}: updated {updated}")
            if "## Conflicts" in text and not re.search(r"## Conflicts\s*\n+\s*-\s*None", text):
                add("open conflicts", wiki.rel(path))

    index = read(wiki.wiki / "INDEX.md") if (wiki.wiki / "INDEX.md").exists() else ""
    for path in pages:
        if wiki.rel(path).replace("wiki/", "", 1) not in index:
            add("not in INDEX.md (lint --fix-index adds them)", wiki.rel(path))
    for path in pages:
        if inbound[path] == 0:
            add("orphan pages (no links from other pages)", wiki.rel(path))
    for target in re.findall(r"\]\((pages/[^)\s]+)\)", index):
        if not (wiki.wiki / target).exists():
            add("INDEX.md lines pointing nowhere (lint --fix-index drops them)", target)

    for sid, (path, f, body) in cards.items():
        origin = str(f.get("origin", ""))
        if origin.startswith("raw/") and not (wiki.wiki / origin).exists():
            add("cards whose raw file is missing", f"{sid}: {origin}")
        filed = body.split("## Filed into", 1)[-1] if "## Filed into" in body else ""
        if not re.search(r"pages/\S+", filed) and sid not in cited:
            add("unused sources", f"{sid}: {f.get('title', '')}")
        for key in ("title", "trust", "captured"):
            value = f.get(key, "")
            if not value or "|" in str(value):
                add("card fields to fill", f"{sid}: {key}")
    carded = {str(f.get("origin", "")) for _, f, _ in cards.values()}
    for raw in wiki.raw_files():
        if wiki.origin(raw) not in carded:
            add("raw files without a card", wiki.rel(raw))

    for path in wiki.reports():
        head = read(path)[:1500].lower()
        for field in ("question", "as of", "sources"):
            if field not in head:
                add("report headers", f"{wiki.rel(path)}: missing '{field}'")
        fields, _ = frontmatter(read(path))
        when = parse_date(fields.get("as_of") or fields.get("date") or path.name[:10])
        if when and (today - when).days > 60:
            add("old reports (snapshots; re-run if still used)", f"{wiki.rel(path)}: {when}")
        if str(fields.get("promoted", "")).lower() == "no" and when and (today - when).days > 30:
            add("reports not promoted after 30 days (file durable facts with wiki-ingest)",
                f"{wiki.rel(path)}: {when}")

    work = [p for p in (wiki.root / "work").rglob("*.md")] if (wiki.root / "work").is_dir() else []
    work_text = [read(p) for p in work]
    drafts = []
    for path in pages:
        if frontmatter(read(path))[0].get("status") == "draft":
            key = wiki.rel(path).replace("wiki/", "", 1)
            drafts.append((sum(key in t for t in work_text), key))
    for n, key in sorted(drafts, key=lambda d: (-d[0], d[1])):
        add("draft pages to review (most used in work/ first)", f"{key}: {n} work file(s)")

    for lens in unfired_lenses(wiki, work_text):
        add("lenses that never fired (retirement candidates; keep if still relevant)", lens)

    origins = {str(f.get("origin_id", "")) for _, f, _ in cards.values() if f.get("origin_id")}
    for e in catalog_entries(wiki) if (wiki.wiki / "catalog").is_dir() else []:
        if not e["done"] and e.get("id") and e["id"] in origins:
            add("catalog lines already carded but not ticked", f"{e['catalog']}:{e['line']}: {e['title']}")
        if e["done"] and e["card"] and e["card"] not in cards:
            add("catalog lines pointing at a missing card", f"{e['catalog']}:{e['line']}: {e['card']}")
    for sid, f, why in due(wiki, today):
        add("sources due for recheck", f"{sid}: {why}")
    for note in wiki.notes().values():
        if note["status"] in ("open", "needs-info"):
            add("open notes", f"{note['id']}: {note.get('file')} [{note['status']}]")
    return report


LENS_TAG = re.compile(r"(?:\*\*lens:\*\*|\blens:)\s*`?(\d+)", re.I)


def unfired_lenses(wiki, work_text, min_reviews=5):
    """Lenses no review-log entry tags and no coverage table marks missing, partial or
    unverified. Empty until there are min_reviews log entries and coverage tables."""
    path = wiki.wiki / "lenses.md"
    lenses = re.findall(r"^## (\d+)\.\s*(.+)$", read(path), re.M) if path.exists() else []
    log = read(wiki.wiki / "review-log.md") if (wiki.wiki / "review-log.md").exists() else ""
    fired = set(LENS_TAG.findall(log))
    reviews = len(re.findall(r"^## \d{4}-\d{2}-\d{2}", log, re.M))
    for text in work_text:
        fired |= set(LENS_TAG.findall(text))
        rows = re.findall(r"^\|\s*(\d+)\s*\|[^|\n]*\|\s*([^|\n]*?)\s*\|", text, re.M)
        reviews += bool(rows)
        fired |= {n for n, state in rows if state.lower().strip("*") in ("missing", "partial", "unverified")}
    return [f"{n}. {name}" for n, name in lenses if n not in fired] if reviews >= min_reviews else []


def fix_index(wiki):
    """Drop INDEX.md lines whose page is gone and add a line for each unlisted page under
    its section. Curated lines and text are kept as they are."""
    path = wiki.wiki / "INDEX.md"
    lines = read(path).splitlines() if path.exists() else ["# Wiki index"]
    dead = [l for l in lines if re.match(r"^- \[.*\]\((pages/[^)\s]+)\)", l)
            and not (wiki.wiki / re.match(r"^- \[.*\]\((pages/[^)\s]+)\)", l).group(1)).exists()]
    lines = [l for l in lines if l not in dead]
    added = []
    for page in wiki.pages():
        key = wiki.rel(page).replace("wiki/", "", 1)
        if any(f"]({key})" in l for l in lines):
            continue
        fields, body = frontmatter(read(page))
        title = next((l[2:].strip() for l in body.splitlines() if l.startswith("# ")), page.stem)
        summary = next((l.strip() for l in body.splitlines() if l.strip() and l[0] not in "#-|<"), "")
        line = (f"- [{title}]({key}) ({fields.get('status', 'draft')}, {fields.get('updated', '?')}): "
                f"{summary[:100] or '(describe)'}")
        section = "## " + page.parent.name.capitalize()
        if section not in lines:
            lines += ["", section]
        at = lines.index(section) + 1
        while at < len(lines) and lines[at].startswith("- "):
            at += 1
        lines.insert(at, line)
        added.append(key)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return added, dead


def cmd_lint(wiki, args):
    if args.fix_index:
        added, dead = fix_index(wiki)
        print(f"INDEX.md: added {len(added)} line(s), dropped {len(dead)} dead line(s)")
        for key in added:
            print(f"+ {key}")
        for line in dead:
            print(f"- {line}")
        return
    report = lint(wiki, today_arg(args.today))
    if args.json:
        print(json.dumps(report, indent=2))
        return
    for check, items in report.items():
        print(f"## {check}: {len(items)}")
        for item in items[:args.limit]:
            print(f"- {item}")
        if len(items) > args.limit:
            print(f"- ... {len(items) - args.limit} more (use --json for all)")
    if not report:
        print("lint: no mechanical issues found")


# Work folder types by name prefix (work/YYYY-MM-DD-<prefix>...); anything else is an ask.
WORK_TYPES = {"rfp-": "rfp", "mktg-": "marketing", "call-": "call", "expand-": "expand",
              "gaps-": "gaps", "compete-": "competitive", "landscape-": "landscape"}


def status(wiki, today):
    """What needs the PM's attention: open notes, due sources, lint age, recent work."""
    notes = [n for n in wiki.notes().values() if n["status"] in ("open", "needs-info")]
    work = wiki.root / "work"
    lints = sorted(p.name[:10] for p in work.glob("*wiki-lint*")) if work.is_dir() else []
    last_lint = parse_date(lints[-1]) if lints else None
    asks = []
    if work.is_dir():
        for d in sorted((d for d in work.iterdir() if d.is_dir() and re.match(r"\d{4}-\d{2}-\d{2}-", d.name)
                         and "wiki-lint" not in d.name), reverse=True)[:5]:
            kind = next((k for prefix, k in WORK_TYPES.items() if d.name[11:].startswith(prefix)), "ask")
            if kind == "ask":
                stages = [s for s in ("intake", "landscape", "coverage", "prd") if (d / f"{s}.md").exists()]
                reviews = sorted(int(m.group(1)) for p in d.glob("review-*.md")
                                 for m in [re.fullmatch(r"review-(\d+)\.md", p.name)] if m)
                stages += [f"critical-review ({len(reviews)})"] if reviews else []
            else:
                stages = sorted(p.stem for p in d.glob("*.md") if p.name != "README.md")
            asks.append({"folder": f"work/{d.name}", "type": kind, "stages": stages})
    reports = []
    for path in sorted(wiki.reports(), reverse=True)[:3]:
        fields, body = frontmatter(read(path))
        title = fields.get("title") or next((l[2:].strip() for l in body.splitlines() if l.startswith("# ")), path.stem)
        reports.append({"path": wiki.rel(path), "title": title})
    catalog = catalog_entries(wiki) if (wiki.wiki / "catalog").is_dir() else []
    marker = wiki.root / ".pm-toolkit-version"
    installed = re.search(r"\d+\.\d+(\.\d+)?", read(marker)) if marker.exists() else None
    cards = wiki.cards()
    empty = not wiki.pages() and not cards
    # Draft cards (trust still to choose): documents saved but not yet read into the wiki.
    to_ingest = [{"id": sid, "title": f.get("title", ""), "origin": f.get("origin", "")}
                 for sid, (_, f, _) in cards.items() if not f.get("trust") or "|" in str(f["trust"])]
    waiting = [{"id": n["id"], "file": n.get("file"), "note": n.get("text", ""),
                "needs": (n["history"][-1].get("resolution") if n["history"] else "")}
               for n in notes if n["status"] == "needs-info"]
    return {"tools_version": VERSION, "installed_version": installed.group(0) if installed else None,
            "upgrade_pending": bool(installed) and installed.group(0) != VERSION,
            "open_notes": len([n for n in notes if n["status"] == "open"]),
            "catalog_pages": len(catalog), "catalog_ingested": len([e for e in catalog if e["done"]]),
            "unfinished_runs": sorted(wiki.rel(h.parent) for h in work.glob("*/HANDOFF.md")) if work.is_dir() else [],
            "needs_info_notes": len(waiting), "needs_info": waiting,
            "sources_due": len(due(wiki, today)), "to_ingest": to_ingest,
            "last_lint": last_lint.isoformat() if last_lint else None,
            "lint_due": not empty and (last_lint is None or (today - last_lint).days > 30),
            "recent_reports": reports, "recent_asks": asks}


def cmd_status(wiki, args):
    s = status(wiki, today_arg(args.today))
    if args.json:
        print(json.dumps(s, indent=2))
        return
    print(f"Open notes: {s['open_notes']} (waiting on you: {s['needs_info_notes']})")
    for n in s["needs_info"]:
        print(f"  {n['id']} ({n['file']}): {n['note'][:100]!r} needs: {n['needs'][:120]}")
    if s["needs_info"]:
        print('  Record the PM\'s answer with: python3 tools/wiki.py note-reply <id> "<answer>"')
    if s["to_ingest"]:
        print(f"Saved documents waiting for wiki-ingest: {len(s['to_ingest'])} "
              f"({', '.join(c['id'] for c in s['to_ingest'][:8])})")
    print(f"Sources due for a recheck: {s['sources_due']}")
    print(f"Last wiki check: {s['last_lint'] or 'never'}{' (due)' if s['lint_due'] else ''}")
    for a in s["recent_asks"]:
        label = "Ask" if a["type"] == "ask" else f"Work ({a['type']})"
        print(f"{label}: {a['folder']} [{', '.join(a['stages']) or 'not started'}]")
    for r in s["recent_reports"]:
        print(f"Report: {r['title']} ({r['path']})")
    if s["catalog_pages"]:
        print(f"Catalogs: {s['catalog_ingested']} of {s['catalog_pages']} pages ingested")
    for folder in s["unfinished_runs"]:
        print(f"Unfinished run: {folder} (see HANDOFF.md)")
    if s["upgrade_pending"]:
        print(f"Upgrade: tools are {s['tools_version']}, .pm-toolkit-version says {s['installed_version']};"
              " offer to finish the upgrade (setup, Upgrade)")


def git(root, *cmd, check=True):
    out = subprocess.run(["git", "-C", str(root), *cmd], capture_output=True, text=True)
    if check and out.returncode:
        sys.exit(f"git {' '.join(cmd)} failed: {out.stderr.strip()}")
    return out


def cmd_toolkit_branch(wiki, args):
    """Commit a toolkit release, exactly as shipped, to the `pm-toolkit` branch.
    The PM's working tree is never touched: the branch is built in a temporary worktree."""
    root, kit = wiki.root, pathlib.Path(args.kit).resolve()
    manifest = kit / "plugin" / ".claude-plugin" / "plugin.json"
    if not manifest.exists():
        sys.exit(f"{kit} is not a pm-toolkit release (no plugin/.claude-plugin/plugin.json)")
    version = json.loads(read(manifest))["version"]
    if pathlib.Path(git(root, "rev-parse", "--show-toplevel").stdout.strip()).resolve() != root:
        sys.exit(f"{root} is not the root of a git repository")
    if git(root, "status", "--porcelain", "--untracked-files=no").stdout.strip():
        sys.exit("uncommitted changes: commit them on the working branch first")
    exists = not git(root, "rev-parse", "--verify", "-q", "refs/heads/" + BRANCH, check=False).returncode
    if args.baseline == exists:
        sys.exit(f"branch {BRANCH} already exists; drop --baseline" if exists
                 else f"no {BRANCH} branch yet; create it with --baseline (setup, Upgrade)")
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="pm-toolkit-")) / "tree"
    git(root, "worktree", "add", "--detach", str(tmp))
    try:
        git(tmp, "switch", "--orphan" if args.baseline else "-q", BRANCH)
        git(tmp, "rm", "-r", "-q", "--ignore-unmatch", ".")
        junk = shutil.ignore_patterns("__pycache__", ".DS_Store")
        shutil.copytree(kit / "plugin" / "workspace", tmp, dirs_exist_ok=True, ignore=junk)
        if not args.no_skills:
            shutil.copytree(kit / "plugin" / "skills", tmp / ".claude" / "skills", dirs_exist_ok=True, ignore=junk)
        git(tmp, "add", "-A")
        if git(tmp, "diff", "--cached", "--quiet", check=False).returncode == 0 and not args.baseline:
            print(f"{BRANCH} already holds this release ({version})")
            return
        git(tmp, "commit", "-q", "-m", f"pm-toolkit {version}")
    finally:
        git(root, "worktree", "remove", "--force", str(tmp), check=False)
    if args.baseline:
        git(root, "merge", "-q", "--allow-unrelated-histories", "-s", "ours", "-m",
            f"pm-toolkit {version}: baseline (this tree already holds the release)", BRANCH)
        print(f"Created {BRANCH} with release {version} and recorded it as the baseline of the current branch.")
    else:
        print(f"Committed release {version} to {BRANCH}. Now run: git merge {BRANCH}")


def cmd_reports_index(wiki, args):
    lines = ["# Reports index", "",
             "Generated by `python3 tools/wiki.py reports-index`. Do not edit by hand.", ""]
    for path in sorted(wiki.reports(), reverse=True):
        text = read(path)
        fields, body = frontmatter(text)
        title = fields.get("title") or next(
            (l[2:].strip() for l in body.splitlines() if l.startswith("# ")), path.stem)
        question = fields.get("question") or next(
            (re.sub(r"^\W*question\W*", "", l, flags=re.I).strip() for l in body.splitlines()
             if re.match(r"^\W*question\b", l, re.I)), "")
        when = fields.get("as_of") or fields.get("date") or path.name[:10]
        lines.append(f"- [{title}]({path.name}) ({when}): {question}".rstrip(": "))
    (wiki.wiki / "reports" / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"reports/INDEX.md: {len(lines) - 4} report(s)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".", help="workspace root (default: current directory)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("status", help="what needs attention: notes, due sources, lint, recent work")
    p.add_argument("--json", action="store_true")
    p.add_argument("--today")
    p.set_defaults(fn=cmd_status)
    sub.add_parser("next-id", help="print the next free source ID").set_defaults(fn=cmd_next_id)
    p = sub.add_parser("cards-from-raw", help="create draft cards for raw files that have none")
    p.add_argument("files", nargs="*")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(fn=cmd_cards_from_raw)
    p = sub.add_parser("due", help="list sources due for a freshness recheck")
    p.add_argument("--today")
    p.set_defaults(fn=cmd_due)
    p = sub.add_parser("pdf-text", help="save a PDF's text as page-marked parts plus contents.md (macOS)")
    p.add_argument("file")
    p.add_argument("--pages-per-part", type=int, default=40)
    p.set_defaults(fn=cmd_pdf_text)
    p = sub.add_parser("raw-hits", help="raw lines matching terms that cards and pages don't mention")
    p.add_argument("terms", nargs="+")
    p.add_argument("--all", action="store_true", help="also show lines whose terms are summarized")
    p.add_argument("--files", type=int, default=10, help="files to show; the rest are named")
    p.set_defaults(fn=cmd_raw_hits)
    p = sub.add_parser("find", help="search pages, reports, cards and raw files at once, best matches first")
    p.add_argument("terms", nargs="+")
    p.add_argument("--limit", type=int, default=12, help="files to show per section; the rest are named")
    p.add_argument("--width", type=int, default=200, help="characters shown per matching line")
    p.set_defaults(fn=cmd_find)
    p = sub.add_parser("catalog-search", help="find catalogued (not yet ingested) pages by terms and aliases")
    p.add_argument("terms", nargs="+")
    p.add_argument("--all", action="store_true", help="include pages already ingested")
    p.add_argument("--limit", type=int, default=15)
    p.set_defaults(fn=cmd_catalog_search)
    p = sub.add_parser("catalog-mark", help="tick a catalog line once its page is ingested")
    p.add_argument("page", help="page id, url or export file from the catalog line")
    p.add_argument("card", help="the new source card, S-NNNN")
    p.set_defaults(fn=cmd_catalog_mark)
    p = sub.add_parser("save-fetched", help="save a connector page you fetched to raw/ verbatim, from the session log")
    p.add_argument("page_id")
    p.add_argument("dest", help="wiki/raw/YYYY-MM-DD-short-title.md")
    p.add_argument("--url", help="origin URL for the first line, when the fetch result has none")
    p.add_argument("--logs", help="the folder of session logs, if not the default")
    p.set_defaults(fn=cmd_save_fetched)
    p = sub.add_parser("spend", help="cost: recent sessions of this workspace, a run's ledger, or one session log")
    p.add_argument("--ledger", help="JSON lines of `claude -p --output-format json` results")
    p.add_argument("--session-id", help="estimate from this Claude Code session's log")
    p.add_argument("--session", help="estimate from this session .jsonl log (path)")
    p.add_argument("--since", help="ISO time; for log estimates, count only messages after it")
    p.add_argument("--days", type=int, help="this workspace's sessions in the last N days, largest first")
    p.add_argument("--top", type=int, default=10, help="sessions to list with --days")
    p.add_argument("--logs", help="with --days: the folder of session logs, if not the default")
    p.add_argument("--today")
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_spend)
    p = sub.add_parser("notes", help="list notes and where their quotes are now")
    p.add_argument("--all", action="store_true", help="include closed notes")
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_notes)
    p = sub.add_parser("note-status", help="append a status event for a note")
    p.add_argument("id")
    p.add_argument("status", choices=STATUSES)
    p.add_argument("--resolution", required=True)
    p.add_argument("--by", default="agent")
    p.set_defaults(fn=cmd_note_status)
    p = sub.add_parser("note-reply", help="record the PM's answer to a note; reopens it")
    p.add_argument("id")
    p.add_argument("text")
    p.set_defaults(fn=cmd_note_reply)
    p = sub.add_parser("lint", help="mechanical wiki checks")
    p.add_argument("--json", action="store_true")
    p.add_argument("--today")
    p.add_argument("--limit", type=int, default=15)
    p.add_argument("--fix-index", action="store_true", help="add missing INDEX.md lines, drop dead ones")
    p.set_defaults(fn=cmd_lint)
    sub.add_parser("reports-index", help="rebuild wiki/reports/INDEX.md").set_defaults(fn=cmd_reports_index)
    p = sub.add_parser("toolkit-branch", help="commit a toolkit release as shipped to the pm-toolkit branch")
    p.add_argument("kit", help="the unzipped toolkit release (folder holding plugin/)")
    p.add_argument("--baseline", action="store_true",
                   help="create the branch and record it as already merged into the current branch")
    p.add_argument("--no-skills", action="store_true", help="plugin mode: workspace files only")
    p.set_defaults(fn=cmd_toolkit_branch)
    args = ap.parse_args()
    args.fn(Wiki(args.root), args)


if __name__ == "__main__":
    main()
