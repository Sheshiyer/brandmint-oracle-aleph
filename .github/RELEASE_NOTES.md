# Release Notes

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
