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


if __name__ == "__main__":
    unittest.main()
