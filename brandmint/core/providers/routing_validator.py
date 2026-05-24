"""
Provider routing validation — enforces model-endpoint validation and runtime routing checks.

This module:
1. Validates provider-model combinations at runtime
2. Checks endpoint availability before generation
3. Enforces routing contracts (no silent fallbacks without logging)
4. Provides routing validation reports
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from .model_mapping import MODEL_MAPPING, get_model_id


@dataclass
class RoutingValidation:
    """Result of routing validation."""
    is_valid: bool
    provider: str
    model: str
    endpoint: str = ""
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class RoutingContract:
    """Defines valid provider-model-endpoint combinations."""
    provider: str
    supported_models: Set[str] = field(default_factory=set)
    default_model: str = ""
    requires_api_key: bool = True
    env_var: str = ""


# Define routing contracts for each provider
ROUTING_CONTRACTS: Dict[str, RoutingContract] = {
    "fal": RoutingContract(
        provider="fal",
        supported_models={"nano-banana-pro", "nano-banana-2", "gpt-image-2", "flux-2-pro", "flux-dev", "recraft-v3", "recraft-v4-pro"},
        default_model="nano-banana-pro",
        requires_api_key=True,
        env_var="FAL_KEY",
    ),
    "openrouter": RoutingContract(
        provider="openrouter",
        supported_models={"nano-banana-pro", "nano-banana-2", "gpt-image-2", "flux-2-pro", "flux-dev", "recraft-v3", "recraft-v4-pro"},
        default_model="nano-banana-pro",
        requires_api_key=True,
        env_var="OPENROUTER_API_KEY",
    ),
    "openai": RoutingContract(
        provider="openai",
        supported_models={"nano-banana-pro", "nano-banana-2", "gpt-image-2", "flux-2-pro", "flux-dev", "recraft-v3", "recraft-v4-pro"},
        default_model="gpt-image-2",
        requires_api_key=True,
        env_var="OPENAI_API_KEY",
    ),
    "replicate": RoutingContract(
        provider="replicate",
        supported_models={"nano-banana-pro", "nano-banana-2", "gpt-image-2", "flux-2-pro", "flux-dev", "recraft-v3", "recraft-v4-pro"},
        default_model="nano-banana-pro",
        requires_api_key=True,
        env_var="REPLICATE_API_TOKEN",
    ),
    "inference": RoutingContract(
        provider="inference",
        supported_models={"nano-banana-pro", "nano-banana-2", "gpt-image-2", "flux-2-pro", "flux-dev", "recraft-v3", "recraft-v4-pro"},
        default_model="nano-banana-pro",
        requires_api_key=True,
        env_var="INFERENCE_API_KEY",
    ),
    "gpt-image2": RoutingContract(
        provider="gpt-image2",
        supported_models={"nano-banana-pro", "nano-banana-2", "gpt-image-2", "flux-2-pro", "flux-dev", "recraft-v3", "recraft-v4-pro"},
        default_model="gpt-image-2",
        requires_api_key=False,  # Uses ChatGPT subscription
        env_var="",
    ),
}


def validate_routing(provider: str, model: str) -> RoutingValidation:
    """Validate a provider-model combination.

    Args:
        provider: Provider name
        model: Logical model name

    Returns:
        RoutingValidation with validity and any errors/warnings
    """
    errors = []
    warnings = []

    # Check provider exists
    if provider not in ROUTING_CONTRACTS:
        return RoutingValidation(
            is_valid=False,
            provider=provider,
            model=model,
            errors=[f"Unknown provider: {provider}"],
        )

    contract = ROUTING_CONTRACTS[provider]

    # Check model is supported
    if model not in contract.supported_models:
        errors.append(f"Model '{model}' not supported by provider '{provider}'")
        warnings.append(f"Supported models: {', '.join(sorted(contract.supported_models))}")

    # Check API key if required
    if contract.requires_api_key and contract.env_var:
        import os
        if not os.environ.get(contract.env_var):
            errors.append(f"Provider '{provider}' requires {contract.env_var} to be set")

    # Get endpoint
    endpoint = ""
    try:
        endpoint = get_model_id(provider, model)
    except ValueError:
        warnings.append(f"Could not resolve endpoint for {provider}/{model}")

    return RoutingValidation(
        is_valid=len(errors) == 0,
        provider=provider,
        model=model,
        endpoint=endpoint,
        errors=errors,
        warnings=warnings,
    )


def validate_routing_config(config: dict) -> List[RoutingValidation]:
    """Validate routing configuration from brand-config.yaml.

    Args:
        config: Brand config dict

    Returns:
        List of routing validations
    """
    validations = []
    generation = config.get("generation", {})

    # Check default model
    default_model = generation.get("default_model", "nano-banana-pro")
    provider = generation.get("provider", "fal")
    validations.append(validate_routing(provider, default_model))

    # Check model overrides
    model_overrides = generation.get("model_overrides", {})
    for asset_id, override_model in model_overrides.items():
        validations.append(validate_routing(provider, override_model))

    return validations
