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
  and `cases` (`id`, `skill`, `core`, `prompt`, `fixtures[]`, `output_file`, `must_find[]`, `must_not[]`,
  `notes`). `must_find` items carry `critical` and, where relevant, the `fact` they test.
- `GRADER.md`: judge prompt. Returns `{case_id, pass, found, missed, violations, notes}`.

## Run one case manually
1. Copy the sample to a fresh temp directory (every case starts from a clean copy):
   ```
   T=$(mktemp -d) && cp -R samples/kestrel/. "$T" && cp plugin/workspace/AGENTS.md plugin/workspace/CLAUDE.md "$T"
   ```
   If the case has `fixtures`, copy each `from` (relative to this repo) to its `to`
   (relative to `$T`). Fixtures live in `evals/fixtures/` so the sample stays clean for demos.
2. Make the pm-toolkit skills available there (plugin installed, or copy `plugin/skills/`
   into `"$T/.claude/skills/"`).
3. Open Claude Code in `$T`, paste the case's `prompt`, and let it finish.
4. Open the case's `output_file`. Give the judge model `GRADER.md`, the case object, the
   referenced planted facts and the output. Read the JSON verdict.

## Run headlessly
`python3 scripts/run_evals.py` runs the core cases (`--all` for every case, `--case <id>` for
one), each in a fresh temp copy with no web tools, grades them with `GRADER.md` and writes
outputs, transcripts and verdicts to `evals/results/` (gitignored). By hand:
```
cd "$T"
claude -p "<case prompt>" > transcript.txt
```
Then grade `"$T/<output_file>"` (plus `transcript.txt` when the case notes ask for the final
reply) with `GRADER.md`, for example with another `claude -p` call that includes the grader
prompt, the case JSON and the output. Headless runs can't answer permission prompts; allow
file edits for the temp directory only (e.g. `--permission-mode acceptEdits`), and never
give eval runs network tools or connectors. Some cases chain skills (landscape-map runs
intake first, prd runs the whole discovery), so their outputs and dates can vary; output
folder dates in `output_file` are a guide, grade the file the run produced.

## Cost and when to run
Each case is a full agent run over about 60 files, and coverage, critical-review and prd
cases chain several skills and should use the strongest model. Expect a full suite to take
a significant number of tokens. Run the `core: true` cases (intake, landscape, coverage,
critical review, RFP, marketing check, review-log backfill, injection safety) on every model change or skill edit;
run the full suite before a release. Run each case two or three times when judging a change:
single runs are noisy.

## Adding a case
Plant the fact in the sample first (raw doc plus card, and a page only if it should be
filed), add it to `planted_facts` with every file that holds it, then write the case with
specific, checkable `must_find` items. Keep the sample fully fictional.
