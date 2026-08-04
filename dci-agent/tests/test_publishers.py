import unittest

from dci_agent.publishers import _upsert_by_key


class PublisherTests(unittest.TestCase):
    def test_upsert_by_key_is_idempotent(self) -> None:
        existing = [
            {
                "writer_id": "w-001",
                "period_start": "2026-05-01",
                "period_end": "2026-05-14",
                "dci": "0.9",
            }
        ]
        incoming = [
            {
                "writer_id": "w-001",
                "period_start": "2026-05-01",
                "period_end": "2026-05-14",
                "dci": "0.8",
            }
        ]

        merged_once = _upsert_by_key(existing, incoming)
        merged_twice = _upsert_by_key(merged_once, incoming)

        self.assertEqual(len(merged_once), 1)
        self.assertEqual(len(merged_twice), 1)
        self.assertEqual(merged_twice[0]["dci"], "0.8")


if __name__ == "__main__":
    unittest.main()
