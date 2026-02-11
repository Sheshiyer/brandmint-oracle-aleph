#!/usr/bin/env python3
"""
fal.ai API client for Flux 1.1 Pro and Nano Banana image generation.
Part of the visual-asset-generator skill in the brand-visual-pipeline.

Usage:
    python fal_client.py --prompt "..." --output path/to/output.png
    python fal_client.py --prompt "..." --model nano-banana --image-url "https://..." --output path/to/output.png

Environment:
    FAL_KEY - fal.ai API key (required)
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error


FAL_API_BASE = "https://queue.fal.run"

MODELS = {
    "flux-pro": "fal-ai/flux-pro/v1.1",
    "flux-dev": "fal-ai/flux/dev",
    "nano-banana": "fal-ai/nano-banana",
}


def get_api_key():
    key = os.environ.get("FAL_KEY")
    if not key:
        print("ERROR: FAL_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)
    return key


def submit_request(model_id: str, arguments: dict, api_key: str) -> dict:
    """Submit a generation request to fal.ai queue."""
    url = f"{FAL_API_BASE}/{model_id}"
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
        print(f"ERROR: fal.ai API returned {e.code}: {body}", file=sys.stderr)
        sys.exit(1)


def poll_status(request_id: str, model_id: str, api_key: str, max_wait: int = 300,
                status_url: str = None, response_url: str = None) -> dict:
    """Poll for request completion using fal.ai queue status endpoint."""
    if not status_url:
        status_url = f"{FAL_API_BASE}/{model_id}/requests/{request_id}/status"
    if not response_url:
        response_url = f"{FAL_API_BASE}/{model_id}/requests/{request_id}"
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
            print(f"  Poll error {e.code}: {body[:200]}", file=sys.stderr)
            # Some models return result directly via response_url
            if e.code == 405:
                # Try fetching the result directly
                try:
                    req2 = urllib.request.Request(result_url, headers=headers, method="GET")
                    with urllib.request.urlopen(req2, timeout=60) as resp2:
                        return json.loads(resp2.read().decode("utf-8"))
                except urllib.error.HTTPError as e2:
                    if e2.code == 400:
                        # Result not ready yet, wait and retry
                        print(f"  Result not ready, waiting...", file=sys.stderr)
                        time.sleep(5)
                        continue
                    raise
            time.sleep(5)
            continue

        req_status = status.get("status", "UNKNOWN")

        if req_status == "COMPLETED":
            # Check if response_url is provided
            resp_url = status.get("response_url", result_url)
            try:
                req2 = urllib.request.Request(resp_url, headers=headers, method="GET")
                with urllib.request.urlopen(req2, timeout=60) as resp2:
                    return json.loads(resp2.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8") if e.fp else ""
                print(f"ERROR: Failed to fetch result: {e.code}: {body[:200]}", file=sys.stderr)
                sys.exit(1)

        if req_status in ("FAILED", "CANCELLED"):
            print(f"ERROR: Generation failed: {json.dumps(status)}", file=sys.stderr)
            sys.exit(1)

        pos = status.get("queue_position", "?")
        print(f"  Status: {req_status} (position: {pos})... waiting", file=sys.stderr)
        time.sleep(5)

    print(f"ERROR: Timed out after {max_wait}s", file=sys.stderr)
    sys.exit(1)


def download_image(url: str, output_path: str):
    """Download image from URL to local path."""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=60) as resp:
        with open(output_path, "wb") as f:
            f.write(resp.read())
    print(f"  Saved: {output_path}", file=sys.stderr)


def generate_image(
    prompt: str,
    model: str = "flux-pro",
    width: int = 1024,
    height: int = 1024,
    guidance_scale: float = 7.5,
    steps: int = 50,
    negative_prompt: str = "",
    image_url: str = None,
    output_path: str = "output.png",
):
    """Generate an image using fal.ai."""
    api_key = get_api_key()
    model_id = MODELS.get(model, model)

    arguments = {
        "prompt": prompt,
        "image_size": {"width": width, "height": height},
        "num_inference_steps": steps,
        "guidance_scale": guidance_scale,
        "safety_tolerance": "2",
    }

    if negative_prompt:
        arguments["negative_prompt"] = negative_prompt

    if image_url:
        arguments["image_url"] = image_url

    print(f"Generating with {model_id}...", file=sys.stderr)
    print(f"  Prompt: {prompt[:100]}...", file=sys.stderr)

    result = submit_request(model_id, arguments, api_key)

    # Handle queue-based response
    if "request_id" in result:
        print(f"  Queued: {result['request_id']}", file=sys.stderr)
        # Use URLs from response if provided (preferred), else construct them
        status_url = result.get("status_url")
        response_url = result.get("response_url")
        print(f"  Status URL: {status_url}", file=sys.stderr)
        print(f"  Response URL: {response_url}", file=sys.stderr)
        result = poll_status(
            result["request_id"], model_id, api_key,
            status_url=status_url, response_url=response_url
        )

    # Extract image URL from result
    image_result_url = None
    if "images" in result and len(result["images"]) > 0:
        image_result_url = result["images"][0].get("url")
    elif "image" in result:
        image_result_url = result["image"].get("url")

    if not image_result_url:
        print(f"ERROR: No image URL in response: {json.dumps(result, indent=2)}", file=sys.stderr)
        sys.exit(1)

    download_image(image_result_url, output_path)

    # Return metadata
    return {
        "status": "completed",
        "output_path": output_path,
        "image_url": image_result_url,
        "model": model_id,
        "prompt": prompt,
        "dimensions": {"width": width, "height": height},
    }


def main():
    parser = argparse.ArgumentParser(description="fal.ai image generation client")
    parser.add_argument("--prompt", required=True, help="Generation prompt")
    parser.add_argument("--model", default="flux-pro", choices=list(MODELS.keys()), help="Model to use")
    parser.add_argument("--width", type=int, default=1024, help="Image width")
    parser.add_argument("--height", type=int, default=1024, help="Image height")
    parser.add_argument("--guidance-scale", type=float, default=7.5, help="Guidance scale")
    parser.add_argument("--steps", type=int, default=50, help="Inference steps")
    parser.add_argument("--negative-prompt", default="", help="Negative prompt")
    parser.add_argument("--image-url", default=None, help="Input image URL (for Nano Banana enhancement)")
    parser.add_argument("--output", required=True, help="Output file path")

    args = parser.parse_args()

    result = generate_image(
        prompt=args.prompt,
        model=args.model,
        width=args.width,
        height=args.height,
        guidance_scale=args.guidance_scale,
        steps=args.steps,
        negative_prompt=args.negative_prompt,
        image_url=args.image_url,
        output_path=args.output,
    )

    # Output metadata as JSON
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
