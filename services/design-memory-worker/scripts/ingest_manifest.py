#!/usr/bin/env python3
"""Ingest a design-assets JSONL manifest into the Design Memory Worker."""
from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def post_batch(worker_url: str, token: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
    body = json.dumps({"records": records}).encode("utf-8")
    request = urllib.request.Request(
        f"{worker_url.rstrip('/')}/ingest",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "brandmint-design-memory-ingest/0.1",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8")
        raise RuntimeError(f"Ingest failed with {error.code}: {detail}") from error


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest Design Memory manifest")
    parser.add_argument("--manifest", default="data/design-assets.jsonl", help="Manifest JSONL path")
    parser.add_argument("--worker-url", required=True, help="Worker base URL")
    parser.add_argument("--batch-size", type=int, default=20, help="Records per request")
    parser.add_argument("--admin-token", default=os.environ.get("ADMIN_TOKEN", ""), help="Admin token or ADMIN_TOKEN env")
    args = parser.parse_args()

    if not args.admin_token:
        raise SystemExit("ADMIN_TOKEN is required. Pass --admin-token or set ADMIN_TOKEN env.")

    records = read_jsonl(Path(args.manifest).expanduser().resolve())
    total = 0
    for index in range(0, len(records), args.batch_size):
        batch = records[index : index + args.batch_size]
        result = post_batch(args.worker_url, args.admin_token, batch)
        count = len(result.get("ingested", []))
        total += count
        print(json.dumps({"batch": index // args.batch_size + 1, "ingested": count, "model": result.get("model")}, indent=2))

    print(json.dumps({"total_ingested": total, "manifest_records": len(records)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
