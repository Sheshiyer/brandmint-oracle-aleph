# Brandmint

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-4.1.0-green.svg)](https://github.com/Sheshiyer/brandmint-oracle-aleph/releases/tag/v4.1.0)
[![Claude Code](https://img.shields.io/badge/Claude_Code-Install-blueviolet?logo=anthropic)](#claude-code)
[![Claude Desktop](https://img.shields.io/badge/Claude_Desktop-MCP-purple?logo=anthropic)](#claude-desktop)
[![GitHub Copilot](https://img.shields.io/badge/Copilot-Compatible-black?logo=github)](#github-copilot)
[![Cursor IDE](https://img.shields.io/badge/Cursor-Compatible-00D084)](#cursor-ide)

> End-to-end brand identity orchestration — from strategy to visual assets to campaign copy to published documentation sites.

Brandmint transforms a single `brand-config.yaml` into comprehensive marketing outputs using **44 specialized skills across 9 categories**. The system chains text strategy (buyer personas, positioning, voice) through AI-generated visual assets (via FAL.AI) to campaign copy, and now includes a **full publishing pipeline** that generates wiki documentation and glassmorphism Astro sites with automatic visual asset integration.

## What It Does

```
brand-config.yaml
       │
  Wave Planner ──── Scenario Recommender
       │                    │
  ┌────┴────┐         (selects skills
  │  Waves  │          for scenario)
  │  1 → 6  │
  └────┬────┘
       │
  Skills Registry (44 skills, 9 categories)
       │
  Hydrator (feeds outputs into config)
       │
  Visual Pipeline (FAL.AI: 19+ assets)
       │
  Publishing Pipeline (wiki → Astro site)
       │
  ┌────┴────────────────┐
  │  Wiki Documentation │ → Glassmorphism Astro Site
  │  (parallel agents)  │   with visual asset integration
  └─────────────────────┘
```

## Skill Categories (44 skills)

| Category | Skills | Purpose |
|----------|--------|---------|
| **text-strategy/** | 7 | Buyer personas, positioning, voice, competitive analysis |
| **visual-prompters/** | 9 | AI image prompt generation (product, fashion, editorial) |
| **campaign-copy/** | 6 | Campaign pages, video scripts, press releases |
| **email-sequences/** | 3 | Welcome, pre-launch, launch email flows |
| **brand-foundation/** | 3 | Packaging design, unboxing experience |
| **social-growth/** | 5 | Content calendar, influencer outreach, community |
| **advertising/** | 5 | Pre-launch ads, live campaign ads, affiliate programs |
| **publishing/** | 2 | Wiki generation, Astro site builder |
| **visual-pipeline/** | 4 | FAL.AI asset generation orchestration |

## Wave Execution

Skills execute in dependency-ordered waves:

| Wave | Purpose | Examples |
|------|---------|----------|
| 1 | Foundation | buyer-persona, competitor-analysis, niche-validator |
| 2 | Strategy | product-positioning, voice-and-tone, messaging-direction |
| 3 | Visual Identity | visual-identity-core + assets 2A/2B/2C |
| 4 | Products & Content | campaign-page-copy + assets 3A/3B/4A |
| 5 | Campaign Assets | email sequences + assets 5A/7A/8A |
| 6 | Distribution | ads, press, social content |

## Scenarios

Pre-built execution profiles that select skills and set context:

| Scenario | Budget | Best For |
|----------|--------|----------|
| `brand-genesis` | Bootstrapped | Pre-launch foundation building |
| `crowdfunding-lean` | Lean | Kickstarter/Indiegogo essentials |
| `crowdfunding-full` | Standard | Full crowdfunding campaign |
| `bootstrapped-dtc` | Bootstrapped | Shopify/organic DTC launch |
| `enterprise-gtm` | Premium | B2B SaaS go-to-market |

## Quick Start

```bash
# 1. Install
curl -sSL https://raw.githubusercontent.com/brandmint/brandmint/main/install.sh | bash

# 2. Set your image provider API key (FAL.AI recommended, but supports multiple providers)
echo "FAL_KEY=your_key_here" >> ~/.claude/.env
# Or use: OPENROUTER_API_KEY, OPENAI_API_KEY, or REPLICATE_API_TOKEN

# 3. Create a brand config
bm init --output ./my-brand/brand-config.yaml

# 4. Get scenario recommendations
bm plan recommend --config ./my-brand/brand-config.yaml

# 5. Launch full pipeline (text + visuals)
bm launch --config ./my-brand/brand-config.yaml --scenario crowdfunding-lean
```

### Non-Interactive Mode (Agents & CI)

For agent environments (Claude Code Desktop, API, CI pipelines) where TTY prompts aren't available:

```bash
# Fully automated — no prompts, auto-detects scenario, runs all waves
bm launch --config ./my-brand/brand-config.yaml \
  --scenario brand-genesis \
  --waves 1-6 \
  --non-interactive

# With cost guard
bm launch --config ./my-brand/brand-config.yaml \
  --scenario brand-genesis \
  --non-interactive \
  --max-cost 5.00

# Resume from a specific wave
bm launch --config ./my-brand/brand-config.yaml \
  --resume-from 4 \
  --non-interactive
```

The pipeline auto-detects non-interactive environments via `sys.stdin.isatty()` and falls back gracefully — no `Confirm.ask()` blocking, no skipped skills.

## Image Providers

Brandmint supports multiple image generation providers:

| Provider | Style Anchor Support | Cost | Best For |
|----------|---------------------|------|----------|
| **FAL.AI** (default) | Full | $0.04-0.08/img | Maximum consistency |
| **OpenRouter** | Text-only | $0.03-0.05/img | Single API key |
| **OpenAI** | Limited | $0.04-0.08/img | Creative variations |
| **Replicate** | Limited | $0.03-0.05/img | Budget batches |

```bash
# Set provider via env var
export IMAGE_PROVIDER=openrouter

# Or in brand-config.yaml
generation:
  provider: openrouter
```

See [docs/providers.md](docs/providers.md) for full provider documentation.

Or run just the visual pipeline:

```bash
bm visual generate --config ./my-brand/brand-config.yaml
bm visual execute --config ./my-brand/brand-config.yaml --batch anchor  # Style anchor FIRST
bm visual execute --config ./my-brand/brand-config.yaml --batch all
```

## Visual Assets Generated

| Category | Assets | Model |
|----------|--------|-------|
| **Brand Identity** | Bento Grid (2A), Seal (2B), Logo Emboss (2C) | Nano Banana Pro / Flux 2 Pro |
| **Products** | Capsule Collection (3A), Hero Book (3B), Essence Vial (3C) | Flux 2 Pro |
| **Photography** | Catalog Layout (4A), Flatlay (4B) | Nano Banana Pro / Flux 2 Pro |
| **Illustration** | Heritage Engraving (5A), Campaign Grid (5B), Art Panel (5C) | Recraft V3 / Nano Banana Pro |
| **Icons** | Regional Traditions (5D-1), Life Ceremonies (5D-2), Epic Narratives (5D-3) | Flux 2 Pro |
| **Campaign** | Contact Sheets (7A), Seeker Poster (8A), Poster Series (9A), Sequences (10A-C) | Nano Banana Pro |
| **Social** | Email Hero, IG Story, OG Image, Twitter Header | Nano Banana Pro / Flux 2 Pro |

**Cost:** ~$2-4 per full visual run (26 asset IDs x 2 seeds)

## Publishing Pipeline

After pipeline execution, brandmint includes two post-pipeline publishing skills that transform outputs into a complete documentation site:

### Wiki Documentation Generation

Transforms `.brandmint/outputs/*.json` into structured, interconnected wiki markdown using parallel agent dispatch:

```bash
# Inventory source documents (text + visual assets)
python3 scripts/inventory-sources.py /path/to/.brandmint/outputs/

# Map visual assets to wiki pages
python3 scripts/map-assets-to-wiki.py /path/to/generated/

# Agents generate wiki pages in parallel (4-6 agents via Task tool)
```

Outputs structured markdown with frontmatter, cross-references, and automatic image embedding from 26 visual asset categories.

### Astro Wiki Site Builder

Converts wiki markdown into a glassmorphism-styled Astro site:

```bash
# Initialize Astro project
./scripts/init-astro-wiki.sh my-wiki

# Process markdown WITH visual assets
./scripts/process-markdown.sh wiki-output/ my-wiki/src/content/docs --images generated/

# Build
cd my-wiki && bun run build
```

Features iOS26-inspired glassmorphism design, dark/light mode, search, and automatic visual asset integration.

## Key Architecture

### Hydrator Pattern
Text skill outputs automatically feed back into `brand-config.yaml`:
- `buyer-persona` → `audience.persona_name`, `audience.pain_points`
- `voice-and-tone` → `brand.voice`, `brand.tone`
- `product-positioning` → `positioning.statement`, `positioning.pillars`

### Style Anchor Cascade
The 2A Bento Grid generates first and serves as visual reference for all subsequent Nano Banana Pro calls — ensuring style consistency across all assets.

### Domain-Aware Asset Selection
Assets auto-filter based on `brand.domain_tags` (dtc, saas, app, crowdfunding). Only relevant assets are generated.

### Visual Asset Integration
The `map-assets-to-wiki.py` script bridges visual assets to wiki pages using a 26-category mapping. Each asset ID (2A, 3B, 5D-1, etc.) maps to specific wiki pages with roles (hero, inline, gallery, meta). The `process-markdown.sh --images` flag copies all generated assets to the Astro site's `public/images/` directory.

## CLI Reference

```bash
bm launch     # Full pipeline wizard (text + visuals)
bm plan       # Scenario planning (context, recommend, compare)
bm visual     # Visual pipeline (generate, execute, verify, status)
bm registry   # Skill management (list, info, sync)
bm install    # Setup (skills, check)
bm report     # Execution reports (markdown, json, html)
bm cache      # Cache management (stats, clear)
bm version    # Version info
```

### Key Flags

| Flag | Command | Purpose |
|------|---------|---------|
| `--non-interactive` | `bm launch` | Skip all TTY prompts (agents/CI) |
| `--dry-run` | `bm launch` | Show plan without executing |
| `--max-cost` | `bm launch` | Abort if estimated cost exceeds budget |
| `--resume-from` | `bm launch` | Resume from specific wave number |
| `--webhook` | `bm launch` | POST notification on completion |
| `--json` | `bm launch` | Agent-compatible JSON output |
| `--force` | `bm visual execute` | Bypass cache, regenerate all |

## Agent Execution

Brandmint includes a `CLAUDE.md` at the repo root that guides any Claude agent operating in the repository. This prevents agents from running skills individually (which breaks the dependency chain) and directs them to use `bm launch --non-interactive` instead.

Key paths for agent environments:
- **Brand config:** `<brand-dir>/brand-config.yaml`
- **Prompts:** `<brand-dir>/.brandmint/prompts/`
- **Outputs:** `<brand-dir>/.brandmint/outputs/`
- **Visual assets:** `<brand-dir>/<brand-slug>/generated/`
- **Pipeline state:** `<brand-dir>/.brandmint/state.json`

## AI Assistant Installation

<details>
<summary><strong>Claude Code</strong></summary>

One-line install:
```bash
curl -sSL https://raw.githubusercontent.com/brandmint/brandmint/main/install.sh | bash
```

Or manual:
```bash
git clone https://github.com/brandmint/brandmint.git ~/.claude/skills/brandmint
cd ~/.claude/skills/brandmint
uv pip install -e ".[dev]"
bm install skills
```

Verify: `bm install check`

</details>

<details>
<summary><strong>Claude Desktop</strong></summary>

Add to your Claude Desktop MCP config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "brandmint": {
      "command": "bm",
      "args": ["mcp-serve"],
      "env": {
        "FAL_KEY": "your_fal_key_here"
      }
    }
  }
}
```

Requires brandmint installed via Claude Code method first.

</details>

<details>
<summary><strong>GitHub Copilot</strong></summary>

Copilot automatically reads `.github/copilot-instructions.md` when working in this repository. No additional setup needed—just clone the repo and start coding.

```bash
git clone https://github.com/brandmint/brandmint.git
cd brandmint
```

</details>

<details>
<summary><strong>Cursor IDE</strong></summary>

Cursor automatically reads `.cursorrules` when working in this repository. No additional setup needed—just open the project folder.

```bash
git clone https://github.com/brandmint/brandmint.git
cursor brandmint/
```

</details>

## License

MIT
