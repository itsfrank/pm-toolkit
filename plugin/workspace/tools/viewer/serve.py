#!/usr/bin/env python3
"""Local web viewer for the PM wiki: renders markdown, links citations, searches, shows what
needs attention, and records the PM's notes, requests and saved documents. Standard library
only; binds 127.0.0.1. It writes notes to wiki/notes.jsonl, and documents the PM adds as new
files in wiki/raw/ with a draft card in wiki/sources/. It never changes an existing file.

Usage: python3 tools/viewer/serve.py [--port 8765] [--open] [--detach] [--stop] [--root PATH]
       python3 tools/viewer/serve.py --install-app [--app-name "PM Wiki"]   (macOS launcher)
"""
import argparse
import datetime
import hashlib
import http.server
import json
import os
import pathlib
import plistlib
import re
import secrets
import shlex
import sqlite3
import subprocess
import sys
import threading
import urllib.parse
import urllib.request
import webbrowser

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE)]
import search as searchtools  # noqa: E402  (tools/viewer/search.py)
import wiki as wikitools  # noqa: E402  (tools/wiki.py, shared status logic)
import design as designtools  # noqa: E402  (tools/design.py, inlines a page's stylesheets)
STATIC = HERE / "static"
TYPES = {".html": "text/html", ".js": "text/javascript", ".css": "text/css"}
MAX_BODY = 64 * 1024
MAX_UPLOAD = 50 * 1024 * 1024
FRONT = re.compile(r"\A---\n(.*?)\n---\n", re.S)
LOCK = threading.Lock()
ROOT = None
SERVER = None
INDEX = searchtools.Index()
APP_ID = "local.pm-toolkit.wiki"
KINDS = (("wiki/pages/", "pages"), ("wiki/reports/", "reports"), ("wiki/sources/", "sources"),
         ("wiki/raw/", "originals"), ("work/", "work"), ("design/", "design"))


# Originals in wiki/raw/ are untrusted: anything that a browser could run is sent as text,
# and every raw response is sandboxed by CSP.
RAW_TYPES = {".pdf": "application/pdf", ".png": "image/png", ".jpg": "image/jpeg",
             ".jpeg": "image/jpeg", ".gif": "image/gif", ".md": "text/plain", ".txt": "text/plain",
             ".csv": "text/plain", ".json": "text/plain", ".html": "text/plain",
             ".htm": "text/plain", ".eml": "text/plain", ".xml": "text/plain"}
RAW_CSP = "default-src 'none'; img-src 'self'; style-src 'unsafe-inline'; sandbox"
# Mockups the agent wrote under design/ render as pages, sandboxed away from the viewer and
# the network. Saved references (design/refs/) are originals: treated like wiki/raw/.
DESIGN_PAGES = ("mockups", "products", "systems")
DESIGN_CSP = ("default-src 'none'; img-src data:; style-src 'unsafe-inline'; font-src data:; "
              "script-src 'unsafe-inline'; sandbox allow-scripts")


def raw_file(path, base=("wiki", "raw")):
    """Resolve a path to a file under wiki/raw/ (or base); None if it escapes that folder."""
    try:
        p = (ROOT / path).resolve()
        p.relative_to(ROOT.joinpath(*base).resolve())
    except (OSError, ValueError):
        return None
    return p if p.is_file() else None


def inside(path):
    """Resolve a workspace-relative path; None if it escapes ROOT or isn't a .md file."""
    try:
        p = (ROOT / path).resolve()
    except (OSError, ValueError):
        return None
    if p.suffix != ".md" or not p.is_file():
        return None
    try:
        p.relative_to(ROOT)
    except ValueError:
        return None
    return p


def md_files():
    for top in ("wiki", "work", "design"):
        base = ROOT / top
        if not base.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
            for name in sorted(filenames):
                if name.endswith(".md") and not name.startswith((".", "_")):
                    p = pathlib.Path(dirpath) / name
                    if inside(p.relative_to(ROOT)):
                        yield p


def title_of(p, text):
    m = FRONT.match(text)
    front = re.search(r"^title:\s*(.+)$", m.group(1), re.M) if m else None
    h = re.search(r"^# (.+)$", text, re.M)
    return (front.group(1).split("  #")[0].strip() if front else "") or (h.group(1).strip() if h else p.stem)


def find(query):
    """Ranked full-text search over the viewer's markdown and the text originals in wiki/raw/."""
    wiki = wikitools.Wiki(ROOT)
    files = {p.relative_to(ROOT).as_posix(): p for p in md_files()}
    files.update({wiki.rel(p): p for p in wiki.raw_files() if p.suffix.lower() in wikitools.TEXT})
    synonyms = lambda term: wikitools.aliases(wiki, [term])
    found = None
    with LOCK:
        try:
            INDEX.refresh(sorted(files.items()), title_of)
            found = INDEX.search(query, synonyms)
        except sqlite3.OperationalError:  # no FTS5 in this Python, or a query it can't parse
            pass
    if found is None:  # plain substring search, same answer shape
        term, hits = query.lower(), []
        for key, p in sorted(files.items()):
            text = p.read_text(encoding="utf-8", errors="replace")
            lines = [{"line": n, "text": line.strip()[:320], "best": True}
                     for n, line in enumerate(text.splitlines(), 1) if term in line.lower()]
            if term and lines and len(hits) < 100:
                hits.append({"path": key, "title": title_of(p, text), "matches": len(lines), "lines": lines[:3]})
        found = {"hits": hits, "corrected": None, "any": False}
    for hit in found["hits"]:  # what the result is, for the filter chips and badges
        m = meta(files[hit["path"]]) if hit["path"].endswith(".md") else {}
        hit.update(kind=next((k for prefix, k in KINDS if hit["path"].startswith(prefix)), "other"),
                   type=m.get("type", ""), status=m.get("status", ""))
    return found


def home():
    """What the Home page shows: the same checks `wiki.py status`, `due` and `lint` print."""
    wiki, today = wikitools.Wiki(ROOT), wikitools.today_arg(None)
    report = wikitools.lint(wiki, today)
    notes = [n for n in wiki.notes().values() if n["status"] == "open"]
    uncited = {}
    for item in report.get("uncited lines", []):
        path, line = item.split(":")[:2]
        uncited.setdefault(path, []).append(int(line))
    return {"status": wikitools.status(wiki, today),
            "queued": [{"id": n["id"], "file": n.get("file") or "", "text": n.get("text", ""),
                        "replies": n["replies"]} for n in notes],
            "due": [{"id": sid, "title": f.get("title", ""), "why": why, "url": f.get("origin_url", "")}
                    for sid, f, why in wikitools.due(wiki, today)],
            "conflicts": report.get("open conflicts", []),
            "uncited": [{"path": k, "count": len(v), "line": v[0]} for k, v in uncited.items()]}


def save_raw(name, data):
    """Save one new file into wiki/raw/ (never over an existing one) and draft its card."""
    stem, dot, ext = name.rpartition(".")
    stem, ext = (stem, ext) if dot and stem else (name, "")
    ext = re.sub(r"[^a-z0-9]", "", ext.lower())[:8]
    slug = re.sub(r"[\W_]+", "-", stem.lower()).strip("-")[:60] or "untitled"
    if not re.match(r"\d{4}-\d{2}-\d{2}-", slug):
        slug = f"{wikitools.today_arg(None).isoformat()}-{slug}"
    folder = ROOT / "wiki" / "raw"
    folder.mkdir(parents=True, exist_ok=True)
    wiki = wikitools.Wiki(ROOT)
    with LOCK:
        for n in range(1, 100):
            path = folder / (slug + (f"-{n}" if n > 1 else "") + (f".{ext}" if ext else ""))
            try:
                with open(path, "xb") as fh:
                    fh.write(data)
                break
            except FileExistsError:
                continue
        else:
            return None
        made = wikitools.cards_from_raw(wiki, [path]) if (wiki.wiki / "sources" / "_TEMPLATE.md").exists() else []
    return {"path": wiki.rel(path), "card": made[0][0] if made else None}


def meta(p):
    text = p.read_text(encoding="utf-8", errors="replace")
    fields = {}
    m = FRONT.match(text)
    if m:
        for line in m.group(1).splitlines():
            k, sep, v = line.partition(":")
            if sep and not line.startswith((" ", "\t")):
                fields[k.strip()] = v.split("#")[0].strip()
    h = re.search(r"^# (.+)$", text, re.M)
    title = fields.get("title") or (h.group(1).strip() if h else p.stem)
    return {"path": p.relative_to(ROOT).as_posix(), "title": title,
            **{k: fields.get(k, "") for k in ("type", "status", "updated", "trust")}}


def commit():
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                             text=True, timeout=5)
        return out.stdout.strip() or None if out.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def notes_for(path):
    log = ROOT / "wiki" / "notes.jsonl"
    notes, status = {}, {}
    if log.exists():
        for line in log.read_text(encoding="utf-8").splitlines():
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            if ev.get("type") == "note" and ev.get("file") == path:
                notes[ev["id"]] = ev
            elif ev.get("type") == "status":
                status[ev.get("id")] = ev
    for nid, n in notes.items():
        s = status.get(nid, {})
        n["status"] = s.get("status", "open")
        n["resolution"] = s.get("resolution", "")
    return list(notes.values())


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


class Handler(http.server.BaseHTTPRequestHandler):
    def send(self, code, body, ctype="application/json", csp=None, download=None):
        data = json.dumps(body).encode() if ctype == "application/json" else body
        self.send_response(code)
        text = ctype.startswith("text/") or ctype == "application/json"
        self.send_header("Content-Type", ctype + ("; charset=utf-8" if text else ""))
        if download:
            self.send_header("Content-Disposition", f'attachment; filename="{download}"')
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", csp or
                         "default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        pass

    def local(self):
        """Refuse requests that didn't come from this viewer's own page: another site reaching
        127.0.0.1 through a hostname of its own, or posting here from the PM's browser."""
        host = self.headers.get("Host", "").rsplit(":", 1)[0]
        ok = host in ("127.0.0.1", "localhost") and (self.command == "GET" or self.headers.get("X-PM-Viewer") == "1")
        if not ok:
            self.send(403, {"error": "not from the viewer"})
        return ok

    def do_GET(self):
        if not self.local():
            return
        url = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(url.query)
        arg = lambda k: (q.get(k) or [""])[0]
        if url.path == "/api/tree":
            return self.send(200, [meta(p) for p in md_files()])
        if url.path == "/api/file":
            p = inside(arg("path"))
            if not p:
                return self.send(404, {"error": "not found"})
            raw = p.read_bytes()
            return self.send(200, {"path": p.relative_to(ROOT).as_posix(),
                                   "text": raw.decode("utf-8", "replace"),
                                   "sha256": hashlib.sha256(raw).hexdigest(), "commit": commit()})
        if url.path == "/api/search":
            return self.send(200, find(arg("q").strip()[:200]))
        if url.path == "/api/home":
            try:
                return self.send(200, home())
            except (SystemExit, Exception) as e:  # a broken wiki file must not break the viewer
                return self.send(200, {"error": str(e)})
        if url.path == "/api/notes":
            return self.send(200, notes_for(arg("path")))
        if url.path == "/api/raw":
            p = raw_file(arg("path"))
            if not p:
                return self.send(404, {"error": "not found"})
            ctype = RAW_TYPES.get(p.suffix.lower(), "application/octet-stream")
            name = re.sub(r'[^\w.-]', "_", p.name)
            # Browsers won't show a PDF under a sandbox CSP; PDFs can't script the page anyway.
            csp = "default-src 'none'" if ctype == "application/pdf" else RAW_CSP
            return self.send(200, p.read_bytes(), ctype, csp=csp,
                             download=None if p.suffix.lower() in RAW_TYPES else name)
        if url.path == "/api/design":
            p = raw_file(arg("path"), ("design",))
            if not p:
                return self.send(404, {"error": "not found"})
            page = p.suffix.lower() in (".html", ".htm") and \
                p.relative_to((ROOT / "design").resolve()).parts[0] in DESIGN_PAGES
            if page:
                return self.send(200, designtools.bundled(p).encode("utf-8"), "text/html", csp=DESIGN_CSP)
            return self.send(200, p.read_bytes(), RAW_TYPES.get(p.suffix.lower(), "text/plain"), csp=RAW_CSP)
        if url.path == "/api/whoami":
            return self.send(200, {"app": "pm-wiki-viewer", "root": str(ROOT), "pid": os.getpid()})
        if url.path == "/api/status":
            try:
                return self.send(200, wikitools.status(wikitools.Wiki(ROOT), wikitools.today_arg(None)))
            except (SystemExit, Exception) as e:  # status is a convenience; never break the viewer
                return self.send(200, {"error": str(e)})
        name = "index.html" if url.path in ("/", "/index.html") else url.path.lstrip("/")
        f = STATIC / name
        if "/" not in name and f.suffix in TYPES and f.is_file():
            return self.send(200, f.read_bytes(), TYPES[f.suffix])
        self.send(404, {"error": "not found"})

    def do_POST(self):
        if not self.local():
            return
        route = urllib.parse.urlparse(self.path).path
        size = int(self.headers.get("Content-Length") or 0)
        upload = route == "/api/capture" and self.headers.get("X-Filename")
        if size < 0 or size > (MAX_UPLOAD if upload else MAX_BODY) or (size == 0 and route != "/api/stop"):
            return self.send(413, {"error": "too large or empty"})
        data = self.rfile.read(size)
        if route == "/api/stop":
            self.send(200, {"stopped": True})
            return threading.Thread(target=SERVER.shutdown, daemon=True).start()
        if upload:
            saved = save_raw(urllib.parse.unquote(upload).replace("\\", "/").rsplit("/", 1)[-1], data)
            return self.send(201 if saved else 409, saved or {"error": "could not find a free file name"})
        try:
            body = json.loads(data)
            text = str(body.get("text", "")).strip()
            quote = body.get("quote") or {}
            line = body.get("line")
        except (ValueError, AttributeError):
            return self.send(400, {"error": "invalid JSON"})
        if not text:
            return self.send(400, {"error": "nothing to save"})
        if route == "/api/capture":  # pasted text, saved verbatim
            saved = save_raw((str(body.get("title", "")).strip() or "pasted text") + ".md",
                             (text + "\n").encode("utf-8"))
            return self.send(201 if saved else 409, saved or {"error": "could not find a free file name"})
        if route == "/api/reply":  # the PM's answer to a note that is waiting on them
            wiki = wikitools.Wiki(ROOT)
            with LOCK:
                if str(body.get("id")) not in wiki.notes():
                    return self.send(404, {"error": "unknown note"})
                return self.send(201, wikitools.note_reply(wiki, str(body["id"]), text))
        if route != "/api/notes":
            return self.send(404, {"error": "not found"})
        note = {"type": "note",
                "id": "N-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S-") + secrets.token_hex(2),
                "created": now()}
        if body.get("kind") == "request":  # from the Home page: a request with no page or quote
            note.update(kind="request", file="", text=text)
        else:
            p = inside(str(body.get("file", "")))
            if not p or not str(quote.get("exact", "")).strip():
                return self.send(400, {"error": "need an existing .md file, a quote and text"})
            note.update(file=p.relative_to(ROOT).as_posix(),
                        quote={"exact": str(quote.get("exact", "")),
                               "prefix": str(quote.get("prefix", ""))[-60:],
                               "suffix": str(quote.get("suffix", ""))[:60]},
                        line=line if isinstance(line, int) else None, commit=commit(),
                        file_sha256=hashlib.sha256(p.read_bytes()).hexdigest(), text=text)
        log = ROOT / "wiki" / "notes.jsonl"
        with LOCK:
            log.parent.mkdir(parents=True, exist_ok=True)
            with log.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(note, ensure_ascii=False) + "\n")
        self.send(201, note)


LAUNCHER = """#!/bin/sh
# Opens the PM wiki viewer for one workspace. Written by tools/viewer/serve.py --install-app.
ROOT={root}
for py in /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do
  if [ -x "$py" ]; then
    "$py" "$ROOT/tools/viewer/serve.py" --root "$ROOT" --open --detach && exit 0
    break
  fi
done
osascript -e 'on run a' -e 'display alert "The wiki could not open" message "Check that this folder still exists, then ask Claude to set up the wiki launcher again: " & item 1 of a' -e 'end run' "$ROOT"
"""


def install_app(name, folder):
    """Write a double-clickable macOS app (a folder with a shell script) that opens this
    workspace's viewer. Spotlight and Launchpad find it in ~/Applications."""
    if sys.platform != "darwin":
        print("The launcher app is for macOS. Elsewhere, start the viewer with: python3 tools/viewer/serve.py --open")
        return 1
    name = re.sub(r"[/:]", " ", name).strip() or "PM Wiki"
    app = pathlib.Path(folder).expanduser() / f"{name}.app"
    info = app / "Contents" / "Info.plist"
    if app.exists():
        try:
            ours = plistlib.loads(info.read_bytes()).get("CFBundleIdentifier") == APP_ID
        except (OSError, ValueError):
            ours = False
        if not ours:
            print(f"{app} exists and is not a wiki launcher; pick another name with --app-name")
            return 1
    script = app / "Contents" / "MacOS" / "wiki"
    script.parent.mkdir(parents=True, exist_ok=True)
    info.write_bytes(plistlib.dumps({
        "CFBundleName": name, "CFBundleDisplayName": name, "CFBundleIdentifier": APP_ID,
        "CFBundleExecutable": "wiki", "CFBundlePackageType": "APPL",
        "CFBundleShortVersionString": wikitools.VERSION, "LSUIElement": True}))
    script.write_text(LAUNCHER.format(root=shlex.quote(str(ROOT))), encoding="utf-8")
    script.chmod(0o755)
    print(f"Installed {app}: opens the wiki for {ROOT}. Find it with Spotlight or Launchpad as \"{name}\". "
          "To remove it, move it to the Trash. If the workspace folder moves, run this again.")
    return 0


def running_here(url):
    """The pid of a viewer for this same workspace answering at url, else None."""
    try:
        with urllib.request.urlopen(url + "api/whoami", timeout=1) as r:
            info = json.loads(r.read().decode("utf-8"))
    except (OSError, ValueError):
        return None
    if info.get("app") == "pm-wiki-viewer" and info.get("root") == str(ROOT):
        return info.get("pid")
    return None


def detach(args):
    """Relaunch as a separate background process that outlives this shell or session,
    then report its URL. The child prints one line and stops writing to the pipe."""
    cmd = [sys.executable, str(pathlib.Path(__file__).resolve()), "--child",
           "--port", str(args.port), "--root", str(ROOT)]
    flags = {"start_new_session": True} if os.name == "posix" else \
        {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS}
    child = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True, **flags)
    line = child.stdout.readline().strip() or "The viewer did not start."
    child.stdout.close()
    print(line)
    m = re.search(r"http://\S+/", line)
    if args.open and m:
        webbrowser.open(m.group(0))
    return 0 if m else 1


def main():
    global ROOT, SERVER
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--open", action="store_true", help="open the browser")
    ap.add_argument("--detach", action="store_true", help="keep running in the background")
    ap.add_argument("--stop", action="store_true", help="stop this workspace's viewer")
    ap.add_argument("--install-app", action="store_true", help="macOS: add a launcher app for this workspace")
    ap.add_argument("--app-name", default="PM Wiki", help="name of the launcher app")
    ap.add_argument("--app-dir", default="~/Applications", help="where the launcher app goes")
    ap.add_argument("--child", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--root", default=str(HERE.parent.parent), help="workspace folder")
    args = ap.parse_args()
    ROOT = pathlib.Path(args.root).resolve()
    ports = range(args.port, args.port + 10)
    if args.install_app:
        sys.exit(install_app(args.app_name, args.app_dir))
    if args.stop:
        pids = [pid for pid in (running_here(f"http://127.0.0.1:{p}/") for p in ports) if pid]
        for pid in pids:
            os.kill(pid, 15)
        print(f"Stopped the wiki viewer for {ROOT}" if pids else f"No wiki viewer running for {ROOT}")
        return
    if args.detach:
        sys.exit(detach(args))
    server = None
    for port in ports:
        url = f"http://127.0.0.1:{port}/"
        if running_here(url):
            print(f"Wiki viewer for {ROOT} is already running at {url}", flush=True)
            if args.open:
                webbrowser.open(url)
            return
        try:
            server = SERVER = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
            break
        except OSError:  # port taken by something else; try the next one
            continue
    if server is None:
        print(f"No free port in {args.port}-{args.port + 9}; pass --port", flush=True)
        sys.exit(1)
    stop = "python3 tools/viewer/serve.py --stop" if args.child else "Ctrl+C"
    print(f"Wiki viewer for {ROOT} at {url} (to stop: {stop})", flush=True)
    if args.child:  # the launcher has read its line; never write to the pipe again
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, 1)
        os.dup2(devnull, 2)
    if args.open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
