from __future__ import annotations

import tempfile
from datetime import date
from pathlib import Path

import pandas as pd
import pydeck as pdk
import streamlit as st

from .disaster import discover_assets
from .disaster_models import DiscoveryRequest
from .orchestrator import investigate
from .repairs import apply_approved_repairs


def disaster_finder() -> None:
    st.header("Disaster satellite evidence finder")
    st.caption("Resolve place and time with Ollama, map matched districts, then list candidate filenames first.")
    query = st.text_area("Disaster requirement", "January 2025 earthquake near Dingri, Tibet and Nepal", key="disaster_query")
    left, right = st.columns(2)
    start = left.date_input("Start date", date(2025, 1, 1))
    end = right.date_input("End date", date(2025, 1, 31))
    platforms = st.multiselect("Platforms", ["LANDSAT_9", "SENTINEL_1C"], default=["LANDSAT_9", "SENTINEL_1C"])
    products = st.multiselect("Products", ["OPTICAL_L2SP", "SAR_SLC", "SAR_GRD", "DERIVED_INSAR"], default=["OPTICAL_L2SP", "SAR_SLC", "SAR_GRD", "DERIVED_INSAR"])
    mode = st.selectbox("Event resolution", ["ollama", "deterministic"], help="Ollama resolves free text; deterministic mode keeps the demo reproducible.")
    if st.button("Find satellite candidates", type="primary"):
        if end < start:
            st.error("End date must not precede start date.")
        else:
            with st.spinner("Resolving event, matching districts, filtering candidates, and verifying catalog metadata..."):
                st.session_state["discovery_result"] = discover_assets(DiscoveryRequest(
                    query=query, start_date=start, end_date=end, platforms=platforms, product_types=products
                ), mode=mode)

    result = st.session_state.get("discovery_result")
    if not result:
        return
    event = result.event
    a, b, c = st.columns(3)
    a.metric("Resolved event", event.event_name)
    b.metric("Candidate files", len(result.assets))
    c.metric("Resolver confidence", f"{event.confidence:.0%}")
    st.write(f"**Location:** {event.location_text} · **Hazard:** {event.hazard} · **Resolver:** {event.resolution_source}")
    if result.districts:
        district_records = [{
            "polygon": d.boundary, "title": d.name, "kind": "TARGET DISTRICT",
            "detail": f"{d.admin1} · {d.country_or_area}", "time": "Event area",
            "crs": "EPSG:4326 display", "bands": "—",
        } for d in result.districts if d.boundary]
        asset_records = [{
            "polygon": asset.footprint, "title": asset.filename, "kind": "SATELLITE FOOTPRINT",
            "detail": f"{asset.platform} · {asset.product_type}",
            "time": asset.acquisition_datetime.isoformat() if asset.acquisition_datetime else asset.acquisition_date.isoformat(),
            "crs": asset.crs, "bands": ", ".join(asset.bands),
            "fill": [33, 150, 243, 55] if asset.platform == "SENTINEL_1C" else [46, 204, 113, 55],
        } for asset in result.assets if asset.footprint]
        center_lat = sum(d.latitude for d in result.districts) / len(result.districts)
        center_lon = sum(d.longitude for d in result.districts) / len(result.districts)
        target_layer = pdk.Layer(
            "PolygonLayer", district_records, get_polygon="polygon",
            get_fill_color=[220, 38, 38, 25], get_line_color=[239, 68, 68, 255],
            line_width_min_pixels=3, stroked=True, filled=True, pickable=True,
        )
        scene_layer = pdk.Layer(
            "PolygonLayer", asset_records, get_polygon="polygon", get_fill_color="fill",
            get_line_color=[37, 99, 235, 210], line_width_min_pixels=2,
            stroked=True, filled=True, pickable=True,
        )
        tooltip = {"html": (
            "<b>{kind}</b><br/><b>{title}</b><hr/>"
            "{detail}<br/><b>Time:</b> {time}<br/><b>CRS:</b> {crs}<br/><b>Bands:</b> {bands}"
        ), "style": {"backgroundColor": "#111827", "color": "white"}}
        st.markdown("**Map layers:** 🔴 target district boundary · 🔵 Sentinel-1C footprint · 🟢 Landsat 9 footprint")
        st.pydeck_chart(pdk.Deck(
            layers=[scene_layer, target_layer],
            initial_view_state=pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=7.2, pitch=0),
            map_style="light", tooltip=tooltip,
        ), use_container_width=True, height=590)
    for warning in result.warnings:
        st.warning(warning)
    st.subheader("Candidate filenames")
    if result.assets:
        assets = pd.DataFrame([asset.model_dump(mode="json") for asset in result.assets])
        selected_name = st.selectbox("Inspect a satellite candidate", [asset.filename for asset in result.assets])
        selected = next(asset for asset in result.assets if asset.filename == selected_name)
        meta_left, meta_right = st.columns(2)
        with meta_left:
            st.markdown(f"**Platform / product:** {selected.platform} / {selected.product_type}")
            st.markdown(f"**Acquisition:** {selected.acquisition_datetime or selected.acquisition_date}")
            st.markdown(f"**CRS / resolution:** {selected.crs} / {selected.spatial_resolution_m or 'unknown'} m")
        with meta_right:
            st.markdown(f"**Bands or polarizations:** {', '.join(selected.bands) or 'not supplied'}")
            st.markdown(f"**Orbit:** {selected.orbit_direction or 'not applicable'}")
            st.markdown(f"**Catalog status:** {selected.catalog_status} · remote verified: {selected.verified_remote}")
        st.caption(selected.notes)
        ordered = ["filename", "platform", "product_type", "acquisition_datetime", "bands", "crs", "spatial_resolution_m", "district_id", "catalog_status", "verified_remote"]
        st.dataframe(assets[ordered], hide_index=True, use_container_width=True)
        st.download_button("Download candidate metadata", result.model_dump_json(indent=2), "satellite-candidates.json", "application/json")
    else:
        st.info("No candidates match the selected districts, dates, platforms, and products.")
    if result.catalog_quality_report:
        st.caption(f"Catalog metadata quality run: {result.catalog_quality_run_id}")


def table_investigator() -> None:
    st.header("Table reliability investigator")
    st.caption("Agent-selected checks. Deterministic evidence. Human-approved repairs.")
    uploaded = st.file_uploader("Upload a table", type=["csv", "xlsx", "json", "parquet"])
    goal = st.text_area("What decision will this data support?", "Assess whether this dataset is reliable for KPI reporting")
    mode = st.selectbox("Planning mode", ["ollama", "deterministic"], key="table_mode")
    if uploaded and st.button("Investigate table", type="primary"):
        workspace = Path(tempfile.mkdtemp(prefix="data-reliability-"))
        source = workspace / uploaded.name
        source.write_bytes(uploaded.getvalue())
        with st.spinner("Profiling, planning checks, gathering evidence, and verifying claims..."):
            st.session_state["table_result"] = investigate(source, goal, mode=mode, output_root=workspace / "outputs")
    result = st.session_state.get("table_result")
    if not result:
        return
    left, middle, right = st.columns(3)
    left.metric("Rows", result.profile.rows)
    middle.metric("Verified findings", len(result.findings))
    right.metric("Planning source", result.plan.source)
    for finding in result.findings:
        with st.expander(f"{finding.severity.value.upper()} · {finding.title}", expanded=True):
            st.write(finding.detail)
            st.json(finding.evidence.model_dump(mode="json"))
    st.download_button("Download evidence report", Path(result.report_path).read_bytes(), "data-reliability-report.md")
    if result.repair_proposals:
        st.subheader("Human-approved repairs")
        st.warning("Repairs create a new file. The uploaded source is never overwritten.")
        approved = [p.proposal_id for p in result.repair_proposals if st.checkbox(f"{p.action.value}: {p.reason} — {p.risk}", key=p.proposal_id)]
        if st.button("Create repaired copy", disabled=not approved):
            source = Path(result.profile.path)
            output = source.with_name(f"{source.stem}.repaired{source.suffix}")
            repair_result = apply_approved_repairs(source, output, result.repair_proposals, set(approved))
            st.success("Repaired copy created: " + "; ".join(repair_result.changes_applied))
            st.download_button("Download repaired copy", output.read_bytes(), output.name)


def main() -> None:
    st.set_page_config(page_title="GeoReliability Agent", page_icon="🛰️", layout="wide")
    st.title("GeoReliability Agent")
    st.caption("From a disaster question to mapped districts, satellite candidates, and verified data evidence.")
    disaster_tab, data_tab = st.tabs(["🛰️ Disaster & satellite", "🔎 Data quality"])
    with disaster_tab:
        disaster_finder()
    with data_tab:
        table_investigator()


if __name__ == "__main__":
    main()
