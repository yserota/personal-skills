from pathlib import Path
import tempfile
import unittest

from dci_agent.pipeline import run_pipeline


ROOT = Path(__file__).resolve().parents[1]


class PipelineTests(unittest.TestCase):
    def test_pipeline_writes_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            summary = run_pipeline(
                input_csv_path=str(ROOT / "tests/fixtures/input_valid.csv"),
                schema_path=str(ROOT / "config/input_schema.yaml"),
                formula_path=str(ROOT / "config/dci_formula.yaml"),
                output_dir=str(tmp_path),
                publish_target=None,
                manager_map_path=str(ROOT / "tests/fixtures/writer_manager_map.csv"),
            )
            self.assertEqual(summary["rows_received"], 2)
            self.assertEqual(summary["rows_rejected"], 0)
            self.assertEqual(summary["unmapped_writers"], [])
            self.assertTrue((tmp_path / "dci_writer_scores.csv").exists())
            self.assertTrue((tmp_path / "rejected_rows.csv").exists())
            self.assertTrue((tmp_path / "run_summary.json").exists())


if __name__ == "__main__":
    unittest.main()
