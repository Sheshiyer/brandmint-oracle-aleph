"""
Visual regression tests for the compositing engine — AF-13.

Tests pixel-level fidelity guarantees:
- Logo pixels are preserved exactly (not reinterpreted by AI)
- Product image pixels survive the composite pipeline
- Position/scale math produces correct placement
- Opacity blending is numerically correct
- Multi-layer stacking doesn't corrupt individual layers
"""

import os
import tempfile

import pytest

try:
    from PIL import Image, ImageDraw

    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

pytestmark = pytest.mark.skipif(not HAS_PILLOW, reason="Pillow not installed")

from brandmint.core.compositor import (
    CompositeConfig,
    LayerStack,
    LogoCompositor,
    Position,
    ProductCompositor,
)


def _make_color_block(width: int, height: int, color: tuple) -> Image.Image:
    """Create a solid color block with optional alpha."""
    mode = "RGBA" if len(color) == 4 else "RGB"
    return Image.new(mode, (width, height), color)


class TestLogoPixelFidelity:
    """AF-13: Verify that composited logos retain exact pixels."""

    def test_logo_pixels_preserved_at_center(self):
        """Logo placed at center retains its exact pixel values."""
        bg = _make_color_block(400, 400, (0, 0, 0, 255))
        logo = _make_color_block(40, 40, (255, 0, 0, 255))

        config = CompositeConfig(position=Position.CENTER, scale=0.1, padding=0)
        result = LogoCompositor().composite(bg, logo, config)

        # Logo should be 40px wide (0.1 * 400 = 40)
        cx, cy = 180, 180  # center of 400x400 with 40x40 overlay
        pixel = result.getpixel((cx + 20, cy + 20))  # center of logo
        assert pixel == (255, 0, 0, 255), f"Logo pixel should be pure red, got {pixel}"

    def test_logo_color_exact_match(self):
        """Multiple distinct logo colors survive compositing."""
        bg = _make_color_block(200, 200, (50, 50, 50, 255))

        # Create a logo with two distinct halves
        logo = Image.new("RGBA", (100, 50), (0, 0, 0, 0))
        draw = ImageDraw.Draw(logo)
        draw.rectangle([0, 0, 49, 49], fill=(0, 255, 0, 255))  # left green
        draw.rectangle([50, 0, 99, 49], fill=(0, 0, 255, 255))  # right blue

        config = CompositeConfig(position=Position.CENTER, scale=0.5, padding=0)
        result = LogoCompositor().composite(bg, logo, config)

        # Scale 0.5 of 200 = 100px wide, centered at (50, 75)
        left_pixel = result.getpixel((60, 95))  # in green half
        right_pixel = result.getpixel((140, 95))  # in blue half
        assert left_pixel[:3] == (0, 255, 0), f"Expected green, got {left_pixel}"
        assert right_pixel[:3] == (0, 0, 255), f"Expected blue, got {right_pixel}"

    def test_transparent_regions_show_background(self):
        """Transparent parts of logo reveal the background."""
        bg = _make_color_block(200, 200, (100, 100, 100, 255))

        logo = Image.new("RGBA", (100, 100), (0, 0, 0, 0))  # fully transparent
        draw = ImageDraw.Draw(logo)
        draw.rectangle([25, 25, 75, 75], fill=(255, 0, 0, 255))  # red center

        config = CompositeConfig(position=Position.CENTER, scale=0.5, padding=0)
        result = LogoCompositor().composite(bg, logo, config)

        # Corner of logo region should still be gray background
        corner = result.getpixel((55, 55))  # top-left of logo area, transparent part
        assert corner == (100, 100, 100, 255), f"Background should show through, got {corner}"


class TestPositionMath:
    """Verify exact pixel placement for each position."""

    def test_top_left_exact(self):
        bg = _make_color_block(100, 100, (0, 0, 0, 255))
        logo = _make_color_block(10, 10, (255, 255, 255, 255))
        config = CompositeConfig(position=Position.TOP_LEFT, scale=0.1, padding=5)
        result = LogoCompositor().composite(bg, logo, config)
        # At (5,5) should be white
        assert result.getpixel((5, 5)) == (255, 255, 255, 255)
        # At (4,4) should be black (background)
        assert result.getpixel((4, 4)) == (0, 0, 0, 255)

    def test_bottom_right_exact(self):
        bg = _make_color_block(100, 100, (0, 0, 0, 255))
        logo = _make_color_block(10, 10, (255, 255, 255, 255))
        config = CompositeConfig(position=Position.BOTTOM_RIGHT, scale=0.1, padding=5)
        result = LogoCompositor().composite(bg, logo, config)
        # Bottom-right: logo at (85, 85) to (95, 95)
        assert result.getpixel((90, 90)) == (255, 255, 255, 255)
        assert result.getpixel((96, 96)) == (0, 0, 0, 255)


class TestOpacityRegression:
    """Verify opacity blending produces correct pixel values."""

    def test_50_percent_opacity(self):
        """50% opacity overlay should be visibly lighter than background but darker than full opacity."""
        bg = _make_color_block(100, 100, (0, 0, 0, 255))
        overlay = _make_color_block(100, 100, (255, 255, 255, 255))

        # Full opacity result
        full_config = CompositeConfig(position=Position.CENTER, scale=1.0, opacity=1.0, padding=0)
        full_result = LogoCompositor().composite(bg, overlay, full_config)

        # Half opacity result
        half_config = CompositeConfig(position=Position.CENTER, scale=1.0, opacity=0.5, padding=0)
        half_result = LogoCompositor().composite(bg, overlay, half_config)

        full_pixel = full_result.getpixel((50, 50))
        half_pixel = half_result.getpixel((50, 50))

        # Full opacity should be pure white
        assert full_pixel[0] == 255, f"Full opacity should be white, got {full_pixel}"
        # Half opacity should be darker than full but lighter than black
        assert 0 < half_pixel[0] < 255, f"Half opacity should be between black and white, got {half_pixel}"

    def test_zero_opacity_invisible(self):
        """0% opacity overlay should leave background untouched."""
        bg = _make_color_block(100, 100, (42, 42, 42, 255))
        overlay = _make_color_block(100, 100, (255, 0, 0, 255))

        config = CompositeConfig(position=Position.CENTER, scale=1.0, opacity=0.0, padding=0)
        result = LogoCompositor().composite(bg, overlay, config)

        pixel = result.getpixel((50, 50))
        assert pixel == (42, 42, 42, 255), f"Background should be unchanged, got {pixel}"


class TestProductFidelity:
    """Verify product image compositing preserves key pixels."""

    def test_product_center_pixel(self):
        bg = _make_color_block(400, 400, (200, 200, 200, 255))
        product = _make_color_block(100, 100, (255, 128, 0, 255))

        comp = ProductCompositor()
        result = comp.composite(bg, product, scale=0.25, feather_radius=0)
        # Product is 100x100 scaled to 25% of 400 = 100px, centered at (150, 150)
        center = result.getpixel((200, 200))
        assert center[:3] == (255, 128, 0), f"Product center should be orange, got {center}"


class TestLayerStackRegression:
    """Verify multi-layer stacking maintains order and fidelity."""

    def test_later_layers_on_top(self):
        """Later layers should overlay earlier ones."""
        stack = LayerStack((100, 100))
        stack.add_background(_make_color_block(100, 100, (255, 0, 0, 255)))  # red
        stack.add_layer(
            _make_color_block(50, 50, (0, 255, 0, 255)),
            Position.TOP_LEFT, scale=0.5, padding=0,
        )
        result = stack.flatten()

        # Top-left should be green (second layer)
        assert result.getpixel((10, 10))[:3] == (0, 255, 0)
        # Bottom-right should be red (background)
        assert result.getpixel((90, 90))[:3] == (255, 0, 0)

    def test_three_layer_ordering(self):
        """Background → product → logo ordering is correct."""
        stack = LayerStack((200, 200))
        stack.add_background(_make_color_block(200, 200, (0, 0, 0, 255)))   # black
        stack.add_product(
            _make_color_block(100, 100, (0, 0, 255, 255)),  # blue product
            Position.CENTER, scale=0.5,
        )
        stack.add_logo(
            _make_color_block(20, 20, (255, 255, 0, 255)),  # yellow logo
            Position.CENTER, scale=0.1, padding=0,
        )
        result = stack.flatten()

        # Center should be yellow (logo on top)
        assert result.getpixel((100, 100))[:3] == (255, 255, 0)

    def test_roundtrip_save_load(self):
        """Flatten → save → load preserves pixel values."""
        stack = LayerStack((100, 100))
        stack.add_background(_make_color_block(100, 100, (42, 84, 126, 255)))
        stack.add_logo(
            _make_color_block(10, 10, (200, 100, 50, 255)),
            Position.CENTER, scale=0.1, padding=0,
        )

        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "roundtrip.png")
            stack.flatten_and_save(path)
            loaded = Image.open(path).convert("RGBA")
            # Center should have logo color
            assert loaded.getpixel((50, 50))[:3] == (200, 100, 50)
