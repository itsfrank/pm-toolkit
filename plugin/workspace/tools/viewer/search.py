"""Full-text search for the viewer, with no model and nothing to install: SQLite's FTS5
engine, which ships inside Python. Ranked (BM25, titles weigh more), stemmed (pricing finds
priced), prefix matching on every word, glossary synonyms, and a retry with the closest known
words when a query finds nothing. The index lives in memory and is rebuilt when files change.
"""
import difflib
import re
import sqlite3

WORD = re.compile(r"[^\W_]+")
A, Z = "\x01", "\x02"  # marks around matched words; the browser turns them into <mark>


def phrase(text, prefix=False):
    words = WORD.findall(text.lower())
    return ('"' + " ".join(words) + '"' + ("*" if prefix else "")) if words else None


class Index:
    def __init__(self):
        self.db, self.stamp, self.vocab = None, None, set()

    def refresh(self, files, title):
        """files: [(key, path)]. Rebuilds only when a file was added, removed or changed.
        Raises sqlite3.OperationalError if this Python's SQLite has no FTS5."""
        stamp = [(key, p.stat().st_mtime_ns, p.stat().st_size) for key, p in files]
        if stamp == self.stamp:
            return
        db = sqlite3.connect(":memory:", check_same_thread=False)
        db.execute("create virtual table docs using fts5(path unindexed, title, body, tokenize='porter unicode61')")
        vocab = set()
        for key, p in files:
            text = p.read_text(encoding="utf-8", errors="replace").replace(A, "").replace(Z, "")
            db.execute("insert into docs values (?, ?, ?)", (key, title(p, text), text))
            vocab.update(w for w in WORD.findall(text.lower()) if len(w) >= 4)
        self.db, self.stamp, self.vocab = db, stamp, vocab

    def run(self, words, synonyms, joiner, whole=None, limit=100):
        groups = []
        for w in words:
            alts = [phrase(w, True)] + [phrase(a) for a in synonyms(w) if a != w]
            groups.append("(" + " OR ".join(a for a in alts if a) + ")")
        expr = f" {joiner} ".join(groups)
        extra = [phrase(a) for a in synonyms(whole) if a != whole] if whole and len(words) > 1 else []
        expr = " OR ".join([f"({expr})"] + [a for a in extra if a])
        rows = self.db.execute(
            "select path, title, highlight(docs, 2, ?, ?) from docs where docs match ? "
            "order by bm25(docs, 0, 10.0, 1.0) limit ?", (A, Z, expr, limit)).fetchall()
        hits = []
        for path, title, body in rows:
            lines = [(line.count(A), n, line.strip()) for n, line in enumerate(body.split("\n"), 1) if A in line]
            best = {n for _, n, _ in sorted(lines, key=lambda l: -l[0])[:3]}  # shown first; the rest unfold
            hits.append({"path": path, "title": title, "matches": len(lines),
                         "lines": [{"line": n, "text": clip(text), "best": n in best}
                                   for _, n, text in lines if n in best or len(lines) <= 40 or n <= lines[39][1]]})
        return hits

    def search(self, query, synonyms):
        """Every word must match (as a prefix, a stem or a synonym). With no result: retry with
        the closest known spelling of unknown words, then with any of the words."""
        words = WORD.findall(query.lower())[:8]
        if not words or self.db is None:
            return {"hits": [], "corrected": None, "any": False}
        whole = " ".join(words)
        hits = self.run(words, synonyms, "AND", whole)
        corrected, loose = None, False
        if not hits:
            fixed = [w if len(w) < 4 or any(v.startswith(w) for v in self.vocab)
                     else next(iter(difflib.get_close_matches(w, self.vocab, 1, 0.75)), w) for w in words]
            if fixed != words:
                hits = self.run(fixed, synonyms, "AND")
                corrected = " ".join(fixed) if hits else None
                words = fixed if hits else words
        if not hits and len(words) > 1:
            hits, loose = self.run(words, synonyms, "OR"), True
        return {"hits": hits, "corrected": corrected, "any": loose and bool(hits)}


def clip(text, width=320):
    """A line cut to width around its first match, marks kept whole."""
    at = text.find(A)
    start = max(0, at - 60) if len(text) > width else 0
    cut = text[start:start + width]
    if cut.count(A) > cut.count(Z):
        cut += Z
    return ("…" if start else "") + cut + ("…" if start + width < len(text) else "")
