"""
OpenRouter provider adapter.

OpenRouter provides a unified API for multiple image generation models
including Flux, Stable Diffusion, and others.

Docs: https://openrouter.ai/docs
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from typing import Any, Optional

from .base import ImageProvider, GenerationResult, ProviderName
from .model_mapping import get_model_id


class OpenRouterProvider(ImageProvider):
    """OpenRouter image generation provider.
    
    Supports:
    - Flux 1.1 Pro (via Black Forest Labs)
    - Flux Dev
    - Stable Diffusion XL
    
    Environment:
        OPENROUTER_API_KEY: OpenRouter API key (required)
    """
    
    OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
    
    @property
    def name(self) -> ProviderName:
        return ProviderName.OPENROUTER
    
    @property
    def display_name(self) -> str:
        return "OpenRouter"
    
    def is_available(self) -> bool:
        return bool(os.environ.get("OPENROUTER_API_KEY"))
    
    def supports_image_reference(self) -> bool:
        return False  # OpenRouter doesn't support image-to-image for most models
    
    def get_model_id(self, logical_model: str) -> str:
        return get_model_id("openrouter", logical_model)
    
    def _get_api_key(self) -> str:
        key = os.environ.get("OPENROUTER_API_KEY")
        if not key:
            raise EnvironmentError("OPENROUTER_API_KEY environment variable not set")
        return key
    
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
        """Generate an image using OpenRouter."""
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
        
        # OpenRouter uses a chat completions-style API for image generation
        # with specific models that support image output
        payload = {
            "model": model_id,
            "prompt": prompt,
            "n": 1,
            "size": f"{width}x{height}",
        }
        
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        
        # Note: image_url is ignored as OpenRouter doesn't support image references
        if image_url:
            print(f"  [{self.display_name}] Warning: Image reference not supported, using text prompt only", file=sys.stderr)
        
        try:
            print(f"  [{self.display_name}] Generating with {model_id}...", file=sys.stderr)
            print(f"  Prompt: {prompt[:100]}...", file=sys.stderr)
            
            url = f"{self.OPENROUTER_API_BASE}/images/generations"
            data = json.dumps(payload).encode("utf-8")
            
            req = urllib.request.Request(
                url,
                data=data,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://brandmint.ai",
                    "X-Title": "Brandmint",
                },
                method="POST",
            )
            
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            
            # Extract image URL from response
            if "data" in result and len(result["data"]) > 0:
                image_data = result["data"][0]
                image_result_url = image_data.get("url")
                
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
                            "dimensions": {"width": width, "height": height},
                            "prompt": prompt,
                        },
                    )
                
                # Some responses return base64 data instead of URL
                if "b64_json" in image_data:
                    import base64
                    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
                    with open(output_path, "wb") as f:
                        f.write(base64.b64decode(image_data["b64_json"]))
                    print(f"  Saved: {output_path}", file=sys.stderr)
                    
                    return GenerationResult(
                        success=True,
                        local_path=output_path,
                        model_used=model_id,
                        provider=self.display_name,
                        metadata={
                            "dimensions": {"width": width, "height": height},
                            "prompt": prompt,
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
                error=f"OpenRouter API error {e.code}: {body[:200]}",
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
    
    def _download_image(self, url: str, output_path: str) -> None:
        """Download image from URL to local path."""
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=60) as resp:
            with open(output_path, "wb") as f:
                f.write(resp.read())
