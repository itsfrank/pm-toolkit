#!/usr/bin/env python3
"""Memorization probe for a real-data pack: ask each gold question with no workspace and
no tools (`claude -p --model sonnet`, 3 samples), let a small judge compare each answer
with the expected fields, and mark items the model answers unaided.

Questions come from .private/ext-packs/_maps/<pack>-probe.json, written by the pack
builder in the ORIGINAL (unrenamed) terms, so the probe measures memorization of the
source itself: [{"id", "question", "keys": {"<field>": "<expected value>", ...}}]; items
with "skip": true are left out.
Results go to <pack>/probe.json and replace the "Contamination probe" section of
<pack>/README.md.

Usage: python3 scripts/datasets/probe.py --pack apache-pilot [--samples 3] [--limit N]
"""
import argparse
import json
import re

from common import EXT, claude, ledger_total, log, parse_json_reply, write

SYSTEM = ("Answer from your own knowledge in two or three sentences. If you do not know, "
          "say \"I don't know\". Do not invent specifics you are unsure of.")


def judge(question, keys, answer, pack):
    prompt = ("Compare an answer with the expected facts. For each field, say whether the answer "
              "states that value (same meaning counts; a guess hedged as unsure still counts if it "
              "names the value). Also say whether the answer declines to answer.\n"
              f"QUESTION: {question}\nEXPECTED: {json.dumps(keys)}\nANSWER: {answer}\n"
              'Reply with JSON only: {"fields": {"<field>": true|false, ...}, "abstained": true|false}')
    text, _ = claude(prompt, model="haiku", tag=f"{pack}:probe-judge")
    try:
        return parse_json_reply(text)
    except (ValueError, IndexError):
        return {"fields": {}, "abstained": False, "error": text[:200]}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--pack", required=True)
    ap.add_argument("--samples", type=int, default=3)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--model", default="sonnet")
    args = ap.parse_args()
    items = [i for i in json.loads((EXT / "_maps" / f"{args.pack}-probe.json").read_text())
             if not i.get("skip")]  # workspace-only facts have nothing to probe
    if args.limit:
        items = items[:args.limit]
    before = ledger_total(f"{args.pack}:probe")
    results = []
    for it in items:
        samples = []
        for i in range(args.samples):
            ans, _ = claude(it["question"], model=args.model, tag=f"{args.pack}:probe",
                            system=SYSTEM, salt=f"sample-{i}")
            v = judge(it["question"], it["keys"], ans, args.pack)
            fields = v.get("fields", {})
            samples.append({"answer": ans[:600], "fields": fields, "abstained": bool(v.get("abstained")),
                            "all_correct": bool(fields) and all(fields.values()) and not v.get("abstained")})
        hits = sum(s["all_correct"] for s in samples)
        per_field = {f: sum(1 for s in samples if s["fields"].get(f)) for f in it["keys"]}
        flag = ("answered_unaided" if hits >= 2 else
                "partial" if any(n >= 2 for n in per_field.values()) else "clean")
        results.append({"id": it["id"], "flag": flag, "hits": hits, "per_field": per_field,
                        "abstained": sum(s["abstained"] for s in samples), "samples": samples})
        log(f"  {it['id']}: {flag} {per_field}")
    cost = round(ledger_total(f"{args.pack}:probe") - before, 4)
    pack = EXT / args.pack
    write(pack / "probe.json", json.dumps({"model": args.model, "samples": args.samples,
                                           "cost_usd_this_run": cost, "items": results}, indent=1))
    counts = {k: sum(1 for r in results if r["flag"] == k) for k in ("answered_unaided", "partial", "clean")}
    flagged = [r["id"] for r in results if r["flag"] != "clean"]
    section = (f"## Contamination probe\n{args.model}, {args.samples} samples per item, no workspace, no tools; "
               f"Haiku judge. Questions use the original (unrenamed) names.\n\n"
               f"- Items: {len(results)}; answered unaided: {counts['answered_unaided']}; partial (some field "
               f"right in 2+ samples): {counts['partial']}; clean: {counts['clean']}.\n"
               f"- Drop or down-weight: {', '.join(flagged) or 'none'}.\n"
               f"- Probe cost (this run, uncached calls): ${cost:.2f}. Details: probe.json.\n")
    readme = pack / "README.md"
    text = readme.read_text() if readme.exists() else f"# {args.pack}\n"
    text = re.sub(r"## Contamination probe\n.*?(?=\n## |\Z)", "", text, flags=re.S).rstrip() + "\n\n" + section
    write(readme, text)
    log(section)


if __name__ == "__main__":
    main()
