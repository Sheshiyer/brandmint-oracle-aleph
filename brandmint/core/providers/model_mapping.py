"""
Model mapping configuration for multi-provider support.

Maps Brandmint's logical model names to provider-specific model IDs.
Users can override these defaults in brand-config.yaml.
"""

from typing import Dict

# Brandmint logical model names used in ASSET_CATALOG
LOGICAL_MODELS = {
    "nano-banana-pro",  # Style anchor, image-reference capable
    "flux-2-pro",       # High quality general purpose
    "recraft-v3",       # Vector/illustration focused
}

# Default model mappings per provider
# Format: logical_model -> provider_model_id
MODEL_MAPPING: Dict[str, Dict[str, str]] = {
    "fal": {
        "nano-banana-pro": "fal-ai/nano-banana",
        "flux-2-pro": "fal-ai/flux-pro/v1.1",
        "flux-dev": "fal-ai/flux/dev",
        "recraft-v3": "fal-ai/recraft-v3",
    },
    "openrouter": {
        # OpenRouter uses standard model paths
        "nano-banana-pro": "black-forest-labs/flux-1.1-pro",
        "flux-2-pro": "black-forest-labs/flux-1.1-pro",
        "flux-dev": "black-forest-labs/flux-dev",
        "recraft-v3": "stabilityai/stable-diffusion-xl-base-1.0",
    },
    "openai": {
        # OpenAI only has DALL-E models
        "nano-banana-pro": "gpt-image-1",  # Best for style consistency
        "flux-2-pro": "dall-e-3",
        "flux-dev": "dall-e-3",
        "recraft-v3": "dall-e-3",
    },
    "replicate": {
        # Replicate model versions
        "nano-banana-pro": "black-forest-labs/flux-1.1-pro",
        "flux-2-pro": "black-forest-labs/flux-1.1-pro",
        "flux-dev": "black-forest-labs/flux-dev",
        "recraft-v3": "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
    },
}

# Provider capabilities
PROVIDER_CAPABILITIES = {
    "fal": {
        "supports_image_reference": True,  # Nano Banana Pro only
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
}

# Cost estimates per image (USD)
COST_ESTIMATES = {
    "fal": {
        "nano-banana-pro": 0.08,
        "flux-2-pro": 0.05,
        "flux-dev": 0.03,
        "recraft-v3": 0.04,
    },
    "openrouter": {
        "nano-banana-pro": 0.05,
        "flux-2-pro": 0.05,
        "flux-dev": 0.03,
        "recraft-v3": 0.04,
    },
    "openai": {
        "nano-banana-pro": 0.08,  # GPT-Image-1
        "flux-2-pro": 0.04,       # DALL-E 3 standard
        "flux-dev": 0.04,
        "recraft-v3": 0.04,
    },
    "replicate": {
        "nano-banana-pro": 0.05,
        "flux-2-pro": 0.05,
        "flux-dev": 0.03,
        "recraft-v3": 0.04,
    },
}


def get_model_id(provider: str, logical_model: str) -> str:
    """Get provider-specific model ID for a logical model name.
    
    Args:
        provider: Provider name (fal, openrouter, openai, replicate)
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
        # Fall back to flux-2-pro equivalent if unknown model
        return provider_models.get("flux-2-pro", list(provider_models.values())[0])
    
    return provider_models[logical_model]


def get_cost_estimate(provider: str, logical_model: str) -> float:
    """Get estimated cost per image for a provider/model combination."""
    if provider not in COST_ESTIMATES:
        return 0.05  # Default estimate
    return COST_ESTIMATES[provider].get(logical_model, 0.05)


def supports_image_reference(provider: str) -> bool:
    """Check if provider supports image-to-image style references."""
    return PROVIDER_CAPABILITIES.get(provider, {}).get("supports_image_reference", False)
