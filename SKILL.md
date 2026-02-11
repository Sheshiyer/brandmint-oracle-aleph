---
name: brandmint
description: End-to-end brand identity orchestration system. Generates text strategy, visual assets, campaign copy, and publishing outputs using 44 specialized skills across 9 categories. Chains FAL.AI/Nano Banana/Flux visual generation with brand positioning, buyer personas, and campaign workflows via wave-based execution.
---

# Brandmint

Orchestrated brand identity system that transforms a brand definition into comprehensive marketing outputs — from strategic text documents through AI-generated visual assets to published documentation sites.

## Architecture Overview

```
brand-config.yaml
       |
  Wave Planner ──── Scenario Recommender
       |                    |
  ┌────┴────┐         (selects skills
  │  Waves  │          for scenario)
  │  1 → 6  │
  └────┬────┘
       |
  Skills Registry (44 skills, 9 categories)
       |
  Hydrator (feeds outputs into config)
       |
  Generate Pipeline (FAL.AI visual assets)
       |
  Publishing Pipeline (wiki → Astro site)
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

Skills execute in dependency-ordered waves:

| Wave | Skills | Purpose |
|------|--------|---------|
| 1 | buyer-persona, competitor-analysis | Foundation research |
| 2 | product-positioning-summary, mds-messaging-direction-summary | Strategic positioning |
| 3 | voice-and-tone, visual-identity-core | Brand personality |
| 4 | campaign-page-copy, detailed-product-description | Core copy |
| 5 | email sequences, social-content-engine, ads | Channels |
| 6 | Visual pipeline, publishing pipeline | Assets & output |

## Hydrator

The hydrator feeds text skill outputs back into `brand-config.yaml` for downstream consumption:

| Skill Output | Config Section |
|-------------|---------------|
| buyer-persona | `hydrated.buyer_persona` |
| product-positioning-summary | `hydrated.positioning` |
| mds-messaging-direction-summary | `hydrated.messaging` |
| voice-and-tone | `hydrated.voice` |
| competitor-analysis | `hydrated.competitors` |

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
| `brandmint/core/skills_registry.py` | 3-source skill discovery (orchestrator + brand + Claude) |
| `brandmint/core/scenario_recommender.py` | Scenario-based skill selection |
| `brandmint/installer/setup_skills.py` | Symlink management for Claude Code discovery |

## Critical Learnings

1. **Anchor cascade** — Style anchor bento MUST generate before all other visual assets
2. **Recraft V3 returns SVG/WebP** — Must detect and convert to PNG
3. **Recraft 1000-char limit** — Prompts silently truncate
4. **Product identity in prompts** — Use `{product_hero_physical}` not generic descriptors
5. **Nano Banana aspect ratios** — Use `16:9` format not Flux `landscape_16_9`
6. **API keys** — Always `load_dotenv(os.path.expanduser("~/.claude/.env"))`
