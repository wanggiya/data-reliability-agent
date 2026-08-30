from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from data_reliability.boundaries import _point_in_ring, resolve_political_boundaries
from data_reliability.disaster_models import DistrictMatch


class BoundaryProviderTests(unittest.TestCase):
    def test_point_in_polygon(self) -> None:
        ring = [[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]]
        self.assertTrue(_point_in_ring(1, 1, ring))
        self.assertFalse(_point_in_ring(3, 1, ring))

    @patch("data_reliability.boundaries._country_boundaries")
    def test_provider_geometry_replaces_fallback(self, provider) -> None:
        provider.return_value = (
            {"boundaryID": "NPL-ADM2-test", "boundaryYearRepresented": "2006", "boundaryLicense": "Public Domain"},
            {"features": [{"properties": {"shapeName": "Solukhumbu"}, "geometry": {"type": "Polygon", "coordinates": [[[86, 27], [87, 27], [87, 28], [86, 28], [86, 27]]]}}]},
        )
        district = DistrictMatch(district_id="NP-P1-SOLU", name="fallback", admin1="Koshi", country_or_area="Nepal", latitude=27.7, longitude=86.6, match_reason="test", boundary=[[0, 0], [1, 0], [0, 0]])
        with tempfile.TemporaryDirectory() as temp:
            warnings = resolve_political_boundaries([district], Path(temp))
        self.assertEqual(warnings, [])
        self.assertEqual(district.name, "Solukhumbu")
        self.assertEqual(district.boundary_status, "authoritative-provider")
        self.assertIn("geoBoundaries", district.boundary_source)


if __name__ == "__main__":
    unittest.main()
