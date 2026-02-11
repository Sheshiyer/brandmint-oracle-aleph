"""
Replicate provider adapter.

Replicate provides serverless GPU inference for open-source models.
Pay-per-second pricing can be cost effective for batch jobs.

Docs: https://replicate.com/docs
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


class ReplicateProvider(ImageProvider):
    """Replicate image generation provider.
    
    Supports:
    - Flux 1.1 Pro (Black Forest Labs)
    - Flux Dev
    - Stable Diffusion XL
    
    Environment:
        REPLICATE_API_TOKEN: Replicate API token (required)
    """
    
    REPLICATE_API_BASE = "https://api.replicate.com/v1"
    
    # Model version mappings (Replicate requires specific versions)
    MODEL_VERSIONS = {
        "black-forest-labs/flux-1.1-pro": "black-forest-labs/flux-1.1-pro",
        "black-forest-labs/flux-dev": "black-forest-labs/flux-dev",
        "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b": "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
    }
    
    @property
    def name(self) -> ProviderName:
        return ProviderName.REPLICATE
    
    @property
    def display_name(self) -> str:
        return "Replicate"
    
    def is_available(self) -> bool:
        return bool(os.environ.get("REPLICATE_API_TOKEN"))
    
    def supports_image_reference(self) -> bool:
        return True  # Some models support img2img
    
    def get_model_id(self, logical_model: str) -> str:
        return get_model_id("replicate", logical_model)
    
    def _get_api_key(self) -> str:
        key = os.environ.get("REPLICATE_API_TOKEN")
        if not key:
            raise EnvironmentError("REPLICATE_API_TOKEN environment variable not set")
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
        """Generate an image using Replicate."""
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
        
        # Build input parameters based on model
        input_params = {
            "prompt": prompt,
            "width": width,
            "height": height,
            "num_inference_steps": num_steps,
            "guidance_scale": guidance_scale,
        }
        
        if negative_prompt:
            input_params["negative_prompt"] = negative_prompt
        
        if image_url:
            input_params["image"] = image_url
            input_params["prompt_strength"] = 0.8  # How much to follow prompt vs image
        
        try:
            print(f"  [{self.display_name}] Generating with {model_id}...", file=sys.stderr)
            print(f"  Prompt: {prompt[:100]}...", file=sys.stderr)
            
            # Create prediction
            prediction = self._create_prediction(model_id, input_params, api_key)
            prediction_id = prediction.get("id")
            
            if not prediction_id:
                return GenerationResult(
                    success=False,
                    error=f"No prediction ID in response: {json.dumps(prediction)[:200]}",
                    model_used=model_id,
                    provider=self.display_name,
                )
            
            print(f"  Prediction ID: {prediction_id}", file=sys.stderr)
            
            # Poll for completion
            result = self._poll_prediction(prediction_id, api_key)
            
            if result.get("status") == "succeeded":
                output = result.get("output")
                
                # Output format varies by model
                if isinstance(output, list) and len(output) > 0:
                    image_result_url = output[0]
                elif isinstance(output, str):
                    image_result_url = output
                else:
                    return GenerationResult(
                        success=False,
                        error=f"Unexpected output format: {type(output)}",
                        model_used=model_id,
                        provider=self.display_name,
                    )
                
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
                        "prediction_id": prediction_id,
                    },
                )
            else:
                error = result.get("error", "Unknown error")
                return GenerationResult(
                    success=False,
                    error=f"Prediction failed: {error}",
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
    
    def _create_prediction(self, model_id: str, input_params: dict, api_key: str) -> dict:
        """Create a new prediction on Replicate."""
        # Determine if we need to use model or version endpoint
        if ":" in model_id:
            # Full version string
            owner, rest = model_id.split("/", 1)
            model_name, version = rest.split(":", 1)
            url = f"{self.REPLICATE_API_BASE}/predictions"
            payload = {
                "version": version,
                "input": input_params,
            }
        else:
            # Official model (uses deployments)
            url = f"{self.REPLICATE_API_BASE}/models/{model_id}/predictions"
            payload = {
                "input": input_params,
            }
        
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
        
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    
    def _poll_prediction(self, prediction_id: str, api_key: str, max_wait: int = 300) -> dict:
        """Poll for prediction completion."""
        url = f"{self.REPLICATE_API_BASE}/predictions/{prediction_id}"
        headers = {"Authorization": f"Bearer {api_key}"}
        start = time.time()
        
        while time.time() - start < max_wait:
            req = urllib.request.Request(url, headers=headers, method="GET")
            
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            
            status = result.get("status")
            
            if status in ("succeeded", "failed", "canceled"):
                return result
            
            print(f"  Status: {status}...", file=sys.stderr)
            time.sleep(2)
        
        raise TimeoutError(f"Prediction timed out after {max_wait}s")
    
    def _download_image(self, url: str, output_path: str) -> None:
        """Download image from URL to local path."""
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=60) as resp:
            with open(output_path, "wb") as f:
                f.write(resp.read())
