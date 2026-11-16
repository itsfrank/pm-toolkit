#!/usr/bin/env python3
"""Fail if any term from a private denylist appears in files git would publish.

The denylist lives outside version control (default: .private/denylist.txt in the main
checkout, also when run from a git worktree; one case-insensitive term per line, '#'
comments). Without a denylist this check is a no-op, so it is safe to run anywhere. Use it
to keep employer, customer or personal names out of a public fork.

Usage: python3 scripts/check_leaks.py [--denylist PATH] [--history]
"""
import argparse
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def private_root():
    """The main checkout's .private/, also from a git worktree."""
    common = pathlib.Path(git("rev-parse", "--git-common-dir").strip())
    return (common if common.is_absolute() else ROOT / common).resolve().parent / ".private"


def load_terms(path):
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    return [l.strip() for l in lines if l.strip() and not l.lstrip().startswith("#")]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--denylist", default=str(private_root() / "denylist.txt"))
    parser.add_argument("--history", action="store_true", help="also scan commit messages")
    args = parser.parse_args()

    terms = load_terms(pathlib.Path(args.denylist))
    if not terms:
        print("check_leaks: no denylist found, skipping")
        return 0

    files = git("ls-files", "--cached", "--others", "--exclude-standard").splitlines()
    hits = []
    for rel in files:
        path = ROOT / rel
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8").lower()
        except UnicodeDecodeError:
            continue
        for term in terms:
            if term.lower() in text:
                line = next(i for i, l in enumerate(text.splitlines(), 1) if term.lower() in l)
                hits.append(f"{rel}:{line}: matches denylisted term #{terms.index(term) + 1}")
        if any(t.lower() in rel.lower() for t in terms):
            hits.append(f"{rel}: path matches a denylisted term")

    if args.history:
        try:
            log = git("log", "--format=%H %B").lower()
        except subprocess.CalledProcessError:
            log = ""
        for term in terms:
            if term.lower() in log:
                hits.append(f"commit messages: match denylisted term #{terms.index(term) + 1}")

    for hit in hits:
        print(hit)
    print(f"check_leaks: scanned {len(files)} files, {len(hits)} hit(s)")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
