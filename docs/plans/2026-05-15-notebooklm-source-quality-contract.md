# NotebookLM Source Quality Contract (Phase 1, Wave 1)

Date: `2026-05-15`
Initiative: `NotebookLM Source Quality Hardening`
Milestone: `NotebookLM Source Quality Hardening`
Task anchors: `P1-W1-SA-T01`, `P1-W1-SD-T04`

## Objective

Define non-negotiable quality boundaries for any document uploaded to NotebookLM so generated artifacts read as brand-native outcomes, not pipeline-internal metadata.

## Contract Scope

Applies to all files selected for upload by Wave 7 publishing from:

- `deliverables/notebooklm/sources/*.md`
- source-builder outputs
- curator-selected markdown documents

## Forbidden Lexicon (Must Not Ship)

The following language is disallowed in publish-ready sources:

1. `source skill`
2. `This mandatory artifact has not been generated yet`
3. `waiting on <skill-id> output`
4. `the analysis shows`
5. `the data reveals`
6. `source document`

These indicate process/meta framing instead of brand voice.

## Placeholder Markers (Hard Blockers)

Any doc containing one or more of these must be suppressed or quarantined by default:

- `Missing Mandatory Artifacts`
- `waiting on \``
- `_This mandatory artifact has not been generated yet._`
- `Readiness: In progress (0/`

## Source Scoring Model

Each source gets a quality score `0-100` using:

- weighted forbidden hits
- placeholder marker count
- list-heavy formatting penalty
- low-content penalty

Classification:

- `pass`: `>= 85`
- `warn`: `70-84.99`
- `fail`: `< 70`

## Publish Readiness Gate (Wave 7 Precondition)

Default gate target for quality publish runs:

- average source score `>= 85`
- `0` files classified as `fail`
- `0` placeholder-heavy files selected for upload

If any condition fails, Wave 7 must fail-fast with diagnostics and remediation hints.

## Scenario/Depth Guardrail

Before Wave 7, operators must run a preflight coverage report to confirm scenario/depth produced sufficient upstream content.

This explicitly prevents "markdown-only planning artifacts" from becoming the dominant source set.

## Evidence Requirements

For each run, persist:

- JSON quality report
- Markdown quality report
- source selection report with skip reasons
- gate pass/fail result in state and publish report

## Non-Goals

- Do not rewrite brand strategy content semantics in Phase 1.
- Do not block intentional debug-only profiles, but require explicit operator override.
