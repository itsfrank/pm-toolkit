# Evals

Regression tests for the pm-toolkit skills, run against the fictional sample workspace in
`samples/kestrel/`. The sample has facts planted in specific places (some only in raw
documents, some conflicting, one deliberately undocumented, one prompt injection). Each case
in `cases.json` says which skill to run, what to tell Claude, which file it should produce,
what it must find and what it must never do. `GRADER.md` is the LLM-judge prompt that grades
a produced file.

Use them to check that a skill edit or a model change didn't make the toolkit worse at the
things that matter: finding facts that are scattered or unfiled, labeling unknowns honestly,
surfacing conflicts, not overclaiming, and ignoring instructions inside documents.

## Files
- `fixtures/`: inputs some cases copy into the workspace (a weak PRD, an email, feedback).
- `cases.json`: `planted_facts` (the gold: every planted fact and the files that hold it)
  and `cases` (`id`, `skill`, `core`, `kind` (`regression` or `capability`), `prompt`,
  `fixtures[]`, `output_file`, `must_find[]`, `must_not[]`, `notes`, optional `connector`).
  `must_find` items carry `critical` and, where relevant, the `fact` they test. An item with
  `check` (`file_exists`, `contains`, `regex`) or `log_check` (`fetched`, `not_fetched`,
  `searched_alias`) is decided by the runner, not the judges.
- `GRADER.md`: the judge prompt. Judges return a verdict and an exact quote per item.
- `tools/fake_connector.py`: a read-only fake document connector (MCP over stdio) for cases
  that test searching beyond the wiki. It logs every call; write tools are traps.

## Run one case manually
1. Copy the sample to a fresh temp directory (every case starts from a clean copy):
   ```
   T=$(mktemp -d) && cp -R samples/kestrel/. "$T" && cp plugin/workspace/AGENTS.md plugin/workspace/CLAUDE.md "$T"
   cp -R plugin/workspace/tools "$T/tools"
   ```
   If the case has `fixtures`, copy each `from` (relative to this repo) to its `to`
   (relative to `$T`). Fixtures live in `evals/fixtures/` so the sample stays clean for demos.
2. Make the pm-toolkit skills available there (plugin installed, or copy `plugin/skills/`
   into `"$T/.claude/skills/"`).
3. Open Claude Code in `$T`, paste the case's `prompt`, and let it finish.
4. Open the case's `output_file`. Give the judge model `GRADER.md`, the case object, the
   referenced planted facts and the output. Read the JSON verdict.

## Run headlessly
```
python3 scripts/run_evals.py                      # core cases, once
python3 scripts/run_evals.py --all --repeat 3     # every case, three times
python3 scripts/run_evals.py --case rfp-halvard --graders opus
python3 scripts/run_evals.py --kit ../other-checkout   # test another version's plugin/
python3 scripts/run_evals.py --arm agents-only    # ablation: none | agents-only | full
python3 scripts/run_evals.py regrade evals/results/<stamp>   # re-grade saved outputs
```
Each run gets a fresh temp copy of the sample with the skills and tools, the scenario date
(`PM_TODAY`), no web tools, no user-level settings or memory (`--setting-sources project`,
`--strict-mcp-config`) and, for `connector` cases, the fake connector. The runner records
cost and turns from `--output-format json`.

**Grading.** Two judges with pinned models (`JUDGES` in the runner) grade every run:
Claude (`claude -p`) and Codex (`codex exec`). Each `found` or `violated` verdict must quote
the output; a quote the runner can't find counts against it. When the judges disagree the
item is `disputed`, and the summary reports two pass rates with Wilson 95% intervals:
**strict** (a critical item needs both judges; a violation needs one) and **lenient** (one
judge suffices for an item; a violation needs both). The truth lies between them. Timeouts
and unparseable verdicts are errors, excluded from the rates. Results go to
`evals/results/<stamp>/` (gitignored): per run `output.md`, `changed.md`, `reply.md`,
`grade.json`, and a `summary.md`, `summary.json` and `disputes.md` for hand labeling.
Changing `GRADER.md` or a judge model changes the numbers: re-grade saved runs with
`regrade` before comparing with older results.

## Cost and when to run
Each case is a full agent run over about 60 files, and coverage, critical-review and prd
cases chain several skills and should use the strongest model. Expect a full suite to take
a significant number of tokens. Run the `core: true` cases (intake, landscape, coverage,
critical review, RFP, marketing check, review-log backfill, injection safety) on every model change or skill edit;
run the full suite before a release. Run each case two or three times when judging a change:
single runs are noisy. Use `--repeat 3` and compare intervals, not single verdicts.

## Adding a case
Plant the fact in the sample first (raw doc plus card, and a page only if it should be
filed), add it to `planted_facts` with every file that holds it, then write the case with
specific, checkable `must_find` items. Keep the sample fully fictional.
