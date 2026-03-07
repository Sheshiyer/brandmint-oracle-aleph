# NotebookLM Brand Sources Guide

## Overview

Brandmint v5 enhances the NotebookLM publishing pipeline to upload brand materials as rich, contextualized sources. This produces dramatically better PDFs, infographics, and reports that genuinely feel "on brand."

## The Problem

Previously, visual assets were uploaded as raw images without descriptive context. Logos weren't analyzed textually. Brand materials (style guide, palette, typography) weren't structured as source documents. NotebookLM couldn't leverage them effectively when generating artifacts.

## What's New

### Vision-Powered Image Descriptions (NB-01)

Each generated visual asset can now have a companion text description generated via LLM vision analysis. These descriptions cover:
- **Composition**: Layout structure, visual hierarchy, use of space
- **Color Palette**: Dominant colors, accents, gradients
- **Typography**: Visible text and typographic treatment
- **Brand Elements**: Logos, icons, patterns, motifs
- **Mood & Tone**: Emotional quality, brand personality expressed

### Brand Style Guide Source (NB-04)

Brand config data (palette, typography, aesthetic, theme) is automatically transformed into a narrative style guide document uploaded as a high-priority source.

### Raw Brand Material Scanning (NB-08)

User-provided logos and product images from `logo_files` in brand config are uploaded as sources alongside their LLM-generated descriptions.

## Configuration

### brand-config.yaml

```yaml
publishing:
  synthesize: true                    # LLM prose synthesis
  include_brand_materials: true       # Upload logos, style guide, visual descriptions
  vision_descriptions: true           # Generate LLM descriptions for visual assets
  vision_model: ""                    # Override model (default: claude-3.5-haiku)
  max_sources: 50                     # NotebookLM Standard plan limit
```

### CLI Flags

```bash
# Include brand materials as sources
bm publish notebooklm --config brand-config.yaml --include-brand-materials

# Also generate vision descriptions for each visual asset
bm publish notebooklm --config brand-config.yaml \
  --include-brand-materials \
  --vision-descriptions

# Dry run to see what sources would be uploaded
bm publish notebooklm --config brand-config.yaml \
  --include-brand-materials --dry-run
```

## Source Types & Priority

| Source Type | Score Range | Description |
|-----------|-------------|-------------|
| Prose (synthesized) | 95 | LLM-generated narrative from skill outputs |
| Visual Description | 75 | LLM vision analysis of generated assets |
| Brand Style Guide | 80 | Palette, typography, aesthetic as narrative |
| Config | 78 | Raw brand-config.yaml |
| Brand Material | 70 | User-provided logos, product photos |
| Image | 40-88 | Generated visual assets (raw upload) |
| Wiki | 30-72 | Wiki page content |

### Logo Description Bonus

Logo-related descriptions receive a +10 content_value bonus since logo fidelity is critical for all downstream artifacts.

### Complementary Scoring

When both a raw image AND its text description exist, both receive a +5 category_bonus. The description helps NotebookLM understand what it's looking at; the image provides the actual visual reference.

## How Sources Flow

```
brand-config.yaml
  ├── palette, typography, aesthetic
  │   → BrandStyleGuideBuilder → style-guide.md → Source
  │
  ├── logo_files
  │   → Logo image → Source (raw upload)
  │   → VisionDescriber (logo mode) → logo-description.md → Source
  │
  └── generated/ visual assets
      → Image → Source (raw upload, as before)
      → VisionDescriber → {asset-id}-description.md → Source
```

## Cost Impact

| Feature | Extra Cost | Notes |
|---------|-----------|-------|
| Brand materials upload | $0 | Just uploading existing files |
| Style guide synthesis | ~$0.005 | Single LLM call for structured data |
| Vision descriptions (all assets) | ~$0.50-1.00 | ~19 assets × $0.03-0.05 per vision call |
| Vision descriptions (logo only) | ~$0.05 | Single logo analysis |

Vision descriptions are **optional** — enable only when artifact quality matters.

## Artifact Quality Improvements

With brand materials as sources, NotebookLM generates:

- **Infographics** that use the actual brand color palette and reference logo placement
- **PDF Reports** with brand-appropriate headers, typography directions, and color schemes  
- **Slide Decks** that reference the visual language and style guide
- **Audio Overviews** that can describe the brand's visual identity verbally

## Cache

Vision descriptions are cached in `.brandmint/vision-cache/`. Clear with:

```bash
rm -rf .brandmint/vision-cache/
```

Style guide sources are cached in `.brandmint/sources/brand-style-guide.md`.
