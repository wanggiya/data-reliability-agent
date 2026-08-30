from __future__ import annotations

import unittest
from pathlib import Path


class OpenLayersFrontendTests(unittest.TestCase):
    def test_full_screen_map_contract(self) -> None:
        root = Path(__file__).resolve().parents[1] / "web"
        html = (root / "index.html").read_text(encoding="utf-8")
        css = (root / "styles.css").read_text(encoding="utf-8")
        script = (root / "app.js").read_text(encoding="utf-8")
        self.assertIn('id="map"', html)
        self.assertIn("html,body,#map", css)
        self.assertIn("data-layer=\"DERIVED_INSAR\"", html)
        self.assertIn("Acquisition timeline", html)
        self.assertIn("new Map", script)
        self.assertIn("Affected-area planning zone", script)
        self.assertIn('id="basemap"', html)
        self.assertIn("data-collapse", html)
        self.assertIn("className:'basemap-dark'", script)
        self.assertIn("extent.every(Number.isFinite)", script)
        self.assertIn("World_Imagery", script)
        self.assertIn("World_Topo_Map", script)
        self.assertIn("World_Hillshade", script)
        self.assertIn("Esri_Hydro_Reference_Overlay", script)
        self.assertIn("Illustrative flood planning zone", script)
        self.assertIn("setZIndex(80)", script)
        self.assertIn("hatchPattern", script)
        self.assertIn('id="report"', html)
        self.assertIn("downloadReport", script)
        self.assertIn('class="dual-range"', html)
        self.assertIn("turf.intersect", script)
        self.assertIn("Political-area image overlap", script)
        self.assertIn("Radius-influenced image overlap", script)
        self.assertIn("hydroLayer.setZIndex(65)", script)
        self.assertIn('id="boundary-texture"', html)
        self.assertIn('id="impact-texture"', html)
        self.assertIn("boundaryCoverageLayers).forEach", script)
        self.assertIn("impactCoverageLayers).forEach", script)
        self.assertIn("dist/ol.js", html)


if __name__ == "__main__":
    unittest.main()
