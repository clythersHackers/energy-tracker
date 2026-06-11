import unittest
from datetime import datetime, timezone

from octopus_agile_tracker.clickhouse import clickhouse_dt, ttl_clause_for_days


class ClickHouseTests(unittest.TestCase):
    def test_clickhouse_dt_uses_datetime64_friendly_utc_format(self) -> None:
        value = datetime(2026, 6, 11, 12, 34, 56, 789123, tzinfo=timezone.utc)
        self.assertEqual(clickhouse_dt(value), "2026-06-11 12:34:56.789")

    def test_ttl_clause_disabled_for_zero_days(self) -> None:
        self.assertEqual(ttl_clause_for_days(0), "")

    def test_ttl_clause_uses_valid_to(self) -> None:
        self.assertEqual(ttl_clause_for_days(730), " TTL valid_to + INTERVAL 730 DAY DELETE")


if __name__ == "__main__":
    unittest.main()
