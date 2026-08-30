# Improvement Changelog

| Stage | What was tried and why | Evidence | Decision / learning |
|---|---|---|---|
| Baseline | Missing-value and exact-duplicate script as a reasonable basic inspection | Run `make baseline` and record benchmark metrics | Establishes the starting point |
| Iteration 1 | Added deterministic profiling and a controlled check catalog | Unit tests and benchmark output | Keep; factual evidence should come from code |
| Iteration 2 | Added Ollama planning so checks respond to schema and user goal | Planning source recorded in trajectory | Keep with deterministic fallback |
| Iteration 3 | Added independent evidence-contract verification | Accepted/rejected counts in every report | Keep; prevents unsupported claims reaching the report |
| Final Day 1 | Combined planner, tools, verifier, report, and trace into one CLI execution | `make test`, `make demo`, `make evaluate` | Complete vertical slice; expand formats and benchmark next |
| Day 2 / Iteration 4 | Expanded the loader to Excel, JSON and Parquet so the workflow matches common analyst inputs | Format round-trip tests; optional dependency groups | Keep; preserve one normalized internal DataFrame contract |
| Day 2 / Iteration 5 | Added automatic repairs initially, then placed them behind explicit human approval after reviewing silent-corruption risk | Tests reject empty approval, unknown IDs and source overwrite | Keep the approval boundary; never execute generated repair code |
| Day 2 / Iteration 6 | Expanded the benchmark from 6 to 11 cases, including cross-field reconciliation | Baseline F1 0.333; agent F1 1.000 on controlled cases | Keep all cases and disclose that synthetic performance is not real-world accuracy |
| Day 2 / Iteration 7 | Added Streamlit and Docker for a realistic end-to-end demonstration | UI import smoke test and container build | Keep; feature-freeze the backend before video recording |

## Main failure mode

Without a user-supplied data contract, the workflow can detect structural anomalies but cannot always determine whether a surprising value is genuinely incorrect. A repaired negative value also becomes a missing value; repair changes the risk rather than magically proving correctness.

## Hot take

The most reliable data agent is not the one allowed to write arbitrary analysis code. It is the one that chooses from transparent tools while deterministic evidence and an independent verifier control what becomes a factual claim.
# Day 2 geospatial integration

- Added Ollama-assisted disaster event resolution with deterministic fallback.
- Added offline district matching and map-ready coordinates.
- Added date/platform/product filtering over an explicitly illustrative satellite catalog.
- Distinguished Sentinel-1 SLC/GRD products from derived InSAR artifacts.
- Reused the reliability investigator to audit filtered catalog metadata.
- Added CLI, FastAPI, and a map-first Streamlit workflow while retaining table analysis.
- Added four remote-sensing regression tests (13 total tests passing).
- Added centered interactive polygon mapping for target boundaries and satellite footprints.
- Added acquisition timestamps, bands, CRS, resolution, and map tooltip metadata.
- Added a catalog-options API endpoint and a full scene inspection panel.
- Added a geometry/metadata contract regression test (14 total tests passing).
- Added Sentinel-2 Level-2A candidates, a global landing map, sidebar search, automatic incident recentering, and a pre/post-event acquisition timeline (15 total tests passing).
- Added geoBoundaries ADM2 resolution with caching and explicit fallback provenance, translucent map UI, product-class visibility controls, distinct optical/SAR/InSAR colors, and a separate affected-area planning overlay (17 total tests passing).
