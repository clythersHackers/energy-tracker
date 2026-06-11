import unittest

from octopus_agile_tracker.config import product_from_tariff, region_from_tariff


class ConfigTests(unittest.TestCase):
    def test_product_from_tariff_with_region_suffix(self) -> None:
        self.assertEqual(product_from_tariff("E-1R-AGILE-FLEX-22-11-25-A"), "AGILE-FLEX-22-11-25")

    def test_region_from_tariff(self) -> None:
        self.assertEqual(region_from_tariff("E-1R-AGILE-FLEX-22-11-25-A"), "A")


if __name__ == "__main__":
    unittest.main()

