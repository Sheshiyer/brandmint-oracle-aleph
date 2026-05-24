"""
Visual QA heuristic checks — validates generated visual assets for quality.

This module:
1. Checks image dimensions match expected aspect ratios
2. Validates file sizes are within acceptable ranges
3. Detects corrupted or invalid image files
4. Generates QA reports for operator review
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# Expected aspect ratios and their pixel dimensions
ASPECT_RATIOS = {
    "1:1": [(1024, 1024), (2048, 2048)],
    "16:9": [(1792, 1024), (3584, 2048)],
    "9:16": [(1024, 1792), (2048, 3584)],
    "3:4": [(1536, 2048)],
    "4:3": [(2048, 1536)],
}

# File size limits (MB)
MIN_FILE_SIZE_KB = 50  # 50KB minimum
MAX_FILE_SIZE_MB = 20  # 20MB maximum


@dataclass
class VisualQAResult:
    """Result of visual QA check for a single asset."""
    asset_id: str
    file_path: str
    passed: bool
    checks: Dict[str, bool] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class VisualQAReport:
    """Full visual QA report."""
    total_assets: int
    passed_assets: int
    failed_assets: int
    results: List[VisualQAResult] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        if self.total_assets == 0:
            return 100.0
        return (self.passed_assets / self.total_assets) * 100


def check_image_dimensions(file_path: Path, expected_aspect: str = "1:1") -> Tuple[bool, str]:
    """Check if image dimensions match expected aspect ratio."""
    try:
        from PIL import Image
        with Image.open(file_path) as img:
            width, height = img.size
            expected_dims = ASPECT_RATIOS.get(expected_aspect, [(1024, 1024)])
            if (width, height) in expected_dims:
                return True, f"{width}x{height} matches {expected_aspect}"
            else:
                return False, f"{width}x{height} does not match {expected_aspect}"
    except ImportError:
        return True, "PIL not available, skipping dimension check"
    except Exception as e:
        return False, f"Error checking dimensions: {str(e)}"


def check_file_size(file_path: Path) -> Tuple[bool, str]:
    """Check if file size is within acceptable range."""
    size_bytes = file_path.stat().st_size
    size_kb = size_bytes / 1024
    size_mb = size_bytes / (1024 * 1024)

    if size_kb < MIN_FILE_SIZE_KB:
        return False, f"File too small: {size_kb:.1f}KB (min {MIN_FILE_SIZE_KB}KB)"
    if size_mb > MAX_FILE_SIZE_MB:
        return False, f"File too large: {size_mb:.1f}MB (max {MAX_FILE_SIZE_MB}MB)"
    return True, f"File size: {size_mb:.2f}MB"


def check_image_valid(file_path: Path) -> Tuple[bool, str]:
    """Check if image file is valid and not corrupted."""
    try:
        from PIL import Image
        with Image.open(file_path) as img:
            img.verify()
        return True, "Image is valid"
    except ImportError:
        return True, "PIL not available, skipping validation"
    except Exception as e:
        return False, f"Image corrupted or invalid: {str(e)}"


def run_visual_qa(
    generated_dir: Path,
    expected_aspects: Optional[Dict[str, str]] = None,
) -> VisualQAReport:
    """Run visual QA checks on all generated assets.

    Args:
        generated_dir: Directory containing generated assets
        expected_aspects: Map of asset_id to expected aspect ratio

    Returns:
        VisualQAReport with QA results
    """
    if expected_aspects is None:
        expected_aspects = {}

    results = []
    passed_count = 0

    if not generated_dir.is_dir():
        return VisualQAReport(total_assets=0, passed_assets=0, failed_assets=0)

    for image_file in sorted(generated_dir.glob("*.png")) + sorted(generated_dir.glob("*.webp")):
        stem = image_file.stem
        asset_id = stem.split("-")[0] if "-" in stem else stem

        checks = {}
        errors = []
        warnings = []

        # Check 1: Image validity
        valid, msg = check_image_valid(image_file)
        checks["image_valid"] = valid
        if not valid:
            errors.append(msg)

        # Check 2: File size
        size_ok, msg = check_file_size(image_file)
        checks["file_size"] = size_ok
        if not size_ok:
            errors.append(msg)

        # Check 3: Dimensions (if PIL available)
        expected_aspect = expected_aspects.get(asset_id, "1:1")
        dims_ok, msg = check_image_dimensions(image_file, expected_aspect)
        checks["dimensions"] = dims_ok
        if not dims_ok:
            warnings.append(msg)

        passed = all(checks.values())
        if passed:
            passed_count += 1

        results.append(VisualQAResult(
            asset_id=asset_id,
            file_path=str(image_file),
            passed=passed,
            checks=checks,
            errors=errors,
            warnings=warnings,
        ))

    return VisualQAReport(
        total_assets=len(results),
        passed_assets=passed_count,
        failed_assets=len(results) - passed_count,
        results=results,
    )


def generate_visual_qa_report(report: VisualQAReport) -> str:
    """Generate human-readable visual QA report."""
    parts = ["# Visual QA Report\n"]

    parts.append("## Summary\n")
    parts.append(f"- Total assets: {report.total_assets}")
    parts.append(f"- Passed: {report.passed_assets}")
    parts.append(f"- Failed: {report.failed_assets}")
    parts.append(f"- Pass rate: {report.pass_rate:.1f}%")
    parts.append("")

    if report.failed_assets > 0:
        parts.append("## Failed Assets\n")
        for result in report.results:
            if not result.passed:
                parts.append(f"### {result.asset_id}")
                parts.append(f"- **File:** {result.file_path}")
                for check_name, passed in result.checks.items():
                    icon = "✅" if passed else "❌"
                    parts.append(f"- {icon} {check_name}")
                if result.errors:
                    parts.append(f"- **Errors:** {'; '.join(result.errors)}")
                parts.append("")

    return "\n".join(parts)
