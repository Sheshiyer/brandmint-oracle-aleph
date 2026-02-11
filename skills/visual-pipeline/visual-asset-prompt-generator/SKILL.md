---
name: visual-asset-prompt-generator
description: Reads brand documentation (visual identity, product description, positioning) and generates optimized prompts for image generation (Nano Banana/Flux via fal.ai) and 3D model generation (Hunyuan3D). Use when generating visual assets from brand docs.
---

# Visual Asset Prompt Generator

Extracts brand context from documentation and generates structured prompts for AI image and 3D model generation, tailored to the output target (landing page, pitch deck, website).

## When to Use

- User wants to generate visual assets (images, 3D models) for a brand
- User says "generate visuals", "create assets", "brand images", "3D models from brand"
- As Step 1 of the brand-visual-pipeline

## Input Variables

- `[BRAND_NAME]` — Name of the brand (matches `brands/{name}/` directory)
- `[BRAND_DOCS_DIR]` — Path to brand docs (default: `brands/{BRAND_NAME}/`)
- `[OUTPUT_CONTEXT]` — Target: `landing-page` | `pitch-deck` | `website` | `social`
- `[ASSET_TYPES]` — What to generate: `hero-image` | `product-shot` | `3d-model` | `texture` | `all`
- `[PRODUCT_FOCUS]` — Optional: specific product/feature to emphasize

## The Protocol

### Phase 1: Brand Context Extraction

Read the following brand docs (in order of priority):

1. **Visual Identity** (`06-visual-identity.md` or `visual-identity-guide.md`)
   - Extract: color palette (hex codes), mood keywords, imagery style, illustration style
   - Extract: what to AVOID (visual positioning "Avoid" column)
   - Extract: graphic elements (patterns, textures, borders)

2. **Product Description** (`04-detailed-product-description.md`)
   - Extract: product features, physical characteristics, materials
   - Extract: core offerings and what the product IS

3. **Product Positioning** (`02-product-positioning.md`)
   - Extract: market position, brand essence, target perception

4. **Logo Prompts** (`12-logo-prompts.md`, if exists)
   - Extract: visual keywords, symbolic concepts, brand essence visuals

5. **MDS** (`05-messaging-direction-summary.md`)
   - Extract: pitch, USP, emotional drivers

### Phase 2: Build Brand Context Object

Compile extracted data into a structured context:

```json
{
  "brand": "[BRAND_NAME]",
  "colors": {
    "primary": { "name": "...", "hex": "#..." },
    "secondary": { "name": "...", "hex": "#..." },
    "accent": { "name": "...", "hex": "#..." }
  },
  "mood_keywords": ["keyword1", "keyword2", ...],
  "imagery_style": "description of photography/illustration style",
  "avoid": ["thing1", "thing2", ...],
  "product_essence": "one-line product description",
  "materials": ["material1", "material2"],
  "graphic_elements": "patterns, textures, etc."
}
```

### Phase 3: Generate Prompts by Asset Type

**For Hero Images (fal.ai / Nano Banana / Flux):**
- Compose a detailed scene description incorporating brand mood and colors
- Include lighting style from imagery guidelines
- Add negative prompt from avoid list
- Tailor composition to output context:
  - `landing-page`: Wide, atmospheric, emotional — 16:9 or 21:9 aspect ratio
  - `pitch-deck`: Clean, professional, product-focused — 16:9
  - `website`: Versatile, multiple crops possible — 3:2 or 4:3
  - `social`: Square or 4:5, high impact, minimal

**For Product Shots (fal.ai / Nano Banana / Flux):**
- Focus on product features and materials
- Use brand color palette for background/environment
- Clean studio-style or contextual lifestyle based on brand guidelines
- Include texture and material details

**For 3D Models (Hunyuan3D):**
- Keep text_prompt under 200 characters (Hunyuan3D limit)
- Focus on object description, not scene
- Include material and finish (matte, glossy, textured)
- Calculate bbox_condition ratios from product dimensions
- Generate as English-only prompt

**For Textures (PolyHaven search terms):**
- Generate search category keywords from brand materials
- Match brand aesthetic (e.g., "wood" for craft, "stone" for architectural)

### Phase 4: Context-Specific Optimization

Apply output-target modifications:

| Context | Emphasis | Style | Format |
|---------|----------|-------|--------|
| landing-page | Emotional, atmospheric | Lifestyle + product | 16:9, 1920x1080 |
| pitch-deck | Professional, clear | Product on clean BG | 16:9, 1920x1080 |
| website | Versatile, consistent | Multiple angles | 3:2, 1200x800 |
| social | High impact, bold | Minimal, eye-catching | 1:1, 1080x1080 |

## Output Format

Generate a JSON file at `brands/{BRAND_NAME}/visual-prompts.json`:

```json
{
  "brand": "[BRAND_NAME]",
  "generated_at": "ISO_DATE",
  "output_context": "[OUTPUT_CONTEXT]",
  "brand_context": {
    "colors": { ... },
    "mood_keywords": [...],
    "avoid": [...],
    "imagery_style": "..."
  },
  "prompts": [
    {
      "asset_id": "hero-001",
      "type": "hero-image",
      "service": "fal-flux",
      "prompt": "detailed generation prompt...",
      "negative_prompt": "things to avoid...",
      "parameters": {
        "width": 1920,
        "height": 1080,
        "guidance_scale": 7.5,
        "num_inference_steps": 50
      },
      "brand_alignment": {
        "primary_color": "#HEX",
        "mood": "keyword",
        "style": "description"
      }
    },
    {
      "asset_id": "model-001",
      "type": "3d-model",
      "service": "hunyuan3d",
      "prompt": "short english description under 200 chars",
      "parameters": {
        "bbox_condition": [1.0, 0.8, 0.3]
      },
      "brand_alignment": {
        "materials": ["material1"],
        "finish": "matte/glossy"
      }
    }
  ]
}
```

Also generate a human-readable summary at `brands/{BRAND_NAME}/visual-generation-guide.md`.

## Integration

- **Upstream**: visual-identity-core, detailed-product-description, product-positioning-summary
- **Downstream**: visual-asset-generator (consumes the prompts JSON)
- **Part of**: brand-visual-pipeline orchestrator

## CLI Usage

```bash
bun scripts/cli.ts activate visual-asset-prompt-generator
```
