from __future__ import annotations

import unittest
from datetime import date

from data_reliability.disaster import discover_assets, match_districts, resolve_event
from data_reliability.disaster_models import DiscoveryRequest


class DisasterDiscoveryTests(unittest.TestCase):
    def test_deterministic_resolution(self) -> None:
        event = resolve_event("January 2025 Dingri Tibet earthquake", mode="deterministic")
        self.assertEqual(event.start_date, date(2025, 1, 7))
        self.assertEqual(event.hazard, "earthquake")

    def test_district_matching_includes_cross_border_context(self) -> None:
        matches = match_districts("Dingri County, Tibet", "earthquake affecting Tibet and Nepal")
        self.assertEqual({item.district_id for item in matches}, {"CN-XZ-DINGRI", "NP-P1-SOLU", "NP-P3-DOLAKHA"})

    def test_discovery_filters_dates_and_keeps_filename_first_contract(self) -> None:
        result = discover_assets(DiscoveryRequest(
            query="Dingri Tibet Nepal earthquake",
            start_date=date(2025, 1, 7), end_date=date(2025, 1, 10),
        ), mode="deterministic", verify_catalog=False)
        self.assertTrue(result.assets)
        self.assertTrue(all(date(2025, 1, 7) <= item.acquisition_date <= date(2025, 1, 10) for item in result.assets))
        self.assertTrue(all(item.catalog_status == "illustrative" for item in result.assets))

    def test_insar_is_explicitly_derived(self) -> None:
        result = discover_assets(DiscoveryRequest(
            query="Dingri Tibet earthquake",
            start_date=date(2025, 1, 1), end_date=date(2025, 1, 31),
            product_types=["DERIVED_INSAR"],
        ), mode="deterministic", verify_catalog=False)
        self.assertEqual(len(result.assets), 1)
        self.assertEqual(result.assets[0].processing_level, "DERIVED")
        self.assertIn("not a raw Sentinel product", result.assets[0].notes)


if __name__ == "__main__":
    unittest.main()
