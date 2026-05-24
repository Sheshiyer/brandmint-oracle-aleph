"""
Asset coverage checker — validates planned vs generated visual assets.

This module:
1. Compares expected asset matrix against generated files
2. Detects missing, mismatched, or extra assets
3. Provides coverage reports for operator review
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


@dataclass
class AssetCoverageResult:
    """Result of asset coverage check."""
    asset_id: str
    expected: bool
    generated: bool
    is_matching: bool
    mismatch_type: str = ""  # "missing", "extra", "mismatched"
    details: str = ""


@dataclass
class CoverageReport:
    """Full coverage report."""
    total_expected: int
    total_generated: int
    total_matching: int
    missing_assets: List[str] = field(default_factory=list)
    extra_assets: List[str] = field(default_factory=list)
    mismatched_assets: List[str] = field(default_factory=list)
    results: List[AssetCoverageResult] = field(default_factory=list)

    @property
    def coverage_percentage(self) -> float:
        if self.total_expected == 0:
            return 100.0
        return (self.total_matching / self.total_expected) * 100


def check_asset_coverage(
    expected_assets: Set[str],
    generated_dir: Path,
) -> CoverageReport:
    """Check coverage of expected vs generated assets.

    Args:
        expected_assets: Set of expected asset IDs
        generated_dir: Directory containing generated assets

    Returns:
        CoverageReport with coverage details
    """
    results = []
    missing = []
    extra = []
    mismatched = []
    matching_count = 0

    # Get generated files
    generated_files = set()
    if generated_dir.is_dir():
        for f in generated_dir.glob("*.png"):
            # Extract asset ID from filename (e.g., "2A-v1.png" -> "2A")
            stem = f.stem
            asset_id = stem.split("-")[0] if "-" in stem else stem
            generated_files.add(asset_id)
        for f in generated_dir.glob("*.webp"):
            stem = f.stem
            asset_id = stem.split("-")[0] if "-" in stem else stem
            generated_files.add(asset_id)

    # Check expected assets
    for asset_id in expected_assets:
        is_generated = asset_id in generated_files
        result = AssetCoverageResult(
            asset_id=asset_id,
            expected=True,
            generated=is_generated,
            is_matching=is_generated,
        )
        if not is_generated:
            result.mismatch_type = "missing"
            result.details = f"Asset '{asset_id}' was expected but not generated"
            missing.append(asset_id)
        else:
            matching_count += 1
        results.append(result)

    # Check for extra assets
    for asset_id in generated_files:
        if asset_id not in expected_assets:
            result = AssetCoverageResult(
                asset_id=asset_id,
                expected=False,
                generated=True,
                is_matching=False,
                mismatch_type="extra",
                details=f"Asset '{asset_id}' was generated but not expected",
            )
            extra.append(asset_id)
            results.append(result)

    return CoverageReport(
        total_expected=len(expected_assets),
        total_generated=len(generated_files),
        total_matching=matching_count,
        missing_assets=missing,
        extra_assets=extra,
        mismatched_assets=mismatched,
        results=results,
    )


def generate_coverage_report(report: CoverageReport) -> str:
    """Generate human-readable coverage report."""
    parts = ["# Asset Coverage Report\n"]

    parts.append("## Summary\n")
    parts.append(f"- Expected assets: {report.total_expected}")
    parts.append(f"- Generated assets: {report.total_generated}")
    parts.append(f"- Matching assets: {report.total_matching}")
    parts.append(f"- Coverage: {report.coverage_percentage:.1f}%")
    parts.append("")

    if report.missing_assets:
        parts.append("## Missing Assets\n")
        for asset_id in report.missing_assets:
            parts.append(f"- ❌ {asset_id}")
        parts.append("")

    if report.extra_assets:
        parts.append("## Extra Assets\n")
        for asset_id in report.extra_assets:
            parts.append(f"- ⚠️ {asset_id}")
        parts.append("")

    return "\n".join(parts)
