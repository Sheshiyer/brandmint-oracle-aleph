# Brandmint — Prompt Templates

All templates use `{variable}` substitution from `brand-config.yaml`. The `generate_pipeline.py` script renders these templates with brand-specific values.

## Variable Reference

| Variable | Source | Example |
|----------|--------|---------|
| `{brand_name}` | `brand.name` | Tryambakam Noesis |
| `{brand_tagline}` | `brand.tagline` | Train you to author your own meaning |
| `{archetype}` | `brand.archetype` | The Seasoned Cartographer |
| `{voice}` | `brand.voice` | Grounded, direct, respectful-challenging |
| `{domain}` | `brand.domain` | Philosophical Practice |
| `{theme_name}` | `theme.name` | Bioluminescent Architecture |
| `{theme_description}` | `theme.description` | Tech-Solarpunk-Art-Nouveau... |
| `{primary_name}` / `{primary_hex}` | `palette.primary` | Void Teal / #0A1628 |
| `{secondary_name}` / `{secondary_hex}` | `palette.secondary` | Phosphor Cream / #F0EDE3 |
| `{accent_name}` / `{accent_hex}` | `palette.accent` | Solar Bronze / #C4873B |
| `{support_name}` / `{support_hex}` | `palette.support` | Titanium / #8A9BA8 |
| `{signal_name}` / `{signal_hex}` | `palette.signal` | Chlorophyll / #4A7C59 |
| `{header_font}` | `typography.header.font` | Exo 2 |
| `{body_font}` | `typography.body.font` | Space Grotesk |
| `{data_font}` | `typography.data.font` | Fira Code |
| `{materials_list}` | `materials` (joined) | brushed titanium, glass, moss... |
| `{photo_style}` | `photography.style` | High contrast + accent lighting |
| `{photo_environment}` | `photography.environment` | Art Nouveau greenhouse |
| `{photo_constraint}` | `photography.constraint` | Hands not faces |
| `{photo_camera}` | `photography.camera` | Phase One XF, 80mm |
| `{illus_style}` | `illustration.style` | Art Nouveau + Art Deco fusion |
| `{illus_references}` | `illustration.references` | Mucha meets tech |
| `{sigil_description}` | `sigil.description` | Three converging filaments |
| `{sigil_components}` | `sigil.components` (joined) | Soma, Manas, Muladhara |
| `{negative_prompt}` | `negative_prompt` | cartoon, anime, clipart... |

---

## Composition Reference Images

Each Nano Banana Pro prompt can be paired with a **composition reference image** that guides the layout/structure of the generated asset. These are stored in `references/images/` and auto-loaded by generated scripts via the `REF_IMAGES` mapping.

### Primary Composition References

These are the 14 images directly mapped to prompt template IDs. They serve as `image_urls` composition references for Nano Banana Pro, or as visual documentation for Flux 2 Pro / Recraft V3.

| Prompt ID | Reference Image | Purpose | Model |
|-----------|----------------|---------|-------|
| 2A | `ref-2A-bento-grid.jpg` | 6-module bento grid layout structure | Nano Banana Pro |
| 2B | `ref-2B-brand-seal.jpg` | Wax seal / emblem composition | Flux 2 Pro (ref unused) |
| 2C | `ref-2C-logo-emboss.jpg` | Frosted glass logo emboss style | Flux 2 Pro (ref unused) |
| 3A | `ref-3A-capsule-collection.jpg` | Product lineup / flatlay composition | Flux 2 Pro (ref unused) |
| 3B | `ref-3B-hero-product.jpg` | Individual branded product shots | Flux 2 Pro (ref unused) |
| 3C | `ref-3C-essence-vial.jpg` | Branded vessel / vial product shots | Flux 2 Pro (ref unused) |
| 4A | `ref-4A-catalog-layout.jpg` | Product catalog with spec callouts | Nano Banana Pro |
| 4B | `ref-4B-flatlay.jpg` | Minimal white product photography | Flux 2 Pro (ref unused) |
| 5A | `ref-5A-heritage-engraving.jpg` | Fine-line botanical heritage engraving | Recraft V3 (ref unused) |
| 5B | `ref-5B-campaign-grid.jpg` | 2-column asymmetric campaign grid | Nano Banana Pro |
| 5D | `ref-5D-engine-icons.jpg` | Minimal icon set on solid background | Recraft V3 (ref unused) |
| 7A | `ref-7A-contact-sheet.jpg` | 3x3 grid-tiled photo composition | Nano Banana Pro |
| 8A | `ref-8A-seeker-poster.jpg` | Brand presentation poster layout | Nano Banana Pro |
| 9A | `ref-9A-engine-poster.jpg` | Detailed single-object poster with labels | Nano Banana Pro |
| 10A-C | `ref-7A-contact-sheet.jpg` | Grid layout (reuses 7A) | Nano Banana Pro |

**Note:** Only Nano Banana Pro accepts `image_urls` for composition references. Flux 2 Pro and Recraft V3 do not — their reference images are stored for documentation/inspiration purposes only.

### Supplementary Style References

Alternative style references available in `references/images/`. Use these to swap composition references for different aesthetics.

| Filename | Relevant Template | Description |
|----------|-------------------|-------------|
| `ref-alt-glass-editorial.jpg` | 2C alt | Frosted glass editorial layouts |
| `ref-alt-emboss-monochrome.jpg` | 2C alt | Monochrome glossy emboss on colored surfaces |
| `ref-alt-chrome-logos.jpg` | 2B alt | Polished 3D chrome logo renders |
| `ref-alt-3d-sticker-logos.jpg` | 2B alt | 3D tactile logo artifacts |
| `ref-alt-minimal-logos.jpg` | 2B alt | Clean metallic minimal logo reimaginings |
| `ref-alt-foil-stickers.jpg` | misc | Crinkled foil / balloon textured brand stickers |
| `ref-alt-leather-duffles.jpg` | 3A alt | Branded luxury duffle bag lineup |
| `ref-alt-passport-covers.jpg` | 3B alt | Branded accessory product shots |
| `ref-alt-leather-bags.jpg` | 3A alt | Branded leather bag product shots |
| `ref-alt-beverage-bottles.jpg` | 3C alt | Branded bottles on colored backgrounds |
| `ref-alt-branded-shoes.jpg` | 3A alt | Cross-brand product design collabs |
| `ref-alt-varsity-jackets.jpg` | 3A alt | Branded apparel in environmental setting |
| `ref-alt-embossed-tshirts.jpg` | 3A alt | Material texture detail in branded apparel |
| `ref-alt-boxing-gloves.jpg` | 3B alt | Luxury branded product concept |
| `ref-alt-organic-logo.jpg` | misc | Logo-as-organic-material concept |
| `ref-alt-calligraphic-initials.jpg` | 5A alt | Ornate typography / letterform style |
| `ref-alt-dieline-to-3d.jpg` | misc | Packaging design dieline-to-3D workflow |
| `ref-alt-product-branding-workflow.jpg` | misc | Product branding workflow diagram |
| `ref-alt-sneaker-collabs.jpg` | misc | Cross-brand sneaker collab product design |

### Portrait/Character Style References

Demonstrate Nano Banana Pro's portrait/character capabilities. Less directly relevant to brands using "hands not faces" constraint but show valuable style techniques.

| Filename | Style |
|----------|-------|
| `ref-style-fashion-tutorial.jpg` | Fashion prompt tutorial (3 person photos) |
| `ref-style-bold-portrait-grid.jpg` | Celebrity portraits with bold color blocks |
| `ref-style-collage-portraits.jpg` | Collage/glitch torn-paper portrait effect |
| `ref-style-duotone-faces.jpg` | Minimalist duotone flat vector face illustrations |
| `ref-style-line-portraits.jpg` | B&W minimal line-art portrait icons |
| `ref-style-retro-typography.jpg` | Retro baseball-style brand typography |
| `ref-style-line-sketches.jpg` | Line-art character sketches |
| `ref-style-cartoon-caricatures.jpg` | Colored cartoon caricatures |
| `ref-style-graffiti-overlay.jpg` | Graffiti/crackle face overlays with doodles |
| `ref-style-halftone-portraits.jpg` | Halftone dot comic-style portraits |
| `ref-style-fashion-prompt.jpg` | Fashion prompt with outfit changes |

### Demo / Inspiration Gallery

Nano Banana Pro demonstration images showing creative concept possibilities.

| Filename | Description |
|----------|-------------|
| `ref-demo-aerial-logo.jpg` | Logo made of aerial people (creative concept) |
| `ref-demo-superhero-composite.jpg` | Superhero characters composite |
| `ref-demo-product-design-tutorial.jpg` | Creative product design tutorial slide |
| `ref-demo-metal-grillz.jpg` | Metal grillz/jewelry with brand names |
| `ref-demo-box-christmas-trees.jpg` | Christmas trees made of brand boxes |

---

## Category 1: Brand Identity

### 2A — Bento Grid (Style Anchor)

**Model:** Nano Banana Pro | **Aspect:** 16:9 | **Priority:** MUST RUN FIRST

This generates the visual style anchor that all subsequent Nano Banana Pro calls reference.

```
{brand_name} ({domain}).
Act as Lead Brand Designer creating a comprehensive "Brand Identity System"
presentation (Bento-Grid Layout).

6 distinct modules:
Block 1 (Hero): Product photograph in {photo_environment}. {accent_name} light.
Materials: {materials_list}. "{brand_name}" wordmark in {secondary_name}.
Block 2 (Social): {primary_name} background, "{brand_tagline}" text.
Block 3 (Palette): 5 color swatches with HEX codes.
Block 4 (Typography): {header_font} specimen.
Block 5 (Sigil): {sigil_description}.
Block 6 (DNA): Manifesto card with archetype, voice, visuals.
```

### 2B — Brand Seal

**Model:** Flux 2 Pro | **Aspect:** 1:1 (square_hd)

```
{brand_name} brand seal emblem. Oxidized copper circular seal
with geometric precision. Central sigil: {sigil_description}.
"{brand_name}" around perimeter in {header_font}. Material: oxidized
copper with {accent_name} patina. Background: {primary_name}.
```

### 2C — Logo Emboss

**Model:** Flux 2 Pro | **Aspect:** 16:9 (landscape_16_9)

```
{brand_name} stained-glass logo emboss. Brand sigil as stained-glass
window panel. Colors: {primary_hex}, {accent_hex}, {signal_hex}.
Backlit with warm diffused light. "{brand_name}" wordmark in
{header_font} SemiBold below.
```

---

## Category 2: Product Concepts

### 3A — Capsule Collection

**Model:** Flux 2 Pro | **Aspect:** 4:3 (landscape_4_3)

```
{brand_name} capsule collection product lineup.
Three products on polished surface. Materials: {materials_list}.
Environment: {photo_environment}. {photo_style}. {photo_constraint}.
```

### 3B — Hero Book

**Model:** Flux 2 Pro | **Aspect:** 1:1 (square_hd)

```
{brand_name} hero book product shot. Hardcover codex with custom
spine in {accent_name} material. Geometric diagrams in {data_font}.
{photo_style}. Environment: {photo_environment}.
```

### 3C — Essence Vial

**Model:** Nano Banana Pro | **Aspect:** 1:1

```
{brand_name} essence vial. Small borosilicate glass bottle with
oxidized metal dropper cap. Etched label in {data_font}. Brand name
etched dominant. {primary_name} background. Sharp high-contrast lighting.
```

---

## Category 3: Product Photography

### 4A — Catalog Layout

**Model:** Nano Banana Pro | **Aspect:** 3:4

```
{brand_name} product design catalog page. Top: lifestyle product image
inside {photo_environment}. Bottom: technical specification panel with
architectural drawings in {accent_name} on {primary_name} background.
Material swatches: {materials_list}.
```

### 4B — Flatlay

**Model:** Flux 2 Pro | **Aspect:** 1:1 (square_hd)

```
{brand_name} product collection flat-lay. Five brand objects on
polished surface. Materials: {materials_list}. Overhead composition.
{accent_name} directional light. {photo_constraint}.
```

---

## Category 4: Illustrations

### 5A — Heritage Engraving

**Model:** Recraft V3 (digital_illustration) | **Aspect:** 1:1 (square_hd)

**WARNING:** Must be under 1000 chars for Recraft.

```
{brand_name} heritage engraving logomark. {illus_style}. Thin delicate
hairlines. Central sigil: {sigil_description}. "{brand_name}" in
{header_font}. {secondary_name} paper. {primary_name} lines.
{accent_name} accent on borders.
```

### 5B — Campaign Grid

**Model:** Nano Banana Pro | **Aspect:** 3:4

```
{brand_name} Campaign Visual Identity Grid. 2-column asymmetrical
layout. Sigil blocks in {primary_name}. Slogan blocks in {accent_name}.
Duotone photography using {primary_hex} + {accent_hex}. Typography:
{header_font} ONLY. {photo_constraint}.
```

### 5C — Art Panel

**Model:** Recraft V3 (digital_illustration) | **Aspect:** 3:4 (portrait_4_3)

**WARNING:** Must be under 1000 chars for Recraft.

```
{brand_name} conceptual panel illustration. {illus_style}.
{illus_references}. Flat color planes in {primary_name}, {accent_name},
{signal_name}. Bio-digital structure with fiber-optic filaments.
No mystical imagery.
```

### 5D — Engine Icons (Batched)

**Model:** Recraft V3 (vector_illustration/line_circuit) | **Aspect:** 1:1 (square_hd)

**WARNING:** Must be under 1000 chars. Returns SVG — auto-convert to PNG.

```
{count} minimalist styled flat vector icons for {brand_name}
"{group_name}" in {layout} layout. Only {primary_name} ({primary_hex})
and {secondary_name} ({secondary_hex}). No gradients.
Icons: {icon_list}. {data_font} labels.
```

---

## Category 5: Narrative

### 7A — Contact Sheet

**Model:** Nano Banana Pro | **Aspect:** 1:1

Pass composition reference image alongside anchor for best grid layout.

```
{brand_name} editorial contact sheet. 3x3 grid, 9 panels, hands-only
photography inside {photo_environment}. No face. Same hands all panels.
Materials: {materials_list}. Camera: {photo_camera}. {accent_name}
highlights. 2px {support_name} borders. 8K detail.
```

---

## Category 6: Posters

### 8A — Seeker Poster

**Model:** Nano Banana Pro | **Aspect:** 3:4

```
{brand_name} "The Seeker" conceptual portrait poster. Figure from
behind, split vertically. LEFT: material reality. RIGHT: inner
architecture blueprint. Split line glows {accent_name}.
Typography: "THE SEEKER" in {header_font} Light.
```

### 9A — Engine Posters (Template)

**Model:** Nano Banana Pro | **Aspect:** 3:4

Uses `BASE_PROMPT.format(**engine_data)` for batch generation. Each engine has its own `{object}`, `{material_a}`, `{material_b}`, `{bg_color}`, `{bg_hex}`.

```
{brand_name} campaign poster. Single {object} centered on {bg_color}
({bg_hex}) background. Part {material_a}, part {material_b}, with
fiber-optic filaments glowing {secondary_name}. Art Deco border in
{accent_name}. "{engine_name}" in {header_font} Bold.
"{tagline}" in {header_font} Light.
```

### 10A-C — Ritual Sequences (Template)

**Model:** Nano Banana Pro | **Aspect:** 1:1

Uses `BASE_PROMPT.format(sequence_title=..., panel_descriptions=...)`.

```
{brand_name} "{sequence_title}" sequential practice narrative.
3x3 grid of 9 panels. Hands-only progression. Environment:
{photo_environment}. Materials: {materials_list}.
9 PANELS: {panel_descriptions}
Camera: {photo_camera}. {accent_name} highlights. 2px borders. 8K.
```

---

## Adding New Templates

1. Define the template in this file with `{variable}` placeholders
2. Add the template constant to `generate_pipeline.py`
3. Create a script generator function
4. Add the prompt type to `brand-config.yaml` under `prompts`
5. Re-run `generate_pipeline.py` to generate the new script
