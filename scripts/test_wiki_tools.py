#!/usr/bin/env python3
"""Unit checks for plugin/workspace/tools/wiki.py, run against a copy of the Kestrel sample.
Standard library only.

Usage: python3 scripts/test_wiki_tools.py
"""
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOLS = ROOT / "plugin" / "workspace" / "tools"


class WikiTools(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ws = pathlib.Path(self.tmp.name) / "ws"
        shutil.copytree(ROOT / "samples" / "kestrel", self.ws)
        shutil.copytree(TOOLS, self.ws / "tools")

    def tearDown(self):
        self.tmp.cleanup()

    def run_wiki(self, *args, ok=True):
        env = dict(os.environ, PM_TODAY="2026-10-06")
        out = subprocess.run([sys.executable, "tools/wiki.py", *args], cwd=self.ws, env=env,
                             capture_output=True, text=True)
        if ok:
            self.assertEqual(out.returncode, 0, out.stderr)
        return out.stdout

    def write(self, rel, text):
        path = self.ws / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def status(self):
        return json.loads(self.run_wiki("status", "--json"))

    # install and upgrade
    def test_version_matches_plugin(self):
        manifest = json.loads((ROOT / "plugin" / ".claude-plugin" / "plugin.json").read_text())
        source = (TOOLS / "wiki.py").read_text()
        self.assertIn(f'VERSION = "{manifest["version"]}"', source)

    def test_status_offers_upgrade_on_mismatch(self):
        self.assertFalse(self.status()["upgrade_pending"])  # no version file: nothing to compare
        self.write(".pm-toolkit-version", "0.0.9 2026-01-02\n")
        self.assertTrue(self.status()["upgrade_pending"])
        self.assertIn("Upgrade:", self.run_wiki("status"))
        version = re.search(r'VERSION = "([^"]+)"', (TOOLS / "wiki.py").read_text()).group(1)
        self.write(".pm-toolkit-version", f"{version} 2026-01-02\n")
        self.assertFalse(self.status()["upgrade_pending"])

    # raw-hits
    def test_raw_hits_short_terms_match_whole_words(self):
        self.write("wiki/raw/2026-10-03-neutral.md", "# Neutral memo\nThe team stayed neutral on zx-42.\n")
        self.assertNotIn("neutral.md", self.run_wiki("raw-hits", "eu"))

    def test_raw_hits_ranks_by_terms_matched_and_names_the_rest(self):
        out = self.run_wiki("raw-hits", "eu", "backups", "--files", "2")
        files = re.findall(r"^(wiki/raw/\S+)  \[", out, re.M)
        self.assertEqual(len(files), 2)
        self.assertTrue(all("(2 of the terms)" in l for l in out.splitlines() if l.startswith("wiki/raw/")))
        more = re.search(r"^\+(\d+) more files: (.+)$", out, re.M)
        self.assertTrue(more)
        self.assertEqual(int(more.group(1)), len(more.group(2).split(", ")))
        self.assertIn("2024-05-21-decision-eu-region-not-now.md", more.group(2))  # matches one term

    def test_raw_hits_uses_glossary_synonyms(self):
        self.write("wiki/raw/2026-10-03-ops.md", "# Ops\nThe Warehouse EU cut-over moved to 2027-02-01.\n")
        self.assertIn("2026-10-03-ops.md", self.run_wiki("raw-hits", "fjord"))

    def test_raw_hits_stoplist_and_skipped_files_and_pages(self):
        self.write("wiki/raw/2026-10-03-guide.pdf", "%PDF-1.4 binary")
        self.write("wiki/raw/2026-10-03-guide/part-01.md",
                   "# Guide\n<!-- p.1 -->\nIntro.\n<!-- p.7 -->\nEU backups are kept for 35 days.\n"
                   "EU support is generally whatever.\n")
        out = self.run_wiki("raw-hits", "eu", "--files", "50")
        self.assertIn("1 non-text raw file(s) not searched", out)
        self.assertRegex(out, r"  5 p\.7: \(new: .*35")
        self.assertIn("  6 p.7: (new: eu) EU support", out)  # stoplisted words aren't details

    # due, cards-from-raw, catalog-search
    def test_due_skips_superseded_cards(self):
        self.assertIn("S-0014", self.run_wiki("due"))
        card = self.ws / "wiki/sources/S-0014.md"
        card.write_text(card.read_text().replace("---\n", "---\nsuperseded_by: S-0099\n", 1))
        self.assertNotIn("S-0014", self.run_wiki("due"))

    def test_cards_from_raw_takes_origin_only_from_first_line(self):
        self.write("wiki/raw/2026-10-04-linked.md",
                   "https://wiki.example/pages/123\n# Linked page\nSee https://other.example/x.\n")
        self.write("wiki/raw/2026-10-04-mentions.md",
                   "# Call notes\n\nThey showed https://competitor.example/pricing on screen.\n")
        out = self.run_wiki("cards-from-raw", "--dry-run")
        self.assertRegex(out, r"raw/2026-10-04-linked\.md  https://wiki\.example/pages/123")
        self.assertRegex(out, r"raw/2026-10-04-mentions\.md  \(no origin url\)")

    def test_catalog_search_ties_newest_first(self):
        self.write("wiki/catalog/t.md", "# Catalog\n\n"
                   "- [ ] [Gizmo plan A](https://x.example/1) · id: 1 · modified: 2025-01-01\n"
                   "- [ ] [Gizmo plan B](https://x.example/2) · id: 2 · modified: 2026-05-01\n"
                   "- [ ] [Gizmo plan C](https://x.example/3) · id: 3 · labels: gizmo · modified: 2024-01-01\n")
        titles = re.findall(r"\] (Gizmo plan \w)", self.run_wiki("catalog-search", "gizmo"))
        self.assertEqual(titles, ["Gizmo plan C", "Gizmo plan B", "Gizmo plan A"])

    # status and notes
    def test_status_folder_types_and_review_stage(self):
        ask = "work/2026-10-05-eu-data-residency"
        self.write(f"{ask}/intake.md", "# Intake\n")
        self.write(f"{ask}/review-1.md", "# Review 1\n")
        self.write(f"{ask}/review-2.md", "# Review 2\n")
        self.write("work/2026-10-06-rfp-halvard/answers.md", "# Answers\n")
        self.write("work/2026-10-06-call-nordhavn/prep.md", "# Prep\n")
        rows = {a["folder"]: a for a in self.status()["recent_asks"]}
        self.assertEqual(rows[f"work/{ask[5:]}"]["stages"], ["intake", "critical-review (2)"])
        self.assertEqual(rows["work/2026-10-06-rfp-halvard"]["type"], "rfp")
        self.assertEqual(rows["work/2026-10-06-call-nordhavn"]["type"], "call")
        out = self.run_wiki("status")
        self.assertIn("Work (rfp): work/2026-10-06-rfp-halvard [answers]", out)
        self.assertNotIn("rfp-halvard [not started]", out)

    def test_status_no_lint_offer_on_empty_wiki(self):
        self.assertTrue(self.status()["lint_due"])
        shutil.rmtree(self.ws / "wiki" / "pages")
        for card in (self.ws / "wiki" / "sources").glob("S-*.md"):
            card.unlink()
        self.assertFalse(self.status()["lint_due"])

    def test_needs_info_notes_listed_and_reopened_by_reply(self):
        note = {"type": "note", "id": "N-1", "file": "wiki/pages/products/kestrel-collect.md",
                "quote": {"exact": "Kestrel Collect"}, "line": 1, "text": "Fetch the SDK page and add it."}
        self.write("wiki/notes.jsonl", json.dumps(note) + "\n")
        self.run_wiki("note-status", "N-1", "needs-info", "--resolution", "a fetch: confirm in chat")
        s = self.status()
        self.assertEqual(s["needs_info_notes"], 1)
        self.assertEqual(s["needs_info"][0]["needs"], "a fetch: confirm in chat")
        self.assertIn("note-reply", self.run_wiki("status"))
        self.assertNotIn("N-1", self.run_wiki("notes"))
        self.run_wiki("note-reply", "N-1", "Yes, fetch it.")
        out = self.run_wiki("notes")
        self.assertIn("N-1  [open]", out)
        self.assertIn("reply: 'Yes, fetch it.'", out)
        self.assertIn("1 note(s)", out)
        self.assertEqual(self.status()["needs_info_notes"], 0)

    # lint
    def lint(self):
        return json.loads(self.run_wiki("lint", "--json"))

    def test_lint_fix_index_adds_and_drops_keeping_curated_text(self):
        index = self.ws / "wiki/INDEX.md"
        curated = index.read_text()
        self.write("wiki/pages/products/kestrel-pulse.md",
                   "---\ntype: product\nstatus: draft\nupdated: 2026-10-01\n---\n\n# Kestrel Pulse\n\n"
                   "Real-time alerting add-on. [S-0001]\n")
        index.write_text(curated + "- [Gone](pages/topics/gone.md) (draft, 2026-01-01): removed page.\n")
        report = self.lint()
        self.assertIn("pages/topics/gone.md", sum(report.values(), []))
        out = self.run_wiki("lint", "--fix-index")
        self.assertIn("added 1 line(s), dropped 1 dead line(s)", out)
        text = index.read_text()
        self.assertNotIn("pages/topics/gone.md", text)
        products = text.split("## Products")[1].split("## ")[0]
        self.assertIn("- [Kestrel Pulse](pages/products/kestrel-pulse.md) (draft, 2026-10-01): "
                      "Real-time alerting add-on. [S-0001]", products)
        for line in curated.splitlines():
            self.assertIn(line, text)
        self.assertIn("added 0 line(s), dropped 0", self.run_wiki("lint", "--fix-index"))

    def test_lint_lists_unpromoted_reports_and_drafts_by_use(self):
        self.write("wiki/reports/2026-08-01-overlaps.md", "---\ntitle: Overlaps\nquestion: Where do plans clash?\n"
                   "as_of: 2026-08-01\nsources: [S-0004]\npromoted: no\n---\n# Overlaps\n")
        self.write("wiki/reports/2026-09-30-recent.md", "---\ntitle: Recent\nquestion: q\n"
                   "as_of: 2026-09-30\nsources: [S-0004]\npromoted: no\n---\n# Recent\n")
        self.write("work/2026-10-05-eu-data-residency/landscape.md",
                   "See [Govern](../../wiki/pages/products/kestrel-govern.md) and pages/teams/govern-team.md.\n")
        self.write("work/2026-10-05-eu-data-residency/coverage.md", "Govern: pages/products/kestrel-govern.md\n")
        report = self.lint()
        unpromoted = next(v for k, v in report.items() if k.startswith("reports not promoted"))
        self.assertEqual(unpromoted, ["wiki/reports/2026-08-01-overlaps.md: 2026-08-01"])
        drafts = next(v for k, v in report.items() if k.startswith("draft pages"))
        self.assertEqual(drafts[:2], ["pages/products/kestrel-govern.md: 2 work file(s)",
                                      "pages/teams/govern-team.md: 1 work file(s)"])

    def test_lint_lists_lenses_that_never_fired_once_there_is_history(self):
        def unfired():
            return next((v for k, v in self.lint().items() if k.startswith("lenses that never fired")), [])
        self.assertEqual(unfired(), [])  # one review-log entry is too little history
        for n in range(4):
            self.write(f"work/2026-0{n + 1}-01-ask-{n}/coverage.md",
                       "| # | Lens | Status | Finding |\n|---|---|---|---|\n"
                       "| 8 | Security and privacy | missing | no audit story |\n"
                       "| 9 | Compliance | covered | fine |\n")
        names = unfired()
        self.assertIn("9. Compliance, regulation, certification", names)
        self.assertNotIn("8. Security and privacy", names)
        self.assertNotIn("14. Support and operations", names)  # tagged in review-log.md

    # spend
    def test_spend_sums_a_ledger(self):
        run = {"type": "result", "subtype": "success", "session_id": "a", "total_cost_usd": 1.25,
               "modelUsage": {"claude-sonnet-x": {"inputTokens": 1000, "outputTokens": 200, "costUSD": 1.0},
                              "claude-haiku-x": {"inputTokens": 50, "outputTokens": 5, "costUSD": 0.25}}}
        run2 = dict(run, session_id="b", total_cost_usd=0.75,
                    modelUsage={"claude-sonnet-x": {"inputTokens": 500, "outputTokens": 100, "costUSD": 0.75}})
        self.write("work/run/ledger.jsonl", json.dumps(run) + "\nnot json\n" + json.dumps(run2) + "\n")
        (s,) = json.loads(self.run_wiki("spend", "--ledger", "work/run/ledger.jsonl", "--json"))
        self.assertEqual((s["runs"], s["usd"]), (2, 2.0))
        self.assertEqual(s["models"]["claude-sonnet-x"], {"inputTokens": 1500, "outputTokens": 300, "costUSD": 1.75})
        out = self.run_wiki("spend", "--ledger", "work/run/ledger.jsonl")
        self.assertIn("total: $2.00", out)
        self.assertNotIn("estimate", out)

    def test_spend_log_by_session_id_is_an_estimate_and_never_guesses(self):
        out = subprocess.run([sys.executable, "tools/wiki.py", "spend"], cwd=self.ws, capture_output=True, text=True)
        self.assertNotEqual(out.returncode, 0)
        config = pathlib.Path(self.tmp.name) / "config"
        msg = {"timestamp": "2026-10-06T10:00:00Z", "message": {"id": "m1", "model": "claude-sonnet-x",
               "usage": {"input_tokens": 10, "output_tokens": 5}}}
        log = config / "projects" / "-some-folder" / "sess-1.jsonl"
        log.parent.mkdir(parents=True)
        log.write_text(json.dumps(msg) + "\n" + json.dumps(msg) + "\n")
        (log.parent / "sess-2.jsonl").write_text(json.dumps(msg) + "\n")  # another session, newer
        env = dict(os.environ, CLAUDE_CONFIG_DIR=str(config))
        out = subprocess.run([sys.executable, "tools/wiki.py", "spend", "--session-id", "sess-1", "--json"],
                             cwd=self.ws, env=env, capture_output=True, text=True)
        (s,) = json.loads(out.stdout)
        self.assertEqual((s["source"], s["messages"], s["usd"]), ("estimate", 1, None))
        self.assertTrue(s["file"].endswith("sess-1.jsonl"))


if __name__ == "__main__":
    unittest.main()
