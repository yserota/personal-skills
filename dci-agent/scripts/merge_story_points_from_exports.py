"""Merge Story Points from one or more Jira CSV exports into a target export by issue Key."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


STORY_POINT_HEADERS = ("Story Points", "Custom field (Story Points)")
KEY_HEADERS = ("Key", "Issue key")


def _read_story_point_map(paths: list[Path]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for path in paths:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                continue
            key_col = next((h for h in KEY_HEADERS if h in reader.fieldnames), None)
            sp_col = next((h for h in STORY_POINT_HEADERS if h in reader.fieldnames), None)
            if not key_col or not sp_col:
                raise SystemExit(f"{path} is missing Key or Story Points columns")
            for row in reader:
                key = (row.get(key_col) or "").strip()
                sp = (row.get(sp_col) or "").strip()
                if key and sp:
                    mapping[key] = sp
    return mapping


def merge_story_points(target_csv: Path, reference_csvs: list[Path], output_csv: Path | None) -> dict:
    sp_map = _read_story_point_map(reference_csvs)
    with target_csv.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise SystemExit(f"{target_csv} has no header row")
        fieldnames = list(reader.fieldnames)
        if "Story Points" not in fieldnames:
            if "StartWork" in fieldnames:
                insert_at = fieldnames.index("StartWork")
                fieldnames.insert(insert_at, "Story Points")
            else:
                fieldnames.append("Story Points")
        rows = list(reader)

    matched = 0
    for row in rows:
        key = (row.get("Key") or row.get("Issue key") or "").strip()
        if key in sp_map:
            row["Story Points"] = sp_map[key]
            matched += 1
        else:
            row.setdefault("Story Points", row.get("Story Points", ""))

    out_path = output_csv or target_csv
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "target_csv": str(target_csv),
        "output_csv": str(out_path),
        "reference_files": [str(p) for p in reference_csvs],
        "reference_keys_with_sp": len(sp_map),
        "target_rows": len(rows),
        "rows_matched": matched,
    }
    print(json.dumps(summary, ensure_ascii=True, indent=2))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge Story Points into a Jira export CSV by issue Key.")
    parser.add_argument("target_csv", help="CSV to enrich (updated in place unless --output is set)")
    parser.add_argument(
        "reference_csvs",
        nargs="+",
        help="One or more Jira CSV exports containing Story Points",
    )
    parser.add_argument("--output", help="Optional output path (default: overwrite target)")
    args = parser.parse_args()
    merge_story_points(Path(args.target_csv), [Path(p) for p in args.reference_csvs], Path(args.output) if args.output else None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
