## What's New in v4.0.0

### Wave 1: UX Polish & Resilience
- **Progress Spinners** - Visual feedback during API calls
- **Status Icons** - Standardized ○ ◐ ● ✗ ◌ system
- **ASCII Logo** - Branded version command
- **Graceful Interrupts** - Ctrl+C saves state for resume
- **Config Validation** - Required fields checked on load
- **Retry Logic** - Exponential backoff for API calls
- **Desktop Notifications** - macOS/Linux alerts on completion

### Wave 2: Performance & Observability
- **Structured Logging** - `--verbose/-v`, `--debug`, `--quiet` flags
- **Execution Reports** - `bm report --format markdown|json|html`
- **Prompt Caching** - Skip regeneration if unchanged
- **Parallel Batches** - ThreadPoolExecutor for visual assets
- **Cost Tracking** - Estimated vs actual with variance display

### Wave 3: Documentation & Advanced Features
- **Cache CLI** - `bm cache stats`, `bm cache clear`
- **Force Regeneration** - `bm visual execute --force`
- **Webhook Notifications** - Slack/Discord on completion
- **Budget Gates** - `--max-cost 5.00` aborts if exceeded
- **Resume Support** - `--resume-from 3` continues from wave

### Documentation
- Website: https://brandmint-openclaw.vercel.app
- 44 skills across 9 categories
- FAL.AI/Nano Banana visual pipeline
