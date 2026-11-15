#!/usr/bin/env python3
"""Mechanical helpers for a pm-toolkit wiki: IDs, source cards, freshness, notes, lint.
Standard library only (Python 3.8+). Run from the workspace root or pass --root.

  python3 tools/wiki.py status [--json] [--today YYYY-MM-DD]
  python3 tools/wiki.py next-id
  python3 tools/wiki.py cards-from-raw [--dry-run] [FILE ...]
  python3 tools/wiki.py due [--today YYYY-MM-DD]
  python3 tools/wiki.py raw-hits TERM [TERM ...] [--all]
  python3 tools/wiki.py catalog-search TERM [TERM ...] [--all] [--limit N]
  python3 tools/wiki.py catalog-mark ID_OR_URL S-NNNN
  python3 tools/wiki.py spend [--since ISO_TIME] [--marker TEXT] [--session FILE] [--json]
  python3 tools/wiki.py notes [--all] [--json]
  python3 tools/wiki.py note-status ID STATUS --resolution TEXT [--by NAME]
  python3 tools/wiki.py lint [--json] [--today YYYY-MM-DD]
  python3 tools/wiki.py reports-index

Dates default to today; set PM_TODAY=YYYY-MM-DD to pin them (the sample and evals do).

Read-only except: cards-from-raw writes new cards, note-status appends to notes.jsonl,
reports-index rewrites wiki/reports/INDEX.md, catalog-mark edits one catalog line.
spend reads Claude Code's own session logs under ~/.claude/projects/ (read-only).
"""
import argparse
import datetime
import difflib
import json
import os
import pathlib
import re
import sys

VERSION = "0.1.0"  # the toolkit release these tools came with; keep equal to plugin.json
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
            if event.get("type") == "note":
                notes[event["id"]] = dict(event, status="open", history=[])
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
    url = fields.get("source") or fields.get("url") or next(iter(URL.findall(head)), "")
    m = re.match(r"(\d{4}-\d{2}-\d{2})", raw.name)
    captured = m.group(1) if m else datetime.date.fromtimestamp(raw.stat().st_mtime).isoformat()
    page_id = re.search(r"pageId=(\d+)|/pages/(\d+)", url or "")
    origin_id = next((g for g in page_id.groups() if g), "") if page_id else ""
    recheck = "never" if raw.suffix.lower() == ".pdf" or not url else "30"
    return {"title": title, "origin": wiki.rel(raw).replace("wiki/", "", 1), "origin_url": url,
            "origin_id": origin_id, "captured": captured, "recheck_days": recheck}


def cmd_cards_from_raw(wiki, args):
    cards = wiki.cards()
    carded = {str(f.get("origin", "")) for _, f, _ in cards.values()}
    raws = [pathlib.Path(p).resolve() for p in args.files] if args.files else wiki.raw_files()
    nums = [int(k[2:]) for k in cards] or [0]
    n = max(nums)
    template = read(wiki.wiki / "sources" / "_TEMPLATE.md")
    for raw in raws:
        fields = guess_card(wiki, raw)
        if fields["origin"] in carded:
            continue
        n += 1
        sid = f"S-{n:04d}"
        text = template.replace("id: S-NNNN", f"id: {sid}")
        for key, value in fields.items():
            text = re.sub(rf"^{key}:.*$", f"{key}: {value}".rstrip(), text, count=1, flags=re.M)
        text = re.sub(r"^last_checked:.*$", f"last_checked: {fields['captured']}" if fields["origin_url"]
                      else "last_checked:", text, count=1, flags=re.M)
        print(f"{sid}  {fields['origin']}  {fields['origin_url'] or '(no origin url)'}")
        if not args.dry_run:
            (wiki.wiki / "sources" / f"{sid}.md").write_text(text, encoding="utf-8")
    if not args.dry_run:
        print("Fill in type, trust, summary, key facts and caveats on each new card.")


def due(wiki, today):
    out = []
    for sid, (path, f, _) in wiki.cards().items():
        days = str(f.get("recheck_days", "")).strip()
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
    rows.sort(key=lambda r: (-r[0], r[1].get("modified", "")), reverse=False)
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


def session_logs(root, session=None, marker=None):
    """Claude Code's log for the current session in this workspace, plus its subagents' logs."""
    if session:
        main = pathlib.Path(session)
    else:
        base = pathlib.Path(os.environ.get("CLAUDE_CONFIG_DIR", pathlib.Path.home() / ".claude"))
        folder = base / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(root))
        logs = sorted(folder.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
        if marker:  # several sessions can share a workspace; pick the one that saw the marker
            logs = [p for p in logs if marker in read(p)]
        if not logs:
            sys.exit(f"no Claude Code session log found in {folder}" + (" containing the marker" if marker else ""))
        main = logs[0]
    return [main] + sorted((main.parent / main.stem / "subagents").glob("*.jsonl"))


def spend(root, prices_path, since=None, session=None, marker=None):
    """Tokens per model since a time, counting each message once, priced from prices.json."""
    usage = {}  # message id -> (model, usage); log lines repeat per content block
    files = session_logs(root, session, marker)
    for path in files:
        for line in read(path).splitlines():
            try:
                e = json.loads(line)
            except ValueError:
                continue
            m = e.get("message")
            if not isinstance(m, dict) or not m.get("usage") or (since and e.get("timestamp", "") < since):
                continue
            usage[m.get("id") or e.get("uuid")] = (m.get("model", "unknown"), m["usage"])
    keys = ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
    price_keys = dict(zip(keys, ("input", "output", "cache_write", "cache_read")))
    prices = {}
    if prices_path.exists():
        prices = json.loads(read(prices_path)).get("models", {})
    models = {}
    for model, u in usage.values():
        row = models.setdefault(model, dict.fromkeys(keys, 0))
        for k in keys:
            row[k] += u.get(k) or 0
    total, priced = 0.0, True
    for model, row in models.items():
        rate = next((v for k, v in prices.items() if model.startswith(k)), None)
        if rate and all(isinstance(rate.get(price_keys[k]), (int, float)) for k in keys):
            row["usd"] = round(sum(row[k] * rate[price_keys[k]] for k in keys) / 1e6, 4)
            total += row["usd"]
        else:
            priced = False
    return {"session": str(files[0]), "subagent_logs": len(files) - 1, "since": since,
            "messages": len(usage), "models": models,
            "usd": round(total, 2) if priced and models else None,
            "note": None if priced else "no complete price for some models in tools/prices.json; budget in tokens"}


def cmd_spend(wiki, args):
    s = spend(wiki.root, wiki.root / "tools" / "prices.json", args.since, args.session, args.marker)
    if args.json:
        print(json.dumps(s, indent=2))
        return
    print(f"session log: {s['session']} (+{s['subagent_logs']} subagent logs), {s['messages']} messages"
          + (f" since {s['since']}" if s["since"] else ""))
    for model, row in s["models"].items():
        tokens = ", ".join(f"{k.replace('_input_tokens', '').replace('_tokens', '')} {v:,}"
                           for k, v in row.items() if k != "usd")
        print(f"  {model}: {tokens}" + (f"  = ${row['usd']:.2f}" if "usd" in row else ""))
    print(f"total: ${s['usd']:.2f}" if s["usd"] is not None else f"total: unpriced ({s['note']})")


TOKEN = re.compile(r"[a-z0-9][a-z0-9.\-]*[a-z0-9]")


def distinctive(token):
    """Words that carry a specific detail: codes and numbers (us-east-1, 72, v3) or long
    technical words. Short common words are ignored."""
    return any(c.isdigit() for c in token) or "-" in token or len(token) >= 8


def raw_hits(wiki, terms, show_all=False, per_file=8):
    """Lines in raw files that match a term and say something the file's card and the pages
    citing it never mention: the term itself, or a distinctive word (a region code, a number,
    a long technical word). These are the details summaries most often drop."""
    terms = [t.lower() for t in terms if len(t) >= 2]
    by_origin = {str(f.get("origin", "")): (sid, read(path).lower()) for sid, (path, f, _) in wiki.cards().items()}
    page_text = {p: read(p).lower() for p in wiki.pages()}
    out = []
    for raw in wiki.raw_files():
        if raw.suffix.lower() not in (".md", ".txt", ".csv", ".html", ".eml"):
            continue
        sid, card = by_origin.get(wiki.rel(raw).replace("wiki/", "", 1), (None, ""))
        summaries = card + "".join(t for t in page_text.values() if sid and sid.lower() in t)
        known = set(TOKEN.findall(summaries))
        hits = []
        for n, line in enumerate(read(raw).splitlines(), 1):
            low = line.lower()
            matched = [t for t in terms if t in low]
            if not matched:
                continue
            new = [t for t in matched if t not in summaries]
            new += sorted({w for w in TOKEN.findall(low) if distinctive(w) and w not in known} - set(new))
            if new or show_all:
                hits.append((n, new or matched, line.strip()))
        if hits:
            hits.sort(key=lambda h: -len(h[1]))
            out.append((wiki.rel(raw), sid, sorted(hits[:per_file]), len(hits)))
    return out


def cmd_raw_hits(wiki, args):
    rows = raw_hits(wiki, args.terms, args.all)
    for path, sid, hits, total in rows:
        print(f"{path}  [{sid or 'no card'}]")
        for n, why, line in hits:
            print(f"  {n}: (new: {', '.join(why[:6])}) {line[:160]}")
        if total > len(hits):
            print(f"  ... {total - len(hits)} more lines")
    print(f"{len(rows)} raw file(s) with details not in their card or pages"
          + (" (or matching, with --all)" if args.all else ""))


def anchor(wiki, note):
    """Find where a note's quote is now. Returns (line or None, how)."""
    path = wiki.root / note.get("file", "")
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
                         created=note.get("created"), commit=note.get("commit")))
    if args.json:
        print(json.dumps(rows, indent=2))
        return
    for r in rows:
        print(f"{r['id']}  [{r['status']}]  {r['file']}:{r['line_now'] or '?'} ({r['anchor']})\n"
              f"    quote: {r['quote'][:100]!r}\n    note:  {r['text'][:200]!r}")
    print(f"{len(rows)} note(s)")


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
            add("not in INDEX.md", wiki.rel(path))
        if inbound[path] == 0:
            add("orphan pages (no links from other pages)", wiki.rel(path))

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
        if wiki.rel(raw).replace("wiki/", "", 1) not in carded:
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


def cmd_lint(wiki, args):
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
            stages = [s for s in ("intake", "landscape", "coverage", "prd", "critical-review")
                      if (d / f"{s}.md").exists()]
            asks.append({"folder": f"work/{d.name}", "stages": stages})
    reports = []
    for path in sorted(wiki.reports(), reverse=True)[:3]:
        fields, body = frontmatter(read(path))
        title = fields.get("title") or next((l[2:].strip() for l in body.splitlines() if l.startswith("# ")), path.stem)
        reports.append({"path": wiki.rel(path), "title": title})
    catalog = catalog_entries(wiki) if (wiki.wiki / "catalog").is_dir() else []
    marker = wiki.root / ".pm-toolkit-version"
    installed = re.search(r"\d+\.\d+(\.\d+)?", read(marker)) if marker.exists() else None
    return {"tools_version": VERSION, "installed_version": installed.group(0) if installed else None,
            "upgrade_pending": bool(installed) and installed.group(0) != VERSION,
            "open_notes": len([n for n in notes if n["status"] == "open"]),
            "catalog_pages": len(catalog), "catalog_ingested": len([e for e in catalog if e["done"]]),
            "unfinished_runs": sorted(wiki.rel(h.parent) for h in work.glob("*/HANDOFF.md")) if work.is_dir() else [],
            "needs_info_notes": len([n for n in notes if n["status"] == "needs-info"]),
            "sources_due": len(due(wiki, today)),
            "last_lint": last_lint.isoformat() if last_lint else None,
            "lint_due": last_lint is None or (today - last_lint).days > 30,
            "recent_reports": reports, "recent_asks": asks}


def cmd_status(wiki, args):
    s = status(wiki, today_arg(args.today))
    if args.json:
        print(json.dumps(s, indent=2))
        return
    print(f"Open notes: {s['open_notes']} (waiting on you: {s['needs_info_notes']})")
    print(f"Sources due for a recheck: {s['sources_due']}")
    print(f"Last wiki check: {s['last_lint'] or 'never'}{' (due)' if s['lint_due'] else ''}")
    for a in s["recent_asks"]:
        print(f"Ask: {a['folder']} [{', '.join(a['stages']) or 'not started'}]")
    for r in s["recent_reports"]:
        print(f"Report: {r['title']} ({r['path']})")
    if s["catalog_pages"]:
        print(f"Catalogs: {s['catalog_ingested']} of {s['catalog_pages']} pages ingested")
    for folder in s["unfinished_runs"]:
        print(f"Unfinished run: {folder} (see HANDOFF.md)")
    if s["upgrade_pending"]:
        print(f"Upgrade: tools are {s['tools_version']}, .pm-toolkit-version says {s['installed_version']};"
              " offer to finish the upgrade (setup, Upgrade)")


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
    p = sub.add_parser("raw-hits", help="raw lines matching terms that cards and pages don't mention")
    p.add_argument("terms", nargs="+")
    p.add_argument("--all", action="store_true", help="also show lines whose terms are summarized")
    p.set_defaults(fn=cmd_raw_hits)
    p = sub.add_parser("catalog-search", help="find catalogued (not yet ingested) pages by terms and aliases")
    p.add_argument("terms", nargs="+")
    p.add_argument("--all", action="store_true", help="include pages already ingested")
    p.add_argument("--limit", type=int, default=15)
    p.set_defaults(fn=cmd_catalog_search)
    p = sub.add_parser("catalog-mark", help="tick a catalog line once its page is ingested")
    p.add_argument("page", help="page id, url or export file from the catalog line")
    p.add_argument("card", help="the new source card, S-NNNN")
    p.set_defaults(fn=cmd_catalog_mark)
    p = sub.add_parser("spend", help="tokens and cost of this Claude Code session (reads its own logs)")
    p.add_argument("--since", help="ISO time; count only messages after it (the run's start)")
    p.add_argument("--marker", help="pick the session whose log contains this text")
    p.add_argument("--session", help="path to a session .jsonl log")
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
    p = sub.add_parser("lint", help="mechanical wiki checks")
    p.add_argument("--json", action="store_true")
    p.add_argument("--today")
    p.add_argument("--limit", type=int, default=15)
    p.set_defaults(fn=cmd_lint)
    sub.add_parser("reports-index", help="rebuild wiki/reports/INDEX.md").set_defaults(fn=cmd_reports_index)
    args = ap.parse_args()
    args.fn(Wiki(args.root), args)


if __name__ == "__main__":
    main()
