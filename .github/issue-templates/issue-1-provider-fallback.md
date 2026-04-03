## Description

Integrate the new `ProviderFallbackChain` into the visual pipeline to enable automatic retry with alternative providers when the primary fails.

**Improvement:** +0.7 quality score points (7.1 → 7.8)  
**Impact:** 99.9% uptime for visual generation

## Background

Currently, if the primary image generation provider (e.g., FAL.AI) fails or is rate-limited, the entire visual pipeline fails. This requires manual intervention to switch providers.

The new `ProviderFallbackChain` automatically tries alternative providers in order:
1. fal (primary)
2. replicate
3. openrouter  
4. openai

## Implementation Files

**Created (experiments/):**
- ✅ `brandmint/core/providers/fallback_chain.py`
- ✅ `brandmint/core/providers/__init__.py` (updated)

**Need Updates:**
- `brandmint/pipeline/visual_backend.py`
- `brandmint/cli/report.py`
- `assets/brand-config-schema.yaml`
- `docs/providers.md`

## Tasks

### Core Integration
- [ ] Update `visual_backend.py` to use `ProviderFallbackChain`
- [ ] Add fallback attempt logging to execution reports
- [ ] Preserve provider metadata in `GenerationResult`
- [ ] Add fallback summary to visual asset metadata

### Configuration
- [ ] Add `fallback_order` field to brand-config schema
- [ ] Validate `fallback_order` format in config validator
- [ ] Update example configs with fallback_order
- [ ] Set sensible defaults when fallback_order not specified

### Documentation
- [ ] Update `docs/providers.md` with fallback examples
- [ ] Add migration guide to CHANGELOG
- [ ] Add integration examples to experiments/INTEGRATION_EXAMPLES.md
- [ ] Update README features section

## Acceptance Criteria

- [ ] Visual backend uses `ProviderFallbackChain` for all generations
- [ ] Fallback attempts are logged in execution reports
- [ ] Config validation rejects invalid `fallback_order`
- [ ] Documentation is complete and accurate
- [ ] **Manual test:** Unset `FAL_KEY`, verify fallback to Replicate succeeds
- [ ] **Manual test:** Check logs show attempt details

## Testing Strategy

```bash
# Test 1: Primary provider works (no fallback)
export FAL_KEY="fal_..."
bm visual --config test.yaml --asset 2A
# Expected: Uses FAL, no fallback

# Test 2: Primary fails, fallback succeeds
unset FAL_KEY
export REPLICATE_API_TOKEN="r8_..."
bm visual --config test.yaml --asset 2A
# Expected: Skips FAL, uses Replicate

# Test 3: Check logs for attempt details
tail -f logs/brandmint.log
# Expected: Shows provider attempts
```

## Integration Example

```python
# Before:
provider = get_provider(self.config.get("generation", {}).get("provider", "fal"))
result = provider.generate(...)

# After:
from brandmint.core.providers import ProviderFallbackChain
chain = ProviderFallbackChain(self.config)
result = chain.generate_with_fallback(...)
summary = chain.get_attempt_summary()
```

## Dependencies

None (can be done in parallel with Issue #2)

## Labels

`enhancement`, `priority-high`, `v4.4.1`, `resilience`

## Estimated Effort

1 day
