#!/usr/bin/env python3
"""Local web viewer for the PM wiki: renders markdown, links citations, and records
highlight notes into wiki/notes.jsonl. Standard library only; binds 127.0.0.1.

Usage: python3 tools/viewer/serve.py [--port 8765] [--open] [--detach] [--stop] [--root PATH]
"""
import argparse
import datetime
import hashlib
import http.server
import json
import os
import pathlib
import re
import secrets
import subprocess
import sys
import threading
import urllib.parse
import urllib.request
import webbrowser

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import wiki as wikitools  # noqa: E402  (tools/wiki.py, shared status logic)
STATIC = HERE / "static"
TYPES = {".html": "text/html", ".js": "text/javascript", ".css": "text/css"}
MAX_BODY = 64 * 1024
FRONT = re.compile(r"\A---\n(.*?)\n---\n", re.S)
LOCK = threading.Lock()
ROOT = None


# Originals in wiki/raw/ are untrusted: anything that a browser could run is sent as text,
# and every raw response is sandboxed by CSP.
RAW_TYPES = {".pdf": "application/pdf", ".png": "image/png", ".jpg": "image/jpeg",
             ".jpeg": "image/jpeg", ".gif": "image/gif", ".md": "text/plain", ".txt": "text/plain",
             ".csv": "text/plain", ".json": "text/plain", ".html": "text/plain",
             ".htm": "text/plain", ".eml": "text/plain", ".xml": "text/plain"}
RAW_CSP = "default-src 'none'; img-src 'self'; style-src 'unsafe-inline'; sandbox"


def raw_file(path):
    """Resolve a path to a file under wiki/raw/; None if it escapes that folder."""
    try:
        p = (ROOT / path).resolve()
        p.relative_to((ROOT / "wiki" / "raw").resolve())
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
    for top in ("wiki", "work"):
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

    def do_GET(self):
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
            term = arg("q").lower()
            hits = []
            if len(term) >= 2:
                for p in md_files():
                    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
                    for i, line in enumerate(lines, 1):
                        if term in line.lower():
                            hits.append({"path": p.relative_to(ROOT).as_posix(), "line": i,
                                         "text": line.strip()[:200]})
                            if len(hits) >= 50:
                                return self.send(200, hits)
            return self.send(200, hits)
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
        if urllib.parse.urlparse(self.path).path != "/api/notes":
            return self.send(404, {"error": "not found"})
        size = int(self.headers.get("Content-Length") or 0)
        if size <= 0 or size > MAX_BODY:
            return self.send(413, {"error": "body too large or empty"})
        try:
            body = json.loads(self.rfile.read(size))
            quote = body.get("quote") or {}
            text = str(body.get("text", "")).strip()
            line = body.get("line")
        except (ValueError, AttributeError):
            return self.send(400, {"error": "invalid JSON"})
        p = inside(str(body.get("file", "")))
        if not p or not text or not str(quote.get("exact", "")).strip():
            return self.send(400, {"error": "need an existing .md file, a quote and text"})
        note = {
            "type": "note",
            "id": "N-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S-") + secrets.token_hex(2),
            "created": now(),
            "file": p.relative_to(ROOT).as_posix(),
            "quote": {"exact": str(quote.get("exact", "")),
                      "prefix": str(quote.get("prefix", ""))[-60:],
                      "suffix": str(quote.get("suffix", ""))[:60]},
            "line": line if isinstance(line, int) else None,
            "commit": commit(),
            "file_sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "text": text,
        }
        log = ROOT / "wiki" / "notes.jsonl"
        with LOCK:
            log.parent.mkdir(parents=True, exist_ok=True)
            with log.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(note, ensure_ascii=False) + "\n")
        self.send(201, note)


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
    global ROOT
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--open", action="store_true", help="open the browser")
    ap.add_argument("--detach", action="store_true", help="keep running in the background")
    ap.add_argument("--stop", action="store_true", help="stop this workspace's viewer")
    ap.add_argument("--child", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--root", default=str(HERE.parent.parent), help="workspace folder")
    args = ap.parse_args()
    ROOT = pathlib.Path(args.root).resolve()
    ports = range(args.port, args.port + 10)
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
            server = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
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
