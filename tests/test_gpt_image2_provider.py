"""Tests for GPT Image 2 provider."""
from __future__ import annotations

import os
from unittest.mock import patch, MagicMock

import pytest

from brandmint.core.providers.gpt_image2_provider import GptImage2Provider
from brandmint.core.providers import get_provider, get_available_providers


class TestGptImage2ProviderAvailability:
    """Test provider availability checks."""

    @patch("brandmint.core.providers.gpt_image2_provider.shutil.which")
    @patch("brandmint.core.providers.gpt_image2_provider.os.access")
    @patch("brandmint.core.providers.gpt_image2_provider.Path.is_file")
    def test_available_when_all_deps_present(self, mock_is_file, mock_access, mock_which):
        mock_which.return_value = "/usr/bin/codex"
        mock_access.return_value = True
        mock_is_file.return_value = True

        provider = GptImage2Provider()
        assert provider.is_available()

    @patch("brandmint.core.providers.gpt_image2_provider.shutil.which")
    def test_not_available_when_codex_missing(self, mock_which):
        mock_which.return_value = None

        provider = GptImage2Provider()
        assert not provider.is_available()


class TestGptImage2ProviderGeneration:
    """Test image generation."""

    @patch("brandmint.core.providers.gpt_image2_provider.subprocess.run")
    @patch("brandmint.core.providers.gpt_image2_provider.shutil.which")
    @patch("brandmint.core.providers.gpt_image2_provider.os.access")
    @patch("brandmint.core.providers.gpt_image2_provider.Path.is_file")
    @patch("brandmint.core.providers.gpt_image2_provider.Path.exists")
    def test_successful_generation(self, mock_exists, mock_is_file, mock_access, mock_which, mock_run):
        mock_which.return_value = "/usr/bin/codex"
        mock_access.return_value = True
        mock_is_file.return_value = True
        mock_exists.return_value = True
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        provider = GptImage2Provider()
        result = provider.generate(
            prompt="A brand logo",
            model="nano-banana-pro",
            output_path="/tmp/test.png",
        )

        assert result.success
        assert result.model_used == "gpt-image-2"
        assert result.provider == "gpt-image2"

    @patch("brandmint.core.providers.gpt_image2_provider.subprocess.run")
    @patch("brandmint.core.providers.gpt_image2_provider.shutil.which")
    @patch("brandmint.core.providers.gpt_image2_provider.os.access")
    @patch("brandmint.core.providers.gpt_image2_provider.Path.is_file")
    def test_failed_generation(self, mock_is_file, mock_access, mock_which, mock_run):
        mock_which.return_value = "/usr/bin/codex"
        mock_access.return_value = True
        mock_is_file.return_value = True
        mock_run.return_value = MagicMock(returncode=5, stdout="", stderr="codex exec failed")

        provider = GptImage2Provider()
        result = provider.generate(
            prompt="A brand logo",
            model="nano-banana-pro",
            output_path="/tmp/test.png",
        )

        assert not result.success
        assert "codex exec failed" in result.error.lower() or "exit code 5" in result.error.lower()

    @patch("brandmint.core.providers.gpt_image2_provider.subprocess.run")
    @patch("brandmint.core.providers.gpt_image2_provider.shutil.which")
    @patch("brandmint.core.providers.gpt_image2_provider.os.access")
    @patch("brandmint.core.providers.gpt_image2_provider.Path.is_file")
    @patch("brandmint.core.providers.gpt_image2_provider.Path.exists")
    def test_local_reference_paths_are_passed_to_gen_script(self, mock_exists, mock_is_file, mock_access, mock_which, mock_run):
        mock_which.return_value = "/usr/bin/codex"
        mock_access.return_value = True
        mock_is_file.return_value = True
        mock_exists.return_value = True
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        provider = GptImage2Provider()
        provider.generate(
            prompt="A brand logo",
            model="gpt-image-2",
            output_path="/tmp/test.png",
            image_urls=["/tmp/ref-a.png", "https://example.com/ref-b.png"],
        )

        cmd = mock_run.call_args.args[0]
        assert "--ref" in cmd
        assert "/tmp/ref-a.png" in cmd
        assert "https://example.com/ref-b.png" not in cmd


class TestGptImage2ProviderCost:
    """Test cost estimation."""

    def test_zero_cost(self):
        provider = GptImage2Provider()
        assert provider.estimate_cost("nano-banana-pro") == 0.0
        assert provider.estimate_cost("gpt-image-2") == 0.0


class TestGptImage2ProviderCapabilities:
    """Test provider capabilities."""

    def test_supports_model(self):
        provider = GptImage2Provider()
        assert provider.supports_model("nano-banana-pro")
        assert provider.supports_model("gpt-image-2")
        assert provider.supports_model("any-model")

    def test_capabilities(self):
        provider = GptImage2Provider()
        caps = provider.get_capabilities()
        assert caps["supports_image_reference"] is True
        assert caps["supports_negative_prompt"] is False
        assert caps["max_prompt_length"] == 2000


class TestGptImage2ProviderFactory:
    """Test provider factory integration."""

    def test_provider_registered(self):
        from brandmint.core.providers import PROVIDERS
        assert "gpt-image2" in PROVIDERS

    def test_default_fallback_includes_gpt_image2(self):
        from brandmint.core.providers import DEFAULT_FALLBACK_CHAIN
        assert "gpt-image2" in DEFAULT_FALLBACK_CHAIN
        # Should be first in fallback chain (free with subscription)
        assert DEFAULT_FALLBACK_CHAIN[0] == "gpt-image2"
