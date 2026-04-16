# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [4.4.1] - 2026-04-16

### Added
- Signed macOS bootstrap release artifacts for the Tauri desktop app:
  - `Brandmint_4.4.1_macos-aarch64.dmg`
  - `Brandmint_4.4.1_macos-aarch64.app.zip`
  - `Brandmint.app.tar.gz`
  - `Brandmint.app.tar.gz.sig`
  - `latest.json`
- Isolated bootstrap OTA publication path at `https://brandmintupdates.thoughtseed.space/bootstrap/...`
- Focused resilience test coverage:
  - `tests/test_visual_backend_fallback_chain.py`
  - `tests/test_state_validation_integration.py`
- Added `docs/INTEGRATION_EXAMPLES.md` to mirror operator integration guidance under docs.

### Changed
- Visual pipeline scripts backend now retries across providers using configurable `generation.fallback_order`, with fallback attempt summaries surfaced in execution reports.
- Execution + NotebookLM state files now use safe load/save validation via `load_state_safe` / `save_state_safe`.
- Brandmint desktop updater now trusts the new Brandmint-specific signing key and targets the custom Cloudflare updater hostname with R2 fallback support.
- Local Tauri builds now auto-load both `~/.tauri/brandmint.key` and `~/.tauri/brandmint.key.password` for unattended signed desktop builds.
- `README.md` now documents resilience features, desktop bootstrap release behavior, and current updater release channels.
- Release-facing docs now describe the `4.4.1` bootstrap rollout and asset set consistently.

### Release Notes
- `4.4.1` is a bootstrap desktop release because the updater trust root rotated.
- Existing desktop installs must manually reinstall from the DMG or `.app.zip` once before future OTA releases can update on the new signing key.

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
