# Brandmint Development Guide

Brand identity orchestration system that transforms `brand-config.yaml` into marketing outputs: text strategies, AI-generated visual assets (via FAL.AI), and campaign copy.

## Build & Test

```bash
# Install (Python 3.10+, use uv)
uv venv .venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# Run all tests
pytest

# Run single test
pytest tests/test_hydrator.py::TestHydrateBrandConfig::test_hydrates_buyer_persona -v

# Lint
ruff check brandmint/
```

## CLI Commands

```bash
# Main entry points (both work)
brandmint [command]
bm [command]

# Full pipeline wizard (depth: surface|focused|comprehensive|exhaustive)
bm launch --config brand-config.yaml --scenario crowdfunding-lean --waves 1-3

# Visual asset generation (3-phase)
bm visual generate --config brand-config.yaml           # Phase 1: Generate scripts
bm visual execute --config brand-config.yaml --batch anchor     # Phase 2a: Anchor FIRST
bm visual execute --config brand-config.yaml --batch identity   # Phase 2b: Parallel batches
bm visual execute --config brand-config.yaml --batch products
bm visual execute --config brand-config.yaml --batch photography
bm visual execute --config brand-config.yaml --batch all        # Or run all remaining
bm visual verify --config brand-config.yaml             # Phase 3: Validate

# Scenario planning
bm plan context --config brand-config.yaml
bm plan recommend --config brand-config.yaml

# Skill management
bm install skills    # Creates symlinks in ~/.claude/skills/
bm install check     # Verify installation
bm registry list     # List all 44 skills
```

## Architecture

### Wave-Based Execution

Skills execute in dependency-ordered waves (1→6). Use `depth` to control how many waves run:

| Depth | Waves | Use Case |
|-------|-------|----------|
| `surface` | 1-2 | Quick positioning only |
| `focused` | 1-5 | Standard launch (default) |
| `comprehensive` | 1-6 | Full campaign |
| `exhaustive` | all | Enterprise/premium |

| Wave | Purpose | Examples |
|------|---------|----------|
| 1 | Foundation | buyer-persona, competitor-analysis |
| 2 | Strategy | product-positioning-summary, voice-and-tone |
| 3 | Visual Identity | visual-identity-core + assets 2A/2B/2C |
| 4 | Products & Content | campaign-page-copy + assets 3A/3B/4A |
| 5 | Campaign Assets | email sequences + assets 5A/7A/8A |
| 6 | Distribution | ads, press, social |

### Scenarios

Pre-built execution profiles that filter skills and set execution context:

| Scenario ID | Budget | Best For |
|-------------|--------|----------|
| `brand-genesis` | Bootstrapped | Pre-launch foundation |
| `crowdfunding-lean` | Lean | Kickstarter/Indiegogo essentials |
| `crowdfunding-full` | Standard | Full crowdfunding campaign |
| `bootstrapped-dtc` | Bootstrapped | Shopify/organic launch |
| `enterprise-gtm` | Premium | B2B SaaS go-to-market |
| `custom-hybrid` | Any | Pick-and-choose skills |

### Style Anchor Cascade

**Critical:** The 2A Bento Grid MUST generate before all other visual assets. It's uploaded as a visual reference to all subsequent Nano Banana Pro calls to ensure style consistency.

### Domain Tags & Asset Filtering

Assets are filtered by `brand.domain_tags` in config. Only matching assets are generated:

| Tag | Assets Included |
|-----|-----------------|
| `*` (universal) | 2A, 2B (always generated) |
| `dtc`, `crowdfunding` | 2C, 3A, 3B, 4A, 4B, 5A-C, 7A, 8A |
| `app`, `saas` | APP-ICON, APP-SCREENSHOT, OG-IMAGE |
| `social` | IG-STORY, TWITTER-HEADER |
| `enterprise` | PITCH-HERO, 2C |

### Image Providers

Brandmint supports multiple image generation providers. Set via env var or config:

```bash
# Environment variable
export IMAGE_PROVIDER=fal  # or: openrouter, openai, replicate, auto

# Or in brand-config.yaml
generation:
  provider: openrouter
```

| Provider | Env Var | Style Anchor | Notes |
|----------|---------|--------------|-------|
| **FAL.AI** (default) | `FAL_KEY` | ✅ Full | Best consistency, recommended |
| **OpenRouter** | `OPENROUTER_API_KEY` | ❌ | Unified API, text-only prompts |
| **OpenAI** | `OPENAI_API_KEY` | ⚠️ Limited | DALL-E 3 has fixed sizes |
| **Replicate** | `REPLICATE_API_TOKEN` | ⚠️ Limited | Pay-per-second pricing |

**Important:** Only FAL.AI's Nano Banana Pro supports image references (style anchor cascade). Other providers use text-only prompts.

### Cost Estimation

| Item | FAL | OpenRouter | OpenAI |
|------|-----|------------|--------|
| Full brand run (19 assets × 2 seeds) | ~$2-3 | ~$2-2.50 | ~$3-4 |
| Nano Banana Pro equivalent | $0.08/img | $0.05/img | $0.08/img |
| Flux 2 Pro equivalent | $0.05/img | $0.05/img | $0.04/img |
| Recraft V3 equivalent | $0.04/img | $0.04/img | $0.04/img |

Use `bm visual preview --config brand-config.yaml --json` for detailed cost breakdown.

### Hydrator Pattern

Text skill outputs are fed back into `brand-config.yaml` for downstream consumption:

```python
from brandmint.core.hydrator import hydrate_brand_config

# HYDRATION_MAP defines the mappings:
# buyer-persona        → audience.persona_name, audience.aspiration, audience.pain_points
# product-positioning  → positioning.statement, positioning.pillars
# mds-messaging        → positioning.hero_headline, positioning.tagline
# voice-and-tone       → brand.voice, brand.tone
# competitor-analysis  → competitive_context.differentiate_from
```

**Backup behavior:** `save_hydrated_config()` creates `.yaml.bak` before overwriting.

### Skills Registry (3-Source Discovery)

Skills are discovered from multiple locations, later sources override earlier:
1. `skills/manifest.yaml` (orchestrator manifest)
2. `brandmint/skills/**/SKILL.md` (local brand skills)
3. `~/.claude/skills/*/SKILL.md` (Claude skills)

## Key Conventions

### API Keys

Always load from Claude's env file:
```python
from dotenv import load_dotenv
load_dotenv(os.path.expanduser("~/.claude/.env"))
# Expects: FAL_KEY=your_key_here
```

### AI Model Constraints

| Model | Constraint |
|-------|------------|
| Recraft V3 | **1000-char prompt limit** (silently truncates!), returns SVG/WebP (must convert to PNG) |
| Nano Banana Pro | Use `16:9` aspect ratio format, NOT Flux's `landscape_16_9` |
| Flux 2 Pro | No image reference support (can't use style anchor cascade) |

### Product Identity in Prompts

Use specific placeholder `{product_hero_physical}` not generic descriptors — ensures product identity carries through all assets.

### Publishing Pipeline

Transforms brand outputs into documentation sites (requires Bun):

```bash
# 1. Generate wiki markdown from brand outputs (wiki-doc-generator skill)

# 2. Build Astro site with iOS26 glassmorphism design
./skills/publishing/markdown-to-astro-wiki/scripts/init-astro-wiki.sh my-wiki
./skills/publishing/markdown-to-astro-wiki/scripts/process-markdown.sh ./docs ./my-wiki/src/content/docs
cd my-wiki && bun run build
```

### Brand Config Schema

Every brand is defined by `brand-config.yaml`. Reference:
- Schema: `assets/brand-config-schema.yaml`
- Example: `assets/example-tryambakam-noesis.yaml`

Key sections: `brand`, `theme`, `palette`, `typography`, `aesthetic`, `logo_files`, `products`, `prompts`

## Project Structure

```
brandmint/
├── cli/           # Typer CLI (app.py is entry point)
├── core/          # Business logic
│   ├── wave_planner.py       # Wave computation engine
│   ├── skills_registry.py    # 3-source skill discovery
│   ├── hydrator.py           # Feeds skill outputs → config
│   └── scenario_recommender.py
├── models/        # Pydantic models
├── pipeline/      # Pipeline executor
└── installer/     # Symlink management
scripts/           # Standalone pipeline scripts
skills/            # 44 skills across 9 categories
assets/            # Schema, registry, examples
```
