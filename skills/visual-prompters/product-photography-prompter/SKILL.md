---
name: product-photography-prompter
description: Generate AI prompts for commercial product photography including beverage hero shots, cosmetic flat-lays, and design catalog layouts with technical specification panels. Use when photographing REAL products (not speculative concepts) with JSON-structured prompts optimized for Nano Banana Pro and GPT Image.
---

# Product Photography Prompter

Generate production-ready AI image prompts for commercial product photography. Unlike brand-product-prompter (which creates imagined products), this skill photographs existing products with studio-quality lighting, frozen motion, and technical catalog layouts.

## When to Use

- Creating commercial beverage photography (frozen splashes, hero shots)
- Generating beauty/cosmetic flat-lay product shots
- Building product design catalog pages (lifestyle hero + technical drawings)
- Any real-product photography requiring JSON-structured prompts

## Workflow

1. **Accept inputs:** Product reference image or description + photography style (catalog / beverage-hero / beauty-flatlay)
2. **Select template** from `references/prompt-templates.md`
3. **Configure parameters:** Resolution (8K UHD default), lighting type, environment, motion effects
4. **Output** JSON-structured prompt ready for Nano Banana Pro or GPT Image

## Template Categories

| Category | Template | Source | Best For |
|----------|----------|--------|----------|
| Design Catalog | Product Design Journal | Firat Bilal | Dual-section layout: lifestyle hero (top 60%) + technical drawings (bottom 40%) |
| Beverage Hero | Commercial Beverage | Johnn | Frozen-motion beverage shots with splash physics, ice cubes, coffee beans |
| Beauty Flat-lay | Cosmetic Product | Oogie | Skincare/beauty editorial with floral arrangements, dewy moisture |

## Key Design Principles

- JSON structure for higher AI adherence vs prose prompts
- 8K UHD resolution default with extreme clarity
- Frozen motion capture for liquid/splash photography
- Orthographic projection for technical drawing views
- 60-30-10 color distribution in catalog layouts
