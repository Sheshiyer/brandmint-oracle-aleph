#!/usr/bin/env python3
"""
Hunyuan3D generation client via HuggingFace Inference API.
Fallback for when Blender MCP is not available.
Part of the visual-asset-generator skill in the brand-visual-pipeline.

Usage:
    python hunyuan_generate.py --prompt "..." --output path/to/output/
    python hunyuan_generate.py --image-url "https://..." --output path/to/output/

Environment:
    HF_TOKEN - HuggingFace Pro token (required)

Note: Prefer using Blender MCP tools (generate_hunyuan3d_model) when Blender is running.
      This script is the fallback for headless / non-Blender environments.
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error


HF_API_BASE = "https://api-inference.huggingface.co/models"
HUNYUAN3D_MODEL = "tencent/Hunyuan3D-2"


def get_token():
    token = os.environ.get("HF_TOKEN")
    if not token:
        print("ERROR: HF_TOKEN environment variable not set", file=sys.stderr)
        sys.exit(1)
    return token


def submit_text_to_3d(prompt: str, token: str) -> dict:
    """Submit text-to-3D generation request."""
    url = f"{HF_API_BASE}/{HUNYUAN3D_MODEL}"
    data = json.dumps({
        "inputs": prompt,
        "parameters": {
            "task": "text-to-3d",
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            content_type = resp.headers.get("Content-Type", "")
            if "application/json" in content_type:
                return json.loads(resp.read().decode("utf-8"))
            else:
                # Binary response (model file)
                return {"binary": resp.read(), "content_type": content_type}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        if e.code == 503:
            # Model loading, retry
            try:
                info = json.loads(body)
                wait = info.get("estimated_time", 60)
                print(f"  Model loading, waiting {wait}s...", file=sys.stderr)
                return {"loading": True, "estimated_time": wait}
            except (json.JSONDecodeError, KeyError):
                pass
        print(f"ERROR: HuggingFace API returned {e.code}: {body}", file=sys.stderr)
        sys.exit(1)


def submit_image_to_3d(image_url: str, token: str) -> dict:
    """Submit image-to-3D generation request."""
    url = f"{HF_API_BASE}/{HUNYUAN3D_MODEL}"
    data = json.dumps({
        "inputs": {
            "image_url": image_url,
        },
        "parameters": {
            "task": "image-to-3d",
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            content_type = resp.headers.get("Content-Type", "")
            if "application/json" in content_type:
                return json.loads(resp.read().decode("utf-8"))
            else:
                return {"binary": resp.read(), "content_type": content_type}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        print(f"ERROR: HuggingFace API returned {e.code}: {body}", file=sys.stderr)
        sys.exit(1)


def generate_3d(
    prompt: str = None,
    image_url: str = None,
    output_dir: str = "output",
    max_retries: int = 3,
):
    """Generate a 3D model using Hunyuan3D via HuggingFace."""
    token = get_token()
    os.makedirs(output_dir, exist_ok=True)

    print(f"Generating 3D model with Hunyuan3D...", file=sys.stderr)
    if prompt:
        print(f"  Text prompt: {prompt}", file=sys.stderr)
    if image_url:
        print(f"  Image URL: {image_url}", file=sys.stderr)

    for attempt in range(max_retries):
        if image_url:
            result = submit_image_to_3d(image_url, token)
        elif prompt:
            result = submit_text_to_3d(prompt, token)
        else:
            print("ERROR: Must provide --prompt or --image-url", file=sys.stderr)
            sys.exit(1)

        # Handle model loading
        if isinstance(result, dict) and result.get("loading"):
            wait = result.get("estimated_time", 60)
            print(f"  Attempt {attempt + 1}: Model loading, waiting {wait}s...", file=sys.stderr)
            time.sleep(wait)
            continue

        # Handle binary response (model file)
        if isinstance(result, dict) and "binary" in result:
            output_path = os.path.join(output_dir, "model.glb")
            with open(output_path, "wb") as f:
                f.write(result["binary"])
            print(f"  Saved model: {output_path}", file=sys.stderr)
            return {
                "status": "completed",
                "output_path": output_path,
                "model": HUNYUAN3D_MODEL,
                "prompt": prompt or image_url,
            }

        # Handle JSON response (job ID or error)
        if isinstance(result, dict):
            if "error" in result:
                print(f"  Error: {result['error']}", file=sys.stderr)
                if attempt < max_retries - 1:
                    print(f"  Retrying in 30s...", file=sys.stderr)
                    time.sleep(30)
                    continue
                sys.exit(1)

            # Save whatever we got
            output_path = os.path.join(output_dir, "result.json")
            with open(output_path, "w") as f:
                json.dump(result, f, indent=2)
            print(f"  Saved result: {output_path}", file=sys.stderr)
            return {
                "status": "completed",
                "output_path": output_path,
                "model": HUNYUAN3D_MODEL,
                "result": result,
            }

    print("ERROR: Max retries exceeded", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Hunyuan3D generation via HuggingFace API")
    parser.add_argument("--prompt", default=None, help="Text prompt for text-to-3D")
    parser.add_argument("--image-url", default=None, help="Image URL for image-to-3D")
    parser.add_argument("--output", required=True, help="Output directory path")

    args = parser.parse_args()

    if not args.prompt and not args.image_url:
        print("ERROR: Must provide --prompt or --image-url", file=sys.stderr)
        sys.exit(1)

    result = generate_3d(
        prompt=args.prompt,
        image_url=args.image_url,
        output_dir=args.output,
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
