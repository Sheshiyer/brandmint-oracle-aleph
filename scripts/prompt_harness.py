#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def score_case(case: dict) -> dict:
    # Mock deterministic scoring scaffold; replace with model calls later.
    complexity = case.get("complexity", "medium")
    base = {"simple": 0.94, "medium": 0.9, "complex": 0.86}.get(complexity, 0.9)
    return {
        "correctness": round(base, 2),
        "completeness": round(base - 0.01, 2),
        "clarity": round(base - 0.02, 2),
        "tone_fit": round(base - 0.01, 2),
        "hallucination_risk": round(max(0.01, 1 - base - 0.05), 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run prompt harness over golden set.")
    parser.add_argument("--registry", required=True)
    parser.add_argument("--golden", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    registry = json.loads(Path(args.registry).read_text())
    golden = json.loads(Path(args.golden).read_text())

    results = []
    for case in golden.get("cases", []):
        scores = score_case(case)
        aggregate = round(
            (scores["correctness"] + scores["completeness"] + scores["clarity"] + scores["tone_fit"]) / 4,
            2,
        )
        passed = aggregate >= golden.get("target_pass_rate", 0.9)
        results.append(
            {
                "case_id": case.get("id"),
                "complexity": case.get("complexity"),
                "aggregate": aggregate,
                "passed": passed,
                "scores": scores,
            }
        )

    pass_rate = 0.0
    if results:
        pass_rate = round(sum(1 for r in results if r["passed"]) / len(results), 2)

    payload = {
        "registry_version": registry.get("version"),
        "golden_version": golden.get("version"),
        "cases": len(results),
        "pass_rate": pass_rate,
        "target_pass_rate": golden.get("target_pass_rate", 0.9),
        "gate_b_ready": pass_rate >= golden.get("target_pass_rate", 0.9),
        "results": results,
    }

    Path(args.output).write_text(json.dumps(payload, indent=2))
    print(f"WROTE:{args.output}")
    print(f"PASS_RATE:{pass_rate}")


if __name__ == "__main__":
    main()
