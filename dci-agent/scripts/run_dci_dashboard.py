"""End-to-end DCI dashboard run: Jira export → scores → dashboard tabs."""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _configure_logging(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    log_file = output_dir / "run.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(log_file, encoding="utf-8"), logging.StreamHandler()],
    )


def _run_step(label: str, command: list[str]) -> int:
    logging.info("Running %s: %s", label, " ".join(command))
    completed = subprocess.run(command, cwd=ROOT, check=False)
    if completed.returncode != 0:
        logging.error("%s failed with exit code %s", label, completed.returncode)
    return completed.returncode


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run full DCI dashboard workflow (Jira transform + score + dashboard tabs)."
    )
    parser.add_argument(
        "--jira-input",
        default=os.getenv("DCI_JIRA_INPUT", str(ROOT.parent / "jira-export.csv")),
        help="Path to raw Jira CSV export",
    )
    parser.add_argument(
        "--period-start",
        default=os.getenv("DCI_PERIOD_START", "2026-01-01"),
        help="Reporting window start (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--period-end",
        default=os.getenv("DCI_PERIOD_END", "2026-03-31"),
        help="Reporting window end (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--input-csv",
        default=os.getenv("DCI_INPUT_CSV_PATH", "data/input.from_jira.csv"),
        help="Normalized input CSV path",
    )
    parser.add_argument("--output-dir", default=os.getenv("DCI_OUTPUT_DIR", "out"))
    parser.add_argument(
        "--manager-map",
        default=os.getenv("DCI_MANAGER_MAP_PATH", "config/writer_manager_map.csv"),
    )
    parser.add_argument(
        "--skip-transform",
        action="store_true",
        help="Skip Jira transform; use existing --input-csv",
    )
    parser.add_argument(
        "--publish-target",
        choices=["none", "google_sheets", "excel"],
        default=os.getenv("DCI_PUBLISH_TARGET", "none"),
    )
    parser.add_argument(
        "--sheet-id",
        default=os.getenv("DCI_GOOGLE_SHEET_ID", ""),
        help="Google Sheets spreadsheet ID (required when --publish-target=google_sheets)",
    )
    parser.add_argument(
        "--service-account-json",
        default=os.getenv("DCI_GOOGLE_SERVICE_ACCOUNT_JSON_PATH", ""),
        help="Path to GCP service-account key JSON (required when --publish-target=google_sheets)",
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

    output_dir = Path(args.output_dir)
    _configure_logging(output_dir)

    jira_path = Path(args.jira_input)
    if not args.skip_transform:
        if not jira_path.exists():
            logging.error("Jira export not found: %s", jira_path)
            return 2
        transform_code = _run_step(
            "jira-transform",
            [
                sys.executable,
                "scripts/transform_jira_to_dci_input.py",
                "--jira-input",
                str(jira_path),
                "--period-start",
                args.period_start,
                "--period-end",
                args.period_end,
                "--output-csv",
                args.input_csv,
                "--manager-map",
                args.manager_map,
            ],
        )
        if transform_code != 0:
            return transform_code

    input_csv = Path(args.input_csv)
    if not input_csv.exists():
        logging.error("Input CSV not found: %s", input_csv)
        return 2

    # run_pipeline.py only understands none/google_sheets; excel is handled here
    pipeline_publish = args.publish_target if args.publish_target in ("none", "google_sheets") else "none"
    pipeline_command = [
        sys.executable,
        "scripts/run_pipeline.py",
        "--input-csv",
        str(input_csv),
        "--output-dir",
        str(output_dir),
        "--publish-target",
        pipeline_publish,
        "--manager-map",
        args.manager_map,
    ]
    if args.teams:
        pipeline_command += ["--teams", args.teams]
    if args.pods:
        pipeline_command += ["--pods", args.pods]
    if args.managers:
        pipeline_command += ["--managers", args.managers]
    pipeline_code = _run_step("dci-pipeline", pipeline_command)
    if pipeline_code != 0:
        return pipeline_code

    dashboard_dir = output_dir / "dashboard"
    tab_names = sorted(p.name for p in dashboard_dir.glob("Tab*.csv")) if dashboard_dir.exists() else []

    excel_path: str = ""
    if args.publish_target == "excel":
        period_label = f"{args.period_start}_to_{args.period_end}".replace("-", "")
        xlsx_file = output_dir / f"DCI_Dashboard_{period_label}.xlsx"
        logging.info("Building Excel workbook → %s", xlsx_file)
        tabs: dict[str, list[dict[str, str]]] = {}
        for tab_file in sorted(dashboard_dir.glob("Tab*.csv")):
            with tab_file.open(encoding="utf-8", newline="") as fh:
                tabs[tab_file.stem] = list(csv.DictReader(fh))
        try:
            from dci_agent.publishers import publish_excel
            result = publish_excel(tabs=tabs, output_path=xlsx_file)
            excel_path = str(xlsx_file)
            logging.info("Excel workbook written: %s (%d rows)", excel_path, result.rows_written)
        except Exception as exc:
            logging.error("Excel export failed: %s", exc)
            return 3

    sheets_url: str = ""
    if args.publish_target == "google_sheets":
        if not args.sheet_id or not args.service_account_json:
            logging.error(
                "--sheet-id and --service-account-json are required when --publish-target=google_sheets"
            )
            return 2
        logging.info("Uploading %d dashboard tabs to Google Sheets …", len(tab_names))
        tabs: dict[str, list[dict[str, str]]] = {}
        for tab_file in sorted(dashboard_dir.glob("Tab*.csv")):
            with tab_file.open(encoding="utf-8", newline="") as fh:
                tabs[tab_file.stem] = list(csv.DictReader(fh))
        try:
            from dci_agent.publishers import publish_dashboard_tabs
            result = publish_dashboard_tabs(
                tabs=tabs,
                sheet_id=args.sheet_id,
                service_account_json_path=args.service_account_json,
            )
            sheets_url = f"https://docs.google.com/spreadsheets/d/{args.sheet_id}"
            logging.info(
                "Uploaded %d rows across %d tabs → %s",
                result.rows_written,
                len(tabs),
                sheets_url,
            )
        except Exception as exc:
            logging.error("Google Sheets upload failed: %s", exc)
            return 3

    # Read SP DCI and scope from run_summary.json written by the pipeline
    summary_path = output_dir / "run_summary.json"
    org_sp_dci: float | None = None
    org_sp_coverage_pct: float | None = None
    if summary_path.exists():
        with summary_path.open(encoding="utf-8") as _f:
            _run_summary = json.load(_f)
        org_sp_dci = _run_summary.get("org_sp_dci")
        org_sp_coverage_pct = _run_summary.get("org_sp_coverage_pct")

    deliverables: dict[str, object] = {
        "period_start": args.period_start,
        "period_end": args.period_end,
        "scope_teams": args.teams,
        "scope_pods": args.pods,
        "scope_managers": args.managers,
        "org_sp_dci": org_sp_dci,
        "org_sp_coverage_pct": org_sp_coverage_pct,
        "writers_scored_csv": str(output_dir / "dci_writer_scores.csv"),
        "ai_impact_md": str(output_dir / "DCI_AI_Impact_Analysis.md"),
        "ai_impact_csv": str(output_dir / "dci_ai_impact_summary.csv"),
        "dashboard_dir": str(dashboard_dir),
        "dashboard_tabs": tab_names,
        "dashboard_readme": str(dashboard_dir / "README_Google_Sheets_Dashboard.md"),
        "run_summary": str(output_dir / "run_summary.json"),
    }
    if excel_path:
        deliverables["excel_workbook"] = excel_path
    if sheets_url:
        deliverables["google_sheet_url"] = sheets_url
    print(json.dumps(deliverables, ensure_ascii=True, indent=2))
    logging.info("Dashboard run complete. Import tabs from %s", dashboard_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
