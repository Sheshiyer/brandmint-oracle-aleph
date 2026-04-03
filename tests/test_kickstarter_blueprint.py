import json
from pathlib import Path

from brandmint.core.kickstarter_blueprint import (
    MANDATORY_KICKSTARTER_ARTIFACTS,
    MANDATORY_KICKSTARTER_SECTIONS,
    artifact_ids_for_source_skill,
    build_kickstarter_readiness,
    build_kickstarter_readiness_from_outputs,
    mandatory_source_skill_ids,
    section_ids_for_source_skills,
)


def test_mandatory_sections_cover_expected_artifact_count() -> None:
    assert len(MANDATORY_KICKSTARTER_SECTIONS) == 6
    assert len(MANDATORY_KICKSTARTER_ARTIFACTS) == 15


def test_mandatory_source_skill_ids_are_unique_and_backed() -> None:
    skill_ids = mandatory_source_skill_ids()
    assert len(skill_ids) == len(set(skill_ids))
    assert "buyer-persona" in skill_ids
    assert "mds-messaging-direction-summary" in skill_ids
    assert "campaign-page-copy" in skill_ids



def test_skill_to_artifact_and_section_mappings_are_stable() -> None:
    assert artifact_ids_for_source_skill("campaign-page-copy") == [
        "landing-page-copy",
        "campaign-page-copy",
    ]
    assert section_ids_for_source_skills([
        "buyer-persona",
        "voice-and-tone",
        "campaign-page-copy",
    ]) == [
        "market-understanding",
        "product-detailing",
        "crafting-compelling-copy",
        "campaign-messaging",
    ]



def test_build_kickstarter_readiness_reports_missing_artifacts() -> None:
    outputs = {
        "buyer-persona": {"persona": {"name": "Asha"}},
        "competitor-analysis": {"handoff": {"competitors": ["A", "B"]}},
        "campaign-page-copy": {"handoff": {"headline": "Launch better"}},
    }

    readiness = build_kickstarter_readiness(outputs)

    assert readiness["artifact_status"]["market-buyer-persona"] is True
    assert readiness["artifact_status"]["competitor-summary"] is True
    assert readiness["artifact_status"]["landing-page-copy"] is True
    assert readiness["artifact_status"]["campaign-page-copy"] is True
    assert readiness["artifact_status"]["voice-and-tone"] is False

    market = readiness["section_status"]["market-understanding"]
    assert market["ready"] is True
    assert market["completed"] == 2

    product = readiness["section_status"]["product-detailing"]
    assert product["ready"] is False
    assert set(product["missing_artifact_ids"]) == {
        "detailed-product-description",
        "product-positioning-summary",
        "mds",
        "voice-and-tone",
    }

    assert readiness["all_ready"] is False



def test_build_kickstarter_readiness_from_outputs_dir(tmp_path: Path) -> None:
    outputs_dir = tmp_path / ".brandmint" / "outputs"
    outputs_dir.mkdir(parents=True)
    (outputs_dir / "buyer-persona.json").write_text(json.dumps({"persona": {"name": "Asha"}}))
    (outputs_dir / "competitor-analysis.json").write_text(json.dumps({"handoff": {"competitors": ["A"]}}))
    (outputs_dir / "voice-and-tone.json").write_text(json.dumps({"voice_persona": {"identity": "Calm guide"}}))
    (outputs_dir / "not-mandatory.json").write_text(json.dumps({"ignored": True}))

    readiness = build_kickstarter_readiness_from_outputs(outputs_dir)

    assert readiness["section_status"]["market-understanding"]["ready"] is True
    assert readiness["section_status"]["product-detailing"]["completed"] == 1
    assert readiness["artifact_status"]["voice-and-tone"] is True
    assert readiness["artifact_status"]["campaign-page-copy"] is False
