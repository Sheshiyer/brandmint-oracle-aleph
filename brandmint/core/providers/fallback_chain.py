"""
Provider fallback chain orchestrator.

Automatically retries image generation with alternative providers when
the primary provider fails, based on configurable fallback order.

Example usage:
    chain = ProviderFallbackChain(config)
    result = chain.generate_with_fallback(
        prompt="A brand logo...",
        model="flux-2-pro",
        output_path="logo.png",
    )
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import ImageProvider, GenerationResult, ProviderName

logger = logging.getLogger(__name__)


class ProviderFallbackChain:
    """Orchestrates provider fallback with automatic retry.
    
    Tries providers in order until one succeeds or all fail.
    Respects provider capabilities (e.g., image reference support).
    """
    
    DEFAULT_FALLBACK_ORDER = [
        ProviderName.FAL,
        ProviderName.REPLICATE,
        ProviderName.OPENROUTER,
        ProviderName.OPENAI,
    ]
    
    def __init__(
        self,
        config: dict,
        fallback_order: Optional[List[str]] = None,
        skip_unavailable: bool = True,
    ):
        """Initialize fallback chain.
        
        Args:
            config: Brand configuration dict
            fallback_order: Ordered list of provider names to try.
                           Defaults to: fal → replicate → openrouter → openai
            skip_unavailable: If True, skip providers that aren't configured
        """
        self.config = config
        self.skip_unavailable = skip_unavailable
        
        # Get fallback order from config or use default
        configured_order = (
            config.get("generation", {})
            .get("fallback_order", [])
        )
        self.fallback_order = (
            [ProviderName(p) for p in configured_order]
            if configured_order
            else self.DEFAULT_FALLBACK_ORDER
        )
        
        # Track provider attempts for reporting
        self.attempt_log: List[Dict[str, Any]] = []
    
    def _get_available_providers(
        self,
        require_image_reference: bool = False,
    ) -> List[ImageProvider]:
        """Get list of available providers in fallback order.
        
        Args:
            require_image_reference: If True, only return providers that
                                     support image-to-image generation
        
        Returns:
            List of provider instances ready to use
        """
        from . import get_provider

        providers = []
        
        for provider_name in self.fallback_order:
            try:
                provider = get_provider(str(provider_name))
                
                # Skip if provider is not configured
                if self.skip_unavailable and not provider.is_available():
                    logger.debug(
                        f"Skipping {provider.display_name}: not configured"
                    )
                    continue
                
                # Skip if image reference is required but not supported
                if require_image_reference and not provider.supports_image_reference():
                    logger.debug(
                        f"Skipping {provider.display_name}: "
                        "image reference not supported"
                    )
                    continue
                
                providers.append(provider)
                
            except Exception as e:
                logger.warning(
                    f"Failed to initialize provider {provider_name}: {e}"
                )
        
        return providers
    
    def generate_with_fallback(
        self,
        prompt: str,
        model: str,
        output_path: str,
        width: int = 1024,
        height: int = 1024,
        image_url: Optional[str] = None,
        negative_prompt: str = "",
        guidance_scale: float = 7.5,
        num_steps: int = 50,
        **kwargs: Any,
    ) -> GenerationResult:
        """Generate image with automatic provider fallback.
        
        Tries providers in order until one succeeds. If image_url is
        provided, only tries providers that support image references.
        
        Args:
            prompt: Text description of the image
            model: Logical model name (e.g., "flux-2-pro")
            output_path: Where to save the generated image
            width: Image width in pixels
            height: Image height in pixels
            image_url: Optional reference image for style transfer
            negative_prompt: Things to avoid
            guidance_scale: How closely to follow prompt
            num_steps: Number of diffusion steps
            **kwargs: Provider-specific parameters
        
        Returns:
            GenerationResult with success status and metadata
        """
        require_image_ref = bool(image_url)
        providers = self._get_available_providers(
            require_image_reference=require_image_ref
        )
        
        if not providers:
            error_msg = (
                "No available providers configured. "
                f"Required: {'image reference support' if require_image_ref else 'any provider'}. "
                f"Fallback order: {[str(p) for p in self.fallback_order]}"
            )
            logger.error(error_msg)
            return GenerationResult(
                success=False,
                error=error_msg,
                model_used=model,
                provider="fallback_chain",
            )
        
        logger.info(
            f"Trying {len(providers)} providers in order: "
            f"{[p.display_name for p in providers]}"
        )
        
        # Reset attempt log
        self.attempt_log = []
        
        # Try each provider in order
        for idx, provider in enumerate(providers):
            attempt_num = idx + 1
            is_last = attempt_num == len(providers)
            
            logger.info(
                f"[Attempt {attempt_num}/{len(providers)}] "
                f"Trying {provider.display_name}..."
            )
            
            try:
                result = provider.generate(
                    prompt=prompt,
                    model=model,
                    output_path=output_path,
                    width=width,
                    height=height,
                    image_url=image_url,
                    negative_prompt=negative_prompt,
                    guidance_scale=guidance_scale,
                    num_steps=num_steps,
                    **kwargs,
                )
                
                # Log the attempt
                self.attempt_log.append({
                    "provider": provider.display_name,
                    "success": result.success,
                    "error": result.error,
                    "model_used": result.model_used,
                })
                
                if result.success:
                    logger.info(
                        f"✓ {provider.display_name} succeeded "
                        f"(attempt {attempt_num}/{len(providers)})"
                    )
                    return result
                
                # Log failure and try next provider
                logger.warning(
                    f"✗ {provider.display_name} failed: {result.error}"
                )
                
                if is_last:
                    logger.error(
                        "All providers failed. "
                        f"Attempts: {len(self.attempt_log)}"
                    )
                
            except Exception as e:
                # Catch unexpected errors
                logger.error(
                    f"✗ {provider.display_name} raised exception: {e}",
                    exc_info=True,
                )
                
                self.attempt_log.append({
                    "provider": provider.display_name,
                    "success": False,
                    "error": str(e),
                    "model_used": model,
                })
                
                if is_last:
                    logger.error("All providers failed with exceptions")
        
        # All providers failed
        error_summary = "; ".join([
            f"{a['provider']}: {a['error']}"
            for a in self.attempt_log
        ])
        
        return GenerationResult(
            success=False,
            error=f"All {len(providers)} providers failed. {error_summary}",
            model_used=model,
            provider="fallback_chain",
            metadata={"attempt_log": self.attempt_log},
        )
    
    def get_attempt_summary(self) -> Dict[str, Any]:
        """Get summary of the last generation attempt.
        
        Returns:
            Dict with attempt count, success/failure breakdown
        """
        if not self.attempt_log:
            return {"attempts": 0, "succeeded": 0, "failed": 0}
        
        return {
            "attempts": len(self.attempt_log),
            "succeeded": sum(1 for a in self.attempt_log if a["success"]),
            "failed": sum(1 for a in self.attempt_log if not a["success"]),
            "providers_tried": [a["provider"] for a in self.attempt_log],
            "final_error": self.attempt_log[-1].get("error") if self.attempt_log[-1].get("error") else None,
        }
