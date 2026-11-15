#!/usr/bin/env python3
"""Checks for generated fixture documents (used by gen_fixture.py, also runnable on a
built pack). Standard library only, no LLM.

Per document:
- names: every "Firstname Lastname" after an owner/author/role cue, and every frontmatter
  author, is a person in the spec;
- dates: every YYYY-MM-DD is on or before the document's date, or a planned date the
  spec knows (fact keys, alternates, ask dates);
- gold placement: a carrier holds its fact's key strings; no other document holds them
  (alternate values only where the manifest says so);
- lexical overlap: the sentence holding a key shares few words with the fact's question
  (token Jaccard <= lexical_overlap_max);
- hint words: none of the spec's signpost words, fact ids or "planted".

Usage: python3 scripts/datasets/validate_fixture.py <pack dir>   (reads manifest.json)
"""
import json
import pathlib
import re
import sys

STOP = set("a an the of to in on for and or is are was were be by with at as it its this that "
           "from if how what who when which can could would should do does did we our us they "
           "their there any all not no".split())
CUE = re.compile(r"(?:Owner|Author|Authors|By|PM|EM|Lead|Attendees|Approved by|Reviewer|"
                 r"Reviewers|DRI|Contact|with|from|asked|said)\s*[:\-]?\s*((?:[A-Z][a-z]+(?:-[A-Z][a-z]+)?"
                 r"(?: [A-Z][a-z]+(?:-[A-Z][a-z]+)?)(?:,\s*|\s+and\s+)?)+)")
NAME = re.compile(r"\b([A-Z][a-z]+ [A-Z][a-z]+(?:-[A-Z][a-z]+)?)\b")


def tokens(s):
    return {w for w in re.findall(r"[a-z0-9']+", s.lower()) if w not in STOP}


def jaccard(a, b):
    a, b = tokens(a), tokens(b)
    return len(a & b) / max(1, len(a | b))


def sentence_with(text, key):
    i = text.find(key)
    if i < 0:
        return ""
    start = max(text.rfind(".", 0, i), text.rfind("\n", 0, i)) + 1
    ends = [j for j in (text.find(".", i + len(key)), text.find("\n", i + len(key))) if j >= 0]
    return text[start:min(ends) if ends else len(text)]


def known_dates(spec):
    dates = {a["date"] for a in spec["asks"]}
    for f in spec["facts"]:
        for v in f.get("keys", []) + f.get("alt", []):
            dates.update(re.findall(r"\d{4}-\d{2}-\d{2}", v))
        dates.update(re.findall(r"\d{4}-\d{2}-\d{2}", f["statement"]))
    return dates


def check_doc(doc, text, spec):
    """Problems for one generated document (doc = manifest entry)."""
    problems = []
    people = {p["name"] for p in spec["people"]}
    allowed = people | {c for c in spec.get("customers", [])} | set(spec.get("partners", []))
    allowed |= {p["name"] for p in spec["products"]} | {t["name"] for t in spec["teams"]}
    allowed |= {g[0] for g in spec.get("glossary", [])} | {spec["company"]}
    for m in CUE.finditer(text):
        for name in NAME.findall(m.group(1)):
            if name not in allowed and not any(name in a for a in allowed):
                problems.append(f"unknown person '{name}'")
    if doc.get("author") and doc["author"] not in people:
        problems.append(f"author '{doc['author']}' not in spec")
    future_ok = known_dates(spec)
    for d in re.findall(r"\b(20\d\d-\d\d-\d\d)\b", text):
        if d > doc["date"] and d not in future_ok:
            problems.append(f"date {d} after document date {doc['date']}")
    facts = {f["id"]: f for f in spec["facts"]}
    carries = set(doc.get("facts", []))
    alt_ok = set(doc.get("alt_of", []))
    low = text.lower()
    for fid, f in facts.items():
        for key in f.get("keys", []):
            present = key.lower() in low
            if fid in carries and fid not in alt_ok and not present:
                problems.append(f"{fid}: key '{key}' missing from carrier")
            if present and (fid not in carries or fid in alt_ok):
                problems.append(f"{fid}: key '{key}' leaked into a non-carrier")
            if present and fid in carries:
                sent = sentence_with(text, key) or sentence_with(low, key.lower())
                j = jaccard(sent, f["question"])
                if j > spec.get("lexical_overlap_max", 0.3):
                    problems.append(f"{fid}: overlap {j:.2f} with question")
        for alt in f.get("alt", []):
            if alt.lower() in low and fid not in alt_ok:
                problems.append(f"{fid}: alternate value '{alt}' outside its noise document")
    for w in spec.get("hint_words", []):
        if w.lower() in low:
            problems.append(f"hint word '{w}'")
    for fid in facts:
        if re.search(rf"\b{fid}\b", text):
            problems.append(f"fact id {fid} in text")
    return problems


def main(pack):
    pack = pathlib.Path(pack)
    manifest = json.loads((pack / "manifest.json").read_text())
    spec = manifest["spec"]
    total = 0
    for doc in manifest["docs"]:
        path = pack / doc["path"]
        if not path.exists():
            print(f"{doc['id']}: missing {doc['path']}")
            total += 1
            continue
        probs = check_doc(doc, path.read_text(encoding="utf-8"), spec)
        for p in probs:
            print(f"{doc['id']} ({doc['path']}): {p}")
        total += len(probs)
    print(f"validate_fixture: {len(manifest['docs'])} docs, {total} problem(s)")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
