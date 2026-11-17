#!/usr/bin/env python3
"""Checks for the viewer (plugin/workspace/tools/viewer/): search, the Home page data, saving
documents and requests, and the launcher app. Runs a real server on a free local port against
a copy of the Kestrel sample. Standard library only.

Usage: python3 scripts/test_viewer.py
"""
import http.server
import json
import os
import pathlib
import plistlib
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOLS = ROOT / "plugin" / "workspace" / "tools"
sys.path.insert(0, str(TOOLS / "viewer"))
os.environ["PM_TODAY"] = "2026-10-06"
import serve  # noqa: E402


class Viewer(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ws = pathlib.Path(self.tmp.name).resolve() / "ws"
        shutil.copytree(ROOT / "samples" / "kestrel", self.ws)
        shutil.copytree(TOOLS, self.ws / "tools")
        serve.ROOT = self.ws
        serve.INDEX = serve.searchtools.Index()
        self.server = serve.SERVER = http.server.ThreadingHTTPServer(("127.0.0.1", 0), serve.Handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.tmp.cleanup()

    def call(self, path, body=None, headers=None, method=None):
        data = json.dumps(body).encode() if isinstance(body, (dict, list)) else body
        head = {"X-PM-Viewer": "1"} if data is not None or method == "POST" else {}
        head.update(headers or {})
        req = urllib.request.Request(self.url + path, data=data if data is not None else (b"" if method else None),
                                     headers=head, method=method)
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def search(self, q):
        return self.call("/api/search?q=" + urllib.parse.quote(q))[1]

    def paths(self, q):
        return [h["path"] for h in self.search(q)["hits"]]

    # search
    def test_search_ranks_marks_and_stems(self):
        r = self.search("residency")
        self.assertTrue(r["hits"])
        self.assertIn("\x01", r["hits"][0]["lines"][0]["text"])
        self.assertGreater(r["hits"][0]["lines"][0]["line"], 0)
        self.assertTrue(r["hits"][0]["lines"][0]["best"])
        kinds = {h["kind"] for h in r["hits"]}
        self.assertTrue({"pages", "sources", "originals"} <= kinds, kinds)
        page = next(h for h in r["hits"] if h["kind"] == "pages")
        self.assertTrue(page["type"] and page["status"])
        many = next(h for h in self.search("warehouse")["hits"] if h["matches"] > 3)
        self.assertEqual(sum(l["best"] for l in many["lines"]), 3, "three lines show; the rest unfold")
        self.assertEqual(len(many["lines"]), many["matches"])
        (self.ws / "wiki/pages/topics/stems.md").write_text("# Stems\n\nOne quokka policy.\n")
        self.assertEqual(self.paths("quokkas policies"), ["wiki/pages/topics/stems.md"], "plurals find the singular")
        self.assertTrue(self.paths("resid"), "a word being typed matches as a prefix")

    def test_search_uses_glossary_synonyms(self):
        (self.ws / "wiki/pages/topics/only-nickname.md").write_text("# Nickname\n\nOnly the ingest queue is named here.\n")
        self.assertIn("wiki/pages/topics/only-nickname.md", self.paths("spool"))

    def test_search_retries_typos_then_any_word(self):
        r = self.search("wharehouse")
        self.assertEqual(r["corrected"], "warehouse")
        self.assertTrue(r["hits"])
        r = self.search("residency zzzzqqq")
        self.assertTrue(r["any"] and r["hits"])
        self.assertEqual(self.search("zzzzqqq")["hits"], [])
        self.assertEqual(self.search('"); drop')["hits"], self.search("drop")["hits"])

    def test_search_sees_new_files_and_text_originals(self):
        self.assertEqual(self.paths("quokkaword"), [])
        (self.ws / "wiki/raw/2026-10-06-export.txt").write_text("a quokkaword in a text export\n")
        self.assertEqual(self.paths("quokkaword"), ["wiki/raw/2026-10-06-export.txt"])

    # guards
    def test_posts_need_the_viewer_header_and_a_local_host(self):
        req = urllib.request.Request(self.url + "/api/notes", data=b'{"kind":"request","text":"x"}')
        with self.assertRaises(urllib.error.HTTPError) as e:
            urllib.request.urlopen(req, timeout=10)
        self.assertEqual(e.exception.code, 403)
        self.assertEqual(self.call("/api/tree", headers={"Host": "evil.example:80"})[0], 403)
        self.assertFalse((self.ws / "wiki/notes.jsonl").exists())

    # capture
    def test_capture_saves_a_new_raw_file_with_a_draft_card_and_never_overwrites(self):
        name = urllib.parse.quote("../../Pricing notes Q4.TXT")
        code, a = self.call("/api/capture", b"zebrafish pricing tiers", {"X-Filename": name})
        self.assertEqual(code, 201)
        self.assertEqual(a["path"], "wiki/raw/2026-10-06-pricing-notes-q4.txt")
        code, b = self.call("/api/capture", b"second file", {"X-Filename": name})
        self.assertEqual(b["path"], "wiki/raw/2026-10-06-pricing-notes-q4-2.txt")
        self.assertEqual((self.ws / a["path"]).read_text(), "zebrafish pricing tiers")
        card = (self.ws / "wiki/sources" / f"{a['card']}.md").read_text()
        self.assertIn("origin: raw/2026-10-06-pricing-notes-q4.txt", card)
        self.assertNotEqual(a["card"], b["card"])
        self.assertEqual(self.paths("zebrafish"), [a["path"]])
        home = self.call("/api/home")[1]
        self.assertEqual([c["id"] for c in home["status"]["to_ingest"]], [a["card"], b["card"]])
        out = subprocess.run([sys.executable, "tools/wiki.py", "status"], cwd=self.ws, capture_output=True, text=True)
        self.assertIn("Saved documents waiting for wiki-ingest: 2", out.stdout)

    def test_capture_pasted_text_and_size_limit(self):
        code, r = self.call("/api/capture", {"title": "Call with Halvard", "text": "They asked about SSO."})
        self.assertEqual(r["path"], "wiki/raw/2026-10-06-call-with-halvard.md")
        self.assertEqual((self.ws / r["path"]).read_text(), "They asked about SSO.\n")
        self.assertEqual(self.call("/api/capture", {"title": "", "text": "x"})[1]["path"],
                         "wiki/raw/2026-10-06-pasted-text.md")
        self.assertEqual(self.call("/api/capture", {"title": "empty", "text": " "})[0], 400)
        req = urllib.request.Request(self.url + "/api/capture", data=b"x", method="POST", headers={
            "X-PM-Viewer": "1", "X-Filename": "big.bin", "Content-Length": str(serve.MAX_UPLOAD + 1)})
        with self.assertRaises((urllib.error.HTTPError, OSError)):
            urllib.request.urlopen(req, timeout=10)

    # requests and replies
    def test_request_notes_and_replies_reach_wiki_notes(self):
        code, note = self.call("/api/notes", {"kind": "request", "text": "Compare Orbit and Kestrel hosting."})
        self.assertEqual((code, note["file"], note["kind"]), (201, "", "request"))
        run = lambda *a: subprocess.run([sys.executable, "tools/wiki.py", *a], cwd=self.ws, capture_output=True, text=True).stdout
        self.assertIn("request (no page)", run("notes"))
        self.assertEqual(self.call("/api/home")[1]["queued"][0]["text"], "Compare Orbit and Kestrel hosting.")
        run("note-status", note["id"], "needs-info", "--resolution", "Which Orbit plan?")
        home = self.call("/api/home")[1]
        self.assertEqual(home["status"]["needs_info"][0]["needs"], "Which Orbit plan?")
        self.assertEqual(self.call("/api/reply", {"id": "N-nope", "text": "x"})[0], 404)
        self.assertEqual(self.call("/api/reply", {"id": note["id"], "text": "The Team plan."})[0], 201)
        home = self.call("/api/home")[1]
        self.assertEqual(home["status"]["needs_info"], [])
        self.assertEqual(home["queued"][0]["replies"], ["The Team plan."])

    def test_page_notes_still_need_a_file_and_a_quote(self):
        self.assertEqual(self.call("/api/notes", {"file": "wiki/INDEX.md", "text": "x"})[0], 400)
        code, note = self.call("/api/notes", {"file": "wiki/INDEX.md", "quote": {"exact": "Wiki"}, "text": "x"})
        self.assertEqual((code, note["file"]), (201, "wiki/INDEX.md"))

    def test_home_lists_what_lint_and_due_find(self):
        home = self.call("/api/home")[1]
        self.assertNotIn("error", home)
        for key in ("status", "queued", "due", "conflicts", "uncited"):
            self.assertIn(key, home)
        self.assertEqual(len(home["due"]), home["status"]["sources_due"])

    def test_stop_ends_the_server(self):
        self.assertEqual(self.call("/api/stop", method="POST")[0], 200)
        self.thread.join(5)
        self.assertFalse(self.thread.is_alive())

    # launcher
    @unittest.skipUnless(sys.platform == "darwin", "the launcher app is for macOS")
    def test_install_app_writes_a_launcher_for_this_workspace(self):
        apps = pathlib.Path(self.tmp.name) / "Applications"
        run = lambda *a: subprocess.run([sys.executable, "tools/viewer/serve.py", "--install-app", "--app-dir", str(apps), *a],
                                        cwd=self.ws, capture_output=True, text=True)
        self.assertEqual(run().returncode, 0)
        app = apps / "PM Wiki.app" / "Contents"
        self.assertEqual(plistlib.loads((app / "Info.plist").read_bytes())["CFBundleExecutable"], "wiki")
        script = app / "MacOS" / "wiki"
        self.assertTrue(os.access(script, os.X_OK))
        self.assertIn(str(self.ws), script.read_text())
        self.assertEqual(subprocess.run(["sh", "-n", str(script)]).returncode, 0)
        self.assertEqual(run().returncode, 0, "installing again replaces our own launcher")
        other = apps / "Notes.app" / "Contents"
        other.mkdir(parents=True)
        (other / "Info.plist").write_bytes(plistlib.dumps({"CFBundleIdentifier": "com.example.notes"}))
        self.assertEqual(run("--app-name", "Notes").returncode, 1)


if __name__ == "__main__":
    unittest.main()
