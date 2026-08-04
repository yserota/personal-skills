"""Save a Jira MCP search page to tmp/jira_batches/batch_NNNN.json."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Save Jira MCP issues JSON to a batch file.")
    parser.add_argument("batch_num", type=int, help="Batch number (1-based), e.g. 1 -> batch_0001.json")
    parser.add_argument(
        "--input",
        default="-",
        help="Path to JSON file with issues array or {issues: [...]} (default: stdin)",
    )
    parser.add_argument(
        "--batch-dir",
        default="tmp/jira_batches",
        help="Directory for batch_*.json files",
    )
    args = parser.parse_args()

    source = Path(args.input) if args.input != "-" else None
    raw = source.read_text(encoding="utf-8") if source else __import__("sys").stdin.read()
    payload = json.loads(raw)

    if isinstance(payload, list):
        issues = payload
    elif isinstance(payload, dict):
        issues = payload.get("issues") or payload.get("results") or payload.get("data") or []
    else:
        raise SystemExit("Expected JSON array or object with issues key")

    batch_dir = Path(args.batch_dir)
    batch_dir.mkdir(parents=True, exist_ok=True)
    out_path = batch_dir / f"batch_{args.batch_num:04d}.json"
    out_path.write_text(json.dumps(issues, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"batch": str(out_path), "issues": len(issues)}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
