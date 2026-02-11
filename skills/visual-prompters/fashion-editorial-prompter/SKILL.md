---
name: fashion-editorial-prompter
description: Generate AI image prompts for high-fashion editorial photography, apparel lookbooks, sport jerseys, cross-brand fashion collaborations, and identity-preserving pose grids. This skill should be used when creating fashion campaigns, editorial shoots, branded apparel visualizations, or multi-angle contact sheets with JSON-structured identity anchoring.
---

# Fashion Editorial Prompter

Generate production-ready AI image prompts for fashion photography and apparel design. Features two prompt architectures: JSON-structured identity-preserving prompts for consistent characters across poses, and text-based apparel templates for branded fashion concepts.

## When to Use

- Creating editorial fashion photography with identity preservation
- Generating multi-angle contact sheets (3x3 grids) with consistent character
- Designing branded apparel concepts (jerseys, outerwear, Crocs collabs)
- Building fashion campaign triptychs
- Creating hypebeast showroom still-life photography
- Reimagining brands as sport clubs

## Workflow

1. **Accept inputs:** Brand name + fashion type (editorial / apparel / campaign / collab / showroom / sport-club)
2. **Select template** from `references/prompt-templates.md`
3. **For editorial prompts:** Apply JSON structure with identity anchoring, negative prompts, and camera specs
4. **For apparel prompts:** Replace `[BRAND NAME]` and customize materials/colors
5. **Apply camera defaults:** Phase One XF, 80mm, f/8, butterfly lighting (editorial) or softbox (apparel)
6. **Output** JSON-structured or text prompt with identity preservation constraints

## Template Categories

| Category | Templates | Output |
|----------|-----------|--------|
| Editorial | A, B | Identity-preserving JSON prompts |
| Apparel | 7.1, 7.3, 7.4, 7.7 | Branded clothing visualization |
| Campaigns | 7.2, 7.6 | Fashion campaign layouts |
| Collaborations | 7.4, 7.5 | Cross-brand outerwear and footwear |
| Sport | 7.1, 7.8 | Jerseys and brand-as-sport-club |

## Key Principles

- Identity Preservation: JSON prompts use negative prompts to prevent identity drift
- Wardrobe Consistency: All panels must match fabric, accessories, styling exactly
- Camera Specs: Phase One XF with 80mm is standard for editorial realism
- Material Authenticity: Specify exact fabric types (wool gabardine, cotton-blend knit)
- Pose Psychology: Poses communicate brand attitude (predatory for power, relaxed for lifestyle)
