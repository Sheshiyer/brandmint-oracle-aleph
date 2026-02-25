#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


def run(prompt: str, model: str, endpoint: str) -> str:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:4191",
            "X-Title": "brandmint-ui-bridge",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"OpenRouter HTTP {exc.code}: {detail}") from exc

    data = json.loads(body)
    choices = data.get("choices", [])
    if not choices:
        raise RuntimeError("OpenRouter returned no choices")
    message = choices[0].get("message", {}).get("content", "")
    if not message:
        raise RuntimeError("OpenRouter returned empty content")
    return message


def main() -> None:
    parser = argparse.ArgumentParser(description="Run OpenRouter completion and optionally persist markdown output.")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--model", default="openai/gpt-4o-mini")
    parser.add_argument("--endpoint", default="https://openrouter.ai/api/v1/chat/completions")
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    content = run(args.prompt, args.model, args.endpoint)
    print(content)

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content, encoding="utf-8")
        print(f"\n[openrouter-runner] wrote: {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
