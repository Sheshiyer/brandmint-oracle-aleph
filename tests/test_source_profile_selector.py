"""Tests for source profile selector and gating."""
from __future__ import annotations

import pytest

from brandmint.publishing.source_builder import (
    SOURCE_PROFILES,
    DEFAULT_SOURCE_PROFILE,
    resolve_source_profile,
    get_profile_config,
    filter_groups_by_profile,
    get_source_group_definitions,
)


class TestResolveSourceProfile:
    """Test profile resolution from config."""

    def test_default_profile_when_not_set(self):
        config = {}
        assert resolve_source_profile(config) == DEFAULT_SOURCE_PROFILE

    def test_default_profile_when_empty(self):
        config = {"publishing": {"notebooklm": {"source_profile": ""}}}
        assert resolve_source_profile(config) == DEFAULT_SOURCE_PROFILE

    def test_valid_profile_from_config(self):
        config = {"publishing": {"notebooklm": {"source_profile": "strategy-internal"}}}
        assert resolve_source_profile(config) == "strategy-internal"

    def test_invalid_profile_falls_back_to_default(self):
        config = {"publishing": {"notebooklm": {"source_profile": "nonexistent"}}}
        assert resolve_source_profile(config) == DEFAULT_SOURCE_PROFILE

    def test_legacy_config_ignored(self):
        config = {"notebooklm": {"source_profile": "debug-internal"}}
        assert resolve_source_profile(config) == DEFAULT_SOURCE_PROFILE

    def test_case_insensitive_profile(self):
        config = {"publishing": {"notebooklm": {"source_profile": "Brand-Public"}}}
        assert resolve_source_profile(config) == "brand-public"


class TestGetProfileConfig:
    """Test profile configuration retrieval."""

    def test_brand_public_config(self):
        cfg = get_profile_config("brand-public")
        assert cfg["min_quality_score"] == 85
        assert cfg["allow_placeholders"] is False
        assert cfg["allow_meta_content"] is False

    def test_strategy_internal_config(self):
        cfg = get_profile_config("strategy-internal")
        assert cfg["min_quality_score"] == 75
        assert cfg["allow_placeholders"] is True
        assert cfg["allow_meta_content"] is True

    def test_kickstarter_conditional_config(self):
        cfg = get_profile_config("kickstarter-conditional")
        assert cfg["min_quality_score"] == 80
        assert cfg["require_kickstarter_complete"] is True

    def test_debug_internal_config(self):
        cfg = get_profile_config("debug-internal")
        assert cfg["min_quality_score"] == 0
        assert cfg["allow_placeholders"] is True

    def test_unknown_profile_returns_default(self):
        cfg = get_profile_config("unknown")
        default_cfg = get_profile_config(DEFAULT_SOURCE_PROFILE)
        assert cfg == default_cfg


class TestFilterGroupsByProfile:
    """Test group filtering based on profiles."""

    def test_brand_public_includes_all_core_groups(self):
        groups = get_source_group_definitions("hybrid")
        filtered = filter_groups_by_profile(groups, "brand-public")
        # Should include all core groups
        assert "brand-foundation" in filtered
        assert "brand-strategy" in filtered
        assert "campaign-content" in filtered
        assert "communications-social" in filtered
        assert "visual-asset-catalog" in filtered

    def test_strategy_internal_excludes_campaign_and_social(self):
        groups = get_source_group_definitions("hybrid")
        filtered = filter_groups_by_profile(groups, "strategy-internal")
        # Should include foundation and strategy
        assert "brand-foundation" in filtered
        assert "brand-strategy" in filtered
        # Should exclude campaign and social
        assert "campaign-content" not in filtered
        assert "communications-social" not in filtered

    def test_debug_internal_includes_all_groups(self):
        groups = get_source_group_definitions("hybrid")
        filtered = filter_groups_by_profile(groups, "debug-internal")
        # Should include all groups
        assert len(filtered) == len(groups)

    def test_empty_profile_returns_all_groups(self):
        groups = get_source_group_definitions("hybrid")
        filtered = filter_groups_by_profile(groups, "")
        assert filtered == groups

    def test_unknown_profile_returns_all_groups(self):
        groups = get_source_group_definitions("hybrid")
        filtered = filter_groups_by_profile(groups, "nonexistent")
        assert filtered == groups


class TestSourceGroupDefinitionsWithProfile:
    """Test source group definitions with profile filtering."""

    def test_hybrid_mode_with_brand_public_profile(self):
        groups = get_source_group_definitions("hybrid", "brand-public")
        # Should have core groups filtered by brand-public
        assert "brand-foundation" in groups
        assert "brand-strategy" in groups

    def test_hybrid_mode_with_strategy_internal_profile(self):
        groups = get_source_group_definitions("hybrid", "strategy-internal")
        # Should have filtered groups
        assert "brand-foundation" in groups
        assert "brand-strategy" in groups
        assert "campaign-content" not in groups
        assert "communications-social" not in groups

    def test_legacy_only_mode_with_profile(self):
        groups = get_source_group_definitions("legacy-only", "brand-public")
        # Should have core groups only (no kickstarter)
        assert "brand-foundation" in groups
        assert "kickstarter-readiness" not in groups

    def test_kickstarter_only_mode_with_profile(self):
        groups = get_source_group_definitions("kickstarter-only", "brand-public")
        # Should have kickstarter groups
        assert "kickstarter-readiness" in groups
        # Core groups should NOT be in kickstarter-only mode
        assert "brand-foundation" not in groups

    def test_empty_profile_returns_unfiltered_groups(self):
        groups_unfiltered = get_source_group_definitions("hybrid", "")
        groups_all = get_source_group_definitions("hybrid")
        assert groups_unfiltered == groups_all


class TestProfileDeterminism:
    """Test that profile filtering produces deterministic results."""

    def test_same_profile_same_result(self):
        groups1 = get_source_group_definitions("hybrid", "strategy-internal")
        groups2 = get_source_group_definitions("hybrid", "strategy-internal")
        assert groups1 == groups2

    def test_profile_filtering_is_idempotent(self):
        groups = get_source_group_definitions("hybrid")
        filtered1 = filter_groups_by_profile(groups, "strategy-internal")
        filtered2 = filter_groups_by_profile(filtered1, "strategy-internal")
        assert filtered1 == filtered2

    def test_all_profiles_produce_valid_groups(self):
        for profile_name in SOURCE_PROFILES:
            groups = get_source_group_definitions("hybrid", profile_name)
            assert isinstance(groups, dict)
            assert len(groups) > 0
            for group_id, group_def in groups.items():
                assert "title" in group_def
                assert "description" in group_def
                assert "skills" in group_def
