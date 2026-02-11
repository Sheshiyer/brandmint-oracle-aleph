# Brandmint

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-Install-blueviolet?logo=anthropic)](#claude-code)
[![Claude Desktop](https://img.shields.io/badge/Claude_Desktop-MCP-purple?logo=anthropic)](#claude-desktop)
[![GitHub Copilot](https://img.shields.io/badge/Copilot-Compatible-black?logo=github)](#github-copilot)
[![Cursor IDE](https://img.shields.io/badge/Cursor-Compatible-00D084)](#cursor-ide)

> End-to-end brand identity orchestration — from strategy to visual assets to campaign copy.

Brandmint transforms a single `brand-config.yaml` into comprehensive marketing outputs using **44 specialized skills across 9 categories**. The system chains text strategy (buyer personas, positioning, voice) through AI-generated visual assets (via FAL.AI) to campaign copy and publishing pipelines.

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

## Image Providers

Brandmint supports multiple image generation providers:

| Provider | Style Anchor Support | Cost | Best For |
|----------|---------------------|------|----------|
| **FAL.AI** (default) | ✅ Full | $0.04-0.08/img | Maximum consistency |
| **OpenRouter** | ❌ Text-only | $0.03-0.05/img | Single API key |
| **OpenAI** | ⚠️ Limited | $0.04-0.08/img | Creative variations |
| **Replicate** | ⚠️ Limited | $0.03-0.05/img | Budget batches |

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
| **Campaign** | Contact Sheets (7A), Seeker Poster (8A), Sequences (10A-C) | Nano Banana Pro |

**Cost:** ~$2-3 per full visual run (19 assets × 2 seeds)

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

## CLI Reference

```bash
bm launch     # Full pipeline wizard (text + visuals)
bm plan       # Scenario planning (context, recommend, compare)
bm visual     # Visual pipeline (generate, execute, verify, status)
bm registry   # Skill management (list, info, sync)
bm install    # Setup (skills, check)
```

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
