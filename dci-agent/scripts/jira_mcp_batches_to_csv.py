"""Merge Jira MCP batch JSON files into a DCI-compatible CSV."""

from __future__ import annotations

import argparse
import json
from datetime import date

from dci_agent.jira_mcp_csv import build_jql, write_batches_to_csv


def _parse_date(value: str, field_name: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise SystemExit(f"{field_name} must be YYYY-MM-DD") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert Jira MCP batch JSON to DCI CSV.")
    parser.add_argument(
        "--batch-dir",
        default="tmp/jira_batches",
        help="Directory containing batch_*.json files from jira_search",
    )
    parser.add_argument(
        "--output-csv",
        default="../jira-export-mcp.csv",
        help="Output CSV path (DCI-compatible headers)",
    )
    parser.add_argument(
        "--summary",
        default="out/jira_fetch_summary.json",
        help="Write fetch summary JSON here",
    )
    parser.add_argument("--period-start", help="Reporting window start (YYYY-MM-DD)")
    parser.add_argument("--period-end", help="Reporting window end (YYYY-MM-DD)")
    parser.add_argument(
        "--print-jql-only",
        action="store_true",
        help="Print JQL for period-start/end and exit (no CSV conversion)",
    )
    args = parser.parse_args()

    if args.period_start and args.period_end:
        period_start = _parse_date(args.period_start, "period-start")
        period_end = _parse_date(args.period_end, "period-end")
        if period_end < period_start:
            raise SystemExit("period-end cannot be earlier than period-start")
        print(build_jql(period_start, period_end))
        if args.print_jql_only:
            return 0

    summary = write_batches_to_csv(
        args.batch_dir,
        args.output_csv,
        summary_path=args.summary,
    )
    print(json.dumps(summary, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
