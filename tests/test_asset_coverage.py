"""Tests for asset coverage checker."""
from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from brandmint.publishing.asset_coverage import (
    check_asset_coverage,
    generate_coverage_report,
    CoverageReport,
    AssetCoverageResult,
)


class TestCheckAssetCoverage:
    """Test asset coverage checking."""

    def test_full_coverage(self, tmp_path):
        expected = {"2A", "2B", "3A"}
        # Create generated files
        (tmp_path / "2A-v1.png").touch()
        (tmp_path / "2B-v1.png").touch()
        (tmp_path / "3A-v1.png").touch()

        report = check_asset_coverage(expected, tmp_path)
        assert report.total_expected == 3
        assert report.total_generated == 3
        assert report.total_matching == 3
        assert report.coverage_percentage == 100.0
        assert len(report.missing_assets) == 0

    def test_missing_assets(self, tmp_path):
        expected = {"2A", "2B", "3A"}
        # Only create some files
        (tmp_path / "2A-v1.png").touch()

        report = check_asset_coverage(expected, tmp_path)
        assert report.total_matching == 1
        assert len(report.missing_assets) == 2
        assert "2B" in report.missing_assets
        assert "3A" in report.missing_assets

    def test_extra_assets(self, tmp_path):
        expected = {"2A"}
        # Create extra files
        (tmp_path / "2A-v1.png").touch()
        (tmp_path / "99Z-v1.png").touch()

        report = check_asset_coverage(expected, tmp_path)
        assert len(report.extra_assets) == 1
        assert "99Z" in report.extra_assets

    def test_empty_expected(self, tmp_path):
        report = check_asset_coverage(set(), tmp_path)
        assert report.total_expected == 0
        assert report.coverage_percentage == 100.0

    def test_nonexistent_directory(self):
        report = check_asset_coverage({"2A"}, Path("/nonexistent"))
        assert report.total_generated == 0
        assert len(report.missing_assets) == 1


class TestGenerateCoverageReport:
    """Test coverage report generation."""

    def test_generates_report_with_missing(self):
        report = CoverageReport(
            total_expected=3,
            total_generated=1,
            total_matching=1,
            missing_assets=["2B", "3A"],
        )
        text = generate_coverage_report(report)
        assert "# Asset Coverage Report" in text
        assert "Expected assets: 3" in text
        assert "Coverage: 33.3%" in text
        assert "## Missing Assets" in text
        assert "2B" in text

    def test_generates_report_with_extra(self):
        report = CoverageReport(
            total_expected=1,
            total_generated=2,
            total_matching=1,
            extra_assets=["99Z"],
        )
        text = generate_coverage_report(report)
        assert "## Extra Assets" in text
        assert "99Z" in text
