#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON_BIN:-python3}"
WINDOW_DAYS="${WINDOW_DAYS:-7}"
DB_PATH="${VIRELION_DB:-data/virelion_intelligence.sqlite3}"

if [[ "${DRY_RUN:-0}" == "1" ]]; then
  DB_PATH="${VIRELION_DRYRUN_DB:-data/dryrun.sqlite3}"
fi

"$PYTHON" -m virelion_intelligence run --window-days "$WINDOW_DAYS" --db "$DB_PATH"
"$PYTHON" -m virelion_intelligence report --db "$DB_PATH" --output "reports/latest/intelligence.md"
"$PYTHON" -m virelion_intelligence status --db "$DB_PATH"
