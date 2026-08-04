"""Validate input CSV against DCI schema."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from dci_agent.io_utils import load_yaml, read_csv
from dci_agent.validation import validate_rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate DCI input CSV.")
    parser.add_argument("--input-csv", required=True)
    parser.add_argument("--schema", default="config/input_schema.yaml")
    parser.add_argument("--output-json", default="out/validation_summary.json")
    args = parser.parse_args()

    rows = read_csv(args.input_csv)
    schema = load_yaml(args.schema)
    result = validate_rows(rows, schema)
    summary = {
        "rows_received": len(rows),
        "rows_accepted": len(result.accepted_rows),
        "rows_rejected": len(result.rejected_rows),
        "sample_rejections": result.rejected_rows[:10],
    }
    Path(args.output_json).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output_json, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=True, default=str)
    print(json.dumps(summary, ensure_ascii=True))
    return 0 if summary["rows_rejected"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
