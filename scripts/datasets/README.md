# Dataset builders (maintainer tools)

Scripts that build larger eval packs than the Kestrel sample. Standard library only.
**Real data never enters the repo:** every builder writes to `.private/ext-packs/` in the
main checkout (gitignored; override with `PM_EXT_PACKS`), with an HTTP and LLM cache in
`.private/ext-packs/_cache/` and rename maps and probe questions in `_maps/`. The repo holds
only these scripts, the synthetic spec in `specs/`, and fictional fixtures.

| Script | What it does |
|---|---|
| `common.py` | Private paths, cached HTTP (at most 1 request/s), cached `claude -p` calls with a cost ledger (`_cache/llm/ledger.jsonl`), HTML to markdown, workspace seeding. |
| `apache_fetch.py` | Fetches Kafka KIP and Flink FLIP pages (new ones plus an older sample), their versions, dev-list DISCUSS/VOTE/RESULT mail and linked JIRA issues. |
| `apache_pack.py` | Renames and date-shifts that data into a pack: a partly ingested workspace, everything on the connector, gold from status fields, votes and JIRA, Opus-extracted reviewer concerns for a pilot (`needs_human_check`), plus a messy ad-hoc KB (`<pack>-messy/`) for migration rehearsals. |
| `gen_fixture.py` | Synthetic scale fixture from a seeded spec (`specs/copperline.json`, a fictional studio-booking SaaS). Tiers S (~40 docs), M (300 + a 200-page manual), L (800 + a ~1,000-page manual). |
| `validate_fixture.py` | Checks generated documents: known names and dates, gold only in its carriers, low word overlap between a planted fact and its question, no hint words. |
| `drills.py` | Small drill packs: OrgForge SILENCE (absence), WikiContradict (conflicts), LLMail-Inject payloads, GOV.UK service assessments (critical review), HERB (stale versions, unanswerables; non-commercial). Checks each licence first and skips what it can't confirm. |
| `probe.py` | Memorization probe: asks each gold question with no workspace and no tools (3 samples), judges the answers, and writes the result into the pack README. |
| `check_connector.py` | Validates a fake-connector page folder and its search expectations (used for `samples/kestrel-connector/`). |

## Pack format
```
<pack>/
  workspace/            a pm-toolkit workspace (wiki/raw, sources, pages, INDEX.md, glossary.md, work/<ask>/ask.md)
  connector/pages/      <id>.md pages for the fake connector; older versions as <id>@v<N>.md
  fixtures/             files that cases copy in (paths in a case's "fixtures" are pack-relative)
  cases.json            same schema as evals/cases.json, plus "connector" and "log_check" on items
  README.md             provenance, licence, build command, cost, contamination-probe status
```
Connector page frontmatter: `id`, `title`, `space`, `parent`, `url`, `version`, `modified`,
`access` (`ok` or `denied`), optional `author`, `labels`, `history: [1, 3]`.
`log_check` on a `must_find` or `must_not` item is one of `{"fetched": "<id>"}`,
`{"not_fetched": "<id>"}` or `{"searched_alias": "<term>"}`.

## Typical run
```
python3 scripts/datasets/apache_fetch.py --new 18,8 --older 3,1     # ~30 proposals, polite, resumable
python3 scripts/datasets/apache_pack.py --pack apache-pilot --concerns 10
python3 scripts/datasets/probe.py --pack apache-pilot
python3 scripts/datasets/gen_fixture.py --tier S                    # M and L: same command, bigger bill
python3 scripts/datasets/drills.py --n 10
python3 scripts/datasets/probe.py --pack drills-govuk               # and the other drills with gold
```
Cost so far is in the ledger: `python3 -c "import sys; sys.path.insert(0, 'scripts/datasets');
import common; print(common.ledger_total())"`.
