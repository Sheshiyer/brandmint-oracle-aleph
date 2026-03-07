# Asset Fidelity Guide

## Overview

Brandmint v5 introduces **asset fidelity mode** — the ability to preserve pixel-exact user-provided logos and product images in generated visual assets, instead of relying on AI models to "reinterpret" them.

## The Problem

Previously, user logos were passed to Nano Banana Pro as `image_urls[]` style references. The AI model treated them as **style conditioning** — loose inspiration, not pixel-exact reproduction. For Flux 2 Pro assets (2B, 2C), logos couldn't even be passed as images at all.

**Result:** Generated assets contained AI-hallucinated logos that looked "inspired by" but never matched the real thing.

## Solution: Four Asset Modes

Configure via `brand-config.yaml`:

```yaml
generation:
  asset_mode: "composite"  # generate | composite | inpaint | hybrid
```

### `generate` (default)
Current behavior. AI generates everything from scratch using text prompts and style references. Logo fidelity is not guaranteed.

### `composite`
AI generates the background scene → PIL composites the real logo/product image on top with precise positioning, opacity, shadow, and blend modes. **Best for: guaranteed pixel fidelity.**

### `inpaint`
Uses FAL's flux-fill inpainting to generate scenes that flow naturally around the real logo. Requires FAL provider. **Best for: natural integration of logo into scene.**

### `hybrid`
Tries inpainting first, falls back to composite. **Best for: best-of-both-worlds when provider supports it.**

## Configuration

### Global Settings

```yaml
generation:
  asset_mode: "composite"
  composite_config:
    logo_position: "bottom-right"
    logo_scale: 0.15
    logo_padding: 20
    logo_opacity: 1.0
    logo_shadow: false
    product_position: "center"
    product_scale: 0.5
    product_feather: 5
```

### Position Grid

Nine positions available (3×3 grid):

```
top-left      top-center      top-right
center-left   center          center-right
bottom-left   bottom-center   bottom-right
```

### Per-Asset Overrides

Different assets can use different modes:

```yaml
generation:
  asset_mode: "composite"
  composite_config:
    per_asset_overrides:
      "2A-bento-grid": "generate"    # Style anchor always generates
      "2B-logo-lockup": "composite"  # Logo lockup uses exact composite
      "3A-product-hero": "inpaint"   # Product hero uses inpainting
```

**Note:** The 2A Bento Grid (style anchor) **always generates** regardless of mode — it's the visual reference for all downstream assets.

## CLI Usage

```bash
# Composite mode (recommended for logo fidelity)
bm visual execute --config brand-config.yaml --asset-mode composite

# Inpaint mode (requires FAL provider)
bm visual execute --config brand-config.yaml --asset-mode inpaint

# Hybrid (try inpaint, fallback to composite)
bm visual execute --config brand-config.yaml --asset-mode hybrid
```

## How It Works

### Composite Pipeline

```
1. AI generates scene (gen_with_provider)
   ↓
2. Route decision (asset_mode.route_asset)
   ↓
3. If composite needed:
   a. Load real logo from logo_files in config
   b. Analyze logo (transparency, bounding box, aspect ratio)
   c. Scale and position per asset type defaults
   d. PIL alpha_composite onto generated scene
   e. Save composited result
```

### Multi-Layer Stacking

For complex assets, the `LayerStack` API supports arbitrary layer composition:

```python
from brandmint.core.compositor import LayerStack, Position

result = (
    LayerStack((1920, 1080))
    .add_background(ai_generated_scene)
    .add_product(product_photo, Position.CENTER, scale=0.4)
    .add_logo(brand_logo, Position.BOTTOM_RIGHT, scale=0.12)
    .flatten()
)
```

### Provider Routing

The `route_asset()` function automatically determines the best approach per asset:

| Asset Type | Default Mode | Logo Composite | Product Composite |
|-----------|-------------|----------------|-------------------|
| 2A Bento Grid | Always generate | — | — |
| 2B Logo Lockup | Per config | ✅ (center, 35%) | — |
| 3A/3B Product Hero | Per config | ✅ (bottom-right, 12%) | ✅ (center, 50%) |
| 4A/4B Lifestyle | Per config | ✅ (bottom-left, 10%) | ✅ (center-right, 35%) |
| 5A Packaging | Per config | ✅ (top-center, 20%) | ✅ (center, 45%) |

### Inpainting Pipeline (FAL only)

```
1. Load real logo
2. Create mask covering logo placement zone
3. Upload logo + mask to FAL flux-fill
4. flux-fill generates scene that flows around the logo
5. Real logo is pixel-preserved; scene adapts to it
```

## Provenance Tracking

Every generated asset is tracked with its source type:

```python
from brandmint.core.asset_provenance import AssetProvenance

provenance = AssetProvenance(brand_dir)
provenance.register("2B-logo-lockup-seed42", source="composited", ...)
```

Provenance data is persisted to `.brandmint/asset-provenance.json` and available for audit.

## Cost Impact

| Mode | Extra Cost | Notes |
|------|-----------|-------|
| generate | $0 | Status quo |
| composite | $0 | PIL processing only, no API calls |
| inpaint | ~$0.08/asset | FAL flux-fill API call per asset |
| hybrid | $0-0.08/asset | Depends on inpaint success rate |

## Supported Providers

| Provider | Generate | Composite | Inpaint | Edge-Guided |
|----------|----------|-----------|---------|-------------|
| FAL | ✅ | ✅ | ✅ (flux-fill) | ✅ (flux-canny) |
| OpenRouter | ✅ | ✅ | ❌ | ❌ |
| OpenAI | ✅ | ✅ | ❌ | ❌ |
| Replicate | ✅ | ✅ | ❌ | ❌ |

**Note:** Composite mode works with ALL providers (PIL-based, no API needed). Inpaint/hybrid modes require FAL.
