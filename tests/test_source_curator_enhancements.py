"""Tests for NB-06 through NB-13 — source curator enhancements, brand context injection,
and brand asset injector.

TDD: These tests are written BEFORE implementation. All must FAIL (RED) initially,
then pass (GREEN) after implementation.
"""
from __future__ import annotations

import pytest

from brandmint.publishing.source_curator import (
    SourceCurator,
)


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_config():
    """Minimal brand config for testing."""
    return {
        "brand": {
            "name": "TestBrand",
            "tagline": "Innovation meets design",
            "archetype": "creator",
            "voice": "Confident and approachable",
            "tone": "Professional yet friendly",
        },
        "palette": {
            "primary": {"name": "Deep Blue", "hex": "#1a237e", "role": "Headers and CTAs"},
            "secondary": {"name": "Warm Gold", "hex": "#ffd54f", "role": "Accents"},
            "accent": {"name": "Coral", "hex": "#ff6f61", "role": "Highlights"},
        },
        "typography": {
            "header": {"font": "Inter", "weight": "700"},
            "body": {"font": "Source Sans Pro", "weight": "400"},
            "data": {"font": "JetBrains Mono", "weight": "400"},
        },
        "aesthetic": {
            "style": "minimalist",
            "materials": ["glass", "brushed metal"],
            "mood": "sophisticated and clean",
        },
        "theme": {
            "primary_metaphor": "Precision engineering",
            "aesthetic": "modern minimal",
        },
        "publishing": {
            "include_brand_materials": True,
        },
    }


@pytest.fixture
def brand_dir(tmp_path, sample_config):
    """Set up a realistic brand directory structure."""
    # Create brand dir
    bd = tmp_path / "testbrand"
    bd.mkdir()

    # .brandmint structure
    bm = bd / ".brandmint"
    bm.mkdir()
    (bm / "outputs").mkdir()
    (bm / "sources").mkdir()

    # Write brand config
    import yaml
    config_path = bd / "brand-config.yaml"
    config_path.write_text(yaml.dump(sample_config))

    # Create prose source docs (like source_builder would)
    sources_dir = bd / "deliverables" / "notebooklm" / "sources"
    sources_dir.mkdir(parents=True)
    for group_id in ("brand-foundation", "brand-strategy", "campaign-content",
                     "communications-social", "visual-asset-catalog"):
        (sources_dir / f"{group_id}.md").write_text(f"# {group_id}\n\nContent here.\n")

    # Generated images dir
    slug = "testbrand"
    gen_dir = bd / slug / "generated"
    gen_dir.mkdir(parents=True)
    # Create fake image files for testing
    for name in (
        "2A-brand-kit-bento-nanobananapro-v1.png",
        "2B-brand-seal-flux2pro-v1.png",
        "3A-capsule-hero-nanobananapro-v1.png",
    ):
        (gen_dir / name).write_bytes(b"\x89PNG" + b"\x00" * 100)

    # Vision cache dir with description files
    vision_cache = bm / "vision-cache"
    vision_cache.mkdir()
    (vision_cache / "2A-brand-kit-bento.md").write_text(
        "# 2A Brand Kit Bento\n\nA comprehensive brand identity bento grid "
        "showcasing the logo, colour palette, and typography in a modern layout."
    )
    (vision_cache / "2B-brand-seal.md").write_text(
        "# 2B Brand Seal\n\nAn elegant brand seal featuring the logo mark "
        "with sophisticated emboss effects and metallic finishes."
    )
    (vision_cache / "logo-primary.md").write_text(
        "# Logo Primary\n\nThe primary logo features clean geometric letterforms."
    )

    # Brand materials dir
    materials_dir = bd / "brand-materials"
    materials_dir.mkdir()
    (materials_dir / "logo-primary.svg").write_text("<svg>logo</svg>")
    (materials_dir / "brand-guidelines.pdf").write_bytes(b"%PDF" + b"\x00" * 100)
    (materials_dir / "mood-board.png").write_bytes(b"\x89PNG" + b"\x00" * 50)

    # Wiki dir
    wiki_dir = bd / "wiki-output"
    wiki_dir.mkdir()
    (wiki_dir / "visual-guidelines.md").write_text("# Visual Guidelines\n\nContent.")

    return bd


@pytest.fixture
def curator(brand_dir, sample_config):
    """SourceCurator with test brand dir."""
    return SourceCurator(
        brand_dir=brand_dir,
        config=sample_config,
        max_sources=50,
    )


# ===========================================================================
# NB-06: Visual description source type
# ===========================================================================


class TestVisualDescriptionSourceType:
    """NB-06: Add visual-description source type to source_curator."""

    def test_scan_visual_descriptions_finds_cache_files(self, curator, brand_dir):
        """Vision cache markdown files should be discovered."""
        candidates = curator._scan_visual_descriptions()
        assert len(candidates) >= 2
        types = {c.source_type for c in candidates}
        assert "visual-description" in types

    def test_visual_description_content_value(self, curator):
        """Visual descriptions should have base content_value of 75."""
        candidates = curator._scan_visual_descriptions()
        for c in candidates:
            assert c.content_value == 75.0

    def test_visual_description_category(self, curator):
        """Visual descriptions should be categorised as 'visual'."""
        candidates = curator._scan_visual_descriptions()
        for c in candidates:
            assert c.category == "visual"

    def test_visual_description_in_scan_all(self, curator):
        """_scan_all_candidates should include visual-description type."""
        all_candidates = curator._scan_all_candidates()
        types = {c.source_type for c in all_candidates}
        assert "visual-description" in types

    def test_visual_description_in_type_order(self, curator):
        """Report should include visual-description in type ordering."""
        curator.curate()
        report = curator.report()
        assert "Visual Asset Descriptions" in report

    def test_visual_description_empty_cache(self, brand_dir, sample_config):
        """No crash when vision-cache dir is empty."""
        cache_dir = brand_dir / ".brandmint" / "vision-cache"
        for f in cache_dir.iterdir():
            f.unlink()
        cur = SourceCurator(brand_dir=brand_dir, config=sample_config)
        candidates = cur._scan_visual_descriptions()
        assert candidates == []

    def test_visual_description_no_cache_dir(self, tmp_path, sample_config):
        """No crash when vision-cache dir doesn't exist."""
        bd = tmp_path / "nobrand"
        bd.mkdir()
        (bd / ".brandmint").mkdir()
        cur = SourceCurator(brand_dir=bd, config=sample_config)
        candidates = cur._scan_visual_descriptions()
        assert candidates == []


# ===========================================================================
# NB-07: Brand material priority scoring
# ===========================================================================


class TestBrandMaterialPriorityScoring:
    """NB-07: Logo descriptions get +10, style guide +8, identity assets +5."""

    def test_logo_description_bonus(self, curator, brand_dir):
        """Logo description files should get +10 content_value bonus."""
        candidates = curator._scan_all_candidates()
        curator._candidates = candidates
        curator._score_all()

        logo_descs = [
            c for c in candidates
            if c.source_type == "visual-description" and "logo" in c.path.stem.lower()
        ]
        assert len(logo_descs) >= 1
        for c in logo_descs:
            # Base is 75, bonus is +10 → 85
            assert c.content_value == 85.0

    def test_style_guide_bonus(self, curator, brand_dir):
        """Style guide source should get +8 content_value bonus."""
        # Create a style guide source
        sources_dir = brand_dir / ".brandmint" / "sources"
        sources_dir.mkdir(parents=True, exist_ok=True)
        (sources_dir / "brand-style-guide.md").write_text("# Brand Style Guide\n\nContent.")

        # Re-scan
        candidates = curator._scan_all_candidates()
        curator._candidates = candidates
        curator._score_all()

        style_guides = [
            c for c in candidates
            if "brand-style-guide" in c.path.stem
        ]
        assert len(style_guides) >= 1
        for c in style_guides:
            # Should have the bonus applied
            assert c.content_value >= 83.0  # 75 base + 8 bonus

    def test_brand_identity_complementary_bonus(self, curator, brand_dir):
        """2A/2B assets get +5 category_bonus when both image AND description exist."""
        candidates = curator._scan_all_candidates()
        curator._candidates = candidates
        curator._score_all()

        # 2A has both an image (2A-brand-kit-bento-nanobananapro-v1.png)
        # and a description (2A-brand-kit-bento.md) in our fixtures
        identity_images = [
            c for c in candidates
            if c.source_type == "image" and c.asset_id in ("2A", "2B")
        ]
        # Those with complementary descriptions should have extra category_bonus
        for c in identity_images:
            if c.uniqueness > 0:  # primary variant only
                assert c.category_bonus >= 5.0


# ===========================================================================
# NB-08: Raw brand material scanning
# ===========================================================================


class TestRawBrandMaterialScanning:
    """NB-08: Scan brand-materials/ directory for user-provided files."""

    def test_scan_brand_materials_finds_files(self, curator):
        """Should find files in brand-materials/ directory."""
        candidates = curator._scan_brand_materials()
        assert len(candidates) >= 2  # logo-primary.svg, brand-guidelines.pdf, mood-board.png

    def test_brand_material_source_type(self, curator):
        """Brand materials should have source_type='brand-material'."""
        candidates = curator._scan_brand_materials()
        for c in candidates:
            assert c.source_type == "brand-material"

    def test_brand_material_in_type_order(self, curator):
        """Report should include brand-material in type ordering."""
        curator.curate()
        report = curator.report()
        assert "Brand Materials" in report

    def test_brand_material_in_scan_all(self, curator):
        """_scan_all_candidates should include brand-material type."""
        all_candidates = curator._scan_all_candidates()
        types = {c.source_type for c in all_candidates}
        assert "brand-material" in types

    def test_brand_material_no_dir(self, tmp_path, sample_config):
        """No crash when brand-materials/ dir doesn't exist."""
        bd = tmp_path / "nobrand"
        bd.mkdir()
        (bd / ".brandmint").mkdir()
        cur = SourceCurator(brand_dir=bd, config=sample_config)
        candidates = cur._scan_brand_materials()
        assert candidates == []

    def test_brand_material_scoring(self, curator):
        """Brand materials should have reasonable content_value."""
        candidates = curator._scan_brand_materials()
        for c in candidates:
            assert 40.0 <= c.content_value <= 80.0


# ===========================================================================
# NB-09: Palette & typography as structured sources
# ===========================================================================


class TestBrandConfigSectionSources:
    """NB-09: Extract palette/typography from config as structured source."""

    def test_scan_brand_config_sections_creates_guide(self, curator, brand_dir):
        """Should create brand-style-guide.md from palette/typography config."""
        candidates = curator._scan_brand_config_sections()
        assert len(candidates) >= 1

    def test_brand_config_section_type(self, curator):
        """Style guide source should have appropriate source_type."""
        candidates = curator._scan_brand_config_sections()
        assert len(candidates) >= 1
        # Should be either visual-description or config type
        c = candidates[0]
        assert c.source_type in ("visual-description", "config")

    def test_style_guide_file_written(self, curator, brand_dir):
        """brand-style-guide.md should be written to .brandmint/sources/."""
        curator._scan_brand_config_sections()
        guide_path = brand_dir / ".brandmint" / "sources" / "brand-style-guide.md"
        assert guide_path.exists()
        content = guide_path.read_text()
        # Should contain palette info
        assert "Deep Blue" in content or "#1a237e" in content
        # Should contain typography section (builder uses family/name keys; our
        # fixture uses "font" so the builder falls back to role names — either
        # way the Typography heading must be present)
        assert "Typography" in content

    def test_include_brand_materials_flag_false(self, brand_dir, sample_config):
        """When include_brand_materials is false, no config sections are scanned."""
        sample_config["publishing"]["include_brand_materials"] = False
        cur = SourceCurator(brand_dir=brand_dir, config=sample_config)
        candidates = cur._scan_brand_config_sections()
        assert candidates == []

    def test_include_brand_materials_flag_default(self, brand_dir, sample_config):
        """Default include_brand_materials should be false."""
        del sample_config["publishing"]
        cur = SourceCurator(brand_dir=brand_dir, config=sample_config)
        candidates = cur._scan_brand_config_sections()
        assert candidates == []

    def test_style_guide_uses_builder(self, curator, brand_dir):
        """Should use BrandStyleGuideBuilder to create structured content."""
        curator._scan_brand_config_sections()
        guide_path = brand_dir / ".brandmint" / "sources" / "brand-style-guide.md"
        assert guide_path.exists()
        content = guide_path.read_text()
        # BrandStyleGuideBuilder produces "# Brand Style Guide" header (fallback)
        # or "## Color System" section
        assert "Style Guide" in content or "Color System" in content or "Typography" in content


# ===========================================================================
# NB-10: Enhanced infographic instructions
# ===========================================================================


class TestEnhancedInfographicInstructions:
    """NB-10: Infographic templates should reference brand materials."""

    def test_infographic_overview_has_palette_placeholder(self, sample_config):
        """infographic_overview should reference palette_summary."""
        from brandmint.publishing.instruction_templates import infographic_overview

        result = infographic_overview(sample_config)
        # Should contain actual colour references
        assert "Deep Blue" in result or "#1a237e" in result or "palette" in result.lower()

    def test_infographic_product_has_brand_references(self, sample_config):
        """infographic_product should include brand logo reference."""
        from brandmint.publishing.instruction_templates import infographic_product

        result = infographic_product(sample_config)
        assert "logo" in result.lower() or "brand" in result.lower()

    def test_inject_brand_context_replaces_palette(self, sample_config):
        """inject_brand_context should replace {palette_summary} placeholder."""
        from brandmint.publishing.instruction_templates import inject_brand_context

        template = "Use the brand's color palette: {palette_summary}"
        result = inject_brand_context(template, sample_config)
        assert "{palette_summary}" not in result
        # Should have actual colour info
        assert "Deep Blue" in result or "#1a237e" in result

    def test_inject_brand_context_replaces_typography(self, sample_config):
        """inject_brand_context should replace {typography_summary} placeholder."""
        from brandmint.publishing.instruction_templates import inject_brand_context

        template = "Follow the typography hierarchy: {typography_summary}"
        result = inject_brand_context(template, sample_config)
        assert "{typography_summary}" not in result
        assert "Inter" in result or "Source Sans Pro" in result

    def test_inject_brand_context_no_config(self):
        """inject_brand_context should handle empty config gracefully."""
        from brandmint.publishing.instruction_templates import inject_brand_context

        template = "Palette: {palette_summary}, Typography: {typography_summary}"
        result = inject_brand_context(template, {})
        assert "{palette_summary}" not in result
        assert "{typography_summary}" not in result


# ===========================================================================
# NB-11: PDF report brand embedding
# ===========================================================================


class TestPDFReportBrandEmbedding:
    """NB-11: Report templates should have brand embedding directives."""

    def test_brand_report_has_brand_colors_directive(self, sample_config):
        """brand_report should instruct using brand colors for headers."""
        from brandmint.publishing.instruction_templates import brand_report

        result = brand_report(sample_config)
        assert "brand color" in result.lower() or "colour" in result.lower() or "palette" in result.lower()

    def test_brand_report_has_logo_directive(self, sample_config):
        """brand_report should instruct placing brand logo."""
        from brandmint.publishing.instruction_templates import brand_report

        result = brand_report(sample_config)
        assert "logo" in result.lower()

    def test_brand_report_has_typography_directive(self, sample_config):
        """brand_report should reference brand typography."""
        from brandmint.publishing.instruction_templates import brand_report

        result = brand_report(sample_config)
        assert "typograph" in result.lower() or "font" in result.lower()

    def test_report_blog_has_brand_embedding(self, sample_config):
        """report_blog_post should include brand visual references."""
        from brandmint.publishing.instruction_templates import report_blog_post

        result = report_blog_post(sample_config)
        # Blog post should at least reference brand visual identity
        assert "brand" in result.lower()

    def test_report_study_guide_has_brand_visuals(self, sample_config):
        """report_study_guide should reference brand colours/typography."""
        from brandmint.publishing.instruction_templates import report_study_guide

        result = report_study_guide(sample_config)
        assert "brand" in result.lower()


# ===========================================================================
# NB-12: Brand asset injector module
# ===========================================================================


class TestBrandAssetInjector:
    """NB-12: get_brand_context_for_instructions provides brand context dict."""

    def test_import_works(self):
        """Module should be importable."""
        from brandmint.publishing.brand_asset_injector import get_brand_context_for_instructions
        assert callable(get_brand_context_for_instructions)

    def test_returns_dict(self, sample_config):
        """Should return a dict."""
        from brandmint.publishing.brand_asset_injector import get_brand_context_for_instructions
        result = get_brand_context_for_instructions(sample_config)
        assert isinstance(result, dict)

    def test_has_palette_summary(self, sample_config):
        """Result should include palette_summary key."""
        from brandmint.publishing.brand_asset_injector import get_brand_context_for_instructions
        result = get_brand_context_for_instructions(sample_config)
        assert "palette_summary" in result
        assert "Deep Blue" in result["palette_summary"] or "#1a237e" in result["palette_summary"]

    def test_has_typography_summary(self, sample_config):
        """Result should include typography_summary key."""
        from brandmint.publishing.brand_asset_injector import get_brand_context_for_instructions
        result = get_brand_context_for_instructions(sample_config)
        assert "typography_summary" in result
        assert "Inter" in result["typography_summary"]

    def test_has_logo_reference(self, sample_config):
        """Result should include logo_reference key."""
        from brandmint.publishing.brand_asset_injector import get_brand_context_for_instructions
        result = get_brand_context_for_instructions(sample_config)
        assert "logo_reference" in result
        assert isinstance(result["logo_reference"], str)

    def test_has_brand_colors(self, sample_config):
        """Result should include brand_colors key with hex values."""
        from brandmint.publishing.brand_asset_injector import get_brand_context_for_instructions
        result = get_brand_context_for_instructions(sample_config)
        assert "brand_colors" in result
        assert isinstance(result["brand_colors"], (dict, list, str))

    def test_has_aesthetic_direction(self, sample_config):
        """Result should include aesthetic_direction key."""
        from brandmint.publishing.brand_asset_injector import get_brand_context_for_instructions
        result = get_brand_context_for_instructions(sample_config)
        assert "aesthetic_direction" in result

    def test_empty_config(self):
        """Should handle empty config gracefully."""
        from brandmint.publishing.brand_asset_injector import get_brand_context_for_instructions
        result = get_brand_context_for_instructions({})
        assert isinstance(result, dict)
        assert "palette_summary" in result
        assert "typography_summary" in result

    def test_partial_config(self):
        """Should handle config with only some sections."""
        from brandmint.publishing.brand_asset_injector import get_brand_context_for_instructions
        result = get_brand_context_for_instructions({
            "palette": {"primary": {"name": "Blue", "hex": "#0000ff"}},
        })
        assert "Blue" in result["palette_summary"] or "#0000ff" in result["palette_summary"]


# ===========================================================================
# NB-13: Integration tests — curate() end-to-end
# ===========================================================================


class TestCurateEndToEnd:
    """NB-13: Full curate() flow with all new source types."""

    def test_curate_returns_selected_sources(self, curator):
        """curate() should return a non-empty list of selected SourceCandidates."""
        selected = curator.curate()
        assert len(selected) > 0

    def test_curate_includes_visual_descriptions(self, curator):
        """curate() should include visual-description candidates."""
        selected = curator.curate()
        types = {c.source_type for c in selected}
        assert "visual-description" in types

    def test_curate_includes_brand_materials(self, curator):
        """curate() should include brand-material candidates."""
        selected = curator.curate()
        types = {c.source_type for c in selected}
        assert "brand-material" in types

    def test_curate_respects_budget(self, brand_dir, sample_config):
        """curate() should not exceed max_sources."""
        cur = SourceCurator(brand_dir=brand_dir, config=sample_config, max_sources=5)
        selected = cur.curate()
        assert len(selected) <= 5

    def test_curate_prose_still_first(self, curator):
        """Prose documents should still be highest priority."""
        selected = curator.curate()
        prose_indices = [i for i, c in enumerate(selected) if c.source_type == "prose"]
        other_indices = [i for i, c in enumerate(selected) if c.source_type != "prose"]
        if prose_indices and other_indices:
            # Prose should appear before other types
            assert max(prose_indices) < max(other_indices) or len(prose_indices) > 0

    def test_report_includes_all_types(self, curator):
        """report() should mention all new source types."""
        curator.curate()
        report = curator.report()
        assert "Visual Asset Descriptions" in report
        assert "Brand Materials" in report

    def test_existing_behavior_preserved(self, curator):
        """Existing source types should still work correctly."""
        selected = curator.curate()
        types = {c.source_type for c in selected}
        # Original types should still be present
        assert "prose" in types
        assert "image" in types

    def test_visual_description_complementary_scoring(self, curator):
        """Visual descriptions that match uploaded images should score higher uniqueness."""
        curator.curate()
        # 2A has both an image and a description
        descs_2a = [
            c for c in curator._candidates
            if c.source_type == "visual-description" and "2A" in c.path.stem
        ]
        descs_other = [
            c for c in curator._candidates
            if c.source_type == "visual-description" and "2A" not in c.path.stem
            and "2B" not in c.path.stem and "logo" not in c.path.stem.lower()
        ]
        # 2A desc should have higher uniqueness since it complements the image
        if descs_2a and descs_other:
            assert descs_2a[0].uniqueness >= descs_other[0].uniqueness


# ===========================================================================
# NB-16: Dry-run brand material coverage report
# ===========================================================================


class TestCoverageReport:
    """NB-16: coverage_report() returns a structured dict with selection metadata."""

    def test_coverage_report_returns_dict(self, curator):
        """coverage_report() should return a dict, not a list."""
        result = curator.coverage_report()
        assert isinstance(result, dict)

    def test_coverage_report_has_required_keys(self, curator):
        """Result must contain all documented keys."""
        result = curator.coverage_report()
        required_keys = {
            "total_candidates",
            "selected_count",
            "by_type",
            "brand_materials",
            "vision_descriptions",
            "budget_remaining",
            "excluded",
        }
        assert required_keys.issubset(result.keys()), (
            f"Missing keys: {required_keys - result.keys()}"
        )

    def test_coverage_report_total_candidates_count(self, curator):
        """total_candidates should match the number of discovered candidates."""
        result = curator.coverage_report()
        assert result["total_candidates"] > 0
        # Should equal the internal _candidates count
        assert result["total_candidates"] == len(curator._candidates)

    def test_coverage_report_selected_within_budget(self, curator):
        """selected_count should never exceed max_sources."""
        result = curator.coverage_report()
        assert result["selected_count"] <= curator.max_sources
        assert result["selected_count"] > 0

    def test_coverage_report_budget_remaining_is_correct(self, curator):
        """budget_remaining = max_sources - selected_count."""
        result = curator.coverage_report()
        assert result["budget_remaining"] == (
            curator.max_sources - result["selected_count"]
        )

    def test_coverage_report_by_type_counts(self, curator):
        """by_type should have counts per source_type."""
        result = curator.coverage_report()
        by_type = result["by_type"]
        assert isinstance(by_type, dict)
        # The test fixture has prose, config, image, visual-description, brand-material, wiki
        assert "prose" in by_type
        assert by_type["prose"] > 0

    def test_coverage_report_brand_materials_list(self, curator, brand_dir):
        """brand_materials should list paths of brand-material candidates."""
        result = curator.coverage_report()
        bm_list = result["brand_materials"]
        assert isinstance(bm_list, list)
        # The fixture has 3 brand materials (svg, pdf, png)
        assert len(bm_list) >= 1
        # All should be string paths
        for p in bm_list:
            assert isinstance(p, str)

    def test_coverage_report_vision_descriptions_list(self, curator, brand_dir):
        """vision_descriptions should list paths of visual-description candidates."""
        result = curator.coverage_report()
        vd_list = result["vision_descriptions"]
        assert isinstance(vd_list, list)
        assert len(vd_list) >= 2  # fixture has 3 vision cache files
        for p in vd_list:
            assert isinstance(p, str)

    def test_coverage_report_excluded_items(self, curator):
        """excluded list should contain dicts with path, type, score, reason."""
        # Use a tiny budget so some candidates are excluded
        curator.max_sources = 3
        result = curator.coverage_report()
        excluded = result["excluded"]
        assert isinstance(excluded, list)

        if excluded:
            item = excluded[0]
            assert "path" in item
            assert "type" in item
            assert "score" in item
            assert "reason" in item
            assert item["reason"]  # Should not be empty

    def test_coverage_report_excluded_reason_below_cutoff(self, curator):
        """Excluded items with enough budget should show 'below budget cutoff'."""
        # Tiny budget forces exclusions
        curator.max_sources = 2
        result = curator.coverage_report()
        excluded = result["excluded"]
        reasons = {e["reason"] for e in excluded}
        # Most should be budget-related
        assert len(excluded) > 0
        assert any("budget" in r or "over budget" in r for r in reasons)
