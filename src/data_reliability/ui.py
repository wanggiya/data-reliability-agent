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


def _earth_background() -> None:
    st.subheader("Global disaster monitoring")
    st.caption("Describe an incident in the search panel. The map will fly to the matched target area.")
    st.pydeck_chart(pdk.Deck(
        layers=[],
        initial_view_state=pdk.ViewState(latitude=18, longitude=15, zoom=0.8, pitch=0),
        map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
    ), use_container_width=True, height=680)


def _incident_map(result, visible_assets, show_boundaries: bool, show_affected: bool, impact_radius_km: int) -> None:
    district_records = [{
        "polygon": d.boundary, "title": d.name, "kind": "TARGET ADMINISTRATIVE AREA",
        "detail": f"{d.admin1} · {d.country_or_area}", "time": "Event area",
        "crs": "EPSG:4326 display", "bands": "—", "phase": "—",
        "source": f"{d.boundary_source} · {d.boundary_year or 'year unknown'} · {d.boundary_status}",
    } for d in result.districts if d.boundary]
    colors = {
        "OPTICAL_L2SP": ([34, 197, 94, 65], [22, 163, 74, 240]),
        "OPTICAL_L2A": ([245, 158, 11, 70], [217, 119, 6, 240]),
        "SAR_SLC": ([37, 99, 235, 65], [29, 78, 216, 240]),
        "SAR_GRD": ([6, 182, 212, 65], [8, 145, 178, 240]),
        "DERIVED_INSAR": ([217, 70, 239, 75], [162, 28, 175, 245]),
    }
    asset_records = [{
        "polygon": asset.footprint, "title": asset.filename, "kind": "SATELLITE FOOTPRINT",
        "detail": f"{asset.platform} · {asset.product_type}",
        "time": asset.acquisition_datetime.isoformat() if asset.acquisition_datetime else asset.acquisition_date.isoformat(),
        "crs": asset.crs, "bands": ", ".join(asset.bands), "phase": asset.temporal_phase,
        "source": f"{asset.source_catalog} · {asset.catalog_status}",
        "fill": colors.get(asset.product_type, ([168, 85, 247, 65], [126, 34, 206, 240]))[0],
        "line": colors.get(asset.product_type, ([168, 85, 247, 65], [126, 34, 206, 240]))[1],
    } for asset in visible_assets if asset.footprint]
    coordinates = [point for record in district_records + asset_records for point in record["polygon"]]
    center_lon = (min(p[0] for p in coordinates) + max(p[0] for p in coordinates)) / 2
    center_lat = (min(p[1] for p in coordinates) + max(p[1] for p in coordinates)) / 2
    target_layer = pdk.Layer("PolygonLayer", district_records, get_polygon="polygon", get_fill_color=[220, 38, 38, 8], get_line_color=[255, 45, 45, 255], line_width_min_pixels=4, stroked=True, filled=True, pickable=True)
    scene_layer = pdk.Layer("PolygonLayer", asset_records, get_polygon="polygon", get_fill_color="fill", get_line_color="line", line_width_min_pixels=2, stroked=True, filled=True, pickable=True)
    event_point = [{"position": [result.event.longitude, result.event.latitude], "title": result.event.event_name, "kind": "EVENT EPICENTER", "detail": f"Planning radius: {impact_radius_km} km", "time": result.event.start_date.isoformat(), "crs": "EPSG:4326", "bands": "—", "phase": "EVENT", "source": result.event.resolution_source}] if result.event.longitude is not None and result.event.latitude is not None else []
    impact_layer = pdk.Layer("ScatterplotLayer", event_point, get_position="position", get_radius=impact_radius_km * 1000, get_fill_color=[239, 68, 68, 28], get_line_color=[239, 68, 68, 180], line_width_min_pixels=2, stroked=True, filled=True, pickable=True)
    epicenter_layer = pdk.Layer("ScatterplotLayer", event_point, get_position="position", get_radius=3500, get_fill_color=[220, 38, 38, 240], get_line_color=[255, 255, 255, 255], line_width_min_pixels=2, stroked=True, pickable=True)
    tooltip = {"html": "<b>{kind}</b><br/><b>{title}</b><hr/>{detail}<br/><b>Phase:</b> {phase}<br/><b>Time:</b> {time}<br/><b>CRS:</b> {crs}<br/><b>Bands:</b> {bands}<br/><b>Source:</b> {source}", "style": {"backgroundColor": "rgba(15,23,42,0.88)", "color": "white", "backdropFilter": "blur(8px)"}}
    st.markdown("🔴 boundary/impact · 🟢 Landsat optical · 🟠 Sentinel-2 optical · 🔵 SLC · 🩵 GRD · 🟣 InSAR")
    layers = []
    if show_affected:
        layers.append(impact_layer)
    layers.append(scene_layer)
    if show_boundaries:
        layers.append(target_layer)
    layers.append(epicenter_layer)
    st.pydeck_chart(pdk.Deck(
        layers=layers,
        initial_view_state=pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=6.8, pitch=0),
        map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json", tooltip=tooltip,
    ), use_container_width=True, height=650)


def disaster_finder() -> None:
    with st.sidebar:
        st.header("Incident search")
        query = st.text_area("Disaster requirement", "January 2025 earthquake near Dingri, Tibet and Nepal", key="disaster_query")
        start = st.date_input("Catalog start", date(2025, 1, 1))
        end = st.date_input("Catalog end", date(2025, 1, 31))
        platforms = st.multiselect("Platforms", ["LANDSAT_9", "SENTINEL_1C", "SENTINEL_2"], default=["LANDSAT_9", "SENTINEL_1C", "SENTINEL_2"])
        products = st.multiselect("Products", ["OPTICAL_L2SP", "OPTICAL_L2A", "SAR_SLC", "SAR_GRD", "DERIVED_INSAR"], default=["OPTICAL_L2SP", "OPTICAL_L2A", "SAR_SLC", "SAR_GRD", "DERIVED_INSAR"])
        mode = st.selectbox("Event resolution", ["ollama", "deterministic"])
        st.divider()
        st.subheader("Visible layers")
        show_landsat = st.checkbox("Landsat optical", True)
        show_sentinel2 = st.checkbox("Sentinel-2 optical", True)
        show_slc = st.checkbox("Sentinel-1 SLC", True)
        show_grd = st.checkbox("Sentinel-1 GRD", True)
        show_insar = st.checkbox("Derived InSAR", True)
        show_boundaries = st.checkbox("Administrative boundaries", True)
        show_affected = st.checkbox("Affected-area planning radius", True)
        impact_radius_km = st.slider("Planning radius (km)", 10, 150, 75, 5)
        search = st.button("Locate incident", type="primary", use_container_width=True)
    if search:
        if end < start:
            st.error("End date must not precede start date.")
        else:
            with st.spinner("Resolving event, locating boundaries, and filtering acquisitions..."):
                st.session_state["discovery_result"] = discover_assets(DiscoveryRequest(query=query, start_date=start, end_date=end, platforms=platforms, product_types=products), mode=mode)
                st.session_state.pop("scene_timeline", None)

    result = st.session_state.get("discovery_result")
    if not result:
        _earth_background()
        return
    event = result.event
    visible_assets = result.assets
    if result.assets:
        minimum = min(asset.acquisition_date for asset in result.assets)
        maximum = max(asset.acquisition_date for asset in result.assets)
        timeline = st.slider("Acquisition timeline — narrow this range to update the map", minimum, maximum, (minimum, maximum), key="scene_timeline")
        visible_assets = [asset for asset in result.assets if timeline[0] <= asset.acquisition_date <= timeline[1]]
        enabled_products = set()
        if show_landsat:
            enabled_products.add("OPTICAL_L2SP")
        if show_sentinel2:
            enabled_products.add("OPTICAL_L2A")
        if show_slc:
            enabled_products.add("SAR_SLC")
        if show_grd:
            enabled_products.add("SAR_GRD")
        if show_insar:
            enabled_products.add("DERIVED_INSAR")
        visible_assets = [asset for asset in visible_assets if asset.product_type in enabled_products]
        pre = sum(asset.temporal_phase == "PRE_EVENT" for asset in visible_assets)
        post = sum(asset.temporal_phase == "POST_EVENT" for asset in visible_assets)
        st.caption(f"Event marker: {event.start_date.isoformat()} · visible acquisitions: {len(visible_assets)} · pre-event: {pre} · post-event: {post}")

    if result.districts:
        _incident_map(result, visible_assets, show_boundaries, show_affected, impact_radius_km)
    a, b, c, d = st.columns(4)
    a.metric("Event", event.event_name)
    b.metric("Event date", event.start_date.isoformat())
    c.metric("Visible scenes", len(visible_assets))
    d.metric("Confidence", f"{event.confidence:.0%}")
    st.caption(f"{event.location_text} · {event.hazard} · resolved by {event.resolution_source}")
    coverage = pd.DataFrame([{
        "area": district.name, "candidate_scenes": sum(a.district_id == district.district_id for a in visible_assets),
        "boundary_status": district.boundary_status, "boundary_source": district.boundary_source,
    } for district in result.districts])
    with st.expander("Affected areas and scene coverage"):
        st.dataframe(coverage, hide_index=True, use_container_width=True)
    for warning in result.warnings:
        st.warning(warning)
    if not visible_assets:
        st.info("No acquisitions fall inside the selected timeline range.")
        return
    timeline_table = pd.DataFrame([{"acquired": a.acquisition_datetime, "phase": a.temporal_phase, "platform": a.platform, "filename": a.filename} for a in visible_assets])
    st.dataframe(timeline_table, hide_index=True, use_container_width=True)
    selected_name = st.selectbox("Inspect an acquisition", [asset.filename for asset in visible_assets])
    selected = next(asset for asset in visible_assets if asset.filename == selected_name)
    meta_left, meta_right = st.columns(2)
    with meta_left:
        st.markdown(f"**Platform / product:** {selected.platform} / {selected.product_type}")
        st.markdown(f"**Acquisition / phase:** {selected.acquisition_datetime or selected.acquisition_date} / {selected.temporal_phase}")
        st.markdown(f"**CRS / resolution:** {selected.crs} / {selected.spatial_resolution_m or 'unknown'} m")
    with meta_right:
        st.markdown(f"**Bands or polarizations:** {', '.join(selected.bands) or 'not supplied'}")
        st.markdown(f"**Orbit:** {selected.orbit_direction or 'not applicable'}")
        st.markdown(f"**Catalog status:** {selected.catalog_status} · remote verified: {selected.verified_remote}")
    st.caption(selected.notes)
    st.download_button("Download candidate metadata", result.model_dump_json(indent=2), "satellite-candidates.json", "application/json")


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
    st.markdown("""
        <style>
        .block-container {padding-top: 1rem; padding-left: 1.2rem; padding-right: 1.2rem; max-width: 100%;}
        [data-testid="stSidebar"] {background: rgba(15, 23, 42, 0.84); backdrop-filter: blur(14px);}
        [data-testid="stSidebar"] label, [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] p {color: #f8fafc;}
        [data-testid="stMetric"] {background: rgba(255, 255, 255, 0.72); border: 1px solid rgba(148, 163, 184, 0.35); border-radius: 12px; padding: 10px; backdrop-filter: blur(10px);}
        [data-testid="stExpander"] {background: rgba(255, 255, 255, 0.76); border-radius: 12px; backdrop-filter: blur(10px);}
        iframe {border-radius: 14px;}
        </style>
    """, unsafe_allow_html=True)
    st.title("GeoReliability Agent")
    st.caption("From a disaster question to mapped districts, satellite candidates, and verified data evidence.")
    disaster_tab, data_tab = st.tabs(["🛰️ Disaster & satellite", "🔎 Data quality"])
    with disaster_tab:
        disaster_finder()
    with data_tab:
        table_investigator()


if __name__ == "__main__":
    main()
