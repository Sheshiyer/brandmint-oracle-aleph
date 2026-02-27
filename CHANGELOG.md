# Changelog

All notable changes to this project will be documented in this file.

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
