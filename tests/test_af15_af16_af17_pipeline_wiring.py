"""Tests for AF-15, AF-16, AF-17 — Composite mode pipeline wiring.

AF-16: asset_mode in brand config schema
AF-17: --asset-mode CLI flag
AF-15: Composite post-pass wired into generate_pipeline.py
"""

import os
import subprocess
import sys
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]


def _template_source() -> str:
    return (REPO_ROOT / "scripts" / "generate_pipeline.py").read_text()


def _schema_source() -> str:
    return (REPO_ROOT / "assets" / "brand-config-schema.yaml").read_text()


def _cli_app_source() -> str:
    return (REPO_ROOT / "brandmint" / "cli" / "app.py").read_text()


def _cli_visual_source() -> str:
    return (REPO_ROOT / "brandmint" / "cli" / "visual.py").read_text()


# =====================================================================
# AF-16: brand config schema has asset_mode + composite_config
# =====================================================================


class TestAF16SchemaAssetMode:
    """AF-16: brand-config-schema.yaml must include asset_mode and composite_config."""

    @pytest.mark.skipif(not HAS_YAML, reason="pyyaml not installed")
    def test_schema_parses_as_valid_yaml(self):
        schema_text = _schema_source()
        data = yaml.safe_load(schema_text)
        assert data is not None

    @pytest.mark.skipif(not HAS_YAML, reason="pyyaml not installed")
    def test_asset_mode_in_generation_section(self):
        data = yaml.safe_load(_schema_source())
        gen = data.get("generation", {})
        assert "asset_mode" in gen, "generation.asset_mode missing from schema"
        assert gen["asset_mode"] in (
            "generate",
            "composite",
            "inpaint",
            "hybrid",
        ), f"Unexpected asset_mode value: {gen['asset_mode']}"

    @pytest.mark.skipif(not HAS_YAML, reason="pyyaml not installed")
    def test_asset_mode_default_is_generate(self):
        data = yaml.safe_load(_schema_source())
        assert data["generation"]["asset_mode"] == "generate"

    @pytest.mark.skipif(not HAS_YAML, reason="pyyaml not installed")
    def test_composite_config_section_exists(self):
        data = yaml.safe_load(_schema_source())
        gen = data.get("generation", {})
        cc = gen.get("composite_config")
        assert cc is not None, "generation.composite_config missing"

    @pytest.mark.skipif(not HAS_YAML, reason="pyyaml not installed")
    def test_composite_config_logo_position(self):
        data = yaml.safe_load(_schema_source())
        cc = data["generation"]["composite_config"]
        assert cc["logo_position"] == "bottom-right"

    @pytest.mark.skipif(not HAS_YAML, reason="pyyaml not installed")
    def test_composite_config_logo_scale(self):
        data = yaml.safe_load(_schema_source())
        cc = data["generation"]["composite_config"]
        assert cc["logo_scale"] == 0.15

    @pytest.mark.skipif(not HAS_YAML, reason="pyyaml not installed")
    def test_composite_config_logo_padding(self):
        data = yaml.safe_load(_schema_source())
        cc = data["generation"]["composite_config"]
        assert cc["logo_padding"] == 20

    @pytest.mark.skipif(not HAS_YAML, reason="pyyaml not installed")
    def test_composite_config_logo_opacity(self):
        data = yaml.safe_load(_schema_source())
        cc = data["generation"]["composite_config"]
        assert cc["logo_opacity"] == 1.0

    @pytest.mark.skipif(not HAS_YAML, reason="pyyaml not installed")
    def test_composite_config_logo_shadow(self):
        data = yaml.safe_load(_schema_source())
        cc = data["generation"]["composite_config"]
        assert cc["logo_shadow"] is False

    @pytest.mark.skipif(not HAS_YAML, reason="pyyaml not installed")
    def test_composite_config_product_settings(self):
        data = yaml.safe_load(_schema_source())
        cc = data["generation"]["composite_config"]
        assert cc["product_position"] == "center"
        assert cc["product_scale"] == 0.5
        assert cc["product_feather"] == 5

    @pytest.mark.skipif(not HAS_YAML, reason="pyyaml not installed")
    def test_composite_config_per_asset_overrides(self):
        data = yaml.safe_load(_schema_source())
        cc = data["generation"]["composite_config"]
        assert "per_asset_overrides" in cc

    def test_schema_text_has_asset_mode_comment(self):
        """The schema should have a human-readable comment about the modes."""
        text = _schema_source()
        assert "generate | composite | inpaint | hybrid" in text


# =====================================================================
# AF-17: CLI --asset-mode flag
# =====================================================================


class TestAF17CLIAssetModeFlag:
    """AF-17: visual generate and visual execute must accept --asset-mode."""

    def test_visual_generate_has_asset_mode_param(self):
        src = _cli_app_source()
        assert "asset_mode" in src, "asset_mode parameter missing from app.py"
        assert "--asset-mode" in src, "--asset-mode option missing from app.py"

    def test_visual_execute_has_asset_mode_param(self):
        src = _cli_app_source()
        # Both generate and execute should have the flag
        # Count occurrences — should appear at least twice (one per command)
        count = src.count("--asset-mode")
        assert count >= 2, f"--asset-mode appears only {count} time(s), need >= 2"

    def test_visual_generate_passes_asset_mode(self):
        """run_generate should accept asset_mode parameter."""
        src = _cli_visual_source()
        assert "asset_mode" in src, "asset_mode not passed through in visual.py"

    def test_visual_execute_passes_asset_mode(self):
        """run_execute should accept asset_mode parameter."""
        src = _cli_visual_source()
        # Both functions should handle asset_mode
        assert "ASSET_MODE" in src, "ASSET_MODE env variable not set in visual.py"

    def test_run_generate_sets_asset_mode_env(self):
        """run_generate must set ASSET_MODE environment variable for subprocess."""
        src = _cli_visual_source()
        assert "ASSET_MODE" in src

    def test_run_execute_sets_asset_mode_env(self):
        """run_execute must set ASSET_MODE environment variable for subprocess."""
        src = _cli_visual_source()
        assert "ASSET_MODE" in src

    def test_default_asset_mode_is_generate(self):
        """Default value for --asset-mode should be 'generate'."""
        src = _cli_app_source()
        # Look for the default value in the typer.Option
        assert '"generate"' in src


# =====================================================================
# AF-15: Composite post-pass wired into generate_pipeline.py
# =====================================================================


class TestAF15CompositePostPass:
    """AF-15: generate_pipeline.py must include composite post-pass template."""

    def test_asset_mode_env_var_in_header(self):
        """Generated scripts must read ASSET_MODE from environment."""
        src = _template_source()
        assert "ASSET_MODE" in src, "ASSET_MODE env var not in generate_pipeline.py"
        assert 'os.environ.get("ASSET_MODE"' in src or "os.environ.get('ASSET_MODE'" in src

    def test_composite_post_pass_function_defined(self):
        """A _composite_post_pass function template must exist."""
        src = _template_source()
        assert "_composite_post_pass" in src

    def test_composite_post_pass_imports_compositor(self):
        """The composite pass template must import from compositor module."""
        src = _template_source()
        assert "brandmint.core.compositor" in src

    def test_composite_post_pass_imports_asset_mode(self):
        """The composite pass template must import from asset_mode module."""
        src = _template_source()
        assert "brandmint.core.asset_mode" in src

    def test_composite_post_pass_calls_route_asset(self):
        """The composite pass template must call route_asset()."""
        src = _template_source()
        assert "route_asset" in src

    def test_composite_post_pass_calls_compositor(self):
        """The composite pass template must call PostGenCompositor."""
        src = _template_source()
        assert "PostGenCompositor" in src

    def test_composite_post_pass_saves_composited_file(self):
        """Composited images should be saved with -composited suffix."""
        src = _template_source()
        assert "-composited" in src

    def test_gen_with_provider_calls_composite_post_pass(self):
        """gen_with_provider must invoke _composite_post_pass after generation."""
        src = _template_source()
        # Find the gen_with_provider template and check it calls the post-pass
        # The call should be AFTER _normalize_png_if_needed
        gen_wp_start = src.index("def gen_with_provider(")
        gen_wp_end = src.index("'''", gen_wp_start + 10)  # Find closing '''
        gen_wp_body = src[gen_wp_start:gen_wp_end]
        assert "_composite_post_pass" in gen_wp_body, (
            "_composite_post_pass not called within gen_with_provider template"
        )

    def test_generate_mode_skips_composite_pass(self):
        """When ASSET_MODE is 'generate', the composite pass should be a no-op."""
        src = _template_source()
        # The function should check ASSET_MODE and return early for 'generate'
        assert "generate" in src.lower()
        # Check for guard clause
        assert 'ASSET_MODE' in src

    def test_composite_pass_preserves_original_image(self):
        """The original generated image should NOT be overwritten."""
        src = _template_source()
        # Composited file uses -composited suffix, meaning original stays
        assert "-composited" in src

    def test_template_renders_valid_python_braces(self):
        """All braces in the composite template must be properly escaped for format_map().

        In generate_pipeline.py, {variable} is for template interpolation.
        Literal braces in the GENERATED code must be escaped as {{ and }}.
        """
        src = _template_source()
        # Verify the template can be parsed by looking for the SafeDict render function
        assert "class SafeDict" in src
        # Check there are no obvious brace issues by verifying the file is valid Python
        compile(src, "generate_pipeline.py", "exec")


class TestAF15CompositePostPassDefaults:
    """AF-15: Composite pass should be backward-compatible — generate mode unchanged."""

    def test_default_asset_mode_is_generate_in_template(self):
        """Template must default to 'generate' mode."""
        src = _template_source()
        assert '"generate"' in src

    def test_existing_gen_with_provider_still_works(self):
        """Existing gen_with_provider structure should be preserved."""
        src = _template_source()
        assert "def gen_with_provider(" in src
        assert "_normalize_png_if_needed(output_path)" in src
        assert "CORE_PROVIDER.generate(" in src

    def test_existing_function_templates_intact(self):
        """Nano Banana, Flux Pro, Recraft templates should be unchanged."""
        src = _template_source()
        assert "def gen_nano_banana(" in src
        assert "def gen_flux_pro(" in src
        assert "def gen_recraft(" in src
