from __future__ import annotations

import unittest
from datetime import date
from unittest.mock import patch

from data_reliability.disaster import discover_assets, match_districts, resolve_event
from data_reliability.disaster_models import DiscoveryRequest, ResolvedEvent


class DisasterDiscoveryTests(unittest.TestCase):
    def test_deterministic_resolution(self) -> None:
        event = resolve_event("January 2025 Dingri Tibet earthquake", mode="deterministic")
        self.assertEqual(event.start_date, date(2025, 1, 7))
        self.assertEqual(event.hazard, "earthquake")

    def test_pakistan_flood_demo_has_mappable_fallback(self) -> None:
        event = resolve_event("August 2022 floods near Sukkur and Larkana, Pakistan", mode="deterministic")
        self.assertEqual(event.hazard, "flood")
        self.assertIsNotNone(event.latitude)
        self.assertIsNotNone(event.longitude)
        result = discover_assets(DiscoveryRequest(
            query=event.query, start_date=date(2022, 8, 1), end_date=date(2022, 9, 15)
        ), mode="deterministic", verify_catalog=False, boundary_mode="offline")
        self.assertEqual(len(result.districts[0].boundary), 25)
        self.assertEqual(result.districts[0].boundary_status, "illustrative-planning-area")

    def test_district_matching_includes_cross_border_context(self) -> None:
        matches = match_districts("Dingri County, Tibet", "earthquake affecting Tibet and Nepal")
        self.assertEqual({item.district_id for item in matches}, {"CN-XZ-DINGRI", "NP-P1-SOLU", "NP-P3-DOLAKHA"})

    def test_discovery_filters_dates_and_keeps_filename_first_contract(self) -> None:
        result = discover_assets(DiscoveryRequest(
            query="Dingri Tibet Nepal earthquake",
            start_date=date(2025, 1, 7), end_date=date(2025, 1, 10),
        ), mode="deterministic", verify_catalog=False, boundary_mode="offline")
        self.assertTrue(result.assets)
        self.assertTrue(all(date(2025, 1, 7) <= item.acquisition_date <= date(2025, 1, 10) for item in result.assets))
        self.assertTrue(all(item.catalog_status == "illustrative" for item in result.assets))

    def test_insar_is_explicitly_derived(self) -> None:
        result = discover_assets(DiscoveryRequest(
            query="Dingri Tibet earthquake",
            start_date=date(2025, 1, 1), end_date=date(2025, 1, 31),
            product_types=["DERIVED_INSAR"],
        ), mode="deterministic", verify_catalog=False, boundary_mode="offline")
        self.assertEqual(len(result.assets), 1)
        self.assertEqual(result.assets[0].processing_level, "DERIVED")
        self.assertIn("not a raw Sentinel product", result.assets[0].notes)

    def test_map_geometry_and_scene_metadata_are_exposed(self) -> None:
        result = discover_assets(DiscoveryRequest(
            query="Dingri Tibet earthquake", start_date=date(2025, 1, 1), end_date=date(2025, 1, 31)
        ), mode="deterministic", verify_catalog=False, boundary_mode="offline")
        self.assertTrue(all(len(district.boundary) >= 4 for district in result.districts))
        self.assertTrue(all(len(asset.footprint) == 5 for asset in result.assets))
        self.assertTrue(all(asset.crs and asset.bands and asset.acquisition_datetime for asset in result.assets))

    def test_event_date_is_preserved_and_acquisitions_are_phased(self) -> None:
        result = discover_assets(DiscoveryRequest(
            query="Dingri Tibet earthquake", start_date=date(2025, 1, 1), end_date=date(2025, 1, 31)
        ), mode="deterministic", verify_catalog=False, boundary_mode="offline")
        self.assertEqual(result.event.start_date, date(2025, 1, 7))
        self.assertIn("SENTINEL_2", {asset.platform for asset in result.assets})
        self.assertIn("PRE_EVENT", {asset.temporal_phase for asset in result.assets})
        self.assertIn("POST_EVENT", {asset.temporal_phase for asset in result.assets})

    def test_uncatalogued_flood_gets_labeled_planning_candidates(self) -> None:
        flood = ResolvedEvent(
            query="July 2026 river flood near Test City",
            event_name="Test City flood",
            location_text="Test City",
            start_date=date(2026, 7, 10),
            end_date=date(2026, 7, 14),
            hazard="flood",
            resolution_source="ollama:test",
            confidence=0.8,
            latitude=35.0,
            longitude=-90.0,
        )
        with patch("data_reliability.disaster.resolve_event", return_value=flood):
            result = discover_assets(DiscoveryRequest(
                query=flood.query,
                start_date=date(2026, 7, 5),
                end_date=date(2026, 7, 20),
            ), verify_catalog=False, boundary_mode="offline")
        self.assertEqual(result.districts[0].boundary_status, "illustrative-planning-area")
        self.assertTrue(result.assets)
        self.assertIn("SAR_GRD", {asset.product_type for asset in result.assets})
        self.assertTrue(all(asset.filename.startswith("ILLUSTRATIVE_") for asset in result.assets))
        self.assertTrue(all(not asset.verified_remote for asset in result.assets))
        self.assertTrue(any("not a confirmed provider asset" in asset.notes for asset in result.assets))


if __name__ == "__main__":
    unittest.main()
