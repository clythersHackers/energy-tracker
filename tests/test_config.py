import unittest
from unittest.mock import patch

from octopus_agile_tracker.config import load_config, product_from_tariff, region_from_tariff


class ConfigTests(unittest.TestCase):
    def test_product_from_tariff_with_region_suffix(self) -> None:
        self.assertEqual(product_from_tariff("X-Y-PRODUCT-CODE-A"), "PRODUCT-CODE")

    def test_region_from_tariff(self) -> None:
        self.assertEqual(region_from_tariff("X-Y-PRODUCT-CODE-A"), "A")

    def test_version_defaults_to_unknown(self) -> None:
        with patch.dict("os.environ", {"OCTOPUS_TARIFF_CODE": "X-Y-PRODUCT-CODE-A"}, clear=True):
            self.assertEqual(load_config().version, "unknown")

    def test_version_comes_from_environment(self) -> None:
        with patch.dict(
            "os.environ",
            {"ENERGY_TRACKER_VERSION": "0.1.4", "OCTOPUS_TARIFF_CODE": "X-Y-PRODUCT-CODE-A"},
            clear=True,
        ):
            self.assertEqual(load_config().version, "0.1.4")


if __name__ == "__main__":
    unittest.main()
