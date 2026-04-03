from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

CONTRACT_VERSION = "1"
DEFAULT_MAPPING_SPEC_VERSION = "2026-03-30"
FINGERPRINT_ALGORITHM = "sha256"
FINGERPRINT_SCOPE = "semantic-config-v1"
APPROVAL_ERROR_CODE = "config_not_approved"
APPROVAL_REMEDIATION = (
    "Review pending fields in the Brand Config Wizard, approve the config, "
    "and save the approved brand-config.yaml before launching."
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_copy(value: Any) -> Any:
    return json.loads(json.dumps(value or {}))


def _normalize_for_hash(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _normalize_for_hash(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_normalize_for_hash(item) for item in value]
    return value


def semantic_payload_from_document(document: Mapping[str, Any] | None) -> dict[str, Any]:
    payload = _json_copy(document or {})
    payload.pop("_brandmint", None)
    return payload


def compute_source_hash(source_text: str) -> str:
    if not source_text:
        return ""
    digest = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def compute_semantic_fingerprint(document_or_payload: Mapping[str, Any] | None) -> str:
    payload = semantic_payload_from_document(document_or_payload)
    normalized = json.dumps(
        _normalize_for_hash(payload),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _normalize_review_fields(fields: Mapping[str, Any] | None) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for path, raw in (fields or {}).items():
        entry = dict(raw or {})
        review_state = str(entry.get("review_state") or entry.get("reviewState") or "needs_review").strip().lower()
        normalized[str(path)] = {
            "source_keys": list(entry.get("source_keys") or entry.get("sourceKeys") or []),
            "confidence": float(entry.get("confidence") or 0),
            "review_state": review_state if review_state in {"needs_review", "confirmed", "edited"} else "needs_review",
            "source_snippets": list(entry.get("source_snippets") or entry.get("sourceSnippets") or []),
            "extracted_value": entry.get("extracted_value") or entry.get("extractedValue") or "",
            "current_value": entry.get("current_value") or entry.get("currentValue") or "",
            "label": entry.get("label") or str(path),
        }
    return normalized


def _review_lists(review: Mapping[str, Any] | None, fields: Mapping[str, Any]) -> tuple[list[str], list[str]]:
    pending_fields = sorted(
        {
            str(path)
            for path in (
                review.get("pending_fields")
                or review.get("pendingFields")
                or [key for key, value in fields.items() if value.get("review_state") == "needs_review"]
            )
        }
    )
    edited_fields = sorted(
        {
            str(path)
            for path in (
                review.get("edited_fields")
                or review.get("editedFields")
                or [key for key, value in fields.items() if value.get("review_state") == "edited"]
            )
        }
    )
    return pending_fields, edited_fields


def compose_config_document(
    semantic_config: Mapping[str, Any] | None,
    *,
    review: Mapping[str, Any] | None = None,
    source_text: str = "",
    source_uri: str = "",
    source_type: str = "product-md",
    extractor_version: str = "front-ui-v1",
    mapping_spec_version: str = DEFAULT_MAPPING_SPEC_VERSION,
    state: str = "draft",
    approved_by: str = "",
    approved_at: str = "",
    approval_note: str = "",
    existing_document: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    semantic = semantic_payload_from_document(semantic_config)
    existing_meta = dict((existing_document or {}).get("_brandmint") or {})
    existing_lineage = dict(existing_meta.get("lineage") or {})

    fields = _normalize_review_fields((review or {}).get("fields"))
    pending_fields, edited_fields = _review_lists(review or {}, fields)

    now = utc_now()
    document_state = "approved" if state == "approved" and not pending_fields else "draft"
    fingerprint_value = compute_semantic_fingerprint(semantic) if document_state == "approved" else ""

    if document_state == "approved":
        approved_by = approved_by.strip() or "brandmint-ui"
        approved_at = approved_at.strip() or now
    else:
        approved_by = ""
        approved_at = ""
        approval_note = ""

    document = semantic
    document["_brandmint"] = {
        "document": {
            "kind": "brand-config",
            "contract_version": CONTRACT_VERSION,
            "state": document_state,
        },
        "lineage": {
            "source_type": source_type or existing_lineage.get("source_type") or "product-md",
            "source_uri": source_uri or existing_lineage.get("source_uri") or "",
            "source_hash": compute_source_hash(source_text) or existing_lineage.get("source_hash") or "",
            "extractor_version": extractor_version or existing_lineage.get("extractor_version") or "",
            "mapping_spec_version": mapping_spec_version or existing_lineage.get("mapping_spec_version") or DEFAULT_MAPPING_SPEC_VERSION,
            "created_at": existing_lineage.get("created_at") or now,
            "updated_at": now,
        },
        "review": {
            "pending_fields": pending_fields,
            "edited_fields": edited_fields,
            "fields": fields,
        },
        "approval": {
            "approved_by": approved_by,
            "approved_at": approved_at,
            "approval_note": approval_note,
            "fingerprint_algorithm": FINGERPRINT_ALGORITHM,
            "fingerprint_scope": FINGERPRINT_SCOPE,
            "fingerprint_value": fingerprint_value,
        },
    }
    return document


def dump_config_document(document: Mapping[str, Any]) -> str:
    return yaml.safe_dump(_json_copy(document), sort_keys=False, allow_unicode=False)


def read_config_document(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError("Config YAML must decode to a mapping")
    return _json_copy(raw)


def write_config_document(path: Path, document: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_config_document(document), encoding="utf-8")


def config_launch_status(document: Mapping[str, Any] | None) -> dict[str, Any]:
    meta = dict((document or {}).get("_brandmint") or {})
    review = dict(meta.get("review") or {})
    approval = dict(meta.get("approval") or {})
    document_meta = dict(meta.get("document") or {})
    pending_fields = list(review.get("pending_fields") or [])
    approved = (
        document_meta.get("state") == "approved"
        and not pending_fields
        and bool(approval.get("approved_by"))
        and bool(approval.get("approved_at"))
        and bool(approval.get("fingerprint_value"))
    )
    return {
        "state": document_meta.get("state") or "draft",
        "pending_fields": pending_fields,
        "edited_fields": list(review.get("edited_fields") or []),
        "fingerprint_value": approval.get("fingerprint_value") or "",
        "is_launchable": approved,
    }


def build_approval_error(config_path: str | Path | None, pending_fields: Sequence[str] | None = None) -> str:
    pending_fields = list(pending_fields or [])
    prefix = f"Config '{config_path}' is not approved." if config_path else "Config is not approved."
    if pending_fields:
        preview = ", ".join(pending_fields[:3])
        if len(pending_fields) > 3:
            preview = f"{preview}, +{len(pending_fields) - 3} more"
        return f"{prefix} Pending review fields: {preview}. {APPROVAL_REMEDIATION}"
    return f"{prefix} {APPROVAL_REMEDIATION}"


def require_launchable_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"Config file not found: {path}")
    document = read_config_document(path)
    status = config_launch_status(document)
    if not status["is_launchable"]:
        raise ValueError(build_approval_error(path, status.get("pending_fields")))
    return document
