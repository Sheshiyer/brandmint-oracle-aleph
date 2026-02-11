````skill
---
name: brandmint
description: End-to-end brand identity orchestration system. Generates text strategy, visual assets, campaign copy, and publishing outputs using 44 specialized skills across 9 categories. Chains FAL.AI/Nano Banana/Flux visual generation with brand positioning, buyer personas, and campaign workflows via wave-based execution.
---

# Brandmint

Orchestrated brand identity system that transforms a brand definition into comprehensive marketing outputs — from strategic text documents through AI-generated visual assets to published documentation sites.

## Architecture Overview

```
brand-config.yaml
       ↓
┌─────────────┐     ┌───────────────────┐
│ Wave Planner│←────│Scenario Recommender│
└──────┬──────┘     └───────────────────┘
       ↓
   Waves 1→6
       ↓
   Skills Registry (44 skills, 9 categories)
       ↓
   Hydrator (feeds outputs → config)
       ↓
   Visual Pipeline (FAL.AI assets)
       ↓
   Publishing Pipeline (wiki → Astro)
```

## Prerequisites

- Python 3.10+ with `uv` package manager
- FAL_KEY in `~/.claude/.env`
- Dependencies: `python-dotenv`, `fal-client`, `requests`, `pyyaml`
- Bun (for Astro wiki publishing)

```bash
uv venv .venv && source .venv/bin/activate
uv pip install python-dotenv fal-client requests pyyaml
```

## CLI Commands

```bash
# Main entry points (both work)
brandmint [command]
bm [command]

# Global flags (available on all commands)
bm --verbose launch ...   # Enable verbose logging
bm --debug launch ...     # Maximum verbosity
bm --quiet launch ...     # Suppress most output

# Full pipeline wizard
bm launch --config brand-config.yaml --scenario crowdfunding-lean --waves 1-3
bm launch --config brand-config.yaml --max-cost 5.00     # Abort if cost exceeds budget
bm launch --config brand-config.yaml --resume-from 3      # Resume from specific wave

# Visual asset generation (3-phase)
bm visual generate --config brand-config.yaml           # Phase 1: Generate scripts
bm visual execute --config brand-config.yaml --batch anchor     # Phase 2a: Anchor FIRST
bm visual execute --config brand-config.yaml --batch identity   # Phase 2b: Parallel batches
bm visual execute --config brand-config.yaml --batch all        # Or run all remaining
bm visual execute --config brand-config.yaml --force            # Bypass cache, regenerate
bm visual verify --config brand-config.yaml             # Phase 3: Validate

# Execution reports
bm report --config brand-config.yaml                    # Console summary
bm report --config brand-config.yaml --format json      # JSON output
bm report --config brand-config.yaml --format html -o report.html

# Cache management
bm cache stats                                          # Show cache statistics
bm cache clear                                          # Clear all cached prompts
bm cache clear --expired                                # Clear only expired entries

# Scenario planning
bm plan context --config brand-config.yaml
bm plan recommend --config brand-config.yaml

# Skill management
bm install skills    # Creates symlinks in ~/.claude/skills/
bm install check     # Verify installation
bm registry list     # List all 44 skills
```

## Image Providers

Set via env var or config (`generation.provider` in brand-config.yaml):

| Provider | Env Var | Style Anchor | Notes |
|----------|---------|--------------|-------|
| **FAL.AI** (default) | `FAL_KEY` | ✅ Full | Best consistency, recommended |
| **OpenRouter** | `OPENROUTER_API_KEY` | ❌ | Unified API, text-only prompts |
| **OpenAI** | `OPENAI_API_KEY` | ⚠️ Limited | DALL-E 3 has fixed sizes |
| **Replicate** | `REPLICATE_API_TOKEN` | ⚠️ Limited | Pay-per-second pricing |

**Note:** Only FAL.AI's Nano Banana Pro supports image references (style anchor cascade).

## Skill Categories (44 skills)

| Category | Count | Purpose |
|----------|-------|---------|
| `text-strategy/` | 7 | Brand positioning, personas, voice, competitive analysis |
| `visual-prompters/` | 9 | AI image prompt generation (product, fashion, editorial, brand) |
| `campaign-copy/` | 6 | Campaign page copy, ads, hooks, press releases |
| `email-sequences/` | 3 | Welcome, pre-launch, and launch email sequences |
| `brand-foundation/` | 3 | Visual identity, brand naming, logo concept design |
| `social-growth/` | 5 | Social content calendar, community, influencer outreach |
| `advertising/` | 5 | Pre-launch ads, competitive ad extraction, niche validation |
| `publishing/` | 2 | Wiki doc generation + Astro site builder |
| `visual-pipeline/` | 4 | AI visual asset generation + integration orchestrator |

## Workflow Routing

- **"Create a brand for [X]"** → Full orchestration: Waves 1-6 → visual pipeline → publishing
- **"Generate assets for [X]"** → Execute visual pipeline only (needs existing config)
- **"Build wiki from outputs"** → Publishing pipeline: wiki-doc-generator → markdown-to-astro-wiki
- **"Run [skill-name] for [X]"** → Individual skill execution

## Wave Execution

Skills execute in dependency-ordered waves. Use `depth` to control how many waves run:

| Depth | Waves | Use Case |
|-------|-------|----------|
| `surface` | 1-2 | Quick positioning only |
| `focused` | 1-5 | Standard launch (default) |
| `comprehensive` | 1-6 | Full campaign |
| `exhaustive` | all | Enterprise/premium |

| Wave | Skills | Purpose |
|------|--------|---------|
| 1 | buyer-persona, competitor-analysis | Foundation research |
| 2 | product-positioning-summary, mds-messaging-direction-summary | Strategic positioning |
| 3 | voice-and-tone, visual-identity-core | Brand personality |
| 4 | campaign-page-copy, detailed-product-description | Core copy |
| 5 | email sequences, social-content-engine, ads | Channels |
| 6 | Visual pipeline, publishing pipeline | Assets & output |

## Scenarios

Pre-built execution profiles that filter skills and set execution context:

| Scenario ID | Budget | Best For |
|-------------|--------|----------|
| `brand-genesis` | Bootstrapped | Pre-launch foundation |
| `crowdfunding-lean` | Lean | Kickstarter/Indiegogo essentials |
| `crowdfunding-full` | Standard | Full crowdfunding campaign |
| `bootstrapped-dtc` | Bootstrapped | Shopify/organic launch |
| `enterprise-gtm` | Premium | B2B SaaS go-to-market |
| `custom-hybrid` | Any | Pick-and-choose skills |

## Domain Tags

Assets are filtered by `brand.domain_tags` in config. Only matching assets generate:

| Tag | Assets Included |
|-----|----------------|
| `*` (universal) | 2A, 2B (always generated) |
| `dtc`, `crowdfunding` | 2C, 3A, 3B, 4A, 4B, 5A-C, 7A, 8A |
| `app`, `saas` | APP-ICON, APP-SCREENSHOT, OG-IMAGE |
| `social` | IG-STORY, TWITTER-HEADER |
| `enterprise` | PITCH-HERO, 2C |

## Hydrator

The hydrator feeds text skill outputs back into `brand-config.yaml` for downstream consumption:

| Skill Output | Config Section |
|-------------|---------------|
| buyer-persona | `hydrated.buyer_persona` |
| product-positioning-summary | `hydrated.positioning` |
| mds-messaging-direction-summary | `hydrated.messaging` |
| voice-and-tone | `hydrated.voice` |
| competitor-analysis | `hydrated.competitors` |

**Backup behavior:** `save_hydrated_config()` creates `.yaml.bak` before overwriting.

## Visual Generation Pipeline

```bash
# Phase 1: Generate prompt cookbook + Python scripts
python3 scripts/generate_pipeline.py ./brand-config.yaml

# Phase 2: Execute (anchor first, then parallel batches)
python3 scripts/run_pipeline.py execute --batch anchor
python3 scripts/run_pipeline.py execute --batch identity  # parallel
python3 scripts/run_pipeline.py execute --batch products   # parallel
python3 scripts/run_pipeline.py execute --batch photography # parallel

# Phase 3: Verify
python3 scripts/run_pipeline.py verify --config ./brand-config.yaml
```

## Publishing Pipeline

```bash
# Generate wiki markdown from brand outputs
# (uses wiki-doc-generator skill)

# Build Astro documentation site
./skills/publishing/markdown-to-astro-wiki/scripts/init-astro-wiki.sh my-wiki
./skills/publishing/markdown-to-astro-wiki/scripts/process-markdown.sh ./docs ./my-wiki/src/content/docs
cd my-wiki && bun run build
```

## Key Files

| File | Purpose |
|------|---------|
| `scripts/generate_pipeline.py` | Template engine: config → prompts → generation scripts |
| `scripts/run_pipeline.py` | Pipeline executor with batch dispatch |
| `brandmint/core/wave_planner.py` | Dependency-ordered skill execution |
| `brandmint/core/hydrator.py` | Feeds skill outputs into config |
| `brandmint/core/skills_registry.py` | 3-source skill discovery |
| `brandmint/core/cache.py` | Prompt hash caching for regeneration avoidance |
| `brandmint/cli/report.py` | Execution report generator (markdown/json/html) |
| `brandmint/cli/logging.py` | Structured logging with Rich integration |
| `brandmint/cli/notifications.py` | macOS/Linux desktop + webhook notifications |

## Brand Config Schema

Every brand is defined by `brand-config.yaml`:

- **Schema:** `assets/brand-config-schema.yaml`
- **Example:** `assets/example-tryambakam-noesis.yaml`
- **Key sections:** `brand`, `theme`, `palette`, `typography`, `aesthetic`, `logo_files`, `products`, `prompts`

## Cost Estimation

| Item | FAL | OpenRouter | OpenAI |
|------|-----|------------|--------|
| Full brand run (19 assets × 2 seeds) | ~$2-3 | ~$2-2.50 | ~$3-4 |
| Nano Banana Pro equivalent | $0.08/img | $0.05/img | $0.08/img |
| Flux 2 Pro equivalent | $0.05/img | $0.05/img | $0.04/img |

Use `bm visual preview --config brand-config.yaml --json` for detailed cost breakdown.

## Critical Learnings

1. **Anchor cascade** — Style anchor bento MUST generate before all other visual assets
2. **Recraft V3 returns SVG/WebP** — Must detect and convert to PNG
3. **Recraft 1000-char limit** — Prompts silently truncate
4. **Product identity in prompts** — Use `{product_hero_physical}` not generic descriptors
5. **Nano Banana aspect ratios** — Use `16:9` format not Flux `landscape_16_9`
6. **API keys** — Always `load_dotenv(os.path.expanduser("~/.claude/.env"))`

## Trigger Phrases

Claude should invoke this skill when user says:

- "create a brand", "brand identity", "brand launch"
- "generate brand assets", "visual assets for brand"
- "run brandmint", "execute brand workflow"
- "crowdfunding campaign", "launch campaign"
- "brand positioning", "buyer persona"
- "generate visual pipeline", "brand visuals"

````

