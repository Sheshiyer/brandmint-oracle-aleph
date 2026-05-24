"""Tests for upload policy."""
from __future__ import annotations

import pytest

from brandmint.publishing.upload_policy import (
    UploadPolicy,
    PolicyViolation,
    PolicyValidationResult,
    matches_pattern,
    validate_upload_policy,
    filter_by_policy,
    generate_policy_report,
    get_policy_for_profile,
)


class TestMatchesPattern:
    """Test pattern matching."""

    def test_exact_match(self):
        assert matches_pattern("brand-foundation", "brand-foundation")

    def test_wildcard_match(self):
        assert matches_pattern("kickstarter-readiness", "kickstarter-*")

    def test_wildcard_no_match(self):
        assert not matches_pattern("brand-foundation", "kickstarter-*")

    def test_question_mark_match(self):
        assert matches_pattern("test1", "test?")

    def test_case_insensitive(self):
        assert matches_pattern("Brand-Foundation", "brand-foundation")


class TestValidateUploadPolicy:
    """Test policy validation."""

    def test_valid_documents_pass(self):
        docs = ["brand-foundation", "brand-strategy", "campaign-content"]
        result = validate_upload_policy(docs)
        assert result.is_valid
        assert len(result.allowed_documents) == 3

    def test_denied_documents_fail(self):
        docs = ["brand-foundation", "debug-internal", "brand-strategy"]
        result = validate_upload_policy(docs)
        assert not result.is_valid  # debug-internal is denied
        assert "debug-internal" in result.denied_documents

    def test_min_document_count_enforced(self):
        docs = ["brand-foundation"]
        result = validate_upload_policy(docs)
        assert not result.is_valid
        assert any(v.violation_type == "min_count" for v in result.violations)

    def test_min_core_documents_enforced(self):
        docs = ["campaign-content", "communications-social", "visual-asset-catalog"]
        result = validate_upload_policy(docs)
        assert not result.is_valid
        assert any(v.violation_type == "min_core" for v in result.violations)

    def test_max_document_count_warning(self):
        docs = [f"doc-{i}" for i in range(60)]
        policy = UploadPolicy(allowlist=["*"], max_document_count=50, strict_mode=False, min_document_count=1, min_core_documents=0)
        result = validate_upload_policy(docs, policy)
        assert any(v.violation_type == "max_count" for v in result.violations)

    def test_strict_mode_denies_unknown(self):
        docs = ["brand-foundation", "unknown-doc"]
        policy = UploadPolicy(strict_mode=True)
        result = validate_upload_policy(docs, policy)
        assert "unknown-doc" in result.denied_documents

    def test_non_strict_mode_allows_unknown(self):
        docs = ["brand-foundation", "unknown-doc"]
        policy = UploadPolicy(strict_mode=False, min_document_count=1, min_core_documents=0)
        result = validate_upload_policy(docs, policy)
        assert "unknown-doc" in result.allowed_documents


class TestFilterByPolicy:
    """Test document filtering."""

    def test_filters_denied_documents(self):
        docs = {
            "brand-foundation": "content1",
            "debug-internal": "content2",
            "brand-strategy": "content3",
        }
        filtered = filter_by_policy(docs)
        assert "brand-foundation" in filtered
        assert "debug-internal" not in filtered
        assert "brand-strategy" in filtered

    def test_empty_documents(self):
        filtered = filter_by_policy({})
        assert filtered == {}


class TestGeneratePolicyReport:
    """Test report generation."""

    def test_generates_report_with_violations(self):
        result = PolicyValidationResult(
            is_valid=False,
            violations=[
                PolicyViolation(
                    violation_type="denylist",
                    document_id="debug-internal",
                    message="Document 'debug-internal' matches denylist pattern 'debug-*'",
                    severity="error",
                ),
            ],
            allowed_documents=["brand-foundation"],
            denied_documents=["debug-internal"],
        )
        report = generate_policy_report(result)
        assert "# Upload Policy Report" in report
        assert "Valid: No" in report
        assert "Violations: 1" in report
        assert "debug-internal" in report

    def test_generates_report_without_violations(self):
        result = PolicyValidationResult(
            is_valid=True,
            violations=[],
            allowed_documents=["brand-foundation", "brand-strategy"],
            denied_documents=[],
        )
        report = generate_policy_report(result)
        assert "# Upload Policy Report" in report
        assert "Valid: Yes" in report
        assert "Violations: 0" in report


class TestGetPolicyForProfile:
    """Test policy presets for profiles."""

    def test_brand_public_policy(self):
        policy = get_policy_for_profile("brand-public")
        assert policy.strict_mode is True
        assert policy.min_document_count == 3
        assert "brand-foundation" in policy.allowlist

    def test_strategy_internal_policy(self):
        policy = get_policy_for_profile("strategy-internal")
        assert policy.strict_mode is False
        assert policy.min_document_count == 2

    def test_kickstarter_conditional_policy(self):
        policy = get_policy_for_profile("kickstarter-conditional")
        assert policy.strict_mode is True
        assert policy.min_document_count == 5
        assert "kickstarter-*" in policy.allowlist

    def test_debug_internal_policy(self):
        policy = get_policy_for_profile("debug-internal")
        assert policy.strict_mode is False
        assert policy.allowlist == ["*"]
        assert policy.denylist == []

    def test_unknown_profile_defaults_to_brand_public(self):
        policy = get_policy_for_profile("unknown")
        brand_public_policy = get_policy_for_profile("brand-public")
        assert policy.strict_mode == brand_public_policy.strict_mode
