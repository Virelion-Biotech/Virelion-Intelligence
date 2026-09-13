from __future__ import annotations

import argparse
from pathlib import Path

from virelion_intelligence.db import IntelligenceDB
from virelion_intelligence.validation import validate_dataset


def main() -> int:
    parser = argparse.ArgumentParser(description="Check stored Virelion Intelligence provenance and dataset gates")
    parser.add_argument("--db", type=Path, default=Path("data/virelion_intelligence.sqlite3"))
    args = parser.parse_args()
    errors = 0
    with IntelligenceDB(args.db) as db:
        for dataset in db.list_datasets(500):
            # Review-required datasets are valid corpus records; they are not ingestion targets.
            if dataset.suitability_status == "ACCEPTED" and validate_dataset(dataset):
                errors += 1
    print("source/dataset check: " + ("PASS" if errors == 0 else f"FAIL ({errors})"))
    return 0 if errors == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
