"""
Curation scoring — calculates quality scores for source documents and applies
penalties for placeholder/meta content density.

NotebookLM generates better artifacts from high-quality source documents.
This module:
1. Calculates base quality scores for documents
2. Applies penalties for placeholder density
3. Applies penalties for meta-content density
4. Produces final curation scores for upload prioritization
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .anti_meta_transform import detect_meta_content, AntiMetaPolicy
from .completeness_gate import detect_placeholders, calculate_placeholder_percentage, CompletenessGate


@dataclass
class CurationScore:
    """Quality score for a source document."""
    doc_id: str
    base_score: float  # 0-100
    placeholder_penalty: float  # 0-100
    meta_penalty: float  # 0-100
    final_score: float  # 0-100
    is_uploadable: bool
    suppression_reasons: List[str] = field(default_factory=list)


@dataclass
class CurationWeights:
    """Weights for curation scoring."""
    # Base score weight (content quality, length, etc.)
    base_weight: float = 1.0
    # Placeholder penalty multiplier
    placeholder_penalty_multiplier: float = 2.0
    # Meta-content penalty multiplier
    meta_penalty_multiplier: float = 1.5
    # Minimum final score to be uploadable
    min_uploadable_score: float = 70.0


# ---------------------------------------------------------------------------
# Base score calculation
# ---------------------------------------------------------------------------


def calculate_base_score(text: str, gate: Optional[CompletenessGate] = None) -> float:
    """Calculate base quality score for a document (0-100)."""
    if gate is None:
        gate = CompletenessGate()

    score = 50.0  # Base score

    # Content length bonus (up to +20 points)
    length_ratio = min(1.0, len(text) / max(gate.min_content_length * 2, 400))
    score += length_ratio * 20

    # Placeholder penalty (up to -30 points)
    detections = detect_placeholders(text)
    placeholder_percentage = calculate_placeholder_percentage(text, detections)
    placeholder_penalty = min(30.0, (placeholder_percentage / gate.max_placeholder_percentage) * 30)
    score -= placeholder_penalty

    # Ensure score is within bounds
    return max(0.0, min(100.0, score))


# ---------------------------------------------------------------------------
# Penalty calculations
# ---------------------------------------------------------------------------


def calculate_placeholder_penalty(text: str, gate: Optional[CompletenessGate] = None) -> float:
    """Calculate placeholder penalty (0-100)."""
    if gate is None:
        gate = CompletenessGate()

    detections = detect_placeholders(text)
    placeholder_percentage = calculate_placeholder_percentage(text, detections)

    # Penalty scales with percentage
    penalty = (placeholder_percentage / gate.max_placeholder_percentage) * 100
    return min(100.0, max(0.0, penalty))


def calculate_meta_penalty(text: str, policy: Optional[AntiMetaPolicy] = None) -> float:
    """Calculate meta-content penalty (0-100)."""
    if policy is None:
        policy = AntiMetaPolicy()

    detections = detect_meta_content(text, policy)

    if not detections:
        return 0.0

    # Calculate meta-content percentage
    meta_chars = sum(d.end_pos - d.start_pos for d in detections)
    meta_percentage = (meta_chars / len(text) * 100) if text else 0

    # Penalty scales with percentage
    penalty = meta_percentage * 2  # Multiplier for emphasis
    return min(100.0, max(0.0, penalty))


# ---------------------------------------------------------------------------
# Final score calculation
# ---------------------------------------------------------------------------


def calculate_curation_score(
    doc_id: str,
    text: str,
    weights: Optional[CurationWeights] = None,
    gate: Optional[CompletenessGate] = None,
    policy: Optional[AntiMetaPolicy] = None
) -> CurationScore:
    """Calculate final curation score for a document."""
    if weights is None:
        weights = CurationWeights()
    if gate is None:
        gate = CompletenessGate()
    if policy is None:
        policy = AntiMetaPolicy()

    # Calculate base score
    base_score = calculate_base_score(text, gate)

    # Calculate penalties
    placeholder_penalty = calculate_placeholder_penalty(text, gate)
    meta_penalty = calculate_meta_penalty(text, policy)

    # Apply weighted penalties
    final_score = (
        base_score * weights.base_weight
        - placeholder_penalty * weights.placeholder_penalty_multiplier
        - meta_penalty * weights.meta_penalty_multiplier
    )

    # Ensure score is within bounds
    final_score = max(0.0, min(100.0, final_score))

    # Determine if uploadable
    is_uploadable = final_score >= weights.min_uploadable_score

    # Collect suppression reasons
    suppression_reasons = []
    if not is_uploadable:
        if final_score < weights.min_uploadable_score:
            suppression_reasons.append(f"Score {final_score:.1f} < {weights.min_uploadable_score} minimum")
        if placeholder_penalty > 50:
            suppression_reasons.append(f"High placeholder penalty ({placeholder_penalty:.1f})")
        if meta_penalty > 50:
            suppression_reasons.append(f"High meta-content penalty ({meta_penalty:.1f})")

    return CurationScore(
        doc_id=doc_id,
        base_score=base_score,
        placeholder_penalty=placeholder_penalty,
        meta_penalty=meta_penalty,
        final_score=final_score,
        is_uploadable=is_uploadable,
        suppression_reasons=suppression_reasons,
    )


# ---------------------------------------------------------------------------
# Batch processing
# ---------------------------------------------------------------------------


def calculate_curation_scores(
    documents: Dict[str, str],
    weights: Optional[CurationWeights] = None,
    gate: Optional[CompletenessGate] = None,
    policy: Optional[AntiMetaPolicy] = None
) -> Dict[str, CurationScore]:
    """Calculate curation scores for multiple documents."""
    scores = {}
    for doc_id, text in documents.items():
        scores[doc_id] = calculate_curation_score(doc_id, text, weights, gate, policy)
    return scores


def filter_uploadable_documents(
    documents: Dict[str, str],
    scores: Dict[str, CurationScore]
) -> Dict[str, str]:
    """Filter documents to only include uploadable ones."""
    return {
        doc_id: text
        for doc_id, text in documents.items()
        if scores.get(doc_id, CurationScore(doc_id, 0, 0, 0, 0, False)).is_uploadable
    }


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def generate_curation_report(scores: Dict[str, CurationScore]) -> str:
    """Generate a human-readable curation report."""
    parts = ["# Curation Scoring Report\n"]

    total_docs = len(scores)
    uploadable_docs = sum(1 for s in scores.values() if s.is_uploadable)
    suppressed_docs = total_docs - uploadable_docs

    avg_score = sum(s.final_score for s in scores.values()) / max(1, total_docs)

    parts.append("## Summary\n")
    parts.append(f"- Total documents: {total_docs}")
    parts.append(f"- Uploadable: {uploadable_docs}")
    parts.append(f"- Suppressed: {suppressed_docs}")
    parts.append(f"- Average score: {avg_score:.1f}")
    parts.append("")

    if suppressed_docs > 0:
        parts.append("## Suppressed Documents\n")
        for doc_id, score in sorted(scores.items(), key=lambda x: x[1].final_score):
            if score.is_uploadable:
                continue

            parts.append(f"### {doc_id}")
            parts.append(f"- **Final score:** {score.final_score:.1f}")
            parts.append(f"- **Base score:** {score.base_score:.1f}")
            parts.append(f"- **Placeholder penalty:** {score.placeholder_penalty:.1f}")
            parts.append(f"- **Meta penalty:** {score.meta_penalty:.1f}")
            if score.suppression_reasons:
                parts.append(f"- **Reasons:** {'; '.join(score.suppression_reasons)}")
            parts.append("")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Weight presets
# ---------------------------------------------------------------------------


def get_weights_for_profile(profile_name: str) -> CurationWeights:
    """Get curation weights preset for a source profile."""
    if profile_name == "brand-public":
        return CurationWeights(
            base_weight=1.0,
            placeholder_penalty_multiplier=2.0,
            meta_penalty_multiplier=1.5,
            min_uploadable_score=75.0,
        )
    elif profile_name == "strategy-internal":
        return CurationWeights(
            base_weight=1.0,
            placeholder_penalty_multiplier=1.5,
            meta_penalty_multiplier=1.0,
            min_uploadable_score=60.0,
        )
    elif profile_name == "kickstarter-conditional":
        return CurationWeights(
            base_weight=1.0,
            placeholder_penalty_multiplier=3.0,
            meta_penalty_multiplier=2.0,
            min_uploadable_score=85.0,
        )
    elif profile_name == "debug-internal":
        return CurationWeights(
            base_weight=1.0,
            placeholder_penalty_multiplier=0.5,
            meta_penalty_multiplier=0.5,
            min_uploadable_score=0.0,
        )
    else:
        # Default to brand-public weights
        return get_weights_for_profile("brand-public")
