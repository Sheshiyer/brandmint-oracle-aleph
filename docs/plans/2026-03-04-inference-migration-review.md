# Inference.sh Integration Review and Migration Plan

Date: 2026-03-04
Scope: Integrate `inference-sh/skills` and move Brandmint toward an Inference-first runtime for image and X automation without breaking existing flows.

## Executive Summary

Brandmint now has the first safety layer for external skill imports (conflict detection, aliasing, normalization, validation). The highest remaining risk is not the registry anymore; it is runtime architecture drift in the visual generation path.

Key point: adding an `inference` adapter in `brandmint/core/providers` is necessary but not sufficient, because `bm launch` currently executes generated scripts that bypass the core provider adapters.

## Source-Backed Inference Platform Facts

- Inference docs expose app execution via run APIs with async lifecycle support.
  - Run apps docs: https://inference.sh/docs/apps/running
  - REST endpoints docs (`run`, `task status`, `task result`): https://inference.sh/docs/api/rest
- Inference docs show API key authentication for API calls.
  - Auth docs: https://inference.sh/docs/quickstart/authentication
- Inference X integration docs specify available X apps and setup requirements.
  - X apps: https://inference.sh/docs/integrations/twitter/apps
  - Required scopes: https://inference.sh/docs/integrations/twitter/required-scopes
  - Callback URL requirement: https://inference.sh/docs/integrations/twitter/callback-url
- `inference-sh/skills` is actively maintained and includes tooling-focused skills such as `agent-tools`, `agent-browser`, `ai-image-generation`, `ai-video-generation`, `llm-models`, `web-search`, and `python-executor`.
  - Repo: https://github.com/inference-sh/skills

## Current Brandmint State (What Is Solid)

- Skill registry safety hardening completed:
  - conflict policy, alias support, recursive discovery, doctor checks.
- External import pipeline in place:
  - pinned vendor snapshot + normalized namespaced IDs + validation script.
- Allowlisted import completed at commit `9a723cdec71c3da5019296ee4ce844a6041c466c` into:
  - `skills/external/inference-sh/upstream/9a723cdec71c/`
  - `skills/external/inference-sh/normalized/`

## Gaps Found (Deep Review)

### Gap A: Non-FAL crash hazards in generated scripts

Generated scripts still contain unguarded `fal_client.upload_file(...)` calls in non-FAL execution paths.

- Evidence: `scripts/generate_pipeline.py` around lines `1656`, `1970`, `2142`, `2275`, `2294`, `2310`.
- Issue: https://github.com/Sheshiyer/brandmint-oracle-aleph/issues/67

### Gap B: Main visual path bypasses core provider adapters

`bm launch` -> `WaveExecutor` -> subprocess `scripts/run_pipeline.py execute` -> generated scripts with embedded provider logic.

- Evidence: `brandmint/pipeline/executor.py:577-585`, `scripts/run_pipeline.py:669-684`, provider logic in `scripts/generate_pipeline.py:985+`.
- Issue: https://github.com/Sheshiyer/brandmint-oracle-aleph/issues/68

### Gap C: Cost reporting is provider-only, not model-aware

Visual costs are calculated from a static provider map and ignore actual model/provider combinations.

- Evidence: `brandmint/pipeline/executor.py:63-69`, `603-607`.
- Issue: https://github.com/Sheshiyer/brandmint-oracle-aleph/issues/69

### Gap D: Docs/runtime fallback mismatch

Provider docs promise automatic fallback chain, but launch runtime does not implement chain retries in the generated-script path.

- Evidence: `docs/providers.md:112-119`, runtime flow above.
- Issue: https://github.com/Sheshiyer/brandmint-oracle-aleph/issues/70

### Existing tracked integration gaps

- Skills registry and ID drift issues: #60, #61, #62
- External pack import pipeline: #63
- Inference provider adapter: #64
- Provider-aware install checks: #65
- Inference X automation path: #66

## Recommended Execution Order (No-Break)

## Phase 1: Runtime Correctness Before New Provider

1. Fix non-FAL upload crashes (#67).
2. Align docs/runtime fallback behavior (#70).
3. Make cost reporting model-aware (#69).

Exit criteria:
- Non-FAL runs complete without `fal_client` errors.
- Fallback semantics are explicit and tested.
- Reports include credible per-asset costs.

## Phase 2: Unify Provider Architecture

1. Route generated visual execution through core provider abstraction (#68).
2. Keep backward-compatibility shim during migration.

Exit criteria:
- One provider execution path for launch runtime.
- No duplicated provider HTTP logic in generated scripts.

## Phase 3: Inference Provider + X Bridge

1. Implement `inference` adapter with async task lifecycle support (#64).
2. Add provider-aware install/check support (#65).
3. ~~Add X integration preflight + dry-run with scope/callback checks (#66).~~ **DONE (2026-03-25)**

Phase 3.3 implementation (#66):
- `brandmint/automation/x_actions.py` — Action executor with dry-run support (6 X actions mapped to inference-sh apps)
- `brandmint/automation/x_preflight.py` — OAuth/scope validation (per-action scope mapping)
- `brandmint/automation/x_audit.py` — Append-only JSONL audit log with query filters
- `brandmint/automation/x_smoke_test.py` — Safe-account smoke test (post → like → cleanup)
- CLI: `bm x {preflight,post,like,retweet,dm,follow,audit,smoke-test}` with `--dry-run` and `--json`
- Tests: `tests/test_x_actions.py`

Exit criteria:
- `generation.provider=inference` works in launch path.
- ~~X automation can be dry-run and audited safely.~~ **MET** — dry-run mode, audit log, scope checks all implemented.

## Phase 4: Controlled Rollout

1. Ring 0 (dev): inference optional, default off.
2. Ring 1 (internal): inference enabled for selected assets/workflows.
3. Ring 2 (scenario-level default-on) after parity reports pass.

Required reports per ring:
- success/failure rate
- latency
- cost deltas
- style-anchor parity notes

## Risk Controls

- Keep `fal` as fallback until parity thresholds are met.
- Maintain import manifests and pinned upstream commits for reproducibility.
- Block rollout if:
  - unresolved duplicate skill IDs
  - provider preflight auth/scope failures
  - regression in baseline scenario outputs.

## Immediate Next Actions

1. Implement #67 and #70 first (fastest path to runtime safety).
2. Start #68 refactor spike with a minimal adapter bridge into generated scripts.
3. In parallel, scaffold #64 using Inference run/task APIs and add tests for async status/result handling.

