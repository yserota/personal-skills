"""DCI calculation logic."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any


@dataclass
class ComputationResult:
    output_rows: list[dict[str, Any]]
    run_audit: dict[str, Any]


def _safe_round(value: float | None, precision: int) -> float | None:
    if value is None:
        return None
    return round(value, precision)


def _confidence_for_row(row: dict[str, Any], formula_cfg: dict[str, Any]) -> tuple[float, str]:
    base = float(formula_cfg.get("confidence", {}).get("base", 1.0))
    floor = float(formula_cfg.get("confidence", {}).get("floor", 0.0))
    penalties = formula_cfg.get("confidence", {}).get("penalties", {})
    score = base
    reason = "ok"

    if row["period_end"] == row["period_start"]:
        score -= float(penalties.get("partial_window", 0.0))
        reason = "partial_window"

    for field in ("pod", "team", "work_type", "manual_vs_ai_flag"):
        if (row.get(field) or "").strip() == "":
            score -= float(penalties.get("missing_optional_fields", 0.0)) / 4.0

    if "intake_count" not in row and float(penalties.get("missing_intake_fields", 0.0)) > 0:
        score -= float(penalties.get("missing_intake_fields", 0.0))
        reason = "missing_intake_fields"

    return max(score, floor), reason


def _ratio(numerator: float, denominator: float) -> float | None:
    if denominator == 0.0:
        return None
    return numerator / denominator


def _optional_float(row: dict[str, Any], key: str, default: float = 0.0) -> float:
    value = row.get(key, default)
    if value is None or (isinstance(value, str) and not value.strip()):
        return default
    return float(value)


def calculate_dci(validated_rows: list[dict[str, Any]], formula_cfg: dict[str, Any]) -> ComputationResult:
    precision = int(formula_cfg.get("output", {}).get("precision", 4))
    output_rows: list[dict[str, Any]] = []
    null_reason = formula_cfg.get("rules", {}).get("divide_by_zero", {}).get("reason", "active_capacity_realized_zero")
    computed_at = datetime.now(timezone.utc).isoformat()
    formula_version = formula_cfg.get("formula", {}).get("version", "1.1.0")

    dci_null_count = 0
    intake_dci_null_count = 0
    for row in validated_rows:
        incoming = float(row["incoming_demand"])
        capacity = float(row["resolved_count"])
        intake = float(row.get("intake_count", 0.0))
        queue_lag = float(row.get("avg_queue_lag_days", 0.0))
        ai_started = _optional_float(row, "ai_started_count")
        manual_started = _optional_float(row, "manual_started_count")
        untagged_started = _optional_float(row, "untagged_started_count")
        ai_finished = _optional_float(row, "ai_finished_count")
        manual_finished = _optional_float(row, "manual_finished_count")
        untagged_finished = _optional_float(row, "untagged_finished_count")
        cycle_days_ai = _optional_float(row, "active_cycle_days_ai")
        cycle_days_manual = _optional_float(row, "active_cycle_days_manual")
        period_start: date = row["period_start"]
        period_end: date = row["period_end"]
        cycle_days = float(row["active_cycle_days"])
        story_points_started = _optional_float(row, "story_points_started")
        story_points_finished = _optional_float(row, "story_points_finished")
        story_points_intake = _optional_float(row, "story_points_intake")
        story_points_coverage_pct = _optional_float(row, "story_points_coverage_pct")

        dci_value: float | None
        dci_status = "ok"
        dci_reason = "ok"
        operational_dci = _ratio(incoming, capacity)
        if operational_dci is None:
            dci_value = None
            dci_status = "error"
            dci_reason = null_reason
            dci_null_count += 1
        else:
            dci_value = operational_dci

        intake_dci = _ratio(intake, capacity)
        if intake_dci is None:
            intake_dci_null_count += 1
        backlog_pressure = intake - incoming

        operational_dci_points = _ratio(story_points_started, story_points_finished)
        intake_dci_points = _ratio(story_points_intake, story_points_finished)
        avg_story_points_per_finish = _ratio(story_points_finished, capacity)

        operational_dci_ai = _ratio(ai_started, ai_finished)
        operational_dci_manual = _ratio(manual_started, manual_finished)
        ai_adoption_pct = _ratio(ai_finished, capacity)
        tagged_finished = ai_finished + manual_finished
        ai_adoption_tagged_pct = _ratio(ai_finished, tagged_finished)
        ai_field_coverage_pct = _ratio(tagged_finished, capacity)
        dci_ai_vs_manual_delta: float | None = None
        if operational_dci_ai is not None and operational_dci_manual is not None:
            dci_ai_vs_manual_delta = operational_dci_ai - operational_dci_manual
        cycle_ai_vs_manual_delta: float | None = None
        if ai_finished > 0 and manual_finished > 0:
            cycle_ai_vs_manual_delta = cycle_days_ai - cycle_days_manual

        confidence_score, confidence_reason = _confidence_for_row(row, formula_cfg)
        window_days = (period_end - period_start).days + 1
        predictability_proxy = (
            None
            if window_days <= 0 or incoming == 0
            else max(0.0, min(1.0, capacity / incoming))
        )

        output_rows.append(
            {
                "writer_id": row["writer_id"],
                "writer_name": row["writer_name"],
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "window_days": window_days,
                "incoming_demand": _safe_round(incoming, precision),
                "active_capacity_realized": _safe_round(capacity, precision),
                "story_points_started": _safe_round(story_points_started, precision),
                "story_points_finished": _safe_round(story_points_finished, precision),
                "story_points_intake": _safe_round(story_points_intake, precision),
                "story_points_coverage_pct": _safe_round(story_points_coverage_pct, precision),
                "operational_dci_points": _safe_round(operational_dci_points, precision),
                "intake_dci_points": _safe_round(intake_dci_points, precision),
                "avg_story_points_per_finish": _safe_round(avg_story_points_per_finish, precision),
                "intake_count": _safe_round(intake, precision),
                "avg_queue_lag_days": _safe_round(queue_lag, precision),
                "active_cycle_days": _safe_round(cycle_days, precision),
                "active_cycle_days_ai": _safe_round(cycle_days_ai if ai_finished > 0 else None, precision),
                "active_cycle_days_manual": _safe_round(
                    cycle_days_manual if manual_finished > 0 else None, precision
                ),
                "ai_started_count": _safe_round(ai_started, precision),
                "manual_started_count": _safe_round(manual_started, precision),
                "untagged_started_count": _safe_round(untagged_started, precision),
                "ai_finished_count": _safe_round(ai_finished, precision),
                "manual_finished_count": _safe_round(manual_finished, precision),
                "untagged_finished_count": _safe_round(untagged_finished, precision),
                "ai_adoption_pct": _safe_round(
                    ai_adoption_pct * 100 if ai_adoption_pct is not None else None, precision
                ),
                "ai_adoption_tagged_pct": _safe_round(
                    ai_adoption_tagged_pct * 100 if ai_adoption_tagged_pct is not None else None, precision
                ),
                "ai_field_coverage_pct": _safe_round(
                    ai_field_coverage_pct * 100 if ai_field_coverage_pct is not None else None, precision
                ),
                "operational_dci_ai": _safe_round(operational_dci_ai, precision),
                "operational_dci_manual": _safe_round(operational_dci_manual, precision),
                "dci_ai_vs_manual_delta": _safe_round(dci_ai_vs_manual_delta, precision),
                "cycle_ai_vs_manual_delta": _safe_round(cycle_ai_vs_manual_delta, precision),
                "operational_dci": _safe_round(operational_dci, precision),
                "dci": _safe_round(dci_value, precision),
                "intake_dci": _safe_round(intake_dci, precision),
                "backlog_pressure": _safe_round(backlog_pressure, precision),
                "dci_status": dci_status,
                "dci_reason": dci_reason,
                "predictability_proxy": _safe_round(predictability_proxy, precision),
                "confidence_score": _safe_round(confidence_score, precision),
                "confidence_reason": confidence_reason,
                "pod": (row.get("pod") or "").strip(),
                "team": (row.get("team") or "").strip(),
                "manager_name": (row.get("manager_name") or "").strip(),
                "manager_id": (row.get("manager_id") or "").strip(),
                "work_type": (row.get("work_type") or "").strip(),
                "manual_vs_ai_flag": (row.get("manual_vs_ai_flag") or "").strip(),
                "formula_version": formula_version,
                "computed_at_utc": computed_at,
            }
        )

    audit = {
        "computed_at_utc": computed_at,
        "formula_version": formula_version,
        "rows_scored": len(output_rows),
        "dci_null_count": dci_null_count,
        "intake_dci_null_count": intake_dci_null_count,
    }
    return ComputationResult(output_rows=output_rows, run_audit=audit)
