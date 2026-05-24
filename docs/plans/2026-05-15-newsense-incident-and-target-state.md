# Newsense Wave 7 Source Incident + Target State

Date: `2026-05-15`
Milestone: `NotebookLM Source Quality Hardening`
Task anchors: `P1-W1-SC-T03`, `P1-W1-SD-T04`

## Incident Summary

Newsense NotebookLM publish sources produced low-quality downstream artifacts because the uploaded source pack was dominated by process/meta language and incomplete placeholder documents.

Baseline evidence (`docs/plans/2026-05-15-newsense-source-quality-baseline.md`):

- 18 files scanned
- average score: `56.91`
- classification: `pass=3`, `warn=7`, `fail=8`
- forbidden hits: `40`
- placeholder markers: `25`

## Why It Happened

1. Scenario filtering selected a minimal skill set, leaving major downstream sections under-populated.
2. Kickstarter section documents were generated even when backing skill outputs were absent.
3. Source docs included explicit process labels (`Source skill`, `waiting on ... output`).
4. Curator uploaded these files because no quality gate blocked them pre-publish.
5. NotebookLM then synthesized artifacts from this low-signal input mix.

## User-Visible Failure Mode

Output looked like planning/process markdown instead of polished brand-native narrative and visual strategy artifacts.

## Target State (Definition of 100%)

For publish-quality runs, all of the following must be true before Wave 7 executes:

1. Average source quality score `>= 85`.
2. `0` source files classified as `fail`.
3. `0` placeholder-heavy docs in upload set.
4. `0` forbidden lexicon hits in selected upload docs.
5. Scenario/depth preflight confirms sufficient upstream content coverage.
6. Visual/FAL coverage checker confirms required assets are generated and valid.

## Operational Gate Behavior

When any target-state criterion fails:

- publishing must fail-fast,
- diagnostics must identify specific failing files/reasons,
- remediation guidance must be shown (`resume-from`, scenario switch, or policy override),
- state/report artifacts must persist the gate decision.

## Immediate Next Actions

1. Keep source-quality inspector in CI and local preflight.
2. Implement source suppression rules for missing-artifact documents.
3. Add source curation penalties for meta/placeholder-heavy docs.
4. Add Wave 7 precondition gate tied to objective metrics.
