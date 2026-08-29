from __future__ import annotations

from fastapi import FastAPI, HTTPException

from .disaster import discover_assets
from .disaster_models import DiscoveryRequest, DiscoveryResult


app = FastAPI(title="GeoReliability API", version="0.2.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/discover", response_model=DiscoveryResult)
def discover(request: DiscoveryRequest, mode: str = "ollama") -> DiscoveryResult:
    if mode not in {"ollama", "deterministic"}:
        raise HTTPException(status_code=400, detail="mode must be ollama or deterministic")
    try:
        return discover_assets(request, mode=mode)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
