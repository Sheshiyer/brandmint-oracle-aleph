# Image Provider Configuration

Brandmint supports multiple image generation providers. This allows you to choose the best provider for your needs, budget, and availability.

## Supported Providers

| Provider | Models | Style Anchor Support | Cost (per image) |
|----------|--------|---------------------|------------------|
| **FAL.AI** (default) | Nano Banana Pro, Flux 2 Pro, Recraft V3 | ✅ Yes | $0.04-0.08 |
| **OpenRouter** | Flux 1.1 Pro, SDXL | ❌ No | $0.03-0.05 |
| **OpenAI** | DALL-E 3, GPT-Image-1 | ⚠️ Limited | $0.04-0.08 |
| **Replicate** | Flux 1.1 Pro, SDXL | ⚠️ Limited | $0.03-0.05 |

## Quick Setup

1. **Get an API key** from your chosen provider:
   - FAL.AI: https://fal.ai/dashboard/keys
   - OpenRouter: https://openrouter.ai/keys
   - OpenAI: https://platform.openai.com/api-keys
   - Replicate: https://replicate.com/account/api-tokens

2. **Set the environment variable** in your `.env` file:
   ```bash
   # Copy .env.example to .env
   cp .env.example .env
   
   # Add your key
   FAL_KEY=key_...
   ```

3. **Optionally set a default provider**:
   ```bash
   IMAGE_PROVIDER=fal  # or: openrouter, openai, replicate
   ```

## Configuration

### Environment Variables

```bash
# Primary provider selection (auto | fal | openrouter | openai | replicate)
IMAGE_PROVIDER=auto

# Provider API keys (only need one)
FAL_KEY=key_...
OPENROUTER_API_KEY=sk-or-...
OPENAI_API_KEY=sk-...
REPLICATE_API_TOKEN=r8_...
```

### Brand Config Override

You can also set the provider in your `brand-config.yaml`:

```yaml
generation:
  output_dir: generated
  provider: fal  # or: openrouter, openai, replicate, auto
```

## Model Mapping

When you specify a logical model (like `nano-banana-pro`), Brandmint maps it to the appropriate model on your chosen provider:

| Logical Model | FAL.AI | OpenRouter | OpenAI | Replicate |
|---------------|--------|------------|--------|-----------|
| `nano-banana-pro` | fal-ai/nano-banana | flux-1.1-pro | gpt-image-1 | flux-1.1-pro |
| `flux-2-pro` | fal-ai/flux-pro/v1.1 | flux-1.1-pro | dall-e-3 | flux-1.1-pro |
| `recraft-v3` | fal-ai/recraft-v3 | sdxl | dall-e-3 | sdxl |

## Style Anchor Cascade

The **style anchor cascade** is Brandmint's key feature for visual consistency. It works by:

1. Generating the **2A Bento Grid** first (the "style anchor")
2. Using that image as a reference for all subsequent assets

**⚠️ Important:** Only **FAL.AI's Nano Banana Pro** fully supports image references. Other providers generate with text-only prompts, which means:

- Assets will still match your brand colors and typography
- But visual style consistency may be lower
- Consider using FAL.AI for the anchor batch, then switching providers for other assets

## Provider-Specific Notes

### FAL.AI (Recommended)
- Best style anchor support (image references)
- Fastest queue times
- Recraft V3 produces actual SVG files
- **Best for:** Full brand generation with maximum consistency

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

When `IMAGE_PROVIDER=auto`, Brandmint tries providers in this order:
1. FAL.AI
2. OpenRouter
3. Replicate
4. OpenAI

If a provider fails, it automatically tries the next one.

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
    fallback_chain=["fal", "openrouter", "replicate"],
)
```

## Cost Estimation

Run a preview to see estimated costs before generating:

```bash
python scripts/run_pipeline.py preview --config ./brand-config.yaml --json
```

This shows:
- Number of assets per model
- Cost per provider
- Recommended provider based on your config
