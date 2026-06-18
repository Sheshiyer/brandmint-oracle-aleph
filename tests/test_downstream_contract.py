from __future__ import annotations

from brandmint.core.downstream_contract import build_downstream_variable_contract


def sample_brand_config() -> dict:
    return {
        "brand": {
            "name": "Cambium",
            "archetype": "company-compiler",
            "voice": "direct, vivid, precise",
            "tone": "warm operational clarity",
        },
        "audience": {"persona_name": "founder-operator"},
        "positioning": {
            "statement": "Turn a thoughtseed into a running company.",
            "hero_headline": "Compile the company",
            "tagline": "Idea in. Venture out.",
            "pillars": ["composition", "taste", "memory"],
        },
        "palette": {
            "primary": {"name": "Cambium Green", "hex": "#3C7A4B"},
            "accent": {"name": "Signal Gold", "hex": "#E0B84C"},
        },
        "typography": {"header": {"font": "Figtree"}, "body": {"font": "Inter"}},
        "aesthetic": {
            "hero_object_type": "living tree-ring map",
            "hero_surface": "tactile woven substrate",
            "logo_treatment": "embossed seal",
        },
        "products": {"hero": {"name": "Cambium operator", "description": "Self-running venture OS"}},
    }


def test_brandmint_outputs_downstream_seed_variables() -> None:
    result = build_downstream_variable_contract(sample_brand_config())

    assert result["brand_system"]["brand_archetype"] == "company-compiler"
    assert result["brand_system"]["positioning"] == "Turn a thoughtseed into a running company."
    assert "copy_system" in result
    assert result["copy_system"]["hero_headline"] == "Compile the company"
    assert "visual_primitives" in result
    assert result["visual_primitives"]["hero_object_type"] == "living tree-ring map"
    assert "asset_requirements" in result
    assert "logo" in result["asset_requirements"]["required"]
    assert "hero_media" in result["asset_requirements"]["required"]
    assert result["section_defaults"]["ordered_sections"] == ["hero", "problem", "solution", "proof", "pricing", "cta"]


def test_downstream_seed_pack_includes_cambium_aliases() -> None:
    result = build_downstream_variable_contract(sample_brand_config())

    assert result["visual_system"] == result["visual_primitives"]
    assert result["asset_plan"] == result["asset_requirements"]
    assert result["section_plan"] == result["section_defaults"]["ordered_sections"]


def test_wave_plan_visual_assets_feed_asset_requirements() -> None:
    result = build_downstream_variable_contract(
        sample_brand_config(),
        wave_plan=[{"visual_assets": ["2A", "3B", "APP-SCREENSHOT"]}],
    )

    assert "2A" in result["asset_requirements"]["required"]
    assert "3B" in result["asset_requirements"]["required"]
    assert "APP-SCREENSHOT" in result["asset_requirements"]["required"]
