"""
Completeness gate — suppresses placeholder-heavy and incomplete source documents
from NotebookLM upload.

NotebookLM generates poor artifacts when source documents contain:
- Placeholder content (TODO, TBD, coming soon, etc.)
- Missing mandatory sections
- Incomplete artifact data

This module:
1. Detects placeholder-heavy documents
2. Checks for mandatory artifact completeness
3. Suppresses incomplete documents from upload
4. Provides operator override mechanisms
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


# ---------------------------------------------------------------------------
# Placeholder pattern definitions
# ---------------------------------------------------------------------------

PLACEHOLDER_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("todo", re.compile(r'\b(?:TODO|TBD|FIXME|XXX|HACK)\b', re.IGNORECASE)),
    ("coming_soon", re.compile(r'\b(?:coming soon|coming shortly|stay tuned|watch this space)\b', re.IGNORECASE)),
    ("placeholder_text", re.compile(r'\b(?:lorem ipsum|placeholder text|sample text|dummy text|example text)\b', re.IGNORECASE)),
    ("incomplete_section", re.compile(r'\b(?:section incomplete|work in progress|draft|under construction|not yet implemented)\b', re.IGNORECASE)),
    ("missing_data", re.compile(r'\b(?:N/A|not available|data missing|no data|pending|awaiting)\b', re.IGNORECASE)),
    ("template_marker", re.compile(r'\{\{.*?\}\}|\[.*?\]', re.IGNORECASE)),  # {{variable}} or [variable]
    ("empty_list", re.compile(r'^\s*[-*]\s*$', re.MULTILINE)),  # Empty bullet points
    ("short_content", re.compile(r'^.{0,50}$', re.MULTILINE)),  # Very short lines (likely placeholders)
]


@dataclass
class PlaceholderDetection:
    """Result of placeholder detection in a document."""
    pattern_name: str
    match_text: str
    start_pos: int
    end_pos: int
    line_number: int = 0


@dataclass
class CompletenessResult:
    """Result of completeness check for a document."""
    doc_id: str
    is_complete: bool
    placeholder_count: int = 0
    placeholder_percentage: float = 0.0
    missing_sections: List[str] = field(default_factory=list)
    detections: List[PlaceholderDetection] = field(default_factory=list)
    suppression_reason: str = ""
    can_override: bool = True


@dataclass
class CompletenessGate:
    """Configuration for completeness gate."""
    # Maximum percentage of placeholder content allowed
    max_placeholder_percentage: float = 15.0
    # Maximum number of placeholder detections allowed
    max_placeholder_count: int = 10
    # Whether to check for mandatory sections
    check_mandatory_sections: bool = True
    # Minimum content length (characters) to consider complete
    min_content_length: int = 200
    # Whether suppression can be overridden by operator
    allow_override: bool = True


# ---------------------------------------------------------------------------
# Detection engine
# ---------------------------------------------------------------------------


def detect_placeholders(text: str) -> List[PlaceholderDetection]:
    """Detect placeholder patterns in text."""
    detections = []

    for pattern_name, pattern in PLACEHOLDER_PATTERNS:
        for match in pattern.finditer(text):
            # Calculate line number
            line_number = text[:match.start()].count('\n') + 1

            detections.append(PlaceholderDetection(
                pattern_name=pattern_name,
                match_text=match.group(),
                start_pos=match.start(),
                end_pos=match.end(),
                line_number=line_number,
            ))

    return detections


def calculate_placeholder_percentage(text: str, detections: List[PlaceholderDetection]) -> float:
    """Calculate percentage of text that is placeholder content."""
    if not text or not detections:
        return 0.0

    # Calculate total placeholder characters (avoiding double-counting overlaps)
    placeholder_chars = set()
    for detection in detections:
        for pos in range(detection.start_pos, detection.end_pos):
            placeholder_chars.add(pos)

    return (len(placeholder_chars) / len(text)) * 100


# ---------------------------------------------------------------------------
# Completeness check
# ---------------------------------------------------------------------------


def check_completeness(
    doc_id: str,
    text: str,
    mandatory_sections: Optional[List[str]] = None,
    gate: Optional[CompletenessGate] = None
) -> CompletenessResult:
    """Check if a document meets completeness requirements."""
    if gate is None:
        gate = CompletenessGate()

    # Check content length
    if len(text) < gate.min_content_length:
        return CompletenessResult(
            doc_id=doc_id,
            is_complete=False,
            suppression_reason=f"Content too short ({len(text)} chars < {gate.min_content_length} min)",
            can_override=gate.allow_override,
        )

    # Detect placeholders
    detections = detect_placeholders(text)
    placeholder_percentage = calculate_placeholder_percentage(text, detections)

    # Check placeholder thresholds
    if len(detections) > gate.max_placeholder_count:
        return CompletenessResult(
            doc_id=doc_id,
            is_complete=False,
            placeholder_count=len(detections),
            placeholder_percentage=placeholder_percentage,
            detections=detections,
            suppression_reason=f"Too many placeholders ({len(detections)} > {gate.max_placeholder_count} max)",
            can_override=gate.allow_override,
        )

    if placeholder_percentage > gate.max_placeholder_percentage:
        return CompletenessResult(
            doc_id=doc_id,
            is_complete=False,
            placeholder_count=len(detections),
            placeholder_percentage=placeholder_percentage,
            detections=detections,
            suppression_reason=f"Placeholder content too high ({placeholder_percentage:.1f}% > {gate.max_placeholder_percentage}% max)",
            can_override=gate.allow_override,
        )

    # Check mandatory sections
    missing_sections = []
    if gate.check_mandatory_sections and mandatory_sections:
        for section in mandatory_sections:
            if section.lower() not in text.lower():
                missing_sections.append(section)

    if missing_sections:
        return CompletenessResult(
            doc_id=doc_id,
            is_complete=False,
            placeholder_count=len(detections),
            placeholder_percentage=placeholder_percentage,
            missing_sections=missing_sections,
            detections=detections,
            suppression_reason=f"Missing mandatory sections: {', '.join(missing_sections)}",
            can_override=gate.allow_override,
        )

    # Document is complete
    return CompletenessResult(
        doc_id=doc_id,
        is_complete=True,
        placeholder_count=len(detections),
        placeholder_percentage=placeholder_percentage,
        detections=detections,
    )


# ---------------------------------------------------------------------------
# Batch processing
# ---------------------------------------------------------------------------


def check_documents_completeness(
    documents: Dict[str, str],
    mandatory_sections: Optional[Dict[str, List[str]]] = None,
    gate: Optional[CompletenessGate] = None
) -> Dict[str, CompletenessResult]:
    """Check completeness of multiple documents."""
    results = {}
    for doc_id, text in documents.items():
        doc_sections = mandatory_sections.get(doc_id, []) if mandatory_sections else []
        results[doc_id] = check_completeness(doc_id, text, doc_sections, gate)
    return results


def filter_complete_documents(
    documents: Dict[str, str],
    completeness_results: Dict[str, CompletenessResult],
    allow_overrides: Optional[Set[str]] = None
) -> Dict[str, str]:
    """Filter documents to only include complete ones (with optional overrides)."""
    if allow_overrides is None:
        allow_overrides = set()

    filtered = {}
    for doc_id, text in documents.items():
        result = completeness_results.get(doc_id)
        if result is None:
            # No completeness check performed, include by default
            filtered[doc_id] = text
            continue

        if result.is_complete:
            filtered[doc_id] = text
        elif doc_id in allow_overrides and result.can_override:
            # Operator override
            filtered[doc_id] = text

    return filtered


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def generate_completeness_report(results: Dict[str, CompletenessResult]) -> str:
    """Generate a human-readable completeness report."""
    parts = ["# Completeness Gate Report\n"]

    total_docs = len(results)
    complete_docs = sum(1 for r in results.values() if r.is_complete)
    suppressed_docs = total_docs - complete_docs

    parts.append(f"## Summary\n")
    parts.append(f"- Total documents: {total_docs}")
    parts.append(f"- Complete: {complete_docs}")
    parts.append(f"- Suppressed: {suppressed_docs}")
    parts.append("")

    if suppressed_docs > 0:
        parts.append("## Suppressed Documents\n")
        for doc_id, result in sorted(results.items()):
            if result.is_complete:
                continue

            parts.append(f"### {doc_id}")
            parts.append(f"- **Reason:** {result.suppression_reason}")
            parts.append(f"- **Placeholders:** {result.placeholder_count} ({result.placeholder_percentage:.1f}%)")
            if result.missing_sections:
                parts.append(f"- **Missing sections:** {', '.join(result.missing_sections)}")
            parts.append(f"- **Can override:** {'Yes' if result.can_override else 'No'}")
            parts.append("")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Gate presets
# ---------------------------------------------------------------------------


def get_gate_for_profile(profile_name: str) -> CompletenessGate:
    """Get completeness gate preset for a source profile."""
    if profile_name == "brand-public":
        return CompletenessGate(
            max_placeholder_percentage=5.0,
            max_placeholder_count=5,
            check_mandatory_sections=True,
            min_content_length=300,
            allow_override=True,
        )
    elif profile_name == "strategy-internal":
        return CompletenessGate(
            max_placeholder_percentage=15.0,
            max_placeholder_count=15,
            check_mandatory_sections=False,
            min_content_length=200,
            allow_override=True,
        )
    elif profile_name == "kickstarter-conditional":
        return CompletenessGate(
            max_placeholder_percentage=0.0,  # No placeholders allowed
            max_placeholder_count=0,
            check_mandatory_sections=True,
            min_content_length=500,
            allow_override=False,  # No override for kickstarter
        )
    elif profile_name == "debug-internal":
        return CompletenessGate(
            max_placeholder_percentage=100.0,  # Allow all
            max_placeholder_count=1000,
            check_mandatory_sections=False,
            min_content_length=0,
            allow_override=True,
        )
    else:
        # Default to brand-public gate
        return get_gate_for_profile("brand-public")
