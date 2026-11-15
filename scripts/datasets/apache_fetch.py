#!/usr/bin/env python3
"""Fetch Apache proposal pages (Kafka KIPs, Flink FLIPs), their version history, the
matching dev-list DISCUSS/VOTE/RESULT threads and JIRA issues, for local eval packs.

The Apache wiki has no content licence, so everything stays under
.private/ext-packs/_cache/apache/ (never in the repo). Requests are cached, resumable and
spaced at least one second apart.

Usage:
  python3 scripts/datasets/apache_fetch.py --since 2026-07-01 --new 22,8 --older 4,2
Then: python3 scripts/datasets/apache_pack.py
"""
import argparse
import email
import email.policy
import json
import mailbox
import random
import re
import urllib.parse

from common import CACHE, fetch, fetch_json, log, write

WIKI = "https://cwiki.apache.org/confluence/rest/api/content"
SPACES = {"KAFKA": {"prefix": "KIP", "list": "dev@kafka.apache.org"},
          "FLINK": {"prefix": "FLIP", "list": "dev@flink.apache.org"}}
OUT = CACHE / "apache"


def cql_search(cql, limit=50):
    results, start = [], 0
    while True:
        q = urllib.parse.urlencode({"cql": cql, "limit": limit, "start": start,
                                    "expand": "version,history"})
        page = fetch_json(f"{WIKI}/search?{q}")
        if not page:
            break
        results += page["results"]
        if page.get("size", 0) < limit:
            break
        start += limit
    return results


def proposal_number(space, title):
    m = re.match(rf"\s*{SPACES[space]['prefix']}[- ]?(\d+)", title)
    return int(m.group(1)) if m else None


def select(space, since, n_new, n_older, older_window, seed):
    pre = SPACES[space]["prefix"]
    new = [r for r in cql_search(f'space={space} and type=page and created>="{since}"')
           if proposal_number(space, r["title"])]
    new.sort(key=lambda r: r["history"]["createdDate"])
    rng = random.Random(seed)
    picked_new = new if len(new) <= n_new else sorted(rng.sample(new, n_new),
                                                      key=lambda r: r["history"]["createdDate"])
    lo, hi = older_window
    old = [r for r in cql_search(f'space={space} and type=page and title~"{pre}" and '
                                 f'created>="{lo}" and created<"{hi}"')
           if proposal_number(space, r["title"])]
    picked_old = rng.sample(old, min(n_older, len(old)))
    log(f"{space}: {len(new)} new proposals (picked {len(picked_new)}), "
        f"{len(old)} older (picked {len(picked_old)})")
    return [(r, "new") for r in picked_new] + [(r, "older") for r in picked_old]


def fetch_page(pid, max_versions):
    cur = fetch_json(f"{WIKI}/{pid}?expand=body.storage,version,history,ancestors")
    n = cur["version"]["number"]
    wanted = sorted({1, n, *[round(1 + i * (n - 1) / max(1, max_versions - 1))
                              for i in range(max_versions)]}) if n > 1 else [1]
    versions = {}
    for v in wanted:
        if v == n:
            versions[v] = cur
            continue
        old = fetch_json(f"{WIKI}/{pid}?status=historical&version={v}&expand=body.storage,version")
        if old:
            versions[v] = old
    comments = fetch_json(f"{WIKI}/{pid}/child/comment?expand=body.storage,version&limit=50")
    return cur, versions, (comments or {}).get("results", [])


def months_between(start, end):
    y, m = int(start[:4]), int(start[5:7])
    ey, em = int(end[:4]), int(end[5:7])
    out = []
    while (y, m) <= (ey, em):
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def add_months(ym, k):
    y, m = int(ym[:4]), int(ym[5:7]) - 1 + k
    return f"{y + m // 12:04d}-{m % 12 + 1:02d}"


def message_text(msg):
    try:
        part = msg.get_body(preferencelist=("plain",))
        text = part.get_content() if part else ""
    except (LookupError, KeyError, ValueError):
        text = ""
    keep = []
    for line in text.splitlines():
        if re.match(r"^\s*On .{5,120}wrote:\s*$", line) or line.startswith("-----Original"):
            break
        if not line.startswith(">"):
            keep.append(line)
    return "\n".join(keep).strip()[:6000]


def mail_threads(listaddr, months, numbers, prefix):
    """Messages per proposal number from monthly mbox archives."""
    local, domain = listaddr.split("@")
    found = {n: [] for n in numbers}
    pat = re.compile(rf"\b{prefix}[- ]?(\d+)\b", re.I)
    for ym in months:
        url = (f"https://lists.apache.org/api/mbox.lua?list={local}&domain={domain}&d={ym}")
        data = fetch(url, binary=True)
        if not data:
            continue
        path = OUT / "mbox" / f"{local}.{domain}.{ym}.mbox"
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_bytes(data)
        for msg in mailbox.mbox(str(path), factory=lambda f: email.message_from_binary_file(
                f, policy=email.policy.default)):
            try:
                subject = str(msg.get("subject", ""))
            except (ValueError, TypeError):
                continue
            m = pat.search(subject)
            if not m or int(m.group(1)) not in found:
                continue
            kind = next((k for k in ("RESULT", "VOTE", "DISCUSS") if k in subject.upper()), "OTHER")
            found[int(m.group(1))].append({
                "kind": kind, "subject": re.sub(r"\s+", " ", subject).strip(),
                "from": re.sub(r"\s*<.*?>|\s+via \w+", "", str(msg.get("from", ""))).strip(' "'),
                "date": str(msg.get("date", "")), "message_id": str(msg.get("message-id", "")),
                "in_reply_to": str(msg.get("in-reply-to", "")), "body": message_text(msg)})
    return found


def fetch_jira(keys):
    out = {}
    for key in keys:
        fields = "summary,status,assignee,reporter,created,updated,fixVersions,resolution,description"
        out[key] = fetch_json(f"https://issues.apache.org/jira/rest/api/2/issue/{key}?fields={fields}")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--since", default="2026-07-01")
    ap.add_argument("--new", default="22,8", help="new proposals per space: KAFKA,FLINK")
    ap.add_argument("--older", default="4,2", help="older sample per space: KAFKA,FLINK")
    ap.add_argument("--older-window", default="2024-07-01,2025-07-01")
    ap.add_argument("--max-versions", type=int, default=3)
    ap.add_argument("--today", default="2026-11-15")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    new_counts = [int(x) for x in args.new.split(",")]
    old_counts = [int(x) for x in args.older.split(",")]
    selection = []
    for i, (space, conf) in enumerate(SPACES.items()):
        picked = select(space, args.since, new_counts[i], old_counts[i],
                        args.older_window.split(","), args.seed)
        months = set()
        entries = []
        for r, slice_ in picked:
            pid, created = r["id"], r["history"]["createdDate"][:10]
            log(f"  {space} {r['title'][:70]}")
            cur, versions, comments = fetch_page(pid, args.max_versions)
            write(OUT / "pages" / f"{pid}.json", json.dumps(
                {"current": cur, "versions": versions, "comments": comments}))
            body = cur["body"]["storage"]["value"]
            keys = sorted(set(re.findall(rf"\b{space}-\d+\b", body)))[:2]
            jira = fetch_jira(keys)
            write(OUT / "jira" / f"{pid}.json", json.dumps(jira))
            end = args.today[:7] if slice_ == "new" else add_months(created[:7], 3)
            months.update(months_between(created[:7], min(end, args.today[:7])))
            entries.append({"space": space, "id": pid, "title": r["title"], "slice": slice_,
                            "number": proposal_number(space, r["title"]), "created": created,
                            "version": cur["version"]["number"],
                            "versions_fetched": sorted(int(v) for v in versions),
                            "creator": cur["history"]["createdBy"].get("displayName", ""),
                            "ancestors": [a["title"] for a in cur.get("ancestors", [])],
                            "jira": keys})
        threads = mail_threads(conf["list"], sorted(months), [e["number"] for e in entries],
                               conf["prefix"])
        for e in entries:
            write(OUT / "threads" / f"{e['id']}.json", json.dumps(threads[e["number"]]))
            e["mail_counts"] = {k: sum(1 for m in threads[e["number"]] if m["kind"] == k)
                                for k in ("DISCUSS", "VOTE", "RESULT")}
        selection += entries
    write(OUT / "selection.json", json.dumps(selection, indent=1))
    log(f"selection: {len(selection)} proposals -> {OUT / 'selection.json'}")


if __name__ == "__main__":
    main()
