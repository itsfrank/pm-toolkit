#!/usr/bin/env python3
"""Large-PDF retrieval pack: a workspace holding long PDF manuals ingested the toolkit's way
(`tools/wiki.py pdf-text` parts, one card each), and question-answering cases whose gold
is an exact quote on a known page.

Each question is written by Opus from a few consecutive pages, in one of several retrieval
shapes (a value in a table, an answer under a heading that doesn't name it, a cross-reference
to another page, a step in a procedure, a detail the manual doesn't give, a plain-language
question that doesn't name the feature, an answer spread over distant pages). A question is
kept only if its quotes are found on the pages it names; pages that repeat a quote (manuals
copy whole sections) count as gold too. Every case asks the agent for a batch of
questions, so one run grades several; each question has a judged answer item and a
mechanical item that the answer cites a gold page.

Usage:
  python3 scripts/datasets/pdf_pack.py --pack pdf-pack \\
      --pdf .private/ext-packs/_cache/pdf/Big_Guide.pdf --pdf .private/ext-packs/_cache/pdf/Other.pdf \\
      [--questions 32] [--per-case 8] [--seed 7] [--mix table,vague,spread]
Writes <pack>/workspace, fixtures, cases.json, README.md and _maps/<pack>-probe.json.
Corrections from reviewing the gold go in _maps/<pack>-fixes.json ([{"match": "<start of the
question>", "answer": ...}], or "drop": true) and are applied on every rebuild.
"""
import argparse
import json
import random
import re
import shutil
import subprocess
import sys

from common import EXT, REPO, claude, frontmatter, guard_private, ledger_total, log, parse_json_reply, seed_workspace, write

TODAY = "2026-11-15"
SHAPES = {
    "table": "The answer is a value in a table or a field/option description (a default, limit, "
             "allowed value, unit, or which option does what).",
    "paraphrase": "The answer sits under a heading that does not name it. Ask in plain words a PM "
                  "would use, avoiding the distinctive terms of the heading and of the answer "
                  "sentence wherever a plain synonym exists.",
    "crossref": "The answer needs two places: the pages shown and the page they refer to "
                "(\"see ... on page N\"). Only use this if a cross-reference is shown; the second "
                "quote must come from the referred page, which is included below.",
    "procedure": "The answer is a specific step, prerequisite, permission or ordering constraint "
                 "inside a procedure.",
    "absent": "Ask about a specific detail that a reader of these pages would expect but that the "
              "pages do NOT state (for example a limit, default or supported version that is not "
              "given). The gold answer is that the manual does not say; quote the nearby text "
              "that comes closest.",
    "vague": "Ask the way a PM who has never opened the manual would: describe the need or "
             "situation in everyday words. Do not name the console, node, snap-in, tab, field, "
             "driver or feature, and avoid every distinctive word of the heading and the answer "
             "sentence.",
    "spread": "The complete answer needs facts from at least three of the excerpts below, which "
              "come from distant pages. Ask one natural question whose full answer combines them "
              "(for example every place, condition or option that applies). Give one quote per "
              "page used.",
}
MIX = ["table", "paraphrase", "table", "crossref", "procedure", "paraphrase", "table", "absent"]
GEN = """You write retrieval test questions for a product manual of {pages} pages.
A test agent will get the whole manual (split into text parts with page markers) and must
find the answer. Below are pages {first}-{last}{extra} of "{title}".

Write ONE question of this shape: {shape}

Rules:
- The question must make sense on its own, without "this page" or "this section", and must
  have a single correct answer in the manual (avoid details that likely repeat elsewhere
  with different values, such as generic UI steps).
- {naming}
- The answer is short (one or two sentences, or a short list).
- Each quote is copied exactly, character for character, from one page below, at most 30
  words, and proves the answer.
- If no good question of this shape fits these pages, reply {{"skip": true}}.

Reply with JSON only:
{{"question": "...", "answer": "...", "quotes": [{{"page": N, "text": "..."}}]}}

{text}"""


def norm(s):
    return " ".join(re.findall(r"[a-z0-9]+", s.lower()))


def load_pages(folder):
    """{page: text} from pdf-text parts."""
    pages = {}
    for part in sorted(folder.glob("part-*.md")):
        page = None
        for line in part.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^<!-- p\.(\d+) -->$", line.strip())
            if m:
                page = int(m.group(1))
                pages[page] = []
            elif page:
                pages[page].append(line)
    return {p: "\n".join(lines) for p, lines in pages.items()}


def ingest(ws, pdfs):
    """Save each PDF and its pdf-text parts into raw/, card it, and list it on one page."""
    docs = []
    for n, pdf in enumerate(pdfs, 1):
        slug = re.sub(r"[^a-z0-9]+", "-", pdf.stem.lower()).strip("-")
        raw = ws / "wiki" / "raw" / f"{TODAY}-{slug}.pdf"
        raw.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(pdf, raw)
        subprocess.run([sys.executable, str(ws / "tools" / "wiki.py"), "--root", str(ws), "pdf-text",
                        str(raw)], check=True, stdout=subprocess.DEVNULL)
        folder = raw.with_suffix("")
        contents = (folder / "contents.md").read_text(encoding="utf-8").splitlines()
        top = [l for l in contents if l.startswith("- ") or l.startswith("  - ")]
        title = pdf.stem.replace("_", " ")
        pages = load_pages(folder)
        sid = f"S-{n:04d}"
        card = frontmatter({
            "id": sid, "title": title, "type": "other", "origin": f"raw/{raw.name}", "origin_url": "",
            "origin_id": "", "origin_version": "", "author_or_owner": "vendor documentation",
            "published": "", "captured": TODAY, "last_checked": "", "recheck_days": "never",
            "trust": "authoritative", "external_ok": "no", "supersedes": ""})
        card += (f"## Summary\nProduct manual, {len(pages)} pages. Text in `raw/{folder.name}/part-NN.md` "
                 f"with `<!-- p.N -->` page markers; full bookmark list in `raw/{folder.name}/contents.md`.\n\n"
                 "## Contents\n" + "\n".join(top) + "\n\n## Key facts\n\n## Caveats\nTables lose their "
                 "layout in the text parts; check the PDF page when a table cell matters.\n\n## Filed into\n"
                 "- pages/topics/product-manuals.md\n")
        write(ws / "wiki" / "sources" / f"{sid}.md", card)
        docs.append({"sid": sid, "title": title, "folder": folder, "pages": pages})
    write(ws / "wiki" / "pages" / "topics" / "product-manuals.md", frontmatter({
        "title": "Product manuals", "type": "topic", "status": "reviewed", "updated": TODAY}) +
        "# Product manuals\n\nThe vendor manuals for the product, ingested whole. Open the card's "
        "Contents to find the part and page, then read that part.\n\n" +
        "\n".join(f"- {d['title']}: {len(d['pages'])} pages [{d['sid']}]" for d in docs) +
        "\n\n## Open questions\n\n## Related\n")
    index = (REPO / "plugin" / "workspace" / "wiki" / "INDEX.md").read_text(encoding="utf-8")
    write(ws / "wiki" / "INDEX.md", index.replace("## Topics\n", "## Topics\n- [Product manuals]"
          f"(pages/topics/product-manuals.md) (reviewed, {TODAY}): which manuals exist and where their "
          "text and page index are.\n"))
    shutil.copy(REPO / "plugin" / "workspace" / "wiki" / "glossary.md", ws / "wiki" / "glossary.md")
    return docs


def spread_terms(doc, rng, k):
    """k distinctive words that appear on 3-6 pages at least 60 pages apart."""
    seen = {}
    for p, t in doc["pages"].items():
        for w in set(re.findall(r"\b[A-Za-z][A-Za-z0-9-]{7,}\b", t)):
            seen.setdefault(w.lower(), set()).add(p)
    terms = sorted(w for w, ps in seen.items() if 3 <= len(ps) <= 6 and max(ps) - min(ps) >= 60)
    rng.shuffle(terms)
    return terms[:k]


def snippets(doc, term, pages):
    out = []
    for p in pages:
        lines = doc["pages"][p].splitlines()
        hit = next(i for i, l in enumerate(lines) if term in l.lower())
        out.append(f"<!-- p.{p} -->\n" + "\n".join(lines[max(0, hit - 12):hit + 13]))
    return "\n\n".join(out)


def windows(doc, rng, k):
    """k starting pages spread over the document, on pages with real text."""
    good = [p for p, t in sorted(doc["pages"].items()) if len(t) > 900 and p > 12]
    step = len(good) / k
    return [good[int(i * step + rng.random() * step * 0.8)] for i in range(k)]


def make_question(docs, doc, start, shape, total_pages):
    pages = doc["pages"]
    span = [p for p in range(start, start + 3) if p in pages] if shape != "spread" else []
    extra_pages = []
    if shape == "spread":
        span = sorted(p for p, t in pages.items() if start in t.lower())
        text = snippets(doc, start, span)
    elif shape == "crossref":
        refs = [int(m) for p in span for m in re.findall(r"on page\s+(\d+)", pages[p])]
        refs = [r for r in refs if r in pages and abs(r - start) > 5]
        if not refs:
            return None
        extra_pages = [refs[0]]
    if shape != "spread":
        text = "\n\n".join(f"<!-- p.{p} -->\n{pages[p]}" for p in span + extra_pages)
    naming = ("Don't name the feature; the question must still have one answer in the manual."
              if shape == "vague" else
              "Name the product area so the question is unambiguous, but don't give away the page.")
    prompt = GEN.format(pages=total_pages, first=span[0], last=span[-1], title=doc["title"],
                        extra=f" and page {extra_pages[0]}" if extra_pages else "",
                        shape=SHAPES[shape], naming=naming, text=text)
    if shape == "spread":
        prompt = prompt.replace(f"Below are pages {span[0]}-{span[-1]}", "Below are excerpts")
    reply, _ = claude(prompt, model="opus", tag="pdf-pack:questions")
    try:
        q = parse_json_reply(reply)
    except (ValueError, IndexError):
        return None
    if q.get("skip") or not q.get("quotes"):
        return None
    for quote in q["quotes"]:  # every quote must be on the page it names
        page = pages.get(int(quote.get("page", 0)), "")
        if not norm(quote.get("text", "")) or norm(quote["text"]) not in norm(page):
            log(f"  dropped ({shape}, p.{start}): quote not on p.{quote.get('page')}")
            return None
    for x in q["quotes"]:
        x["copies"] = sorted({(d["sid"], p) for d in docs for p, t in d["pages"].items() if norm(x["text"]) in norm(t)})
    also = {c for x in q["quotes"] for c in map(tuple, x["copies"])}
    q.update(shape=shape, doc=doc["sid"], title=doc["title"], docs=sorted({sid for sid, _ in also}),
             pages=sorted({int(x["page"]) for x in q["quotes"]}), all_pages=sorted({p for _, p in also}))
    return q


def page_regex(qid, pages):
    """The answer's own section cites one of the gold pages (or a neighbour, for quotes that
    run over a page break)."""
    near = sorted({x for p in pages for x in (p - 1, p, p + 1)})
    alts = "|".join(str(p) for p in near)
    return rf"(?s)^#+ *{qid}\b(?:(?!^#+ *Q\d).)*?\bp(?:p|ages?)?\.? ?(?:\d+[-–, ]+)*(?:{alts})\b"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--pack", required=True)
    ap.add_argument("--pdf", action="append", required=True)
    ap.add_argument("--questions", type=int, default=32)
    ap.add_argument("--per-case", type=int, default=8)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--mix", help="comma list of shapes to cycle through (default: a fixed mix "
                    "without vague and spread)")
    args = ap.parse_args()
    root = guard_private(EXT / args.pack)
    for old in ("workspace", "fixtures"):  # results/ and probe.json survive a rebuild
        shutil.rmtree(root / old, ignore_errors=True)
    ws = root / "workspace"
    seed_workspace(ws)
    shutil.copytree(REPO / "plugin" / "workspace" / "tools", ws / "tools",
                    ignore=shutil.ignore_patterns("__pycache__"))
    pdfs = [guard_private(p) for p in map(__import__("pathlib").Path, args.pdf)]
    docs = ingest(ws, pdfs)
    shutil.rmtree(ws / "tools")  # the runner copies the kit's tools in

    rng = random.Random(args.seed)
    mix = args.mix.split(",") if args.mix else MIX
    weights = [len(d["pages"]) for d in docs]
    quota = [max(4, round(args.questions * w / sum(weights))) for w in weights]
    quota[0] = args.questions - sum(quota[1:])
    questions = []
    for doc, want in zip(docs, quota):
        got = []
        starts = windows(doc, rng, want * 2)
        terms = spread_terms(doc, rng, want * 2) if "spread" in mix else []
        for i in range(want * 2):
            if len(got) >= want:
                break
            shape = mix[len(got) % len(mix)]
            start = terms[i] if shape == "spread" else starts[i]
            log(f"{doc['sid']} {start} {shape}")
            q = make_question(docs, doc, start, shape, len(doc["pages"]))
            if q is None and shape == "crossref":
                q = make_question(docs, doc, start, "table", len(doc["pages"]))
            if q:
                got.append(q)
        questions += got
    rng.shuffle(questions)
    for n, q in enumerate(questions, 1):
        q["id"] = f"Q{n}"
    fixes = EXT / "_maps" / f"{args.pack}-fixes.json"  # hand corrections: [{"match": <question start>, ...}]
    for fix in json.loads(fixes.read_text()) if fixes.exists() else []:
        for q in questions:
            if q["question"].startswith(fix["match"]):
                q.update({k: v for k, v in fix.items() if k != "match"})
    questions = [q for q in questions if not q.get("drop")]  # ids keep their gaps

    cases, probe = [], []
    for c in range(0, len(questions), args.per_case):
        batch = questions[c:c + args.per_case]
        name = f"pdf-qa-{c // args.per_case + 1}"
        qfile = f"fixtures/{name}-questions.md"
        write(root / qfile, "# Questions\n\n" + "\n".join(f"{q['id']}. {q['question']}" for q in batch) + "\n")
        must_find = []
        for q in batch:
            if q["shape"] == "absent":
                text = (f"{q['id']}: says the manuals do not state this (the nearest the manual gets: "
                        f"{q['answer']}); does not invent a value")
            else:
                text = f"{q['id']}: {q['answer']} (cites {' or '.join(q['docs'])} with a page locator)"
            if q["shape"] == "spread":
                text += "; must cover every part, one item per quote below"
            must_find.append({"id": q["id"], "fact": q["id"], "critical": True, "text": text})
            if q["shape"] != "absent":  # page recall: one item per gold page (any copy of it)
                groups = ([[p for _, p in x["copies"]] for x in q["quotes"]] if q["shape"] == "spread"
                          else [q["pages"] + q["all_pages"]])
                for k, group in enumerate(groups):
                    copies = sorted(set(group))
                    must_find.append({"id": f"{q['id']}p{k + 1 if len(groups) > 1 else ''}", "critical": False,
                                      "text": f"{q['id']} cites page {', '.join(map(str, copies))}",
                                      "check": {"regex": page_regex(q["id"], copies)}})
            probe.append({"id": q["id"], "question": q["question"] + " Say I don't know if unsure.",
                          "keys": {"answer": q["answer"]}, "skip": q["shape"] == "absent"})
        cases.append({
            "id": name, "skill": "wiki-answer", "core": False, "tags": ["capability", "real-data", "large-pdf"],
            "prompt": (f"Answer the questions in work/{name}/questions.md from the wiki. Write "
                       f"work/{name}/answers.md with one `## Qn` section per question: the answer, cited "
                       "with a page locator like [S-0001 p.123]. If the sources don't answer a question, "
                       "say so and name where you looked. Work non-interactively."),
            "fixtures": [{"from": qfile, "to": f"work/{name}/questions.md"}],
            "output_file": f"work/{name}/answers.md",
            "must_find": must_find,
            "must_not": [{"id": f"{name}-N1", "text": "States a specific value (number, default, version, "
                          "name) that the cited manual page does not support"}],
            "notes": "Gold answers and quotes were written by Opus from the cited pages and checked "
                     "mechanically for the quotes only; shapes: " + ", ".join(q["shape"] for q in batch)})
    gold = [{"id": q["id"], "shape": q["shape"], "doc": q["doc"], "pages": q["pages"],
             "all_pages": q["all_pages"], "docs": q["docs"],
             "question": q["question"], "answer": q["answer"], "quotes": q["quotes"],
             **({"reviewed": q["reviewed"]} if q.get("reviewed") else {"needs_human_check": True})}
            for q in questions]
    write(root / "cases.json", json.dumps({
        "version": 1, "pack": args.pack, "scenario_today": TODAY,
        "grading": "See evals/GRADER.md. Gold comes from an Opus pass over the cited pages "
                   "(needs_human_check); quotes are verified to be on those pages.",
        "gold_facts": gold, "cases": cases}, indent=1))
    write(EXT / "_maps" / f"{args.pack}-probe.json", json.dumps(probe, indent=1))
    shapes = {s: sum(q["shape"] == s for q in questions) for s in SHAPES}
    write(root / "README.md", f"""# {args.pack} (local only, never commit)

## Provenance and licence
Vendor PDF manuals (publicly downloadable, copyrighted): {", ".join(d["title"] for d in docs)}.
Local-only. Not renamed: the questions test retrieval in the real documents.

## How it was built
`scripts/datasets/pdf_pack.py --pack {args.pack} --seed {args.seed}`. Each PDF went through
`tools/wiki.py pdf-text` and got one card whose Contents lists chapters and sections; one
topic page lists the cards. No facts were filed into pages.

- Questions: {len(questions)} ({", ".join(f"{k} {v}" for k, v in shapes.items())}), {len(cases)} cases.
- Gold: Opus-written answer and exact quotes per question, quotes checked on the named page;
  `needs_human_check`.
- LLM cost of this build: ${ledger_total('pdf-pack'):.2f}.

## Contamination probe
Not run yet: `python3 scripts/datasets/probe.py --pack {args.pack}`.
""")
    log(f"{len(questions)} questions in {len(cases)} cases -> {root}")


if __name__ == "__main__":
    main()
