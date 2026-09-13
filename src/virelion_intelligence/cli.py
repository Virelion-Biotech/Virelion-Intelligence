from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from . import PIPELINE_VERSION
from .db import Database
from .models import RunManifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="virelion-intel", description="Virelion cardiovascular research intelligence")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="initialize a reproducible intelligence run")
    run.add_argument("--window-days", type=int, default=7)
    run.add_argument("--db", type=Path, default=Path("data/virelion_intelligence.sqlite3"))
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "run":
        if args.window_days < 1:
            raise SystemExit("--window-days must be >= 1")
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=args.window_days)
        run_id = f"R-{end:%Y%m%d-%H%M%S}-{uuid4().hex[:8]}"
        manifest = RunManifest(
            run_id=run_id,
            pipeline_version=PIPELINE_VERSION,
            window_start=start,
            window_end=end,
            status="CREATED",
        )
        db = Database(args.db)
        try:
            db.upsert_json(
                "runs", "run_id", run_id, manifest.model_dump(mode="json"),
                {
                    "pipeline_version": manifest.pipeline_version,
                    "started_at": manifest.started_at.isoformat(),
                    "window_start": manifest.window_start.isoformat(),
                    "window_end": manifest.window_end.isoformat(),
                    "status": manifest.status,
                    "counts_json": "{}",
                },
            )
        finally:
            db.close()
        print(f"run_id={run_id}")
        print(f"window={start.isoformat()}..{end.isoformat()}")
        print(f"database={args.db}")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
