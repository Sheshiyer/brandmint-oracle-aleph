import json
import os
from pathlib import Path

import yaml

from brandmint.publishing.source_builder import build_source_documents
from brandmint.publishing.source_curator import SourceCurator


SAMPLE_CONFIG = {
    "brand": {"name": "Prototype Brand"},
}


SAMPLE_OUTPUTS = {
    "buyer-persona": {"persona": {"name": "Asha"}},
    "competitor-analysis": {"handoff": {"key_differentiators": ["clear"]}},
    "detailed-product-description": {"hero_product": {"name": "Prototype Pack"}},
    "product-positioning-summary": {"positioning_statement": "Own your flow"},
    "mds-messaging-direction-summary": {"hero_headline": "Own your flow"},
    "voice-and-tone": {"voice_persona": {"identity": "Calm guide"}},
    "campaign-page-copy": {"handoff": {"headline": "Back us"}},
    "pre-launch-ads": {"handoff": {"hooks": ["Be first"]}},
    "welcome-email-sequence": {"handoff": {"emails": ["welcome-1"]}},
    "pre-launch-email-sequence": {"handoff": {"emails": ["tease-1"]}},
    "launch-email-sequence": {"handoff": {"emails": ["launch-1"]}},
    "campaign-video-script": {"handoff": {"beats": ["problem"]}},
    "live-campaign-ads": {"handoff": {"variants": ["urgency"]}},
    "press-release-copy": {"handoff": {"headline": "Prototype launches"}},
}


def test_curator_recognizes_kickstarter_sources(tmp_path: Path) -> None:
    outputs_dir = tmp_path / ".brandmint" / "outputs"
    outputs_dir.mkdir(parents=True)
    for skill_id, payload in SAMPLE_OUTPUTS.items():
        (outputs_dir / f"{skill_id}.json").write_text(json.dumps(payload))

    config_path = tmp_path / "brand-config.yaml"
    config_path.write_text(yaml.safe_dump(SAMPLE_CONFIG, sort_keys=False))

    sources_dir = tmp_path / "deliverables" / "notebooklm" / "sources"
    build_source_documents(
        outputs_dir=outputs_dir,
        config=SAMPLE_CONFIG,
        config_path=config_path,
        brand_dir=tmp_path,
        output_dir=sources_dir,
        synthesize=False,
    )

    curator = SourceCurator(
        brand_dir=tmp_path,
        config=SAMPLE_CONFIG,
        max_sources=50,
        sources_dir=sources_dir,
    )
    selected = curator.curate()

    names = {candidate.path.name for candidate in selected}
    assert "kickstarter-market-understanding.md" in names
    assert "kickstarter-product-detailing.md" in names
    assert "artifact-market-buyer-persona.md" in names
    assert "kickstarter-readiness.md" in names

    kickstarter_candidates = [c for c in selected if "kickstarter" in c.path.stem or "artifact-" in c.path.stem]
    assert len(kickstarter_candidates) >= 10



def test_curator_prioritizes_section_docs_under_tight_budget(tmp_path: Path) -> None:
    outputs_dir = tmp_path / ".brandmint" / "outputs"
    outputs_dir.mkdir(parents=True)
    for skill_id, payload in SAMPLE_OUTPUTS.items():
        (outputs_dir / f"{skill_id}.json").write_text(json.dumps(payload))

    config = {
        **SAMPLE_CONFIG,
        "execution_context": {"launch_channel": "kickstarter"},
    }
    config_path = tmp_path / "brand-config.yaml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False))

    sources_dir = tmp_path / "deliverables" / "notebooklm" / "sources"
    build_source_documents(
        outputs_dir=outputs_dir,
        config=config,
        config_path=config_path,
        brand_dir=tmp_path,
        output_dir=sources_dir,
        synthesize=False,
    )

    curator = SourceCurator(
        brand_dir=tmp_path,
        config=config,
        max_sources=8,
        sources_dir=sources_dir,
    )
    selected = curator.curate()

    names = {candidate.path.name for candidate in selected}
    assert names == {
        "brand-config-source.md",
        "kickstarter-market-understanding.md",
        "kickstarter-product-detailing.md",
        "kickstarter-crafting-compelling-copy.md",
        "kickstarter-email-strategy.md",
        "kickstarter-campaign-messaging.md",
        "kickstarter-driving-continual-interest.md",
        "kickstarter-readiness.md",
    }



def test_curator_limits_images_to_manifest_assets_and_prefers_newest_variant(tmp_path: Path) -> None:
    brand_name = "Prototype Brand"
    slug = "prototype-brand"
    generated_dir = tmp_path / slug / "generated"
    generated_dir.mkdir(parents=True)

    current = generated_dir / "3A-capsule-collection-nanobananapro-v2.png"
    old_variant = generated_dir / "3A-capsule-collection-nanobananapro-v1.png"
    stale_other = generated_dir / "5A-heritage-engraving-recraft-v1.png"
    for path in [current, old_variant, stale_other]:
        path.write_bytes(b"png")

    os.utime(old_variant, (1_700_000_000, 1_700_000_000))
    os.utime(current, (1_800_000_000, 1_800_000_000))
    os.utime(stale_other, (1_900_000_000, 1_900_000_000))

    (generated_dir / "generation-manifest.json").write_text(json.dumps({
        "assets": [{"id": "3A", "name": "Capsule Collection"}]
    }))

    curator = SourceCurator(
        brand_dir=tmp_path,
        config={"brand": {"name": brand_name}, "publishing": {"notebooklm": {"image_source_policy": "manifest-only"}}},
        max_sources=50,
        sources_dir=tmp_path / "deliverables" / "notebooklm" / "sources",
    )

    images = curator._scan_images()

    assert {candidate.asset_id for candidate in images} == {"3A"}
    assert images[0].path.name == "3A-capsule-collection-nanobananapro-v2.png"
    assert images[0].uniqueness == 100.0
    assert all(candidate.path.name != "5A-heritage-engraving-recraft-v1.png" for candidate in images)



def test_curator_can_use_product_reference_images_only(tmp_path: Path) -> None:
    products_dir = tmp_path / "products"
    products_dir.mkdir(parents=True)
    (products_dir / "phantom-purple.png").write_bytes(b"png")
    (products_dir / "storm-grey.png").write_bytes(b"png")

    config = {
        "brand": {"name": "Prototype Brand"},
        "generation": {
            "product_reference_images": [
                "products/phantom-purple.png",
                "products/storm-grey.png",
            ]
        },
        "publishing": {"notebooklm": {"image_source_policy": "product-reference-only"}},
    }
    (tmp_path / "brand-config.yaml").write_text(yaml.safe_dump(config, sort_keys=False))

    curator = SourceCurator(
        brand_dir=tmp_path,
        config=config,
        max_sources=50,
        sources_dir=tmp_path / "deliverables" / "notebooklm" / "sources",
    )

    images = curator._scan_images()

    assert [candidate.path.name for candidate in images] == ["phantom-purple.png", "storm-grey.png"]
    assert all(candidate.asset_id.startswith("PRODUCT-REF-") for candidate in images)
