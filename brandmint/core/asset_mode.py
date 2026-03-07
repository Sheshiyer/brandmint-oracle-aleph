"""
asset_mode.py — Provider routing based on asset generation mode.

Routes each visual asset to the appropriate pipeline:
- generate:  Pure AI generation (current default behavior)
- composite: AI generates scene → PIL composites real logo/product on top
- inpaint:   Mask logo zone → FAL flux-fill paints scene around real logo
- hybrid:    Generate scene → selective inpaint in logo zone → composite fallback

This is the decision layer between brand-config's `generation.asset_mode`
and the actual execution path in generate_pipeline.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class AssetMode(str, Enum):
    """How to produce each visual asset."""

    GENERATE = "generate"  # Pure AI generation (status quo)
    COMPOSITE = "composite"  # Generate scene → overlay real assets
    INPAINT = "inpaint"  # Mask-based inpainting with real assets
    HYBRID = "hybrid"  # Try inpaint → fallback to composite


class AssetType(str, Enum):
    """Broad categories of visual assets."""

    BENTO_GRID = "bento-grid"  # 2A — style anchor
    LOGO_LOCKUP = "logo-lockup"  # 2B
    PATTERN = "pattern"  # 2C
    PRODUCT_HERO = "product-hero"  # 3A, 3B
    LIFESTYLE = "lifestyle"  # 4A, 4B
    PACKAGING = "packaging"  # 5A
    CAMPAIGN = "campaign"  # Campaign assets
    SOCIAL = "social"  # Social media assets
    APP = "app"  # App icons, screenshots
    OTHER = "other"


@dataclass
class RouteDecision:
    """Result of routing — tells the pipeline what to do."""

    mode: AssetMode
    use_logo_composite: bool = False
    use_product_composite: bool = False
    logo_position: str = "bottom-right"
    logo_scale: float = 0.15
    product_position: str = "center"
    product_scale: float = 0.5
    inpaint_model: str = "flux-fill"
    fallback_mode: Optional[AssetMode] = None

    @property
    def needs_composite_pass(self) -> bool:
        return self.mode in (AssetMode.COMPOSITE, AssetMode.HYBRID)

    @property
    def needs_inpaint(self) -> bool:
        return self.mode in (AssetMode.INPAINT, AssetMode.HYBRID)

    @property
    def needs_generation(self) -> bool:
        return self.mode != AssetMode.INPAINT


def _classify_asset(asset_id: str) -> AssetType:
    """Map an asset ID to its broad category."""
    asset_id_lower = asset_id.lower().replace("_", "-")
    mapping = {
        "2a": AssetType.BENTO_GRID,
        "bento": AssetType.BENTO_GRID,
        "2b": AssetType.LOGO_LOCKUP,
        "logo-lockup": AssetType.LOGO_LOCKUP,
        "2c": AssetType.PATTERN,
        "pattern": AssetType.PATTERN,
        "3a": AssetType.PRODUCT_HERO,
        "3b": AssetType.PRODUCT_HERO,
        "product": AssetType.PRODUCT_HERO,
        "4a": AssetType.LIFESTYLE,
        "4b": AssetType.LIFESTYLE,
        "lifestyle": AssetType.LIFESTYLE,
        "5a": AssetType.PACKAGING,
        "packaging": AssetType.PACKAGING,
    }
    for key, asset_type in mapping.items():
        if key in asset_id_lower:
            return asset_type
    if "social" in asset_id_lower or "ig" in asset_id_lower or "twitter" in asset_id_lower:
        return AssetType.SOCIAL
    if "app" in asset_id_lower:
        return AssetType.APP
    return AssetType.OTHER


def route_asset(
    asset_id: str,
    global_mode: AssetMode = AssetMode.GENERATE,
    has_logo: bool = False,
    has_product_images: bool = False,
    provider_supports_inpaint: bool = False,
    provider_supports_edge_guided: bool = False,
    per_asset_overrides: Optional[dict[str, AssetMode]] = None,
) -> RouteDecision:
    """
    Determine how to generate a specific asset.

    Priority:
    1. Per-asset override (if configured)
    2. Smart routing based on asset type + available capabilities
    3. Global mode fallback
    """
    # 1. Check per-asset override
    if per_asset_overrides and asset_id in per_asset_overrides:
        override_mode = per_asset_overrides[asset_id]
        return _build_decision(
            asset_id, override_mode, has_logo, has_product_images,
            provider_supports_inpaint,
        )

    asset_type = _classify_asset(asset_id)

    # 2. Style anchor (2A) ALWAYS generates — it IS the reference
    if asset_type == AssetType.BENTO_GRID:
        return RouteDecision(mode=AssetMode.GENERATE)

    # 3. Smart routing per asset type
    if global_mode == AssetMode.GENERATE:
        return RouteDecision(mode=AssetMode.GENERATE)

    return _build_decision(
        asset_id, global_mode, has_logo, has_product_images,
        provider_supports_inpaint,
    )


def _build_decision(
    asset_id: str,
    mode: AssetMode,
    has_logo: bool,
    has_product_images: bool,
    provider_supports_inpaint: bool,
) -> RouteDecision:
    """Build a RouteDecision for a specific mode + asset combination."""
    asset_type = _classify_asset(asset_id)

    if mode == AssetMode.GENERATE:
        return RouteDecision(mode=AssetMode.GENERATE)

    if mode == AssetMode.COMPOSITE:
        return RouteDecision(
            mode=AssetMode.COMPOSITE,
            use_logo_composite=has_logo and asset_type in _LOGO_ASSETS,
            use_product_composite=has_product_images and asset_type in _PRODUCT_ASSETS,
            logo_position=_logo_position_for(asset_type),
            logo_scale=_logo_scale_for(asset_type),
            product_position=_product_position_for(asset_type),
            product_scale=_product_scale_for(asset_type),
        )

    if mode == AssetMode.INPAINT:
        if not provider_supports_inpaint:
            # Fallback to composite when provider can't inpaint
            return RouteDecision(
                mode=AssetMode.COMPOSITE,
                use_logo_composite=has_logo and asset_type in _LOGO_ASSETS,
                use_product_composite=has_product_images and asset_type in _PRODUCT_ASSETS,
                logo_position=_logo_position_for(asset_type),
                logo_scale=_logo_scale_for(asset_type),
                fallback_mode=AssetMode.INPAINT,
            )
        return RouteDecision(
            mode=AssetMode.INPAINT,
            use_logo_composite=has_logo and asset_type in _LOGO_ASSETS,
            inpaint_model="flux-fill",
        )

    if mode == AssetMode.HYBRID:
        return RouteDecision(
            mode=AssetMode.HYBRID,
            use_logo_composite=has_logo and asset_type in _LOGO_ASSETS,
            use_product_composite=has_product_images and asset_type in _PRODUCT_ASSETS,
            logo_position=_logo_position_for(asset_type),
            logo_scale=_logo_scale_for(asset_type),
            inpaint_model="flux-fill" if provider_supports_inpaint else "",
            fallback_mode=AssetMode.COMPOSITE,
        )

    return RouteDecision(mode=AssetMode.GENERATE)


# ---------------------------------------------------------------------------
# Asset type → compositing parameter mappings
# ---------------------------------------------------------------------------

_LOGO_ASSETS = frozenset({
    AssetType.LOGO_LOCKUP,
    AssetType.PRODUCT_HERO,
    AssetType.LIFESTYLE,
    AssetType.PACKAGING,
    AssetType.CAMPAIGN,
    AssetType.SOCIAL,
})

_PRODUCT_ASSETS = frozenset({
    AssetType.PRODUCT_HERO,
    AssetType.LIFESTYLE,
    AssetType.PACKAGING,
})


def _logo_position_for(asset_type: AssetType) -> str:
    """Default logo placement per asset type."""
    return {
        AssetType.LOGO_LOCKUP: "center",
        AssetType.PRODUCT_HERO: "bottom-right",
        AssetType.LIFESTYLE: "bottom-left",
        AssetType.PACKAGING: "top-center",
        AssetType.CAMPAIGN: "bottom-right",
        AssetType.SOCIAL: "bottom-right",
    }.get(asset_type, "bottom-right")


def _logo_scale_for(asset_type: AssetType) -> float:
    """Default logo scale (fraction of canvas width) per asset type."""
    return {
        AssetType.LOGO_LOCKUP: 0.35,
        AssetType.PRODUCT_HERO: 0.12,
        AssetType.LIFESTYLE: 0.10,
        AssetType.PACKAGING: 0.20,
        AssetType.CAMPAIGN: 0.15,
        AssetType.SOCIAL: 0.12,
    }.get(asset_type, 0.15)


def _product_position_for(asset_type: AssetType) -> str:
    return {
        AssetType.PRODUCT_HERO: "center",
        AssetType.LIFESTYLE: "center-right",
        AssetType.PACKAGING: "center",
    }.get(asset_type, "center")


def _product_scale_for(asset_type: AssetType) -> float:
    return {
        AssetType.PRODUCT_HERO: 0.50,
        AssetType.LIFESTYLE: 0.35,
        AssetType.PACKAGING: 0.45,
    }.get(asset_type, 0.40)
