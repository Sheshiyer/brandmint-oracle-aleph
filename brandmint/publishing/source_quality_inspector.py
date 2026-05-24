"""Source quality inspector for NotebookLM publish readiness.

Detects meta/process language leakage and placeholder-heavy source docs,
then scores each document for publish suitability.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence


@dataclass(frozen=True)
class ForbiddenRule:
    """A forbidden language rule for source documents."""

    key: str
    pattern: str
    reason: str
    severity: int = 1


DEFAULT_FORBIDDEN_RULES: Sequence[ForbiddenRule] = (
    ForbiddenRule(
        key="source_skill_label",
        pattern=r"source\s+skill",
        reason="Pipeline-internal labels leak into published prose.",
        severity=2,
    ),
    ForbiddenRule(
        key="missing_artifact_stub",
        pattern=r"this\s+mandatory\s+artifact\s+has\s+not\s+been\s+generated\s+yet",
        reason="Placeholder stubs should never ship to NotebookLM.",
        severity=3,
    ),
    ForbiddenRule(
        key="waiting_on_stub",
        pattern=r"waiting\s+on\s+`?[a-z0-9\-]+`?\s+output",
        reason="Dependency placeholders indicate incomplete source material.",
        severity=3,
    ),
    ForbiddenRule(
        key="analysis_shows",
        pattern=r"\b(the\s+)?analysis\s+shows\b",
        reason="Meta analytical framing should be rewritten to direct brand voice.",
        severity=2,
    ),
    ForbiddenRule(
        key="data_reveals",
        pattern=r"\b(the\s+)?data\s+reveals\b",
        reason="Meta analytical framing should be rewritten to direct brand voice.",
        severity=2,
    ),
    ForbiddenRule(
        key="source_document_wording",
        pattern=r"\bsource\s+document(s)?\b",
        reason="Internal document framing should not appear in published content.",
        severity=1,
    ),
)


PLACEHOLDER_MARKERS: Sequence[str] = (
    "Missing Mandatory Artifacts",
    "waiting on `",
    "_This mandatory artifact has not been generated yet._",
    "Readiness: In progress (0/",
)


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'\-]+\b", text))


def _non_blank_lines(text: str) -> List[str]:
    return [line for line in text.splitlines() if line.strip()]


def _bullet_count(lines: Iterable[str]) -> int:
    return sum(1 for line in lines if line.lstrip().startswith(("-", "*")))


def _heading_count(lines: Iterable[str]) -> int:
    return sum(1 for line in lines if line.lstrip().startswith("#"))


def _classify(score: float) -> str:
    if score >= 85:
        return "pass"
    if score >= 70:
        return "warn"
    return "fail"


def analyze_source_text(
    text: str,
    rules: Optional[Sequence[ForbiddenRule]] = None,
) -> Dict[str, Any]:
    """Analyze one source document and return quality metrics.

    Scoring model is intentionally conservative for publishing quality:
    - Forbidden/meta hits are heavily penalized.
    - Placeholder markers are heavily penalized.
    - Overly list-like docs get mild penalties.
    """
    active_rules = rules or DEFAULT_FORBIDDEN_RULES
    lines = _non_blank_lines(text)
    words = _word_count(text)

    forbidden_hits: List[Dict[str, Any]] = []
    forbidden_count = 0
    forbidden_weighted = 0

    for rule in active_rules:
        matches = re.findall(rule.pattern, text, flags=re.IGNORECASE)
        hit_count = len(matches)
        if not hit_count:
            continue
        forbidden_hits.append(
            {
                "key": rule.key,
                "count": hit_count,
                "severity": rule.severity,
                "reason": rule.reason,
            }
        )
        forbidden_count += hit_count
        forbidden_weighted += hit_count * rule.severity

    placeholder_count = sum(text.count(marker) for marker in PLACEHOLDER_MARKERS)
    bullet_count = _bullet_count(lines)
    heading_count = _heading_count(lines)
    line_count = len(lines)
    bullet_ratio = (bullet_count / line_count) if line_count else 0.0
    chars = len(text)

    penalties = 0.0
    penalties += forbidden_weighted * 4.5
    penalties += placeholder_count * 10.0
    if bullet_ratio > 0.45:
        penalties += min(20.0, (bullet_ratio - 0.45) * 80.0)
    if words < 120:
        penalties += 12.0

    score = max(0.0, min(100.0, 100.0 - penalties))
    classification = _classify(score)
    meta_density = (forbidden_count / max(1, words)) * 1000.0

    return {
        "score": round(score, 2),
        "classification": classification,
        "word_count": words,
        "char_count": chars,
        "line_count": line_count,
        "heading_count": heading_count,
        "bullet_count": bullet_count,
        "bullet_ratio": round(bullet_ratio, 4),
        "forbidden_hit_count": forbidden_count,
        "forbidden_weighted_hits": forbidden_weighted,
        "placeholder_marker_count": placeholder_count,
        "meta_density_per_1k_words": round(meta_density, 2),
        "forbidden_hits": forbidden_hits,
    }


def analyze_source_file(
    path: Path,
    rules: Optional[Sequence[ForbiddenRule]] = None,
) -> Dict[str, Any]:
    """Analyze a markdown source file."""
    text = path.read_text(encoding="utf-8")
    metrics = analyze_source_text(text, rules=rules)
    return {
        "file": path.name,
        "path": str(path),
        **metrics,
    }


def analyze_sources_dir(
    sources_dir: Path,
    rules: Optional[Sequence[ForbiddenRule]] = None,
) -> Dict[str, Any]:
    """Analyze all markdown files in a source directory."""
    files = sorted(sources_dir.glob("*.md"))
    reports = [analyze_source_file(path, rules=rules) for path in files]
    reports.sort(key=lambda row: (row["score"], row["file"]))

    if not reports:
        return {
            "sources_dir": str(sources_dir),
            "file_count": 0,
            "average_score": 0.0,
            "failing_files": 0,
            "warning_files": 0,
            "passing_files": 0,
            "total_forbidden_hits": 0,
            "total_placeholder_markers": 0,
            "files": [],
        }

    average_score = sum(row["score"] for row in reports) / len(reports)
    passing_files = sum(1 for row in reports if row["classification"] == "pass")
    warning_files = sum(1 for row in reports if row["classification"] == "warn")
    failing_files = sum(1 for row in reports if row["classification"] == "fail")
    total_forbidden_hits = sum(row["forbidden_hit_count"] for row in reports)
    total_placeholder_markers = sum(row["placeholder_marker_count"] for row in reports)

    return {
        "sources_dir": str(sources_dir),
        "file_count": len(reports),
        "average_score": round(average_score, 2),
        "failing_files": failing_files,
        "warning_files": warning_files,
        "passing_files": passing_files,
        "total_forbidden_hits": total_forbidden_hits,
        "total_placeholder_markers": total_placeholder_markers,
        "files": reports,
    }


def render_markdown_report(payload: Dict[str, Any]) -> str:
    """Render analysis payload as a markdown report."""
    lines: List[str] = []
    lines.append("# NotebookLM Source Quality Baseline")
    lines.append("")
    lines.append(f"- **Sources dir:** `{payload['sources_dir']}`")
    lines.append(f"- **Files scanned:** {payload['file_count']}")
    lines.append(f"- **Average score:** {payload['average_score']}")
    lines.append(
        f"- **Classification counts:** pass={payload['passing_files']}, warn={payload['warning_files']}, fail={payload['failing_files']}"
    )
    lines.append(f"- **Total forbidden hits:** {payload['total_forbidden_hits']}")
    lines.append(f"- **Total placeholder markers:** {payload['total_placeholder_markers']}")
    lines.append("")
    lines.append("## Worst Files First")
    lines.append("")

    for row in payload["files"]:
        lines.append(
            f"### {row['file']} — score {row['score']} ({row['classification']})"
        )
        lines.append(
            f"- words={row['word_count']}, bullets={row['bullet_count']}, forbidden_hits={row['forbidden_hit_count']}, placeholders={row['placeholder_marker_count']}"
        )
        if row["forbidden_hits"]:
            lines.append("- forbidden patterns:")
            for hit in row["forbidden_hits"]:
                lines.append(
                    f"  - `{hit['key']}` x{hit['count']} (severity {hit['severity']}): {hit['reason']}"
                )
        lines.append("")

    return "\n".join(lines).strip() + "\n"
