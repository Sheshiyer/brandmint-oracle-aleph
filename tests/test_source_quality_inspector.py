from __future__ import annotations

from pathlib import Path

from brandmint.publishing.source_quality_inspector import (
    analyze_source_text,
    analyze_sources_dir,
)


def test_analyze_source_text_flags_meta_and_placeholders() -> None:
    text = """
# Part 5 — Perfecting the Campaign Messaging

## Missing Mandatory Artifacts
- Campaign Page Copy: waiting on `campaign-page-copy` output

_This mandatory artifact has not been generated yet._
"""
    report = analyze_source_text(text)
    assert report["classification"] == "fail"
    assert report["forbidden_hit_count"] >= 2
    assert report["placeholder_marker_count"] >= 2
    assert report["score"] < 70


def test_analyze_source_text_passes_clean_brand_narrative() -> None:
    text = """
## Quiet Craft, Loud Results

Newsense builds restrained brand systems for commissioning creative directors who demand precision.
We translate material truth into campaign language that stays consistent from first storyboard to final frame.

Our studio voice is calm, specific, and grounded in light, texture, and composition.
Each engagement pairs strategic clarity with film-grade production discipline so launch assets feel cohesive,
premium, and unmistakably authored.

The result is a brand presence that signals confidence without noise and converts on substance.
"""
    report = analyze_source_text(text)
    assert report["classification"] in {"pass", "warn"}
    assert report["forbidden_hit_count"] == 0
    assert report["placeholder_marker_count"] == 0


def test_analyze_sources_dir_aggregates_and_sorts_worst_first(tmp_path: Path) -> None:
    sources = tmp_path / "sources"
    sources.mkdir(parents=True)

    bad = sources / "bad.md"
    bad.write_text(
        "Source skill: `x`\nwaiting on `campaign-page-copy` output\n"
        "_This mandatory artifact has not been generated yet._\n",
        encoding="utf-8",
    )
    good = sources / "good.md"
    good.write_text(
        "## Studio Perspective\n"
        "Newsense designs restrained brand systems with deliberate pacing and material clarity.\n"
        * 20,
        encoding="utf-8",
    )

    payload = analyze_sources_dir(sources)
    assert payload["file_count"] == 2
    assert payload["files"][0]["file"] == "bad.md"
    assert payload["total_forbidden_hits"] >= 1
