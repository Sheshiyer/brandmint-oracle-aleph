# Brandmint

> Mint production-ready visual brand assets from a single YAML config.

Brandmint transforms a `brand-config.yaml` definition into 19+ production-ready visual assets using [FAL.AI](https://fal.ai) image generation models. One config file defines your brand's colors, typography, photography style, and aesthetic language — the pipeline generates scripts that produce consistent, on-brand visuals across every asset type.

## What It Generates

| Category | Assets | Model |
|----------|--------|-------|
| **Brand Identity** | Bento Grid (2A), Seal (2B), Logo Emboss (2C) | Nano Banana Pro / Flux 2 Pro |
| **Products** | Capsule Collection (3A), Hero Book (3B), Essence Vial (3C) | Flux 2 Pro |
| **Photography** | Catalog Layout (4A), Flatlay (4B) | Nano Banana Pro / Flux 2 Pro |
| **Illustration** | Heritage Engraving (5A), Campaign Grid (5B), Art Panel (5C), Icon Sets (5D) | Recraft V3 / Nano Banana Pro |
| **Narrative** | Contact Sheets (7A) | Nano Banana Pro |
| **Campaign** | Seeker Poster (8A), Engine Posters (9A), Sequences (10A-C) | Nano Banana Pro |

**Estimated cost:** ~$2-3 per full brand run (19 assets × 2 seed variants).

## Quick Start

```bash
# 1. Set up environment
cd brandmint
uv venv .venv && source .venv/bin/activate
uv pip install -r requirements.txt

# 2. Set your FAL API key
echo "FAL_KEY=your_key_here" >> ~/.claude/.env

# 3. Create a brand config (interactive)
python3 scripts/init_brand.py --output ./my-brand/brand-config.yaml

# 4. Generate pipeline scripts
python3 scripts/generate_pipeline.py ./my-brand/brand-config.yaml --output-dir ./my-brand

# 5. Execute (anchor first, then rest in parallel)
python3 scripts/run_pipeline.py execute --config ./my-brand/brand-config.yaml --batch anchor
python3 scripts/run_pipeline.py execute --config ./my-brand/brand-config.yaml --batch all
```

## Brand Config

Every brand is defined by a single `brand-config.yaml` file. See [`assets/brand-config-schema.yaml`](assets/brand-config-schema.yaml) for the full schema and [`assets/example-tryambakam-noesis.yaml`](assets/example-tryambakam-noesis.yaml) for a working example.

Key sections:

- **`brand:`** — Name, tagline, archetype, voice, domain
- **`theme:`** — Visual theme name, metaphor, mood keywords
- **`palette:`** — 5 colors with hex codes and usage roles (60/30/10 split)
- **`typography:`** — Header, body, and data fonts with weights
- **`aesthetic:`** — Override default visual language (prevents all brands from looking the same)
- **`logo_files:`** — Point to actual logo PNGs for visual reference injection
- **`products:`** — What the brand sells (drives product photography prompts)
- **`prompts:`** — Which asset types to generate

## How It Works

```
brand-config.yaml
       ↓
  generate_pipeline.py    →  7 Python scripts + prompt cookbook
       ↓
  run_pipeline.py         →  Executes scripts against FAL.AI
       ↓
  generated/              →  19+ PNG assets with consistent brand identity
```

**Style Anchor Cascade:** The 2A Bento Grid is generated first and uploaded as a visual reference to all subsequent Nano Banana Pro calls, ensuring style consistency across the entire asset set.

## AI Models

| Model | Use | Cost/call | Image Refs |
|-------|-----|-----------|------------|
| **Nano Banana Pro** | Complex compositions, multi-element layouts | ~$0.08 | Yes (image_urls) |
| **Flux 2 Pro** | Clean product shots, seals, logos | ~$0.05 | No |
| **Recraft V3** | Vector illustrations, icons, engravings | ~$0.04 | No |

## Claude Code Integration

Brandmint works as a Claude Code skill. When symlinked to `~/.claude/skills/brandmint`, it automatically triggers on brand-related prompts and provides the full pipeline workflow.

## License

MIT
