#!/usr/bin/env python3
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a Tauri updater latest.json manifest.")
    parser.add_argument("--archive", required=True, help="Path to the generated updater archive.")
    parser.add_argument("--signature", required=True, help="Path to the updater signature file.")
    parser.add_argument("--version", required=True, help="Release version to publish.")
    parser.add_argument("--base-url", required=True, help="Base URL where updater assets are hosted.")
    parser.add_argument("--output", required=True, help="Path to write latest.json.")
    parser.add_argument("--platform", default="darwin-aarch64", help="Updater platform key.")
    parser.add_argument("--notes", default=None, help="Optional release notes override.")
    parser.add_argument("--pub-date", default=None, help="Optional RFC3339 publication date override.")
    return parser.parse_args()


def resolve_pub_date(explicit_value: str | None) -> str:
    if explicit_value:
        return explicit_value
    if os.getenv("BRANDMINT_UPDATER_PUB_DATE"):
        return os.environ["BRANDMINT_UPDATER_PUB_DATE"]
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def resolve_notes(explicit_value: str | None) -> str | None:
    if explicit_value is not None:
        return explicit_value.strip() or None
    env_value = os.getenv("BRANDMINT_UPDATER_NOTES")
    if env_value is None:
        return None
    trimmed = env_value.strip()
    return trimmed or None


def main() -> None:
    args = parse_args()
    archive_path = Path(args.archive)
    signature_path = Path(args.signature)
    output_path = Path(args.output)

    signature = signature_path.read_text(encoding="utf-8").strip()
    payload = {
        "version": args.version.lstrip("v"),
        "pub_date": resolve_pub_date(args.pub_date),
        "platforms": {
            args.platform: {
                "signature": signature,
                "url": f"{args.base_url.rstrip('/')}/{archive_path.name}",
            }
        },
    }

    notes = resolve_notes(args.notes)
    if notes:
        payload["notes"] = notes

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(f"{json.dumps(payload, indent=2)}\n", encoding="utf-8")


if __name__ == "__main__":
    main()
