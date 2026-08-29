from __future__ import annotations

from fastapi import FastAPI, HTTPException

from .disaster import discover_assets, load_asset_catalog, load_gazetteer
from .disaster_models import DiscoveryRequest, DiscoveryResult


app = FastAPI(title="GeoReliability API", version="0.2.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/catalog/options")
def catalog_options() -> dict[str, object]:
    catalog = load_asset_catalog()
    return {
        "platforms": sorted(catalog["platform"].unique().tolist()),
        "product_types": sorted(catalog["product_type"].unique().tolist()),
        "crs": sorted(catalog["crs"].unique().tolist()),
        "districts": [{"district_id": item["district_id"], "name": item["name"]} for item in load_gazetteer()],
        "geometry_status": "illustrative-demo",
    }


@app.post("/discover", response_model=DiscoveryResult)
def discover(request: DiscoveryRequest, mode: str = "ollama") -> DiscoveryResult:
    if mode not in {"ollama", "deterministic"}:
        raise HTTPException(status_code=400, detail="mode must be ollama or deterministic")
    try:
        return discover_assets(request, mode=mode)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
