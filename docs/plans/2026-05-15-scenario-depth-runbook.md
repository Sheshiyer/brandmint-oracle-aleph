# Scenario/Depth Runbook for Publish-Quality NotebookLM Outputs

Date: `2026-05-15`
Task anchor: `P1-W3-SD-T12`

## Goal

Choose scenario and depth settings that produce a complete, high-signal source pack before Wave 7 publishing.

## Step 1: Run Coverage Preflight

```bash
python3 scripts/wave_coverage_preflight.py \
  --config /path/to/brand-config.yaml \
  --scenario <scenario-id> \
  --depth <depth> \
  --output docs/plans/<brand>-coverage-preflight.json
```

## Step 2: Evaluate Gate Conditions

Treat run as blocked for Wave 7 if:

1. `missing_mandatory_source_skills` is non-empty, or
2. waves `4-6` include empty execution waves.

## Step 3: Adjust Inputs

If blocked:

1. Move from `brand-genesis` to `custom-hybrid` (or campaign-capable scenario).
2. Keep depth at least `comprehensive` for publish-quality runs.
3. Confirm visual assets are not over-filtered by domain tags.

## Step 4: Re-run Preflight

Repeat until warnings are cleared or explicitly accepted for a diagnostic-only run.

## Step 5: Execute Launch

Use the validated scenario/depth values for non-interactive execution.

## Newsense Example

`brand-genesis + comprehensive` produced:

- missing mandatory source skills: `9`
- empty execution waves: `[4, 5, 6]`

Result: block Wave 7 for quality run; switch scenario/profile first.
