"""
Upload policy — defines allowlist/denylist and minimum composition requirements
for NotebookLM source uploads.

This module:
1. Validates documents against allowlist/denylist patterns
2. Checks minimum composition requirements (e.g., at least X core docs)
3. Enforces policy during upload stage
4. Provides policy violation reporting
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class UploadPolicy:
    """Policy configuration for source uploads."""
    # Document ID patterns that are always allowed
    allowlist: List[str] = field(default_factory=lambda: [
        "brand-foundation", "brand-strategy", "campaign-content",
        "communications-social", "visual-asset-catalog",
    ])
    # Document ID patterns that are always denied
    denylist: List[str] = field(default_factory=lambda: [
        "debug-*", "test-*", "internal-notes*",
    ])
    # Minimum number of documents required for upload
    min_document_count: int = 3
    # Minimum number of core documents required
    min_core_documents: int = 2
    # Core document patterns
    core_patterns: List[str] = field(default_factory=lambda: [
        "brand-foundation", "brand-strategy",
    ])
    # Maximum number of documents allowed
    max_document_count: int = 50
    # Whether to enforce policy strictly
    strict_mode: bool = True


@dataclass
class PolicyViolation:
    """A policy violation detected during validation."""
    violation_type: str  # "denylist", "min_count", "min_core", "max_count"
    document_id: str = ""
    message: str = ""
    severity: str = "error"  # "error", "warning"


@dataclass
class PolicyValidationResult:
    """Result of policy validation."""
    is_valid: bool
    violations: List[PolicyViolation] = field(default_factory=list)
    allowed_documents: List[str] = field(default_factory=list)
    denied_documents: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Pattern matching
# ---------------------------------------------------------------------------


def matches_pattern(document_id: str, pattern: str) -> bool:
    """Check if a document ID matches a glob-like pattern."""
    # Convert glob pattern to regex
    regex_pattern = pattern.replace("*", ".*").replace("?", ".")
    return bool(re.fullmatch(regex_pattern, document_id, re.IGNORECASE))


# ---------------------------------------------------------------------------
# Policy validation
# ---------------------------------------------------------------------------


def validate_upload_policy(
    document_ids: List[str],
    policy: Optional[UploadPolicy] = None
) -> PolicyValidationResult:
    """Validate a set of documents against upload policy."""
    if policy is None:
        policy = UploadPolicy()

    violations = []
    allowed = []
    denied = []

    # Check each document against allowlist/denylist
    for doc_id in document_ids:
        is_denied = False
        is_allowed = False

        # Check denylist first
        for pattern in policy.denylist:
            if matches_pattern(doc_id, pattern):
                denied.append(doc_id)
                is_denied = True
                violations.append(PolicyViolation(
                    violation_type="denylist",
                    document_id=doc_id,
                    message=f"Document '{doc_id}' matches denylist pattern '{pattern}'",
                    severity="error",
                ))
                break

        if is_denied:
            continue

        # Check allowlist
        for pattern in policy.allowlist:
            if matches_pattern(doc_id, pattern):
                allowed.append(doc_id)
                is_allowed = True
                break

        if is_allowed:
            continue

        # If not explicitly allowed or denied, check strict mode
        if policy.strict_mode:
            denied.append(doc_id)
            violations.append(PolicyViolation(
                violation_type="denylist",
                document_id=doc_id,
                message=f"Document '{doc_id}' not in allowlist (strict mode)",
                severity="warning",
            ))
        else:
            allowed.append(doc_id)

    # Check minimum document count
    if len(allowed) < policy.min_document_count:
        violations.append(PolicyViolation(
            violation_type="min_count",
            message=f"Only {len(allowed)} documents allowed, minimum is {policy.min_document_count}",
            severity="error",
        ))

    # Check maximum document count
    if len(allowed) > policy.max_document_count:
        violations.append(PolicyViolation(
            violation_type="max_count",
            message=f"{len(allowed)} documents exceed maximum of {policy.max_document_count}",
            severity="warning",
        ))

    # Check minimum core documents
    core_count = 0
    for doc_id in allowed:
        for pattern in policy.core_patterns:
            if matches_pattern(doc_id, pattern):
                core_count += 1
                break

    if core_count < policy.min_core_documents:
        violations.append(PolicyViolation(
            violation_type="min_core",
            message=f"Only {core_count} core documents, minimum is {policy.min_core_documents}",
            severity="error",
        ))

    # Determine validity
    is_valid = not any(v.severity == "error" for v in violations)

    return PolicyValidationResult(
        is_valid=is_valid,
        violations=violations,
        allowed_documents=allowed,
        denied_documents=denied,
    )


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------


def filter_by_policy(
    documents: Dict[str, str],
    policy: Optional[UploadPolicy] = None
) -> Dict[str, str]:
    """Filter documents based on upload policy."""
    if policy is None:
        policy = UploadPolicy()

    result = validate_upload_policy(list(documents.keys()), policy)
    return {doc_id: documents[doc_id] for doc_id in result.allowed_documents}


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def generate_policy_report(result: PolicyValidationResult) -> str:
    """Generate a human-readable policy validation report."""
    parts = ["# Upload Policy Report\n"]

    parts.append("## Summary\n")
    parts.append(f"- Valid: {'Yes' if result.is_valid else 'No'}")
    parts.append(f"- Allowed documents: {len(result.allowed_documents)}")
    parts.append(f"- Denied documents: {len(result.denied_documents)}")
    parts.append(f"- Violations: {len(result.violations)}")
    parts.append("")

    if result.violations:
        parts.append("## Violations\n")
        for violation in result.violations:
            icon = "❌" if violation.severity == "error" else "⚠️"
            parts.append(f"- {icon} **{violation.violation_type}**: {violation.message}")
        parts.append("")

    if result.denied_documents:
        parts.append("## Denied Documents\n")
        for doc_id in result.denied_documents:
            parts.append(f"- {doc_id}")
        parts.append("")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Policy presets
# ---------------------------------------------------------------------------


def get_policy_for_profile(profile_name: str) -> UploadPolicy:
    """Get upload policy preset for a source profile."""
    if profile_name == "brand-public":
        return UploadPolicy(
            allowlist=[
                "brand-foundation", "brand-strategy", "campaign-content",
                "communications-social", "visual-asset-catalog",
            ],
            denylist=["debug-*", "test-*", "internal-notes*"],
            min_document_count=3,
            min_core_documents=2,
            max_document_count=50,
            strict_mode=True,
        )
    elif profile_name == "strategy-internal":
        return UploadPolicy(
            allowlist=[
                "brand-foundation", "brand-strategy",
            ],
            denylist=["debug-*", "test-*"],
            min_document_count=2,
            min_core_documents=1,
            max_document_count=30,
            strict_mode=False,
        )
    elif profile_name == "kickstarter-conditional":
        return UploadPolicy(
            allowlist=[
                "brand-foundation", "brand-strategy", "kickstarter-*",
            ],
            denylist=["debug-*", "test-*", "internal-notes*"],
            min_document_count=5,
            min_core_documents=2,
            max_document_count=40,
            strict_mode=True,
        )
    elif profile_name == "debug-internal":
        return UploadPolicy(
            allowlist=["*"],  # Allow everything
            denylist=[],
            min_document_count=1,
            min_core_documents=0,
            max_document_count=100,
            strict_mode=False,
        )
    else:
        # Default to brand-public policy
        return get_policy_for_profile("brand-public")
