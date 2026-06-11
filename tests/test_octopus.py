import unittest
from datetime import datetime, timezone

from octopus_agile_tracker.octopus import AgileRate, dedupe_rates, iso_z, parse_dt


class OctopusTests(unittest.TestCase):
    def test_iso_z_uses_utc_z_suffix(self) -> None:
        value = datetime(2026, 6, 11, 12, 34, 56, tzinfo=timezone.utc)
        self.assertEqual(iso_z(value), "2026-06-11T12:34:56Z")

    def test_parse_dt_accepts_z(self) -> None:
        self.assertEqual(parse_dt("2026-06-11T12:30:00Z"), datetime(2026, 6, 11, 12, 30, tzinfo=timezone.utc))

    def test_dedupe_rates_preserves_first(self) -> None:
        valid_from = datetime(2026, 6, 11, 12, 30, tzinfo=timezone.utc)
        valid_to = datetime(2026, 6, 11, 13, 0, tzinfo=timezone.utc)
        fetched_at = datetime(2026, 6, 11, 12, 0, tzinfo=timezone.utc)
        first = AgileRate("p", "t", "A", "", valid_from, valid_to, 1.0, 1.2, fetched_at, "url1")
        second = AgileRate("p", "t", "A", "", valid_from, valid_to, 2.0, 2.4, fetched_at, "url2")
        self.assertEqual(dedupe_rates([first, second]), [first])


if __name__ == "__main__":
    unittest.main()

