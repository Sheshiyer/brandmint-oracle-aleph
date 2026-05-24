# NotebookLM Config Normalization Contract (Phase 1, Wave 2)

Date: `2026-05-15`
Task anchors: `P1-W2-SA-T05`, `P1-W2-SB-T06`

## Problem

NotebookLM settings were split across two shapes:

- legacy: `notebooklm.*`
- newer: `publishing.notebooklm.*`

This allowed silent configuration drift where intended settings were ignored.

## Canonical Shape

Canonical path is now:

- `publishing.notebooklm`

Examples:

- `publishing.notebooklm.max_parallel_workers`
- `publishing.notebooklm.inter_artifact_delay`
- `publishing.notebooklm.reuse_policy`
- `publishing.notebooklm.artifacts`

## Compatibility and Precedence

Legacy path remains supported for compatibility, but merge precedence is strict:

1. Start with `notebooklm` (legacy fallback).
2. Overlay `publishing.notebooklm` (canonical wins).

If both are present, canonical values override legacy values.

## Hook-Level Synthesis Settings

For Wave 7 synthesis values:

- canonical: `publishing.notebooklm.synthesize`, `publishing.notebooklm.synthesis_model`
- legacy fallback: `publishing.synthesize`, `publishing.synthesis_model`

## Validation Expectations

1. Nested canonical values must be observed at runtime.
2. Legacy-only configs must still function.
3. Mixed configs must resolve deterministically to canonical values.

## Non-Goals

- No breaking removal of legacy keys in this phase.
- No schema hard-fail yet; warnings/deprecations are introduced in later phases.
