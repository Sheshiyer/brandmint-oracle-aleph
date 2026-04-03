# Integration Examples for New Optimizations

This document shows exactly how to integrate the new provider fallback chain and state validation into existing Brandmint code.

---

## 1. Visual Backend Integration

**File:** `brandmint/pipeline/visual_backend.py`

### Current Code (Before):
```python
def generate_asset(self, asset_id: str, prompt: str, **kwargs):
    provider_name = self.config.get("generation", {}).get("provider", "fal")
    provider = get_provider(provider_name)
    
    result = provider.generate(
        prompt=prompt,
        model=kwargs.get("model", "flux-2-pro"),
        output_path=output_path,
        **kwargs
    )
    
    if not result.success:
        logger.error(f"Generation failed: {result.error}")
        return None
    
    return result
```

### New Code (After):
```python
from brandmint.core.providers import ProviderFallbackChain

def generate_asset(self, asset_id: str, prompt: str, **kwargs):
    # Use fallback chain instead of single provider
    chain = ProviderFallbackChain(
        config=self.config,
        skip_unavailable=True,
    )
    
    result = chain.generate_with_fallback(
        prompt=prompt,
        model=kwargs.get("model", "flux-2-pro"),
        output_path=output_path,
        **kwargs
    )
    
    if not result.success:
        # Now we have detailed attempt log
        summary = chain.get_attempt_summary()
        logger.error(
            f"Generation failed after {summary['attempts']} attempts. "
            f"Providers tried: {summary['providers_tried']}"
        )
        return None
    
    # Log which provider succeeded
    logger.info(f"Generated with {result.provider}")
    return result
```

---

## 2. Executor State Management

**File:** `brandmint/pipeline/executor.py`

### Current Code (Before):
```python
def _load_or_create_state(self) -> ExecutionState:
    if self.state_path.is_file():
        try:
            return ExecutionState.from_dict(
                json.loads(self.state_path.read_text())
            )
        except (json.JSONDecodeError, OSError):
            pass
    
    # Return empty state
    return ExecutionState()

def _save_state(self) -> None:
    self.state_path.parent.mkdir(parents=True, exist_ok=True)
    self.state_path.write_text(
        json.dumps(self.state.to_dict(), indent=2)
    )
```

### New Code (After):
```python
from brandmint.models.state_validator import load_state_safe, save_state_safe

def _load_or_create_state(self) -> ExecutionState:
    # Safe load with auto-repair
    state_dict, was_repaired = load_state_safe(
        self.state_path,
        state_type="execution"
    )
    
    if was_repaired:
        self.console.print(
            "[yellow]⚠ State file was corrupted and auto-repaired[/yellow]"
        )
        self.console.print(
            f"  [dim]Backup saved to: {self.state_path.stem}.corrupted-*.json[/dim]"
        )
    
    return ExecutionState.from_dict(state_dict)

def _save_state(self) -> None:
    # Safe save with validation
    success = save_state_safe(
        self.state.to_dict(),
        self.state_path,
        state_type="execution"
    )
    
    if not success:
        self.console.print(
            "[red]✗ Failed to save state (validation failed)[/red]"
        )
```

---

## 3. NotebookLM Publisher State

**File:** `brandmint/publishing/notebooklm_publisher.py`

### Current Code (Before):
```python
def _load_state(path: Path) -> dict:
    if path.is_file():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}

def _save_state(state: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2))
```

### New Code (After):
```python
from brandmint.models.state_validator import load_state_safe, save_state_safe

def _load_state(path: Path) -> dict:
    state, was_repaired = load_state_safe(
        path,
        state_type="notebooklm"
    )
    
    if was_repaired:
        logger.warning("NotebookLM state was corrupted and repaired")
    
    return state

def _save_state(state: dict, path: Path) -> None:
    success = save_state_safe(
        state,
        path,
        state_type="notebooklm"
    )
    
    if not success:
        logger.error("Failed to save NotebookLM state (invalid format)")
```

---

## 4. Brand Config Fallback Order

**File:** `<brand-dir>/brand-config.yaml`

### Add Fallback Configuration:
```yaml
generation:
  provider: fal  # Primary provider
  
  # NEW: Fallback order when primary fails
  fallback_order:
    - fal
    - replicate
    - openrouter
    - openai
  
  # Existing settings
  seeds: 2
  batch_size: 4
```

**Note:** If `fallback_order` is not specified, the default order is used:
`fal → replicate → openrouter → openai`

---

## 5. Testing Corrupted State Recovery

### Manual Test:
```bash
# 1. Create a corrupted state file
cd <brand-dir>/.brandmint
echo '{"invalid": json}' > state.json

# 2. Run pipeline - should auto-repair
bm launch --config ../brand-config.yaml --waves 1 --non-interactive

# 3. Check for backup
ls -la state.corrupted-*.json

# 4. Verify repaired state
cat state.json | jq .
```

### Expected Output:
```
[yellow]⚠ State file was corrupted and auto-repaired[/yellow]
  Backup saved to: state.corrupted-20260402-143022.json
```

---

## 6. Testing Provider Fallback

### Simulate Provider Failure:
```bash
# 1. Unset primary provider API key
unset FAL_KEY

# 2. Set secondary providers
export REPLICATE_API_TOKEN="r8_..."
export OPENROUTER_API_KEY="sk-or-..."

# 3. Run visual generation
bm visual --config brand-config.yaml --asset 2A

# 4. Check logs for fallback attempts
tail -f logs/brandmint.log
```

### Expected Log Output:
```
[INFO] Trying 3 providers in order: ['FAL.AI', 'Replicate', 'OpenRouter']
[DEBUG] Skipping FAL.AI: not configured
[INFO] [Attempt 1/2] Trying Replicate...
[INFO] ✓ Replicate succeeded (attempt 1/2)
```

---

## 7. Error Message Comparison

### Before (Single Provider):
```
[ERROR] FAL API error 429: Rate limit exceeded
[ERROR] Generation failed
```

### After (Fallback Chain):
```
[WARN] [Attempt 1/4] Trying FAL.AI...
[WARN] ✗ FAL.AI failed: Rate limit exceeded
[INFO] [Attempt 2/4] Trying Replicate...
[INFO] ✓ Replicate succeeded (attempt 2/4)
[INFO] Generated with Replicate
```

---

## 8. State Validation Example

### Valid State:
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
  "completed_skills": ["niche-validator", "buyer-persona"],
  "failed_skills": [],
  "last_checkpoint": "2026-04-02T10:15:00"
}
```

### Corrupted State:
```json
{
  "scenario": "brand-genesis",
  "wave_states": "invalid",  // Should be object
  "completed_skills": "not-an-array",  // Should be array
  "missing_required": true
}
```

### Auto-Repaired State:
```json
{
  "scenario": "brand-genesis",
  "wave_states": {},
  "completed_skills": [],
  "failed_skills": [],
  "last_checkpoint": null
}
```

---

## 9. Migration Checklist

- [ ] Update `pipeline/executor.py` to use `load_state_safe` / `save_state_safe`
- [ ] Update `pipeline/visual_backend.py` to use `ProviderFallbackChain`
- [ ] Update `publishing/notebooklm_publisher.py` state functions
- [ ] Add `fallback_order` to example configs in `docs/`
- [ ] Test with corrupted state files
- [ ] Test with failed primary provider
- [ ] Update CLI help text to mention fallback
- [ ] Add fallback status to execution reports

---

## 10. Backward Compatibility

**Good news:** Both new features are backward compatible!

- **Provider fallback**: If no `fallback_order` is specified, uses default order
- **State validation**: Automatically repairs old state files on first load

No breaking changes to existing configurations or workflows.
