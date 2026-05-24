#!/usr/bin/env python3
"""Run scenario/depth coverage preflight for brandmint launch planning."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from brandmint.core.coverage_preflight import build_coverage_preflight


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Wave coverage preflight")
    parser.add_argument("--config", type=Path, required=True, help="Path to brand-config.yaml")
    parser.add_argument("--scenario", type=str, default=None, help="Scenario ID override")
    parser.add_argument("--depth", type=str, default=None, help="Depth override")
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON output path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.config.is_file():
        print(f"ERROR: config not found: {args.config}", file=sys.stderr)
        return 2

    cfg = yaml.safe_load(args.config.read_text(encoding="utf-8")) or {}
    report = build_coverage_preflight(cfg, scenario_id=args.scenario, depth=args.depth)

    print(f"Scenario: {report['scenario_id'] or '(auto)'} | Depth: {report['depth']}")
    print(f"Waves: {report['wave_count']}")
    print(f"Planned text skills: {len(report['planned_text_skills'])}")
    print(f"Planned visual assets: {len(report['planned_visual_assets'])}")
    print(f"Missing mandatory source skills: {len(report['missing_mandatory_source_skills'])}")
    print(f"Empty execution waves: {report['empty_execution_waves']}")
    for warning in report["warnings"]:
        print(f"WARNING: {warning}")

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Wrote report: {args.output}")

    return 1 if report["warnings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
