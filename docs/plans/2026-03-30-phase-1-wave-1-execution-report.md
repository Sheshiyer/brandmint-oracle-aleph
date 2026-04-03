# Phase 1 Wave 1 Execution Report

Generated: 2026-03-30
Repository: `https://github.com/Sheshiyer/brandmint-oracle-aleph`
Plan reference: `docs/plans/2026-03-30-brandmint-clawable-swarm-plan.md`
Wave scope:
- `P1-W1-SA-T01` Audit open non-vision issues and PRs
- `P1-W1-SA-T02` Define archive/defer policy for `vision-upgrade` issue stack
- `P1-W1-SB-T03` Capture clean Tauri, Vite, and bridge startup evidence
- `P1-W1-SB-T04` Produce dependency and environment matrix

## Result

Phase 1 Wave 1 is complete.

- Active non-vision GitHub backlog is narrow and clear.
- The `vision-upgrade` stack is a deferred roadmap, not the active product problem.
- The desktop runtime is reproducible locally with the Tauri-managed Python sidecar.
- Operator prerequisites can now be expressed as a concrete environment matrix rather than tribal knowledge.

## T01. Audit Open Non-Vision Issues and PRs

Live GitHub state checked on 2026-03-30:

### Open non-vision issues

| Issue | Title | Labels | Decision |
|---|---|---|---|
| `#113` | `[Tauri Releases] Publish macOS app bundles and zipped desktop artifacts to GitHub Releases` | `enhancement`, `tauri-v2`, `phase:5-distro`, `priority:tier-1` | Keep active; directly aligned to desktop distribution hardening |
| `#66` | `[Automation] Add Inference X integration path with scope checks + dry-run safeguards` | `enhancement`, `priority:tier-2`, `inference-migration`, `automation` | Defer unless explicitly reprioritized; not required for clawable run-path hardening |

### Open PRs

| PR | Title | Branch | Decision |
|---|---|---|---|
| `#116` | `Add macOS Tauri release asset workflow` | `codex/tauri-release-assets` | Keep visible as related distribution work; review against issue `#113` acceptance |

### Backlog shape

- Open issues observed: `45`
- Open non-vision issues observed: `2`
- Open `vision-upgrade` issues observed: `43`
- Open PRs observed: `1`

Conclusion:
- The active execution backlog for this initiative is not the large vision stack.
- The real near-term GitHub surface is `#113`, `#66`, and PR `#116`.

## T02. Archive/Defer Policy For `vision-upgrade`

### Policy

Any open issue matching all of the following conditions should be treated as deferred roadmap work, not active execution:

1. It carries the `vision-upgrade` label.
2. It does not unblock approved-config gating, the HITL loop, app-domain visual policy, Tauri runtime hardening, or clawable SOP work.
3. It is not explicitly called into the current milestone by a new dependency decision.

### Operational rule

- Do not use the `vision-upgrade` stack to represent the active product roadmap.
- Remove those issues from the active initiative milestone/query once the GitHub cleanup phase lands.
- Preserve them as deferred roadmap work rather than silently deleting history.
- Re-activate only if a later phase explicitly needs one of those capabilities.

### Sample mapping by issue range

| Issue range | Current label group | Wave meaning | Phase 1 Wave 1 disposition |
|---|---|---|---|
| `#9-#18` | `wave-1-foundation` | visual foundations | defer/archive from active backlog |
| `#19-#27` | `wave-2-computed` | computed image metadata | defer/archive from active backlog |
| `#28-#36` | `wave-3-embeddings` | CLIP/FAISS/embedding work | defer/archive from active backlog |
| `#37-#44` | `wave-4-vision-api` | vision intelligence layer | defer/archive from active backlog |
| `#45-#51` | `wave-5-integration` | integration and migration work | defer/archive from active backlog |

### Why this policy is correct

- The user-facing failure being investigated is not "missing vision intelligence."
- The current failure is architectural drift between the intended review-first flow and the live pipeline.
- Leaving `vision-upgrade` as the dominant open backlog makes the repo look like it is prioritizing the wrong problem.

## T03. Runtime Evidence

### Verified commands

| Command | Result |
|---|---|
| `npm --prefix ui run build` | passed |
| `cargo build` in `ui/src-tauri` | passed |
| `pytest tests/test_generate_pipeline_spec_lock.py tests/test_visual_backend.py tests/test_source_curator.py` | passed (`18` tests) |
| `npm --prefix ui run tauri:dev` | passed; Vite and Tauri app started successfully |
| `curl -sS http://127.0.0.1:4191/api/health` during Tauri run | returned healthy bridge response |

### Fresh startup transcript highlights

- Vite served locally on `http://127.0.0.1:4188/`
- Tauri launched `target/aarch64-apple-darwin/debug/brandmint-app`
- Rust app spawned sidecar using `/opt/homebrew/bin/python3`
- Sidecar script path resolved to `scripts/ui_backend_bridge.py`
- Bridge reported healthy after `2` attempts
- Health endpoint returned:

```json
{"ok": true, "service": "ui-backend-bridge", "time": "2026-03-30T01:52:26.741202+00:00"}
```

### Runtime risk already confirmed

- If a standalone bridge is already bound to port `4191`, the Tauri-managed sidecar collides with it and startup fails.
- That is a real Phase 5 hardening item, not just an operator mistake.

## T04. Dependency And Environment Matrix

### Local toolchain observed in this workspace

| Layer | Requirement from repo | Local version observed | Notes |
|---|---|---|---|
| Python | `>=3.10` from `pyproject.toml` | `Python 3.14.3` | compatible |
| Node.js | required by Vite/Tauri frontend | `v25.8.1` | used successfully for `npm` workflows |
| npm | required by frontend scripts | `11.11.0` | used successfully for build and dev |
| Rust | crate declares `rust-version = "1.77.2"` | `rustc 1.89.0` | compatible, above minimum |
| Cargo | required for Tauri/Rust build | `cargo 1.89.0` | used successfully for local build |
| OS target | inferred from Tauri build path | `aarch64-apple-darwin` | inference from successful local build output |

### Operator entrypoints

| Surface | Source | Command |
|---|---|---|
| Desktop dev | `Makefile` | `make dev` |
| Desktop build | `Makefile` | `make build` |
| Standalone sidecar | `Makefile` | `make sidecar` |
| Dependency bootstrap | `Makefile` | `make install` |
| CLI entrypoint | `pyproject.toml` | `brandmint` |
| CLI alias | `pyproject.toml` | `bm` |

### Command definitions checked

| Command | Resolved behavior |
|---|---|
| `make dev` | `cd ui && npm run tauri:dev` |
| `make build` | `cd ui && npm run tauri:build` |
| `make sidecar` | `python3 scripts/ui_backend_bridge.py` |
| `make install` | `cd ui && npm install` then `cd ui/src-tauri && cargo build` |

### Core Python package dependencies

| Dependency | Role |
|---|---|
| `typer` | CLI surface |
| `rich` | terminal rendering |
| `pydantic` | config/data validation |
| `pyyaml` | YAML import/export |
| `python-dotenv` | environment loading |
| `requests` | HTTP calls |
| `fal-client` | image provider path |

Optional groups defined:
- `dev`
- `publishing`
- `vision`
- `embeddings`

### Required and optional environment variables

| Variable | Status | Purpose |
|---|---|---|
| `IMAGE_PROVIDER` | selector | choose image backend |
| `FAL_KEY` | optional provider credential | fal.ai generation |
| `OPENROUTER_API_KEY` | optional provider credential | OpenRouter image and prose workflows |
| `OPENAI_API_KEY` | optional provider credential | OpenAI image/text fallback |
| `REPLICATE_API_TOKEN` | optional provider credential | Replicate image backend |
| `ANTHROPIC_API_KEY` | required for current text-skill path | text generation |
| `ELEVENLABS_API_KEY` | optional | voice generation |
| `HF_TOKEN` | optional | Hugging Face access |

### Rust/Tauri package evidence

| Field | Value |
|---|---|
| Package | `brandmint-app` |
| Version | `4.4.0` |
| Edition | `2021` |
| Minimum Rust | `1.77.2` |
| Tauri crate | `2.10.0` |

## Wave 1 Handoff

Phase 1 Wave 1 leaves the initiative in a clean state for Wave 1.2:

- Backlog truth is established.
- Deferred vision-roadmap policy is defined.
- Runtime reproducibility is verified.
- Operator prerequisites are documented.

Recommended next execution batch:

1. `P1-W2-SA-T05` Compare front-end wizard spec against current UI behavior.
2. `P1-W2-SA-T06` Compare runtime docs against current CLI and Tauri behavior.
3. `P1-W2-SB-T07` Synthesize the main failure themes from code, issues, and changelog.
4. `P1-W2-SB-T08` Define the exact "GitHub URL only -> run Brandmint" acceptance story.
