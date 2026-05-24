"""Tests for visual QA."""
from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from brandmint.publishing.visual_qa import (
    run_visual_qa,
    generate_visual_qa_report,
    VisualQAReport,
    VisualQAResult,
    check_file_size,
)


class TestCheckFileSize:
    """Test file size checking."""

    def test_valid_file_size(self, tmp_path):
        file_path = tmp_path / "test.png"
        # Create a 100KB file
        file_path.write_bytes(b"x" * (100 * 1024))
        ok, msg = check_file_size(file_path)
        assert ok

    def test_file_too_small(self, tmp_path):
        file_path = tmp_path / "test.png"
        file_path.write_bytes(b"x" * 10)  # 10 bytes
        ok, msg = check_file_size(file_path)
        assert not ok
        assert "too small" in msg.lower()


class TestRunVisualQA:
    """Test visual QA execution."""

    def test_empty_directory(self, tmp_path):
        report = run_visual_qa(tmp_path)
        assert report.total_assets == 0
        assert report.pass_rate == 100.0

    def test_nonexistent_directory(self):
        report = run_visual_qa(Path("/nonexistent"))
        assert report.total_assets == 0

    def test_generates_report(self):
        report = VisualQAReport(
            total_assets=5,
            passed_assets=4,
            failed_assets=1,
            results=[
                VisualQAResult(
                    asset_id="2A",
                    file_path="/tmp/2A.png",
                    passed=False,
                    checks={"image_valid": False},
                    errors=["Image corrupted"],
                ),
            ],
        )
        text = generate_visual_qa_report(report)
        assert "# Visual QA Report" in text
        assert "Pass rate: 80.0%" in text
        assert "## Failed Assets" in text
        assert "2A" in text
