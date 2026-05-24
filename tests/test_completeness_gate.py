"""Tests for completeness gate."""
from __future__ import annotations

import pytest

from brandmint.publishing.completeness_gate import (
    CompletenessGate,
    CompletenessResult,
    PlaceholderDetection,
    detect_placeholders,
    calculate_placeholder_percentage,
    check_completeness,
    check_documents_completeness,
    filter_complete_documents,
    generate_completeness_report,
    get_gate_for_profile,
)


class TestDetectPlaceholders:
    """Test placeholder detection."""

    def test_detects_todo(self):
        text = "TODO: Implement this feature."
        detections = detect_placeholders(text)
        assert any(d.pattern_name == "todo" for d in detections)

    def test_detects_coming_soon(self):
        text = "Coming soon to a store near you!"
        detections = detect_placeholders(text)
        assert any(d.pattern_name == "coming_soon" for d in detections)

    def test_detects_placeholder_text(self):
        text = "This is placeholder text for the layout."
        detections = detect_placeholders(text)
        assert any(d.pattern_name == "placeholder_text" for d in detections)

    def test_detects_template_markers(self):
        text = "Hello {{name}}, welcome to {{company}}."
        detections = detect_placeholders(text)
        template_detections = [d for d in detections if d.pattern_name == "template_marker"]
        assert len(template_detections) == 2

    def test_no_placeholders_in_clean_text(self):
        text = "We believe in creating exceptional products that deliver value."
        detections = detect_placeholders(text)
        assert len(detections) == 0

    def test_detects_line_numbers(self):
        text = "Line one\nTODO: Fix this\nLine three"
        detections = detect_placeholders(text)
        todo_detection = next(d for d in detections if d.pattern_name == "todo")
        assert todo_detection.line_number == 2


class TestCalculatePlaceholderPercentage:
    """Test placeholder percentage calculation."""

    def test_zero_placeholders(self):
        text = "Clean text with no placeholders."
        percentage = calculate_placeholder_percentage(text, [])
        assert percentage == 0.0

    def test_single_placeholder(self):
        text = "TODO: Fix this"
        detections = [PlaceholderDetection(
            pattern_name="todo",
            match_text="TODO",
            start_pos=0,
            end_pos=4,
            line_number=1,
        )]
        percentage = calculate_placeholder_percentage(text, detections)
        assert percentage > 0.0
        assert percentage <= 100.0

    def test_empty_text(self):
        percentage = calculate_placeholder_percentage("", [])
        assert percentage == 0.0


class TestCheckCompleteness:
    """Test completeness checking."""

    def test_complete_document(self):
        text = "We believe in creating exceptional products that deliver value to our customers every single day. Our mission is to transform the industry through innovative solutions and customer-centric design. We have built a comprehensive platform that addresses all key market needs."
        result = check_completeness("doc1", text)
        assert result.is_complete
        assert result.suppression_reason == ""

    def test_suppressed_for_too_many_placeholders(self):
        text = "TODO TBD FIXME XXX HACK TODO TBD FIXME XXX HACK TODO " * 5
        result = check_completeness("doc1", text)
        assert not result.is_complete
        assert "Too many placeholders" in result.suppression_reason

    def test_suppressed_for_high_placeholder_percentage(self):
        text = "{{name}} {{company}} {{product}} {{feature}} {{benefit}} {{value}} {{mission}} {{vision}} {{goal}} {{target}} " * 3
        gate = CompletenessGate(max_placeholder_percentage=10.0, max_placeholder_count=100, min_content_length=50)
        result = check_completeness("doc1", text, gate=gate)
        assert not result.is_complete
        assert "Placeholder content too high" in result.suppression_reason

    def test_suppressed_for_short_content(self):
        text = "Short."
        result = check_completeness("doc1", text)
        assert not result.is_complete
        assert "Content too short" in result.suppression_reason

    def test_suppressed_for_missing_sections(self):
        text = "Some content without required sections. This document has sufficient length to pass the minimum content check but lacks the mandatory sections that are required for completeness validation. We need to add more content here to ensure we exceed the minimum character threshold of 200 characters for the default gate configuration."
        result = check_completeness("doc1", text, mandatory_sections=["Brand Foundation", "Target Audience"])
        assert not result.is_complete
        assert "Missing mandatory sections" in result.suppression_reason
        assert len(result.missing_sections) == 2

    def test_override_allowed(self):
        text = "TODO: Complete this later."
        result = check_completeness("doc1", text)
        assert result.can_override

    def test_override_not_allowed_for_kickstarter(self):
        text = "TODO: Complete this later. " * 10
        gate = CompletenessGate(allow_override=False, max_placeholder_count=5)
        result = check_completeness("doc1", text, gate=gate)
        assert not result.can_override


class TestCheckDocumentsCompleteness:
    """Test batch completeness checking."""

    def test_checks_multiple_documents(self):
        docs = {
            "doc1": "Complete content here with sufficient length to pass the minimum content check and be considered complete. This document has enough characters to exceed the default gate threshold of 200 characters for sure.",
            "doc2": "TODO: Incomplete.",
            "doc3": "Another complete document with sufficient length to pass all completeness checks and be marked as complete. This document also exceeds the minimum character threshold required by the default gate configuration.",
        }
        results = check_documents_completeness(docs)
        assert len(results) == 3
        assert results["doc1"].is_complete
        assert not results["doc2"].is_complete
        assert results["doc3"].is_complete

    def test_empty_documents_dict(self):
        results = check_documents_completeness({})
        assert results == {}


class TestFilterCompleteDocuments:
    """Test document filtering."""

    def test_filters_incomplete_documents(self):
        docs = {
            "doc1": "Complete content.",
            "doc2": "TODO: Incomplete.",
            "doc3": "Another complete doc.",
        }
        results = {
            "doc1": CompletenessResult(doc_id="doc1", is_complete=True),
            "doc2": CompletenessResult(doc_id="doc2", is_complete=False, suppression_reason="test"),
            "doc3": CompletenessResult(doc_id="doc3", is_complete=True),
        }
        filtered = filter_complete_documents(docs, results)
        assert "doc1" in filtered
        assert "doc2" not in filtered
        assert "doc3" in filtered

    def test_allows_overrides(self):
        docs = {
            "doc1": "Complete content.",
            "doc2": "TODO: Incomplete but overridden.",
        }
        results = {
            "doc1": CompletenessResult(doc_id="doc1", is_complete=True),
            "doc2": CompletenessResult(doc_id="doc2", is_complete=False, suppression_reason="test", can_override=True),
        }
        filtered = filter_complete_documents(docs, results, allow_overrides={"doc2"})
        assert "doc1" in filtered
        assert "doc2" in filtered  # Override allowed

    def test_includes_unchecked_documents(self):
        docs = {"doc1": "Content without completeness check."}
        filtered = filter_complete_documents(docs, {})
        assert "doc1" in filtered  # Included by default


class TestGenerateCompletenessReport:
    """Test report generation."""

    def test_generates_report_with_suppressed_docs(self):
        results = {
            "doc1": CompletenessResult(doc_id="doc1", is_complete=True),
            "doc2": CompletenessResult(
                doc_id="doc2",
                is_complete=False,
                suppression_reason="Too many placeholders",
                placeholder_count=15,
                placeholder_percentage=25.0,
                can_override=True,
            ),
        }
        report = generate_completeness_report(results)
        assert "# Completeness Gate Report" in report
        assert "## Summary" in report
        assert "Total documents: 2" in report
        assert "Suppressed: 1" in report
        assert "## Suppressed Documents" in report
        assert "### doc2" in report

    def test_generates_report_with_no_suppressed_docs(self):
        results = {
            "doc1": CompletenessResult(doc_id="doc1", is_complete=True),
            "doc2": CompletenessResult(doc_id="doc2", is_complete=True),
        }
        report = generate_completeness_report(results)
        assert "# Completeness Gate Report" in report
        assert "Suppressed: 0" in report
        assert "## Suppressed Documents" not in report


class TestGetGateForProfile:
    """Test gate presets for profiles."""

    def test_brand_public_gate(self):
        gate = get_gate_for_profile("brand-public")
        assert gate.max_placeholder_percentage == 5.0
        assert gate.max_placeholder_count == 5
        assert gate.check_mandatory_sections is True
        assert gate.min_content_length == 300

    def test_strategy_internal_gate(self):
        gate = get_gate_for_profile("strategy-internal")
        assert gate.max_placeholder_percentage == 15.0
        assert gate.check_mandatory_sections is False

    def test_kickstarter_conditional_gate(self):
        gate = get_gate_for_profile("kickstarter-conditional")
        assert gate.max_placeholder_percentage == 0.0
        assert gate.max_placeholder_count == 0
        assert gate.allow_override is False

    def test_debug_internal_gate(self):
        gate = get_gate_for_profile("debug-internal")
        assert gate.max_placeholder_percentage == 100.0
        assert gate.min_content_length == 0

    def test_unknown_profile_defaults_to_brand_public(self):
        gate = get_gate_for_profile("unknown")
        brand_public_gate = get_gate_for_profile("brand-public")
        assert gate.max_placeholder_percentage == brand_public_gate.max_placeholder_percentage
