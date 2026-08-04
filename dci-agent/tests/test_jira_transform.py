from datetime import date
from pathlib import Path
import unittest

from dci_agent.jira_transform import transform_jira_export


ROOT = Path(__file__).resolve().parents[1]


class JiraTransformTests(unittest.TestCase):
    def test_transform_jira_sample(self) -> None:
        result = transform_jira_export(
            ROOT / "tests/fixtures/jira_raw_sample.tsv",
            period_start=date(2026, 5, 1),
            period_end=date(2026, 5, 14),
        )
        self.assertEqual(len(result.skipped_rows), 0)
        self.assertEqual(len(result.normalized_rows), 3)
        matt = [r for r in result.normalized_rows if r["writer_name"] == "Matt Thies"][0]
        rick = [r for r in result.normalized_rows if r["writer_name"] == "Rick Fox"][0]
        self.assertEqual(matt["manual_vs_ai_flag"], "ai")
        self.assertEqual(rick["manual_vs_ai_flag"], "manual")
        self.assertEqual(matt["ai_finished_count"], 1)
        self.assertEqual(rick["manual_finished_count"], 1)
        self.assertEqual(matt["resolved_count"], 1)
        self.assertEqual(matt["story_points_finished"], 8.0)
        self.assertEqual(rick["story_points_finished"], 3.0)
        self.assertEqual(matt["intake_count"], 1)
        self.assertGreaterEqual(matt["avg_queue_lag_days"], 0.0)


if __name__ == "__main__":
    unittest.main()
