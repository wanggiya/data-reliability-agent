from __future__ import annotations

import json
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from .disaster_models import DistrictMatch


COUNTRY_ISO = {"CN-XZ-DINGRI": "CHN", "NP-P1-SOLU": "NPL", "NP-P3-DOLAKHA": "NPL"}


def _point_in_ring(longitude: float, latitude: float, ring: list[list[float]]) -> bool:
    inside = False
    previous = ring[-1]
    for current in ring:
        x1, y1 = previous[:2]
        x2, y2 = current[:2]
        if (y1 > latitude) != (y2 > latitude):
            crossing = (x2 - x1) * (latitude - y1) / (y2 - y1) + x1
            if longitude < crossing:
                inside = not inside
        previous = current
    return inside


def _outer_rings(geometry: dict) -> list[list[list[float]]]:
    if geometry.get("type") == "Polygon":
        return [geometry["coordinates"][0]]
    if geometry.get("type") == "MultiPolygon":
        return [polygon[0] for polygon in geometry["coordinates"]]
    return []


def _read_json(url: str) -> dict:
    request = Request(url, headers={"User-Agent": "GeoReliability-Hackathon/0.3"})
    with urlopen(request, timeout=8) as response:
        return json.loads(response.read().decode("utf-8"))


def _country_boundaries(iso: str, cache_root: Path) -> tuple[dict, dict]:
    cache_root.mkdir(parents=True, exist_ok=True)
    cache = cache_root / f"geoboundaries-{iso}-ADM2.json"
    metadata_cache = cache_root / f"geoboundaries-{iso}-ADM2-metadata.json"
    if cache.exists() and metadata_cache.exists():
        return json.loads(metadata_cache.read_text(encoding="utf-8")), json.loads(cache.read_text(encoding="utf-8"))
    metadata = _read_json(f"https://www.geoboundaries.org/api/current/gbOpen/{iso}/ADM2/")
    geojson = _read_json(metadata["simplifiedGeometryGeoJSON"])
    metadata_cache.write_text(json.dumps(metadata), encoding="utf-8")
    cache.write_text(json.dumps(geojson), encoding="utf-8")
    return metadata, geojson


def resolve_political_boundaries(
    districts: list[DistrictMatch], cache_root: str | Path = "outputs/boundary_cache"
) -> list[str]:
    warnings: list[str] = []
    by_country: dict[str, list[DistrictMatch]] = {}
    for district in districts:
        iso = COUNTRY_ISO.get(district.district_id)
        if iso:
            by_country.setdefault(iso, []).append(district)
    for iso, country_districts in by_country.items():
        try:
            metadata, geojson = _country_boundaries(iso, Path(cache_root))
            for district in country_districts:
                matched = None
                for feature in geojson.get("features", []):
                    for ring in _outer_rings(feature.get("geometry", {})):
                        if _point_in_ring(district.longitude, district.latitude, ring):
                            matched = (feature, ring)
                            break
                    if matched:
                        break
                if not matched:
                    warnings.append(f"No geoBoundaries ADM2 polygon contained {district.name}; retained illustrative fallback.")
                    continue
                feature, ring = matched
                district.boundary = ring
                district.name = str(feature.get("properties", {}).get("shapeName") or district.name)
                district.boundary_source = f"geoBoundaries {metadata.get('boundaryID', iso)}"
                district.boundary_status = "authoritative-provider"
                district.boundary_year = str(metadata.get("boundaryYearRepresented", "")) or None
                district.boundary_license = metadata.get("boundaryLicense")
        except (URLError, TimeoutError, KeyError, ValueError, OSError, json.JSONDecodeError) as error:
            warnings.append(f"geoBoundaries was unavailable for {iso}; using visibly labeled illustrative fallback ({type(error).__name__}).")
    return warnings
