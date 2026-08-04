---
name: dci-fetch-jira
description: Pull Jira DOC/DOCS tickets via policy-broker MCP (jira_search) for the DCI pipeline, convert to CSV, and optionally chain into dci-run-dashboard. Use when the user asks to fetch Jira for DCI, pull tickets, refresh the Jira export, or run DCI without a manual CSV export.
---

# DCI Fetch Jira (MCP)

## Purpose

Replace manual Jira CSV exports with an MCP-driven fetch that produces a CSV compatible with [`transform_jira_export`](../../dci_agent/jira_transform.py), then optionally runs the DCI dashboard pipeline.

## When to use

- User says: fetch Jira for DCI, pull Jira tickets, refresh Jira export, get tickets from Jira.
- User wants to run DCI but has no `jira-export.csv`.
- User invokes `dci-run-dashboard` without an export file — run this skill first.

## Prerequisites

1. **Repo root:** `dci-agent`
2. **MCP server:** `policy-broker` with `jira_search` enabled in Cursor (Settings → MCP) for this workspace.
3. **Python package:** `python -m pip install -e .` from repo root.

Smoke test before fetching:

```
jira_search(jql="project = DOC ORDER BY created DESC", limit=1)
```

If this fails, stop and tell the user to enable policy-broker MCP. Do not invent ticket data.

---

## Step 1 — Ask for the reporting window (required)

**Always ask the user for both dates before calling `jira_search`.** Do not guess or reuse `.env` defaults unless the user explicitly confirms them.

Ask:

> What **start date** and **end date** should I use for the Jira query? (Format: `YYYY-MM-DD`, e.g. `2026-01-01` to `2026-06-30`)

If the user gives only one date, ask for the other. If they give a quarter label (e.g. "Q1 2026"), confirm the exact range:

| Label | Start | End |
|-------|-------|-----|
| Q1 2026 | 2026-01-01 | 2026-03-31 |
| Q2 2026 | 2026-04-01 | 2026-06-30 |
| Q3 2026 | 2026-07-01 | 2026-09-30 |
| Q4 2026 | 2026-10-01 | 2026-12-31 |
| H1 2026 | 2026-01-01 | 2026-06-30 |
| H2 2026 | 2026-07-01 | 2026-12-31 |

Validate: `period_end >= period_start`. Echo the chosen window back to the user before proceeding.

---

## Step 1b — Ask for team scope (required)

**Always ask which teams, pods, or managers to include before fetching.** Default is all teams if the user says "all" or doesn't specify.

Ask:

> Which teams should be included? Reply with **All** to include all writers, or pick one or more from:
>
> | Scope type | Options |
> |------------|---------|
> | Pod | Pod 1, Pod 2, SOH |
> | Team | Execution, Standards |
> | Manager | Adam Christensen, Danielle Biber, Vita Gilin |
>
> You can mix types (e.g. "Pod 1 and Pod 2" or "Execution only").

Echo the confirmed scope before fetching, e.g.:
> Reporting window: **2026-04-01 to 2026-06-30** · Scope: **Pod 1, Pod 2** (Execution team)

Store the confirmed scope — it will be passed to `run_dci_dashboard.py` in Step 5.

---

## Step 2 — Build JQL

Field mapping and JQL template live in [`config/jira_mcp_fields.yaml`](../../config/jira_mcp_fields.yaml).

Print JQL for verification (optional):

```powershell
python scripts/jira_mcp_batches_to_csv.py `
  --period-start 2026-01-01 `
  --period-end 2026-06-30 `
  --print-jql-only
```

---

## Step 3 — Paginated `jira_search`

Call `jira_search` on server **policy-broker** with:

| Parameter | Value |
|-----------|-------|
| `jql` | From Step 2 |
| `fields` | `summary,status,issuetype,assignee,created,customfield_12258,customfield_12259,customfield_16126,customfield_21925,customfield_10128,customfield_10020,updated,resolutiondate,labels,customfield_10014` |
| `limit` | `50` (max) |
| `start_at` | `0`, then `50`, `100`, … until no more issues |

**Field reference:**

| Field param | CSV column | Notes |
|-------------|-----------|-------|
| `customfield_10128` | `Story Points` | Numeric; missing/invalid → blank (defaults to 1.0 weight in DCI) |
| `customfield_10020` | `Sprint` | Array of sprint objects; active sprint name is extracted, or last sprint if none active |
| `updated` | `Updated` | Last-updated date (YYYY-MM-DD) |
| `resolutiondate` | `Resolved` | Resolution/close date (YYYY-MM-DD) |
| `labels` | `Labels` | Multi-value list joined with `"; "` |
| `customfield_10014` | `Epic Link` | Epic issue key (e.g. `DOC-123`). After a smoke-test fetch, inspect one raw `batch_0001.json` and confirm the epic key appears under `customfield_10014`. If not, find the correct field ID and update `config/jira_mcp_fields.yaml`. |

**Pagination loop:**

1. Call `jira_search` with current `start_at`.
2. Save the raw JSON array to `tmp/jira_batches/batch_NNNN.json` (zero-padded, e.g. `batch_0001.json`).
3. If fewer than 50 issues returned, stop.
4. Otherwise increment `start_at` by 50 and repeat.

Report progress: `Fetched page N (issues so far: X)`.

Create `tmp/jira_batches/` if it does not exist. Clear old batch files in that folder before a new fetch unless the user asks to append.

---

## Step 4 — Convert batches to CSV

```powershell
python scripts/jira_mcp_batches_to_csv.py `
  --batch-dir tmp/jira_batches `
  --output-csv "../jira-export-{period-label}.csv" `
  --summary out/jira_fetch_summary.json
```

Use a descriptive `{period-label}` (e.g. `h1-2026`, `q2-2026`).

Confirm `out/jira_fetch_summary.json`:

- `issues_written` — total tickets in CSV
- `issues_missing_writer` — rows with no Assignee and no Assigned Technical Writer (will be skipped by DCI transform)

---

## Step 5 — Chain to DCI dashboard (if requested)

Pass the **same** `period-start`, `period-end`, and scope flags confirmed in Steps 1 and 1b.

```powershell
python scripts/run_dci_dashboard.py `
  --jira-input "../jira-export-h1-2026.csv" `
  --period-start 2026-01-01 `
  --period-end 2026-06-30 `
  --output-dir out/h1-2026
```

If the user selected a specific scope, append the appropriate flag(s):

| User selection | Flag to add |
|----------------|-------------|
| Pod 1 only | `--pods "Pod 1"` |
| Pod 1 and Pod 2 | `--pods "Pod 1,Pod 2"` |
| Execution team | `--teams "Execution"` |
| Adam Christensen's group | `--managers "Adam Christensen"` |
| All | (no flag — omit for full roster) |

Then follow [`dci-run-dashboard`](../dci-run-dashboard/SKILL.md) for manifest and headline metrics.

---

## Agent workflow checklist

1. Ask user for **start date** and **end date** (required — do not skip).
2. Ask user for **team scope** (required — default to "All" only if user explicitly says so).
3. Echo confirmed window and scope before any Jira call.
4. Smoke-test `jira_search` (1 issue).
5. Paginate fetch → `tmp/jira_batches/batch_*.json`.
6. Run `jira_mcp_batches_to_csv.py`.
7. Report `issues_written` and `issues_missing_writer`.
8. If user wants DCI scores → `run_dci_dashboard.py` with matching period and scope flags.

Do **not** commit batch JSON, CSV exports, or output unless the user asks.

---

## Failure rules

| Failure | Action |
|---------|--------|
| MCP not available | Stop; instruct user to enable policy-broker |
| User did not provide dates | Ask before any fetch |
| User did not specify scope | Confirm "All teams?" before proceeding |
| `issues_missing_writer` high | Report count; suggest Jira hygiene on Assignee / ATW fields |
| Empty batch dir after fetch | Re-check JQL and date range with user |
| DCI `skipped_rows` | Compare CSV to manual export; verify custom field IDs in `jira_mcp_fields.yaml` |

---

## CSV columns produced

`Key`, `Issue Type`, `Status`, `Summary`, `Assignee`, `Assigned Technical Writer`, `Story Points`, `StartWork`, `FinishWork`, `Created`, `TW-AI Usage`, `Sprint`, `Updated`, `Resolved`, `Labels`, `Epic Link`

Multi-value fields (`TW-AI Usage`, `Labels`) are joined with `; `.  
`Story Points` → numeric string; blank if missing (DCI pipeline defaults to weight 1.0).  
`Sprint` → active sprint name (or last sprint if none active); blank if tickets have no sprint.  
`Updated` / `Resolved` → YYYY-MM-DD; blank if not set.  
`Epic Link` → epic issue key string (e.g. `DOC-123`); blank if not linked.

---

## Related files

| File | Purpose |
|------|---------|
| [`config/jira_mcp_fields.yaml`](../../config/jira_mcp_fields.yaml) | JQL template + custom field IDs |
| [`scripts/jira_mcp_batches_to_csv.py`](../../scripts/jira_mcp_batches_to_csv.py) | Batch JSON → CSV |
| [`dci_agent/jira_mcp_csv.py`](../../dci_agent/jira_mcp_csv.py) | Conversion logic |
| [`dci-run-dashboard`](../dci-run-dashboard/SKILL.md) | Score + dashboard after fetch |
