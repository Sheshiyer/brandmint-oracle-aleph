# FAL.AI Model Routing Guide

Decision tree for selecting the right FAL.AI model for each asset type.

## Model Overview

| Model | Endpoint | Best For | Supports Image Ref |
|-------|----------|----------|-------------------|
| **Nano Banana Pro** | `fal-ai/nano-banana-pro` | Photorealistic products, scenes, contact sheets | Yes (`image_urls`) |
| **Flux 2 Pro** | `fal-ai/flux-2-pro` | High-fidelity text rendering, standalone products | No |
| **Recraft V3** | `fal-ai/recraft/v3/text-to-image` | Vector icons, digital illustrations | No (uses `colors`) |

## Decision Tree

```
Is it photorealistic with complex scene/environment?
├── YES → Does it need style anchor consistency?
│   ├── YES → Nano Banana Pro (with image_urls=[anchor])
│   └── NO  → Flux 2 Pro
├── NO → Is it a vector icon or line illustration?
│   ├── YES → Recraft V3 (vector_illustration/line_circuit)
│   └── NO  → Is it a digital illustration with color planes?
│       ├── YES → Recraft V3 (digital_illustration)
│       └── NO  → Flux 2 Pro (default)
```

## Model Parameters

### Nano Banana Pro

```python
fal_client.subscribe(
    "fal-ai/nano-banana-pro",
    arguments={
        "prompt": full_prompt,
        "image_urls": [anchor_url, comp_ref_url],  # Style anchor + composition ref
        "aspect_ratio": "16:9",  # or "1:1", "3:4", "4:3"
        "resolution": "2K",
        "output_format": "png",
        "seed": 42,
        "num_images": 1,
    },
)
```

**Key parameter: `image_urls`** — Pass the style anchor (2A bento output) as first element to maintain visual consistency across all assets. Optionally add a composition reference image as second element.

### Flux 2 Pro

```python
fal_client.subscribe(
    "fal-ai/flux-2-pro",
    arguments={
        "prompt": full_prompt,
        "image_size": "landscape_16_9",  # or "square_hd", "portrait_4_3", "landscape_4_3"
        "num_images": 1,
        "seed": 42,
    },
)
```

**Note:** Flux 2 Pro does NOT support `image_urls`. Use for standalone assets that don't need anchor consistency.

### Recraft V3

```python
fal_client.subscribe(
    "fal-ai/recraft/v3/text-to-image",
    arguments={
        "prompt": condensed_prompt,  # MUST be under 1000 chars!
        "image_size": "square_hd",   # or "portrait_4_3", "landscape_4_3"
        "style": "vector_illustration/line_circuit",  # or "digital_illustration"
        "seed": 42,
        "colors": [{"rgb": "#0A1628"}, {"rgb": "#F0EDE3"}],  # Palette-lock
    },
)
```

**Critical gotchas:**
- `vector_illustration` styles → returns **SVG** (must convert to PNG)
- `digital_illustration` styles → returns **WebP** (must convert to PNG)
- Prompt limit: **1000 characters** (silently truncates beyond this)
- Colors: Must wrap hex in `{"rgb": "#hex"}` format

## Asset-to-Model Mapping

| Asset ID | Asset Type | Model | Aspect | Style |
|----------|-----------|-------|--------|-------|
| 2A | Bento Grid (anchor) | Nano Banana Pro | 16:9 | — |
| 2B | Brand Seal | Flux 2 Pro | square_hd | — |
| 2C | Logo Emboss | Flux 2 Pro | landscape_16_9 | — |
| 3A | Capsule Collection | Flux 2 Pro | landscape_4_3 | — |
| 3B | Hero Book | Flux 2 Pro | square_hd | — |
| 3C | Essence Vial | Nano Banana Pro | 1:1 | — |
| 4A | Catalog Layout | Nano Banana Pro | 3:4 | — |
| 4B | Flatlay | Flux 2 Pro | square_hd | — |
| 5A | Heritage Engraving | Recraft V3 | square_hd | digital_illustration |
| 5B | Campaign Grid | Nano Banana Pro | 3:4 | — |
| 5C | Art Panel | Recraft V3 | portrait_4_3 | digital_illustration |
| 5D | Engine Icons | Recraft V3 | square_hd | vector_illustration/line_circuit |
| 7A | Contact Sheet | Nano Banana Pro | 1:1 | — |
| 8A | Seeker Poster | Nano Banana Pro | 3:4 | — |
| 9A | Engine Posters | Nano Banana Pro | 3:4 | — |
| 10A-C | Ritual Sequences | Nano Banana Pro | 1:1 | — |

## Format Conversion Reference

### SVG to PNG (from Recraft vector_illustration)
```bash
# Requires: brew install librsvg
rsvg-convert -w 2048 -h 2048 --keep-aspect-ratio file.svg -o file.png
```

### WebP to PNG (from Recraft digital_illustration)
```bash
# macOS built-in
sips -s format png file.webp --out file.png
```
