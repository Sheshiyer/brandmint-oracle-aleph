# Brandmint Tauri v2 Desktop App — Conversion Plan

> **Generated:** 2026-03-02
> **Planning depth:** Deeply detailed (120+ tasks)
> **Delivery mode:** Prototype first
> **Team:** Solo (me + Claude)
> **Backend strategy:** Python sidecar (keep all Python logic as-is)
> **Target platform:** macOS only (Apple Silicon primary)
> **Output:** Markdown plan + GitHub Issues

---

## Discovery Summary

### Current Architecture
- **Python CLI** (`bm`) — 45 skills, 7 waves, Typer + Rich
- **React 19 UI** (`ui/`) — Vite 7, TypeScript 5.9, single monolithic `App.tsx` (~1400 lines)
- **Python HTTP bridge** (`scripts/ui_backend_bridge.py`) — stdlib `ThreadingHTTPServer` on port 4191, 15+ REST endpoints
- **Frontend ↔ Backend:** `fetch('/api/...')` calls proxied via Vite dev server

### Target Architecture
- **Tauri v2 desktop app** with embedded webview
- **Python sidecar** spawned by Tauri (replaces localhost HTTP bridge)
- **Tauri IPC commands** replace all `fetch('/api/...')` calls
- **Event system** for real-time log streaming (replaces polling)
- **Native features:** file dialogs, notifications, menu bar, auto-update

### Prototype-First Strategy
Phase 1 delivers a working desktop app immediately by:
1. Wrapping the existing React UI in a Tauri webview
2. Spawning the Python HTTP bridge as a sidecar
3. Keeping all `fetch()` calls working against `127.0.0.1:4191`

Then Phases 2-6 incrementally migrate to native Tauri patterns.

---

## Assumptions & Constraints

1. Python 3.11+ available via system install or bundled virtualenv
2. Rust toolchain installed via `rustup` (stable channel)
3. Node.js 18+ for frontend build
4. macOS 13+ (Ventura) minimum target
5. Apple Silicon (aarch64-apple-darwin) primary, Intel optional
6. No mobile targets in scope
7. The Python pipeline (`brandmint/`) remains untouched — sidecar only
8. The existing React UI is the conversion target (no rewrite)

---

## Phase Map

| Phase | Focus | Tasks | Est. Hours |
|-------|-------|------:|----------:|
| **1** | Tauri Shell & Sidecar Prototype | 28 | 48 |
| **2** | IPC Command Migration | 30 | 56 |
| **3** | Frontend Component Refactor | 28 | 52 |
| **4** | Native Features & UX | 18 | 32 |
| **5** | Distribution & Packaging | 12 | 24 |
| **6** | Testing & Quality | 10 | 20 |
| **Total** | | **126** | **232** |

---

## Phase 1: Tauri Shell & Sidecar Prototype

> **Objective:** Working desktop app that launches, shows the React UI, and runs the pipeline.
> **Exit criteria:** `cargo tauri dev` opens a window, Python sidecar starts, pipeline can be triggered.

### Wave 1.1 — Project Scaffolding (Swarm A: Infra)

| ID | Title | Area | Owner | Est | Deps | Deliverable | Acceptance | Validation |
|----|-------|------|-------|-----|------|-------------|------------|------------|
| P1-001 | Initialize Tauri v2 project in `src-tauri/` | infra | DevOps | 4h | — | `src-tauri/` directory with `Cargo.toml`, `tauri.conf.json`, `src/main.rs` | `cargo tauri dev` compiles without errors | `cargo build` exits 0 |
| P1-002 | Configure `tauri.conf.json` for React dev server | infra | DevOps | 2h | P1-001 | Dev server URL points to `http://localhost:4188` | Webview loads Vite dev server content | Screenshot shows React UI in Tauri window |
| P1-003 | Add `@tauri-apps/cli` and `@tauri-apps/api` to `ui/package.json` | frontend | Frontend Eng | 1h | P1-001 | Updated `package.json` with Tauri deps | `npm install` succeeds, `@tauri-apps/api` importable | `npm ls @tauri-apps/api` shows version |
| P1-004 | Create `ui/src-tauri/` symlink or move Tauri into `ui/` | infra | DevOps | 2h | P1-001 | Decide monorepo layout: `src-tauri/` at root or inside `ui/` | `npm run tauri dev` works from correct directory | Dev server + Tauri window both launch |
| P1-005 | Configure Vite build output for Tauri (`distDir`) | frontend | Frontend Eng | 1h | P1-002 | `tauri.conf.json` `build.distDir` points to Vite's `dist/` | `cargo tauri build` bundles the frontend | Built `.app` contains frontend assets |
| P1-006 | Set up `capabilities/default.json` with initial permissions | infra | DevOps | 2h | P1-001 | Permissions for shell:execute, shell:spawn, fs:read, fs:write, notification | Sidecar can be spawned, files can be read | `cargo tauri dev` shows no permission errors |
| P1-007 | Create `.cargo/config.toml` with Apple Silicon target | infra | DevOps | 1h | P1-001 | `[build] target = "aarch64-apple-darwin"` | Compiles for ARM64 | `file` command on binary shows arm64 |
| P1-008 | Add Tauri plugins: `shell`, `fs`, `notification`, `dialog`, `process` | infra | DevOps | 2h | P1-001 | Cargo.toml includes all required plugin crates | All plugins compile | `cargo build` with all plugins exits 0 |

### Wave 1.2 — Python Sidecar Setup (Swarm B: Backend)

| ID | Title | Area | Owner | Est | Deps | Deliverable | Acceptance | Validation |
|----|-------|------|-------|-----|------|-------------|------------|------------|
| P1-009 | Create sidecar wrapper script `binaries/brandmint-bridge` | backend | Backend Eng | 2h | — | Shell script that launches `python3 scripts/ui_backend_bridge.py` | Script starts the HTTP bridge on port 4191 | `curl localhost:4191/api/health` returns 200 |
| P1-010 | Add platform-specific sidecar binary name (`-aarch64-apple-darwin`) | infra | DevOps | 1h | P1-009 | `binaries/brandmint-bridge-aarch64-apple-darwin` | Tauri recognizes the sidecar binary | `cargo tauri dev` logs show sidecar found |
| P1-011 | Register sidecar in `tauri.conf.json` `bundle.externalBin` | infra | DevOps | 1h | P1-009, P1-010 | `"externalBin": ["binaries/brandmint-bridge"]` in config | Tauri bundles the sidecar | Built app contains sidecar binary |
| P1-012 | Write Rust `spawn_sidecar()` function in `src/sidecar.rs` | backend | Backend Eng | 4h | P1-008, P1-011 | Rust module that spawns Python bridge, captures stdout/stderr | Sidecar starts on app launch, logs visible | Console shows bridge startup messages |
| P1-013 | Implement sidecar health check loop (retry on port not ready) | backend | Backend Eng | 2h | P1-012 | Rust function that polls `localhost:4191/api/health` until ready | App waits for bridge before showing UI | Splash/loading state shown while waiting |
| P1-014 | Implement sidecar shutdown on app close | backend | Backend Eng | 2h | P1-012 | `on_window_close` handler that sends SIGTERM to sidecar | Sidecar process terminates when app closes | `ps aux | grep ui_backend_bridge` shows no orphans |
| P1-015 | Handle sidecar crash/restart recovery | backend | Backend Eng | 4h | P1-012, P1-013 | Watcher that detects sidecar death and restarts | If bridge crashes, app auto-restarts it | Kill sidecar manually → app recovers |
| P1-016 | Configure sidecar environment variables (FAL_KEY, OPENROUTER_API_KEY, etc.) | backend | Backend Eng | 2h | P1-012 | Env vars from `.env` file passed to sidecar process | Sidecar has access to all API keys | Pipeline can call FAL API via sidecar |
| P1-017 | Create Python venv bundling strategy for sidecar | infra | DevOps | 4h | P1-009 | Script or Makefile target that creates portable venv with `brandmint` installed | Sidecar uses bundled Python env, not system Python | `which python3` inside sidecar points to bundled venv |

### Wave 1.3 — Dev Workflow & Hot Reload (Swarm A: Infra)

| ID | Title | Area | Owner | Est | Deps | Deliverable | Acceptance | Validation |
|----|-------|------|-------|-----|------|-------------|------------|------------|
| P1-018 | Create `npm run tauri:dev` script combining Vite + Tauri | infra | DevOps | 1h | P1-004 | Package.json script: `"tauri:dev": "tauri dev"` | Single command starts full dev stack | `npm run tauri:dev` opens window with hot reload |
| P1-019 | Configure Tauri `beforeDevCommand` and `beforeBuildCommand` | infra | DevOps | 1h | P1-018 | `tauri.conf.json` runs `npm run dev` before dev, `npm run build` before build | Automatic frontend build on `cargo tauri build` | Build produces working app |
| P1-020 | Set up Rust `#[cfg(debug_assertions)]` for dev vs prod paths | backend | Backend Eng | 1h | P1-012 | Dev mode uses direct `python3` call, prod uses bundled sidecar | Dev: spawns local Python; Prod: spawns bundled binary | Both modes work correctly |
| P1-021 | Add `Makefile` or `justfile` with dev/build/clean targets | infra | DevOps | 2h | P1-018 | `make dev`, `make build`, `make clean`, `make sidecar` | All targets work | `make dev` starts full stack |

### Wave 1.4 — Prototype UI Polish (Swarm C: Frontend)

| ID | Title | Area | Owner | Est | Deps | Deliverable | Acceptance | Validation |
|----|-------|------|-------|-----|------|-------------|------------|------------|
| P1-022 | Add Tauri-aware loading/splash screen | frontend | Frontend Eng | 2h | P1-013 | React component shown while sidecar initializes | Users see "Starting Brandmint..." instead of blank screen | Loading screen visible for 1-3s on startup |
| P1-023 | Detect Tauri environment in React (`window.__TAURI__`) | frontend | Frontend Eng | 1h | P1-003 | Utility function `isTauri()` for conditional behavior | Frontend knows if running in Tauri vs browser | `isTauri()` returns true in app, false in browser |
| P1-024 | Remove port-guard logic from Tauri mode | frontend | Frontend Eng | 1h | P1-023 | Skip `localhost_port_guard.py` when running inside Tauri | No port conflict warnings in Tauri mode | App starts cleanly without port checks |
| P1-025 | Set window title to "Brandmint" with version | frontend | Frontend Eng | 1h | P1-002 | `tauri.conf.json` title: "Brandmint v4.3.1" | Window title shows correct name and version | Title bar reads "Brandmint v4.3.1" |
| P1-026 | Configure window dimensions (1280x800 default, resizable) | frontend | Frontend Eng | 1h | P1-002 | `tauri.conf.json` window width/height/resizable settings | Window opens at reasonable size | Window is 1280x800 and resizable |
| P1-027 | Add app icon (use existing brandmint branding) | frontend | Frontend Eng | 2h | P1-001 | `icons/` directory with icon.png, icon.icns for macOS | App shows branded icon in dock/titlebar | Icon visible in macOS dock |
| P1-028 | Verify full pipeline run through Tauri prototype | qa | QA | 2h | P1-022 | Run `bm launch` via UI, verify all waves complete | Pipeline works end-to-end inside Tauri app | All wave outputs generated successfully |

---

## Phase 2: IPC Command Migration

> **Objective:** Replace all `fetch('/api/...')` calls with native Tauri `invoke()` commands.
> **Exit criteria:** Python HTTP bridge no longer needed. All API calls go through Rust IPC.

### Wave 2.1 — Core IPC Infrastructure (Swarm A: Backend)

| ID | Title | Area | Owner | Est | Deps | Deliverable | Acceptance | Validation |
|----|-------|------|-------|-----|------|-------------|------------|------------|
| P2-001 | Design Tauri command naming convention | product | Frontend Eng | 1h | P1-028 | Document: snake_case Rust commands, camelCase JS invocations | Team agrees on naming pattern | Naming doc in docs/plans/ |
| P2-002 | Create `src/commands/mod.rs` module structure | backend | Backend Eng | 1h | P1-001 | Rust module: `commands/health.rs`, `commands/state.rs`, etc. | `mod.rs` compiles, all submodules importable | `cargo build` exits 0 |
| P2-003 | Create shared Rust `AppState` struct for sidecar handle | backend | Backend Eng | 2h | P1-012 | `tauri::State<AppState>` with sidecar process handle + runtime config | State accessible from all commands | Command can read sidecar PID from state |
| P2-004 | Create Rust HTTP client for sidecar communication | backend | Backend Eng | 2h | P2-003 | `reqwest` or `ureq` client that calls `127.0.0.1:4191/api/*` | Rust commands can proxy to Python sidecar | Health check returns 200 via Rust |
| P2-005 | Create TypeScript `api.ts` module with typed `invoke()` wrappers | frontend | Frontend Eng | 2h | P1-003 | `ui/src/api.ts` with typed functions for each command | All API calls go through typed wrappers | TypeScript compiles with no type errors |
| P2-006 | Create `api-bridge.ts` abstraction layer (fetch vs invoke) | frontend | Frontend Eng | 2h | P2-005, P1-023 | Module that auto-selects `fetch()` or `invoke()` based on `isTauri()` | Same code works in browser and Tauri | Both modes functional |

### Wave 2.2 — Health, State & Settings Commands (Swarm B: Backend + Frontend)

| ID | Title | Area | Owner | Est | Deps | Deliverable | Acceptance | Validation |
|----|-------|------|-------|-----|------|-------------|------------|------------|
| P2-007 | Implement `get_health` Tauri command | backend | Backend Eng | 1h | P2-004 | `#[tauri::command] fn get_health()` → proxies to sidecar `/api/health` | Returns health status JSON | `invoke('get_health')` returns `{status: "ok"}` |
| P2-008 | Implement `get_state` Tauri command | backend | Backend Eng | 2h | P2-004 | `#[tauri::command] fn get_state()` → proxies to sidecar `/api/state` | Returns runtime state (run_state, runner, pid) | Frontend shows correct pipeline state |
| P2-009 | Implement `get_settings` Tauri command | backend | Backend Eng | 2h | P2-004 | `#[tauri::command] fn get_settings()` → proxies to sidecar `/api/settings` | Returns integration settings with masked keys | Settings panel loads correctly |
| P2-010 | Implement `update_settings` Tauri command | backend | Backend Eng | 2h | P2-004 | `#[tauri::command] fn update_settings(payload: Value)` → POST to sidecar | Settings persist across restarts | Save settings, restart, settings still there |
| P2-011 | Migrate `loadIntegrationSettings()` to use `invoke` | frontend | Frontend Eng | 1h | P2-009, P2-006 | Replace `fetch("/api/settings")` with `invoke("get_settings")` | Settings load on app start | Settings panel shows correct values |
| P2-012 | Migrate `saveIntegrationSettings()` to use `invoke` | frontend | Frontend Eng | 1h | P2-010, P2-006 | Replace `fetch("/api/settings", {method: "POST"})` with `invoke("update_settings")` | Settings save correctly | Changed settings persist after restart |

### Wave 2.3 — Pipeline Control Commands (Swarm C: Backend + Frontend)

| ID | Title | Area | Owner | Est | Deps | Deliverable | Acceptance | Validation |
|----|-------|------|-------|-----|------|-------------|------------|------------|
| P2-013 | Implement `start_run` Tauri command | backend | Backend Eng | 4h | P2-004 | `#[tauri::command] fn start_run(runner, scenario, waves, config_path, ...)` → POST `/api/run/start` | Pipeline starts via Tauri command | Run state transitions to "running" |
| P2-014 | Implement `abort_run` Tauri command | backend | Backend Eng | 2h | P2-004 | `#[tauri::command] fn abort_run()` → POST `/api/run/abort` | Running pipeline is killed | Run state transitions to "aborted" |
| P2-015 | Implement `retry_run` Tauri command | backend | Backend Eng | 2h | P2-004 | `#[tauri::command] fn retry_run()` → POST `/api/run/retry` | Failed pipeline retries with port cleanup | Run state transitions to "retrying" then "running" |
| P2-016 | Implement `start_publish` Tauri command | backend | Backend Eng | 2h | P2-004 | `#[tauri::command] fn start_publish(stage)` → POST `/api/publish/start` | Publishing stage runs | Publish state shows completion |
| P2-017 | Implement `load_intake` Tauri command | backend | Backend Eng | 2h | P2-004 | `#[tauri::command] fn load_intake(brand_folder)` → POST `/api/intake/load` | Brand folder loads product.md + config | Extraction data appears in UI |
| P2-018 | Migrate `postJson()` helper to use `invoke()` in Tauri mode | frontend | Frontend Eng | 2h | P2-013, P2-006 | `postJson()` routes through `invoke()` when in Tauri | All POST actions work via IPC | Start/abort/retry work in Tauri mode |
| P2-019 | Migrate run control buttons to use new commands | frontend | Frontend Eng | 2h | P2-018 | Start, Abort, Retry buttons use `invoke()` | All pipeline control works | Click Start → pipeline runs |

### Wave 2.4 — Data Query Commands (Swarm D: Backend + Frontend)

| ID | Title | Area | Owner | Est | Deps | Deliverable | Acceptance | Validation |
|----|-------|------|-------|-----|------|-------------|------------|------------|
| P2-020 | Implement `get_runners` Tauri command | backend | Backend Eng | 1h | P2-004 | `#[tauri::command] fn get_runners()` → GET `/api/runners` | Returns list of available runners | Runner dropdown populates correctly |
| P2-021 | Implement `get_artifacts` Tauri command | backend | Backend Eng | 2h | P2-004 | `#[tauri::command] fn get_artifacts(limit)` → GET `/api/artifacts` | Returns artifact file list with metadata | Artifacts panel shows files |
| P2-022 | Implement `get_references` Tauri command | backend | Backend Eng | 2h | P2-004 | `#[tauri::command] fn get_references(limit)` → GET `/api/references` | Returns reference image catalog | Reference library renders images |
| P2-023 | Implement `get_reference_image` Tauri command (binary response) | backend | Backend Eng | 4h | P2-004 | `#[tauri::command] fn get_reference_image(path)` → serves image file bytes | Returns image binary data for display | Reference images render in UI |
| P2-024 | Migrate artifact loading to `invoke("get_artifacts")` | frontend | Frontend Eng | 1h | P2-021, P2-006 | Replace `fetch("/api/artifacts")` | Artifacts load via IPC | Artifact panel works |
| P2-025 | Migrate reference loading to `invoke("get_references")` | frontend | Frontend Eng | 2h | P2-022, P2-006 | Replace `fetch("/api/references")` | References load via IPC | Reference library works |
| P2-026 | Migrate runner loading to `invoke("get_runners")` | frontend | Frontend Eng | 1h | P2-020, P2-006 | Replace `fetch("/api/runners")` | Runner list loads via IPC | Runner dropdown works |
| P2-027 | Handle reference image URLs in Tauri mode (asset protocol or base64) | frontend | Frontend Eng | 4h | P2-023 | Images served via `tauri://localhost` asset protocol or base64 data URIs | Reference images display correctly | All 160 reference images render |

### Wave 2.5 — Log Streaming via Events (Swarm E: Backend + Frontend)

| ID | Title | Area | Owner | Est | Deps | Deliverable | Acceptance | Validation |
|----|-------|------|-------|-----|------|-------------|------------|------------|
| P2-028 | Implement Tauri event emitter for sidecar stdout | backend | Backend Eng | 4h | P1-012 | Sidecar stdout/stderr → `app.emit("sidecar-log", payload)` | Log events fire in real-time | Frontend receives log events |
| P2-029 | Implement `pipeline-state-changed` event | backend | Backend Eng | 2h | P2-028 | State changes (idle→running→complete) emit events | Frontend updates without polling | State transitions are instant |
| P2-030 | Replace polling-based log fetcher with event listener | frontend | Frontend Eng | 2h | P2-028 | `listen("sidecar-log", handler)` replaces `setInterval` + `fetch("/api/logs")` | Logs appear in real-time without polling | Log panel updates instantly |
| P2-031 | Replace polling-based state check with event listener | frontend | Frontend Eng | 2h | P2-029 | `listen("pipeline-state-changed", handler)` replaces state polling | State updates are event-driven | No more polling interval |
| P2-032 | Remove HTTP bridge dependency from production path | backend | Backend Eng | 2h | P2-030, P2-031 | All commands go through IPC; bridge only used as sidecar internal | HTTP bridge no longer directly called by frontend | No `fetch('/api/...')` calls in production code |

---

## Phase 3: Frontend Component Refactor

> **Objective:** Split monolithic `App.tsx` into proper components, add state management, improve UX.
> **Exit criteria:** Each page/view is a separate component, state is managed centrally, navigation works.

### Wave 3.1 — State Management & Project Structure (Swarm A: Frontend)

| ID | Title | Area | Owner | Est | Deps | Deliverable | Acceptance | Validation |
|----|-------|------|-------|-----|------|-------------|------------|------------|
| P3-001 | Install and configure Zustand for state management | frontend | Frontend Eng | 2h | P2-032 | `npm install zustand`, create `ui/src/stores/` directory | Zustand importable and configured | `import { useStore } from './stores'` works |
| P3-002 | Create `pipelineStore` (run state, runner, logs) | frontend | Frontend Eng | 2h | P3-001 | `stores/pipelineStore.ts` with typed state + actions | Pipeline state managed by store | Components read state from store |
| P3-003 | Create `settingsStore` (integration settings, API keys) | frontend | Frontend Eng | 2h | P3-001 | `stores/settingsStore.ts` | Settings state managed by store | Settings page reads/writes to store |
| P3-004 | Create `projectStore` (brand folder, config, extraction) | frontend | Frontend Eng | 2h | P3-001 | `stores/projectStore.ts` | Project state managed by store | Wizard reads project data from store |
| P3-005 | Create `referenceStore` (references, selected refs) | frontend | Frontend Eng | 2h | P3-001 | `stores/referenceStore.ts` | Reference state managed by store | Reference library uses store |
| P3-006 | Create `artifactStore` (artifacts, groups) | frontend | Frontend Eng | 1h | P3-001 | `stores/artifactStore.ts` | Artifact state managed by store | Artifacts panel uses store |
| P3-007 | Migrate all `useState` from App.tsx to stores | frontend | Frontend Eng | 4h | P3-002 through P3-006 | All ~40 `useState` calls replaced with store selectors | App.tsx has zero local state for shared data | TypeScript compiles, app functional |
| P3-008 | Create `ui/src/types/` directory with shared type definitions | frontend | Frontend Eng | 2h | — | `types/pipeline.ts`, `types/settings.ts`, `types/reference.ts`, etc. | All types extracted from App.tsx into dedicated files | Zero type definitions in App.tsx |

### Wave 3.2 — Component Decomposition (Swarm B: Frontend)

| ID | Title | Area | Owner | Est | Deps | Deliverable | Acceptance | Validation |
|----|-------|------|-------|-----|------|-------------|------------|------------|
| P3-009 | Create `components/Layout/` — Shell, Sidebar, Header | frontend | Frontend Eng | 4h | P3-007 | Layout components with navigation sidebar | App has consistent layout chrome | Navigation visible on all pages |
| P3-010 | Extract `components/Pipeline/PipelineControl.tsx` | frontend | Frontend Eng | 2h | P3-002 | Start/Abort/Retry buttons + runner selector | Pipeline control is self-contained component | Buttons work independently |
| P3-011 | Extract `components/Pipeline/LogViewer.tsx` | frontend | Frontend Eng | 2h | P3-002 | Scrollable log viewer with level filtering | Logs display with auto-scroll | Log viewer works standalone |
| P3-012 | Extract `components/Pipeline/StateIndicator.tsx` | frontend | Frontend Eng | 1h | P3-002 | Status badge showing idle/running/retrying/aborted | State indicator updates in real-time | Correct color for each state |
| P3-013 | Extract `components/Wizard/IntakeStep.tsx` | frontend | Frontend Eng | 2h | P3-004 | Brand folder selection + product.md paste area | Intake step works as wizard page | Brand folder loads correctly |
| P3-014 | Extract `components/Wizard/ExtractionStep.tsx` | frontend | Frontend Eng | 2h | P3-004 | AI extraction display + confirm/edit flow | Extraction step works as wizard page | Extracted fields editable |
| P3-015 | Extract `components/Wizard/ConfigStep.tsx` | frontend | Frontend Eng | 2h | P3-004 | Config draft editor (brand, audience, positioning, visual) | Config step works as wizard page | All fields editable |
| P3-016 | Extract `components/Wizard/ExportStep.tsx` | frontend | Frontend Eng | 2h | P3-004 | YAML export + download | Export step works as wizard page | YAML generates correctly |
| P3-017 | Extract `components/References/ReferenceLibrary.tsx` | frontend | Frontend Eng | 4h | P3-005 | Grid view of reference images with search/filter/tags | Reference library is self-contained | Search, filter, selection all work |
| P3-018 | Extract `components/References/ReferenceCuration.tsx` | frontend | Frontend Eng | 2h | P3-005 | Reference curation tools (tag, remove, prioritize) | Curation tools work independently | Tags can be added/removed |
| P3-019 | Extract `components/Artifacts/ArtifactBrowser.tsx` | frontend | Frontend Eng | 2h | P3-006 | File browser for outputs/deliverables/state | Artifact browser is self-contained | Files grouped by type |
| P3-020 | Extract `components/Settings/SettingsPanel.tsx` | frontend | Frontend Eng | 2h | P3-003 | Provider settings (OpenRouter, NBrain, API keys) | Settings panel works standalone | Settings save and load correctly |
| P3-021 | Extract `components/Taskmaster/TaskmasterViewer.tsx` | frontend | Frontend Eng | 2h | — | Phase/sprint/task tree viewer | Taskmaster plan renders correctly | All phases/tasks visible |
| P3-022 | Extract `components/Publishing/PublishPanel.tsx` | frontend | Frontend Eng | 2h | P3-002 | NotebookLM, Decks, Reports, Diagrams, Video publish controls | Publish actions work | Each publish stage triggerable |

### Wave 3.3 — Navigation & Routing (Swarm C: Frontend)

| ID | Title | Area | Owner | Est | Deps | Deliverable | Acceptance | Validation |
|----|-------|------|-------|-----|------|-------------|------------|------------|
| P3-023 | Install React Router v7 (or keep in-memory nav) | frontend | Frontend Eng | 1h | P3-009 | Router configured for Tauri (hash-based routing) | Navigation between pages works | URL changes don't break Tauri |
| P3-024 | Create route definitions for all PageKind values | frontend | Frontend Eng | 2h | P3-023 | Routes for: journey, intake, extraction, wizard, export, launch, activity, triage, settings, reference-curation, reference-library, fal-dry-run, runner-workbench, runner-matrix, artifacts, handoff, publish-notebooklm, wiki-handoff, astro-build | All 18 pages navigable | Each page renders correct component |
| P3-025 | Migrate page selection from `selectedPageId` state to routes | frontend | Frontend Eng | 2h | P3-024 | Remove `setSelectedPageId`, use router navigation | Page changes use router | Back/forward navigation works |
| P3-026 | Add keyboard navigation (arrow keys, Cmd+K command palette) | frontend | Frontend Eng | 2h | P3-025 | Keyboard shortcuts for page navigation | Arrow keys navigate between pages | Cmd+K opens command palette |

### Wave 3.4 — UI Component Library (Swarm D: Frontend)

| ID | Title | Area | Owner | Est | Deps | Deliverable | Acceptance | Validation |
|----|-------|------|-------|-----|------|-------------|------------|------------|
| P3-027 | Create shared `components/ui/Button.tsx` | frontend | Frontend Eng | 1h | — | Reusable button component with variants (primary, danger, ghost) | All buttons use shared component | Visual consistency across app |
| P3-028 | Create shared `components/ui/Card.tsx` | frontend | Frontend Eng | 1h | — | Card container with header, body, footer slots | Cards used throughout app | Consistent card styling |
| P3-029 | Create shared `components/ui/Badge.tsx` | frontend | Frontend Eng | 1h | — | Status badges (idle, running, complete, error) | Badges used for state indicators | Correct colors per state |
| P3-030 | Create shared `components/ui/Input.tsx` and `Select.tsx` | frontend | Frontend Eng | 1h | — | Form components with labels and validation | Forms use shared components | Consistent form styling |
| P3-031 | Create `components/ui/Toast.tsx` notification system | frontend | Frontend Eng | 2h | — | Toast notifications for success/error/warning | Toasts appear on actions | Toasts auto-dismiss after 3s |
| P3-032 | Apply consistent dark theme CSS (glassmorphism style) | frontend | Frontend Eng | 4h | P3-027 through P3-031 | Unified dark theme matching existing `globals.css` | All components follow dark theme | No unstyled components |
| P3-033 | Create responsive layout breakpoints | frontend | Frontend Eng | 2h | P3-009 | CSS breakpoints for sidebar collapse, panel reflow | App looks good at 1024px-2560px | No layout breaks at any size |
| P3-034 | Add loading skeletons for async data | frontend | Frontend Eng | 2h | P3-027 | Skeleton components for references, artifacts, settings | Loading states show skeletons | No flash of empty content |
| P3-035 | Migrate inline styles from App.tsx to CSS modules | frontend | Frontend Eng | 4h | P3-032 | All inline `style={{}}` replaced with CSS classes | Zero inline styles in components | CSS modules used consistently |
| P3-036 | Clean up App.tsx — should be <50 lines (just router + providers) | frontend | Frontend Eng | 2h | P3-007 through P3-035 | App.tsx contains only router setup + store providers | App.tsx is minimal shell | Line count under 50 |

---

## Phase 4: Native Features & UX

> **Objective:** Leverage Tauri's native APIs for desktop-quality UX.
> **Exit criteria:** File dialogs, notifications, menu bar, and system tray all functional.

### Wave 4.1 — Native File Operations (Swarm A: Frontend + Backend)

| ID | Title | Area | Owner | Est | Deps | Deliverable | Acceptance | Validation |
|----|-------|------|-------|-----|------|-------------|------------|------------|
| P4-001 | Implement native folder picker for brand directory | frontend | Frontend Eng | 2h | P1-008 | `@tauri-apps/plugin-dialog` `open({ directory: true })` | macOS native folder picker opens | Selected folder path returned to app |
| P4-002 | Implement native file picker for brand-config.yaml | frontend | Frontend Eng | 1h | P4-001 | File picker filtered to `.yaml` files | User picks config file natively | Config path set in app |
| P4-003 | Implement native file picker for product.md import | frontend | Frontend Eng | 1h | P4-001 | File picker filtered to `.md` files | User picks product.md natively | File content loaded into app |
| P4-004 | Read brand-config.yaml via Tauri FS plugin (bypass sidecar for reads) | backend | Backend Eng | 2h | P1-008 | `#[tauri::command] fn read_brand_config(path)` using `std::fs` | Config parsed directly in Rust (fast) | Config loads in <10ms |
| P4-005 | Implement drag-and-drop for brand folder | frontend | Frontend Eng | 2h | P4-001 | Drop zone accepts folder path via Tauri drag event | Drag folder onto app → loads brand | Drop indicator visible during drag |
| P4-006 | Implement "Open in Finder" for output files | frontend | Frontend Eng | 1h | P1-008 | Button that calls `shell.open(path)` to reveal in Finder | Click → Finder opens to file location | Finder shows correct folder |

### Wave 4.2 — Native Notifications (Swarm B: Backend)

| ID | Title | Area | Owner | Est | Deps | Deliverable | Acceptance | Validation |
|----|-------|------|-------|-----|------|-------------|------------|------------|
| P4-007 | Replace `osascript` notifications with Tauri notification plugin | backend | Backend Eng | 2h | P1-008 | `@tauri-apps/plugin-notification` for pipeline completion | macOS notification appears on pipeline complete | Notification shows in Notification Center |
| P4-008 | Add notification for sidecar crash/recovery | backend | Backend Eng | 1h | P4-007 | Notification when sidecar dies and restarts | User alerted if sidecar crashes | Notification visible |
| P4-009 | Add notification for publish stage completion | backend | Backend Eng | 1h | P4-007 | Notification when NotebookLM/decks/reports/etc. complete | User notified of deliverable ready | Click notification → opens deliverable |

### Wave 4.3 — Menu Bar & System Tray (Swarm C: Frontend + Backend)

| ID | Title | Area | Owner | Est | Deps | Deliverable | Acceptance | Validation |
|----|-------|------|-------|-----|------|-------------|------------|------------|
| P4-010 | Create macOS menu bar with File, Edit, View, Pipeline menus | backend | Backend Eng | 4h | P1-001 | Rust menu configuration in `setup()` | Menu bar visible with correct items | All menu items clickable |
| P4-011 | Add "Open Brand Folder..." menu item (Cmd+O) | backend | Backend Eng | 1h | P4-010, P4-001 | Menu item triggers folder picker | Cmd+O opens folder picker | Shortcut works globally |
| P4-012 | Add "Start Pipeline" menu item (Cmd+R) | backend | Backend Eng | 1h | P4-010, P2-013 | Menu item triggers pipeline start | Cmd+R starts pipeline | Shortcut disabled when already running |
| P4-013 | Add system tray icon with pipeline status | backend | Backend Eng | 4h | P1-001 | Tray icon changes color based on state (green=idle, yellow=running, red=error) | Tray icon visible in macOS menu bar | Icon updates with state changes |
| P4-014 | Add tray context menu (Show Window, Start Pipeline, Quit) | backend | Backend Eng | 2h | P4-013 | Right-click tray icon shows menu | All tray menu items work | "Show Window" brings app to front |

### Wave 4.4 — Window Management (Swarm D: Frontend)

| ID | Title | Area | Owner | Est | Deps | Deliverable | Acceptance | Validation |
|----|-------|------|-------|-----|------|-------------|------------|------------|
| P4-015 | Remember window position and size across sessions | backend | Backend Eng | 2h | P1-001 | Window state saved to `~/.brandmint/window-state.json` | Window reopens at last position/size | Close and reopen → same position |
| P4-016 | Add "Always on Top" toggle (View menu) | backend | Backend Eng | 1h | P4-010 | Window stays above other windows when toggled | Toggle works via menu | Window stays on top |
| P4-017 | Handle macOS close behavior (hide to dock vs quit) | backend | Backend Eng | 2h | P4-013 | Cmd+W hides window, Cmd+Q quits app + sidecar | Close button hides, quit terminates | Sidecar survives close, dies on quit |
| P4-018 | Add deep link handler (`brandmint://open?config=...`) | backend | Backend Eng | 2h | P1-001 | Custom URL scheme opens app with pre-loaded config | `brandmint://open?config=/path/to/config.yaml` works | Click deep link → app opens with config |

---

## Phase 5: Distribution & Packaging

> **Objective:** Package the app for macOS distribution with auto-updates.
> **Exit criteria:** `.dmg` installer works, auto-update pulls new versions.

### Wave 5.1 — macOS Bundle (Swarm A: Infra)

| ID | Title | Area | Owner | Est | Deps | Deliverable | Acceptance | Validation |
|----|-------|------|-------|-----|------|-------------|------------|------------|
| P5-001 | Configure `tauri.conf.json` bundle identifier (`com.brandmint.desktop`) | infra | DevOps | 1h | P1-001 | Bundle ID, category, copyright in config | Bundle metadata correct | `mdls Brandmint.app` shows correct metadata |
| P5-002 | Generate macOS icon set (icon.icns from brandmint logo) | infra | DevOps | 2h | P1-027 | `icons/icon.icns` + all required sizes (16x16 to 1024x1024) | Icon renders at all sizes | Finder, Dock, Spotlight all show icon |
| P5-003 | Build `.app` bundle with `cargo tauri build` | infra | DevOps | 2h | P5-001, P5-002 | `target/release/bundle/macos/Brandmint.app` | App bundle launches correctly | Double-click `.app` → app starts |
| P5-004 | Build `.dmg` installer | infra | DevOps | 2h | P5-003 | `target/release/bundle/dmg/Brandmint_4.3.1_aarch64.dmg` | DMG mounts, drag to Applications works | App installs and runs from /Applications |
| P5-005 | Bundle Python virtualenv inside `.app` | infra | DevOps | 4h | P1-017, P5-003 | Python 3.11 + brandmint deps bundled in `Brandmint.app/Contents/Resources/venv/` | App works without system Python | Fresh Mac user can run app |
| P5-006 | Test first-launch experience on clean macOS | qa | QA | 2h | P5-005 | Test on new user account with no dev tools | App launches, pipeline works | No missing dependency errors |

### Wave 5.2 — Code Signing & Notarization (Swarm B: Infra)

| ID | Title | Area | Owner | Est | Deps | Deliverable | Acceptance | Validation |
|----|-------|------|-------|-----|------|-------------|------------|------------|
| P5-007 | Set up Apple Developer certificate for code signing | infra | DevOps | 4h | — | Developer ID Application certificate in Keychain | Certificate valid and trusted | `security find-identity` shows cert |
| P5-008 | Configure Tauri code signing in `tauri.conf.json` | infra | DevOps | 2h | P5-007 | Signing identity and entitlements configured | `cargo tauri build` produces signed app | `codesign -v Brandmint.app` passes |
| P5-009 | Submit app for Apple notarization | infra | DevOps | 2h | P5-008 | App notarized via `xcrun notarytool` | macOS Gatekeeper allows app to open | No "unidentified developer" warning |

### Wave 5.3 — Auto-Update (Swarm C: Backend)

| ID | Title | Area | Owner | Est | Deps | Deliverable | Acceptance | Validation |
|----|-------|------|-------|-----|------|-------------|------------|------------|
| P5-010 | Configure Tauri updater plugin | backend | Backend Eng | 2h | P5-003 | `@tauri-apps/plugin-updater` configured with update endpoint | App checks for updates on launch | Update check request visible in logs |
| P5-011 | Set up update JSON endpoint (GitHub Releases or custom server) | infra | DevOps | 2h | P5-010 | GitHub Release-based update manifest | New releases trigger update notification | In-app update prompt appears |
| P5-012 | Implement in-app update dialog | frontend | Frontend Eng | 2h | P5-010 | "Update Available" dialog with changelog, download, install | Users can update without re-downloading DMG | Update installs and app restarts |

---

## Phase 6: Testing & Quality

> **Objective:** Automated tests for Rust commands, React components, and E2E flows.
> **Exit criteria:** >80% coverage on critical paths, CI pipeline green.

### Wave 6.1 — Unit & Integration Tests (Swarm A: QA)

| ID | Title | Area | Owner | Est | Deps | Deliverable | Acceptance | Validation |
|----|-------|------|-------|-----|------|-------------|------------|------------|
| P6-001 | Write Rust unit tests for all Tauri commands | qa | QA | 4h | P2-032 | `#[cfg(test)]` modules in each `commands/*.rs` | All commands have test coverage | `cargo test` passes |
| P6-002 | Write Rust integration test for sidecar lifecycle | qa | QA | 4h | P1-015 | Test: spawn sidecar, health check, shutdown | Sidecar lifecycle tested | `cargo test --test sidecar` passes |
| P6-003 | Set up Vitest for React component tests | qa | QA | 2h | P3-036 | `vitest.config.ts`, test utilities, mocks for Tauri API | `npm run test` runs Vitest | Vitest runs and reports results |
| P6-004 | Write component tests for Pipeline control | qa | QA | 2h | P6-003, P3-010 | Tests for PipelineControl start/abort/retry | Component tests pass | `npm run test` passes |
| P6-005 | Write component tests for Wizard flow | qa | QA | 2h | P6-003, P3-013 through P3-016 | Tests for each wizard step | Wizard flow tested | All wizard tests pass |

### Wave 6.2 — E2E Tests (Swarm B: QA)

| ID | Title | Area | Owner | Est | Deps | Deliverable | Acceptance | Validation |
|----|-------|------|-------|-----|------|-------------|------------|------------|
| P6-006 | Set up WebDriverIO or Playwright for Tauri E2E tests | qa | QA | 2h | P5-003 | E2E test harness that launches Tauri app | E2E framework launches app | App starts in test mode |
| P6-007 | Write E2E test: app launch → sidecar ready → UI visible | qa | QA | 2h | P6-006 | Test verifies full startup sequence | Startup E2E passes | Test completes in <30s |
| P6-008 | Write E2E test: open brand folder → configure → start pipeline | qa | QA | 2h | P6-006 | Test verifies full pipeline flow | Pipeline E2E passes | Test completes successfully |
| P6-009 | Write E2E test: settings save/load persistence | qa | QA | 1h | P6-006 | Test verifies settings survive restart | Settings E2E passes | Settings persist after restart |
| P6-010 | Add CI workflow (GitHub Actions) for Rust + Frontend tests | qa | QA | 2h | P6-001 through P6-005 | `.github/workflows/tauri-tests.yml` | CI runs on every push | GitHub Actions badge green |

---

## Dependency Rationale

### Critical Path
```
P1-001 → P1-002 → P1-008 → P1-012 → P1-013 → P1-028 (Phase 1 prototype)
  ↓
P2-003 → P2-004 → P2-007..P2-027 → P2-032 (IPC migration)
  ↓
P3-001 → P3-007 → P3-009..P3-036 (Component refactor)
  ↓
P4-001..P4-018 (Native features — can parallel with P3)
  ↓
P5-001 → P5-005 → P5-006 (Distribution)
```

### Parallel Tracks
- **Swarm A (Infra)** and **Swarm B (Backend)** can run in parallel within each wave
- **Phase 4 (Native Features)** can start as soon as Phase 2 is complete, running parallel to Phase 3
- **Phase 6 (Testing)** can start writing test infrastructure during Phase 3

### Key Dependencies
- All Phase 2 commands depend on P2-004 (HTTP client to sidecar)
- All Phase 3 components depend on P3-007 (state migration to stores)
- Phase 5 distribution depends on Phase 1 prototype being stable
- Phase 6 E2E tests depend on Phase 5 build

---

## Verification Strategy

| Layer | Method | Frequency |
|-------|--------|-----------|
| Rust compilation | `cargo build` + `cargo clippy` | Every task |
| Frontend compilation | `npm run build` (tsc + vite) | Every task |
| Rust unit tests | `cargo test` | Every backend task |
| Frontend component tests | `npm run test` | Every frontend task |
| Integration test | Launch app, verify sidecar + UI | End of each wave |
| E2E test | Full pipeline run through app | End of each phase |
| Visual verification | Screenshot comparison | End of Phase 3, 4 |
| Distribution test | DMG install on clean account | End of Phase 5 |

---

## GitHub Sync Strategy

### Labels
- `phase:1-scaffold`, `phase:2-ipc`, `phase:3-refactor`, `phase:4-native`, `phase:5-distro`, `phase:6-testing`
- `area:frontend`, `area:backend`, `area:infra`, `area:qa`
- `wave:1.1`, `wave:1.2`, etc.

### Milestones
- **M1: Working Prototype** (Phase 1 complete)
- **M2: IPC Migration** (Phase 2 complete)
- **M3: Component Architecture** (Phase 3 complete)
- **M4: Native Desktop** (Phase 4 complete)
- **M5: Distribution Ready** (Phase 5 complete)
- **M6: Quality Gate** (Phase 6 complete)

### Dispatch Strategy
Use `dispatching-parallel-agents` skill to parallelize:
- Within each wave, independent swarms run concurrently
- Phase 4 waves run in parallel with Phase 3
- Test infrastructure (P6-001..P6-003) starts during Phase 3

---

## Risks & Fallback Plan

| Risk | Impact | Mitigation |
|------|--------|------------|
| Python sidecar bundling fails on macOS | Distribution blocked | Fallback: require system Python + `pip install brandmint` |
| Tauri v2 sidecar stdin/stdout unreliable | IPC migration blocked | Fallback: keep HTTP bridge, connect via localhost |
| Reference image serving slow via IPC | UX degradation | Fallback: use Tauri asset protocol for direct file serving |
| App bundle size too large (Python venv) | Distribution friction | Mitigation: use `pyinstaller` to create standalone binary |
| Code signing requires Apple Developer account ($99/yr) | Can't distribute outside App Store | Fallback: distribute unsigned, user right-clicks to open |
| Monolithic App.tsx refactor introduces regressions | Feature breakage | Mitigation: add component tests before splitting |

---

## Appendix: API Endpoint Migration Map

| HTTP Bridge Endpoint | Tauri Command | Phase |
|---------------------|---------------|-------|
| `GET /api/health` | `get_health` | P2 |
| `GET /api/state` | `get_state` → replaced by events | P2 |
| `GET /api/runners` | `get_runners` | P2 |
| `GET /api/settings` | `get_settings` | P2 |
| `POST /api/settings` | `update_settings` | P2 |
| `GET /api/logs?since=N` | `sidecar-log` event stream | P2 |
| `GET /api/artifacts` | `get_artifacts` | P2 |
| `GET /api/references` | `get_references` | P2 |
| `GET /api/reference-image` | `get_reference_image` / asset protocol | P2 |
| `POST /api/run/start` | `start_run` | P2 |
| `POST /api/run/retry` | `retry_run` | P2 |
| `POST /api/run/abort` | `abort_run` | P2 |
| `POST /api/publish/start` | `start_publish` | P2 |
| `POST /api/intake/load` | `load_intake` | P2 |
