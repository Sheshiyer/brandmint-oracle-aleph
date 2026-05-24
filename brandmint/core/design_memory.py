"""Client helpers for the Brandmint Design Memory Worker."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional


def search_design_memory(
    worker_url: str,
    *,
    query: str,
    limit: int = 3,
    brand: Optional[str] = None,
    aspect: Optional[str] = None,
    flow: Optional[str] = None,
    timeout_sec: int = 10,
    require_existing: bool = True,
) -> List[str]:
    """Return local reference image paths from the Design Memory Worker.

    Network failures intentionally return an empty list so visual generation can
    continue through the normal provider fallback path.
    """
    worker_url = (worker_url or "").strip().rstrip("/")
    if not worker_url or not query.strip():
        return []

    payload: Dict[str, Any] = {"query": query, "limit": max(1, int(limit or 1))}
    if brand:
        payload["brand"] = brand
    if aspect:
        payload["aspect"] = aspect
    if flow:
        payload["flow"] = flow

    request = urllib.request.Request(
        f"{worker_url}/search",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "User-Agent": "brandmint-design-memory-client/0.1",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout_sec) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError):
        return []

    paths: List[str] = []
    for item in data.get("results", []):
        asset = item.get("asset", {}) if isinstance(item, dict) else {}
        path = asset.get("path")
        if not isinstance(path, str) or not path.strip():
            continue
        resolved = str(Path(path).expanduser())
        if require_existing and not Path(resolved).exists():
            continue
        if resolved not in paths:
            paths.append(resolved)
    return paths
