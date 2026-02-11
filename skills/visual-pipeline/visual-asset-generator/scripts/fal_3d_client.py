#!/usr/bin/env python3
"""
fal.ai 3D model generation client.
Supports Hunyuan3D V3 (text-to-3d, image-to-3d), TripoSR, and Hunyuan3D V2.
Part of the visual-asset-generator skill in the brand-visual-pipeline.

Usage:
    # Text to 3D (Hunyuan3D V3)
    python fal_3d_client.py --mode text-to-3d --prompt "a leather journal" --output ./output/

    # Image to 3D (Hunyuan3D V3)
    python fal_3d_client.py --mode image-to-3d --image-url "https://..." --output ./output/

    # Image to 3D (TripoSR - faster, cheaper)
    python fal_3d_client.py --mode triposr --image-url "https://..." --output ./output/

    # Image to 3D (Hunyuan3D V2)
    python fal_3d_client.py --mode hunyuan-v2 --image-url "https://..." --output ./output/

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

MODELS_3D = {
    "text-to-3d": "fal-ai/hunyuan3d-v3/text-to-3d",
    "image-to-3d": "fal-ai/hunyuan3d-v3/image-to-3d",
    "triposr": "fal-ai/triposr",
    "hunyuan-v2": "fal-ai/hunyuan3d/v2",
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


def poll_status(request_id: str, model_id: str, api_key: str,
                max_wait: int = 600, status_url: str = None,
                response_url: str = None) -> dict:
    """Poll for request completion. 3D models can take 2-3 minutes."""
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
            if e.code == 405:
                try:
                    req2 = urllib.request.Request(result_url, headers=headers, method="GET")
                    with urllib.request.urlopen(req2, timeout=60) as resp2:
                        return json.loads(resp2.read().decode("utf-8"))
                except urllib.error.HTTPError as e2:
                    if e2.code == 400:
                        print(f"  Result not ready, waiting...", file=sys.stderr)
                        time.sleep(10)
                        continue
                    raise
            time.sleep(10)
            continue

        req_status = status.get("status", "UNKNOWN")
        elapsed = int(time.time() - start)

        if req_status == "COMPLETED":
            resp_url = status.get("response_url", result_url)
            inference_time = status.get("metrics", {}).get("inference_time", "?")
            print(f"  Completed in {inference_time}s", file=sys.stderr)
            try:
                req2 = urllib.request.Request(resp_url, headers=headers, method="GET")
                with urllib.request.urlopen(req2, timeout=120) as resp2:
                    return json.loads(resp2.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8") if e.fp else ""
                print(f"ERROR: Failed to fetch result: {e.code}: {body[:200]}", file=sys.stderr)
                sys.exit(1)

        if req_status in ("FAILED", "CANCELLED"):
            print(f"ERROR: Generation failed: {json.dumps(status)}", file=sys.stderr)
            sys.exit(1)

        pos = status.get("queue_position", "?")
        print(f"  [{elapsed}s] Status: {req_status} (position: {pos})...", file=sys.stderr)
        time.sleep(10)

    print(f"ERROR: Timed out after {max_wait}s", file=sys.stderr)
    sys.exit(1)


def download_file(url: str, output_path: str):
    """Download file from URL to local path."""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=300) as resp:
        with open(output_path, "wb") as f:
            f.write(resp.read())
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  Saved: {output_path} ({size_mb:.1f} MB)", file=sys.stderr)


def generate_3d(
    mode: str,
    prompt: str = None,
    image_url: str = None,
    output_dir: str = "output",
    enable_pbr: bool = True,
    face_count: int = 100000,
    generate_type: str = "Normal",
):
    """Generate a 3D model using fal.ai."""
    api_key = get_api_key()
    model_id = MODELS_3D.get(mode, mode)
    os.makedirs(output_dir, exist_ok=True)

    # Build arguments based on mode
    arguments = {}

    if mode == "text-to-3d":
        if not prompt:
            print("ERROR: --prompt required for text-to-3d", file=sys.stderr)
            sys.exit(1)
        arguments = {
            "prompt": prompt,
            "enable_pbr": enable_pbr,
            "face_count": face_count,
            "generate_type": generate_type,
        }
        print(f"Generating 3D from text with {model_id}...", file=sys.stderr)
        print(f"  Prompt: {prompt}", file=sys.stderr)

    elif mode == "image-to-3d":
        if not image_url:
            print("ERROR: --image-url required for image-to-3d", file=sys.stderr)
            sys.exit(1)
        arguments = {
            "input_image_url": image_url,
            "enable_pbr": enable_pbr,
            "face_count": face_count,
            "generate_type": generate_type,
        }
        print(f"Generating 3D from image with {model_id}...", file=sys.stderr)
        print(f"  Image: {image_url[:100]}", file=sys.stderr)

    elif mode == "triposr":
        if not image_url:
            print("ERROR: --image-url required for triposr", file=sys.stderr)
            sys.exit(1)
        arguments = {
            "image_url": image_url,
        }
        print(f"Generating 3D with TripoSR...", file=sys.stderr)
        print(f"  Image: {image_url[:100]}", file=sys.stderr)

    elif mode == "hunyuan-v2":
        if not image_url:
            print("ERROR: --image-url required for hunyuan-v2", file=sys.stderr)
            sys.exit(1)
        arguments = {
            "image_url": image_url,
        }
        print(f"Generating 3D with Hunyuan3D V2...", file=sys.stderr)
        print(f"  Image: {image_url[:100]}", file=sys.stderr)

    # Submit request
    result = submit_request(model_id, arguments, api_key)

    if "request_id" in result:
        print(f"  Queued: {result['request_id']}", file=sys.stderr)
        status_url = result.get("status_url")
        response_url = result.get("response_url")
        result = poll_status(
            result["request_id"], model_id, api_key,
            max_wait=600,  # 10 min timeout for 3D
            status_url=status_url, response_url=response_url
        )

    # Extract and download model files
    downloaded = {}

    # Hunyuan3D V3 response format
    if "model_glb" in result:
        glb_url = result["model_glb"].get("url")
        if glb_url:
            glb_path = os.path.join(output_dir, "model.glb")
            download_file(glb_url, glb_path)
            downloaded["glb"] = glb_path

    if "model_urls" in result:
        for fmt, info in result["model_urls"].items():
            if info and isinstance(info, dict) and info.get("url"):
                fmt_path = os.path.join(output_dir, f"model.{fmt}")
                download_file(info["url"], fmt_path)
                downloaded[fmt] = fmt_path

    if "thumbnail" in result and result["thumbnail"]:
        thumb_url = result["thumbnail"].get("url")
        if thumb_url:
            thumb_path = os.path.join(output_dir, "preview.png")
            download_file(thumb_url, thumb_path)
            downloaded["preview"] = thumb_path

    # TripoSR response format
    if "model_mesh" in result:
        mesh_url = result["model_mesh"].get("url")
        if mesh_url:
            mesh_path = os.path.join(output_dir, "model.glb")
            download_file(mesh_url, mesh_path)
            downloaded["glb"] = mesh_path

    if not downloaded:
        # Save raw result for debugging
        raw_path = os.path.join(output_dir, "result.json")
        with open(raw_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"  No model files found. Raw result saved to {raw_path}", file=sys.stderr)
        downloaded["raw"] = raw_path

    output = {
        "status": "completed",
        "mode": mode,
        "model": model_id,
        "output_dir": output_dir,
        "files": downloaded,
        "prompt": prompt,
        "image_url": image_url,
    }

    return output


def main():
    parser = argparse.ArgumentParser(description="fal.ai 3D model generation client")
    parser.add_argument("--mode", required=True,
                        choices=list(MODELS_3D.keys()),
                        help="Generation mode")
    parser.add_argument("--prompt", default=None,
                        help="Text prompt (for text-to-3d)")
    parser.add_argument("--image-url", default=None,
                        help="Input image URL (for image-to-3d, triposr, hunyuan-v2)")
    parser.add_argument("--output", required=True,
                        help="Output directory path")
    parser.add_argument("--enable-pbr", action="store_true", default=True,
                        help="Enable PBR materials (Hunyuan3D V3)")
    parser.add_argument("--face-count", type=int, default=100000,
                        help="Target polygon count (Hunyuan3D V3)")
    parser.add_argument("--generate-type", default="Normal",
                        choices=["Normal", "LowPoly", "Geometry"],
                        help="Generation type (Hunyuan3D V3)")

    args = parser.parse_args()

    result = generate_3d(
        mode=args.mode,
        prompt=args.prompt,
        image_url=args.image_url,
        output_dir=args.output,
        enable_pbr=args.enable_pbr,
        face_count=args.face_count,
        generate_type=args.generate_type,
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
