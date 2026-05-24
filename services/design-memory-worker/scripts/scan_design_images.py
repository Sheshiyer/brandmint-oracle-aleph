#!/usr/bin/env python3
"""Scan a design image directory and write a JSONL ingestion manifest.

Default source directory:
/Volumes/madara/2026/twc-vault/03-Resources/Design
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def image_dimensions(path: Path) -> Tuple[Optional[int], Optional[int]]:
    try:
        from PIL import Image  # type: ignore

        with Image.open(path) as image:
            return image.size
    except Exception:
        return None, None


def infer_source(path: Path) -> str:
    lowered = str(path).lower()
    if "generated" in lowered:
        return "generated"
    if "reference" in lowered or "references" in lowered:
        return "reference"
    return "unknown"


def infer_asset_id(path: Path) -> Optional[str]:
    stem = path.stem
    token = stem.split("-")[0]
    if re.fullmatch(r"(?:\d+[A-Z]|[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*)", token):
        return token
    return None


def data_uri(path: Path) -> str:
    mime = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }.get(path.suffix.lower(), "application/octet-stream")
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def build_record(path: Path, root: Path, include_data_uri: bool) -> Dict[str, Any]:
    width, height = image_dimensions(path)
    record: Dict[str, Any] = {
        "sha256": sha256_file(path),
        "path": str(path),
        "relativePath": str(path.relative_to(root)),
        "name": path.name,
        "source": infer_source(path),
        "assetId": infer_asset_id(path),
        "width": width,
        "height": height,
        "tags": [],
        "flows": [],
        "colors": [],
    }
    if include_data_uri:
        record["imageDataUri"] = data_uri(path)
    return record


def scan(root: Path, include_data_uri: bool) -> list[Dict[str, Any]]:
    records = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            records.append(build_record(path, root, include_data_uri))
    seen = set()
    deduped = []
    for record in records:
        if record["sha256"] in seen:
            continue
        seen.add(record["sha256"])
        deduped.append(record)
    return deduped


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan design images into JSONL manifest")
    parser.add_argument(
        "--root",
        default="/Volumes/madara/2026/twc-vault/03-Resources/Design",
        help="Design image root directory",
    )
    parser.add_argument("--out", default="data/design-assets.jsonl", help="Output JSONL path")
    parser.add_argument("--include-data-uri", action="store_true", help="Embed image bytes as data URI")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    out = Path(args.out).expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"Design root does not exist: {root}")

    records = scan(root, args.include_data_uri)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    print(json.dumps({"root": str(root), "out": str(out), "records": len(records)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
