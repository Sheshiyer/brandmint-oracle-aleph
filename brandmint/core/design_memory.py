"""Client helpers for the Brandmint Design Memory Worker."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional


def design_memory_anchors(contract: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract retrieval anchors from a downstream variable contract."""
    if not isinstance(contract, dict):
        return {}
    brand = contract.get("brand_system", {}) if isinstance(contract.get("brand_system"), dict) else {}
    visual = contract.get("visual_primitives") or contract.get("visual_system") or {}
    if not isinstance(visual, dict):
        visual = {}
    assets = contract.get("asset_requirements") or contract.get("asset_plan") or {}
    if not isinstance(assets, dict):
        assets = {}
    sections = contract.get("section_defaults", {}) if isinstance(contract.get("section_defaults"), dict) else {}
    return {
        "brand_archetype": brand.get("brand_archetype"),
        "positioning": brand.get("positioning"),
        "visual_primitives": visual,
        "asset_requirements": assets.get("required", []),
        "section_defaults": sections.get("ordered_sections", []),
    }


def search_design_memory(
    worker_url: str,
    *,
    query: str,
    limit: int = 3,
    brand: Optional[str] = None,
    aspect: Optional[str] = None,
    flow: Optional[str] = None,
    variable_contract: Optional[Dict[str, Any]] = None,
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
    anchors = design_memory_anchors(variable_contract)
    if anchors:
        payload["contract"] = variable_contract
        payload["anchors"] = anchors

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
