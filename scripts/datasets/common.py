"""Shared helpers for the dataset builders: private paths, a polite cached HTTP client,
cached `claude -p` calls with a cost ledger, HTML-to-markdown and pack writing.

Standard library only. Real data never goes under the repo: everything lands in
`<main checkout>/.private/ext-packs/` (override with PM_EXT_PACKS).
"""
import hashlib
import html
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser

REPO = pathlib.Path(__file__).resolve().parents[2]
USER_AGENT = "pm-toolkit-dataset-builder/0.1 (offline eval packs; 1 req/s)"


def private_root():
    """The main checkout's .private/, also from a git worktree."""
    out = subprocess.run(["git", "rev-parse", "--git-common-dir"], cwd=REPO,
                         capture_output=True, text=True)
    common = pathlib.Path(out.stdout.strip()) if out.returncode == 0 else REPO / ".git"
    if not common.is_absolute():
        common = (REPO / common).resolve()
    return common.parent / ".private"


EXT = pathlib.Path(os.environ.get("PM_EXT_PACKS") or private_root() / "ext-packs")
CACHE = EXT / "_cache"


def log(*args):
    print(*args, file=sys.stderr, flush=True)


# ---------- HTTP ----------
_last_request = [0.0]


def fetch(url, binary=False, min_interval=1.0, retries=4, refresh=False):
    """GET with an on-disk cache under _cache/http/ and at most one request per
    min_interval seconds. Returns text (or bytes), or None on 404/403."""
    key = hashlib.sha256(url.encode()).hexdigest()[:24]
    host = re.sub(r"[^a-z0-9.]", "_", url.split("/")[2].lower())
    path = CACHE / "http" / host / key
    meta = path.with_suffix(".url")
    if path.exists() and not refresh:
        data = path.read_bytes()
        return data if binary else data.decode("utf-8", "replace")
    if path.with_suffix(".missing").exists() and not refresh:
        return None
    for attempt in range(retries):
        wait = _last_request[0] + min_interval - time.time()
        if wait > 0:
            time.sleep(wait)
        _last_request[0] = time.time()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            meta.write_text(url + "\n")
            return data if binary else data.decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (403, 404, 410):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.with_suffix(".missing").write_text(f"{e.code} {url}\n")
                return None
            log(f"  HTTP {e.code} on {url}; retry {attempt + 1}")
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            log(f"  {e} on {url}; retry {attempt + 1}")
        time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"giving up on {url}")


def fetch_json(url, **kw):
    text = fetch(url, **kw)
    return json.loads(text) if text else None


# ---------- LLM ----------
LEDGER = CACHE / "llm" / "ledger.jsonl"


def claude(prompt, model="sonnet", tag="misc", system=None, salt="", timeout=900):
    """One `claude -p` call with no tools, run from an empty directory. Cached by a hash of
    (model, system, prompt, salt); each real call appends its total_cost_usd to the ledger.
    Returns (text, cost_usd_of_this_call_or_0_if_cached)."""
    h = hashlib.sha256(json.dumps([model, system, prompt, salt]).encode()).hexdigest()
    path = CACHE / "llm" / f"{h}.json"
    if path.exists():
        return json.loads(path.read_text())["result"], 0.0
    cmd = ["claude", "-p", "--model", model, "--output-format", "json", "--tools", "",
           "--setting-sources", "", "--no-session-persistence", "--strict-mcp-config"]
    if system:
        cmd += ["--system-prompt", system]
    with tempfile.TemporaryDirectory() as empty:
        out = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                             cwd=empty, timeout=timeout)
    try:
        res = json.loads(out.stdout)
    except ValueError:
        raise RuntimeError(f"claude -p failed: {out.stderr[:500]} {out.stdout[:500]}")
    if res.get("is_error"):
        raise RuntimeError(f"claude -p error: {str(res)[:500]}")
    cost = float(res.get("total_cost_usd") or 0)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"model": model, "tag": tag, "result": res.get("result", ""),
                                "cost": cost}))
    with LEDGER.open("a") as f:
        f.write(json.dumps({"t": time.strftime("%Y-%m-%dT%H:%M:%S"), "tag": tag,
                            "model": model, "cost": cost, "hash": h}) + "\n")
    return res.get("result", ""), cost


def ledger_total(prefix=""):
    if not LEDGER.exists():
        return 0.0
    rows = [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]
    return round(sum(r["cost"] for r in rows if r["tag"].startswith(prefix)), 4)


def parse_json_reply(text):
    """First JSON object or array in a model reply (tolerates code fences)."""
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    body = m.group(1) if m else text
    start = min([i for i in (body.find("{"), body.find("[")) if i >= 0] or [0])
    return json.loads(body[start:body.rfind("}" if body[start] == "{" else "]") + 1])


# ---------- HTML (Confluence storage format) to markdown ----------
class _MD(HTMLParser):
    BLOCK = {"p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr", "pre", "blockquote",
             "table", "ul", "ol", "br"}
    SKIP = {"ac:parameter", "style", "script", "ri:attachment"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.lists, self.href, self.skip = [], [], None, 0
        self.row, self.cell, self.in_pre, self.table_rows = None, None, 0, None

    def _w(self, s):
        if self.cell is not None:
            self.cell.append(s)
        else:
            self.out.append(s)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in self.SKIP:
            self.skip += 1
            return
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._w("\n\n" + "#" * int(tag[1]) + " ")
        elif tag in ("p", "div", "blockquote"):
            self._w("\n\n")
        elif tag == "br":
            self._w("\n")
        elif tag in ("ul", "ol"):
            self.lists.append([tag, 0])
        elif tag == "li":
            if self.lists:
                self.lists[-1][1] += 1
            kind, n = self.lists[-1] if self.lists else ("ul", 1)
            self._w("\n" + "  " * (len(self.lists) - 1) + ("- " if kind == "ul" else f"{n}. "))
        elif tag == "table":
            self.table_rows = []
        elif tag == "tr":
            self.row = []
        elif tag in ("td", "th"):
            self.cell = []
        elif tag == "a":
            self.href = a.get("href")
            self._w("[")
        elif tag in ("strong", "b"):
            self._w("**")
        elif tag in ("em", "i"):
            self._w("*")
        elif tag == "code" and not self.in_pre:
            self._w("`")
        elif tag == "pre" or (tag == "ac:plain-text-body"):
            self.in_pre += 1
            self._w("\n\n```\n")
        elif tag == "ri:user":
            self._w("@user")
        elif tag == "ri:page":
            self._w(a.get("ri:content-title", ""))

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self.skip = max(0, self.skip - 1)
            return
        if tag in ("ul", "ol") and self.lists:
            self.lists.pop()
            self._w("\n")
        elif tag in ("td", "th") and self.cell is not None and self.row is not None:
            self.row.append(re.sub(r"\s+", " ", "".join(self.cell)).strip().replace("|", "\\|"))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            if self.table_rows is not None:
                self.table_rows.append(self.row)
            self.row = None
        elif tag == "table" and self.table_rows is not None:
            rows, self.table_rows = self.table_rows, None
            if rows:
                width = max(len(r) for r in rows)
                rows = [r + [""] * (width - len(r)) for r in rows]
                lines = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * width]
                lines += ["| " + " | ".join(r) + " |" for r in rows[1:]]
                self._w("\n\n" + "\n".join(lines) + "\n")
        elif tag == "a":
            self._w(f"]({self.href})" if self.href else "]")
            self.href = None
        elif tag in ("strong", "b"):
            self._w("**")
        elif tag in ("em", "i"):
            self._w("*")
        elif tag == "code" and not self.in_pre:
            self._w("`")
        elif tag == "pre" or tag == "ac:plain-text-body":
            self.in_pre = max(0, self.in_pre - 1)
            self._w("\n```\n")

    def handle_data(self, data):
        if self.skip:
            return
        self._w(data if self.in_pre else re.sub(r"\s+", " ", data))

    def handle_unknown_decl(self, data):  # CDATA inside code macros
        if data.startswith("CDATA["):
            self._w(data[6:])


def html_to_md(src):
    p = _MD()
    p.feed(src or "")
    p.close()
    text = "".join(p.out)
    text = re.sub(r"\*\*\s*\*\*|\[\]\(None\)", "", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"


def strip_tags(src):
    return html.unescape(re.sub(r"<[^>]+>", " ", src or ""))


# ---------- pack writing ----------
def frontmatter(fields):
    lines = ["---"]
    for k, v in fields.items():
        if isinstance(v, list):
            lines.append(f"{k}:")
            lines += [f"  - {x}" for x in v]
        else:
            lines.append(f"{k}: {v}")
    return "\n".join(lines) + "\n---\n\n"


def write(path, text):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def guard_private(path):
    """Refuse to write real-data output inside the repo checkout."""
    p = pathlib.Path(path).resolve()
    if REPO in p.parents and ".private" not in p.parts:
        raise SystemExit(f"refusing to write a real-data pack inside the repo: {p}")
    return p


TEMPLATE_FILES = ["wiki/README.md", "wiki/CHEATSHEET.md", "wiki/catalog/README.md",
                  "wiki/sources/_TEMPLATE.md", "wiki/pages/_TEMPLATE.md", "wiki/lenses.md",
                  "wiki/review-log.md", "wiki/watch.md", "wiki/reports/INDEX.md",
                  "work/README.md"]


def seed_workspace(ws):
    """Copy the empty-workspace convention files from plugin/workspace/."""
    for rel in TEMPLATE_FILES:
        src = REPO / "plugin" / "workspace" / rel
        if src.exists():
            write(pathlib.Path(ws) / rel, src.read_text(encoding="utf-8"))
    (pathlib.Path(ws) / "wiki" / "pages" / "people").mkdir(parents=True, exist_ok=True)
    (pathlib.Path(ws) / "wiki" / "pages" / "people" / ".gitkeep").touch()


def dir_stats(path):
    files = [p for p in pathlib.Path(path).rglob("*") if p.is_file()]
    return len(files), sum(p.stat().st_size for p in files)
