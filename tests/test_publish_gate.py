"""Tests for publish gate."""
from __future__ import annotations

import pytest

from brandmint.publishing.publish_gate import (
    PublishGateConfig,
    PublishGateResult,
    SourceQualityResult,
    check_source_quality,
    check_forbidden_lexicon,
    check_placeholder_documents,
    check_document_count,
    check_upload_policy,
    run_publish_gate,
    generate_gate_report,
)


class TestCheckSourceQuality:
    """Test source quality check."""

    def test_passes_with_high_scores(self):
        results = {
            "doc1": SourceQualityResult(doc_id="doc1", score=90.0),
            "doc2": SourceQualityResult(doc_id="doc2", score=85.0),
        }
        assert check_source_quality(results)

    def test_fails_with_low_scores(self):
        results = {
            "doc1": SourceQualityResult(doc_id="doc1", score=50.0),
            "doc2": SourceQualityResult(doc_id="doc2", score=60.0),
        }
        assert not check_source_quality(results)

    def test_fails_with_empty_results(self):
        assert not check_source_quality({})


class TestCheckForbiddenLexicon:
    """Test forbidden lexicon check."""

    def test_passes_with_no_hits(self):
        results = {
            "doc1": SourceQualityResult(doc_id="doc1", score=90.0, forbidden_hits=[]),
        }
        assert check_forbidden_lexicon(results)

    def test_fails_with_too_many_hits(self):
        results = {
            "doc1": SourceQualityResult(doc_id="doc1", score=90.0, forbidden_hits=["hit1", "hit2"]),
        }
        assert not check_forbidden_lexicon(results)


class TestCheckPlaceholderDocuments:
    """Test placeholder documents check."""

    def test_passes_with_clean_documents(self):
        docs = {
            "doc1": "High quality content with sufficient length and no placeholders or issues. This document contains comprehensive information that meets all standards and exceeds the minimum length threshold for completeness validation.",
            "doc2": "Another clean document with good content and sufficient length to pass the check and meet all requirements for completeness validation and quality standards and publishing requirements and additional content to ensure we exceed the threshold.",
        }
        assert check_placeholder_documents(docs)

    def test_fails_with_empty_documents(self):
        assert not check_placeholder_documents({})


class TestCheckDocumentCount:
    """Test document count check."""

    def test_passes_with_enough_documents(self):
        docs = {"doc1": "content1", "doc2": "content2", "doc3": "content3"}
        assert check_document_count(docs)

    def test_fails_with_too_few_documents(self):
        docs = {"doc1": "content1"}
        assert not check_document_count(docs)


class TestCheckUploadPolicy:
    """Test upload policy check."""

    def test_passes_when_not_enforced(self):
        config = PublishGateConfig(enforce_upload_policy=False)
        result = check_upload_policy(["doc1"], config)
        assert result.is_valid

    def test_passes_with_valid_documents(self):
        docs = ["brand-foundation", "brand-strategy", "campaign-content"]
        result = check_upload_policy(docs)
        assert result.is_valid


class TestRunPublishGate:
    """Test full gate validation."""

    def test_passes_all_checks(self):
        docs = {
            "brand-foundation": "High quality content with sufficient length and no placeholders or issues. This document contains comprehensive information that meets all standards and exceeds the minimum length threshold for completeness validation.",
            "brand-strategy": "Another clean document with good content and sufficient length to pass the check and meet all requirements for completeness validation and quality standards and publishing requirements and additional content to ensure we exceed the threshold.",
            "campaign-content": "Third document with enough content to satisfy all gate checks and validation rules and meet the minimum length requirements for publishing and completeness validation and quality assurance and additional content to exceed two hundred characters.",
        }
        quality_results = {
            "brand-foundation": SourceQualityResult(doc_id="brand-foundation", score=90.0, forbidden_hits=[]),
            "brand-strategy": SourceQualityResult(doc_id="brand-strategy", score=85.0, forbidden_hits=[]),
            "campaign-content": SourceQualityResult(doc_id="campaign-content", score=88.0, forbidden_hits=[]),
        }
        result = run_publish_gate(docs, quality_results)
        assert result.passed

    def test_fails_on_low_quality(self):
        docs = {
            "doc1": "High quality content with sufficient length and no placeholders or issues. This document contains comprehensive information that meets all standards.",
            "doc2": "Another clean document with good content and sufficient length to pass the check and meet requirements.",
            "doc3": "Third document with enough content to satisfy all gate checks and validation rules.",
        }
        quality_results = {
            "doc1": SourceQualityResult(doc_id="doc1", score=50.0, forbidden_hits=[]),
            "doc2": SourceQualityResult(doc_id="doc2", score=60.0, forbidden_hits=[]),
            "doc3": SourceQualityResult(doc_id="doc3", score=55.0, forbidden_hits=[]),
        }
        result = run_publish_gate(docs, quality_results)
        assert not result.passed
        assert not result.checks.get("source_quality", False)

    def test_fails_on_forbidden_hits(self):
        docs = {
            "doc1": "High quality content with sufficient length and no placeholders or issues. This document contains comprehensive information that meets all standards.",
            "doc2": "Another clean document with good content and sufficient length to pass the check and meet requirements.",
            "doc3": "Third document with enough content to satisfy all gate checks and validation rules.",
        }
        quality_results = {
            "doc1": SourceQualityResult(doc_id="doc1", score=90.0, forbidden_hits=["hit1", "hit2"]),
            "doc2": SourceQualityResult(doc_id="doc2", score=85.0, forbidden_hits=[]),
            "doc3": SourceQualityResult(doc_id="doc3", score=88.0, forbidden_hits=[]),
        }
        result = run_publish_gate(docs, quality_results)
        assert not result.passed
        assert not result.checks.get("forbidden_lexicon", False)

    def test_fail_fast_returns_early(self):
        docs = {"doc1": "Short."}
        quality_results = {
            "doc1": SourceQualityResult(doc_id="doc1", score=50.0, forbidden_hits=["hit1", "hit2"]),
        }
        config = PublishGateConfig(fail_fast=True)
        result = run_publish_gate(docs, quality_results, config)
        assert not result.passed
        # Should fail on first check (source_quality) and return early
        assert "source_quality" in result.checks
        # May not have all checks populated due to fail_fast
        assert len(result.failures) == 1


class TestGenerateGateReport:
    """Test report generation."""

    def test_generates_passed_report(self):
        result = PublishGateResult(
            passed=True,
            checks={"source_quality": True, "forbidden_lexicon": True},
            details={"total_documents": 5},
        )
        report = generate_gate_report(result)
        assert "# Publish Gate Report" in report
        assert "Result: PASSED" in report
        assert "source_quality: Passed" in report

    def test_generates_failed_report(self):
        result = PublishGateResult(
            passed=False,
            checks={"source_quality": False},
            failures=["Low quality score"],
            warnings=["Minor issue"],
            details={"total_documents": 2},
        )
        report = generate_gate_report(result)
        assert "Result: FAILED" in report
        assert "source_quality: Failed" in report
        assert "Low quality score" in report
        assert "Minor issue" in report
