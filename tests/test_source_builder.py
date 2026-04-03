import json
from pathlib import Path

import yaml

from brandmint.publishing.source_builder import build_source_documents


SAMPLE_CONFIG = {
    "brand": {"name": "Prototype Brand"},
    "palette": {"primary": {"name": "Indigo", "hex": "#4f46e5"}},
}


SAMPLE_OUTPUTS = {
    "buyer-persona": {"persona": {"name": "Asha", "pain_points": ["waste", "clutter"]}},
    "competitor-analysis": {"handoff": {"key_differentiators": ["cleaner", "faster"]}},
    "detailed-product-description": {"hero_product": {"name": "Prototype Pack", "description": "A modular carry system."}},
    "product-positioning-summary": {"positioning_statement": "The fastest way to organize."},
    "mds-messaging-direction-summary": {"hero_headline": "Own your flow", "tagline": "Carry less, do more"},
    "voice-and-tone": {"voice_persona": {"identity": "Calm guide"}, "tone_calibration": ["clear", "assured"]},
    "campaign-page-copy": {"handoff": {"headline": "Back the future of carry"}},
    "pre-launch-ads": {"handoff": {"hooks": ["Be first", "Carry smarter"]}},
    "welcome-email-sequence": {"handoff": {"emails": ["welcome-1", "welcome-2"]}},
    "pre-launch-email-sequence": {"handoff": {"emails": ["tease-1", "tease-2"]}},
    "launch-email-sequence": {"handoff": {"emails": ["launch-now"]}},
    "campaign-video-script": {"handoff": {"beats": ["problem", "solution", "cta"]}},
    "live-campaign-ads": {"handoff": {"variants": ["urgency", "proof"]}},
    "press-release-copy": {"handoff": {"headline": "Prototype Brand launches"}},
}


def test_build_source_documents_emits_kickstarter_docs(tmp_path: Path) -> None:
    outputs_dir = tmp_path / ".brandmint" / "outputs"
    outputs_dir.mkdir(parents=True)
    for skill_id, payload in SAMPLE_OUTPUTS.items():
        (outputs_dir / f"{skill_id}.json").write_text(json.dumps(payload))

    config_path = tmp_path / "brand-config.yaml"
    config_path.write_text(yaml.safe_dump(SAMPLE_CONFIG, sort_keys=False))

    output_dir = tmp_path / "deliverables" / "notebooklm" / "sources"
    result = build_source_documents(
        outputs_dir=outputs_dir,
        config=SAMPLE_CONFIG,
        config_path=config_path,
        brand_dir=tmp_path,
        output_dir=output_dir,
        synthesize=False,
    )

    assert (output_dir / "kickstarter-market-understanding.md").exists()
    assert (output_dir / "kickstarter-product-detailing.md").exists()
    assert (output_dir / "artifact-market-buyer-persona.md").exists()
    assert (output_dir / "artifact-press-release-copy.md").exists()
    assert (output_dir / "kickstarter-readiness.md").exists()

    readiness_text = (output_dir / "kickstarter-readiness.md").read_text()
    assert "Kickstarter Prototype Readiness" in readiness_text
    assert "Part 1 — Understanding the Market" in readiness_text

    section_text = (output_dir / "kickstarter-market-understanding.md").read_text()
    assert "Market Buyer Persona" in section_text
    assert "Competitor Summary" in section_text

    assert "kickstarter-readiness" in result
    assert "artifact-market-buyer-persona" in result



def test_build_source_documents_respects_document_mode_and_cleans_stale_docs(tmp_path: Path) -> None:
    outputs_dir = tmp_path / ".brandmint" / "outputs"
    outputs_dir.mkdir(parents=True)
    for skill_id, payload in SAMPLE_OUTPUTS.items():
        (outputs_dir / f"{skill_id}.json").write_text(json.dumps(payload))

    config_path = tmp_path / "brand-config.yaml"
    config_path.write_text(yaml.safe_dump(SAMPLE_CONFIG, sort_keys=False))
    output_dir = tmp_path / "deliverables" / "notebooklm" / "sources"

    build_source_documents(
        outputs_dir=outputs_dir,
        config=SAMPLE_CONFIG,
        config_path=config_path,
        brand_dir=tmp_path,
        output_dir=output_dir,
        synthesize=False,
    )
    assert (output_dir / "brand-foundation.md").exists()
    assert (output_dir / "kickstarter-market-understanding.md").exists()

    kickstarter_only = {
        **SAMPLE_CONFIG,
        "publishing": {
            "notebooklm": {
                "source_document_mode": "kickstarter-only",
            }
        },
    }
    build_source_documents(
        outputs_dir=outputs_dir,
        config=kickstarter_only,
        config_path=config_path,
        brand_dir=tmp_path,
        output_dir=output_dir,
        synthesize=False,
    )

    assert not (output_dir / "brand-foundation.md").exists()
    assert (output_dir / "kickstarter-market-understanding.md").exists()
    assert (output_dir / "kickstarter-readiness.md").exists()

    legacy_only = {
        **SAMPLE_CONFIG,
        "publishing": {
            "notebooklm": {
                "source_document_mode": "legacy-only",
            }
        },
    }
    result = build_source_documents(
        outputs_dir=outputs_dir,
        config=legacy_only,
        config_path=config_path,
        brand_dir=tmp_path,
        output_dir=output_dir,
        synthesize=False,
    )

    assert (output_dir / "brand-foundation.md").exists()
    assert not (output_dir / "kickstarter-market-understanding.md").exists()
    assert not (output_dir / "kickstarter-readiness.md").exists()
    assert "brand-foundation" in result
    assert "kickstarter-readiness" not in result
