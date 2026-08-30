# Reproduction guide

This guide verifies both the intentionally simple baseline and the advanced GeoReliability Agent from a clean Linux or WSL Ubuntu environment.

## Environment

- Python 3.11 or newer (tested with Python 3.12)
- Node.js 18 or newer, used only for a JavaScript syntax check
- Optional: Ollama with any locally installed chat model
- Optional UI dependencies are included in the `all` extra

The deterministic path has no API fee and needs no credentials. After dependencies are installed, its tests and benchmark normally complete in under one minute. Live boundary lookup and map tiles require internet access. Ollama runtime depends on the selected model and machine.

## Clean installation

```bash
git clone https://github.com/wanggiya/data-reliability-agent.git
cd data-reliability-agent
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[all]'
make submission-check
```

Expected benchmark summary:

| Solution | Precision | Recall | F1 |
|---|---:|---:|---:|
| Baseline | 1.000 | 0.200 | 0.333 |
| Advanced workflow | 1.000 | 1.000 | 1.000 |

These values measure 15 expected finding types across 11 controlled synthetic cases. They are regression evidence, not a claim of real-world accuracy.

## Run the baseline

```bash
make baseline
```

The baseline reports missing cells and exact duplicate rows only.

## Run the advanced table workflow

```bash
make demo
```

Expected output is a JSON summary containing `run_id`, `findings`, `report`, and `trajectory`. Inspect the three files under `outputs/<run-id>/`.

## Run the geospatial workflow

```bash
make discover
```

This deterministic example resolves the January 2025 Dingri earthquake, matches planning areas, and returns date-filtered illustrative satellite candidates.

Start the map UI:

```bash
make web
```

Open `http://127.0.0.1:8001/app/`. If the port is occupied, use `make web PORT=8010` and open that port instead.

Suggested second scenario:

```text
August 2022 floods near Sukkur and Larkana, Pakistan
```

## Optional Ollama path

```bash
ollama list
export OLLAMA_MODEL=qwen2.5-coder:7b
curl http://localhost:11434/api/tags
data-reliability investigate benchmark/cases/case_06_multi_issue.csv \
  --goal "Assess whether this dataset is safe for monthly KPI reporting" \
  --mode ollama
```

Replace the model name with one shown by `ollama list`. If Ollama is unreachable or returns invalid structured output, the workflow records that condition and falls back to deterministic planning.

## What is live and what is illustrative

- Data checks, evidence counts, verification, benchmark scores, dates, filters, and repair controls are executable.
- geoBoundaries polygons are retrieved live when available and labeled with provenance; an offline planning fallback is used otherwise.
- Satellite identifiers and footprints are illustrative planning candidates, not verified archive search results.
- The affected-area radius and textures support comparison; they are not an observed damage assessment.

## Docker alternative

```bash
docker compose up --build
```

Then open `http://127.0.0.1:8501`. The container does not bundle Ollama.
