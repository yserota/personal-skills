from datetime import date
from pathlib import Path
import csv
import json
import tempfile
import unittest

from dci_agent.jira_mcp_csv import (
    batches_to_rows,
    build_jql,
    issue_to_csv_row,
    write_batches_to_csv,
)
from dci_agent.jira_transform import transform_jira_export


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/jira_mcp_batch_sample.json"


class JiraMcpCsvTests(unittest.TestCase):
    def test_build_jql(self) -> None:
        jql = build_jql(date(2026, 1, 1), date(2026, 6, 30))
        self.assertIn('project in (DOC, DOCS)', jql)
        self.assertIn('"StartWork" >= "2026-01-01"', jql)
        self.assertIn('created <= "2026-06-30"', jql)

    def test_issue_to_csv_row(self) -> None:
        issues = json.loads(FIXTURE.read_text(encoding="utf-8"))
        row = issue_to_csv_row(issues[0])
        self.assertEqual(row["Key"], "DOC-22649")
        self.assertEqual(row["Assignee"], "kreuveny")
        self.assertEqual(row["Assigned Technical Writer"], "kreuveny")
        self.assertEqual(row["Created"], "2026-05-27")
        issues[0]["customfield_10128"] = {"value": 5}
        row_with_sp = issue_to_csv_row(issues[0])
        self.assertEqual(row_with_sp["Story Points"], "5")

    def test_batches_to_csv_and_transform(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            batch_dir = Path(tmp)
            (batch_dir / "batch_0001.json").write_text(
                FIXTURE.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            output_csv = batch_dir / "jira-export-mcp.csv"
            summary = write_batches_to_csv(batch_dir, output_csv, summary_path=None)
            self.assertEqual(summary["issues_written"], 3)

            with output_csv.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 3)
            self.assertIn("TW-AI Usage", rows[0])

            result = transform_jira_export(
                output_csv,
                period_start=date(2026, 5, 1),
                period_end=date(2026, 5, 31),
                manager_map_path=ROOT / "tests/fixtures/writer_manager_map.csv",
                roster_only=False,
            )
            self.assertGreaterEqual(len(result.normalized_rows), 1)


if __name__ == "__main__":
    unittest.main()
