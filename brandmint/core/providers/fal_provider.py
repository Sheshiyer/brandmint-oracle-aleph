"""
FAL.AI provider adapter.

This is the default provider, refactored from the original fal_client.py.
Supports Nano Banana Pro with image references (style anchor cascade).
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from typing import Any, Optional

from .base import ImageProvider, GenerationResult, ProviderName
from .model_mapping import get_model_id, PROVIDER_CAPABILITIES


class FalProvider(ImageProvider):
    """FAL.AI image generation provider.
    
    Supports:
    - Flux Pro 1.1 (high quality)
    - Nano Banana Pro (style references)
    - Recraft V3 (illustrations)
    
    Environment:
        FAL_KEY: fal.ai API key (required)
    """
    
    FAL_API_BASE = "https://queue.fal.run"
    
    @property
    def name(self) -> ProviderName:
        return ProviderName.FAL
    
    @property
    def display_name(self) -> str:
        return "FAL.AI"
    
    def is_available(self) -> bool:
        return bool(os.environ.get("FAL_KEY"))
    
    def supports_image_reference(self) -> bool:
        return True  # Nano Banana Pro supports image references
    
    def get_model_id(self, logical_model: str) -> str:
        return get_model_id("fal", logical_model)
    
    def _get_api_key(self) -> str:
        key = os.environ.get("FAL_KEY")
        if not key:
            raise EnvironmentError("FAL_KEY environment variable not set")
        return key
    
    def _submit_request(self, model_id: str, arguments: dict, api_key: str) -> dict:
        """Submit a generation request to fal.ai queue."""
        url = f"{self.FAL_API_BASE}/{model_id}"
        data = json.dumps(arguments).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Key {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8") if e.fp else ""
            raise RuntimeError(f"FAL API error {e.code}: {body}")
    
    def _poll_status(
        self,
        request_id: str,
        model_id: str,
        api_key: str,
        max_wait: int = 300,
        status_url: Optional[str] = None,
        response_url: Optional[str] = None,
    ) -> dict:
        """Poll for request completion using fal.ai queue status endpoint."""
        if not status_url:
            status_url = f"{self.FAL_API_BASE}/{model_id}/requests/{request_id}/status"
        if not response_url:
            response_url = f"{self.FAL_API_BASE}/{model_id}/requests/{request_id}"
        result_url = response_url
        headers = {"Authorization": f"Key {api_key}"}
        start = time.time()

        while time.time() - start < max_wait:
            try:
                req = urllib.request.Request(status_url, headers=headers, method="GET")
                with urllib.request.urlopen(req, timeout=30) as resp:
                    status = json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8") if e.fp else ""
                # Some models return result directly via response_url
                if e.code == 405:
                    try:
                        req2 = urllib.request.Request(result_url, headers=headers, method="GET")
                        with urllib.request.urlopen(req2, timeout=60) as resp2:
                            return json.loads(resp2.read().decode("utf-8"))
                    except urllib.error.HTTPError as e2:
                        if e2.code == 400:
                            time.sleep(5)
                            continue
                        raise
                time.sleep(5)
                continue

            req_status = status.get("status", "UNKNOWN")

            if req_status == "COMPLETED":
                resp_url = status.get("response_url", result_url)
                try:
                    req2 = urllib.request.Request(resp_url, headers=headers, method="GET")
                    with urllib.request.urlopen(req2, timeout=60) as resp2:
                        return json.loads(resp2.read().decode("utf-8"))
                except urllib.error.HTTPError as e:
                    body = e.read().decode("utf-8") if e.fp else ""
                    raise RuntimeError(f"Failed to fetch result: {e.code}: {body[:200]}")

            if req_status in ("FAILED", "CANCELLED"):
                raise RuntimeError(f"Generation failed: {json.dumps(status)}")

            time.sleep(5)

        raise TimeoutError(f"Timed out after {max_wait}s")
    
    def _download_image(self, url: str, output_path: str) -> None:
        """Download image from URL to local path."""
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=60) as resp:
            with open(output_path, "wb") as f:
                f.write(resp.read())
    
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
        """Generate an image using FAL.AI."""
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
        
        arguments = {
            "prompt": prompt,
            "image_size": {"width": width, "height": height},
            "num_inference_steps": num_steps,
            "guidance_scale": guidance_scale,
            "safety_tolerance": "2",
        }
        
        if negative_prompt:
            arguments["negative_prompt"] = negative_prompt
        
        # Image reference support (Nano Banana Pro style anchor)
        if image_url and "nano-banana" in model_id:
            arguments["image_url"] = image_url
        
        try:
            print(f"  [{self.display_name}] Generating with {model_id}...", file=sys.stderr)
            print(f"  Prompt: {prompt[:100]}...", file=sys.stderr)
            
            result = self._submit_request(model_id, arguments, api_key)
            
            # Handle queue-based response
            if "request_id" in result:
                print(f"  Queued: {result['request_id']}", file=sys.stderr)
                result = self._poll_status(
                    result["request_id"],
                    model_id,
                    api_key,
                    status_url=result.get("status_url"),
                    response_url=result.get("response_url"),
                )
            
            # Extract image URL from result
            image_result_url = None
            if "images" in result and len(result["images"]) > 0:
                image_result_url = result["images"][0].get("url")
            elif "image" in result:
                image_result_url = result["image"].get("url")
            
            if not image_result_url:
                return GenerationResult(
                    success=False,
                    error=f"No image URL in response: {json.dumps(result)[:200]}",
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
                },
            )
            
        except Exception as e:
            return GenerationResult(
                success=False,
                error=str(e),
                model_used=model_id,
                provider=self.display_name,
            )
