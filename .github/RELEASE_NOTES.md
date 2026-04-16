# Release Notes

## What's New in v4.4.1

### Bootstrap Desktop Release
- **One-time manual reinstall release** — `v4.4.1` rotates the Brandmint desktop updater trust root, so existing installs need one manual reinstall before future OTA updates can continue normally.
- **Prepared macOS release assets** — GitHub release payload should include:
  - `Brandmint_4.4.1_macos-aarch64.dmg`
  - `Brandmint_4.4.1_macos-aarch64.app.zip`
  - `Brandmint.app.tar.gz`
  - `Brandmint.app.tar.gz.sig`
  - `latest.json`
- **Bootstrap OTA channel** — Signed updater payload is staged at `https://brandmintupdates.thoughtseed.space/bootstrap/latest.json` so `stable` can remain untouched until the post-bootstrap OTA cut.

### Desktop Distribution Hardening
- **Brandmint-specific updater key** — Tauri updater config now embeds the final Brandmint public key instead of the superseded trust root.
- **Custom updater host** — Desktop updater prefers `brandmintupdates.thoughtseed.space` and keeps the public R2 host as fallback.
- **Noninteractive local signing** — Local Tauri release builds now auto-load both `~/.tauri/brandmint.key` and `~/.tauri/brandmint.key.password`, removing the prior failure mode around unattended signing.

### Resilience Features Landed in the Release Line
- **Provider fallback chain** — Script-backed visual execution retries across `generation.fallback_order` providers and records fallback attempt summaries in reports.
- **Safe state validation** — Execution and NotebookLM state files now load/save through repair-aware validation with backup snapshots for corrupted state.

## What's New in v4.4.0

### Full NotebookLM Artifact Matrix (23 artifacts)
- **All 9 artifact types** — Expanded from 5 artifacts to 23 across every NotebookLM type: slide decks, videos, audio, reports, quiz, flashcards, infographics, data tables, and mind maps
- **Slide Decks (4)** — Format (detailed/presenter) x length (full/short) = 4 variations with brand-informed instructions
- **Video (2)** — Explainer + brief with brand archetype-matched visual style (12 archetypes mapped: e.g., "outlaw" to retro-print, "sage" to classic)
- **Audio (3)** — Deep-dive (long), brief (short), and debate formats
- **Reports (3)** — Briefing doc, blog post, and study guide
- **Quiz (2)** — Medium and hard difficulty
- **Flashcards (2)** — Standard and detailed
- **Infographic (3)** — Landscape, portrait, and square orientations
- **Data Tables (3)** — Competitive analysis, product features, persona matrices
- **Mind Map (1)** — Auto-generated from all sources

### LLM Prose Synthesis
- **Narrative source documents** — Skill outputs are transformed from raw JSON into rich prose optimized for NotebookLM ingestion
- **OpenRouter integration** — Uses Claude 3.5 Haiku by default, configurable via `--synthesis-model`
- **Per-document caching** — Synthesized prose is cached; clear with `--clear-prose-cache`
- **Graceful fallback** — Falls back to mechanical rendering if synthesis fails or is disabled (`--no-synthesize`)

### 5-Phase Parallel Execution Engine
- **Phase 1 (instant)** — Mind map generated synchronously (~1 min)
- **Phase 2 (slow-start)** — Video + audio kicked off early with staggered delays
- **Phase 3 (parallel-1)** — Decks + reports generated in parallel (configurable workers)
- **Phase 4 (parallel-2)** — Quiz + flashcards + infographic + data tables in parallel
- **Phase 5 (slow-poll)** — Wait for video/audio completion
- **~35 min wall clock** vs ~4 hours sequential execution
- **`--max-parallel`** — Control worker count (default: 3)

### Publishing Streamlining
- **Removed local generators** — Marp decks, Typst reports, Markmap diagrams, and Remotion videos removed in favor of NotebookLM-native artifact generation
- **Wave 7 simplified** — Single `bm publish notebooklm` command replaces 5 separate publish subcommands
- **Enhanced filtering** — `--artifacts` supports type-level (`slide-deck`), group-level, and individual ID matching
- **Legacy compatibility** — Old artifact IDs (`brand-overview-deck`, `audio-overview`, etc.) mapped to new IDs via alias system

### brand-config.yaml Overrides
```yaml
notebooklm:
  artifacts:
    disabled: [quiz-hard, flashcards-detailed]
    video_style: heritage
  max_parallel_workers: 2
  inter_artifact_delay: 5
```

### Other Changes
- **Tauri v2 Phase 1** — Shell and sidecar prototype for desktop app
- **Pipeline fix** — Single braces in generated pipeline scripts (was double-brace causing Python format errors)
- **Timeout bump** — Artifact generation timeout increased to 30 min (was 20) for long video renders

---

## What's New in v4.3.0

### Semantic Reference Matching
- **4-gate matching pipeline** — Domain filter, subject type filter, diversity slot allocation, and aesthetic tiebreaker replace the old aesthetic-only distance scoring
- **5 new semantic fields** — Every reference image (138 entries) annotated with `subject_type`, `domain_suitability`, `lighting_register`, `color_temperature`, `composition_format`
- **Domain-aware routing** — Leather bags no longer match SaaS brands; calligraphic logos no longer match food brands
- **Diversity slots** — Multi-domain brands (3+ tags) get references spanning different domain categories

### 5D Icon Removal
- **Deleted entirely** — `PROMPT_5D_ICONS`, `PROMPT_5D_ICONS_FLUX`, all 4 model branches (recraft_vector, recraft_digital, flux, nano_banana), and `ref-5D-engine-icons` catalog entry
- **Rationale** — Reference images with icon templates provide better style consistency than generated icons

### Nano Banana Migration
- **3A, 3B, 4B migrated** from Flux 2 Pro to Nano Banana Pro with full reference image assembly (style anchor + composition ref + supplementary refs)
- **2B, 2C stay on Flux** — Identity geometry assets (Brand Seal, Logo Emboss) need Flux's text precision

### Vision Intelligence Foundation
- **`brandmint[vision]`** — Optional dependency group: Pillow, colorgram.py, imagehash, numpy, scikit-image, opencv-python-headless, scipy
- **`brandmint[embeddings]`** — Optional dependency group: transformers, torch, sentence-transformers, faiss-cpu
- **`brandmint/vision/` package** — Scaffold for 5-wave upgrade (pixel features, CLIP embeddings, Gemini Vision, feedback loop)
- **43 GitHub issues** (#9-#51) tracking the full vision upgrade roadmap across 5 waves

### Pipeline Fixes
- Removed hardcoded Noesis/Tryambakam defaults from `build_vars()` — brand-config values now always win
- Fixed `_PID_CONTEXT` missing entries for 3A, 3B, 3C, 4B
- Fixed `_DEFAULT_REF_IMAGES["3C"]` wrong filename

---

## What's New in v4.2.1

### Documentation & Packaging Alignment
- **README refresh** — Updated positioning copy, release-aware badge strategy, architecture/health sections, and corrected skills inventory to match repository reality (45 skills across 9 categories)
- **Release timeline alignment** — README now distinguishes published GitHub releases from repo-documented milestones
- **Version metadata** — Bumped package version to `4.2.1` in `pyproject.toml` for a clean patch release
- **Generator config** — Added `.readme-gen.json` to persist README generation style (`modern`) and badge style (`flat-square`)
- **Changelog bootstrap** — Introduced `CHANGELOG.md` with consolidated entries for v4.0.0 through v4.2.1

---

## What's New in v4.2.0

### Programmatic Video Generation (Wave 7F)
- **Remotion Video Generator** — Scaffolds a temporary Remotion (React) project per brand, injects brand data as React props via Jinja2 templates, and renders 3 video compositions to MP4
- **Brand Sizzle Reel** (60-90s) — 6-scene video: hook, problem, solution, proof, offer, CTA — sourced from positioning, persona, identity, and voice outputs
- **Product Showcase** (30-60s) — 4-scene video: hero, features, differentiation, CTA — sourced from product description and competitive analysis
- **Audio + Slides** (dynamic duration) — Auto-paced slides synced to NotebookLM MP3 audio with brand visual assets as slide backgrounds
- **Standalone CLI** — `bm publish video --config <path>` with `--videos` filter and `--force` regeneration

### Full Wave 7 Publishing Pipeline
- **7A: Brand Theme Export** — CSS, Typst, JSON, and Remotion constants generated from brand-config.yaml palette/typography
- **7B: NotebookLM Publishing** — Notebook creation with source documents and artifact generation
- **7C: Slide Decks** — PDF slide decks via Marp CLI
- **7D: Reports** — PDF reports via Typst
- **7E: Mind Maps & Diagrams** — Markmap and Mermaid CLI output
- **7F: Video Overviews** — Remotion-rendered MP4 videos (new in v4.2.0)

### Infrastructure
- **`pip install 'brandmint[video]'`** — New optional dependency group for Jinja2 templates
- **State persistence** — `videos-state.json` for idempotent video generation (skip already-rendered unless `--force`)
- **Graceful degradation** — Node.js check with helpful install instructions; audio-slides skipped if no NotebookLM MP3 exists
- **npm caching** — `node_modules` cached between runs in `.remotion-workspace/`

### Documentation
- **README** — Updated architecture diagram, Wave 7 table, publishing pipeline section, CLI reference
- **CLAUDE.md** — Wave 7 publishing commands and deliverable paths
- **SKILL.md** — Updated skill categories, wave table, publishing pipeline section

---

## What's New in v4.1.0

### Non-Interactive Pipeline Execution
- **`--non-interactive` flag** — Skip all TTY prompts for agent/CI environments
- **Auto-detection** — Pipeline detects non-interactive environments via `sys.stdin.isatty()` and adapts automatically
- **No more skipped skills** — Fixed `Confirm.ask()` blocking that caused skills to be silently skipped in Desktop/API contexts
- **Auto scenario selection** — Non-interactive mode selects the best scenario automatically when none is specified
- **Extended polling** — Non-interactive timeout increased to 600s with 30-second progress indicators

### Agent Execution Guide (CLAUDE.md)
- **CLAUDE.md at repo root** — Automatically read by Claude Code agents, prevents ad-hoc skill execution
- **Pipeline-first enforcement** — Guides agents to use `bm launch --non-interactive` instead of running skills individually
- **Key paths documented** — Brand config, prompts, outputs, visual assets, pipeline state

### Publishing Pipeline
- **Wiki Documentation Generator** — Transforms pipeline JSON outputs into structured, interconnected wiki markdown using 4-6 parallel agents
- **Astro Wiki Site Builder** — Converts wiki markdown into iOS26 glassmorphism-styled Astro sites with dark/light mode
- **Visual Asset Integration** — `map-assets-to-wiki.py` bridges 26 asset categories to wiki pages with hero/inline/gallery roles
- **`process-markdown.sh --images`** — Copies generated visual assets to Astro `public/images/` alongside markdown
- **`inventory-sources.py` visual scanning** — Inventories both text documents and visual assets from `generated/` directory
- **Asset gallery page** — `brand/visual-assets.md` catalogs all generated assets organized by category

### Visual Pipeline Fixes
- **JPEG-as-PNG detection** — Flux 2 Pro API returns JPEG data but pipeline names files `.png`; now auto-detects via magic bytes and converts
- **Executor bug fixes** — Fixed `scenario_id` AttributeError and `all_success` UnboundLocalError in executor.py

### Documentation
- **README overhaul** — Added publishing pipeline section, non-interactive mode docs, CLI flags table, agent execution section, visual asset integration architecture
- **Version badge** — Added version badge linking to GitHub release
- **Expanded visual assets table** — Now includes Icons (5D series), Social assets (Email Hero, IG Story, OG Image, Twitter Header)
- **Execution context headers** — Publishing skills now document their position in the pipeline lifecycle

---

## What's New in v4.0.0

### Wave 1: UX Polish & Resilience
- **Progress Spinners** - Visual feedback during API calls
- **Status Icons** - Standardized circle/half/filled/cross/empty system
- **ASCII Logo** - Branded version command
- **Graceful Interrupts** - Ctrl+C saves state for resume
- **Config Validation** - Required fields checked on load
- **Retry Logic** - Exponential backoff for API calls
- **Desktop Notifications** - macOS/Linux alerts on completion

### Wave 2: Performance & Observability
- **Structured Logging** - `--verbose/-v`, `--debug`, `--quiet` flags
- **Execution Reports** - `bm report --format markdown|json|html`
- **Prompt Caching** - Skip regeneration if unchanged
- **Parallel Batches** - ThreadPoolExecutor for visual assets
- **Cost Tracking** - Estimated vs actual with variance display

### Wave 3: Documentation & Advanced Features
- **Cache CLI** - `bm cache stats`, `bm cache clear`
- **Force Regeneration** - `bm visual execute --force`
- **Webhook Notifications** - Slack/Discord on completion
- **Budget Gates** - `--max-cost 5.00` aborts if exceeded
- **Resume Support** - `--resume-from 3` continues from wave

### Documentation
- Website: https://brandmint-openclaw.vercel.app
- 44 skills across 9 categories
- FAL.AI/Nano Banana visual pipeline
