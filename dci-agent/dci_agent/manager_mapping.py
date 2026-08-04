"""Join technical writers to managers from an external mapping file."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .io_utils import read_csv


@dataclass
class ManagerMappingResult:
    rows: list[dict[str, Any]]
    unmapped_writers: list[str]


def _normalize_key(value: str) -> str:
    return (value or "").strip().lower()


def load_manager_map(path: str | Path) -> dict[str, dict[str, str]]:
    rows = read_csv(path)
    required = {"manager_name"}
    if not rows:
        return {}

    columns = set(rows[0].keys())
    if not required.issubset(columns):
        raise ValueError("Manager map must include at least manager_name column")
    if "writer_id" not in columns and "writer_name" not in columns:
        raise ValueError("Manager map must include writer_id and/or writer_name")

    mapping: dict[str, dict[str, str]] = {}
    for row in rows:
        entry = {
            "manager_name": (row.get("manager_name") or "").strip(),
            "manager_id": (row.get("manager_id") or "").strip(),
            "pod": (row.get("pod") or "").strip(),
            "team": (row.get("team") or "").strip(),
        }
        writer_id = (row.get("writer_id") or "").strip()
        writer_name = (row.get("writer_name") or "").strip()
        if writer_id:
            mapping[_normalize_key(writer_id)] = entry
        if writer_name:
            mapping[_normalize_key(writer_name)] = entry
    return mapping


def apply_manager_mapping(
    rows: list[dict[str, Any]],
    manager_map_path: str | Path | None,
) -> ManagerMappingResult:
    if not manager_map_path:
        enriched = []
        for row in rows:
            copy = dict(row)
            copy.setdefault("manager_name", "")
            copy.setdefault("manager_id", "")
            if not copy.get("pod"):
                copy["pod"] = ""
            enriched.append(copy)
        return ManagerMappingResult(rows=enriched, unmapped_writers=[])

    mapping = load_manager_map(manager_map_path)
    enriched: list[dict[str, Any]] = []
    unmapped: list[str] = []

    for row in rows:
        copy = dict(row)
        writer_id = _normalize_key(str(copy.get("writer_id", "")))
        writer_name = _normalize_key(str(copy.get("writer_name", "")))
        match = mapping.get(writer_id) or mapping.get(writer_name)

        if match:
            copy["manager_name"] = match.get("manager_name", "")
            copy["manager_id"] = match.get("manager_id", "")
            if not (copy.get("pod") or "").strip() and match.get("pod"):
                copy["pod"] = match["pod"]
            if not (copy.get("team") or "").strip() and match.get("team"):
                copy["team"] = match["team"]
        else:
            copy["manager_name"] = ""
            copy["manager_id"] = ""
            unmapped.append(str(copy.get("writer_name") or copy.get("writer_id")))

        enriched.append(copy)

    return ManagerMappingResult(rows=enriched, unmapped_writers=sorted(set(unmapped)))
