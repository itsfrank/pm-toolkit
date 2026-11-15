#!/usr/bin/env python3
"""Run eval cases headlessly with the Claude Code CLI and grade them with evals/GRADER.md.

Each case runs in a fresh copy of samples/kestrel with the skills copied into
.claude/skills/, no web tools, and file edits limited to that copy. Results (output file,
transcript, verdict JSON) go to evals/results/<timestamp>/ (gitignored).

Usage:
  python3 scripts/run_evals.py                 # core cases
  python3 scripts/run_evals.py --all
  python3 scripts/run_evals.py --case rfp-halvard --case intake-eu-residency
  python3 scripts/run_evals.py --model sonnet --strong-model opus --grader-model sonnet
"""
import argparse
import concurrent.futures
import datetime
import difflib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
STRONG_SKILLS = {"coverage-review", "critical-review", "prd", "pre-prd"}
ALLOWED = ["Read", "Write", "Edit", "Glob", "Grep", "Skill", "Task",
           "Bash(ls:*)", "Bash(grep:*)", "Bash(find:*)", "Bash(cat:*)", "Bash(head:*)",
           "Bash(wc:*)", "Bash(mkdir:*)", "Bash(cp:*)", "Bash(diff:*)", "Bash(date:*)"]
DENIED = ["WebFetch", "WebSearch"]


def workspace_for(case):
    tmp = pathlib.Path(tempfile.mkdtemp(prefix=f"pmtk-{case['id']}-"))
    shutil.copytree(ROOT / "samples" / "kestrel", tmp, dirs_exist_ok=True)
    for name in ("AGENTS.md", "CLAUDE.md"):
        shutil.copy(ROOT / "plugin" / "workspace" / name, tmp / name)
    skills = tmp / ".claude" / "skills"
    for skill in (ROOT / "plugin" / "skills").iterdir():
        if skill.is_dir() and skill.name != "setup":
            shutil.copytree(skill, skills / skill.name)
    for fx in case.get("fixtures", []):
        dest = tmp / fx["to"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / fx["from"], dest)
    return tmp


def claude(prompt, cwd, model, timeout):
    cmd = ["claude", "-p", prompt, "--model", model, "--permission-mode", "acceptEdits",
           "--allowedTools", *ALLOWED, "--disallowedTools", *DENIED]
    out = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    return out.stdout + (("\n[stderr]\n" + out.stderr) if out.returncode else "")


def find_output(ws, case):
    path = ws / case["output_file"]
    if path.exists():
        return path
    # Dated work folders can differ from the case's guess; match by file name.
    candidates = sorted(ws.rglob(pathlib.Path(case["output_file"]).name),
                        key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def snapshot(ws):
    return {p: p.read_text(encoding="utf-8", errors="replace")
            for p in ws.rglob("*") if p.is_file() and ".claude" not in p.parts}


def changed_files(ws, before, out):
    parts = []
    for p in sorted(ws.rglob("*")):
        if not p.is_file() or ".claude" in p.parts or p == out:
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        if p not in before:
            parts.append(f"### NEW {p.relative_to(ws)}\n{text}")
        elif before[p] != text:
            diff = difflib.unified_diff(before[p].splitlines(), text.splitlines(), lineterm="", n=1)
            parts.append(f"### CHANGED {p.relative_to(ws)}\n```diff\n" + "\n".join(diff) + "\n```")
    deleted = [str(p.relative_to(ws)) for p in before if not p.exists()]
    if deleted:
        parts.append("### DELETED\n" + "\n".join(deleted))
    return "\n\n".join(parts) or "(none)"


def run_case(case, facts, args, outdir):
    ws = workspace_for(case)
    before = snapshot(ws)
    model = args.strong_model if case["skill"] in STRONG_SKILLS else args.model
    transcript = claude(case["prompt"], ws, model, args.timeout)
    out = find_output(ws, case)
    output = out.read_text(encoding="utf-8") if out else "(no output file produced)"
    case_dir = outdir / case["id"]
    case_dir.mkdir(parents=True)
    (case_dir / "transcript.txt").write_text(transcript, encoding="utf-8")
    (case_dir / "output.md").write_text(output, encoding="utf-8")
    changed = changed_files(ws, before, out)
    (case_dir / "changed.md").write_text(changed, encoding="utf-8")

    refs = {m.get("fact") for m in case["must_find"]} - {None}
    grader = (ROOT / "evals" / "GRADER.md").read_text(encoding="utf-8")
    prompt = (f"{grader}\n\n## Case\n```json\n{json.dumps(case, indent=2)}\n```\n\n"
              f"## Planted facts\n```json\n{json.dumps([f for f in facts if f['id'] in refs], indent=2)}\n```\n\n"
              f"## Output file ({out.relative_to(ws) if out else 'missing'})\n{output}\n\n"
              f"## Other files created or changed by the run\n{changed[:40000]}\n\n"
              f"## Final reply / transcript\n{transcript[-6000:]}\n\n"
              "Return only the JSON verdict.")
    verdict_raw = subprocess.run(["claude", "-p", prompt, "--model", args.grader_model,
                                  "--tools", ""], capture_output=True, text=True,
                                 timeout=args.timeout).stdout
    m = re.search(r"\{.*\}", verdict_raw, re.S)
    try:
        verdict = json.loads(m.group(0)) if m else {"pass": False, "notes": verdict_raw}
    except ValueError:
        verdict = {"pass": False, "notes": verdict_raw}
    verdict.update(case_id=case["id"], model=model, workspace=str(ws))
    (case_dir / "verdict.json").write_text(json.dumps(verdict, indent=2), encoding="utf-8")
    return verdict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--case", action="append", default=[])
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--strong-model", default="opus")
    ap.add_argument("--grader-model", default="sonnet")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--timeout", type=int, default=1800)
    args = ap.parse_args()

    data = json.loads((ROOT / "evals" / "cases.json").read_text(encoding="utf-8"))
    cases = [c for c in data["cases"]
             if (c["id"] in args.case) or (not args.case and (args.all or c.get("core")))]
    outdir = ROOT / "evals" / "results" / datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    outdir.mkdir(parents=True)
    with concurrent.futures.ThreadPoolExecutor(args.jobs) as pool:
        verdicts = list(pool.map(lambda c: run_case(c, data["planted_facts"], args, outdir), cases))
    (outdir / "summary.json").write_text(json.dumps(verdicts, indent=2), encoding="utf-8")
    for v in verdicts:
        print(f"{'PASS' if v.get('pass') else 'FAIL'}  {v['case_id']}  ({v['model']})  "
              f"missed={len(v.get('missed', []))} violations={len(v.get('violations', []))}")
    print(f"results: {outdir.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
