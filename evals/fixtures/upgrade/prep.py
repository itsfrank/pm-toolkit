#!/usr/bin/env python3
"""Build the git state for an upgrade case: an installed workspace with the PM's own changes,
and a newer toolkit release unzipped at .pm-toolkit/new/ (plus .pm-toolkit/old/ for the
pre-branch case). The new release is the kit under test with a few upstream edits.

  python3 evals/fixtures/upgrade/prep.py WORKSPACE KIT both-edited|local-files|no-branch
"""
import json
import pathlib
import re
import shutil
import subprocess
import sys

ws, kit, scenario = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3]
WIKI_PY = kit / "plugin" / "workspace" / "tools" / "wiki.py"


def git(*cmd):
    subprocess.run(["git", "-C", str(ws), *cmd], check=True, capture_output=True)


def edit(path, old, new):
    text = path.read_text(encoding="utf-8")
    assert old in text, f"{path}: anchor not found: {old!r}"
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def release(dest):
    shutil.copytree(kit / "plugin", dest / "plugin", ignore=shutil.ignore_patterns("__pycache__"))
    return dest / "plugin"


version = json.loads((kit / "plugin" / ".claude-plugin" / "plugin.json").read_text())["version"]
major, minor = re.match(r"(\d+)\.(\d+)", version).groups()
new_version = f"{major}.{int(minor) + 1}.0"

# Installed state: copy mode, every skill including setup, version marker.
for skill in (kit / "plugin" / "skills").iterdir():
    if skill.is_dir() and not (ws / ".claude" / "skills" / skill.name).exists():
        shutil.copytree(skill, ws / ".claude" / "skills" / skill.name)
for f in ("AGENTS.md", "CLAUDE.md"):
    if not (ws / f).exists():
        shutil.copy(kit / "plugin" / "workspace" / f, ws / f)
(ws / ".pm-toolkit-version").write_text(f"{version} 2026-10-01\n")
subprocess.run(["git", "init", "-q", "-b", "main", str(ws)], check=True)
git("config", "user.name", "Kestrel PM")
git("config", "user.email", "pm@kestrel.example")
(ws / ".git" / "info" / "exclude").write_text(".pm-toolkit/\n__pycache__/\n")
git("add", "-A")
git("commit", "-q", "-m", "workspace")
if scenario != "no-branch":
    subprocess.run([sys.executable, str(WIKI_PY), "--root", str(ws), "toolkit-branch", str(kit), "--baseline"],
                   check=True, capture_output=True)

# The new release.
new = release(ws / ".pm-toolkit" / "new")
edit(new / ".claude-plugin" / "plugin.json", f'"version": "{version}"', f'"version": "{new_version}"')
changes = []
prd, intake = ".claude/skills/prd/SKILL.md", ".claude/skills/intake/SKILL.md"
if scenario in ("both-edited", "no-branch"):
    edit(new / "skills" / "prd" / "SKILL.md", "Phases, beta, flags, rollback, dependencies with owners and dates.",
         "Phases with exit criteria for each, beta, flags, rollback, dependencies with owners and dates.")
    changes.append("prd: each rollout phase has exit criteria.")
if scenario == "both-edited":
    edit(new / "skills" / "prd" / "SKILL.md", "- After drafting, suggest `critical-review`.",
         "- Keep the body under six pages; move detail to an appendix.\n- After drafting, suggest `critical-review`.")
    changes.append("prd: body under six pages.")
if scenario == "local-files":
    edit(new / "workspace" / "wiki" / "lenses.md", "- Abuse cases: how could an attacker or a careless admin misuse it?",
         "- Abuse cases: how could an attacker or a careless admin misuse it?\n"
         "- Which logs or analytics would record the new data, and who can read them?")
    (new / "workspace" / "work" / "README.md").unlink()
    (new / "skills" / "release-notes").mkdir()
    (new / "skills" / "release-notes" / "SKILL.md").write_text(
        "---\nname: release-notes\ndescription: Draft release notes from a shipped PRD. Use when the user asks for "
        "release notes.\n---\n\n# Release notes\n\nRead the PRD and its sources; write `work/<slug>/release-notes.md`; "
        "cite every claim.\n")
    changes += ["lenses: probe for logs and analytics under security.", "work/README.md removed.",
                "New skill: release-notes."]
(new.parent / "CHANGELOG.md").write_text(f"# Changelog\n\n## {new_version}\n" + "".join(f"- {c}\n" for c in changes))

# The PM's own changes.
if scenario == "both-edited":
    edit(ws / prd, "Phases, beta, flags, rollback, dependencies with owners and dates.",
         "Phases, beta, flags, rollback, dependencies with owners and dates. Name the launch review gates "
         "(security, privacy, support readiness) and who signs off each.")
    (ws / "LOCAL-CHANGES.md").write_text(
        "# Local changes\n\n## 2026-10-20 prd: rollout section lists review gates\nFiles: " + prd + "\n"
        "Intent: every PRD's rollout section names the launch review gates and who signs off each.\n"
        "Why: reviewers asked for it on two PRDs in a row.\nScope: general\n")
    git("add", "-A")
    git("commit", "-q", "-m", "prd: rollout lists review gates")
    edit(ws / intake, "Keep it to two pages or less.", "Keep it to one page.")  # left uncommitted
if scenario == "local-files":
    edit(ws / "wiki" / "lenses.md", "- Does it change an existing certification scope or a public compliance statement?",
         "- Does it change an existing certification scope or a public compliance statement?\n"
         "- Does it need a data processing impact assessment? [org-checklist]")
    (ws / ".claude" / "skills" / "standup-notes").mkdir()
    (ws / ".claude" / "skills" / "standup-notes" / "SKILL.md").write_text(
        "---\nname: standup-notes\ndescription: Turn my standup scribbles into three bullets. Use when I paste "
        "standup notes.\n---\n\n# Standup notes\n\nThree bullets: done, next, blocked.\n")
    with open(ws / "AGENTS.md", "a", encoding="utf-8") as f:
        f.write("\n## Local rules\n- Write product names exactly as in `wiki/glossary.md`.\n")
    git("add", "-A")
    git("commit", "-q", "-m", "local lenses, standup skill, local rule")
if scenario == "no-branch":
    release(ws / ".pm-toolkit" / "old")
    edit(ws / prd, "- After drafting, suggest `critical-review`.",
         "- Put the decision needed and its deadline in the first line of the summary.\n"
         "- After drafting, suggest `critical-review`.")
    git("add", "-A")
    git("commit", "-q", "-m", "prd: decision first")
