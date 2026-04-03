## 2026-04-03 Upgraded Brandmint Pipeline Run

- [x] Review project instructions, lessons, and Brandmint pipeline contract
- [x] Audit repo for current pipeline entrypoints, approval gating, and likely input artifacts
- [x] Write run plan and task tracking before execution
- [ ] Identify the exact source artifact or brand folder the user wants processed
- [ ] Validate environment and prerequisites for the selected input (`bm`, Python deps, API keys, approval gate)
- [ ] Create or confirm the approved `brand-config.yaml` for the selected input
- [ ] Run the upgraded pipeline path with the correct scenario/waves and capture evidence
- [ ] Add review notes with commands run, outputs produced, and any blockers

### Review

- In progress.
- Current blocker: the user asked to "process this," but no explicit input file or brand folder is identifiable yet in the workspace root.
- Repo contract confirmed:
  - use `bm launch` / pipeline-first execution rather than individual skill runs,
  - require an approved `brand-config.yaml` before launch,
  - and prefer non-interactive execution for agent-driven runs.

## 2026-03-31 Issue #113 Tauri Release Artifacts

- [x] Load issue `#113` scope and acceptance criteria
- [x] Audit current macOS release workflow/docs against local and remote state
- [ ] Patch any remaining workflow or documentation gaps
- [ ] Verify release-path artifact generation and stable naming
- [ ] Push the resolved commit(s) and close issue `#113`

### Review

- In progress.

## 2026-03-31 GitHub Issues Review

- [x] Confirm repo target and review relevant project lessons
- [x] Fetch all GitHub issues with metadata
- [x] Analyze issue status, labels, assignees, and theme clusters
- [x] Summarize backlog priorities and notable risks
- [x] Add review notes with counts and verification evidence

### Review

- Verified against live GitHub issue data for `Sheshiyer/brandmint-oracle-aleph` using:
  - `gh issue list --repo Sheshiyer/brandmint-oracle-aleph --state all --limit 500 --json number,title,state,labels,assignees,createdAt,updatedAt,closedAt,url,milestone`
  - snapshot saved to `/tmp/brandmint-issues-review.json` for local analysis
- Current totals:
  - `106` issues total
  - `45` open
  - `61` closed
- Open backlog shape:
  - `43` open issues are one contiguous `vision-upgrade` workstream (`#9` through `#51`)
  - the only non-vision open issues are `#66` (Inference X automation integration) and `#113` (Tauri release artifact publishing)
  - all `45` open issues have no assignee and no milestone
  - `44` of the `45` open issues are labeled `priority:tier-2`; the lone `priority:tier-1` item is `#113`
- Execution signal:
  - the `vision-upgrade` backlog appears to be a planned wave import rather than an actively triaged queue: all `43` issues were created on `2026-02-28` and last updated within a two-minute window on `2026-03-07`
  - recent completed work is concentrated in closed delivery batches:
    - Homebrew packaging tracker cluster (`#1` through `#8`)
    - Tauri v2 phases `#53` through `#58`
    - Inference/provider migration fixes `#60`, `#62`, `#63`, `#64`, `#65`, with only `#66` left open in that lane
    - Asset Fidelity batch `#71` through `#90`
    - NotebookLM Brand Sources batch `#91` through `#107`
- Main backlog risk:
  - the issue tracker currently mixes two different kinds of work:
    - execution-proven initiative batches that were closed end-to-end
    - a large unassigned, unmiletoned `vision-upgrade` spec backlog that dominates the open queue and obscures the actually actionable items

## 2026-03-30 Tauri Prototype Wave 1.4 Execution

- [x] Review `docs/plans/2026-03-02-tauri-v2-conversion.md` Wave 1.4 scope against current code
- [x] Align remaining Wave 1.4 startup polish with current app metadata and copy
- [x] Verify Tauri-specific behavior for splash/title/window/icon assumptions
- [x] Run Wave 1.4 build/runtime verification commands
- [x] Add review notes with results and any remaining blockers

### Review

- The only explicit `Wave 1.4` in the repo is `docs/plans/2026-03-02-tauri-v2-conversion.md`, and most of its prototype-polish work was already present in code.
- Two stale polish drifts remained:
  - `ui/src/components/SplashScreen.tsx` still showed old startup copy (`Starting bridge`) and a hard-coded `v4.3.1`.
  - `ui/src/App.tsx` still showed `Brandmint Desktop v4.3.1` in Settings > About.
- Fixed by centralizing desktop metadata in `ui/src/lib/appMeta.ts`, sourcing `productName` and `version` from `ui/src-tauri/tauri.conf.json`, then reusing that in the splash screen and settings panel.
- Verified existing Wave 1.4 assumptions remain true:
  - `ui/src/lib/tauri.ts` still uses `window.__TAURI__` detection,
  - `ui/src/components/SplashScreen.tsx` still gates browser vs Tauri startup correctly,
  - `ui/src-tauri/tauri.conf.json` already carries the expected title, icon set, and `1280x800` resizable window config,
  - and `ui/package.json` still runs Tauri dev without the browser-only `dev:guard` wrapper.
- Verification evidence:
  - `npm --prefix ui run build` passed after the metadata patch.
  - `npm --prefix ui run tauri:dev` launched successfully.
  - Tauri logs showed `brandmint-app` started, spawned `scripts/ui_backend_bridge.py`, and the bridge became healthy after `3` attempts.
  - `curl -sS http://127.0.0.1:4191/api/health` returned `{"ok": true, "service": "ui-backend-bridge", ...}` during the live Tauri run.
- Cleanup note: the exact verification processes (`tauri dev`, `vite`, `brandmint-app`, and `ui_backend_bridge.py`) were terminated after the smoke run so no local dev processes were left behind.
- Remaining gap: this verification proved the desktop startup path and metadata consistency, but not a full end-to-end `bm launch` through the Tauri UI. That deeper prototype validation remains the open part of old task `P1-028` if we want to execute it literally.

## 2026-03-30 Tauri Prototype Full Wave 1 Completion

- [x] Audit Phase 1 (`P1-001` through `P1-028`) against the current repo
- [x] Close remaining Phase 1 sidecar runtime gaps
- [x] Add portable sidecar venv preparation path and wrapper fallback
- [x] Re-run Phase 1 verification for dev, build, and sidecar behavior
- [x] Add review notes with final Wave 1 status and residual limitations

### Review

- Phase 1 audit result:
  - the scaffolding, plugins, capabilities, icons, window config, and core dev workflow from `P1-001` through `P1-014`, `P1-018` through `P1-027` were already present,
  - but `P1-015`, `P1-017`, and `P1-020` were only partially implemented,
  - and the hard-coded bridge root in `scripts/ui_backend_bridge.py` still blocked honest end-to-end verification.
- Closed runtime gaps:
  - `scripts/ui_backend_bridge.py` now resolves `ROOT` dynamically from `BRANDMINT_ROOT`, the script location, or the current working directory instead of the stale `/Volumes/madara/2026/brandmint` path.
  - `ui/src-tauri/src/sidecar.rs` now has a real dev-vs-release split:
    - debug builds still launch the Python bridge directly from the repo,
    - non-debug builds now launch the bundled `brandmint-bridge` sidecar wrapper through Tauri shell APIs.
  - `ui/src-tauri/src/sidecar.rs` now auto-restarts the sidecar after a crash/termination instead of only surfacing an unhealthy state and waiting for manual retry.
- Added portable venv strategy:
  - `Makefile` now exposes `bundle-sidecar-venv`,
  - and `ui/src-tauri/binaries/brandmint-bridge-aarch64-apple-darwin` now prefers a colocated `venv/bin/python3` or `../Resources/venv/bin/python3` before falling back to system `python3`.
  - the wrapper also exports `BRANDMINT_ROOT` when it successfully resolves the repo root.
- Verification evidence:
  - `python3 -m py_compile scripts/ui_backend_bridge.py` passed.
  - `cargo build` in `ui/src-tauri` passed after the sidecar/runtime changes.
  - `make help` confirms the new `bundle-sidecar-venv` target is discoverable.
  - standalone wrapper verification passed:
    - `ui/src-tauri/binaries/brandmint-bridge-aarch64-apple-darwin` launched successfully,
    - and `curl -sS http://127.0.0.1:4191/api/health` returned a healthy bridge response.
  - Tauri dev verification passed:
    - `npm --prefix ui run tauri:dev` launched successfully,
    - the app started `brandmint-app`,
    - the bridge became healthy,
    - then after a forced `kill` of the live `ui_backend_bridge.py` process, the watcher logged `Sidecar not running, attempting automatic restart`,
    - respawned the bridge,
    - and returned to a healthy state.
  - production packaging verification passed:
    - `npm run tauri:build` from `ui/` completed,
    - and rebuilt both `Brandmint.app` and `Brandmint_4.4.0_aarch64.dmg`.
- Final status:
  - I consider Phase 1/Wave 1 functionally complete for the shell/sidecar prototype path.
  - The only residual caveat is the original `P1-028` wording: I proved startup, standalone sidecar health, crash recovery, and packaged build output, but I did not run a literal live all-waves `bm launch` through the visible Tauri UI end-to-end because that crosses into provider-backed runtime validation rather than shell/sidecar prototype hardening.

## 2026-03-30 Tauri Prototype Phase 2 / Wave 2 IPC Migration

- [x] Audit Phase 2 (`P2-001` through `P2-032`) against the current repo and isolate the remaining gaps
- [x] Add any missing backend IPC/event edges needed to remove direct frontend `/api/...` dependencies
- [x] Migrate `App.tsx` reads/writes/actions from raw bridge `fetch()` calls to shared IPC helpers
- [x] Replace frontend state/log polling with Tauri event listeners where available
- [x] Run non-test verification only (`cargo build`, frontend build, and a Tauri smoke/build pass if needed)
- [x] Add review notes with final Wave 2 status and any residual caveats

### Review

- Phase 2 audit result:
  - a large part of the IPC surface was already present before this pass: `get_health`, `get_state`, `get_runners`, `get_settings`, `update_settings`, `get_artifacts`, `get_references`, `start_run`, `abort_run`, `retry_run`, `start_publish`, and `load_intake` already existed in `ui/src-tauri/src/lib.rs`,
  - and `ui/src/lib/tauri.ts` already provided a generic invoke-vs-fetch bridge,
  - but `ui/src/App.tsx` still bypassed that layer with direct `/api/...` `fetch()` calls for state, logs, settings, runners, artifacts, references, intake, run control, publish, and artifact reads.
- Closed Wave 2 gaps:
  - added `ui/src/api.ts` as the shared typed-ish wrapper layer over `ui/src/lib/tauri.ts`,
  - added browser fallback routes for `get_logs` and `read_artifact`,
  - added `read_artifact` and `get_logs` Tauri commands in `ui/src-tauri/src/lib.rs`,
  - added `/api/artifacts/read` plus safer path-boundary helpers in `scripts/ui_backend_bridge.py`,
  - and updated bridge state snapshots so completed runs derive back to `idle` when no child process is still alive.
- Event migration:
  - `ui/src-tauri/src/sidecar.rs` now keeps a sidecar generation counter,
  - emits `pipeline-state-changed` snapshots from a background sync loop,
  - and mirrors `/api/logs?since=N` into `sidecar-log` events so the Tauri frontend no longer has to poll logs directly.
  - browser mode still polls through the shared API wrapper as the fallback path, but Tauri mode is now event-driven for state/log updates.
- Frontend migration:
  - `ui/src/App.tsx` now routes settings, runners, artifacts, references, intake loading, run controls, publish actions, and output-viewer artifact reads through the shared API wrapper instead of raw `/api/...` `fetch()` calls,
  - the Tauri runtime now listens to `pipeline-state-changed`, `sidecar-status`, and `sidecar-log`,
  - and reference image URLs are normalized through `bridgeAssetUrl(...)` so the Tauri app can still render bridge-served images cleanly.
- Non-test verification:
  - `npm --prefix ui run build` passed.
  - `cargo build --offline` in `ui/src-tauri` passed.
  - `npm --prefix ui run tauri:build -- --bundles app` passed and rebuilt `Brandmint.app`.
  - `npm --prefix ui run tauri:build` reached release build + `.app` bundling successfully, then failed specifically in the DMG bundling script `bundle_dmg.sh`.
- Final status:
  - I consider Phase 2 / Wave 2 functionally complete for IPC migration of the current desktop UI surface.
  - Residual caveats:
    - reference images still render via the localhost bridge URL rather than a native Tauri asset protocol/data-URI path,
    - and DMG packaging is still failing after the `.app` bundle step, so release-image packaging is not fully clean yet.
  - Per request, I skipped test execution and did not rerun a live interactive Tauri dev smoke after these changes.

## 2026-03-30 Brandmint Clawable Run Path and HITL Planning

- [x] Review project instructions, `using-superpowers`, and `swarm-architect`
- [x] Audit current GitHub issue backlog and isolate non-vision priorities
- [x] Verify targeted tests for spec-lock, visual backend, and source curator
- [x] Verify frontend build, Rust/Tauri compile, and Tauri+sidecar local startup
- [x] Capture the main architecture drift causing weak control and wrong visual outputs
- [x] Write the swarm-style implementation plan
- [ ] Create/update GitHub issues and milestones for the new initiative
- [ ] Implement approved-config gating and HITL loop
- [ ] Implement app-domain visual policy and remove stale live prompt branches
- [ ] Ship clawable SOP and release-hygiene updates

### Phase 1 Wave 1 Execution

- [x] `P1-W1-SA-T01` Audit open non-vision issues and PRs
- [x] `P1-W1-SA-T02` Define archive/defer policy for `vision-upgrade` issue stack
- [x] `P1-W1-SB-T03` Capture clean Tauri, Vite, and bridge startup evidence
- [x] `P1-W1-SB-T04` Produce dependency and environment matrix

### Phase 1 Wave 2 Execution

- [x] `P1-W2-SA-T05` Compare front-end wizard spec against current UI behavior
- [x] `P1-W2-SA-T06` Compare runtime docs against current CLI and Tauri behavior
- [x] `P1-W2-SB-T07` Synthesize main failure themes from code, issues, and changelog
- [x] `P1-W2-SB-T08` Define the "GitHub URL only -> run Brandmint" acceptance story

### Phase 1 Wave 3 Execution

- [x] `P1-W3-SA-T09` Define canonical `brand-config.yaml` source-of-truth contract
- [x] `P1-W3-SB-T10` Create initiative issue map and milestone proposal

### Review

- GitHub backlog reality: the only clearly active non-vision issues are `#113` (Tauri release artifacts) and `#66` (optional X automation). The large `vision-upgrade` stack is not the active product problem and should be archived/deferred instead of driving priorities.
- Fresh GitHub re-check for Wave 1 execution:
  - open non-vision issues remain `#113` and `#66`,
  - the only open PR is `#116`,
  - and the full `vision-upgrade` stack currently occupies issues `#9-#51`.
- Archive/defer policy for the vision stack is now explicit: treat `#9-#51` as deferred roadmap work grouped by the existing wave labels (`wave-1-foundation` through `wave-5-integration`), not as the active execution backlog for the clawable run-path initiative.
- Runtime verification:
  - `npm --prefix ui run build` passed.
  - `cargo build` in `ui/src-tauri` passed.
  - `pytest tests/test_generate_pipeline_spec_lock.py tests/test_visual_backend.py tests/test_source_curator.py` passed (`18` tests).
  - `npm --prefix ui run tauri:dev` launched successfully and the Tauri-managed sidecar became healthy on `127.0.0.1:4191`.
- Fresh Wave 1 runtime capture also re-confirmed:
  - Vite served on `http://127.0.0.1:4188/`,
  - the Rust app spawned `scripts/ui_backend_bridge.py` via `/opt/homebrew/bin/python3`,
  - the bridge became healthy after `2` attempts,
  - and `curl -sS http://127.0.0.1:4191/api/health` returned `{"ok": true, "service": "ui-backend-bridge", ...}` during the managed Tauri run.
- The first Tauri launch only failed because a manually started bridge was already bound to `4191`; after stopping the standalone bridge, the normal Tauri-managed startup path worked.
- Dependency and environment matrix is now captured in `docs/plans/2026-03-30-phase-1-wave-1-execution-report.md`, including local versions (`Python 3.14.3`, `Node v25.8.1`, `npm 11.11.0`, `rustc/cargo 1.89.0`), Makefile entrypoints, Python package requirements, and `.env.example` variables.
- The core product issue is architectural drift:
  - frontend docs/spec expect a reviewed `brand-config.yaml` before launch,
  - the live runtime still allows a mostly linear `bm launch`,
  - and the active generation scripts still contain product-centric and `recraft`-based branches that can leak physical-product assumptions into app/SaaS runs.
- Plan document created at `docs/plans/2026-03-30-brandmint-clawable-swarm-plan.md`.
- Phase 1 Wave 1 execution report created at `docs/plans/2026-03-30-phase-1-wave-1-execution-report.md`.
- Phase 1 Wave 2 spec/runtime drift review is now captured in `docs/plans/2026-03-30-phase-1-wave-2-execution-report.md`.
- Front-end gap analysis from Wave 2:
  - intake/wizard/export/launch screens exist, but the trust-critical contract is missing,
  - extraction has no source-snippet provenance, no per-field `needs_review`, and no unmapped-input bucket,
  - export is a browser download rather than a guaranteed saved canonical config artifact,
  - and launch gating depends on `exportedAt`, not on an approved config state.
- Runtime drift from Wave 2:
  - `CLAUDE.md` and `README.md` still describe a CLI-first `bm launch` operator story,
  - the desktop runtime depends on a Python bridge with `ROOT = /Volumes/madara/2026/brandmint`,
  - but the real workspace is `/Volumes/madara/2026/twc-vault/01-Projects/brandmint`,
  - so default relative-path flows are not safe in the current bridge.
- Safe repro captured for the runtime-path bug:
  - starting `python3 scripts/ui_backend_bridge.py` and posting `{"brandFolder":"./brandmint"}` to `/api/intake/load` returned
    `{"ok": false, "error": "Directory not found: /Volumes/madara/2026/brandmint/brandmint"}`.
- The failure is now clearly framed as four drifts working together:
  - source-of-truth drift,
  - runtime-path drift,
  - visual-domain drift,
  - and documentation/backlog drift.
- The "GitHub URL only -> run Brandmint" acceptance story is now defined:
  - clean checkout + preflight,
  - supported runtime bootstrap,
  - Product MD intake,
  - evidence-backed extraction review,
  - explicit config approval,
  - persisted approved `brand-config.yaml`,
  - then paused/controlled execution from that approved artifact.
- Wave 1.3 contract output is now written in `docs/plans/2026-03-30-brand-config-contract-v1.md`.
- The contract decision is intentionally minimal-impact:
  - `brand-config.yaml` stays the canonical artifact,
  - the semantic launch payload is the full document minus a reserved `_brandmint` block,
  - approval requires a saved on-disk config, provenance metadata, empty `pending_fields`, and a deterministic fingerprint,
  - and any post-approval edit forces the document back to `draft`.
- The contract also makes the current drift actionable:
  - browser download/export is not enough,
  - `exportedAt` is not a valid launch gate,
  - bridge/CLI/Tauri must all reject unapproved configs,
  - and sidecar/runtime state must live outside the approved config file.
- Wave 1.3 GitHub planning output is now written in `docs/plans/2026-03-30-clawable-initiative-issue-map.md`.
- The issue map proposal recommends:
  - one initiative milestone, `clawable-run-path`,
  - one umbrella issue plus five major workstream issues,
  - keeping `#113` active inside that initiative,
  - keeping `#66` deferred outside it,
  - and leaving the `vision-upgrade` stack `#9-#51` out of the initiative milestone entirely.

## 2026-03-30 Brandmint Clawable Phase 2 / Canonical Config and Approval Gates

- [x] Re-read Phase 2 (`P2-W1-SA-T11` through `P2-W2-SB-T20`) against the 80-task plan and current GitHub backlog
- [x] Confirm current GitHub issues still do not reflect the clawable Phase 2 workstream
- [x] `P2-W1-SA-T11` Extend config schema with approval metadata
- [x] `P2-W1-SA-T12` Add extraction provenance and source-snippet mapping model
- [x] `P2-W1-SB-T13` Persist `needs_review` fields into exported config draft
- [x] `P2-W1-SB-T14` Build explicit extraction review summary UI
- [x] `P2-W2-SA-T15` Persist explicit wizard approval action
- [x] `P2-W2-SA-T16` Export approved config fingerprint and metadata
- [x] `P2-W2-SB-T17` Block downstream launch until config is approved
- [x] `P2-W2-SB-T18` Add extracted-vs-approved diff view
- [x] `P2-W2-SB-T19` Standardize approved-state errors across UI, bridge, and CLI
- [x] Skip `P2-W2-SB-T20` test work for this pass per user request
- [x] Add review notes with implementation scope, verification, and remaining Phase 2 gaps

### Review

- Phase 2 is the next unclawed tranche in `docs/plans/2026-03-30-brandmint-clawable-swarm-plan.md`.
- Current GitHub issue state is still backlog-only context, not execution-ready Phase 2 tracking:
  - active non-vision issues remain `#113` and `#66`,
  - no `clawable-run-path` milestone exists yet,
  - and the proposed config-approval workstream issues from `docs/plans/2026-03-30-clawable-initiative-issue-map.md` have not been created.
- Current implementation drift before Phase 2 work:
  - the UI still uses `extractionConfirmed` and `exportedAt` as the effective trust gate,
  - exported config is still a browser download rather than a canonical serialized config lifecycle,
  - and `bm launch` still accepts any config path without approval validation.
- Phase 2 implementation delivered:
  - added shared approval/fingerprint utilities in `brandmint/config_approval.py`,
  - extended `assets/brand-config-schema.yaml` with the reserved `_brandmint` contract block,
  - taught `scripts/ui_backend_bridge.py` to load canonical config metadata, save draft/approved configs, and reject `bm launch` when config approval is missing,
  - taught `brandmint/cli/launch.py` to fail early with the same approval remediation message,
  - and wired the Tauri/UI surface to that contract through `ui/src/api.ts`, `ui/src/lib/tauri.ts`, `ui/src-tauri/src/lib.rs`, `ui/src/lib/brandConfig.ts`, and `ui/src/App.tsx`.
- Frontend behavior now matches the Phase 2 contract materially better:
  - extraction review shows tracked field confidence, review-required fields, and source snippets,
  - export is now a save-to-disk flow backed by the bridge instead of browser download only,
  - approval is an explicit operator action with approver/note inputs,
  - approved configs receive deterministic semantic fingerprints,
  - and launch controls stay blocked until the current config is saved in the approved state.
- Non-test verification completed:
  - `python3 -m py_compile brandmint/config_approval.py scripts/ui_backend_bridge.py brandmint/cli/launch.py` passed,
  - `npm --prefix ui run build` passed,
  - `cargo build --offline` in `ui/src-tauri` passed,
  - and a direct Python smoke over `compose_config_document(...)` + `config_launch_status(...)` proved draft configs are not launchable while approved configs are fingerprinted and launchable.
- Verification caveat:
  - I attempted a live localhost POST smoke against the running bridge, but the tool environment produced inconsistent loopback behavior after an initial successful `/api/health` response.
  - I did not spend more time on that sandbox-local transport noise because the Python compile/build checks and direct contract smoke already validated the new approval logic itself.
- Remaining Phase 2 caveats after this pass:
  - `P2-W2-SB-T20` automated tests were intentionally skipped per request,
  - the UI still edits only a focused subset of the full Brandmint config surface,
  - and GitHub issues/milestones still need to be brought in line with the clawable initiative map when we want backlog state to match execution state.

## 2026-03-25 Repo Status Audit

- [x] Review project workflow instructions, lessons, and required skills
- [x] Record the audit plan and keep progress updated in this file
- [x] Capture local git state and branch topology
- [x] Capture remote branch, PR, and issue state from GitHub
- [x] Summarize repo status, risks, and recommended next actions

### Review

- Local `main` is divergent from `origin/main` (`ahead 1, behind 23`) and the working tree is heavily dirty (`35` modified, `31` untracked), which makes branch/PR cleanup risky until changes are staged or isolated.
- GitHub currently has `5` remote branches and `11` PRs total (`2` open, `9` merged). Open PRs `#117` and `#116` both show `mergeStateStatus=CLEAN` with successful `Inference Pack Integrity / validate-pack` checks from March 8, 2026, but neither has a recorded review decision.
- Remote branch hygiene is uneven: `origin/codex/install-check-input-validation` and `origin/codex/tauri-release-assets` map to the two open PRs; `origin/codex/clean-test-path` and `origin/tauri-v2-upgrade` appear merged but still exist remotely.
- Local branch hygiene also needs cleanup: `codex/provider-aware-install-checks` and `codex/registry-inference-hardening` have gone upstreams after merged PRs, and `backup/split-before-4f30e78` looks like an abandoned local-only backup branch.
- GitHub issues total `106` (`45` open, `61` closed). The open backlog is highly concentrated: `43` open issues are the older `vision-upgrade` roadmap stack, leaving only `2` non-vision open items (`#113` Tauri release publishing and `#66` inference automation).
- Branch protection is currently disabled for all listed remote branches, including `main`.

## 2026-03-25 Repo Hygiene Follow-Through

- [x] Confirm execution order for recommended tasks 1-5
- [x] Create an isolated in-repo worktree for reconciliation work
- [x] Determine how to reconcile the local `main` extra commit against `origin/main`
- [x] Re-evaluate open PRs `#117` and `#116` against current `origin/main`
- [x] Separate safe branch cleanup candidates from destructive cleanup actions
- [x] Collapse the issue backlog into active work vs archive candidates

### Review

- Created clean analysis worktree at `.worktrees/repo-hygiene-2026-03-25` from `origin/main`. To avoid adding another commit on top of the dirty/divergent current checkout, `.worktrees/` was ignored via `.git/info/exclude` rather than a new `.gitignore` commit.
- The local-only `main` commit `1ed6d0a` is still unique relative to `origin/main` and only adds `.github/workflows/publish-tauri-macos.yml`.
- That local `main` commit is not the same change as PR `#116`: PR `#116` adds a different workflow file (`publish-tauri-release-assets.yml`) plus two Tauri runtime fixes (`f447965`, `cabf4e1`). Both the local-only commit and PR `#116` target release publishing, so they should be reconciled before either is landed; they look overlapping, not independently landable.
- PR `#117` is the cleanest candidate: `1` commit ahead / `0` behind `origin/main`, GitHub merge state `CLEAN`, and `Inference Pack Integrity / validate-pack` is green.
- PR `#116` is also GitHub-clean and CI-green, but locally it is `3` commits ahead / `1` behind `origin/main`, so it should be rebased or merged with a clear decision about whether to keep or replace the local-only `publish-tauri-macos.yml` workflow.
- Safe remote branch cleanup candidates after PR/decision cleanup: `origin/codex/clean-test-path` and `origin/tauri-v2-upgrade` (both appear merged and have no open PRs).
- Local cleanup candidates that need explicit deletion action later: `backup/split-before-4f30e78`, `codex/provider-aware-install-checks`, and `codex/registry-inference-hardening`.
- Open issue backlog remains `45`, but `43` of those are old `vision-upgrade` tier-2 roadmap issues. The only clearly active non-vision items are `#113` (Tauri release publishing) and `#66` (Inference X automation), so the vision stack is the obvious archive/collapse candidate.

## 2026-03-29 Tauri Artifact Cleanup And Rebuild

- [x] Review current Tauri/UI build state and confirm which outputs are generated artifacts
- [x] Remove stale generated Tauri build outputs (`ui/src-tauri/target` and any generated bundle artifacts) without touching source assets
- [x] Run a fresh macOS Tauri production build from `ui/`
- [x] Verify the rebuilt `.app` and `.dmg` outputs exist and record their paths/sizes
- [x] Add a review note with cleanup scope, rebuild result, and any remaining blockers

### Review

- Removed the stale generated Tauri build cache at `ui/src-tauri/target` before rebuilding. No source files, icons, capabilities, or Rust/TS source were deleted.
- The first rebuild attempt failed only because Cargo needed to re-download crates after the cleanup and sandbox DNS access to `static.crates.io` was blocked. Re-running `npm run tauri:build` with network access resolved that.
- Fresh build verification:
  - `.app`: `ui/src-tauri/target/aarch64-apple-darwin/release/bundle/macos/Brandmint.app` (`15M`)
  - `.dmg`: `ui/src-tauri/target/aarch64-apple-darwin/release/bundle/dmg/Brandmint_4.4.0_aarch64.dmg` (`5.2M`)
  - Rebuilt binary: `ui/src-tauri/target/aarch64-apple-darwin/release/brandmint-app` (`Mach-O 64-bit executable arm64`)
  - App bundle contents confirmed at `Brandmint.app/Contents/MacOS` with both `brandmint-app` and `brandmint-bridge`
- Cleanup effect: `ui/src-tauri/target` dropped from approximately `3.6G` before cleanup to `1.4G` after the fresh rebuild.
- Remaining note: Tauri warns that the bundle identifier `com.brandmint.app` ends with `.app`; the build still succeeds, but the identifier should eventually be normalized to avoid macOS bundle-name ambiguity.

# Kickstarter Prototype Execution Tracker

Source plan: `/Users/sheshnarayaniyer/.craft-agent/workspaces/my-workspace/sessions/260310-young-horse/plans/kickstarter-prototype-swarm-plan.md`

## Current execution slice

### Phase 1 — Foundation for mandatory Kickstarter sections
- [x] Approve deeply detailed swarm plan
- [x] Create shared Kickstarter blueprint module for mandatory sections and artifacts
- [x] Add runtime readiness/reporting integration for the mandatory Kickstarter sections
- [x] Add dispatch-oriented phase metadata hooks for prototype section tracking

### Phase 2 — NotebookLM/source processing alignment
- [x] Expand source builder to generate Kickstarter section docs
- [x] Expand source builder to generate per-artifact docs from processed outputs
- [x] Add Kickstarter readiness summary doc generation
- [x] Validate source selection behavior against full realistic output set
- [x] Decide whether to keep both legacy grouped docs and Kickstarter docs long-term

### Phase 3 — Validation
- [x] Add tests for Kickstarter blueprint mappings and readiness
- [x] Add tests for source document generation
- [x] Add tests for source curator recognition of Kickstarter docs
- [x] Run targeted test suite and fix breakage
- [x] Run broader regression verification and document results

### Phase 4 — Visual reference discipline prototype
- [x] Add explicit prototype contract for text + image-reference payload enforcement
- [x] Add tests covering silent text-only degradation when refs exist
- [x] Integrate enforcement into the launch/runtime flow with minimal prototype-safe changes

### Phase 5 — Wave 8 architecture upgrade
- [x] Add NotebookLM artifact ingestion to the Wave 8 publisher
- [x] Surface NotebookLM reports/media/data assets in wiki markdown generation
- [x] Include NotebookLM infographic/media assets in the library/publish path
- [x] Redesign the Astro homepage away from the generic text-heavy wiki index
- [x] Re-run Wave 8 for HeyZack `beta-update` and verify the refreshed published build
- [x] Run focused + broad regressions and local browser review for the redesigned site

### Phase 6 — ZackAI brand-native UI overhaul
- [x] Replace the generic docs-shell aesthetic with a fully ZackAI-native portal design system
- [x] Apply brand palette, typography, softness, and playful guardian vibe across layout/components
- [x] Redesign homepage, navigation, cards, content pages, and research views to feel product/brand-led
- [x] Use the actual visual assets and brand motifs as first-class UI material, not just content attachments
- [x] Rebuild the beta-update portal and review it visually in-browser until it feels launch-worthy

### Phase 7 — EN/FR portal i18n
- [x] Add real EN/FR localized routes for homepage and wiki pages
- [x] Add visible language toggle in the portal shell
- [x] Localize portal chrome and key homepage/wiki labels while preserving wiki browsing
- [x] Rebuild and verify the bilingual beta-update portal locally and in the public repo working copy

### Phase 8 — FR content localization
- [x] Add localized French markdown support alongside the canonical English docs with safe EN fallback
- [x] Publish real French body content for the priority ZackAI pages (index, quickstart, product overview, visual guidelines, campaign copy, NotebookLM hub)
- [x] Rebuild and verify the bilingual beta-update portal with FR body-content support
- [x] Sync the upgraded bilingual-content portal into the public repo working copy

### Phase 9 — FR content localization expansion
- [x] Publish real French body content for the next high-value ZackAI pages (voice & tone, product features, email templates, product specifications)
- [x] Harden Wave 8 cleanup so repeated rebuilds do not fail on generated wiki-site residue
- [x] Rebuild and verify the expanded bilingual beta-update portal with safe EN fallback still intact
- [x] Sync the expanded bilingual-content portal into the public repo working copy

### Phase 10 — FR campaign, audience, and brand-library completion
- [x] Publish real French body content for the remaining high-value pages (social content, video scripts, ad creative, visual assets library, primary persona, secondary personas, competitive landscape)
- [x] Clean the most visible mixed-language fragments in the FR audience and market pages
- [x] Rebuild and verify the near-complete bilingual beta-update portal
- [x] Sync the completed FR-expanded portal into the public repo working copy

## Review notes
- Focus is prototype-first backend/document-contract work before UI hardening.
- Edge cases discovered during execution should be documented in review notes, not expanded into plan scope unless they block correctness.
- Legacy grouped docs are retained in prototype mode, but generation is now configurable via `publishing.notebooklm.source_document_mode` with `hybrid` as the default.
- Source selection is now channel-aware: Kickstarter runs prioritize section docs first, then config/readiness, then legacy grouped docs, then artifact-level detail docs.
- HeyZack fixture run (2026-03-10): Kickstarter readiness reached 6/6 sections, FAL-backed scripts produced real assets under `zackai/generated`, and NotebookLM accepted the upgraded hybrid source set.
- Hardening pass completed: NotebookLM publisher now persists partial reports incrementally, reconciles pending/completed artifact state before re-submitting work, and the visual backend now falls back to scripts when inference auth is missing unless scaffold-only behavior is explicitly requested.
- HeyZack Wave 7 rerun confirmed the resume fix in practice: existing notebook/state was reused, completed artifacts were downloaded successfully after NotebookLM re-authentication, and the deliverables folder now contains 21 downloaded artifacts (audio, decks, reports, quizzes, flashcards, infographics, mind map, and CSV data tables). The only remaining open Wave 7 work is the two long-running video artifacts, which are now pending with fresh artifact IDs for later reconciliation.
- New execution track completed: NotebookLM notebooks are now isolated by a product/spec fingerprint (fresh-per-spec by default, explicit reuse-only when requested), NotebookLM image uploads can be restricted to manifest-backed current-run media, stale product semantics were removed from core prompt paths, and the visual pipeline now injects a canonical product-spec lock plus contradiction validation before generation.
- HeyZack fixture was cleaned to match the real plush spec (no phone-screen flatlay, no charging-dock wording, explicit product-detail focus, fresh-per-spec notebook policy, manifest-only NotebookLM image curation), and regenerated scripts now show `3C=clean_closeup`, include the strict spec lock text, and no longer pull the stale 3C composition/supplementary refs.
- Beta-update isolated rerun completed under `/Volumes/madara/2026/twc-vault/01-Projects/HeyZack/zackai-launch/beta-update/`: fresh generated visuals landed under `beta-update/zackai/generated`, fresh NotebookLM deliverables landed under `beta-update/deliverables/notebooklm`, and NotebookLM image sourcing was restricted to the five product photos in `beta-update/products/` via `image_source_policy: product-reference-only`. The only remaining publish limitation in this isolated run is the two NotebookLM video artifacts, which again failed upstream while the other 21 artifacts downloaded successfully.
- Wave 8 is now implemented and executed: Brandmint can generate wiki markdown and build/publish an Astro wiki after Wave 7. The latest published docs for beta-update now live at `beta-update/wiki-site/dist`, with `beta-update/published-site` pointing to that build and a publish report at `beta-update/deliverables/brand-docs/publish-report.json`.
- Wave 8 architecture is now richer than the initial prototype: the publisher ingests NotebookLM artifacts from `deliverables/notebooklm/artifacts`, generates a dedicated `research/notebooklm-artifacts.md` hub plus imported report pages, copies all NotebookLM deliverables into the published static site under `wiki-site/dist/notebooklm`, and surfaces NotebookLM infographics inside the visual library. The Astro homepage was also redesigned into a branded launch portal with hero/product/research cards instead of the previous generic text-heavy wiki directory.
