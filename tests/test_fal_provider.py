"""Tests for FAL provider — flux-fill (inpainting) and flux-canny (edge-guided).

TDD: Written BEFORE implementation.  Red → Green → Refactor.
"""

import json

from brandmint.core.providers.base import ImageProvider
from brandmint.core.providers.fal_provider import FalProvider
from brandmint.core.providers.model_mapping import (
    LOGICAL_MODELS,
    MODEL_MAPPING,
    COST_ESTIMATES,
    PROVIDER_CAPABILITIES,
    get_model_id,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _Response:
    """Fake urllib response for monkeypatching."""

    def __init__(self, body: bytes):
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


# ---------------------------------------------------------------------------
# 1. model_mapping.py tests
# ---------------------------------------------------------------------------


class TestModelMappingExtensions:
    """Verify flux-fill and flux-canny are registered correctly."""

    def test_logical_models_contains_flux_fill(self):
        assert "flux-fill" in LOGICAL_MODELS

    def test_logical_models_contains_flux_canny(self):
        assert "flux-canny" in LOGICAL_MODELS

    def test_fal_mapping_flux_fill(self):
        assert MODEL_MAPPING["fal"]["flux-fill"] == "fal-ai/flux-pro/v1/fill"

    def test_fal_mapping_flux_canny(self):
        assert MODEL_MAPPING["fal"]["flux-canny"] == "fal-ai/flux-pro/v1/canny"

    def test_get_model_id_flux_fill(self):
        assert get_model_id("fal", "flux-fill") == "fal-ai/flux-pro/v1/fill"

    def test_get_model_id_flux_canny(self):
        assert get_model_id("fal", "flux-canny") == "fal-ai/flux-pro/v1/canny"

    def test_cost_estimates_flux_fill(self):
        assert "flux-fill" in COST_ESTIMATES["fal"]
        assert isinstance(COST_ESTIMATES["fal"]["flux-fill"], float)

    def test_cost_estimates_flux_canny(self):
        assert "flux-canny" in COST_ESTIMATES["fal"]
        assert isinstance(COST_ESTIMATES["fal"]["flux-canny"], float)

    def test_provider_capabilities_inpainting(self):
        assert PROVIDER_CAPABILITIES["fal"]["supports_inpainting"] is True

    def test_provider_capabilities_edge_guided(self):
        assert PROVIDER_CAPABILITIES["fal"]["supports_edge_guided"] is True


# ---------------------------------------------------------------------------
# 2. base.py capability methods
# ---------------------------------------------------------------------------


class TestBaseCapabilityMethods:
    """Verify new capability query methods on ImageProvider & FalProvider."""

    def test_fal_supports_inpainting(self):
        provider = FalProvider()
        assert provider.supports_inpainting() is True

    def test_fal_supports_edge_guided(self):
        provider = FalProvider()
        assert provider.supports_edge_guided() is True

    def test_default_supports_inpainting_is_false(self):
        """ImageProvider.supports_inpainting() defaults to False."""
        assert ImageProvider.supports_inpainting.__doc__ is not None or True
        # We can't instantiate ABC directly; test via a minimal concrete stub.
        from brandmint.core.providers.openrouter_provider import OpenRouterProvider

        p = OpenRouterProvider()
        assert p.supports_inpainting() is False

    def test_default_supports_edge_guided_is_false(self):
        from brandmint.core.providers.openrouter_provider import OpenRouterProvider

        p = OpenRouterProvider()
        assert p.supports_edge_guided() is False


# ---------------------------------------------------------------------------
# 3. FalProvider._build_arguments tests
# ---------------------------------------------------------------------------


class TestBuildArgumentsFluxFill:
    """Verify _build_arguments produces correct payload for flux-fill."""

    def setup_method(self):
        self.provider = FalProvider()
        self.model_id = "fal-ai/flux-pro/v1/fill"

    def test_basic_payload(self):
        args = self.provider._build_arguments(
            model_id=self.model_id,
            prompt="fill the sky with stars",
            width=1024,
            height=1024,
            image_url="https://example.com/scene.png",
            negative_prompt="",
            guidance_scale=7.5,
            num_steps=50,
            mask_url="https://example.com/mask.png",
        )

        assert args["prompt"] == "fill the sky with stars"
        assert args["image"] == "https://example.com/scene.png"
        assert args["mask"] == "https://example.com/mask.png"
        assert args["output_format"] == "png"

    def test_seed_forwarded(self):
        args = self.provider._build_arguments(
            model_id=self.model_id,
            prompt="test",
            width=1024,
            height=1024,
            image_url="https://example.com/scene.png",
            negative_prompt="",
            guidance_scale=7.5,
            num_steps=50,
            mask_url="https://example.com/mask.png",
            seed=42,
        )
        assert args["seed"] == 42

    def test_no_seed_when_not_provided(self):
        args = self.provider._build_arguments(
            model_id=self.model_id,
            prompt="test",
            width=1024,
            height=1024,
            image_url="https://example.com/scene.png",
            negative_prompt="",
            guidance_scale=7.5,
            num_steps=50,
            mask_url="https://example.com/mask.png",
        )
        assert "seed" not in args

    def test_missing_mask_url_raises(self):
        """flux-fill requires mask_url — should error cleanly."""
        import pytest

        with pytest.raises(ValueError, match="mask_url"):
            self.provider._build_arguments(
                model_id=self.model_id,
                prompt="test",
                width=1024,
                height=1024,
                image_url="https://example.com/scene.png",
                negative_prompt="",
                guidance_scale=7.5,
                num_steps=50,
            )

    def test_missing_image_url_raises(self):
        """flux-fill requires image_url — should error cleanly."""
        import pytest

        with pytest.raises(ValueError, match="image_url"):
            self.provider._build_arguments(
                model_id=self.model_id,
                prompt="test",
                width=1024,
                height=1024,
                image_url=None,
                negative_prompt="",
                guidance_scale=7.5,
                num_steps=50,
                mask_url="https://example.com/mask.png",
            )


class TestBuildArgumentsFluxCanny:
    """Verify _build_arguments produces correct payload for flux-canny."""

    def setup_method(self):
        self.provider = FalProvider()
        self.model_id = "fal-ai/flux-pro/v1/canny"

    def test_basic_payload(self):
        args = self.provider._build_arguments(
            model_id=self.model_id,
            prompt="a futuristic city",
            width=1024,
            height=1024,
            image_url="https://example.com/edges.png",
            negative_prompt="",
            guidance_scale=30.0,
            num_steps=50,
        )

        assert args["prompt"] == "a futuristic city"
        assert args["control_image"] == "https://example.com/edges.png"
        assert args["output_format"] == "png"
        assert args["guidance_scale"] == 30.0
        assert args["num_inference_steps"] == 50

    def test_custom_guidance_and_steps(self):
        args = self.provider._build_arguments(
            model_id=self.model_id,
            prompt="test",
            width=1024,
            height=1024,
            image_url="https://example.com/edges.png",
            negative_prompt="",
            guidance_scale=15.0,
            num_steps=28,
        )
        assert args["guidance_scale"] == 15.0
        assert args["num_inference_steps"] == 28

    def test_seed_forwarded(self):
        args = self.provider._build_arguments(
            model_id=self.model_id,
            prompt="test",
            width=1024,
            height=1024,
            image_url="https://example.com/edges.png",
            negative_prompt="",
            guidance_scale=30.0,
            num_steps=50,
            seed=99,
        )
        assert args["seed"] == 99

    def test_missing_control_image_raises(self):
        """flux-canny requires image_url as control_image — should error."""
        import pytest

        with pytest.raises(ValueError, match="image_url.*control_image"):
            self.provider._build_arguments(
                model_id=self.model_id,
                prompt="test",
                width=1024,
                height=1024,
                image_url=None,
                negative_prompt="",
                guidance_scale=30.0,
                num_steps=50,
            )


# ---------------------------------------------------------------------------
# 4. End-to-end generate() integration (queue submit → poll → download)
# ---------------------------------------------------------------------------


class TestFalProviderFluxFillGenerate:
    """End-to-end generate() with mocked HTTP for flux-fill."""

    def test_flux_fill_success(self, monkeypatch, tmp_path):
        monkeypatch.setenv("FAL_KEY", "fal_test_key")
        monkeypatch.setattr(
            "brandmint.core.providers.fal_provider.time.sleep", lambda _: None
        )

        call_log = {"submit": 0, "poll": 0}

        def fake_urlopen(req, timeout=0):
            url = req.full_url if hasattr(req, "full_url") else str(req)
            method = req.get_method() if hasattr(req, "get_method") else "GET"

            # Queue submit
            if "fal-ai/flux-pro/v1/fill" in url and method == "POST":
                call_log["submit"] += 1
                return _Response(
                    json.dumps(
                        {
                            "request_id": "fill-req-001",
                            "status_url": "https://queue.fal.run/fal-ai/flux-pro/v1/fill/requests/fill-req-001/status",
                            "response_url": "https://queue.fal.run/fal-ai/flux-pro/v1/fill/requests/fill-req-001",
                        }
                    ).encode()
                )

            # Poll status
            if "fill-req-001/status" in url and method == "GET":
                call_log["poll"] += 1
                if call_log["poll"] == 1:
                    return _Response(
                        json.dumps({"status": "IN_PROGRESS"}).encode()
                    )
                return _Response(
                    json.dumps(
                        {
                            "status": "COMPLETED",
                            "response_url": "https://queue.fal.run/fal-ai/flux-pro/v1/fill/requests/fill-req-001",
                        }
                    ).encode()
                )

            # Fetch result
            if "fill-req-001" in url and method == "GET" and "status" not in url:
                return _Response(
                    json.dumps(
                        {"images": [{"url": "https://cdn.fal.run/filled.png"}]}
                    ).encode()
                )

            # Image download
            if url == "https://cdn.fal.run/filled.png":
                return _Response(b"\x89PNG\r\n\x1a\nfakepng")

            raise AssertionError(f"Unexpected request: {method} {url}")

        monkeypatch.setattr(
            "brandmint.core.providers.fal_provider.urllib.request.urlopen",
            fake_urlopen,
        )

        output = tmp_path / "filled.png"
        provider = FalProvider()
        result = provider.generate(
            prompt="add flowers to the garden",
            model="flux-fill",
            output_path=str(output),
            image_url="https://example.com/garden.png",
            mask_url="https://example.com/garden_mask.png",
        )

        assert result.success is True
        assert result.provider == "FAL.AI"
        assert result.model_used == "fal-ai/flux-pro/v1/fill"
        assert result.image_url == "https://cdn.fal.run/filled.png"
        assert output.exists()
        assert call_log["submit"] == 1
        assert call_log["poll"] >= 2


class TestFalProviderFluxCannyGenerate:
    """End-to-end generate() with mocked HTTP for flux-canny."""

    def test_flux_canny_success(self, monkeypatch, tmp_path):
        monkeypatch.setenv("FAL_KEY", "fal_test_key")
        monkeypatch.setattr(
            "brandmint.core.providers.fal_provider.time.sleep", lambda _: None
        )

        call_log = {"submit": 0, "poll": 0}

        def fake_urlopen(req, timeout=0):
            url = req.full_url if hasattr(req, "full_url") else str(req)
            method = req.get_method() if hasattr(req, "get_method") else "GET"

            # Queue submit
            if "fal-ai/flux-pro/v1/canny" in url and method == "POST":
                call_log["submit"] += 1
                return _Response(
                    json.dumps(
                        {
                            "request_id": "canny-req-001",
                            "status_url": "https://queue.fal.run/fal-ai/flux-pro/v1/canny/requests/canny-req-001/status",
                            "response_url": "https://queue.fal.run/fal-ai/flux-pro/v1/canny/requests/canny-req-001",
                        }
                    ).encode()
                )

            # Poll status
            if "canny-req-001/status" in url and method == "GET":
                call_log["poll"] += 1
                if call_log["poll"] == 1:
                    return _Response(
                        json.dumps({"status": "IN_PROGRESS"}).encode()
                    )
                return _Response(
                    json.dumps(
                        {
                            "status": "COMPLETED",
                            "response_url": "https://queue.fal.run/fal-ai/flux-pro/v1/canny/requests/canny-req-001",
                        }
                    ).encode()
                )

            # Fetch result
            if "canny-req-001" in url and method == "GET" and "status" not in url:
                return _Response(
                    json.dumps(
                        {"images": [{"url": "https://cdn.fal.run/canny_out.png"}]}
                    ).encode()
                )

            # Image download
            if url == "https://cdn.fal.run/canny_out.png":
                return _Response(b"\x89PNG\r\n\x1a\nfakepng")

            raise AssertionError(f"Unexpected request: {method} {url}")

        monkeypatch.setattr(
            "brandmint.core.providers.fal_provider.urllib.request.urlopen",
            fake_urlopen,
        )

        output = tmp_path / "canny_out.png"
        provider = FalProvider()
        result = provider.generate(
            prompt="futuristic cityscape",
            model="flux-canny",
            output_path=str(output),
            image_url="https://example.com/edges.png",
            guidance_scale=30.0,
            num_steps=50,
        )

        assert result.success is True
        assert result.provider == "FAL.AI"
        assert result.model_used == "fal-ai/flux-pro/v1/canny"
        assert result.image_url == "https://cdn.fal.run/canny_out.png"
        assert output.exists()
        assert call_log["submit"] == 1
        assert call_log["poll"] >= 2


class TestFalProviderFluxFillMissingKey:
    """flux-fill gracefully fails when FAL_KEY is missing."""

    def test_missing_key_returns_error(self, monkeypatch, tmp_path):
        monkeypatch.delenv("FAL_KEY", raising=False)
        provider = FalProvider()
        result = provider.generate(
            prompt="test",
            model="flux-fill",
            output_path=str(tmp_path / "out.png"),
            image_url="https://example.com/scene.png",
            mask_url="https://example.com/mask.png",
        )
        assert result.success is False
        assert "FAL_KEY" in (result.error or "")


# ---------------------------------------------------------------------------
# 5. Existing model behavior preserved (regression guard)
# ---------------------------------------------------------------------------


class TestExistingModelsUnchanged:
    """Verify existing models still produce identical payloads."""

    def setup_method(self):
        self.provider = FalProvider()

    def test_flux_default_payload(self):
        args = self.provider._build_arguments(
            model_id="fal-ai/flux-2-pro",
            prompt="a brand logo",
            width=1024,
            height=1024,
            image_url=None,
            negative_prompt="",
            guidance_scale=7.5,
            num_steps=50,
        )
        assert args["prompt"] == "a brand logo"
        assert args["num_inference_steps"] == 50
        assert args["guidance_scale"] == 7.5

    def test_nano_banana_payload(self):
        args = self.provider._build_arguments(
            model_id="fal-ai/nano-banana-pro",
            prompt="stylish hero",
            width=1024,
            height=1024,
            image_url=None,
            negative_prompt="",
            guidance_scale=7.5,
            num_steps=50,
        )
        assert args["prompt"] == "stylish hero"
        assert "aspect_ratio" in args

    def test_recraft_payload(self):
        args = self.provider._build_arguments(
            model_id="fal-ai/recraft/v3/text-to-image",
            prompt="illustration",
            width=1024,
            height=1024,
            image_url=None,
            negative_prompt="",
            guidance_scale=7.5,
            num_steps=50,
            colors=["#243984", "#E82F89"],
        )
        assert args["prompt"] == "illustration"
        assert args["style"] == "digital_illustration"
        assert args["colors"] == [
            {"r": 36, "g": 57, "b": 132},
            {"r": 232, "g": 47, "b": 137},
        ]
