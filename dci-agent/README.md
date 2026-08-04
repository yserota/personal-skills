# DCI Agent

Local skill-driven pipeline to calculate Demand-to-Capacity Index (DCI) per writer and publish results to dashboards.

## What It Does

- Validates input CSV rows against `config/input_schema.yaml`.
- Calculates writer-level DCI from `config/dci_formula.yaml`.
- Produces canonical outputs:
  - `out/dci_writer_scores.csv`
  - `out/rejected_rows.csv`
  - `out/run_summary.json`
  - `out/run.log`
- Optionally publishes to Google Sheets (`dci_writer_scores` + `run_audit_log` tabs).

## Project Layout

- `dci_agent/`: reusable pipeline package.
- `scripts/`: command-line entry points.
- `config/`: schema and formula definitions.
- `.cursor/skills/dci-run-dashboard/SKILL.md`: full Jira → DCI → dashboard skill (invoke explicitly).
- `tests/`: fixtures + unit tests.

## Setup

```powershell
python -m pip install -e .
```

If you only need local CSV outputs and not Google Sheets, `PyYAML` is the only required runtime dependency.

## Input Contract

Required columns:

- `writer_id`
- `writer_name`
- `period_start` (`YYYY-MM-DD`)
- `period_end` (`YYYY-MM-DD`)
- `incoming_demand` (StartWork-based inflow)
- `resolved_count` (FinishWork-based outflow)
- `active_cycle_days`

Optional enrichment columns:

- `intake_count` (Created-based inflow)
- `avg_queue_lag_days` (average StartWork - Created)
- `pod`, `team`, `work_type`, `manual_vs_ai_flag`

## Dual Metrics Model

The pipeline reports two complementary views per writer:

| Metric | Meaning | Source |
|---|---|---|
| `operational_dci` | Execution load vs completed work | StartWork / FinishWork |
| `intake_dci` | Backlog intake pressure vs completed work | Created / FinishWork |
| `backlog_pressure` | Created minus started in window | Created - StartWork |
| `avg_queue_lag_days` | Wait time before work starts | StartWork - Created |

`dci` is kept as an alias of `operational_dci` for backward compatibility.

## Writer-to-Manager Mapping

Manager is not tracked in Jira, so maintain a local lookup file:

- Default path: `config/writer_manager_map.csv`

Required columns:

- `manager_name`
- at least one of: `writer_id`, `writer_name`

Optional columns:

- `manager_id`, `pod`, `team`

Example:

```csv
writer_id,writer_name,manager_name,manager_id,pod,team
matt_thies,Matt Thies,Adam Christensen,adam_christensen,Pod 1,Execution
rick_fox,Rick Fox,Danielle Biber,danielle_biber,Pod 2,Execution
```

The pipeline joins this file automatically (or via `--manager-map`). Unmapped writers are listed in `run_summary.json` under `unmapped_writers`.

## Raw Jira Input (automatic transform)

If your source file is a raw Jira export with headers like:

- `Issue Type`, `Key`, `Status`, `Summary`, `Assignee`, `Assigned Technical Writer`, `Story Points`, `Sprint`, `StartWork`, `FinishWork`
- Optional: `Created` (required for intake-health metrics)

DCI windowing uses **StartWork** (operational inflow), **FinishWork** (outflow), and **Created** (intake health).

Recommended JQL (operational + intake health) for **Q1-26** (`2026-01-01` to `2026-03-31`):

```jql
project in (DOC, DOCS)
AND (
  "StartWork" >= "2026-01-01" AND "StartWork" <= "2026-03-31"
  OR "FinishWork" >= "2026-01-01" AND "FinishWork" <= "2026-03-31"
  OR created >= "2026-01-01" AND created <= "2026-03-31"
)
ORDER BY "Assigned Technical Writer", "StartWork" ASC
```

```powershell
python scripts/transform_jira_to_dci_input.py `
  --jira-input "C:\path\to\jira-export.csv" `
  --period-start 2026-01-01 `
  --period-end 2026-03-31 `
  --output-csv data/input.from_jira.csv
```

Then run the DCI pipeline:

```powershell
python scripts/run_pipeline.py --input-csv data/input.from_jira.csv --publish-target none
```

## Run Commands

Validate input:

```powershell
python scripts/validate_input.py --input-csv data/input.csv
```

Calculate only (no publish):

```powershell
python scripts/run_pipeline.py --input-csv data/input.csv --publish-target none
```

Calculate + publish to Google Sheets:

```powershell
$env:DCI_PUBLISH_TARGET = "google_sheets"
$env:DCI_GOOGLE_SHEET_ID = "<sheet_id>"
$env:DCI_GOOGLE_SERVICE_ACCOUNT_JSON_PATH = "C:\\path\\to\\service-account.json"
python scripts/run_pipeline.py --input-csv data/input.csv --publish-target google_sheets
```

## Windows Task Scheduler (daily run example)

Program/script:

- `python`

Arguments:

- `scripts/run_pipeline.py --input-csv data/input.csv --publish-target none`

Start in:

- `C:\Users\<your-username>\Documents\Cursor-AI\dci-agent`

If using Google Sheets, configure required env vars for the scheduled task user profile.

## Testing

```powershell
python -m unittest discover -s tests -p "test_*.py"
```
