---
name: brand-visual-pipeline
description: Orchestrates the complete visual asset pipeline from brand docs to production-ready output. Chains visual-asset-prompt-generator, visual-asset-generator, and visual-asset-integrator in sequence. Use when generating and integrating visual assets for a brand.
---

# Brand Visual Pipeline

Meta-skill that orchestrates the complete visual asset generation workflow, from reading brand documentation to producing a finished landing page, pitch deck, or website with AI-generated visuals.

**Pipeline inspired by:** Dilum Sanjaya's workflow (Midjourney -> Nano Banana -> Hunyuan3D -> Gemini Pro), adapted to use brand docs as input instead of manual image searches.

## When to Use

- User says "generate visual assets for [brand]"
- User says "create a landing page with AI visuals for [brand]"
- User says "build pitch deck visuals from brand docs"
- User says "run the visual pipeline"
- Any request combining brand docs + AI image/3D generation + output target

## Input Variables

- `[BRAND_NAME]` — Brand name (required)
- `[OUTPUT_CONTEXT]` — Target: `landing-page` | `pitch-deck` | `website` | `all`
- `[ASSET_TYPES]` — What to generate: `hero-image` | `product-shot` | `3d-model` | `all`
- `[PRODUCT_FOCUS]` — Optional: specific product/feature

## Required Environment

```bash
FAL_KEY=xxx       # fal.ai API key
HF_TOKEN=hf_xxx  # HuggingFace Pro token (optional, for HF fallback)
```

## The Protocol

### Step 1: Invoke `visual-asset-prompt-generator`

Read brand docs and generate structured prompts.

**Input:** Brand docs directory, output context, asset types
**Output:** `brands/{BRAND_NAME}/visual-prompts.json`

**Verification:** Confirm prompts JSON exists and contains entries for requested asset types. Verify brand colors and mood keywords are present in prompts.

### Step 2: Invoke `visual-asset-generator`

Execute AI generation using the prompts.

**Input:** Prompts JSON from Step 1
**Output:** `assets/{BRAND_NAME}/manifest.json` + generated files

**For images (fal.ai):**
- Call Flux 1.1 Pro or Nano Banana via fal.ai API
- Download results, create WebP + thumbnails
- Typically completes in 10-30 seconds per image

**For 3D models (Hunyuan3D):**
- If Blender MCP connected: use Blender tools
- If not: use HuggingFace API or skip with warning
- Async polling required — can take 5-10 minutes
- Export GLB + viewport render

**Verification:** Confirm manifest.json exists with status "completed" for all assets. Check files exist on disk.

### Step 3: Invoke `visual-asset-integrator`

Place generated assets into the target output.

**Input:** Asset manifest + brand visual identity
**Output:** Production-ready HTML/markdown/package

**Verification:** Open generated HTML in browser to visually verify brand alignment.

### Step 4: Report

Generate summary of what was created:
- Number of assets generated
- Services used (fal.ai, Hunyuan3D, PolyHaven)
- Output files with paths
- Any errors or skipped items

## Example Invocation

```
User: "Generate visual assets for NOESIS and create a landing page"

Pipeline execution:
1. visual-asset-prompt-generator
   - Reads brands/noesis-brand-docs/ (13 docs)
   - Extracts: Deep Ink #1A1A2E, Bone #F5F0E8, Aged Gold #B8860B
   - Mood: grounded, substantial, architectural
   - Avoid: ethereal, mystical, soft
   - Generates: 2 image prompts (hero, product) + 1 3D prompt
   - Output: brands/noesis/visual-prompts.json

2. visual-asset-generator
   - Calls fal.ai Flux 1.1 Pro for hero image (1920x1080)
   - Calls fal.ai Flux 1.1 Pro for product shot (1200x800)
   - Calls Hunyuan3D for product 3D model (polls until done)
   - Post-processes: PNG, WebP, thumbnails
   - Output: assets/noesis/manifest.json

3. visual-asset-integrator
   - Reads manifest + visual identity
   - Generates: noesis-landing-page.html
   - Includes: hero section, product gallery, 3D viewer
   - Brand-aligned CSS: Deep Ink bg, Bone text, Gold CTAs
   - Output: brands/noesis/landing-page/index.html

4. Report
   - 3 assets generated (2 images, 1 3D model)
   - Services: fal.ai (2), Hunyuan3D (1)
   - Output: landing page HTML with all assets integrated
```

## Error Recovery

| Failure | Recovery |
|---------|----------|
| fal.ai unavailable | Skip image gen, report which prompts weren't executed |
| Blender not connected | Skip 3D gen or use HF API fallback |
| Partial generation | Continue with available assets, note gaps in report |
| Brand docs missing | Report which docs are needed, suggest running upstream skills |

## Integration

- **Chains**: visual-asset-prompt-generator -> visual-asset-generator -> visual-asset-integrator
- **Upstream**: visual-identity-core (brand must have visual identity docs)
- **Integrates with**: pitchdeck-skill *(deferred — Phase 4)*, campaign-page-builder
- **External APIs**: fal.ai, HuggingFace, Blender MCP
