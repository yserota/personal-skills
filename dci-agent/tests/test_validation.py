from pathlib import Path
import unittest

from dci_agent.io_utils import load_yaml, read_csv
from dci_agent.validation import validate_rows


ROOT = Path(__file__).resolve().parents[1]


class ValidationTests(unittest.TestCase):
    def test_validation_accepts_valid_rows(self) -> None:
        rows = read_csv(ROOT / "tests/fixtures/input_valid.csv")
        schema = load_yaml(ROOT / "config/input_schema.yaml")
        result = validate_rows(rows, schema)
        self.assertEqual(len(result.accepted_rows), 2)
        self.assertEqual(len(result.rejected_rows), 0)

    def test_validation_rejects_invalid_rows(self) -> None:
        rows = read_csv(ROOT / "tests/fixtures/input_invalid.csv")
        schema = load_yaml(ROOT / "config/input_schema.yaml")
        result = validate_rows(rows, schema)
        self.assertEqual(len(result.accepted_rows), 0)
        self.assertEqual(len(result.rejected_rows), 3)


if __name__ == "__main__":
    unittest.main()
