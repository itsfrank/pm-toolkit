#!/usr/bin/env python3
"""Mechanical helpers for a pm-toolkit wiki: IDs, source cards, freshness, notes, lint.
Standard library only (Python 3.8+). Run from the workspace root or pass --root.

  python3 tools/wiki.py status [--json] [--today YYYY-MM-DD]
  python3 tools/wiki.py next-id
  python3 tools/wiki.py cards-from-raw [--dry-run] [FILE ...]
  python3 tools/wiki.py due [--today YYYY-MM-DD]
  python3 tools/wiki.py notes [--all] [--json]
  python3 tools/wiki.py note-status ID STATUS --resolution TEXT [--by NAME]
  python3 tools/wiki.py lint [--json] [--today YYYY-MM-DD]
  python3 tools/wiki.py reports-index

Dates default to today; set PM_TODAY=YYYY-MM-DD to pin them (the sample and evals do).

Read-only except: cards-from-raw writes new cards, note-status appends to notes.jsonl,
reports-index rewrites wiki/reports/INDEX.md.
"""
import argparse
import datetime
import difflib
import json
import os
import pathlib
import re
import sys

CITE = re.compile(r"\[(S-\d{4}[^\]]*)\]")
SID = re.compile(r"S-\d{4}")
LABELS = ("(inferred)", "(assumption)", "(unknown)")
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
URL = re.compile(r"https?://[^\s)>\]]+")
STATUSES = ("open", "applied", "rejected", "needs-info")
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
    return {"open_notes": len([n for n in notes if n["status"] == "open"]),
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
