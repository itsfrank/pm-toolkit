#!/usr/bin/env python3
"""Scale fixture generator. A seeded skeleton (from a spec in specs/) owns every fact; an
LLM writes only the prose of each document; validate_fixture.py checks each document and
failures are regenerated (up to 2 retries). Output is a pack (workspace/, connector/pages/,
cases.json, manifest.json, README.md) under .private/ext-packs/.

Steps:
1. skeleton (no LLM): fact carriers, filler documents from the topic tree, authors active
   on each date, noise (shuffled paragraphs, misfiled space, near-duplicates with a changed
   fact, stale older versions), a long manual split into parts with plants in appendix tables;
2. prose: one `claude -p --model sonnet` call per document (per manual section), cached by a
   hash of the spec version, tier, seed and document entry;
3. validation and retries; 4. pack writing (workspace share vs connector share by tier).

Usage: python3 scripts/datasets/gen_fixture.py --spec scripts/datasets/specs/copperline.json --tier S
"""
import argparse
import datetime as dt
import json
import pathlib
import random
import re
import shutil

from common import (EXT, claude, dir_stats, frontmatter, guard_private, ledger_total, log,
                    seed_workspace, write)
from validate_fixture import check_doc

HERE = pathlib.Path(__file__).resolve().parent


def slug(s, n=60):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:n].strip("-")


def active(spec, team, date):
    out = [p for p in spec["people"] if p["team"] == team and p["joined"] <= date
           and (not p.get("left") or p["left"] >= date)]
    return out or [p for p in spec["people"] if p["joined"] <= date and not p.get("left")]


def rand_date(rng, lo, hi):
    a, b = dt.date.fromisoformat(lo), dt.date.fromisoformat(hi)
    return (a + dt.timedelta(days=rng.randint(0, (b - a).days))).isoformat()


# ---------- 1. skeleton ----------
TYPE_HINTS = [(r"guide|rules|flow|formats|codes|setup|macros|checklist", ["runbook", "faq"]),
              (r"review|notes|planning|scan|board|sync", ["meeting-notes", "report"]),
              (r"audit|incident|drill", ["report", "retro"]),
              (r"policy|settings|balances|freeze|refunds|limits|lifetime", ["policy", "design-doc"])]


def filler_type(topic, rng, spec):
    for pat, kinds in TYPE_HINTS:
        if re.search(pat, topic, re.I):
            return rng.choice(kinds)
    return rng.choice(["design-doc", "prd", "release-notes"])

def build_manifest(spec, tier, seed):
    rng = random.Random(seed)
    T = spec["tiers"][tier]
    types = spec["doc_types"]
    docs, manual_plants = [], []

    def add(**d):
        d["id"] = f"D-{len(docs) + 1:04d}"
        author = rng.choice(active(spec, d["team"], d["date"]))
        d.setdefault("author", author["name"])
        d.setdefault("folder", types[d["type"]]["folder"])
        docs.append(d)
        return d

    for f in spec["facts"]:
        for c in f["carriers"]:
            if c["type"] == "manual":
                manual_plants.append((f["id"], c))
                continue
            d = add(kind="carrier", type=c["type"], title=c["topic"], team=c["team"], date=c["date"],
                    facts=[f["id"]], where=f["where"], trust=f.get("trust", types[c["type"]]["trust"]))
            if f.get("noise") == "near-duplicate":
                add(kind="near-duplicate", type=c["type"], title=c["topic"] + " (notes copy)", team=c["team"],
                    date=(dt.date.fromisoformat(c["date"]) + dt.timedelta(days=9)).isoformat(),
                    facts=[f["id"]], alt_of=[f["id"]], derived_from=d["id"], where="card",
                    trust=types[c["type"]]["trust"])
            if f.get("noise") == "stale-version":
                add(kind="stale-version", type=c["type"], title=c["topic"], team=c["team"],
                    date=(dt.date.fromisoformat(c["date"]) - dt.timedelta(days=24)).isoformat(),
                    facts=[f["id"]], alt_of=[f["id"]], derived_from=d["id"], where=f["where"],
                    trust=types[c["type"]]["trust"])
    n_manual_docs = T["manual_parts"]
    topics = [(team, t) for team, ts in spec["filler_topics"].items() for t in ts]
    rng.shuffle(topics)
    i = 0
    while len(docs) + n_manual_docs < T["docs"]:
        team, topic = topics[i % len(topics)]
        rnd = i // len(topics)
        add(kind="filler", type=filler_type(topic, rng, spec), team=team,
            title=topic + (f" ({2024 + rnd + 1} update)" if rnd else ""),
            date=rand_date(rng, spec["start"], spec["today"]), facts=[], where="filler",
            trust=None)
        i += 1
    for d in docs:
        d["trust"] = d["trust"] or types[d["type"]]["trust"]
    # manual: outline-first; plants go into appendix tables of specific parts
    parts = T["manual_parts"]
    per_part = max(1, T["manual_pages"] // max(1, parts) // 5)
    for p in range(parts):
        plants = [fid for k, (fid, _) in enumerate(manual_plants) if parts - 1 - k % parts == p]
        add(kind="manual", type="manual", team="frontdesk", title=f"Studio operations manual, part {p + 1} of {parts}",
            date="2026-04-02", facts=plants, where="manual", trust="authoritative", sections=per_part,
            author="Lucia Brandt", part=p + 1, parts=parts)
    # tier-wide noise on filler (rates from the spec)
    filler = [d for d in docs if d["kind"] == "filler"]
    nz = spec["noise"]
    for d in rng.sample(filler, round(len(filler) * nz["shuffled"])):
        d["shuffle"] = True
    folders = sorted({t["folder"] for t in types.values()})
    for d in rng.sample(filler, round(len(filler) * nz["misfiled"])):
        d["misfiled_to"] = rng.choice([f for f in folders if f != d["folder"]])
    for d in rng.sample(filler, round(len(filler) * nz["near_duplicates"])):
        add(kind="near-duplicate", type=d["type"], title=d["title"] + " (copy)", team=d["team"],
            date=d["date"], facts=[], derived_from=d["id"], where="filler", trust=d["trust"], changed_numbers=True)
    for d in rng.sample(filler, round(len(filler) * nz["stale_versions"])):
        add(kind="stale-version", type=d["type"], title=d["title"], team=d["team"],
            date=(dt.date.fromisoformat(d["date"]) - dt.timedelta(days=30)).isoformat(),
            facts=[], derived_from=d["id"], where="filler", trust=d["trust"], changed_numbers=True)
    # placement: workspace raw vs connector
    for d in docs:
        if d["where"] == "connector":
            d["home"] = "connector"
        elif d["where"] in ("raw-only", "card", "card+page", "manual"):
            d["home"] = "workspace"
        elif d["kind"] in ("near-duplicate", "stale-version") and d.get("derived_from"):
            d["home"] = None  # follows its source below
        else:
            d["home"] = "connector" if rng.random() < T["connector_share"] else "workspace"
    by_id = {d["id"]: d for d in docs}
    for d in docs:
        if d["home"] is None:
            d["home"] = by_id[d["derived_from"]]["home"]
    return docs


# ---------- 2. prose ----------
def cast(spec, d):
    """People who may appear: joined by the date, and not a planted key of another fact."""
    keys = {k for f in spec["facts"] if f["id"] not in d["facts"] for k in f["keys"]}
    return [p for p in spec["people"] if p["joined"] <= d["date"] and p["name"] not in keys
            and not any(p["name"] in k for k in keys)]


def doc_prompt(spec, d, attempt_note=""):
    facts = {f["id"]: f for f in spec["facts"]}
    t = spec["doc_types"][d["type"]]
    words = t["words"]
    carry = [facts[i] for i in d["facts"]]
    avoid = [f for f in spec["facts"] if f["id"] not in d["facts"]]
    planned = sorted({x for f in carry for x in re.findall(r"\d{4}-\d{2}-\d{2}", f["statement"])})
    lines = [
        "You are writing one internal document for a FICTIONAL company's knowledge base. It is test data "
        "for evaluating search tools; every name and number is invented.",
        f"Company: {spec['company']}, {spec['domain']}.",
        f"Products: " + "; ".join(f"{p['name']} (also called {', '.join(p['aliases'])})" for p in spec["products"]),
        f"Document type: {d['type']}. Title: {d['title']}. Date: {d['date']}. Author: {d['author']} "
        f"({d['team']} team). Trust level of this kind of document: {d['trust']}.",
        f"Length: about {words} words of markdown. Start with '# {d['title']}' and a short metadata line "
        "(author, date, status) the way a real document of this type would.",
        "People you may name (no other people): " + "; ".join(
            f"{p['name']} ({p['role']}, {p['team']})" for p in cast(spec, d)),
        f"Customers you may name: {', '.join(spec['customers'])}. Partners: {', '.join(spec['partners'])}.",
        f"Do not mention any calendar date later than {d['date']}" + (
            f", except these planned dates: {', '.join(planned)}." if planned else "."),
        "Never use these words or phrases: " + ", ".join(f"'{w}'" for w in spec["hint_words"]) + ".",
    ]
    if d["kind"] == "manual":
        lines.append(f"This is part {d['part']} of {d['parts']} of a long operations manual for studio staff and "
                     "admins: numbered sections with procedures, settings and a closing appendix with at least "
                     "one table. Do not repeat a table of contents.")
    if carry:
        lines.append("Include the following facts. State each one in passing inside an ordinary section, a table "
                     "row or a footnote whose main subject is something else. Never put them in a heading, a "
                     "summary, bold text or a list of highlights, and do not signal that they matter. Use the "
                     "exact quoted strings:")
        for f in carry:
            lines.append(f"- {f['statement']} (exact strings: {', '.join(repr(k) for k in f['keys'])})")
        lines.append("Use your own wording for everything else; do not reuse the wording of this question: " +
                     " / ".join(f["question"] for f in carry))
    lines.append("Do not state anything about these subjects, and never use these strings: " + "; ".join(
        f"{f['statement']} [{', '.join(f['keys'] + f.get('alt', []))}]" for f in avoid))
    if attempt_note:
        lines.append("A previous draft had these problems; avoid them: " + attempt_note)
    lines.append("Write only the document.")
    return "\n".join(lines)


def derive(spec, d, src_text, rng):
    """Near-duplicates and stale versions are deterministic edits of their source."""
    facts = {f["id"]: f for f in spec["facts"]}
    text = src_text
    for fid in d.get("alt_of", []):
        for key, alt in zip(facts[fid]["keys"], facts[fid].get("alt", [])):
            text = text.replace(key, alt)
    if d.get("changed_numbers"):
        text = re.sub(r"\b(\d{2,3})\b(?![-:/])", lambda m: str(int(m.group(1)) + rng.choice([-3, 2, 5, 10])), text, count=4)
    text = re.sub(r"^# .*$", f"# {d['title']}", text, count=1, flags=re.M)
    return re.sub(r"\b20\d\d-\d\d-\d\d\b", lambda m: d["date"] if m.group(0) > d["date"] and not any(
        m.group(0) in k for f in facts.values() for k in f.get("keys", []) + f.get("alt", [])) else m.group(0), text)


def generate(spec, docs, tier, seed, pack):
    texts, problems = {}, {}
    rng = random.Random(seed + 1)
    for d in docs:
        if d["kind"] in ("near-duplicate", "stale-version"):
            continue
        note = ""
        for attempt in range(3):
            if d["kind"] == "manual" and d.get("sections", 1) > 1:
                chunks = []
                for s in range(d["sections"]):
                    sub = dict(d, title=f"{d['title']}, section {s + 1}", facts=d["facts"] if s == d["sections"] - 1 else [])
                    t, _ = claude(doc_prompt(spec, sub, note), model="sonnet", tag=f"{pack}:gen",
                                  salt=f"{spec['spec_version']}/{tier}/{seed}/{attempt}")
                    chunks.append(t)
                text = "\n\n".join(chunks)
            else:
                text, _ = claude(doc_prompt(spec, d, note), model="sonnet", tag=f"{pack}:gen",
                                 salt=f"{spec['spec_version']}/{tier}/{seed}/{attempt}")
            text = text.strip() + "\n"
            probs = check_doc(d, text, spec)
            if not probs:
                break
            note = "; ".join(probs[:6])
            log(f"  {d['id']} attempt {attempt + 1}: {note}")
        texts[d["id"]] = text
        if probs:
            problems[d["id"]] = probs
    for d in docs:
        if d["kind"] in ("near-duplicate", "stale-version"):
            texts[d["id"]] = derive(spec, d, texts[d["derived_from"]], rng)
            probs = check_doc(d, texts[d["id"]], spec)
            if probs:
                problems[d["id"]] = probs
        if d.get("shuffle"):
            head, *blocks = texts[d["id"]].split("\n\n")
            random.Random(d["id"]).shuffle(blocks)
            texts[d["id"]] = "\n\n".join([head] + blocks)
    return texts, problems


# ---------- 4. pack ----------
def write_pack(spec, docs, texts, problems, out, tier, seed):
    ws, conn = out / "workspace", out / "connector" / "pages"
    seed_workspace(ws)
    facts = {f["id"]: f for f in spec["facts"]}
    by_id = {d["id"]: d for d in docs}
    spaces = {t["id"]: t["id"].upper()[:6] for t in spec["teams"]}
    home_ids = {}
    for t in spec["teams"]:
        pid = str(80001 + len(home_ids))
        home_ids[t["id"]] = pid
        write(conn / f"{pid}.md", frontmatter({"id": pid, "title": f"{t['name']} home", "space": spaces[t["id"]],
              "parent": "", "url": f"https://wiki.copperline.example/{spaces[t['id']]}/pages/{pid}", "version": 3,
              "modified": spec["start"], "access": "ok", "author": active(spec, t["id"], spec["today"])[0]["name"]}) +
              f"# {t['name']}\n\nOwns: {t['owns']}.\n")
    # org chart (deterministic, S-0001)
    org = "# Product & Engineering org (snapshot)\n\n| Team | People | Owns |\n|---|---|---|\n" + "\n".join(
        f"| {t['name']} | " + ", ".join(f"{p['name']} ({p['role']})" for p in spec["people"]
                                        if p["team"] == t["id"] and not p.get("left")) + f" | {t['owns']} |"
        for t in spec["teams"]) + "\n"
    raw_files = {"D-ORG": ("2026-07-01-org-chart.md", org)}
    write(ws / "wiki" / "raw" / "2026-07-01-org-chart.md", org)
    cards, page_ids = [("S-0001", "D-ORG", "Product & Engineering org (snapshot)", "2026-07-01", "authoritative", "org-chart")], {}
    for d in sorted(docs, key=lambda d: d["date"]):
        text = texts[d["id"]]
        version_of = d["derived_from"] if d["kind"] == "stale-version" and d["home"] == "connector" else None
        if d["home"] == "connector":
            if version_of:
                continue  # written as history of its source below
            pid = page_ids.setdefault(d["id"], str(81001 + len(page_ids)))
            space = spaces[d["team"]] if not d.get("misfiled_to") else spaces[random.Random(d["id"]).choice(list(spaces))]
            stale = [x for x in docs if x.get("derived_from") == d["id"] and x["kind"] == "stale-version"]
            fm = {"id": pid, "title": d["title"], "space": space, "parent": home_ids[d["team"]],
                  "url": f"https://wiki.copperline.example/{space}/pages/{pid}", "version": 2 if stale else 1,
                  "modified": d["date"], "access": "ok", "author": d["author"]}
            if stale:
                fm["history"] = "[1]"
                write(conn / f"{pid}@v1.md", frontmatter(dict(fm, version=1, modified=stale[0]["date"])) + texts[stale[0]["id"]])
                stale[0]["path"] = f"connector/pages/{pid}@v1.md"
                stale[0]["page_id"] = pid
            write(conn / f"{pid}.md", frontmatter(fm) + text)
            d["path"], d["page_id"] = f"connector/pages/{pid}.md", pid
        else:
            name = f"{d['date']}-{slug(d['title'])}.md"
            write(ws / "wiki" / "raw" / name, text)
            d["path"] = f"workspace/wiki/raw/{name}"
            if d["kind"] == "manual" and d["part"] == d["parts"]:
                write(ws / "wiki" / "raw" / "studio-operations-manual-index.md", "# Studio operations manual: index\n\n"
                      "One document split into parts:\n" + "\n".join(
                          f"- part {x['part']}: {x['date']}-{slug(x['title'])}.md" for x in docs if x["kind"] == "manual") + "\n")
            sid = f"S-{len(cards) + 1:04d}"
            cards.append((sid, d["id"], d["title"], d["date"], d["trust"], d["type"]))
            raw_files[d["id"]] = (name, text)
    for sid, did, title, date, trust, typ in cards:
        d = by_id.get(did, {})
        name, text = raw_files[did]
        first = re.sub(r"\s+", " ", re.sub(r"^#.*$", "", text, count=1, flags=re.M)).strip()[:280]
        kf = [facts[f]["statement"] for f in d.get("facts", []) if d.get("where") in ("card", "card+page")
              and f not in d.get("alt_of", [])]
        if d.get("misfiled_to"):
            typ = d["misfiled_to"]
        write(ws / "wiki" / "sources" / f"{sid}.md", frontmatter({
            "id": sid, "title": title, "type": typ, "origin": f"raw/{name}", "origin_url": "", "origin_id": "",
            "origin_version": '""', "last_checked": date, "recheck_days": 90, "author_or_owner": d.get("author", "Product Operations"),
            "published": date, "captured": date, "trust": trust, "external_ok": "no"}) +
            f"## Summary\n{first}\n\n## Key facts\n" + ("\n".join(f"- {k}" for k in kf) or "- See raw.") +
            "\n\n## Caveats\nNone noted.\n\n## Filed into\n- (not filed)\n")
        if d:
            d["card"] = sid
    # pages: products, teams from the org chart; decision pages for card+page facts
    index = ["# Wiki index\n", "## Products"]
    for p in spec["products"]:
        write(ws / "wiki" / "pages" / "products" / f"{slug(p['name'])}.md", frontmatter({
            "type": "product", "status": "draft", "updated": "2026-07-01", "aliases": f"[{', '.join(p['aliases'])}]",
            "sources": "[S-0001]"}) + f"# {p['name']}\n\nOwned by the {p['team']} team. [S-0001]\n")
        index.append(f"- [{p['name']}](pages/products/{slug(p['name'])}.md) (draft, 2026-07-01): owner team.")
    index.append("\n## Decisions")
    for d in docs:
        if d.get("where") == "card+page" and d["kind"] == "carrier" and d["type"] == "decision-record":
            write(ws / "wiki" / "pages" / "decisions" / f"{slug(d['title'])}.md", frontmatter({
                "type": "decision", "status": "reviewed", "updated": d["date"], "aliases": "[]",
                "sources": f"[{d['card']}]"}) + f"# {d['title']}\n\n" + "\n".join(
                f"- {facts[f]['statement']} [{d['card']}]" for f in d["facts"]) + "\n")
            index.append(f"- [{d['title']}](pages/decisions/{slug(d['title'])}.md) (reviewed, {d['date']}): decision and revisit trigger.")
    write(ws / "wiki" / "INDEX.md", "\n".join(index) + "\n")
    write(ws / "wiki" / "glossary.md", "# Glossary\n\n| Term | Means | Also called | Source |\n|---|---|---|---|\n" +
          "\n".join(f"| {a} | {b} | {c} | (team usage) |" for a, b, c in spec["glossary"]) + "\n")
    for a in spec["asks"]:
        write(ws / "work" / f"{a['date']}-{a['id']}" / "ask.md", f"# Ask\n\n- **From:** {a['from']}\n- **To:** {a['to']}\n"
              f"- **Date:** {a['date']}\n\n## Verbatim\n> {a['verbatim']}\n")
    # cases
    cases = []
    asks = {a["id"]: a for a in spec["asks"]}
    for c in spec["cases"]:
        a = asks[c["ask"]]
        d0 = f"work/{a['date']}-{a['id']}"
        must = []
        for i, fid in enumerate(c["must"]):
            f = facts[fid]
            carrier = next((d for d in docs if fid in d["facts"] and d["kind"] in ("carrier", "manual")), None)
            item = {"id": f"{c['id'].split('-')[1][:2].upper()}{i + 1}", "fact": fid, "critical": f["where"] != "manual",
                    "text": ("Reports as unknown (with what was searched), never as yes or no: " if f["where"] == "absent" else "") + f["statement"]}
            if carrier and carrier.get("home") == "connector":
                item["log_check"] = {"fetched": carrier["page_id"]}
            must.append(item)
        cases.append({"id": c["id"], "skill": c["skill"], "core": False, "tags": ["capability", "scale", tier],
                      "connector": c["connector"], "prompt": f"Run {c['skill']} for the ask in {d0}/. A read-only Confluence "
                      "connector is available. Work non-interactively: do not stop at checkpoints or wait for answers; "
                      "record open questions in the files instead.", "output_file": f"{d0}/{c['output']}",
                      "must_find": must, "must_not": [
                          {"id": "SN1", "text": "Uses a value from a near-duplicate or stale version as current without flagging the conflict."},
                          {"id": "SN2", "text": "States the hearsay claim (offline already works) as fact."},
                          {"id": "SN3", "text": "Calls any connector write tool."},
                          {"id": "NX-invent", "text": "Invents a quote, metric, owner, date or approval not in the sources."}],
                      "notes": f"Generated from {spec['spec_version']} tier {tier} seed {seed}."})
    gold = [dict(f, files=[d["path"] for d in docs if f["id"] in d["facts"] and d.get("path")]) for f in spec["facts"]]
    write(out / "cases.json", json.dumps({"version": 1, "pack": out.name, "scenario_today": spec["today"],
          "grading": "See evals/GRADER.md.", "planted_facts": gold, "cases": cases}, indent=1))
    write(out / "manifest.json", json.dumps({"spec": spec, "tier": tier, "seed": seed, "docs": docs,
                                             "problems": problems}, indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--spec", default=str(HERE / "specs" / "copperline.json"))
    ap.add_argument("--tier", default="S", choices=["S", "M", "L"])
    ap.add_argument("--seed", type=int, default=20261020)
    ap.add_argument("--pack", default=None)
    ap.add_argument("--plan-only", action="store_true", help="write the skeleton and exit (no LLM)")
    args = ap.parse_args()
    spec = json.loads(pathlib.Path(args.spec).read_text())
    pack = args.pack or f"scale-{args.tier.lower()}"
    out = guard_private(EXT / pack)
    docs = build_manifest(spec, args.tier, args.seed)
    kinds = {k: sum(1 for d in docs if d["kind"] == k) for k in sorted({d["kind"] for d in docs})}
    log(f"skeleton: {len(docs)} documents {kinds}")
    if args.plan_only:
        print(json.dumps(docs, indent=1))
        return
    before = ledger_total(f"{pack}:gen")
    texts, problems = generate(spec, docs, args.tier, args.seed, pack)
    if out.exists():
        shutil.rmtree(out)
    write_pack(spec, docs, texts, problems, out, args.tier, args.seed)
    cost_total = ledger_total(f"{pack}:gen")
    files, size = dir_stats(out)
    words = sum(len(t.split()) for t in texts.values())
    write(out / "README.md", f"""# {pack}: synthetic scale fixture, tier {args.tier}

Fictional ({spec['company']}: {spec['domain']}). {spec['canary']}

- Built by `scripts/datasets/gen_fixture.py --spec {pathlib.Path(args.spec).name} --tier {args.tier} --seed {args.seed}`;
  skeleton and gold in `manifest.json`, cases in `cases.json`.
- Documents: {len(docs)} ({kinds}); {words} words; workspace share vs connector share
  {1 - spec['tiers'][args.tier]['connector_share']:.0%} / {spec['tiers'][args.tier]['connector_share']:.0%} for filler.
- Files: {files}, {size // 1024} KB.
- Validation: {len(problems)} document(s) still failing after 2 retries: {', '.join(problems) or 'none'}
  (details in manifest.json `problems`; rerun `python3 scripts/datasets/validate_fixture.py {out}`).
- Generation cost (sum of total_cost_usd from `claude -p --output-format json`, all calls for this
  pack including retries and cached earlier runs): ${cost_total:.2f}; this run: ${cost_total - before:.2f}.
- Licence: generated fictional content, no third-party text. Kept local because outputs are
  frozen per version and not committed (only spec and seed are).
""")
    log(f"pack {out}: {files} files, {size // 1024} KB, cost ${cost_total:.2f}, failing docs {len(problems)}")


if __name__ == "__main__":
    main()
