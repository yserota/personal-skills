---
name: dci-run-dashboard
description: Run the full TW DCI + AI dashboard pipeline from a Jira CSV export—transform, score writers, build Google Sheets dashboard tabs, and optional publish. Use when the user asks to run DCI, refresh the dashboard, score writers, update roster metrics, or share DCI/AI stats with TLs or Ofrit.
---

# DCI Run Dashboard

## Purpose

One repeatable workflow for the `dci-agent` project:

1. Transform raw Jira export → normalized input (TW-AI Usage merged, roster filter applied).
2. Score writers using **story-point-weighted DCI** as the primary metric.
3. Write dashboard tab CSVs for Google Sheets / Looker Studio.
4. Optionally publish to Google Sheets.

## When to use

- User says: run DCI, refresh dashboard, score Q1, update writer metrics, rebuild dashboard tabs.
- User adds a writer to `writer_manager_map.csv` / `jira_username_map.csv` and wants scores refreshed.
- User has a new `jira-export.csv` and wants shareable TL/Ofrit outputs.
- User has no Jira export — run [`dci-fetch-jira`](../dci-fetch-jira/SKILL.md) first (asks for start/end dates and team scope, pulls via MCP).

## Prerequisites

From the **dci-agent repo root**:

```powershell
python -m pip install -e .
```

Jira export path (default): `../jira-export.csv` relative to dci-agent, or set `DCI_JIRA_INPUT`.

## Primary command (run this)

```powershell
cd C:\Users\yserota\Documents\Cursor-AI\dci-agent
python scripts/run_dci_dashboard.py `
  --period-start 2026-04-01 `
  --period-end 2026-06-30
```

### Common overrides

```powershell
python scripts/run_dci_dashboard.py `
  --jira-input "C:\Users\yserota\Documents\Cursor-AI\jira-export.csv" `
  --period-start 2026-04-01 `
  --period-end 2026-06-30 `
  --output-dir out/q2-2026
```

Scope to specific teams, pods, or managers (combine flags as needed):

```powershell
# By pod
python scripts/run_dci_dashboard.py `
  --period-start 2026-04-01 `
  --period-end 2026-06-30 `
  --pods "Pod 1,Pod 2"

# By team
python scripts/run_dci_dashboard.py `
  --period-start 2026-04-01 `
  --period-end 2026-06-30 `
  --teams "Execution"

# By manager
python scripts/run_dci_dashboard.py `
  --period-start 2026-04-01 `
  --period-end 2026-06-30 `
  --managers "Adam Christensen,Danielle Biber"
```

Re-score from existing normalized input (skip Jira transform):

```powershell
python scripts/run_dci_dashboard.py --skip-transform --input-csv data/input.from_jira.csv
```

Publish to Google Sheets (requires `.env` or env vars):

```powershell
python scripts/run_dci_dashboard.py --publish-target google_sheets
```

## Scope flags reference

| Flag | Accepts | Example |
|------|---------|---------|
| `--teams` | Comma-separated team names | `"Execution"` or `"Execution,Standards"` |
| `--pods` | Comma-separated pod names | `"Pod 1"` or `"Pod 1,Pod 2"` |
| `--managers` | Comma-separated manager names | `"Adam Christensen"` |

Valid values: Pods = `Pod 1`, `Pod 2`, `SOH` · Teams = `Execution`, `Standards` · Managers = `Adam Christensen`, `Danielle Biber`, `Vita Gilin`.

Omit all three flags to include the full roster. Scope filtering is applied **after** manager mapping, so team/pod/manager fields must be present in `writer_manager_map.csv`.

## Environment defaults (optional)

Copy `.env.example` → `.env`:

| Variable | Purpose |
|----------|---------|
| `DCI_JIRA_INPUT` | Raw Jira CSV path |
| `DCI_PERIOD_START` / `DCI_PERIOD_END` | Reporting window |
| `DCI_INPUT_CSV_PATH` | Normalized input output |
| `DCI_OUTPUT_DIR` | Default `out` |
| `DCI_MANAGER_MAP_PATH` | Writer roster + pod mapping |
| `DCI_PUBLISH_TARGET` | `none` or `google_sheets` |
| `DCI_GOOGLE_SHEET_ID` | Target spreadsheet |
| `DCI_GOOGLE_SERVICE_ACCOUNT_JSON_PATH` | Service account key JSON |

## Config files (edit before run if roster changes)

| File | Purpose |
|------|---------|
| `config/writer_manager_map.csv` | Writer → manager, pod, team |
| `config/jira_username_map.csv` | Jira username → display name |
| `config/dci_formula.yaml` | DCI + AI segmentation formulas |
| `config/input_schema.yaml` | Input validation |

### Add a writer

1. Add row to `config/writer_manager_map.csv` (`writer_id`, `writer_name`, `manager_name`, `manager_id`, `pod`, `team`).
2. Add Jira alias to `config/jira_username_map.csv` (`jira_username`, `writer_name`).
3. Re-run `python scripts/run_dci_dashboard.py`.

## Outputs (deliver to Ofrit / TLs)

After a successful run, confirm these exist:

| Path | Use |
|------|-----|
| `out/dci_writer_scores.csv` | Full metrics (all columns) |
| `out/dci_ai_impact_summary.csv` | Slim AI vs manual comparison |
| `out/DCI_AI_Impact_Analysis.md` | Narrative AI impact analysis |
| `out/dashboard/Tab0_Cover.csv` | Google Sheets — exec KPIs + insights |
| `out/dashboard/Tab1_Executive_Summary.csv` | Org + pod rollup |
| `out/dashboard/Tab2_Writer_Scorecard.csv` | TL scorecard (DCI + AI, includes SP columns) |
| `out/dashboard/Tab3_AI_Impact.csv` | AI vs manual by writer |
| `out/dashboard/Tab4_Chart_Data.csv` | Pre-shaped chart rows |
| `out/dashboard/Tab5_Metric_Definitions.csv` | Metric glossary |
| `out/dashboard/Tab6_Team_Rollup.csv` | SP-weighted DCI by team |
| `out/dashboard/Tab7_Manager_Rollup.csv` | SP-weighted DCI by manager group |
| `out/dashboard/README_Google_Sheets_Dashboard.md` | Import + chart instructions |
| `out/run_summary.json` | Run audit metadata (includes org SP DCI + coverage %) |

### Primary metric: Story-Point-Weighted DCI

**SP DCI** (`operational_dci_points` = `story_points_started ÷ story_points_finished`) is the primary complexity-adjusted metric. It accounts for ticket difficulty — a writer finishing high-complexity tickets at a sustainable pace scores correctly even if raw ticket counts look low.

**When to trust SP DCI:** it is most meaningful when `story_points_coverage_pct ≥ 70%` for a writer or group. Check `Tab2_Writer_Scorecard.csv`; writers below 70% coverage will show SP DCI but it relies heavily on the 1.0 default weight for untagged tickets. For those writers, use Ticket DCI as a cross-check.

**DCI zones (same for SP DCI and Ticket DCI):**

| Value | Zone | Meaning |
|-------|------|---------|
| > 1.0 | Backlog building | Starting more than finishing — backlog grows |
| 0.80–0.95 | Healthy runway | Sustainable throughput with a modest backlog buffer |
| 0.75–0.80 | Watch band | Marginal — monitor closely |
| < 0.75 | Backlog drain | Finishing more than starting — backlog shrinking |

After reviewing outputs, run [`dci-score-and-publish`](../dci-score-and-publish/SKILL.md) to build the interactive SP-weighted canvas dashboard with embedded metric explanations.

## Agent workflow

When the user invokes this skill:

0. **Confirm reporting period.** If the user came from `dci-fetch-jira`, echo the already-confirmed window. Otherwise ask:
   > What reporting period should I use? (e.g. Q2 2026 = 2026-04-01 to 2026-06-30)
   Validate `period_end >= period_start` before proceeding.

0b. **Confirm team scope.** Ask:
   > Which teams, pods, or managers should be included? (All, or pick from: Pod 1 · Pod 2 · SOH · Execution · Standards · Adam Christensen · Danielle Biber · Vita Gilin)
   If user says "all" or doesn't specify, use full roster (omit scope flags).

1. **No Jira CSV?** → Run [`dci-fetch-jira`](../dci-fetch-jira/SKILL.md) first. That skill **must ask the user for start date, end date, and team scope** before querying Jira.
2. **Confirm repo root** is `dci-agent` (install editable package if imports fail).
3. **Check config** if user mentioned new writers — update maps first.
4. **Run** `python scripts/run_dci_dashboard.py` with user-provided paths, dates, and scope flags.
5. **Report manifest** — print from `run_summary.json`:
   - Period and scope
   - Writer count
   - **Org SP DCI** (primary) and coverage %
   - Ticket DCI (secondary)
   - AI adoption %
6. **Summarize headline metrics** from `out/dashboard/Tab0_Cover.csv` or `DCI_AI_Impact_Analysis.md`.
7. **Remind user** to import `out/dashboard/Tab*.csv` into Google Sheets (see README) unless auto-publish is configured.

Do **not** commit config or output changes unless the user asks.

## Failure rules

- Non-zero exit from `run_dci_dashboard.py` → read `out/run.log` and report the failing step.
- `rows_rejected > 0` in `run_summary.json` → surface `out/rejected_rows.csv`.
- `unmapped_writers` non-empty → prompt to update `writer_manager_map.csv` / `jira_username_map.csv`.
- Jira export missing → run [`dci-fetch-jira`](../dci-fetch-jira/SKILL.md) or ask for path; do not guess data.
- `org_sp_coverage_pct < 70` → note in summary that SP DCI is less reliable; suggest Jira hygiene on Story Points field.
- Scope flags produce 0 writers → re-check spelling against valid values in `writer_manager_map.csv`.

## Google Sheets share steps (manual)

1. New spreadsheet: `TW DCI + AI Dashboard — [period] [scope if scoped]`
2. Import each `out/dashboard/Tab*.csv` as a new tab (comma separator).
3. Add charts from `Tab4_Chart_Data` (see dashboard README).
4. Create filter views on **Writer Scorecard** for Pod 1, Pod 2, SOH.
5. Share Viewer access with Ofrit and TLs.

## Related scripts (advanced)

- [`dci-fetch-jira`](../dci-fetch-jira/SKILL.md) — pull tickets from Jira via MCP (asks user for dates and scope)
- `scripts/jira_mcp_batches_to_csv.py` — convert MCP batch JSON to DCI CSV
- `scripts/transform_jira_to_dci_input.py` — Jira transform only
- `scripts/run_pipeline.py` — score + dashboard only
- `scripts/validate_input.py` — validate input CSV only
- `scripts/publish_google_sheet.py` — publish only

For deeper reference, see [reference.md](reference.md).
