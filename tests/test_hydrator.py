"""
Tests for brandmint.core.hydrator -- Auto-hydration bridge.

Tests the mapping of text skill JSON outputs into brand-config.yaml fields.
RED phase: these tests define the contract before implementation.
"""

from __future__ import annotations

import copy
import os
import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest
import yaml

from brandmint.core.hydrator import (
    HYDRATION_MAP,
    _get_nested,
    _set_nested,
    get_hydration_status,
    hydrate_brand_config,
    save_hydrated_config,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def empty_config() -> dict:
    """Brand config with empty placeholder fields."""
    return {
        "brand": {"name": "Test Brand", "voice": "", "tone": ""},
        "theme": {"palette": {}},
        "audience": {"persona_name": "", "aspiration": "", "pain_points": []},
        "positioning": {
            "statement": "",
            "pillars": [],
            "hero_headline": "",
            "tagline": "",
        },
        "competitive_context": {"differentiate_from": []},
    }


@pytest.fixture
def buyer_persona_output() -> dict:
    """Sample buyer-persona skill output."""
    return {
        "persona": {
            "name": "The Adventurous Explorer",
            "aspirations": ["authentic local experiences", "cultural immersion"],
            "pain_points": ["language barriers", "tourist traps"],
        }
    }


@pytest.fixture
def product_positioning_output() -> dict:
    """Sample product-positioning-summary skill output."""
    return {
        "positioning_statement": "For adventurous travelers who seek authentic experiences",
        "key_pillars": ["Authenticity", "Local Connection", "Confidence"],
    }


@pytest.fixture
def mds_output() -> dict:
    """Sample mds-messaging-direction-summary skill output."""
    return {
        "hero_headline": "Travel Like a Local",
        "tagline": "Your Confident Local Friend",
    }


@pytest.fixture
def voice_tone_output() -> dict:
    """Sample voice-and-tone skill output."""
    return {
        "voice_persona": "The Confident Local Friend",
        "tone_calibration": "warm, knowledgeable, encouraging",
    }


@pytest.fixture
def competitor_output() -> dict:
    """Sample competitor-analysis skill output."""
    return {
        "key_differentiators": [
            "local curator network",
            "AI-powered itinerary personalization",
        ]
    }


@pytest.fixture
def all_skill_outputs(
    buyer_persona_output,
    product_positioning_output,
    mds_output,
    voice_tone_output,
    competitor_output,
) -> Dict[str, dict]:
    """All Wave 2 skill outputs combined."""
    return {
        "buyer-persona": buyer_persona_output,
        "product-positioning-summary": product_positioning_output,
        "mds-messaging-direction-summary": mds_output,
        "voice-and-tone": voice_tone_output,
        "competitor-analysis": competitor_output,
    }


# ---------------------------------------------------------------------------
# _get_nested tests
# ---------------------------------------------------------------------------

class TestGetNested:
    """Tests for dot-path traversal of nested dicts."""

    def test_single_level(self):
        assert _get_nested({"a": 1}, "a") == 1

    def test_two_levels(self):
        assert _get_nested({"a": {"b": 2}}, "a.b") == 2

    def test_three_levels(self):
        assert _get_nested({"a": {"b": {"c": 3}}}, "a.b.c") == 3

    def test_missing_key_returns_none(self):
        assert _get_nested({"a": 1}, "b") is None

    def test_missing_nested_key_returns_none(self):
        assert _get_nested({"a": {"b": 1}}, "a.c") is None

    def test_deep_missing_returns_none(self):
        assert _get_nested({"a": 1}, "a.b.c") is None

    def test_empty_dict_returns_none(self):
        assert _get_nested({}, "a.b") is None

    def test_returns_list_values(self):
        data = {"items": {"list": [1, 2, 3]}}
        assert _get_nested(data, "items.list") == [1, 2, 3]

    def test_returns_dict_values(self):
        inner = {"x": 1, "y": 2}
        assert _get_nested({"outer": inner}, "outer") == inner


# ---------------------------------------------------------------------------
# _set_nested tests
# ---------------------------------------------------------------------------

class TestSetNested:
    """Tests for dot-path setting of nested dicts."""

    def test_single_level(self):
        d: dict = {}
        _set_nested(d, "a", 1)
        assert d == {"a": 1}

    def test_two_levels(self):
        d: dict = {}
        _set_nested(d, "a.b", 2)
        assert d == {"a": {"b": 2}}

    def test_three_levels(self):
        d: dict = {}
        _set_nested(d, "a.b.c", 3)
        assert d == {"a": {"b": {"c": 3}}}

    def test_overwrites_existing(self):
        d = {"a": {"b": "old"}}
        _set_nested(d, "a.b", "new")
        assert d["a"]["b"] == "new"

    def test_creates_intermediate_dicts(self):
        d = {"a": {}}
        _set_nested(d, "a.b.c", "deep")
        assert d == {"a": {"b": {"c": "deep"}}}

    def test_preserves_sibling_keys(self):
        d = {"a": {"x": 1}}
        _set_nested(d, "a.y", 2)
        assert d == {"a": {"x": 1, "y": 2}}

    def test_sets_list_value(self):
        d: dict = {}
        _set_nested(d, "items", [1, 2, 3])
        assert d == {"items": [1, 2, 3]}


# ---------------------------------------------------------------------------
# hydrate_brand_config tests
# ---------------------------------------------------------------------------

class TestHydrateBrandConfig:
    """Tests for the main hydration function."""

    def test_hydrates_buyer_persona(self, empty_config, buyer_persona_output):
        outputs = {"buyer-persona": buyer_persona_output}
        result = hydrate_brand_config(empty_config, outputs)

        assert result["audience"]["persona_name"] == "The Adventurous Explorer"
        assert result["audience"]["aspiration"] == [
            "authentic local experiences",
            "cultural immersion",
        ]
        assert result["audience"]["pain_points"] == [
            "language barriers",
            "tourist traps",
        ]

    def test_hydrates_product_positioning(self, empty_config, product_positioning_output):
        outputs = {"product-positioning-summary": product_positioning_output}
        result = hydrate_brand_config(empty_config, outputs)

        assert result["positioning"]["statement"] == (
            "For adventurous travelers who seek authentic experiences"
        )
        assert result["positioning"]["pillars"] == [
            "Authenticity",
            "Local Connection",
            "Confidence",
        ]

    def test_hydrates_mds(self, empty_config, mds_output):
        outputs = {"mds-messaging-direction-summary": mds_output}
        result = hydrate_brand_config(empty_config, outputs)

        assert result["positioning"]["hero_headline"] == "Travel Like a Local"
        assert result["positioning"]["tagline"] == "Your Confident Local Friend"

    def test_hydrates_voice_and_tone(self, empty_config, voice_tone_output):
        outputs = {"voice-and-tone": voice_tone_output}
        result = hydrate_brand_config(empty_config, outputs)

        assert result["brand"]["voice"] == "The Confident Local Friend"
        assert result["brand"]["tone"] == "warm, knowledgeable, encouraging"

    def test_hydrates_competitor_analysis(self, empty_config, competitor_output):
        outputs = {"competitor-analysis": competitor_output}
        result = hydrate_brand_config(empty_config, outputs)

        assert result["competitive_context"]["differentiate_from"] == [
            "local curator network",
            "AI-powered itinerary personalization",
        ]

    def test_hydrates_all_skills(self, empty_config, all_skill_outputs):
        result = hydrate_brand_config(empty_config, all_skill_outputs)

        # Spot-check several fields
        assert result["brand"]["voice"] == "The Confident Local Friend"
        assert result["audience"]["persona_name"] == "The Adventurous Explorer"
        assert result["positioning"]["hero_headline"] == "Travel Like a Local"
        assert len(result["positioning"]["pillars"]) == 3

    def test_modifies_in_place(self, empty_config, voice_tone_output):
        outputs = {"voice-and-tone": voice_tone_output}
        result = hydrate_brand_config(empty_config, outputs)
        assert result is empty_config  # Same reference

    def test_returns_config(self, empty_config, voice_tone_output):
        outputs = {"voice-and-tone": voice_tone_output}
        result = hydrate_brand_config(empty_config, outputs)
        assert isinstance(result, dict)

    def test_skips_unknown_skills(self, empty_config):
        outputs = {"unknown-skill": {"some": "data"}}
        original = copy.deepcopy(empty_config)
        result = hydrate_brand_config(empty_config, outputs)
        assert result == original

    def test_skips_missing_output_fields(self, empty_config):
        # buyer-persona output missing 'persona' key
        outputs = {"buyer-persona": {"wrong_key": "value"}}
        result = hydrate_brand_config(empty_config, outputs)
        # Should not crash; persona_name stays empty
        assert result["audience"]["persona_name"] == ""

    def test_empty_outputs(self, empty_config):
        original = copy.deepcopy(empty_config)
        result = hydrate_brand_config(empty_config, {})
        assert result == original

    def test_preserves_existing_fields(self, empty_config, voice_tone_output):
        empty_config["brand"]["name"] = "My Brand"
        empty_config["theme"]["palette"] = {"primary": "#FF0000"}
        outputs = {"voice-and-tone": voice_tone_output}
        result = hydrate_brand_config(empty_config, outputs)

        assert result["brand"]["name"] == "My Brand"
        assert result["theme"]["palette"]["primary"] == "#FF0000"

    def test_creates_missing_intermediate_keys(self, voice_tone_output):
        # Config without the 'brand' key at all
        config: dict = {}
        outputs = {"voice-and-tone": voice_tone_output}
        result = hydrate_brand_config(config, outputs)
        assert result["brand"]["voice"] == "The Confident Local Friend"


# ---------------------------------------------------------------------------
# save_hydrated_config tests
# ---------------------------------------------------------------------------

class TestSaveHydratedConfig:
    """Tests for saving hydrated config to YAML."""

    def test_writes_yaml_file(self, empty_config):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "brand-config.yaml"
            # Write initial file so save can back it up
            path.write_text(yaml.dump(empty_config))

            empty_config["brand"]["voice"] = "Test Voice"
            save_hydrated_config(empty_config, path)

            loaded = yaml.safe_load(path.read_text())
            assert loaded["brand"]["voice"] == "Test Voice"

    def test_creates_backup(self, empty_config):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "brand-config.yaml"
            path.write_text(yaml.dump({"brand": {"voice": "original"}}))

            save_hydrated_config(empty_config, path)

            bak_path = path.with_suffix(".yaml.bak")
            assert bak_path.exists()
            backup = yaml.safe_load(bak_path.read_text())
            assert backup["brand"]["voice"] == "original"

    def test_yaml_formatting(self, empty_config):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "brand-config.yaml"
            path.write_text(yaml.dump(empty_config))

            save_hydrated_config(empty_config, path)
            content = path.read_text()

            # default_flow_style=False produces block style, not inline braces
            assert "{" not in content or content.strip().startswith("{") is False

    def test_handles_new_file(self, empty_config):
        """save_hydrated_config should work even if no prior file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "brand-config.yaml"
            # No file exists yet -- should not crash
            save_hydrated_config(empty_config, path)
            assert path.exists()


# ---------------------------------------------------------------------------
# get_hydration_status tests
# ---------------------------------------------------------------------------

class TestGetHydrationStatus:
    """Tests for checking which skills have output available."""

    def test_all_available(self, all_skill_outputs):
        status = get_hydration_status(all_skill_outputs)
        for skill_id in HYDRATION_MAP:
            assert status[skill_id] is True

    def test_none_available(self):
        status = get_hydration_status({})
        for skill_id in HYDRATION_MAP:
            assert status[skill_id] is False

    def test_partial_availability(self, voice_tone_output):
        status = get_hydration_status({"voice-and-tone": voice_tone_output})
        assert status["voice-and-tone"] is True
        assert status["buyer-persona"] is False

    def test_returns_all_mapped_skills(self):
        status = get_hydration_status({})
        assert set(status.keys()) == set(HYDRATION_MAP.keys())


# ---------------------------------------------------------------------------
# HYDRATION_MAP integrity tests
# ---------------------------------------------------------------------------

class TestHydrationMap:
    """Structural tests for the mapping constant."""

    def test_all_skill_ids_are_strings(self):
        for skill_id in HYDRATION_MAP:
            assert isinstance(skill_id, str)

    def test_all_paths_are_dot_notation(self):
        for skill_id, mappings in HYDRATION_MAP.items():
            for config_path, output_path in mappings.items():
                assert isinstance(config_path, str)
                assert isinstance(output_path, str)
                # Paths should be alphanumeric with dots and underscores
                for part in config_path.split("."):
                    assert part.replace("_", "").replace("-", "").isalnum(), (
                        f"Bad config path segment '{part}' in {config_path}"
                    )

    def test_expected_skills_present(self):
        expected = {
            "buyer-persona",
            "product-positioning-summary",
            "mds-messaging-direction-summary",
            "voice-and-tone",
            "competitor-analysis",
        }
        assert expected == set(HYDRATION_MAP.keys())
