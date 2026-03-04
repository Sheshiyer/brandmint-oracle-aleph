# Inference Skills Integration Plan (No-Break Rollout)

Date: 2026-03-04
Target: integrate selected skills from `https://github.com/inference-sh/skills` into Brandmint without overriding existing behavior.

## Success Criteria
- No regressions in current `bm launch` scenario execution.
- No silent overrides of existing Brandmint skills.
- Imported skills are namespaced, validated, and auditable.
- Safe rollback available in one command/revert.

## Constraints
- Keep existing `skills/` tree and wave orchestration unchanged by default.
- Do not activate imported skills in scenarios until explicitly allowlisted.
- Treat `inference-sh/skills` as upstream content source, not runtime authority.
- Treat `inference.sh` runtime as a candidate primary execution plane for image + X automation, but keep a reversible dual-provider path until parity is proven.

## Plan
- [x] Perform deep compatibility review of current Brandmint skill system.
- [x] Perform deep compatibility review of `inference-sh/skills` structure and quality.
- [x] Check in with stakeholder before implementation begins (approve this plan and scope).
- [x] Add currently observed integration blockers to GitHub issues before proceeding to rollout work.

### Phase 1: Safety Rails First
- [x] Add source-aware conflict detection in `brandmint/core/skills_registry.py` (fail or warn on ID collisions instead of silent overwrite).
- [x] Add recursive external skill discovery support for vendor tree.
- [x] Unify discovery file checks between CLI and core (`SKILL.md`, `skill.md`, `instructions.md`) to avoid visibility drift.
- [x] Add `bm registry doctor` command for schema/path/conflict checks.

### Phase 2: Vendor + Normalize (No Runtime Activation)
- [x] Create vendor layout:
  - `skills/external/inference-sh/upstream/<commit>/`
  - `skills/external/inference-sh/normalized/`
- [x] Build importer script `scripts/import_inference_skills.py`:
  - clone/fetch pinned commit
  - copy upstream snapshot
  - generate normalized namespaced skills: `infsh-<slug>`
  - write import manifest (`source`, `commit`, `imported_at`, `mapping`)
- [x] Auto-fix known upstream metadata issues during normalization:
  - invalid frontmatter for `agent-ui`, `chat-ui`, `tools-ui`, `widgets-ui`
  - broken skill aliases/references (`@inference-sh`, `@markdown-ui`, `@seo`)
  - browser invocation style drift

### Phase 3: Validation Gates
- [x] Add validator `scripts/validate_skill_pack.py` with checks:
  - YAML/frontmatter parse validity
  - required fields (`name`, `description`, `allowed-tools`)
  - cross-skill reference resolution
  - duplicate ID detection across all sources
- [x] Add tests:
  - `tests/test_skills_registry.py` (conflicts, alias resolution, recursive discovery, instructions.md guard)
- [ ] Add CI job for external-pack validation (non-blocking initially, then blocking).

### Phase 4: Controlled Adoption
- [x] Create allowlist file for initial adoption (suggested first batch):
  - `agent-tools`
  - `agent-browser`
  - `ai-image-generation`
  - `ai-video-generation`
  - `llm-models`
  - `web-search`
  - `python-executor`
- [x] Map allowlisted imports to Brandmint use-cases without changing existing wave IDs.
- [x] Add feature flag/config to enable imported skills per scenario.
- [ ] Run A/B dry-runs on representative configs (`baseline` vs `import-enabled`) and diff outputs.

### Phase 5: Rollout + Rollback
- [ ] Ship in 3 rings:
  - Ring 0: local/dev only
  - Ring 1: internal default-off
  - Ring 2: selected scenarios default-on
- [ ] Define rollback procedure:
  - disable feature flag
  - revert import manifest commit
  - rerun registry doctor + smoke tests
- [ ] Publish operator docs (`docs/inference-skills-integration.md`) with upgrade cadence.

### Phase 6: Inference.sh-First Provider Track (Fal.ai Alternative)
- [ ] Check in with stakeholder: approve migration goal `Fal-primary -> Inference-primary`.
- [ ] Add provider adapter `brandmint/core/providers/inference_provider.py` using Inference API app execution.
- [ ] Extend provider registry and mapping:
  - register `inference` in provider factory and capabilities map
  - map logical models to Inference app/function identifiers
  - add env configuration (`INFERENCE_API_KEY`, optional `INFERENCE_BASE_URL`)
- [ ] Keep style-anchor safety:
  - detect assets requiring reference image parity
  - fallback to Fal/OpenAI path if Inference app lacks image-reference capability
  - mark parity gap per asset in execution report
- [ ] Add X automation integration track (optional but first-class):
  - support `x/post-tweet`, `x/post-create`, `x/post-like`, `x/post-retweet`, `x/dm-send`, `x/user-follow`
  - add connection checks for X integration and OAuth scopes
  - add dry-run mode for social posting
- [ ] Add flow orchestration hooks:
  - support Inference flow run trigger from Brandmint CLI
  - map campaign milestones to flow entry points
  - persist flow run IDs in `.brandmint-state.json`
- [ ] Add provider policy controls in config:
  - `generation.provider: inference|fal|...`
  - `generation.fallback_chain: [inference, fal, openrouter, ...]`
  - per-asset provider override for high-risk deliverables
- [ ] Add migration test suite:
  - golden-set render diff on representative assets
  - latency/cost comparison report
  - failure-mode tests (expired token, missing integration, rate-limit)

### Phase 6A: Runtime Safety Corrections (Pre-Adapter)
- [x] Fix non-FAL crash risk from unguarded `fal_client.upload_file` in generated scripts (#67).
- [x] Align provider fallback documentation with actual launch runtime behavior (#70).
- [x] Unify launch runtime provider execution path to core adapters (#68).
- [x] (Deferred) Make model-aware visual cost accounting and reporting updates (#69) -- parked by scope decision.

### Phase 6B: Pipeline Separation + Inference Capability Scaffolding (Current Priority)
- [x] Refactor visual execution into pluggable backends (`scripts` default, `inference` scaffold backend).
- [x] Introduce inference media-agent scaffold generator (per-asset prompt scaffolds + runbook).
- [x] Map asset batches to imported normalized inference skills (`infsh-*`) for execution guidance.
- [x] Wire backend selection via config (default no behavior change).
- [x] Add verification tests for backend factory and scaffold output contract.

## Verification Plan (Must Pass Before Completion)
- [ ] `pytest -q`
- [x] `bm registry list` (no missing/duplicate surprises)
- [ ] `bm launch --scenario crowdfunding-lean --waves 1-3 --non-interactive` (baseline parity)
- [ ] `bm launch` with import flag enabled on test config (no crash + expected skill resolution)
- [ ] Diff report: `baseline vs import-enabled` on prompts and outputs
- [ ] `bm launch` with `generation.provider=inference` on visual batches (compare success rate vs fal baseline)
- [ ] X automation dry-run and scoped live test with safe account (single post + cleanup)
- [ ] Documented rollback drill executed successfully (`inference -> fal`)

## Review (Deep Findings Summary)
- Current Brandmint risk: registry uses last-source-wins override behavior; collisions can silently replace skills.
- Current Brandmint risk: local naming drift already exists (`buyer-persona` vs `buyer-persona-generator`) and can trigger stub fallback.
- Current Brandmint risk: CLI and core discovery rules differ; visibility can mismatch.
- Upstream risk (`inference-sh/skills`): 4 skills have invalid frontmatter/missing keys; not fully discoverable without normalization.
- Upstream risk (`inference-sh/skills`): some aliases/references point to non-existent skill IDs.
- Decision: integrate via pinned vendor + normalization + allowlist, not direct install.
- Substantiated platform fit (`inference.sh` official docs):
  - API supports running apps via `POST /api/v1/apps/run` and async polling (`/status`, `/result`).
  - Multi-function app execution is supported via `function` parameter.
  - Tool orchestration is built-in with automatic tool calling and logging.
  - Integrations include managed OAuth connections and BYOK options.
  - X integration docs define required OAuth scopes and callback handling.
  - Image generation app exists, but image-reference parity with Brandmint style-anchor flow must be validated before full Fal replacement.
- Implementation progress (this session):
  - Hardened `SkillsRegistry` with conflict policy (`warn_skip|warn_overwrite|error`), alias resolution, recursive discovery, and exportable conflicts/aliases.
  - Added `bm registry doctor` and upgraded `bm registry sync` to output JSON snapshot.
  - Added `scripts/import_inference_skills.py` and `scripts/validate_skill_pack.py`.
  - Imported allowlisted normalized pack from `inference-sh/skills` @ `9a723cdec71c` into `skills/external/inference-sh/normalized/`.
  - Added registry regression tests in `tests/test_skills_registry.py` (5 passing tests).
- Current verification note:
  - Full `pytest -q` still has 2 pre-existing failures in `tests/test_hydrator.py` unrelated to this change-set.
- Runtime safety verification (Phase 6A):
  - `python3 -m py_compile scripts/generate_pipeline.py` passed.
  - `pytest -q tests/test_generate_pipeline_template.py tests/test_skills_registry.py` passed (7 tests).
  - Static check confirms only one remaining `fal_client.upload_file` call in template and it is inside provider-gated helper `upload_reference()`.
- Pipeline separation + inference scaffold verification (Phase 6B):
  - `python3 -m py_compile brandmint/pipeline/visual_backend.py brandmint/pipeline/executor.py` passed.
  - `pytest -q tests/test_visual_backend.py` passed (3 tests).
  - End-to-end scaffold smoke test passed (backend `inference` created runbook + per-asset scaffold files under `.brandmint/inference-agent-scaffolds/<batch>/`).
- New blockers logged to GitHub before rollout continuation:
  - #67 Non-FAL provider crash risk from unguarded `fal_client.upload_file` calls in generated scripts.
  - #68 Main visual launch path bypasses core provider adapters (duplicated provider logic).
  - #69 Cost accounting is provider-only (not model-aware; no inference cost path).
  - #70 Provider fallback behavior mismatch between docs and runtime execution.
  - #64 and #66 updated with Inference docs-backed API/X integration requirements (run/status/result, OAuth scopes, callback URL).

---

## Task Addendum (2026-03-04): Inference Media Scaffold Mapping

Objective: inspect imported inference skills in `skills/external/inference-sh/normalized`, then define a concrete batch-type → skill mapping and a minimal scaffold output schema for per-asset custom prompts.

### Plan
- [x] Inventory normalized inference skills and import manifest metadata.
- [x] Extract media-relevant capability coverage from imported `SKILL.md` files.
- [x] Cross-map Brandmint visual batch taxonomy (`anchor`, `identity`, `products`, `photography`, `illustration`, `narrative`, `posters`) to inferred skill responsibilities.
- [x] Propose minimal scaffold file schema for per-asset custom prompt generation.
- [x] Deliver recommendation with concrete mapping and schema.

### Review
- Confirmed imported normalized skill IDs:
  - `infsh-agent-tools`
  - `infsh-agentic-browser`
  - `infsh-ai-image-generation`
  - `infsh-ai-video-generation`
  - `infsh-llm-models`
  - `infsh-python-executor`
  - `infsh-web-search`
- Confirmed current visual batch taxonomy from runtime:
  - `anchor`, `identity`, `products`, `photography`, `illustration`, `narrative`, `posters`
- Recommendation direction:
  - image-first batches map to `infsh-ai-image-generation`;
  - prompt-authoring maps to `infsh-llm-models`;
  - optional enrichment/automation maps to browser/search/python support skills.

---

## Task Addendum (2026-03-04): Controlled Imported Skill Adoption

Objective: add a no-break, config-gated path to use imported `infsh-*` skills in existing waves without changing wave IDs.

### Plan
- [x] Add default inference imported-skill allowlist file under `skills/external/inference-sh/normalized/`.
- [x] Implement policy loader for imported-skill enablement, allowlist, and scenario override mapping.
- [x] Wire execution-time skill substitution in `WaveExecutor` (default off, explicit opt-in only).
- [x] Pass selected scenario ID into executor so overrides can be scenario-scoped.
- [x] Add regression tests for policy resolution and substitution behavior.
- [x] Verify with targeted `pytest` and compile checks.

### Review
- Superseded by user clarification: integration scope narrowed to image-generation flows only.

### Correction Note (User Clarification)
- [x] Narrow imported-skill adoption to **image-generation-specific** flows only.
- [x] Remove text-skill substitution path for imported `infsh-*` IDs.
- [x] Keep allowlist + overrides only in inference visual backend scaffolding.
- [x] Update docs/config examples to reflect image-only scope.
- [x] Replace tests accordingly and re-verify.
- Result:
  - Image-skill policy now lives in `generation.inference_skill_policy` and is enforced in `brandmint/pipeline/visual_backend.py`.
  - Allowlisted, supported image roles only:
    - scaffold: `infsh-llm-models`
    - media: `infsh-ai-image-generation`, `infsh-agentic-browser`
  - Verification:
    - `python3 -m py_compile brandmint/pipeline/visual_backend.py brandmint/pipeline/executor.py brandmint/cli/launch.py`
    - `pytest -q tests/test_visual_backend.py tests/test_generate_pipeline_template.py tests/test_skills_registry.py`
    - `python3 -m brandmint.cli.app launch --config assets/example-tryambakam-noesis.yaml --scenario crowdfunding-lean --dry-run --non-interactive`

### Meta-Semantic Upgrade ("Brain" Routing)
- [x] Add meta-semantic media skill selector in inference backend.
- [x] Allow semantic config for browser-routing intent via `semantic_routing`.
- [x] Keep explicit overrides as highest priority and keep allowlist enforcement.
- [x] Add tests for enabled/disabled semantic behavior.
- [x] Verify compile + targeted tests + launch dry-run.
- Result:
  - `generation.inference_skill_policy.semantic_routing` now drives semantic selection.
  - Default semantic intent maps screenshot/UI semantics to `infsh-agentic-browser`.
  - Non-screenshot visual assets keep `infsh-ai-image-generation` unless overrides apply.

---

## Task Addendum (2026-03-04): One-Shot 20 Improvements Implementation

Objective: implement the full 20-point one-shot improvement pack for inference visual integration, safety rails, diagnostics, and rollout controls.

### Plan
- [x] 1) Add `bm inference doctor`.
- [x] 2) Add semantic routing confidence + reason in scaffold payloads.
- [x] 3) Externalize semantic rules into versioned YAML.
- [x] 4) Add `--inference-only-visual` launch flag.
- [x] 5) Add per-asset backend fallback planning (`inference -> scripts`) in scaffolds.
- [x] 6) Add strict scaffold schema validation.
- [x] 7) Add deterministic run/scaffold IDs.
- [x] 8) Add prompt lineage in scaffold payloads and markdown.
- [x] 9) Add golden prompt diff test coverage.
- [x] 10) Add `bm visual diff`.
- [x] 11) Add style-anchor carry-forward checks.
- [x] 12) Add post-run asset contract validation command.
- [x] 13) Add semantic domain packs.
- [x] 14) Add UI controls for inference policy (settings bridge + UI state payload).
- [x] 15) Add semantic route test command.
- [x] 16) Add CI integrity check for normalized inference pack.
- [x] 17) Add runbook status fields per asset.
- [x] 18) Add rerun-failed command for runbooks.
- [x] 19) Add execution report section for routing decisions.
- [x] 20) Add rollout mode controls (`ring0|ring1|ring2`).

### Review
- Added new CLI groups/commands:
  - `bm inference doctor`
  - `bm inference route-test`
  - `bm inference rerun-failed`
  - `bm visual diff`
  - `bm visual contract-verify`
- Added rollout-aware launch controls:
  - `bm launch --inference-only-visual`
  - `bm launch --inference-rollout-mode ring0|ring1|ring2`
- Added external semantic rules file:
  - `config/inference-semantic-routing.v1.yaml` (default + domain packs)
- Added runbook tooling module:
  - `brandmint/pipeline/inference_runbook.py` (diff, fingerprint, contract validation, failed-asset extraction)
- Added execution report routing capture:
  - `ExecutionReport.routing_decisions`
  - wave executor now records routing decisions per batch when supported by backend
- Added UI/bridge controls for inference policy:
  - backend + frontend settings support for visual backend, rollout mode, semantic routing toggle, semantic domain pack, fallback toggle
- Added CI integrity job:
  - `.github/workflows/inference-pack-integrity.yml`
- Added test coverage:
  - `tests/test_inference_runbook.py`
  - expanded `tests/test_visual_backend.py`
- Verification:
  - `python3 -m py_compile brandmint/cli/app.py brandmint/cli/launch.py brandmint/cli/visual.py brandmint/cli/inference.py brandmint/cli/report.py brandmint/pipeline/visual_backend.py brandmint/pipeline/executor.py brandmint/pipeline/inference_runbook.py scripts/ui_backend_bridge.py`
  - `pytest -q tests/test_visual_backend.py tests/test_inference_runbook.py tests/test_generate_pipeline_template.py tests/test_skills_registry.py` (20 passed)
  - `python3 -m brandmint.cli.app inference doctor --config assets/example-tryambakam-noesis.yaml`
  - `python3 -m brandmint.cli.app inference route-test --config assets/example-tryambakam-noesis.yaml --batch products --assets APP-SCREENSHOT,3A`
  - `python3 -m brandmint.cli.app visual diff --left <runbook-a> --right <runbook-b> --strict`
  - `python3 -m brandmint.cli.app visual contract-verify --runbook <runbook>`
  - `python3 -m brandmint.cli.app inference rerun-failed --config assets/example-tryambakam-noesis.yaml --runbook <failed-runbook> --backend inference`

---

## Task Addendum (2026-03-04): CLI Pipeline + Skill Pack Latest Hardening

Objective: fix CLI pipeline regressions, restore green validation/build paths, and refresh external inference skills to latest upstream shape.

### Plan
- [x] Baseline audit: full pytest, CLI doctor commands, skill-pack validation, UI build.
- [x] Fix hydrator test contract drift after expanded hydration map.
- [x] Fix UI TypeScript build blockers (`JSX` namespace + Node type resolution for `vite.config.ts`).
- [x] Update inference importer for latest upstream repository layout (no legacy `skills/` root assumption).
- [x] Refresh external inference snapshot to latest upstream commit and regenerate normalized pack.
- [x] Regenerate normalized allowlist after import and re-run pack validation.
- [x] Prevent upstream source snapshot directories from polluting active skill discovery.
- [x] Re-run CLI smoke matrix + Tauri dev boot validation.

### Review
- Hydrator tests fixed by updating fixtures/expectations for newly mapped skills:
  - `visual-identity-core`
  - `detailed-product-description`
- UI build fixed:
  - `ui/src/App.tsx` output viewer return type annotation simplified (removes `JSX.Element` namespace dependency).
  - `ui/tsconfig.node.json` now includes Node types.
  - installed `@types/node` in `ui` dev dependencies.
- Inference importer upgraded for latest upstream structure:
  - supports recursive `SKILL.md` discovery when upstream has no top-level `skills/` directory.
  - slug conflict handling for nested paths.
  - auto-generates `normalized/allowlist.yaml` from imported normalized IDs.
- Latest external snapshot imported from `inference-sh/skills`:
  - commit: `ab546d072f1e`
  - imported (curated): 7 skills
  - path: `skills/external/inference-sh/upstream/ab546d072f1e/`
- Registry hardening:
  - excludes `skills/external/**/upstream/**` from active skill discovery.
  - avoids false conflict spikes from raw upstream snapshots.
- Verification matrix:
  - `pytest -q` -> `60 passed`
  - `npm --prefix ui run build` -> pass
  - `python3 scripts/validate_skill_pack.py --pack-root skills/external/inference-sh/normalized` -> pass
  - `python3 -m brandmint.cli.app registry doctor` -> pass/warn (non-blocking duplicate IDs in external Claude skill tree)
  - `python3 -m brandmint.cli.app inference doctor --config assets/example-tryambakam-noesis.yaml` -> pass/warn (expected warnings for default `visual_backend=scripts` and missing API key)
  - `python3 -m brandmint.cli.app launch ... --inference-only-visual --inference-rollout-mode ring1 --dry-run` -> pass
  - Tauri dev smoke (`npm --prefix ui run tauri:dev -- --no-watch`) -> boot success; sidecar healthy.

---

## Task Addendum (2026-03-04): Strict Registry + Provider Bridge Wave

Objective: remove false-positive registry conflicts in strict mode and execute the next runtime unification wave by routing non-FAL generated-script execution through core provider adapters (with safe fallback).

### Plan
- [x] Add variant-aware dedupe logic in `SkillsRegistry` for known `.claude/skills` duplicate families (`Thinking/`, `Utilities/`, `document-skills/`) without suppressing real collisions.
- [x] Add regression tests proving variant duplicates are mergeable while unrelated duplicate IDs still conflict.
- [x] Re-run `bm registry doctor --strict` and confirm strict pass.
- [x] Add a no-break provider bridge in generated script header:
  - prefer `brandmint.core.providers` for non-FAL execution.
  - keep legacy inline provider code as fallback when adapter import/setup is unavailable.
- [x] Route non-FAL generation callsites (`nano-banana`, `flux`, `recraft`) through the bridge helper.
- [x] Extend template tests to assert bridge presence and callsite routing.
- [x] Run full verification matrix (tests + build + doctors + launch dry-run + route-test).

### Review
- Strict registry cleanup:
  - `brandmint/core/skills_registry.py` now canonicalizes known Claude duplicate family roots (`Thinking`, `Utilities`, `document-skills`) and merges these as the same skill lineage.
  - canonical markdown path is preserved on merge (first-discovered path retained).
  - Result: `python3 -m brandmint.cli.app registry doctor --strict` now reports `ID conflicts = 0` and exits cleanly.
- Registry tests:
  - Added/extended `tests/test_skills_registry.py` with:
    - variant duplicate merge coverage
    - non-variant duplicate conflict coverage
  - verification: `pytest -q tests/test_skills_registry.py` -> passed.
- Provider-path unification bridge:
  - `scripts/generate_pipeline.py` generated script header now attempts to load `brandmint.core.providers.get_provider` for non-FAL execution.
  - Added `gen_with_non_fal(...)` helper that prefers core adapter execution and falls back to legacy inline provider implementations if adapter import/setup fails.
  - Non-FAL callsites in `gen_nano_banana`, `gen_flux_pro`, and `gen_recraft` now route through the bridge helper.
- Template tests:
  - Expanded `tests/test_generate_pipeline_template.py` to assert:
    - core provider bridge import markers
    - bridge helper presence
    - legacy fallback path retention
    - non-FAL callsite routing through bridge helper
  - verification: `pytest -q tests/test_generate_pipeline_template.py` -> passed.
- Full verification matrix:
  - `python3 -m py_compile brandmint/core/skills_registry.py scripts/generate_pipeline.py` -> pass
  - `pytest -q` -> `64 passed`
  - `npm --prefix ui run build` -> pass
  - `python3 -m brandmint.cli.app inference doctor --config assets/example-tryambakam-noesis.yaml` -> pass/warn (expected: scripts backend default + missing API key)
  - `python3 -m brandmint.cli.app inference route-test --config assets/example-tryambakam-noesis.yaml --assets APP-SCREENSHOT,LOGO` -> pass
  - `python3 -m brandmint.cli.app launch --config assets/example-tryambakam-noesis.yaml --inference-only-visual --inference-rollout-mode ring1 --dry-run` -> pass
  - script generation smoke (`python3 scripts/run_pipeline.py generate ...`) produced bridge-enabled scripts successfully.

---

## Task Addendum (2026-03-04): #68 Full Core Adapterization + #64 Inference Provider Runtime

Objective: complete provider-path unification by removing inline provider HTTP logic from generated scripts (including FAL direct branches), then add a real core `inference` provider adapter so `generation.provider=inference` executes in the launch runtime.

### Plan
- [x] Refactor generated script template to use core provider adapters for all providers (`fal`, `openrouter`, `openai`, `replicate`, `inference`) and remove inline provider HTTP implementations.
- [x] Remove direct `fal_client.subscribe` execution branches from generated template functions and route all model calls through a single core-provider helper.
- [x] Add `InferenceProvider` in `brandmint/core/providers` with run + poll task lifecycle against Inference REST endpoints and image output download.
- [x] Register `inference` provider in core provider factory + model mapping + capability/cost metadata.
- [x] Wire template/runtime config so `generation.provider=inference` sets endpoint/key inputs correctly for generated scripts.
- [x] Update docs/schema defaults and provider docs for `api.inference.sh` endpoint and unified provider path behavior.
- [x] Add/adjust tests for:
  - provider registry mapping includes `inference`
  - generated template contains no inline provider HTTP path markers
  - inference provider task lifecycle happy/failure parsing (mocked HTTP)
- [x] Run full verification matrix (commit + push next).

### Review
- Implemented #68 full adapterization in generated script templates:
  - removed inline provider HTTP generation functions
  - removed direct `fal_client.subscribe` runtime branches
  - unified model generation through `gen_with_provider()` -> `CORE_PROVIDER.generate(...)`
  - retained reference handling via `upload_reference()` path handoff into provider adapters.
- Implemented #64 runtime inference provider adapter:
  - added `brandmint/core/providers/inference_provider.py`
  - registered `inference` in provider factory, provider enum, fallback chain, and model/capability/cost maps
  - added Inference task lifecycle support (`/api/v1/apps/run` + `/api/v1/tasks/{id}` + `/api/v1/tasks/{id}/result` fallback).
- Updated endpoint defaults/docs to `https://api.inference.sh` and refreshed provider mapping docs.
- Added/updated tests:
  - `tests/test_generate_pipeline_template.py` (adapter-only template assertions)
  - `tests/test_inference_provider.py` (factory registration + runtime task lifecycle mock).
- Verification executed:
  - `python3 -m py_compile brandmint/core/providers/inference_provider.py brandmint/core/providers/fal_provider.py scripts/generate_pipeline.py` -> pass
  - `pytest -q tests/test_generate_pipeline_template.py tests/test_inference_provider.py` -> `7 passed`
  - `pytest -q` -> `67 passed`
  - `npm --prefix ui run build` -> pass
  - `python3 -m brandmint.cli.app inference doctor --config ./assets/example-tryambakam-noesis.yaml` -> pass/warn (expected warnings for scripts backend default and missing API key)
  - `python3 -m brandmint.cli.app inference route-test --config ./assets/example-tryambakam-noesis.yaml --batch products --assets APP-SCREENSHOT,3A` -> pass
  - `python3 -m brandmint.cli.app registry doctor --strict` -> pass
  - `python3 -m brandmint.cli.app launch --config ./assets/example-tryambakam-noesis.yaml --dry-run` -> pass
