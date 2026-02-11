"""
Base class for image generation providers.

All provider adapters inherit from ImageProvider and implement
the generate() method with provider-specific API calls.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum


class ProviderName(str, Enum):
    """Supported image generation providers."""
    FAL = "fal"
    OPENROUTER = "openrouter"
    OPENAI = "openai"
    REPLICATE = "replicate"


@dataclass
class GenerationResult:
    """Result of an image generation request."""
    success: bool
    image_url: Optional[str] = None
    local_path: Optional[str] = None
    model_used: str = ""
    provider: str = ""
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __bool__(self) -> bool:
        return self.success


class ImageProvider(ABC):
    """Abstract base class for image generation providers.
    
    Each provider adapter implements this interface to provide
    a unified API for image generation across different services.
    
    Example usage:
        provider = get_provider("fal")
        result = provider.generate(
            prompt="A brand logo...",
            model="flux-2-pro",
            width=1024,
            height=1024,
        )
        if result.success:
            print(f"Image saved to: {result.local_path}")
    """
    
    @property
    @abstractmethod
    def name(self) -> ProviderName:
        """Provider identifier."""
        pass
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable provider name for logging."""
        pass
    
    @abstractmethod
    def generate(
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
        """Generate an image from a prompt.
        
        Args:
            prompt: Text description of the image to generate.
            model: Logical model name (e.g., "flux-2-pro", "nano-banana-pro").
                   The provider maps this to its specific model ID.
            output_path: Local path to save the generated image.
            width: Image width in pixels.
            height: Image height in pixels.
            image_url: Optional reference image URL for style transfer.
                       Only supported by some providers (FAL's Nano Banana).
            negative_prompt: Things to avoid in the generation.
            guidance_scale: How closely to follow the prompt (higher = more literal).
            num_steps: Number of diffusion steps (higher = more quality, slower).
            **kwargs: Provider-specific parameters.
            
        Returns:
            GenerationResult with success status, paths, and metadata.
        """
        pass
    
    @abstractmethod
    def supports_image_reference(self) -> bool:
        """Returns True if provider supports image-to-image/style reference.
        
        This is critical for the style anchor cascade - if a provider
        doesn't support image references, we fall back to text-only prompts.
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is configured and ready to use.
        
        Returns True if the required API key is set in environment.
        """
        pass
    
    @abstractmethod
    def get_model_id(self, logical_model: str) -> str:
        """Map a logical model name to provider-specific model ID.
        
        Args:
            logical_model: Brandmint's logical model name (e.g., "flux-2-pro")
            
        Returns:
            Provider-specific model identifier.
        """
        pass
    
    def validate_dimensions(self, width: int, height: int) -> tuple[int, int]:
        """Validate and adjust dimensions to provider constraints.
        
        Override in subclasses if provider has specific size requirements.
        Default implementation returns dimensions unchanged.
        """
        return width, height
