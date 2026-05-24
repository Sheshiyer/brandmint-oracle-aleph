#!/usr/bin/env python3
"""Inspect NotebookLM source docs for meta/process leakage quality."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from brandmint.publishing.source_quality_inspector import (
    analyze_sources_dir,
    render_markdown_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze NotebookLM source markdown quality",
    )
    parser.add_argument(
        "sources_dir",
        type=Path,
        help="Path to deliverables/notebooklm/sources directory",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=None,
        help="Optional path to write JSON report",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=None,
        help="Optional path to write Markdown report",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=85.0,
        help="Minimum passing average score (default: 85)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.sources_dir.is_dir():
        print(f"ERROR: sources_dir not found: {args.sources_dir}", file=sys.stderr)
        return 2

    payload = analyze_sources_dir(args.sources_dir)

    print(f"Scanned {payload['file_count']} files in {payload['sources_dir']}")
    print(
        f"Average score: {payload['average_score']} "
        f"(pass={payload['passing_files']}, warn={payload['warning_files']}, fail={payload['failing_files']})"
    )
    print(
        f"Forbidden hits: {payload['total_forbidden_hits']} | "
        f"Placeholder markers: {payload['total_placeholder_markers']}"
    )

    if args.output_json is not None:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Wrote JSON report: {args.output_json}")

    if args.output_md is not None:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text(render_markdown_report(payload), encoding="utf-8")
        print(f"Wrote Markdown report: {args.output_md}")

    if payload["average_score"] < args.min_score:
        print(
            f"Quality gate failed: average score {payload['average_score']} < {args.min_score}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
