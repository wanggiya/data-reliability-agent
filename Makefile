.PHONY: install install-all test benchmark demo baseline evaluate discover ui api web docker-up docker-down clean

install:
	python3 -m pip install -e .

install-all:
	python3 -m pip install -e '.[all]'

test:
	PYTHONPATH=src python3 -m unittest discover -s tests -v

benchmark:
	PYTHONPATH=src python3 benchmark/generate_cases.py

demo: benchmark
	PYTHONPATH=src python3 -m data_reliability.cli investigate benchmark/cases/case_06_multi_issue.csv --goal "Assess whether this monthly operations dataset is safe for KPI reporting" --mode deterministic

baseline: benchmark
	PYTHONPATH=src python3 -m data_reliability.cli baseline benchmark/cases/case_06_multi_issue.csv

evaluate: benchmark
	PYTHONPATH=src python3 -m data_reliability.cli evaluate benchmark/expected_findings.json

discover:
	PYTHONPATH=src python3 -m data_reliability.cli discover-assets "January 2025 earthquake near Dingri, Tibet and Nepal" --start 2025-01-01 --end 2025-01-31 --mode deterministic

ui:
	PYTHONPATH=src streamlit run streamlit_app.py

HOST ?= 127.0.0.1
PORT ?= 8001

api:
	PYTHONPATH=src uvicorn data_reliability.api:app --reload --host $(HOST) --port $(PORT)

web: api

docker-up:
	docker compose up --build

docker-down:
	docker compose down

clean:
	find outputs -type f ! -name .gitkeep -delete
