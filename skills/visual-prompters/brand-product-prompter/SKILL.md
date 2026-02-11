---
name: brand-product-prompter
description: Generate AI image prompts for branded product concepts, packaging mockups, luxury reinterpretations, and product visualizations. This skill should be used when creating speculative brand products, souvenir collections, mockups (duffle bags, sneakers, passport covers), or dieline-to-3D packaging renders with [BRAND NAME] substitution.
---

# Brand Product Prompter

Generate production-ready AI image prompts for branded product concepts and mockups using battle-tested templates from commercial designers (Warner Music, PepsiCo, Spotify). All prompts use [BRAND NAME] variable substitution and are optimized for Nano Banana Pro / Gemini 3 Pro Image.

## When to Use

- Creating speculative product concepts for any brand
- Generating branded merchandise collections (capsule, souvenir)
- Designing product mockups (bags, sneakers, stickers, passport covers, beverage packaging)
- Converting packaging dielines into 3D renders
- Running the "Viral Product Architect" system prompt for unexpected brand objects

## Workflow

1. **Accept inputs:** Brand name + product type (concept / beverage / souvenir / mockup / collab / dieline)
2. **Select template** from `references/prompt-templates.md` based on product type
3. **Inject variables:** Replace `[BRAND NAME]` with target brand. Customize material, color, and environment parameters if requested.
4. **Apply camera defaults** (unless overridden): Phase One medium format, 100mm macro, f/8, shallow DOF
5. **Apply UI overlay defaults:** Manrope Regular bottom-left description, monochrome gray bottom-right logo
6. **Output** the complete prompt ready for image generation

## Template Categories

| Category | Templates | Best For |
|----------|-----------|----------|
| Product Concepts | 1.1, 1.2, 1.5 | Speculative brand objects, beverages, viral concepts |
| Souvenirs | 1.3, 1.4 | Branded merchandise collections, gift items |
| Packaging | 1.6, 6.4, 6.5 | Dieline renders, bottle design, minimal packaging |
| Accessories | 6.1, 6.2, 6.7 | Bags, leather goods, passport covers |
| Collaborations | 6.6 | Cross-brand sneaker collabs |
| Marketing | 6.3 | Branded sticker assets |

## Key Design Principles

- Swiss Design influence: clean, grid-based, generous negative space
- Hyper-premium materials: titanium, ceramic, carbon fiber, exotic leather
- Cinematic photography: Phase One camera, softbox lighting, shallow DOF, smooth bokeh
- Consistent UI overlay: Manrope Regular text (bottom-left) + monochrome logo (bottom-right)
- Variable substitution: every prompt uses `[BRAND NAME]` for instant brand adaptation

## Notes

- Always preserve the full prompt structure -- camera specs, material descriptions, and UI overlay placement are critical for quality output
- The "Viral Product Architect" (1.5) is a system prompt, not an image prompt -- use it to generate image prompts dynamically
- For cross-brand collabs (6.6), specify both brand names
- Material contrast drives visual interest: luxury materials on mundane objects creates the "thumb-stopping" effect
