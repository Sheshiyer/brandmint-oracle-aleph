"""
Publish gate — fail-fast preconditions for NotebookLM publishing.

This module enforces strict preconditions before allowing NotebookLM
publishing to proceed, preventing low-quality uploads.

Gate checks:
1. Source quality score >= threshold
2. No forbidden lexicon hits
3. No placeholder-heavy documents
4. Minimum document count met
5. Upload policy validation passed
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from .completeness_gate import CompletenessGate, check_completeness
from .curation_scorer import CurationWeights, calculate_curation_score, CurationScore
from .upload_policy import UploadPolicy, validate_upload_policy, PolicyValidationResult


@dataclass
class SourceQualityResult:
    """Simple quality result for gate checks."""
    doc_id: str
    score: float = 0.0
    forbidden_hits: List[str] = field(default_factory=list)


@dataclass
class PublishGateResult:
    """Result of publish gate validation."""
    passed: bool
    checks: Dict[str, bool] = field(default_factory=dict)
    failures: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PublishGateConfig:
    """Configuration for publish gate."""
    # Minimum average source quality score
    min_avg_quality_score: float = 85.0
    # Maximum number of forbidden lexicon hits allowed
    max_forbidden_hits: int = 0
    # Maximum percentage of placeholder-heavy documents
    max_placeholder_docs_percentage: float = 10.0
    # Minimum number of documents required
    min_document_count: int = 3
    # Whether to enforce upload policy
    enforce_upload_policy: bool = True
    # Whether to fail fast on first error
    fail_fast: bool = False


# ---------------------------------------------------------------------------
# Gate checks
# ---------------------------------------------------------------------------


def check_source_quality(
    quality_results: Dict[str, SourceQualityResult],
    config: Optional[PublishGateConfig] = None
) -> bool:
    """Check if source quality scores meet threshold."""
    if config is None:
        config = PublishGateConfig()

    if not quality_results:
        return False

    avg_score = sum(r.score for r in quality_results.values()) / len(quality_results)
    return avg_score >= config.min_avg_quality_score


def check_forbidden_lexicon(
    quality_results: Dict[str, SourceQualityResult],
    config: Optional[PublishGateConfig] = None
) -> bool:
    """Check if forbidden lexicon hits are within limits."""
    if config is None:
        config = PublishGateConfig()

    total_hits = sum(len(r.forbidden_hits) for r in quality_results.values())
    return total_hits <= config.max_forbidden_hits


def check_placeholder_documents(
    documents: Dict[str, str],
    config: Optional[PublishGateConfig] = None,
    gate: Optional[CompletenessGate] = None
) -> bool:
    """Check if placeholder-heavy documents are within limits."""
    if config is None:
        config = PublishGateConfig()
    if gate is None:
        gate = CompletenessGate()

    if not documents:
        return False

    placeholder_count = 0
    for doc_id, text in documents.items():
        result = check_completeness(doc_id, text, gate=gate)
        if not result.is_complete:
            placeholder_count += 1

    placeholder_percentage = (placeholder_count / len(documents)) * 100
    return placeholder_percentage <= config.max_placeholder_docs_percentage


def check_document_count(
    documents: Dict[str, str],
    config: Optional[PublishGateConfig] = None
) -> bool:
    """Check if minimum document count is met."""
    if config is None:
        config = PublishGateConfig()

    return len(documents) >= config.min_document_count


def check_upload_policy(
    document_ids: List[str],
    config: Optional[PublishGateConfig] = None,
    policy: Optional[UploadPolicy] = None
) -> PolicyValidationResult:
    """Check if documents meet upload policy requirements."""
    if config is None:
        config = PublishGateConfig()

    if not config.enforce_upload_policy:
        return PolicyValidationResult(is_valid=True)

    return validate_upload_policy(document_ids, policy)


# ---------------------------------------------------------------------------
# Full gate validation
# ---------------------------------------------------------------------------


def run_publish_gate(
    documents: Dict[str, str],
    quality_results: Dict[str, SourceQualityResult],
    config: Optional[PublishGateConfig] = None,
    gate: Optional[CompletenessGate] = None,
    weights: Optional[CurationWeights] = None,
    policy: Optional[UploadPolicy] = None
) -> PublishGateResult:
    """Run all publish gate checks."""
    if config is None:
        config = PublishGateConfig()

    result = PublishGateResult(passed=True)

    # Check 1: Source quality
    quality_passed = check_source_quality(quality_results, config)
    result.checks["source_quality"] = quality_passed
    if not quality_passed:
        result.passed = False
        avg_score = sum(r.score for r in quality_results.values()) / max(1, len(quality_results))
        result.failures.append(f"Average quality score {avg_score:.1f} < {config.min_avg_quality_score} minimum")
        if config.fail_fast:
            return result

    # Check 2: Forbidden lexicon
    forbidden_passed = check_forbidden_lexicon(quality_results, config)
    result.checks["forbidden_lexicon"] = forbidden_passed
    if not forbidden_passed:
        result.passed = False
        total_hits = sum(len(r.forbidden_hits) for r in quality_results.values())
        result.failures.append(f"Total forbidden hits {total_hits} > {config.max_forbidden_hits} maximum")
        if config.fail_fast:
            return result

    # Check 3: Placeholder documents
    placeholder_passed = check_placeholder_documents(documents, config, gate)
    result.checks["placeholder_documents"] = placeholder_passed
    if not placeholder_passed:
        result.passed = False
        result.failures.append("Too many placeholder-heavy documents")
        if config.fail_fast:
            return result

    # Check 4: Document count
    count_passed = check_document_count(documents, config)
    result.checks["document_count"] = count_passed
    if not count_passed:
        result.passed = False
        result.failures.append(f"Only {len(documents)} documents, minimum is {config.min_document_count}")
        if config.fail_fast:
            return result

    # Check 5: Upload policy
    policy_result = check_upload_policy(list(documents.keys()), config, policy)
    result.checks["upload_policy"] = policy_result.is_valid
    if not policy_result.is_valid:
        result.passed = False
        for violation in policy_result.violations:
            if violation.severity == "error":
                result.failures.append(violation.message)
            else:
                result.warnings.append(violation.message)
        if config.fail_fast:
            return result

    # Add details
    result.details["total_documents"] = len(documents)
    result.details["quality_results"] = len(quality_results)
    result.details["avg_quality_score"] = (
        sum(r.score for r in quality_results.values()) / max(1, len(quality_results))
    ) if quality_results else 0

    return result


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def generate_gate_report(result: PublishGateResult) -> str:
    """Generate a human-readable gate validation report."""
    parts = ["# Publish Gate Report\n"]

    parts.append(f"## Result: {'PASSED' if result.passed else 'FAILED'}\n")

    parts.append("## Checks\n")
    for check_name, passed in result.checks.items():
        icon = "✅" if passed else "❌"
        parts.append(f"- {icon} {check_name}: {'Passed' if passed else 'Failed'}")
    parts.append("")

    if result.failures:
        parts.append("## Failures\n")
        for failure in result.failures:
            parts.append(f"- ❌ {failure}")
        parts.append("")

    if result.warnings:
        parts.append("## Warnings\n")
        for warning in result.warnings:
            parts.append(f"- ⚠️ {warning}")
        parts.append("")

    if result.details:
        parts.append("## Details\n")
        for key, value in result.details.items():
            parts.append(f"- {key}: {value}")
        parts.append("")

    return "\n".join(parts)
