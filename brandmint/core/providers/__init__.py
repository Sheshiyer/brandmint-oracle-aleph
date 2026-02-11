"""
Brandmint Image Provider Factory.

Multi-provider abstraction layer for image generation.
Supports FAL.AI (default), OpenRouter, OpenAI, and Replicate.

Usage:
    from brandmint.core.providers import get_provider, get_available_providers
    
    # Get default provider (FAL.AI or first available)
    provider = get_provider()
    
    # Get specific provider
    provider = get_provider("openrouter")
    
    # Generate with fallback
    result = generate_with_fallback(
        prompt="...",
        model="flux-2-pro",
        output_path="output.png",
        fallback_chain=["fal", "openrouter", "replicate"],
    )
"""

import os
from typing import Optional, List, Dict, Type

from .base import ImageProvider, GenerationResult, ProviderName
from .fal_provider import FalProvider
from .openrouter_provider import OpenRouterProvider
from .openai_provider import OpenAIProvider
from .replicate_provider import ReplicateProvider
from .model_mapping import (
    get_model_id,
    get_cost_estimate,
    supports_image_reference,
    MODEL_MAPPING,
    PROVIDER_CAPABILITIES,
    COST_ESTIMATES,
)

__all__ = [
    # Base classes
    "ImageProvider",
    "GenerationResult",
    "ProviderName",
    # Provider implementations
    "FalProvider",
    "OpenRouterProvider", 
    "OpenAIProvider",
    "ReplicateProvider",
    # Factory functions
    "get_provider",
    "get_available_providers",
    "generate_with_fallback",
    # Mapping utilities
    "get_model_id",
    "get_cost_estimate",
    "supports_image_reference",
    "MODEL_MAPPING",
    "PROVIDER_CAPABILITIES",
    "COST_ESTIMATES",
]

# Provider registry
PROVIDERS: Dict[str, Type[ImageProvider]] = {
    "fal": FalProvider,
    "openrouter": OpenRouterProvider,
    "openai": OpenAIProvider,
    "replicate": ReplicateProvider,
}

# Default fallback order
DEFAULT_FALLBACK_CHAIN = ["fal", "openrouter", "replicate", "openai"]


def get_provider(name: Optional[str] = None) -> ImageProvider:
    """Get an image provider instance by name.
    
    Args:
        name: Provider name ("fal", "openrouter", "openai", "replicate").
              If None or "auto", returns first available provider.
              
    Returns:
        ImageProvider instance
        
    Raises:
        ValueError: If provider name is unknown or unavailable
    """
    if name is None or name == "auto":
        # Check IMAGE_PROVIDER env var first
        env_provider = os.environ.get("IMAGE_PROVIDER", "").lower()
        if env_provider and env_provider in PROVIDERS:
            provider = PROVIDERS[env_provider]()
            if provider.is_available():
                return provider
        
        # Fall back to first available
        for provider_name in DEFAULT_FALLBACK_CHAIN:
            provider = PROVIDERS[provider_name]()
            if provider.is_available():
                return provider
        
        raise ValueError(
            "No image provider available. Set one of: "
            "FAL_KEY, OPENROUTER_API_KEY, OPENAI_API_KEY, or REPLICATE_API_TOKEN"
        )
    
    name = name.lower()
    if name not in PROVIDERS:
        raise ValueError(
            f"Unknown provider: {name}. "
            f"Available: {', '.join(PROVIDERS.keys())}"
        )
    
    provider = PROVIDERS[name]()
    if not provider.is_available():
        env_var = {
            "fal": "FAL_KEY",
            "openrouter": "OPENROUTER_API_KEY",
            "openai": "OPENAI_API_KEY",
            "replicate": "REPLICATE_API_TOKEN",
        }.get(name, "API_KEY")
        raise ValueError(f"Provider {name} requires {env_var} to be set")
    
    return provider


def get_available_providers() -> List[str]:
    """Get list of providers that are currently available (have API keys set).
    
    Returns:
        List of available provider names
    """
    available = []
    for name, provider_class in PROVIDERS.items():
        provider = provider_class()
        if provider.is_available():
            available.append(name)
    return available


def generate_with_fallback(
    prompt: str,
    model: str,
    output_path: str,
    fallback_chain: Optional[List[str]] = None,
    **kwargs,
) -> GenerationResult:
    """Generate an image with automatic provider fallback.
    
    Tries each provider in the fallback chain until one succeeds.
    
    Args:
        prompt: Image generation prompt
        model: Logical model name (e.g., "flux-2-pro")
        output_path: Where to save the generated image
        fallback_chain: List of provider names to try in order.
                        Defaults to DEFAULT_FALLBACK_CHAIN.
        **kwargs: Additional arguments passed to generate()
        
    Returns:
        GenerationResult from the first successful provider
    """
    if fallback_chain is None:
        fallback_chain = DEFAULT_FALLBACK_CHAIN
    
    errors = []
    
    for provider_name in fallback_chain:
        try:
            provider = get_provider(provider_name)
        except ValueError:
            continue  # Provider not available
        
        result = provider.generate(
            prompt=prompt,
            model=model,
            output_path=output_path,
            **kwargs,
        )
        
        if result.success:
            return result
        
        errors.append(f"{provider_name}: {result.error}")
    
    # All providers failed
    return GenerationResult(
        success=False,
        error=f"All providers failed: {'; '.join(errors)}",
        model_used=model,
        provider="fallback",
    )
