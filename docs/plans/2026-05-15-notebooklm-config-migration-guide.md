# NotebookLM Config Migration Guide (Phase 1, Wave 2)

Date: `2026-05-15`
Task anchor: `P1-W2-SD-T08`

## Summary

NotebookLM configuration is now normalized around one canonical path:

- `publishing.notebooklm`

Legacy paths still work, but emit migration warnings and should be updated.

## Canonical Keys

```yaml
publishing:
  notebooklm:
    synthesize: true
    synthesis_model: anthropic/claude-3.5-haiku
    max_parallel_workers: 5
    inter_artifact_delay: 1.0
    reuse_policy: fresh-per-spec
    artifacts:
      disabled: []
      custom: []
```

## Legacy Keys (Still Supported)

1. Top-level:

```yaml
notebooklm:
  max_parallel_workers: 5
```

2. Publishing root:

```yaml
publishing:
  synthesize: true
  synthesis_model: anthropic/claude-3.5-haiku
```

## Precedence Rules

When both legacy and canonical keys are present:

1. Start with top-level `notebooklm` values.
2. Overlay `publishing.notebooklm` values (canonical wins).
3. For synthesis settings, `publishing.notebooklm.*` overrides `publishing.*`.

## Warnings You Will See

During Wave 7 publishing, you may see warnings like:

- `Top-level notebooklm config is deprecated...`
- `Publishing synthesis keys at publishing.{synthesize,synthesis_model} are legacy...`
- `NotebookLM config found in both notebooklm and publishing.notebooklm...`

These are informational in this phase and do not hard-fail execution.

## Operator Checklist

1. Move all NotebookLM keys under `publishing.notebooklm`.
2. Remove top-level `notebooklm` keys after confirming behavior parity.
3. Remove `publishing.synthesize` and `publishing.synthesis_model` once nested values are set.
4. Run a dry run and confirm no migration warnings remain.
