#!/usr/bin/env python3
"""Check a fake-connector page folder (connector/pages/ in a pack, or
samples/kestrel-connector/pages/): required frontmatter, parents and history files exist,
and optional search expectations hold under a plain token search of title + body.

Usage: python3 scripts/datasets/check_connector.py samples/kestrel-connector
Expectations (optional, <dir>/expectations.json):
  {"found_by": {"<id>": ["query", ...]}, "not_found_by": {"<id>": ["query", ...]}}
A query matches a page when every word of it appears in the page's title or body.
"""
import json
import pathlib
import re
import sys

REQUIRED = ["id", "title", "space", "parent", "url", "version", "modified", "access"]


def parse(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None, text
    fields = dict(re.findall(r"^(\w+):[ \t]*(.*)$", m.group(1), re.M))
    return fields, text[m.end():]


def words(s):
    return set(re.findall(r"[a-z0-9]+", s.lower()))


def main(root):
    root = pathlib.Path(root)
    pages_dir = root / "pages" if (root / "pages").is_dir() else root
    errors, pages = [], {}
    for path in sorted(pages_dir.glob("*.md")):
        fields, body = parse(path)
        if fields is None:
            errors.append(f"{path.name}: no frontmatter")
            continue
        missing = [k for k in REQUIRED if k not in fields]
        if missing:
            errors.append(f"{path.name}: missing {', '.join(missing)}")
            continue
        if fields["access"] not in ("ok", "denied"):
            errors.append(f"{path.name}: access must be ok or denied")
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", fields["modified"]):
            errors.append(f"{path.name}: modified must be YYYY-MM-DD")
        if "@v" in path.stem:
            continue
        if path.stem != fields["id"]:
            errors.append(f"{path.name}: file name must be <id>.md")
        pages[fields["id"]] = (fields, body)
    for pid, (fields, _) in pages.items():
        if fields["parent"] and fields["parent"] not in pages:
            errors.append(f"{pid}: parent {fields['parent']} not found")
        for v in re.findall(r"\d+", fields.get("history", "")):
            older = pages_dir / f"{pid}@v{v}.md"
            if not older.exists():
                errors.append(f"{pid}: history lists v{v} but {older.name} is missing")
            elif int(v) >= int(fields["version"]):
                errors.append(f"{pid}: history v{v} is not older than version {fields['version']}")
    exp_path = root / "expectations.json"
    if exp_path.exists():
        exp = json.loads(exp_path.read_text())
        index = {pid: words(f["title"] + " " + body) for pid, (f, body) in pages.items()}
        for pid, queries in exp.get("found_by", {}).items():
            for q in queries:
                if not words(q) <= index.get(pid, set()):
                    errors.append(f"{pid}: expected to match query '{q}'")
        for pid, queries in exp.get("not_found_by", {}).items():
            for q in queries:
                if words(q) <= index.get(pid, set()):
                    errors.append(f"{pid}: must not match query '{q}'")
    denied = sum(1 for f, _ in pages.values() if f["access"] == "denied")
    print(f"check_connector: {len(pages)} pages ({denied} denied), {len(errors)} error(s)")
    for e in errors:
        print("  " + e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "samples/kestrel-connector"))
