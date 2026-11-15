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


if __name__ == "__main__":
    unittest.main()
