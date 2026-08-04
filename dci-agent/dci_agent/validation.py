"""Validation logic for the DCI input schema."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass
class ValidationResult:
    accepted_rows: list[dict[str, Any]]
    rejected_rows: list[dict[str, Any]]


def _parse_date(value: str, column: str) -> date:
    try:
        return date.fromisoformat(value.strip())
    except Exception as exc:  # pragma: no cover - explicit message path
        raise ValueError(f"{column} is not an ISO date (YYYY-MM-DD): {value}") from exc


def _coerce_number(value: str, column: str) -> float:
    text = (value or "").strip()
    if text == "":
        raise ValueError(f"{column} is required and must be numeric")
    try:
        return float(text)
    except Exception as exc:  # pragma: no cover - explicit message path
        raise ValueError(f"{column} must be numeric: {value}") from exc


def _coerce_optional_number(value: str, default: float = 0.0) -> float:
    text = (value or "").strip()
    if text == "":
        return default
    return float(text)


def validate_rows(rows: list[dict[str, str]], schema: dict[str, Any]) -> ValidationResult:
    required = schema.get("required_columns", [])
    optional = schema.get("optional_columns", [])
    constraints = schema.get("constraints", {})
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for idx, row in enumerate(rows, start=2):
        errors: list[str] = []
        for col in required:
            if (row.get(col) or "").strip() == "":
                errors.append(f"missing required column value: {col}")

        if errors:
            rejected.append({"row_number": idx, "reason": "; ".join(errors), **row})
            continue

        normalized: dict[str, Any] = dict(row)
        try:
            normalized["period_start"] = _parse_date(row["period_start"], "period_start")
            normalized["period_end"] = _parse_date(row["period_end"], "period_end")
            normalized["incoming_demand"] = _coerce_number(row["incoming_demand"], "incoming_demand")
            normalized["resolved_count"] = _coerce_number(row["resolved_count"], "resolved_count")
            normalized["active_cycle_days"] = _coerce_number(row["active_cycle_days"], "active_cycle_days")
            for col in optional:
                if (
                    col.endswith("_count")
                    or col.startswith("story_points")
                    or col in {
                        "intake_count",
                        "avg_queue_lag_days",
                        "active_cycle_days_ai",
                        "active_cycle_days_manual",
                    }
                ):
                    normalized[col] = _coerce_optional_number(row.get(col, ""))
        except ValueError as exc:
            rejected.append({"row_number": idx, "reason": str(exc), **row})
            continue

        if normalized["period_end"] < normalized["period_start"]:
            rejected.append(
                {
                    "row_number": idx,
                    "reason": "period_end is earlier than period_start",
                    **row,
                }
            )
            continue

        violated: list[str] = []
        for col, rule in constraints.items():
            if col not in normalized:
                continue
            value = normalized[col]
            if isinstance(value, str):
                continue
            if "min" in rule and value < float(rule["min"]):
                violated.append(f"{col} below min {rule['min']}")
        if violated:
            rejected.append({"row_number": idx, "reason": "; ".join(violated), **row})
            continue

        accepted.append(normalized)

    return ValidationResult(accepted_rows=accepted, rejected_rows=rejected)
