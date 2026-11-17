#!/usr/bin/env python3
"""Structural checks for pm-toolkit: skill frontmatter, JSON files, workspace template
completeness, relative markdown links, and the code rules (Python standard library only,
no external loads in browser code). Standard library only.

Usage: python3 scripts/validate.py
"""
import ast
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILLS = ROOT / "plugin" / "skills"
WORKSPACE = ROOT / "plugin" / "workspace"
REQUIRED_WORKSPACE = [
    "AGENTS.md", "CLAUDE.md", "work/README.md",
    "wiki/README.md", "wiki/INDEX.md", "wiki/glossary.md", "wiki/lenses.md",
    "wiki/review-log.md", "wiki/sources/_TEMPLATE.md", "wiki/pages/_TEMPLATE.md",
    "wiki/reports/INDEX.md", "wiki/pages/people", "wiki/CHEATSHEET.md", "wiki/catalog/README.md", "wiki/watch.md",
    "tools/prices.json", "tools/wiki.py", "tools/viewer/serve.py", "tools/design.py",
    "design/README.md", "design/INDEX.md", "design/preferences.md",
    "tools/viewer/README.md", "tools/viewer/search.py",
]
SAMPLES = ROOT / "samples"
# Convention files every sample workspace keeps identical to the template.
SHARED = ["wiki/README.md", "wiki/sources/_TEMPLATE.md", "wiki/pages/_TEMPLATE.md",
          "wiki/CHEATSHEET.md", "wiki/catalog/README.md", "design/README.md"]
EXTERNAL = re.compile(r"""(?:src|href)\s*=\s*["']\s*(?:https?:)?//|@import\s+url\(\s*["']?(?:https?:)?//"""
                      r"""|\bimport\b[^;\n]*["'](?:https?:)?//|fetch\(\s*["'](?:https?:)?//""", re.I)
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
errors = []


def published_files():
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                         cwd=ROOT, capture_output=True, text=True)
    if out.returncode == 0:
        return [ROOT / p for p in out.stdout.splitlines()]
    return [p for p in ROOT.rglob("*") if ".private" not in p.parts and ".git" not in p.parts]


def check_skills():
    for skill_dir in sorted(p for p in SKILLS.iterdir() if p.is_dir()):
        md = skill_dir / "SKILL.md"
        if not md.exists():
            errors.append(f"{skill_dir.relative_to(ROOT)}: missing SKILL.md")
            continue
        text = md.read_text(encoding="utf-8")
        m = re.match(r"---\n(.*?)\n---\n", text, re.S)
        if not m:
            errors.append(f"{md.relative_to(ROOT)}: missing frontmatter")
            continue
        fields = dict(re.findall(r"^(\w[\w-]*):\s*(.*)$", m.group(1), re.M))
        if fields.get("name") != skill_dir.name:
            errors.append(f"{md.relative_to(ROOT)}: name must equal folder name '{skill_dir.name}'")
        desc = fields.get("description", "")
        if not desc or len(desc) > 1024:
            errors.append(f"{md.relative_to(ROOT)}: description missing or over 1024 chars")


def check_json(files):
    for path in files:
        if path.suffix == ".json" and path.is_file():
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except ValueError as e:
                errors.append(f"{path.relative_to(ROOT)}: invalid JSON ({e})")


def check_workspace():
    for rel in REQUIRED_WORKSPACE:
        if not (WORKSPACE / rel).exists():
            errors.append(f"plugin/workspace/{rel}: missing")


def check_code():
    if not (ROOT / "plugin" / "MIGRATION.md").exists():
        errors.append("plugin/MIGRATION.md: missing")
    stdlib = getattr(sys, "stdlib_module_names", None)
    for path in sorted((ROOT / "plugin").rglob("*.py")):
        rel = path.relative_to(ROOT)
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, str(rel))
        except SyntaxError as e:
            errors.append(f"{rel}: syntax error ({e})")
            continue
        if stdlib is None:
            continue
        local = {p.stem for p in path.parent.parent.glob("*.py")} | {p.stem for p in path.parent.glob("*.py")}
        for node in ast.walk(tree):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else \
                [node.module] if isinstance(node, ast.ImportFrom) and node.module and not node.level else []
            for name in names:
                if name.split(".")[0] not in stdlib | local:
                    errors.append(f"{rel}: imports non-standard-library module '{name}'")
    for path in sorted((ROOT / "plugin").rglob("*")):
        if path.suffix in (".js", ".html", ".css") and EXTERNAL.search(path.read_text(encoding="utf-8")):
            errors.append(f"{path.relative_to(ROOT)}: loads an external URL")


def check_samples():
    for sample in sorted(p for p in SAMPLES.iterdir() if (p / "wiki").is_dir()):
        for rel in SHARED:
            mine, theirs = sample / rel, WORKSPACE / rel
            if not mine.exists() or mine.read_bytes() != theirs.read_bytes():
                errors.append(f"{mine.relative_to(ROOT)}: differs from plugin/workspace/{rel}; copy it over")


def check_links(files):
    for path in files:
        if path.suffix != ".md" or not path.is_file() or path.name == "_TEMPLATE.md":
            continue
        text = re.sub(r"```.*?```", "", path.read_text(encoding="utf-8"), flags=re.S)
        text = re.sub(r"`[^`\n]*`", "", text)
        for target in LINK.findall(text):
            if re.match(r"^[a-z]+:", target) or target.startswith("#"):
                continue
            rel = target.split("#")[0]
            if rel and not (path.parent / rel).exists():
                errors.append(f"{path.relative_to(ROOT)}: broken link {target}")


def main():
    files = published_files()
    check_skills()
    check_json(files)
    check_workspace()
    check_code()
    check_samples()
    check_links(files)
    for e in errors:
        print(e)
    print(f"validate: {len(files)} files, {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
