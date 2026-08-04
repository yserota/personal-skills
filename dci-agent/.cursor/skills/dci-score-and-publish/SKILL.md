---
name: dci-score-and-publish
description: Build the SP-weighted DCI canvas dashboard and open it in Cursor after the DCI pipeline has run. Use when the user says "build canvas", "publish dashboard", "open DCI canvas", "show me the dashboard", or after running dci-run-dashboard.
---

# DCI Score and Publish — Canvas Dashboard

## Purpose

After `dci-run-dashboard` has produced scored outputs, this skill builds the interactive SP-weighted DCI canvas dashboard and opens it beside the chat.

The canvas shows four views:
- **Headline stats** — Org SP DCI (primary), Ticket DCI, AI adoption %, SP coverage %, writer count
- **Per Technical Writer** — table sorted by SP-weighted DCI, with SP coverage % and metric explanations
- **By Team** — SP DCI bar chart + rollup table
- **By Manager Group** — SP DCI bar chart + rollup table (Adam Christensen, Danielle Biber, Vita Gilin)
- **Metrics Guide** — inline definitions of every metric, formula, and DCI zone threshold

## When to use

- User says: build canvas, publish dashboard, open DCI canvas, show DCI dashboard, show me the dashboard.
- After `dci-run-dashboard` completes successfully.
- User wants to share or review the SP-weighted DCI results visually.

## Prerequisites

- `dci-run-dashboard` must have been run first (or the `out/` directory must contain `dci_writer_scores.csv`, `out/dashboard/Tab6_Team_Rollup.csv`, and `Tab7_Manager_Rollup.csv`).
- If those files are missing, run [`dci-run-dashboard`](../dci-run-dashboard/SKILL.md) first.
- Know the period and scope used in the pipeline run — pass them through so the canvas title and filter are accurate.

## Primary command

```powershell
cd C:\Users\yserota\Documents\Cursor-AI\dci-agent
python scripts/build_dci_sp_canvas.py `
  --output-dir out `
  --period-start 2026-04-01 `
  --period-end 2026-06-30
```

### Common overrides

```powershell
python scripts/build_dci_sp_canvas.py `
  --output-dir out/h1-2026 `
  --period-start 2026-01-01 `
  --period-end 2026-06-30 `
  --canvases-dir "C:\Users\yserota\.cursor\projects\c-Users-yserota-Documents-Cursor-AI-dci-agent\canvases"
```

Scope the canvas to a subset of teams (must match the scope used in `run_dci_dashboard.py`):

```powershell
python scripts/build_dci_sp_canvas.py `
  --output-dir out `
  --period-start 2026-04-01 `
  --period-end 2026-06-30 `
  --teams "Execution"

python scripts/build_dci_sp_canvas.py `
  --output-dir out `
  --period-start 2026-04-01 `
  --period-end 2026-06-30 `
  --pods "Pod 1,Pod 2"
```

## Agent workflow

0. **Confirm period and scope.** Ask if not already known:
   > What period and scope were used for this run? (e.g. Q2 2026, Pod 1 + Pod 2)
   Echo back before building: `Period: 2026-04-01 to 2026-06-30 · Scope: Pod 1, Pod 2`

1. Confirm `out/dci_writer_scores.csv`, `out/dashboard/Tab6_Team_Rollup.csv`, and `out/dashboard/Tab7_Manager_Rollup.csv` all exist. If missing, run `dci-run-dashboard` first.
2. Run `python scripts/build_dci_sp_canvas.py` with `--period-start`, `--period-end`, and scope flag(s) matching the pipeline run.
3. The script prints a JSON summary: `canvas` path, `writers`, `teams`, `manager_groups`.
4. Link the canvas to the user using the absolute path from the summary, e.g.:  
   `[dci-sp-dashboard](C:\Users\yserota\.cursor\projects\c-Users-yserota-Documents-Cursor-AI-dci-agent\canvases\dci-sp-dashboard.canvas.tsx)`
5. Tell the user they can open it beside the chat by clicking the link.

## Outputs

| File | Description |
|------|-------------|
| `~/.cursor/projects/c-Users-yserota-Documents-Cursor-AI-dci-agent/canvases/dci-sp-dashboard.canvas.tsx` | SP-weighted dashboard canvas with embedded metric explanations |

The canvas embeds all data inline — no network calls, no server needed.

## Canvas sections

| Section | What it shows |
|---------|--------------|
| Headline stats | Org SP DCI (primary), Ticket DCI, AI adoption %, SP coverage badge, writer count |
| Per Technical Writer | Table: writer, manager, SP started, SP finished, SP DCI, SP coverage %, ticket DCI, AI adoption, DCI zone |
| By Team | Bar chart (SP DCI + ticket DCI) + rollup table |
| By Manager Group | Bar chart (SP DCI + ticket DCI) + rollup table |
| Metrics Guide | Inline definitions: SP DCI formula, Ticket DCI, AI adoption %, SP coverage %, DCI zones, confidence score |

## Metric definitions embedded in canvas

The canvas Metrics Guide section explains:

| Metric | Formula / Definition |
|--------|---------------------|
| SP DCI (primary) | `story_points_started ÷ story_points_finished` — complexity-weighted throughput ratio |
| Ticket DCI | `tickets_started ÷ tickets_resolved` — secondary; use when SP coverage < 70% |
| AI Adoption % | `tickets_finished_with_AI ÷ total_tickets_finished × 100` |
| SP Coverage % | `tickets_with_explicit_SP ÷ total_tickets × 100` — reliability indicator for SP DCI |
| DCI Zone: Backlog building | SP DCI > 1.0 — starting more than finishing |
| DCI Zone: Healthy runway | SP DCI 0.80–0.95 — sustainable throughput |
| DCI Zone: Watch band | SP DCI 0.75–0.80 — monitor closely |
| DCI Zone: Backlog drain | SP DCI < 0.75 — finishing more than starting |
| Confidence score | 0.0–1.0; penalties for partial window (−0.2), missing optional fields (−0.1), missing intake fields (−0.15) |
| Missing SP default | Tickets with no Story Points tagged are weighted as 1.0 in SP DCI calculations |

## Failure rules

| Failure | Action |
|---------|--------|
| Missing `Tab6_Team_Rollup.csv` or `Tab7_Manager_Rollup.csv` | Re-run `run_dci_dashboard.py` — these tabs are generated automatically |
| Canvas appears blank | Confirm the `.canvas.tsx` was written to the correct path printed in the script output |
| `story_points_dci` shows `n/a` for all writers | Check `story_points_coverage_pct` in scores — if 0%, story points are not tagged in Jira for this period |
| Scope mismatch between pipeline and canvas | Re-run canvas builder with same `--teams/--pods/--managers` flags used in `run_dci_dashboard.py` |

## Related skills

- [`dci-fetch-jira`](../dci-fetch-jira/SKILL.md) — pull Jira data (step 1)
- [`dci-run-dashboard`](../dci-run-dashboard/SKILL.md) — score writers and build tab CSVs (step 2)
