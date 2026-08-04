from pathlib import Path
import unittest

from dci_agent.calculation import calculate_dci
from dci_agent.io_utils import load_yaml, read_csv
from dci_agent.validation import validate_rows


ROOT = Path(__file__).resolve().parents[1]


class CalculationTests(unittest.TestCase):
    def _validated(self, path: str):
        schema = load_yaml(ROOT / "config/input_schema.yaml")
        rows = read_csv(ROOT / path)
        result = validate_rows(rows, schema)
        self.assertEqual(len(result.rejected_rows), 0)
        return result.accepted_rows

    def test_calculate_dci_values(self) -> None:
        formula = load_yaml(ROOT / "config/dci_formula.yaml")
        accepted_rows = self._validated("tests/fixtures/input_valid.csv")
        for row in accepted_rows:
            row["intake_count"] = 22.0
            row["avg_queue_lag_days"] = 3.5
        computed = calculate_dci(accepted_rows, formula)
        self.assertEqual(len(computed.output_rows), 2)
        first = computed.output_rows[0]
        self.assertEqual(first["operational_dci"], 0.8)
        self.assertEqual(first["dci"], 0.8)
        self.assertEqual(first["intake_dci"], 0.88)
        self.assertEqual(first["backlog_pressure"], 2.0)
        self.assertEqual(first["dci_status"], "ok")

    def test_zero_capacity_sets_null_dci(self) -> None:
        formula = load_yaml(ROOT / "config/dci_formula.yaml")
        accepted_rows = self._validated("tests/fixtures/input_zero_capacity.csv")
        computed = calculate_dci(accepted_rows, formula)
        row = computed.output_rows[0]
        self.assertIsNone(row["dci"])
        self.assertEqual(row["dci_status"], "error")
        self.assertEqual(row["dci_reason"], "active_capacity_realized_zero")


if __name__ == "__main__":
    unittest.main()
