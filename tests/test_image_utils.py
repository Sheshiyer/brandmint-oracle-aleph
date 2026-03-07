"""Tests for brandmint.core.image_utils — AF-01, AF-02, AF-03."""

import os
import tempfile

import pytest
from PIL import Image

from brandmint.core.image_utils import (
    AssetMetadata,
    BoundingBox,
    ColorMode,
    DominantColor,
    ImageFormat,
    LogoAnalysis,
    analyze_logo,
    convert_format,
    extract_metadata,
    generate_transparency_mask,
    get_dimensions,
    get_format,
    load_image,
    save_image,
)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def fixture_path(name: str) -> str:
    return os.path.join(FIXTURES_DIR, name)


# ---------------------------------------------------------------------------
# AF-01: Image I/O
# ---------------------------------------------------------------------------


class TestLoadImage:
    def test_load_png(self):
        img = load_image(fixture_path("test-logo-transparent.png"))
        assert isinstance(img, Image.Image)
        assert img.size == (200, 100)
        assert img.mode == "RGBA"

    def test_load_jpeg(self):
        img = load_image(fixture_path("test-logo-opaque.jpg"))
        assert isinstance(img, Image.Image)
        assert img.size == (300, 300)
        assert img.mode == "RGB"

    def test_load_webp(self):
        img = load_image(fixture_path("test-small.webp"))
        assert isinstance(img, Image.Image)
        assert img.size == (64, 64)

    def test_load_nonexistent_raises(self):
        with pytest.raises(Exception):
            load_image(fixture_path("nonexistent.png"))


class TestSaveImage:
    def test_save_png(self):
        img = Image.new("RGBA", (50, 50), (255, 0, 0, 128))
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            path = f.name
        try:
            result = save_image(img, path)
            assert os.path.exists(result)
            reloaded = Image.open(result)
            assert reloaded.size == (50, 50)
        finally:
            os.unlink(path)

    def test_save_jpeg_strips_alpha(self):
        img = Image.new("RGBA", (50, 50), (255, 0, 0, 128))
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            path = f.name
        try:
            save_image(img, path)
            reloaded = Image.open(path)
            assert reloaded.mode == "RGB"
        finally:
            os.unlink(path)


class TestConvertFormat:
    def test_png_to_jpeg(self):
        src = fixture_path("test-logo-transparent.png")
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            dst = f.name
        try:
            convert_format(src, dst)
            assert os.path.exists(dst)
            img = Image.open(dst)
            assert img.mode == "RGB"  # Alpha stripped
        finally:
            os.unlink(dst)

    def test_jpeg_to_png(self):
        src = fixture_path("test-logo-opaque.jpg")
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            dst = f.name
        try:
            convert_format(src, dst)
            assert os.path.exists(dst)
            fmt = get_format(dst)
            assert fmt == ImageFormat.PNG
        finally:
            os.unlink(dst)


class TestGetFormat:
    def test_png_magic_bytes(self):
        assert get_format(fixture_path("test-logo-transparent.png")) == ImageFormat.PNG

    def test_jpeg_magic_bytes(self):
        assert get_format(fixture_path("test-logo-opaque.jpg")) == ImageFormat.JPEG

    def test_webp_magic_bytes(self):
        assert get_format(fixture_path("test-small.webp")) == ImageFormat.WEBP


class TestGetDimensions:
    def test_png_dimensions(self):
        w, h = get_dimensions(fixture_path("test-logo-transparent.png"))
        assert w == 200
        assert h == 100

    def test_jpeg_dimensions(self):
        w, h = get_dimensions(fixture_path("test-logo-opaque.jpg"))
        assert w == 300
        assert h == 300


# ---------------------------------------------------------------------------
# AF-02: Metadata Extraction
# ---------------------------------------------------------------------------


class TestExtractMetadata:
    def test_png_with_transparency(self):
        meta = extract_metadata(fixture_path("test-logo-transparent.png"))
        assert isinstance(meta, AssetMetadata)
        assert meta.width == 200
        assert meta.height == 100
        assert meta.format == ImageFormat.PNG
        assert meta.color_mode == ColorMode.RGBA
        assert meta.has_transparency is True
        assert meta.file_size_kb > 0
        assert meta.aspect_ratio == 2.0
        assert meta.is_landscape is True

    def test_jpeg_no_transparency(self):
        meta = extract_metadata(fixture_path("test-logo-opaque.jpg"))
        assert meta.format == ImageFormat.JPEG
        assert meta.color_mode == ColorMode.RGB
        assert meta.has_transparency is False
        assert meta.width == 300
        assert meta.height == 300
        assert meta.is_square is True

    def test_webp_metadata(self):
        meta = extract_metadata(fixture_path("test-small.webp"))
        assert meta.format == ImageFormat.WEBP
        assert meta.width == 64
        assert meta.height == 64

    def test_high_dpi(self):
        meta = extract_metadata(fixture_path("test-square-300dpi.png"))
        # DPI can have minor rounding (299 vs 300) depending on PNG metadata encoding
        assert abs(meta.dpi[0] - 300) <= 2
        assert abs(meta.dpi[1] - 300) <= 2
        assert meta.width == 512

    def test_file_path_stored(self):
        path = fixture_path("test-logo-transparent.png")
        meta = extract_metadata(path)
        assert meta.file_path == path


# ---------------------------------------------------------------------------
# AF-03: Logo Analysis
# ---------------------------------------------------------------------------


class TestAnalyzeLogo:
    def test_transparent_logo(self):
        result = analyze_logo(fixture_path("test-logo-transparent.png"))
        assert isinstance(result, LogoAnalysis)
        assert result.has_transparency is True
        assert result.is_svg is False
        assert result.original_width == 200
        assert result.original_height == 100
        # Bounding box should be smaller than original (has transparent padding)
        assert result.bounding_box.width > 0
        assert result.bounding_box.width <= 200
        assert result.trimmed_width > 0

    def test_opaque_logo(self):
        result = analyze_logo(fixture_path("test-logo-opaque.jpg"))
        assert result.has_transparency is False
        assert result.original_width == 300
        assert result.original_height == 300

    def test_dominant_colors_extracted(self):
        result = analyze_logo(fixture_path("test-logo-transparent.png"), max_colors=3)
        assert len(result.dominant_colors) > 0
        assert len(result.dominant_colors) <= 3
        for color in result.dominant_colors:
            assert isinstance(color, DominantColor)
            assert 0 <= color.r <= 255
            assert 0 <= color.g <= 255
            assert 0 <= color.b <= 255
            assert color.hex.startswith("#")
            assert len(color.hex) == 7

    def test_color_count(self):
        result = analyze_logo(fixture_path("test-logo-transparent.png"))
        assert result.color_count > 0

    def test_aspect_ratio(self):
        result = analyze_logo(fixture_path("test-logo-transparent.png"))
        # 200x100 → trimmed aspect should be roughly 2:1
        assert result.aspect_ratio > 1.0

    def test_bounding_box_values(self):
        result = analyze_logo(fixture_path("test-logo-transparent.png"))
        bb = result.bounding_box
        assert isinstance(bb, BoundingBox)
        assert bb.left >= 0
        assert bb.top >= 0
        assert bb.right <= 200
        assert bb.bottom <= 100
        assert bb.width > 0
        assert bb.height > 0
        assert bb.center[0] > 0
        assert bb.center[1] > 0


class TestTransparencyMask:
    def test_mask_from_transparent_image(self):
        mask = generate_transparency_mask(fixture_path("test-logo-transparent.png"))
        assert mask is not None
        assert mask.mode == "L"
        assert mask.size == (200, 100)
        # Should have both black (transparent) and white (opaque) pixels
        extrema = mask.getextrema()
        assert extrema[0] == 0  # Has transparent regions
        assert extrema[1] == 255  # Has opaque regions

    def test_mask_from_opaque_image(self):
        mask = generate_transparency_mask(fixture_path("test-logo-opaque.jpg"))
        assert mask is not None
        assert mask.mode == "L"
        # All-white mask (fully opaque)
        assert mask.getextrema() == (255, 255)
