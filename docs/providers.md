# Image Provider Configuration

Brandmint supports multiple image generation providers. This allows you to choose the best provider for your workload and availability requirements.

## Supported Providers

| Provider | Models | Style Anchor Support |
|----------|--------|----------------------|
| **FAL.AI** (default) | Nano Banana Pro, Flux 2 Pro, Recraft V3 | ✅ Full |
| **Inference** | infsh-ai-image-generation (app-routed) | ✅ Full |
| **OpenRouter** | Flux 1.1 Pro, SDXL | ⚠️ Limited |
| **OpenAI** | DALL-E 3, GPT-Image-1 | ⚠️ Limited |
| **Replicate** | Flux 1.1 Pro, SDXL | ⚠️ Limited |

## Quick Setup

1. **Get an API key** from your chosen provider:
   - FAL.AI: https://fal.ai/dashboard/keys
   - OpenRouter: https://openrouter.ai/keys
   - OpenAI: https://platform.openai.com/api-keys
   - Replicate: https://replicate.com/account/api-tokens
   - Inference: https://app.inference.sh

2. **Set the environment variable** in your `.env` file:
   ```bash
   # Copy .env.example to .env
   cp .env.example .env
   
   # Add your key
   FAL_KEY=key_...
   ```

3. **Optionally set a default provider**:
   ```bash
   IMAGE_PROVIDER=fal  # or: inference, openrouter, openai, replicate
   ```

## Configuration

### Environment Variables

```bash
# Primary provider selection (auto | fal | inference | openrouter | openai | replicate)
IMAGE_PROVIDER=auto

# Provider API keys (only need one)
FAL_KEY=key_...
OPENROUTER_API_KEY=sk-or-...
OPENAI_API_KEY=sk-...
REPLICATE_API_TOKEN=r8_...
INFERENCE_API_KEY=inf_...
```

### Brand Config Override

You can also set the provider in your `brand-config.yaml`:

```yaml
generation:
  output_dir: generated
  provider: fal  # or: inference, openrouter, openai, replicate, auto
  visual_backend: scripts  # or: inference (writes asset-level inference scaffolds)
  inference_endpoint: https://api.inference.sh
  inference_rollout_mode: ring0  # ring0|ring1|ring2
  inference_skill_policy:
    # Image-generation skills only (inference scaffold backend)
    # Optional relative/absolute path (default ships in repo)
    allowlist_file: skills/external/inference-sh/normalized/allowlist.yaml
    fallback_to_scripts: true
    default:
      scaffold_skill_id: infsh-llm-models
      media_skill_id: infsh-ai-image-generation
    semantic_routing:
      enabled: true
      rules_file: config/inference-semantic-routing.v1.yaml
      domain_pack: ""  # optional override; auto-inferred from brand domain tags
      browser_assets: [APP-SCREENSHOT]
      browser_keywords: [screenshot, ui, interface, dashboard, app store]
    batch_overrides: {}
    asset_overrides:
      APP-SCREENSHOT:
        media_skill_id: infsh-agentic-browser
```

### Visual Backend Mode

`generation.visual_backend` controls *how* visual batches are executed:

- `scripts` (default): existing generated-script pipeline execution
- `inference`: writes per-asset Inference agent scaffolds + runbook files under:
  - `.brandmint/inference-agent-scaffolds/<batch>/`
  - `<asset>.json` (execution contract)
  - `<asset>.md` (agent prompt scaffold)
  - `runbook.json` (batch manifest)
  - Uses `INFERENCE_API_KEY` (or `generation.inference_api_key`) for authenticated execution paths.

## Model Mapping

When you specify a logical model (like `nano-banana-pro`), Brandmint maps it to the appropriate model on your chosen provider:

| Logical Model | FAL.AI | Inference | OpenRouter | OpenAI | Replicate |
|---------------|--------|-----------|------------|--------|-----------|
| `nano-banana-pro` | `fal-ai/nano-banana-pro` | `infsh-ai-image-generation`* | `black-forest-labs/flux-1.1-pro` | `gpt-image-1` | `black-forest-labs/flux-1.1-pro` |
| `flux-2-pro` | `fal-ai/flux-2-pro` | `infsh-ai-image-generation`* | `black-forest-labs/flux-1.1-pro` | `dall-e-3` | `black-forest-labs/flux-1.1-pro` |
| `recraft-v3` | `fal-ai/recraft/v3/text-to-image` | `infsh-ai-image-generation`* | `stabilityai/stable-diffusion-xl-base-1.0` | `dall-e-3` | `stability-ai/sdxl:...` |

\* Override app routing with `INFERENCE_IMAGE_APP` or `generation.inference_app`.

## Style Anchor Cascade

The **style anchor cascade** is Brandmint's key feature for visual consistency. It works by:

1. Generating the **2A Bento Grid** first (the "style anchor")
2. Using that image as a reference for all subsequent assets

**⚠️ Important:** Full style-anchor behavior is strongest on **FAL.AI** and **Inference** paths. Text-only or model-limited providers may reduce cascade fidelity, which means:

- Assets will still match your brand colors and typography
- But visual style consistency may be lower
- Consider using FAL.AI/Inference for the anchor batch, then switching providers for other assets if needed

## Provider-Specific Notes

### FAL.AI (Recommended)
- Best style anchor support (image references)
- Fastest queue times
- Recraft V3 produces actual SVG files
- **Best for:** Full brand generation with maximum consistency

### Inference
- Adapter-backed runtime execution for `generation.provider=inference`
- Supports app-level routing via `INFERENCE_IMAGE_APP`
- Works with both generated scripts and inference scaffold backend
- **Best for:** Inference-first production routing and app-based orchestration

### OpenRouter
- Unified API for multiple models
- Good fallback option
- No image reference support
- **Best for:** Users who want a single API key for multiple models

### OpenAI
- DALL-E 3 has fixed size options (1024², 1792x1024)
- Very creative interpretations
- GPT-Image-1 supports limited style references
- **Best for:** Creative variations, not strict brand consistency

### Replicate
- Pay-per-second pricing (can be cheaper for batch jobs)
- Good model selection
- Community models available
- **Best for:** Budget-conscious batch processing

## Fallback Chain

Brandmint currently has **two provider execution paths**:

1. **Core provider API** (`brandmint.core.providers.generate_with_fallback`)
   - Supports explicit fallback order and retry across providers.
2. **Launch visual pipeline** (`bm launch` -> generated scripts via `scripts/run_pipeline.py`)
   - Uses a single selected provider per run.
   - Does **not** automatically hop to the next provider on runtime failure.

Default core fallback order is:
1. FAL.AI
2. OpenRouter
3. Replicate
4. OpenAI
5. Inference

If you need fallback semantics today, use the core provider API path or rerun launch with a different provider.

## Imported Inference Skills (Image Generation Scope)

Imported skills from `inference-sh/skills` are used in Brandmint only for the inference visual scaffold path (`generation.visual_backend=inference`).

- Current equivalence mapping (image pipeline):
  - Brandmint prompt scaffolding role -> `infsh-llm-models`
  - Brandmint image generation role -> `infsh-ai-image-generation`
  - Brandmint app screenshot capture role -> `infsh-agentic-browser`

- Default allowlist file:
  - `skills/external/inference-sh/normalized/allowlist.yaml`
- Configure image skill mapping with:
  - `generation.inference_skill_policy.default`
  - `generation.inference_skill_policy.semantic_routing` (meta-semantic selector)
  - `generation.inference_skill_policy.batch_overrides`
  - `generation.inference_skill_policy.asset_overrides`

Safety behavior:
- If an override skill is not in the allowlist, Brandmint falls back to default image skill mapping.
- If an override skill is missing on disk, Brandmint falls back to default image skill mapping.
- Semantic routing rules are externalized in `config/inference-semantic-routing.v1.yaml` with domain packs.
- Rollout control is supported through `generation.inference_rollout_mode` (`ring0|ring1|ring2`).

Operational commands:
- `bm inference doctor --config <brand-config.yaml>`
- `bm inference route-test --config <brand-config.yaml> --batch products --assets APP-SCREENSHOT,3A`
- `bm visual diff --left <runbook-a.json> --right <runbook-b.json>`
- `bm visual contract-verify --runbook <runbook.json>`

## Programmatic Usage

```python
from brandmint.core.providers import get_provider, generate_with_fallback

# Get specific provider
provider = get_provider("openrouter")
result = provider.generate(
    prompt="A brand logo...",
    model="flux-2-pro",
    output_path="output.png",
)

# Or use automatic fallback
result = generate_with_fallback(
    prompt="A brand logo...",
    model="flux-2-pro",
    output_path="output.png",
    fallback_chain=["fal", "openrouter", "replicate", "openai", "inference"],
)
```
