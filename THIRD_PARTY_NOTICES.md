# Third-party services and attribution

This prototype does not redistribute map tiles or boundary datasets. The browser requests them from their providers at runtime, and availability or permitted use remains subject to each provider's current terms.

| Component or service | Use | License / attribution |
|---|---|---|
| OpenLayers 10.6.1 | Browser map rendering | BSD 2-Clause; https://openlayers.org/ |
| Turf.js 7.2.0 | Browser geometry operations | MIT; https://github.com/Turfjs/turf |
| jsDelivr | CDN delivery of OpenLayers and Turf.js | https://www.jsdelivr.com/terms |
| geoBoundaries `gbOpen` | Optional live administrative boundaries | CC BY 4.0; © geoBoundaries, https://www.geoboundaries.org/ |
| Esri World Topographic Map, World Imagery, World Hillshade, and Hydro Reference Overlay | Optional runtime basemap/context tiles | © Esri and contributing data providers; service credits are shown in the map. See https://www.esri.com/en-us/legal/terms/web-site-service |
| CARTO basemaps | Streamlit fallback map styles | © OpenStreetMap contributors, © CARTO; https://carto.com/legal |
| Ollama | Optional local planning runtime | https://github.com/ollama/ollama; the selected model has its own license |

Satellite mission names and product descriptions refer to public USGS, ESA, and Copernicus documentation. The bundled scene identifiers, footprints, and affected-area textures are explicitly illustrative planning metadata and are not redistributed provider imagery.

Before deploying beyond a noncommercial hackathon demonstration, replace public anonymous tile endpoints with a service plan appropriate to the expected traffic and recheck the providers' current terms.
