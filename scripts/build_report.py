from __future__ import annotations

import argparse
from pathlib import Path

from virelion_intelligence.db import IntelligenceDB
from virelion_intelligence.reports import build_markdown_report
from virelion_intelligence.validation import validate_report_text


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Virelion Intelligence Markdown report")
    parser.add_argument("--db", type=Path, default=Path("data/virelion_intelligence.sqlite3"))
    parser.add_argument("--output", type=Path, default=Path("reports/latest/intelligence.md"))
    args = parser.parse_args()

    with IntelligenceDB(args.db) as db:
        report = build_markdown_report(db)
    errors = validate_report_text(report)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"built: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
