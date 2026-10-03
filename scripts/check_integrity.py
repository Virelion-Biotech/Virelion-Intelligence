from __future__ import annotations

import argparse
from pathlib import Path

from virelion_intelligence.validation import check_secret_paths, validate_report_text


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Virelion Intelligence repository artifacts")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    errors: list[str] = []
    errors.extend(f"forbidden runtime artifact: {x}" for x in check_secret_paths(args.root))
    if args.report and args.report.is_file():
        errors.extend(validate_report_text(args.report.read_text(encoding="utf-8")))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 2
    print("integrity: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
