"""
Model mapping configuration for multi-provider support.

Maps Brandmint's logical model names to provider-specific model IDs.
Users can override these defaults in brand-config.yaml.
"""

from typing import Dict

# Brandmint logical model names used in ASSET_CATALOG
LOGICAL_MODELS = {
    "nano-banana-pro",  # Style anchor, image-reference capable (Gemini 2.0 Flash Pro)
    "nano-banana-2",   # Fast generation + editing (Gemini 2.0 Flash fast tier)
    "gpt-image-2",     # Superior text rendering, design layouts (OpenAI GPT Image 2 via FAL)
    "flux-2-pro",      # High quality general purpose (Black Forest Labs)
    "flux-dev",        # Development/cheaper Flux variant
    "recraft-v3",      # Vector/illustration focused
    "recraft-v4-pro",  # Upgraded Recraft with better composition
}

# Default model mappings per provider
# Format: logical_model -> provider_model_id
MODEL_MAPPING: Dict[str, Dict[str, str]] = {
    "fal": {
        "nano-banana-pro": "fal-ai/nano-banana-pro",
        "nano-banana-2": "fal-ai/nano-banana-2",
        "gpt-image-2": "fal-ai/gpt-image-2",
        "flux-2-pro": "fal-ai/flux-2-pro",
        "flux-dev": "fal-ai/flux/dev",
        "recraft-v3": "fal-ai/recraft/v3/text-to-image",
        "recraft-v4-pro": "fal-ai/recraft/v4/pro/text-to-image",
    },
    "openrouter": {
        # OpenRouter uses standard model paths
        "nano-banana-pro": "black-forest-labs/flux-1.1-pro",
        "nano-banana-2": "black-forest-labs/flux-1.1-pro",
        "gpt-image-2": "openai/gpt-image-1",
        "flux-2-pro": "black-forest-labs/flux-1.1-pro",
        "flux-dev": "black-forest-labs/flux-dev",
        "recraft-v3": "stabilityai/stable-diffusion-xl-base-1.0",
        "recraft-v4-pro": "stabilityai/stable-diffusion-xl-base-1.0",
    },
    "openai": {
        # OpenAI native models (when not routed through FAL)
        "nano-banana-pro": "gpt-image-1",
        "nano-banana-2": "gpt-image-1",
        "gpt-image-2": "gpt-image-1",  # Will upgrade when OpenAI API adds gpt-image-2
        "flux-2-pro": "dall-e-3",
        "flux-dev": "dall-e-3",
        "recraft-v3": "dall-e-3",
        "recraft-v4-pro": "dall-e-3",
    },
    "replicate": {
        "nano-banana-pro": "black-forest-labs/flux-1.1-pro",
        "nano-banana-2": "black-forest-labs/flux-1.1-pro",
        "gpt-image-2": "black-forest-labs/flux-1.1-pro",  # Closest equivalent
        "flux-2-pro": "black-forest-labs/flux-1.1-pro",
        "flux-dev": "black-forest-labs/flux-dev",
        "recraft-v3": "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
        "recraft-v4-pro": "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
    },
    "inference": {
        # Inference apps are provider-routed via app + input model hints.
        # Override with INFERENCE_IMAGE_APP for production routing.
        "nano-banana-pro": "infsh-ai-image-generation",
        "nano-banana-2": "infsh-ai-image-generation",
        "gpt-image-2": "infsh-ai-image-generation",
        "flux-2-pro": "infsh-ai-image-generation",
        "flux-dev": "infsh-ai-image-generation",
        "recraft-v3": "infsh-ai-image-generation",
        "recraft-v4-pro": "infsh-ai-image-generation",
    },
    "gpt-image2": {
        # GPT Image 2 via local Codex CLI — always uses GPT Image 2 regardless of logical model
        "nano-banana-pro": "gpt-image-2",
        "nano-banana-2": "gpt-image-2",
        "gpt-image-2": "gpt-image-2",
        "flux-2-pro": "gpt-image-2",
        "flux-dev": "gpt-image-2",
        "recraft-v3": "gpt-image-2",
        "recraft-v4-pro": "gpt-image-2",
    },
}

# Provider capabilities
PROVIDER_CAPABILITIES = {
    "fal": {
        "supports_image_reference": True,  # Nano Banana Pro + GPT Image 2 only
        "supports_negative_prompt": True,
        "max_prompt_length": 1000,  # Recraft has 1000 char limit
        "supported_aspects": ["1:1", "16:9", "9:16", "3:4", "4:3"],
    },
    "openrouter": {
        "supports_image_reference": False,
        "supports_negative_prompt": True,
        "max_prompt_length": 4096,
        "supported_aspects": ["1:1", "16:9", "9:16", "3:4", "4:3"],
    },
    "openai": {
        "supports_image_reference": True,  # GPT-Image-1 supports it
        "supports_negative_prompt": False,  # DALL-E doesn't support negative
        "max_prompt_length": 4000,
        "supported_aspects": ["1:1", "16:9", "9:16"],  # Limited aspects
        "fixed_sizes": {  # DALL-E has fixed size options
            "1:1": (1024, 1024),
            "16:9": (1792, 1024),
            "9:16": (1024, 1792),
        },
    },
    "replicate": {
        "supports_image_reference": True,  # Some models support it
        "supports_negative_prompt": True,
        "max_prompt_length": 4096,
        "supported_aspects": ["1:1", "16:9", "9:16", "3:4", "4:3"],
    },
    "inference": {
        "supports_image_reference": True,
        "supports_negative_prompt": True,
        "max_prompt_length": 8192,
        "supported_aspects": ["1:1", "16:9", "9:16", "3:4", "4:3"],
    },
    "gpt-image2": {
        "supports_image_reference": True,  # Via --ref flag
        "supports_negative_prompt": False,
        "max_prompt_length": 2000,
        "supported_aspects": ["1:1", "16:9", "9:16", "3:4", "4:3"],
    },
}

# Model-specific capabilities (override provider defaults for specific models)
MODEL_CAPABILITIES = {
    "nano-banana-pro": {
        "supports_image_reference": True,
        "supports_negative_prompt": True,
        "supports_editing": True,
        "supports_multi_image": True,
        "description": "Gemini 2.0 Flash Pro — style anchor with image reference support",
    },
    "nano-banana-2": {
        "supports_image_reference": True,
        "supports_negative_prompt": True,
        "supports_editing": True,
        "supports_multi_image": True,
        "description": "Gemini 2.0 Flash fast tier — fast generation + editing",
    },
    "gpt-image-2": {
        "supports_image_reference": True,
        "supports_negative_prompt": False,
        "supports_editing": True,
        "supports_multi_image": True,
        "description": "OpenAI GPT Image 2 — superior text rendering and design layouts",
    },
    "flux-2-pro": {
        "supports_image_reference": False,
        "supports_negative_prompt": True,
        "supports_editing": False,
        "supports_multi_image": False,
        "description": "Black Forest Labs Flux 2 Pro — high quality general purpose",
    },
    "flux-dev": {
        "supports_image_reference": False,
        "supports_negative_prompt": True,
        "supports_editing": False,
        "supports_multi_image": False,
        "description": "Black Forest Labs Flux Dev — development/cheaper variant",
    },
    "recraft-v3": {
        "supports_image_reference": False,
        "supports_negative_prompt": True,
        "supports_editing": False,
        "supports_multi_image": False,
        "description": "Recraft V3 — vector/illustration focused",
    },
    "recraft-v4-pro": {
        "supports_image_reference": False,
        "supports_negative_prompt": True,
        "supports_editing": False,
        "supports_multi_image": False,
        "description": "Recraft V4 Pro — improved composition and design quality",
    },
}

# Cost estimates per image (USD)
COST_ESTIMATES = {
    "fal": {
        "nano-banana-pro": 0.08,
        "nano-banana-2": 0.06,
        "gpt-image-2": 0.10,
        "flux-2-pro": 0.05,
        "flux-dev": 0.03,
        "recraft-v3": 0.04,
        "recraft-v4-pro": 0.06,
    },
    "openrouter": {
        "nano-banana-pro": 0.05,
        "nano-banana-2": 0.04,
        "gpt-image-2": 0.08,
        "flux-2-pro": 0.05,
        "flux-dev": 0.03,
        "recraft-v3": 0.04,
        "recraft-v4-pro": 0.06,
    },
    "openai": {
        "nano-banana-pro": 0.08,  # GPT-Image-1
        "nano-banana-2": 0.06,
        "gpt-image-2": 0.10,
        "flux-2-pro": 0.04,       # DALL-E 3 standard
        "flux-dev": 0.04,
        "recraft-v3": 0.04,
        "recraft-v4-pro": 0.06,
    },
    "replicate": {
        "nano-banana-pro": 0.05,
        "nano-banana-2": 0.04,
        "gpt-image-2": 0.06,
        "flux-2-pro": 0.05,
        "flux-dev": 0.03,
        "recraft-v3": 0.04,
        "recraft-v4-pro": 0.06,
    },
    "inference": {
        "nano-banana-pro": 0.05,
        "nano-banana-2": 0.04,
        "gpt-image-2": 0.06,
        "flux-2-pro": 0.05,
        "flux-dev": 0.04,
        "recraft-v3": 0.05,
        "recraft-v4-pro": 0.06,
    },
    "gpt-image2": {
        # GPT Image 2 is covered by ChatGPT subscription — $0 per image
        "nano-banana-pro": 0.0,
        "nano-banana-2": 0.0,
        "gpt-image-2": 0.0,
        "flux-2-pro": 0.0,
        "flux-dev": 0.0,
        "recraft-v3": 0.0,
        "recraft-v4-pro": 0.0,
    },
}


def get_model_id(provider: str, logical_model: str) -> str:
    """Get provider-specific model ID for a logical model name.
    
    Args:
        provider: Provider name (fal, inference, openrouter, openai, replicate)
        logical_model: Brandmint logical model name
        
    Returns:
        Provider-specific model identifier
        
    Raises:
        ValueError: If provider or model is unknown
    """
    if provider not in MODEL_MAPPING:
        raise ValueError(f"Unknown provider: {provider}")
    
    provider_models = MODEL_MAPPING[provider]
    if logical_model not in provider_models:
        # Fall back to nano-banana-pro equivalent if unknown model
        return provider_models.get("nano-banana-pro", list(provider_models.values())[0])
    
    return provider_models[logical_model]


def get_cost_estimate(provider: str, logical_model: str) -> float:
    """Get estimated cost per image for a provider/model combination."""
    if provider not in COST_ESTIMATES:
        return 0.05  # Default estimate
    return COST_ESTIMATES[provider].get(logical_model, 0.05)


def supports_image_reference(provider: str) -> bool:
    """Check if provider supports image-to-image style references."""
    return PROVIDER_CAPABILITIES.get(provider, {}).get("supports_image_reference", False)


def get_model_capabilities(logical_model: str) -> dict:
    """Get capabilities for a specific logical model."""
    return MODEL_CAPABILITIES.get(logical_model, {
        "supports_image_reference": False,
        "supports_negative_prompt": True,
        "supports_editing": False,
        "supports_multi_image": False,
        "description": "Unknown model",
    })


def resolve_model(asset_id: str, logical_model: str, config: dict) -> str:
    """Resolve the effective model for an asset, checking config overrides.

    Priority order:
    1. config.generation.model_overrides[asset_id] (per-asset override)
    2. config.generation.default_model (brand-wide default)
    3. logical_model (from asset registry)

    Args:
        asset_id: Asset ID like "2A", "3B", etc.
        logical_model: Default model from asset registry or code.
        config: Brand config dict.

    Returns:
        Effective logical model name.
    """
    gen = config.get("generation", {})
    model_overrides = gen.get("model_overrides", {})
    default_model = gen.get("default_model", "nano-banana-pro")

    # Priority: per-asset override → brand default → asset registry default
    effective = model_overrides.get(asset_id, default_model)
    if not effective:
        effective = logical_model

    return effective
