from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator


class ResolvedEvent(BaseModel):
    query: str
    event_name: str
    location_text: str
    start_date: date
    end_date: date
    hazard: str
    resolution_source: str
    confidence: float = Field(ge=0, le=1)
    latitude: float | None = None
    longitude: float | None = None

    @model_validator(mode="after")
    def valid_range(self) -> "ResolvedEvent":
        if self.end_date < self.start_date:
            raise ValueError("end_date must not precede start_date")
        return self


class DistrictMatch(BaseModel):
    district_id: str
    name: str
    admin1: str
    country_or_area: str
    latitude: float
    longitude: float
    match_reason: str
    boundary: list[list[float]] = Field(default_factory=list)
    boundary_source: str = "offline-demo"
    boundary_status: str = "illustrative"
    boundary_year: str | None = None
    boundary_license: str | None = None


class SatelliteAsset(BaseModel):
    filename: str
    platform: str
    product_type: str
    processing_level: str
    acquisition_date: date
    acquisition_datetime: datetime | None = None
    district_id: str
    orbit_direction: str | None = None
    polarization: str | None = None
    bands: list[str] = Field(default_factory=list)
    crs: str
    spatial_resolution_m: float | None = None
    footprint: list[list[float]] = Field(default_factory=list)
    temporal_phase: str = "UNKNOWN"
    source_catalog: str
    catalog_status: str
    verified_remote: bool = False
    notes: str = ""


class DiscoveryRequest(BaseModel):
    query: str
    start_date: date | None = None
    end_date: date | None = None
    platforms: list[str] = Field(default_factory=list)
    product_types: list[str] = Field(default_factory=list)


class DiscoveryResult(BaseModel):
    event: ResolvedEvent
    districts: list[DistrictMatch]
    assets: list[SatelliteAsset]
    filters_applied: dict[str, object]
    warnings: list[str] = Field(default_factory=list)
    catalog_quality_run_id: str | None = None
    catalog_quality_report: str | None = None
