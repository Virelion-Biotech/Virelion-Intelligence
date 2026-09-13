.PHONY: install test lint run report status check

install:
	python -m pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check src tests scripts

run:
	bash scripts/run_intelligence.sh

report:
	python scripts/build_report.py

status:
	python -m virelion_intelligence status

check:
	python scripts/check_integrity.py
	python scripts/check_sources.py
