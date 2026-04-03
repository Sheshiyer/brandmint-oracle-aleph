# Brandmint Clawable Run Path and HITL Hardening Plan

Generated: 2026-03-30
Repository: https://github.com/Sheshiyer/brandmint-oracle-aleph
Planning mode: Swarm Architect
Planning depth: deeply detailed
Delivery mode: hardening
CI/CD expectation: production-grade
Release model: phased rollout
Quality bar: tests + smoke checks + docs walkthrough + release gating
Team topology: solo builder with agent assistance

## Discovery Summary

- The current desktop app is operational as a Tauri wrapper around the existing Python HTTP bridge, not yet a fully self-explanatory "give the repo URL and run it" product.
- The intended frontend journey is config-first and review-first:
  `Product MD -> extraction review -> brand-config wizard -> export brand-config.yaml -> launch`.
- The live runtime still permits a mostly linear `bm launch` flow with only light gating, so the approval contract is not enforced end to end.
- The backlog is misaligned with current priorities:
  `#113` is the only immediate Tauri distribution issue; `#66` is optional automation work; the open `vision-upgrade` stack is mostly unrelated to the current product problem and should be archived/deferred, not treated as the active roadmap.
- The main user-facing failure is architectural drift:
  config approval, human-in-the-loop control, app-domain visual routing, and repo-URL-only SOP expectations are specified in pieces, but not unified in the live launch path.

## Baseline Evidence

- `npm --prefix ui run build` passes.
- `cargo build` in `ui/src-tauri` passes.
- `pytest tests/test_generate_pipeline_spec_lock.py tests/test_visual_backend.py tests/test_source_curator.py` passes (`18` tests).
- `npm --prefix ui run tauri:dev` launches successfully with the Tauri-managed sidecar and the bridge becomes healthy on `http://127.0.0.1:4191/api/health`.
- If a standalone bridge is already running, Tauri sidecar startup collides on port `4191` with `OSError: [Errno 48] Address already in use`, so singleton/ownership policy still needs hardening.
- Live generation code still contains active product-centric and `recraft-v3` branches in `scripts/generate_pipeline.py` and `scripts/run_pipeline.py`, even though the changelog says older Noesis/icon defaults were removed.

## Assumptions and Constraints

- Target platform for the desktop hardening path is macOS first.
- Existing CLI and Python pipeline remain the execution backend during this initiative; no full backend rewrite is in scope.
- We should not delete or execute the `vision-upgrade` issue stack; we should classify and archive/defer it.
- `brand-config.yaml` becomes the canonical source of truth for downstream execution, with explicit approval metadata and provenance.
- Downstream text and visual generation must not proceed automatically until the approved config checkpoint is satisfied.
- App/SaaS brands need a separate visual policy from physical-product brands.
- The current worktree is dirty, so implementation should use an isolated branch or worktree before code changes begin.

## Phase Map

| Phase | Focus | Waves | Tasks | Outcome |
|---|---|---:|---:|---|
| 1 | Problem alignment and backlog reset | 3 | 10 | One canonical initiative definition and issue map |
| 2 | Canonical config and approval gates | 2 | 10 | Approved `brand-config.yaml` enforced as source of truth |
| 3 | Human-in-the-loop execution loop | 2 | 10 | Pause/approve/revise/continue workflow across waves |
| 4 | Visual domain safety for app vs product brands | 3 | 12 | No more physical-product prompt leakage into app runs |
| 5 | Tauri runtime and sidecar hardening | 2 | 10 | Deterministic desktop startup and recovery behavior |
| 6 | Clawable SOP and operator docs | 2 | 10 | Repo-URL-to-running-app instructions an agent can follow |
| 7 | GitHub issue and release hygiene | 2 | 8 | Active backlog matches real priorities |
| 8 | QA, acceptance, and rollout | 2 | 10 | Verified release-ready initiative closure |

Total planned tasks: 80

## Detailed Phase 1 Wave and Swarm Layout

### Wave 1.1 - Backlog truth

- Swarm A: issue and PR triage
- Swarm B: runtime evidence capture

### Wave 1.2 - Drift diagnosis

- Swarm A: front-end journey vs runtime flow
- Swarm B: code/docs/issues synthesis

### Wave 1.3 - Initiative contract

- Swarm A: source-of-truth config contract
- Swarm B: GitHub milestone and issue map

## Full Task List

### Phase 1 - Problem Alignment and Backlog Reset

| id | wave | swarm | title | area | owner_role | est_hours | dependencies | deliverable | acceptance | validation |
|---|---|---|---|---|---|---:|---|---|---|---|
| P1-W1-SA-T01 | 1.1 | A | Audit open non-vision issues and PRs | product | Product/PM | 4 | [] | Classified inventory of active non-vision work | Inventory names immediate, deferred, and archive candidates | Saved audit doc with issue numbers and states |
| P1-W1-SA-T02 | 1.1 | A | Define archive/defer policy for `vision-upgrade` issue stack | product | Product/PM | 4 | [P1-W1-SA-T01] | Policy for closing, deferring, or relabeling old vision issues | Team can apply one repeatable rule to all vision issues | Policy doc and sample mapping for issue IDs |
| P1-W1-SB-T03 | 1.1 | B | Capture clean Tauri, Vite, and bridge startup evidence | qa | QA/Runtime Eng | 6 | [] | Verified notes for build, bridge, and Tauri runtime behavior | Startup path is reproducible from commands and logs | Command transcript with successful health checks |
| P1-W1-SB-T04 | 1.1 | B | Produce dependency and environment matrix | infra | DevOps | 4 | [P1-W1-SB-T03] | Matrix for Python, Node, Rust, env vars, OS requirements | A new operator can see what is required before launch | Markdown matrix checked against actual commands |
| P1-W2-SA-T05 | 1.2 | A | Compare front-end wizard spec against current UI behavior | product | Product/UX | 6 | [P1-W1-SB-T03] | Gap analysis between intended journey and real UI | Every required user checkpoint is marked implemented, partial, or missing | Spec-vs-UI review with file references |
| P1-W2-SA-T06 | 1.2 | A | Compare runtime docs against current CLI and Tauri behavior | product | Product/UX | 4 | [P1-W2-SA-T05] | Drift report for `CLAUDE.md`, launch docs, and Tauri docs | Contradictions are explicit and actionable | Drift checklist with command evidence |
| P1-W2-SB-T07 | 1.2 | B | Synthesize main failure themes from code, issues, and changelog | product | Product/PM | 6 | [P1-W1-SA-T01, P1-W2-SA-T06] | Single diagnosis memo naming the core product problem | Memo explains why users still see wrong visual outputs and weak control | Memo reviewed against live code paths |
| P1-W2-SB-T08 | 1.2 | B | Define the "GitHub URL only -> run Brandmint" acceptance story | product | Product/PM | 6 | [P1-W1-SB-T04, P1-W2-SB-T07] | Acceptance contract for clawable execution | A user prompt like "run this repo" maps to a deterministic SOP | Acceptance checklist with preconditions and outputs |
| P1-W3-SA-T09 | 1.3 | A | Define canonical `brand-config.yaml` source-of-truth contract | data | Backend/Data Eng | 6 | [P1-W2-SA-T05, P1-W2-SB-T07] | Contract covering provenance, approvals, and mutation rules | Downstream systems have one canonical approved config contract | Versioned schema contract doc |
| P1-W3-SB-T10 | 1.3 | B | Create initiative issue map and milestone proposal | product | Product/PM | 4 | [P1-W1-SA-T02, P1-W2-SB-T08, P1-W3-SA-T09] | Proposed issue breakdown and milestone layout | Work can be synchronized back to GitHub cleanly | Issue matrix with milestone and label plan |

### Phase 2 - Canonical Config and Approval Gates

| id | wave | swarm | title | area | owner_role | est_hours | dependencies | deliverable | acceptance | validation |
|---|---|---|---|---|---|---:|---|---|---|---|
| P2-W1-SA-T11 | 2.1 | A | Extend config schema with approval metadata | data | Backend Eng | 6 | [P1-W3-SA-T09] | Schema fields for approval state, approver, timestamp, and fingerprint | Approved configs serialize and validate cleanly | Schema tests and sample YAML |
| P2-W1-SA-T12 | 2.1 | A | Add extraction provenance and source-snippet mapping model | data | Backend Eng | 6 | [P2-W1-SA-T11] | Data model linking extracted fields to source text and confidence | Low-confidence fields retain traceable evidence | Unit tests for provenance serialization |
| P2-W1-SB-T13 | 2.1 | B | Persist `needs_review` fields into exported config draft | backend | Backend Eng | 4 | [P2-W1-SA-T12] | Export path that preserves review-required fields | Review-required fields survive round-trip export/import | Round-trip tests on YAML output |
| P2-W1-SB-T14 | 2.1 | B | Build explicit extraction review summary UI | frontend | Frontend Eng | 8 | [P2-W1-SA-T12] | Review surface showing confidence, source snippets, and edits | Users can see what needs confirmation before proceeding | UI interaction test and screenshot |
| P2-W2-SA-T15 | 2.2 | A | Persist explicit wizard approval action | frontend | Frontend Eng | 6 | [P2-W1-SB-T14] | Approve action that seals the current config draft | Launch cannot proceed until approval exists | UI state test with approval toggle |
| P2-W2-SA-T16 | 2.2 | A | Export approved config fingerprint and metadata | backend | Backend Eng | 4 | [P2-W2-SA-T15] | Approved config file with deterministic fingerprint block | Fingerprint changes only when approved content changes | YAML diff test across edits |
| P2-W2-SB-T17 | 2.2 | B | Block downstream launch until config is approved | backend | Backend Eng | 6 | [P2-W2-SA-T15] | Launch guard in CLI, bridge, and Tauri path | Unapproved configs fail with actionable guidance | CLI/bridge tests covering rejection path |
| P2-W2-SB-T18 | 2.2 | B | Add extracted-vs-approved diff view | frontend | Frontend Eng | 6 | [P2-W1-SB-T14, P2-W2-SA-T15] | UI diff for operator review before approval | Operators can see exactly what changed from raw extraction | UI test with edited fields |
| P2-W2-SB-T19 | 2.2 | B | Standardize approved-state errors across UI, bridge, and CLI | backend | Backend Eng | 4 | [P2-W2-SB-T17] | Consistent error contract for missing approval | All entry points report the same remediation message | API response snapshots and CLI output checks |
| P2-W2-SB-T20 | 2.2 | B | Add config gating and round-trip test suite | qa | QA Eng | 6 | [P2-W1-SA-T12, P2-W2-SA-T15, P2-W2-SA-T16, P2-W2-SB-T17] | Test coverage for approval gating and export behavior | Approval contract is covered in CI | Passing unit/integration test targets |

### Phase 3 - Human-in-the-Loop Execution Loop

| id | wave | swarm | title | area | owner_role | est_hours | dependencies | deliverable | acceptance | validation |
|---|---|---|---|---|---|---:|---|---|---|---|
| P3-W1-SA-T21 | 3.1 | A | Define wave-level checkpoint model | product | Product/PM | 6 | [P2-W2-SB-T17] | Approved checkpoint design for wave boundaries | The product has a clear rule for when execution pauses | State machine spec |
| P3-W1-SA-T22 | 3.1 | A | Implement executor pause-on-checkpoint behavior | backend | Backend Eng | 8 | [P3-W1-SA-T21] | Executor can stop and await operator approval | Execution pauses without losing progress | Integration test with paused run state |
| P3-W1-SB-T23 | 3.1 | B | Add CLI flags for approval mode and resume behavior | backend | Backend Eng | 4 | [P3-W1-SA-T21] | CLI controls for strict approval mode | Operators can opt into or default to approval gates | CLI smoke test |
| P3-W1-SB-T24 | 3.1 | B | Expose continue/revise endpoints in bridge and Tauri path | backend | Backend Eng | 6 | [P3-W1-SA-T22, P3-W1-SB-T23] | API contract for continue, revise, and resume | Desktop and bridge can drive the same workflow | Endpoint tests and invoke tests |
| P3-W2-SA-T25 | 3.2 | A | Build UI controls for approve, revise, and continue | frontend | Frontend Eng | 8 | [P3-W1-SA-T22, P3-W1-SB-T24] | HITL controls embedded in the run experience | Users can manage the loop without falling back to CLI | UI flow test |
| P3-W2-SA-T26 | 3.2 | A | Persist human decisions and rationale in state | data | Backend Eng | 6 | [P3-W1-SA-T22] | Decision journal in `.brandmint/state.json` or equivalent | Resume behavior retains operator intent | State snapshot test |
| P3-W2-SB-T27 | 3.2 | B | Emit structured awaiting-approval events and logs | backend | Backend Eng | 4 | [P3-W1-SA-T22] | Event model for waiting, approved, revised, resumed | UI can react without polling hacks | Event contract tests |
| P3-W2-SB-T28 | 3.2 | B | Support safe resume after approved-config edits | backend | Backend Eng | 8 | [P3-W1-SB-T24, P3-W2-SA-T26] | Resume logic that invalidates only necessary downstream work | Users can refine needs without full reruns | Resume regression tests |
| P3-W2-SB-T29 | 3.2 | B | Write operator guide for the HITL loop | product | Product Writer | 4 | [P3-W2-SA-T25, P3-W2-SB-T28] | SOP for approve/revise/continue workflow | A non-author operator can execute the loop reliably | Docs walkthrough review |
| P3-W2-SB-T30 | 3.2 | B | Add pause/resume/revise smoke tests | qa | QA Eng | 6 | [P3-W1-SB-T24, P3-W2-SA-T25, P3-W2-SB-T28] | Smoke test suite for HITL control flow | Checkpoint behavior is verified across entry points | Passing smoke logs |

### Phase 4 - Visual Domain Safety for App vs Product Brands

| id | wave | swarm | title | area | owner_role | est_hours | dependencies | deliverable | acceptance | validation |
|---|---|---|---|---|---|---:|---|---|---|---|
| P4-W1-SA-T31 | 4.1 | A | Inventory live product, `recraft`, and icon branches in active generation paths | backend | Backend Eng | 6 | [P1-W2-SB-T07] | Exact list of stale or misrouted active branches | No active prompt/model branch remains unknown | Audit doc with code references |
| P4-W1-SA-T32 | 4.1 | A | Define domain asset policy matrix for app, SaaS, B2B, and physical brands | product | Product/Design Eng | 6 | [P4-W1-SA-T31, P1-W3-SA-T09] | Matrix mapping domains to allowed asset families | App brands never select physical-product families by default | Policy matrix with examples |
| P4-W1-SB-T33 | 4.1 | B | Remove stale 5D/icon and obsolete `recraft` inventory surfaces from live metadata | backend | Backend Eng | 6 | [P4-W1-SA-T31] | Clean metadata surfaces that match real supported assets | Users no longer see deleted asset families in live inventory | Updated inventory outputs and tests |
| P4-W1-SB-T34 | 4.1 | B | Refactor wave planner asset family selection by domain | backend | Backend Eng | 8 | [P4-W1-SA-T32] | Planner that selects families by domain policy, not legacy defaults | App/SaaS plans exclude physical-product asset groups | Planner tests by domain fixture |
| P4-W2-SA-T35 | 4.2 | A | Suppress physical-product prompts for app-only and SaaS configs | backend | Backend Eng | 8 | [P4-W1-SB-T34] | Prompt generation guards for app-only brands | Prompt cookbook for app brands contains no physical product scenes | Cookbook regression test |
| P4-W2-SA-T36 | 4.2 | A | Add app screenshot/reference contract for app-domain brands | data | Backend Eng | 6 | [P4-W1-SA-T32] | Contract requiring UI screenshots or equivalent app refs where needed | App-domain visual prompts are anchored to app references | Contract validation tests |
| P4-W2-SB-T37 | 4.2 | B | Add app-native replacements for legacy product prompt families | backend | Backend Eng | 10 | [P4-W2-SA-T35, P4-W2-SA-T36] | Replacement prompts for interface, dashboard, flow, and system visuals | App-domain runs produce interface/system visuals instead of products | Rendered prompt snapshots |
| P4-W2-SB-T38 | 4.2 | B | Harden semantic routing for `APP-SCREENSHOT` and browser/app capture assets | backend | Backend Eng | 6 | [P4-W2-SA-T36] | Routing rules aligned to app-domain asset policy | App screenshot assets route predictably to the right scaffold path | Visual backend tests |
| P4-W3-SA-T39 | 4.3 | A | Tie NotebookLM/source image policy defaults to domain contract | data | Backend Eng | 6 | [P4-W1-SA-T32, P4-W2-SA-T36] | Domain-aware default for `manifest-only` vs `product-reference-only` | App brands stop ingesting unrelated product imagery by default | Source curator tests |
| P4-W3-SA-T40 | 4.3 | A | Add prompt and asset mismatch doctor report | backend | Backend Eng | 6 | [P4-W1-SB-T34, P4-W2-SB-T38, P4-W3-SA-T39] | Diagnostic command that flags domain/prompt contradictions | Operators can detect leakage before spending on a run | CLI doctor output snapshots |
| P4-W3-SB-T41 | 4.3 | B | Add app-brand regression fixture with no physical product outputs | qa | QA Eng | 6 | [P4-W2-SA-T35, P4-W2-SB-T37] | Fixture representing an app-only brand | Fixture fails if physical product prompts leak back in | Regression fixture in tests |
| P4-W3-SB-T42 | 4.3 | B | Add end-to-end prompt/runbook test from approved app config | qa | QA Eng | 8 | [P4-W2-SB-T37, P4-W3-SB-T41] | End-to-end test from approved config to prompt/runbook output | App-brand prompt/runbook output is domain-correct | Passing integration test and snapshot |

### Phase 5 - Tauri Runtime and Sidecar Hardening

| id | wave | swarm | title | area | owner_role | est_hours | dependencies | deliverable | acceptance | validation |
|---|---|---|---|---|---|---:|---|---|---|---|
| P5-W1-SA-T43 | 5.1 | A | Define deterministic sidecar singleton and port ownership policy | infra | DevOps | 6 | [P1-W1-SB-T03] | Startup contract for bridge ownership on `4191` | Desktop startup has one unambiguous ownership rule | Runtime policy doc |
| P5-W1-SA-T44 | 5.1 | A | Implement reuse-or-restart behavior when port `4191` is occupied | backend | Backend Eng | 8 | [P5-W1-SA-T43] | Runtime behavior that avoids silent address conflicts | App can recover or explain why it cannot start | Integration test for occupied port |
| P5-W1-SB-T45 | 5.1 | B | Add startup diagnostics panel and status surfacing in UI | frontend | Frontend Eng | 6 | [P5-W1-SA-T43] | Visible desktop diagnostics for sidecar, health, and env state | Operators can see startup failures without reading terminal logs | UI screenshot and interaction test |
| P5-W1-SB-T46 | 5.1 | B | Expose sidecar restart and recovery controls | frontend | Frontend Eng | 4 | [P5-W1-SB-T45] | Restart action for unhealthy sidecar conditions | Users can recover from sidecar faults in app | UI action test |
| P5-W2-SA-T47 | 5.2 | A | Create one-command smoke test for Tauri plus sidecar | qa | QA Eng | 6 | [P5-W1-SA-T44] | Repeatable smoke script for desktop startup | A clean startup can be verified by one command | Smoke script log with pass criteria |
| P5-W2-SA-T48 | 5.2 | A | Normalize bundle identifier and packaging defaults | infra | DevOps | 4 | [P1-W1-SB-T03] | Clean packaging config without known warnings | Build no longer emits known identifier ambiguity warning | Build log check |
| P5-W2-SB-T49 | 5.2 | B | Add startup environment bootstrap checks | infra | DevOps | 6 | [P1-W1-SB-T04] | Preflight checks for Python, Node, Rust, and env secrets | Missing prerequisites fail fast with actionable guidance | Preflight test cases |
| P5-W2-SB-T50 | 5.2 | B | Consolidate dev commands and remove duplicate bridge startup guidance | infra | DevOps | 4 | [P5-W2-SA-T47, P5-W2-SB-T49] | Simplified command surface for local desktop dev | Operators have one preferred startup path | Docs and Makefile checks |
| P5-W2-SB-T51 | 5.2 | B | Add integration test for Tauri invoke proxy paths | qa | QA Eng | 6 | [P5-W1-SA-T44, P5-W2-SA-T47] | Coverage for `get_state`, `load_intake`, `start_run`, and related commands | Tauri command bridge is covered by tests | Passing integration target |
| P5-W2-SB-T52 | 5.2 | B | Update release checklist for sidecar and local desktop behavior | product | Product/PM | 4 | [P5-W2-SA-T48, P5-W2-SB-T50, P5-W2-SB-T51] | Release checklist aligned to the real Tauri runtime | Maintainers can verify local and packaged behavior consistently | Checklist review against smoke script |

### Phase 6 - Clawable SOP and Operator Documentation

| id | wave | swarm | title | area | owner_role | est_hours | dependencies | deliverable | acceptance | validation |
|---|---|---|---|---|---|---:|---|---|---|---|
| P6-W1-SA-T53 | 6.1 | A | Write "GitHub URL -> running Brandmint" SOP | product | Product Writer | 8 | [P1-W2-SB-T08, P5-W2-SB-T49] | Operator SOP from repo URL to running app | An agent can follow the SOP without tribal knowledge | Docs walkthrough from clean checkout |
| P6-W1-SA-T54 | 6.1 | A | Write "no frontend or CLI knowledge required" operator narrative | product | Product Writer | 4 | [P6-W1-SA-T53, P5-W2-SB-T50] | User-facing narrative that abstracts internal tools | A non-developer can understand the supported path | Readability and walkthrough review |
| P6-W1-SB-T55 | 6.1 | B | Document canonical config lifecycle and approval gates | product | Product Writer | 6 | [P2-W2-SA-T16, P3-W2-SB-T29] | Documentation for extraction, review, approval, export, and launch | Approval gates are explicit and unavoidable in docs | Docs traceability review |
| P6-W1-SB-T56 | 6.1 | B | Document visual policy for app-domain vs product-domain brands | product | Product Writer | 6 | [P4-W1-SA-T32, P4-W3-SB-T42] | Domain-aware visual rules and examples | Operators know when screenshots vs product refs are required | Example review with fixtures |
| P6-W2-SA-T57 | 6.2 | A | Add minimal app-brand example config and sample Product MD | product | Product Writer | 6 | [P6-W1-SB-T55, P6-W1-SB-T56] | Example inputs for app-only brand runs | Example can be used in smoke and docs flows | Sample fixture validation |
| P6-W2-SA-T58 | 6.2 | A | Add troubleshooting guide for port conflicts, missing deps, and paused runs | product | Product Writer | 6 | [P5-W1-SA-T44, P5-W2-SB-T49, P6-W1-SA-T53] | Failure playbook for common operator issues | Operators can recover without code spelunking | Docs walkthrough on failure cases |
| P6-W2-SB-T59 | 6.2 | B | Add agent prompt recipe for "run this repo" style requests | product | Product Writer | 4 | [P6-W1-SA-T53, P6-W1-SA-T54] | Reusable prompt contract for agentic operators | Repo URL requests map cleanly to the SOP | Prompt recipe reviewed against actual steps |
| P6-W2-SB-T60 | 6.2 | B | Document backend-only/headless support or explicitly document non-support | product | Product Writer | 4 | [P5-W2-SB-T50, P6-W1-SA-T53] | Clear position on CLI-free/headless operation | No operator ambiguity about supported launch modes | Support matrix review |
| P6-W2-SB-T61 | 6.2 | B | Document issue hygiene policy for ignoring archived vision work | product | Product Writer | 4 | [P1-W1-SA-T02, P1-W3-SB-T10] | Project policy for current vs archived issue stacks | Operators know which issues matter for current work | Docs review with issue links |
| P6-W2-SB-T62 | 6.2 | B | Run full docs QA against real commands and paths | qa | QA Eng | 6 | [P6-W1-SA-T53, P6-W1-SA-T54, P6-W1-SB-T55, P6-W1-SB-T56, P6-W2-SA-T57, P6-W2-SA-T58, P6-W2-SB-T59, P6-W2-SB-T60, P6-W2-SB-T61] | Verified documentation set | Every documented command works or is clearly marked unsupported | Docs QA report |

### Phase 7 - GitHub Issue and Release Hygiene

| id | wave | swarm | title | area | owner_role | est_hours | dependencies | deliverable | acceptance | validation |
|---|---|---|---|---|---|---:|---|---|---|---|
| P7-W1-SA-T63 | 7.1 | A | Keep issue `#113` active as distribution hardening work | product | Product/PM | 2 | [P1-W3-SB-T10] | Updated issue status for Tauri artifact publishing | `#113` is explicitly tracked as active work | Issue comment/status review |
| P7-W1-SA-T64 | 7.1 | A | Decide defer status for issue `#66` | product | Product/PM | 2 | [P1-W3-SB-T10] | Clear decision on X automation timing | `#66` is either deferred or scheduled with rationale | Issue label/comment review |
| P7-W1-SB-T65 | 7.1 | B | Apply archive/defer strategy to `vision-upgrade` issue stack | product | Product/PM | 6 | [P1-W1-SA-T02, P1-W3-SB-T10] | Archived or relabeled vision backlog | Active backlog no longer looks like the product roadmap | Issue list diff before/after |
| P7-W1-SB-T66 | 7.1 | B | Create issues for config approvals, HITL loop, visual app policy, Tauri singleton, and docs | product | Product/PM | 6 | [P1-W3-SB-T10, P4-W1-SA-T32, P5-W1-SA-T43, P6-W1-SA-T53] | New issue set aligned to real initiative | Each major workstream has an issue owner and scope | Issue creation checklist |
| P7-W2-SA-T67 | 7.2 | A | Create clawable milestone and label taxonomy | product | Product/PM | 4 | [P7-W1-SA-T63, P7-W1-SA-T64, P7-W1-SB-T66] | Milestone and labels for this initiative | Work can be queried cleanly by milestone and label | GitHub query checks |
| P7-W2-SA-T68 | 7.2 | A | Update release checklist and PR templates to reference new SOPs | product | Product/PM | 4 | [P5-W2-SB-T52, P6-W1-SA-T53] | Release and PR templates aligned to clawable run path | Release process explicitly requires SOP/doc validation | Template diff review |
| P7-W2-SB-T69 | 7.2 | B | Post execution summary and risks back to active issues and PRs | product | Product/PM | 4 | [P7-W1-SA-T63, P7-W1-SA-T64, P7-W1-SB-T65, P7-W1-SB-T66, P7-W2-SA-T67, P7-W2-SA-T68] | GitHub comments linking plan to live work | Stakeholders can trace plan to execution | Comment audit |
| P7-W2-SB-T70 | 7.2 | B | Verify release artifact path against issue `#113` acceptance | infra | DevOps | 6 | [P5-W2-SA-T48, P7-W2-SA-T68] | Distro validation plan tied to release issue | `#113` acceptance is mapped to concrete checks | Workflow review and checklist evidence |

### Phase 8 - QA, Acceptance, and Rollout

| id | wave | swarm | title | area | owner_role | est_hours | dependencies | deliverable | acceptance | validation |
|---|---|---|---|---|---|---:|---|---|---|---|
| P8-W1-SA-T71 | 8.1 | A | Add unit tests for approval metadata and config gating | qa | QA Eng | 6 | [P2-W2-SB-T20] | Unit coverage for approved-config contract | Approval metadata failures are caught in CI | Passing test target |
| P8-W1-SA-T72 | 8.1 | A | Add unit tests for HITL pause and resume states | qa | QA Eng | 6 | [P3-W2-SB-T30] | Unit coverage for checkpoint transitions | Pause/resume logic is regression-safe | Passing test target |
| P8-W1-SB-T73 | 8.1 | B | Add regression tests for app-domain asset suppression and routing | qa | QA Eng | 6 | [P4-W3-SB-T42] | Regression suite for app-brand visual policy | App-brand runs cannot regress to physical-product outputs silently | Passing regression suite |
| P8-W1-SB-T74 | 8.1 | B | Smoke test clean Tauri startup with managed sidecar only | qa | QA Eng | 4 | [P5-W2-SA-T47, P5-W2-SB-T51] | Runtime smoke record for desktop startup | Tauri startup works without manual bridge interference | Startup smoke log |
| P8-W2-SA-T75 | 8.2 | A | Smoke test repo-URL bootstrap to first config export | qa | QA Eng | 6 | [P6-W1-SA-T53, P6-W2-SA-T57] | End-to-end SOP verification from clone to config export | A fresh operator can reach a valid approved config | Walkthrough report |
| P8-W2-SA-T76 | 8.2 | A | Smoke test approved config to paused wave execution | qa | QA Eng | 6 | [P3-W2-SB-T30, P6-W1-SB-T55] | Proof that approval gates actually pause execution | Run pauses at the documented checkpoint | Smoke log and state snapshot |
| P8-W2-SB-T77 | 8.2 | B | Smoke test revise approved config and resume downstream work | qa | QA Eng | 6 | [P3-W2-SB-T28, P6-W1-SB-T55] | Resume proof after config revision | Only affected downstream work is invalidated and rerun | Smoke log and diff |
| P8-W2-SB-T78 | 8.2 | B | Validate docs by following the SOP exactly from a clean checkout | qa | QA Eng | 6 | [P6-W2-SB-T62, P8-W2-SA-T75] | Black-box docs validation report | Docs match reality with no unstated tribal knowledge | Walkthrough checklist |
| P8-W2-SB-T79 | 8.2 | B | Prepare release readiness review and signoff packet | product | Product/PM | 4 | [P7-W2-SB-T70, P8-W1-SA-T71, P8-W1-SA-T72, P8-W1-SB-T73, P8-W1-SB-T74, P8-W2-SA-T75, P8-W2-SA-T76, P8-W2-SB-T77, P8-W2-SB-T78] | Final readiness packet for landing | A staff-level reviewer can approve or reject with evidence | Review packet with links to checks |
| P8-W2-SB-T80 | 8.2 | B | Run retro, update lessons, and sync final issue states | product | Product/PM | 4 | [P8-W2-SB-T79] | Closure notes and next-wave backlog | Initiative ends with lessons and clean GitHub state | Retro notes and issue state diff |

## Dependency Rationale

- Phase 1 establishes the truth: active problems, runtime evidence, and the correct product contract.
- Phase 2 must land before meaningful execution refactors, because the approved config contract is the foundation for any HITL system.
- Phase 3 depends on Phase 2 because checkpointing without a canonical approved config would just formalize ambiguity.
- Phase 4 depends on Phase 1 and 2 because domain-safe visual generation must key off the approved config and an explicit policy matrix.
- Phase 5 can run partly in parallel with Phase 4, but the sidecar and Tauri hardening should not block config and domain policy work.
- Phase 6 depends on the earlier phases so the SOP documents the real system, not an aspirational one.
- Phase 7 should trail Phase 1 and 6 closely so GitHub reflects the real roadmap and not the stale one.
- Phase 8 is explicit verification and rollout; nothing is "done" until these checks pass.

## Verification Strategy

- Unit tests:
  approval metadata, config roundtrip, launch gating, pause/resume state, domain asset suppression, screenshot routing.
- Integration tests:
  prompt cookbook generation from approved app-brand config, Tauri command bridge behavior, sidecar recovery.
- Smoke tests:
  Tauri startup with managed sidecar, repo-URL bootstrap to config export, approved config to paused run, revise-and-resume workflow.
- Build checks:
  `npm --prefix ui run build`, `cargo build`, targeted pytest suites, release workflow validation.
- Docs validation:
  Follow the new SOP from a clean checkout without relying on undocumented context.
- GitHub hygiene validation:
  confirm only relevant issues remain active for this initiative.

## GitHub Sync and Dispatch Strategy

- Keep `#113` active and map it to Phase 5 and Phase 7 packaging tasks.
- Treat `#66` as deferred unless the user explicitly prioritizes automation now.
- Archive or relabel the `vision-upgrade` stack as deferred roadmap work rather than active execution.
- Create a new milestone such as `clawable-run-path`.
- Create issues for:
  - approved config gating
  - HITL execution loop
  - app-domain visual policy
  - Tauri singleton and startup diagnostics
  - clawable SOP and docs
- Post concise phase completion comments back to the linked issues.
- Use one issue per major workstream, then reference task IDs inside issue bodies or checklists.

## Risks and Fallback Plan

- Dirty worktree risk:
  use an isolated worktree or branch before implementation so initiative changes do not collide with unrelated edits.
- Approval-gate regression risk:
  hide strict gating behind a feature flag if immediate compatibility is needed during rollout.
- Visual-policy overcorrection risk:
  keep explicit domain fixtures for app, SaaS, B2B, and physical-product brands so new suppression logic does not break legitimate product runs.
- Tauri runtime variability risk:
  harden and verify macOS first, then widen platform support only after singleton and packaging behavior are stable.
- Documentation overpromise risk:
  if true repo-URL-only automation is not yet fully scripted, state the exact prerequisites and failure cases explicitly rather than implying zero setup.

## Proposed Implementation Order

1. Phase 1
2. Phase 2
3. Phase 4
4. Phase 3
5. Phase 5
6. Phase 6
7. Phase 7
8. Phase 8

This ordering front-loads source-of-truth config and app-domain visual correctness before deeper workflow and release polish.
