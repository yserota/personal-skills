import unittest
from pathlib import Path

from dci_agent.manager_mapping import apply_manager_mapping


ROOT = Path(__file__).resolve().parents[1]


class ManagerMappingTests(unittest.TestCase):
    def test_apply_manager_mapping_by_writer_name(self) -> None:
        rows = [
            {
                "writer_id": "w-001",
                "writer_name": "Jane Doe",
                "pod": "",
            }
        ]
        result = apply_manager_mapping(rows, ROOT / "tests/fixtures/writer_manager_map.csv")
        self.assertEqual(result.rows[0]["manager_name"], "Adam Christensen")
        self.assertEqual(result.rows[0]["pod"], "Pod 1")
        self.assertEqual(result.unmapped_writers, [])

    def test_unmapped_writer_reported(self) -> None:
        rows = [{"writer_id": "unknown", "writer_name": "Unknown Person", "pod": ""}]
        result = apply_manager_mapping(rows, ROOT / "tests/fixtures/writer_manager_map.csv")
        self.assertEqual(result.rows[0]["manager_name"], "")
        self.assertEqual(result.unmapped_writers, ["Unknown Person"])


if __name__ == "__main__":
    unittest.main()
