.PHONY: install test benchmark demo baseline evaluate clean

install:
	python3 -m pip install -e .

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

clean:
	find outputs -type f ! -name .gitkeep -delete

