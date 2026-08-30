from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import date, datetime, time, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

import pandas as pd

from .disaster_models import (
    DiscoveryRequest,
    DiscoveryResult,
    DistrictMatch,
    ResolvedEvent,
    SatelliteAsset,
)
from .orchestrator import investigate
from .boundaries import resolve_political_boundaries


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GAZETTEER = PROJECT_ROOT / "catalog" / "gazetteer.json"
DEFAULT_CATALOG = PROJECT_ROOT / "catalog" / "satellite_assets.csv"


def _planning_target(event: ResolvedEvent) -> DistrictMatch | None:
    """Create an explicitly non-administrative search area for uncatalogued events."""
    if event.latitude is None or event.longitude is None:
        return None
    half_size = 0.55
    lon, lat = event.longitude, event.latitude
    boundary = [
        [lon - half_size, lat - half_size], [lon + half_size, lat - half_size],
        [lon + half_size, lat + half_size], [lon - half_size, lat + half_size],
        [lon - half_size, lat - half_size],
    ]
    return DistrictMatch(
        district_id="dynamic-planning-area",
        name=f"Planning area near {event.location_text}",
        admin1="Unresolved administrative area",
        country_or_area="Resolved by event coordinates",
        latitude=lat,
        longitude=lon,
        match_reason="coordinate-centered fallback; not a political boundary",
        boundary=boundary,
        boundary_source="generated-search-area",
        boundary_status="illustrative-planning-area",
    )


def _illustrative_candidates(
    event: ResolvedEvent, filter_start: date, filter_end: date
) -> list[SatelliteAsset]:
    """Build transparent demo candidates when no curated archive rows match."""
    if event.latitude is None or event.longitude is None:
        return []
    sample_dates = sorted({filter_start, max(filter_start, min(event.start_date, filter_end)), filter_end})
    products = [
        ("Sentinel-1C", "SAR_GRD", "GRD", ["VV", "VH"], 10.0, "DESCENDING"),
        ("Sentinel-1C", "SAR_SLC", "SLC", ["VV", "VH"], 5.0, "ASCENDING"),
        ("Sentinel-2", "OPTICAL_L2A", "L2A", ["B02", "B03", "B04", "B08", "B11", "B12"], 10.0, None),
        ("Landsat 9", "OPTICAL_L2SP", "L2SP", ["SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7"], 30.0, None),
    ]
    hazard_note = {
        "flood": "SAR GRD is prioritized for cloud-tolerant flood extent mapping.",
        "storm": "SAR and optical candidates support post-storm comparison.",
        "cyclone": "SAR and optical candidates support post-cyclone comparison.",
        "wildfire": "Optical NIR/SWIR candidates support burn-severity assessment.",
        "landslide": "Optical and SAR candidates support surface-change assessment.",
        "earthquake": "SAR SLC candidates support potential InSAR analysis.",
    }.get(event.hazard.casefold(), "Candidate mix supports general before/after assessment.")
    assets: list[SatelliteAsset] = []
    for date_index, acquired in enumerate(sample_dates):
        for product_index, (platform, product_type, level, bands, resolution, orbit) in enumerate(products):
            offset = (product_index - 1.5) * 0.06
            half_width = 0.62 + product_index * 0.04
            lon, lat = event.longitude + offset, event.latitude - offset
            footprint = [
                [lon - half_width, lat - half_width], [lon + half_width, lat - half_width],
                [lon + half_width, lat + half_width], [lon - half_width, lat + half_width],
                [lon - half_width, lat - half_width],
            ]
            prefix = platform.upper().replace(" ", "-")
            filename = f"ILLUSTRATIVE_{prefix}_{level}_{acquired:%Y%m%d}_{date_index + 1:02d}"
            temporal_phase = "PRE_EVENT" if acquired < event.start_date else (
                "EVENT_DAY" if acquired == event.start_date else "POST_EVENT"
            )
            assets.append(SatelliteAsset(
                filename=filename,
                platform=platform,
                product_type=product_type,
                processing_level=level,
                acquisition_date=acquired,
                acquisition_datetime=datetime.combine(acquired, time(10, 30), tzinfo=timezone.utc),
                district_id="dynamic-planning-area",
                orbit_direction=orbit,
                polarization="VV|VH" if product_type.startswith("SAR") else None,
                bands=bands,
                crs="EPSG:4326 (planning footprint)",
                spatial_resolution_m=resolution,
                footprint=footprint,
                temporal_phase=temporal_phase,
                source_catalog="generated demonstration candidate",
                catalog_status="illustrative-unverified",
                verified_remote=False,
                notes=f"{hazard_note} This is a generated candidate name, not a confirmed provider asset.",
            ))
    return assets


def _deterministic_event(query: str) -> ResolvedEvent:
    lower = query.casefold()
    if "flood" in lower and any(term in lower for term in ("sukkur", "larkana", "pakistan")):
        return ResolvedEvent(
            query=query,
            event_name="2022 Pakistan floods",
            location_text="Sukkur and Larkana, Sindh, Pakistan",
            start_date=date(2022, 8, 14),
            end_date=date(2022, 9, 15),
            hazard="flood",
            resolution_source="deterministic-demo-gazetteer",
            confidence=0.72,
            latitude=27.70,
            longitude=68.50,
        )
    if any(term in lower for term in ("dingri", "tingri", "tibet", "nepal")):
        return ResolvedEvent(
            query=query,
            event_name="Southern Tibetan Plateau earthquake",
            location_text="Dingri County, Shigatse, Tibet",
            start_date=date(2025, 1, 7),
            end_date=date(2025, 1, 21),
            hazard="earthquake",
            resolution_source="deterministic-demo-gazetteer",
            confidence=0.75,
            latitude=28.639,
            longitude=87.360,
        )
    today = date.today()
    return ResolvedEvent(
        query=query,
        event_name=query.strip() or "Unspecified event",
        location_text=query.strip(),
        start_date=today,
        end_date=today,
        hazard="unknown",
        resolution_source="unresolved-fallback",
        confidence=0.1,
    )


def resolve_event(query: str, mode: str = "ollama") -> ResolvedEvent:
    if mode != "ollama":
        return _deterministic_event(query)
    model = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    prompt = (
        "Resolve the disaster description into structured metadata. Return JSON only with "
        "event_name, location_text, start_date, end_date, hazard, confidence, latitude, longitude. Dates must be YYYY-MM-DD. "
        "If uncertain, say so through a low confidence; never invent satellite product IDs. "
        f"Description: {query}"
    )
    request = Request(
        f"{base_url}/api/generate",
        data=json.dumps({"model": model, "prompt": prompt, "stream": False, "format": "json"}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        ollama_timeout = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "5"))
        with urlopen(request, timeout=ollama_timeout) as response:
            envelope = json.loads(response.read().decode())
        payload = json.loads(envelope["response"])
        if payload.get("latitude") is None or payload.get("longitude") is None:
            raise ValueError("Ollama response did not contain mappable coordinates")
        return ResolvedEvent(
            query=query,
            event_name=payload["event_name"],
            location_text=payload["location_text"],
            start_date=payload["start_date"],
            end_date=payload["end_date"],
            hazard=payload["hazard"],
            resolution_source=f"ollama:{model}",
            confidence=float(payload.get("confidence", 0.5)),
            latitude=payload.get("latitude"),
            longitude=payload.get("longitude"),
        )
    except (URLError, TimeoutError, KeyError, ValueError, json.JSONDecodeError):
        fallback = _deterministic_event(query)
        fallback.resolution_source = "deterministic-fallback"
        return fallback


def load_gazetteer(path: str | Path = DEFAULT_GAZETTEER) -> list[dict[str, object]]:
    return json.loads(Path(path).read_text(encoding="utf-8"))["districts"]


def match_districts(location_text: str, query: str, gazetteer_path: str | Path = DEFAULT_GAZETTEER) -> list[DistrictMatch]:
    text = f"{location_text} {query}".casefold()
    matches: list[DistrictMatch] = []
    for item in load_gazetteer(gazetteer_path):
        aliases = [str(item["name"]), *[str(alias) for alias in item.get("aliases", [])]]
        matched = next((alias for alias in aliases if re.search(rf"\b{re.escape(alias.casefold())}\b", text)), None)
        region_match = str(item.get("region_keyword", "")).casefold() in text
        if matched or region_match:
            matches.append(DistrictMatch(
                district_id=str(item["district_id"]),
                name=str(item["name"]),
                admin1=str(item["admin1"]),
                country_or_area=str(item["country_or_area"]),
                latitude=float(item["latitude"]),
                longitude=float(item["longitude"]),
                match_reason=f"alias:{matched}" if matched else f"regional context:{item['region_keyword']}",
                boundary=item.get("boundary", []),
            ))
    return matches


def load_asset_catalog(path: str | Path = DEFAULT_CATALOG) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["acquisition_date"] = pd.to_datetime(frame["acquisition_date"], errors="raise").dt.date
    frame["bands"] = frame["bands"].fillna("").map(lambda value: [item for item in str(value).split("|") if item])
    frame["footprint"] = frame.apply(
        lambda row: [[row.min_lon, row.min_lat], [row.max_lon, row.min_lat],
                     [row.max_lon, row.max_lat], [row.min_lon, row.max_lat],
                     [row.min_lon, row.min_lat]], axis=1
    )
    frame = frame.drop(columns=["min_lon", "min_lat", "max_lon", "max_lat"])
    return frame


def discover_assets(
    request: DiscoveryRequest,
    mode: str = "ollama",
    catalog_path: str | Path = DEFAULT_CATALOG,
    gazetteer_path: str | Path = DEFAULT_GAZETTEER,
    verify_catalog: bool = True,
    output_root: str | Path = "outputs",
    boundary_mode: str = "live",
) -> DiscoveryResult:
    event = resolve_event(request.query, mode)
    filter_start = request.start_date or event.start_date
    filter_end = request.end_date or event.end_date
    if filter_end < filter_start:
        raise ValueError("End date must not precede start date")

    districts = match_districts(event.location_text, request.query, gazetteer_path)
    boundary_warnings = []
    if boundary_mode == "live" and districts:
        boundary_warnings = resolve_political_boundaries(districts, Path(output_root) / "boundary_cache")
    frame = load_asset_catalog(catalog_path)
    district_ids = {district.district_id for district in districts}
    selected = frame[
        frame["district_id"].isin(district_ids)
        & frame["acquisition_date"].between(filter_start, filter_end)
    ].copy()
    if request.platforms:
        selected = selected[selected["platform"].isin(request.platforms)]
    if request.product_types:
        selected = selected[selected["product_type"].isin(request.product_types)]
    selected = selected.sort_values(["acquisition_date", "platform", "filename"])
    selected["temporal_phase"] = selected["acquisition_date"].map(
        lambda acquired: "PRE_EVENT" if acquired < event.start_date else (
            "EVENT_DAY" if acquired == event.start_date else "POST_EVENT"
        )
    )
    records = selected.astype(object).where(pd.notna(selected), None).to_dict(orient="records")
    assets = [SatelliteAsset.model_validate(record) for record in records]

    if not districts:
        planning_target = _planning_target(event)
        if planning_target:
            districts = [planning_target]
    if not assets:
        assets = _illustrative_candidates(event, filter_start, filter_end)
        if request.platforms:
            assets = [asset for asset in assets if asset.platform in request.platforms]
        if request.product_types:
            assets = [asset for asset in assets if asset.product_type in request.product_types]

    warnings = list(boundary_warnings)
    if not districts:
        warnings.append("No district matched the offline gazetteer; add a verified district record before operational use.")
    elif any(district.boundary_status == "illustrative-planning-area" for district in districts):
        warnings.append("No political boundary matched; the displayed target is an illustrative coordinate-centered planning area.")
    if any(asset.catalog_status.startswith("illustrative") for asset in assets):
        warnings.append("Illustrative filenames demonstrate filtering and product semantics; verify exact archive availability before operational use.")
    run_id = None
    report = None
    if verify_catalog and len(selected):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as handle:
            quality_path = Path(handle.name)
        selected.to_csv(quality_path, index=False)
        quality = investigate(quality_path, "Verify the reliability of filtered satellite catalog metadata", mode="deterministic", output_root=output_root)
        run_id = quality.run_id
        report = quality.report_path
        quality_path.unlink(missing_ok=True)

    return DiscoveryResult(
        event=event,
        districts=districts,
        assets=assets,
        filters_applied={
            "start_date": filter_start.isoformat(),
            "end_date": filter_end.isoformat(),
            "event_start_date": event.start_date.isoformat(),
            "platforms": request.platforms,
            "product_types": request.product_types,
            "district_ids": sorted(district_ids),
        },
        warnings=warnings,
        catalog_quality_run_id=run_id,
        catalog_quality_report=report,
    )
