<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=0,1,12,13&height=200&text=Brandmint&fontSize=52&fontAlignY=35&desc=Unified%20brand%20orchestration%20from%20strategy%20to%20visuals%20to%20publishing&descAlignY=55&fontColor=ffffff" width="100%" />

</div>

<!-- readme-gen:start:badges -->
<p align="center">
  <a href="https://pypi.org/project/brandmint/"><img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white"></a>
  <a href="./pyproject.toml"><img alt="Codebase Version" src="https://img.shields.io/badge/codebase-v5.0.0-1f883d?style=flat-square"></a>
  <a href="https://github.com/Sheshiyer/brandmint-oracle-aleph/releases/latest"><img alt="Latest GitHub Release" src="https://img.shields.io/github/v/release/Sheshiyer/brandmint-oracle-aleph?style=flat-square&logo=github"></a>
  <a href="./.github/RELEASE_NOTES.md"><img alt="Release Notes" src="https://img.shields.io/badge/release_notes-v4.0~v5.0.0-6f42c1?style=flat-square"></a>
  <a href="https://brandmint-openclaw.vercel.app"><img alt="OpenClaw Integration" src="https://img.shields.io/badge/OpenClaw-Integrated-0ea5e9?style=flat-square&logo=github&logoColor=white"></a>
  <a href="https://github.com/Sheshiyer/brandmint-oracle-aleph/pkgs/container/brandmint"><img alt="GHCR Package" src="https://img.shields.io/badge/GHCR-package-blue?style=flat-square&logo=docker&logoColor=white"></a>
  <a href="./ui/"><img alt="Desktop App" src="https://img.shields.io/badge/Desktop-Tauri_v2-FFC131?style=flat-square&logo=tauri&logoColor=white"></a>
</p>
<!-- readme-gen:end:badges -->

<!-- readme-gen:start:tech-stack -->
<p align="center">
  <img src="https://skillicons.dev/icons?i=py,rust,tauri,react,ts,docker&theme=dark" alt="Tech stack" />
</p>
<!-- readme-gen:end:tech-stack -->

> Build complete brand systems from one config file.
> **Brandmint** orchestrates strategy, messaging, visual assets, campaigns, and publishing deliverables through a wave-based pipeline.

<div align="center">
<img src="./docs/assets/showcase/hero-pitch.jpg" alt="Mint Your Brand Identity" width="100%" />
</div>

<img src="https://capsule-render.vercel.app/api?type=rect&color=gradient&customColorList=0,1,12,13&height=2" width="100%" />

## Why Brandmint

- **Pipeline-first execution**: run the full chain with `bm launch` instead of ad-hoc skill runs.
- **45 specialized skills / 9 categories**: from buyer persona and positioning to visual generation and publishing.
- **Asset Fidelity Pipeline** *(v5.0)*: PIL compositing preserves pixel-exact logos and product images — no more AI reinterpretation. Supports generate, composite, inpaint, and hybrid modes.
- **Semantic reference matching**: 4-gate pipeline (domain, subject type, diversity, aesthetic) routes the right reference images to the right assets.
- **Full NotebookLM publishing (Wave 7)**: 23 artifacts across all 9 types — decks, videos, audio, reports, quiz, flashcards, infographics, data tables, and mind maps — with LLM prose synthesis for source documents.
- **Brand-aware NotebookLM sources** *(v5.0)*: LLM vision descriptions, brand style guides, and raw brand materials uploaded as contextualized sources for dramatically better artifact quality.
- **Agent-friendly**: non-interactive mode for CI/desktop/API contexts.
- **OpenClaw integration**: documentation and orchestration flows are aligned for OpenClaw-powered agent setups.

## Quick Start

```bash
# 1) clone
git clone https://github.com/Sheshiyer/brandmint-oracle-aleph.git
cd brandmint-oracle-aleph

# 2) install (editable)
pip install -e .

# 3) initialize config
bm init --output ./my-brand/brand-config.yaml

# 4) run full non-interactive pipeline
bm launch --config ./my-brand/brand-config.yaml \
  --scenario brand-genesis \
  --waves 1-7 \
  --non-interactive
```

## Install via Homebrew

```bash
brew tap Sheshiyer/brandmint
brew install brandmint
bm --help
```

Homebrew packaging docs:
- [docs/homebrew-packaging.md](./docs/homebrew-packaging.md)
- [docs/release-checklist.md](./docs/release-checklist.md)

Troubleshooting:
- If you hit checksum mismatch, refresh tap and reinstall:
  - `brew update && brew untap Sheshiyer/brandmint && brew tap Sheshiyer/brandmint`
- If Python version conflicts appear, ensure `python@3.11` is installed.

## GitHub Package (Container)

Brandmint is now configured to publish a container package to GitHub Container Registry (GHCR).

```bash
docker pull ghcr.io/sheshiyer/brandmint:latest
docker run --rm ghcr.io/sheshiyer/brandmint:latest --help
```

Publishing is automated via GitHub Actions on release publish (`.github/workflows/publish-ghcr.yml`).

## Semantic Reference Matching (v4.3.0)

The visual pipeline now routes reference images to generated assets using a 4-gate semantic filter:

1. **Domain filter** — candidate `domain_suitability` must match brand's `domain_tags`
2. **Subject type filter** — candidate `subject_type` must match the target PID (e.g., `multi-product` for 3A)
3. **Diversity slots** — multi-domain brands get refs spanning different domain tags
4. **Aesthetic tiebreaker** — 5-axis distance scoring within filtered candidates

160 reference images are annotated with 5 semantic fields: `subject_type`, `domain_suitability`, `lighting_register`, `color_temperature`, `composition_format`.

Install vision extras for pixel-level analysis:

```bash
pip install -e '.[vision]'       # Pillow, colorgram, imagehash, scikit-image, OpenCV
pip install -e '.[embeddings]'   # CLIP, FAISS, torch (coming in v4.4)
```

## Asset Fidelity Pipeline (v5.0.0)

The visual pipeline now supports **pixel-exact preservation** of user-provided logos and product images via PIL compositing — instead of feeding them to AI models that reinterpret them.

**The problem:** Nano Banana Pro's `image_urls` parameter is *style conditioning*, not an edit API. Logos get "reinterpreted" — colors shift, shapes morph. For Flux 2 Pro, logos can't even be passed as images.

**The solution:** Four asset modes controlled via config or CLI:

| Mode | How it works | Best for |
|---|---|---|
| `generate` | AI generates everything (default, legacy behavior) | Abstract/artistic assets |
| `composite` | AI generates background, PIL overlays exact logo/product | Logo lockups, product heroes |
| `inpaint` | FAL flux-fill paints around a masked logo region | Seamless integration |
| `hybrid` | Inpaint if provider supports it, else composite fallback | Maximum quality |

```bash
# Use composite mode for pixel-exact logos
bm visual execute --config brand-config.yaml --asset-mode composite

# Or set in brand-config.yaml:
# generation:
#   asset_mode: composite
```

The **style anchor (2A Bento Grid) always generates** regardless of mode — it's the visual reference for all downstream assets.

See [docs/asset-fidelity.md](./docs/asset-fidelity.md) for full configuration guide.

## NotebookLM Brand Sources (v5.0.0)

NotebookLM artifacts (PDFs, infographics, reports) now receive **brand-aware context** through enriched source documents:

- **LLM Vision Descriptions**: Each visual asset gets a companion text description via multimodal LLM analysis (composition, colors, typography, mood)
- **Brand Style Guide Source**: Palette, typography, and aesthetic config transformed into narrative prose
- **Raw Brand Materials**: User-provided logos and product images uploaded with descriptive context
- **Priority Scoring**: Logo descriptions get +10 bonus, style guides +8, complementary image+description pairs +5

```bash
# Include brand materials as NotebookLM sources
bm publish notebooklm --config brand-config.yaml --include-brand-materials

# Also generate vision descriptions for visual assets
bm publish notebooklm --config brand-config.yaml \
  --include-brand-materials --vision-descriptions
```

Result: infographics use actual brand colors, PDFs reference logo placement, slide decks match the visual language.

See [docs/notebooklm-brand-sources.md](./docs/notebooklm-brand-sources.md) for full guide.

## Core CLI Commands

```bash
bm launch     # end-to-end pipeline (waves)
bm plan       # scenario context/recommend/compare
bm visual     # visual generation pipeline
bm publish    # notebooklm (23 artifacts across 9 types)
bm report     # markdown/json/html execution reports
bm cache      # cache stats / clear
```

## Wave Model

| Wave | Focus | Typical Outputs |
|---|---|---|
| 1 | Foundation | persona, competitors, niche inputs |
| 2 | Strategy | positioning, voice, messaging |
| 3 | Visual identity | core visual system + identity assets |
| 4 | Product/campaign | product narratives + campaign copy/assets |
| 5 | Launch assets | email and campaign collateral |
| 6 | Distribution | ads, social, outreach content |
| 7 | Publishing | NotebookLM: 23 artifacts (decks, videos, audio, reports, quiz, flashcards, infographics, data tables, mind maps) |

## Publishing Deliverables (`bm publish`)

Wave 7 publishes brand intelligence to Google NotebookLM, generating **23 artifacts** across all 9 supported types:

| Type | Variations | Customization |
|---|---:|---|
| Slide Deck | 4 | format (detailed/presenter) x length (full/short) |
| Video | 2 | explainer + brief, brand-matched visual style |
| Audio | 3 | deep-dive, brief, debate |
| Report | 3 | briefing, blog post, study guide |
| Quiz | 2 | medium + hard difficulty |
| Flashcards | 2 | standard + detailed |
| Infographic | 3 | landscape, portrait, square |
| Data Table | 3 | competitive, product, persona matrices |
| Mind Map | 1 | auto-generated |

```bash
# Full publish (all 23 artifacts)
bm publish notebooklm --config <brand-config.yaml>

# Filter by type or ID
bm publish notebooklm --config <brand-config.yaml> --artifacts slide-deck
bm publish notebooklm --config <brand-config.yaml> --artifacts video,audio

# Control parallelism
bm publish notebooklm --config <brand-config.yaml> --max-parallel 5

# Dry run
bm publish notebooklm --config <brand-config.yaml> --dry-run
```

Source documents are built using **LLM prose synthesis** — skill outputs are transformed into narrative-form text optimized for NotebookLM ingestion. Video visual styles are auto-resolved from brand archetype (e.g., "outlaw" maps to retro-print, "sage" maps to classic).

<!-- readme-gen:start:architecture -->
## Architecture (high level)

```mermaid
graph TD
    A[🧾 brand-config.yaml] --> B[🧠 Scenario Planner]
    B --> C[🌊 Wave Executor]
    C --> D[📝 Text Skills]
    C --> E[🎨 Visual Pipeline]
    E --> K[🔍 Semantic Reference Matcher]
    K --> L[📸 Nano Banana / Flux / Recraft]
    L --> M[🎯 Asset Fidelity Engine]
    M -->|composite| N[🖼️ PIL Compositor]
    M -->|inpaint| O[✂️ FAL Flux-Fill]
    M -->|generate| P[✅ Direct Output]
    D --> F[💧 Hydrator]
    F --> A
    C --> G[📦 Publishing Pipeline]
    G --> H[✨ Prose Synthesizer]
    G --> Q[👁️ Vision Describer]
    G --> R[🎨 Brand Asset Injector]
    H --> I[📚 NotebookLM]
    Q --> I
    R --> I
    I --> J[📊 23 Artifacts]
```
<!-- readme-gen:end:architecture -->

## Sample Output

Every pipeline run generates a complete brand asset suite. Here's what a single `bm launch --waves 1-7` produces:

<!-- readme-gen:start:showcase -->
<div align="center">

<table>
<tr>
<td align="center" width="60%">
<img src="./docs/assets/showcase/brand-kit-bento.jpg" alt="Brand Kit Bento — visual identity system" width="100%" />
<br /><sub><b>Brand Kit Bento</b> — Visual identity system (Nano Banana Pro)</sub>
</td>
<td align="center" width="40%">
<img src="./docs/assets/showcase/brand-seal.jpg" alt="Brand Seal" width="100%" />
<br /><sub><b>Brand Seal</b> — Identity mark (Flux 2 Pro)</sub>
<br /><br />
<img src="./docs/assets/showcase/heritage-engraving.jpg" alt="Heritage Engraving" width="100%" />
<br /><sub><b>Heritage Engraving</b> — Print asset (Recraft)</sub>
</td>
</tr>
<tr>
<td align="center" colspan="2">
<img src="./docs/assets/showcase/campaign-grid.jpg" alt="Campaign Grid — multi-format campaign assets" width="100%" />
<br /><sub><b>Campaign Grid</b> — Multi-format campaign assets (Nano Banana Pro)</sub>
</td>
</tr>
<tr>
<td align="center">
<img src="./docs/assets/showcase/seeker-poster.jpg" alt="Archetype Poster — The Seeker" width="100%" />
<br /><sub><b>Archetype Poster</b> — Brand persona visualization (Nano Banana Pro)</sub>
</td>
<td align="center">
<img src="./docs/assets/showcase/art-panel.jpg" alt="Art Panel — editorial illustration" width="100%" />
<br /><sub><b>Art Panel</b> — Editorial illustration (Recraft)</sub>
</td>
</tr>
</table>

<sub>All assets generated from a single <code>brand-config.yaml</code> — no manual design work required.</sub>

</div>
<!-- readme-gen:end:showcase -->

## Skills Inventory (repo reality)

| Category | Skills |
|---|---:|
| text-strategy | 7 |
| visual-prompters | 9 |
| campaign-copy | 6 |
| email-sequences | 3 |
| brand-foundation | 3 |
| social-growth | 5 |
| advertising | 5 |
| visual-pipeline | 4 |
| publishing | 3 |
| **Total** | **45** |

## Release Highlights (from all repo releases)

- **v4.0.0** — UX, resilience, logging/caching/reporting foundations, budget gates, resume support.
- **v4.1.0** — robust `--non-interactive` pipeline behavior, publishing + wiki pipeline, visual asset integration fixes.
- **v4.2.0** — Remotion video generation (Wave 7F), full Wave 7 publishing flow hardening, optional `brandmint[video]` extras.
- **v4.2.1** — README/metadata alignment: release-aware badges, corrected inventory counts, and changelog initialization.
- **v4.3.0** — Semantic reference matching: 4-gate pipeline, 5 new semantic metadata fields on 138 catalog entries, 5D icon removal, 3A/3B/4B migrated to Nano Banana Pro, `brandmint[vision]` + `brandmint[embeddings]` optional dependency groups, 43-task vision upgrade roadmap (issues #9-#51).
- **v4.3.1** — Twitter sync pipeline: automated community prompt discovery via bird CLI, AmirMushich tracking with per-account overrides, unified `twitter_sync_all.sh` runner, launchd weekly automation, 73 curated references from 41 contributors, rebuilt reference catalog (160 entries).
- **v4.4.0** — Full NotebookLM artifact matrix: 23 artifacts across all 9 types (was 5), LLM prose synthesis for source documents, 5-phase parallel execution engine (~35 min wall clock), brand archetype-matched video styles, configurable artifact filtering and parallelism, Tauri v2 Phase 1 shell prototype, removed local generators (Remotion/Marp/report/diagram).
- **v5.0.0** *(current)* — Asset Fidelity Pipeline: PIL compositing for pixel-exact logo/product preservation (4 modes: generate, composite, inpaint, hybrid), FAL flux-fill + flux-canny providers. NotebookLM Brand Sources: LLM vision descriptions for visual assets, brand style guide synthesis, raw brand material scanning, priority scoring with logo/style guide bonuses, enriched infographic/PDF templates with brand embedding. 305 tests, 37 issues closed.

See: [GitHub Releases](https://github.com/Sheshiyer/brandmint-oracle-aleph/releases) and [repo release notes](./.github/RELEASE_NOTES.md).

<!-- readme-gen:start:health -->
## Project Health Snapshot

| Category | Signal |
|---|---|
| Tests | 305 passing across 15 test files |
| CI/CD | `publish-ghcr.yml` (container), `update-homebrew-tap.yml` (formula) |
| Packaging | `pyproject.toml` + console scripts (`brandmint`, `bm`) + Homebrew tap + GHCR container |
| Extras | `brandmint[vision]` (Pillow, colorgram, imagehash, scikit-image, OpenCV) / `brandmint[embeddings]` (CLIP, FAISS, torch) |
| Docs | `README.md`, `CLAUDE.md`, `.github/RELEASE_NOTES.md`, `docs/` |
| State/Reports | execution state + report pipeline implemented |
<!-- readme-gen:end:health -->

## Desktop App (Tauri v2)

Brandmint includes a native desktop app built with **Tauri v2** (Rust backend + React/TypeScript frontend). The app provides a local GUI for pipeline orchestration, replacing the need for terminal-only workflows.

**Phase 1 (current):** Shell and sidecar prototype — Tauri window embeds the `bm` CLI as a sidecar process, with a React UI for config loading, wave selection, and live pipeline output streaming.

```bash
# Development
cd ui && npm run tauri dev

# Build (macOS universal)
cd ui && npm run tauri build
```

**Requires:** Rust toolchain (`rustup`), Node.js 18+, and Xcode Command Line Tools (macOS).

> Phase 2 will add real-time artifact previews, drag-and-drop config editing, and NotebookLM artifact gallery.

## OpenClaw Integration

Brandmint supports OpenClaw-oriented workflows and docs publication paths.

- OpenClaw docs/site touchpoint: [brandmint-openclaw.vercel.app](https://brandmint-openclaw.vercel.app)
- Use the same pipeline-first contract (`bm launch --non-interactive`) for reliable agent orchestration.

## Twitter Sync Pipeline

Brandmint includes an automated Twitter/X sync pipeline that discovers prompt engineering techniques, typography workflows, and visual design references from the community.

```bash
# Full sync (discover + curate + download assets)
./scripts/twitter_sync_all.sh

# Preview only
./scripts/twitter_sync_all.sh --dry-run

# Sync without downloading images
./scripts/twitter_sync_all.sh --skip-download

# Override minimum likes threshold
./scripts/twitter_sync_all.sh --min-likes=5
```

**Requires:** [bird CLI](https://github.com/dawsbot/bird) (`brew install bird`) authenticated via `bird auth`.

Weekly automation is available via the included launchd plist (`scripts/com.brandmint.twitter-sync.plist`).

### Community Credits

Brandmint's reference library includes **73 curated references** from **41 contributors** on X/Twitter. Special thanks to:

| Contributor | References | Focus |
|---|---:|---|
| [@AmirMushich](https://x.com/AmirMushich) | 18 | Nano Banana Pro prompts, typography design, text masking workflows |
| [@azed_ai](https://x.com/azed_ai) | 4 | Prompt sharing, Nano Banana Pro techniques |
| [@Kashberg_0](https://x.com/Kashberg_0) | 3 | Gemini + Nano Banana Pro workflows |
| [@john_my07](https://x.com/john_my07) | 3 | Brand design references |
| [@alex_prompter](https://x.com/alex_prompter) | 1 | Prompt engineering research |
| [@godofprompt](https://x.com/godofprompt) | 1 | Creative prompting techniques |

And 35 other community members whose shared work enriches the reference catalog. All references are attributed with original tweet links and author handles in the prompt files.

## Notes for Agent/CI execution

If you're using an agent environment, follow the pipeline contract in [CLAUDE.md](./CLAUDE.md):

- Prefer `bm launch --non-interactive`
- Avoid running individual skills out of orchestration order
- Use `.brandmint/prompts/` + `.brandmint/outputs/` handoff model for text skills

## License

No `LICENSE` file is currently present in the repository root. Add one before public distribution.

<!-- readme-gen:start:footer -->
<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=0,1,12,13&height=110&section=footer" width="100%" />

Built with Craft Agent support · powered by wave orchestration

</div>
<!-- readme-gen:end:footer -->
