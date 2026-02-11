# Brandmint Architecture Improvements

**Created:** 2026-02-11  
**Status:** ✅ COMPLETED (Wave 1-3)  
**Total Items:** 21 (21 done)  

---

## Wave 1: Quick Wins & Foundation (Est. 6 hours) ✅ COMPLETED

Focus on immediate UX polish and foundational improvements that unblock Wave 2.

### Phase 1A: Visual Polish (2 hours) ✅ COMPLETED

- [x] **1. Live Progress Spinners for API Calls**
  - File: `brandmint/cli/spinners.py` (NEW)
  - Deps: `rich.progress`
  - Description: Add spinner/progress bar during 2-8s API waits
  - Effort: 1hr
  ```python
  # Key components:
  # - SpinnerColumn("dots12")
  # - BarColumn with brand colors
  # - TimeElapsedColumn
  ```

- [x] **12. ASCII Art Logo for Version**
  - File: `brandmint/cli/app.py`
  - Description: Replace plain `bm version` with branded ASCII banner
  - Effort: 15min

- [x] **13. Standardized Status Icons**
  - File: `brandmint/cli/icons.py` (NEW)
  - Description: Unify `v`, `x`, `o` into consistent icon system
  - Effort: 30min
  ```python
  class Icons:
      PENDING = "○"
      IN_PROGRESS = "◐"
      COMPLETED = "●"
      FAILED = "✗"
      SKIPPED = "◌"
  ```

- [x] **3. Animated Brand Banner**
  - File: `brandmint/cli/ui.py`
  - Description: Typing effect reveal for premium feel
  - Effort: 30min

### Phase 1B: Resilience & Safety (2.5 hours) ✅ COMPLETED

- [x] **5. Graceful Interrupt Handling**
  - File: `brandmint/pipeline/executor.py`
  - Description: Catch Ctrl+C, save state, clean exit
  - Effort: 30min

- [x] **6. Config Validation on Load**
  - File: `brandmint/models/validation.py`
  - Description: Validate required fields before execution
  - Effort: 1hr
  ```python
  required_fields = [
      "brand.name",
      "brand.domain_tags", 
      "theme.palette",
      "execution_context.depth_level"
  ]
  ```

- [x] **4. Retry Logic with Exponential Backoff**
  - File: `brandmint/core/providers/base.py`
  - Description: Auto-retry failed API calls (3 attempts, 1s → 2s → 4s)
  - Effort: 1hr

### Phase 1C: UX Finishing Touches (1.5 hours) ✅ COMPLETED

- [x] **11. Completion Notification (macOS)**
  - File: `brandmint/cli/notifications.py` (NEW)
  - Description: System notification when pipeline completes
  - Effort: 30min

- [x] **2. Wave Progress Bar**
  - File: `brandmint/pipeline/executor.py`
  - Description: Visual progress bar in `execute()` loop
  - Effort: 30min

- [x] **15. Dry-Run Cost Preview Table**
  - File: `brandmint/cli/ui.py`
  - Description: Detailed per-asset cost breakdown in `--dry-run`
  - Effort: 30min

---

## Wave 2: Performance & Observability (Est. 7 hours) ✅ COMPLETED

Focus on performance optimizations, caching, and operational visibility.

### Phase 2A: Observability (2 hours) ✅ COMPLETED

- [x] **7. Structured Logging with Levels**
  - File: `brandmint/cli/logging.py` (NEW)
  - Description: Add `--verbose/-v` flag, RichHandler, proper log levels
  - Effort: 1hr
  ```python
  # Add to pyproject.toml CLI:
  # --verbose/-v flag on all commands
  ```

- [x] **8. Cost Tracking Per Session**
  - File: `brandmint/pipeline/executor.py`
  - Description: Track actual vs estimated costs, show running total
  - Effort: 30min

- [x] **14. Summary Report Export**
  - File: `brandmint/cli/report.py` (NEW)
  - Description: `bm report --format markdown|json|html`
  - Effort: 1hr

### Phase 2B: Performance (5 hours) ✅ COMPLETED

- [x] **9. Asset Hash Caching**
  - File: `brandmint/core/cache.py` (NEW)
  - Description: Skip regeneration if prompt+model+seed unchanged
  - Effort: 2hr
  ```python
  # Cache key: sha256(prompt|model|seed)[:12]
  # Add --force flag to bypass cache
  ```

- [x] **10. Parallel Batch Execution**
  - File: `brandmint/pipeline/executor.py`
  - Description: Run `identity`, `products`, `photography` batches concurrently
  - Effort: 2hr
  - Deps: Requires #9 (caching) to avoid duplicate work
  ```python
  from concurrent.futures import ThreadPoolExecutor, as_completed
  # max_workers=3 for non-anchor batches
  ```

---

## Wave 3: Documentation & Advanced Features (Est. 3 hours) ✅ COMPLETED

### Phase 3B: Documentation & Polish (1.5 hours) ✅ COMPLETED

- [x] **16. Update SKILL.md with new CLI features**
  - File: `SKILL.md`
  - Description: Add `--verbose`, `--quiet`, `report`, `cache` commands
  - Effort: 30min

- [x] **17. Add `bm cache` subcommand**
  - File: `brandmint/cli/app.py`
  - Description: `bm cache stats`, `bm cache clear`, `bm cache clear --expired`
  - Effort: 30min

- [x] **18. Add `--force` flag to visual execute**
  - File: `brandmint/cli/app.py`, `brandmint/cli/visual.py`
  - Description: Bypass cache, regenerate all assets
  - Effort: 15min

### Phase 3C: Advanced Features (1.5 hours) ✅ COMPLETED

- [x] **19. Webhook notifications**
  - File: `brandmint/cli/notifications.py`
  - Description: POST to Slack/Discord on completion via `--webhook` flag
  - Effort: 45min

- [x] **20. Cost budgets**
  - File: `brandmint/cli/launch.py`
  - Description: `--max-cost $5.00` abort if estimated cost exceeds budget
  - Effort: 15min

- [x] **21. Resume from specific wave**
  - File: `brandmint/cli/launch.py`
  - Description: `--resume-from 3` to continue from a specific wave
  - Effort: 15min

---

## New Files Summary

| File | Wave | Phase | Purpose |
|------|------|-------|---------|
| `brandmint/cli/spinners.py` | 1 | 1A | Progress indicators |
| `brandmint/cli/icons.py` | 1 | 1A | Standardized status icons |
| `brandmint/cli/notifications.py` | 1 | 1C | OS notifications |
| `brandmint/cli/logging.py` | 2 | 2A | Structured logging |
| `brandmint/cli/report.py` | 2 | 2A | Execution reports |
| `brandmint/core/cache.py` | 2 | 2B | Prompt hash caching |

---

## Modified Files Summary

| File | Items |
|------|-------|
| `brandmint/cli/app.py` | #12 (logo), #14 (report cmd), verbose flags, cache CLI, #18 |
| `brandmint/cli/ui.py` | #3, #13 (import), #15 |
| `brandmint/cli/launch.py` | #20 (cost budget), #21 (resume-from), webhook |
| `brandmint/cli/visual.py` | #18 (--force flag) |
| `brandmint/cli/notifications.py` | #19 (webhooks) |
| `brandmint/pipeline/executor.py` | #2, #5, #8, #10 (cost tracking, parallel exec) |
| `brandmint/core/providers/base.py` | #4 |
| `brandmint/models/validation.py` | #6 |
| `SKILL.md` | #16 (CLI docs update) |

---

## Dependency Graph

```
Wave 1 (no deps)
  ├── Phase 1A: Icons, Spinners, Banner, ASCII
  ├── Phase 1B: Interrupt, Validation, Retry
  └── Phase 1C: Notification, Progress Bar, Cost Table

Wave 2 (depends on Wave 1)
  ├── Phase 2A: Logging, Cost Tracking, Reports
  └── Phase 2B: Caching (#9) → Parallel Execution (#10)

Wave 3 (depends on Wave 2)
  ├── Phase 3B: SKILL.md update, cache CLI, --force flag
  └── Phase 3C: Webhooks, Cost budgets, Resume from wave
```

---

## Execution Checklist

### Before Wave 1
- [x] Create feature branch: `git checkout -b feat/architecture-improvements`
- [ ] Ensure tests pass: `pytest`

### After Wave 1
- [x] Run full pipeline with new UI: `bm launch --config brands/test/brand-config.yaml --dry-run`
- [x] Verify Ctrl+C handling
- [x] Test retry logic with network disconnect
- [ ] Commit: `git commit -m "feat: Wave 1 - UX polish, resilience, safety"`

### After Wave 2
- [x] Benchmark parallel vs sequential execution
- [x] Test cache hit/miss scenarios
- [x] Verify `--verbose` logging output
- [x] Generate sample report: `bm report --config ... --format markdown`
- [ ] Commit: `git commit -m "feat: Wave 2 - Performance, caching, observability"`

### After Wave 3
- [x] Test `bm cache stats` and `bm cache clear`
- [x] Test `bm visual execute --force`
- [x] Test `bm launch --max-cost 5.00`
- [x] Test `bm launch --resume-from 3`
- [x] Test webhook notifications with Slack/Discord URL
- [ ] Commit: `git commit -m "feat: Wave 3 - Docs, cache CLI, webhooks, budgets"`

---

## Notes

- **Testing:** Add unit tests for new modules (cache.py, validation.py)
- **Docs:** Update SKILL.md with new CLI flags after Wave 2
- **Deps:** No new dependencies required (all use existing `rich`)
