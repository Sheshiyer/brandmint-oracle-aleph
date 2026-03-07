"""Tests for brandmint.publishing.vision_describer — NB-01 through NB-04."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

try:
    from PIL import Image

    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

from brandmint.publishing.vision_describer import (
    AssetDescription,
    BrandStyleGuideBuilder,
    VisionDescriber,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_image(tmp_path):
    """Create a sample PNG image."""
    if not HAS_PILLOW:
        pytest.skip("Pillow not installed")
    img = Image.new("RGB", (100, 100), (255, 0, 0))
    path = tmp_path / "sample.png"
    img.save(str(path))
    return path


@pytest.fixture
def sample_logo(tmp_path):
    """Create a sample logo with transparency."""
    if not HAS_PILLOW:
        pytest.skip("Pillow not installed")
    img = Image.new("RGBA", (200, 100), (0, 0, 0, 0))
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.rectangle([20, 20, 180, 80], fill=(0, 100, 200, 255))
    path = tmp_path / "logo.png"
    img.save(str(path))
    return path


@pytest.fixture
def vision_describer(tmp_path):
    """VisionDescriber with cache dir."""
    return VisionDescriber(cache_dir=tmp_path / "cache")


@pytest.fixture
def sample_config():
    return {
        "brand": {
            "name": "TestBrand",
            "tagline": "Innovation meets design",
            "mission": "To revolutionize the industry",
            "voice": "Confident and approachable",
            "tone": "Professional yet friendly",
        },
        "palette": {
            "primary": {"name": "Deep Blue", "hex": "#1a237e", "usage": "Headers and CTAs"},
            "secondary": {"name": "Warm Gold", "hex": "#ffd54f", "usage": "Accents"},
            "neutral": "#f5f5f5",
        },
        "typography": {
            "heading": {"family": "Inter", "weight": "700", "style": "Bold, modern"},
            "body": {"family": "Source Sans Pro", "weight": "400"},
            "display": "Playfair Display",
        },
        "aesthetic": {
            "style": "minimalist",
            "materials": ["glass", "brushed metal", "matte"],
            "mood": "sophisticated and clean",
        },
        "theme": {
            "primary_metaphor": "Precision engineering",
            "visual_language": "Clean lines and geometric forms",
        },
    }


# ---------------------------------------------------------------------------
# NB-01: VisionDescriber core tests
# ---------------------------------------------------------------------------

class TestVisionDescriberInit:
    def test_no_api_key_not_available(self, tmp_path):
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}, clear=False):
            describer = VisionDescriber(cache_dir=tmp_path)
            # Force re-read
            describer._api_key = ""
            assert describer.available is False

    def test_with_api_key_available(self, tmp_path):
        describer = VisionDescriber(cache_dir=tmp_path)
        describer._api_key = "test-key"
        assert describer.available is True


class TestVisionDescriberValidation:
    def test_nonexistent_file_raises(self, vision_describer):
        with pytest.raises(FileNotFoundError):
            vision_describer.describe_asset("/nonexistent/image.png")

    def test_unsupported_format_raises(self, tmp_path, vision_describer):
        bad_file = tmp_path / "test.svg"
        bad_file.write_text("<svg></svg>")
        with pytest.raises(ValueError, match="Unsupported format"):
            vision_describer.describe_asset(str(bad_file))

    def test_oversized_file_raises(self, tmp_path, vision_describer):
        big_file = tmp_path / "huge.png"
        big_file.write_bytes(b"x" * (11 * 1024 * 1024))
        with pytest.raises(ValueError, match="too large"):
            vision_describer.describe_asset(str(big_file))


class TestVisionDescriberCache:
    def test_cache_write_and_read(self, sample_image, tmp_path):
        cache_dir = tmp_path / "cache"
        describer = VisionDescriber(cache_dir=cache_dir)
        describer._api_key = "test-key"

        # Mock the API call
        mock_response = ("A beautiful red image.", {"total_tokens": 100, "total_cost": 0.01})
        with patch.object(describer, "_call_vision", return_value=mock_response):
            result = describer.describe_asset(
                str(sample_image), asset_id="test-asset"
            )
            assert result.description == "A beautiful red image."
            assert not result.cached

        # Second call should hit cache
        result2 = describer.describe_asset(
            str(sample_image), asset_id="test-asset"
        )
        assert result2.description == "A beautiful red image."
        assert result2.cached

    def test_no_cache_dir_skips_cache(self, sample_image):
        describer = VisionDescriber(cache_dir=None)
        describer._api_key = "test-key"

        mock_response = ("Description.", {"total_tokens": 50, "total_cost": 0.005})
        with patch.object(describer, "_call_vision", return_value=mock_response):
            result = describer.describe_asset(str(sample_image))
            assert not result.cached


class TestVisionDescriberDescribe:
    def test_describe_returns_asset_description(self, sample_image, tmp_path):
        describer = VisionDescriber(cache_dir=tmp_path / "cache")
        describer._api_key = "test-key"

        mock_response = (
            "A solid red 100x100 pixel image with uniform color.",
            {"total_tokens": 150, "total_cost": 0.02},
        )
        with patch.object(describer, "_call_vision", return_value=mock_response):
            result = describer.describe_asset(
                str(sample_image),
                asset_id="2A-bento",
                asset_type="visual",
                brand_context="Premium tech brand",
            )

        assert isinstance(result, AssetDescription)
        assert result.asset_id == "2A-bento"
        assert result.asset_type == "visual"
        assert result.tokens_used == 150
        assert result.cost_usd == 0.02
        assert "red" in result.description.lower()

    def test_logo_asset_type_uses_logo_prompt(self, sample_logo, tmp_path):
        describer = VisionDescriber(cache_dir=tmp_path / "cache")
        describer._api_key = "test-key"

        calls = []

        def capture_call(system, user, path):
            calls.append(system)
            return ("Logo description.", {"total_tokens": 100})

        with patch.object(describer, "_call_vision", side_effect=capture_call):
            describer.describe_asset(
                str(sample_logo), asset_id="brand-logo", asset_type="logo"
            )

        assert len(calls) == 1
        assert "brand identity expert" in calls[0].lower()

    def test_empty_response_no_crash(self, sample_image, tmp_path):
        describer = VisionDescriber(cache_dir=tmp_path / "cache")
        describer._api_key = "test-key"

        with patch.object(describer, "_call_vision", return_value=("", None)):
            result = describer.describe_asset(str(sample_image))
            assert result.description == ""


class TestVisionDescriberBatch:
    def test_batch_describe(self, sample_image, sample_logo, tmp_path):
        describer = VisionDescriber(cache_dir=tmp_path / "cache")
        describer._api_key = "test-key"

        mock_response = ("Batch description.", {"total_tokens": 80, "total_cost": 0.01})
        with patch.object(describer, "_call_vision", return_value=mock_response):
            results = describer.describe_batch(
                assets=[
                    {"path": str(sample_image), "asset_id": "asset-1"},
                    {"path": str(sample_logo), "asset_id": "asset-2", "asset_type": "logo"},
                ],
                brand_context="Test brand",
            )

        assert len(results) == 2
        ids = {r.asset_id for r in results}
        assert "asset-1" in ids
        assert "asset-2" in ids

    def test_batch_telemetry(self, sample_image, tmp_path):
        describer = VisionDescriber(cache_dir=tmp_path / "cache")
        describer._api_key = "test-key"

        mock_response = ("Description.", {"total_tokens": 100, "total_cost": 0.01})
        with patch.object(describer, "_call_vision", return_value=mock_response):
            describer.describe_batch(
                assets=[
                    {"path": str(sample_image), "asset_id": f"a{i}"}
                    for i in range(3)
                ],
            )

        telemetry = describer.get_telemetry()
        assert telemetry["total_tokens"] == 300
        assert abs(telemetry["total_cost_usd"] - 0.03) < 0.001


class TestImageEncoding:
    def test_encode_image_produces_base64(self, sample_image):
        describer = VisionDescriber()
        encoded = describer._encode_image(sample_image)
        import base64
        decoded = base64.b64decode(encoded)
        assert decoded[:4] == b"\x89PNG"


# ---------------------------------------------------------------------------
# NB-04: Brand Style Guide Builder
# ---------------------------------------------------------------------------

class TestBrandStyleGuideBuilder:
    def test_builds_from_config(self, sample_config):
        builder = BrandStyleGuideBuilder()
        builder._api_key = ""  # No API = structured fallback
        guide = builder.build_style_guide(sample_config)

        assert "Brand Style Guide" in guide
        assert "Deep Blue" in guide
        assert "#1a237e" in guide
        assert "Inter" in guide
        assert "TestBrand" in guide

    def test_empty_config_returns_empty(self):
        builder = BrandStyleGuideBuilder()
        guide = builder.build_style_guide({})
        assert guide == ""

    def test_color_system_formatting(self, sample_config):
        builder = BrandStyleGuideBuilder()
        builder._api_key = ""
        guide = builder.build_style_guide(sample_config)
        assert "Warm Gold" in guide
        assert "Headers and CTAs" in guide

    def test_typography_formatting(self, sample_config):
        builder = BrandStyleGuideBuilder()
        builder._api_key = ""
        guide = builder.build_style_guide(sample_config)
        assert "Source Sans Pro" in guide
        assert "Playfair Display" in guide

    def test_aesthetic_formatting(self, sample_config):
        builder = BrandStyleGuideBuilder()
        builder._api_key = ""
        guide = builder.build_style_guide(sample_config)
        assert "minimalist" in guide
        assert "glass" in guide

    def test_synthesis_when_api_available(self, sample_config):
        builder = BrandStyleGuideBuilder()
        builder._api_key = "test-key"

        # Mock the HTTP call
        with patch.object(builder, "_synthesize_guide", return_value="Synthesized style guide prose."):
            guide = builder.build_style_guide(sample_config)
            assert guide == "Synthesized style guide prose."

    def test_synthesis_failure_falls_back(self, sample_config):
        builder = BrandStyleGuideBuilder()
        builder._api_key = "test-key"

        with patch.object(builder, "_synthesize_guide", return_value=None):
            guide = builder.build_style_guide(sample_config)
            assert "Deep Blue" in guide  # Falls back to structured
