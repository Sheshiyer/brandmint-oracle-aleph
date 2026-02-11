---
name: visual-asset-integrator
description: Takes generated visual assets (images, 3D models) and integrates them into landing pages, pitch decks, and websites with brand-aligned styling. Reads asset manifest and brand visual identity to produce production-ready output.
---

# Visual Asset Integrator

Places generated visual assets into target outputs (landing pages, pitch decks, websites) with brand-consistent styling derived from the visual identity guide.

## When to Use

- After visual-asset-generator has produced assets and manifest
- User says "build the landing page", "integrate assets", "create the page with these visuals"
- As Step 3 of the brand-visual-pipeline

## Input Variables

- `[BRAND_NAME]` — Brand name
- `[BRAND_DOCS_DIR]` — Brand docs path (default: `brands/{BRAND_NAME}/`)
- `[ASSET_MANIFEST]` — Path to manifest (default: `assets/{BRAND_NAME}/manifest.json`)
- `[TARGET]` — Output target: `landing-page` | `pitch-deck` | `slide-deck` | `website`

## The Protocol

### Phase 1: Load Context

1. Read asset manifest from visual-asset-generator
2. Read brand visual identity (colors, typography, graphic elements)
3. Read brand copy if available (campaign-page-copy, MDS)
4. Categorize assets by type (hero, product, 3D, texture)

### Phase 2: Generate Brand Stylesheet

From the visual identity guide, generate CSS custom properties:

```css
:root {
  /* Colors from brand visual identity */
  --brand-primary: {colors.primary.hex};
  --brand-secondary: {colors.secondary.hex};
  --brand-accent: {colors.accent.hex};
  --brand-support: {colors.support.hex};
  --brand-warning: {colors.warning.hex};

  /* Typography */
  --font-display: '{typography.header.family}', serif;
  --font-body: '{typography.body.family}', sans-serif;
  --font-mono: '{typography.accent.family}', monospace;

  /* Type Scale */
  --text-h1: 48px;
  --text-h2: 36px;
  --text-h3: 24px;
  --text-body: 18px;
  --text-small: 14px;
}
```

### Phase 3: Target-Specific Integration

#### Landing Page (`landing-page`)

Generate complete HTML file with:

**Structure:**
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <!-- Google Fonts -->
  <!-- Brand CSS -->
  <!-- model-viewer for 3D (if applicable) -->
</head>
<body>
  <header> Brand logo/wordmark </header>

  <section class="hero">
    <!-- hero-image asset, full-width -->
    <h1> Brand headline (from MDS/campaign copy) </h1>
    <p> Subheadline / pitch </p>
    <a class="cta"> Call to action </a>
  </section>

  <section class="product">
    <!-- product-shot assets in grid -->
    <!-- 3D model viewer if model exists -->
  </section>

  <section class="features">
    <!-- Feature blocks with supporting images -->
  </section>

  <footer> Brand info </footer>
</body>
</html>
```

**Asset Integration Rules:**
- Hero images: `<picture>` with WebP source + PNG fallback
- Product shots: Responsive grid with lazy loading
- 3D models: `<model-viewer>` web component with auto-rotate
- Textures: CSS background-image at reduced opacity
- All images include alt text from asset metadata

**Styling Rules (from brand identity):**
- Background: brand primary or secondary
- Text: high-contrast using brand colors
- Accent: used sparingly for CTAs and highlights
- Borders: 1px, sharp corners (per brand guidelines)
- Generous whitespace / margins
- Max-width content for readability

#### Pitch Deck (`pitch-deck`)

Generate markdown source document for NotebookLM/Gamma with asset references:

```markdown
# [BRAND_NAME] Pitch Deck

## Visual Assets Library
[List all available assets with recommended slide placement]

## Slide 1: Title
**Background**: assets/{brand}/images/hero-shots/hero-001.webp
**Content**: Brand name, tagline
**Style**: Full-bleed hero, text overlay with brand colors

## Slide 3: Product
**Visual**: assets/{brand}/3d-models/model-001/render.png
**Alternative**: Embed 3D viewer (model.glb) if platform supports
**Layout**: 60% visual / 40% text split

...
```

Also generate:
- `{brand}-gamma-prompt.md` — Prompt for Gamma.app
- `{brand}-notebooklm-prompt.md` — Prompt for NotebookLM
- `{brand}-slide-data.json` — Structured slide data with asset paths

#### Slide Deck (`slide-deck`)

Integrates with visual-slidedeck-generator output format. Appends asset library to existing slide source document.

#### Website (`website`)

Generates an asset package:
- `index.html` — Homepage with integrated assets
- `styles.css` — Brand-derived stylesheet
- `assets/` — Optimized images (WebP + PNG)
- `manifest.json` — Asset inventory

### Phase 4: Quality Checks

1. **Brand compliance**: All colors match palette, typography correct
2. **Accessibility**: Alt text present, contrast ratios meet WCAG AA
3. **Performance**: Images have WebP + fallback, lazy loading for below-fold
4. **Responsiveness**: Assets have responsive sizing

### Phase 5: Generate Integration Report

Output `brands/{BRAND_NAME}/visual-integration-report.md`:

```markdown
# Visual Integration Report: [BRAND_NAME]

## Summary
- Target: [landing-page/pitch-deck/website]
- Assets integrated: X
- Generated: [DATE]

## Assets Used
| Asset ID | Type | Placement | File |
|----------|------|-----------|------|
| hero-001 | Hero Image | Hero section | images/hero-shots/hero-001.png |
| model-001 | 3D Model | Product section | 3d-models/model-001/model.glb |

## Brand Compliance
- Colors: All within palette
- Typography: Correct fonts loaded
- Imagery style: Matches guidelines

## Output Files
- [list of generated files with paths]
```

## Templates

- `templates/landing-page.html` — Base landing page structure
- `templates/pitch-deck-assets.md` — Pitch deck asset integration template
- `templates/styles.css` — Brand-derived stylesheet template

## Integration

- **Upstream**: visual-asset-generator (consumes manifest), visual-identity-core
- **Integrates with**: pitchdeck-skill *(deferred — Phase 4)*, campaign-page-builder, visual-slidedeck-generator *(deferred — Phase 4)*
- **Part of**: brand-visual-pipeline orchestrator
