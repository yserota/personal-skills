"""Transform raw Jira exports into normalized DCI input rows."""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from statistics import mean
from typing import Any

from .io_utils import read_csv


def _load_tw_roster(manager_map_path: Path | None) -> set[str]:
    if manager_map_path is None or not manager_map_path.exists():
        return set()
    rows = read_csv(manager_map_path)
    return {(row.get("writer_name") or "").strip() for row in rows if (row.get("writer_name") or "").strip()}


CANONICAL_COLUMNS = (
    "Issue Type",
    "Key",
    "Status",
    "Summary",
    "Assignee",
    "Assigned Technical Writer",
    "Story Points",
    "Sprint",
    "StartWork",
    "FinishWork",
    "Created",
    "TW-AI Usage",
)

JIRA_COLUMN_ALIASES: dict[str, str] = {
    "Issue key": "Key",
    "Key": "Key",
    "Issue Type": "Issue Type",
    "Custom field (StartWork)": "StartWork",
    "StartWork": "StartWork",
    "Custom field (FinishWork)": "FinishWork",
    "FinishWork": "FinishWork",
    "Custom field (Assigned Technical Writer)": "Assigned Technical Writer",
    "Assigned Technical Writer": "Assigned Technical Writer",
    "Custom field (Story Points)": "Story Points",
    "Custom field (TW-AI Usage)": "TW-AI Usage",
    "TW-AI Usage": "TW-AI Usage",
}

REQUIRED_AFTER_NORMALIZE = (
    "Key",
    "Status",
    "Summary",
    "Assignee",
)

OPTIONAL_AFTER_NORMALIZE = (
    "Issue Type",
    "Assigned Technical Writer",
    "Story Points",
    "Sprint",
    "Created",
    "TW-AI Usage",
)

DATE_FORMATS = (
    "%Y-%m-%d",
    "%d/%b/%y %I:%M %p",
    "%d/%b/%y %H:%M",
    "%d/%b/%y",
)


@dataclass
class JiraTransformResult:
    normalized_rows: list[dict[str, Any]]
    skipped_rows: list[dict[str, Any]]


def _detect_dialect(path: Path) -> csv.Dialect:
    sample = path.read_text(encoding="utf-8-sig")[:4096]
    try:
        return csv.Sniffer().sniff(sample, delimiters=",\t;")
    except csv.Error:
        return csv.get_dialect("excel")


def _parse_optional_date(raw: str) -> date | None:
    value = (raw or "").strip()
    if not value:
        return None
    iso_candidate = value[:10]
    try:
        return date.fromisoformat(iso_candidate)
    except ValueError:
        pass
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _in_period(value: date | None, period_start: date, period_end: date) -> bool:
    return value is not None and period_start <= value <= period_end


def _load_username_map(path: Path | None) -> dict[str, str]:
    if path is None or not path.exists():
        return {}
    rows = read_csv(path)
    mapping: dict[str, str] = {}
    for row in rows:
        username = (row.get("jira_username") or "").strip().lower()
        writer_name = (row.get("writer_name") or "").strip()
        if username and writer_name:
            mapping[username] = writer_name
    return mapping


def _resolve_writer(raw: str, username_map: dict[str, str]) -> str:
    value = (raw or "").strip()
    if not value:
        return ""
    return username_map.get(value.lower(), value)


def _merge_jira_csv_row(headers: list[str], values: list[str]) -> dict[str, str]:
    """Merge duplicate Jira export headers (multi-select fields repeat the column name)."""
    merged: dict[str, list[str]] = defaultdict(list)
    for header, value in zip(headers, values, strict=False):
        canonical = JIRA_COLUMN_ALIASES.get(header, header)
        stripped = (value or "").strip()
        if stripped:
            merged[canonical].append(stripped)
        else:
            merged.setdefault(canonical, [])
    return {key: "; ".join(parts) for key, parts in merged.items()}



def _tw_ai_usage_values(row: dict[str, str]) -> list[str]:
    raw = (row.get("TW-AI Usage") or "").strip()
    if not raw:
        return []
    return [part.strip() for part in raw.split(";") if part.strip()]


def _writer_from_row(row: dict[str, str], username_map: dict[str, str]) -> str:
    assignee = _resolve_writer(row.get("Assignee", ""), username_map)
    technical_writer = _resolve_writer(row.get("Assigned Technical Writer", ""), username_map)
    return assignee or technical_writer


def _parse_story_points(raw: str) -> tuple[float, bool]:
    """Return (weight, has_explicit_value). Missing SP defaults to 1.0 ticket weight."""
    text = (raw or "").strip()
    if not text:
        return 1.0, False
    try:
        value = float(text)
    except ValueError:
        return 1.0, False
    if value < 0:
        return 1.0, False
    return value, True


def _ai_flag_from_row(row: dict[str, str]) -> str:
    manual_markers = {"none", "n/a", "manual", "no", "no usage"}
    usages = _tw_ai_usage_values(row)
    if usages:
        if any(usage.lower() not in manual_markers for usage in usages):
            return "ai"
        return "manual"
    return "unknown"


def transform_jira_export(
    jira_path: str | Path,
    period_start: date,
    period_end: date,
    username_map_path: str | Path | None = "config/jira_username_map.csv",
    manager_map_path: str | Path | None = "config/writer_manager_map.csv",
    roster_only: bool = True,
) -> JiraTransformResult:
    file_path = Path(jira_path)
    dialect = _detect_dialect(file_path)
    username_map = _load_username_map(Path(username_map_path) if username_map_path else None)
    tw_roster = _load_tw_roster(Path(manager_map_path) if manager_map_path else None) if roster_only else set()
    skipped: list[dict[str, Any]] = []
    grouped: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "incoming_demand": 0,
            "resolved_count": 0,
            "intake_count": 0,
            "cycle_times": [],
            "queue_lags": [],
            "work_type_counts": defaultdict(int),
            "manual_vs_ai_flag": "unknown",
            "ai_started": 0,
            "manual_started": 0,
            "untagged_started": 0,
            "ai_finished": 0,
            "manual_finished": 0,
            "untagged_finished": 0,
            "ai_cycle_times": [],
            "manual_cycle_times": [],
            "untagged_cycle_times": [],
            "story_points_started": 0.0,
            "story_points_finished": 0.0,
            "story_points_intake": 0.0,
            "tickets_with_story_points": 0,
            "tickets_seen": 0,
        }
    )

    with file_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, dialect=dialect)
        try:
            headers = next(reader)
        except StopIteration as exc:
            raise ValueError("Jira export has no header row") from exc
        if not headers:
            raise ValueError("Jira export has no header row")

        for idx, values in enumerate(reader, start=2):
            row = _merge_jira_csv_row(headers, values)
            missing = [c for c in REQUIRED_AFTER_NORMALIZE if c not in row]
            if missing:
                skipped.append(
                    {
                        "row_number": idx,
                        "reason": f"missing required columns after normalization: {', '.join(missing)}",
                        "key": row.get("Key", ""),
                    }
                )
                continue

            writer = _writer_from_row(row, username_map)
            if not writer:
                skipped.append(
                    {
                        "row_number": idx,
                        "reason": "missing writer (Assignee or Assigned Technical Writer)",
                        "key": row.get("Key", ""),
                    }
                )
                continue

            start = _parse_optional_date(row.get("StartWork", ""))
            finish = _parse_optional_date(row.get("FinishWork", ""))
            created = _parse_optional_date(row.get("Created", ""))

            if not (
                _in_period(start, period_start, period_end)
                or _in_period(finish, period_start, period_end)
                or _in_period(created, period_start, period_end)
            ):
                continue

            bucket = grouped[writer]
            issue_type = (row.get("Issue Type") or "").strip().lower() or "unknown"
            bucket["work_type_counts"][issue_type] += 1
            story_points, has_story_points = _parse_story_points(row.get("Story Points", ""))
            bucket["tickets_seen"] += 1
            if has_story_points:
                bucket["tickets_with_story_points"] += 1

            ai_flag = _ai_flag_from_row(row)

            if _in_period(start, period_start, period_end):
                bucket["incoming_demand"] += 1
                bucket["story_points_started"] += story_points
                if ai_flag == "ai":
                    bucket["ai_started"] += 1
                elif ai_flag == "manual":
                    bucket["manual_started"] += 1
                else:
                    bucket["untagged_started"] += 1

            if _in_period(finish, period_start, period_end):
                bucket["resolved_count"] += 1
                bucket["story_points_finished"] += story_points
                if ai_flag == "ai":
                    bucket["ai_finished"] += 1
                elif ai_flag == "manual":
                    bucket["manual_finished"] += 1
                else:
                    bucket["untagged_finished"] += 1

            if _in_period(created, period_start, period_end):
                bucket["intake_count"] += 1
                bucket["story_points_intake"] += story_points

            if created and start:
                lag = (start - created).days
                if lag >= 0:
                    bucket["queue_lags"].append(float(lag))

            if start and finish and (
                _in_period(start, period_start, period_end)
                or _in_period(finish, period_start, period_end)
            ):
                cycle = (finish - start).days
                if cycle >= 0:
                    bucket["cycle_times"].append(float(cycle))
                    if ai_flag == "ai":
                        bucket["ai_cycle_times"].append(float(cycle))
                    elif ai_flag == "manual":
                        bucket["manual_cycle_times"].append(float(cycle))
                    else:
                        bucket["untagged_cycle_times"].append(float(cycle))

            if ai_flag == "ai":
                bucket["manual_vs_ai_flag"] = "ai"
            elif ai_flag == "manual" and bucket["manual_vs_ai_flag"] not in {"ai", "mixed"}:
                bucket["manual_vs_ai_flag"] = "manual"
            elif ai_flag == "unknown" and bucket["manual_vs_ai_flag"] == "unknown":
                bucket["manual_vs_ai_flag"] = "unknown"
            elif (
                ai_flag in {"ai", "manual"}
                and bucket["manual_vs_ai_flag"] in {"ai", "manual"}
                and bucket["manual_vs_ai_flag"] != ai_flag
            ):
                bucket["manual_vs_ai_flag"] = "mixed"

    normalized: list[dict[str, Any]] = []
    for writer, stats in sorted(grouped.items()):
        if tw_roster and writer not in tw_roster:
            continue

        dominant_work_type = "unknown"
        if stats["work_type_counts"]:
            dominant_work_type = max(stats["work_type_counts"].items(), key=lambda item: item[1])[0]

        avg_cycle = mean(stats["cycle_times"]) if stats["cycle_times"] else 0.0
        avg_cycle_ai = mean(stats["ai_cycle_times"]) if stats["ai_cycle_times"] else 0.0
        avg_cycle_manual = mean(stats["manual_cycle_times"]) if stats["manual_cycle_times"] else 0.0
        avg_queue_lag = mean(stats["queue_lags"]) if stats["queue_lags"] else 0.0
        tickets_seen = int(stats["tickets_seen"])
        tickets_with_sp = int(stats["tickets_with_story_points"])
        story_points_coverage_pct = (
            round(100.0 * tickets_with_sp / tickets_seen, 4) if tickets_seen else 0.0
        )
        writer_id = writer.lower().replace(" ", "_").replace(".", "_")
        normalized.append(
            {
                "writer_id": writer_id,
                "writer_name": writer,
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "incoming_demand": stats["incoming_demand"],
                "resolved_count": stats["resolved_count"],
                "intake_count": stats["intake_count"],
                "story_points_started": round(stats["story_points_started"], 4),
                "story_points_finished": round(stats["story_points_finished"], 4),
                "story_points_intake": round(stats["story_points_intake"], 4),
                "story_points_coverage_pct": story_points_coverage_pct,
                "avg_queue_lag_days": round(avg_queue_lag, 2),
                "active_cycle_days": round(avg_cycle, 2),
                "active_cycle_days_ai": round(avg_cycle_ai, 2),
                "active_cycle_days_manual": round(avg_cycle_manual, 2),
                "ai_started_count": stats["ai_started"],
                "manual_started_count": stats["manual_started"],
                "untagged_started_count": stats["untagged_started"],
                "ai_finished_count": stats["ai_finished"],
                "manual_finished_count": stats["manual_finished"],
                "untagged_finished_count": stats["untagged_finished"],
                "pod": "",
                "team": "",
                "work_type": dominant_work_type,
                "manual_vs_ai_flag": stats["manual_vs_ai_flag"],
            }
        )

    return JiraTransformResult(normalized_rows=normalized, skipped_rows=skipped)
