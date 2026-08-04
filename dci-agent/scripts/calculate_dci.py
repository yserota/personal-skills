"""Calculate DCI scores and write canonical outputs."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from dci_agent.pipeline import run_pipeline


def main() -> int:
    parser = argparse.ArgumentParser(description="Run DCI calculation only.")
    parser.add_argument("--input-csv", required=True)
    parser.add_argument("--schema", default="config/input_schema.yaml")
    parser.add_argument("--formula", default="config/dci_formula.yaml")
    parser.add_argument("--output-dir", default="out")
    parser.add_argument(
        "--manager-map",
        default=os.getenv("DCI_MANAGER_MAP_PATH", "config/writer_manager_map.csv"),
    )
    args = parser.parse_args()

    manager_map = args.manager_map.strip() or None
    if manager_map and not Path(manager_map).exists():
        manager_map = None

    summary = run_pipeline(
        input_csv_path=args.input_csv,
        schema_path=args.schema,
        formula_path=args.formula,
        output_dir=args.output_dir,
        publish_target=None,
        manager_map_path=manager_map,
    )
    print(json.dumps(summary, ensure_ascii=True))
    return 0 if summary["rows_rejected"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
