from __future__ import annotations

import argparse
from pathlib import Path

from . import PIPELINE_VERSION
from .db import IntelligenceDB
from .pipeline import run
from .reports import build_markdown_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="virelion-intel", description="Virelion cardiovascular research intelligence")
    sub = parser.add_subparsers(dest="command", required=True)

    r = sub.add_parser("run", help="discover, normalize, rank, persist, and summarize")
    r.add_argument("--window-days", type=int, default=7)
    r.add_argument("--db", type=Path, default=Path("data/virelion_intelligence.sqlite3"))
    r.add_argument("--query", action="append", dest="queries", help="override/add a discovery query; repeatable")

    s = sub.add_parser("status", help="show stored corpus counts")
    s.add_argument("--db", type=Path, default=Path("data/virelion_intelligence.sqlite3"))

    p = sub.add_parser("report", help="render the current corpus as Markdown")
    p.add_argument("--db", type=Path, default=Path("data/virelion_intelligence.sqlite3"))
    p.add_argument("--output", type=Path, default=Path("reports/latest/intelligence.md"))

    sub.add_parser("version", help="print pipeline version")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "version":
        print(PIPELINE_VERSION)
        return 0
    if args.command == "run":
        if args.window_days < 1:
            raise SystemExit("--window-days must be >= 1")
        manifest = run(window_days=args.window_days, db_path=str(args.db), query_texts=args.queries)
        print(manifest.model_dump_json(indent=2))
        return 0 if manifest.status == "COMPLETE" else 1
    if args.command == "status":
        with IntelligenceDB(args.db) as db:
            for table in ("sources", "papers", "claims", "evidence", "datasets", "opportunities", "runs"):
                print(f"{table}: {db.count(table)}")
        return 0
    if args.command == "report":
        with IntelligenceDB(args.db) as db:
            output = build_markdown_report(db)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
        print(args.output)
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
