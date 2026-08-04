"""End-to-end DCI pipeline orchestration."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .ai_analysis import build_ai_impact_csv_rows, build_ai_impact_markdown
from .calculation import calculate_dci
from .dashboard_export import build_dashboard_exports
from .io_utils import load_yaml, read_csv, write_csv, write_json
from .manager_mapping import apply_manager_mapping
from .publishers import publish_google_sheet
from .validation import validate_rows


def _apply_scope_filter(
    rows: list[dict[str, Any]],
    teams: list[str] | None = None,
    pods: list[str] | None = None,
    managers: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Return only rows matching any of the specified teams, pods, or managers.

    Filters are OR'd: a writer is included if they match any supplied filter.
    Returns all rows unchanged when no filters are supplied.
    """
    if not any([teams, pods, managers]):
        return rows
    result: list[dict[str, Any]] = []
    for row in rows:
        if teams and row.get("team") in teams:
            result.append(row)
            continue
        if pods and row.get("pod") in pods:
            result.append(row)
            continue
        if managers and row.get("manager_name") in managers:
            result.append(row)
    return result


def run_pipeline(
    input_csv_path: str,
    schema_path: str,
    formula_path: str,
    output_dir: str,
    publish_target: str | None = None,
    publish_config: dict[str, Any] | None = None,
    manager_map_path: str | None = None,
    teams: list[str] | None = None,
    pods: list[str] | None = None,
    managers: list[str] | None = None,
) -> dict[str, Any]:
    schema = load_yaml(schema_path)
    formula = load_yaml(formula_path)
    raw_rows = read_csv(input_csv_path)

    validation = validate_rows(raw_rows, schema)
    mapped = apply_manager_mapping(validation.accepted_rows, manager_map_path)
    scoped_rows = _apply_scope_filter(mapped.rows, teams=teams, pods=pods, managers=managers)
    compute = calculate_dci(scoped_rows, formula)

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    canonical_csv = out_dir / "dci_writer_scores.csv"
    rejected_csv = out_dir / "rejected_rows.csv"
    canonical_json = out_dir / "run_summary.json"

    write_csv(canonical_csv, compute.output_rows)
    write_csv(rejected_csv, validation.rejected_rows)
    write_csv(out_dir / "dci_ai_impact_summary.csv", build_ai_impact_csv_rows(compute.output_rows))
    period_label = ""
    if compute.output_rows:
        first = compute.output_rows[0]
        period_label = f"{first.get('period_start', '')} to {first.get('period_end', '')}"
    ai_report_path = out_dir / "DCI_AI_Impact_Analysis.md"
    ai_report_path.write_text(build_ai_impact_markdown(compute.output_rows, period_label), encoding="utf-8")

    dashboard_dir = out_dir / "dashboard"
    dashboard_dir.mkdir(parents=True, exist_ok=True)
    for tab_name, tab_rows in build_dashboard_exports(compute.output_rows).items():
        write_csv(dashboard_dir / f"{tab_name}.csv", tab_rows)

    # Org-level SP DCI and coverage for manifest surfacing
    _sp_started = sum(float(r.get("story_points_started") or 0) for r in compute.output_rows)
    _sp_finished = sum(float(r.get("story_points_finished") or 0) for r in compute.output_rows)
    _org_sp_dci: float | None = round(_sp_started / _sp_finished, 4) if _sp_finished else None
    _coverages = [float(r.get("story_points_coverage_pct") or 0) for r in compute.output_rows]
    _org_sp_coverage: float | None = round(sum(_coverages) / len(_coverages), 1) if _coverages else None

    summary: dict[str, Any] = {
        "run_started_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_csv_path": str(input_csv_path),
        "rows_received": len(raw_rows),
        "rows_accepted": len(validation.accepted_rows),
        "rows_rejected": len(validation.rejected_rows),
        "writers_scored": len(compute.output_rows),
        "unmapped_writers": mapped.unmapped_writers,
        "scope_teams": teams,
        "scope_pods": pods,
        "scope_managers": managers,
        "org_sp_dci": _org_sp_dci,
        "org_sp_coverage_pct": _org_sp_coverage,
        **compute.run_audit,
        "publish_target": publish_target or "none",
    }

    published = None
    if publish_target == "google_sheets":
        if not publish_config:
            raise ValueError("publish_config is required for google_sheets target")
        result = publish_google_sheet(
            rows=compute.output_rows,
            audit_rows=[summary],
            sheet_id=publish_config["sheet_id"],
            worksheet_name=publish_config.get("worksheet_name", "dci_writer_scores"),
            audit_worksheet_name=publish_config.get("audit_worksheet_name", "run_audit_log"),
            service_account_json_path=publish_config["service_account_json_path"],
        )
        published = {"target": result.target, "rows_written": result.rows_written}

    if published:
        summary["publish_result"] = published
    write_json(canonical_json, summary)
    return summary
