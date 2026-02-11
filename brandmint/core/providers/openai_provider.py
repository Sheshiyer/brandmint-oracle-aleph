"""
OpenAI provider adapter.

Supports DALL-E 3 and GPT-Image-1 for image generation.

Docs: https://platform.openai.com/docs/guides/images
"""

import json
import os
import sys
import base64
import urllib.request
import urllib.error
from typing import Any, Optional

from .base import ImageProvider, GenerationResult, ProviderName
from .model_mapping import get_model_id, PROVIDER_CAPABILITIES


class OpenAIProvider(ImageProvider):
    """OpenAI image generation provider.
    
    Supports:
    - DALL-E 3 (high quality, creative)
    - GPT-Image-1 (newer, supports image references)
    
    Environment:
        OPENAI_API_KEY: OpenAI API key (required)
    """
    
    OPENAI_API_BASE = "https://api.openai.com/v1"
    
    # DALL-E 3 has fixed size options
    DALLE3_SIZES = {
        (1024, 1024): "1024x1024",
        (1792, 1024): "1792x1024",
        (1024, 1792): "1024x1792",
    }
    
    @property
    def name(self) -> ProviderName:
        return ProviderName.OPENAI
    
    @property
    def display_name(self) -> str:
        return "OpenAI"
    
    def is_available(self) -> bool:
        return bool(os.environ.get("OPENAI_API_KEY"))
    
    def supports_image_reference(self) -> bool:
        return True  # GPT-Image-1 supports image references
    
    def get_model_id(self, logical_model: str) -> str:
        return get_model_id("openai", logical_model)
    
    def _get_api_key(self) -> str:
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            raise EnvironmentError("OPENAI_API_KEY environment variable not set")
        return key
    
    def validate_dimensions(self, width: int, height: int) -> tuple[int, int]:
        """Adjust dimensions to DALL-E 3's fixed size options."""
        # Find closest supported size
        aspect = width / height
        
        if aspect > 1.5:  # Landscape
            return 1792, 1024
        elif aspect < 0.67:  # Portrait
            return 1024, 1792
        else:  # Square-ish
            return 1024, 1024
    
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
        """Generate an image using OpenAI."""
        try:
            api_key = self._get_api_key()
        except EnvironmentError as e:
            return GenerationResult(
                success=False,
                error=str(e),
                model_used=model,
                provider=self.display_name,
            )
        
        model_id = self.get_model_id(model)
        
        # Adjust dimensions for DALL-E 3
        adj_width, adj_height = self.validate_dimensions(width, height)
        size_str = f"{adj_width}x{adj_height}"
        
        if (adj_width, adj_height) != (width, height):
            print(f"  [{self.display_name}] Adjusted size from {width}x{height} to {size_str}", file=sys.stderr)
        
        # DALL-E doesn't support negative prompts, so we prepend avoidance to main prompt
        full_prompt = prompt
        if negative_prompt:
            full_prompt = f"{prompt}\n\nAvoid: {negative_prompt}"
        
        payload = {
            "model": model_id,
            "prompt": full_prompt,
            "n": 1,
            "size": size_str,
            "response_format": "url",
        }
        
        # DALL-E 3 specific options
        if model_id == "dall-e-3":
            payload["quality"] = "hd"  # Use HD quality for brand assets
            payload["style"] = "natural"  # More photorealistic
        
        try:
            print(f"  [{self.display_name}] Generating with {model_id}...", file=sys.stderr)
            print(f"  Prompt: {prompt[:100]}...", file=sys.stderr)
            
            # Note: image_url reference requires GPT-Image-1 and different endpoint
            if image_url and model_id == "gpt-image-1":
                # Use image edit endpoint for style reference
                return self._generate_with_reference(
                    prompt, model_id, output_path, image_url, 
                    adj_width, adj_height, api_key
                )
            
            url = f"{self.OPENAI_API_BASE}/images/generations"
            data = json.dumps(payload).encode("utf-8")
            
            req = urllib.request.Request(
                url,
                data=data,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            
            if "data" in result and len(result["data"]) > 0:
                image_result_url = result["data"][0].get("url")
                
                if image_result_url:
                    self._download_image(image_result_url, output_path)
                    print(f"  Saved: {output_path}", file=sys.stderr)
                    
                    return GenerationResult(
                        success=True,
                        image_url=image_result_url,
                        local_path=output_path,
                        model_used=model_id,
                        provider=self.display_name,
                        metadata={
                            "dimensions": {"width": adj_width, "height": adj_height},
                            "prompt": prompt,
                            "revised_prompt": result["data"][0].get("revised_prompt"),
                        },
                    )
            
            return GenerationResult(
                success=False,
                error=f"No image in response: {json.dumps(result)[:200]}",
                model_used=model_id,
                provider=self.display_name,
            )
            
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8") if e.fp else ""
            return GenerationResult(
                success=False,
                error=f"OpenAI API error {e.code}: {body[:200]}",
                model_used=model_id,
                provider=self.display_name,
            )
        except Exception as e:
            return GenerationResult(
                success=False,
                error=str(e),
                model_used=model_id,
                provider=self.display_name,
            )
    
    def _generate_with_reference(
        self,
        prompt: str,
        model_id: str,
        output_path: str,
        image_url: str,
        width: int,
        height: int,
        api_key: str,
    ) -> GenerationResult:
        """Generate with image reference using GPT-Image-1."""
        # GPT-Image-1 uses the images/edits endpoint for style references
        # This is a simplified implementation - full version would download
        # the reference image and upload it as multipart form data
        print(f"  [{self.display_name}] Using image reference with GPT-Image-1", file=sys.stderr)
        
        # For now, fall back to standard generation with enhanced prompt
        enhanced_prompt = f"Create an image in the exact same visual style as the reference. {prompt}"
        
        payload = {
            "model": model_id,
            "prompt": enhanced_prompt,
            "n": 1,
            "size": f"{width}x{height}",
        }
        
        url = f"{self.OPENAI_API_BASE}/images/generations"
        data = json.dumps(payload).encode("utf-8")
        
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        
        if "data" in result and len(result["data"]) > 0:
            image_result_url = result["data"][0].get("url")
            if image_result_url:
                self._download_image(image_result_url, output_path)
                return GenerationResult(
                    success=True,
                    image_url=image_result_url,
                    local_path=output_path,
                    model_used=model_id,
                    provider=self.display_name,
                )
        
        return GenerationResult(
            success=False,
            error="Failed to generate with image reference",
            model_used=model_id,
            provider=self.display_name,
        )
    
    def _download_image(self, url: str, output_path: str) -> None:
        """Download image from URL to local path."""
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=60) as resp:
            with open(output_path, "wb") as f:
                f.write(resp.read())
