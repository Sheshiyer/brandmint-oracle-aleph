# Scenario/Wave Coverage Contract (Phase 1, Wave 3)

Date: `2026-05-15`
Task anchors: `P1-W3-SA-T09`, `P1-W3-SB-T10`

## Purpose

Prevent Wave 7 publishing from running on weak upstream content plans caused by scenario/depth filtering.

## Required Preflight

Before `bm launch` for publish-quality runs, execute a coverage preflight that reports:

1. Planned text skill count
2. Planned visual asset count
3. Missing mandatory source skills
4. Empty execution waves
5. Blocking warnings

## Blocking Conditions

A run is considered high-risk for Wave 7 if either is true:

1. `missing_mandatory_source_skills` is non-empty
2. any core content wave (`4`, `5`, `6`) is in `empty_execution_waves`

## Newsense Validation Snapshot

From `docs/plans/2026-05-15-newsense-wave-coverage-preflight.json`:

- scenario: `brand-genesis`
- depth: `comprehensive`
- planned text skills: `7`
- planned visual assets: `2`
- missing mandatory source skills: `9`
- empty execution waves: `[4, 5, 6]`

Interpretation: this configuration predicts placeholder-heavy sources and poor NotebookLM artifact quality unless scenario/depth/profile is adjusted.

## Operator Guidance

Use this contract to choose one of:

1. switch scenario to one that includes campaign/email skills, or
2. use custom-hybrid with explicit required skill set, or
3. run in diagnostic mode and block Wave 7 until gaps are remediated.
