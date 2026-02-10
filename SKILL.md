---
name: brandmint
description: Use when creating a complete visual brand identity system with AI-generated assets. Generates prompt cookbooks, Python generation scripts, and executes FAL.AI pipelines for any brand — from config to 50+ production assets.
---

# Brandmint

End-to-end visual brand generation system. Transform a brand definition into 50+ production-ready visual assets using FAL.AI models (Nano Banana Pro, Flux 2 Pro, Recraft V3).

## Prerequisites

- Python 3.10+ with `uv` package manager
- FAL_KEY in `~/.claude/.env`
- Dependencies: `python-dotenv`, `fal-client`, `requests`, `pyyaml`
- macOS: `brew install librsvg` (for SVG-to-PNG conversion)

Install dependencies:
```bash
uv venv .venv && source .venv/bin/activate
uv pip install python-dotenv fal-client requests pyyaml
```

## Workflow Routing

Route based on intent:

- "Create a visual brand for [X]" or "Build brand assets for [X]" -> **Full Pipeline** (Phase 1-4)
- "Generate assets for [X]" or "Run the pipeline for [X]" -> **Execute Only** (Phase 3-4, needs existing config)
- "Add [type] to [X] brand" or "Extend [X] brand with [type]" -> **Extend** (add template + generate)

---

## Phase 1: Brand Definition

Create the brand config file that drives everything.

**Option A — Interactive:** Run `scripts/init_brand.py`
```bash
python3 scripts/init_brand.py --output ./my-brand/brand-config.yaml
```

**Option B — Manual:** Create `brand-config.yaml` using the schema in `assets/brand-config-schema.yaml`.
See `assets/example-tryambakam-noesis.yaml` for a working reference.

**Option C — From conversation:** Extract brand details from user conversation, populate the YAML programmatically.

Present the config to the user for approval before proceeding.

### Required Config Sections

| Section | Purpose | Critical Fields |
|---------|---------|----------------|
| `brand` | Identity | name, tagline, archetype, voice, domain |
| `theme` | Visual direction | name, description, metaphor, mood_keywords |
| `palette` | Colors | primary/secondary/accent/support/signal with name, hex, role |
| `typography` | Fonts | header, body, data fonts with weights |
| `materials` | Physical vocabulary | List of 8-15 material descriptors |
| `photography` | Camera direction | style, environment, constraint, camera |
| `illustration` | Illustration direction | style, references |
| `negative_prompt` | What to avoid | Multi-line string of negative terms |
| `generation` | Technical settings | output_dir, seeds, resolution, env_file |
| `prompts` | What to generate | Categories with enabled prompt types |

---

## Phase 2: Cookbook + Script Generation

Read config, apply prompt templates, generate Python scripts and markdown cookbook.

```bash
python3 scripts/generate_pipeline.py ./my-brand/brand-config.yaml
```

This produces:
- `my-brand/prompt-cookbook.md` — All prompts with model routing, aspect ratios, references
- `my-brand/scripts/generate-anchor.py` — Style anchor (MUST run first)
- `my-brand/scripts/generate-identity.py` — Brand identity assets (seal, logo)
- `my-brand/scripts/generate-products.py` — Product concepts
- `my-brand/scripts/generate-photography.py` — Product photography
- `my-brand/scripts/generate-illustrations.py` — Illustrations + icons
- `my-brand/scripts/generate-narrative.py` — Contact sheets + sequences
- `my-brand/scripts/generate-posters.py` — Campaign posters

### Prompt Templates

All templates are in `references/prompt-templates.md`. Each uses `{variable}` substitution from the config. Templates cover 20+ asset types across 7 categories.

---

## Phase 3: Execute Pipeline

### Critical: Anchor First

The style anchor (bento grid) MUST generate before all other assets. It establishes visual consistency.

```bash
python3 scripts/run_pipeline.py execute --config ./my-brand/brand-config.yaml --batch anchor
```

### Then: Parallel Batches

After anchor completes, dispatch remaining batches in parallel using `dispatching-parallel-agents`:

```
Agent 1: python3 scripts/run_pipeline.py execute --batch identity
Agent 2: python3 scripts/run_pipeline.py execute --batch products
Agent 3: python3 scripts/run_pipeline.py execute --batch photography
Agent 4: python3 scripts/run_pipeline.py execute --batch illustration
Agent 5: python3 scripts/run_pipeline.py execute --batch narrative
Agent 6: python3 scripts/run_pipeline.py execute --batch posters
```

Each agent runs independently. No shared state between batches.

---

## Phase 4: Verify + Report

```bash
python3 scripts/run_pipeline.py verify --config ./my-brand/brand-config.yaml
```

Check:
- All expected files exist in output directory
- PNG files have valid headers (magic bytes `89 50 4E 47`)
- File sizes > 100KB (rules out broken/empty files)
- SVG/WebP native files preserved alongside PNG conversions
- Report total: X PNG + Y SVG + Z WebP = N total files

---

## Critical Learnings (Read `references/learnings.md` for full details)

These are hard-won patterns from production use. Violating them causes broken assets.

1. **Recraft V3 returns SVG for `vector_illustration`, WebP for `digital_illustration`** — NO API parameter to override. Must detect and convert.
2. **Recraft 1000-char prompt limit** — Prompts silently truncate. Always condense for Recraft.
3. **Style anchor cascade** — Upload bento output via `fal_client.upload_file()`, pass as `image_urls=[anchor_url]` to all Nano Banana Pro calls.
4. **SVG-to-PNG** — `rsvg-convert -w 2048 -h 2048 --keep-aspect-ratio file.svg -o file.png`
5. **WebP-to-PNG** — `sips -s format png file.webp --out file.png` (macOS)
6. **API keys** — Always `load_dotenv(os.path.expanduser("~/.claude/.env"))`. Never hardcode.
7. **Seed strategy** — seed 42 (v1), seed 137 (v2). Two variations per prompt.

See `references/model-routing-guide.md` for the complete model selection decision tree.

---

## Extend Workflow

Add new prompt types to an existing brand:

1. Define new template in `references/prompt-templates.md` using existing variables
2. Add entry to config `prompts` section
3. Re-run `generate_pipeline.py` — only new scripts generated
4. Execute new batch only

---

## File Naming Convention

All generated assets follow: `{ID}-{slug}-{model}-{variant}.{ext}`

Examples:
- `2A-brand-kit-bento-nanobananapro-v1.png`
- `5D-1-vedic-engine-icons-recraft-v1.svg`
- `9A-01-vimshottari-dasha-poster-v1.png`
