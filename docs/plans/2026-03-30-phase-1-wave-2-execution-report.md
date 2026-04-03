# Phase 1 Wave 2 Execution Report

Generated: 2026-03-30
Repository: `https://github.com/Sheshiyer/brandmint-oracle-aleph`
Plan reference: `docs/plans/2026-03-30-brandmint-clawable-swarm-plan.md`
Wave scope:
- `P1-W2-SA-T05` Compare front-end wizard spec against current UI behavior
- `P1-W2-SA-T06` Compare runtime docs against current CLI and Tauri behavior
- `P1-W2-SB-T07` Synthesize main failure themes from code, issues, and changelog
- `P1-W2-SB-T08` Define the "GitHub URL only -> run Brandmint" acceptance story

## Result

Phase 1 Wave 2 is complete.

- The front-end specs and the live UI are directionally aligned, but the important trust mechanisms are still missing.
- Runtime docs still describe a config-first CLI pipeline, while the current desktop surface is a hybrid draft studio with incomplete approval semantics.
- The most damaging mismatch is no longer just "wrong visuals"; it is a compound drift across source-of-truth, runtime pathing, and domain policy.
- The initiative now has a concrete acceptance contract for a future repo-URL-driven operator flow.

## T05. Front-End Wizard Spec vs Current UI

### Summary

The UI has the broad shape of the intended journey:

`Product MD intake -> extraction -> wizard -> export -> launch`

But it does not yet implement the spec's core review and traceability guarantees. The current app is a draft-oriented studio, not an approval-oriented config gate.

### Comparison matrix

| Spec requirement | Current behavior | Status | Evidence |
|---|---|---|---|
| Product-MD-first intake | Intake page exists with file upload, paste/edit field, and saved draft restore | partial | `docs/front-ui/product-md-intake-requirements.md`, `ui/src/App.tsx` |
| Minimum length 250 chars, warn-not-block on missing audience/offer | UI blocks below 80 chars and has no explicit warn-only checks for missing audience or offer | missing | spec says 250 + warn-only; UI enforces 80-char gate |
| Preserve source snippets for traceability | Extraction stores only flat strings plus one global confidence score | missing | no snippet/provenance model in extraction state |
| Mark low-confidence fields as `needs_review` | No per-field confidence or `needs_review` state exists | missing | UI only renders single confidence percentage |
| Keep unmapped inputs | Unknown content is not persisted under an unmapped bucket | missing | config draft model has no unmapped field |
| Review extraction summary before config synthesis | Extraction review page exists with editable extracted fields and confirm action | implemented | extraction page and confirm action are present |
| Wizard to shape canonical config | Five-step wizard exists | implemented | brand/audience/voice/visual/review wizard flow exists |
| Review + export config as a confidence gate | Export page exists, but export is just a browser download and not an approval checkpoint | partial | export is not tied to an approved state |
| Launch handoff after export | Launch page exists, but launch is not blocked on an approved/saved config artifact | partial | launch only keys off `exportedAt` and current path string |

### High-signal evidence

- Spec says the intake phase should support file upload, paste text, and saved draft continuation, with validation behavior such as:
  - minimum input length `250`
  - warn-not-block when audience or offer is missing
  - preserve original snippets for traceability
  - autosave every `5` seconds
  - restore draft on return
  Source: `docs/front-ui/product-md-intake-requirements.md`.

- Current intake implementation:
  - supports file upload and draft restore
  - blocks extraction below `80` characters
  - does not compute targeted missing-field warnings
  - does not capture source snippets or a fallback manual mapping mode
  Source: `ui/src/App.tsx`.

- Mapping spec requires:
  - source snippet references per mapped field
  - `needs_review` when confidence `< 0.75`
  - `notes.unmapped_inputs`
  - metadata such as source hash, extraction timestamp, and prompt versions
  Source: `docs/front-ui/brand-config-mapping-spec.md`.

- Current extraction/config model:
  - `parseProductMd()` returns only eight strings plus one overall confidence value
  - `extractionToConfig()` injects fallback defaults like `"Brandmint Product"` and `"ai-product"`
  - `configToYaml()` emits only brand/audience/positioning/campaign/visual sections, with no provenance or approval metadata
  Source: `ui/src/App.tsx`.

- Export and launch are not coupled to an approved config artifact:
  - `exportConfigFiles()` downloads YAML/JSON based on the filename portion of `configPath`
  - `startRun()` posts the current `configPath` string to the bridge
  - `pageStatusMap` treats launch as effectively unlocked once `exportedAt` is set
  Source: `ui/src/App.tsx`.

### T05 conclusion

The UI has enough scaffolding to demonstrate the intended journey, but not enough enforcement to claim that `brand-config.yaml` is the reviewed source of truth. It currently behaves like:

`extract -> edit -> draft -> download -> fire bm launch`

instead of:

`extract -> review evidence -> edit -> approve canonical config -> export saved artifact -> handoff`

## T06. Runtime Docs vs Current CLI and Tauri Behavior

### Summary

The docs still present Brandmint as a config-first CLI pipeline. The current Tauri app is a Python-bridge wrapper around that CLI, but its operational semantics are not cleanly documented, and some runtime assumptions are now incorrect.

### Drift matrix

| Doc/runtime statement | Current reality | Status |
|---|---|---|
| `bm launch` is the sole canonical entrypoint | still true for execution backend | aligned |
| Desktop/Tauri local run path is self-explanatory from docs | desktop prerequisites and startup path are under-documented | drift |
| Relative repo paths are safe in the desktop bridge | bridge hardcodes a nonexistent repo root in this workspace | broken |
| Launch from desktop uses the exported config as source of truth | launch uses the current `configPath` string, not a persisted approved artifact | drift |
| Current pipeline removed old Tryambakam/icon/recraft pathways | active product and `recraft-v3` branches remain live in generation code | drift |
| Inference provider defaults are consistent across UI and bridge | UI default endpoint is `.net`; bridge default endpoint is `.sh` | drift |

### High-signal evidence

- `CLAUDE.md` still frames the system almost entirely as:
  - prepare `brand-config.yaml`
  - run `bm launch --config ... --non-interactive`
  - let the pipeline orchestrate everything
  Source: `CLAUDE.md`.

- `README.md` quick start also presents a CLI-first story:
  - clone repo
  - `pip install -e .`
  - `bm init`
  - `bm launch`
  It does not explain the full desktop bootstrap requirements for Tauri local use (`npm`, Rust, frontend install/build, sidecar behavior, Vite port expectations).
  Source: `README.md`.

- The Tauri/bridge runtime currently depends on a Python HTTP bridge that hardcodes:

```python
ROOT = Path("/Volumes/madara/2026/brandmint")
```

  but the actual workspace for this run is:

```text
/Volumes/madara/2026/twc-vault/01-Projects/brandmint
```

  That means relative path resolution in the bridge does not target the live repo checkout.

- Safe repro captured during this wave:

```bash
curl -sS -X POST http://127.0.0.1:4191/api/intake/load \
  -H 'Content-Type: application/json' \
  -d '{"brandFolder":"./brandmint","productMdFile":"product.md","configFile":"brand-config.yaml"}'
```

  Response:

```json
{"ok": false, "error": "Directory not found: /Volumes/madara/2026/brandmint/brandmint"}
```

  This proves the app's default relative brand-folder path is not valid under the bridge's current root assumption.

- UI/provider defaults are inconsistent:
  - app default inference endpoint: `https://api.inference.net`
  - bridge default inference endpoint: `https://api.inference.sh`

- The desktop app labels launch as a safe retry workflow "on 4188," but:
  - bridge itself listens on `4191`
  - Vite dev server uses `4188`
  - retry logic clears port `4188`
  This is recoverable internally, but still confusing as a user-facing execution model.

### T06 conclusion

The docs are still closer to "CLI operator guide" than "desktop runtime contract." The system is currently runnable, but its documented mental model is simpler and cleaner than the actual runtime surface.

## T07. Main Failure Themes

### Core diagnosis

The main issue is not one bad prompt or one stale visual setting. The real failure is multi-layer architectural drift.

### Theme 1. Source-of-truth drift

- Specs assume a reviewed canonical config with provenance.
- UI generates a mutable in-memory draft.
- Export marks success via `exportedAt`.
- Launch uses the `configPath` string, not an approved persisted artifact.

Impact:
- users can believe they are launching "the approved config" when the system is really launching whatever path string is present at runtime.

### Theme 2. Runtime-path drift

- UI defaults use relative repo-friendly paths such as `./brandmint` and `./brand-config.yaml`.
- Bridge resolves relative paths against a hardcoded `ROOT` that is wrong in this workspace.
- Intake repro already proves the default desktop relative path flow is broken.

Impact:
- the app is not yet robust enough for the future "give the repo URL and run it" requirement.

### Theme 3. Visual-domain drift

- Changelog claims the old Noesis/Tryambakam defaults and 5D icon generation were removed.
- Live generation code still keeps:
  - strongly product-centric asset catalog entries
  - `recraft-v3` paths for `5A` and `5C`
  - `5D` icon entry in `run_pipeline.py`
  - SaaS defaults that still describe screens/devices/merchandise as "product" outputs

Impact:
- app/SaaS brands can still inherit product-led imagery semantics and unrelated physical-object assumptions.

### Theme 4. Documentation-roadmap drift

- Front-end docs describe a review-first, confidence-first flow.
- `CLAUDE.md` and `README.md` still describe a launch-first pipeline.
- GitHub backlog is dominated by old `vision-upgrade` issues unrelated to the current run-path/HITL problem.

Impact:
- contributors and agents are being pointed at the wrong layer of the problem.

### T07 conclusion

The user-visible symptom "it still generates the wrong kinds of images" is downstream of a larger issue:

the system has no enforced approved-config boundary, no stable runtime path contract, and no fully separated app-domain visual policy.

## T08. "GitHub URL Only -> Run Brandmint" Acceptance Story

### Acceptance statement

Brandmint should be considered clawable for this use case only when an operator or agent can take a GitHub repository URL and deterministically reach an approved `brand-config.yaml` plus a controlled execution handoff without relying on tribal knowledge.

### Preconditions

The following must be explicit and validated:

1. Clean checkout of the repository.
2. Python, Node/npm, and Rust/Cargo are installed at supported versions.
3. Required environment variables are declared and checked before launch.
4. Supported run mode is explicit:
   - desktop/Tauri
   - CLI/headless
   - or documented non-support for a given mode
5. Repo-relative paths resolve against the real checkout, not a hardcoded machine path.

### Acceptable operator story

1. User gives the GitHub repository URL and says "run Brandmint."
2. Agent clones the repo and runs a preflight that verifies:
   - Python
   - Node/npm
   - Rust/Cargo
   - required env vars
   - supported run mode
3. Agent starts the supported runtime.
4. User supplies Product MD or the repo's expected brand folder content.
5. System extracts structured fields and shows:
   - source snippets
   - confidence
   - `needs_review` markers
6. User edits and explicitly approves the config draft.
7. System writes an approved `brand-config.yaml` with:
   - provenance
   - approval metadata
   - fingerprint
8. System pauses and asks for the next explicit action:
   - export only
   - launch selected waves
   - publish later
9. If the user chooses launch, execution starts from the approved config artifact, not from a stale path string or mutable draft state.

### Required outputs

- approved `brand-config.yaml`
- saved filesystem path for that config
- approval metadata and provenance
- operator-visible state saying whether execution is paused, ready, or running
- actionable errors if preflight, intake, export, or runtime startup fail

### Non-goals for this acceptance story

The following are not required to mark the flow clawable:

- full pipeline completion without user review
- a fully autonomous zero-input brand run
- old `vision-upgrade` work
- optional X automation from issue `#66`

### Current blockers against acceptance

1. No approved-config gate exists across UI, bridge, and CLI.
2. Export is a client download, not a guaranteed saved source-of-truth artifact.
3. Bridge path resolution is tied to a hardcoded root that is wrong for this workspace.
4. Desktop docs do not yet explain the true bootstrap contract.
5. App/SaaS visual policy is not yet separated enough from product-led prompt defaults.

## Wave 2 Handoff

Phase 1 Wave 2 leaves the initiative ready for Wave 1.3:

- The UI/spec gap is explicit.
- The runtime/docs drift is explicit.
- The main failure has been named as architectural drift, not just visual regression.
- The clawable acceptance story is now concrete enough to drive the config contract and GitHub issue map.

Recommended next execution batch:

1. `P1-W3-SA-T09` Define canonical `brand-config.yaml` source-of-truth contract.
2. `P1-W3-SB-T10` Create initiative issue map and milestone proposal.
