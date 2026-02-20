# NotebookLM Publisher

**Wave:** 7 (Publishing)
**Type:** Post-hook (no text skills or visual assets)
**Depends on:** Wave 6 (all brand outputs complete)

## What It Does

Transforms all brandmint pipeline outputs into a Google NotebookLM notebook
and generates 5 branded artifacts:

| Artifact | Type | Format | Est. Time |
|----------|------|--------|-----------|
| Brand Overview Deck | slide-deck | PDF | 5-15 min |
| Product Showcase Deck | slide-deck | PDF | 5-15 min |
| Audio Overview | audio | MP3 | 10-20 min |
| Brand Report | report | Markdown | 5-15 min |
| Mind Map | mind-map | JSON | <1 min |

## How It Works

1. **Source Building**: Reads `.brandmint/outputs/*.json` (16 skill outputs) and
   `brand-config.yaml`, converts them into 5 structured markdown documents
   optimised for NotebookLM processing

2. **Notebook Creation**: Creates a "{Brand} — Brand Intelligence" notebook
   in NotebookLM and uploads the 5 source documents

3. **Artifact Generation**: Generates artifacts with brand-specific instructions
   that inject colours, typography, voice/tone, and positioning data

4. **Parallel Execution**: Mind map first (instant), then decks + report in
   parallel (3 workers), then audio (sequential). Total ~25 min wall time.

5. **Download**: All artifacts downloaded to `deliverables/notebooklm/artifacts/`

## Prerequisites

```bash
pip install notebooklm-py    # or: pip install 'brandmint[publishing]'
notebooklm login             # Google OAuth — opens browser
```

## Usage

### Via pipeline (Wave 7)

```bash
bm launch --config brand-config.yaml --waves 1-7
```

### Standalone

```bash
bm publish notebooklm --config brand-config.yaml
bm publish notebooklm --config brand-config.yaml --dry-run
bm publish notebooklm --config brand-config.yaml --artifacts audio-overview,mind-map
bm publish notebooklm --config brand-config.yaml --force
```

## Output Structure

```
<brand-dir>/
  deliverables/
    notebooklm/
      sources/
        brand-foundation.md
        brand-strategy.md
        campaign-content.md
        communications-social.md
        visual-asset-catalog.md
      artifacts/
        brand-overview-deck.pdf
        product-showcase-deck.pdf
        brand-audio-overview.mp3
        brand-report.md
        brand-mind-map.json
      publish-report.json
```

## Idempotency

State is persisted at `.brandmint/notebooklm-state.json`. Re-running the
command skips already-completed steps (sources already indexed, artifacts
already downloaded). Use `--force` to start fresh.

## Source Groups

| Document | Skills | Purpose |
|----------|--------|---------|
| Brand Foundation | niche-validator, buyer-persona, competitor-analysis + config | Market, audience, brand definition |
| Brand Strategy | positioning, MDS, voice-and-tone, product description, visual identity | Strategy and identity |
| Campaign Content | campaign copy, video script, ads, press release | Marketing creative |
| Communications & Social | email sequences, social calendar, hooks, influencer, reviews | Comms and distribution |
| Visual Asset Catalog | Generated asset inventory | Visual system reference |
