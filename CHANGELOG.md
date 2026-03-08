# Changelog

All notable changes to this project will be documented in this file.

## [5.1.0] - 2026-03-07

### Added

#### Full Skill Wiring
- `skills/manifest.yaml`: Restored orchestrator manifest with all 31 text skills across 10 parts, including upstream dependencies, required_keys, and template paths.
- 11 skills newly wired into `WAVE_DEFINITIONS`: brand-name-studio (W1), brand-guidelines (W2), logo-concept-architect (W2), campaign-page-builder (W4), competitive-ads-extractor (W4), packaging-experience-designer (W5), unboxing-journey-guide (W5), affiliate-program-designer (W6), community-manager-brain (W6), update-strategy-sequencer (W6), campaign-orchestrator (W6).
- All 5 named scenarios updated with newly available skills: brand-genesis 8→10, crowdfunding-lean 12→13, crowdfunding-full 20→27, bootstrapped-dtc 9→11, enterprise-gtm 11→14.
- Zero orphaned skills — every scenario skill now has a wave assignment.

#### Tauri v2 Desktop App (Phases 2-6)
- Event streaming system: `EventStore` with 1000-event ring buffer, typed channels (pipeline-log, state-changed, progress, sidecar-status), JSON line parsing from sidecar stdout.
- 28-file component architecture: monolithic 3439-line App.tsx split into 6 Zustand stores, 8 page components, 5 UI components, 3 layout components.
- Native file dialogs via `@tauri-apps/plugin-dialog`, drag-drop enhancement, system notifications with browser fallback.
- macOS menu bar: 5 submenus (File, Pipeline, View, Window, Help) with keyboard shortcuts (⌘O, ⌘R, ⌘1-4).
- Window state persistence: position/size saved on close to `~/Library/Application Support/com.brandmint.desktop/window-state.json`, restored on startup.
- 18 IPC commands (13 original + 2 event + 3 window management).
- 8 Rust unit tests for EventStore (ring buffer, since-filter, channel routing).
- 48 Vitest component/store tests with Tauri API mocks (6 store suites + 4 component suites).
- Vitest + @testing-library/react + jsdom test infrastructure.

### Fixed
- `Header.tsx` and `IntakePage.tsx`: Replaced CommonJS `require()` calls with ESM `import` — fixes blank screen crash on launch.

### Changed
- `WAVE_DEFINITIONS` expanded from 20 to 31 unique text skills across waves 1-6.
- `tauri.conf.json` and `Cargo.toml` bumped to v5.0.0.
- Window title updated to "Brandmint v5.0.0".

## [5.0.0] - 2026-03-07

### Added

#### Asset Fidelity Pipeline (Phase 1)
- `brandmint/core/image_utils.py`: Image I/O, metadata extraction, logo analysis (transparency detection, bounding box, dominant colors).
- `brandmint/core/compositor.py`: PIL compositing engine — LogoCompositor, ProductCompositor, PostGenCompositor, LayerStack with 9-grid positioning, blend modes, and opacity control.
- `brandmint/core/asset_mode.py`: Provider routing with 4 modes (generate, composite, inpaint, hybrid) and per-asset override support.
- `brandmint/core/asset_provenance.py`: Asset provenance tracking (provided/generated/composited) with JSON persistence.
- FAL flux-fill inpainting provider (`fal-ai/flux-pro/v1/fill`) for masked logo region painting.
- FAL flux-canny edge-guided generation provider (`fal-ai/flux-pro/v1/canny`) for structure-preserving generation.
- `--asset-mode` CLI flag on `bm visual generate` and `bm visual execute`.
- `generation.asset_mode` and `generation.composite_config` in brand config schema.
- Composite post-pass wired into `generate_pipeline.py` code generator.

#### NotebookLM Brand Sources (Phase 2)
- `brandmint/publishing/vision_describer.py`: LLM vision integration for image description generation via OpenRouter multimodal API. Supports asset and logo-specific description modes with caching.
- `brandmint/publishing/brand_asset_injector.py`: Extracts palette, typography, logo references, and aesthetic direction from brand config for instruction template injection.
- `BrandStyleGuideBuilder`: Transforms brand config (palette, typography, aesthetic, theme) into narrative style guide source documents.
- Source curator enhancements: `visual-description` source type (content_value 75), brand material scanning, priority scoring (+10 logo, +8 style guide, +5 complementary pairs).
- Enhanced infographic and PDF report instruction templates with brand material references, color palette directives, logo placement, and typography instructions.
- `coverage_report()` method on SourceCurator for dry-run brand material coverage analysis.
- `--include-brand-materials` and `--vision-descriptions` CLI flags on `bm publish notebooklm`.
- `publishing` section in brand config schema: `include_brand_materials`, `vision_descriptions`, `vision_model`, `max_sources`.

#### Documentation
- `docs/asset-fidelity.md`: Complete guide to asset fidelity modes, configuration, and cost impact.
- `docs/notebooklm-brand-sources.md`: Guide to brand-aware NotebookLM source enrichment.

#### Tests
- 305 tests total (was ~20), including:
  - 26 image utility tests, 12 asset provenance tests, 31 compositor tests
  - 27 asset mode routing tests, 29 FAL provider tests, 11 visual regression tests
  - 33 pipeline wiring tests, 12 E2E composite pipeline tests
  - 20 vision describer tests, 59 source curator enhancement tests, 10 coverage report tests

### Changed
- Updated `brandmint/core/providers/base.py` with `supports_inpainting()` and `supports_edge_guided()` methods.
- Updated `brandmint/core/providers/fal_provider.py` with flux-fill and flux-canny branches.
- Updated `brandmint/core/providers/model_mapping.py` with flux-fill/flux-canny model entries.
- Updated `brandmint/publishing/source_curator.py` with visual-description, brand material, and config section scanning.
- Updated `brandmint/publishing/instruction_templates.py` with `inject_brand_context()` and brand embedding directives.
- Updated `brandmint/publishing/notebooklm_publisher.py` to accept brand material and vision description parameters.
- Architecture diagram updated with Asset Fidelity Engine and Brand Sources layers.

### GitHub
- 37 issues created and closed (#71-#107) across 2 milestones.
- Milestone 7: Asset Fidelity Pipeline (20 issues).
- Milestone 8: NotebookLM Brand Sources (17 issues).
- Project #5: Brandmint v5 — Asset Fidelity & Brand Sources.

## [4.3.0] - 2026-02-28

### Added
- Semantic reference matching: 4-gate pipeline (domain filter, subject type, diversity slots, aesthetic tiebreaker) in `scripts/generate_pipeline.py`.
- 5 new semantic metadata fields on all 138 reference catalog entries: `subject_type`, `domain_suitability`, `lighting_register`, `color_temperature`, `composition_format`.
- `brandmint[vision]` optional dependency group: Pillow, colorgram.py, imagehash, numpy, scikit-image, opencv-python-headless, scipy.
- `brandmint[embeddings]` optional dependency group: transformers, torch, sentence-transformers, faiss-cpu.
- `brandmint/vision/` package scaffold for upcoming pixel-level analysis modules.
- 43 GitHub issues (#9-#51) tracking 5-wave vision intelligence upgrade roadmap.

### Changed
- Migrated PIDs 3A, 3B, 4B from Flux 2 Pro to Nano Banana Pro with reference image support.
- Removed hardcoded Noesis/Tryambakam defaults from `build_vars()` in hydrator.
- Updated architecture diagram in README to include semantic reference matching layer.
- Fixed CI/CD health snapshot in README (workflows were present but unreported).

### Removed
- 5D icon generation: deleted `PROMPT_5D_ICONS`, `PROMPT_5D_ICONS_FLUX`, all 4 icon model branches (recraft_vector, recraft_digital, flux, nano_banana), `ref-5D-engine-icons` catalog entry.

## [4.2.1] - 2026-02-28

### Changed
- Refreshed `README.md` with release-aware badges and updated architecture/health sections.
- Corrected skill inventory references to match repository reality (45 skills / 9 categories).
- Added `.readme-gen.json` for persisted README generation preferences.

### Metadata
- Bumped package version in `pyproject.toml` from `4.2.0` to `4.2.1`.

## [4.2.0] - 2026-02-26

### Added
- Remotion video generation pipeline (`Wave 7F`) with three video compositions.
- Full Wave 7 publishing hardening across themes, NotebookLM, decks, reports, diagrams, and videos.
- Optional video dependency group: `brandmint[video]`.

## [4.1.0] - 2026-02-13

### Added
- `bm launch --non-interactive` for agent/CI-safe orchestration.
- Publishing pipeline and visual asset integration workflow enhancements.

### Fixed
- Non-interactive prompt flow regressions and executor stability issues.
- JPEG-as-PNG detection and conversion behavior for Flux responses.

## [4.0.0] - 2026-02-11

### Added
- UX resilience improvements (spinners, status icons, graceful interrupts).
- Performance and observability features (logging flags, reports, caching).
- Budget gates, webhook notifications, and resume support.
