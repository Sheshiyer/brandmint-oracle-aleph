"""Tests for brandmint.core.asset_mode — AF-12: Provider routing."""

import pytest

from brandmint.core.asset_mode import (
    AssetMode,
    AssetType,
    RouteDecision,
    _classify_asset,
    route_asset,
)


class TestClassifyAsset:
    def test_2a_is_bento(self):
        assert _classify_asset("2A-bento-grid") == AssetType.BENTO_GRID

    def test_2b_is_logo_lockup(self):
        assert _classify_asset("2B-logo-lockup") == AssetType.LOGO_LOCKUP

    def test_3a_is_product_hero(self):
        assert _classify_asset("3A-product-hero") == AssetType.PRODUCT_HERO

    def test_4a_is_lifestyle(self):
        assert _classify_asset("4A-lifestyle") == AssetType.LIFESTYLE

    def test_5a_is_packaging(self):
        assert _classify_asset("5A-packaging") == AssetType.PACKAGING

    def test_social_detected(self):
        assert _classify_asset("ig-story-template") == AssetType.SOCIAL
        assert _classify_asset("twitter-header") == AssetType.SOCIAL

    def test_app_detected(self):
        assert _classify_asset("app-icon") == AssetType.APP

    def test_unknown_is_other(self):
        assert _classify_asset("random-asset") == AssetType.OTHER


class TestRouteAssetGenerate:
    def test_default_is_generate(self):
        decision = route_asset("2B-logo-lockup")
        assert decision.mode == AssetMode.GENERATE

    def test_explicit_generate(self):
        decision = route_asset("3A-product-hero", global_mode=AssetMode.GENERATE)
        assert decision.mode == AssetMode.GENERATE
        assert not decision.use_logo_composite
        assert not decision.use_product_composite


class TestRouteAssetComposite:
    def test_composite_with_logo(self):
        decision = route_asset(
            "2B-logo-lockup",
            global_mode=AssetMode.COMPOSITE,
            has_logo=True,
        )
        assert decision.mode == AssetMode.COMPOSITE
        assert decision.use_logo_composite is True
        assert decision.needs_composite_pass is True

    def test_composite_without_logo(self):
        decision = route_asset(
            "2B-logo-lockup",
            global_mode=AssetMode.COMPOSITE,
            has_logo=False,
        )
        assert decision.use_logo_composite is False

    def test_composite_product_hero(self):
        decision = route_asset(
            "3A-product-hero",
            global_mode=AssetMode.COMPOSITE,
            has_logo=True,
            has_product_images=True,
        )
        assert decision.use_logo_composite is True
        assert decision.use_product_composite is True

    def test_composite_lifestyle_no_product(self):
        decision = route_asset(
            "4A-lifestyle",
            global_mode=AssetMode.COMPOSITE,
            has_logo=True,
            has_product_images=False,
        )
        assert decision.use_logo_composite is True
        assert decision.use_product_composite is False


class TestRouteAssetInpaint:
    def test_inpaint_with_provider_support(self):
        decision = route_asset(
            "3A-product-hero",
            global_mode=AssetMode.INPAINT,
            has_logo=True,
            provider_supports_inpaint=True,
        )
        assert decision.mode == AssetMode.INPAINT
        assert decision.inpaint_model == "flux-fill"

    def test_inpaint_fallback_to_composite(self):
        """When provider doesn't support inpaint, falls back to composite."""
        decision = route_asset(
            "3A-product-hero",
            global_mode=AssetMode.INPAINT,
            has_logo=True,
            provider_supports_inpaint=False,
        )
        assert decision.mode == AssetMode.COMPOSITE
        assert decision.fallback_mode == AssetMode.INPAINT


class TestRouteAssetHybrid:
    def test_hybrid_with_inpaint(self):
        decision = route_asset(
            "2B-logo-lockup",
            global_mode=AssetMode.HYBRID,
            has_logo=True,
            provider_supports_inpaint=True,
        )
        assert decision.mode == AssetMode.HYBRID
        assert decision.needs_composite_pass is True
        assert decision.needs_inpaint is True
        assert decision.inpaint_model == "flux-fill"

    def test_hybrid_without_inpaint(self):
        decision = route_asset(
            "2B-logo-lockup",
            global_mode=AssetMode.HYBRID,
            has_logo=True,
            provider_supports_inpaint=False,
        )
        assert decision.mode == AssetMode.HYBRID
        assert decision.inpaint_model == ""
        assert decision.fallback_mode == AssetMode.COMPOSITE


class TestStyleAnchorAlwaysGenerates:
    def test_bento_grid_always_generate(self):
        """2A style anchor must ALWAYS generate — it's the reference for everything else."""
        for mode in AssetMode:
            decision = route_asset(
                "2A-bento-grid",
                global_mode=mode,
                has_logo=True,
                provider_supports_inpaint=True,
            )
            assert decision.mode == AssetMode.GENERATE, f"2A should generate in {mode}"


class TestPerAssetOverride:
    def test_override_takes_priority(self):
        decision = route_asset(
            "3A-product-hero",
            global_mode=AssetMode.GENERATE,
            has_logo=True,
            per_asset_overrides={"3A-product-hero": AssetMode.COMPOSITE},
        )
        assert decision.mode == AssetMode.COMPOSITE

    def test_override_doesnt_affect_others(self):
        decision = route_asset(
            "4A-lifestyle",
            global_mode=AssetMode.GENERATE,
            per_asset_overrides={"3A-product-hero": AssetMode.COMPOSITE},
        )
        assert decision.mode == AssetMode.GENERATE


class TestRouteDecisionProperties:
    def test_generate_properties(self):
        d = RouteDecision(mode=AssetMode.GENERATE)
        assert d.needs_generation is True
        assert d.needs_composite_pass is False
        assert d.needs_inpaint is False

    def test_composite_properties(self):
        d = RouteDecision(mode=AssetMode.COMPOSITE)
        assert d.needs_generation is True
        assert d.needs_composite_pass is True
        assert d.needs_inpaint is False

    def test_inpaint_properties(self):
        d = RouteDecision(mode=AssetMode.INPAINT)
        assert d.needs_generation is False
        assert d.needs_composite_pass is False
        assert d.needs_inpaint is True

    def test_hybrid_properties(self):
        d = RouteDecision(mode=AssetMode.HYBRID)
        assert d.needs_generation is True
        assert d.needs_composite_pass is True
        assert d.needs_inpaint is True


class TestLogoPositionDefaults:
    def test_logo_lockup_center(self):
        decision = route_asset(
            "2B-logo-lockup",
            global_mode=AssetMode.COMPOSITE,
            has_logo=True,
        )
        assert decision.logo_position == "center"
        assert decision.logo_scale == 0.35

    def test_product_hero_bottom_right(self):
        decision = route_asset(
            "3A-product-hero",
            global_mode=AssetMode.COMPOSITE,
            has_logo=True,
        )
        assert decision.logo_position == "bottom-right"
        assert decision.logo_scale == 0.12
