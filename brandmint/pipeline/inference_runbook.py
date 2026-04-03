"""Helpers for inference scaffold runbooks."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Tuple


FAILED_STATUSES = {"failed", "failed_validation", "validation_failed"}


def load_runbook(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Invalid runbook (expected object): {path}")
    assets = data.get("assets", [])
    if not isinstance(assets, list):
        raise ValueError(f"Invalid runbook assets (expected list): {path}")
    return data


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def prompt_fingerprint(asset_payload: Mapping[str, Any]) -> str:
    basis = {
        "asset_id": asset_payload.get("asset_id"),
        "agent_prompt": asset_payload.get("agent_prompt"),
        "media_prompt": (asset_payload.get("media_input") or {}).get("prompt"),
        "skills": asset_payload.get("skills"),
        "routing": asset_payload.get("routing"),
        "prompt_lineage": asset_payload.get("prompt_lineage"),
    }
    return hashlib.sha1(_stable_json(basis).encode("utf-8")).hexdigest()[:16]


def diff_runbooks(left: Mapping[str, Any], right: Mapping[str, Any]) -> List[Dict[str, Any]]:
    left_assets = {str(a.get("asset_id")): a for a in left.get("assets", []) if isinstance(a, Mapping)}
    right_assets = {str(a.get("asset_id")): a for a in right.get("assets", []) if isinstance(a, Mapping)}
    out: List[Dict[str, Any]] = []

    for asset_id in sorted(set(left_assets) | set(right_assets)):
        la = left_assets.get(asset_id)
        ra = right_assets.get(asset_id)
        if la is None or ra is None:
            out.append(
                {
                    "asset_id": asset_id,
                    "change": "missing",
                    "left_present": la is not None,
                    "right_present": ra is not None,
                }
            )
            continue

        left_skill = (la.get("skills") or {}).get("media_skill_id")
        right_skill = (ra.get("skills") or {}).get("media_skill_id")
        left_reason = (la.get("routing") or {}).get("reason")
        right_reason = (ra.get("routing") or {}).get("reason")
        left_conf = (la.get("routing") or {}).get("confidence")
        right_conf = (ra.get("routing") or {}).get("confidence")
        left_fp = prompt_fingerprint(la)
        right_fp = prompt_fingerprint(ra)

        changed = (
            left_skill != right_skill
            or left_reason != right_reason
            or left_conf != right_conf
            or left_fp != right_fp
        )
        if not changed:
            continue

        out.append(
            {
                "asset_id": asset_id,
                "change": "updated",
                "left_media_skill_id": left_skill,
                "right_media_skill_id": right_skill,
                "left_reason": left_reason,
                "right_reason": right_reason,
                "left_confidence": left_conf,
                "right_confidence": right_conf,
                "left_prompt_fingerprint": left_fp,
                "right_prompt_fingerprint": right_fp,
            }
        )

    return out


def validate_asset_contract(runbook: Mapping[str, Any], *, runbook_path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for asset in runbook.get("assets", []):
        if not isinstance(asset, Mapping):
            continue
        asset_id = str(asset.get("asset_id", "unknown"))
        expected = asset.get("expected_outputs", {})
        if not isinstance(expected, Mapping):
            rows.append(
                {
                    "asset_id": asset_id,
                    "status": "failed",
                    "reason": "expected_outputs_missing",
                    "matched_files": [],
                }
            )
            continue

        output_dir = str(expected.get("output_dir", "")).strip()
        pattern = str(expected.get("file_glob", "")).strip()
        if not output_dir or not pattern:
            rows.append(
                {
                    "asset_id": asset_id,
                    "status": "failed",
                    "reason": "output_dir_or_file_glob_missing",
                    "matched_files": [],
                }
            )
            continue

        out_dir_path = Path(output_dir)
        if not out_dir_path.is_absolute():
            out_dir_path = (runbook_path.parent / out_dir_path).resolve()

        matches = sorted(str(p) for p in out_dir_path.glob(pattern))
        rows.append(
            {
                "asset_id": asset_id,
                "batch": asset.get("batch_type", ""),
                "status": "ok" if matches else "failed",
                "reason": "matched_output" if matches else "missing_output",
                "matched_files": matches,
                "output_dir": str(out_dir_path),
                "file_glob": pattern,
            }
        )
    return rows


def collect_failed_assets(runbook: Mapping[str, Any]) -> Tuple[Dict[str, List[str]], int]:
    by_batch: Dict[str, List[str]] = {}
    failed = 0
    for asset in runbook.get("assets", []):
        if not isinstance(asset, Mapping):
            continue
        status = str(asset.get("status", "")).strip().lower()
        validation_errors = asset.get("validation_errors", [])
        if status in FAILED_STATUSES or (isinstance(validation_errors, list) and validation_errors):
            batch = str(asset.get("batch_type", "misc")).strip() or "misc"
            asset_id = str(asset.get("asset_id", "")).strip()
            if asset_id:
                by_batch.setdefault(batch, []).append(asset_id)
                failed += 1
    return by_batch, failed
