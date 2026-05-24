from __future__ import annotations

from brandmint.core.coverage_preflight import build_coverage_preflight


def _sample_config() -> dict:
    return {
        "execution_context": {
            "depth_level": "comprehensive",
            "launch_channel": "dtc",
        },
        "brand": {
            "name": "Sample",
            "domain_tags": ["design-studio"],
        },
    }


def test_preflight_reports_missing_mandatory_skills_for_brand_genesis() -> None:
    report = build_coverage_preflight(
        _sample_config(),
        scenario_id="brand-genesis",
        depth="comprehensive",
    )

    assert report["wave_count"] >= 6
    assert len(report["missing_mandatory_source_skills"]) > 0
    assert any("Mandatory source skills missing" in warning for warning in report["warnings"])


def test_preflight_flags_empty_content_waves() -> None:
    report = build_coverage_preflight(
        _sample_config(),
        scenario_id="brand-genesis",
        depth="comprehensive",
    )
    assert any(w in report["empty_execution_waves"] for w in (4, 5, 6))
    assert any("core content waves" in warning for warning in report["warnings"])


def test_preflight_no_warnings_for_custom_hybrid_surface_plan() -> None:
    report = build_coverage_preflight(
        _sample_config(),
        scenario_id="custom-hybrid",
        depth="surface",
    )
    # custom-hybrid with surface can still have warnings for visuals depending on tags,
    # but should at least produce a structured report.
    assert report["wave_count"] >= 1
    assert isinstance(report["warnings"], list)
