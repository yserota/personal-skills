from pathlib import Path
import unittest

from dci_agent.dashboard_export import build_dashboard_exports
from dci_agent.io_utils import read_csv


ROOT = Path(__file__).resolve().parents[1]


class DashboardExportTests(unittest.TestCase):
    def test_build_dashboard_exports_from_scores(self) -> None:
        rows = read_csv(ROOT / "out/dci_writer_scores.csv")
        exports = build_dashboard_exports(rows)
        self.assertIn("Tab0_Cover", exports)
        self.assertIn("Tab2_Writer_Scorecard", exports)
        self.assertGreater(len(exports["Tab0_Cover"]), 5)
        self.assertEqual(len(exports["Tab2_Writer_Scorecard"]), len(rows))
        scorecard = exports["Tab2_Writer_Scorecard"][0]
        self.assertIn("operational_dci", scorecard)
        self.assertIn("ai_adoption_pct", scorecard)


if __name__ == "__main__":
    unittest.main()
