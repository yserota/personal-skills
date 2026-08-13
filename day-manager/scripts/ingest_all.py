"""
Orchestrates day-manager ingestion:
  - Gmail + Calendar: exported by Google Apps Script → synced to local disk by
    Google Drive for Desktop. This script verifies those files exist.
  - Slack: fetched directly via the Slack API by ingest_slack.py.

Usage:
    python scripts/ingest_all.py
    python scripts/ingest_all.py --skip-slack     # verify Drive files only
    python scripts/ingest_all.py --skip-verify    # skip Drive file check
"""

import argparse
import logging
import os
import subprocess
import sys
from datetime import datetime, date
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "ingest.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

SCRIPTS_DIR = Path(__file__).parent
PYTHON = sys.executable
DATA_DIR = Path(os.getenv("DATA_DIR", "data"))

DRIVE_FILES = ["gmail.txt", "calendar.txt"]

# Optional files — warn if missing but don't block the pipeline
DRIVE_FILES_OPTIONAL = ["gemini_notes.txt"]


def check_drive_files() -> bool:
    """
    Verify that today's Gmail and Calendar files exist in DATA_DIR.
    These are written by the Google Apps Script and synced via Google Drive for Desktop.
    Optional files (e.g. gemini_notes.txt) produce a warning but do not fail.
    Returns True if all required files are present.
    """
    today = date.today().strftime("%Y-%m-%d")
    day_dir = DATA_DIR / today
    missing = []

    for filename in DRIVE_FILES:
        filepath = day_dir / filename
        if filepath.exists() and filepath.stat().st_size > 0:
            log.info(f"✓ Found {filepath}")
        else:
            missing.append(str(filepath))

    for filename in DRIVE_FILES_OPTIONAL:
        filepath = day_dir / filename
        if filepath.exists() and filepath.stat().st_size > 0:
            log.info(f"✓ Found {filepath} (optional)")
        else:
            log.warning(
                f"Optional file not found: {filepath}\n"
                f"  Gemini meeting notes will be skipped. "
                f"Check that the Apps Script has run and Google Drive for Desktop has synced."
            )

    if missing:
        log.warning(
            f"Drive files not yet synced — missing:\n"
            + "\n".join(f"  {f}" for f in missing)
            + f"\n\nMake sure:\n"
            + f"  1. The Apps Script has run today (script.google.com → day-manager → Run exportAll)\n"
            + f"  2. Google Drive for Desktop has synced (check the tray icon)\n"
            + f"  3. DATA_DIR in .env points to the synced Drive folder:\n"
            + f"     DATA_DIR={DATA_DIR.resolve()}"
        )
        return False

    log.info(f"Drive files verified for {today}.")
    return True


def run_slack() -> bool:
    """Run the Slack ingestion script. Returns True on success."""
    script = SCRIPTS_DIR / "ingest_slack.py"
    log.info("▶ Starting Slack ingestion…")
    start = datetime.now()
    result = subprocess.run([PYTHON, str(script)])
    elapsed = (datetime.now() - start).total_seconds()
    if result.returncode == 0:
        log.info(f"✓ Slack completed in {elapsed:.1f}s")
        return True
    else:
        log.error(f"✗ Slack failed (exit {result.returncode}) after {elapsed:.1f}s")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run day-manager ingestion.")
    parser.add_argument(
        "--skip-slack",
        action="store_true",
        help="Skip Slack ingestion (verify Drive files only).",
    )
    parser.add_argument(
        "--skip-verify",
        action="store_true",
        help="Skip Drive file verification (useful when running Apps Script manually later).",
    )
    args = parser.parse_args()

    log.info("=" * 60)
    log.info(f"Day Manager ingestion — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info("=" * 60)
    log.info("Gmail + Calendar: provided by Google Apps Script via Drive sync")

    failures = []

    if not args.skip_verify:
        if not check_drive_files():
            failures.append("drive-sync")

    if not args.skip_slack:
        if not run_slack():
            failures.append("slack")

    log.info("-" * 60)
    if failures:
        log.error(f"Issues: {', '.join(failures)}")
        sys.exit(1)
    else:
        log.info("All checks passed. Ready for /manage-my-day in Cursor.")


if __name__ == "__main__":
    main()
