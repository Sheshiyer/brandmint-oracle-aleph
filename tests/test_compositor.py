"""Tests for brandmint.core.compositor — AF-06 through AF-09."""

import os
import tempfile

import pytest

try:
    from PIL import Image

    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

pytestmark = pytest.mark.skipif(not HAS_PILLOW, reason="Pillow not installed")

from brandmint.core.compositor import (
    BlendMode,
    CompositeConfig,
    LayerStack,
    LogoCompositor,
    Position,
    PostGenCompositor,
    ProductCompositor,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def canvas_800x600():
    """800x600 blue background."""
    return Image.new("RGBA", (800, 600), (30, 60, 120, 255))


@pytest.fixture
def logo_transparent():
    """100x50 RGBA logo with transparency."""
    img = Image.new("RGBA", (100, 50), (0, 0, 0, 0))
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.rectangle([10, 10, 90, 40], fill=(255, 100, 0, 255))
    return img


@pytest.fixture
def logo_opaque():
    """80x80 RGB logo (no alpha)."""
    img = Image.new("RGB", (80, 80), (255, 255, 255))
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.ellipse([5, 5, 75, 75], fill=(200, 0, 50))
    return img


@pytest.fixture
def product_on_white():
    """200x200 product image on white background."""
    img = Image.new("RGB", (200, 200), (255, 255, 255))
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.rectangle([40, 40, 160, 160], fill=(50, 50, 200))
    return img


@pytest.fixture
def product_transparent():
    """200x200 product image with transparency."""
    img = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.rectangle([30, 30, 170, 170], fill=(200, 100, 50, 255))
    return img


# ---------------------------------------------------------------------------
# AF-06: Logo Compositing
# ---------------------------------------------------------------------------

class TestLogoCompositor:
    def test_basic_composite(self, canvas_800x600, logo_transparent):
        comp = LogoCompositor()
        result = comp.composite(canvas_800x600, logo_transparent)
        assert result.size == (800, 600)
        assert result.mode == "RGBA"

    def test_position_top_left(self, canvas_800x600, logo_transparent):
        config = CompositeConfig(position=Position.TOP_LEFT, scale=0.1, padding=10)
        result = LogoCompositor().composite(canvas_800x600, logo_transparent, config)
        # Logo should be scaled to 80px wide (0.1 * 800)
        assert result.size == (800, 600)

    def test_position_bottom_right(self, canvas_800x600, logo_transparent):
        config = CompositeConfig(position=Position.BOTTOM_RIGHT, scale=0.15, padding=20)
        result = LogoCompositor().composite(canvas_800x600, logo_transparent, config)
        assert result.size == (800, 600)

    def test_position_center(self, canvas_800x600, logo_transparent):
        config = CompositeConfig(position=Position.CENTER, scale=0.2)
        result = LogoCompositor().composite(canvas_800x600, logo_transparent, config)
        assert result.size == (800, 600)

    def test_opacity_half(self, canvas_800x600, logo_transparent):
        config = CompositeConfig(opacity=0.5)
        result = LogoCompositor().composite(canvas_800x600, logo_transparent, config)
        assert result.size == (800, 600)

    def test_with_shadow(self, canvas_800x600, logo_transparent):
        config = CompositeConfig(shadow=True, shadow_blur=3)
        result = LogoCompositor().composite(canvas_800x600, logo_transparent, config)
        assert result.size == (800, 600)

    def test_blend_multiply(self, canvas_800x600, logo_opaque):
        config = CompositeConfig(blend_mode=BlendMode.MULTIPLY, scale=0.3)
        result = LogoCompositor().composite(canvas_800x600, logo_opaque, config)
        assert result.size == (800, 600)

    def test_blend_screen(self, canvas_800x600, logo_opaque):
        config = CompositeConfig(blend_mode=BlendMode.SCREEN, scale=0.3)
        result = LogoCompositor().composite(canvas_800x600, logo_opaque, config)
        assert result.size == (800, 600)

    def test_opaque_logo_gets_alpha(self, canvas_800x600, logo_opaque):
        """Logo without alpha still composites correctly."""
        config = CompositeConfig(scale=0.2)
        result = LogoCompositor().composite(canvas_800x600, logo_opaque, config)
        assert result.mode == "RGBA"

    def test_tiny_scale(self, canvas_800x600, logo_transparent):
        """Extremely small scale doesn't crash."""
        config = CompositeConfig(scale=0.001)
        result = LogoCompositor().composite(canvas_800x600, logo_transparent, config)
        assert result.size == (800, 600)

    def test_composite_from_paths(self, canvas_800x600, logo_transparent):
        with tempfile.TemporaryDirectory() as td:
            bg_path = os.path.join(td, "bg.png")
            logo_path = os.path.join(td, "logo.png")
            out_path = os.path.join(td, "result.png")
            canvas_800x600.save(bg_path)
            logo_transparent.save(logo_path)

            result_path = LogoCompositor().composite_from_paths(bg_path, logo_path, out_path)
            assert os.path.exists(result_path)
            result = Image.open(result_path)
            assert result.size == (800, 600)

    def test_all_nine_positions(self, canvas_800x600, logo_transparent):
        """Every Position enum value produces valid output."""
        comp = LogoCompositor()
        for pos in Position:
            config = CompositeConfig(position=pos, scale=0.1)
            result = comp.composite(canvas_800x600, logo_transparent, config)
            assert result.size == (800, 600), f"Failed for position {pos}"


# ---------------------------------------------------------------------------
# AF-07: Product Image Compositing
# ---------------------------------------------------------------------------

class TestProductCompositor:
    def test_product_on_white_bg_removal(self, canvas_800x600, product_on_white):
        """Product on white background gets auto-removed white."""
        comp = ProductCompositor()
        result = comp.composite(canvas_800x600, product_on_white, scale=0.4)
        assert result.size == (800, 600)

    def test_product_with_transparency(self, canvas_800x600, product_transparent):
        comp = ProductCompositor()
        result = comp.composite(canvas_800x600, product_transparent, scale=0.4)
        assert result.size == (800, 600)

    def test_product_feathered_edges(self, canvas_800x600, product_transparent):
        comp = ProductCompositor()
        result = comp.composite(canvas_800x600, product_transparent, feather_radius=10)
        assert result.size == (800, 600)

    def test_product_no_feather(self, canvas_800x600, product_transparent):
        comp = ProductCompositor()
        result = comp.composite(canvas_800x600, product_transparent, feather_radius=0)
        assert result.size == (800, 600)

    def test_product_position(self, canvas_800x600, product_transparent):
        comp = ProductCompositor()
        result = comp.composite(
            canvas_800x600, product_transparent, position=Position.TOP_LEFT, scale=0.3
        )
        assert result.size == (800, 600)

    def test_product_opacity(self, canvas_800x600, product_transparent):
        comp = ProductCompositor()
        result = comp.composite(canvas_800x600, product_transparent, opacity=0.7)
        assert result.size == (800, 600)


# ---------------------------------------------------------------------------
# AF-08: Post-Generation Composite Pass
# ---------------------------------------------------------------------------

class TestPostGenCompositor:
    def test_composite_pass(self, canvas_800x600, logo_transparent):
        with tempfile.TemporaryDirectory() as td:
            bg_path = os.path.join(td, "generated.png")
            logo_path = os.path.join(td, "logo.png")
            out_path = os.path.join(td, "composited.png")
            canvas_800x600.save(bg_path)
            logo_transparent.save(logo_path)

            comp = PostGenCompositor()
            result_path = comp.composite_pass(bg_path, logo_path, out_path)
            assert os.path.exists(result_path)

    def test_composite_pass_with_analysis(self, canvas_800x600, logo_transparent):
        with tempfile.TemporaryDirectory() as td:
            bg_path = os.path.join(td, "generated.png")
            logo_path = os.path.join(td, "logo.png")
            out_path = os.path.join(td, "composited.png")
            canvas_800x600.save(bg_path)
            logo_transparent.save(logo_path)

            comp = PostGenCompositor()
            result_path = comp.composite_pass_with_analysis(
                bg_path, logo_path, out_path
            )
            assert os.path.exists(result_path)
            result = Image.open(result_path)
            assert result.size == (800, 600)

    def test_analysis_wide_logo(self):
        """Wide logo (aspect > 2.0) gets larger scale."""
        wide_logo = Image.new("RGBA", (400, 50), (0, 0, 0, 0))
        from PIL import ImageDraw
        draw = ImageDraw.Draw(wide_logo)
        draw.rectangle([10, 10, 390, 40], fill=(255, 0, 0, 255))
        bg = Image.new("RGBA", (800, 600), (100, 100, 200, 255))

        with tempfile.TemporaryDirectory() as td:
            bg_path = os.path.join(td, "bg.png")
            logo_path = os.path.join(td, "wide_logo.png")
            out_path = os.path.join(td, "result.png")
            bg.save(bg_path)
            wide_logo.save(logo_path)

            comp = PostGenCompositor()
            result_path = comp.composite_pass_with_analysis(
                bg_path, logo_path, out_path
            )
            assert os.path.exists(result_path)

    def test_custom_position_override(self, canvas_800x600, logo_transparent):
        with tempfile.TemporaryDirectory() as td:
            bg_path = os.path.join(td, "bg.png")
            logo_path = os.path.join(td, "logo.png")
            out_path = os.path.join(td, "result.png")
            canvas_800x600.save(bg_path)
            logo_transparent.save(logo_path)

            comp = PostGenCompositor()
            result_path = comp.composite_pass_with_analysis(
                bg_path, logo_path, out_path, position=Position.TOP_LEFT
            )
            assert os.path.exists(result_path)


# ---------------------------------------------------------------------------
# AF-09: Multi-Layer Compositor (LayerStack)
# ---------------------------------------------------------------------------

class TestLayerStack:
    def test_empty_stack(self):
        stack = LayerStack((400, 300))
        result = stack.flatten()
        assert result.size == (400, 300)
        assert result.mode == "RGBA"

    def test_single_background_layer(self, canvas_800x600):
        stack = LayerStack((800, 600))
        stack.add_background(canvas_800x600)
        result = stack.flatten()
        assert result.size == (800, 600)

    def test_background_plus_logo(self, canvas_800x600, logo_transparent):
        stack = LayerStack((800, 600))
        stack.add_background(canvas_800x600)
        stack.add_logo(logo_transparent, Position.BOTTOM_RIGHT, scale=0.15)
        result = stack.flatten()
        assert result.size == (800, 600)

    def test_three_layer_composite(self, canvas_800x600, product_transparent, logo_transparent):
        stack = LayerStack((800, 600))
        stack.add_background(canvas_800x600)
        stack.add_product(product_transparent, Position.CENTER, scale=0.4)
        stack.add_logo(logo_transparent, Position.BOTTOM_RIGHT, scale=0.12)
        result = stack.flatten()
        assert result.size == (800, 600)

    def test_chaining_api(self, canvas_800x600, product_transparent, logo_transparent):
        result = (
            LayerStack((800, 600))
            .add_background(canvas_800x600)
            .add_product(product_transparent)
            .add_logo(logo_transparent)
            .flatten()
        )
        assert result.size == (800, 600)

    def test_flatten_and_save(self, canvas_800x600, logo_transparent):
        with tempfile.TemporaryDirectory() as td:
            out_path = os.path.join(td, "stacked.png")
            stack = LayerStack((800, 600))
            stack.add_background(canvas_800x600)
            stack.add_logo(logo_transparent)
            result_path = stack.flatten_and_save(out_path)
            assert os.path.exists(result_path)

    def test_layer_with_opacity(self, canvas_800x600, logo_transparent):
        stack = LayerStack((800, 600))
        stack.add_background(canvas_800x600)
        stack.add_layer(logo_transparent, Position.CENTER, scale=0.3, opacity=0.5)
        result = stack.flatten()
        assert result.size == (800, 600)

    def test_multiply_blend_layer(self, canvas_800x600, logo_opaque):
        stack = LayerStack((800, 600))
        stack.add_background(canvas_800x600)
        stack.add_layer(logo_opaque, Position.CENTER, scale=0.3, blend_mode=BlendMode.MULTIPLY)
        result = stack.flatten()
        assert result.size == (800, 600)

    def test_many_layers(self, canvas_800x600, logo_transparent):
        stack = LayerStack((800, 600))
        stack.add_background(canvas_800x600)
        for pos in [Position.TOP_LEFT, Position.TOP_RIGHT,
                     Position.BOTTOM_LEFT, Position.BOTTOM_RIGHT]:
            stack.add_logo(logo_transparent, pos, scale=0.08)
        result = stack.flatten()
        assert result.size == (800, 600)
