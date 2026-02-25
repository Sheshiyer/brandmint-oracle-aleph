#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


def _extract_content(payload: dict) -> str:
    choices = payload.get("choices", [])
    if choices:
        first = choices[0]
        if isinstance(first, dict):
            message = first.get("message", {})
            if isinstance(message, dict):
                text = message.get("content")
                if isinstance(text, str) and text.strip():
                    return text
            text = first.get("text")
            if isinstance(text, str) and text.strip():
                return text

    for key in ("output", "content", "text", "response"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value

    return ""


def run(prompt: str, model: str, endpoint: str) -> str:
    api_key = os.environ.get("NBRAIN_API_KEY")
    if not api_key:
        raise RuntimeError("NBRAIN_API_KEY is not set")
    if not endpoint.strip():
        raise RuntimeError("NBrain endpoint is required")

    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-Title": "brandmint-ui-bridge-nbrain",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"NBrain HTTP {exc.code}: {detail}") from exc

    data = json.loads(raw)
    content = _extract_content(data)
    if not content:
        raise RuntimeError("NBrain returned empty response content")
    return content


def main() -> None:
    parser = argparse.ArgumentParser(description="Run NBrain completion and optionally persist markdown output.")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--model", default="nbrain/default")
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    content = run(args.prompt, args.model, args.endpoint)
    print(content)

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content, encoding="utf-8")
        print(f"\n[nbrain-runner] wrote: {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
