#!/usr/bin/env python3
"""Enforce independent line and branch coverage thresholds."""

import argparse
import json
from pathlib import Path


def percentage(covered: int, total: int) -> float:
    return 100.0 if total == 0 else covered / total * 100


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", nargs="?", default="coverage.json")
    parser.add_argument("--line", type=float, default=95.0)
    parser.add_argument("--branch", type=float, default=95.0)
    args = parser.parse_args()

    report_path = Path(args.report)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    totals = report["totals"]
    line_coverage = percentage(totals["covered_lines"], totals["num_statements"])
    branch_coverage = percentage(
        totals["covered_branches"], totals["num_branches"]
    )

    print(f"Line coverage:   {line_coverage:.2f}% (required: {args.line:.2f}%)")
    print(f"Branch coverage: {branch_coverage:.2f}% (required: {args.branch:.2f}%)")

    failed = []
    if line_coverage < args.line:
        failed.append("line")
    if branch_coverage < args.branch:
        failed.append("branch")
    if failed:
        print(f"Coverage gate failed: {', '.join(failed)}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
