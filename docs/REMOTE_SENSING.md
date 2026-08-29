# Remote-sensing workflow

## What the demo does

1. Ollama converts a disaster request into event, location, hazard, and date fields.
2. A small offline gazetteer maps the location to district points.
3. Deterministic filters select satellite metadata by district, acquisition date, platform, and product type.
4. The existing data-reliability engine audits the filtered catalog metadata.
5. The UI presents filenames first and makes their verification status visible.

The bundled catalog is intentionally marked `illustrative`. It demonstrates product naming and workflow behavior without claiming that each exact identifier exists in a remote archive. An operational version should query USGS EarthExplorer/M2M and the Copernicus Data Space APIs, preserve provider identifiers, footprints, cloud cover/orbit metadata, and mark records verified only after a successful catalog response.

## Product semantics

- Landsat 9 Collection 2 Level-2 products are optical surface products.
- Sentinel-1C is a C-band SAR mission; SLC is the appropriate raw product class for interferometric processing.
- An InSAR interferogram is a derived artifact created from a compatible SAR acquisition pair. It is not a raw satellite product, so this project labels it `DERIVED_INSAR` and `DERIVED`.

## Demo limitation

District geometry is represented by point coordinates in a small offline gazetteer, not authoritative administrative polygons. This keeps the demo offline and reproducible. Production integration should use verified boundary geometries and provider catalog searches.

## Authoritative references

- USGS M7.1 Southern Tibetan Plateau event: https://earthquake.usgs.gov/earthquakes/eventpage/us6000pi9w
- Landsat 9 mission: https://www.usgs.gov/landsat-missions/landsat-9
- Landsat Collection 2 naming: https://www.usgs.gov/faqs/what-naming-convention-landsat-collection-2-level-1-and-level-2-scenes
- Copernicus Sentinel-1 product documentation: https://documentation.dataspace.copernicus.eu/Data/Sentinel1.html
- ESA Sentinel-1C launch: https://www.esa.int/Applications/Observing_the_Earth/Copernicus/Sentinel-1/Double_win_for_Europe_Sentinel-1C_and_Vega-C_take_to_the_skies
- ESA InSAR explanation and Sentinel-1C demonstration: https://www.esa.int/Applications/Observing_the_Earth/Copernicus/Sentinel-1/Sentinel-1C_demonstrates_power_to_map_land_deformation
