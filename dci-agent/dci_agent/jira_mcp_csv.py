"""Convert Jira MCP search batch JSON into a DCI-compatible CSV."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

from .io_utils import write_csv, write_json


DEFAULT_CONFIG_PATH = Path("config/jira_mcp_fields.yaml")
CSV_COLUMNS = (
    "Key",
    "Issue Type",
    "Status",
    "Summary",
    "Assignee",
    "Assigned Technical Writer",
    "Story Points",
    "StartWork",
    "FinishWork",
    "Created",
    "TW-AI Usage",
    "Sprint",
    "Updated",
    "Resolved",
    "Labels",
    "Epic Link",
)


def load_jira_mcp_config(path: str | Path | None = None) -> dict[str, Any]:
    config_path = Path(path) if path else DEFAULT_CONFIG_PATH
    with config_path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def build_jql(period_start: date, period_end: date, config: dict[str, Any] | None = None) -> str:
    cfg = config or load_jira_mcp_config()
    projects = ", ".join(cfg.get("projects", ["DOC", "DOCS"]))
    template = (cfg.get("jql_template") or "").strip()
    return template.format(
        projects=projects,
        period_start=period_start.isoformat(),
        period_end=period_end.isoformat(),
    )


def _unwrap_value(raw: Any) -> Any:
    if isinstance(raw, dict):
        if "value" in raw and len(raw) == 1:
            return raw.get("value")
        if "name" in raw:
            return raw.get("name")
        if "displayName" in raw:
            return raw.get("displayName")
    return raw


def _get_nested(issue: dict[str, Any], path: str) -> Any:
    if path.startswith("customfield_"):
        raw = issue.get(path)
        if raw is None:
            fields = issue.get("fields")
            if isinstance(fields, dict):
                raw = fields.get(path)
        return _unwrap_value(raw)

    parts = path.split(".")
    current: Any = issue
    if parts[0] not in issue and isinstance(issue.get("fields"), dict):
        current = issue["fields"]
    for part in parts:
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return _unwrap_value(current)


def _format_date_value(raw: Any) -> str:
    if raw is None:
        return ""
    if isinstance(raw, date) and not isinstance(raw, datetime):
        return raw.isoformat()
    text = str(raw).strip()
    if not text:
        return ""
    if "T" in text:
        return text.split("T", 1)[0]
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        return text[:10]
    for fmt in ("%d/%b/%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return text


def _format_story_points(raw: Any) -> str:
    if raw is None:
        return ""
    value = _unwrap_value(raw)
    if value is None or str(value).strip() == "":
        return ""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    if number < 0:
        return ""
    text = f"{number:.4f}".rstrip("0").rstrip(".")
    return text


def _format_ai_usage(raw: Any) -> str:
    if raw is None:
        return ""
    if isinstance(raw, list):
        parts = []
        for item in raw:
            value = _unwrap_value(item)
            if value is None:
                continue
            text = str(value).strip()
            if text:
                parts.append(text)
        return "; ".join(parts)
    text = str(_unwrap_value(raw)).strip()
    return text


def _format_sprint(raw: Any) -> str:
    """Return the active sprint name, falling back to the last sprint in the list."""
    if raw is None:
        return ""
    if isinstance(raw, str):
        return raw.strip()
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict) and item.get("state") == "active":
                return str(item.get("name", "")).strip()
        if raw:
            last = raw[-1]
            if isinstance(last, dict):
                return str(last.get("name", "")).strip()
    return str(_unwrap_value(raw) or "").strip()


def _format_labels(raw: Any) -> str:
    """Join a list of label strings with '; '."""
    if raw is None:
        return ""
    if isinstance(raw, list):
        return "; ".join(str(item).strip() for item in raw if str(item).strip())
    return str(raw).strip()


def issue_to_csv_row(issue: dict[str, Any], field_map: dict[str, str] | None = None) -> dict[str, str]:
    cfg = load_jira_mcp_config()
    mapping = field_map or cfg.get("field_map") or {}
    row: dict[str, str] = {}
    for column in CSV_COLUMNS:
        source = mapping.get(column, "")
        raw = _get_nested(issue, source) if source else None
        if column in {"StartWork", "FinishWork", "Created", "Updated", "Resolved"}:
            row[column] = _format_date_value(raw)
        elif column == "TW-AI Usage":
            row[column] = _format_ai_usage(raw)
        elif column == "Story Points":
            row[column] = _format_story_points(raw)
        elif column == "Assignee":
            assignee = _get_nested(issue, "assignee.name")
            if not assignee:
                assignee = _get_nested(issue, "assignee")
            row[column] = str(assignee or "").strip()
        elif column == "Sprint":
            row[column] = _format_sprint(raw)
        elif column == "Labels":
            row[column] = _format_labels(raw)
        else:
            row[column] = str(raw or "").strip()
    return row


def _load_batch_file(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8-sig")
    payload = json.loads(text)
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("issues", "results", "data"):
            items = payload.get(key)
            if isinstance(items, list):
                return [item for item in items if isinstance(item, dict)]
        if payload.get("key"):
            return [payload]
    raise ValueError(f"Unsupported batch JSON shape in {path}")


def batches_to_rows(batch_paths: list[Path], field_map: dict[str, str] | None = None) -> tuple[list[dict[str, str]], dict[str, Any]]:
    deduped: dict[str, dict[str, str]] = {}
    missing_writer = 0
    files_read = 0

    for path in sorted(batch_paths):
        issues = _load_batch_file(path)
        files_read += 1
        for issue in issues:
            row = issue_to_csv_row(issue, field_map=field_map)
            key = row.get("Key", "").strip()
            if not key:
                continue
            deduped[key] = row
            if not row.get("Assignee") and not row.get("Assigned Technical Writer"):
                missing_writer += 1

    rows = [{column: deduped[key].get(column, "") for column in CSV_COLUMNS} for key in sorted(deduped)]
    summary = {
        "batch_files_read": files_read,
        "issues_written": len(rows),
        "issues_missing_writer": missing_writer,
    }
    return rows, summary


def write_batches_to_csv(
    batch_glob: str | Path,
    output_csv: str | Path,
    *,
    summary_path: str | Path | None = "out/jira_fetch_summary.json",
    field_map: dict[str, str] | None = None,
) -> dict[str, Any]:
    batch_dir = Path(batch_glob)
    if batch_dir.is_dir():
        paths = sorted(batch_dir.glob("*.json"))
    else:
        paths = sorted(Path(".").glob(str(batch_glob)))

    if not paths:
        raise FileNotFoundError(f"No batch JSON files matched: {batch_glob}")

    rows, summary = batches_to_rows(paths, field_map=field_map)
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_csv(output_path, rows)

    summary = {
        **summary,
        "output_csv": str(output_path),
        "batch_glob": str(batch_glob),
    }
    if summary_path:
        summary_file = Path(summary_path)
        summary_file.parent.mkdir(parents=True, exist_ok=True)
        write_json(summary_file, summary)
        summary["summary_path"] = str(summary_file)
    return summary
