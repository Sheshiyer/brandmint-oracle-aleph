## Description

Replace all state file operations with safe load/save functions that validate and auto-repair corrupted state files.

**Improvement:** +0.7 quality score points (7.8 → 8.5)  
**Impact:** Zero crashes from state corruption

## Background

Pipeline state files (`.brandmint-state.json`, `notebooklm-state.json`) can become corrupted through:
- Manual editing
- Interrupted writes (disk full, process kill)
- File system issues
- Invalid JSON from bugs

Corrupted state currently crashes the pipeline with cryptic errors.

The new `StateValidator` module provides:
- JSON schema validation
- Auto-repair with data preservation
- Automatic backup before repair
- Safe load/save functions

## Implementation Files

**Created (experiments/):**
- ✅ `brandmint/models/state_validator.py`

**Need Updates:**
- `brandmint/pipeline/executor.py`
- `brandmint/publishing/notebooklm_publisher.py`
- `brandmint/cli/ui.py` (for repair notifications)

## Tasks

### Executor Integration
- [ ] Replace `_load_or_create_state()` with `load_state_safe()`
- [ ] Replace `_save_state()` with `save_state_safe()`
- [ ] Add CLI notification when state is repaired
- [ ] Add backup file path to notification
- [ ] Test with corrupted execution state

### NotebookLM Integration
- [ ] Replace `_load_state()` with `load_state_safe()`
- [ ] Replace `_save_state()` with `save_state_safe()`
- [ ] Add logging for state repair events
- [ ] Test with corrupted NotebookLM state

### Testing
- [ ] Create corrupted state test fixtures (invalid JSON, wrong types, missing fields)
- [ ] Write unit test: valid state passes validation
- [ ] Write unit test: corrupted state auto-repairs
- [ ] Write unit test: repaired state preserves valid data
- [ ] Write unit test: backup created before repair
- [ ] Write unit test: safe_save rejects invalid state
- [ ] Write integration test: full pipeline with corrupted state
- [ ] Test recovery message displayed to user

### Documentation
- [ ] Document state backup behavior
- [ ] Update state schema docs
- [ ] Add corruption recovery examples
- [ ] Update troubleshooting guide

## Acceptance Criteria

- [ ] Executor uses `load_state_safe` / `save_state_safe`
- [ ] NotebookLM publisher uses safe state functions
- [ ] Corrupted state auto-repairs with backup
- [ ] User sees clear notification when repair happens
- [ ] Backup file created with timestamp
- [ ] All unit tests pass
- [ ] **Manual test:** Corrupt state file, verify auto-repair

## Testing Strategy

```bash
# Test 1: Corrupt execution state
cd <brand-dir>/.brandmint
echo '{"invalid": json}' > state.json
bm launch --config ../brand-config.yaml --waves 1 --non-interactive
# Expected: Auto-repair, backup created, pipeline continues

# Test 2: Verify backup
ls -la state.corrupted-*.json
# Expected: Backup file exists with timestamp

# Test 3: Verify repaired state
cat state.json | jq .
# Expected: Valid minimal state structure
```

## State Schema Examples

### Valid State
```json
{
  "scenario": "brand-genesis",
  "wave_states": {
    "1": {
      "status": "completed",
      "started_at": "2026-04-02T10:00:00",
      "completed_at": "2026-04-02T10:15:00",
      "skill_outputs": {}
    }
  },
  "completed_skills": ["niche-validator"],
  "failed_skills": [],
  "last_checkpoint": "2026-04-02T10:15:00"
}
```

### Auto-Repaired State
```json
{
  "scenario": null,
  "wave_states": {},
  "completed_skills": [],
  "failed_skills": [],
  "last_checkpoint": null
}
```

## Integration Example

```python
# Before:
if self.state_path.is_file():
    try:
        state = json.loads(self.state_path.read_text())
    except:
        state = {}

# After:
from brandmint.models.state_validator import load_state_safe
state, was_repaired = load_state_safe(self.state_path, state_type="execution")
if was_repaired:
    self.console.print("[yellow]⚠ State file was corrupted and auto-repaired[/yellow]")
```

## Dependencies

None (can be done in parallel with Issue #1)

## Labels

`enhancement`, `priority-high`, `v4.4.1`, `resilience`

## Estimated Effort

1 day
