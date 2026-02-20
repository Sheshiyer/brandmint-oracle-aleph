# Detailed Product Description

## Overview
Brandmint is an end-to-end brand identity orchestration system that transforms a single YAML configuration file into comprehensive marketing outputs—from strategic text documents and AI-generated visual assets to campaign copy and documentation sites.

## Specifications
- **Skills**: 44 specialized skills across 9 categories
- **Categories**: text-strategy, visual-prompters, campaign-copy, email-sequences, brand-foundation, social-growth, advertising, publishing, visual-pipeline
- **Runtime**: Python 3.10+
- **Package Manager**: uv (recommended), pipx, or pip
- **AI Models**: FAL.AI (Nano Banana Pro, Flux 2 Pro, Recraft V3)
- **Dependencies**: typer, rich, pydantic, pyyaml, python-dotenv, requests, fal-client
- **License**: MIT

## Features & Functions
- **Wave-Based Execution** — Skills execute in dependency-ordered waves (1→6), ensuring upstream outputs feed downstream prompts — eliminates manual orchestration and guarantees consistent data flow
- **Style Anchor Cascade** — The 2A Bento Grid generates first and serves as visual reference for all subsequent Nano Banana Pro calls — maintains visual consistency across 19+ generated assets
- **Hydrator Pattern** — Automatically injects text skill outputs (buyer-persona, voice-and-tone, positioning) back into brand-config.yaml — enables downstream skills to use strategy data without manual copy-paste
- **Scenario System** — Pre-built execution profiles (crowdfunding-lean, enterprise-gtm, bootstrapped-dtc) filter skills and set context — reduces decision fatigue and optimizes for specific launch types
- **Domain-Aware Asset Selection** — Assets auto-filter based on brand.domain_tags (dtc, saas, app, crowdfunding) — generates only relevant assets, saving cost and time
- **Programmatic Video Generation** — Remotion-based video pipeline (Wave 7F) scaffolds a React project per brand, injects data as props, and renders 3 MP4 videos (sizzle reel, product showcase, audio+slides) — professional video deliverables without manual editing
- **Full Publishing Pipeline** — Wave 7 produces 6 deliverable types: brand themes (CSS/Typst/JSON), NotebookLM notebooks, slide decks (Marp), reports (Typst), diagrams (Markmap/Mermaid), and videos (Remotion)

## How To Use
1. **Install**: Run `curl -sSL https://raw.githubusercontent.com/brandmint/brandmint/main/install.sh | bash` or clone and run `uv pip install -e ".[dev]"`
2. **Configure**: Create a `brand-config.yaml` defining your brand's name, palette, typography, products, and domain tags (see `assets/example-tryambakam-noesis.yaml`)
3. **Plan**: Run `bm plan recommend --config brand-config.yaml` to get scenario recommendations, then `bm launch --config brand-config.yaml --scenario crowdfunding-lean`
4. **Generate**: Execute visual pipeline with `bm visual generate` then `bm visual execute --batch anchor` followed by `bm visual execute --batch all`

## Summary
Brandmint eliminates the chaos of brand launches by providing a unified orchestration layer that connects strategic thinking to visual execution. Instead of juggling separate tools for positioning, copywriting, and asset generation, teams define their brand once and let the system cascade that identity across 44 specialized skills and 19+ visual assets. The result: agency-grade brand packages at ~$2-3 per full run, completed in hours instead of weeks, with guaranteed consistency from buyer persona to campaign poster.

```json
{
  "product": {
    "name": "Brandmint",
    "price": "Open Source (MIT) + ~$2-3/brand run for FAL.AI generation"
  },
  "specs": {
    "skills": "44 across 9 categories",
    "runtime": "Python 3.10+",
    "ai_models": "Nano Banana Pro ($0.08), Flux 2 Pro ($0.05), Recraft V3 ($0.04)",
    "visual_assets": "19+ per brand run",
    "video_deliverables": "3 MP4 videos (brand sizzle, product showcase, audio+slides)",
    "publishing_deliverables": "6 types (themes, NotebookLM, decks, reports, diagrams, videos)",
    "scenarios": "6 pre-built (brand-genesis, crowdfunding-lean, crowdfunding-full, bootstrapped-dtc, enterprise-gtm, custom-hybrid)"
  }
}
```
