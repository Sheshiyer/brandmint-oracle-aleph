"""AF-19: End-to-end test for the logo composite pipeline.

Tests the full flow: brand-config → route_asset → composite → provenance.
Verifies pixel fidelity of composited logos and provenance tracking.

TDD: Tests written FIRST, before any new production code is needed.
These tests exercise the EXISTING modules in an integrated fashion.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from brandmint.core.asset_mode import AssetMode, route_asset
from brandmint.core.asset_provenance import AssetProvenance, AssetSource
from brandmint.core.compositor import CompositeConfig, LogoCompositor, Position
from brandmint.core.image_utils import load_image


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FIXTURE_DIR = Path(__file__).parent / "fixtures"
LOGO_PATH = FIXTURE_DIR / "test-logo-transparent.png"


@pytest.fixture
def logo_image() -> Image.Image:
    """Load the test logo fixture."""
    return load_image(str(LOGO_PATH))


@pytest.fixture
def background_image() -> Image.Image:
    """Create a synthetic 1024x1024 background (simulates AI-generated scene)."""
    bg = Image.new("RGBA", (1024, 1024), (30, 60, 120, 255))
    # Add some variation so it's not flat
    for x in range(0, 1024, 64):
        for y in range(0, 1024, 64):
            r = (x * 37 + y * 13) % 200 + 30
            g = (x * 11 + y * 29) % 200 + 30
            b = (x * 23 + y * 7) % 200 + 30
            bg.putpixel((x, y), (r, g, b, 255))
    return bg


@pytest.fixture
def brand_config() -> dict:
    """Minimal brand config with logo_files."""
    return {
        "brand": {
            "name": "TestBrand",
            "tagline": "Pixel-perfect logos",
        },
        "generation": {
            "asset_mode": "composite",
        },
        "logo_files": [str(LOGO_PATH)],
    }


@pytest.fixture
def provenance_dir(tmp_path) -> Path:
    """Temp directory for provenance storage."""
    return tmp_path / "test-brand"


@pytest.fixture
def compositor() -> LogoCompositor:
    return LogoCompositor()


# ---------------------------------------------------------------------------
# Test 1: Route decision for logo-bearing composite asset
# ---------------------------------------------------------------------------


class TestRouteDecisionForComposite:
    """Verify route_asset returns COMPOSITE mode for logo-bearing assets."""

    def test_product_hero_routes_to_composite_with_logo(self):
        """3A-product-hero should route to COMPOSITE when global mode is composite
        and has_logo is True."""
        decision = route_asset(
            asset_id="3A-product-hero",
            global_mode=AssetMode.COMPOSITE,
            has_logo=True,
        )
        assert decision.mode == AssetMode.COMPOSITE
        assert decision.use_logo_composite is True
        assert decision.needs_composite_pass is True

    def test_email_hero_routes_to_composite_with_logo(self):
        """5A-email-hero (PACKAGING type) should route to COMPOSITE."""
        decision = route_asset(
            asset_id="5A-email-hero",
            global_mode=AssetMode.COMPOSITE,
            has_logo=True,
        )
        assert decision.mode == AssetMode.COMPOSITE
        assert decision.use_logo_composite is True

    def test_bento_grid_always_generates(self):
        """2A-bento-grid is the style anchor — it ALWAYS generates."""
        decision = route_asset(
            asset_id="2A-bento-grid-lockup",
            global_mode=AssetMode.COMPOSITE,
            has_logo=True,
        )
        assert decision.mode == AssetMode.GENERATE
        assert decision.use_logo_composite is False


# ---------------------------------------------------------------------------
# Test 2: Logo compositing produces valid output
# ---------------------------------------------------------------------------


class TestLogoCompositing:
    """Verify LogoCompositor produces valid images with correct dimensions."""

    def test_composite_returns_rgba_image(self, background_image, logo_image, compositor):
        """Composite output should be an RGBA image."""
        config = CompositeConfig(
            position=Position.BOTTOM_RIGHT,
            scale=0.15,
            padding=20,
        )
        result = compositor.composite(background_image, logo_image, config)
        assert result.mode == "RGBA"

    def test_composite_preserves_background_dimensions(
        self, background_image, logo_image, compositor
    ):
        """Output should have the same dimensions as the background."""
        config = CompositeConfig(position=Position.CENTER, scale=0.20)
        result = compositor.composite(background_image, logo_image, config)
        assert result.size == background_image.size


# ---------------------------------------------------------------------------
# Test 3: Pixel fidelity — composited image contains original logo pixels
# ---------------------------------------------------------------------------


class TestPixelFidelity:
    """Verify the composited image contains logo pixels at the expected location."""

    def test_logo_pixels_present_in_composite(
        self, background_image, logo_image, compositor
    ):
        """After compositing, the region where the logo was placed should
        differ from the original background — proving the logo was applied."""
        config = CompositeConfig(
            position=Position.BOTTOM_RIGHT,
            scale=0.15,
            padding=20,
        )
        result = compositor.composite(background_image, logo_image, config)

        # Calculate where the logo was placed
        logo_w = int(background_image.width * config.scale)
        ratio = logo_w / logo_image.width
        logo_h = int(logo_image.height * ratio)
        x = background_image.width - logo_w - config.padding
        y = background_image.height - logo_h - config.padding

        # Sample pixels from the logo region in the composite
        # At least some pixels should differ from the original background
        changed_pixels = 0
        total_sampled = 0
        for dx in range(0, logo_w, max(1, logo_w // 10)):
            for dy in range(0, logo_h, max(1, logo_h // 10)):
                px, py = x + dx, y + dy
                if 0 <= px < result.width and 0 <= py < result.height:
                    orig = background_image.getpixel((px, py))
                    comp = result.getpixel((px, py))
                    total_sampled += 1
                    if orig != comp:
                        changed_pixels += 1

        # The logo has transparent pixels, so not ALL pixels will change,
        # but a meaningful fraction should be different
        assert total_sampled > 0, "Should have sampled some pixels"
        assert changed_pixels > 0, (
            f"No pixels changed in logo region — logo was not applied! "
            f"(sampled {total_sampled} pixels)"
        )

    def test_non_logo_region_unchanged(self, background_image, logo_image, compositor):
        """Pixels far from the logo placement should match the original background."""
        config = CompositeConfig(
            position=Position.BOTTOM_RIGHT,
            scale=0.15,
            padding=20,
        )
        result = compositor.composite(background_image, logo_image, config)

        # Top-left corner should be untouched (logo is bottom-right)
        for x in range(0, 50, 5):
            for y in range(0, 50, 5):
                orig = background_image.getpixel((x, y))
                comp = result.getpixel((x, y))
                assert orig == comp, (
                    f"Pixel ({x},{y}) changed unexpectedly: {orig} → {comp}"
                )


# ---------------------------------------------------------------------------
# Test 4: Provenance records composited source
# ---------------------------------------------------------------------------


class TestProvenanceTracking:
    """Verify AssetProvenance correctly records composited assets."""

    def test_register_composited_source(self, provenance_dir):
        """register_composited should store source='composited'."""
        prov = AssetProvenance(str(provenance_dir))
        record = prov.register_composited(
            asset_id="3A-product-hero",
            file_path="/output/3A-product-hero-composited.png",
            layers=[str(LOGO_PATH), "/output/3A-background.png"],
            model="nano-banana-pro",
            provider="fal",
            seed=42,
        )
        assert record.source == AssetSource.COMPOSITED
        assert record.asset_id == "3A-product-hero"
        assert len(record.composite_layers) == 2

    def test_provenance_persists_and_retrieves(self, provenance_dir):
        """Provenance should persist to disk and be retrievable."""
        prov = AssetProvenance(str(provenance_dir))
        prov.register_composited(
            asset_id="5A-email-hero",
            file_path="/output/5A-composited.png",
            layers=[str(LOGO_PATH)],
        )
        # Reload from disk
        prov2 = AssetProvenance(str(provenance_dir))
        record = prov2.get("5A-email-hero")
        assert record is not None
        assert record.source == AssetSource.COMPOSITED


# ---------------------------------------------------------------------------
# Test 5: Full E2E pipeline — route → composite → record provenance
# ---------------------------------------------------------------------------


class TestFullE2EPipeline:
    """Integration test: the full route → composite → provenance flow."""

    def test_e2e_product_hero_composite_pipeline(
        self, background_image, logo_image, provenance_dir, compositor
    ):
        """Full pipeline: route 3A-product-hero → composite logo → record provenance.

        Steps:
        1. Create brand config with logo_files
        2. Route 3A-product-hero with composite mode
        3. Composite the logo onto a generated background
        4. Record provenance as 'composited'
        5. Verify pixel fidelity + provenance correctness
        """
        # Step 1: Route
        decision = route_asset(
            asset_id="3A-product-hero",
            global_mode=AssetMode.COMPOSITE,
            has_logo=True,
        )
        assert decision.mode == AssetMode.COMPOSITE
        assert decision.use_logo_composite is True

        # Step 2: Composite
        config = CompositeConfig(
            position=Position(decision.logo_position),
            scale=decision.logo_scale,
        )
        result = compositor.composite(background_image, logo_image, config)
        assert result.size == background_image.size
        assert result.mode == "RGBA"

        # Step 3: Verify pixel fidelity — result differs from background
        # Check that at least the composited result is different from background somewhere
        def _get_data(im):
            return im.get_flattened_data() if hasattr(im, "get_flattened_data") else im.getdata()

        bg_data = list(_get_data(background_image))
        result_data = list(_get_data(result))
        diff_count = sum(1 for a, b in zip(bg_data, result_data) if a != b)
        assert diff_count > 0, "Composited image should differ from background"

        # Step 4: Record provenance
        output_path = str(provenance_dir / "3A-product-hero-composited.png")
        prov = AssetProvenance(str(provenance_dir))
        record = prov.register_composited(
            asset_id="3A-product-hero",
            file_path=output_path,
            layers=[str(LOGO_PATH), "background-generated.png"],
            model="nano-banana-pro",
            provider="fal",
            seed=1337,
        )

        # Step 5: Verify provenance
        assert record.source == AssetSource.COMPOSITED
        assert record.source.value == "composited"
        assert record.model_used == "nano-banana-pro"
        assert str(LOGO_PATH) in record.composite_layers

        # Verify persistence
        retrieved = prov.get("3A-product-hero", seed=1337)
        assert retrieved is not None
        assert retrieved.source == AssetSource.COMPOSITED

    def test_e2e_save_and_reload_composited_image(
        self, background_image, logo_image, tmp_path, compositor
    ):
        """Full pipeline with disk I/O: composite → save → reload → verify."""
        config = CompositeConfig(
            position=Position.BOTTOM_RIGHT,
            scale=0.12,
            padding=20,
        )
        result = compositor.composite(background_image, logo_image, config)

        # Save to disk
        output_path = str(tmp_path / "composited-output.png")
        result.save(output_path)

        # Reload and verify
        reloaded = load_image(output_path)
        assert reloaded.size == result.size

        # Spot check a few pixels match
        for x, y in [(0, 0), (512, 512), (100, 100)]:
            assert reloaded.getpixel((x, y)) == result.getpixel((x, y))

    def test_e2e_lifestyle_asset_routes_correctly(self):
        """4A-lifestyle should route to composite with logo in bottom-left."""
        decision = route_asset(
            asset_id="4A-lifestyle-scene",
            global_mode=AssetMode.COMPOSITE,
            has_logo=True,
        )
        assert decision.mode == AssetMode.COMPOSITE
        assert decision.use_logo_composite is True
        assert decision.logo_position == "bottom-left"  # lifestyle default
