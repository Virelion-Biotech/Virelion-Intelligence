#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

WINDOW_DAYS="${WINDOW_DAYS:-7}"
DB_PATH="${DB_PATH:-data/virelion_intelligence.sqlite3}"

printf '[01] Python package check\n'
python -c 'import virelion_intelligence; print(virelion_intelligence.PIPELINE_VERSION)'

printf '[02] Initialize reproducible run\n'
python -m virelion_intelligence run --window-days "$WINDOW_DAYS" --db "$DB_PATH"

printf '[03] Foundation smoke tests\n'
pytest

printf '[04] FOUNDATION RUN COMPLETE\n'
printf 'Next stages: source discovery -> normalization -> ranking -> evidence -> datasets -> opportunities -> report.\n'
