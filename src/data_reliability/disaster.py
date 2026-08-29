from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import date
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


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GAZETTEER = PROJECT_ROOT / "catalog" / "gazetteer.json"
DEFAULT_CATALOG = PROJECT_ROOT / "catalog" / "satellite_assets.csv"


def _deterministic_event(query: str) -> ResolvedEvent:
    lower = query.casefold()
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
        "event_name, location_text, start_date, end_date, hazard, confidence. Dates must be YYYY-MM-DD. "
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
        with urlopen(request, timeout=60) as response:
            envelope = json.loads(response.read().decode())
        payload = json.loads(envelope["response"])
        return ResolvedEvent(
            query=query,
            event_name=payload["event_name"],
            location_text=payload["location_text"],
            start_date=payload["start_date"],
            end_date=payload["end_date"],
            hazard=payload["hazard"],
            resolution_source=f"ollama:{model}",
            confidence=float(payload.get("confidence", 0.5)),
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
            ))
    return matches


def load_asset_catalog(path: str | Path = DEFAULT_CATALOG) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["acquisition_date"] = pd.to_datetime(frame["acquisition_date"], errors="raise").dt.date
    return frame


def discover_assets(
    request: DiscoveryRequest,
    mode: str = "ollama",
    catalog_path: str | Path = DEFAULT_CATALOG,
    gazetteer_path: str | Path = DEFAULT_GAZETTEER,
    verify_catalog: bool = True,
    output_root: str | Path = "outputs",
) -> DiscoveryResult:
    event = resolve_event(request.query, mode)
    if request.start_date:
        event.start_date = request.start_date
    if request.end_date:
        event.end_date = request.end_date
    if event.end_date < event.start_date:
        raise ValueError("End date must not precede start date")

    districts = match_districts(event.location_text, request.query, gazetteer_path)
    frame = load_asset_catalog(catalog_path)
    district_ids = {district.district_id for district in districts}
    selected = frame[
        frame["district_id"].isin(district_ids)
        & frame["acquisition_date"].between(event.start_date, event.end_date)
    ].copy()
    if request.platforms:
        selected = selected[selected["platform"].isin(request.platforms)]
    if request.product_types:
        selected = selected[selected["product_type"].isin(request.product_types)]
    selected = selected.sort_values(["acquisition_date", "platform", "filename"])
    records = selected.astype(object).where(pd.notna(selected), None).to_dict(orient="records")
    assets = [SatelliteAsset.model_validate(record) for record in records]

    warnings = []
    if not districts:
        warnings.append("No district matched the offline gazetteer; add a verified district record before operational use.")
    if any(asset.catalog_status == "illustrative" for asset in assets):
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
            "start_date": event.start_date.isoformat(),
            "end_date": event.end_date.isoformat(),
            "platforms": request.platforms,
            "product_types": request.product_types,
            "district_ids": sorted(district_ids),
        },
        warnings=warnings,
        catalog_quality_run_id=run_id,
        catalog_quality_report=report,
    )
