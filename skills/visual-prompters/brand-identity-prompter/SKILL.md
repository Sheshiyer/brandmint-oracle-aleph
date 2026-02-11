---
name: brand-identity-prompter
description: Generate AI image prompts for brand identity visuals including logo variations (Swiss Design, glass, metallic, wax seal, crowd-formed), brand kit bento grids, and 3D logo treatments. This skill should be used when visualizing logos, creating brand presentation boards, or generating 3D logo renders with [BRAND NAME] substitution.
---

# Brand Identity Prompter

Generate production-ready AI image prompts for brand identity systems and logo visualizations. Creates comprehensive brand kits, logo style variations, and 3D logo treatments using [BRAND NAME] substitution.

## When to Use

- Creating comprehensive brand kit presentations (bento-grid layout)
- Generating logo variations in different styles (Swiss, glass, metallic, crowd, wax seal)
- Rendering logos as 3D objects (chrome, plastic, wax, grillz)
- Retexturing existing logos with new materials
- Reimagining brand identities in retro-modernist or geometric styles

## Workflow

1. **Accept inputs:** Brand name + identity type (kit / swiss / glass / metallic / wax / crowd / retexture / grillz)
2. **Select template** from `references/prompt-templates.md`
3. **Inject variables:** Replace `[BRAND NAME]`, `[COLOR]`, `[MATERIAL]`
4. **Customize** color palette, material finish, or environment if requested
5. **Output** the complete prompt ready for image generation

## Template Categories

| Category | Templates | Output |
|----------|-----------|--------|
| Brand Kit | 2.1 | 6-module bento grid (hero, social, palette, type, logo, manifesto) |
| Logo Styles | 2.2, 2.3, 2.4 | Swiss poster, glass emboss, crowd aerial |
| 3D Logos | 3.1, 3.2, 3.3, 3.4 | Chrome, wax seal, retextured plastic, grillz |

## Key Design Principles

- Brand Kit (2.1) uses three autonomous phases: Visual Strategy, Layout, Aesthetic Finish
- Swiss logos (2.2) demand reductive geometry -- fewest possible shapes
- Glass logos (2.3) rely on monochromatic palette + specular highlights on raised bezels
- 3D treatments all use cinematic studio lighting with shallow DOF and film grain
- Material authenticity is critical: each 3D treatment specifies exact material properties

## Notes

- The brand kit (2.1) is the most complex template -- generates entire presentation board in one prompt
- For glass logos, the `[COLOR]` variable controls the entire monochromatic palette
- Logo retexturing (3.3) works best with uploaded reference images of existing logos
- The crowd logo (2.4) requires specifying the exact logo silhouette shape
