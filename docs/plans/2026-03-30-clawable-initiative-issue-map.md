# Clawable Run-Path Issue Map And Milestone Proposal

## Status

- Date: `2026-03-30`
- Task: `P1-W3-SB-T10`
- Scope: translate the 80-task plan into a GitHub issue structure that can be synchronized later without carrying forward the stale vision backlog as active work

## Current GitHub Baseline

Live issue inspection confirms:

- the active non-vision backlog is still `#113` and `#66`
- every open `vision-upgrade` issue `#9-#51` is still open and unmigrated
- open issues currently have `null` milestone values

Active non-vision issues today:

- `#113` `[Tauri Releases] Publish macOS app bundles and zipped desktop artifacts to GitHub Releases`
- `#66` `[Automation] Add Inference X integration path with scope checks + dry-run safeguards`

Interpretation:

- `#113` remains legitimate active work
- `#66` is real but not part of the clawable run-path critical path
- the `vision-upgrade` stack is roadmap inventory, not the product problem this initiative is solving

## Proposed Milestone

Create one initiative milestone:

- `clawable-run-path`

Purpose:

- collect the work required to make `GitHub URL -> approved config -> controlled Brandmint execution` real
- avoid mixing current operator-path work with the deferred vision roadmap
- let Phase 7 GitHub hygiene query one clean milestone instead of a fragmented wave-label stack

Milestone completion means:

1. approved config gating exists
2. the HITL loop exists
3. app-domain visual policy exists
4. the Tauri/sidecar path is hardened enough for the supported workflow
5. the SOP/docs path matches reality

## Proposed Label Taxonomy

Keep existing labels where they already fit:

- `priority:tier-1`
- `priority:tier-2`
- `tauri-v2`
- `phase:5-distro`
- `enhancement`

Add only the minimum new labels needed to query the initiative cleanly:

- `initiative:clawable-run-path`
- `area:config-approval`
- `area:hitl-loop`
- `area:visual-policy`
- `area:tauri-runtime`
- `area:operator-docs`

Guidance:

- milestone answers "is this part of the initiative?"
- area labels answer "which workstream owns it?"
- priority labels answer "should we execute it now?"

## Proposed Issue Set

Use one umbrella issue plus one issue per major workstream.

### Recommended new umbrella issue

Title:

- `Clawable run path: repo URL -> approved config -> controlled Brandmint execution`

Purpose:

- hold the initiative acceptance summary
- link the five major workstream issues
- carry the Phase 1/Phase 8 review links

Labels:

- `initiative:clawable-run-path`
- `priority:tier-1`

Milestone:

- `clawable-run-path`

## Workstream Issue Matrix

| Type | Proposed issue | Plan coverage | Milestone | Labels | Notes |
|---|---|---|---|---|---|
| New | Canonical brand-config contract, provenance, and approval gating | `P2-W1-SA-T11` through `P2-W2-SB-T20` | `clawable-run-path` | `initiative:clawable-run-path`, `area:config-approval`, `priority:tier-1`, `enhancement` | Covers schema, provenance, fingerprinting, launch guards, error contract, and test coverage |
| New | Human-in-the-loop pause, revise, continue execution loop | `P3-W1-SA-T21` through `P3-W2-SB-T30` | `clawable-run-path` | `initiative:clawable-run-path`, `area:hitl-loop`, `priority:tier-1`, `enhancement` | Covers checkpoint model, pause/resume behavior, bridge endpoints, UI controls, decision journal, and smoke tests |
| New | App-domain visual policy and prompt-family safety | `P4-W1-SA-T31` through `P4-W3-SB-T42` | `clawable-run-path` | `initiative:clawable-run-path`, `area:visual-policy`, `priority:tier-1`, `enhancement` | Covers stale product/recraft cleanup, domain policy, app screenshot contract, prompt replacements, routing, and app-brand regression fixtures |
| New | Tauri sidecar singleton, diagnostics, and startup hardening | `P5-W1-SA-T43` through `P5-W2-SB-T52` | `clawable-run-path` | `initiative:clawable-run-path`, `area:tauri-runtime`, `priority:tier-1`, `tauri-v2`, `enhancement` | Covers port ownership, recovery, diagnostics, smoke path, bootstrap checks, and release checklist alignment |
| New | Repo-URL operator SOP and canonical lifecycle docs | `P6-W1-SA-T53` through `P6-W2-SB-T62` | `clawable-run-path` | `initiative:clawable-run-path`, `area:operator-docs`, `priority:tier-1`, `enhancement` | Covers the core SOP, lifecycle docs, visual policy docs, examples, troubleshooting, prompt recipe, and docs QA |
| Existing | Keep `#113` as distribution hardening follow-through | `P7-W1-SA-T63`, `P7-W2-SA-T68`, `P7-W2-SB-T70` plus packaging follow-through from Phase 5 | `clawable-run-path` | keep current labels and add `initiative:clawable-run-path` | This stays active, but it should be treated as the distribution track attached to the initiative, not the entire initiative |
| Existing | Keep `#66` deferred unless priorities change | `P7-W1-SA-T64` | none | keep `priority:tier-2`, `automation`, `inference-migration` | Explicitly exclude from `clawable-run-path` unless the user re-prioritizes automation |
| Existing stack | `#9-#51` vision backlog stays archived/deferred from the initiative | `P7-W1-SB-T65`, `P6-W2-SB-T61` | none | keep `vision-upgrade`, wave labels, `priority:tier-2` | Do not place under the new milestone; they should stop dominating active backlog views |

## Why This Mapping Is The Right Granularity

This split matches the plan's later GitHub sync strategy:

- one issue per major workstream
- one milestone for the initiative
- existing active distro issue preserved
- unrelated automation issue explicitly deferred
- stale vision roadmap kept out of the active milestone

It is also the right execution shape:

- config approval work is the core trust boundary
- HITL loop is distinct runtime behavior layered on top of that trust boundary
- visual policy is separate domain safety work
- Tauri runtime hardening is a platform concern
- docs/SOP work should trail the real implementation and remain queryable on its own

## Proposed Creation Order

Create or update issues in this order:

1. umbrella initiative issue
2. config approval issue
3. HITL loop issue
4. visual policy issue
5. Tauri runtime issue
6. operator docs issue
7. update `#113`
8. comment/defer `#66`
9. apply archive/defer handling to `#9-#51`

This ordering preserves the dependency chain from the plan:

- approval before HITL
- policy before docs examples
- runtime hardening before final SOP claims

## Recommended Body Checklist Shape For New Issues

Each new issue should include:

- linked task IDs from the swarm plan
- problem statement
- acceptance criteria copied from the plan
- explicit non-goals
- validation section naming the required tests or walkthroughs

That keeps the later `P7-W1-SB-T66` issue creation step deterministic.

## Query Model After Sync

After the actual GitHub sync work lands, the project should support these clean queries:

- active initiative work: milestone `clawable-run-path`
- config-only work: milestone `clawable-run-path` + label `area:config-approval`
- Tauri-only work: milestone `clawable-run-path` + label `area:tauri-runtime`
- deferred automation: label `automation` + `priority:tier-2` without the milestone
- archived vision roadmap: label `vision-upgrade` without the milestone

## Immediate Phase 7 Implications

When Phase 7 begins, this proposal should drive the real GitHub changes:

- `#113` gets linked into the milestone
- `#66` gets an explicit defer decision
- `#9-#51` are kept out of the initiative milestone
- five new workstream issues are created
- the initiative milestone and area labels are added

That is the cleanest path from the current noisy backlog to a backlog that actually reflects the product work.
