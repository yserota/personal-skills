"""Main pipeline launcher with optional Google Sheets publishing."""

from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path

from dci_agent.pipeline import run_pipeline


def _configure_logging(output_dir: str) -> None:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    log_file = Path(output_dir) / "run.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(log_file, encoding="utf-8"), logging.StreamHandler()],
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run DCI pipeline.")
    parser.add_argument("--input-csv", required=True)
    parser.add_argument("--schema", default="config/input_schema.yaml")
    parser.add_argument("--formula", default="config/dci_formula.yaml")
    parser.add_argument("--output-dir", default="out")
    parser.add_argument(
        "--publish-target",
        choices=["none", "google_sheets"],
        default=os.getenv("DCI_PUBLISH_TARGET", "none"),
    )
    parser.add_argument(
        "--manager-map",
        default=os.getenv("DCI_MANAGER_MAP_PATH", "config/writer_manager_map.csv"),
        help="CSV mapping writer to manager (set empty to disable)",
    )
    parser.add_argument(
        "--teams",
        default=None,
        help="Comma-separated team names to include (e.g. 'Execution,Standards'). Omit for all.",
    )
    parser.add_argument(
        "--pods",
        default=None,
        help="Comma-separated pod names to include (e.g. 'Pod 1,Pod 2'). Omit for all.",
    )
    parser.add_argument(
        "--managers",
        default=None,
        help="Comma-separated manager names to include (e.g. 'Adam Christensen'). Omit for all.",
    )
    args = parser.parse_args()
    _configure_logging(args.output_dir)
    logging.info("DCI pipeline starting")

    publish_cfg = None
    target = None if args.publish_target == "none" else args.publish_target
    if target == "google_sheets":
        publish_cfg = {
            "sheet_id": os.getenv("DCI_GOOGLE_SHEET_ID", ""),
            "service_account_json_path": os.getenv("DCI_GOOGLE_SERVICE_ACCOUNT_JSON_PATH", ""),
            "worksheet_name": os.getenv("DCI_GOOGLE_WORKSHEET", "dci_writer_scores"),
            "audit_worksheet_name": os.getenv("DCI_GOOGLE_AUDIT_WORKSHEET", "run_audit_log"),
        }

    manager_map = args.manager_map.strip() or None
    if manager_map and not Path(manager_map).exists():
        logging.warning("Manager map not found: %s", manager_map)
        manager_map = None

    def _parse_csv_list(value: str | None) -> list[str] | None:
        if not value:
            return None
        return [v.strip() for v in value.split(",") if v.strip()]

    try:
        summary = run_pipeline(
            input_csv_path=args.input_csv,
            schema_path=args.schema,
            formula_path=args.formula,
            output_dir=args.output_dir,
            publish_target=target,
            publish_config=publish_cfg,
            manager_map_path=manager_map,
            teams=_parse_csv_list(args.teams),
            pods=_parse_csv_list(args.pods),
            managers=_parse_csv_list(args.managers),
        )
    except Exception:
        logging.exception("DCI pipeline failed")
        return 2

    logging.info(
        "DCI pipeline completed. accepted=%s rejected=%s",
        summary["rows_accepted"],
        summary["rows_rejected"],
    )
    print(json.dumps(summary, ensure_ascii=True))
    return 0 if summary["rows_rejected"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
