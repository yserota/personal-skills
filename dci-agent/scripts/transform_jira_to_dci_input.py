"""Transform raw Jira export into normalized DCI input CSV."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from dci_agent.io_utils import write_csv, write_json
from dci_agent.jira_transform import transform_jira_export


def _parse_date(value: str, field_name: str) -> date:
    try:
        return date.fromisoformat(value)
    except Exception as exc:
        raise SystemExit(f"{field_name} must be YYYY-MM-DD") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize Jira export for DCI pipeline.")
    parser.add_argument("--jira-input", required=True, help="Path to raw Jira CSV/TSV export")
    parser.add_argument("--period-start", required=True, help="YYYY-MM-DD")
    parser.add_argument("--period-end", required=True, help="YYYY-MM-DD")
    parser.add_argument("--output-csv", default="data/input.from_jira.csv")
    parser.add_argument("--output-summary", default="out/jira_transform_summary.json")
    parser.add_argument(
        "--manager-map",
        default="config/writer_manager_map.csv",
        help="TW roster filter source (use --no-roster-only to disable filtering)",
    )
    parser.add_argument("--no-roster-only", action="store_true")
    args = parser.parse_args()

    period_start = _parse_date(args.period_start, "period-start")
    period_end = _parse_date(args.period_end, "period-end")
    if period_end < period_start:
        raise SystemExit("period-end cannot be earlier than period-start")

    transformed = transform_jira_export(
        args.jira_input,
        period_start,
        period_end,
        manager_map_path=args.manager_map,
        roster_only=not args.no_roster_only,
    )
    write_csv(args.output_csv, transformed.normalized_rows)

    summary = {
        "jira_input": args.jira_input,
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "normalized_rows": len(transformed.normalized_rows),
        "skipped_rows": len(transformed.skipped_rows),
        "output_csv": args.output_csv,
        "sample_skipped": transformed.skipped_rows[:20],
    }
    Path(args.output_summary).parent.mkdir(parents=True, exist_ok=True)
    write_json(args.output_summary, summary)
    print(json.dumps(summary, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
